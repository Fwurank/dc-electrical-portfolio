# Project 04 context · storage layers vs time

| Header | |
|---|---|
| Title / version / date | Storage layers context note · v0.1 · 2026-10-29 |
| Status | **CONCEPT / DRAFT — requires review by a licensed electrical engineer** |
| Assumptions | Numbers are taken unchanged from DB-001 Rev P2 and CALC-004 Rev P1a. Rack BBU and capacitor values come from the OCP spec and are not part of the Project 01 base design. |
| Codes (pointers) | EN 50600-2-2 · IEC 62040 · ISO 8528-1 · IEC 62933-5-2 · IEC 60364 / SS 436 40 00 · LVD: all [Unverified] |
| Figure | `FIG-004S_storage_layers_block-v0.1-2026-10-29-en.svg / .pdf` |

Labels: [Verified: opened source] · [Vendor claim] · [Search-level] · [Unverified] · [Inference]. Retrieval date: 2026-10-29.

**Context (for the Project 04 page)**
1. Each layer covers one time band. Rack capacitors ride through up to 20 ms, the UPS covers 5–8 min, the campus BESS 27 min, and the gensets 24 h of fuel. Sources: OCP Mt. Diablo v1.0.0 [Verified (KB 2026-10-26)]; DB-001 P2; CALC-004.
2. The 10 MW / 20 MWh BESS works in the band from 150 ms to hours. It is not counted in redundancy and does not replace the UPS or the gensets (CALC-004 §4).
3. AI-training ripple at 0.1–2 Hz needs a response of about 10 ms or faster. A 150 ms BESS still leaves 5.6 MW peak-to-peak, so the fast band needs capacitors or a supercap. A 23 kWh supercap per 10 MW brings it down to 0.79 MW (CALC-004 model).
4. The 3 MW/min ramp limit (A) is a power problem, not an energy one: about 11.4 MW but only 0.46 MWh (CALC-004).
5. The 10–15 s gap between grid loss and the gensets is bridged by the UPS behind the open-transition ATS, not by the BESS at 20 kV (CALC-004; DB-001 IL-3).
6. Uptime sets at least 12 h of fuel at N for all Tiers; this campus holds 24 h. Source: https://journal.uptimeinstitute.com/fuel-system-design-reliability/ [Verified, opened 2026-10-29].
7. Rack BBUs (45–90 s at 100 % load) would only come in with an 800 VDC rack design. See the Project 05 draft and the OCP Mt. Diablo spec, https://www.opencompute.org/wp-content/uploads/2026/10/OCP-Specification-Mt.-Diablo-Disaggregated-Power-Rack-Specification-v1.0.0.pdf [Verified (KB 2026-10-26)]. [Inference]: link to Project 05 only.

*Fictional case · D. Wu portfolio · CONCEPT / DRAFT — requires review by a licensed electrical engineer.*
