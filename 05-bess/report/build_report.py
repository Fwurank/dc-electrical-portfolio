"""Build DWU-DC-E-CALC-004 (A4 PDF): BESS study for the 30 MW campus.
HTML → headless Chrome PDF, same pipeline/style as CALC-002/003.  Run scripts/make_all.py first (uses results/summary.json)."""
import base64, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from bessdc import __version__, assumptions as A, backup as B, ai_swing as AI

HERE, FIG = os.path.join(ROOT, "report"), os.path.join(ROOT, "figures")
DOC, REV, DATE, NPAGES = "DWU-DC-E-CALC-004", "P1a", "2026-10-25", 5
S = json.load(open(os.path.join(ROOT, "results", "summary.json")))
pk, bk, ai, bz, rv, cp = S["peak"], S["backup"], S["ai"], S["business"], S["revenue"], S["compat"]
isl = bk["island"]
f0 = lambda x: f"{x:,.0f}".replace(",", "\u00a0")
f1 = lambda x: f"{x:,.1f}".replace(",", "\u00a0")
f2 = lambda x: f"{x:.2f}"
M = lambda x: f"{x / 1e6:.2f}"


def img(name, width="100%"):
    b = base64.b64encode(open(os.path.join(FIG, name), "rb").read()).decode()
    return f"<img src='data:image/png;base64,{b}' style='width:{width}; display:block; margin:2pt auto'/>"


def table(head, body, cls=""):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in body)
    return f"<table class='{cls}'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


ok = lambda b: "✓" if b else "<b class='bad'>✗</b>"
r26 = rv["2026"]
comp_cost = cp["No grid limit (stand-alone)"]["total"] - cp["40 MW limit + max extra IT"]["total"]
kpi = bz["kpi"]
sc = bz["scenarios"]
hy, ba = ai["hybrid"], ai["base"]
rs_ = ai["resp_sweep"]
ann = bz["it"]["npv_per_keur_mw"]

# ------------------------------------------------------------------ page 1
p1 = f"""
<h1>Battery Energy Storage (BESS) Study — Peak Shaving, Backup, Markets, AI Smoothing</h1>
<h2 class="sub">30 MW IT hyperscale campus, Dalarna (SE3), Sweden · fictional · conceptual study · 10 MW / 20 MWh at the reserved MSG-20 bays</h2>
{table(["Item", "Value"], [
    ["<b>Document</b>", f"{DOC}, Rev {REV} (concept; errata on sheet 5) — Python package <code>bessdc</code> v{__version__}; LPs solved with HiGHS (scipy)"],
    ["<b>Basis</b>", "DWU-DC-E-DB-001 Rev P1, superseded by Rev P2 (40 MW subscription, MSG-20 BESS bay), CALC-002 (dcsizing PUE model, 37.8 / 42.6 MW), CALC-003 (relay settings, I''k)"],
    ["<b>Author / date</b>", f"Donglin (Franklin) Wu — portfolio project 05 · {DATE}"],
    ["<b>Status</b>", "Concept — <b>not for construction or investment</b>. Public market data cited (accessed 2026-10-24), all other values [ASSUMED]; no employer/vendor data"]], "meta")}
<h3>1. Scope and method</h3>
<p class="small">Hourly design year (8 760 h): synthetic Dalarna temperature (mean +4.5 °C, 5-day July heat wave to the +32 °C design ambient), IT utilisation
(mean 0.80, diurnal/weekly, AI batch blocks, 100 % on heat-wave afternoons) × PUE(T) from the CALC-002 bin model, calibrated so 100 % IT at +32 °C = <b>37.8 MW</b>;
UPS recharge after an outage (+4.8 MW, 1.5 h) placed on the hottest afternoon (CALC-002 campus max <b>42.6 MW</b>). Synthetic SE3 spot price scaled to the Nord Pool 2025 mean
(46.23 €/MWh, ≈4 % hours ≤ 0); capacity prices = Svk Mimer annual means (2025, 2026 Jan–Aug, “saturated” = ½ × 2026 [ASSUMED]) with an hourly lognormal shape.
<b>(a)</b> LP: max extra IT x s.t. L<sub>t</sub> + x·s<sub>t</sub> + c<sub>t</sub> − d<sub>t</sub> ≤ 40 MW, SOC 5–95 %, η<sub>rt</sub> 0.88, cyclic SOC.
<b>(c)</b> LP co-optimising FCR-N, FCR-D up/down, mFRR CM up and behind-the-meter arbitrage with Svk LER endurance (FCR-N 1 h, FCR-D 20 min), power head-room,
and the 40 MW limit including full down-activation. <b>(d)</b> 0.02 s simulation of a 12 MW synchronous AI training cluster. <b>(e)</b> 15-yr cash flow with fade/augmentation.</p>
<h3>2. Key results</h3>
<ul class="small">
<li><b>Grid limit is already exceeded without BESS</b> on the design day: 42.6 MW (incl. UPS recharge) vs 40 MW → headroom {f2(pk['x_no_bess'])} MW IT. With recharge limited: +{f2(pk['x_no_bess_no_recharge'])} MW.
The 10 MW / 20 MWh BESS gives <b>+{f2(pk['x_bess'])} MW IT</b> ({f2(pk['x_bess'] - pk['x_no_bess'])} MW gain) but only <b>+{f2(pk['x_firm'])} MW firm</b> with one 5 MW unit out. Peaks are few ({pk['hours_over']} h/yr) but long
(heat-wave afternoons), so <b>energy, not power, binds</b>: 10 MW → 20 MW adds nothing; 20 → 40 MWh adds +1.9 MW.</li>
<li><b>Backup</b>: {f1(bk['usable_mwh'])} MWh usable = {f0(bk['autonomy'][-1]['minutes'])} min at campus peak (and 10 MW &lt; 37.8 MW) vs 24 h fuel. Replacing all 36 gensets would need ≈ {f0(bk['replace_all']['e_mwh'])} MWh
(≈ {bk['replace_all']['ratio']:.1f} × genset CAPEX) and still not meet Tier III / EN 50600 Class 3. Island fault current {f0(isl['i_mv_a'])} A at 20 kV: R-FDR would take ≈ 60 s → island protection needed.</li>
<li><b>Markets</b>: {M(r26['total'])} M€/yr at 2026 prices (FCR-N {M(r26['rev']['fcrn'])}, mFRR {M(r26['rev']['mfrr_up'])}, arbitrage {M(r26['rev']['arbitrage'])} M€), {M(rv['2025']['total'])} M€ at 2025 prices, {M(rv['saturated']['total'])} M€ saturated.
Honouring the 40 MW limit with max extra IT costs only <b>{f0(comp_cost / 1e3)} k€/yr</b> ({comp_cost / cp['No grid limit (stand-alone)']['total'] * 100:.1f} %) → (a) and (c) are compatible if the EMS reserves head-room.</li>
<li><b>AI smoothing</b>: 3 MW/min ramp limit needs ≈ {f1(ai['ramp_sweep'][2]['p_bess_req_mw'])} MW but only {f2(ai['ramp_sweep'][2]['e_req_mwh'])} MWh; a 150 ms BESS leaves {f1(ba['grid_osc_pp_mw'])} MW p-p ripple in 0.1–2 Hz
(limit 1.0 MW) — needs ≲ 10 ms effective response (20 ms → {f2(rs_[1]['grid_osc_pp_mw'])} MW). Hybrid with a {f0(hy['e_sc_kwh'])} kWh / {f0(hy['p_sc_req_mw'])} MW supercap: {f2(hy['grid_osc_pp_mw'])} MW ✓.</li>
<li><b>Business case</b>: CAPEX {M(kpi['capex'])} M€ → NPV {f1(kpi['npv'] / 1e6)} M€, IRR {kpi['irr'] * 100:.0f} %, payback {f1(kpi['payback_y'])} yr (2026 prices, −3 %/yr); saturated: NPV {f1(sc['saturated']['npv'] / 1e6)} M€, payback {f1(sc['saturated']['payback_y'])} yr.
Capacity prices dominate; value is market risk, not engineering value. Each 100 k€/MW·yr of enabled-IT value adds {f1(ann * 100)} M€ NPV.</li>
</ul>
<h3>3. (a) Grid-capacity-limited peak shaving</h3>
{img("fig_peak_week.png", "74%")}
"""

# ------------------------------------------------------------------ page 2
es = {r["e_mwh"]: r["x_mw"] for r in S["peak_e_sweep"]}
ps_ = {r["p_mw"]: r["x_mw"] for r in S["peak_p_sweep"]}
can_rows = [[a, ("<b class='bad'>" + b + "</b>") if b in ("No", "Not recommended") else b, c] for a, b, c in B.CAN_CANNOT]
isl_rows = [[r["device"], f0(r["i_fault_a"]), f0(r["pickup_a"]), f2(r["multiple"]),
             ("∞" if r["t_clear_s"] is None else f2(r["t_clear_s"])), ok(r["ok"])] for r in bk["island_rows"]]
p2 = f"""
{img("fig_extra_it.png", "80%")}
<p class="tiny2">Extra IT (MW nameplate) vs BESS energy at 10 MW: {', '.join(f"{f1(k)} MWh → {x:+.2f}" for k, x in es.items())}. Power at 20 MWh: {', '.join(f"{f0(k)} MW → {x:+.2f}" for k, x in ps_.items())}.
Perfect foresight: real EMS needs a peak forecast and must hold SOC high before hot afternoons; firm capacity assumes the N-1 BESS (one 5 MW / 10 MWh unit out of service).
Alternative levers without BESS: staggered UPS recharge (≤ 2.2 MW) and IT power capping in the few design hours.</p>
<h3>4. (b) Backup role — what a BESS can and cannot credibly replace</h3>
{table(["Function", "Credible?", "Reason (concept level)"], can_rows, "tiny")}
<p class="tiny2"><b>Tier III / EN 50600.</b> Uptime Institute Tier III treats on-site engine generation as the primary power source that must carry the design load with no runtime limit; EN 50600-2-2 Class 3/4 needs an
independent secondary supply. A finite-energy battery does not satisfy this, so gensets stay N-rated per DR block. <b>Ratings</b> (ISO 8528-1): ESP (standby, limited hours) is not enough alone; PRP/COP
and data-centre ratings with unlimited hours at variable load are accepted — DB-001 uses 2 750 kVA / 2 200 kWe DCC (manufacturer's data-centre continuous rating). <b>Start-up</b>: gensets reach load in ≈ 10–15 s (UPS bridges this); the BESS at 20 kV cannot reach the LV bus behind an open-transition ATS.</p>
<h3>Island fault clearing with the CALC-003 settings (BESS {f0(isl['i_mv_a'])} A at 20 kV = 1.2 × I<sub>n</sub> of 11 MVA)</h3>
{table(["Device", "I fault (A)", "Pick-up (A)", "× pick-up", "t clear (s)", "≤ 1 s"], isl_rows, "small num")}
<p class="tiny2">Grid-connected the BESS adds +{f2(isl['grid_contrib_ka'])} kA: MSG-20 {f1(isl['ik_msg20_grid_ka'])} → {f1(isl['ik_msg20_with_bess_ka'])} kA (worst abnormal {f1(isl['ik_msg20_worst_ka'])} → {f1(isl['ik_msg20_worst_with_bess_ka'])} kA vs 25 kA, 92 %).
In an inverter-fed island the 20 kV inverse-time relays are too slow or never pick up; LV devices still trip (fault current referred to LV ≈ {f1(isl['i_lv_ka'])} kA). Island mode would need 51V/27 definite-time, 87L or
a fault-current-boosting grid-forming PCS. LV-side ACBs clear in 0.35 s but the whole island voltage collapses during the fault (UPS on battery).</p>
<h3>Fire safety (concept)</h3>
<p class="tiny2">{' · '.join(f"<b>{a}</b>: {b}" for a, b in B.FIRE_SAFETY)}.<br><b>Design intent:</b> {'; '.join(B.FIRE_DESIGN)}.</p>
"""

# ------------------------------------------------------------------ page 3
lab = {"fcrn": "FCR-N", "fcrd_up": "FCR-D up", "fcrd_dn": "FCR-D down", "mfrr_up": "mFRR CM up", "arbitrage": "Arbitrage (BTM)",
       "degradation": "Degradation (15 €/MWh)", "fcrn_losses": "FCR-N activation losses"}
rev_rows = [[lab[k]] + [f0(rv[s]["rev"][k] / 1e3) for s in ("2025", "2026", "saturated")] for k in lab]
rev_rows.append(["<b>Total</b>"] + [f"<b>{f0(rv[s]['total'] / 1e3)}</b>" for s in ("2025", "2026", "saturated")])
rev_rows.append(["Equivalent full cycles /yr"] + [f0(rv[s]["efc"]) for s in ("2025", "2026", "saturated")])
pt = A.PRICE_TABLE
price_rows = [[lab[k], *(f1(pt[s][k]) for s in ("2025", "2026", "saturated"))] for k in ("fcrn", "fcrd_up", "fcrd_dn", "mfrr_up")]
p3 = f"""
<h3>5. (c) Revenue stacking — FCR-N / FCR-D / mFRR / arbitrage</h3>
{img("fig_revenue.png", "86%")}
<table style="width:100%; border:none"><tr><td style="width:56%; vertical-align:top; border:none; padding:0">
{table(["k€/yr (avail. 97 %)", "2025", "2026", "saturated"], rev_rows, "tiny num")}</td>
<td style="vertical-align:top; border:none; padding:0 0 0 6pt">{table(["€/MW/h (mean)", "2025", "2026", "sat."], price_rows, "tiny num")}
<p class="tiny2">Svk Mimer annual means via Flexnavet (secondary); Svk monthly FCR report Dec 2025 (FCR-N 16.3, FCR-D up 5.0 €/MW/h) and the Svk Balancing Market Outlook 2030 confirm falling prices as BESS volume grows.</p></td></tr></table>
<p class="tiny2">Perfect-foresight LP is an upper bound → ×0.85 realisation in (e). FCR-N throughput ≈ 10 % activation [ASSUMED]; down-reserve activation imports energy and is counted against the 40 MW limit (the compatibility
constraint with (a)); no export assumed (behind the meter). Market depth not modelled: FCR volumes are a few hundred MW nationally, so revenue per MW does not scale to large fleets. mFRR CM up 2025 (40.9 €/MW/h)
collapsed in 2026 (11.3) — this alone moves the 2025 total by ≈ 2.8 M€.</p>
<h3>6. (d) AI-training power-swing smoothing</h3>
{img("fig_ai_swing.png", "84%")}
"""

# ------------------------------------------------------------------ page 4
rs = ai["resp_sweep"]
alt_rows = [list(r) for r in AI.ALTERNATIVES]
grid_csv = [l.strip().split(",") for l in open(os.path.join(ROOT, "results", "sizing_grid.csv"))][1:]
changes = [
    ["B22", "20 kV BESS bays", "bay reserved", "2 × 630 A CB bays (5 MW each); 50/51, 67N, 27/59, 81, ROCOF, intertrip, 25"],
    ["B23", "SLD-001", "bay symbol", "Draw CB/CT/VT/SA, PCS transformers Dyn 2 × 5.5 MVA, metering"],
    ["B24/25", "MSG-20 I''k / Ic", "13.0 kA / 22 A", f"{f1(isl['ik_msg20_with_bess_ka'])} kA (worst {f1(isl['ik_msg20_worst_with_bess_ka'])} kA, 92 %); Ic +≈1 A"],
    ["B26", "UPS recharge vs 40 MW", "assumed inside", "42.6 MW &gt; 40 MW → limit/stagger recharge or BESS cover"],
    ["B27", "EMS priorities", "—", "Import limit → SOC reserve → down-reserve head-room → markets; firm IT only N-1"],
    ["B28", "Backup concept", "—", "BESS not counted for Tier III; island mode needs 51V/27/87L + grid-forming"],
    ["B29–31", "Q/harmonics, fire, AI", "—", "Harmonic study; ≥ 10 m separation, UL 9540A; ramp clause + fast smoothing"]]
p4 = f"""
{img("fig_ai_sweep.png", "80%")}
<p class="tiny2">Base 24 MW + 12 MW AI: 6 s iterations (compute 1.0 / all-reduce 0.35 pu), 0.5 s facility rise time, checkpoints every 15 min (45 s at 0.2 pu), job start, crash and restart [ASSUMED, after NERC Large Loads observations].
Controller: LPF (30 s) + SOC feedback + 3 MW/min rate limiter; actuator = transport delay + 20 ms current loop. Residual ripple vs response: {', '.join(f"{r['response_ms']:.0f} ms → {f2(r['grid_osc_pp_mw'])}" for r in rs)} MW p-p.
Slow response (≥ 300 ms) is <b>worse than no smoothing</b> for the ripple (delayed injection). Smoothing throughput ≈ {f1(ba['throughput_mwh_per_h'])} MWh/h ≈ +{f0(ba['throughput_mwh_per_h'] * 6000 / (0.9 * 20))} EFC/yr at 6 000 h training → shortens life.</p>
{table(["Option", "Response", "Energy", "Cycle life", "Comment"], alt_rows, "tiny")}
<h3>7. (e) Business case and sizing sensitivity</h3>
<table style="width:100%; border:none"><tr><td style="width:60%; border:none; padding:0">{img("fig_business.png", "100%")}</td>
<td style="border:none; padding:0">{img("fig_sizing_grid.png", "100%")}</td></tr></table>
<p class="tiny2">CAPEX = (120 €/kWh·E + 75 €/kW·P) × 1.20 BoP + 0.3 M€ bays [ASSUMED; ≈ 157 €/kWh turnkey at 2 h vs BNEF 2025 Europe 177 USD/kWh]. OPEX 2 %/yr, WACC 7 %, 15 yr, ancillary prices −3 %/yr,
fade 1 %/yr + cycles (6 000 EFC to 80 %), augmentation to 90 % when SOH &lt; 80 %, avoided subscription {f1(bz['shaved_mw'])} MW × 242 SEK/kW·yr = {f0(bz['subs_eur'] / 1e3)} k€/yr. NPV scales ~linearly with power
because FCR is paid per MW — but only while the market is not saturated; 2 h is the sweet spot (FCR-N needs 2 MWh/MW, more energy mainly buys extra IT).</p>
<h3>8. Conclusions and design changes (→ TODO_final_fixes.md B22–B31)</h3>
{table(["#", "Item", "Phase 1–3", "Project 05"], changes, "tiny")}
<p class="tiny2"><b>Limitations.</b> Synthetic profiles and prices (one weather/price year, perfect foresight); hourly LP misses intra-hour FCR activation and SOC drift; no market depth, bidding or aggregator model; no export
or DSO tariff for BESS; generic PCS fault current (1.2 pu) and response; AI profile is illustrative, not measured; grid-code ramp/oscillation limits are [ASSUMED] (no Svk/DSO limit exists yet for this case);
Tier III/EN 50600 statements are interpretations at concept level, not certification advice. Code: <code>scripts/make_all.py</code> regenerates figures/results; {23} pytest tests incl. Streamlit AppTest.</p>
"""

css = open(os.path.join(ROOT, "..", "03-load-sizing", "report", "build_report.py")).read().split('css = """')[1].split('"""')[0]
css += """ ul { margin: 1pt 0 3pt 14pt; padding: 0; } li { margin: 0 0 1.5pt 0; }
table.num td { text-align: right; } table.num td:first-child { text-align: left; } .bad { color: #c00000; }"""


def tb(n): return f"""<div class="tb">
<div style="flex:2.3"><span class="lbl">PROJECT</span><b>D. Wu — Portfolio</b><br>30 MW IT DC campus, Dalarna SE3 (fictional)</div>
<div style="flex:2.9"><span class="lbl">TITLE</span><b>BESS study: peak shaving, backup, markets, AI</b><br>Concept — not for construction</div>
<div style="flex:1.9"><span class="lbl">DOCUMENT NO.</span><b>{DOC}</b></div>
<div style="flex:0.5"><span class="lbl">REV</span><b>{REV}</b></div>
<div style="flex:0.9"><span class="lbl">DATE</span>{DATE}</div>
<div style="flex:0.8"><span class="lbl">SHEET</span>{n} of {NPAGES} (A4)</div></div>"""


# ------------------------------------------------------------------ errata page (Rev P1a)
pE = f"""
<h2>Revision history and errata</h2>
{table(["Rev", "Date", "Description"], [["P1", "2026-10-24", "First issue"], ["P1a", "2026-10-25", "Errata only: cross-references to DB-001 Rev P2 / SLD Rev P2; superseded statements listed below. No calculation result changed."], ["P1a, ed.", "2026-10-29", "Editorial: genset rating wording on sheet 2 aligned to DB-001 (2 750 kVA / 2 200 kWe DCC, previously \"DCP\"). No calculation result changed."]], "meta")}
<div class="errata"><b>Note (Rev P1a, 2026-10-25).</b> Results are unchanged. Changes B22–B31 are implemented in <b>DB-001 Rev P2</b> §7.5–7.6 and the new
drawing <b>SLD-004</b> (BESS plant), with bays Q19 / Q29 on SLD-001 sh 2. The I″<sub>k</sub> values here supersede the "no BESS contribution" limitation in CALC-003.</div>
"""

pages = [p1, p2, p3, p4, pE]
html = ("<!doctype html><html><head><meta charset='utf-8'><style>" + css + "</style></head><body>"
        + "".join(f"<div class='page'>{p}{tb(i)}</div>" for i, p in enumerate(pages, 1)) + "</body></html>")
hp = os.path.join(HERE, f"{DOC}_report.html")
open(hp, "w").write(html)
pdf = os.path.join(HERE, f"{DOC}_BESS_Study.pdf")
subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", "file://" + hp], check=True, capture_output=True)
print(pdf)
