"""Tests for the Rev P2 SLD generators (project 01): every sheet renders, carries its key labels,
keeps all text >= 2.5 mm cap height at A3 and has no text overlaps (scripts/check_drawings.py)."""
import importlib, json, os, subprocess, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS)
from sheets import SHEETS  # noqa: E402

LABELS = {"SLD-000_legend_notes": ["IEC 60617", "Current transformer", "Surge arrester"],
          "SLD-001-1_130kV_substation": ["130", "20 kV"],
          "SLD-001-2_MSG-20_switchgear": ["20 kV", "BESS", "Petersen"],
          "SLD-002-1_DH1_MV_and_blocks": ["DH-1", "HV-DH1", "MSB-A"],
          "SLD-002-2_DH1_whitespace_mech": ["UPS-A", "UOSB-A", "4N/3"],
          "SLD-003-1_block_A_MV_LV": ["MSB-A", "R-TX", "50ARC"],
          "SLD-003-2_block_A_UPS_critical": ["UPS-A1", "SBS-A", "Q-MBB"],
          "SLD-004_BESS_plant": ["BESS-1", "Q19", "ROCOF"]}


@pytest.mark.parametrize("modname,stem", SHEETS)
def test_sheet_renders(tmp_path, modname, stem):
    importlib.import_module(modname).draw(str(tmp_path)); plt.close("all")
    for ext in ("svg", "pdf", "png"):
        f = tmp_path / f"{stem}.{ext}"
        assert f.exists() and f.stat().st_size > 5_000, f
    svg = (tmp_path / f"{stem}.svg").read_text(encoding="utf-8")
    assert "P2" in svg
    for lab in LABELS[stem]:
        assert lab in svg, f"{lab!r} missing in {stem}"


def test_text_height_and_layout(tmp_path):
    out = tmp_path / "check.json"
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_drawings.py"), "--json", str(out)],
                       capture_output=True, text=True, env={**os.environ, "SLD_CHECK_OUT": str(tmp_path)})
    assert r.returncode == 0, r.stdout + r.stderr
    rep = json.loads(out.read_text())
    assert len(rep["sheets"]) == len(SHEETS)
    for stem, s in rep["sheets"].items():
        assert s["min_cap_mm"] >= 2.5, stem
        assert not s["layout_issues"] and s["ok"], stem


def test_design_basis_mentions_key_numbers():
    md = open(os.path.join(os.path.dirname(__file__), "..", "docs", "01_Design_Basis.md"), encoding="utf-8").read()
    for s in ("40 MW", "SE3", "4N/3", "3 000 MVA", "BESS", "Rev P2"):
        assert s in md
