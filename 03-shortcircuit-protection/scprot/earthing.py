"""20 kV neutral earthing comparison: compensated (Petersen coil + parallel resistor) vs low-resistance (NER),
conceptual earth-potential-rise / touch-voltage screening against EN 50522.  All cable capacitances,
earth resistance and reduction factor are [ASSUMED] typical values."""
import math
from dataclasses import dataclass

W = 2 * math.pi * 50

# EN 50522:2010 permissible touch voltage UTp (Fig. 4 / Table B.3) — verify against the standard edition in use
UTP_TABLE = [(0.05, 716), (0.10, 654), (0.20, 537), (0.50, 220), (1.00, 117), (2.00, 96), (5.00, 86), (10.0, 85)]


def utp(t_s: float) -> float:
    if t_s <= UTP_TABLE[0][0]:
        return UTP_TABLE[0][1]
    for (t1, u1), (t2, u2) in zip(UTP_TABLE, UTP_TABLE[1:]):
        if t_s <= t2:
            f = (math.log(t_s) - math.log(t1)) / (math.log(t2) - math.log(t1))
            return math.exp(math.log(u1) + f * (math.log(u2) - math.log(u1)))
    return UTP_TABLE[-1][1]


@dataclass
class EarthingData:
    un_kv: float = 20.0
    c240_uf_km: float = 0.32       # 12/20 kV XLPE 1×240 Al, per phase [ASSUMED]
    c95_uf_km: float = 0.22        # 12/20 kV XLPE 1×95 Al [ASSUMED]
    feeders_per_section: int = 6
    feeder_km: float = 0.6
    tx_per_section: int = 18       # 6 halls × 3 transformer cables on each 20 kV section
    tx_cable_km: float = 0.15
    other_ic_a: float = 3.0        # switchgear, BESS/aux cables, transformer windings [ASSUMED]
    detuning: float = 0.10         # over-compensation 10 %
    loss_pct: float = 2.5          # coil + cable losses, % of Ic
    ir_par_a: float = 10.0         # parallel resistor (switched in for the 67N measurement)
    ner_a: float = 500.0           # low-resistance option, 10 s rated
    re_ohm: float = 0.2            # campus global earthing system resistance [ASSUMED]
    r_factor: float = 0.6          # reduction factor (cable screens carry part of the return current) [ASSUMED]


def ic_section(e: EarthingData = None) -> float:
    """Capacitive earth-fault current of one 20 kV section: Ic = √3·ω·C·Un."""
    e = e or EarthingData()
    c = (e.feeders_per_section * e.feeder_km * e.c240_uf_km + e.tx_per_section * e.tx_cable_km * e.c95_uf_km) * 1e-6
    return math.sqrt(3) * W * c * e.un_kv * 1e3 + e.other_ic_a


def compare(e: EarthingData = None, coupler_closed: bool = False) -> dict:
    e = e or EarthingData()
    ic = ic_section(e) * (2 if coupler_closed else 1)
    uph = e.un_kv * 1e3 / math.sqrt(3)
    # compensated
    il = ic * (1 + e.detuning)
    i_comp = math.hypot(il - ic, e.ir_par_a + e.loss_pct / 100 * ic)
    y_comp = i_comp / uph
    # low resistance (NER sized for e.ner_a; Ic adds in quadrature)
    i_lr = math.hypot(e.ner_a, ic)
    rn = uph / e.ner_a
    # high-resistance fault sensitivity: neutral displacement ≥ 10 % (compensated, 59N/67N admittance),
    # 51N at 10 % of NER current (low resistance)
    rf_comp = (1 / 0.10 - 1) / y_comp
    rf_lr = uph / (0.10 * e.ner_a) - rn
    res = {"ic_a": ic, "uph_v": uph}
    for k, i_f, t in (("compensated", i_comp, 10.0), ("low_resistance", i_lr, 0.5)):
        epr = e.r_factor * i_f * e.re_ohm
        res[k] = {"if_a": i_f, "clear_s": t, "epr_v": epr, "utp_v": utp(t), "two_utp_v": 2 * utp(t),
                  "ok_simplified": epr <= 2 * utp(t)}
    res["compensated"]["rf_detect_ohm"] = rf_comp
    res["low_resistance"]["rf_detect_ohm"] = rf_lr
    res["low_resistance"]["rn_ohm"] = rn
    res["compensated"]["coil_a"] = il
    return res


def hv_earth_fault_epr(ik1_ka: float = 8.0, r_factor: float = 0.5, re_ohm: float = 0.2, t_s: float = 0.1) -> dict:
    """130 kV earth fault at the campus substation (solidly earthed system, line earth wires return part of
    the current).  Ik1 and r are [ASSUMED] pending DSO data — this case normally governs the earthing design."""
    epr = r_factor * ik1_ka * 1e3 * re_ohm
    return {"ik1_ka": ik1_ka, "epr_v": epr, "utp_v": utp(t_s), "two_utp_v": 2 * utp(t_s), "t_s": t_s,
            "needs_detailed_design": epr > 2 * utp(t_s)}
