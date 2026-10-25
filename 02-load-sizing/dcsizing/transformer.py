"""MV/LV and HV/MV transformer sizing, loading, losses and IEC 60909 short-circuit at the LV/MV bus."""
import cmath
import math
from .tables import STD_TX_KVA, DRY_TX_LOSSES_KW
from .util import next_std


def select_transformer(load_kva_failure: float, load_kva_normal: float, max_failure: float = 1.00,
                       max_normal: float = 0.80, series=STD_TX_KVA) -> float:
    """Smallest standard rating meeting both the N-1 (failure-mode) and normal loading limits.
    Limits are design policy [ASSUMED]: ≤ 100 % of AN rating in failure mode (fans give extra
    margin per IEC 60076-11/-12), ≤ 80 % in normal operation."""
    need = max(load_kva_failure / max_failure, load_kva_normal / max_normal)
    return next_std(need, series)


def loading(load_kva: float, rating_kva: float) -> float:
    return load_kva / rating_kva


def losses_kw(rating_kva: float, load_kva: float, table=DRY_TX_LOSSES_KW, p0_pk=None) -> float:
    p0, pk = p0_pk if p0_pk else table[rating_kva]
    return p0 + pk * (load_kva / rating_kva) ** 2


def rated_current(rating_kva: float, u_v: float) -> float:
    return rating_kva * 1000 / (math.sqrt(3) * u_v)


def z_network(sk_mva: float, u_kv: float, c: float = 1.1, x_over_r: float = 10.0) -> complex:
    """IEC 60909-0 eq. (6): Z_Q = c·U_n² / S''_kQ, split by X/R."""
    z = c * u_kv ** 2 / sk_mva
    r = z / math.sqrt(1 + x_over_r ** 2)
    return complex(r, r * x_over_r)


def z_transformer(rating_kva: float, uk: float, pk_kw: float, u_kv: float, kt: bool = True,
                  cmax: float = 1.05) -> complex:
    """IEC 60909-0 eq. (7)-(9) + correction factor KT eq. (12a) (network transformers)."""
    sn = rating_kva / 1000.0
    z = uk * u_kv ** 2 / sn
    r = (pk_kw / 1000.0) / sn * u_kv ** 2 / sn
    x = math.sqrt(max(z ** 2 - r ** 2, 0))
    zt = complex(r, x)
    if kt:
        xt = x / (u_kv ** 2 / sn)
        zt *= 0.95 * cmax / (1 + 0.6 * xt)
    return zt


def ik3_at_lv_bus(rating_kva: float, uk: float, pk_kw: float, sk_mv_mva: float, u_lv_kv: float = 0.4,
                  ur_lv_kv: float = 0.42, c: float = 1.05, mv_x_over_r: float = 10.0,
                  extra_z: complex = 0j) -> dict:
    """Max initial symmetrical short-circuit current I''k3 (kA) at the LV bus of a MV/LV transformer.

    Network impedance referred to the LV side with the transformer rated ratio. c = 1.05 for LV
    systems with +6 % tolerance (IEC 60909-0 Table 1).  Returns kA and the peak current ip.
    """
    zq = z_network(sk_mv_mva, ur_lv_kv, c=1.1, x_over_r=mv_x_over_r)   # referred to LV
    zt = z_transformer(rating_kva, uk, pk_kw, ur_lv_kv, kt=True, cmax=c)
    zk = zq + zt + extra_z
    ik = c * u_lv_kv / (math.sqrt(3) * abs(zk))   # kA
    rx = zk.real / zk.imag
    kappa = 1.02 + 0.98 * math.exp(-3 * rx)        # eq. (55)
    return {"ik_ka": ik, "ip_ka": kappa * math.sqrt(2) * ik, "r_over_x": rx, "z_ohm": zk}


def ik3_mv(sk_hv_mva: float, rating_mva: float, uk: float, pk_kw: float, u_kv: float = 20.0,
           ur_kv: float = 21.0, n_parallel: int = 1, c: float = 1.1) -> float:
    """I''k3 (kA) at the MV bus fed by n parallel HV/MV transformers (paralleling normally blocked → n=1)."""
    zq = z_network(sk_hv_mva, ur_kv, c=c)
    zt = z_transformer(rating_mva * 1000, uk, pk_kw, ur_kv, kt=True, cmax=c) / n_parallel
    return c * u_kv / (math.sqrt(3) * abs(zq + zt))


def ik3_generator(rating_kva: float, xd2: float, u_kv: float = 0.4, c: float = 1.05, rg_over_xd: float = 0.15):
    """Generator-only contribution at its terminals (IEC 60909-0 §6.6.1, KG ≈ 1 assumed)."""
    zbase = u_kv ** 2 / (rating_kva / 1000)
    x = xd2 * zbase
    z = complex(rg_over_xd * x, x)
    return c * u_kv / (math.sqrt(3) * abs(z))
