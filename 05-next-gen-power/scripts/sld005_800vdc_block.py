"""DWU-DC-E-SLD-005 (draft v0.1): power block A, 800 VDC concept as an alternative to SLD-003 (Project 01).
Same block as Project 01: T-A 2 500 kVA, G-A 2 750 kVA, MSB-A, 4N/3 distributed redundancy, 1.25 / 1.67 MW."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import sld_lib as L
from draft_frame import frame_and_title_draft

OUT = os.path.join(os.path.dirname(__file__), "..", "drawings")
STEM = "SLD-005_800VDC_block_A_concept-v0.1-2026-10-29-en"
MV, LV, DC, CT_ = L.MV_C, L.LV_C, L.UPS_C, L.CTL_C


def sscb(ax, x, y_top, tag, lines, lx=7.0):
    """DC feeder breaker (SSCB / hybrid / DC MCCB, type TBD): breaker symbol + '=' mark. Returns y_bottom."""
    L.line(ax, [(x, y_top), (x, y_top - 2)], c=DC)
    L.breaker(ax, x, y_top - 2 - L.SW_H, c=DC)
    L.lines_text(ax, x + lx, y_top - 1.0, [tag] + lines, first_bold=True)
    return y_top - 2 - L.SW_H



def battery_stack(ax, x, y_top, c=L.INK, n=2):
    """IEC 60617 S00898-style battery: n series cells, each a long thin plate (+) over a short thick plate (−),
    joined by short leads. The '+' / '−' marks and equal plate widths keep it distinct from the earth symbol
    (three bars of decreasing width). Returns y_bottom."""
    y = y_top
    L.line(ax, [(x, y), (x, y - 1.5)], c=c); y -= 1.5
    for i in range(n):
        L.line(ax, [(x - 3.6, y), (x + 3.6, y)], c=c, lw=L.LW)            # long plate, positive
        L.line(ax, [(x - 1.7, y - 1.8), (x + 1.7, y - 1.8)], c=c, lw=L.LW + 1.8)  # short plate, negative
        y -= 1.8
        if i < n - 1:
            L.line(ax, [(x, y), (x, y - 2.0)], c=c); y -= 2.0
    L.text(ax, x - 4.6, y_top - 1.5, "+", ha="right", va="center")
    L.text(ax, x - 4.6, y, "−", ha="right", va="center")
    return y

def main():
    fig, ax = L.new_sheet()

    # ------------------------------------------------ main scheme: LF transformer T-A + rectifiers
    xT = 70
    L.offpage(ax, xT, 268, "from HV-DH1 S1-Q1A (SLD-002 sh 1)", direction="up", ha="left")
    y, cen = L.chain(ax, xT, 268, [
        ("CB", ["S1-Q1A", "VCB 630 A 25 kA (as SLD-003)"], {"c": MV, "bold": True}),
        ("CT", ["CT 150/1 → R-TX (as SLD-003)"], {"c": MV}),
        ("L", None, {"h": 3, "c": MV}),
        ("TX", ["T-A", "2 500 kVA 20/0.42 kV Dyn11", "uk 6 % (as SLD-003)"], {"c": MV, "c2": LV, "bold": True}),
        ("L", ["BTS 4 000 A"], {"h": 10, "c": LV, "lx": -4}),
        ("CB", ["Q-UI ACB 4 000 A"], {"c": LV, "lx": -7, "key": "qui"}),
        ("L", None, {"h": 5, "c": LV}),
    ], lx=7.0)
    yMSB = y
    L.bus(ax, 30, 220, yMSB, c=LV)
    L.text(ax, 80, yMSB + 1.8, "MSB-A", fs=L.FS_TAG, weight="bold", va="bottom")
    L.text(ax, 101, yMSB + 1.8, "400/230 V TN-S · 4 000 A · Icw 65 kA 1 s (as SLD-003)", va="bottom")

    xG = 212
    yg, cg = L.chain(ax, xG, 266, [
        ("G", ["G-A", "2 750 kVA / 2 200 kWe DCC", "HVO100 (as SLD-003)"], {"c": L.GEN_C, "bold": True, "lx": -9}),
        ("L", None, {"h": 1, "c": LV}),
    ])
    yQ = cen["qui"]
    L.line(ax, [(xG, yg), (xG, yQ + L.SW_H / 2)], c=LV)
    L.breaker(ax, xG, yQ - L.SW_H / 2, c=LV)
    L.line(ax, [(xG, yQ - L.SW_H / 2), (xG, yMSB)], c=LV)
    L.text(ax, xG - 7, yQ, "Q-GI ACB 4 000 A", ha="right")
    yIL = yQ + 6.5
    L.interlock(ax, [(xT + 2, yQ + 1), (xT + 2, yIL), (xG - 2, yIL), (xG - 2, yQ + 1)])
    L.text(ax, 110, yIL + 1.4, "IL-3: Q-UI / Q-GI open transition only (as SLD-003)", va="bottom")

    # MSB outgoing feeders -> rectifiers
    for k, x in (("R1", 45), ("R2", 110)):
        yy, _ = L.chain(ax, x, yMSB, [
            ("L", None, {"h": 3, "c": LV}),
            ("CB", [f"Q-{k} 2 000 A"], {"c": LV}),
            ("L", None, {"h": 3, "c": LV}),
            ("CONV", [f"RECT-A{k[1]}", "AC/DC 1 000 kW", "400 V AC → 800 V DC", "[Inference]"], {"c": DC, "kind": "ac/dc", "bold": True}),
            ("L", None, {"h": 10, "c": DC}),
        ])
        yDC = yy
    xLB = 175
    yy, _ = L.chain(ax, xLB, yMSB, [("L", None, {"h": 3, "c": LV}), ("CB", ["Q-LB 2 500 A", "load bank"], {"c": LV}), ("L", None, {"h": 4, "c": LV})])
    L.arrow_down(ax, xLB, yy + 0.5)

    # 800 V DC block bus
    L.bus(ax, 30, 220, yDC, c=DC)
    L.text(ax, 172, yDC + 6.4, "DCB-A 800 V DC", fs=L.FS_TAG, weight="bold", va="bottom")
    L.text(ax, 172, yDC + 1.8, "±400 V · 3 200 A [Inference]", va="bottom")

    # DC feeders to pair-groups AB / AC / AD (block A is in three pair-groups)
    yS = None
    for x, tag in ((55, "F-AB"), (90, "F-AC"), (125, "F-AD")):
        L.dot(ax, x, yDC)
        yS = sscb(ax, x, yDC, tag, ["1 250 A", "type TBD"], lx=4.5)
    yR = 100                                   # rack box top
    # AB goes into the typical rack; AC / AD leave the sheet
    for x, lab in ((90, "→ pair-group AC"), (125, "→ pair-group AD")):
        L.line(ax, [(x, yS), (x, yS - 6)], c=DC)
        L.arrow_down(ax, x, yS - 5.5)
        L.text(ax, x, yS - 12, lab, ha="center", va="top")

    # ESS on the DC bus (takes the role of the UPS battery)
    xE = 165
    L.dot(ax, xE, yDC)
    L.line(ax, [(xE, yDC), (xE, yDC - 2)], c=DC)
    L.breaker(ax, xE, yDC - 2 - L.SW_H, c=DC)
    yb = L.converter(ax, xE, yDC - 2 - L.SW_H - 1, "dc/dc", c=DC)
    L.line(ax, [(xE, yDC - 2 - L.SW_H), (xE, yDC - 3 - L.SW_H)], c=DC)
    L.line(ax, [(xE, yb), (xE, yb - 1)], c=DC)
    battery_stack(ax, xE, yb - 1, c=DC)
    L.lines_text(ax, xE + 6.5, yDC - 3, ["ESS-A", "DC/DC + LFP", "energy TBD", "(01: 2 × 165 kWh)"], first_bold=True)

    # midpoint earthing
    xM = 214
    L.dot(ax, xM, yDC)
    L.line(ax, [(xM, yDC), (xM, yDC - 4)], c=DC)
    L.resistor(ax, xM, yDC - 4, c=DC)
    L.line(ax, [(xM, yDC - 12), (xM, yDC - 13)], c=DC)
    L.earth(ax, xM, yDC - 13)
    L.lines_text(ax, xM + 4, yDC - 3, ["midpoint: HRG", "or solid, TBD"])

    # typical rack in pair-group AB, fed from block A and block B
    xr0, yr0, wr, hr = 30, 58, 170, 42
    L.box(ax, xr0, yr0, wr, hr, ls=(0, (4, 2)), lw=L.THIN)
    L.text(ax, xr0 + 2, yr0 + hr - 3.2, "RACK (typ.) in pair-group AB · DC PDU / power shelf", weight="bold")
    xA, xB, xc, yc = 55, 105, 80, yr0 + 20
    L.line(ax, [(xA, yS), (xA, yc)], c=DC)
    L.bts(ax, xA, yS - 3, xA, yr0 + hr + 2, c=DC)
    L.text(ax, xA - 2, yS - 8, "busway", ha="right")
    L.text(ax, xA - 2, yS - 12.6, "2-wire+PE", ha="right")
    L.text(ax, xB + 2, yr0 + hr + 9, "from DCB-B F-BA (typ.)", va="bottom")
    L.arrow_down(ax, xB, yr0 + hr + 8)
    L.line(ax, [(xB, yr0 + hr + 3), (xB, yc)], c=DC)
    L.line(ax, [(xA, yc), (xc - 4.5, yc)], c=DC); L.dot(ax, xA, yc)
    L.line(ax, [(xB, yc), (xc + 4.5, yc)], c=DC); L.dot(ax, xB, yc)
    L.line(ax, [(xA, yc), (xA, yc)], c=DC)
    L.converter(ax, xc, yc + 4.5, "dc/dc", c=DC)
    L.line(ax, [(xc, yc - 4.5), (xc, yr0 + 6)], c=DC)
    L.arrow_down(ax, xc, yr0 + 7)
    L.text(ax, xc + 3, yr0 + 4.5, "54 / 12 V to trays", va="center")
    L.lines_text(ax, 118, yr0 + 32, ["A/B ORing, DC/DC 800 → 54 V,", "BBU + capacitors in the rack", "(OCP Mt. Diablo v1.0.0,", "[Verified spec]; values TBD)",
                                     "RCD + ground-fault detection", "per DC PDU output"])

    # notes (bottom left)
    L.lines_text(ax, 25, 54, [
        "NOTES",
        "1. Same block as SLD-003: 4N/3, 1.25 MW normal, 1.67 MW N-1 (83 % of 2 × 1 000 kW). MV, T-A, G-A, IL-3 kept.",
        "2. Only the UPS / LV critical distribution is replaced. Aux, mechanical and AC loads stay as SLD-003.",
        "3. Feeder current I = P / U: 0.83 MW / 800 V ≈ 1 040 A in N-1, 0.42 MW ≈ 520 A normal [Inference].",
        "4. DC fault current = capacitor discharge + current-limited RECT / ESS. No IEEE 1584 method for DC;",
        "    IEEE P3002.12 (DC arcing-fault guide) is an active PAR, not a standard [Verified, opened 2026-10-29].",
        "5. Breaker type (SSCB / hybrid / DC MCCB), Icw, earthing, IMD and RCD settings: TBD from vendor data.",
        "6. Labels: [Verified] = source opened · [Search-level] · [Inference] = own estimate. All ratings concept only.",
    ], first_bold=True)

    # ------------------------------------------------ alternative B inset: SST
    x0, y0, w, h = 228, 168, 178, 104
    L.box(ax, x0, y0, w, h, ls=(0, (6, 2)), lw=L.THIN)
    L.text(ax, x0 + 3, y0 + h - 4, "ALTERNATIVE B: SST 20 kV AC → 800 V DC (outline only)", weight="bold")
    xs2 = 250
    L.offpage(ax, xs2, 250, "from HV-DH1 S1-Q1A", direction="up", ha="left")
    yy, _ = L.chain(ax, xs2, 250, [
        ("CB", ["S1-Q1A VCB 630 A"], {"c": MV}),
        ("L", None, {"h": 4, "c": MV}),
        ("CONV", ["SST-A", "MV AC/DC, isolated", "rating TBD", "[Search-level]"], {"c": DC, "kind": "ac/dc", "bold": True}),
        ("L", None, {"h": 6, "c": DC}),
    ])
    L.bus(ax, 235, 300, yy, c=DC)
    L.text(ax, 235, yy - 2.0, "DCB-A 800 V DC → as main scheme", va="top")
    L.lines_text(ax, 318, 250, [
        "Removes the T-A and RECT stages.",
        "No LV point for G-A + IL-3: needs",
        "MV gensets or an AC bus ahead",
        "of the SST [Inference].",
        "MV-side fault and arc study new.",
        "OCP SST spec v0.3.0",
        "[Search-level / Unverified]",
    ])

    # protection box (right column)
    L.relay(ax, 228, 120, ["SSCB / DC trip: I>, di/dt (TBD)", "IMD / ground fault (mandatory)", "optical arc detection, DC rated (TBD)",
                           "selectivity with rack fuses (TBD)"], tag="R-DC  (per DC feeder)")
    L.lines_text(ax, 228, 100, [
        "CODES (pointers, [Unverified] unless opened)",
        "IEC 60364 / SS 436 40 00 · EN 50600-2-2 · LVD 2014/35/EU",
        "IEC 61439 · IEC 62040 · IEC 60947-2 (DC breakers)",
        "OCP Mt. Diablo v1.0.0 [Verified] · NVIDIA 800 V DC [Vendor claim]",
        "No IEC / EN 800 V DC PDU standard in sources read [Inference].",
    ], first_bold=True)

    frame_and_title_draft(ax, "DWU-DC-E-SLD-005", "Power block A — 800 V DC concept (draft)",
                          "Alternative to SLD-003 · same 5 MW hall, 4N/3, blocks A–D",
                          revdesc="Research draft for Project 05, not issued")
    L.save(fig, OUT, STEM)


if __name__ == "__main__":
    main()
