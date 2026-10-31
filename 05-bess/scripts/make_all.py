"""Run the full study → figures/*.png and results/*.csv/json (used by the report and, as cache, the app)."""
import csv
import json
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bessdc import study, assumptions as A, backup as B, ai_swing as AI, business as Bz  # noqa: E402

FIG, RES = os.path.join(ROOT, "figures"), os.path.join(ROOT, "results")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 150})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=160)
    plt.close(fig)


def write_csv(name, rows):
    with open(os.path.join(RES, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def fig_peak(S):
    ps = S["peak"]
    L, per, d = ps["load"], ps["per"], ps["dispatch"]
    x = ps["x_bess"]
    h0, h1 = 194 * 24, 202 * 24
    hh = np.arange(h0, h1) / 24
    fig, ax = plt.subplots(3, 1, figsize=(8, 6.2), sharex=True, gridspec_kw={"height_ratios": [2.2, 1, 1]})
    ax[0].plot(hh, L[h0:h1], color="0.6", lw=1, label="Campus load, design IT (30 MW)")
    ax[0].plot(hh, (L + x * per)[h0:h1], color="C3", lw=1.2, label=f"+ {x:.1f} MW extra IT (no BESS)")
    ax[0].plot(hh, d["grid"][h0:h1], color="C0", lw=1.5, label="Grid import with BESS")
    ax[0].axhline(40, color="k", ls="--", lw=1, label="Subscribed limit 40 MW")
    ax[0].set_ylabel("MW")
    ax[0].legend(fontsize=7, loc="lower left", ncol=2)
    ax[0].set_title("(a) Design heat-wave week (15–19 Jul) with UPS recharge after an outage, LP dispatch")
    ax[1].bar(hh, (d["d"] - d["c"])[h0:h1], width=1 / 24, color=np.where((d["d"] - d["c"])[h0:h1] > 0, "C2", "C1"))
    ax[1].set_ylabel("BESS MW\n(+ dis.)")
    ax[2].plot(hh, d["e"][h0:h1], color="C4")
    ax[2].set_ylabel("Energy MWh")
    ax[2].set_xlabel("Day of year")
    t2 = ax[0].twinx()
    t2.plot(hh, ps["temp"][h0:h1], color="C1", lw=0.6, alpha=0.5)
    t2.set_ylabel("Ambient °C", color="C1")
    t2.grid(False)
    save(fig, "fig_peak_week.png")


def fig_extra(S):
    ps = S["peak"]
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    e = [r["e_mwh"] for r in ps["e_sweep"]]
    ax[0].plot(e, [r["x_mw"] for r in ps["e_sweep"]], "o-", label="BESS 10 MW, energy varied")
    ax[0].axhline(ps["x_no_bess"], color="C3", ls="--", label="No BESS (with recharge peak)")
    ax[0].axhline(ps["x_no_bess_no_recharge"], color="0.5", ls=":", label="No BESS, recharge limited")
    ax[0].axvline(20, color="k", lw=0.6)
    ax[0].set_xlabel("BESS energy MWh")
    ax[0].set_ylabel("Extra IT nameplate MW")
    ax[0].legend(fontsize=7)
    p = [r["p_mw"] for r in ps["p_sweep"]]
    ax[1].plot(p, [r["x_mw"] for r in ps["p_sweep"]], "s-", color="C2", label="BESS 20 MWh, power varied")
    ax[1].axhline(ps["x_no_bess"], color="C3", ls="--")
    ax[1].set_xlabel("BESS power MW")
    ax[1].legend(fontsize=7)
    fig.suptitle("Extra IT that fits under 40 MW (hourly LP, perfect foresight)", fontsize=9)
    save(fig, "fig_extra_it.png")


def fig_revenue(S):
    rv = S["revenue"]
    keys = ["fcrn", "fcrd_up", "fcrd_dn", "mfrr_up", "arbitrage"]
    lab = {"fcrn": "FCR-N", "fcrd_up": "FCR-D up", "fcrd_dn": "FCR-D down", "mfrr_up": "mFRR CM up", "arbitrage": "Arbitrage (BTM)"}
    fig, ax = plt.subplots(1, 2, figsize=(8, 3), gridspec_kw={"width_ratios": [1.3, 1]})
    sc = list(rv["scenarios"])
    bottom = np.zeros(len(sc))
    for k in keys:
        v = np.array([rv["scenarios"][s]["rev"][k] / 1e6 for s in sc])
        ax[0].bar(sc, v, bottom=bottom, label=lab[k])
        bottom += v
    neg = np.array([(rv["scenarios"][s]["rev"]["degradation"] + rv["scenarios"][s]["rev"]["fcrn_losses"]) / 1e6 for s in sc])
    ax[0].bar(sc, neg, color="0.5", label="Degradation + losses")
    for i, s in enumerate(sc):
        ax[0].text(i, bottom[i] + 0.05, f"{rv['scenarios'][s]['total']/1e6:.2f} M€", ha="center", fontsize=7)
    ax[0].set_ylabel("M€/yr (10 MW / 20 MWh, avail. 97 %)")
    ax[0].legend(fontsize=6.5, ncol=1, loc="upper right")
    ax[0].set_ylim(top=max(bottom) * 1.12)
    ax[0].set_title("(c) Revenue stack by price scenario (LP)", fontsize=9)
    cp = rv["compat"]
    names = list(cp)
    ax[1].barh(range(len(names)), [cp[n]["total"] / 1e6 for n in names], color="C0")
    ax[1].set_yticks(range(len(names)))
    ax[1].set_yticklabels([n.replace(" (", "\n(") for n in names], fontsize=6.5)
    ax[1].set_xlim(min(cp[n]["total"] for n in names) / 1e6 * 0.95, max(cp[n]["total"] for n in names) / 1e6 * 1.01)
    for i, n in enumerate(names):
        ax[1].text(cp[n]["total"] / 1e6, i, f" {cp[n]['total']/1e6:.3f}", va="center", fontsize=7)
    ax[1].set_xlabel("M€/yr (2026 prices)")
    ax[1].set_title("Compatibility with peak shaving", fontsize=9)
    save(fig, "fig_revenue.png")


def fig_ai(S):
    a = S["ai"]
    t, L, g, hy = a["t"], a["load"], a["base"]["p_grid"], a["hybrid"]["p_grid"]
    fig, ax = plt.subplots(2, 2, figsize=(8, 5.2))
    for axx, (lo, hi, ttl) in zip([ax[0, 0], ax[0, 1], ax[1, 0]],
                                  [(100, 400, "Job start + first checkpoint"), (1000, 1030, "Iteration ripple (6 s)"),
                                   (2650, 3000, "Crash at 2700 s, restart 2950 s")]):
        m = (t >= lo) & (t <= hi)
        axx.plot(t[m], L[m], color="0.6", lw=0.7, label="AI campus load")
        axx.plot(t[m], g[m], color="C0", lw=1.0, label="Grid, BESS 150 ms")
        axx.plot(t[m], hy[m], color="C3", lw=1.0, label="Grid, BESS + supercap")
        axx.set_title(ttl, fontsize=8.5)
        axx.set_xlabel("s")
        axx.set_ylabel("MW")
    ax[0, 0].legend(fontsize=6.5)
    f, X = a["spec_load"]
    ax[1, 1].semilogy(f, X + 1e-6, color="0.6", lw=0.7, label="Load")
    ax[1, 1].semilogy(*a["spec_grid"], color="C0", lw=0.7, label="Grid, BESS")
    f2, X2 = a["spec_hybrid"]
    ax[1, 1].semilogy(f2, X2 + 1e-6, color="C3", lw=0.7, label="Grid, hybrid")
    ax[1, 1].axvspan(0.1, 2, color="C1", alpha=0.1, label="0.1–2 Hz band")
    ax[1, 1].set_xlim(0.01, 5)
    ax[1, 1].set_ylim(1e-4, 10)
    ax[1, 1].set_xscale("log")
    ax[1, 1].set_xlabel("Hz")
    ax[1, 1].set_ylabel("Amplitude MW")
    ax[1, 1].legend(fontsize=6.5)
    ax[1, 1].set_title("Spectrum", fontsize=8.5)
    fig.suptitle("(d) 12 MW synchronous AI training on a 24 MW base — ramp limit 3 MW/min", fontsize=9)
    save(fig, "fig_ai_swing.png")


def fig_ai_sweep(S):
    a = S["ai"]
    lim = A.AiSwing()
    fig, ax = plt.subplots(1, 2, figsize=(8, 2.8))
    rs = a["resp_sweep"]
    ax[0].plot([r["response_ms"] for r in rs], [r["grid_osc_pp_mw"] for r in rs], "o-", label="Residual 0.1–2 Hz p-p")
    ax[0].axhline(lim.osc_band_mw, color="k", ls="--", label=f"Limit {lim.osc_band_mw} MW")
    ax[0].axhline(a["m_base"]["load_osc_pp_mw"], color="0.6", ls=":", label="No BESS")
    ax[0].axhline(a["m_hybrid"]["grid_osc_pp_mw"], color="C3", ls="-.", label="Hybrid (supercap 5 ms)")
    ax[0].set_xlabel("BESS response time ms (delay)")
    ax[0].set_ylabel("MW p-p")
    ax[0].legend(fontsize=6.5)
    sw = a["ramp_sweep"]
    ax[1].plot([r["ramp_mw_min"] for r in sw], [r["e_req_mwh"] for r in sw], "o-", color="C4", label="Energy needed")
    ax[1].set_xscale("log")
    ax[1].set_xlabel("Grid ramp limit MW/min")
    ax[1].set_ylabel("MWh", color="C4")
    t2 = ax[1].twinx()
    t2.plot([r["ramp_mw_min"] for r in sw], [r["p_bess_req_mw"] for r in sw], "s--", color="C2")
    t2.set_ylabel("Power needed MW", color="C2")
    t2.grid(False)
    ax[1].set_title("BESS size vs ramp limit", fontsize=8.5)
    save(fig, "fig_ai_sweep.png")


def fig_business(S):
    bz = S["business"]
    rows = bz["base"]["rows"]
    cx = bz["base"]["kpi"]["capex"]
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    yrs = [0] + [r["year"] for r in rows]
    cum = np.concatenate([[-cx], -cx + np.cumsum([r["cf"] for r in rows])]) / 1e6
    ax[0].plot(yrs, cum, "o-", ms=3, label="2026 prices, −3 %/yr")
    for sc, col in (("2025", "C2"), ("saturated", "C3")):
        c = Bz.case(pr=A.Prices(scenario=sc))
        ax[0].plot(yrs, np.concatenate([[-cx], -cx + np.cumsum([r["cf"] for r in c["rows"]])]) / 1e6, "o-", ms=3,
                   color=col, label=f"{sc} prices")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_xlabel("Year")
    ax[0].set_ylabel("Cumulative cash flow M€ (undiscounted)")
    ax[0].legend(fontsize=7)
    ax[0].set_title(f"(e) 10 MW / 20 MWh, CAPEX {cx/1e6:.2f} M€", fontsize=9)
    td = bz["tornado"]
    base = bz["base"]["kpi"]["npv"] / 1e6
    for i, r in enumerate(td):
        lo, hi = r["low"] / 1e6, r["high"] / 1e6
        ax[1].barh(i, lo - base, left=base, color="C3")
        ax[1].barh(i, hi - base, left=base, color="C2")
    ax[1].set_yticks(range(len(td)))
    ax[1].set_yticklabels([r["label"] for r in td], fontsize=7)
    ax[1].axvline(base, color="k", lw=0.8)
    ax[1].set_xlabel("NPV M€ (WACC 7 %, 15 yr)")
    ax[1].set_title(f"Tornado around base NPV {base:.1f} M€ (red = first value)", fontsize=8.5)
    save(fig, "fig_business.png")


def fig_grid(S):
    g = S["business"]["grid"]
    P = sorted({r["p_mw"] for r in g})
    Hh = sorted({r["h"] for r in g})
    M = np.array([[next(r for r in g if r["p_mw"] == p and r["h"] == h)["npv_meur"] for h in Hh] for p in P])
    X = np.array([[next(r for r in g if r["p_mw"] == p and r["h"] == h)["extra_it_mw"] for h in Hh] for p in P])
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    im = ax.imshow(M, cmap="RdYlGn", origin="lower", aspect="auto")
    for i in range(len(P)):
        for j in range(len(Hh)):
            ax.text(j, i, f"{M[i, j]:.1f} M€\n+{X[i, j]:.1f} MW IT", ha="center", va="center", fontsize=6.5)
    ax.set_xticks(range(len(Hh)))
    ax.set_xticklabels([f"{h} h" for h in Hh])
    ax.set_yticks(range(len(P)))
    ax.set_yticklabels([f"{p} MW" for p in P])
    ax.set_xlabel("Duration")
    ax.set_ylabel("Power")
    ax.grid(False)
    fig.colorbar(im, label="NPV M€ (2026 prices)")
    ax.set_title("Sizing sensitivity: NPV and extra IT under 40 MW", fontsize=8.5)
    save(fig, "fig_sizing_grid.png")


def summary(S):
    ps, bz, a, bk = S["peak"], S["business"], S["ai"], S["backup"]
    rv = S["revenue"]
    return {
        "peak": {k: ps[k] for k in ("x_no_bess", "x_no_bess_no_recharge", "x_bess", "x_firm", "hours_over", "longest_run_h",
                                     "e_shaved_mwh", "peak_mw", "peak_no_recharge_mw", "mean_mw", "energy_gwh")},
        "peak_e_sweep": ps["e_sweep"], "peak_p_sweep": ps["p_sweep"],
        "revenue": {s: {"total": v["total"], "efc": v["efc"], "rev": v["rev"], "avg_mw": v["avg_mw"]} for s, v in rv["scenarios"].items()},
        "compat": {k: {"x_mw": v["x_mw"], "total": v["total"]} for k, v in rv["compat"].items()},
        "backup": {"usable_mwh": bk["autonomy"][0], "autonomy": bk["autonomy"][1], "replace_all": bk["replace_all"],
                   "fail_to_start": bk["fail_to_start"],
                   "island": {k: v for k, v in bk["island"].items() if k != "rows"}, "island_rows": bk["island"]["rows"]},
        "ai": {"base": a["m_base"], "hybrid": a["m_hybrid"], "ramp_sweep": a["ramp_sweep"], "resp_sweep": a["resp_sweep"]},
        "business": {"kpi": bz["base"]["kpi"], "scenarios": bz["scenarios"], "tornado": bz["tornado"],
                     "shaved_mw": bz["base"]["shaved_mw"], "subs_eur": bz["base"]["subs_eur"], "it": bz["it"],
                     "rows": bz["base"]["rows"]},
    }


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


def main():
    t0 = time.time()
    S = study.run(grid=True)
    for f in (fig_peak, fig_extra, fig_revenue, fig_ai, fig_ai_sweep, fig_business, fig_grid):
        f(S)
    sm = _clean(summary(S))
    with open(os.path.join(RES, "summary.json"), "w") as f:
        json.dump(sm, f, indent=1, ensure_ascii=False)
    write_csv("sizing_grid.csv", S["business"]["grid"])
    write_csv("ai_ramp_sweep.csv", S["ai"]["ramp_sweep"])
    write_csv("ai_response_sweep.csv", S["ai"]["resp_sweep"])
    write_csv("cashflows_base.csv", S["business"]["base"]["rows"])
    write_csv("assumptions_register.csv", A.register(A.Site(), A.Bess(), A.Prices(), A.Finance(), A.AiSwing()))
    ps = S["peak"]
    np.savetxt(os.path.join(RES, "hourly_profiles.csv"),
               np.c_[np.arange(8760), ps["temp"], ps["load"], ps["dispatch"]["grid"], ps["dispatch"]["d"] - ps["dispatch"]["c"]],
               delimiter=",", header="hour,temp_c,load_mw,grid_with_bess_and_extra_it_mw,bess_mw", fmt="%.4f", comments="")
    print(f"done in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
