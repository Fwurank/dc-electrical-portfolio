# Project 05: Next-generation power architecture and commissioning (research and concept study)

> **CONCEPT / DRAFT v0.1 (2026-10-29) — requires review by a licensed electrical engineer.**
> This is a **research and concept study** on the same fictional 30 MW IT campus as Projects 01–04 (Dalarna SE3, 6 halls × 5 MW). Nothing in it has been built, tested or commissioned, and it describes no work done or signed for. All ratings come unchanged from DB-001 Rev P2 and CALC-003 / CALC-004. No employer, client or vendor data is used.

Credibility labels used throughout: `[Verified]` source opened · `[Vendor claim]` · `[Search-level]` · `[Unverified]` · `[Inference]` own reasoning. "(KB 2026-10-26)" marks a page opened for the knowledge base on that date and not re-opened.

| Part | Document | Files |
|---|---|---|
| 1 | DWU-DC-E-NOTE-005: 800 VDC vs 400 VDC vs 400 V AC UPS for one 5 MW hall (A3 one-pager, 13 rows, 12 sources) | [PDF](docs/05-800vdc-architecture-comparison-v0.1-2026-10-29-en.pdf) · [Markdown](docs/05-800vdc-architecture-comparison-v0.1-2026-10-29-en.md) |
| 1 | DWU-DC-E-SLD-005: power block A as an 800 VDC concept, alternative to SLD-003; SST outline as alternative B | [PDF](drawings/SLD-005_800VDC_block_A_concept-v0.1-2026-10-29-en.pdf) · [SVG](drawings/SLD-005_800VDC_block_A_concept-v0.1-2026-10-29-en.svg) · [PNG](drawings/SLD-005_800VDC_block_A_concept-v0.1-2026-10-29-en.png) |
| 2 | DWU-DC-E-CX-005: commissioning & test plan (concept), L0–L5, 11 IST scenarios, genset and MV switchgear selection points, Finland notes, day-one questions (A4, 4 pages, 18 sources) | [PDF](docs/05-commissioning-test-plan-concept-v0.1-2026-10-29-en.pdf) · [Markdown](docs/05-commissioning-test-plan-concept-v0.1-2026-10-29-en.md) |

The storage-layers figure FIG-004S for Project 04 is built by the same scripts and lives in [`../04-bess/context/`](../04-bess/context/).

## Rebuild

```bash
python scripts/sld005_800vdc_block.py        # drawings/SLD-005_*.svg/.pdf/.png
python scripts/fig04_storage_layers.py       # ../04-bess/context/FIG-004S_*.svg/.pdf/.png
python scripts/md2pdf.py docs/05-800vdc-architecture-comparison-v0.1-2026-10-29-en.md docs/05-800vdc-architecture-comparison-v0.1-2026-10-29-en.pdf a3l 7.6
python scripts/md2pdf.py docs/05-commissioning-test-plan-concept-v0.1-2026-10-29-en.md docs/05-commissioning-test-plan-concept-v0.1-2026-10-29-en.pdf a4 9 \
  "DWU-DC-E-CX-005 · v0.1 · 2026-10-29 · CONCEPT / DRAFT — requires review by a licensed electrical engineer"
```

`scripts/sld_lib.py` is an unmodified copy of `../01-design-basis-sld/scripts/sld_lib.py`. The PDF prints need Google Chrome (headless).
