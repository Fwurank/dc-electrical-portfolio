---
title: "Design Basis — 30 MW IT Hyperscale Data Center Campus, Sweden (fictional)"
---

# Design Basis: Electrical Concept
## Nordic Hyperscale Data Center Campus · 30 MW IT · fictional site, bidding zone SE3, Sweden

| Item | Value |
|---|---|
| **Document** | DWU-DC-E-DB-001, **Rev P2** (concept). Supersedes Rev P1 of 2026-10-24 |
| **Author** | Donglin (Franklin) Wu, portfolio project 01 |
| **Date** | 2026-10-25 |
| **Status** | Concept, **not for construction** |
| **Related drawings** | DWU-DC-E-SLD-000 (legend & drawing list), -001 sh. 1–2 (130 kV substation, MSG-20), -002 sh. 1–2 (data hall DH-1), -003 sh. 1–2 (power block A), -004 (BESS plant). All are Rev P2 |
| **Related calculations** | DWU-DC-E-CALC-002 (load & sizing), -CALC-003 (short circuit, protection, arc flash), -CALC-004 (BESS) |

> **Disclaimer.** This is a self-initiated portfolio exercise. The site, the grid connection and all parameters are **fictional assumptions** chosen to be technically plausible. They are based only on public standards and general industry practice. No employer, client or vendor data has been used. Values marked **(A)** are assumptions. Values marked **[C2]**, **[C3]** or **[C4]** were confirmed or changed by calculation CALC-002, -003 or -004.

## Revision history

| Rev | Date | Description | By |
|---|---|---|---|
| P1 | 2026-10-24 | First issue for the concept: design basis, first-pass ratings, SLD-001…003 | D. Wu |
| **P2** | 2026-10-25 | Incorporates every rating change from CALC-002/003/004 (TODO_final_fixes §B rows 1–31). Redrawn SLD set: legend sheet, sheets split for ≥ 2.5 mm text on A3, IEC 60617 symbols for CT, VT, surge arrester, earthing switch, relays, meters and arc sensors, and a new BESS sheet SLD-004. Changes are listed in §12 | D. Wu |
| P2, ed. 2026-10-29 | 2026-10-29 | Editorial, no rating changed: MSG-20 SF₆-free changed from "preferred" to "required" (EU 2024/573, §7.2); load-bank feeder Q-LB limit recorded as an open point (§7.4, §11 item 9, TODO C) | D. Wu |

---

## 1. Purpose and scope

This document fixes the design inputs for the electrical concept of a 30 MW (IT) hyperscale campus. It covers everything from the 130 kV grid connection down to the rack power supplies. It is the common foundation for the later portfolio projects:

| Project | Content | Uses from this basis |
|---|---|---|
| 01 (this) | Design basis + concept single-line diagrams | — |
| 03 | Load calculation & equipment sizing tool (Python/Streamlit), CALC-002 | Load model §5, ratings §8 |
| 04 | IEC 60909 short-circuit, protection coordination & arc flash, CALC-003 | Network data §7–8, Table 8.1 |
| 05 | BESS: peak shaving, backup role, markets, AI-load smoothing, CALC-004 | Grid data §3, 20 kV BESS bays §7.5 |

Out of scope at this stage:
* detailed mechanical design and physical layout (beyond the BESS spacing rule in §7.5)
* cable routing
* detailed earthing-grid design (open point in §11)
* the commercial grid-connection process

## 2. Design objectives

1. **Availability:** meet **EN 50600 Availability Class 3**, which means concurrently maintainable power distribution. Also target the equivalent of **Uptime Institute Tier III**. In addition, no single component failure in the IT power chain may drop IT load. This is fault tolerance beyond Tier III. The **BESS is not counted** towards this capacity (§7.5).
2. **Efficiency:**
   * **Annualised PUE ≤ 1.17** (restated in P2). CALC-002 computes **1.165** at 75 % IT utilisation with Dalarna temperature bins and the P1 equipment.
   * The P1 target of ≤ 1.15 is kept only as a **stretch target**. Reaching it needs one of the following:
     * mechanical pPUE **≤ 0.035 in free-cooling hours**, from EC fans, higher CHW/TCS temperatures and pump turndown, instead of the 0.05 assumed
     * UPS ESS/eco mode (η ≈ 99 %) for at least ≈ 60 % of the hours
   * **Design-peak PUE ≈ 1.26** at +32 °C [C2].
3. **Modularity:** build in 3 phases of 10 MW IT. Every data hall uses repeatable prefabricated 2.5 MVA "power blocks".
4. **Grid friendliness:**
   * Stay within the **40 MW subscription**, including after a grid outage when the UPS batteries recharge (§5.2, §7.5).
   * Provide a 10 MW / 20 MWh BESS for peak shaving and for Svenska kraftnät frequency services (FCR-N / FCR-D / mFRR) [C4].
   * Large synchronous AI-training loads must respect a ramp limit agreed with the DSO (§7.6).
5. **Sustainability:** run gensets on **HVO100** renewable diesel. Allow for heat recovery to the local district-heating network (fjärrvärme).

## 3. Site assumptions (A)

| Item | Assumption |
|---|---|
| Location | Fictional greenfield plot, Dalarna County, Sweden. Electricity bidding zone **SE3** |
| Altitude | ≈ 150 m a.s.l. (no derating of equipment needed) |
| Climate (design) | Annual mean ≈ +4.5 °C. Winter design −28 °C. Summer design 0.4 % dry bulb ≈ +27 °C. Extreme design for heat rejection **+32 °C**. Gensets and dry coolers rated for **−30 … +35 °C** |
| Free cooling | Indirect free cooling (dry coolers / water-side economiser) available **> 95 % of hours** with a 27 °C supply-air envelope (ASHRAE A1 recommended) |
| Grid | Two **independent 130 kV lines** from two regional DSO substations ("Nord", "Syd") on separate routes. Svenska kraftnät 400 kV backbone upstream |
| Grid strength at 130 kV | S″k max **3 000 MVA**, min **1 500 MVA**, X/R ≈ 10. If S″k is above about 4 000 MVA, recheck the 20 kV peak current (§7.2) [C3] |
| Connection capacity | **40 MW** subscribed (abonnerad effekt), power factor at the connection point ≥ 0.95. EU Demand Connection Code (Reg. (EU) 2016/1388) requirements apply as specified by the DSO. **No export** assumed (BESS behind the meter) |
| Soil / seismic | Moraine, no seismic design requirement. Soil resistivity ≈ 500 Ω·m (to be measured) |

## 4. IT load and phasing

| Phase | Data halls | IT load | Cumulative | Notes |
|---|---|---|---|---|
| 1 | DH-1, DH-2 | 10 MW | 10 MW | 130/20 kV substation (both transformers) and MSG-20 built in full in Phase 1 |
| 2 | DH-3, DH-4 | 10 MW | 20 MW | BESS 10 MW / 20 MWh (two 5 MW units) can be added from Phase 2 |
| 3 | DH-5, DH-6 | 10 MW | 30 MW | |
| (4) | — | — | — | Spare 20 kV bays for expansion |

* Each data hall: **5.0 MW IT**, about 200 racks at an average of 25 kW. The design allows up to 4 rows of liquid-cooled AI racks at 80–130 kW per rack, fed through CDUs.
* Racks are **dual-corded**, with two PSUs per server that share load and can each take the full load (standard hyperscale / OCP practice).
* The design IT load is the nameplate allocation. Average utilisation for energy estimates: **75 %** (A).

## 5. Load estimate and PUE (updated to CALC-002)

### 5.1 Per data hall, design peak (+32 °C ambient)

| Load | P1 (MW) | **P2 (MW)** [C2] | Basis (A) |
|---|---|---|---|
| IT (critical) | 5.00 | **5.00** | Allocation |
| UPS losses | 0.21 | **0.18** | Efficiency curve at 62.5 % load, η ≈ 96.6 % |
| Mechanical (dry-cooler fans, trim chillers, pumps, fan walls, CDUs) | 0.85 | **0.85** | Mechanical pPUE 0.17 at +32 °C |
| Transformer and distribution losses | 0.08 | **0.07** | ≈ 1.2 % of the downstream load |
| House services (lighting, BMS, security, UPS-room HVAC) | 0.10 | **0.10** | |
| **Hall total (excl. battery recharge)** | 6.24 | **6.20** | **pPUE ≈ 1.24** |
| Battery recharge (non-coincident, sizing only) | +0.80 | **+0.80** | 10 % of 4 × 2.0 MW |
| **Hall maximum for MV feeder sizing** | ≈ 7.0 MW | **7.00 MW, 7.37 MVA** | **213 A** at 20 kV (feeder 390 A, OK) |

### 5.2 Campus

| Item | Value |
|---|---|
| Campus design-peak demand (6 halls + 0.5 MW services + HV transformer losses) | **37.8 MW / 39.8 MVA** at +32 °C → **design-peak PUE 1.26** [C2] |
| **Campus maximum including non-coincident UPS recharge after a grid outage** | **42.6 MW**. This is **above the 40 MW subscription** [C4]. See the rule below |
| Annualised PUE (75 % IT, Dalarna temperature bins) | **1.165 computed; target ≤ 1.17** (stretch 1.15, §2) |
| Annual energy estimate | 197 GWh IT, **≈ 230 GWh facility** per year |

**Recharge rule (new in P2, TODO B26):** after the grid returns, UPS battery recharge is **staggered by the EPMS and limited to ≤ 2.2 MW in total for the campus**, unless the BESS is available to cover the difference. While on gensets, recharge is limited to 5 % per block (§7.3). The rule keeps the import at or below 40 MW on the design day, and the design must not depend on the BESS for it.

## 6. Redundancy concept

### 6.1 Comparison of UPS / power-train architectures

The table compares the options for one 5 MW data hall. Scores are qualitative, and the CAPEX figures are rough ratios against 2N, based on public industry literature.

| Criterion | **2N** (A/B fully duplicated) | **N+1** (parallel-redundant modules, single bus) | **Distributed redundant (4N/3)** | **Block redundant (4+1 "catcher")** |
|---|---|---|---|---|
| Installed UPS/gen capacity vs. load | 200 % | ≈ 125 % (N = 4) | **133 %** | 125 % |
| Electrical CAPEX (relative) | 100 % (highest) | ≈ 60–65 % | **≈ 75–80 %** | ≈ 75 % |
| Footprint | Largest | Smallest | **Medium** | Medium |
| Concurrent maintainability (Tier III / Class 3) | Yes | **No** (single distribution path) | **Yes** | Yes |
| Single-fault tolerance of distribution | Yes (Tier IV capable) | No | **Yes** (any one block) | Yes, but relies on transfer (STS / bypass) to the reserve |
| Normal UPS loading → efficiency | ≤ 50 % → lowest efficiency | ≈ 80 % → best | **62.5–75 % → good** | Primaries ≈ 80–100 %, reserve idle → good |
| Complexity / operational risk | Simple, intuitive | Simple, but the bus is a single point of failure | Rack-pair allocation and load discipline (DCIM) required | Reserve bus and transfer coordination. A fault on the reserve bus can affect every block |
| Scalability in phases | Pairs of systems | Module by module | **Block by block (good)** | Needs the reserve block early |

### 6.2 Chosen architecture: distributed redundant 4N/3 + 2N mechanical

* Each data hall has **4 identical IT power blocks A–D**, each made up of 20/0.42 kV transformer, genset, MSB, UPS and UOSB. Any **3 blocks carry the full 5 MW**.
* Every rack is dual-corded across a **unique pair of blocks** (pair-groups AB, AC, AD, BC, BD, CD, ≈ 0.83 MW each).
  * Normal block load is **1.25 MW**.
  * After losing any one block, each surviving block carries **1.67 MW**, which is **83 %** of its 2.0 MW UPS rating.
* **Mechanical loads** get **2N** boards (MSB-M1 / M2, each 100 %). Fans, CDUs and pumps are on a **mechanical UPS** for continuous cooling.
* **MV level:** dual-radial 20 kV feeders A and B to each hall, each rated for the full hall load. Hall MV board in two sections with a normally-open coupler.
* **HV level:** two 130 kV lines and two 63 MVA transformers. Each line/transformer pair carries the **whole campus** (N+1).
* **BESS:** not part of the redundancy concept. Gensets and UPS are sized without it (§7.5).

**Why this choice:**

1. It achieves Tier III / Class 3 concurrent maintainability **and** single-fault tolerance for about 20–25 % less electrical plant than 2N.
2. There is no STS or "catcher" reserve bus in the critical path, so there is no shared component whose failure can affect all blocks. Dual-corded IT makes the pairing native.
3. The block is a standard 2.5 MVA prefabricated skid (eHouse + genset). That suits phased hyperscale deployment and repeatable procurement.
4. UPS units run at 62.5 % normally, which is in the high-efficiency region of modern modular UPS. ECO / ESS mode can be considered.
5. **Accepted trade-off:** load placement must keep each block ≤ 1.67 MW in any N-1 case. EPMS/DCIM monitors this, and the allocation rule is part of the operating procedures.

## 7. Electrical system description

### 7.1 Voltage levels and system earthing

| Level | Use | System earthing |
|---|---|---|
| 130 kV | Grid connection (DSO) | Per DSO practice (YN winding provided, neutral earthing per DSO) |
| 20 kV (24 kV equipment) | Campus distribution | **Resonant (compensated) earthing, confirmed in P2** [C3]. See below |
| 400/230 V, 50 Hz | LV distribution, UPS, IT | **TN-S** per SS 436 40 00. 4-pole switching at source transfer, single N-PE bond (central earthing point, CEP) per switchboard |
| 110 V DC | Substation protection and control | 2 × 100 % chargers + battery |
| 24 V DC / 48 V DC | Controls / rack-level (OCP) | — |

**20 kV neutral earthing (TODO B21, B25).** Each MSG-20 section has the following:
* a ZNyn earthing transformer
* an **automatically tuned Petersen coil of at least 50 A**, continuously adjustable, about 10–60 A
* a **10 A parallel resistor**, switched in for selective earth-fault detection

Capacitive current:
* **≈ 22 A per section**, rising to 44 A with the coupler closed.
* The BESS cables and transformers add **≈ +1 A**. The BESS transformers have delta windings at 20 kV, so they add no zero-sequence path.

Detection uses admittance or transient directional earth-fault protection [67N/59N]. Low-resistance earthing at 500 A was evaluated in CALC-003 and rejected. Its arc energy and EPR are higher, and it gives no ride-through on cable faults.

### 7.2 130/20 kV customer substation (sheet SLD-001 sh. 1–2)

**Arrangement and transformers**
* **H-arrangement**: line CB → bus section (normally-open bus-section CB) → transformer CB.
* **T1, T2:** 63 MVA (40 MVA ONAN / 63 MVA ONAF), 130 ±9×1.67 % / 21 kV, YNd11, uk ≈ 12 %, on-load tap changer. P_k ≈ 250 kW.
* Surge arresters are fitted at:
  * the 130 kV line entries
  * the transformer HV terminals
  * the transformer LV terminals and at every 20 kV cable termination

**MSG-20 switchgear**
* 24 kV, 2 500 A, **25 kA / 3 s, Ip 62.5 kA**, IEC 62271-200, LSC2B-PM, IAC AFLR 25 kA 1 s, SF₆-free required (EU F-gas Regulation 2024/573 Art. 13(9)(a) for new MV switchgear up to 24 kV put into operation from 1 Jan 2026) [assumed applicable, to be confirmed against the regulation text].
* Two sections with a normally-open coupler.

**Short-circuit levels [C3]**

| Case | I″k | Peak ip | Against rating |
|---|---|---|---|
| Normal (S0, one transformer per section) | **13.0 kA** | 34.4 kA | Ip 62.5 kA |
| Normal with BESS | **13.3 kA** | — | +0.38 kA inverter contribution at 1.2 × In [C4] |
| Worst abnormal case | 22.7 kA, **23.1 kA with BESS** | — | 92 % of 25 kA |

**Interlocks (TODO B12, B13)**
* **T1//T2 paralleling is interlocked out.** The bus coupler auto-closes only after the incomer of the lost transformer is proven open (break-before-make). With T1//T2 the peak would be ip 58.5 kA, which is 94 % of 62.5 kA, and above 100 % at S″k 4 000 MVA. The R-TX CT would also saturate.
* **Hall-board coupler (HV-DH1 and similar):** it may close only when one of the two hall feeders is open. With both feeders and the coupler closed, T1 and T2 would be in parallel through the hall board (20.9 kA).

**20 kV feeders per section:**
* 6 data-hall feeders (630 A VCB, 3×1×240 mm² Al cable, ≈ 0.6 km, 390 A capacity in ground)
* an earthing transformer bay with the Petersen coil and resistor (§7.1)
* a station-aux transformer (500 kVA)
* **a BESS bay: 630 A, one per section** (§7.5)
* a spare

**Protection settings [C3] (TODO B19, B20)**

| Relay | CT | 51 setting | 50 setting |
|---|---|---|---|
| R-INC (20 kV incomer) | 2 500/1 5P20 15 VA, + 0.2S metering core | Is 2 100 A, IEC SI, TMS 0.16 | I≫ 6 000 A, 0.65 s |
| R-FDR (hall feeder) | **400/1 5P20 15 VA** | Is 320 A, IEC VI, TMS 0.84 | I≫ 2 400 A, 0.35 s |
| R-TX (block transformer, at HV-DH1) | **150/1 5P20 10 VA, Ith ≥ 25 kA 1 s** | Is 100 A, IEC EI, TMS 1.0 | I≫ 1 500 A, 0.05 s |

* All MV grading margins are ≥ 0.30 s.
* **Busbar protection:** reverse-blocking (incomer 50 blocked by any outgoing-feeder start), on both MSG-20 and HV-DH1.
* **Optical arc protection** (light + current, [50ARC]) trips the section incomer and the coupler. This reduces the incident energy in MSG-20 and HV-DH1 from ≈ 106 to ≈ 11 cal/cm² (Lee method) [C3] (TODO B18).

### 7.3 Data hall distribution (sheet SLD-002 sh. 1–2)

**Hall MV board and transformers**
* **Hall MV board HV-DH1:** 24 kV, 1 250 A, 25 kA / 1 s.
  * Section 1 feeds T-A, T-C and T-M1. Section 2 feeds T-B, T-D and T-M2.
  * Coupler interlock as in §7.2.
* **IT block transformers:** 4 × 2 500 kVA cast resin, Dyn11, uk 6 %, **P_k ≈ 19 kW, P₀ ≈ 3.1 kW** (Ecodesign Tier 2 order).
  * P2 aligns the loss values with CALC-002/003; P1 had P_k ≈ 22 kW (TODO B9).
  * Loading 65 % normal, **82 % in N-1** [C2].
* **Mechanical transformers:** 2 × **1 600 kVA kept** (TODO B8).
  * The mechanical load is ≈ 1 030 kVA, so 1 250 kVA would pass at 83 %.
  * 1 600 kVA (65 %) is kept on purpose. It leaves ≈ 20 % margin for growth in liquid cooling (CDUs) and for starting the 400 kW trim chillers. It also gives a common spare with the 1 650 kVA mechanical gensets.

**Gensets and transfer**
* **Gensets:** one per block, each with an ATS.
  * IT: 2 750 kVA / 2 200 kWe DCC, 88 % loaded in N-1.
  * Mechanical: 1 650 kVA / 1 320 kWe, governed by the 400 kW chiller step (≤ 33 %).
* **Open transition in both directions only (TODO B14).** Closed-transition retransfer at the MSB is not permitted. With grid and genset in parallel, the MSB would see 81.8 kA / ip 187 kA, which is above the 65 / 143 kA rating [C3].
* The genset ACB uses short-delay pick-up **Isd ≤ 2.5 × Ir**. The genset specification requires a **sustained short-circuit current of at least 300 % for 2 s** (PMG or AREP excitation) so that the genset ACB and the downstream devices trip.

**Fuel (TODO B6)**
* HVO100, **24 h** at design load on site (A; Tier III requires ≥ 12 h).
* **≈ 51 m³ gross per hall** (46 m³ net, 90 % usable), in bulk and day tanks [C2].
* The volume includes the 5 % recharge allowance, the part-load SFC and the mechanical gensets.

### 7.4 Power block (sheet SLD-003 sh. 1–2)

**Power path**
* MV feeder → T-A → MSB-A (4 000 A) → 2 × 1 000 kW UPS modules in parallel → UPS output bus → UOSB-A (3 200 A) → 6 × 800 A overhead busways (2 runs per pair-group) → 63 A 3P+N tap-offs → rack PDUs.

**Connections and ratings**
* **T-A → MSB:** 4 000 A busbar trunking, ≈ 10 m.
* **Genset → MSB generator incomer:** **4 000 A busbar trunking** (≈ 40 m) (TODO B5). A cable would need 8 × 3×1×240 Cu. The alternative is to locate the genset room next to the MSB.
* **MSB → SBS (static bypass) input:** **3 200 A busbar trunking** (≈ 25 m) (TODO B4). A cable would need 7 × 3×1×240 Cu.
* **MSB:**
  * 65 kA board.
  * **Icw 65 kA / 1 s, Ipk ≥ 143 kA** specified.
  * Computed fault levels:
    * I″k 52.3 kA, ip 122 kA with the cables and busduct modelled [C3]
    * 53.8 kA / ip 129 kA as a hand value at the transformer terminals [C2] (TODO B10)
* **UPS rectifier input breakers:** **2 000 A** (TODO B2). The maximum input current is 1 660 A at rated power plus 10 % recharge. The alternative is to limit grid recharge to ≤ 5 %.
* **UPS battery:** **LFP, 165 kWh nameplate per 1 000 kW module** (TODO B1).
  * Governed by the C-rate: ≤ 8 C at end of life. 120 kWh would need 10.7 C.
  * Gives 5 min at the rated load at end of life, and 8.1 min at the N-1 load.

**Critical distribution: short-circuit ratings (TODO B3, B15, B16)**

| Location | Fault level [C3] | Requirement |
|---|---|---|
| UOSB | 49.3 kA | — |
| Busway start | 37.1 kA | Busway Icw is 36 kA. Each busway is fed by a **current-limiting MCCB, Icu ≥ 50 kA**, with a **tested busway conditional short-circuit rating ≥ 40 kA** (IEC 61439-6) |
| Busway end (tap-off) | 25.1 kA | **63 A MCCB Icu ≥ 36 kA**, or a tested cascade with the busway MCCB |
| Rack inlet | 14.0 kA | **Rack PDU conditional SCCR ≥ 15 kA** |

**LV trip-unit settings (TODO B19)**

| Device | Ir | tr | Isd | tsd | Other |
|---|---|---|---|---|---|
| MSB incomer ACB | 3 600 A | 3 s | 4 × Ir | 0.3 s | — |
| SBS ACB | 2 900 A | 1 s | 2.5 × Ir | 0.2 s | — |
| Busway MCCB | 800 A | — | 4 × Ir | 0.1 s | Ii 12 × Ir |
| Genset ACB | 4 000 A | 12 s | 2.5 × Ir | 0.4 s | — |

**Arc-flash mitigation on MSB and UOSB (TODO B17)**
* **Optical arc relays** with **intertrip of the 20 kV block-transformer VCB**. This covers the MSB line side, which the incomer cannot clear.
* **ZSI** between the incomer and the outgoing ACBs.
* An **arc-reduction maintenance switch (ARMS)** on each incomer.
* Effect: the MSB line side falls from 96 to 3.2 cal/cm², and the bus from 16.8 to 2.4–4.8 cal/cm² (IEEE 1584-2018) [C3].
* Final labels are issued only after the vendor study.

**Bypass and testing**
* **Centralised static bypass (SBS)** and an **external wrap-around maintenance bypass (MBB)**. The MBB is key-interlocked with the UPS output breaker.
* Each MSB has a **load-bank connection** for commissioning and periodic genset testing.
* **Load-bank feeder Q-LB: 2 500 A (SLD-003 sh. 1), rating unchanged; open point (TODO C).** At 400 V it carries √3 × 0.4 kV × 2.5 kA ≈ 1.73 MVA, i.e. ≈ 1.73 MW with a resistive load bank. This is sized for the N-1 block IT load of 1.67 MW (§6.2). It is not enough for the IT genset's N-1 design load of ≈ 1.93 MW (CALC-002) or its full 2 750 kVA / 2 200 kWe DCC rating, so a genset test through Q-LB is limited to ≈ 1.73 MW (≈ 79 % of 2 200 kWe). Options for the design review: (a) upsize Q-LB to 4 000 A (≈ 2.77 MVA, matches the genset ACB and covers 2 750 kVA), or (b) keep 2 500 A and state the limited site-test output, with the full-rating test at the genset factory acceptance test.

### 7.5 Battery energy storage (sheet SLD-004) [C4]

**Plant and connection (TODO B22, B23)**
* **10 MW / 20 MWh LFP** in two units of 5 MW / 10 MWh.
* Each unit has its own **630 A CB bay**, one per MSG-20 section (Q19 and Q29), with these parts:
  * CT 200/1 5P20, plus a 0.2S revenue core
  * VT 20/√3 / 0.1/√3 kV, cl. 0.2/3P
  * surge arresters and an earthing switch
* Unit rating 5.5 MVA, 159 A.
* PCS transformers: 2 × 5.5 MVA, 20/0.69 kV, **Dyn (delta at 20 kV)**.
* PCS: 4-quadrant, grid-following, with a grid-forming option. The **11 MVA** gives Q capability for the p.f. ≥ 0.95 at the connection point.
* Revenue and aggregator metering: cl. 0.2S, separate from the EPMS.

**Bay protection**
* 50/51, 50N/51N/67N
* 27/59, 81U/O, 59N
* loss of mains (ROCOF / vector shift)
* **intertrip from R-INC**, so that the BESS trips when its section loses the grid
* 25 synchro-check, only if the grid-forming mode is used

**Role and limits**
* Peak shaving under 40 MW gives **+2.4 MW** extra IT capacity. The **firm** value at N-1 BESS is only **+0.84 MW**, and only that value may be sold as IT capacity.
* The battery provides FCR-N, FCR-D up/down, mFRR and arbitrage.
* **The BESS is not counted** as Tier III / EN 50600 Class 3 capacity (TODO B28). The gensets and UPS are unchanged, because the BESS has 27 min at campus peak against 24 h of fuel.

**EMS / power-plant controller priorities (TODO B27)**
1. Grid import limit of 40 MW, including recharge (§5.2).
2. SOC reserve before forecast peaks.
3. Reserve headroom for FCR down-activation. Down-activation counts against the import limit.
4. Markets.

If the BESS is unavailable, IT power capping is the fallback.

**Island operation (not in the base design; TODO B28)**
* The 20 kV relays do **not** clear an island fault fed only by the inverters: 381 A at 20 kV, and R-FDR would take ≈ 60 s.
* Bridging a genset fail-to-start would therefore need all of the following:
  * a grid-forming PCS
  * island protection: 51V, definite-time 27, or 87L
  * soft energisation
  * an open-position interlock on the 130 kV CB
  * an island earthing check

**Power quality (TODO B29)**
* A harmonic study to IEC/TR 61000-3-6, with the DSO, of PCS plus UPS rectifiers, is an **open point** (§11).

**Fire safety and layout (TODO B30)**
* Outdoor LFP containers, at least **10 m (A)** from halls, transformers and fuel tanks.
* Container data to UL 9540A, design to NFPA 855, EN IEC 62485-5 and IEC 62933-5-2.
* Explosion control to NFPA 68/69.
* Early consultation with the Räddningstjänst (fire and rescue service).

### 7.6 Large AI-training loads (TODO B31)

Synchronous AI training can swing a hall by several MW within seconds.

**Connection agreement**
* State a **grid ramp limit** in the connection agreement: 3 MW/min (A), agreed with the DSO.
* State an oscillation limit in the 0.1–2 Hz band: ≤ 1 MW peak-to-peak (A).

**What smoothing a 12 MW swing needs** [C4]
* ≈ 11.4 MW of BESS power, so the 10 MW BESS is marginal. The energy needed is below 0.5 MWh.
* A response of **≤ ~10 ms** for the ripple. A BESS with a 150 ms response leaves 5.6 MW peak-to-peak.

**Specified mitigation**, one or a combination of:
* a supercapacitor or hybrid stage (≈ 23 kWh per 10 MW)
* UPS-level smoothing
* a GPU-side power floor or ramp control in the workload scheduler

## 8. Equipment ratings (Rev P2)

| Equipment | Qty (campus) | **Rating (P2)** | Sizing check / source | Change vs P1 |
|---|---|---|---|---|
| 130/20 kV transformer T1, T2 | 2 | 63 MVA ONAF, uk 12 %, YNd11, OLTC | N-1 63 % (ONAF) [C2] | — |
| 20 kV main switchgear MSG-20 | 1 (2 sections) | 2 500 A, 25 kA / 3 s, Ip 62.5 kA | 13.0 kA normal, 13.3 kA with BESS, worst 23.1 kA [C3/C4]; section ≈ 1 150 A | values updated |
| Hall feeders | 12 | 630 A VCB, CT 400/1, 3×1×240 Al | 213 A ≤ 390 A [C2] | CT added |
| BESS bays | **2** | **630 A CB, CT 200/1, VT** | 159 A per unit [C4] | **new** |
| Petersen coil + resistor | 2 | ≥ 50 A adjustable + 10 A | Ic 22 A per section (44 A coupled), +1 A BESS [C3] | specified |
| IT block transformer | 24 | 2 500 kVA, 20/0.42 kV, Dyn11, uk 6 %, Pk 19 kW | N-1 82 % [C2] | Pk aligned |
| Mechanical transformer | 12 | 1 600 kVA, uk 6 % | 65 % (1 250 kVA would be 83 %), margin kept | rationale |
| IT genset | 24 | 2 750 kVA / 2 200 kWe DCC, sustained Isc ≥ 300 % for 2 s | N-1 88 % [C2] | spec added |
| Mechanical genset | 12 | 1 650 kVA / 1 320 kWe | 400 kW chiller step ≤ 33 % [C2] | — |
| Fuel per hall | 6 | **≈ 51 m³ gross** (24 h) | [C2] | 38 → 51 m³ |
| UPS (per block) | 24 × 2 modules | 2 × 1 000 kW, VFI-SS-111 | N-1 83 % | — |
| UPS rectifier input breaker | 48 | **2 000 A** | 1 660 A max [C2] | 1 600 → 2 000 A |
| Battery (per module) | 48 | **LFP 165 kWh nameplate** | C-rate ≤ 8 C at EoL; 5 min at Pr, 8.1 min at N-1 [C2] | 120 → 165 kWh |
| MSB (IT block) | 24 | 4 000 A, **Icw 65 kA / 1 s, Ipk 143 kA**, Form 4b, optical arc relays + MV intertrip, ZSI, ARMS | 52.3 kA / ip 122 kA [C3] | spec added |
| Genset → MSB / MSB → SBS | 24 + 24 | **4 000 A / 3 200 A busbar trunking** | [C2] | cable → BTS |
| UOSB | 24 | 3 200 A, 65 kA / 1 s, optical arc relays | 49.3 kA [C3] | arc protection |
| Busway feeder MCCB | 144 | **Current-limiting, Icu ≥ 50 kA, tested conditional ≥ 40 kA** | busway start 37.1 kA > Icw 36 kA [C3] | specified |
| Busway | 144 | 800 A, Icw 36 kA | survivor 614 A at 40 °C [C2] | — |
| Tap-off devices / rack PDU | — | **63 A MCCB Icu ≥ 36 kA or tested cascade; PDU SCCR ≥ 15 kA** | 25.1 / 14.0 kA [C3] | specified |
| Mechanical UPS | 12 | 2 × 250 kW, 10 min | Fans, CDUs, CHW pumps | — |
| BESS | 1 (2 units) | **10 MW / 20 MWh LFP, PCS 2 × 5.5 MVA, Dyn 20/0.69 kV** | [C4] | **new** |

### 8.1 Network data (as used in CALC-003)

| Element | Data |
|---|---|
| 130 kV grid | S″k max/min 3 000 / 1 500 MVA, c_max = 1.10, R/X = 0.1 |
| T1/T2 | 63 MVA, 130/21 kV, uk = 12 %, P_k ≈ 250 kW, YNd11 |
| 20 kV cables | 3×1×240 Al: R ≈ 0.125 Ω/km, X ≈ 0.11 Ω/km, ≈ 0.6 km per feeder. 3×1×95 Al to transformers ≈ 0.15 km |
| T-A … T-D | 2.5 MVA, 20/0.42 kV, uk = 6 %, **P_k ≈ 19 kW**, Dyn11 |
| IT genset | 2 750 kVA, x″d ≈ 15 %, x′d ≈ 22 %, R/X ≈ 0.15 |
| BESS PCS | 2 × 5 MW, fault current 1.2 × In (A, generic), response ≈ 150 ms (A) |
| **Results** [C3] | **20 kV: 13.0 kA** (P1 hand estimate ≈ 14 kA). **MSB-A: 52.3 kA** full model, 53.8 kA at the transformer terminals (P1 ≈ 52 kA). IEC 60909 with K_T. The pandapower cross-check gives the same result in the max case |

## 9. Protection and control philosophy (concept)

* **130 kV:** line differential / distance [87L/21], transformer differential [87T], restricted earth fault [64REF], Buchholz [63], oil/winding temperature [26/49], breaker failure [50BF]. Coordinated with the DSO.
* **20 kV:**
  * Feeder overcurrent [50/51] and earth fault [50N/51N].
  * Directional earth fault [67N] for resonant earthing (admittance or transient method).
  * Reverse-blocking busbar protection and optical arc protection [50ARC].
  * Incomer/coupler automatic transfer, break-before-make, with lock-out on bus fault.
  * BESS bay protection as in §7.5.
  * Settings are in §7.2.
* **LV:**
  * LSI(G) electronic trip units (settings in §7.4), with ZSI between the incomer and the outgoing ACBs.
  * MCB/MCCB pairs are current-selective only up to ≈ 8.6 kA. Above that, the manufacturer's selectivity tables are required (open point).
  * Arc-flash mitigation as in §7.4.
* **Monitoring:** EPMS with class 0.5S meters on every incomer and outgoing (PUE per EN 50600-4-2), and 0.2S revenue meters at the 20 kV incomers and the BESS. IEC 61850 at MV/HV, Modbus TCP at LV. Integration with DCIM/BMS.

## 10. Applicable standards and regulations

| Area | Reference |
|---|---|
| Swedish regulation | **ELSÄK-FS 2022:1** (Elsäkerhetsverket: how high-voltage/“starkström” installations shall be designed). Elsäkerhetslagen (2016:732). Elsäkerhetsförordningen (2017:218) |
| LV installations | **SS 436 40 00** (Swedish implementation of IEC/HD 60364), **IEC 60364** series |
| HV installations | SS-EN 61936-1 (installations > 1 kV AC), SS-EN 50522 (earthing > 1 kV) |
| LV switchgear / busway | **IEC 61439-1/-2** (switchboards), **IEC 61439-6** (busbar trunking), IEC 60947-2 (breakers) |
| MV/HV switchgear | **IEC 62271-1/-100/-200** |
| Transformers | IEC 60076 series, IEC 60076-5 (short-circuit withstand), IEC 60076-11 (dry type) |
| UPS | **IEC 62040-1/-3** |
| Batteries / BESS | IEC 62619, EN IEC 62485-5, IEC 62933-5-2, UL 9540A (test data), NFPA 855 |
| Gensets | ISO 8528 series |
| Short-circuit / arc flash | **IEC 60909-0**, IEEE 1584-2018 |
| Protection | IEC 60255 series (IEC 60255-151 curves). IEC 61850 (communication) |
| Instrument transformers | IEC 61869-2 (CT), IEC 61869-3 (VT) |
| Surge protection | IEC 60099-4 (MV/HV arresters), IEC 61643-11 (LV SPD), IEC 62305 (lightning) |
| Graphical symbols | IEC 60617 (SLD symbols), IEEE C37.2 (device numbers), ISO 3098 / ISO 5457 (lettering, sheet format) |
| Data centres | **EN 50600-1, -2-2 (power distribution), -4-2 (PUE)**. Uptime Institute Tier Standard: Topology (reference) |
| Grid connection | Regulation (EU) 2016/1388 (Demand Connection Code), DSO technical requirements, Svenska kraftnät rules for FCR/mFRR (BESS prequalification) |

## 11. Key assumptions and open points

1. Grid capacity and connection timeline are assumed available. In reality, grid capacity is the critical-path item for Nordic data centres.
2. **130 kV substation earthing:** this needs a detailed study with DSO data (soil model, EN 50522). The 130 kV earth-fault EPR of ≈ 800 V exceeds 2·UTp at 0.5 s back-up clearing [C3]. This is **open**.
3. Assumed data must be confirmed with the DSO and vendors:
   * grid S″k of 1 500–3 000 MVA (above 4 000 MVA the 20 kV peak margin is lost)
   * UPS inverter current limit
   * PDU rating
   * cable capacitance
   * earth resistance
   * PCS fault-current curve (1.2 pu assumed)
4. Generic LV device curves must be replaced with the selected manufacturer's curves and selectivity/cascade tables. Arc-flash labels are issued only after the final study with vendor clearing times.
5. **BESS:** confirm with the DSO whether FCR activation or export is allowed under the 40 MW subscription. Also check Svk FCR/mFRR prequalification, aggregator terms and market depth. The CALC-004 revenue is an upper bound.
6. A **harmonic and reactive-power study** of the UPS rectifiers, VFDs and BESS PCS, to IEC 61000-3-12, IEC/TR 61000-3-6 and the DSO limits. Long 20 kV cables at light load generate capacitive reactive power. The BESS PCS can absorb it.
7. Rack density growth (AI/liquid cooling) can raise hall IT load above 5 MW. The block approach allows a 5th block per hall if the space is reserved.
8. Heat recovery to district heating (heat pumps ≈ 2–4 MW extra electrical load) is not included in the base load. It would also count against the 40 MW subscription.
9. **Load-bank feeder Q-LB** (§7.4): 2 500 A ≈ 1.73 MVA proves the 1.67 MW N-1 block IT load but not the full genset rating. Decide between upsizing to 4 000 A and a stated limited site-test output. This is **open** (TODO C).

## 12. Changes in Rev P2 (traceability to TODO_final_fixes.md)

| TODO | Change | Section |
|---|---|---|
| A1–A3 | SLD set redrawn: ≥ 2.5 mm text on A3, IEC 60617 symbols, legend sheet SLD-000, sheets split, new SLD-004 | Drawings |
| B1, B2 | Battery 165 kWh per module; rectifier input breaker 2 000 A | §7.4, §8 |
| B3, B15, B16 | Busway MCCB and tap-off device ratings; PDU SCCR | §7.4, §8 |
| B4, B5 | Busbar trunking for MSB → SBS (3 200 A) and genset → MSB (4 000 A) | §7.4, §8 |
| B6 | Fuel 51 m³ per hall | §7.3, §8 |
| B7 | Annual PUE target ≤ 1.17 (stretch 1.15 with conditions) | §2, §5.2 |
| B8 | Mechanical transformer 1 600 kVA kept, with rationale | §7.3 |
| B9 | Block transformer Pk 19 kW | §7.3, §8.1 |
| B10, B11 | I″k 52.3/53.8 kA (MSB) and 13.0 kA (20 kV); Icw/Ipk | §7.2, §7.4, §8.1 |
| B12, B13 | T1//T2 and hall-coupler interlocks | §7.2 |
| B14 | Open-transition-only retransfer; genset sustained Isc | §7.3 |
| B17, B18 | Arc-flash mitigation at LV and MV | §7.2, §7.4 |
| B19, B20 | Trip settings, relay settings, CT ratios | §7.2, §7.4 |
| B21, B25 | Petersen coil + resistor specification; Ic +1 A | §7.1 |
| B22–B24 | BESS bays, BESS single-line, I″k with BESS | §7.2, §7.5, SLD-004 |
| B26 | Recharge rule under 40 MW | §5.2 |
| B27 | EMS priorities; firm IT +0.84 MW | §7.5 |
| B28 | BESS not counted in Tier III; island protection note | §7.5 |
| B29 | Harmonic study open point; Q capability | §7.5, §11 |
| B30 | BESS spacing and fire codes | §7.5 |
| B31 | AI ramp clause | §7.6 |
| C | Open points carried into §11. These are not resolved, because they need DSO or vendor data | §11 |

---
*Appendix A: Concept SLD sheets, Rev P2 (reduced previews; the vector originals are in `drawings/`).*
