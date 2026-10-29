# Project 04: BESS at the 30 MW data-centre campus (DWU-DC-E-CALC-004)

This is a conceptual study of a **10 MW / 20 MWh battery** in the 20 kV bays reserved at MSG-20 (DB-001). The campus is a fictional 30 MW IT campus in Dalarna (SE3). The study uses public data, cited with the date it was accessed (2026-10-24). Every other value is marked [ASSUMED] in `bessdc/assumptions.py`. No employer or vendor data is used. The study is not for construction or investment decisions.

| Part | Question | Method | Code |
|---|---|---|---|
| (a) Peak shaving | How much extra IT fits under the 40 MW import limit? | Hourly LP over 8 760 h (HiGHS): maximise x subject to L + x·s + c − d ≤ 40, the SOC window, efficiency and cyclic SOC | `bessdc/profiles.py`, `bessdc/dispatch.py::max_extra_it` |
| (b) Backup | What a BESS can and cannot replace: Tier III / EN 50600, ESP/PRP/DCP ratings, start-up, fault current, fire safety | Autonomy, genset-replacement sizing, island fault current against the CALC-003 relays | `bessdc/backup.py` (imports `../03-shortcircuit-protection/scprot`) |
| (c) Revenue stacking | FCR-N, FCR-D up/down, mFRR CM up and arbitrage, with degradation and availability. Is this compatible with (a)? | Co-optimisation LP with Svk LER endurance and head-room, plus the grid limit including down-activation | `bessdc/dispatch.py::co_optimise` |
| (d) AI swing smoothing | P, E, response time and ramp limit for a 12 MW synchronous training cluster | 0.02 s simulation: LPF + SOC feedback + rate limiter; delay and current-loop actuator; hybrid supercapacitor; FFT | `bessdc/ai_swing.py` |
| (e) Business case | CAPEX, NPV, IRR, payback, tornado and a P × duration grid | 15-year cash flow with fade and augmentation | `bessdc/business.py` |

## Key results (default inputs)

**(a) Peak shaving**
* The design day (42.6 MW, including UPS recharge) is above 40 MW **without any BESS**. The headroom is −2.08 MW IT.
* The BESS gives **+2.41 MW IT**. With one 5 MW unit out of service (N-1), the firm figure is **+0.84 MW**.
* Energy, not power, is the binding constraint.

**(b) Backup**
* 27 min at campus peak, compared with 24 h of fuel.
* The inverter fault current of 381 A at 20 kV does not operate the 20 kV relays in island mode. The BESS adds 0.38 kA to MSG-20, which goes from 13.0 to 13.3 kA.

**(c) Revenue stacking**
* 1.82 M€/yr at 2026 prices, 4.15 M€/yr at 2025 prices, 0.96 M€/yr in the saturated case.
* Respecting the 40 MW limit costs about 30 k€/yr (1.6 %).

**(d) AI swing smoothing**
* Meeting a 3 MW/min ramp limit needs about 11.4 MW but only 0.46 MWh.
* The 0.1–2 Hz ripple needs a response of about 10 ms or faster. A BESS with a 150 ms response leaves 5.6 MW peak-to-peak.
* A hybrid with a 23 kWh supercapacitor brings this down to 0.79 MW.

**(e) Business case**
* CAPEX 4.08 M€, NPV 7.2 M€, IRR 34 %, payback 2.7 years at 2026 prices with a −3 %/yr trend.
* In the saturated case, NPV is 2.0 M€ and payback 5.3 years.

## Run

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt      # needs ../02-load-sizing and ../03-shortcircuit-protection next to this folder
python scripts/make_all.py               # ≈ 60 s → figures/*.png, results/*.csv|json
python report/build_report.py            # → report/DWU-DC-E-CALC-004_BESS_Study.pdf (4 pages A4)
streamlit run app.py                     # interactive tool (7 tabs)
pytest -q                                # 23 tests incl. Streamlit AppTest
# screenshots: streamlit run app.py --server.port 8599 & python scripts/screenshot_app.py
```

## Files
* `bessdc/`: the study package. `assumptions.py` holds every parameter with a PUBLIC, ASSUMED or PROJECT tag and its source.
* `app.py`: the Streamlit tool. `docs/screenshots/app_01..07_*.png` are the screenshots.
* `figures/`: PNGs used in the report. `results/`: summary JSON, sizing grid, sweeps, cash flows, assumptions register, hourly profiles.
* `report/`: report builder, HTML, PDF and page previews.
* `context/`: FIG-004S storage layers vs time (SVG / PDF / PNG) and a 7-line context note, v0.1, CONCEPT / DRAFT. Its numbers are taken unchanged from DB-001 Rev P2 and CALC-004. Built by `../05-next-gen-power/scripts/fig04_storage_layers.py`.

## Limitations
* Synthetic profiles and prices, with perfect foresight. The realisation factor of 0.85 is applied only in (e).
* Hourly resolution for (a) and (c).
* No model of market depth, bidding or aggregator fees.
* The PCS response and fault current are generic values.
* The grid-code ramp and oscillation limits are assumptions.
* Statements about Tier III and EN 50600 are concept-level interpretations.

## Deploy to Streamlit Community Cloud (not done yet)

1. Create an app from `Fwurank/dc-electrical-portfolio`, branch `main`, main file path `04-bess/app.py`, Python 3.11 or newer. Streamlit Cloud installs `04-bess/requirements.txt`.
2. The app imports `../02-load-sizing` and `../03-shortcircuit-protection` by relative path. Deploy the whole repository, which Streamlit Cloud does by default.
3. The first load solves several LPs (≈ 7 s), and the results are cached after that. No secrets are needed. Deployment needs the repository owner's own login.
