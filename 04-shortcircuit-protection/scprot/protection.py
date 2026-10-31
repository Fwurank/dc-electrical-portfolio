"""Protection devices and coordination checks.

* MV relays: IEC 60255-151 inverse-time curves  t = TMS · k / ((I/Is)^α − 1)  + definite-time 50 stages.
* LV breakers: GENERIC electronic LSI trip units (IEC 60947-2 style) and a generic IEC 60898-1 C-curve MCB.
  These are not any manufacturer's curves — final selectivity must use the selected manufacturer's tables.
All currents in A at the device's own voltage unless stated; `ref_kv` converts to a common plotting base."""
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

IEC_CURVES = {"SI": (0.14, 0.02), "VI": (13.5, 1.0), "EI": (80.0, 2.0), "LTI": (120.0, 1.0)}
BREAKER_MV_S = 0.06      # VCB opening + arcing [ASSUMED]
INF = float("inf")


def iec_time(i, is_a, tms, curve="SI"):
    k, a = IEC_CURVES[curve]
    m = np.asarray(i, dtype=float) / is_a
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(m > 1.0, tms * k / (np.power(np.maximum(m, 1.0000001), a) - 1.0), np.inf)
    return t


@dataclass
class Relay:
    name: str
    kv: float
    ct_pri: float
    is51: float
    tms: float
    curve: str = "SI"
    i50: Optional[float] = None       # definite-time high set
    t50: float = 0.05
    i50_2: Optional[float] = None     # optional second DT stage
    t50_2: float = 0.0
    breaker_s: float = BREAKER_MV_S
    color: str = "C0"

    def trip(self, i):
        """relay operating time (no breaker)"""
        i = np.asarray(i, dtype=float)
        t = iec_time(i, self.is51, self.tms, self.curve)
        if self.i50:
            t = np.where(i >= self.i50, np.minimum(t, self.t50), t)
        if self.i50_2:
            t = np.where(i >= self.i50_2, np.minimum(t, self.t50_2), t)
        return t

    def clear(self, i):
        return self.trip(i) + self.breaker_s

    def settings_row(self):
        return {"Device": self.name, "kV": self.kv, "CT": f"{self.ct_pri:.0f}/1", "51 Is (A)": round(self.is51),
                "Is/In(CT)": round(self.is51 / self.ct_pri, 2), "Curve": f"IEC {self.curve}", "TMS": self.tms,
                "50 I>> (A)": round(self.i50) if self.i50 else "—", "t>> (s)": self.t50 if self.i50 else "—"}


@dataclass
class LSI:
    """Generic electronic trip unit. L: t = tr·(6·Ir/I)² ; S: definite tsd above Isd ; I: instantaneous above Ii."""
    name: str
    kv: float
    frame: float
    ir: float
    tr: float = 12.0
    isd: Optional[float] = None
    tsd: float = 0.1
    ii: Optional[float] = None
    tol_i: float = 0.10
    t_open: float = 0.05      # opening/clearing time at instantaneous / short time
    icu_ka: float = 65.0
    icw_ka: float = 65.0
    color: str = "C1"
    zsi: bool = False

    def _zones(self, i):
        i = np.asarray(i, dtype=float)
        with np.errstate(divide="ignore"):
            tl = np.where(i > 1.05 * self.ir, self.tr * (6 * self.ir / i) ** 2, np.inf)
        return i, tl

    def _t(self, i, scale_i, l_fac, s_add, i_t):
        i, tl = self._zones(np.asarray(i, dtype=float) * scale_i)
        t = tl * l_fac
        if self.isd:   # S zone replaces L above Isd (I²t OFF)
            t = np.where(i >= self.isd, self.tsd + s_add, t)
        if self.ii:
            t = np.where(i >= self.ii, i_t, t)
        return t

    def trip(self, i):
        """earliest trip (lower band edge): +tol on current, L −20 %, S tsd − 0.02 s"""
        return self._t(i, 1 / (1 - self.tol_i), 0.8, -0.02, 0.005)

    def clear(self, i):
        """latest clearing (upper band edge): −tol on current, L +0 %, S tsd + t_open"""
        return self._t(i, 1 / (1 + self.tol_i), 1.0, self.t_open, self.t_open * 0.6)

    def settings_row(self):
        return {"Device": self.name, "Frame (A)": self.frame, "Ir (A)": self.ir, "tr@6Ir (s)": self.tr,
                "Isd (A)": round(self.isd) if self.isd else "—", "tsd (s)": self.tsd if self.isd else "—",
                "Ii (A)": round(self.ii) if self.ii else "OFF", "Icu/Icw (kA)": f"{self.icu_ka:.0f}/{self.icw_ka:.0f}"}


@dataclass
class MCB:
    """Generic IEC 60898-1 C-curve MCB band (conventional limit points), In ≤ 63 A."""
    name: str
    in_a: float = 63.0
    kv: float = 0.4
    icn_ka: float = 15.0
    color: str = "C3"
    UPPER = [(1.45, 3600), (2.55, 120), (5.0, 20), (9.99, 5)]      # latest clearing, thermal
    LOWER = [(1.13, 3600), (2.55, 1.0), (4.99, 0.25)]                # earliest trip, thermal

    def _interp(self, pts, m):
        x = np.log([p[0] for p in pts]); y = np.log([p[1] for p in pts])
        out = np.exp(np.interp(np.log(m), x, y, left=np.inf, right=y[-1]))
        out = np.where(m < pts[0][0], np.inf, out)
        return out

    def clear(self, i):
        m = np.asarray(i, dtype=float) / self.in_a
        t = self._interp(self.UPPER, np.maximum(m, 1e-9))
        return np.where(m >= 10.0, 0.01, t)

    def trip(self, i):
        m = np.asarray(i, dtype=float) / self.in_a
        t = self._interp(self.LOWER, np.maximum(m, 1e-9))
        return np.where(m >= 5.0, 0.004, t)


# ------------------------------------------------------------------ margins
def margin(down, up, i_from, i_to, n=200, up_scale=1.0, down_scale=1.0):
    """Minimum time margin t_up_trip − t_down_clear over current range [i_from, i_to] (A at the downstream
    device's base). up_scale converts downstream amps to upstream device amps (e.g. 0.42/20 for MV relays)."""
    i = np.geomspace(i_from, i_to, n)
    tu = np.asarray(up.trip(i * up_scale), dtype=float)
    td = np.asarray(down.clear(i * down_scale), dtype=float)
    ok = np.isfinite(tu) & np.isfinite(td)
    if not ok.any():
        return {"min_margin_s": INF, "at_a": None}
    with np.errstate(invalid="ignore"):
        d = np.where(ok, tu - td, np.inf)
    k = int(np.argmin(d))
    return {"min_margin_s": float(d[k]), "at_a": float(i[k])}


def margin_relay(down: Relay, up: Relay, i_from, i_to, n=200):
    """MV relay-relay margin: upstream relay time − downstream relay time (CTI includes breaker time)."""
    i = np.geomspace(i_from, i_to, n)
    tu, td = up.trip(i), down.trip(i)
    ok = np.isfinite(tu) & np.isfinite(td)
    with np.errstate(invalid="ignore"):
        d = np.where(ok, tu - td, np.inf)
    k = int(np.argmin(d))
    return {"min_margin_s": float(d[k]), "at_a": float(i[k])}


def pick_tms(down, up: Relay, i_from, i_to, cti=0.3, step=0.01, down_is_relay=True, scale=1.0):
    """Smallest TMS (in `step`) giving ≥ cti over the current range."""
    for k in range(1, 200):
        up.tms = round(k * step, 3)
        m = margin_relay(down, up, i_from, i_to) if down_is_relay else margin(down, up, i_from, i_to, up_scale=scale)
        if m["min_margin_s"] >= cti:
            return up.tms, m
    raise RuntimeError("no TMS found")


# ------------------------------------------------------------------ CT check
@dataclass
class CT:
    name: str
    ipn: float
    alf: float = 20.0         # 5P20
    sn_va: float = 15.0
    rct: float = 2.0
    lead_m: float = 20.0
    lead_mm2: float = 2.5
    relay_va: float = 0.05
    ith_multiple: float = 100.0   # CT short-time thermal rating, × Ipn for 1 s [ASSUMED]

    def check(self, ik_max_ka, i50_a=None):
        rb_rated = self.sn_va  # 1 A secondary: VA = Ω
        r_lead = 2 * self.lead_m * 0.0175 / self.lead_mm2
        rb = r_lead + self.relay_va
        alf_eff = self.alf * (self.rct + rb_rated) / (self.rct + rb)
        need = max(ik_max_ka * 1e3 / self.ipn, (2 * i50_a / self.ipn) if i50_a else 0)
        ith = self.ith_multiple * self.ipn / 1e3
        return {"CT": self.name, "Ratio": f"{self.ipn:.0f}/1", "Class": f"5P{self.alf:.0f} {self.sn_va:.0f} VA",
                "Rct+Rb (Ω)": round(self.rct + rb, 2), "ALF'": round(alf_eff, 1), "Ik max (kA)": round(ik_max_ka, 2),
                "ALF' needed": round(need, 1), "Ith CT 1s (kA)": round(ith, 1),
                "OK": bool(alf_eff >= need and ith >= ik_max_ka)}


# ------------------------------------------------------------------ transformer curves
def tx_damage_curve(sr_mva, uk, ur_kv):
    """IEC 60076-5 2-s through-fault withstand, extended as I²t = const (category II 'frequent fault' shape is
    not modelled — conceptual)."""
    in_a = sr_mva * 1e6 / (math.sqrt(3) * ur_kv * 1e3)
    i2 = in_a / uk
    i = np.geomspace(2 * in_a, i2, 50)
    t = 2.0 * (i2 / i) ** 2
    return i, np.minimum(t, 2000)


def inrush_point(sr_mva, ur_kv, mult=12.0, t=0.1):
    return mult * sr_mva * 1e6 / (math.sqrt(3) * ur_kv * 1e3), t
