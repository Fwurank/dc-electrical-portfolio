"""Runs parts (a)–(e) and returns one dict for scripts/make_all.py, the app and the report."""
from dataclasses import replace

import numpy as np

from .assumptions import Site, Bess, Prices, Finance, AiSwing, PRICE_TABLE
from . import profiles as P, dispatch as D, backup as B, ai_swing as AI, business as Bz


def peak_shaving(site: Site = None, b: Bess = None):
    site, b = site or Site(), b or Bess()
    L0, per = P.campus_load(site)
    Lnr, _ = P.campus_load(site, recharge=False)
    lim = site.grid_limit_mw
    no = D.max_extra_it(L0, per, lim, b, 0, 0)["x_mw"]
    no_nr = D.max_extra_it(Lnr, per, lim, b, 0, 0)["x_mw"]
    full = D.max_extra_it(L0, per, lim, b)
    firm = D.max_extra_it(L0, per, lim, b, p_mw=b.p_mw / 2, e_mwh=b.e_mwh / 2)["x_mw"]   # one 5 MW unit out
    e_sweep = [{"e_mwh": e, "x_mw": D.max_extra_it(L0, per, lim, b, p_mw=b.p_mw, e_mwh=e)["x_mw"]}
               for e in (2.5, 5, 10, 20, 30, 40, 60, 80)]
    p_sweep = [{"p_mw": p, "x_mw": D.max_extra_it(L0, per, lim, b, p_mw=p, e_mwh=b.e_mwh)["x_mw"]}
               for p in (1, 2, 3, 5, 10, 20)]
    Lx = L0 + full["x_mw"] * per
    over = Lx > lim
    # longest continuous run above the limit (h) and energy shaved
    runs, cur = [], 0
    for o in over:
        cur = cur + 1 if o else 0
        runs.append(cur)
    return {"load": L0, "per": per, "x_no_bess": no, "x_no_bess_no_recharge": no_nr, "x_bess": full["x_mw"],
            "x_firm": firm, "dispatch": full, "e_sweep": e_sweep, "p_sweep": p_sweep,
            "hours_over": int(over.sum()), "longest_run_h": int(max(runs)), "e_shaved_mwh": float(np.sum(np.clip(Lx - lim, 0, None))),
            "peak_mw": float(L0.max()), "peak_no_recharge_mw": float(Lnr.max()), "mean_mw": float(L0.mean()),
            "energy_gwh": float(L0.sum() / 1e3), "temp": P.temperature(site)}


def revenue(site: Site = None, b: Bess = None, x_mw=0.0, x_firm=0.0):
    site, b = site or Site(), b or Bess()
    L0, per = P.campus_load(site)
    out = {"scenarios": {}, "compat": {}}
    for sc in PRICE_TABLE:
        pr = Prices(scenario=sc)
        r = D.co_optimise(L0, site.grid_limit_mw, P.spot_price(pr), P.capacity_prices(pr), b,
                          energy_fee=pr.grid_energy_fee, fcrn_act=pr.fcrn_act_share)
        out["scenarios"][sc] = {"rev": r.revenue, "total": r.total, "efc": r.efc,
                                "avg_mw": {k: float(v.mean()) for k, v in r.reserves.items()}}
        if sc == "2026":
            out["dispatch_2026"] = r
    pr = Prices()
    spot, cap = P.spot_price(pr), P.capacity_prices(pr)
    for label, x, gl in [("No grid limit (stand-alone)", 0.0, False), ("40 MW limit, no extra IT", 0.0, True),
                         ("40 MW limit + firm extra IT (N-1 BESS)", x_firm, True), ("40 MW limit + max extra IT", x_mw, True)]:
        r = D.co_optimise(L0 + x * per, site.grid_limit_mw, spot, cap, b, grid_limited=gl,
                          energy_fee=pr.grid_energy_fee, fcrn_act=pr.fcrn_act_share)
        out["compat"][label] = {"x_mw": x, "total": r.total, "rev": r.revenue}
    return out


def ai(a: AiSwing = None):
    a = a or AiSwing()
    t, L = AI.ai_profile(a)
    base = AI.smooth(L, a)
    th, Lh, hy, mh = AI.hybrid(a)
    return {"t": t, "load": L, "base": base, "m_base": AI.metrics(t, L, base, a), "hybrid": hy, "m_hybrid": mh,
            "ramp_sweep": AI.sweep_ramp(a), "resp_sweep": AI.sweep_response(a),
            "spec_load": AI.spectrum(L, a.dt_s), "spec_grid": AI.spectrum(base["p_grid"], a.dt_s),
            "spec_hybrid": AI.spectrum(hy["p_grid"], a.dt_s)}


def business(x_mw=0.0, grid=True):
    base = Bz.case()
    out = {"base": base, "tornado": Bz.tornado(base),
           "scenarios": {sc: Bz.case(pr=Prices(scenario=sc))["kpi"] for sc in PRICE_TABLE},
           "it": Bz.it_breakeven(base, x_mw)}
    if grid:
        out["grid"] = Bz.sizing_grid()
    return out


def run(grid=True):
    ps = peak_shaving()
    return {"peak": ps, "backup": {"autonomy": B.autonomy(), "replace_all": B.replace_all_gensets(mean_load_mw=ps["mean_mw"]),
                                   "fail_to_start": B.fail_to_start_cover(), "island": B.island_fault_check()},
            "revenue": revenue(x_mw=ps["x_bess"], x_firm=ps["x_firm"]), "ai": ai(), "business": business(ps["x_bess"], grid)}
