"""(b) Backup role of the BESS: what it can and cannot credibly replace.

Quantitative parts: autonomy vs campus load, power coverage, genset-replacement sizing, and the fault-current
limitation of an inverter-fed 20 kV island checked against the CALC-003 relay settings.
"""
import math
import os
import sys
from functools import lru_cache

import numpy as np

from .assumptions import Bess, Site

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "04-shortcircuit-protection"))
from scprot import study as _sc  # noqa: E402

FUEL_AUTONOMY_H = 24.0          # DB-001 §6 (project)
N_GENSETS_IT, N_GENSETS_MECH = 24, 12
GENSET_IT_KWE, GENSET_MECH_KWE = 2200, 1320
GENSET_EUR_KWE = 380.0          # [ASSUMED] installed incl. enclosure, tank share, ATS/ACB share
BESS_LONG_EUR_KWH = 180.0       # [ASSUMED] long-duration (≥ 8 h) installed incl. PCS share


@lru_cache(maxsize=1)
def _sc_study():
    return _sc.run()


def autonomy(b: Bess = None, loads_mw=(5, 10, 20, 30, 37.818)):
    b = b or Bess()
    usable = (b.soc_max - b.soc_min) * b.e_mwh * math.sqrt(b.eta_rt)       # discharge-side usable MWh
    rows = []
    for L in loads_mw:
        rows.append({"load_mw": L, "power_ok": L <= b.p_mw, "minutes": 60 * usable / L if L <= b.p_mw else 60 * usable / L,
                     "share_of_campus_peak": L / 37.818})
    return usable, rows


def replace_all_gensets(site: Site = None, b: Bess = None, mean_load_mw=27.9):
    """Battery that could replace all 36 gensets for the 24 h fuel autonomy (and still not meet Tier III)."""
    site = site or Site()
    b = b or Bess()
    p = site.design_peak_mw + site.recharge_mw
    e = mean_load_mw * FUEL_AUTONOMY_H / ((b.soc_max - b.soc_min) * math.sqrt(b.eta_rt))
    gens_kwe = N_GENSETS_IT * GENSET_IT_KWE + N_GENSETS_MECH * GENSET_MECH_KWE
    return {"p_mw": p, "e_mwh": e, "bess_capex_meur": e * 1e3 * BESS_LONG_EUR_KWH / 1e6,
            "genset_capex_meur": gens_kwe * GENSET_EUR_KWE / 1e6, "genset_mwe": gens_kwe / 1e3,
            "ratio": e * 1e3 * BESS_LONG_EUR_KWH / (gens_kwe * GENSET_EUR_KWE)}


def fail_to_start_cover(b: Bess = None, n_fail=(1, 2, 4, 6), block_mw=2.2 * 0.8):
    """Informational: hours a grid-forming BESS at 20 kV could feed blocks whose genset failed to start
    (their ATS stays on the transformer side, so the energised 20 kV island reaches them)."""
    b = b or Bess()
    usable = (b.soc_max - b.soc_min) * b.e_mwh * math.sqrt(b.eta_rt)
    return [{"n_failed": n, "load_mw": n * block_mw, "power_ok": n * block_mw <= b.p_mw,
             "hours": usable / (n * block_mw)} for n in n_fail]


def island_fault_check(b: Bess = None):
    """Inverter fault current (≈ fault_pu × I_rated, IEC 60909-0:2016 current-source model) in a 20 kV island
    vs the grid-connected CALC-003 settings."""
    b = b or Bess()
    s = _sc_study()
    dv = s["devices"]
    i_mv = b.fault_pu * b.s_mva * 1e6 / (math.sqrt(3) * 20e3)          # A at 20 kV, both PCS together
    i_lv = i_mv * 20 / 0.42                                             # through a block transformer, A at 400 V
    mv = {r["scenario"]: r["ik_ka"] for r in s["sc_table"] if r["node"] == "MV-A"}
    ik_msg_grid = float(mv["S0max"])                  # normal operation (CALC-003 S0max)
    ik_msg_worst = float(max(mv.values()))            # worst abnormal case (CALC-003 S1/S3)
    rows = []
    for key, name, i in [("rfd", "R-FDR hall feeder 20 kV", i_mv), ("rin", "R-INC 20 kV incomer", i_mv),
                         ("rtx", "R-TX block transformer 20 kV", i_mv), ("inc", "MSB incomer ACB (LV)", i_lv),
                         ("bw", "Busway feeder MCCB (LV)", i_lv * 0.6)]:
        dev = dv[key]
        t = float(np.atleast_1d(dev.clear(np.array([i])))[0])
        pick = getattr(dev, "is51", None) or getattr(dev, "ir", None)
        rows.append({"device": name, "i_fault_a": i, "pickup_a": pick, "multiple": i / pick,
                     "t_clear_s": t if np.isfinite(t) else float("inf"),
                     "ok": bool(np.isfinite(t) and t <= 1.0)})
    grid_ik_contrib_ka = i_mv / 1e3
    return {"i_mv_a": i_mv, "i_lv_ka": i_lv / 1e3, "rows": rows, "ik_msg20_grid_ka": ik_msg_grid,
            "ik_msg20_with_bess_ka": ik_msg_grid + grid_ik_contrib_ka,
            "ik_msg20_worst_ka": ik_msg_worst, "ik_msg20_worst_with_bess_ka": ik_msg_worst + grid_ik_contrib_ka,
            "switchgear_ka": 25.0, "grid_contrib_ka": grid_ik_contrib_ka,
            "ratio_to_grid_fault": grid_ik_contrib_ka / ik_msg_grid}


# Qualitative assessment table (concept level) – used by app + report
CAN_CANNOT = [
    ("Replace all 36 gensets (Tier III / EN 50600 Class 3)", "No",
     "Tier III needs on-site engine generation able to carry the design load without runtime limit; a battery "
     "with finite energy is not accepted as the generation source. 24 h autonomy needs ≈ 0.85 GWh of storage."),
    ("Replace the static UPS (ride-through of the grid→genset gap)", "No",
     "BESS sits at 20 kV; the gap occurs at LV behind the ATS (open transition) and inside a ~10 ms window. "
     "UPS also gives per-block redundancy (2N/DR) that one MV BESS cannot."),
    ("Reduce number/rating of gensets (N+1 → N)", "Not recommended",
     "DR topology has no stand-alone redundant genset; derating gensets on the assumption that the BESS covers "
     "peaks fails when the BESS is out of service or depleted (single point of dependency)."),
    ("Cover a genset that fails to start (bridging, grid-forming island)", "Possible (informational)",
     "Grid-forming PCS energises the 20 kV island; blocks whose ATS stays on the transformer side are fed for "
     "hours. Needs islanding scheme, soft energisation, island protection (51V/27/87L) and earthing in island."),
    ("Genset load-step / start support, recharge-peak cover", "Yes",
     "Only when the BESS and gensets share a bus (not in current LV-genset topology) or via the 20 kV island; "
     "grid-connected recharge peaks (42.6 MW > 40 MW) are covered — see (a)."),
    ("Genset testing on load (replace load banks), HVO fuel saving", "Yes",
     "Monthly test runs can be loaded by charging the BESS (if synchronised); fewer dummy-load hours."),
    ("Black start / re-energisation of MSG-20 after grid return", "Possible",
     "Soft energisation of 20 kV transformers limits inrush; closed-transition re-transfer reduces UPS cycling."),
]

GENSET_RATINGS = [
    ("ESP – Emergency standby (ISO 8528-1)", "Variable load, ≤ 200 h/yr typ., avg ≤ 70 % of ESP, no overload",
     "Not sufficient alone for Tier III unless the OEM gives a data-centre rating"),
    ("PRP – Prime", "Unlimited hours, variable load, avg ≤ 70 %, 10 % overload 1 h in 12 h", "Accepted"),
    ("COP – Continuous", "Unlimited hours at constant 100 % load", "Accepted (conservative)"),
    ("DCP – Data-centre power (ISO 8528-1:2018)", "Unlimited hours at varying load with grid as primary",
     "Intended for data centres. DB-001 uses 2 750 kVA / 2 200 kWe DCC (manufacturer's data-centre continuous rating)"),
]

FIRE_SAFETY = [
    ("NFPA 855 (2026 ed.)", "Installation of ESS: size/separation limits, explosion control, detection, "
                            "emergency response plan; outdoor separation ≈ 3 m (10 ft) unless reduced by large-scale fire test data"),
    ("UL 9540 / UL 9540A", "System safety listing / cell-module-unit-installation thermal-runaway propagation test"),
    ("IEC 62933-5-2", "Safety requirements for grid-integrated electrochemical EES systems"),
    ("EN IEC 62485-5", "Safety for stationary Li-ion batteries (installation, ventilation, separation)"),
    ("IEC 62619 / IEC 63056", "Cell and battery safety for industrial Li-ion applications"),
    ("NFPA 68 / NFPA 69", "Deflagration venting / explosion prevention (gas detection + exhaust)"),
    ("Swedish context", "LSO (Lag om skydd mot olyckor), BBR (Boverket) fire separation, MSB guidance on "
                        "battery storage, rescue-service consultation; insurer rules (e.g. FM DS 5-33)"),
]

FIRE_DESIGN = [
    "Outdoor containerised LFP units, ≥ 10 m from data halls, 130/20 kV transformers and fuel tanks [ASSUMED project choice]",
    "Per-container gas (H₂/CO) detection, deflagration vents or NFPA 69 exhaust, no walk-in during thermal event",
    "Water supply for defensive cooling of neighbours, no in-container extinguishing reliance",
    "Fire-rated cable routes and separate 20 kV bays/sections so a BESS fire cannot take out both MSG-20 sections",
    "UL 9540A data for the selected product to justify separation; emergency response plan with Räddningstjänst",
]
