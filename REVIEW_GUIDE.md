# DWU Data-Centre Electrical Portfolio: Review Guide / 评审指南

Fictional 30 MW IT hyperscale campus, Dalarna (SE3), Sweden. Author: Donglin (Franklin) Wu. Package date: 2026-10-25, **Rev P2** (DB-001 Rev P2, SLD set Rev P2, CALC-002/003/004 Rev P1a with errata).
虚构的 30 MW IT 超大规模数据中心园区，位于瑞典 Dalarna（SE3 电价区）。

> **Data policy / 数据原则.** The portfolio uses only public standards and public market data, cited with the date accessed. Every other parameter is a plausible assumption marked **[ASSUMED]** or **(A)**. **No employer data (current or previous), and no client or vendor data.** It is a conceptual study, **not for construction or investment decisions**. The apps are not deployed.
> 只使用公开标准、公开市场数据（注明访问日期）和合理假设（标 [ASSUMED]/(A)）。**未使用任何雇主（现任或以前）数据**，也没有客户或厂家数据。本作品集仅为概念研究，**不可用于施工或投资决策**。应用尚未部署。

## 0. Package layout / 目录结构

```
dc-electrical-portfolio/   (repository root; also the GitHub Pages site root: index.html, projects/, assets/)
├── REVIEW_GUIDE.md                  ← this file / 本文件
├── run_apps.md                      ← how to run apps, scripts and reports / 运行说明
├── run_all_tests.sh                 ← runs all 4 test suites (102 tests) / 一键运行全部测试
├── requirements.txt                 ← one environment for all projects / 统一依赖
├── ASSUMPTIONS_REGISTER_ALL.csv     ← 188 rows from 01 and 03–05 (generated) / 全部假设汇总
├── TODO_final_fixes.md              ← fixes and rating changes, with status (A/B done, C mostly open) / 修改清单及状态
├── tools/build_assumptions_register.py
├── 01-design-basis-sld/             ← DB-001 Rev P2 + SLD-000…004 (8 A3 sheets)
├── 02-next-gen-power/               ← research and concept study: NOTE-005 (800 VDC), SLD-005, CX-005 (commissioning), v0.1 drafts
├── 03-load-sizing/                  ← dcsizing + Streamlit app + CALC-002
├── 04-shortcircuit-protection/      ← scprot + CALC-003
└── 05-bess/                         ← bessdc + Streamlit app + CALC-004 (+ context/ FIG-004S storage layers, v0.1 draft)
```

How the projects depend on each other / 依赖关系: 01 (numbers in the design basis) → 03 `dcsizing` → 04 `scprot` (imports 03's conductor tables) → 05 `bessdc` (imports 03's PUE bins and 04's relays and fault levels). Every project's rating changes feed `TODO_final_fixes.md` §B.

Suggested review order / 建议评审顺序: read each project's PDF report first, then this guide's §2 (algorithms), then the code at the locations given, and run the tests last.

| # | Project | Deliverable (PDF) | Code | Tests |
|---|---|---|---|---|
| 01 | Design basis & concept SLD (Rev P2) | `01-design-basis-sld/docs/DWU-DC-E-DB-001_Design_Basis.pdf`, `drawings/DWU-DC-E-SLD_concept_set_RevP2_A3.pdf` | `scripts/` (≈ 1 610 lines, matplotlib) | 10 (render + labels per sheet, text height/layout check, DB Rev P2) |
| 02 | Research and concept study: 800 VDC + commissioning (CONCEPT / DRAFT) | `02-next-gen-power/docs/02-800vdc-architecture-comparison-v0.1-2026-10-29-en.pdf`, `02-next-gen-power/drawings/SLD-005_800VDC_block_A_concept-v0.1-2026-10-29-en.pdf`, `02-next-gen-power/docs/02-commissioning-test-plan-concept-v0.1-2026-10-29-en.pdf` | `scripts/` (drawing and PDF builders) | none |
| 03 | Load calculation & equipment sizing | `03-load-sizing/report/DWU-DC-E-CALC-002_Load_and_Sizing_Calc.pdf` | `dcsizing/` (≈ 950 lines), `app.py` | 44 + 2 AppTest |
| 04 | Short-circuit, protection, arc flash | `04-shortcircuit-protection/report/DWU-DC-E-CALC-003_ShortCircuit_Protection_ArcFlash.pdf` | `scprot/` (≈ 1 110 lines) | 23 |
| 05 | BESS: peak shaving, backup, markets, AI | `05-bess/report/DWU-DC-E-CALC-004_BESS_Study.pdf` | `bessdc/` (≈ 990 lines), `app.py` | 21 + 2 AppTest |

---

## 1. Purpose of each project / 各项目目的

**01 Design basis & SLD / 设计基础与概念单线图.**
* 中文：定义园区，包括 40 MW 签约容量、两回 130 kV 进线、2×63 MVA 主变、20 kV MSG-20、6 个机房×5 MW、每厅 4 个 2.5 MVA 电力块（DR 4N/3）、UPS + LFP、柴油发电机组（HVO）。Rev P2 已并入 03–05 的全部 31 项额定值修改，共 8 张 A3 单线图：图例、130 kV 变电站、MSG-20、机房中压/低压、白区与机械、电力块 MV/LV、UPS/关键回路、储能。图上所有文字 ≥ 2.5 mm，并按 IEC 60617 画出 CT、VT、避雷器、接地开关、继电保护编号、电能表、电弧传感器和联锁。
* EN: Defines the campus, its redundancy concept (distributed redundant 4N/3 + 2N mechanical), the ratings and the network data for 04. Rev P2 brings in all 31 rating changes from 03–05 and has 8 A3 SLD sheets drawn in Python. Every text on them is ≥ 2.5 mm, and the sheets use IEC 60617 symbols (CT, VT, surge arrester, earthing switch, relays, meters, arc sensors, interlocks).

**02 Next-generation power architecture and commissioning (research and concept study).**
* EN: A research and concept study on the same fictional campus, not built or commissioned work. NOTE-005 compares 400 V AC + UPS, 400 VDC and 800 VDC for one 5 MW hall; SLD-005 redraws block A as an 800 VDC concept; CX-005 is an L0–L5 commissioning and test plan concept with genset and MV switchgear selection points. All ratings come unchanged from DB-001 Rev P2 and CALC-003/004. Statements carry credibility labels: [Verified], [Vendor claim], [Search-level], [Unverified] or [Inference].

**03 Load & sizing / 负荷计算与设备选型.**
* 中文：从 IT 负荷推算设施负荷（UPS 损耗、随温度变化的机械 pPUE、配电损耗、电池充电），再按 N-1 工况完成变压器、发电机、UPS/电池、电缆和母线槽选型，并计算年化 PUE。用 Streamlit 工具和 CALC-002 报告与 01 的额定值对比，找出 11 项需要修改的额定值。
* EN: Takes the IT load to the facility load, then sizes the transformer, genset, UPS/battery, cables and busway in normal and failure modes, and computes the annualised PUE. Result: design peak 37.8 MW (42.6 MW with recharge), PUE 1.165, MSB I''k 53.8 kA.

**04 Short-circuit & protection / 短路、保护配合与电弧闪络.**
* 中文：自编 IEC 60909 节点导纳求解器，计算 7 个场景，并用 pandapower 交叉验证。完成 20 kV 到机柜的保护配合（IEC 60255 曲线、LSI、MCB）、CT 校核、IEEE 1584-2018 电弧能量，以及 20 kV 中性点接地方式比较。
* EN: Own IEC 60909 solver over 7 scenarios, cross-checked with pandapower. Also covers the coordination study, CT checks, arc flash, and compensated vs resistance earthing. Main findings: keep the T1//T2 interlock, use open-transition retransfer only, add current-limiting MCCBs for the busway, and add optical arc protection.

**05 BESS / 储能研究.**
* 中文：10 MW / 20 MWh 储能接在 MSG-20 预留间隔，研究 (a) 40 MW 限值下的削峰与增加 IT 容量（LP）；(b) 备用电源角色的边界（Tier III、发电机额定类别、孤岛故障电流）；(c) FCR-N/FCR-D/mFRR/套利收益叠加，以及与削峰的兼容性；(d) AI 训练负荷功率波动平滑；(e) 商业案例与敏感性分析。
* EN: Five studies in one package, plus a Streamlit tool. Main findings: the recharge peak already exceeds 40 MW; the BESS is energy-limited, adding only +0.84 MW of firm IT capacity; it cannot replace gensets; revenue depends on prices; AI ripple needs a response of about 10 ms or faster.

---

## 2. Algorithms, formulas and code locations / 算法、公式与代码位置

### 2.1 Project 01: drawings (Rev P2)
| What | Where | Note |
|---|---|---|
| IEC 60617-style symbol library: CB, withdrawable CB, disconnector, switch-disconnector, fuse, earthing switch, CT, VT, surge arrester, transformer, earthing, genset, UPS compound, SBS, battery, Petersen coil, BTS, meter, relay box, arc sensor, interlock, control line, off-page arrow; A3 frame and uniform 180 mm title block (drawing number 14 pt, all other title-block text 10 pt); `monochrome()` export pass (pure black on white, voltage level by line weight, hollow UPS busbar) | `01-design-basis-sld/scripts/sld_lib.py` | 1 mm = 1 drawing unit at A3; fonts set by cap height (DejaVu Sans cap = 0.729 em): 10 pt = 2.57 mm, 14 pt = 3.6 mm (tags and drawing number) |
| Sheet generators | `scripts/sld000_legend.py`, `sld001_sh1_substation.py`, `sld001_sh2_msg20.py`, `sld002_sh1_hall_mv.py`, `sld002_sh2_whitespace.py`, `sld003_sh1_block_mvlv.py`, `sld003_sh2_block_ups.py`, `sld004_bess.py`; list in `sheets.py` | A3 landscape, SVG/PDF/PNG |
| Drawing checker | `scripts/check_drawings.py` | Parses each SVG. Checks: cap height of every text ≥ 2.5 mm; text/text overlap with 0.8 mm clearance; text/line crossings (Liang–Barsky clipping); text inside the sheet. Writes `drawings/text_height_check.json`; non-zero exit on failure |
| Build | `scripts/build_all.py` | sheets → pdfunite set → checker → markdown → HTML → Chrome PDF (DB-001 with all 8 sheets in Appendix A) |

### 2.2 Project 03: `dcsizing`
| Topic | Formula / method | Code |
|---|---|---|
| UPS losses | η(load) interpolated from a VFI curve [ASSUMED]; loss = P_IT(1/η − 1) | `load.py:7 ups_efficiency`, `tables.py` |
| Mechanical pPUE | Free cooling (0.05) up to T_free; linear to 0.17 at +32 °C; extrapolated above | `load.py:12 mech_ppue` |
| Hall / campus load | P = IT + UPS loss + mech + dist_loss·(…) + house; recharge is non-coincident | `load.py:50 hall_load`, `:63 campus_demand` |
| Annualised PUE | Σ_bins h·P(T)/Σ h·IT over 8 760 h of temperature bins (SMHI-shaped [ASSUMED]) | `load.py:76 annual_pue`; inverse `:100 solve_mech_peak_for_target_pue` |
| Redundancy | DR: P/n normal, P/(n−1) failure; 2N; N+1; BR | `scenario.py:66 block_loads` |
| Transformer | Choose the smallest standard size with failure loading ≤ 100 % and normal ≤ 80 %; losses P0 + Pk·x² | `transformer.py:8, :21` |
| I''k (IEC 60909) | Z_Q = c·Un²/S''k; Z_T = uk·Un²/Sr with R_T = Pk·Un²/Sr², K_T = 0.95·c_max/(1+0.6·x_T); I''k = c·Un/(√3·|Z|); ip = κ√2·I''k | `transformer.py:30–76` |
| Genset | Derating for temperature and altitude; loading ≤ 90 % of DCC; largest step ≤ 33 %; ΔU ≈ x'd·s/(1+x'd·s); HVO fuel and tank volume | `generator.py:7–68` |
| UPS battery | E = P·t/(η_dc·DoD·EoL·k_T); C-rate = P_dc/E_EoL ≤ 8 C | `ups.py:19–54` |
| Cables | Iz = I0(B.52)·k_amb·k_group ≥ In ≥ Ib; ΔU % per Annex G; adiabatic S ≥ √(I²t)/k (Table 43A); I''k at the cable end | `cables.py:10–111` |
| Busway | Ambient derating, ΔU with distributed load ×0.5, Icw ≥ I''k flag | `busway.py:7` |
| Whole campus + checks | `Inputs` → `run()` → flags; `rating_changes()` compares with phase 1 | `scenario.py:28, :88, :275` |
| UI | Streamlit, 6 tabs | `03-load-sizing/app.py` |

### 2.3 Project 04: `scprot`
| Topic | Formula / method | Code |
|---|---|---|
| Nodal solver | Build Y_bus from branches and shunts; Z_bus = Y⁻¹ over the energised nodes; I''k = c·Un/(√3·|Z_kk|); branch contributions from node voltages | `iec60909.py:51 Network`, `:74 _ybus`, `:110 zbus`, `:119 fault` |
| Correction factors | K_T = 0.95·c_max/(1+0.6x_T); K_G = Un/UrG · c_max/(1+x''d·sinφ) | `iec60909.py:192, :197` |
| ip, Ib, Ith | κ by method C (R/X at fc = 20 Hz); Ib = μ·I''k (μ from IkG/IrG and t_min); Ith = I''k·√(m+n) | `iec60909.py:119–190`, `GenDecrement :227` |
| Campus model and scenarios | S0 max/min, S1 T1//T2, S2 N-1, S3 closed transition, S4 genset island, S5/S5b couplers | `campus.py:16 Data`, `:87 Scenario`, `:125 build`, `:185 run_all` |
| Cross-check | pandapower `calc_sc` on the same network | `pp_model.py:14, :65` |
| Relay curves | IEC 60255-151: t = TMS·k/((I/Is)^α − 1); SI 0.14/0.02, VI 13.5/1, EI 80/2; instantaneous 50 | `protection.py:18 iec_time`, `:27 Relay` |
| LV devices | Generic LSI band (IEC 60947-2) and C-curve MCB (IEC 60898-1) | `protection.py:61 LSI`, `:108 MCB` |
| Grading | Margin over the current range ≥ CTI 0.3 s; automatic TMS pick | `protection.py:136 margin`, `:162 pick_tms` |
| CT check | ALF' with burden; Ith ≥ I''k over 1 s; saturation flag | `protection.py:174 CT` |
| Transformer withstand | IEC 60076-5 damage curve, inrush point 12×In at 0.1 s | `protection.py:199, :209` |
| Arc flash | IEEE 1584-2018 (arcflash-calc, iterated with the clearing time); Lee method at 20 kV | `arcflash.py:50 ieee1584`, `:70 lee` |
| Earthing | Ic = 3ωC0·U/√3 per section; compensated vs 500 A resistance; EPR = r·Ik1·Re vs 2·UTp (EN 50522) | `earthing.py:13–75` |
| Study assembly | Tables, selectivity, genset/UPS checks, rating checks, S1 sensitivity | `study.py:198 run` |

### 2.4 Project 05: `bessdc`
| Topic | Formula / method | Code |
|---|---|---|
| Assumptions | Every parameter is `A(value, tag, note, src)` with tag PUBLIC / ASSUMED / PROJECT; `register()` exports them to CSV | `assumptions.py:40, :128` |
| Hourly profiles | AR(1) temperature + seasonal + 5-day heat wave; PUE(T) calibrated to the CALC-002 bins (37.818 MW); diurnal utilisation; UPS recharge event; synthetic spot prices (Nord Pool SE3 2025 mean) and capacity prices (Svk/Mimer) | `profiles.py:37–118` |
| (a) Max extra IT | LP: max x s.t. L_t + x·s_t + c_t − d_t ≤ P_lim; e_t = e_{t−1} + η_c·c_t − d_t/η_d; SOC window [5 %, 95 %]·E; c,d ≤ P; cyclic SOC; x is free (can be negative). HiGHS, sparse | `dispatch.py:57 max_extra_it`, `:39 _soc_rows` |
| (c) Co-optimisation | LP: max Σ cap_price·r·avail + Σ spot·(d − c) − deg·d − FCR-N loss − 5000·ov; headroom c + Σr_dn ≤ P, d + Σr_up ≤ P; endurance e ≥ Emin + Σ r_up·h/η_d, e ≤ Emax − Σ r_dn·h·η_c (FCR-N 1 h, FCR-D 20 min, mFRR 1 h); grid L + c − d − ov + Σ r_dn ≤ P_lim | `dispatch.py:97 co_optimise` |
| (b) Backup | Autonomy = E_usable/P; full genset replacement = 24 h × mean load; island fault current 1.2·In = 381 A at 20 kV checked against 04's relays and ACBs (`dev.clear(I)`) | `backup.py:30–61` |
| (d) AI smoothing | dt = 0.02 s, 3 600 s. Command = LPF(30 s) + k_soc·(SOC_ref − SOC) → rate limiter (R MW/min); actuator = transport delay + 20 ms first-order loop; hybrid split at τ = 5 s with a 5 ms supercap. Metrics: max 1-min change, 1-s ramp, 0.1–2 Hz band p-p (FFT mask), P and E needed | `ai_swing.py:20 ai_profile`, `:53 _Actuator`, `:72 smooth`, `:105 band_pp`, `:119 metrics`, `:152 hybrid` |
| (e) Business | CAPEX = (c_E·E + c_P·P)·1.2 + 0.3 M€; yearly revenue interpolated between LPs at SOH 1.0 and 0.8 × realisation 0.85 × price trend; SOH fade = calendar + EFC/cycle_life·0.2, augment back to 0.9 below 0.8; NPV at WACC 7 %, IRR by brentq; tornado; 4×4 P × duration grid | `business.py:14 capex_eur`, `:49 cashflows`, `:75 kpis`, `:110 tornado`, `:137 sizing_grid` |
| Orchestration and figures | `study.run()` → `scripts/make_all.py` (7 figures, 7 result files) → `report/build_report.py` | `study.py:80` |
| UI | Streamlit, 7 tabs; widgets re-solve the LPs live (cached) | `05-bess/app.py` |

---

## 3. How to run / 如何运行

See `run_apps.md` for details. 详见 `run_apps.md`。Short version:
```bash
cd dc-electrical-portfolio
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
bash run_all_tests.sh                                 # expect 102 passed / 预期 102 个测试全部通过
cd 03-load-sizing && streamlit run app.py            # tool 1 / 工具一
cd ../05-bess && streamlit run app.py --server.port 8502   # tool 2 / 工具二
```
What the tests cover / 测试内容:
* 01: each of the 8 sheets renders, and its key labels and ratings are present. `check_drawings.py` asserts a cap height ≥ 2.5 mm at A3 and no text/text or text/line overlap. The DB is Rev P2.
* 02: unit tests of every sizing function against hand calculations and standard tables, plus a full-scenario regression and 2 Streamlit AppTests.
* 03: IEC 60909 hand values, pandapower agreement, IEEE 1584 Annex D example, grading margins, CT and earthing checks.
* 04: profile calibration, LP feasibility and monotonicity, energy balance, LER endurance, grid limit including down-activation, AI metrics vs response time, NPV and IRR consistency, assumptions register, 2 AppTests.

---

## 4. Assumptions register / 假设登记

The full list is in **`ASSUMPTIONS_REGISTER_ALL.csv`**: 188 rows from Projects 01 and 03–05 (Project 02 changes no rating and adds no rows; its documents list their own assumptions in the header), with columns project, group, name, value, tag, note and source. Regenerate it with `python tools/build_assumptions_register.py`. Per-project sources:
完整清单见 CSV。各项目来源：01 = DB-001 Rev P2 第 3/8.1 节（假设）及第 8 节（Rev P2 额定值，标 PROJECT rating）；03 = `dcsizing/tables.py` 及代码中的 [ASSUMED] 标记；04 = `scprot/campus.py Data`、`earthing.py EarthingData`；05 = `bessdc/assumptions.py`（含来源与访问日期）。

The assumptions that drive the results most / 对结果影响最大的假设:

| Project | Assumption | Value | Effect if wrong / 若不成立的影响 |
|---|---|---|---|
| 01 | Grid S''k at 130 kV | 3 000 / 1 500 MVA, X/R 10 | All fault levels (04). The S1 margin goes negative above about 4 000 MVA |
| 01 | Subscribed capacity | 40 MW, p.f. ≥ 0.95 | Headroom for the whole of 05(a) |
| 01/02 | Climate | Mean +4.5 °C, design +32 °C, SMHI-shaped bins | PUE 1.165 and design peak 37.8 MW |
| 03 | UPS efficiency curve, pPUE 0.05 → 0.17 | vendor-typical | PUE and the size of every upstream device |
| 03 | LFP EoL 0.8, DoD 0.9, C_max 8 | datasheet-typical | Battery 165 kWh per module (TODO B1) |
| 03 | Genset step ≤ 33 %, x'd 0.22 | typical | Genset selection and voltage dip |
| 04 | UPS inverter current limit | 2.0 × In for 100 ms | Selectivity downstream of the UPS in inverter mode |
| 04 | Busway Icw/Z, CT Ith 100 × Ipn, VCB 60 ms | vendor-typical | Busway MCCB requirement, CT adequacy, arc energy |
| 04 | Earth resistance 0.2 Ω, reduction factor 0.6 | typical | EPR vs EN 50522 (open point) |
| 05 | Capacity prices (2025 / 2026 / saturated) | Svk/Mimer means; "saturated" = ½ × 2026 [ASSUMED] | Revenue 4.15 / 1.82 / 0.96 M€/yr; NPV 22.8 / 7.2 / 2.0 M€ |
| 05 | Realisation 0.85, availability 0.97, degradation 15 €/MWh | ASSUMED | NPV scales roughly linearly |
| 05 | BESS cost 120 €/kWh + 75 €/kW, ×1.2 BoP | BNEF 2025 Europe turnkey ≈ 157 €/kWh at 2 h | CAPEX 4.08 M€ |
| 05 | PCS fault current 1.2 pu, response 150 ms | generic | Island protection; AI ripple 5.6 MW p-p |
| 05 | AI load: 12 MW synchronous, 6 s iteration, 1 MW osc. limit, 3 MW/min ramp | ASSUMED (after NERC 2025 large-loads discussion) | Power and energy needed for smoothing |
| 05 | Extra IT value 100 k€/MW·yr | ASSUMED | Each 100 k€ adds about 2.2 M€ NPV |

---

## 5. Limitations / 局限性

* 中文：
  1. 全部为概念级计算；04 已用 pandapower 交叉验证，PowerFactory 结果正在整理，之后会上传。
  2. 厂家数据均为典型值，包括 LV 脱扣曲线、UPS/PCS 故障电流、母线槽 Icw、变压器损耗。
  3. 01 图纸为概念级：IEC 60617 符号已补齐，但图例未标注 IEC 60617 条目编号（未逐条核对数据库）；A3 字高已用程序测量，但尚未做实物打印测试。
  4. 03 未建模电机启动、谐波/K 系数，以及电缆间互热（分组系数以外）。
  5. 04 的 20 kV 电弧能量用 Lee 法，偏保守；接地只做筛查，没有土壤模型。
  6. 05 的负荷、电价为合成曲线且假设完全预知，小时分辨率；未考虑市场深度、报价策略和聚合商费用；AI 负荷与电网限值为假设；Tier III/EN 50600 的结论为概念解读，非认证意见。
  7. 应用未部署；PDF 均为本机无头 Chrome 打印。
* EN:
  1. Concept-level work. 04 is cross-checked with pandapower; PowerFactory results are being prepared and will be uploaded later.
  2. Generic vendor data throughout.
  3. The drawings are concept level. The legend does not show IEC 60617 item numbers, and no physical A3 print test has been done (text height is measured in software).
  4. 03 has no motor-starting or harmonics model.
  5. 04 uses the Lee method at MV and only screens earthing.
  6. 05 uses synthetic, perfect-foresight hourly profiles and models no market depth. Its AI and grid-code limits are assumed, and its Tier III statements are interpretations.
  7. Nothing has been deployed.

---

## 6. TODO status / 修改清单状态

The full list, with a status for every row, is in `TODO_final_fixes.md`. 完整清单及每项状态见该文件。
* **A. Drawings / 图纸: DONE / 已完成.**
  * A1: 8 sheets were measured. Minimum cap height 2.57 mm, tags 3.6 mm, drawing number 3.6 mm, 0 overlaps.
  * A2: IEC 60617 symbols are drawn: CT, VT, SA, ES, relays, meters, Petersen coil, arc sensors, interlocks.
  * A3: re-exported, with set PDF `DWU-DC-E-SLD_concept_set_RevP2_A3.pdf`.
  * Not done: a physical A3 print test, and IEC 60617 item numbers on the legend.
* **B1–B31. Rating changes / 额定值修改: DONE / 已完成** in DB-001 Rev P2 (traceability table §12) and the SLDs.
  * B3 is superseded by B15 (MCCB Icu ≥ 50 kA, tested conditional ≥ 40 kA instead of "Icc ≥ 55 kA").
* **C. Housekeeping / 其他:**
  * Done: the 04 cross-check, and the DB revision table.
  * Partly done: the PCS fault factor is aligned to 1.2 × In everywhere.
  * **Open / 未完成, because they need DSO or vendor data:**
    * 130 kV earthing study
    * manufacturer curves and selectivity tables
    * confirmation of the assumed data
    * final arc-flash labels
    * DSO/Svk confirmation of export, FCR and market depth, and a vendor PCS fault curve
    * load-bank feeder Q-LB 2 500 A (≈ 1.73 MVA) is below the full genset rating: upsize or state the limited test output (DB-001 §7.4, §11 item 9)

### 6.1 Errata in the calculation reports / 计算报告勘误

The calculation results are unchanged. Each report has a new last sheet, "Revision history and errata", and its page 1 says where to find it.
计算结果不变。各报告新增最后一页"修订记录与勘误"，首页注明页码。
* **CALC-002 (sheet 4):**
  * Superseded: "current-limiting MCCB Icc ≥ 55 kA" (B3). It is replaced by CALC-003 / B15.
  * B1–B11 are implemented in DB/SLD Rev P2.
  * Pk is 19 kW.
  * The 42.6 MW recharge peak is handled in DB §5.2.
  * Note: the `dcsizing` code and app still print the original B3 wording, on purpose, so that they reproduce the P1 report. The erratum covers it.
* **CALC-003 (sheet 6):**
  * Superseded: "no BESS contribution". It is replaced by CALC-004: 13.3 / 23.1 kA, 92 % of 25 kA, PCS 1.2 × In, Ic +1 A.
  * B12–B21 are implemented.
* **CALC-004 (sheet 5):** B22–B31 are implemented in DB §7.5–7.6 and SLD-004. Editorial 2026-10-29: the genset rating on sheet 2 now reads DCC, as in DB-001.
* **DB-001 (editorial 2026-10-29, Rev P2 kept):** MSG-20 SF₆-free is required (EU 2024/573), and the Q-LB load-bank limit is recorded as an open point. No rating changed.

## 7. Key results at a glance / 主要结果

| Project | Result |
|---|---|
| 03 | Block 1 250 / 1 667 kW (normal / N-1); transformer 2 500 kVA at 82 % N-1; genset 2 750 kVA at 88 %; MSB 53.8 kA; 20 kV 13.0 kA; campus 37.8 MW (42.6 MW with recharge); PUE 1.165 |
| 04 | MSG-20 13.0 kA; MSB-A 52.3 kA / ip 122 kA; S1 ip 58.5 kA = 94 % of 62.5 kA; S3 81.8 kA > 65 kA; busway 37.1 > 36 kA; MV CTI ≥ 0.30 s; arc flash 96 → 3.2 cal/cm² |
| 05 | Headroom −2.08 MW without a BESS; +2.41 MW (firm +0.84 MW) with 10 MW / 20 MWh; 27 min backup; island 381 A not cleared by 20 kV relays; revenue 1.82 M€/yr (2026); AI needs 11.4 MW / 0.46 MWh, ripple needs ≲ 10 ms; NPV 7.2 M€, IRR 34 %, payback 2.7 years |
