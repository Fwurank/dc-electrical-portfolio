"""(d) AI-training power-swing smoothing (0.1 s resolution).

Synthetic GPU-cluster profile: synchronous training alternates compute (≈1.0 pu) and communication/all-reduce
(≈ duty_low pu) phases with a period of a few seconds, plus checkpoints, job start, crash and restart — the
behaviour described in NERC's Large Loads work (swings up to ~90 %, 0.1–1 Hz cycling).

Controller (BESS at MSG-20, grid-following):
    P_ref  = LPF_τ(P_load) − K_soc·(E − E_mid)          (SOC feedback keeps the battery centred)
    P_grid = rate-limit(P_ref, R)                       (grid-code-style ramp limit, MW/min)
    P_bess = P_load − P_grid, delivered through a first-order lag = response time
Metrics: max 1-min change, max 1-s ramp, 0.1–2 Hz oscillation band peak-to-peak, BESS P/E needs, throughput.
"""
from dataclasses import replace

import numpy as np

from .assumptions import AiSwing


def ai_profile(a: AiSwing = None, seed=3):
    a = a or AiSwing()
    rng = np.random.default_rng(seed)
    n = int(a.horizon_s / a.dt_s)
    t = np.arange(n) * a.dt_s
    phase = (t % a.period_s) / a.period_s
    hi_frac = 0.7
    pu = np.where(phase < hi_frac, 1.0, a.duty_low)
    pu = pu + rng.normal(0, 0.004, n)
    job = np.zeros(n)
    on = (t >= 120) & (t < 2700) | (t >= 2950)
    job[on] = 1.0
    pu = np.where(job > 0, pu, 0.10)                                    # idle GPUs ≈ 10 %
    ck = ((t % a.ckpt_every_s) < a.ckpt_len_s) & (t > 300) & (job > 0)
    pu = np.where(ck, 0.20, pu)                                         # checkpoint: GPUs wait on storage
    # facility-level AI power ramps fast but not instantly (rise_s 10–90 %)
    k = max(1, int(round(a.rise_s / 0.8 / a.dt_s)))
    pu = np.convolve(np.pad(pu, (k, k), mode="edge"), np.ones(k) / k, mode="same")[k:-k]
    base = a.p_base_mw + 0.05 * np.sin(2 * np.pi * t / 900) + rng.normal(0, 0.003, n)
    return t, base + a.p_ai_mw * pu


def _lag(x, tau_s, dt):
    if tau_s <= 0:
        return x.copy()
    y = np.empty_like(x)
    al = dt / (tau_s + dt)
    y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = y[i - 1] + al * (x[i] - y[i - 1])
    return y


class _Actuator:
    """transport delay (measurement + control) followed by a ≈20 ms first-order current loop"""

    def __init__(self, response_ms, dt):
        self.d = int(round(response_ms / 1e3 / dt))
        self.buf = np.zeros(self.d + 1)
        self.k = 0
        self.al = dt / (0.02 + dt)
        self.y = 0.0

    def step(self, cmd):
        if self.d:
            self.buf[self.k] = cmd
            self.k = (self.k + 1) % (self.d + 1)
            cmd = self.buf[self.k]
        self.y += self.al * (cmd - self.y)
        return self.y


def smooth(load, a: AiSwing = None, tau_lpf_s=30.0, response_ms=150.0, ramp_mw_min=None, k_soc=4.0,
           p_max=None, hybrid_split_s=None, sc_response_ms=5.0):
    """Ramp-limited smoothing. With hybrid_split_s the fast part (high-pass, τ = split) goes to a supercapacitor."""
    a = a or AiSwing()
    R = (ramp_mw_min if ramp_mw_min is not None else a.ramp_mw_min) / 60.0 * a.dt_s   # MW per step
    dt_h = a.dt_s / 3600.0
    n = len(load)
    al = a.dt_s / (tau_lpf_s + a.dt_s)
    als = a.dt_s / (hybrid_split_s + a.dt_s) if hybrid_split_s else None
    lp = g = load[0]
    pg, pb, psc, e, esc = (np.empty(n) for _ in range(5))
    ecur = escur = split = 0.0
    bat, sc = _Actuator(response_ms, a.dt_s), _Actuator(sc_response_ms, a.dt_s)
    for i in range(n):
        lp += al * (load[i] - lp)
        g += min(max(lp - k_soc * ecur - g, -R), R)
        cmd = load[i] - g
        if als:
            split += als * (cmd - split)
            ys = sc.step(cmd - split)
            yb = bat.step(split)
        else:
            ys, yb = 0.0, bat.step(cmd)
        if p_max is not None:
            yb = min(max(yb, -p_max), p_max)
        pb[i], psc[i] = yb, ys
        pg[i] = load[i] - yb - ys
        ecur -= yb * dt_h
        escur -= ys * dt_h
        e[i], esc[i] = ecur, escur
    return {"p_grid": pg, "p_bess": pb, "p_sc": psc, "e_rel": e, "e_sc": esc}


def band_pp(x, dt, f_lo=0.1, f_hi=2.0):
    X = np.fft.rfft(x - x.mean())
    f = np.fft.rfftfreq(len(x), dt)
    X[(f < f_lo) | (f > f_hi)] = 0
    y = np.fft.irfft(X, len(x))
    m = len(y) // 20                                       # ignore edge effects
    return float(y[m:-m].max() - y[m:-m].min())


def spectrum(x, dt):
    X = np.abs(np.fft.rfft(x - x.mean())) * 2 / len(x)
    return np.fft.rfftfreq(len(x), dt), X


def metrics(t, load, res, a: AiSwing = None):
    a = a or AiSwing()
    dt = a.dt_s
    pg = res["p_grid"]
    k1 = int(1 / dt)
    g1 = pg[: len(pg) // k1 * k1].reshape(-1, k1).mean(1)   # 1-s means
    l1 = load[: len(load) // k1 * k1].reshape(-1, k1).mean(1)
    ch_min = lambda s: float(np.max(np.abs(s[60:] - s[:-60])))
    usable_frac = 0.9
    e_swing = float(res["e_rel"].max() - res["e_rel"].min())
    thr = float(np.sum(np.clip(res["p_bess"], 0, None)) * dt / 3600)
    return {"load_1min_change_mw": ch_min(l1), "grid_1min_change_mw": ch_min(g1),
            "load_1s_ramp_mw_min": float(np.max(np.abs(np.diff(l1))) * 60),
            "grid_1s_ramp_mw_min": float(np.max(np.abs(np.diff(g1))) * 60),
            "load_osc_pp_mw": band_pp(load, dt), "grid_osc_pp_mw": band_pp(pg, dt),
            "p_bess_req_mw": float(np.max(np.abs(res["p_bess"]))), "e_swing_mwh": e_swing,
            "e_req_mwh": e_swing / usable_frac,
            "p_sc_req_mw": float(np.max(np.abs(res["p_sc"]))),
            "e_sc_kwh": float(res["e_sc"].max() - res["e_sc"].min()) * 1e3, "throughput_mwh_per_h": float(thr * 3600 / (t[-1] + dt)),
            "ok_ramp": bool(ch_min(g1) <= a.ramp_mw_min * 1.05 + 0.05), "ok_osc": bool(band_pp(pg, dt) <= a.osc_band_mw)}


def sweep_ramp(a: AiSwing = None, ramps=(1, 2, 3, 5, 10, 20), **kw):
    a = a or AiSwing()
    t, L = ai_profile(a)
    out = []
    for r in ramps:
        res = smooth(L, a, ramp_mw_min=r, **kw)
        m = metrics(t, L, res, replace(a, ramp_mw_min=r))
        out.append({"ramp_mw_min": r, **m})
    return out


def hybrid(a: AiSwing = None, split_s=5.0, response_ms=150.0, sc_response_ms=5.0):
    a = a or AiSwing()
    t, L = ai_profile(a)
    res = smooth(L, a, response_ms=response_ms, hybrid_split_s=split_s, sc_response_ms=sc_response_ms)
    return t, L, res, metrics(t, L, res, a)


def sweep_response(a: AiSwing = None, resp_ms=(0, 20, 50, 100, 150, 300, 600)):
    a = a or AiSwing()
    t, L = ai_profile(a)
    return [{"response_ms": r, **metrics(t, L, smooth(L, a, response_ms=r), a)} for r in resp_ms]


ALTERNATIVES = [
    ("Li-ion BESS at 20 kV (this study)", "100–300 ms", "Minutes–hours", "≈ 6 000 EFC (shallow µ-cycles less severe)",
     "Shares asset with peak shaving/FCR; must reserve P/E for smoothing; fast oscillations add throughput"),
    ("Supercapacitor / hybrid (EDLC)", "< 10 ms", "Seconds (≈ 1–30 s)", "≈ 10⁶ cycles",
     "Ideal for the 0.1–2 Hz iteration ripple; cannot cover crash/start ramps (needs minutes)"),
    ("UPS battery (LV, per block)", "≈ ms (already online, double conversion)", "≈ 5 min at full IT load",
     "Li-ion UPS ≈ 3 000–6 000 cycles", "Closest to the load; but cycling erodes backup reserve and warranty; "
     "requires UPS firmware support (grid-interactive mode)"),
    ("GPU / software power floor ('burn' kernels, power capping)", "Instant", "n/a (wastes energy)", "n/a",
     "Cheapest; costs energy (e.g. 5–15 % of AI power) and needs workload-owner cooperation"),
]
