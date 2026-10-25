"""DWU-DC-E-SLD-003 sheet 2: power block A UPS system, SBS, MBB, UOSB-A and critical distribution down to the rack."""
from sld_lib import *

STEM = "SLD-003-2_block_A_UPS_critical"
YO, YU = 222.0, 186.0     # UPS output bus, UOSB-A


def ups_module(ax, x, n, q):
    offpage(ax, x, 270, f"from MSB-A {q} (sh 1)", direction="up", c=LV_C)
    y, cen = chain(ax, x, 270, [
        ("L", None, {"h": 2}),
        ("UPS", [f"UPS-A{n}", "1 000 kW · VFI-SS-111", "LFP 165 kWh (5 min EoL)"], {"fs0": FS_TAG, "bside": -1, "c": UPS_C}),
        ("CB", [f"Q-O{n}", "ACB 1 600 A"], {"wd": True, "bold": True}),
    ], c=UPS_C, lx=12)
    line(ax, [(x, y), (x, YO)], c=UPS_C)


def flag(ax, x, y, s):
    """Fault-level flag: kA value in a small box (CALC-003)."""
    w = tw(s) * 1.04 + 3.0
    box(ax, x, y - 2.9, w, 5.8, c=HV_C, lw=THIN, fill="white", z=3)
    text(ax, x + 1.5, y, s, c=HV_C)


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-003", "Power block A — sheet 2",
                    "UPS-A1/A2, SBS, MBB, UOSB-A, busway to rack (typical)", 2, 2)
    ups_module(ax, 46, 1, "Q-R1")
    ups_module(ax, 122, 2, "Q-R2")
    # static bypass
    xs = 196
    offpage(ax, xs, 270, "BTS 3 200 A from Q-SB (sh 1)", direction="up", c=LV_C)
    y, _ = chain(ax, xs, 270, [
        ("L", None, {"h": 2}),
        ("SBS", ["SBS-A", "3 200 A static bypass"], {"fs0": FS_TAG, "c": UPS_C}),
        ("L", None, {"h": 6}),
        ("CB", ["Q-SBO", "ACB 3 200 A"], {"wd": True, "bold": True}),
    ], c=UPS_C, lx=8)
    line(ax, [(xs, y), (xs, YO)], c=UPS_C)
    bus(ax, 30, 214, YO, c=UPS_C)
    text(ax, 32, YO - 1.5, "UPS output bus 3 200 A", va="top", c=UPS_C, weight="bold")
    # output breaker to UOSB (key-interlocked with MBB)
    xq = 160
    y, cq = chain(ax, xq, YO, [("CB", ["Q-UO", "ACB 3 200 A"], {"wd": True, "bold": True, "key": "q"})], c=UPS_C, lx=5, minh=14)
    line(ax, [(xq, y), (xq, YU)], c=UPS_C)
    # maintenance bypass from MSB-A Q-MB
    xm = 262
    offpage(ax, xm, 270, "from MSB-A Q-MB (sh 1)", direction="up", c=LV_C)
    y, cm = chain(ax, xm, 270, [
        ("L", None, {"h": 30}),
        ("CB", ["Q-MBB", "ACB 3 200 A", "maint. bypass"], {"wd": True, "bold": True, "key": "q", "closed": False}),
    ], c=LV_C, lx=5, minh=14)
    line(ax, [(xm, y), (xm, YU)], c=LV_C)
    interlock(ax, [(xq + 2.6, cq["q"]), (xq + 40, cq["q"]), (xq + 40, cm["q"]), (xm - 2.6, cm["q"])])
    text(ax, xq + 42, cq["q"] - 3.5, "IL-4 key interlock: Q-UO / Q-MBB", va="top", c=CTL_C)
    text(ax, xq + 42, cq["q"] - 8.1, "(one key, never both closed)", va="top", c=CTL_C)
    # UOSB-A
    bus(ax, 24, 300, YU, c=UPS_C)
    text(ax, 28, YU + 1.5, "UOSB-A", fs=FS_TAG, weight="bold", va="bottom", c=UPS_C)
    text(ax, 58, YU + 1.5, "3 200 A · Icw 65 kA 1 s", va="bottom", c=UPS_C)
    flag(ax, 278, YU + 5.0, "49.3 kA")
    for x in (100, 230):
        arc_sensor(ax, x, YU + 3.0)
    # SPD type 2
    line(ax, [(290, YU), (290, YU - 4)], c=UPS_C)
    fuse(ax, 290, YU - 10, h=6, c=UPS_C)
    line(ax, [(290, YU - 10), (290, YU - 12)], c=UPS_C)
    arrester(ax, 290, YU - 12, side=1, dx=0.0, c=UPS_C)
    text(ax, 294, YU - 9.0, "SPD T2", c=UPS_C)
    # busway feeders: BW-A1 in full, A2..A6 typical
    for i in range(6):
        xd = 36 if i == 0 else 100 + 36 * (i - 1)
        line(ax, [(xd, YU), (xd, YU - 2)], c=UPS_C)
        breaker(ax, xd, YU - 14, c=UPS_C, withdrawable=True)
        text(ax, xd + 3.0, YU - 6.0, f"MCCB BW-A{i + 1}", c=UPS_C, weight="bold")
        if i == 0:
            continue
        bts(ax, xd, YU - 14, xd, 150)
        arrow_down(ax, xd, 150, c=UPS_C)
        text(ax, xd + 3.0, YU - 22.0, "busway 800 A", c=UPS_C)
        text(ax, xd + 3.0, 154.0, "as BW-A1", c=UPS_C)
    xd = 36
    lines_text(ax, xd + 3.0, YU - 9.3, ["800 A, Icu ≥ 50 kA", "current-limiting"], c=UPS_C)
    bts(ax, xd, YU - 14, xd, 128)
    lines_text(ax, xd + 3.0, 164.0, ["busway 800 A, Icw 36 kA", "cond. ≥ 40 kA (IEC 61439-6)"], c=UPS_C)
    flag(ax, xd + 3.0, 148.0, "37.1 kA")
    # tap-off unit
    box(ax, xd - 6, 110, 50, 18, c=UPS_C, ls=(0, (3, 1.5)), lw=THIN)
    breaker(ax, xd, 114, c=UPS_C)
    line(ax, [(xd, 128), (xd, 124)], c=UPS_C)
    lines_text(ax, xd + 3.0, 125.5, ["tap-off 63 A MCCB", "Icu ≥ 36 kA"], c=UPS_C)
    flag(ax, xd + 26.0, 114.0, "25.1 kA")
    line(ax, [(xd, 114), (xd, 98)], c=UPS_C)
    # rack PDU / server
    box(ax, xd - 8, 86, 16, 12, c=UPS_C)
    text(ax, xd, 92, "PDU-A", ha="center", c=UPS_C)
    box(ax, xd + 22, 86, 16, 12, c=LV_C)
    text(ax, xd + 30, 92, "PDU-B", ha="center", c=LV_C)
    line(ax, [(xd + 30, 98), (xd + 30, 104), (xd + 50, 104)], c=LV_C)
    text(ax, xd + 52, 104, "B-cord from BW-B1 (block B)", c=LV_C)
    line(ax, [(xd, 86), (xd, 80), (xd + 30, 80), (xd + 30, 86)], c=INK)
    text(ax, xd - 8, 75.0, "rack: 2 PSUs, each 100 %", c=INK)
    flag(ax, xd + 42, 90.0, "14.0 kA · PDU SCCR ≥ 15 kA")
    # equipment schedule
    rows = [["Item", "Rating (Rev P2)", "Basis"],
            ["UPS-A1/A2", "1 000 kW each, VFI-SS-111", "N-1 83 %"],
            ["Battery", "LFP 165 kWh per module, ≤ 8 C EoL", "B1"],
            ["Rectifier breaker", "Q-R1/Q-R2 2 000 A (1 660 A max)", "B2"],
            ["SBS / MBB", "3 200 A, BTS 3 200 A from MSB", "B4"],
            ["Busway MCCB", "800 A, Icu ≥ 50 kA, cond. ≥ 40 kA", "B3, B15"],
            ["Tap-off / PDU", "63 A Icu ≥ 36 kA; SCCR ≥ 15 kA", "B16"]]
    table(ax, 140, 140, rows, title="EQUIPMENT SCHEDULE")
    notes = ["NOTES",
             "1. Fault levels in boxes: I″k per CALC-003.",
             "2. SBS is centralised per block; MBB is",
             "    external wrap-around (IL-4).",
             "3. A2…A6 identical to BW-A1; pairing per",
             "    SLD-002 sh 2."]
    lines_text(ax, 300, 160.0, notes, first_bold=True)
    save(fig, outdir, STEM)


if __name__ == "__main__":
    draw(os.path.join(os.path.dirname(__file__), "..", "drawings"))
