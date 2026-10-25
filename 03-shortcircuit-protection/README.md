# 03 — Short-circuit, protection coordination & arc flash (DWU-DC-E-CALC-003)

Portfolio project 03 for a **fictional** 30 MW IT hyperscale campus in Dalarna (SE3), Sweden.
Public standards plus assumed parameters (marked [ASSUMED]) only. No employer or vendor data.
**Conceptual study, not for construction.**

Builds on `../01-design-basis` (DB-001 Rev P2, SLD-000…004) and `../02-load-sizing` (`dcsizing`, including the rating changes in `../TODO_final_fixes.md` §B).

## What it does

| Part | Standard / method | Module |
|---|---|---|
| Short-circuit currents I''k max/min, ip (method C), Ib (μ), Ith (m+n) | IEC 60909-0:2016, own nodal solver with KT/KG | `scprot/iec60909.py`, `scprot/campus.py` |
| Independent cross-check | pandapower 3.5 `calc_sc` (max case Δ 0.00 %, min case −2…−4 %, because pandapower leaves out KT for Ik min) | `scprot/pp_model.py` |
| Scenarios | S0 normal max/min, S1 T1//T2, S2 N-1 T2 out, S3 closed-transition genset, S4 genset island, S5/S5b hall coupler | `scprot/campus.py` |
| Protection coordination 20 kV → rack | IEC 60255-151 curves (SI/VI/EI); **generic** IEC 60947-2 LSI and IEC 60898-1 C-curve bands; CTI ≥ 0.3 s; CT ALF'/Ith check; IEC 60076-5 transformer withstand | `scprot/protection.py`, `scprot/study.py` |
| Arc flash | IEEE 1584-2018 at LV (arcflash-calc 0.1.0, validated against Annex D in the tests); Lee method at 20 kV | `scprot/arcflash.py` |
| 20 kV neutral earthing | Compensated vs 500 A low-resistance; EPR against the EN 50522 2·UTp screen | `scprot/earthing.py` |

## Run

```bash
cd 03-shortcircuit-protection
../.venv/bin/pip install -r requirements.txt   # once
../.venv/bin/python scripts/make_all.py         # figures/*.png + results/*.csv/json
../.venv/bin/python -m pytest                   # 23 tests
../.venv/bin/python report/build_report.py      # report/DWU-DC-E-CALC-003_*.pdf (headless Chrome)
```

## Outputs

* `report/DWU-DC-E-CALC-003_ShortCircuit_Protection_ArcFlash.pdf`: A4, 6 sheets incl. errata sheet (Rev P1a). Previews are in `report/preview/`.
* `figures/fig1_ik_levels.png`: fault levels vs ratings.
* `figures/fig2_tcc_mv.png`: 20 kV time-current curves (TCC).
* `figures/fig3_tcc_lv.png`: 400 V TCC.
* `figures/fig4_tcc_genset.png`: TCC for the genset island and the UPS-inverter-only case.
* `figures/fig5_arcflash.png`: arc-flash results.
* `results/short_circuit.csv`, `results/pandapower_crosscheck.csv`, `results/study_results.json`.

## Key results (S0 = normal operation)

* MSG-20 13.0 kA; MSB-A 52.3 kA / ip 122 kA. The hand values 53.8 / 13.0 kA from project 02 are reproduced exactly when cables are left out.
* T1//T2: ip 58.5 kA, which is 94 % of 62.5 kA. Keep the interlock.
* Closed-transition retransfer: 81.8 kA > 65 kA. Use open transition only.
* Busway start 37.1 kA > Icw 36 kA, so the busway needs a current-limiting MCCB with a tested combination.
* Busway end 25.1 kA, so the tap-off devices must be rated ≥ 36 kA or covered by a tested cascade.
* MV grading margins are ≥ 0.30 s. LV coordination is time-selective plus ZSI. MCB/MCCB is current-selective up to 8.6 kA; above that, manufacturer tables are needed.
* Arc flash: MSB line side 96 → 3.2 cal/cm² with optical arc relays and an MV intertrip.

## Limitations

* PowerFactory results for the same study cases are being prepared and will be added to this repository later.
* LV device curves are generic.
* Grid, cable, genset, UPS and earthing data are assumed.
* No contribution from motors, VFDs or BESS.
* IEEE 1584 is not valid at 20 kV, so the Lee method is used (conservative).
* Touch voltage is only screened. There is no soil model.
