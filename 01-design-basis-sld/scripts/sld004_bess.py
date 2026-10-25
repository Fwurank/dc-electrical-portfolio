"""DWU-DC-E-SLD-004: 10 MW / 20 MWh BESS plant, two units on MSG-20 bays Q19 / Q29."""
from sld_lib import *

STEM = "SLD-004_BESS_plant"


def unit(ax, x, n, q, sec):
    offpage(ax, x, 274, f"from MSG-20 {q} (SLD-001 sh 2)", direction="up", c=MV_C)
    y, cen = chain(ax, x, 274, [
        ("CB", [q, "VCB 630 A"], {"wd": True, "bold": True, "c": MV_C, "key": "cb", "lx": -5}),
        ("CT", ["CT 200/1", "5P20 + 0.2S"], {"cores": 2, "key": "ct", "c": MV_C, "lx": -5}),
        ("VT", ["VT 20/√3 / 0.1/√3 kV", "0.2 / 3P"], {"side": 1, "c": MV_C, "key": "vt"}),
        ("ES", None, {"side": 1, "c": MV_C}),
        ("SA", ["SA 24 kV"], {"side": 1, "c": MV_C}),
        ("L", ["3×1×240 Al 12/20 kV"], {"h": 9, "c": MV_C}),
        ("TX", [f"TR-B{n}", "5.5 MVA 20/0.69 kV", "Dyn11 · uk 8 % (A)"], {"c1": MV_C, "c2": GEN_C, "fs0": FS_TAG}),
        ("CB", [f"Q-B{n}", "ACB 5 000 A"], {"wd": True, "bold": True}),
        ("CONV", [f"PCS-{n}", "5.5 MVA, 4-quadrant", "grid-following (+GFM option)"], {"kind": "ac/dc", "fs0": FS_TAG}),
        ("L", ["DC 1 500 V"], {"h": 8}),
        ("BAT", [f"BESS-{n}", "5 MW / 10 MWh LFP", "4 × 2.5 MWh containers (A)"], {"fs0": FS_TAG}),
    ], c=GEN_C, lx=12, minh=9)
    return cen


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-004", "BESS plant — 10 MW / 20 MWh",
                    "2 units, MSG-20 bays Q19 / Q29, protection and EMS", 1, 1)
    for x, n, q, sec, rx in ((62, 1, "Q19", "S1", 128), (228, 2, "Q29", "S2", 294)):
        cen = unit(ax, x, n, q, sec)
        b = relay(ax, rx, cen["ct"], ["50/51 · 50N/51N · 67N", "27/59 · 81U/O · 59N", "ROCOF / VS (LoM)",
                                      "25 (GFM mode only)", f"intertrip ← R-INC{n}"], tag=f"R-B{n}")
        ctl(ax, [(b[0], cen["ct"] + 1.3), (x + 2.2, cen["ct"] + 1.3)])
        ctl(ax, [(b[0], cen["cb"]), (x + 2.6, cen["cb"])])
        meter(ax, b[0] + 14, b[1] - 9)
        text(ax, b[0] + 21, b[1] - 9, "0.2S revenue", c=CTL_C)
        ctl(ax, [(b[0] + 9.5, b[1] - 9), (x + 4.5, b[1] - 9), (x + 4.5, cen["ct"] - 1.3), (x + 2.2, cen["ct"] - 1.3)])
    # EMS
    box(ax, 340, 150, 66, 44, c=CTL_C, lw=THIN)
    lines_text(ax, 342, 192.5, ["EMS / PPC priorities", "1. Import ≤ 40 MW incl.", "    recharge", "2. SOC reserve before peaks",
                                "3. FCR down headroom", "4. Markets (FCR, mFRR)", "Fallback: IT power capping",
                                "→ R-B1, R-B2, PCS-1/2"], c=CTL_C, first_bold=True)
    rows = [["Item", "Rating (Rev P2)", "Note"],
            ["Bays Q19 / Q29", "VCB 630 A, CT 200/1 5P20 + 0.2S", "unit 159 A at 20 kV"],
            ["TR-B1 / TR-B2", "5.5 MVA 20/0.69 kV Dyn", "delta at 20 kV"],
            ["PCS-1 / PCS-2", "5.5 MVA each, 11 MVA total", "p.f. ≥ 0.95 at PCC"],
            ["BESS-1 / BESS-2", "5 MW / 10 MWh LFP each", "10 MW / 20 MWh"],
            ["I″k contribution", "≤ 1.2 × In (PCS limit), 13.0 → 13.3 kA", "CALC-004"]]
    table(ax, 24, 118, rows, title="BESS SCHEDULE")
    notes = ["NOTES",
             "1. Not counted as Tier III / EN 50600 Class 3 capacity;",
             "    firm IT gain +0.84 MW (peak shaving +2.4 MW).",
             "2. No island operation in the base design: 20 kV",
             "    relays do not clear an inverter-fed island fault",
             "    (381 A, R-FDR ≈ 60 s).",
             "3. Containers ≥ 10 m (A) from halls, transformers,",
             "    fuel; UL 9540A, NFPA 855, IEC 62933-5-2.",
             "4. Harmonic study (IEC/TR 61000-3-6) open."]
    lines_text(ax, 240, 128.0, notes, first_bold=True)
    save(fig, outdir, STEM)


if __name__ == "__main__":
    draw(os.path.join(os.path.dirname(__file__), "..", "drawings"))
