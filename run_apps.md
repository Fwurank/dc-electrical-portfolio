# Run the tools / 运行各工具

All commands are run from the repository root. Use one shared virtual environment.
所有命令都在 the repository root 下执行，四个项目共用一个虚拟环境。

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
bash run_all_tests.sh                    # 102 tests (01: 10, 02: 46, 03: 23, 04: 23)
python tools/build_assumptions_register.py   # regenerate ASSUMPTIONS_REGISTER_ALL.csv
```

Keep the four project folders side by side. Projects 03 and 04 import `../02-load-sizing/dcsizing`, and 04 also imports `../03-shortcircuit-protection/scprot`.
四个项目文件夹必须并列放置，因为 03 和 04 会按相对路径导入 02，04 还会导入 03。

## Interactive apps (Streamlit) / 交互式应用

| Project | Command | URL | Tabs | Typical first run |
|---|---|---|---|---|
| 02 Load & sizing | `cd 02-load-sizing && streamlit run app.py` | http://localhost:8501 | 6: summary, equipment, checks, cables, PUE, compare with phase 1 | < 2 s |
| 04 BESS | `cd 04-bess && streamlit run app.py --server.port 8502` | http://localhost:8502 | 7: overview, peak shaving, backup, revenue, AI smoothing, business, assumptions | ≈ 7 s (LPs + 0.02 s simulation; then cached) |

To check that an app is up without a browser:
`streamlit run app.py --server.headless true --server.port 8599 &` then `curl localhost:8599/_stcore/health` → `ok`.

To re-take the screenshots (needs Playwright + Google Chrome), start the app on port 8599, then run `python scripts/screenshot_app.py` → `docs/screenshots/*.png`.

## Batch scripts and reports / 批处理脚本与报告

| Project | Regenerate figures/results | Build PDF report | Needs |
|---|---|---|---|
| 01 | `cd 01-design-basis-sld && python scripts/build_all.py` builds the 8 SLD sheets (SVG/PDF/PNG), the combined A3 PDF and the DB-001 PDF. It also runs `scripts/check_drawings.py`, which fails the build if any text is below 2.5 mm at A3 or any text overlaps | (same script) | `google-chrome`, `pdfunite` (poppler) |
| 02 | (inside the report) | `cd 02-load-sizing && python report/build_report.py` | `google-chrome` |
| 03 | `cd 03-shortcircuit-protection && python scripts/make_all.py` (≈ 5 s) | `python report/build_report.py` | `google-chrome` |
| 04 | `cd 04-bess && python scripts/make_all.py` (≈ 60 s, includes the 4×4 sizing grid of LPs) | `python report/build_report.py` | `google-chrome` |

The report builders call `google-chrome --headless=new --print-to-pdf`. Without Chrome, the HTML is still written next to the PDF and can be printed from any browser.
报告脚本先生成 HTML，再用无头 Chrome 打印成 PDF。没有 Chrome 时，HTML 仍会生成，可以用任意浏览器打印。

Deployment, for example to Streamlit Community Cloud, has **not** been done. It needs your own GitHub and Streamlit login. See `02-load-sizing/README.md`.
部署（如 Streamlit Community Cloud）**尚未进行**，需要你本人的 GitHub/Streamlit 账号。
