# Portfolio project 01 — Design basis & concept SLD, Rev P2 (30 MW IT data center, Sweden, fictional)

* `docs/01_Design_Basis.md` is the design basis source. `docs/DWU-DC-E-DB-001_Design_Basis.pdf` is the rendered PDF, Rev P2, with all 8 SLD previews in Appendix A. §12 traces every change back to `../TODO_final_fixes.md`.
* `drawings/SLD-*.svg|pdf|png` are the 8 A3 landscape sheets, Rev P2:
  * SLD-000: legend, colour code, drawing list, notes
  * SLD-001-1: 130 kV substation
  * SLD-001-2: MSG-20
  * SLD-002-1: hall DH1, MV and LV columns
  * SLD-002-2: white space and mechanical
  * SLD-003-1: block A, MV/LV and MSB
  * SLD-003-2: block A, UPS and critical path
  * SLD-004: BESS plant
* `drawings/DWU-DC-E-SLD_concept_set_RevP2_A3.pdf` is the combined set. `drawings/superseded_RevP1/` keeps the old 3-sheet P1 set, for reference only.
* `drawings/text_height_check.json` is the measured text-height and layout check:
  * every text has a cap height of ≥ 2.5 mm at A3 (minimum 2.57 mm)
  * the drawing number is 5.14 mm
  * there are 0 overlaps
* `scripts/`:
  * `sld_lib.py`: IEC 60617-style symbols, A3 frame and title block
  * `sld0xx_*.py`: one script per sheet
  * `sheets.py`: the sheet list
  * `check_drawings.py`: text-height and overlap checker
  * `build_all.py`: builds the sheets, the set PDF, the check and the DB PDF

Rebuild: `python3 -m venv .venv && .venv/bin/pip install matplotlib markdown && .venv/bin/python scripts/build_all.py`.
It needs poppler `pdfunite` and Google Chrome for the PDF print. All data are public or assumed; not for construction.
