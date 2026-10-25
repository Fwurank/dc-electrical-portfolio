"""DWU-DC-E-SLD-000: symbol legend, drawing list, abbreviations and general notes for the SLD set."""
from sld_lib import *
from matplotlib.patches import Circle

STEM = "SLD-000_legend_notes"
ROW = 12.0


def sym(ax, kind, x, y):
    """Draw legend symbol `kind` centred around (x, y) (vertical conductor from y+5 to y-5)."""
    c = INK
    if kind in ("CB", "CBW", "DS", "SWD"):
        line(ax, [(x, y + 5), (x, y + 4)], c=c); line(ax, [(x, y - 4), (x, y - 5)], c=c)
        f = {"CB": breaker, "CBW": breaker, "DS": disconnector, "SWD": switch_disconnector}[kind]
        f(ax, x, y - 5, c=c, **({"withdrawable": True} if kind == "CBW" else {}))
    elif kind == "FU":
        line(ax, [(x, y + 5), (x, y - 5)], c=c); fuse(ax, x, y - 3, h=6, c=c)
    elif kind == "ES":
        line(ax, [(x, y + 5), (x, y - 5)], c=c); earthing_switch(ax, x, y + 4, side=1, c=c)
    elif kind == "CT":
        line(ax, [(x, y + 5), (x, y - 5)], c=c); ct(ax, x, y - 1.3, cores=2, c=c)
    elif kind == "VT":
        line(ax, [(x, y + 5), (x, y - 5)], c=c); vt(ax, x, y + 4.5, side=1, c=c, fused=False)
    elif kind == "SA":
        line(ax, [(x, y + 5), (x, y - 5)], c=c); arrester(ax, x, y + 3, side=1, c=c)
    elif kind == "TX":
        transformer(ax, x, y + 7.8, c1=MV_C, c2=LV_C)
    elif kind == "G":
        generator(ax, x, y + 6)
    elif kind == "UPS":
        ax.add_patch(Circle((x, y), 0.01, alpha=0))
        ups(ax, x, y + 6, side=1) if False else (converter(ax, x, y + 4.5, "ac/dc", c=UPS_C), converter(ax, x + 11, y + 4.5, "dc/ac", c=UPS_C))
    elif kind == "SBS":
        static_switch(ax, x, y + 4.5)
    elif kind == "BAT":
        battery(ax, x, y + 4)
    elif kind == "L":
        inductor_adj(ax, x, y + 5, h=10)
    elif kind == "R":
        line(ax, [(x, y + 5), (x, y - 5)], c=c); resistor(ax, x, y + 4, h=8)
    elif kind == "BUS":
        line(ax, [(x - 6, y), (x + 6, y)], lw=BUS_LW)
    elif kind == "BTS":
        bts(ax, x, y + 5, x, y - 5)
    elif kind == "WH":
        meter(ax, x, y)
    elif kind == "ARC":
        arc_sensor(ax, x, y)
    elif kind == "IL":
        interlock(ax, [(x - 6, y), (x + 6, y)])
    elif kind == "CTL":
        ctl(ax, [(x - 6, y), (x + 6, y)])
    elif kind == "OFF":
        arrow_down(ax, x, y + 3, l=6)
    elif kind == "E":
        line(ax, [(x, y + 4), (x, y)]); earth(ax, x, y)
    elif kind == "REL":
        box(ax, x - 6, y - 3.5, 12, 7, c=CTL_C)
        text(ax, x, y, "51", ha="center", c=CTL_C)


LEGEND = [
    ("CB", "Circuit breaker"), ("CBW", "Circuit breaker, withdrawable"), ("DS", "Disconnector"),
    ("SWD", "Switch-disconnector"), ("FU", "Fuse"), ("ES", "Earthing switch"), ("CT", "Current transformer (2 cores)"),
    ("VT", "Voltage transformer"), ("SA", "Surge arrester / SPD"), ("BUS", "Busbar (weight per level)"), ("TX", "Transformer, 2 windings"),
    ("E", "Earth"), ("G", "Generator, 3-phase"),
    ("UPS", "Rectifier (ac/dc), inverter (dc/ac)"), ("SBS", "Static bypass switch"), ("BAT", "Battery"),
    ("L", "Adjustable inductor (Petersen coil)"), ("R", "Resistor"), ("BTS", "Busbar trunking / busway"),
    ("WH", "Energy meter (Wh)"), ("REL", "Protection relay, device no."), ("ARC", "Optical arc sensor"),
    ("IL", "Interlock (mechanical / key)"), ("CTL", "Protection / control signal"), ("OFF", "Off-sheet connector"),
]


def draw(outdir):
    fig, ax = new_sheet()
    frame_and_title(ax, "DWU-DC-E-SLD-000", "Legend, drawing list, notes",
                    "Symbols to IEC 60617 · lettering to ISO 3098", 1, 1)
    text(ax, 24, 280.0, "SYMBOL LEGEND (IEC 60617 forms)", fs=FS_TAG, weight="bold")
    for i, (k, d) in enumerate(LEGEND):
        col, row = divmod(i, 13)
        x0, y = 24 + col * 104, 268 - row * ROW
        sym(ax, k, x0 + 9 + (0 if k != "UPS" else -2), y)
        text(ax, x0 + 26, y, d)
    # line code (monochrome drawings: line weight / style instead of colour)
    yc = 104.0
    text(ax, 24, yc + 6, "LINE CODE (black on white; no colour code)", fs=FS_TAG, weight="bold")
    keys = [("130 kV conductor", dict(lw=COND_LW["hv"])), ("20 kV conductor", dict(lw=COND_LW["mv"])),
            ("0.4 / 0.69 kV conductor", dict(lw=COND_LW["lv"])),
            ("130 kV busbar", dict(lw=BUS_W["hv"])), ("20 kV busbar", dict(lw=BUS_W["mv"])),
            ("0.4 / 0.69 kV busbar", dict(lw=BUS_W["lv"])),
            ("UPS / critical busbar", dict(lw=UPS_BUS_W, core=True)),
            ("protection / control", dict(lw=THIN, ls=(0, (3, 1.5)))),
            ("interlock", dict(lw=THIN, ls=(0, (5, 1.5, 1, 1.5))))]
    for i, (d, k) in enumerate(keys):
        x = 24 + (i % 3) * 66; y = yc - 1 - (i // 3) * 6.5
        ax.plot([x, x + 12], [y, y], color="black", lw=k["lw"], ls=k.get("ls", "-"), solid_capstyle="butt", gid="keep", zorder=3)
        if k.get("core"):
            ax.plot([x, x + 12], [y, y], color="white", lw=UPS_BUS_CORE, solid_capstyle="butt", gid="keep", zorder=3.1)
        text(ax, x + 15, y, d)
    text(ax, 24, yc - 21.5, "Voltage level is also stated on every busbar tag; genset and BESS circuits use the LV weight.")
    rows = [["Drawing / sheet", "Title"],
            ["SLD-000", "Legend, drawing list, notes"],
            ["SLD-001 sh 1", "130/20 kV substation"],
            ["SLD-001 sh 2", "20 kV main switchgear MSG-20"],
            ["SLD-002 sh 1", "Data hall DH-1: HV-DH1, blocks"],
            ["SLD-002 sh 2", "DH-1: UPS, busways, mechanical"],
            ["SLD-003 sh 1", "Power block A: T-A, G-A, MSB-A"],
            ["SLD-003 sh 2", "Power block A: UPS to rack"],
            ["SLD-004", "BESS plant 10 MW / 20 MWh"]]
    table(ax, 232, 274, rows, title="DRAWING LIST (Rev P2)")
    abbr = ["ABBREVIATIONS",
            "ACB / VCB  air / vacuum circuit breaker",
            "ATS  automatic transfer (open transition)",
            "ARMS  arc-reduction maintenance switch",
            "BTS  busbar trunking system",
            "MSB / UOSB  main / UPS output switchboard",
            "SBS / MBB  static / maintenance bypass",
            "PCS / EMS  power conversion / energy mgmt",
            "ZSI  zone-selective interlocking",
            "LoM  loss of mains (ROCOF / vector shift)",
            "(A)  assumed value"]
    lines_text(ax, 232, 212.0, abbr, first_bold=True)
    notes = ["GENERAL NOTES",
             "1. Concept drawings for a fictional campus; not for",
             "    construction. Public standards, [ASSUMED] data.",
             "2. Ratings per DB-001 Rev P2 and CALC-002/003/004.",
             "3. Relay functions: IEEE C37.2 device numbers.",
             "4. Minimum text 10 pt = 2.57 mm cap height at A3",
             "    (checked by scripts/check_drawings.py)."]
    lines_text(ax, 232, 152.0, notes, first_bold=True)
    # the one UPS compound symbol used on every sheet
    text(ax, 24, 72.0, "UPS COMPOUND SYMBOL (all sheets)", fs=FS_TAG, weight="bold")
    line(ax, [(40, 66), (40, 62)], c=UPS_C)
    yb = ups(ax, 40, 62, side=1)
    line(ax, [(40, yb), (40, yb - 4)], c=UPS_C)
    lines_text(ax, 58, 60.0, ["rectifier ac/dc (top), inverter dc/ac (bottom),", "DC link with battery to the side;",
                              "drawn the same for IT UPS and mechanical UPS."])
    save(fig, outdir, STEM)


if __name__ == "__main__":
    draw(os.path.join(os.path.dirname(__file__), "..", "drawings"))
