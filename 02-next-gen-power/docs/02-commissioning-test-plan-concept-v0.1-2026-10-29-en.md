# Commissioning & test plan (concept), with genset and MV switchgear selection points

| Header | |
|---|---|
| Title | Commissioning & test plan (concept) for the fictional 30 MW IT campus, plus genset and MV switchgear selection points |
| Doc no. / version / date | DWU-DC-E-CX-005 · v0.1 · 2026-10-29 |
| Status | **CONCEPT / DRAFT — requires review by a licensed electrical engineer** |
| Scope | The campus of Projects 01 and 03–05 (Dalarna SE3, 6 halls × 5 MW IT), with hall DH1 as the worked example. It is part 2 of Project 02 (research and concept study). A short section covers what changes if the same campus were built in Finland. |
| Assumptions | All ratings come from DB-001 Rev P2 and CALC-003/004 and are not changed here. Commissioning "levels" are industry practice, not one standard [Inference]. The test durations and acceptance values below are my proposals [Inference] unless a source is given. Nothing here describes work I have done or signed for. I hold no Swedish elinstallatör authorisation, and design and installation responsibility stays with the authorised parties. |
| Codes (pointers) | IEC 60364 / SS 436 40 00 · SS-EN 61936-1 · EN 50600-2-2 · LVD 2014/35/EU · IEC 62271-200 · IEC 61439 · IEC 62040-3 · ISO 8528-1/-5 · IEC 61850: all [Unverified] unless opened. EU F-gas Regulation 2024/573 Art. 13(9) [Verified]. |

Labels: [Verified: opened source] · [Vendor claim] · [Search-level] · [Unverified] · [Inference]. Retrieval date for all sources is 2026-10-29. Regulation and grid-code items carry their assumption and stay [Unverified] unless the page was opened.

## 1. Commissioning levels used here

There is no single standard that defines "L1–L5". Vendors and consultants use similar but not identical lists [Search-level: HIOKI, Avtron, Aggreko, constructandcommission, sources 9–12]. The structure below is a common form; the campus content in each row is mine [Inference].

| Level | Purpose | Campus content (DH1 example) | Evidence produced |
|---|---|---|---|
| L0 Design review | Check that the design can be tested | Load-bank points on every MSB (DB-001 §7.4); test switches and CT test blocks in relays; IEC 61850 test mode; a way to load-test the 20 kV feeders | Commented design, test-point list |
| L1 FAT | Factory acceptance test | MSG-20 and HV-DH1: routine tests, interlock check, relay settings loaded. UPS 2 × 1 000 kW: IEC 62040-3 type and routine reports [Unverified], step-load and transfer test at the factory. Gensets: load acceptance steps, Isc ≥ 300 % for 2 s (DB-001), −30 °C rating evidence (DB-001 design range) | FAT reports, witnessed |
| L2 Delivery / installation | Receipt and installation checks | Transport damage, torque marking on busways, cable test (VLF / tan δ on 3×1×240 Al 20 kV feeders [Inference]), IR and continuity on LV | Installation checklists |
| L3 Start-up / pre-functional | Energise each item alone | Primary and secondary injection, CT polarity, 87T stability, 67N direction on the resonant-earthed 20 kV network, Petersen coil tuning, battery string checks | Energisation records |
| L4 Functional | Each system under its own load | Genset on load bank via Q-LB; UPS on load bank (rectifier walk-in, battery discharge); ATS IL-3 open-transition timing; EPMS point-to-point | Functional test scripts signed |
| L5 IST | All systems together under heat load | Utility loss, genset start, ATS and UPS transfer, redundancy and recovery while white space carries load-bank heat (see §3) | IST report, punch list |

## 2. Load-bank plan and one constraint I found in our own design

- Each MSB has a load-bank connection, Q-LB 2 500 A (DB-001 §7.4, SLD-003).
- At 400 V, 2 500 A is √3 × 0.4 kV × 2.5 kA ≈ 1.73 MVA. The IT genset is 2 750 kVA / 2 200 kWe. Through Q-LB alone, a genset can therefore be tested to about 1.73 MW at p.f. 1. That is 79 % of kWe and 63 % of kVA [Inference, arithmetic].
- The N-1 design point of a block is 1.67 MW (DB-001), which is 96 % of what Q-LB can carry. The **block design load can be proven through Q-LB, but the genset's full rating cannot**. The genset's own N-1 design load, including UPS losses and recharge, is ≈ 1.93 MW (CALC-002), which is also above Q-LB [Inference, arithmetic]. DB-001 §7.4 records this as an open point.
- Options: a second load-bank point, a temporary connection on the genset side of Q-GI, or full-rating tests at the factory only (L1) [Inference]. I would raise this at L0.
- White-space heat load for L5: 5 MW per hall ≈ 200 rack-mounted load banks at 25 kW, or AI-row units at 80–130 kW per rack position. They are fed through the normal busways and tap-offs so the real path is tested [Inference].
- Cummins gives a rule of thumb that a genset should run above 30 % of its rating to limit wet stacking [Vendor claim, source 4]. That supports monthly testing on the load bank or on the building load rather than at no load.

## 3. Integrated systems test (L5), DH1 scenarios

All scenarios run with the hall at its stated heat load from load banks. Acceptance values are proposals [Inference] unless a document is named.

| # | Scenario | Expected behaviour (from the design) | Pass check |
|---|---|---|---|
| 1 | Loss of one 130 kV line | H-arrangement keeps both 63 MVA transformers fed; no 20 kV interruption | No UPS on battery |
| 2 | Loss of T1 (130/20 kV) | 20 kV coupler auto-closes only after the T1 incomer is proven open. Break-before-make, **2-of-3 logic: at most two of the incomer A, incomer B and coupler closed**. T1//T2 never parallel (DB-001 §7.2) | Interlock blocks a third close; UPS rides through |
| 3 | Total grid loss | All block UPSs on battery; G-A to G-D start; on load ≈ 10–15 s (CALC-004); ATS transfers by open transition (IL-3) | IT load not interrupted; UPS battery time used < 5 min |
| 4 | One genset fails to start | Under 4N/3 the other three blocks carry 5 MW at 1.67 MW each, 83 % of UPS and 88 % of the genset (DB-001). The BESS is not counted (CALC-004) | No pair-group lost |
| 5 | Block failure (UPS output fault on block A) | Pair-groups AB, AC and AD shift to B, C and D | Busway and STS/ATS loading ≤ design |
| 6 | Retransfer to grid | Open transition only. Closed transition is blocked because it would give 81.8 kA against a 65 kA rating (DB-001) | Interlock proven by attempting a closed-transition command |
| 7 | UPS battery discharge | Run on battery at block load until the low-voltage alarm; compare with 5 min at Pr EoL / 8.1 min in N-1 (DB-001). A new battery gives a longer time; correct for state of health [Inference] | Measured time ≥ the design value corrected to BoL |
| 8 | MBB / SBS maintenance transfer | Key-interlocked wrap-around bypass (DB-001 §7.4) | Key sequence cannot be broken |
| 9 | Arc-flash protection trip | Optical arc relay on MSB-A trips S1-Q1A (20 kV). ZSI and ARMS function (DB-001 §7.4) | Trip by test light and primary-injection current check |
| 10 | Fuel transfer under genset load | Day tank refill while running; pump power path concurrently maintainable [Verified, Uptime source 1] | No genset derate |
| 11 | BESS island / grid events (optional) | Not part of the Tier III design (CALC-004) | Only after a separate island protection study |

## 4. Genset selection points (campus-specific)

- **Rating basis.** DB-001 uses 2 750 kVA / 2 200 kWe **DCC**, a manufacturer's data-centre continuous rating.
  - Uptime's Tier III/IV requirement is that engine generators carry the design load with no limit on runtime; Uptime treats the utility as an "economic alternative". These are quoted via a Cummins white paper, so they are [Vendor claim] until the Uptime original is opened (source 4).
  - The same paper says Uptime accepts a manufacturer's certification of unlimited duration, including a site-specific rating letter [Vendor claim].
- **ISO 8528-1 rating words** (ESP, PRP, COP, LTP and DCP from 2018) [Search-level, sources 4–5].
  - Cummins states that ISO **DCP** is "not appropriate" for Uptime Tier III/IV, because its definition references a reliable utility [Vendor claim].
- **Load steps.**
  - IT gensets see the UPS rectifier walk-in, not a hard step. Rectifier ramp time and the ISO 8528-5 performance class should be in the specification [Unverified].
  - Mechanical gensets are governed by the 400 kW chiller step ≤ 33 % (DB-001).
- **Short-circuit support.** Sustained Isc ≥ 300 % for 2 s (PMG or AREP) so the genset ACB, with Isd ≤ 2.5 × Ir, and downstream devices trip (DB-001). Verify at FAT with an alternator test report.
- **Fuel.**
  - HVO100 for 24 h at design load, ≈ 51 m³ gross per hall (DB-001).
  - Uptime sets at least 12 h at N for all Tiers. Stored fuel counts only after removing the redundant tank [Verified, source 1].
  - The engine maker's HVO approval is needed in writing (fuel standard reference [Unverified]).
- **Climate.** Gensets are rated −30 … +35 °C for a −28 °C winter design (DB-001). The cold-start and low-load behaviour evidence should come from the vendor; I found no source on cold-climate commissioning tests and do not add one.
- **Paralleling.** Not used: one genset per block, no paralleling bus, open-transition ATS only (DB-001).

## 5. MV switchgear selection points (MSG-20 and HV-DH1)

- **Ratings** as in DB-001: MSG-20 24 kV, 2 500 A, 25 kA / 3 s, Ip 62.5 kA. HV-DH1 24 kV, 1 250 A, 25 kA / 1 s.
- **Classification** per IEC 62271-200 as written in DB-001: LSC2B-PM and IAC AFLR 25 kA 1 s.
  - The IAC code gives the accessibility type (A = authorised personnel), the accessible sides (F front, L lateral, R rear), the test current and the duration [Search-level, Schneider FAQ, source 7].
  - IAC is a type test of the switchgear. Room pressure rise and gas-exhaust routing are not covered by it and need a separate building calculation [Search-level, Roxtec, source 8].
  - The edition of IEC 62271-200 to cite is [Unverified].
- **Insulating medium.**
  - **EU F-gas Regulation 2024/573 Art. 13(9)(a) prohibits putting into operation MV switchgear for primary and secondary distribution up to and including 24 kV that uses F-gases in its insulating or breaking medium from 1 January 2026** [Verified, EC FAQ, source 6]. Derogations exist, for example orders placed before 11 March 2024 and procurement-based exceptions.
  - On this basis DB-001 §7.2 requires MSG-20 to be SF₆-free; any derogation would have to be documented [Inference].
  - The 130 kV side falls in the > 52–145 kV band: only GWP < 1 from 1 January 2028 [Verified, source 6].
- **Earthing system.** The 20 kV network is resonant earthed (Petersen coil ≥ 50 A plus a 10 A resistor), so feeder relays need admittance-based or transient 67N (DB-001). The specification should require the relay vendor's proof for compensated networks and a staged earth-fault test at L3/L5 [Inference].
- **Arc protection.** Optical arc plus reverse-blocking busbar protection; MSG-20 incident energy falls from about 106 to 11 cal/cm² (DB-001 / CALC-003). Test light sensors and the trip path at L3.
- **Interlocks.** Incomer, coupler and incomer 2-of-3 logic with break-before-make (DB-001 §7.2). Check it mechanically (key or electrical) and in the IEC 61850 logic, and test both at FAT and IST.
- **Monitoring.** IEC 61850 at MV; 0.2S revenue meters at the incomers and BESS (DB-001). A GOOSE test plan should be in the FAT.

## 6. If the same campus were in Finland (Muhos-type site)

The assumption here is a transmission-connected (Fingrid) demand facility above 30 MW. All points are pointers for the day-one review, not legal advice.

- **Grid code.**
  - KJV2018 is Fingrid's current demand-connection specification, based on EU 2016/1388 [Search-level, source 13].
  - The **KJV2026** draft was out for consultation from 12 June to 21 August 2026. It sets requirements for demand facilities above 30 MW, explicitly including data centres: fault ride-through and the capability to limit power intake. The target for entry into force is March 2027 [Verified, source 14].
  - A separate Fingrid document, "Technical requirements for large demand facilities" (12 June 2026), **applies immediately** to facilities connected directly to Fingrid's transmission grid [Verified, source 14].
  - Effect on this plan: the L5 IST and the grid-compliance tests would need a fault ride-through verification path. That means simulation with Fingrid-format PSS/E or PSCAD models (Fingrid modelling instruction for data centres, source 15 [Search-level]) plus site tests of the power-limiting function [Inference].
- **Installation rules.**
  - The Electrical Safety Act 1135/2016 §§ 31–33: installations meet the essential requirements if they follow the standards listed by the safety authority [Search-level, source 16].
  - Tukes lists the SFS 6000 series for installations up to 1 000 V AC and SFS 6001 above 1 000 V [Search-level, source 17].
  - SFS 6000 covers up to 1 500 V DC, so an 800 VDC system would sit in the LV series [Search-level, SFS store page, source 18].
  - A commissioning inspection and record are required before an installation is put into use [Search-level, source 16]. The Finnish names and the scope of that inspection are [Unverified].
- **Switchgear.** The EU F-gas rule above applies in Finland as in Sweden [Verified, source 6; EU regulation].

## 7. Questions I would ask on day one

1. Which commissioning framework and level names does the owner use, and who signs each level?
2. Is a full-rating genset load test required on site, or is the factory test accepted? This matters because of the Q-LB 2 500 A limit in §2.
3. What genset rating wording does the owner accept (manufacturer unlimited-hours, ISO COP, ISO DCP)? Is there a site rating letter?
4. Is the IST heat load rack-mounted load banks through the real busways, or temporary feeds?
5. Which MV switchgear medium (vacuum + dry air, or other) is on the approved vendor list, and is any F-gas derogation planned?
6. Which grid code applies to the connection point (Svk / DSO in Sweden; Fingrid KJV2018, the large-demand requirements, or KJV2026 in Finland), and who owns the ride-through study?
7. Is a staged 20 kV earth-fault test on the resonant-earthed network allowed by the network owner?
8. How is the UPS battery runtime test corrected for a new battery against the EoL design value?
9. Which relay test sets and IEC 61850 tools are used, and is there a GOOSE simulation step before IST?
10. Who is the authorised electrical installer / supervisor of record for each phase?

## Sources (all retrieved 2026-10-29)
1. Uptime Institute Journal, "Fuel System Design and Reliability" (2014): https://journal.uptimeinstitute.com/fuel-system-design-reliability/ [Verified]
2. Project 01 DB-001 Rev P2 and drawings SLD-001…004, `01-design-basis-sld/` in this repository (own fictional design)
3. Project 05 CALC-004 Rev P1a, `05-bess/report/` in this repository (own fictional study)
4. Cummins, "Data Center Continuous (DCC) ratings" white paper, Bulletin 5600406 Rev 2/25: https://mart.cummins.com/imagelibrary/data/assetfiles/0059642.pdf [Verified opened; content is Vendor claim]
5. Caterpillar, ISO 8528-1 ratings note: https://emc.cat.com/n/api/pubdirect?media_string_id=LEXE0047- [Search-level]
6. European Commission, FAQ on switchgear under F-gas Regulation (EU) 2024/573: https://climate.ec.europa.eu/document/download/cfe52d31-9203-435d-b043-62f74900fd96_en?filename=policy_f-gases_stakeholders_switchgear_faq_en.pdf [Verified, PDF opened]
7. Schneider Electric FAQ on IAC classification: https://www.se.com/us/en/faqs/FA239950/ [Search-level]
8. Roxtec white paper on arc flash and room pressure: https://www.roxtec.com/globalassets/03.-files/whitepapers/roxtec_white_paper_-_arc-flash_.pdf [Search-level]
9. HIOKI, data centre commissioning levels: https://www.hioki.com/global/industries-solutions/facilities/data-center-commissioning-levels.html [Search-level; fetch returned 403]
10. Avtron load banks brochure: https://avtronpower.com/wp-content/uploads/2026/03/Avtron-load-banks-for-data-centres-brochure-Americas-Pub-5246-Rev-.pdf [Search-level, Vendor]
11. Aggreko, data centre commissioning: https://www.aggreko.com/en-us/sectors/data-centres/data-centre-commissioning [Search-level, Vendor]
12. Construct & Commission, 5 levels: https://constructandcommission.com/5-levels-of-commissioning-explained-data-center/ [Search-level]
13. Fingrid, demand connection specifications (KJV2018): https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-code-specifications/grid-specifications-for-demand-connections/ [Search-level]
14. Fingrid, KJV2026 draft for comments: https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-code-specifications/draft-for-comments-kjv2026-grid-code-specifications-for-demand-connections/ [Verified]
15. Fingrid modelling instructions (data centres, PSS/E and PSCAD): https://www.fingrid.fi/en/grid/grid-connection-agreement-phases/grid-code-specifications/modelling-instructions2/ [Search-level]
16. Electrical Safety Act 1135/2016, unofficial English translation: https://tukes.fi/documents/5470659/6372489/sahkoturvallisuuslaki-1135-2016-EN.pdf/d274f714-a446-4448-9abe-d95bfc7ff3a6/sahkoturvallisuuslaki-1135-2016-EN.pdf [Search-level]
17. Tukes, technical requirements for electrical installations: https://tukes.fi/en/electricity/electrical-works-and-contracting/technical-requirements-for-electrical-installations [Search-level; fetch returned 403]
18. SFS, SFS-käsikirja 600-1:2022: https://store.sfs.fi/fi/sfs-k%C3%A4sikirja-600-1-2022 [Search-level]

*Fictional case · D. Wu portfolio · no employer, client or vendor data · CONCEPT / DRAFT — requires review by a licensed electrical engineer.*
