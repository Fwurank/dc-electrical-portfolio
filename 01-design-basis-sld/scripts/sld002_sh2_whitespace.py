"""DWU-DC-E-SLD-002 sheet 2: DH-1 UPS outputs, UOSB boards, busways to the 4N/3 pair-groups, mechanical 2N."""
from sld_lib import *

STEM = "SLD-002-2_DH1_whitespace_mech"
PAIRS = {"A": ("AB", "AC", "AD"), "B": ("AB", "BC", "BD"), "C": ("AC", "BC", "CD"), "D": ("AD", "BD", "CD")}


def it_block(ax, x0, b):
    x, xs, xm = x0 + 10, x0 + 50, x0 + 30
    offpage(ax, xm, 270, f"from MSB-{b} (sh 1)", direction="up", c=LV_C)
    line(ax, [(xm, 270), (xm, 266)], c=LV_C)
    line(ax, [(x, 266), (xs, 266)], c=LV_C, lw=LW + 0.6)
    dot(ax, xm, 266, c=LV_C)
    # UPS branch (2 parallel modules drawn as one compound symbol)
    line(ax, [(x, 266), (x, 264)], c=LV_C)
    breaker(ax, x, 252, c=LV_C, withdrawable=True)
    yb = ups(ax, x, 252)
    text(ax, x + 12, 246.0, f"UPS-{b}", fs=FS_TAG, c=UPS_C, weight="bold")
    text(ax, x + 12, 240.0, "2 × 1 000 kW", c=UPS_C)
    text(ax, x + 12, 235.4, "VFI-SS-111", c=UPS_C)
    line(ax, [(x, yb), (x, 218)], c=UPS_C)
    # static bypass branch
    line(ax, [(xs, 266), (xs, 254)], c=LV_C)
    y2 = static_switch(ax, xs, 254)
    text(ax, xs + 6, 249.5, "SBS", c=UPS_C)
    line(ax, [(xs, y2), (xs, 218)], c=UPS_C)
    # UOSB board and 6 busway feeders
    bus(ax, x0 + 2, x0 + 70, 218, c=UPS_C)
    text(ax, x + 12, 219.8, f"UOSB-{b}", fs=FS_TAG, c=UPS_C, va="bottom", weight="bold")
    for i in range(6):
        xd = x0 + 6 + 12 * i
        line(ax, [(xd, 218), (xd, 216)], c=UPS_C)
        breaker(ax, xd, 204, c=UPS_C, withdrawable=True)
        bts(ax, xd, 204, xd, 152, c=UPS_C)
        arrow_down(ax, xd, 152, c=UPS_C)
        text(ax, xd + 2.2, 200.0, f"BW-{b}{i + 1} → {PAIRS[b][i // 2]}", rot=90, ha="left", va="top", c=UPS_C)
    text(ax, x0 + 36, 141.5, "pair-groups " + " · ".join(PAIRS[b]), ha="center", c=UPS_C)


def mech_col(ax, c, n):
    xa, xb = c - 10, c + 8
    offpage(ax, c, 270, f"from MSB-M{n} (sh 1)", direction="up", c=LV_C)
    line(ax, [(c, 270), (c, 266)], c=LV_C)
    bus(ax, c - 15, c + 18, 266, c=LV_C)
    text(ax, xb + 3.0, 263.0, f"MSB-M{n}", va="top", c=LV_C, weight="bold")
    for xx in (xa, xb):
        line(ax, [(xx, 266), (xx, 264)], c=LV_C)
        breaker(ax, xx, 252, c=LV_C, withdrawable=True)
    line(ax, [(xa, 252), (xa, 160)], c=LV_C)
    arrow_down(ax, xa, 160, c=LV_C)
    text(ax, xa - 2.2, 248.0, "trim chillers, dry coolers (non-UPS)", rot=90, ha="right", va="top", c=LV_C)
    yb = ups(ax, xb, 252, side=1)
    line(ax, [(xb, yb), (xb, 160)], c=UPS_C)
    arrow_down(ax, xb, 160, c=UPS_C)
    text(ax, xb + 2.2, yb - 2.0, f"MUPS-{n} 2 × 250 kW → fans, CDUs, pumps", rot=90, ha="left", va="top", c=UPS_C)


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-002", "Data hall DH-1 — sheet 2",
                    "UPS, UOSB, busways to 4N/3 pair-groups; mechanical 2N", 2, 2)
    for i, b in enumerate("ABCD"):
        it_block(ax, 24 + 72 * i, b)
    for c, n in ((334, 1), (376, 2)):
        mech_col(ax, c, n)
    text(ax, 355, 141.5, "2N: M1 and M2 each 100 %", ha="center", c=LV_C)

    t1 = [["Pair-group", "Busways (block 1)", "Busways (block 2)", "IT load"],
          ["AB", "BW-A1, BW-A2", "BW-B1, BW-B2", "0.83 MW"],
          ["AC", "BW-A3, BW-A4", "BW-C1, BW-C2", "0.83 MW"],
          ["AD", "BW-A5, BW-A6", "BW-D1, BW-D2", "0.83 MW"],
          ["BC", "BW-B3, BW-B4", "BW-C3, BW-C4", "0.83 MW"],
          ["BD", "BW-B5, BW-B6", "BW-D3, BW-D4", "0.83 MW"],
          ["CD", "BW-C5, BW-C6", "BW-D5, BW-D6", "0.83 MW"]]
    x2, _ = table(ax, 24, 130, t1, title="4N/3 ALLOCATION")
    text(ax, 24, 88.0, "Each rack is dual-corded to the two blocks of one pair-group (2 busway runs per block).")
    t2 = [["Case", "Block load", "UPS", "Busway"],
          ["Normal", "1.25 MW", "63 %", "307 A"],
          ["Loss of 1 block", "1.67 MW", "83 %", "614 A"],
          ["DCIM limit", "≤ 1.67 MW", "—", "Ir 800 A"]]
    table(ax, x2 + 14, 130, t2, title="LOADING (CALC-002)")
    notes = ["NOTES",
             "1. UOSB 3 200 A, Icw 65 kA 1 s; SPD type 2.",
             "2. Busway MCCB 800 A current-limiting, Icu ≥ 50 kA,",
             "    tested conditional rating ≥ 40 kA (IEC 61439-6).",
             "3. Busway 800 A, Icw 36 kA; tap-off 63 A MCCB",
             "    Icu ≥ 36 kA; rack PDU SCCR ≥ 15 kA (CALC-003).",
             "4. Battery per UPS module LFP 165 kWh (5 min).",
             "5. Block A detail: SLD-003 sh 1–2."]
    lines_text(ax, 300, 133.0, notes, first_bold=True)
    save(fig, outdir, STEM)


if __name__ == "__main__":
    draw(os.path.join(os.path.dirname(__file__), "..", "drawings"))
