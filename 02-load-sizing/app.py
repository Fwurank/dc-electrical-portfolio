"""DWU-DC-E-CALC-002 — Data-centre load & equipment sizing (portfolio tool).

Run:  streamlit run app.py
All parameters are public-standard based or ASSUMED (see dcsizing/tables.py). Not for construction.
"""
import pandas as pd
import altair as alt
import streamlit as st

from dcsizing import scenario as S, __version__

st.set_page_config(page_title="DC load & equipment sizing", page_icon="⚡", layout="wide")

st.title("⚡ Data-centre load & equipment sizing")
st.caption(f"Portfolio tool DWU-DC-E-CALC-002 · dcsizing v{__version__} · fictional 30 MW campus, Dalarna (SE3) · "
           "public standards + ASSUMED parameters · not for construction")

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Inputs")
    it_mw = st.number_input("Total IT load (MW)", 1.0, 200.0, 30.0, 1.0, key="it_mw")
    halls = st.number_input("Data halls", 1, 40, 6, 1, key="halls")
    scheme = st.selectbox("Redundancy scheme", list(S.SCHEMES), index=0, key="scheme",
                          format_func=lambda k: {"DR": "Distributed redundant (xN/(x-1))", "2N": "2N",
                                                 "N+1": "N+1 (common bus)", "BR": "Block redundant (n+1 catcher)"}[k])
    n_default = {"DR": 4, "2N": 2, "N+1": 3, "BR": 4}[scheme]
    n_label = {"DR": "Blocks per hall (n, ≥3)", "2N": "Block pairs per hall (n)", "N+1": "Active blocks n (n+1 installed)",
               "BR": "Primary blocks n (+1 reserve)"}[scheme]
    n_blocks = st.number_input(n_label, 3 if scheme == "DR" else 1, 12, n_default, 1, key="n_blocks")
    st.subheader("Efficiency & climate")
    pue_mode = st.radio("Mechanical load from", ["pPUE at design peak", "Target hall pPUE"], key="pue_mode", horizontal=True)
    if pue_mode == "pPUE at design peak":
        ppue_mech = st.slider("Mechanical pPUE at design peak", 0.05, 0.50, 0.17, 0.01, key="ppue_mech")
        target = None
    else:
        target = st.slider("Target hall pPUE at design peak", 1.10, 1.60, 1.25, 0.01, key="target")
        ppue_mech = 0.17
    ppue_free = st.slider("Mechanical pPUE in free cooling", 0.02, 0.15, 0.05, 0.005, key="ppue_free")
    amb = st.slider("Design ambient for gensets / heat rejection (°C)", 20, 50, 32, 1, key="amb")
    alt_m = st.number_input("Site altitude (m)", 0, 3000, 150, 50, key="alt")
    it_util = st.slider("Average IT utilisation (annual PUE)", 0.3, 1.0, 0.75, 0.05, key="util")
    with st.expander("UPS / battery / generator"):
        ups_mod = st.selectbox("UPS module (kW)", [250, 500, 800, 1000, 1250], index=3, key="ups_mod")
        bat_min = st.slider("Stored-energy time at EoL (min)", 2.0, 15.0, 5.0, 0.5, key="bat_min")
        bat_t = st.slider("Battery room temperature (°C)", 10, 35, 25, 1, key="bat_t")
        c_max = st.slider("LFP max. discharge C-rate at EoL", 2.0, 12.0, 8.0, 0.5, key="c_max")
        recharge = st.slider("Recharge on grid (% of UPS rating)", 0, 20, 10, 1, key="recharge") / 100
        recharge_g = st.slider("Recharge on generator (%)", 0, 20, 5, 1, key="recharge_g") / 100
        fuel_h = st.slider("Fuel autonomy (h)", 12, 72, 24, 1, key="fuel_h")
        chiller = st.number_input("Largest chiller step (kW)", 50, 2000, 400, 50, key="chiller")
    with st.expander("Grid & distribution"):
        sk = st.number_input("130 kV Sk'' (MVA)", 500, 10000, 3000, 100, key="sk")
        tx_uk = st.select_slider("Block transformer uk", [0.04, 0.05, 0.06, 0.07, 0.08], 0.06, key="uk")
        rack = st.slider("Rack load (kW)", 5, 60, 25, 1, key="rack")

inp = S.Inputs(it_mw_total=it_mw, n_halls=int(halls), scheme=scheme, n_blocks=int(n_blocks), ambient_design_c=amb,
               altitude_m=alt_m, ppue_mech_peak=ppue_mech, ppue_mech_free=ppue_free, target_pue_peak=target,
               it_util=it_util, ups_module_kw=ups_mod, battery_min=bat_min, battery_temp_c=bat_t, battery_c_max=c_max,
               recharge_frac=recharge, recharge_frac_on_gen=recharge_g, fuel_hours=fuel_h, sk_hv_mva=sk,
               tx_uk=tx_uk, largest_chiller_kw=chiller, rack_kw=rack)
try:
    r = S.run(inp)
except ValueError as e:
    st.error(f"Invalid input: {e}")
    st.stop()

flags = pd.DataFrame(r["flags"])
n_fail = int((~flags["ok"]).sum())

# ---------------------------------------------------------------- headline metrics
c = st.columns(6)
c[0].metric("Campus demand", f"{r['campus']['p_kw']/1000:.1f} MW", f"{r['campus']['s_kva']/1000:.1f} MVA", delta_color="off")
c[1].metric("Design-peak PUE", f"{r['campus']['pue']:.3f}")
c[2].metric("Annualised PUE", f"{r['annual']['pue']:.3f}", f"{r['annual']['facility_mwh']/1000:.0f} GWh/yr", delta_color="off")
c[3].metric("Block normal / N-1 (MW)", f"{r['block']['normal']/1000:.2f} / {r['block']['failure']/1000:.2f}")
c[4].metric("MSB I''k (IEC 60909)", f"{r['sc']['ik_msb_ka']:.1f} kA")
c[5].metric("Checks failing", f"{n_fail} / {len(flags)}", delta=None)
st.info(S.SCHEMES[scheme] + (" — **not concurrently maintainable** (single critical bus)" if scheme == "N+1" else "")
        + (" — needs STS / catcher bus to the reserve block" if scheme == "BR" else ""))

tab_sum, tab_eq, tab_flags, tab_cab, tab_pue, tab_cmp = st.tabs(
    ["Summary", "Equipment ratings", "Checks", "Cables & busway", "PUE & energy", "vs phase 1"])

with tab_sum:
    lc, rc = st.columns([1.1, 1])
    with lc:
        st.subheader("Loading: normal vs. failure mode")
        g = r["gen"]
        rows = [("UPS (block)", r["ups"]["loading_normal"], r["ups"]["loading_failure"], inp.ups_max_loading),
                ("Block transformer", r["tx"]["loading_normal"], r["tx"]["loading_failure"], 1.0),
                ("IT genset (kWe)", (g["load_normal_kw"] / g["kwe_site"]) if g["kva"] else None, g["loading_kw"], inp.gen_max_loading),
                ("Mech transformer", (r["mech"]["tx_loading_failure"] or 0) / 2, r["mech"]["tx_loading_failure"], 1.0),
                ("HV transformer", r["hv_loading"] / 2, r["hv_loading"], 1.0)]
        df = pd.DataFrame([{"equipment": a, "mode": m, "loading": v * 100, "limit": lim * 100}
                           for a, n_, f_, lim in rows for m, v in (("normal", n_), ("failure (N-1)", f_)) if v is not None])
        bars = alt.Chart(df).mark_bar().encode(
            y=alt.Y("equipment:N", title=None, sort=None), yOffset="mode:N",
            x=alt.X("loading:Q", title="loading (% of rating)", scale=alt.Scale(domain=[0, 120])),
            color=alt.Color("mode:N", scale=alt.Scale(range=["#4c78a8", "#e45756"])),
            tooltip=["equipment", "mode", alt.Tooltip("loading:Q", format=".1f"), "limit"])
        rule = alt.Chart(df).mark_tick(color="black", thickness=2, size=22).encode(y=alt.Y("equipment:N", sort=None), x="limit:Q")
        st.altair_chart(bars + rule, use_container_width=True)
        st.caption("Black tick = design limit (ASSUMED policy). Failure mode = worst single block / transformer out.")
    with rc:
        st.subheader("Hall load build-up (design peak)")
        h = r["hall"]
        comp = pd.DataFrame({"component": ["IT", "UPS losses", "Mechanical", "Distribution losses", "House", "Recharge (sizing)"],
                             "kW": [h["it_kw"], h["ups_loss_kw"], h["mech_kw"], h["dist_loss_kw"], h["house_kw"], h["recharge_kw"]]})
        st.altair_chart(alt.Chart(comp).mark_arc(innerRadius=60).encode(
            theta="kW:Q", color=alt.Color("component:N", sort=None), tooltip=["component", alt.Tooltip("kW:Q", format=",.0f")]),
            use_container_width=True)
        st.write(f"Hall total **{h['total_kw']:,.0f} kW** (pPUE {h['ppue']:.3f}), max incl. recharge **{h['max_kw']:,.0f} kW** "
                 f"→ 20 kV feeder **{r['mv_feeder_a']:.0f} A**.")
    st.subheader("Scheme comparison (same inputs)")
    cmp_rows = []
    for sch, n in (("DR", 3), ("DR", 4), ("2N", 2), ("N+1", 3), ("BR", 4)):
        try:
            rr = S.run(S.Inputs(**{**inp.as_dict(), "scheme": sch, "n_blocks": n}))
        except ValueError:
            continue
        cmp_rows.append({"scheme": f"{sch} n={n}", "blocks / hall": rr["block"]["blocks"],
                         "UPS installed / IT": rr["installed"]["ups_ratio"],
                         "block N-1 load (kW)": rr["block"]["failure"], "UPS (kW)": rr["ups"]["rating_kw"],
                         "transformer (kVA)": rr["tx"]["kva"], "genset (kVA)": str(rr["gen"]["kva"] or "> std range"),
                         "concurrently maintainable": rr["block"]["conc_maint"],
                         "failing checks": int(sum(not f["ok"] for f in rr["flags"]))})
    cdf = pd.DataFrame(cmp_rows)
    st.dataframe(cdf, hide_index=True, use_container_width=True,
                 column_config={"UPS installed / IT": st.column_config.NumberColumn(format="%.2f"),
                                "block N-1 load (kW)": st.column_config.NumberColumn(format="%.0f")})

with tab_eq:
    g, u, t, b, m = r["gen"], r["ups"], r["tx"], r["battery"], r["mech"]
    eq = [
        ("UPS per block", f"{u['modules']} × {u['module_kw']:.0f} kW = {u['rating_kw']:.0f} kW, VFI-SS-111",
         f"{u['loading_normal']*100:.1f} %", f"{u['loading_failure']*100:.1f} %", "IEC 62040-3"),
        ("Battery per module (LFP)", f"{b['selected_kwh']} kWh nameplate (req. {b['e_required_kwh']:.0f}; energy {b['e_energy_kwh']:.0f})",
         "", f"{b['autonomy_min_at_failure_load']:.1f} min at N-1 load", f"governed by {b['governed_by']}"),
        ("UPS input breaker", f"{u['input_breaker_a']:.0f} A (Imax {u['input_current_a']:.0f} A)", "", "", "IEC 60947-2"),
        ("Block transformer", f"{t['kva']} kVA 20/0.42 kV Dyn11 uk {inp.tx_uk*100:.0f} %",
         f"{t['loading_normal']*100:.1f} %", f"{t['loading_failure']*100:.1f} %", "IEC 60076-11"),
        ("IT genset", f"{g['kva']} kVA / {g['kwe']} kWe DCC (site {g['kwe_site']:.0f} kWe)",
         f"{g['load_normal_kw']/g['kwe_site']*100:.1f} %" if g['kva'] else "", f"{g['loading_kw']*100:.1f} %", "ISO 8528-1/-5"),
        ("MSB", f"{r['msb']['rating_a']} A, {r['msb']['rating_ka']} kA (I''k {r['sc']['ik_msb_ka']:.1f} kA, ip {r['sc']['ip_msb_ka']:.0f} kA)",
         "", "", "IEC 61439-2 / 60909-0"),
        ("UOSB", f"{r['uosb_a']} A", "", "", "IEC 61439-2"),
        ("Mech transformer (2N)", f"{m['tx_kva']} kVA", f"{(m['tx_loading_failure'] or 0)/2*100:.1f} %",
         f"{(m['tx_loading_failure'] or 0)*100:.1f} %", "IEC 60076-11"),
        ("Mech genset (2N)", f"{m['gen']['kva']} kVA / {m['gen']['kwe']} kWe", "", f"{m['gen']['loading_kw']*100:.1f} %",
         f"governed by {m['gen'].get('governed_by', '-')}"),
        ("Fuel per hall", f"{r['fuel']['tank_m3_hall']:.1f} m³ gross for {r['fuel']['hours']:.0f} h ({r['fuel']['lph_hall']:.0f} l/h)",
         "", "", "HVO100, EN 15940"),
        ("HV transformer", f"{inp.hv_tx_mva:.0f} MVA 130/21 kV", f"{r['hv_loading']*50:.1f} %", f"{r['hv_loading']*100:.1f} %",
         f"20 kV I''k {r['sc']['ik_mv_ka']:.1f} kA"),
    ]
    st.dataframe(pd.DataFrame(eq, columns=["item", "rating", "normal", "failure / N-1", "basis"]),
                 hide_index=True, use_container_width=True)
    if g.get("steps"):
        st.subheader("IT genset load steps (UPS walk-in)")
        sd = pd.DataFrame(g["steps"])
        sd["frac %"] = sd["frac"] * 100; sd["ΔU %"] = sd["du"] * 100
        st.altair_chart(alt.Chart(sd).mark_bar().encode(x="step:O", y=alt.Y("frac %:Q", title="step (% of site kWe)"),
                        color=alt.condition("datum.ok", alt.value("#54a24b"), alt.value("#e45756")),
                        tooltip=["kw", "frac %", "ΔU %"]), use_container_width=True)

with tab_flags:
    st.subheader("Pass / fail checks")
    f = flags.copy()
    f["status"] = f["ok"].map({True: "✅ pass", False: "❌ fail"})
    st.dataframe(f[["status", "item", "value", "limit", "note"]], hide_index=True, use_container_width=True,
                 height=36 * (len(f) + 1) + 4,
                 column_config={"value": st.column_config.NumberColumn(format="%.3f"),
                                "limit": st.column_config.NumberColumn(format="%.3f")})

with tab_cab:
    st.subheader("LV reference circuits (IEC 60364-5-52 / -4-43)")
    rows = []
    for cr in r["cables"]:
        x, k = cr["result"], cr["inputs"]
        rows.append({"tag": cr["tag"], "circuit": cr["circuit"], "Ib (A)": x.ib_a, "In (A)": x.in_a,
                     "method": x.method, "L (m)": k["length_m"], "selected": x.label(),
                     "k_amb": x.k_amb, "k_grp": x.k_grp, "Iz (A)": x.iz_a, "ΔU %": x.vd_pct,
                     "S_min SC (mm²)": x.s_min_sc_mm2, "OK": x.ok, "notes": "; ".join(x.notes)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                 column_config={c_: st.column_config.NumberColumn(format="%.2f") for c_ in ["k_amb", "k_grp", "ΔU %"]} |
                               {c_: st.column_config.NumberColumn(format="%.0f") for c_ in ["Ib (A)", "Iz (A)", "S_min SC (mm²)"]})
    st.subheader("Busbar trunking (IEC 61439-6)")
    bw = pd.DataFrame([{"run": "White-space run (survivor)", "Ib (A)": r["run_a"], **r["busway_ws"]},
                       {"run": "Transformer → MSB", "Ib (A)": r["tx"]["i_rated_a"], **r["busway_tx"]}])
    st.dataframe(bw.round(3), hide_index=True, use_container_width=True,
                 column_config={"Ib (A)": st.column_config.NumberColumn(format="%.0f")})
    st.caption("Iz tables: IEC 60364-5-52 B.52.5/B.52.12; ambient B.52.14; grouping B.52.17/B.52.21; k Table 43A. "
               "Busway data ASSUMED typical manufacturer values.")

with tab_pue:
    st.subheader("PUE by outdoor temperature bin (EN 50600-4-2)")
    bins = pd.DataFrame(r["annual"]["bins"])
    base = alt.Chart(bins).encode(x=alt.X("t_c:O", title="bin centre (°C)"))
    st.altair_chart(alt.layer(base.mark_bar(opacity=0.35, color="#4c78a8").encode(y=alt.Y("hours:Q", title="hours")),
                              base.mark_line(point=True, color="#e45756").encode(y=alt.Y("pue:Q", title="PUE", scale=alt.Scale(zero=False))))
                    .resolve_scale(y="independent"), use_container_width=True)
    st.write(f"Annualised PUE **{r['annual']['pue']:.3f}** at {it_util*100:.0f} % IT → facility energy "
             f"**{r['annual']['facility_mwh']/1000:.0f} GWh/yr** (IT {r['annual']['it_mwh']/1000:.0f} GWh/yr).")
    sens = []
    for pf in (0.02, 0.035, 0.05, 0.08):
        for ut in (0.5, 0.75, 1.0):
            rr = S.run(S.Inputs(**{**inp.as_dict(), "ppue_mech_free": pf, "it_util": ut}))
            sens.append({"mech pPUE free cooling": pf, "IT utilisation": ut, "annual PUE": rr["annual"]["pue"]})
    st.altair_chart(alt.Chart(pd.DataFrame(sens)).mark_line(point=True).encode(
        x="IT utilisation:Q", y=alt.Y("annual PUE:Q", scale=alt.Scale(zero=False)), color="mech pPUE free cooling:N"),
        use_container_width=True)

with tab_cmp:
    st.subheader("Ratings vs. phase-1 design basis (DWU-DC-E-DB-001)")
    ch = pd.DataFrame(S.rating_changes(r))
    ch["phase1"] = ch["phase1"].astype(str); ch["project02"] = ch["project02"].astype(str)
    st.dataframe(ch, hide_index=True, use_container_width=True, height=36 * (len(ch) + 1) + 4)
