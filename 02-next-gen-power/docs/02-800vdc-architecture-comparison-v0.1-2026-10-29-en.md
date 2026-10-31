# Project 02 (research and concept study, draft) · 800 VDC vs 400 VDC vs 400 V AC UPS for one 5 MW hall

| Header | |
|---|---|
| Title | 800 VDC architecture comparison, one-pager |
| Doc no. / version / date | DWU-DC-E-NOTE-005 · v0.1 · 2026-10-29 |
| Status | **CONCEPT / DRAFT — requires review by a licensed electrical engineer** |
| Campus | Same fictional campus as Projects 01 and 03–05: Dalarna SE3, 30 MW IT, 6 halls × 5 MW. Hall DH1, blocks A–D. |
| Assumptions | 4N/3 distributed redundancy as DB-001 Rev P2: block 1.25 MW normal, 1.67 MW in N-1, pair-group ≈ 0.83 MW. The 20 kV, T-A 2 500 kVA, G-A 2 750 kVA and IL-3 open transition are unchanged. Only the UPS and the LV critical distribution change. p.f. 1.0 is used for the AC currents [Inference]. |
| Codes (pointers) | IEC 60364 / SS 436 40 00 · EN 50600-2-2 · LVD 2014/35/EU · IEC 61439 · IEC 62040 · IEC 60947-2: all [Unverified]. ETSI EN 300 132-3 V2.3.1 [Verified]. |
| Drawing | SLD-005 (`02-next-gen-power/drawings/`) shows the 800 VDC block as an alternative to SLD-003. |

Labels: [Verified: opened source] · [Vendor claim] · [Search-level] · [Unverified] · [Inference]. Retrieval date is 2026-10-29 for every source. Where a page was opened for the KB on 2026-10-26 and not re-opened today, the label says "(KB 2026-10-26)".

| Row | A · 400 V AC + static UPS (Project 01 baseline) | B · 400 VDC class (260–400 V, 380 V typical) | C · 800 VDC (±400 V, "differential 800 Vdc") |
|---|---|---|---|
| Topology per block | 20/0.42 kV T-A → MSB-A → 2 × 1 000 kW VFI UPS → UOSB → 6 × 800 A AC busways (DB-001 P2) | T-A → MSB-A → rectifiers + battery on the DC bus → DC busway → rack | T-A → MSB-A → 2 × 1 000 kW rectifiers → DCB-A → DC feeders → rack DC/DC (SLD-005). Alternative B: SST from 20 kV straight to 800 VDC [Search-level, OCP SST spec v0.3.0] |
| Conversion stages, MV to 54 V | 3: UPS AC/DC + DC/AC, then rack PSU AC/DC (with PFC) [Inference] | 2: rectifier, rack DC/DC [Inference] | 2: rectifier (or SST), rack DC/DC [Inference]. NVIDIA: +5 % end-to-end efficiency [Vendor claim] |
| Pair-group feeder current, 0.83 MW in N-1 | ≈ 1 200 A per phase, 3 phases + N + PE [Inference] | ≈ 2 180 A at 380 V, 2 wires + PE [Inference] | ≈ 1 040 A at 800 V, 2 wires + PE [Inference]. "45 % less copper" is [Vendor claim] |
| Fault current | Source is T-A: MSB I″k 52.3 kA, Icw 65 kA (DB-001 P2). Closed-transition ATS would reach 81.8 kA, so it is blocked. | Battery-fed: a large, sustained fault current set by battery impedance [Inference] | Capacitor discharge in the first ms, then a current-limited rectifier / ESS. Mt. Diablo rack SCCR 10–40 kA [Verified (KB 2026-10-26)] |
| Protection | ACB / MCCB with ZSI and ARMS; mature IEC 61439 / 60947 kit [Inference] | DC MCCB / fuses; telecom practice exists [Inference] | SSCB vs thermal-magnetic is still an open question [Verified, Dell'Oro (KB)]. RCD per DC-PDU output and ground-fault detection mandatory [Verified, Mt. Diablo (KB)] |
| Earthing | TN-S per SS 436 40 00 (DB-001) | IT or midpoint-earthed, TBD [Inference] | High-resistance or solid, at the ±400 V midpoint or at 800 RTN, pros and cons in Annex A [Verified, Mt. Diablo (KB)] |
| Arc flash | IEEE 1584 applies. MSB line side 96 → 3.2 cal/cm² with ARMS (CALC-003) | NFPA 70E Annex D.5 DC methods (Doan max-power, Stokes-Oppenlander, Paukert) are informative only [Search-level] | Same gap, plus converter-fed transients. Annex D methods "overestimate" here [Vendor claim, Schneider]. IEEE P3002.12 DC arcing-fault guide: active PAR, approved 2026-09-25, 150–3 200 V DC [Verified] |
| Storage integration | LFP 2 × 165 kWh per block behind the UPS: 5 min at Pr EoL, 8.1 min in N-1 (DB-001). Campus BESS at 20 kV, not counted (CALC-004) | Battery directly on the bus (classic telecom style) [Inference] | ESS on DCB via DC/DC (SLD-005), rack BBU 45–90 s at 100 % load, and a capacitor CBU option. Peaks (175 % < 2 ms) must not trigger the BBU [Verified, Mt. Diablo (KB)] |
| Grid interface (20 kV) | UPS rectifier input; ripple and ramps per CALC-004; 3 MW/min (A) | Large rectifier fleet: harmonics and active front ends need study [Inference] | Same as B. SST adds MV power electronics at the POI side. OCP disturbance spec: compute load back to 90 % of pre-fault within 2 s [Verified (KB 2026-10-26), C5 wording]. Fingrid KJV2026 draft adds fault ride-through for > 30 MW demand [Verified] |
| Gensets / ATS | G-A on MSB-A, IL-3 open transition (DB-001) | Unchanged, AC side [Inference] | Unchanged with an LF transformer. With an SST there is no LV point for G-A, so MV gensets or an AC bus ahead of the SST are needed [Inference] |
| Maturity / standards | Mature: IEC 62040 UPS, IEC 61439, EN 50600-2-2 [Unverified pointers] | ETSI EN 300 132-3 V2.3.1 (2023): A3 interface 260–400 VDC; 380 V is an example operating voltage [Verified]. ITU-T L.1230 (10 kV AC to ≤ 400 VDC) [Search-level] | OCP Mt. Diablo v1.0.0, effective 2026-10-08 [Verified (KB)]. OCP SST v0.3.0 is an early draft [Search-level]. OCP says busway and layout are "still incomplete" [Verified (KB)]. Sidecar is the near-term form; facility-wide 800 V is an "ambition" [Verified, Dell'Oro (KB)] |
| Main risks | Copper volume and busway count at 80–130 kW AI racks [Inference] | High current at ≥ 1 MW racks; little AI-rack ecosystem [Inference] | DC breaker and arc-flash method gaps, SCCR coordination, untested O&M (LOTO, live-work rules), Swedish installation-rule interpretation of 800 V DC [Inference] |
| Missing data | Rack PSU efficiency for the actual IT | Real vendor ecosystem in 2026 | Rectifier fault current vs time, SSCB trip curves and Icw, DC busway ratings, DC-PDU IEC certification path, ESS-to-DC-bus control |

**Evidence vs inference.** Every cell marked [Verified] or [Vendor claim] comes from a source listed below. All current, stage-count and topology statements marked [Inference] are my own arithmetic or reading of the drawings (I = P / U, p.f. 1). Vendor percentages (85 % more power, 45 % less copper, 5 % efficiency, 30 % TCO) are not used as design inputs.

**What I would conclude (Inference).** For this campus, C with an LF transformer (SLD-005 main scheme) keeps the MV design, the gensets and IL-3 of Project 01 unchanged and moves the risk into one new place: the 800 V DC bus protection and arc-flash method. The SST variant (B on SLD-005) changes the genset and MV protection concept as well, so I would not take it into a Tier III / EN 50600 Class 3 design until the OCP SST spec is past v0.x. Option B (400 VDC) gives no current advantage over AC at these rack sizes.

### Sources (retrieval 2026-10-29)
1. Project 01 DB-001 Rev P2, CALC-003, CALC-004, this repository (own fictional design data).
2. NVIDIA, "800 V HVDC architecture…": https://developer.nvidia.com/blog/nvidia-800-v-hvdc-architecture-will-power-the-next-generation-of-ai-factories/ [Verified (KB 2026-10-24), benefit numbers Vendor claim]
3. Dell'Oro, "Inside OCP Global Summit 2026…": https://www.delloro.com/inside-ocp-global-summit-2026-cold-plates-800-vdc-sidecars-and-a-buildout-at-full-steam/ [Verified (KB)]
4. OCP Mt. Diablo Disaggregated Power Rack Spec v1.0.0: https://www.opencompute.org/wp-content/uploads/2026/10/OCP-Specification-Mt.-Diablo-Disaggregated-Power-Rack-Specification-v1.0.0.pdf [Verified (KB 2026-10-26)]
5. OCP SST spec v0.3.0: https://www.opencompute.org/documents/ocp-sst-design-specification-v0-3-final-pdf/ [Search-level]
6. OCP news, ecosystem vision (busway "still incomplete"): https://www.opencompute.org/news/realizing-the-ocp-open-data-center-ecosystem-vision/ [Verified (KB 2026-10-26)]
7. OCP disturbance-performance base spec v1.0.0: https://www.opencompute.org/wp-content/uploads/2026/10/OCP-Base-Spec-Interface-Specification-Between-Hyperscalers-and-Utility-Grid-for-Disturbance-Performance.pdf [Verified (KB 2026-10-26)]
8. ETSI EN 300 132-3 V2.3.1 (2023-01): https://www.etsi.org/deliver/etsi_en/300100_300199/30013203/02.03.01_60/en_30013203v020301p.pdf [Verified, opened 2026-10-29]
9. ITU-T L.1230 (08/2022): https://www.itu.int/epublications/publication/itu-t-l-1230-2022-08-specifications-of-10-kvac-input-and-up-to-400-vdc-output-integrated-power-system-in-data-centre-and-telecommunication-room [Search-level]
10. IEEE P3002.12: https://standards.ieee.org/ieee/3002.12/12720/ [Verified, opened 2026-10-29]
11. Schneider Electric WP219, DC arc flash at 800 VDC: https://download.se.com/files?p_Doc_Ref=SPD_WP219_EN&p_enDocType=White+Paper and blog https://blog.se.com/datacenter/2026/08/20/why-arc-flash-safety-analysis-is-critical-to-the-industrys-shift-to-800-vdc-in-ai-data-centers/ [Search-level; claims are Vendor claim]
12. Fingrid KJV2026 draft page: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-code-specifications/draft-for-comments-kjv2026-grid-code-specifications-for-demand-connections/ [Verified, opened 2026-10-29]

*D. Wu portfolio · fictional case · no employer, client or vendor data · CONCEPT / DRAFT — requires review by a licensed electrical engineer.*
