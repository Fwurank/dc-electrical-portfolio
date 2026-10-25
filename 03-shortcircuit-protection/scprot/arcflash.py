"""Arc-flash incident energy — conceptual study.

LV (≤ 15 kV range): IEEE 1584-2018 via the open-source `arcflash` package (arcflash-calc), whose
implementation is validated in tests/ against IEEE 1584-2018 Annex D.1 / D.2 worked examples.
20 kV: OUTSIDE the IEEE 1584-2018 range (208 V–15 kV) → Lee method (theoretical maximum, open air,
very conservative), stated as such.  Arc duration is capped at 2 s (IEEE 1584-2018 §6.9.1 guidance; only valid
where the worker can leave the arc zone)."""
import math
from dataclasses import dataclass
from typing import Callable

from arcflash.ieee_1584.calculation import Calculation
from arcflash.ieee_1584.cubicle import Cubicle
from arcflash.ieee_1584.units import ureg, kA, kV, mm, J_per_sq_cm

sec = ureg.second

CAL = 4.184   # J/cm² per cal/cm²
T_CAP = 2.0


def ppe_category(e_cal: float) -> str:
    """Arc rating needed (NFPA 70E-style category labels mapped from incident energy; IEC 61482-2 APC
    equivalents: APC1 ≈ 4 cal/cm² (box test 4 kA), APC2 ≈ 7 cal/cm² (7 kA) — box-test, not directly equal)."""
    if e_cal < 1.2:
        return "< 1.2 cal/cm² (no arc-rated PPE req.)"
    for lim, cat in ((4, "PPE 1 (≥ 4 cal/cm²)"), (8, "PPE 2 (≥ 8 cal/cm²)"), (25, "PPE 3 (≥ 25 cal/cm²)"),
                     (40, "PPE 4 (≥ 40 cal/cm²)")):
        if e_cal <= lim:
            return cat
    return "> 40 cal/cm² — DANGER, no live work"


@dataclass
class Enclosure:
    name: str
    v_kv: float
    ec: str = "VCB"
    gap_mm: float = 32.0
    dist_mm: float = 609.6
    h_mm: float = 508.0
    w_mm: float = 508.0
    d_mm: float = 508.0


LV_SWGR = Enclosure("LV switchgear (MSB/UOSB)", 0.4, "VCB", 32, 609.6, 508, 508, 508)
LV_PANEL = Enclosure("LV panel / busway tap-off box", 0.4, "VCB", 25, 457.2, 355.6, 304.8, 190.5)


def ieee1584(enc: Enclosure, ibf_ka: float, t_clear: Callable[[float], float]) -> dict:
    """Runs 'full' and 'reduced' arcing current cases; clearing time evaluated at each arcing current
    (t_clear(I_arc_kA) → s). Returns the worst case."""
    cub = Cubicle(V_oc=enc.v_kv * kV, EC=enc.ec, G=enc.gap_mm * mm, D=enc.dist_mm * mm, height=enc.h_mm * mm,
                  width=enc.w_mm * mm, depth=enc.d_mm * mm)
    out = []
    for var in ("full", "reduced"):
        c = Calculation(cub, ibf_ka * kA, var)
        c.calculate_I_arc()
        ia = float(c.I_arc.to(kA).magnitude)
        t = min(float(t_clear(ia)), T_CAP)
        c.calculate_E_AFB(t * sec)
        e = float(c.E.to(J_per_sq_cm).magnitude)
        out.append({"variant": var, "iarc_ka": ia, "t_s": t, "e_jcm2": e, "e_cal": e / CAL,
                    "afb_mm": float(c.AFB.to(mm).magnitude)})
    w = max(out, key=lambda r: r["e_jcm2"])
    w = dict(w, method="IEEE 1584-2018", ibf_ka=ibf_ka, cases=out, ppe=ppe_category(w["e_cal"]))
    return w


def lee(v_kv: float, ibf_ka: float, t_s: float, dist_mm: float = 910.0) -> dict:
    """Lee method (IEEE 1584-2018 §4.2 note for > 15 kV): E[J/cm²] = 2.142e6·V[kV]·Ibf[kA]·t[s]/D²[mm²]."""
    t = min(t_s, T_CAP)
    e = 2.142e6 * v_kv * ibf_ka * t / dist_mm ** 2
    afb = math.sqrt(2.142e6 * v_kv * ibf_ka * t / 5.0)   # boundary at 5.0 J/cm² (1.2 cal/cm²)
    return {"method": "Lee (open air, conservative)", "ibf_ka": ibf_ka, "iarc_ka": ibf_ka, "t_s": t,
            "e_jcm2": e, "e_cal": e / CAL, "afb_mm": afb, "ppe": ppe_category(e / CAL)}
