"""DWU-DC-E-SLD-001 sheet 1: 130/20 kV customer substation (H-arrangement), T1/T2 to the MSG-20 incomers."""
from sld_lib import *

STEM = "SLD-001-1_130kV_substation"


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-001", "130/20 kV substation — sheet 1",
                    "H-arrangement, T1/T2 to the MSG-20 incomers", 1, 2)
    XL, XR = 92, 328
    res = {}
    for x, n, nm, org, side, t, nt in ((XL, 1, "L1 'NORD'", "from DSO substation Nord (A)", -1, "T1", 3),
                                        (XR, 2, "L2 'SYD'", "from DSO substation Syd (A)", 1, "T2", 4)):
        lx = 7.0 if side < 0 else -7.0          # equipment labels towards the middle of the sheet
        text(ax, x, 281, f"130 kV LINE {name}" if False else f"130 kV LINE {nm}", fs=FS_TAG, weight="bold", c=HV_C, ha="center", va="top")
        text(ax, x, 274.5, org, c=HV_C, ha="center", va="top")
        arrow_down(ax, x, 269.5, c=HV_C, l=3.5)
        y, c1 = chain(ax, x, 266, [
            ("SA", ["SA 108 kV"], {"side": side}),
            ("VTU", ["VT 130/√3 / 0.11/√3 kV", "cl. 0.2 / 3P"], {"side": -side}),
            ("ES", [f"Q0{n}-E"], {"side": side}),
            ("DS", [f"Q0{n}-1 line disconnector"], {"lx": lx}),
            ("CT", ["CT 1200/1 A 5P20 + 0.2S"], {"cores": 2, "key": "ct_l", "lx": lx}),
            ("CB", [f"Q0{n}  CB 145 kV 2 000 A 40 kA"], {"key": "cb_l", "lx": lx}),
            ("L", None, {"h": 3}),
        ], c=HV_C, minh=9.5)
        bb_y = y
        x1, x2 = (x - 8, x + 26) if side < 0 else (x - 26, x + 8)
        bus(ax, x1, x2, bb_y, c=HV_C)
        text(ax, x + (-side) * 16, bb_y - 2.0, f"BB{n}", fs=FS_TAG, weight="bold", c=HV_C, ha="center", va="top")
        y_end, c2 = chain(ax, x, bb_y, [
            ("L", None, {"h": 5}),
            ("DS", [f"Q0{nt}-1 disconnector"], {"lx": lx}),
            ("CB", [f"Q0{nt}  CB 145 kV 2 000 A"], {"key": "cb_t", "lx": lx}),
            ("CT", ["CT 400/1 A 5P20 + 5P20"], {"cores": 2, "key": "ct_t", "lx": lx}),
            ("SA", None, {"side": side}),
            ("TX", [f"{t}  63 MVA ONAF", "130 ±9×1.67 % / 21 kV", "YNd11 · uk 12 % · OLTC"],
             {"c1": HV_C, "c2": MV_C, "key": "tx", "lx": lx * 1.6, "bold": True}),
            ("SA", None, {"side": side, "c": MV_C}),
            ("CT", ["CT 2500/1 A 5P20 (87T)"], {"cores": 1, "key": "ct_lv", "c": MV_C, "lx": lx}),
            ("L", ["20 kV cable", "3 × (3×1×630 Al)"], {"h": 10, "c": MV_C, "lx": lx}),
        ], c=HV_C, minh=9.5)
        res[n] = (bb_y, x1, x2)
        offpage(ax, x, y_end, f"MSG-20 {'S1' if n == 1 else 'S2'} incomer Q{n}0, sh 2", c=MV_C)
        # relays on the outer side
        rx = x - 24 if side < 0 else x + 24
        ha = "right" if side < 0 else "left"
        b = relay(ax, rx, c1["ct_l"], ["87L / 21", "50BF / 79 / 25"], tag=f"R-L{n}", ha=ha)
        xb = b[2] if side < 0 else b[0]
        ctl(ax, [(xb, c1["ct_l"]), (x + 2.2 * side, c1["ct_l"])])
        ctl(ax, [(xb, c1["ct_l"] - 4), (x + side * 9, c1["ct_l"] - 4), (x + side * 9, c1["cb_l"]), (x + side * 2.0, c1["cb_l"])])
        b = relay(ax, rx, c2["ct_t"] - 3, ["87T  64REF", "50/51  50N/51N", "63  26/49  50BF"], tag=f"R-{t}", ha=ha)
        xb = b[2] if side < 0 else b[0]
        xk = xb - side * 0 + side * 0
        ctl(ax, [(xb, c2["ct_t"]), (x + 2.2 * side, c2["ct_t"])])
        ctl(ax, [(b[0] + (b[2] - b[0]) / 2, b[1]), (b[0] + (b[2] - b[0]) / 2, c2["ct_lv"]), (x + 2.2 * side, c2["ct_lv"])])
        # YN neutral of the 130 kV winding: neutral disconnector + neutral CT (64REF) to earth
        yn = c2["tx"] + 3.9
        xs, xe = x + side * 6.0, x + side * 15.0
        line(ax, [(xs, yn), (xe, yn), (xe, yn - 1)], c=HV_C)
        disconnector(ax, xe, yn - 11, closed=True, c=HV_C)
        line(ax, [(xe, yn - 11), (xe, yn - 16)], c=HV_C)
        ct(ax, xe, yn - 13.5, c=HV_C)
        earth(ax, xe, yn - 16, c=HV_C)
        text(ax, xe + side * 3.0, yn - 6.0, "YN neutral", c=HV_C, ha="right" if side < 0 else "left")
    # bus-section (bridge) breaker between BB1 and BB2, normally open
    yb = res[1][0]
    xa, xb = res[1][2], res[2][1]
    xm = (xa + xb) / 2
    line(ax, [(xa, yb), (xm - 17, yb)], c=HV_C)
    disconnector_h(ax, xm - 17, yb, c=HV_C)
    breaker_h(ax, xm - 5, yb, closed=False, c=HV_C)
    disconnector_h(ax, xm + 7, yb, c=HV_C)
    line(ax, [(xm + 17, yb), (xb, yb)], c=HV_C)
    text(ax, xm, yb + 7.5, "Q-HBC bus-section CB · N.O.", ha="center", va="bottom", c=HV_C, weight="bold")
    text(ax, xm, yb - 3.5, "145 kV 2 000 A 40 kA", ha="center", va="top", c=HV_C)
    notes = ["SUBSTATION NOTES",
             "1  Each line + transformer carries the",
             "    whole campus (N+1): 37.8 MW design",
             "    peak, 42.6 MW with UPS recharge.",
             "2  Q-HBC closes only with one line out.",
             "3  T1 // T2 via MSG-20 is interlocked out",
             "    (IL-1 on sh 2, TODO B12).",
             "4  Arresters at the line entries and at",
             "    the HV and LV terminals of T1/T2.",
             "5  Protection supply 110 V DC,",
             "    2 × 100 % chargers + battery.",
             "6  Relay functions IEEE C37.2; settings",
             "    and CT data per CALC-003.",
             "7  130 kV earthing study is an open",
             "    point (DSO data, EN 50522)."]
    lines_text(ax, xm - 38, yb - 14, notes, first_bold=True)
    table(ax, 24, 78, [["Short-circuit level (CALC-003/004)", "Value"],
                        ["130 kV S''k max / min (A)", "3 000 / 1 500 MVA"],
                        ["20 kV normal (S0)", "13.0 kA, ip 34.4 kA"],
                        ["20 kV with BESS", "13.3 kA"],
                        ["Worst abnormal + BESS", "23.1 kA = 92 % of 25"],
                        ["T1 // T2 (not permitted)", "ip 58.5 kA = 94 %"]])
    save(fig, outdir, STEM)


if __name__ == "__main__":
    import os
    draw(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drawings"))
