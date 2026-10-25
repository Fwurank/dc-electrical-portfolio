"""(e) Business case: CAPEX, yearly cash flows with degradation/augmentation, NPV/IRR/payback, tornado, sizing grid."""
from dataclasses import replace

import numpy as np
from scipy.optimize import brentq

from .assumptions import Bess, Prices, Finance, Site
from . import dispatch as D
from . import profiles as P

CAP_KEYS = ("fcrn", "fcrd_up", "fcrd_dn", "mfrr_up")


def capex_eur(p_mw, e_mwh, f: Finance = None):
    f = f or Finance()
    return (f.c_energy_eur_kwh * e_mwh * 1e3 + f.c_power_eur_kw * p_mw * 1e3) * (1 + f.bop_frac) + f.bay_eur


def market_year(p_mw, e_mwh, pr: Prices = None, b: Bess = None, site: Site = None, extra_it_mw=0.0,
                grid_limited=True):
    """Solve the co-optimisation LP at SOH 1.0 and 0.8 → revenue components (EUR/yr, availability applied)."""
    pr, b, site = pr or Prices(), b or Bess(), site or Site()
    L0, per = P.campus_load(site)
    load = L0 + extra_it_mw * per
    spot, cap = P.spot_price(pr), P.capacity_prices(pr)
    out = {}
    for soh in (1.0, 0.8):
        r = D.co_optimise(load, site.grid_limit_mw, spot, cap, b, e_mwh=e_mwh * soh, p_mw=p_mw,
                          grid_limited=grid_limited, energy_fee=pr.grid_energy_fee, fcrn_act=pr.fcrn_act_share)
        out[soh] = {"rev": r.revenue, "efc": r.efc, "res": r, "overshoot_mw": r.overshoot_mw}
    return out


def _split(rev):
    cap = sum(rev.get(k, 0.0) for k in CAP_KEYS) + rev.get("fcrn_losses", 0.0)
    arb = rev.get("arbitrage", 0.0)
    return cap, arb          # the LP 'degradation' shadow cost is replaced by explicit fade/augmentation


def subscription_value(p_mw, e_mwh, pr: Prices = None, b: Bess = None, site: Site = None, extra_it_mw=0.0,
                       overshoot_mw=0.0):
    """Avoided increase of subscribed capacity: peak above the limit that the BESS shaves (EUR/yr)."""
    pr, site = pr or Prices(), site or Site()
    L0, per = P.campus_load(site)
    shaved = max(0.0, float(np.max(L0 + extra_it_mw * per)) - site.grid_limit_mw - overshoot_mw)
    return shaved, shaved * 1e3 * pr.subscription_sek_kw / pr.sek_per_eur


def cashflows(capex, m, p_mw, e_mwh, f: Finance = None, b: Bess = None, pr: Prices = None, subs_eur=0.0,
              it_eur=0.0, cap_mult=1.0, arb_mult=1.0):
    f, b, pr = f or Finance(), b or Bess(), pr or Prices()
    cap1, arb1 = _split(m[1.0]["rev"])
    cap8, arb8 = _split(m[0.8]["rev"])
    efc = m[1.0]["efc"]
    soh, rows = 1.0, []
    for y in range(1, int(f.life_y) + 1):
        w = np.clip((soh - 0.8) / 0.2, 0, 1)
        trend = (1 + f.price_trend) ** (y - 1)
        cap = (cap8 + w * (cap1 - cap8)) * cap_mult * trend * pr.realisation
        arb = (arb8 + w * (arb1 - arb8)) * arb_mult * pr.realisation
        opex = f.opex_frac * capex
        fade = b.cal_fade + efc / b.cycle_life * 0.2
        soh -= fade
        aug = 0.0
        if soh < f.soh_floor:
            add = 0.9 - soh
            aug = add * e_mwh * 1e3 * f.c_energy_eur_kwh * (1 + f.aug_cost_trend) ** y * (1 + f.bop_frac)
            soh = 0.9
        cf = cap + arb + subs_eur + it_eur - opex - aug
        rows.append({"year": y, "capacity": cap, "arbitrage": arb, "subscription": subs_eur, "it_value": it_eur,
                     "opex": -opex, "augmentation": -aug, "cf": cf, "soh_end": soh})
    return rows


def kpis(capex, rows, wacc):
    cfs = np.array([r["cf"] for r in rows])
    yrs = np.arange(1, len(cfs) + 1)
    npv = -capex + float(np.sum(cfs / (1 + wacc) ** yrs))
    f = lambda r: -capex + np.sum(cfs / (1 + r) ** yrs)
    try:
        irr = brentq(f, -0.9, 5.0) if f(-0.9) * f(5.0) < 0 else float("nan")
    except ValueError:
        irr = float("nan")
    cum = -capex + np.cumsum(cfs)
    pb = next((y - 1 + (-(cum[y - 2] if y > 1 else -capex)) / cfs[y - 1] for y in yrs if cum[y - 1] >= 0), float("inf"))
    return {"capex": capex, "npv": npv, "irr": irr, "payback_y": float(pb), "year1_cf": float(cfs[0])}


def case(p_mw=10.0, e_mwh=20.0, pr: Prices = None, f: Finance = None, b: Bess = None, site: Site = None,
         extra_it_mw=0.0, m=None):
    pr, f, b, site = pr or Prices(), f or Finance(), b or Bess(), site or Site()
    m = m or market_year(p_mw, e_mwh, pr, b, site, extra_it_mw)
    cx = capex_eur(p_mw, e_mwh, f)
    shaved, subs = subscription_value(p_mw, e_mwh, pr, b, site, extra_it_mw, m[1.0]["overshoot_mw"])
    rows = cashflows(cx, m, p_mw, e_mwh, f, b, pr, subs, f.it_value_keur_mw * 1e3 * extra_it_mw)
    return {"m": m, "rows": rows, "kpi": kpis(cx, rows, f.wacc), "shaved_mw": shaved, "subs_eur": subs}


TORNADO = [   # (label, kind, low, high)
    ("Capacity prices ±50 %", "cap_mult", 0.5, 1.5),
    ("Arbitrage spread ±50 %", "arb_mult", 0.5, 1.5),
    ("CAPEX ±30 %", "capex_mult", 1.3, 0.7),
    ("WACC 10 % / 5 %", "wacc", 0.10, 0.05),
    ("Price trend −10 %/yr / 0", "price_trend", -0.10, 0.0),
    ("Realisation 0.70 / 1.00", "realisation", 0.70, 1.00),
    ("Cycle life 4 000 / 8 000 EFC", "cycle_life", 4000, 8000),
]


def tornado(base, p_mw=10.0, e_mwh=20.0, pr: Prices = None, f: Finance = None, b: Bess = None):
    pr, f, b = pr or Prices(), f or Finance(), b or Bess()
    m = base["m"]
    cx0 = capex_eur(p_mw, e_mwh, f)
    out = []
    for label, kind, lo, hi in TORNADO:
        vals = []
        for v in (lo, hi):
            ff, bb, pp, cx, cm, am = f, b, pr, cx0, 1.0, 1.0
            if kind == "cap_mult":
                cm = v
            elif kind == "arb_mult":
                am = v
            elif kind == "capex_mult":
                cx = cx0 * v
            elif kind in ("wacc", "price_trend"):
                ff = replace(f, **{kind: v})
            elif kind == "realisation":
                pp = replace(pr, realisation=v)
            elif kind == "cycle_life":
                bb = replace(b, cycle_life=v)
            rows = cashflows(cx, m, p_mw, e_mwh, ff, bb, pp, base["subs_eur"], 0.0, cm, am)
            vals.append(kpis(cx, rows, ff.wacc)["npv"])
        out.append({"label": label, "low": vals[0], "high": vals[1]})
    return sorted(out, key=lambda r: abs(r["high"] - r["low"]))


def sizing_grid(powers=(5, 10, 15, 20), durations=(1, 2, 3, 4), pr: Prices = None, f: Finance = None,
                b: Bess = None, site: Site = None):
    pr, f, b, site = pr or Prices(), f or Finance(), b or Bess(), site or Site()
    L0, per = P.campus_load(site)
    out = []
    for p in powers:
        for h in durations:
            e = p * h
            c = case(p, e, pr, f, b, site)
            x = D.max_extra_it(L0, per, site.grid_limit_mw, b, e_mwh=e, p_mw=p)["x_mw"]
            out.append({"p_mw": p, "h": h, "e_mwh": e, "capex_meur": c["kpi"]["capex"] / 1e6,
                        "npv_meur": c["kpi"]["npv"] / 1e6, "irr": c["kpi"]["irr"], "payback_y": c["kpi"]["payback_y"],
                        "year1_meur": c["kpi"]["year1_cf"] / 1e6, "extra_it_mw": x,
                        "efc": c["m"][1.0]["efc"], "overshoot_mw": c["m"][1.0]["overshoot_mw"]})
    return out


def it_breakeven(base_no_it, x_mw, f: Finance = None):
    """k€/MW-IT·yr of enabled IT value that would add 1 M€ NPV (annuity) — shows how strongly IT value dominates."""
    f = f or Finance()
    ann = (1 - (1 + f.wacc) ** -f.life_y) / f.wacc
    return {"annuity_factor": ann, "npv_per_keur_mw": x_mw * 1e3 * ann / 1e6}
