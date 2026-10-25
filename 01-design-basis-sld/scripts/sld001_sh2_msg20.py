"""DWU-DC-E-SLD-001 sheet 2: 20 kV main switchgear MSG-20 (2 sections, 22 bays), earthing, BESS bays, schedule."""
from sld_lib import *

STEM = "SLD-001-2_MSG-20_switchgear"
YB = 210.0  # busbar level


def feeder(ax, x, tag, dest, c=MV_C, es_side=-1):
    text(ax, x + 1.2, YB - 2.0, tag, ha="left", va="top", c=c, weight="bold")
    y = YB - 8.0
    line(ax, [(x, YB), (x, y)], c=c)
    y, cen = chain(ax, x, y, [("CB", None, {"wd": True}), ("CT", None, {}), ("ES", None, {"side": es_side}),
                              ("SA", None, {"side": es_side}), ("L", None, {"h": 3})], c=c, minh=0)
    arrow_down(ax, x, y, c=c)
    text(ax, x, y - 5.0, dest, rot=90, ha="center", va="top", c=c)
    return cen


def incomer(ax, x, n, side):
    """Incomer Q10 / Q20 from T1 / T2 (sheet 1). side=+1 labels to the right."""
    offpage(ax, x, 262, f"from T{n} (sh 1)", direction="up", c=MV_C)
    lx = 7.0 * side
    y, cen = chain(ax, x, 262, [
        ("SA", None, {"side": -side}),
        ("ES", None, {"side": -side}),
        ("CT", [f"CT 2500/1 A 5P20 15 VA + 0.2S"], {"cores": 2, "key": "ct", "lx": lx}),
        ("CB", [f"Q{n}0  VCB 2 500 A 25 kA, withdrawable"], {"wd": True, "key": "cb", "lx": lx}),
        ("L", None, {"h": YB - 0}),
    ], c=MV_C, minh=10)
    return cen


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-001", "20 kV main switchgear MSG-20 — sheet 2",
                    "2 sections, coupler, earthing bays, BESS bays", 2, 2)
    X1, X2 = 34.0, 386.0
    # busbars
    line(ax, [(26, YB), (194, YB)], c=MV_C, lw=BUS_LW)
    line(ax, [(226, YB), (396, YB)], c=MV_C, lw=BUS_LW)
    text(ax, 104, YB + 9.0, "MSG-20 SECTION 1", fs=FS_TAG, weight="bold", c=MV_C, va="bottom")
    text(ax, 104, YB + 2.0, "24 kV 2 500 A 25 kA 3 s · Ip 62.5 kA", c=MV_C, va="bottom")
    text(ax, 316, YB + 9.0, "MSG-20 SECTION 2", fs=FS_TAG, weight="bold", c=MV_C, va="bottom", ha="right")
    text(ax, 316, YB + 2.0, "IEC 62271-200 · LSC2B-PM · IAC AFLR", c=MV_C, va="bottom", ha="right")
    # incomers (chain goes from 262 down to the busbar: clip the trailing line at YB)
    for x, n, side in ((X1, 1, 1), (X2, 2, -1)):
        y = 262.0
        offpage(ax, x, y, f"from T{n}, sh 1", direction="up", c=MV_C)
        lx = 7.0 * side
        yy, cen = chain(ax, x, y, [
            ("SA", None, {"side": -side}),
            ("ES", None, {"side": -side}),
            ("CT", ["CT 2500/1 A 5P20 + 0.2S"], {"cores": 2, "key": "ct", "lx": lx}),
            ("CB", [f"Q{n}0  VCB 2 500 A (wd)"], {"wd": True, "key": "cb", "lx": lx}),
        ], c=MV_C, minh=10)
        line(ax, [(x, yy), (x, YB)], c=MV_C)
        # relay + revenue meter at the incomer (outside the chain label area)
        rx = x + side * 62
        b = relay(ax, rx, 260, ["50/51  50N/51N", "67N  51V", "87B rev. block"], tag=f"R-INC{n}", ha="left" if side > 0 else "right")
        xin = b[0] if side > 0 else b[2]
        ctl(ax, [(xin, 260), (x + side * 4.0, 260), (x + side * 4.0, cen["ct"] + 1.3), (x + side * 2.2, cen["ct"] + 1.3)])
        mx = (b[2] + 9) if side > 0 else (b[0] - 9)
        meter(ax, mx, 262)
        text(ax, mx, 268.5, "0.2S", ha="center", va="bottom", c=CTL_C)
        ctl(ax, [(mx, 257.5), (mx, 247.0), (x + side * 5.5, 247.0), (x + side * 5.5, cen["ct"] - 1.3), (x + side * 2.2, cen["ct"] - 1.3)])
    # coupler Q-BC (N.O.) between the sections
    line(ax, [(194, YB), (196, YB)], c=MV_C)
    disconnector_h(ax, 196, YB, c=MV_C)
    breaker_h(ax, 206, YB, closed=False, c=MV_C)
    line(ax, [(216, YB), (226, YB)], c=MV_C)
    text(ax, 210, YB + 9.0, "Q-BC N.O.", ha="center", va="bottom", c=MV_C, weight="bold")
    text(ax, 210, YB - 3.5, "2 500 A", ha="center", va="top", c=MV_C)
    # interlock IL-1 between Q10, Q-BC, Q20
    yil = 243.0
    interlock(ax, [(X1 - 3, 228), (X1 - 3, yil), (X2 + 3, yil), (X2 + 3, 228)])
    line(ax, [(223, yil), (223, YB + 1.5)], c=CTL_C, lw=THIN, ls=(0, (5, 1.5, 1, 1.5)))
    text(ax, 219, 237.5, "IL-1  2-of-3 (Q10, Q-BC, Q20): no T1 // T2", ha="right", va="center", c=CTL_C)
    text(ax, 219, 232.5, "Q-BC auto-closes only after incomer open", ha="right", va="center", c=CTL_C)
    # feeders
    s1 = [(48, "Q11", "DH-1 A"), (61, "Q12", "DH-2 A"), (74, "Q13", "DH-3 A"), (87, "Q14", "DH-4 A"),
          (100, "Q15", "DH-5 A"), (113, "Q16", "DH-6 A"), (128, "Q17", "ESG-1"), (143, "Q18", "AUX-1"),
          (158, "Q19", "BESS-1"), (173, "Q1A", "spare")]
    s2 = [(372, "Q21", "DH-1 B"), (359, "Q22", "DH-2 B"), (346, "Q23", "DH-3 B"), (333, "Q24", "DH-4 B"),
          (320, "Q25", "DH-5 B"), (307, "Q26", "DH-6 B"), (292, "Q27", "ESG-2"), (277, "Q28", "AUX-2"),
          (262, "Q29", "BESS-2"), (247, "Q2A", "spare")]
    for x, tag, dest in s1 + s2:
        feeder(ax, x, tag, dest, c=GEN_C if "BESS" in dest else MV_C)
    # bus VTs
    for x, tag in ((186, "VT1"), (234, "VT2")):
        text(ax, x + 1.2, YB - 2.0, tag, ha="left", va="top", c=MV_C, weight="bold")
        line(ax, [(x, YB), (x, YB - 8)], c=MV_C)
        disconnector(ax, x, YB - 18, c=MV_C)
        line(ax, [(x, YB - 18), (x, YB - 20)], c=MV_C)
        fuse(ax, x, YB - 26, h=6, c=MV_C)
        line(ax, [(x, YB - 26), (x, YB - 27)], c=MV_C)
        ax.add_patch(Circle((x, YB - 28.8), 1.8, fill=False, ec=MV_C, lw=LW, zorder=4))
        ax.add_patch(Circle((x, YB - 31.0), 1.8, fill=False, ec=MV_C, lw=LW, zorder=4))
        earth(ax, x, YB - 32.8, c=MV_C)
        text(ax, x, YB - 40.0, "20/√3 / 0.1/√3 /\n0.1/3 kV · 59N" if False else "59N  27/59", rot=90, ha="center", va="top", c=MV_C)
    # optical arc sensors on the busbars
    for x in (52, 92, 190, 232, 330, 368):
        arc_sensor(ax, x, YB + 2.2)
    # ---------------- lower part: schedule + details
    rows = [["Bay", "Feeds", "Device", "CT", "Protection / metering"],
            ["Q10 / Q20", "T1 / T2 incomer", "VCB 2 500 A wd", "2500/1 5P20 + 0.2S", "51 SI 2 100 A TMS 0.16\n50 6 000 A 0.65 s"],
            ["Q11–16 / Q21–26", "DH-1…6 feed A / B", "VCB 630 A wd", "400/1 5P20 15 VA", "51 VI 320 A TMS 0.84\n50 2 400 A 0.35 s"],
            ["Q17 / Q27", "ESG: ZNyn + coil", "VCB 630 A wd", "200/1 5P20", "50/51, 51N, 59N"],
            ["Q18 / Q28", "Aux 500 kVA", "VCB 630 A wd", "100/1 5P20", "50/51, 50N/51N"],
            ["Q19 / Q29", "BESS-1 / -2 5.5 MVA", "CB 630 A wd", "200/1 5P20 + 0.2S", "see SLD-004"],
            ["Q1A / Q2A", "spare, equipped", "VCB 630 A wd", "400/1 5P20", "as feeders"],
            ["Q-BC", "coupler (N.O.)", "VCB 2 500 A wd", "2500/1 5P20", "50/51, IL-1"]]
    table(ax, 24, 134, rows, title="FEEDER SCHEDULE (relay settings per CALC-003)")
    # DETAIL B: earthing bay with Petersen coil + parallel resistor (TODO B21/B25)
    text(ax, 24, 70.0, "DETAIL B  earthing bay Q17 / Q27", fs=FS_MIN + 1, weight="bold", va="bottom")
    x = 40
    line(ax, [(x, 67), (x, 64)], c=MV_C)
    y = transformer(ax, x, 64, c1=MV_C, c2=MV_C)
    lines_text(ax, x + 9, 62.5, ["ZNyn earthing transformer", "400 kVA aux winding (A)"], c=MV_C)
    line(ax, [(x, y), (x, y - 3)], c=MV_C)
    y -= 3
    dot(ax, x, y, c=MV_C)
    xr = x + 14
    line(ax, [(x, y), (xr, y)], c=MV_C)
    ye = inductor_adj(ax, x, y - 1, h=11, c=MV_C)
    line(ax, [(x, y), (x, y - 1)], c=MV_C)
    yg = y - 20
    line(ax, [(x, ye), (x, yg)], c=MV_C)
    line(ax, [(xr, y), (xr, y - 1)], c=MV_C)
    breaker(ax, xr, y - 11, closed=False, c=MV_C) if False else switch_disconnector(ax, xr, y - 11, closed=False, c=MV_C)
    line(ax, [(xr, y - 11), (xr, y - 12)], c=MV_C)
    resistor(ax, xr, y - 12, h=6, c=MV_C)
    line(ax, [(xr, y - 18), (xr, yg), (x, yg)], c=MV_C)
    earth(ax, x, yg, c=MV_C)
    lines_text(ax, xr + 6, y + 1.5, ["Petersen coil ≥ 50 A, adjustable", "10 … 60 A, auto-tuned", "∥ 10 A resistor, switched",
                                    "Ic 22 A/section, 44 A coupled,", "+1 A BESS → 67N admittance"], c=MV_C)
    # DETAIL / notes block above the title block
    notes = ["NOTES",
             "1  Resonant (compensated) earthing kept; 500 A",
             "    low-resistance earthing rejected (CALC-003).",
             "2  All feeders: 67N admittance earth-fault relays.",
             "3  Reverse-blocking busbar protection + optical",
             "    arc protection (50ARC, light + current) trips",
             "    the section incomer and Q-BC (TODO B18).",
             "4  Hall-board coupler closes only with one hall",
             "    feeder open (IL-2, SLD-002 sh 1).",
             "5  Every bay: SA 24 kV at the cable end, ES, EPMS 0.5S.",
             "6  DH feeders A → HV-DH1 S1, B → S2 (SLD-002).",
             "7  ESG-1/2: detail B. AUX: 500 kVA station aux.",
             "8  BESS bays Q19 / Q29 → SLD-004 (TODO B22)."]
    lines_text(ax, 296, 136, notes, first_bold=True)
    save(fig, outdir, STEM)


if __name__ == "__main__":
    import os
    draw(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drawings"))
