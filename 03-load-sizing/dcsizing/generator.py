"""Generator sizing: kVA/kWe, site derating, step-load & transient check, HVO fuel autonomy."""
import math
from .tables import STD_GEN_KVA, GEN_DERATE, SFC_HVO_L_PER_KWH, G3_DU_DYN_MAX, GEN_MAX_STEP_FRAC
from .util import interp


def derate_factor(ambient_c: float, altitude_m: float, d=GEN_DERATE) -> float:
    """Site power derating vs. the manufacturer site rating (40 °C / 1000 m) [ASSUMED slopes;
    ISO 3046-1 defines the method, actual curves are engine-specific]."""
    kt = 1 - max(0.0, ambient_c - d["t_ref_c"]) * d["pct_per_k"] / 100
    ka = 1 - max(0.0, altitude_m - d["alt_ref_m"]) / 100 * d["pct_per_100m"] / 100
    return kt * ka


def select_genset(load_kw: float, load_kvar: float, ambient_c: float = 32.0, altitude_m: float = 150.0,
                  max_loading: float = 0.90, pf_rated: float = 0.8, series=STD_GEN_KVA,
                  largest_step_kw: float = 0.0, max_step_frac: float = GEN_MAX_STEP_FRAC) -> dict:
    """Smallest standard genset with derated kWe·max_loading ≥ load_kw and kVA ≥ load kVA.
    max_loading 90 % of DCC (ISO 8528-1 data-center continuous) is a design-margin policy [ASSUMED].
    largest_step_kw: optional single-step load that must stay ≤ max_step_frac of site kWe (ISO 8528-5 G3,
    turbo-charged engine first-step capability, [ASSUMED] 33 %)."""
    k = derate_factor(ambient_c, altitude_m)
    s_load = math.hypot(load_kw, load_kvar)
    for kva in sorted(series):
        kwe = kva * pf_rated * k
        if kwe * max_loading >= load_kw and kva * k >= s_load and largest_step_kw <= max_step_frac * kwe + 1e-9:
            return {"kva": kva, "kwe": kva * pf_rated, "kwe_site": kwe, "derate": k,
                    "loading_kw": load_kw / kwe, "loading_kva": s_load / (kva * k),
                    "governed_by": "step load" if _smaller_ok_without_step(load_kw, s_load, kva, k, pf_rated, max_loading, series)
                    else "kW/kVA loading"}
    return {"kva": None, "kwe": None, "kwe_site": None, "derate": k, "loading_kw": float("inf"),
            "loading_kva": float("inf")}


def transient_voltage_dip(step_kva: float, gen_kva: float, xd1: float = 0.22) -> float:
    """Approximate transient voltage dip for a sudden load step (classic voltage-divider estimate
    ΔU ≈ x'd·s / (1 + x'd·s), s = step/rating).  [ASSUMED simplification; vendor transient
    analysis required]"""
    s = step_kva / gen_kva
    return xd1 * s / (1 + xd1 * s)


def step_load_check(steps_kw, gen_kwe: float, gen_kva: float, pf_step: float = 0.9, xd1: float = 0.22,
                    max_step_frac: float = GEN_MAX_STEP_FRAC, du_max: float = G3_DU_DYN_MAX) -> list:
    out = []
    for i, p in enumerate(steps_kw, 1):
        frac = p / gen_kwe
        du = transient_voltage_dip(p / pf_step, gen_kva, xd1)
        out.append({"step": i, "kw": p, "frac": frac, "du": du,
                    "ok": frac <= max_step_frac + 1e-9 and du <= du_max})
    return out


def sfc(load_frac: float) -> float:
    return interp(SFC_HVO_L_PER_KWH, load_frac)


def fuel_rate_lph(load_kw: float, gen_kwe: float) -> float:
    return load_kw * sfc(load_kw / gen_kwe)


def tank_volume_for_autonomy(hours: float, load_kw: float, gen_kwe: float, usable_frac: float = 0.90) -> float:
    """Gross tank volume (litres) for the required autonomy; usable fraction excludes sump/unpumpable
    volume and the ≥ 10 % reserve [ASSUMED]."""
    return fuel_rate_lph(load_kw, gen_kwe) * hours / usable_frac


def autonomy_hours(tank_l: float, load_kw: float, gen_kwe: float, usable_frac: float = 0.90) -> float:
    return tank_l * usable_frac / fuel_rate_lph(load_kw, gen_kwe)


def _smaller_ok_without_step(load_kw, s_load, kva, k, pf_rated, max_loading, series):
    """True if the next-smaller rating would pass on loading alone (→ selection governed by step load)."""
    smaller = [x for x in sorted(series) if x < kva]
    if not smaller:
        return False
    x = smaller[-1]
    return x * pf_rated * k * max_loading >= load_kw and x * k >= s_load
