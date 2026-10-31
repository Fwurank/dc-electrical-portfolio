# Data center electrical portfolio: 30 MW IT Nordic campus (fictional)

**Donglin (Franklin) Wu**, Electrical Power Systems Engineer. Data center electrical infrastructure & energy storage. Gothenburg, Sweden.
[LinkedIn](https://www.linkedin.com/in/donglinwu1998) · Website: https://fwurank.github.io/dc-electrical-portfolio/

> **About the data.** This is a **fictional 30 MW IT hyperscale campus** in Dalarna (bidding zone SE3), Sweden.
> * It is built only from **public standards, public market data and assumed parameters**. Assumptions are marked `[ASSUMED]` / `(A)`.
> * **No employer, client or vendor data is used.**
> * It is a concept-level study, **not for construction or investment decisions**.

Five connected studies of the same campus. Projects 01 and 03–05 feed their rating changes into each other, and the design basis is at Rev P2, which includes all of them. Project 02 is a **research and concept study** (CONCEPT / DRAFT v0.1) on the same campus: nothing in it has been built or commissioned, and it changes no rating.

| # | Project | Key results | Deliverables |
|---|---|---|---|
| 01 | [Design basis & single-line diagrams](01-design-basis-sld/) | 2 × 130 kV, 2 × 63 MVA, 6 halls × 5 MW, 24 × 2.5 MVA blocks (DR 4N/3). 8 A3 SLD sheets with IEC 60617 symbols; text height ≥ 2.5 mm on A3 is checked automatically (min 2.57 mm, 0 overlaps) | [DB-001 Rev P2](01-design-basis-sld/docs/DWU-DC-E-DB-001_Design_Basis.pdf), [SLD set](01-design-basis-sld/drawings/DWU-DC-E-SLD_concept_set_RevP2_A3.pdf) |
| 02 | [Next-generation power architecture and commissioning (research and concept study)](02-next-gen-power/) | 400 V AC + UPS vs 400 VDC vs 800 VDC for one 5 MW hall, 13 rows with credibility labels; SLD-005 800 VDC concept for block A; L0–L5 commissioning plan with 11 IST scenarios; Q-LB 2 500 A ≈ 1.73 MVA proves the 1.67 MW block load but not the full genset rating [Inference]. CONCEPT / DRAFT | [NOTE-005](02-next-gen-power/docs/02-800vdc-architecture-comparison-v0.1-2026-10-29-en.pdf), [SLD-005](02-next-gen-power/drawings/SLD-005_800VDC_block_A_concept-v0.1-2026-10-29-en.pdf), [CX-005](02-next-gen-power/docs/02-commissioning-test-plan-concept-v0.1-2026-10-29-en.pdf) |
| 03 | [Load & equipment sizing tool](03-load-sizing/) (`dcsizing` + Streamlit) | Design peak 37.8 MW, 42.6 MW with UPS recharge (> 40 MW subscription); PUE 1.165; transformer 82 % N-1; battery 120 → 165 kWh (C-rate); MSB 53.8 kA | [CALC-002](03-load-sizing/report/DWU-DC-E-CALC-002_Load_and_Sizing_Calc.pdf) |
| 04 | [Short-circuit, protection & arc flash](04-shortcircuit-protection/) (`scprot`) | Own IEC 60909 solver = pandapower; MSB 52.3 kA / ip 122 kA; closed transition 81.8 kA > 65 kA, so open transition only; busway 37.1 > 36 kA, so a current-limiting MCCB; arc flash 96 → 3.2 cal/cm² | [CALC-003](04-shortcircuit-protection/report/DWU-DC-E-CALC-003_ShortCircuit_Protection_ArcFlash.pdf) |
| 05 | [BESS in a grid-constrained data center](05-bess/) (`bessdc` + Streamlit) | 10 MW / 20 MWh: headroom −2.08 → +2.41 MW (firm +0.84 MW); 27 min backup, no genset replacement; revenue 1.82 M€/yr (2026), NPV ≈ 7.2 M€; AI ripple needs ≲ 10 ms response | [CALC-004](05-bess/report/DWU-DC-E-CALC-004_BESS_Study.pdf) |

Also in the repository:
* [`ASSUMPTIONS_REGISTER_ALL.csv`](ASSUMPTIONS_REGISTER_ALL.csv): 188 assumptions from Projects 01 and 03–05. Project 02 adds no rows: it changes no rating, and each of its documents lists its own assumptions in its header.
* [`REVIEW_GUIDE.md`](REVIEW_GUIDE.md): algorithms, formulas and a code map.
* [`TODO_final_fixes.md`](TODO_final_fixes.md): every rating change and its status.

## Repository structure

```
dc-electrical-portfolio/
├── index.html, projects/, assets/   GitHub Pages site (plain HTML/CSS, served from the repo root)
├── 01-design-basis-sld/             docs/ (DB-001 md + PDF), drawings/ (SLD-000…004 SVG/PDF/PNG), scripts/, tests/
├── 02-next-gen-power/               research and concept study: docs/ (NOTE-005, CX-005 md + PDF), drawings/ (SLD-005), scripts/
├── 03-load-sizing/                  dcsizing/ package, app.py (Streamlit), report/, scripts/, tests/
├── 04-shortcircuit-protection/      scprot/ package, figures/, results/, report/, scripts/, tests/
├── 05-bess/                         bessdc/ package, app.py (Streamlit), figures/, results/, report/, scripts/, tests/, context/ (FIG-004S)
├── tools/build_assumptions_register.py
├── requirements.txt                 one environment for all projects
├── run_all_tests.sh                 runs all four test suites (102 tests)
├── run_apps.md                      details on apps, scripts and report builds
├── set_github_user.sh               fills in the GitHub username placeholder
└── LICENSE
```

Projects 04 and 05 import `../03-load-sizing` (and 05 also imports `../04-shortcircuit-protection`) by relative path. Keep the folders side by side.

## How to run

Tested with Python 3.13 on Linux. Python 3.11 or newer should work.

```bash
git clone https://github.com/Fwurank/dc-electrical-portfolio.git
cd dc-electrical-portfolio
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
bash run_all_tests.sh                       # expect: 102 passed (01: 10, 02: 46, 03: 23, 04: 23)
```

Rebuilding the outputs:
* Figures and results: `python scripts/make_all.py`, run in 04 or 05.
* Reports: `python report/build_report.py`, run in 03, 04 or 05.
* Drawings and DB PDF: `python scripts/build_all.py`, run in 01.
* The PDF prints need Google Chrome (headless), and project 01 also needs poppler's `pdfunite`. Without Chrome, the HTML is still written.

## Streamlit apps

### Run locally

```bash
cd 03-load-sizing && streamlit run app.py                      # http://localhost:8501  (6 tabs: sizing tool)
cd 05-bess        && streamlit run app.py --server.port 8502   # http://localhost:8502  (7 tabs: BESS study)
```
Headless health check: `streamlit run app.py --server.headless true --server.port 8599 &`, then `curl localhost:8599/_stcore/health` returns `ok`.

### Deploying to Streamlit Community Cloud (not deployed yet)

1. Sign in at share.streamlit.io with the GitHub account that owns this repository, then choose **Create app**.
2. Repository `Fwurank/dc-electrical-portfolio`, branch `main`. Main file path `03-load-sizing/app.py` for the first app and `05-bess/app.py` for the second. Python 3.11 or newer.
3. Streamlit Cloud installs the `requirements.txt` next to each `app.py`. No secrets are needed. The BESS app solves its LPs on first load (≈ 7 s) and caches them after that.

The app links will be added to the website after deployment.

## GitHub Pages

The site is plain HTML/CSS in the **repository root** (`index.html`, `projects/`, `assets/`, `.nojekyll`). It needs no build step, and it links straight to the PDFs and drawings in the project folders.
To publish it: open **Settings → Pages**, choose **Deploy from a branch**, branch `main`, folder **/ (root)**.
Before the first push, run `bash set_github_user.sh Fwurank` to write the GitHub username into the site, the READMEs and `../CV_header_line.txt` (Pages URL: https://fwurank.github.io/dc-electrical-portfolio/).

## License

* **Code** (`*.py`, `*.sh`, and the site's HTML/CSS): [MIT License](LICENSE).
* **Documents**: the reports, design basis, drawings, figures and screenshots are © 2026 D. Wu, all rights reserved. They may be viewed and linked for review.
* Standards are cited by number only. No standard text is reproduced.
