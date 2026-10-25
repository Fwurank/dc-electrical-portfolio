"""DWU-DC-E-SLD-003 sheet 1: power block A (typical of 24), 20 kV feeder, T-A, genset G-A, MSB-A, protection."""
from sld_lib import *

STEM = "SLD-003-1_block_A_MV_LV"
YM = 168.0        # MSB-A busbar
XT, XG = 60.0, 250.0


def feeder(ax, x, tag, rating, dest, c=LV_C):
    line(ax, [(x, YM), (x, YM - 3)], c=c)
    y, cen = chain(ax, x, YM - 3, [("CB", [tag, rating], {"wd": True, "bold": True})], c=c, lx=4.5)
    line(ax, [(x, y), (x, 132)], c=c)
    offpage(ax, x, 132, "", c=c)
    lines_text(ax, x - 3, 124.5, dest, c=c)


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-003", "Power block A — sheet 1",
                    "20 kV feeder, T-A, genset G-A, MSB-A (typical of 24)", 1, 2)
    # --- transformer incomer
    offpage(ax, XT, 274, "from HV-DH1 S1-Q1A (SLD-002 sh 1)", direction="up", c=MV_C)
    y, cen = chain(ax, XT, 274, [
        ("CB", ["S1-Q1A", "VCB 630 A 25 kA"], {"wd": True, "bold": True, "c": MV_C, "key": "cb"}),
        ("CT", ["CT 150/1 5P20 10 VA", "Ith ≥ 25 kA 1 s"], {"key": "ct", "c": MV_C}),
        ("ES", None, {"side": -1, "c": MV_C}),
        ("L", ["3×1×95 Al 12/20 kV"], {"h": 9, "c": MV_C}),
        ("SA", ["SA 24 kV"], {"side": -1, "c": MV_C}),
        ("TX", ["T-A", "2 500 kVA 20/0.42 kV", "Dyn11 · uk 6 % · cast resin", "Pk 19 kW · P0 3.1 kW"],
         {"c1": MV_C, "c2": LV_C, "fs0": FS_TAG}),
        ("L", ["BTS 4 000 A ≈ 10 m"], {"h": 9, "bts": True}),
        ("CT", ["CT 4000/1 → Wh"], {"key": "ctlv"}),
        ("CB", ["Q-UI ACB 4 000 A", "Ir 3 600 A · ARMS"], {"wd": True, "key": "qui", "lx": -5}),
    ], c=LV_C, lx=12, minh=9)
    line(ax, [(XT, y), (XT, YM)], c=LV_C)
    # R-TX relay at the 20 kV bay
    b = relay(ax, 150, cen["ct"], ["50/51 Is 100 A, IEC EI, TMS 1.0", "50 I≫ 1 500 A, 0.05 s", "50N/51N · 86 lock-out"], tag="R-TX")
    ctl(ax, [(b[0], cen["ct"]), (XT + 2.2, cen["ct"])])
    ctl(ax, [(b[0] + 6, b[3]), (b[0] + 6, cen["cb"]), (XT + 2.6, cen["cb"])])
    text(ax, 100, cen["cb"] + 0.8, "trip", c=CTL_C, va="bottom")
    meter(ax, 30, cen["ctlv"])
    ctl(ax, [(34.5, cen["ctlv"]), (XT - 2.2, cen["ctlv"])])
    # --- genset incomer
    y, cg = chain(ax, XG, 270, [
        ("G", ["G-A", "2 750 kVA / 2 200 kWe DCC", "Isc ≥ 300 % for 2 s", "HVO100, 24 h"], {"fs0": FS_TAG, "c": GEN_C}),
        ("CT", ["CT 4000/1 → 51V, Wh"], {"key": "ctg", "c": GEN_C}),
        ("L", ["BTS 4 000 A ≈ 40 m"], {"h": 30, "bts": True, "c": GEN_C}),
    ], c=GEN_C, lx=12, minh=9)
    line(ax, [(XG, y), (XG, YM + 13)], c=GEN_C)
    breaker(ax, XG, YM + 1, c=GEN_C, withdrawable=True)
    line(ax, [(XG, YM + 1), (XG, YM)], c=GEN_C)
    lines_text(ax, XG + 5, YM + 10.5, ["Q-GI ACB 4 000 A", "Isd ≤ 2.5 × Ir"], c=GEN_C)
    # ATS interlock (open transition)
    yq = cen["qui"]
    interlock(ax, [(XT + 2.6, yq), (XG - 2.6, yq)])
    text(ax, 110, yq + 2.0, "IL-3 ATS: Q-UI / Q-GI open transition only", c=CTL_C, va="bottom")
    # --- MSB-A busbar
    bus(ax, 24, 406, YM, c=LV_C)
    text(ax, 110, YM + 1.5, "MSB-A", fs=FS_TAG, weight="bold", va="bottom")
    text(ax, 132, YM + 1.5, "4 000 A · Icw 65 kA 1 s · Ipk ≥ 143 kA", va="bottom")
    text(ax, 236, YM - 2.0, "I″k 52.3 kA / ip 122 kA", va="top")
    # arc protection
    for x in (90, 205, 330, 395):
        arc_sensor(ax, x, YM + 3.0)
    rb = relay(ax, 404, 214, ["50ARC light + I", "trip Q-UI, Q-GI", "intertrip S1-Q1A"], tag="R-ARC", ha="right")
    ctl(ax, [(rb[0] + 10, rb[1]), (rb[0] + 10, YM + 8), (395, YM + 8), (395, YM + 5.5)])
    # outgoing feeders
    feeder(ax, 40, "Q-R1", "2 000 A", ["UPS-A1", "rectifier", "(sh 2)"])
    feeder(ax, 80, "Q-R2", "2 000 A", ["UPS-A2", "rectifier", "(sh 2)"])
    feeder(ax, 120, "Q-SB", "3 200 A", ["BTS 3 200 A", "≈ 25 m", "→ SBS-A (sh 2)"])
    feeder(ax, 168, "Q-MB", "3 200 A", ["MBB-A", "(sh 2)"])
    feeder(ax, 206, "Q-LB", "2 500 A", ["load-bank", "connection"])
    feeder(ax, 330, "Q-AUX", "250 A", ["block aux.", "lighting, BMS"])
    # SPD type 1+2 on the busbar
    line(ax, [(372, YM), (372, YM - 4)], c=LV_C)
    fuse(ax, 372, YM - 10, h=6, c=LV_C)
    line(ax, [(372, YM - 10), (372, YM - 12)], c=LV_C)
    arrester(ax, 372, YM - 12, side=1, dx=0.0, c=LV_C)
    text(ax, 376, YM - 9.0, "SPD T1+2", c=LV_C)
    # trip settings table
    rows = [["Device", "Ir", "tr", "Isd", "tsd", "Other"],
            ["Q-UI incomer", "3 600 A", "3 s", "4 × Ir", "0.3 s", "ZSI, ARMS"],
            ["Q-SB (SBS)", "2 900 A", "1 s", "2.5 × Ir", "0.2 s", "ZSI"],
            ["Q-GI genset", "4 000 A", "12 s", "2.5 × Ir", "0.4 s", "—"],
            ["Busway MCCB", "800 A", "—", "4 × Ir", "0.1 s", "Ii 12 × Ir"]]
    table(ax, 24, 104, rows, title="LV TRIP SETTINGS (CALC-003)")
    notes = ["NOTES",
             "1. ATS: break-before-make, no closed transition",
             "    (closed: 81.8 kA / ip 187 kA > MSB rating).",
             "2. ZSI Q-UI ↔ outgoing ACBs; ARMS on Q-UI.",
             "3. Arc energy MSB line side 96 → 3.2 cal/cm²,",
             "    bus 16.8 → 2.4–4.8 cal/cm² (IEEE 1584).",
             "4. Ratings are [ASSUMED] concept values."]
    lines_text(ax, 260, 112.0, notes, first_bold=True)
    save(fig, outdir, STEM)


if __name__ == "__main__":
    draw(os.path.join(os.path.dirname(__file__), "..", "drawings"))
