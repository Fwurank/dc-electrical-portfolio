"""All inputs of the BESS study in one place, each tagged with its source.

tag = "PUBLIC" -> taken from the cited public source (accessed 2026-10-24)
tag = "ASSUMED" -> plausible engineering/market assumption, to be confirmed
tag = "PROJECT" -> taken from projects 01–03 of this portfolio
"""
from dataclasses import dataclass, field, asdict, fields

ACCESSED = "2026-10-24"

SOURCES = {
    "SVK-FCR-LER": ("Svenska kraftnät, 'What is the minimum duration that FCR should be delivered' (Q&A, reviewed 2025-08-18)",
                    "https://www.svk.se/en/stakeholders-portal/electricity-market/provision-of-ancillary-services/"
                    "questions-and-answers-about-reserves/fcr/what-is-the-minimum-duration-that-fcr-should-be-delivered.../"),
    "SVK-FCR-2025": ("Svenska kraftnät, Månadsrapport FCR – december 2025 (incl. full-year 2025 summary, Mimer data)",
                     "https://www.svk.se/49032d/siteassets/aktorsportalen/bidra-med-reserver/handel-och-prissattning/"
                     "marknadsanalys-balanstjanster/manadsrapport-fcr-december-2025.pdf"),
    "SVK-BMO-2030": ("Svenska kraftnät, Balancing market outlook 2030 (2026 update)",
                     "https://www.svk.se/49db02/siteassets/aktorsportalen/bidra-med-reserver/behov-av-reserver-idag/"
                     "framtidsrapport-om-balansmarknaderna/balancing-market-outlook-2030-2026-update.pdf"),
    "FLEX-WIKI": ("Flexnavet wiki, 'Nordic battery revenue trends 2023–2026' — annual means of Svk Mimer reserve prices "
                  "(2026 = Jan–Aug); secondary source", "https://flexnavet.se/wiki/nordic-battery-revenue-trends-2023-2026/"),
    "NP-DA": ("Nord Pool, day-ahead prices, yearly aggregate SE3 (2025 = 46.23 EUR/MWh; 2026 YTD = 70.70 EUR/MWh)",
              "https://data.nordpoolgroup.com/auction/day-ahead/prices?aggregation=YearlyAggregate&currency=EUR&deliveryAreas=SE3"),
    "VEL-RN-2026": ("Vattenfall Eldistribution, Prisblad regionnät 2026 (Södra Sverige, tariff L1: årseffektavgift 207 SEK/kW, "
                    "högbelastningsavgift 35 SEK/kW, överföring 1.7 öre/kWh)",
                    "https://www.vattenfalleldistribution.se/globalassets/2.-foretag/abonnemang-och-avgifter/avtal-och-elnatsavgift/"
                    "avgifter-och-bestammelser-for-regionnatet/prisblad-rn-2026.pdf"),
    "BNEF-2025": ("BNEF Energy Storage System Cost Survey 2025 as reported by Energy-Storage.News 2025-12-16 "
                  "(turnkey Europe 177 USD/kWh, global 117 USD/kWh)",
                  "https://www.energy-storage.news/battery-storage-system-prices-continue-to-fall-sharply-bnef-and-ember-reports-find/"),
    "NERC-LL": ("NERC, White Paper: Characteristics and Risks of Emerging Large Loads (2025)",
                "https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/whitepaper-characteristics-and-risks-of-emerging-large-loads.pdf"),
    "DB-001": ("DWU-DC-E-DB-001 Design Basis Rev P1 (project 01): 40 MW subscription, 20 kV BESS bay 10 MW / 20 MWh", "../01-design-basis-sld"),
    "CALC-002": ("DWU-DC-E-CALC-002 (project 02, dcsizing): design peak 37.8 MW, 42.6 MW incl. UPS recharge", "../02-load-sizing"),
    "CALC-003": ("DWU-DC-E-CALC-003 (project 03, scprot): MSG-20 13.0 kA, relay settings", "../03-shortcircuit-protection"),
}


def A(value, tag, note, src=None):
    """dataclass field carrying provenance metadata."""
    return field(default=value, metadata={"tag": tag, "note": note, "src": src})


@dataclass
class Site:
    grid_limit_mw: float = A(40.0, "PROJECT", "Subscribed import capacity (abonnerad effekt)", "DB-001")
    it_nameplate_mw: float = A(30.0, "PROJECT", "IT nameplate, 6 halls × 5 MW", "DB-001")
    design_peak_mw: float = A(37.818, "PROJECT", "Campus demand at 100 % IT, +32 °C (dcsizing)", "CALC-002")
    recharge_mw: float = A(4.8, "PROJECT", "UPS battery recharge allowance 10 % of 48 MW UPS (non-coincident)", "CALC-002")
    recharge_h: float = A(1.5, "ASSUMED", "Recharge at full rate after a full discharge, then 1 h taper")
    u_mean: float = A(0.80, "ASSUMED", "Design-year mean IT utilisation (AI-heavy, > DB 75 %)")
    u_diurnal: float = A(0.06, "ASSUMED", "Diurnal utilisation amplitude (peak 14–20 h)")
    u_noise: float = A(0.02, "ASSUMED", "Hourly AR(1) utilisation noise σ")
    heatwave_c: float = A(32.0, "PROJECT", "Extreme design ambient (heat-wave peak, 5 days in July)", "DB-001")
    seed: int = A(2026, "ASSUMED", "Random seed of all synthetic profiles")


@dataclass
class Bess:
    p_mw: float = A(10.0, "PROJECT", "PCS power at the 20 kV bay(s), 2 × 5 MW (one per MSG-20 section)", "DB-001")
    e_mwh: float = A(20.0, "PROJECT", "Nameplate energy at BoL (2 h); usable = SOC window × nameplate", "DB-001")
    soc_min: float = A(0.05, "ASSUMED", "Usable SOC window lower bound (of nameplate)")
    soc_max: float = A(0.95, "ASSUMED", "Usable SOC window upper bound")
    eta_rt: float = A(0.88, "ASSUMED", "AC round-trip efficiency incl. PCS + MV transformer (LFP)")
    availability: float = A(0.97, "ASSUMED", "Commercial availability")
    cal_fade: float = A(0.010, "ASSUMED", "Calendar fade per year (LFP, ~25 °C)")
    cycle_life: float = A(6000.0, "ASSUMED", "Equivalent full cycles to 80 % SOH")
    deg_cost_eur_mwh: float = A(15.0, "ASSUMED", "Throughput degradation cost (DC block cost / cycle life)")
    response_ms: float = A(150.0, "ASSUMED", "PCS full-power step response (grid-following); 20–50 ms grid-forming")
    fault_pu: float = A(1.2, "ASSUMED", "PCS fault-current limit (per unit of rated current)")
    s_mva: float = A(11.0, "ASSUMED", "PCS apparent power (Q for p.f. ≥ 0.95 at the connection point)")


@dataclass
class Prices:
    """Capacity prices in EUR/MW per hour (Svk Mimer annual means), energy in EUR/MWh."""
    scenario: str = A("2026", "PUBLIC", "Price year: '2025', '2026' (Jan–Aug) or 'saturated' (0.5 × 2026, ASSUMED)", "FLEX-WIKI")
    spot_mean: float = A(46.23, "PUBLIC", "SE3 day-ahead annual mean 2025, EUR/MWh (synthetic hourly shape around it)", "NP-DA")
    spot_daily_spread: float = A(0.25, "ASSUMED", "Synthetic diurnal price amplitude (fraction of mean)")
    neg_share: float = A(0.04, "ASSUMED", "Share of hours ≤ 0 EUR/MWh (≈ 3.9 % SE3 2025 per worldpowermonitor)")
    grid_energy_fee: float = A(1.5, "PUBLIC", "Regional-grid transfer fee ≈ 1.7 öre/kWh (L1 Södra) → ≈ 1.5 EUR/MWh", "VEL-RN-2026")
    sek_per_eur: float = A(11.0, "ASSUMED", "Exchange rate SEK/EUR")
    usd_per_eur: float = A(1.13, "ASSUMED", "Exchange rate USD/EUR")
    subscription_sek_kw: float = A(242.0, "PUBLIC", "Årseffektavgift 207 + högbelastning 35 SEK/kW·yr (L1 Södra 2026)", "VEL-RN-2026")
    realisation: float = A(0.85, "ASSUMED", "Perfect-foresight LP → real bidding (forecast error, bid granularity, aggregator fee)")
    fcrn_act_share: float = A(0.10, "ASSUMED", "FCR-N mean activation (|ΔP|/reserved) → throughput losses")


PRICE_TABLE = {   # EUR/MW/h, Svk Mimer annual means (FLEX-WIKI); 'saturated' = 0.5 × 2026 [ASSUMED]
    "2025": {"fcrn": 26.8, "fcrd_up": 6.1, "fcrd_dn": 5.9, "mfrr_up": 40.9},
    "2026": {"fcrn": 22.1, "fcrd_up": 5.6, "fcrd_dn": 3.2, "mfrr_up": 11.3},
    "saturated": {"fcrn": 11.05, "fcrd_up": 2.8, "fcrd_dn": 1.6, "mfrr_up": 5.65},
}
ENDURANCE_H = {"fcrn": 1.0, "fcrd_up": 1 / 3, "fcrd_dn": 1 / 3, "mfrr_up": 1.0}   # SVK-FCR-LER; mFRR 1 h ASSUMED


@dataclass
class Finance:
    c_energy_eur_kwh: float = A(120.0, "ASSUMED", "Energy-related turnkey cost; with c_power gives 157 €/kWh at 2 h ≈ BNEF Europe 2025 177 USD/kWh", "BNEF-2025")
    c_power_eur_kw: float = A(75.0, "ASSUMED", "Power-related turnkey cost (PCS, MV skid)")
    bop_frac: float = A(0.20, "ASSUMED", "Grid connection, civil, fire protection, owner's costs (fraction of turnkey)")
    bay_eur: float = A(300e3, "ASSUMED", "Two 20 kV bay fit-outs incl. protection & metering (bays reserved in DB)")
    opex_frac: float = A(0.02, "ASSUMED", "O&M + insurance + EMS/optimiser fee, fraction of CAPEX per year")
    wacc: float = A(0.07, "ASSUMED", "Nominal WACC")
    life_y: int = A(15, "ASSUMED", "Economic life (years)")
    price_trend: float = A(-0.03, "ASSUMED", "Annual ancillary-price trend (saturation; SVK-BMO-2030 shows decreasing prices)")
    soh_floor: float = A(0.80, "ASSUMED", "Augment energy whenever SOH would fall below this")
    aug_cost_trend: float = A(-0.04, "ASSUMED", "Annual change of cell/augmentation cost")
    it_value_keur_mw: float = A(0.0, "ASSUMED", "Value of enabled IT capacity, k€/MW-IT·yr (0 = conservative base case)")


@dataclass
class AiSwing:
    p_ai_mw: float = A(12.0, "ASSUMED", "AI training cluster at the grid (IT × PUE), synchronous job, ≈ 2 halls")
    p_base_mw: float = A(24.0, "ASSUMED", "Rest of campus (steady)")
    duty_low: float = A(0.35, "ASSUMED", "Communication-phase power (pu of AI peak)")
    period_s: float = A(6.0, "ASSUMED", "Training-iteration period (compute + all-reduce)")
    ckpt_every_s: float = A(900.0, "ASSUMED", "Checkpoint interval")
    ckpt_len_s: float = A(45.0, "ASSUMED", "Checkpoint duration at ~20 % power")
    ramp_mw_min: float = A(3.0, "ASSUMED", "Grid-code-style ramp limit at the connection point (10 % of 30 MW per minute)")
    osc_band_mw: float = A(1.0, "ASSUMED", "Max. residual peak-to-peak swing in 0.1–2 Hz band (≈ 2.5 % of 40 MW; forced-oscillation limit)")
    rise_s: float = A(0.5, "ASSUMED", "Facility-level 10–90 % rise time of AI power steps (many GPUs, PSU/UPS DC links)")
    dt_s: float = A(0.02, "ASSUMED", "Simulation step")
    horizon_s: float = A(3600.0, "ASSUMED", "Simulated window (job start, checkpoints, a crash/restart)")


def register(*objs):
    """Flat assumptions register: [{'group','name','value','tag','note','source'}]."""
    rows = []
    for o in objs:
        for f in fields(o):
            m = f.metadata
            src = m.get("src")
            rows.append({"group": type(o).__name__, "name": f.name, "value": getattr(o, f.name), "tag": m.get("tag", ""),
                         "note": m.get("note", ""), "source": SOURCES[src][0] if src in SOURCES else ""})
    return rows
