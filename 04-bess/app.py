"""DWU-DC-E-CALC-004 — BESS at the 30 MW data-centre campus (portfolio tool).

Run:  streamlit run app.py
Public data (cited, accessed 2026-10-24) + ASSUMED parameters (bessdc/assumptions.py). Not for construction/investment.
"""
import json
import os
from dataclasses import replace, fields

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from bessdc import __version__, assumptions as A, profiles as P, dispatch as D, backup as B, ai_swing as AI, business as Bz

ROOT = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="BESS at a 30 MW data centre", page_icon="🔋", layout="wide")
st.title("🔋 BESS at the 30 MW data-centre campus")
st.caption(f"Portfolio tool DWU-DC-E-CALC-004 · bessdc v{__version__} · fictional campus, Dalarna (SE3) · "
           "public data (cited) + ASSUMED parameters · not for construction or investment decisions")

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("BESS")
    p_mw = st.slider("Power (MW)", 2.0, 20.0, 10.0, 0.5, key="p_mw")
    e_mwh = st.slider("Energy (MWh)", 2.0, 80.0, 20.0, 1.0, key="e_mwh")
    eta = st.slider("Round-trip efficiency", 0.80, 0.95, 0.88, 0.01, key="eta")
    st.header("Site")
    lim = st.number_input("Grid import limit (MW)", 30.0, 60.0, 40.0, 0.5, key="lim")
    recharge = st.checkbox("UPS recharge coincides with heat-wave peak", True, key="recharge")
    st.header("Markets & finance")
    scen = st.selectbox("Price scenario", list(A.PRICE_TABLE), index=1, key="scen")
    real = st.slider("Realisation factor", 0.5, 1.0, 0.85, 0.05, key="real")
    c_e = st.slider("Energy CAPEX (€/kWh)", 60, 250, 120, 5, key="c_e")
    wacc = st.slider("WACC", 0.03, 0.12, 0.07, 0.005, key="wacc")
    trend = st.slider("Ancillary price trend (%/yr)", -15, 5, -3, 1, key="trend") / 100
    it_val = st.number_input("Value of enabled IT (k€/MW·yr)", 0, 2000, 0, 50, key="it_val")
    st.header("AI swing")
    p_ai = st.slider("AI cluster swing (MW)", 2.0, 20.0, 12.0, 1.0, key="p_ai")
    ramp = st.slider("Grid ramp limit (MW/min)", 0.5, 20.0, 3.0, 0.5, key="ramp")
    resp = st.select_slider("BESS response (ms)", [0, 20, 50, 100, 150, 300, 600], 150, key="resp")

site = A.Site(grid_limit_mw=lim)
bess = A.Bess(p_mw=p_mw, e_mwh=e_mwh, eta_rt=eta)
prices = A.Prices(scenario=scen, realisation=real)
fin = A.Finance(c_energy_eur_kwh=c_e, wacc=wacc, price_trend=trend, it_value_keur_mw=it_val)
ai_p = A.AiSwing(p_ai_mw=p_ai, ramp_mw_min=ramp)


@st.cache_data(show_spinner=False)
def peak(lim, p_mw, e_mwh, eta, recharge):
    s, b = A.Site(grid_limit_mw=lim), A.Bess(p_mw=p_mw, e_mwh=e_mwh, eta_rt=eta)
    L0, per = P.campus_load(s, recharge=recharge)
    no = D.max_extra_it(L0, per, lim, b, 0, 0)["x_mw"]
    full = D.max_extra_it(L0, per, lim, b)
    firm = D.max_extra_it(L0, per, lim, b, p_mw=p_mw / 2, e_mwh=e_mwh / 2)["x_mw"]
    sweep = [(e, D.max_extra_it(L0, per, lim, b, e_mwh=e)["x_mw"]) for e in (5, 10, 20, 40, 60)]
    return L0, per, no, full, firm, sweep


@st.cache_data(show_spinner=False)
def market(lim, p_mw, e_mwh, eta, scen, x_mw):
    b, s, pr = A.Bess(p_mw=p_mw, e_mwh=e_mwh, eta_rt=eta), A.Site(grid_limit_mw=lim), A.Prices(scenario=scen)
    m = Bz.market_year(p_mw, e_mwh, pr, b, s, extra_it_mw=0.0)
    L0, per = P.campus_load(s)
    r_x = D.co_optimise(L0 + x_mw * per, lim, P.spot_price(pr), P.capacity_prices(pr), b)
    r_u = D.co_optimise(L0, lim, P.spot_price(pr), P.capacity_prices(pr), b, grid_limited=False)
    slim = {k: {"rev": v["rev"], "efc": v["efc"], "overshoot_mw": v["overshoot_mw"],
                "avg": {kk: float(vv.mean()) for kk, vv in v["res"].reserves.items()}} for k, v in m.items()}
    return slim, r_x.total, r_u.total, m[1.0]["res"].e[:24 * 14]


@st.cache_data(show_spinner=False)
def ai_run(p_ai, ramp, resp):
    a = A.AiSwing(p_ai_mw=p_ai, ramp_mw_min=ramp)
    t, L = AI.ai_profile(a)
    r = AI.smooth(L, a, response_ms=resp)
    h = AI.smooth(L, a, response_ms=resp, hybrid_split_s=5.0)
    return t, L, r["p_grid"], h["p_grid"], AI.metrics(t, L, r, a), AI.metrics(t, L, h, a)


@st.cache_data(show_spinner=False)
def sizing_grid_csv():
    f = os.path.join(ROOT, "results", "sizing_grid.csv")
    return pd.read_csv(f) if os.path.exists(f) else None


L0, per, x_no, full, x_firm, e_sweep = peak(lim, p_mw, e_mwh, eta, recharge)
x_bess = full["x_mw"]
m, tot_x, tot_u, soc14 = market(lim, p_mw, e_mwh, eta, scen, x_bess)
m_full = {k: {"rev": v["rev"], "efc": v["efc"], "overshoot_mw": v["overshoot_mw"]} for k, v in m.items()}
cx = Bz.capex_eur(p_mw, e_mwh, fin)
shaved, subs = Bz.subscription_value(p_mw, e_mwh, prices, bess, site, 0.0, m[1.0]["overshoot_mw"])
rows = Bz.cashflows(cx, m_full, p_mw, e_mwh, fin, bess, prices, subs, it_val * 1e3 * max(x_bess, 0))
kpi = Bz.kpis(cx, rows, wacc)
isl = B.island_fault_check(bess)

tabs = st.tabs(["Overview", "Peak shaving", "Backup role", "Revenue stacking", "AI smoothing", "Business case",
                "Assumptions & sources"])

# ---------------------------------------------------------------- overview
with tabs[0]:
    c = st.columns(5)
    c[0].metric("Extra IT under limit", f"{x_bess:+.2f} MW", f"{x_bess - x_no:+.2f} MW vs no BESS")
    c[1].metric("Firm extra IT (one unit out)", f"{x_firm:+.2f} MW")
    c[2].metric("Market value (LP)", f"{sum(m[1.0]['rev'].values()) / 1e6:.2f} M€/yr")
    c[3].metric("NPV", f"{kpi['npv'] / 1e6:.1f} M€", f"payback {kpi['payback_y']:.1f} yr")
    c[4].metric("Backup at campus peak", f"{60 * B.autonomy(bess)[0] / 37.818:.0f} min", "vs 24 h fuel", delta_color="off")
    st.markdown(
        f"""
**Findings for {p_mw:g} MW / {e_mwh:g} MWh at the reserved MSG-20 bay(s)**

* **Peak shaving** – without BESS the design-day peak ({L0.max():.1f} MW, incl. UPS recharge after an outage) is
  {'above' if x_no < 0 else 'below'} the {lim:g} MW limit (headroom {x_no:+.2f} MW IT). The BESS lets **{x_bess:+.2f} MW** IT
  fit; peaks are few but long (heat-wave afternoons), so energy, not power, binds.
* **Backup** – cannot replace gensets for Tier III / EN 50600 Class 3 (finite energy; {60 * B.autonomy(bess)[0] / 37.818:.0f} min at campus peak).
  Inverter fault current ≈ {isl['i_mv_a']:.0f} A at 20 kV → grid-tuned 20 kV relays do not clear island faults.
* **Revenue** – FCR-N/FCR-D/mFRR + arbitrage ≈ **{sum(m[1.0]['rev'].values()) / 1e6:.2f} M€/yr** ({scen} prices, perfect foresight);
  honouring the grid limit with max extra IT costs only {(tot_u - tot_x) / 1e3:.0f} k€/yr.
* **AI smoothing** – ramp limiting needs ≈ AI-swing power but < 1 MWh; the 0.1–2 Hz ripple needs ≲ 10 ms effective response → supercap/UPS or GPU-side.
* **Business case** – CAPEX {cx / 1e6:.2f} M€, NPV {kpi['npv'] / 1e6:.1f} M€, IRR {kpi['irr'] * 100:.0f} %. Dominated by
  ancillary prices that are falling as BESS floods the Nordic market (Svk Balancing Market Outlook).
""")

# ---------------------------------------------------------------- peak shaving
with tabs[1]:
    c = st.columns(4)
    c[0].metric("Peak demand (no BESS)", f"{L0.max():.2f} MW")
    c[1].metric("Headroom without BESS", f"{x_no:+.2f} MW IT")
    c[2].metric("With BESS", f"{x_bess:+.2f} MW IT")
    c[3].metric("Firm (N-1 BESS)", f"{x_firm:+.2f} MW IT")
    h0, h1 = 194 * 24, 202 * 24
    df = pd.DataFrame({"hour": np.arange(h0, h1), "Load + extra IT (no BESS)": (L0 + x_bess * per)[h0:h1],
                       "Grid with BESS": full["grid"][h0:h1], "Limit": lim})
    dl = df.melt("hour", var_name="series", value_name="MW")
    st.altair_chart(alt.Chart(dl).mark_line().encode(x="hour", y=alt.Y("MW", scale=alt.Scale(zero=False)), color="series")
                    .properties(height=320, title="Design heat-wave week (hourly LP)"), width="stretch")
    st.dataframe(pd.DataFrame(e_sweep, columns=["BESS energy (MWh)", "Extra IT (MW)"]).round(2), hide_index=True)
    st.info("Hourly perfect-foresight LP (HiGHS). Assumes the BESS is fully charged before the design peak; a real EMS needs "
            "a forecast-based SOC reserve and a fallback (IT load shedding/UPS recharge limiting) if the BESS is unavailable.")

# ---------------------------------------------------------------- backup
with tabs[2]:
    usable, aut = B.autonomy(bess)
    c = st.columns(4)
    c[0].metric("Usable energy", f"{usable:.1f} MWh")
    c[1].metric("Inverter fault current", f"{isl['i_mv_a']:.0f} A @ 20 kV")
    c[2].metric("MSG-20 Ik'' with BESS", f"{isl['ik_msg20_with_bess_ka']:.2f} kA", f"+{isl['grid_contrib_ka']:.2f} kA")
    c[3].metric("Worst case vs 25 kA", f"{isl['ik_msg20_worst_with_bess_ka']:.1f} kA")
    st.subheader("Can / cannot replace")
    st.dataframe(pd.DataFrame(B.CAN_CANNOT, columns=["Function", "Credible?", "Why"]), hide_index=True, width="stretch")
    st.subheader("20 kV island fault clearing with CALC-003 settings")
    st.dataframe(pd.DataFrame(isl["rows"]).round(2), hide_index=True, width="stretch")
    st.subheader("Autonomy")
    st.dataframe(pd.DataFrame(aut).round(2), hide_index=True)
    ra = B.replace_all_gensets(site, bess)
    st.warning(f"Replacing all 36 gensets for 24 h would need ≈ {ra['p_mw']:.0f} MW / {ra['e_mwh']:.0f} MWh "
               f"(≈ {ra['bess_capex_meur']:.0f} M€ vs ≈ {ra['genset_capex_meur']:.0f} M€ gensets [ASSUMED costs]) — and still "
               "would not satisfy the unlimited-runtime expectation for Tier III / EN 50600 Class 3 on-site generation.")
    st.subheader("Genset ratings (ISO 8528-1)")
    st.dataframe(pd.DataFrame(B.GENSET_RATINGS, columns=["Rating", "Definition", "Data-centre use"]), hide_index=True)
    st.subheader("Fire safety (concept)")
    st.dataframe(pd.DataFrame(B.FIRE_SAFETY, columns=["Standard", "Scope"]), hide_index=True, width="stretch")
    for f in B.FIRE_DESIGN:
        st.markdown(f"* {f}")

# ---------------------------------------------------------------- revenue
with tabs[3]:
    rev = m[1.0]["rev"]
    c = st.columns(4)
    c[0].metric("Total (LP, SOH 100 %)", f"{sum(rev.values()) / 1e6:.2f} M€/yr")
    c[1].metric("At SOH 80 %", f"{sum(m[0.8]['rev'].values()) / 1e6:.2f} M€/yr")
    c[2].metric("Equivalent full cycles", f"{m[1.0]['efc']:.0f} /yr")
    c[3].metric("Cost of 40 MW limit + max IT", f"{(tot_u - tot_x) / 1e3:.0f} k€/yr")
    dfr = pd.DataFrame({"stream": list(rev), "k€/yr": [v / 1e3 for v in rev.values()]})
    st.altair_chart(alt.Chart(dfr).mark_bar().encode(x="k€/yr", y=alt.Y("stream", sort=None))
                    .properties(height=250, title=f"Revenue stack, {scen} prices"), width="stretch")
    st.dataframe(pd.DataFrame([{"product": k, "avg MW offered": v} for k, v in m[1.0]["avg"].items()]).round(2), hide_index=True)
    st.caption("Capacity prices: Svk Mimer annual means (via Flexnavet wiki), synthetic hourly shape. FCR endurance per "
               "Svk LER rules (FCR-N 1 h, FCR-D 20 min). Down-reserve activation is counted against the import limit.")

# ---------------------------------------------------------------- AI smoothing
with tabs[4]:
    t, L, g, gh, mb, mh = ai_run(p_ai, ramp, resp)
    c = st.columns(4)
    c[0].metric("BESS power needed", f"{mb['p_bess_req_mw']:.1f} MW")
    c[1].metric("BESS energy needed", f"{mb['e_req_mwh']:.2f} MWh")
    c[2].metric("Residual 0.1–2 Hz p-p", f"{mb['grid_osc_pp_mw']:.2f} MW", "OK" if mb["ok_osc"] else "exceeds limit",
                delta_color="normal" if mb["ok_osc"] else "inverse")
    c[3].metric("Hybrid (supercap) p-p", f"{mh['grid_osc_pp_mw']:.2f} MW", f"SC {mh['e_sc_kwh']:.0f} kWh", delta_color="off")
    lo = st.slider("Window start (s)", 0, 3500, 1000, 10, key="ai_win")
    msk = (t >= lo) & (t <= lo + 60)
    dfa = pd.DataFrame({"t": t[msk], "Load": L[msk], "Grid (BESS)": g[msk], "Grid (hybrid)": gh[msk]}).melt("t", var_name="series", value_name="MW")
    st.altair_chart(alt.Chart(dfa).mark_line().encode(x="t", y=alt.Y("MW", scale=alt.Scale(zero=False)), color="series")
                    .properties(height=300), width="stretch")
    st.dataframe(pd.DataFrame(AI.ALTERNATIVES, columns=["Option", "Response", "Energy", "Cycle life", "Comment"]),
                 hide_index=True, width="stretch")

# ---------------------------------------------------------------- business
with tabs[5]:
    c = st.columns(4)
    c[0].metric("CAPEX", f"{cx / 1e6:.2f} M€")
    c[1].metric("NPV", f"{kpi['npv'] / 1e6:.1f} M€")
    c[2].metric("IRR", "n/a" if np.isnan(kpi["irr"]) else f"{kpi['irr'] * 100:.0f} %")
    c[3].metric("Payback", f"{kpi['payback_y']:.1f} yr")
    dfc = pd.DataFrame(rows)
    st.dataframe((dfc.set_index("year") / 1e3).drop(columns=["soh_end"]).round(0).assign(soh_end=dfc.set_index("year")["soh_end"].round(3)),
                 width="stretch")
    ann = Bz.it_breakeven(None, max(x_bess, 0), fin)
    st.info(f"Each 100 k€/MW·yr of value for the {x_bess:.2f} MW enabled IT adds ≈ {ann['npv_per_keur_mw'] * 100:.1f} M€ NPV "
            "(base case counts 0).")
    g = sizing_grid_csv()
    if g is not None:
        st.subheader("Sizing grid (precomputed with defaults by scripts/make_all.py)")
        st.altair_chart(alt.Chart(g).mark_rect().encode(x="h:O", y=alt.Y("p_mw:O", sort="descending"),
                        color=alt.Color("npv_meur", scale=alt.Scale(scheme="redyellowgreen")),
                        tooltip=["p_mw", "h", "npv_meur", "extra_it_mw", "capex_meur"]).properties(height=260),
                        width="stretch")

# ---------------------------------------------------------------- assumptions
with tabs[6]:
    reg = pd.DataFrame(A.register(site, bess, prices, fin, ai_p)).astype({"value": str})
    st.dataframe(reg, hide_index=True, width="stretch")
    st.subheader("Sources (accessed %s)" % A.ACCESSED)
    for k, (title, url) in A.SOURCES.items():
        st.markdown(f"* **{k}** — {title} — {url}")
