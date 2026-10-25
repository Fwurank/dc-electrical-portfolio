"""Build calculation report DWU-DC-E-CALC-002 (A4 PDF) for the 30 MW reference case.
HTML → headless Chrome PDF (same pipeline/style as phase-1 DWU-DC-E-DB-001)."""
import base64, io, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dcsizing import scenario as S, __version__
from dcsizing.tables import SOURCES

HERE = os.path.dirname(os.path.abspath(__file__))
DOC, REV, DATE = "DWU-DC-E-CALC-002", "P1a", "2026-10-25"
r = S.run()
inp = S.Inputs()
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7.5})


def png(fig):
    b = io.BytesIO(); fig.savefig(b, format="png", dpi=200, bbox_inches="tight"); plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


# ---- charts
g = r["gen"]
rows = [("UPS (block)", r["ups"]["loading_normal"], r["ups"]["loading_failure"], 0.90),
        ("Block transformer", r["tx"]["loading_normal"], r["tx"]["loading_failure"], 1.0),
        ("IT genset (kWe)", g["load_normal_kw"] / g["kwe_site"], g["loading_kw"], 0.90),
        ("Mech transformer", r["mech"]["tx_loading_failure"] / 2, r["mech"]["tx_loading_failure"], 1.0),
        ("HV transformer", r["hv_loading"] / 2, r["hv_loading"], 1.0)]
fig, ax = plt.subplots(figsize=(3.6, 2.0))
y = range(len(rows))
ax.barh([i + 0.18 for i in y], [x[1] * 100 for x in rows], 0.36, color="#4c78a8", label="normal")
ax.barh([i - 0.18 for i in y], [x[2] * 100 for x in rows], 0.36, color="#e45756", label="failure / N-1")
for i, x in enumerate(rows):
    ax.plot([x[3] * 100] * 2, [i - 0.45, i + 0.45], color="k", lw=1.4)
ax.set_yticks(list(y)); ax.set_yticklabels([x[0] for x in rows]); ax.invert_yaxis()
ax.set_xlim(0, 110); ax.set_xlabel("loading, % of rating (black = limit)"); ax.legend(fontsize=6.5, loc="lower right")
ax.grid(axis="x", lw=0.3)
chart_load = png(fig)

bins = r["annual"]["bins"]
fig, ax = plt.subplots(figsize=(3.4, 2.0))
ax.bar([str(b["t_c"]) for b in bins], [b["hours"] for b in bins], color="#c6d3e3")
ax.set_ylabel("hours/yr"); ax.set_xlabel("outdoor bin centre, °C")
ax2 = ax.twinx(); ax2.plot([str(b["t_c"]) for b in bins], [b["pue"] for b in bins], "o-", color="#c8102e", ms=3)
ax2.set_ylabel("PUE"); ax.set_title(f"Annualised PUE {r['annual']['pue']:.3f} (75 % IT)", fontsize=7.5)
chart_pue = png(fig)


def f0(x): return f"{x:,.0f}".replace(",", "\u00a0")
def f1(x): return f"{x:,.1f}".replace(",", "\u00a0")
def pc(x): return f"{x*100:.1f} %"


def table(head, body, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in body)
    return f"<table class='{cls}'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


changes = [c for c in S.rating_changes(r) if c["change"]]
fails = [f for f in r["flags"] if not f["ok"]]
u, t, b, m, h = r["ups"], r["tx"], r["battery"], r["mech"], r["hall"]

# ---------------- page 1: summary
p1 = f"""
<h1>Calculation Report — Load & Equipment Sizing</h1>
<h2 class="sub">30 MW IT hyperscale campus, Dalarna (SE3), Sweden · fictional · reference case</h2>
{table(["Item", "Value"], [
    ["<b>Document</b>", f"{DOC}, Rev {REV} (concept; errata on sheet 4) — calculation tool <code>dcsizing</code> v{__version__} + Streamlit app"],
    ["<b>Basis</b>", "DWU-DC-E-DB-001 Rev P1 (design basis, now superseded by Rev P2); drawings SLD-001…003 Rev P1 (superseded by SLD-000…004 Rev P2)"],
    ["<b>Author / date</b>", f"Donglin (Franklin) Wu — portfolio project 02 · {DATE}"],
    ["<b>Status</b>", "Concept — <b>not for construction</b>. Public standards + values marked [ASSUMED]; no employer/vendor data"]], "meta")}
<h3>1. Reference case</h3>
<p>6 halls × 5 MW IT, distributed redundant <b>4N/3</b> (blocks A–D per hall), mechanical 2N; design ambient
+32 °C, altitude 150 m; mech. pPUE 0.17 (peak) / 0.05 (free cooling); UPS 1 000 kW modules, 5 min at EoL, 25 °C;
recharge 10 % (grid) / 5 % (on genset); HVO100 24 h; 130 kV S''k 3 000 MVA, 63 MVA uk 12 %; 2.5 MVA uk 6 %.</p>
<h3>2. Key results</h3>
{table(["Quantity", "Result", "Quantity", "Result"], [
    ["Block load normal / N-1", f"{f0(r['block']['normal'])} / {f0(r['block']['failure'])} kW", "Hall load (design peak)", f"{f0(h['total_kw'])} kW, pPUE {h['ppue']:.3f}"],
    ["UPS per block", f"{u['modules']} × 1 000 kW, {pc(u['loading_normal'])} / {pc(u['loading_failure'])}", "Hall max. incl. recharge", f"{f0(h['max_kw'])} kW → 20 kV {f0(r['mv_feeder_a'])} A"],
    ["Battery per module", f"{b['selected_kwh']} kWh (energy {f0(b['e_energy_kwh'])}, C-rate {f0(b['e_power_kwh'])})", "Campus demand", f"{f1(r['campus']['p_kw']/1000)} MW / {f1(r['campus']['s_kva']/1000)} MVA"],
    ["Block transformer", f"{t['kva']} kVA, {pc(t['loading_normal'])} / {pc(t['loading_failure'])}", "Design-peak PUE", f"{r['campus']['pue']:.3f}"],
    ["IT genset", f"{g['kva']} kVA / {g['kwe']:.0f} kWe, N-1 {pc(g['loading_kw'])}", "Annualised PUE", f"{r['annual']['pue']:.3f} ({f0(r['annual']['facility_mwh']/1000)} GWh/yr)"],
    ["MSB I''k / ip (IEC 60909)", f"{f1(r['sc']['ik_msb_ka'])} kA / {f0(r['sc']['ip_msb_ka'])} kA", "HV transformer N-1", f"{pc(r['hv_loading'])} of 63 MVA"],
    ["Mech. transformer / genset", f"{m['tx_kva']} kVA / {m['gen']['kva']} kVA", "20 kV I''k (one 63 MVA)", f"{f1(r['sc']['ik_mv_ka'])} kA"],
    ["Fuel per hall (24 h)", f"{f1(r['fuel']['tank_m3_hall'])} m³ gross", "Checks passed", f"{len(r['flags'])-len(fails)} / {len(r['flags'])}"]])}
<div class="charts"><img src="{chart_load}"/><img src="{chart_pue}"/></div>
<h3>3. Rating changes vs. phase 1 (to be carried into DB-001 Rev P2 and the SLDs)</h3>
{table(["#", "Item", "Phase 1", "Project 02", "Type", "Reason"],
       [[i, c["item"], c["phase1"], c["project02"], c["kind"], c["reason"]] for i, c in enumerate(changes, 1)], "small")}
"""

# ---------------- page 2: loads, UPS/battery, transformers, gensets
st = r["gen"]["steps"]
p2 = f"""
<h2>A. Load build-up (one hall, design peak +32 °C)</h2>
{table(["Component", "kW", "Basis"], [
    ["IT (critical)", f0(h['it_kw']), "5 MW per hall"],
    ["UPS losses", f0(h['ups_loss_kw']), f"η = {u['eff_normal']*100:.2f} % at {pc(u['loading_normal'])} load (VFI curve [ASSUMED])"],
    ["Mechanical", f0(h['mech_kw']), "pPUE 0.17 at 32 °C; 0.05 below 12 °C, linear [ASSUMED]"],
    ["Distribution losses", f0(h['dist_loss_kw']), "1.2 % (transformers + LV) [ASSUMED]"],
    ["House / lighting / BMS", f0(h['house_kw']), "[ASSUMED]"],
    ["<b>Hall total (PUE basis)</b>", f"<b>{f0(h['total_kw'])}</b>", f"pPUE {h['ppue']:.3f}"],
    ["Battery recharge (sizing only)", f0(h['recharge_kw']), "10 % × 4 × 2 000 kW, non-coincident"],
    ["Campus services + HV transformer losses", f0(r['campus']['p_kw'] - 6*h['total_kw']), "500 kW + 2 × (P0 + Pk·x²)"]], "small")}
<h2>B. Redundancy — block loading (4N/3 distributed redundant)</h2>
<p>Normal: P/n = 5 000/4 = <b>{f0(r['block']['normal'])} kW</b>. Failure (any one block out): P/(n−1) = <b>{f0(r['block']['failure'])} kW</b>.
Busway pair groups C(4,2) = 6; survivor current per run {f0(r['run_a'])} A (pf 0.98).</p>
<h2>C. UPS and LFP battery (IEC 62040-3 terms)</h2>
{table(["Check", "Formula / basis", "Value", "Result"], [
    ["Rated output P<sub>r</sub>", "N-1 load ≤ 90 % P<sub>r</sub> [ASSUMED policy]", f"{u['modules']} × 1 000 kW", f"{pc(u['loading_failure'])} ✓"],
    ["Stored-energy time t<sub>s</sub>", "E = P/η<sub>dc</sub>·t/(DoD·EoL·k<sub>T</sub>), η<sub>dc</sub> 0.97, DoD 0.9, EoL 0.8, k<sub>T</sub>(25 °C) 1.0", f"{f1(b['e_energy_kwh'])} kWh", "energy need"],
    ["Discharge power (C-rate)", "E ≥ P/η<sub>dc</sub>/(c<sub>max</sub>·EoL), c<sub>max</sub> 8C [ASSUMED high-power LFP]", f"{f1(b['e_power_kwh'])} kWh", "<b>governs</b>"],
    ["Phase-1 120 kWh check", "C-rate at EoL / autonomy", f"{b['c_rate_phase1']:.1f} C / {b['autonomy_min_phase1']:.1f} min", "✗ C-rate > 8C"],
    ["Selected", "rounded up to 5 kWh", f"{b['selected_kwh']} kWh / module", f"{b['autonomy_min_at_failure_load']:.1f} min at N-1 load"],
    ["Rectifier input current", "I = (P<sub>r</sub>/η + P<sub>rech</sub>)/(√3·400·0.99)", f"{f0(u['input_current_a'])} A", f"breaker {u['input_breaker_a']} A (was 1 600)"]], "small")}
<h2>D. Transformers (IEC 60076-11) and short circuit (IEC 60909-0)</h2>
{table(["Item", "Load normal / N-1", "Rating", "Loading", "Losses", "Notes"], [
    ["IT block T-A…D", f"{f0(t['s_normal_kva'])} / {f0(t['s_failure_kva'])} kVA", f"{t['kva']} kVA Dyn11 uk 6 %", f"{pc(t['loading_normal'])} / {pc(t['loading_failure'])}",
     f"{f1(t['losses_normal_kw'])} / {f1(t['losses_failure_kw'])} kW", f"P0 {t['p0_kw']} kW, Pk {t['pk_kw']} kW [ASSUMED Ecodesign T2 order]"],
    ["Mechanical (2N)", f"{f0(m['s_kva']/2)} / {f0(m['s_kva'])} kVA", f"{m['tx_kva']} kVA", f"{pc(m['tx_loading_failure']/2)} / {pc(m['tx_loading_failure'])}", "—", "phase 1: 1 600 kVA (growth margin)"],
    ["HV T1/T2", f"{f1(r['campus']['s_kva']/2000)} / {f1(r['campus']['s_kva']/1000)} MVA", "63 MVA (40 ONAN)", f"{pc(r['hv_loading']/2)} / {pc(r['hv_loading'])}", "—",
     f"N-1 = {f1(r['campus']['s_kva']/1000)} MVA ≤ 40 MVA ONAN"]], "small")}
<p class="small">I''k MV: Z<sub>Q</sub> = c·U²/S''<sub>kQ</sub> + Z<sub>T</sub>·K<sub>T</sub> → <b>{f1(r['sc']['ik_mv_ka'])} kA</b> at 20 kV (one 63 MVA unit, paralleling blocked) ⇒ S''k(20 kV) {f0(r['sc']['sk_mv_mva'])} MVA.
I''k LV MSB: c = 1.05, K<sub>T</sub> = 0.95·c<sub>max</sub>/(1+0.6x<sub>T</sub>) → <b>{f1(r['sc']['ik_msb_ka'])} kA</b>, κ = {r['sc']['ip_msb_ka']/r['sc']['ik_msb_ka']/1.4142:.2f} → ip {f0(r['sc']['ip_msb_ka'])} kA ⇒ MSB 65 kA/1 s, Ipk ≥ 143 kA.
Genset alone: {f1(r['sc']['ik_gen_ka'])} kA (x''d 0.15 [ASSUMED]).</p>
<h2>E. Generators (ISO 8528-1/-5, ISO 3046-1)</h2>
{table(["Item", "Load (kW)", "Selected", "Site derate", "Loading", "Step check", "Governed by"], [
    ["IT genset", f"{f0(g['load_failure_kw'])} (N-1, 5 % recharge)", f"{g['kva']} kVA / {g['kwe']:.0f} kWe DCC", f"{g['derate']:.3f}", pc(g['loading_kw']),
     f"UPS walk-in 8 × {f0(st[1]['kw'])} kW = {pc(st[1]['frac'])}, ΔU {pc(st[1]['du'])} ≤ 15 %", g['governed_by']],
    ["Mech genset", f"{f0(m['p_kw'])}", f"{m['gen']['kva']} kVA / {m['gen']['kwe']:.0f} kWe", f"{m['gen']['derate']:.3f}", pc(m['gen']['loading_kw']),
     f"chiller 400 kW = {pc(m['gen']['steps'][0]['frac'])} ≤ 33 %", m['gen']['governed_by']]], "small")}
<p class="small">Derating 1.5 %/K above 40 °C and 1 %/100 m above 1 000 m [ASSUMED]. HVO100 (EN 15940) SFC 0.26–0.33 l/kWh [ASSUMED].
Fuel per hall: 4 IT gensets at normal share ({f0(g['load_normal_kw'])} kW) + 2 mech. gensets at 50 % → {f0(r['fuel']['lph_hall'])} l/h ×
24 h / 0.90 usable = <b>{f1(r['fuel']['tank_m3_hall'])} m³</b>.</p>
"""

# ---------------- page 3: cables, busway, PUE, checks
cab_rows = []
for c in r["cables"]:
    x, k = c["result"], c["inputs"]
    cab_rows.append([c["tag"], c["circuit"], f0(x.ib_a), f0(x.in_a), x.method.replace("_", " "), k["length_m"], k["ambient_c"],
                     f"{x.k_amb:.2f} × {x.k_grp:.2f}", x.label(), f0(x.iz_a), f"{x.vd_pct:.2f}", f"{k['ik_ka']:.0f} kA/{k['t_clear_s']} s → {f0(x.s_min_sc_mm2)}"])
bw, bt = r["busway_ws"], r["busway_tx"]
p3 = f"""
<h2>F. LV cables — IEC 60364-5-52 / IEC 60364-4-43</h2>
<p class="small">Criteria: I<sub>b</sub> ≤ I<sub>n</sub> ≤ I<sub>z</sub> = n·I<sub>0</sub>·k<sub>amb</sub>·k<sub>grp</sub>; ΔU = √3·I·L·(R cosφ + X sinφ)/n with R(90 °C) from IEC 60228 Table 2, X 0.08 Ω/km;
S ≥ I''k·√t/k (k = 143 Cu/XLPE, 94 Al/XLPE, Table 43A; full I''k on one conductor — conservative). I<sub>0</sub>: Table B.52.12 (method F trefoil, E multicore, XLPE 90 °C);
k<sub>amb</sub>: B.52.14; k<sub>grp</sub>: B.52.21 (trefoil, tray) / B.52.17 item 4. Fewest parallel runs, sections ≤ 240 mm².</p>
{table(["Tag", "Circuit", "I<sub>b</sub> A", "I<sub>n</sub> A", "Method", "L m", "θ °C", "k<sub>a</sub>×k<sub>g</sub>", "Selected", "I<sub>z</sub> A", "ΔU %", "SC → S<sub>min</sub> mm²"], cab_rows, "tiny")}
<p class="small">C2 and C3 need 7–8 parallel runs of 240 mm² → <b>use 3 200 A / 4 000 A busbar trunking</b> for MSB→SBS and genset→MSB.</p>
<h2>G. Busbar trunking — IEC 61439-6</h2>
{table(["Run", "I<sub>b</sub> A", "Rating", "k<sub>amb</sub>", "Loading", "ΔU %", "I<sub>cw</sub> vs I''k", "Result"], [
    ["White-space run, 60 m, distributed (×0.5), 40 °C", f0(r['run_a']), f"{bw['rating_a']} A", f"{bw['k_amb']:.2f}", pc(bw['loading']), f"{bw['vd_pct']:.2f}",
     f"{bw['icw_ka']} kA &lt; {f1(r['sc']['ik_msb_ka'])} kA", "✗ needs current-limiting MCCB (conditional Icc)"],
    ["Transformer → MSB, 10 m, 35 °C", f0(t['i_rated_a']), f"{bt['rating_a']} A", f"{bt['k_amb']:.2f}", pc(bt['loading']), f"{bt['vd_pct']:.2f}",
     f"{bt['icw_ka']} kA ≥ {f1(r['sc']['ik_msb_ka'])} kA", "✓"]], "small")}
<h2>H. Annualised PUE (EN 50600-4-2), Dalarna temperature bins [ASSUMED]</h2>
{table(["Bin °C"] + [str(x['t_c']) for x in bins] + ["Year"],
       [["Hours"] + [x['hours'] for x in bins] + [r['annual']['hours']],
        ["PUE"] + [f"{x['pue']:.3f}" for x in bins] + [f"<b>{r['annual']['pue']:.3f}</b>"]], "tiny")}
<p class="small">At 75 % IT the fixed loads (house, campus services, UPS part-load losses, transformer no-load) push the annual PUE to
{r['annual']['pue']:.3f} &gt; 1.15 target. Meeting 1.15 needs a free-cooling mechanical pPUE ≈ 0.035 (EC fans, higher water temperatures) or lower fixed loads/UPS eco-mode.</p>
<h2>I. Failed checks (reference case)</h2>
{table(["Check", "Value", "Limit", "Note"], [[f['item'], "—" if f['value'] is None else f"{f['value']:.3f}", "—" if f['limit'] is None else f"{f['limit']:.3f}", f['note']] for f in fails], "small")}
<h2>J. Standards</h2><p class="tiny2">{' · '.join(f'<b>{k}</b> {v}' for k, v in SOURCES.items())}</p>
"""

css = """
.errata{border:1pt solid #c8102e;background:#fbf3f3;padding:3pt 6pt;margin:4pt 0 6pt 0;font-size:7.6pt}
@page { size: A4; margin: 10mm 13mm 9mm 13mm; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 8.2pt; line-height: 1.32; color: #111; }
h1 { font-size: 15pt; color: #1f3b73; margin: 0 0 2pt 0; }
h2 { font-size: 10pt; color: #1f3b73; border-bottom: 1.1pt solid #1f3b73; padding-bottom: 1.5pt; margin: 8pt 0 3pt 0; }
h2.sub { border: none; font-size: 9.5pt; color: #444; margin-top: 0; }
h3 { font-size: 9pt; color: #1f3b73; margin: 7pt 0 2pt 0; }
p { margin: 2pt 0 4pt 0; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 5pt 0; font-size: 7.5pt; page-break-inside: avoid; }
th, td { border: 0.5pt solid #9aa5b8; padding: 1.8pt 3.5pt; vertical-align: top; text-align: left; }
th { background: #e9eef5; }
table.small { font-size: 7pt; } table.tiny { font-size: 6.4pt; } table.meta td { padding: 1.2pt 3.5pt; }
.small { font-size: 7.2pt; } .tiny2 { font-size: 6.2pt; color: #333; }
.charts { display: flex; justify-content: space-between; } .charts img { width: 49%; }
.page { height: 275mm; position: relative; overflow: hidden; page-break-after: always; box-sizing: border-box; padding-bottom: 19mm; }
.page:last-child { page-break-after: auto; }
code { font-size: 7.5pt; }
.tb { position: absolute; bottom: 0; left: 0; right: 0; box-sizing: border-box; height: 16mm; border: 0.8pt solid #1f3b73; display: flex; font-size: 6.6pt; }
.tb div { border-right: 0.5pt solid #1f3b73; padding: 1.5pt 4pt; } .tb div:last-child { border-right: none; }
.tb b { color: #1f3b73; font-size: 7.6pt; } .tb .lbl { color: #777; font-size: 5.6pt; display: block; }
"""
def tb(n): return f"""<div class="tb">
<div style="flex:2.3"><span class="lbl">PROJECT</span><b>D. Wu — Portfolio</b><br>30 MW IT DC campus, Dalarna SE3 (fictional)</div>
<div style="flex:2.9"><span class="lbl">TITLE</span><b>Load &amp; equipment sizing — calculation report</b><br>Concept — not for construction</div>
<div style="flex:1.9"><span class="lbl">DOCUMENT NO.</span><b>{DOC}</b></div>
<div style="flex:0.5"><span class="lbl">REV</span><b>{REV}</b></div>
<div style="flex:0.9"><span class="lbl">DATE</span>{DATE}</div>
<div style="flex:0.8"><span class="lbl">SHEET</span>{n} of 4 (A4)</div></div>"""
# ------------------------------------------------------------------ errata page (Rev P1a)
pE = f"""
<h2>Revision history and errata</h2>
{table(["Rev", "Date", "Description"], [["P1", "2026-10-24", "First issue"], ["P1a", "2026-10-25", "Errata only: cross-references to DB-001 Rev P2 / SLD Rev P2; superseded statements listed below. No calculation result changed."]], "meta")}
<div class="errata"><b>Errata / superseded items (Rev P1a, 2026-10-25).</b> Calculation results are unchanged. (1) The busway feeder requirement
"current-limiting MCCB, I<sub>cc</sub> ≥ 55 kA" in the rating-change list (B3) is <b>superseded by CALC-003 / TODO B15</b>: MCCB I<sub>cu</sub> ≥ 50 kA, current-limiting,
with a tested busway conditional rating ≥ 40 kA (UOSB 49.3 kA, busway start 37.1 kA). (2) All rating changes B1–B11 are implemented in
<b>DB-001 Rev P2</b> and <b>SLD Rev P2</b>; block transformer P<sub>k</sub> 19 kW is now the single value in DB-001. (3) The 42.6 MW campus maximum incl. recharge is
handled in DB-001 Rev P2 §5.2 (staggered recharge ≤ 2.2 MW, BESS, CALC-004).</div>
"""

html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"
        f"<div class='page'>{p1}{tb(1)}</div><div class='page'>{p2}{tb(2)}</div><div class='page'>{p3}{tb(3)}</div><div class='page'>{pE}{tb(4)}</div></body></html>")
hp = os.path.join(HERE, f"{DOC}_calc_report.html")
open(hp, "w", encoding="utf-8").write(html)
pdf = os.path.join(HERE, f"{DOC}_Load_and_Sizing_Calc.pdf")
subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + hp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("built", pdf)
