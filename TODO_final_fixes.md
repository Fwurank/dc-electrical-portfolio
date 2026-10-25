# TODO — final fixes before the portfolio is published

Status: **A and B implemented in DB-001 Rev P2 and SLD set Rev P2 (2026-10-25)**. C: one item done, one partly done, the rest open, because they need DSO or vendor data.
Collected 2026-10-24. Fixes applied 2026-10-25. Verification: `01-design-basis-sld/scripts/check_drawings.py` → `drawings/text_height_check.json`, and `run_all_tests.sh`.

## A. Drawings DWU-DC-E-SLD-001…003 (project 01) — review feedback

> **Status: DONE (Rev P2).**
> * There are 8 sheets now: SLD-000 legend, 001-1/-2, 002-1/-2, 003-1/-2 and the new SLD-004 BESS sheet.
> * The checker measured all 1 199 texts:
>   * Minimum cap height is **2.57 mm** (10 pt) on every sheet.
>   * Equipment and busbar tags are 3.6 mm (14 pt).
>   * The drawing number is 5.14 mm (20 pt).
>   * There are 0 text/text and text/line overlaps, and no text off the sheet.
> * Symbols: CT, VT, SA, ES, relay numbers, Wh/EPMS meters, Petersen coil, arc sensors and interlocks are drawn and listed in the legend.
> * Set PDF: `drawings/DWU-DC-E-SLD_concept_set_RevP2_A3.pdf`.
> * The A3 print preview is a PDF at true A3 scale. **A physical print test is not done (no printer).** IEC 60617 item numbers are not shown on the legend, because they were not verified against the database.
> * Rev P1 sheets are kept in `drawings/superseded_RevP1/`.

1. **Text too small on an A3 print.** It is readable on screen when zoomed, but not on paper.
   - Raise every text to a **≥ 2.5 mm** printed character height (ISO 3098 / ISO 5457 practice).
   - Busbar and equipment labels ≥ 3.5 mm. Title block ≥ 2.5 mm, drawing number ≥ 5 mm.
   - In `sld_lib.py`, convert font sizes as pt = mm / 0.3528 × 1/0.7, using cap height ≈ 0.7 × em. 2.5 mm ≈ 10 pt.
   - Re-layout the sheets, since bigger text needs more space. Consider splitting SLD-003 into two sheets.
2. **Symbols are simplified.** Add proper **IEC 60617** symbols:
   - Current transformers (CT, 06-09-11), with ratio/class labels such as 2500/1 A 5P20 and 0.5S for metering.
   - Voltage transformers (VT), with ratio labels such as 20/√3 / 0.1/√3 kV, cl. 0.5/3P.
   - Surge arresters (07-22-03): 130 kV line entries, transformer HV/MV terminals and 20 kV cable terminations. Add SPD type 1+2 at the LV MSBs and type 2 at the UOSB/IT boards.
   - Earthing switches (07-13-xx) on HV bays, MV feeders and couplers. Add earthing/neutral points with the earthing symbol.
   - Relay function numbers on the CT secondaries (50/51, 50N/51N, 67N, 87T, 87B, 27/59, 81).
   - Meter symbols (kWh, EPMS) on the incomers and outgoers.
   - Update the legend.
3. Re-export the SVG, PDF and PNG sheets and the combined A3 PDF. Re-check text overlaps at 100 % zoom and in a real A3 print preview.

## B. Rating changes from project 02 (DWU-DC-E-CALC-002) → update DB-001 to Rev P2 and the SLDs

| # | Item | Phase 1 | New | Type | Where to update | Status (Rev P2) |
|---|---|---|---|---|---|---|
| 1 | LFP battery per 1 000 kW UPS module | 120 kWh | **165 kWh** nameplate. C-rate limited: at 120 kWh it would be 10.7 C at end of life against 8 C max. Autonomy becomes 8.1 min at the N-1 load | required | DB §8 / Table 8.1, SLD-003 battery labels | done (see DB §12) |
| 2 | MSB → UPS rectifier input breaker | 1 600 A | **2 000 A** (I max 1 660 A at P_r + 10 % recharge). Alternative: limit grid recharge to ≤ 5 % | required | DB Table 8.1, SLD-003 | done (see DB §12) |
| 3 | White-space busway feeder protection (UOSB) | MCCB, not specified | **Current-limiting MCCB with a tested conditional short-circuit current Icc ≥ 55 kA** for the busway. 800 A busway Icw 36 kA < I''k 53.8 kA | required | SLD-002/003 notes, DB §9 | **superseded by #15** (Icu ≥ 50 kA / tested ≥ 40 kA); CALC-002 carries an erratum |
| 4 | MSB → SBS (static bypass) connection | cable, not specified | **3 200 A busbar trunking**. A cable would need 7 × 3×1×240 Cu | required | SLD-003 | done (see DB §12) |
| 5 | Genset → MSB incomer | cable, not specified | **4 000 A busbar trunking**, or put the genset room next to the MSB. A cable would need 8 × 3×1×240 Cu | required | SLD-003, layout note | done (see DB §12) |
| 6 | Fuel storage per hall, 24 h | ≈ 38 m³ | **≈ 51 m³ gross** (46 m³ net). It includes 5 % recharge, part-load SFC and the mechanical gensets | required | DB §8 fuel text | done (see DB §12) |
| 7 | Annualised PUE | ≤ 1.15 | **1.165** computed at 75 % IT. Either restate the target as ≈ 1.16–1.17, or specify mechanical pPUE ≤ 0.035 in free-cooling mode (EC fans, higher CHW/TCS temperature) or UPS ESS/eco-mode | required (text) | DB §2 and §5 | done (see DB §12) |
| 8 | Mechanical transformer | 1 600 kVA | 1 250 kVA would pass (82.6 % N-1). **Keep 1 600 kVA** for the 20 % growth/motor-start margin, but state that reason in the DB | optional | DB Table 8.1 note | done (see DB §12) |
| 9 | 2.5 MVA block transformer Pk | 22 kW | 19 kW assumed in project 02 (Ecodesign Tier 2 order). Align the DB to one value | editorial | DB §8 | done (see DB §12) |
| 10 | MSB I''k | ≈ 52 kA | 53.8 kA (IEC 60909 with KT and source impedance). The 65 kA board still suits. Ipk ≥ 143 kA → specify Icw 65 kA 1 s / Ipk 143 kA | editorial | DB §7 | done (see DB §12) |
| 11 | 20 kV I''k | ≈ 14 kA | 13.0 kA. The 25 kA switchgear still suits | editorial | DB §7 | done (see DB §12) |
| 12 | MSG-20 T1//T2 parallel / bus-coupler transfer (from project 03, DWU-DC-E-CALC-003) | interlocked | **Keep the interlock.** Coupler auto-close only after the incomer is open (break-before-make). S1 ip 58.5 kA = 94 % of 62.5 kA, > 100 % at Sk 4 000 MVA; R-TX CT would saturate | required | DB §7, SLD-001 interlock note | done (see DB §12) |
| 13 | HV-DH1 hall-board coupler | N.O. | **Interlock: close only with one hall feeder open**. S5b (both feeders + coupler) parallels T1/T2: 20.9 kA | required | SLD-001/002 note | done (see DB §12) |
| 14 | Genset → grid retransfer at MSB | closed transition "to be reconsidered" | **Open transition only**. S3 grid + genset = 81.8 kA / ip 187 kA > 65 / 143 kA | required | DB §8, SLD-003 ATS note | done (see DB §12) |
| 15 | Busway feeder MCCB (refines #3) | Icc ≥ 55 kA | **Icu ≥ 50 kA current-limiting MCCB, tested busway conditional rating ≥ 40 kA** (UOSB 49.3 kA, busway start 37.1 kA > Icw 36 kA) | required | SLD-003 note | done (see DB §12) |
| 16 | Tap-off 63 A devices / rack PDU | MCB, not specified | **63 A MCCB Icu ≥ 36 kA or tested cascade** (busway end 25.1 kA > 15 kA MCB); **PDU conditional SCCR ≥ 15 kA** (14.0 kA at rack inlet) | required | SLD-003, DB §9 | done (see DB §12) |
| 17 | MSB/UOSB arc-flash mitigation | — | **Optical arc relays with intertrip of the 20 kV block-transformer VCB; ZSI; maintenance (ARMS) switch**. Line side 96 → 3.2 cal/cm², bus 16.8 → 2.4–4.8 cal/cm² | required | DB §7/§9, SLD-003 | done (see DB §12) |
| 18 | MSG-20 / HV-DH1 switchgear | IAC AFLR 25 kA 1 s | **Add optical arc protection + reverse-blocking busbar protection** (Lee 106 → 11 cal/cm²) | required | DB §7, SLD-001/002 | done (see DB §12) |
| 19 | LV trip-unit settings | LSIG, not specified | SBS ACB Ir 2 900 / tr 1 s / Isd 2.5× / 0.2 s; incomer Ir 3 600 / tr 3 s / Isd 4× / 0.3 s; **genset ACB Isd ≤ 2.5 Ir**; genset sustained short-circuit ≥ 300 % for 2 s in the genset spec | required | DB §8, protection settings table | done (see DB §12) |
| 20 | 20 kV CTs | not specified | R-INC 2 500/1, R-FDR 400/1, **R-TX 150/1 5P20 with Ith ≥ 25 kA 1 s** | required | SLD-001/002 (draw CTs, see A) | done (see DB §12) |
| 21 | 20 kV neutral earthing | compensated per section | **Keep compensated earthing**: coil ≥ 50 A adjustable + 10 A parallel resistor, 67N admittance protection (Ic 22 A/section, 44 A coupled). Low-resistance 500 A rejected | required | DB §7, SLD-001 | done (see DB §12) |
| 22 | 20 kV BESS bays (from project 04, DWU-DC-E-CALC-004) | "BESS bay (future 10 MW / 20 MWh)" per section | **2 × 630 A CB bays, one per MSG-20 section (5 MW / 5.5 MVA each, 159 A)**. CT 200/1 5P20 + 0.2S metering core, VT. Protection 50/51, 50N/51N/67N, 27/59, 81U/O, 59N, loss-of-mains (ROCOF/vector shift), intertrip from R-INC, 25 synchro-check if grid-forming | required | DB §7, SLD-001 | done (see DB §12) |
| 23 | SLD-001 BESS bays | bay symbol only | **Draw** CB, CT, VT, surge arresters, PCS transformers 20/0.69 kV **Dyn (delta at 20 kV)** 2 × 5.5 MVA, PCS + containers, revenue/aggregator metering | required | SLD-001 (with A) | done (see DB §12) |
| 24 | MSG-20 I''k with BESS | 13.0 kA | **13.3 kA** normal (+0.38 kA inverter, 1.2 × In). Worst abnormal case 22.7 → **23.1 kA = 92 % of 25 kA**. Rating OK; keep the T1//T2 interlock (#12) | editorial | DB §7 | done (see DB §12) |
| 25 | 20 kV earth-fault current | Ic 22 A/section | **+≈1 A** (BESS cables + transformers). Delta windings, so no neutral contribution. The coil (≥ 50 A, #21) still covers it | editorial | DB §7 | done (see DB §12) |
| 26 | UPS recharge after grid return | inside 40 MW? | **New finding:** design peak + recharge = 42.6 MW > 40 MW subscription. Either stagger or limit UPS recharge (≤ 2.2 MW campus) or let the BESS cover it (EMS rule). Without either, the import limit is exceeded on the design day | required | DB §6 (grid capacity text), UPS spec | done (see DB §12) |
| 27 | EMS / power-plant controller | — | **Priority 1: grid import limit; 2: SOC reserve before forecast peaks; 3: reserve headroom for FCR down-activation (counts against the import limit); 4: markets.** Fallback IT power capping if the BESS is unavailable. Count extra IT as firm only at N-1 BESS (**+0.84 MW**, not +2.4 MW) | required | DB §6/§10 controls | done (see DB §12) |
| 28 | BESS in the backup concept | — | **Not counted as Tier III / EN 50600 Class 3 capacity**; gensets and UPS unchanged. Optional fail-to-start bridging needs a grid-forming PCS, island protection (51V / 27 definite-time / 87L: R-FDR would take ≈ 60 s at 381 A), soft energisation, 130 kV CB open interlock, and an island earthing check | required (text) | DB §8 | done (see DB §12) |
| 29 | Reactive power / harmonics | p.f. ≥ 0.95 | PCS 11 MVA (Q capability) can support p.f. at the connection point. **Harmonic study** to IEC/TR 61000-3-6 with the DSO (PCS + UPS rectifiers) | required | DB §7 | done (see DB §12) |
| 30 | BESS fire safety / layout | — | **Outdoor LFP containers ≥ 10 m from halls, transformers and fuel tanks [ASSUMED]**. UL 9540A data, NFPA 855 / EN IEC 62485-5 / IEC 62933-5-2, explosion control (NFPA 68/69), Räddningstjänst consultation | required | DB §4 plot plan, §11 fire | done (see DB §12) |
| 31 | AI-training loads | — | Grid ramp limit in the connection agreement. A 12 MW synchronous AI swing needs ≈ 11.4 MW of BESS power (the 10 MW BESS is marginal) but < 0.5 MWh. The 0.1–2 Hz ripple needs ≤ ~10 ms response: specify supercap/hybrid, UPS-level smoothing or a GPU power floor | recommended | DB §2 load description | done (see DB §12) |

Unchanged and confirmed:

* UPS 2 × 1 000 kW.
* Block transformer 2 500 kVA.
* IT genset 2 750 kVA.
* Mechanical genset 1 650 kVA. It is governed by the 400 kW chiller step (≤ 33 %).
* MSB 4 000 A / 65 kA, UOSB 3 200 A, busway runs 800 A, HV transformers 63 MVA (N-1 63 %), MV feeders (213 A ≤ 390 A).

## C. Other housekeeping

> Status per item is shown in brackets below.

* ~~Project 03 (IEC 60909 / pandapower) must cross-check the 53.8 kA and 13.0 kA values and the busway Icc.~~ **Done** (DWU-DC-E-CALC-003): own solver = hand values when cables/busduct are removed (53.8 / 13.0 kA); full model 52.3 / 13.0 kA; pandapower identical in the max case. Busway Icw 36 kA < 37.1 kA confirmed (#15).
* **[OPEN, needs DSO data]** Detailed 130 kV substation earthing study with DSO data (soil model, EN 50522): 130 kV earth fault EPR ≈ 800 V exceeds 2·UTp at 0.5 s back-up clearing.
* **[OPEN, needs vendor selection]** Replace generic LV curves with the selected manufacturer's curves and selectivity/cascade tables (MCB/MCCB above 8.6 kA is not current-selective).
* **[OPEN, needs DSO/vendor data]** Confirm assumed data with the DSO/vendors: grid Sk 1 500–3 000 MVA (S1 margin is sensitive above 4 000 MVA), UPS inverter current limit, PDU rating, cable capacitance, earth resistance.
* **[OPEN]** Arc-flash labels only after the final study with vendor clearing times (project 03 is conceptual; 20 kV uses the Lee method).
* **[DONE]** (DB-001 revision table + §12 traceability table) Add DB-001 Rev P2 revision table entries for every change in B.
* **[PARTLY DONE]** The PCS fault factor is aligned to 1.2 × In in bessdc, CALC-004 and SLD-004. The DSO, Svk, market and vendor confirmations are **OPEN**. Project 04 follow-ups: confirm with the DSO whether BESS export or FCR activation is allowed under the 40 MW subscription (CALC-004 assumes behind-the-meter, no export). Check Svk FCR/mFRR prequalification and aggregator terms. Check market depth: FCR volumes are small nationally, so the revenue in CALC-004 is an upper bound per MW. Get a vendor PCS fault-current curve (1.2 pu was assumed).
