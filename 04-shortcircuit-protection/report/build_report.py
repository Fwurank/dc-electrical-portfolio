"""Build DWU-DC-E-CALC-003 (A4 PDF): short-circuit, protection coordination and arc-flash study.
HTML → headless Chrome PDF, same pipeline/style as DWU-DC-E-CALC-002.  Run scripts/make_all.py first."""
import base64, math, os, subprocess, sys, warnings
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
warnings.filterwarnings("ignore")
from scprot import study as S, campus as C, __version__

HERE = os.path.join(ROOT, "report")
FIG = os.path.join(ROOT, "figures")
DOC, REV, DATE, NPAGES = "DWU-DC-E-CALC-003", "P1a", "2026-10-25", 6
r = S.run()
R, dv = r["R"], r["devices"]
f0 = lambda x: f"{x:,.0f}".replace(",", "\u00a0")
f1 = lambda x: f"{x:,.1f}".replace(",", "\u00a0")
f2 = lambda x: f"{x:.2f}"


def img(name, width="100%"):
    b = base64.b64encode(open(os.path.join(FIG, name), "rb").read()).decode()
    return f"<img src='data:image/png;base64,{b}' style='width:{width}; display:block; margin:2pt auto'/>"


def table(head, body, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in body)
    return f"<table class='{cls}'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


ok = lambda b: "✓" if b else "<b class='bad'>✗</b>"
g = lambda k, n: R[k]["faults"][n]

# ------------------------------------------------------------------ page 1
sc_rows = []
for n in C.FAULT_NODES:
    a = g("S0max", n)
    cells = [C.NODE_LABEL[n], f1(a["ik_ka"]), f1(a["ip_ka"]), f1(a["ib_ka"]), f1(a["ith_ka"]), f2(a["kappa"]),
             f1(g("S0min", n)["ik_ka"])]
    for k in ("S1", "S3", "S4", "S5b"):
        v = g(k, n)["ik_ka"]
        cells.append(f1(v) if v > 0 else "—")
    sc_rows.append(cells)
s1 = g("S1", "MV-A"); s3 = g("S3", "MSB-A")
sens = {x["sk_mva"]: x for x in r["s1_sens"]}
p1 = f"""
<h1>Short-circuit, Protection Coordination &amp; Arc-flash Study</h1>
<h2 class="sub">30 MW IT hyperscale campus, Dalarna (SE3), Sweden · fictional · conceptual study</h2>
{table(["Item", "Value"], [
    ["<b>Document</b>", f"{DOC}, Rev {REV} (concept; errata on sheet 6) — Python package <code>scprot</code> v{__version__} (own IEC 60909 solver + pandapower cross-check)"],
    ["<b>Basis</b>", "DWU-DC-E-DB-001 Rev P1 §7–8, SLD-001…003 (both superseded by Rev P2); DWU-DC-E-CALC-002 (dcsizing) incl. rating changes B1–B11"],
    ["<b>Author / date</b>", f"Donglin (Franklin) Wu — portfolio project 04 · {DATE}"],
    ["<b>Status</b>", "Concept — <b>not for construction</b>. Public standards, generic device curves, values [ASSUMED]; no employer/vendor data"]], "meta")}
<h3>1. Scope and method</h3>
<p class="small">IEC 60909-0:2016 equivalent-voltage-source method on a nodal model 130 kV grid → T1/T2 63 MVA → MSG-20 → 0.6 km hall feeders →
HV-DH1 → 2.5 MVA block transformers → MSB → SBS/UOSB (bypass) → 800 A busway → rack PDU; genset 2 750 kVA on MSB-A. K<sub>T</sub>/K<sub>G</sub>,
c<sub>max</sub> 1.10/1.05, c<sub>min</sub> 1.00/0.95, conductor θ<sub>e</sub> 80 °C for I<sub>k min</sub>; i<sub>p</sub> method C, I<sub>b</sub> with μ, I<sub>th</sub> with m+n (T<sub>k</sub> 1 s).
Cross-check: pandapower 3.5 <code>calc_sc</code> — max case identical (Δ 0.00 %), min case 2–4 % lower (pandapower omits K<sub>T</sub> for I<sub>k min</sub>; lower value used for sensitivity).
With MV cables/busduct omitted the solver reproduces the CALC-002 hand values exactly (53.8 kA LV, 13.0 kA 20 kV).
Protection: IEC 60255-151 relays; <b>generic</b> IEC 60947-2-style LSI and IEC 60898-1 C-curve bands. Arc flash: IEEE 1584-2018 (arcflash-calc, validated against Annex D.1/D.2 in pytest);
20 kV outside the 15 kV model range → Lee method.</p>
<h3>2. Findings</h3>
<ul class="small">
<li><b>Normal (S0)</b>: MSG-20 {f1(g('S0max','MV-A')['ik_ka'])} kA, MSB-A {f1(g('S0max','MSB-A')['ik_ka'])} kA / i<sub>p</sub> {f0(g('S0max','MSB-A')['ip_ka'])} kA — within 25 kA and 65 kA/143 kA. N-1 cases (S2 T2 out, S5 block/feeder out) give the same levels.</li>
<li><b>T1//T2 (S1) stays interlocked</b>: {f1(s1['ik_ka'])} kA is inside 25 kA but i<sub>p</sub> {f1(s1['ip_ka'])} kA = {s1['ip_ka']/62.5*100:.0f} % of 62.5 kA and the asymmetrical breaking duty (τ ≈ 61 ms &gt; 45 ms) is ≈ 95 % of rating;
at S''<sub>kQ</sub> 4 000 MVA i<sub>p</sub> = {f1(sens[4000]['ip_s1'])} kA <b>exceeds</b> the making rating. Also: R-TX CT saturation, loss of section selectivity, OLTC circulating current.
The hall-board coupler closed with both feeders (S5b) parallels T1/T2 too ({f1(g('S5b','MV-A')['ik_ka'])} kA) → interlock.</li>
<li><b>LV closed-transition retransfer (S3) not permitted</b>: grid + genset on MSB-A = {f1(s3['ik_ka'])} kA / i<sub>p</sub> {f0(s3['ip_ka'])} kA &gt; 65 / 143 kA. Keep open transition.</li>
<li><b>Busway</b>: {f1(g('S0max','BW-A1-0')['ik_ka'])} kA at the busway start &gt; I<sub>cw</sub> 36 kA → current-limiting MCCB with tested conditional rating (confirms B3). Tap-off 63 A devices see {f1(g('S0max','BW-A1-END')['ik_ka'])} kA, rack inlet {f1(g('S0max','RACK')['ik_ka'])} kA.</li>
<li><b>Genset island (S4)</b>: {f1(g('S4','MSB-A')['ik_ka'])} kA initial, ≈ {f1(r['genset']['sustained_ka'])} kA sustained → genset ACB I<sub>sd</sub> 2.5×I<sub>r</sub>, SBS ACB I<sub>sd</sub> 7.25 kA; all devices still trip. UPS on inverter (≈ {f1(r['ups']['ik_inverter_ka'])} kA): rack MCB trips magnetically.</li>
<li><b>Arc flash</b>: MSB line side (cleared by the 20 kV relay) ≈ 96 cal/cm² → optical arc relay with MV intertrip cuts it to ≈ 3 cal/cm²; MSB bus 16.8 → 2.4–4.8 cal/cm² with maintenance mode / ZSI.</li>
<li><b>MV earthing</b>: compensated earthing keeps I<sub>F</sub> ≈ {f1(r['earthing']['compensated']['if_a'])} A (EPR ≈ 1 V) and detects R<sub>F</sub> up to ≈ {f0(r['earthing']['compensated']['rf_detect_ohm']/1000)} kΩ; the 130 kV earth fault governs the earthing design.</li>
</ul>
<h3>3. Short-circuit results (IEC 60909-0, kA)</h3>
{table(["Bus", "S0 I''k max", "i<sub>p</sub>", "I<sub>b</sub>", "I<sub>th</sub> 1 s", "κ", "S0 I''k min", "S1 T1//T2", "S3 closed trans.", "S4 genset", "S5b hall cpl."], sc_rows, "small num")}
<p class="tiny2">S0 = one 63 MVA transformer per 20 kV section, couplers open (also covers N-1 T2 out with coupler closed); min = S''<sub>kQ</sub> 1 500 MVA, c<sub>min</sub>, θ<sub>e</sub> 80 °C.
UOSB/busway/rack values with UPS on static bypass (worst case). Full table incl. S2/S4min/S5: <code>results/short_circuit.csv</code>; pandapower comparison: <code>results/pandapower_crosscheck.csv</code>.</p>
"""

# ------------------------------------------------------------------ page 2
mv = [dv[k] for k in ("rin", "rfd", "rtx")]
m = dv["margins_mv"]
ct_rows = [[c["CT"], c["Ratio"], c["Class"], c["Rct+Rb (Ω)"], c["ALF'"], c["ALF' needed"], f1(c["Ik max (kA)"]), c["Ith CT 1s (kA)"],
            ok(c["OK"]), ok(c["OK if T1//T2"])] for c in r["ct"]]
e, ec = r["earthing"], r["earthing_coupler"]
p2 = f"""
<h2>4. 20 kV protection coordination</h2>
{img("fig2_tcc_mv.png", "74%")}
{table(["Relay", "CT", "51: I<sub>s</sub> A (×I<sub>n,CT</sub>)", "Curve / TMS", "50: I&gt;&gt; A / t s", "Grades with", "Min. margin"], [
    [mv[0].name, f"{mv[0].ct_pri:.0f}/1", f"{mv[0].is51:.0f} ({mv[0].is51/mv[0].ct_pri:.2f})", f"IEC SI / {mv[0].tms}", f"{mv[0].i50:.0f} / {mv[0].t50}", "R-FDR", f"{m['R-INC vs R-FDR']['min_margin_s']:.2f} s"],
    [mv[1].name, f"{mv[1].ct_pri:.0f}/1", f"{mv[1].is51:.0f} ({mv[1].is51/mv[1].ct_pri:.2f})", f"IEC VI / {mv[1].tms}", f"{mv[1].i50:.0f} / {mv[1].t50}", "R-TX", f"{m['R-FDR vs R-TX']['min_margin_s']:.2f} s"],
    [mv[2].name, f"{mv[2].ct_pri:.0f}/1", f"{mv[2].is51:.0f} ({mv[2].is51/mv[2].ct_pri:.2f})", f"IEC EI / {mv[2].tms}", f"{mv[2].i50:.0f} / {mv[2].t50}", "MSB incomer ACB", f"{m['R-TX vs MSB incomer']['min_margin_s']:.2f} s"]], "small")}
<p class="tiny2">TMS chosen as the smallest value giving ≥ 0.30 s over the full current range up to the maximum through-fault (S0). R-FDR I<sub>s</sub> = 1.5 × N-1 feeder load (214 A);
R-INC I<sub>s</sub> = 1.2 × T1 rated current (1 732 A at 21 kV). R-TX: I&gt;&gt; 1 500 A above inrush (866 A) and the LV through-fault (1.10 kA); clears the 2-s withstand current (1 203 A) in
{float(dv['rtx'].clear(1203)):.2f} s. Incomer I&gt;&gt; 0.65 s can be reduced to ≈ 0.1 s by reverse blocking from feeder starts.</p>
<h3>CT check (5P20, 1 A secondary, ALF' = ALF·(R<sub>ct</sub>+R<sub>b,n</sub>)/(R<sub>ct</sub>+R<sub>b</sub>), 2 × 20 m 2.5 mm² leads)</h3>
{table(["CT", "Ratio", "Class", "R<sub>ct</sub>+R<sub>b</sub> Ω", "ALF'", "ALF' needed", "I''k max kA", "I<sub>th</sub> CT kA", "S0", "if T1//T2"], ct_rows, "small num")}
<p class="tiny2">ALF' needed = max(I''k max/I<sub>pn</sub>, 2·I&gt;&gt;/I<sub>pn</sub>). R-TX 150/1 needs a thermal rating ≥ 25 kA 1 s (≈ 167 × I<sub>pn</sub>) — specify; it would saturate if T1//T2 were allowed.</p>
<h3>5. 20 kV neutral earthing — compensated vs low-resistance (conceptual)</h3>
{table(["", "Compensated (Petersen coil + 10 A parallel R)", "Low-resistance (NER 500 A, 10 s)"], [
    ["Earth-fault current", f"I<sub>C</sub> {f1(e['ic_a'])} A per section ({f1(ec['ic_a'])} A coupled); residual |I<sub>C</sub>−I<sub>L</sub>| + I<sub>R</sub> ≈ <b>{f1(e['compensated']['if_a'])} A</b>",
     f"≈ <b>{f0(e['low_resistance']['if_a'])} A</b> (R<sub>N</sub> {f1(e['low_resistance']['rn_ohm'])} Ω via zig-zag)"],
    ["Protection", "67N admittance / transient (Y0&gt;), feeders 1.0 s; 59N U0&gt; backup 3 s", "51N feeders 50 A / 0.3 s DT; incomer/NER 51N 50 A / 0.6 s"],
    ["High-resistance fault detected", f"R<sub>F</sub> ≲ {f0(e['compensated']['rf_detect_ohm']/1000)} kΩ (U0 ≥ 10 %)", f"R<sub>F</sub> ≲ {f0(e['low_resistance']['rf_detect_ohm'])} Ω (I0 ≥ 50 A)"],
    ["EPR = r·I<sub>F</sub>·R<sub>E</sub> (r 0.6, R<sub>E</sub> 0.2 Ω)", f"{f1(e['compensated']['epr_v'])} V ≪ 2·U<sub>Tp</sub>(10 s) = {f0(e['compensated']['two_utp_v'])} V", f"{f0(e['low_resistance']['epr_v'])} V &lt; 2·U<sub>Tp</sub>(0.5 s) = {f0(e['low_resistance']['two_utp_v'])} V"],
    ["Assessment", "Arc self-extinguishes, low EPR and cable-screen stress; Swedish practice. Coil ≥ 50 A adjustable (both sections coupled ≈ 48 A).", "Simple, fast and selective, but 500 A arcs damage cables/switchgear and every fault trips a feeder."]], "small")}
<p class="tiny2">Touch voltage screened with the EN 50522 simplified criterion EPR ≤ 2·U<sub>Tp</sub> (U<sub>Tp</sub> per EN 50522 Fig. 4: 220 V at 0.5 s, 85 V at ≥ 10 s). The 130 kV earth fault governs
(I<sub>k1</sub> 8 kA [ASSUMED], r 0.5): EPR ≈ 800 V — OK for 0.1 s main protection (2·U<sub>Tp</sub> 1 308 V) but not for 0.5 s back-up (440 V) → detailed earthing design with DSO data (SS-EN 61936-1, EN 50522, ELSÄK-FS 2022:1).</p>
"""

# ------------------------------------------------------------------ page 3
lv = [dv[k] for k in ("inc", "sbs", "bw", "gen")]
sel_rows = [[x["downstream"].split(" (")[0], x["upstream"].split(" (")[0], f1(x["ik_max_ka"]),
             ("current-selective to " + f1(x["current_limit_ka"]) + " kA; above → manufacturer energy-selectivity tables") if x["current_limit_ka"] and not x["selective"]
             else f"time-selective, min. band gap {x['min_margin_s']:.2f} s"] for x in r["lv_sel"]]
gen_rows = [[x["device"].split(" (")[0], x["fault_at"], f1(x["ik_initial_ka"]), f1(x["i_at_trip_ka"]), f1(x["pickup_ka"]), ok(x["trips"])] for x in r["genset"]["rows"]]
rat = [[x["item"], x["case"], x["rating"], f1(x["value_ka"]), f"{x['util']*100:.0f} %", ok(x["ok"]), x["note"]] for x in r["ratings"]]
p3 = f"""
<h2>6. 400 V protection coordination</h2>
{img("fig3_tcc_lv.png", "84%")}
{table(["Device (generic trip unit)", "I<sub>r</sub> A", "t<sub>r</sub> @6I<sub>r</sub>", "I<sub>sd</sub> A / t<sub>sd</sub> s", "I<sub>i</sub> A", "I<sub>cu</sub>/I<sub>cw</sub> kA", "Notes"], [
    [lv[0].name, f0(lv[0].ir), f"{lv[0].tr:g} s", f"{f0(lv[0].isd)} / {lv[0].tsd}", "OFF", "65/65", "ZSI to downstream ACBs; maintenance (ARMS) switch"],
    [lv[1].name, f0(lv[1].ir), f"{lv[1].tr:g} s", f"{f0(lv[1].isd)} / {lv[1].tsd}", "OFF", "65/65", "I<sub>sd</sub> ≤ genset sustained current"],
    [lv[2].name, f0(lv[2].ir), f"{lv[2].tr:g} s", f"{f0(lv[2].isd)} / {lv[2].tsd}", f0(lv[2].ii), "≥ 50 (I<sub>cu</sub>)", "current-limiting; tested with busway"],
    [lv[3].name, f0(lv[3].ir), f"{lv[3].tr:g} s", f"{f0(lv[3].isd)} / {lv[3].tsd}", "OFF", "65/65", "plus 51V / 32 / 40 generator protection"],
    ["Rack-group / tap-off 63 A", "63", "C-curve", "magnetic 5–10 I<sub>n</sub>", "—", "≥ 25 (see §8)", "IEC 60898-1 band"]], "small")}
{table(["Downstream", "Upstream", "I''k max kA", "Selectivity (grid supply, S0)"], sel_rows, "small")}
"""

# ------------------------------------------------------------------ page 4
arc_rows = [[x["location"].replace(" (load side of incomer)","").replace(" (on bypass)",""), x["case"], x["method"].split(" (")[0].replace("IEEE 1584-2018","IEEE 1584"), f1(x["ibf_ka"]), f1(x["iarc_ka"]), f"{x['t_s']:.3f}", f1(x["e_cal"]),
             f"{x['afb_mm']/1000:.2f}", x["ppe"].replace(" — DANGER, no live work"," DANGER")] for x in r["arc"]]
changes = [
    ["B12", "MSG-20 T1//T2 and coupler make-before-break", "interlocked (DB)", "Confirmed: keep interlock; coupler auto-close only after incomer open (break-before-make)", "S1 i<sub>p</sub> 94 % of 62.5 kA; &gt; 100 % at 4 000 MVA"],
    ["B13", "HV-DH1 hall coupler", "N.O.", "Interlock: close only with one hall feeder open", "S5b parallels T1/T2 (20.9 kA)"],
    ["B14", "Genset retransfer", "closed transition 'to be reconsidered'", "<b>Open transition only</b>", "S3 81.8 kA / 187 kA &gt; 65 / 143 kA"],
    ["B15", "Busway feeder MCCB (B3)", "Icc ≥ 55 kA", "I<sub>cu</sub> ≥ 50 kA, current-limiting, conditional busway rating ≥ 40 kA (tested combination)", "37.1 kA at busway start &gt; 36 kA"],
    ["B16", "Tap-off 63 A devices / rack PDU", "MCB (n/a)", "63 A MCCB I<sub>cu</sub> ≥ 36 kA or tested cascade; PDU conditional SCCR ≥ 15 kA", "25.1 kA busway end, 14.0 kA rack"],
    ["B17", "MSB/UOSB arc-flash mitigation", "—", "Optical arc relays + MV VCB intertrip; ZSI; maintenance (ARMS) switch", "96 → 3.2 cal/cm² line side"],
    ["B18", "MSG-20 / HV-DH1", "IAC AFLR 25 kA", "Add optical arc protection + reverse-blocking busbar protection", "Lee 106 → 11 cal/cm²"],
    ["B19", "LV trip-unit settings", "LSIG (generic)", "Table §6; genset ACB I<sub>sd</sub> ≤ 2.5 I<sub>r</sub>; genset sustained ≥ 300 % / 2 s in spec", "genset island sensitivity"],
    ["B20", "20 kV CTs", "—", "R-INC 2 500/1, R-FDR 400/1, R-TX 150/1 5P20 with I<sub>th</sub> ≥ 25 kA 1 s", "CT check §4"],
    ["B21", "Petersen coil", "per section", "≥ 50 A adjustable + 10 A parallel resistor; 67N admittance", "I<sub>C</sub> 22 / 44 A"]]
p4 = f"""
<h2>7. Source-limited cases — genset island (S4 min) and UPS inverter</h2>
{img("fig4_tcc_genset.png", "76%")}
{table(["Device", "Fault at", "I''k initial kA", "I at t<sub>sd</sub> kA", "Pick-up (+10 %) kA", "Trips"], gen_rows, "small num")}
<p class="tiny2">Genset decrement: x''<sub>d</sub> 0.15, x'<sub>d</sub> 0.22, T''<sub>d</sub> 15 ms, T'<sub>d</sub> 150 ms, sustained 300 % (PMG/AREP support) [ASSUMED]. UPS inverter ≈ 2 × I<sub>n</sub> for 100 ms [ASSUMED]:
rack MCB clears in 10 ms; a busway fault needs 0.13 s via the 800 A MCCB → UPS transfers to bypass to clear it. Min. L-PE fault at rack PDU (TN-S, c<sub>min</sub>, 80 °C):
{f1(r['ik1_rack'][0]['ik1_ka'])} kA grid / {f1(r['ik1_rack'][1]['ik1_ka'])} kA genset ≫ 630 A (10 × I<sub>n</sub>) → disconnection within 0.4 s (IEC 60364-4-41).</p>
<h2>8. Arc flash (conceptual — IEEE 1584-2018 / Lee)</h2>
{table(["Location", "Case", "Method", "I<sub>bf</sub> kA", "I<sub>arc</sub> kA", "t s", "E cal/cm²", "AFB m", "Arc rating"], arc_rows, "tiny arc")}

"""
p5 = f"""
<h3>8. Arc flash (cont.) — base design vs mitigation</h3>
{img("fig5_arcflash.png", "80%")}
<p class="tiny2">LV: VCB, gap 32 mm, D 610 mm, 508 mm cube (switchgear); 25 mm / 457 mm / shallow panel (tap-off). Worst of full / reduced (VarCF) arcing current, clearing time read from the device band at each.
Arc duration capped at 2 s. MV: Lee method (open-air theoretical maximum, D 910 mm) — conservative; IAC-tested switchgear protects front-access operators with doors closed.
Arc rating labels follow NFPA 70E categories (4/8/25/40 cal/cm²); IEC 61482-2 APC classes are box-test based and must be selected separately.</p>
<h2>9. Conclusions and required design changes (→ TODO_final_fixes.md B12–B21, DB-001 Rev P2)</h2>
{table(["#", "Item", "Phase 1–2", "Project 04", "Reason"], changes, "tiny")}
<p class="small"><b>Ratings check.</b> {sum(1 for x in r['ratings'] if x['ok'])}/{len(r['ratings'])} pass; failures: {', '.join(f"{x['item']} {x['rating']} ({x['case'].split(' (')[0]})" for x in r['ratings'] if not x['ok'])}.
MSB 65 kA/143 kA and 20 kV 25 kA ratings stand (full model 52.3 kA vs 53.8 kA hand value; 13.0 kA confirmed).</p>
<p class="tiny2"><b>Limitations.</b> Generic LV curves (no manufacturer selectivity/cascade tables); assumed grid, cable, genset,
UPS and earthing data; no motor/VFD/BESS fault contribution (BESS inverters ≈ 1.2 × I<sub>n</sub> would add &lt; 0.5 kA at 20 kV); IEEE 1584 not valid at 20 kV;
touch voltage only screened (no soil model). Code: <code>scripts/make_all.py</code> regenerates all figures/results; 23 pytest tests.</p>
<h3>Fig. 1 — Initial short-circuit current per bus and scenario vs equipment ratings (§3)</h3>
{img("fig1_ik_levels.png", "58%")}

"""

css = open(os.path.join(ROOT, "..", "03-load-sizing", "report", "build_report.py")).read().split('css = """')[1].split('"""')[0]
css += """ ul { margin: 1pt 0 3pt 14pt; padding: 0; } li { margin: 0 0 1.5pt 0; }
table.num td { text-align: right; } table.num td:first-child { text-align: left; } .bad { color: #c00000; } table.arc td { text-align: right; white-space: nowrap; } table.arc td:nth-child(-n+3) { text-align: left; } table.arc td:nth-child(2){white-space: normal;}"""


def tb(n): return f"""<div class="tb">
<div style="flex:2.3"><span class="lbl">PROJECT</span><b>D. Wu — Portfolio</b><br>30 MW IT DC campus, Dalarna SE3 (fictional)</div>
<div style="flex:2.9"><span class="lbl">TITLE</span><b>Short-circuit, protection &amp; arc-flash study</b><br>Concept — not for construction</div>
<div style="flex:1.9"><span class="lbl">DOCUMENT NO.</span><b>{DOC}</b></div>
<div style="flex:0.5"><span class="lbl">REV</span><b>{REV}</b></div>
<div style="flex:0.9"><span class="lbl">DATE</span>{DATE}</div>
<div style="flex:0.8"><span class="lbl">SHEET</span>{n} of {NPAGES} (A4)</div></div>"""


# ------------------------------------------------------------------ errata page (Rev P1a)
pE = f"""
<h2>Revision history and errata</h2>
{table(["Rev", "Date", "Description"], [["P1", "2026-10-24", "First issue"], ["P1a", "2026-10-25", "Errata only: cross-references to DB-001 Rev P2 / SLD Rev P2; superseded statements listed below. No calculation result changed."]], "meta")}
<div class="errata"><b>Errata / superseded items (Rev P1a, 2026-10-25).</b> Calculation results are unchanged. (1) "No BESS fault contribution" (limitations, §9) is
<b>superseded by CALC-004</b>: with the 10 MW BESS (PCS limit 1.2 × I<sub>n</sub>) MSG-20 I″<sub>k</sub> is <b>13.3 kA</b>, worst case <b>23.1 kA (92 % of 25 kA)</b>; earth-fault I<sub>c</sub> +≈1 A.
(2) Changes B12–B21 are implemented in <b>DB-001 Rev P2</b> §7 and <b>SLD Rev P2</b> (relays and CTs on SLD-001 sh 1–2, LV trip settings and arc mitigation on SLD-003 sh 1–2).</div>
"""

pages = [p1, p2, p3, p4, p5, pE]
html = ("<!doctype html><html><head><meta charset='utf-8'><style>" + css + "</style></head><body>"
        + "".join(f"<div class='page'>{p}{tb(i)}</div>" for i, p in enumerate(pages, 1)) + "</body></html>")
hp = os.path.join(HERE, f"{DOC}_report.html")
open(hp, "w").write(html)
pdf = os.path.join(HERE, f"{DOC}_ShortCircuit_Protection_ArcFlash.pdf")
subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + hp], check=True, capture_output=True)
print(pdf)
