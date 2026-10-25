"""DWU-DC-E-SLD-002 sheet 1: data hall DH-1, hall MV board HV-DH1, 4 IT power blocks (4N/3) and 2N mechanical."""
from sld_lib import *

STEM = "SLD-002-1_DH1_MV_and_blocks"
YB = 228.0


def mv_bay(ax, x, tag, c=MV_C):
    text(ax, x + 1.2, YB - 2.0, tag, ha="left", va="top", c=c, weight="bold")
    line(ax, [(x, YB), (x, YB - 8)], c=c)
    return chain(ax, x, YB - 8, [
        ("CB", ["VCB 630 A"], {"wd": True}),
        ("CT", ["CT 150/1 → R-TX"], {"key": "ct"}),
        ("ES", None, {"side": 1}),
        ("SA", None, {"side": 1}),
        ("L", ["3×1×95 Al"], {"h": 9}),
        ("SA", None, {"side": 1}),
    ], c=c, lx=12, minh=9)


def lv_column(ax, x, tag, tx, txl, msb, msbl, gen, genl, out, mech=False):
    y, _ = mv_bay(ax, x, tag)
    y, cen = chain(ax, x, y, [
        ("TX", [tx, txl, "Dyn11 · uk 6 %"], {"c1": MV_C, "c2": LV_C, "fs0": FS_TAG}),
        ("L", None if mech else ["BTS 4 000 A"], {"h": 9, "bts": not mech}),
        ("CB", ["ACB", msbl], {"wd": True, "lx": 5}),
    ], c=LV_C, lx=12, minh=9)
    ym = y - 2
    line(ax, [(x, y), (x, ym)], c=LV_C)
    bus(ax, x - 6, x + 40, ym, c=LV_C)
    text(ax, x + 1.2, ym - 1.5, f"{msb}", fs=FS_TAG, va="top", c=LV_C, weight="bold")
    # genset below the MSB through its own ACB (ATS with the transformer incomer, open transition only)
    xg = x + 30
    line(ax, [(xg, ym), (xg, ym - 2)], c=GEN_C)
    breaker(ax, xg, ym - 2 - SW_H, c=GEN_C, withdrawable=True)
    if not mech:
        bts(ax, xg, ym - 2 - SW_H, xg, ym - 16)
    else:
        line(ax, [(xg, ym - 2 - SW_H), (xg, ym - 16)], c=GEN_C)
    generator(ax, xg, ym - 16)
    text(ax, xg + 7.5, ym - 20.0, gen, fs=FS_TAG, c=GEN_C, weight="bold")
    text(ax, xg + 7.5, ym - 26.0, genl, c=GEN_C)
    interlock(ax, [(x + 1.0, ym + 2.2), (x + 23, ym + 2.2), (x + 23, ym - 7), (xg - 2.8, ym - 7)])
    # outgoing to the UPS / mechanical loads (sheet 2)
    xo = x + 6 if False else x
    line(ax, [(x, ym), (x, ym - 9)], c=LV_C)
    arrow_down(ax, x, ym - 9, c=LV_C)
    lines_text(ax, x - 4, ym - 14.0, out, c=UPS_C)


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-002", "Data hall DH-1 — sheet 1",
                    "HV-DH1, IT power blocks A–D (4N/3), mechanical 2N", 1, 2)
    # HV-DH1 busbars + coupler
    line(ax, [(24, YB), (200, YB)], c=MV_C, lw=BUS_LW)
    line(ax, [(222, YB), (406, YB)], c=MV_C, lw=BUS_LW)
    text(ax, 118, YB + 2.0, "HV-DH1 S1", fs=FS_TAG, c=MV_C, va="bottom", weight="bold")
    text(ax, 150, YB + 2.0, "24 kV 1 250 A 25 kA", c=MV_C, va="bottom")
    text(ax, 236, YB + 2.0, "HV-DH1 S2", fs=FS_TAG, c=MV_C, va="bottom", weight="bold")
    text(ax, 268, YB + 2.0, "87B, 50ARC", c=MV_C, va="bottom")
    disconnector_h(ax, 200, YB, c=MV_C)
    breaker_h(ax, 210, YB, closed=False, c=MV_C)
    line(ax, [(220, YB), (222, YB)], c=MV_C)
    text(ax, 211, YB - 3.5, "N.O.", ha="center", va="top", c=MV_C, weight="bold")
    for x in (40, 190, 232, 380):
        arc_sensor(ax, x, YB + 3.0)
    # incomers from MSG-20
    for x, n, side, q in ((59, 1, 1, "Q11"), (362, 2, -1, "Q21")):
        offpage(ax, x, 270, f"from MSG-20 {q} (SLD-001 sh 2)", direction="up", c=MV_C)
        yy, cen = chain(ax, x, 270, [
            ("SA", None, {"side": -side}),
            ("ES", None, {"side": -side}),
            ("CT", ["CT 400/1 5P20 + 0.5S"], {"key": "ct", "lx": 7 * side}),
            ("CB", [f"S{n}-Q0  VCB 1 250 A"], {"wd": True, "lx": 7 * side}),
        ], c=MV_C, minh=8.5)
        line(ax, [(x, yy), (x, YB)], c=MV_C)
    # IL-2 hall-board coupler interlock
    interlock(ax, [(122, 243), (300, 243)])
    line(ax, [(213, 243), (213, YB + 4.5)], c=CTL_C, lw=THIN, ls=(0, (5, 1.5, 1, 1.5)))
    text(ax, 210, 251.5, "IL-2 (S1-Q0, S2-Q0, coupler): coupler closes only with one feeder open", ha="center", c=CTL_C)
    text(ax, 210, 246.5, "(both feeders + coupler = T1 // T2, 20.9 kA) · TODO B13", ha="center", c=CTL_C)
    text(ax, 210, 262, "Normal: S1 fed from MSG-20 S1, S2 from MSG-20 S2.", ha="center")
    text(ax, 210, 257, "Each feeder carries the whole hall: 7.0 MW, 213 A.", ha="center")
    for x, b, q in ((30, "A", "S1-Q1A"), (88, "C", "S1-Q1C"), (232, "B", "S2-Q2B"), (290, "D", "S2-Q2D")):
        lv_column(ax, x, q, f"T-{b}", "2 500 kVA", f"MSB-{b}", "4 000 A", f"G-{b}", "2 750 kVA",
                  [f"UPS-{b} / SBS-{b}", "SLD-002 sh 2"])
    for x, n, q in ((146, 1, "S1-Q1M"), (348, 2, "S2-Q2M")):
        lv_column(ax, x, q, f"T-M{n}", "1 600 kVA", f"MSB-M{n}", "2 500 A", f"G-M{n}", "1 650 kVA",
                  [f"MUPS-{n} / mech.", "SLD-002 sh 2"], mech=True)
    rows = [["Item", "Rating (Rev P2)", "Check (CALC-002/3)"],
            ["T-A…T-D", "2 500 kVA 20/0.42 kV Dyn11, uk 6 %, Pk 19 kW", "N-1 82 %"],
            ["G-A…G-D", "2 750 kVA / 2 200 kWe DCC, Isc ≥ 300 % 2 s", "N-1 88 %"],
            ["MSB-A…D", "4 000 A, Icw 65 kA 1 s, Ipk 143 kA", "52.3 kA"],
            ["UPS-A…D", "2 × 1 000 kW, 2 × 165 kWh LFP", "N-1 83 %"],
            ["UOSB-A…D", "3 200 A, 65 kA 1 s", "49.3 kA"],
            ["T-M1/M2", "1 600 kVA kept (1 250 kVA would be 83 %)", "65 %"],
            ["G-M / MUPS", "1 650 kVA; mech. UPS 2 × 250 kW", "step ≤ 33 %"]]
    table(ax, 24, 62, rows)
    lines_text(ax, 232, 140 if False else 62, [], first_bold=True)
    text(ax, 24, 66.0, "ATS (dash-dot): transformer ACB / genset ACB, open transition only (TODO B14). Gensets via BTS 4 000 A (B5).", va="bottom")
    save(fig, outdir, STEM)


if __name__ == "__main__":
    import os
    draw(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drawings"))
