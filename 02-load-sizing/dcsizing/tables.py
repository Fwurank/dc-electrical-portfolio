"""Reference tables with provenance.

Flags used in comments / SOURCES:
  [STD]   value as given in the cited standard (transcribed; verify against a licensed copy)
  [ASSUMED] engineering assumption / typical vendor value, NOT a standard table value
"""

# ----------------------------------------------------------------------------- conductors
SIZES_MM2 = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400, 500, 630]

# IEC 60228:2004 Table 2 (class 2 stranded) max DC resistance at 20 °C, ohm/km  [STD]
R20_CU = {1.5: 12.1, 2.5: 7.41, 4: 4.61, 6: 3.08, 10: 1.83, 16: 1.15, 25: 0.727, 35: 0.524, 50: 0.387,
          70: 0.268, 95: 0.193, 120: 0.153, 150: 0.124, 185: 0.0991, 240: 0.0754, 300: 0.0601,
          400: 0.0470, 500: 0.0366, 630: 0.0283}
R20_AL = {16: 1.91, 25: 1.20, 35: 0.868, 50: 0.641, 70: 0.443, 95: 0.320, 120: 0.253, 150: 0.206,
          185: 0.164, 240: 0.125, 300: 0.100, 400: 0.0778, 500: 0.0605, 630: 0.0469}
ALPHA20 = {"Cu": 0.00393, "Al": 0.00403}           # temperature coefficient 1/K [STD, IEC 60228 Annex B]
# Reactance per conductor for LV cables, ohm/km. IEC 60364-5-52 Annex G suggests 0.08 mOhm/m
# when no other information is available.                                   [STD, Annex G note]
X_CABLE_OHM_PER_KM = 0.08

# IEC 60364-5-52:2009 Table B.52.12 — XLPE/EPR insulation, 90 °C conductor, 30 °C ambient air,
# three loaded conductors. Current-carrying capacity in A.                    [STD, transcribed]
#  "F_trefoil": reference method F, single-core cables in trefoil, free air / perforated tray
#  "E_multi"  : reference method E, multicore cable, free air / perforated tray
IZ_B52_12 = {
    ("Cu", "F_trefoil"): {25: 141, 35: 176, 50: 216, 70: 279, 95: 342, 120: 400, 150: 464, 185: 533,
                          240: 634, 300: 736, 400: 868, 500: 998, 630: 1151},
    ("Al", "F_trefoil"): {25: 107, 35: 135, 50: 165, 70: 215, 95: 264, 120: 308, 150: 358, 185: 413,
                          240: 492, 300: 571, 400: 694, 500: 806, 630: 942},
    ("Cu", "E_multi"): {1.5: 23, 2.5: 32, 4: 42, 6: 54, 10: 75, 16: 100, 25: 127, 35: 158, 50: 192,
                        70: 246, 95: 298, 120: 346, 150: 399, 185: 456, 240: 538, 300: 621},
    ("Al", "E_multi"): {16: 79, 25: 98, 35: 122, 50: 149, 70: 192, 95: 235, 120: 273, 150: 316,
                        185: 363, 240: 430, 300: 497},
}
# IEC 60364-5-52 Table B.52.5 — XLPE, method C (clipped direct), 3 loaded conductors, Cu  [STD, transcribed]
IZ_B52_5_C_CU = {1.5: 24, 2.5: 33, 4: 45, 6: 58, 10: 80, 16: 107, 25: 138, 35: 171, 50: 209, 70: 269,
                 95: 328, 120: 382, 150: 441, 185: 506, 240: 599, 300: 693}
IZ_TABLES = dict(IZ_B52_12)
IZ_TABLES[("Cu", "C_multi")] = IZ_B52_5_C_CU

# IEC 60364-5-52 Table B.52.14 — ambient air temperature correction, XLPE/EPR  [STD]
K_AMBIENT_AIR_XLPE = {10: 1.15, 15: 1.12, 20: 1.08, 25: 1.04, 30: 1.00, 35: 0.96, 40: 0.91, 45: 0.87,
                      50: 0.82, 55: 0.76, 60: 0.71, 65: 0.65, 70: 0.58}

# IEC 60364-5-52 Table B.52.17 — grouping, item 4: single layer on perforated tray (multicore) [STD]
K_GROUP_TRAY_MULTI = {1: 1.00, 2: 0.88, 3: 0.82, 4: 0.77, 5: 0.75, 6: 0.73, 7: 0.73, 8: 0.72, 9: 0.72}
# IEC 60364-5-52 Table B.52.21 — single-core cables, trefoil, perforated tray, 1 tray, circuits
# touching (simplified to one tray; values beyond 3 circuits extrapolated)  [STD 1–3; ASSUMED ≥4]
K_GROUP_TRAY_TREFOIL = {1: 0.98, 2: 0.96, 3: 0.94, 4: 0.91, 5: 0.89, 6: 0.87, 7: 0.85, 8: 0.83,
                        9: 0.81, 10: 0.80, 12: 0.78}

# IEC 60364-4-43 Table 43A — k for conductor short-circuit withstand (A·s^0.5/mm²)  [STD]
K_SC = {("Cu", "XLPE"): 143, ("Al", "XLPE"): 94, ("Cu", "PVC"): 115, ("Al", "PVC"): 76}

# Voltage drop limits. IEC 60364-5-52 Annex G Table G.52.1: installations supplied from private LV
# supply: 6 % lighting / 8 % other uses (from origin).                         [STD]
# Project design limits (tighter, ASSUMED): 1 % transformer→MSB, 2 % sub-main, 3 % final circuit.
VD_LIMIT_PROJECT = {"main": 1.0, "submain": 2.0, "final": 3.0}

STD_PROTECTIVE_DEVICE_A = [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630,
                           800, 1000, 1250, 1600, 2000, 2500, 3200, 4000, 5000, 6300]

# ----------------------------------------------------------------------------- transformers
# IEC 60076 preferred ratings (R10 series), kVA
STD_TX_KVA = [500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000]
# Dry-type (cast resin) 24 kV losses (P0 no-load, Pk load at 120 °C), kW.
# [ASSUMED] typical values in the order of EU Ecodesign Reg. 548/2014 / 2019/1783 Tier 2 maxima.
DRY_TX_LOSSES_KW = {500: (0.9, 5.5), 630: (1.1, 6.5), 800: (1.3, 8.0), 1000: (1.55, 9.0),
                    1250: (1.8, 11.0), 1600: (2.2, 13.0), 2000: (2.6, 16.0), 2500: (3.1, 19.0),
                    3150: (3.8, 22.0), 4000: (4.6, 27.0)}
# 63 MVA 130/21 kV ONAF oil transformer, P0 / Pk at rated power, kW  [ASSUMED]
HV_TX_LOSSES_KW = {63000: (32.0, 250.0), 40000: (24.0, 180.0), 80000: (38.0, 300.0)}

# ----------------------------------------------------------------------------- generators
# Common diesel genset ratings at 400 V, kVA (pf 0.8 → kWe = 0.8 kVA)  [ASSUMED, market-typical]
STD_GEN_KVA = [800, 1000, 1250, 1400, 1650, 2000, 2250, 2500, 2750, 3000, 3125, 3350]
# Site derating (typical manufacturer curves, relative to 40 °C / 1000 m site rating)  [ASSUMED]
GEN_DERATE = {"t_ref_c": 40.0, "pct_per_k": 1.5, "alt_ref_m": 1000.0, "pct_per_100m": 1.0}
# HVO100 specific fuel consumption, litre/kWh vs load fraction. Diesel ≈ 0.245 l/kWh at full load
# scaled by volumetric energy ratio HVO/EN 590 ≈ 1.05.                         [ASSUMED]
SFC_HVO_L_PER_KWH = {0.25: 0.33, 0.50: 0.285, 0.75: 0.265, 1.00: 0.26}
# ISO 8528-5 performance class G3 transient voltage deviation limit (approx. reading)  [ASSUMED]
G3_DU_DYN_MAX = 0.15
# Max single load step as fraction of kWe for high-BMEP (≈ 25 bar) engines, cf. ISO 8528-5 Fig. 6
GEN_MAX_STEP_FRAC = 0.33                                                        # [ASSUMED]

# ----------------------------------------------------------------------------- UPS / batteries
# Modular double-conversion UPS efficiency (VFI mode, IEC 62040-3 Annex I test), vs load fraction [ASSUMED]
UPS_EFF_CURVE = {0.10: 0.90, 0.25: 0.955, 0.50: 0.965, 0.75: 0.966, 1.00: 0.963}
UPS_MODULE_KW = [250, 500, 600, 800, 1000, 1250]
# LFP capacity vs. cell temperature (relative to 25 °C)  [ASSUMED, typical datasheet]
LFP_TEMP_FACTOR = {0: 0.85, 10: 0.92, 15: 0.95, 20: 0.98, 25: 1.00, 30: 1.00, 35: 1.00}
LFP_DEFAULTS = {"eol": 0.80,        # end-of-life capacity (fraction of nameplate)   [ASSUMED]
                "dod": 0.90,        # usable depth of discharge                       [ASSUMED]
                "eta_dc": 0.97,     # inverter DC→AC efficiency incl. DC path        [ASSUMED]
                "c_max": 8.0}       # max discharge C-rate (P_dc / E_eol), high-rate UPS LFP [ASSUMED]

# ----------------------------------------------------------------------------- busway
STD_BUSWAY_A = [630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000, 5000]
# IEC 61439-6: rated current at 35 °C 24-h average ambient. Derating above that [ASSUMED vendor-typical]
BUSWAY_K_AMB = {35: 1.00, 40: 0.95, 45: 0.90, 50: 0.85}
# Cu busway impedance per phase, mOhm/m (R at operating temp, X)  [ASSUMED vendor-typical]
BUSWAY_Z = {630: (0.100, 0.030), 800: (0.075, 0.025), 1000: (0.060, 0.020), 1250: (0.048, 0.018),
            1600: (0.035, 0.015), 2000: (0.028, 0.012), 2500: (0.022, 0.010), 3200: (0.017, 0.008),
            4000: (0.013, 0.007), 5000: (0.010, 0.006)}
# Rated short-time withstand Icw (1 s), kA  [ASSUMED vendor-typical]
BUSWAY_ICW_KA = {630: 36, 800: 36, 1000: 50, 1250: 50, 1600: 65, 2000: 65, 2500: 80, 3200: 85,
                 4000: 100, 5000: 100}

# ----------------------------------------------------------------------------- climate
# Annual hour bins of outdoor dry-bulb temperature for the fictional Dalarna site (bin centre °C, hours)
# [ASSUMED, shaped after public SMHI climate normals for central Sweden; sums to 8760 h]
CLIMATE_BINS_DALARNA = [(-25, 150), (-15, 600), (-5, 2000), (5, 2900), (15, 2300), (22.5, 550),
                        (27.5, 200), (32, 60)]

SOURCES = {
    "IEC 60364-5-52:2009": "Tables B.52.5, B.52.12 (current-carrying capacity), B.52.14 (ambient), "
                           "B.52.17/B.52.21 (grouping), Annex G (voltage drop)",
    "IEC 60364-4-43:2008": "433.1 overload coordination Ib ≤ In ≤ Iz, I2 ≤ 1.45 Iz; 434.5.2 & Table 43A (k)",
    "IEC 60228:2004": "Table 2 conductor resistance",
    "IEC 60909-0:2016": "equivalent voltage source, c-factors (Table 1), KT transformer correction",
    "IEC 60076-1/-11": "transformer ratings, dry-type",
    "IEC 62040-3:2021": "UPS classification VFI-SS-111, stored-energy time, efficiency",
    "ISO 8528-1/-5": "genset ratings (DCC), transient performance class G3",
    "IEC 61439-6": "busbar trunking systems",
}
