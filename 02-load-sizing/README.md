# Project 02 — Data-centre load calculation & equipment sizing

Portfolio project by Donglin (Franklin) Wu. It covers the fictional 30 MW IT hyperscale campus in Dalarna (SE3), Sweden, and continues
**DWU-DC-E-DB-001** (design basis) and **DWU-DC-E-SLD-000…004** (Rev P2) in `../01-design-basis-sld/`.
All values come from public standards or are **[ASSUMED]**. No employer, client or vendor data has been used. Concept only, **not for construction**.

## Contents

| Path | What |
|---|---|
| `dcsizing/` | Python package of pure, unit-tested sizing functions (see below) |
| `dcsizing/tables.py` | All reference data, each marked `[STD]` (with table number) or `[ASSUMED]` |
| `app.py` | Streamlit app with inputs, ratings, normal/failure loading, pass/fail checks, charts and a comparison with phase 1 |
| `tests/` | pytest suite (44 calculation tests + 2 Streamlit `AppTest` UI tests) |
| `report/build_report.py` | Builds **DWU-DC-E-CALC-002** (A4, 4 sheets incl. errata sheet, Rev P1a) for the reference case |
| `report/DWU-DC-E-CALC-002_Load_and_Sizing_Calc.pdf` | Calculation report |
| `docs/screenshots/` | Headless screenshots of the app's 6 tabs |
| `scripts/screenshot_app.py` | Playwright script that produces the screenshots |

### Modules

| Module | Scope | Standards |
|---|---|---|
| `load.py` | IT → facility load (UPS losses from the efficiency curve, mechanical pPUE vs. ambient, distribution losses, house, recharge), design-peak and annualised PUE from temperature bins, diversity, back-solving mechanical pPUE from a target PUE | EN 50600-4-2 |
| `transformer.py` | Selection with normal ≤ 80 % and N-1 ≤ 100 % limits, losses P0 + Pk·x², I''k at the MV and LV bus with complex impedances and the KT correction, peak current ip | IEC 60076-11, IEC 60909-0 |
| `generator.py` | Site derating (temperature/altitude), selection by kW/kVA loading and largest load step, transient voltage dip, HVO fuel rate, tank volume and autonomy | ISO 8528-1/-5, ISO 3046-1, EN 15940 |
| `ups.py` | Module count, LFP energy at end of life including temperature factor and DoD, C-rate (power) check, autonomy, rectifier input current | IEC 62040-3 |
| `cables.py` | Ampacity (B.52.5/B.52.12), ambient (B.52.14) and grouping (B.52.17/B.52.21) factors, Ib ≤ In ≤ Iz, voltage drop (Annex G), adiabatic k²S² ≥ I²t (Table 43A), Ik at the cable end | IEC 60364-5-52, IEC 60364-4-43, IEC 60228 |
| `busway.py` | Rating with ambient derating, voltage drop (distributed load ×0.5), Icw vs. I''k flag | IEC 61439-6 |
| `scenario.py` | `Inputs` dataclass → full campus results, flags and the comparison with phase-1 ratings (`rating_changes`) | — |

Redundancy schemes in `scenario.block_loads` (n = per-hall parameter):

| Scheme | Blocks | Normal | Failure |
|---|---|---|---|
| `DR` distributed redundant | n (≥ 3) | P/n | P/(n−1) |
| `2N` | 2n | P/2n | P/n |
| `N+1` | n+1, one common bus | P/(n+1) | P/n (flagged: not concurrently maintainable) |
| `BR` block redundant | n + 1 reserve | P/n | P/n, carried by the reserve via STS/catcher bus |

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q                                   # 46 tests
streamlit run app.py                        # opens http://localhost:8501
python report/build_report.py               # rebuilds the PDF (needs google-chrome on PATH)
python scripts/screenshot_app.py            # with the app running on :8599 (edit URL if needed)
```

Headless check as used in CI:
`streamlit run app.py --server.headless true --server.port 8599` and `curl localhost:8599/_stcore/health` → `ok`.

## Deploy to Streamlit Community Cloud (not done yet)

1. On share.streamlit.io choose **Create app**, then pick the repository `Fwurank/dc-electrical-portfolio`, branch `main`, and the main file path `02-load-sizing/app.py`. Use Python 3.11 or newer.
2. Streamlit Cloud installs `02-load-sizing/requirements.txt`, the one next to the app. It holds only the runtime dependencies (streamlit, pandas, altair). The app does not need any secrets.
3. Deployment needs the repository owner's own GitHub and Streamlit login.

## Reference-case results (30 MW, 6 halls, 4N/3)

* Block load: 1 250 kW normal, 1 667 kW N-1. UPS 2 × 1 000 kW at 62.5 % / 83.3 %.
* Transformer: 2 500 kVA at 64.6 % / 82.1 %. Genset: 2 750 kVA at 87.6 % N-1.
* Short circuit: MSB I''k 53.8 kA (65 kA board). 20 kV: 13.0 kA.
* Campus: 37.8 MW / 39.8 MVA, design-peak PUE 1.261, **annualised PUE 1.165 (target 1.15 at risk)**.
* Rating changes found against phase 1 are listed in the report §3 and in `../TODO_final_fixes.md`.

## Limitations

The tool covers concept sizing only. It does not model:

* Motor starting.
* Harmonics, including transformer K-factor.
* Protection selectivity (that is project 03).
* Cable-to-cable mutual heating beyond the tabulated grouping factors.

Vendor data must replace every [ASSUMED] value.
