"""Busbar-trunking (busway) selection per IEC 61439-6."""
import math
from .tables import STD_BUSWAY_A, BUSWAY_K_AMB, BUSWAY_Z, BUSWAY_ICW_KA
from .util import interp


def select_busway(ib_a: float, length_m: float, ambient_c: float = 35.0, distributed: bool = False,
                  cosphi: float = 0.95, vd_limit_pct: float = 1.0, ik_ka: float = 0.0, in_a: float = None,
                  u_v: float = 400.0) -> dict:
    """Smallest standard busway with derated rating ≥ max(Ib, In of upstream device),
    voltage drop ≤ limit and Icw ≥ Ik (otherwise flagged: needs current-limiting upstream device and
    a verified conditional short-circuit current per IEC 61439-6).
    distributed=True: uniformly distributed tap-off load → voltage-drop factor 0.5."""
    k = interp(BUSWAY_K_AMB, max(ambient_c, 35.0))
    need = max(ib_a, in_a or 0)
    for r in STD_BUSWAY_A:
        if r * k < need:
            continue
        rr, xx = BUSWAY_Z[r]
        sinphi = math.sqrt(1 - cosphi ** 2)
        f = 0.5 if distributed else 1.0
        vd = math.sqrt(3) * ib_a * length_m * f * (rr * cosphi + xx * sinphi) / 1000.0 / u_v * 100
        if vd > vd_limit_pct:
            continue
        icw = BUSWAY_ICW_KA[r]
        return {"rating_a": r, "k_amb": k, "loading": ib_a / (r * k), "vd_pct": vd, "icw_ka": icw,
                "sc_ok": icw >= ik_ka, "ok": True}
    return {"rating_a": None, "ok": False, "k_amb": k}
