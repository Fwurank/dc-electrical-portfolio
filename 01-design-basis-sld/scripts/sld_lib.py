"""IEC 60617-style single-line-diagram primitives on matplotlib, Rev P2.

Units: 1 drawing unit = 1 mm on an A3 landscape sheet (420 x 297 mm). The axes fill the figure exactly,
so a font size in pt maps 1:1 to printed size at A3.
Lettering (ISO 3098): the minimum font is FS_MIN = 10 pt. DejaVu Sans cap height is 0.729 em, so the
capital height is 10 x 0.3528 x 0.729 = 2.57 mm, which is >= 2.5 mm.
Busbar/equipment tags use FS_TAG = 14 pt (3.6 mm), and the drawing number uses FS_DWG = 14 pt (3.6 mm).
scripts/check_drawings.py verifies these values on the exported SVG files.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, Arc
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

A3_W, A3_H = 420.0, 297.0
PT_MM = 25.4 / 72.0
CAP = 0.729                      # DejaVu Sans cap height / em
FS_MIN = 10.0                    # -> 2.57 mm caps
FS_TAG = 14.0                    # -> 3.60 mm caps (busbar / equipment tags)
FS_TITLE = 16.0
FS_DWG = 14.0                    # -> 3.60 mm caps (drawing number, title block)
LW, BUS_LW, THIN = 0.8, 3.0, 0.5
# Output is pure black (see monochrome()); the other values are only voltage-level tokens.
INK, HV_C, MV_C, LV_C, UPS_C, GEN_C, CTL_C = "#000000", "#7a1f1f", "#1f3b73", "#111111", "#0b6e4f", "#8a5a00", "#5a2a82"  # noqa: tokens
REV, DATE = "P2", "2026-10-25"
LINE_H = FS_MIN * PT_MM * 1.30   # 4.6 mm line pitch for 10 pt text
R_TX = 6.0                       # one transformer circle radius for every transformer (P1 weakness fixed)

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "pdf.fonttype": 42})
_FP = {w: FontProperties(family="DejaVu Sans", weight=w) for w in ("normal", "bold")}


def tw(s, fs=FS_MIN, weight="normal"):
    """Text width in mm (longest line)."""
    return max(TextPath((0, 0), ln or " ", size=fs, prop=_FP[weight]).get_extents().width for ln in s.split("\n")) * PT_MM


def new_sheet():
    fig = plt.figure(figsize=(A3_W / 25.4, A3_H / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, A3_W); ax.set_ylim(0, A3_H); ax.set_aspect("equal"); ax.axis("off")
    return fig, ax


def line(ax, pts, c=INK, lw=LW, ls="-", z=2):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=c, lw=lw, ls=ls, solid_capstyle="butt", zorder=z)


def text(ax, x, y, s, fs=FS_MIN, ha="left", va="center", rot=0, c=INK, weight="normal", style="normal", z=6):
    assert fs >= FS_MIN, f"font {fs} pt below minimum for {s!r}"
    return ax.text(x, y, s, fontsize=fs, ha=ha, va=va, rotation=rot, color=c, fontweight=weight,
                   fontstyle=style, zorder=z, linespacing=1.25)


def lines_text(ax, x, y_top, lines, fs=FS_MIN, c=INK, ha="left", first_bold=False, fs0=None):
    """Stack of text lines from y_top downwards; fs0 = optional larger size of the first line (tag)."""
    y = y_top
    for i, s in enumerate(lines):
        f = fs0 if (fs0 and i == 0) else fs
        lh = f * PT_MM * 1.30
        text(ax, x, y - lh / 2, s, fs=f, c=c, ha=ha, weight="bold" if (first_bold and i == 0) else "normal")
        y -= lh
    return y


def block_h(lines, fs0=None):
    return LINE_H * len(lines) + ((fs0 - FS_MIN) * PT_MM * 1.30 if fs0 else 0)


def bus(ax, x1, x2, y, c=INK, label=None, sub=None, lw=BUS_LW, at="left"):
    line(ax, [(x1, y), (x2, y)], c=c, lw=lw, z=3)
    if label:
        xx, ha = (x1, "left") if at == "left" else (x2, "right")
        text(ax, xx, y + 4.2, label, fs=FS_TAG, ha=ha, va="bottom", weight="bold", c=c)
        if sub:
            text(ax, xx, y + 1.6, sub, ha=ha, va="bottom", c=c)


def dot(ax, x, y, r=0.8, c=INK):
    ax.add_patch(Circle((x, y), r, color=c, zorder=4))


def earth(ax, x, y, c=INK):
    """IEC 60617 02-15-01 earth; (x, y) is the connection point, symbol hangs below."""
    line(ax, [(x, y), (x, y - 2.0)], c=c)
    for i, w in enumerate((3.2, 2.1, 1.0)):
        line(ax, [(x - w / 2, y - 2.0 - i * 0.9), (x + w / 2, y - 2.0 - i * 0.9)], c=c)


# ---------------------------------------------------------------- switching devices (vertical, bottom -> top)
SW_H = 10.0   # height of a switching-device symbol


def _contact(ax, x, y, closed, c, h=SW_H):
    """Lead-in 2 mm, blade from pivot (x, y+2) to near the fixed contact at (x, y+h-2)."""
    line(ax, [(x, y), (x, y + 2)], c=c)
    line(ax, [(x, y + h - 2), (x, y + h)], c=c)
    tip = (x - 1.6, y + h - 2.4) if closed else (x - 4.2, y + h - 3.4)
    line(ax, [(x, y + 2), tip], c=c, lw=LW + 0.2)
    return y + h - 2


def breaker(ax, x, y, closed=True, c=INK, withdrawable=False):
    """IEC 60617 07-13-05 circuit breaker: switch with a cross at the fixed contact."""
    yc = _contact(ax, x, y, closed, c)
    d = 1.1
    line(ax, [(x - d, yc - d), (x + d, yc + d)], c=c); line(ax, [(x - d, yc + d), (x + d, yc - d)], c=c)
    if withdrawable:
        for yy, s in ((y - 1.4, 1), (y + SW_H + 0.2, 1)):
            line(ax, [(x - 1.4, yy + s * 1.2), (x, yy), (x + 1.4, yy + s * 1.2)], c=c, lw=THIN)
    return y + SW_H


def disconnector(ax, x, y, closed=True, c=INK):
    """IEC 60617 07-13-06 disconnector: switch with a bar at the fixed contact."""
    yc = _contact(ax, x, y, closed, c)
    line(ax, [(x - 1.3, yc), (x + 1.3, yc)], c=c, lw=LW + 0.2)
    return y + SW_H


def switch_disconnector(ax, x, y, closed=True, c=INK):
    yc = _contact(ax, x, y, closed, c)
    line(ax, [(x - 1.3, yc), (x + 1.3, yc)], c=c, lw=LW + 0.2)
    ax.add_patch(Circle((x, yc), 0.7, fill=False, ec=c, lw=THIN, zorder=4))
    return y + SW_H


def fuse(ax, x, y, h=6.0, c=INK):
    ax.add_patch(Rectangle((x - 1.2, y + 1), 2.4, h - 2, fill=False, ec=c, lw=LW, zorder=3))
    line(ax, [(x, y), (x, y + h)], c=c)
    return y + h


def earthing_switch(ax, x, y, side=-1, c=INK, closed=False):
    """IEC 60617 07-13-06 + 02-15-01: earthing switch tapped off the conductor at (x, y); drawn to one side."""
    xe = x + side * 6.0
    dot(ax, x, y, c=c)
    line(ax, [(x, y), (xe, y)], c=c)
    line(ax, [(xe, y), (xe, y - 1.2)], c=c)
    line(ax, [(xe - 1.1, y - 1.2), (xe + 1.1, y - 1.2)], c=c, lw=LW + 0.2)  # fixed contact bar
    tip = (xe, y - 1.6) if closed else (xe + side * 2.6, y - 2.4)
    line(ax, [(xe, y - 5.0), tip], c=c, lw=LW + 0.2)
    earth(ax, xe, y - 5.0, c=c)


# ---------------------------------------------------------------- instrument transformers, arresters, meters
def ct(ax, x, y, cores=1, c=INK):
    """IEC 60617 06-09-11 current transformer: one ring per core on the conductor; returns (y_bottom, y_top)."""
    for i in range(cores):
        ax.add_patch(Circle((x, y + i * 2.6), 1.8, fill=False, ec=c, lw=LW, zorder=4))
    return y - 1.8, y + (cores - 1) * 2.6 + 1.8


def vt(ax, x, y, side=-1, c=INK, fused=True, dx=7.0):
    """Voltage transformer tapped from conductor/bus at (x, y): fuse + two interlinked circles + earth."""
    xe = x + side * dx
    dot(ax, x, y, c=c)
    line(ax, [(x, y), (xe, y)], c=c)
    if fused:
        line(ax, [(xe, y), (xe, y - 1.0)], c=c)
        fuse(ax, xe, y - 6.0, h=5.0, c=c)
        ytop = y - 6.0
    else:
        ytop = y
    line(ax, [(xe, ytop), (xe, ytop - 1.0)], c=c)
    ax.add_patch(Circle((xe, ytop - 2.8), 1.8, fill=False, ec=c, lw=LW, zorder=4))
    ax.add_patch(Circle((xe, ytop - 5.0), 1.8, fill=False, ec=c, lw=LW, zorder=4))
    earth(ax, xe, ytop - 6.8, c=c)
    return xe


def arrester(ax, x, y, side=-1, c=INK, dx=6.0):
    """IEC 60617 07-22-03 surge arrester tapped at (x, y): rectangle with arrow, to earth."""
    xe = x + side * dx
    dot(ax, x, y, c=c)
    line(ax, [(x, y), (xe, y)], c=c)
    line(ax, [(xe, y), (xe, y - 1.0)], c=c)
    ax.add_patch(Rectangle((xe - 1.3, y - 6.0), 2.6, 5.0, fill=False, ec=c, lw=LW, zorder=4))
    line(ax, [(xe, y - 1.6), (xe, y - 5.0)], c=c, lw=THIN)
    ax.add_patch(Polygon([(xe - 0.8, y - 4.0), (xe + 0.8, y - 4.0), (xe, y - 5.4)], closed=True, color=c, zorder=5))
    earth(ax, xe, y - 6.0, c=c)
    return xe


def meter(ax, x, y, label="Wh", c=CTL_C):
    """IEC 60617 08-04-03 integrating meter (watt-hour): square, bar on top, label inside. (x, y) = centre."""
    s = 4.5
    ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, fill=False, ec=c, lw=LW, zorder=4))
    line(ax, [(x - s, y + s - 1.4), (x + s, y + s - 1.4)], c=c, lw=THIN)
    text(ax, x, y - 0.8, label, ha="center", c=c)


def relay(ax, x, y, lines, c=CTL_C, ha="left", tag=None):
    """Protection relay box with IEEE C37.2 / IEC device numbers. (x, y) = left (or right) middle. Returns bbox."""
    rows = ([tag] if tag else []) + list(lines)
    w = max(tw(r, weight="bold" if (tag and i == 0) else "normal") for i, r in enumerate(rows)) * 1.04 + 4.0
    h = len(rows) * LINE_H + 1.6
    x0 = x if ha == "left" else x - w
    ax.add_patch(Rectangle((x0, y - h / 2), w, h, fill=False, ec=c, lw=LW, zorder=4))
    lines_text(ax, x0 + 2.0, y + h / 2 - 0.8, rows, c=c, first_bold=bool(tag))
    return (x0, y - h / 2, x0 + w, y + h / 2)


def ctl(ax, pts, c=CTL_C):
    """Secondary / control connection (dashed)."""
    line(ax, pts, c=c, lw=THIN, ls=(0, (3, 1.5)), z=2)


def arc_sensor(ax, x, y, c=CTL_C):
    """Optical arc-flash sensor marker (point sensor): small circle with three rays."""
    ax.add_patch(Circle((x, y), 1.1, fill=False, ec=c, lw=THIN, zorder=5))
    for dx, dy in ((-1.6, 1.6), (0, 2.2), (1.6, 1.6)):
        line(ax, [(x + dx * 0.7, y + dy * 0.7), (x + dx * 1.4, y + dy * 1.4)], c=c, lw=THIN)


# ---------------------------------------------------------------- machines and converters
def transformer(ax, x, y_top, c1=INK, c2=INK, r=R_TX):
    """IEC 60617 06-09-01 two-winding transformer, vertical; returns y_bottom."""
    ax.add_patch(Circle((x, y_top - r), r, fill=False, ec=c1, lw=LW + 0.1, zorder=4))
    ax.add_patch(Circle((x, y_top - 2.6 * r + r), r, fill=False, ec=c2, lw=LW + 0.1, zorder=4))
    return y_top - 2.6 * r


def generator(ax, x, y_top, c=GEN_C, r=6.0):
    ax.add_patch(Circle((x, y_top - r), r, fill=False, ec=c, lw=LW + 0.1, zorder=4))
    text(ax, x, y_top - r + 2.1, "G", ha="center", c=c, weight="bold")
    text(ax, x, y_top - r - 2.4, "3~", ha="center", c=c)
    return y_top - 2 * r


def converter(ax, x, y_top, kind="ac/dc", s=9.0, c=INK):
    """IEC 60617 06-14-xx converter: square with diagonal; returns y_bottom."""
    x0, y0 = x - s / 2, y_top - s
    ax.add_patch(Rectangle((x0, y0), s, s, fill=False, ec=c, lw=LW, zorder=4))
    line(ax, [(x0, y0), (x0 + s, y0 + s)], c=c, lw=THIN)
    a, b = kind.split("/")
    for sym, (px, py) in ((a, (x0 + 2.4, y0 + s - 2.7)), (b, (x0 + s - 2.4, y0 + 2.4))):
        if sym == "ac":   # tilde drawn as a sine stroke
            import numpy as np
            t = np.linspace(0, 2 * np.pi, 20)
            line(ax, list(zip(px - 1.6 + t / (2 * np.pi) * 3.2, py + 0.7 * np.sin(t))), c=c, lw=THIN)
        else:             # '=' as two strokes (DC)
            line(ax, [(px - 1.6, py + 0.5), (px + 1.6, py + 0.5)], c=c, lw=THIN)
            line(ax, [(px - 1.6, py - 0.5), (px + 1.6, py - 0.5)], c=c, lw=THIN, ls=(0, (1, 0.6)))
    return y0


def battery(ax, x, y_top, c=INK, n=2):
    """IEC 60617 06-15-01 battery (cells); returns y_bottom."""
    y = y_top
    line(ax, [(x, y), (x, y - 1.5)], c=c); y -= 1.5
    for _ in range(n):
        line(ax, [(x - 3.0, y), (x + 3.0, y)], c=c, lw=LW + 0.2)
        line(ax, [(x - 1.6, y - 1.3), (x + 1.6, y - 1.3)], c=c, lw=LW + 1.2)
        y -= 2.6
    line(ax, [(x, y + 1.3), (x, y - 0.5)], c=c)
    return y - 0.5


def ups(ax, x, y_top, c=UPS_C, batt=True, side=1):
    """Consistent UPS compound symbol used on every sheet: rectifier (ac/dc) over inverter (dc/ac),
    DC link with battery to one side. Returns y_bottom. Height 25 mm."""
    yb = converter(ax, x, y_top, "ac/dc", c=c)
    line(ax, [(x, yb), (x, yb - 3.0)], c=c)
    if batt:
        xb = x + side * 9.0
        dot(ax, x, yb - 1.5, c=c)
        line(ax, [(x, yb - 1.5), (xb, yb - 1.5)], c=c)
        battery(ax, xb, yb - 1.5, c=c)
    return converter(ax, x, yb - 3.0, "dc/ac", c=c) - 0.0


def static_switch(ax, x, y_top, c=UPS_C, w=9.0, h=9.0):
    """Static bypass switch: box with antiparallel thyristors (two triangles with gate stubs)."""
    x0, y0 = x - w / 2, y_top - h
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=c, lw=LW, zorder=4))
    for xx, s in ((x - 1.8, 1), (x + 1.8, -1)):
        yc = y0 + h / 2
        ax.add_patch(Polygon([(xx - 1.4, yc + s * 1.3), (xx + 1.4, yc + s * 1.3), (xx, yc - s * 1.3)],
                             closed=True, fill=False, ec=c, lw=THIN, zorder=5))
        line(ax, [(xx - 1.4, yc - s * 1.3), (xx + 1.4, yc - s * 1.3)], c=c, lw=THIN)
    return y0


def inductor_adj(ax, x, y_top, h=10.0, c=INK):
    """Adjustable inductor (Petersen coil): 4 half-loops + diagonal arrow; vertical; returns y_bottom."""
    n = 4; seg = h / n
    for i in range(n):
        ax.add_patch(Arc((x, y_top - seg / 2 - i * seg), 3.2, seg, theta1=-90, theta2=90, ec=c, lw=LW, zorder=4))
    line(ax, [(x - 3.0, y_top - h + 1), (x + 4.2, y_top - 1)], c=c, lw=THIN)
    ax.add_patch(Polygon([(x + 4.2, y_top - 1), (x + 2.9, y_top - 1.4), (x + 3.7, y_top - 2.4)], closed=True, color=c, zorder=5))
    return y_top - h


def resistor(ax, x, y_top, h=8.0, c=INK):
    ax.add_patch(Rectangle((x - 1.4, y_top - h), 2.8, h, fill=False, ec=c, lw=LW, zorder=4))
    return y_top - h


def bts(ax, x1, y1, x2, y2, c=INK):
    """Busbar trunking system drawn as a double line (offset 1.0 mm)."""
    import numpy as np
    d = np.array([x2 - x1, y2 - y1], float); n = np.array([-d[1], d[0]]) / (np.hypot(*d) or 1) * 0.9
    for s in (1, -1):
        line(ax, [(x1 + s * n[0], y1 + s * n[1]), (x2 + s * n[0], y2 + s * n[1])], c=c, lw=LW)


def arrow_down(ax, x, y, c=INK, l=4.0):
    line(ax, [(x, y), (x, y - l + 1.6)], c=c)
    ax.add_patch(Polygon([(x - 1.3, y - l + 1.8), (x + 1.3, y - l + 1.8), (x, y - l)], closed=True, color=c, zorder=4))


def offpage(ax, x, y, label, direction="down", c=INK, ha="center"):
    """Off-sheet connector arrow with a reference label (sheet/zone)."""
    if direction == "down":
        arrow_down(ax, x, y, c=c)
        text(ax, x, y - 6.2, label, ha=ha, va="top", c=c)
    else:   # incoming from top: label above, arrow pointing down onto the conductor
        text(ax, x, y + 6.0, label, ha=ha, va="bottom", c=c)
        arrow_down(ax, x, y + 5.0, c=c, l=5.0)


def box(ax, x, y, w, h, c=INK, lw=LW, ls="-", fill=None, z=1):
    ax.add_patch(Rectangle((x, y), w, h, fill=fill is not None, fc=fill or "none", ec=c, lw=lw, ls=ls, zorder=z))


def interlock(ax, pts, label=None, c=CTL_C, lpos=None, ha="left"):
    """Mechanical / electrical interlock: dash-dot line, optional label."""
    line(ax, pts, c=c, lw=THIN, ls=(0, (5, 1.5, 1, 1.5)), z=2)
    if label:
        lx, ly = lpos or pts[-1]
        text(ax, lx, ly, label, c=c, ha=ha)


def table(ax, x, y_top, rows, widths=None, header=True, pad=1.4, c=INK, title=None):
    """Simple table; each cell is 10 pt text (can contain \n). Returns (x2, y_bottom)."""
    ncol = len(rows[0])
    if widths is None:
        widths = [max(tw(str(r[j]), weight="bold" if (header and i == 0) else "normal") for i, r in enumerate(rows)) * 1.04 + 2 * pad + 0.6
                  for j in range(ncol)]
    y = y_top
    if title:
        text(ax, x, y + 1.2, title, fs=FS_MIN + 1, weight="bold", va="bottom", c=c)
    for i, r in enumerate(rows):
        nl = max(str(cell).count("\n") + 1 for cell in r)
        h = nl * LINE_H + 1.0
        xx = x
        for j, cell in enumerate(r):
            box(ax, xx, y - h, widths[j], h, c=c, lw=THIN, fill=None)
            lines_text(ax, xx + pad, y - 0.5, str(cell).split("\n"), first_bold=False)
            if header and i == 0:
                ax.texts[-1].set_fontweight("bold")
            xx += widths[j]
        y -= h
    return x + sum(widths), y


# ---------------------------------------------------------------- frame and title block (ISO 5457 / ISO 7200 style)
def frame_and_title(ax, dwg_no, title, subtitle, sheet, sheets, revs=None):
    box(ax, 20, 10, 390, 277, lw=1.4)                    # ISO 5457: 20 mm filing margin left, 10 mm others
    for i in range(8):                                    # grid reference zones (columns 1..8, rows A..F)
        xm = 20 + (i + 0.5) * 390 / 8
        text(ax, xm, 290.5, str(i + 1), ha="center"); text(ax, xm, 6.2, str(i + 1), ha="center")
    for j, L in enumerate("FEDCBA"):
        ym = 10 + (j + 0.5) * 277 / 6
        text(ax, 15, ym, L, ha="center"); text(ax, 414.5, ym, L, ha="center")
    # Title block: ONE uniform 180 mm wide rectangle anchored in the bottom-right corner of the frame.
    # Rows bottom -> top, all full width: Drawing no. / Sheet / Rev; title, subtitle, status;
    # project lines; revision table. Every text is FS_MIN (10 pt, 2.57 mm caps) except the drawing
    # number (FS_DWG = 14 pt, 3.6 mm caps).
    x0, y0, w = 230, 10, 180
    line(ax, [(x0 + 118, y0), (x0 + 118, y0 + 12)], lw=THIN)
    line(ax, [(x0 + 148, y0), (x0 + 148, y0 + 12)], lw=THIN)
    text(ax, x0 + 2, y0 + 9.0, "Drawing no.")
    text(ax, x0 + 2, y0 + 3.8, dwg_no, fs=FS_DWG, weight="bold")
    text(ax, x0 + 120, y0 + 9.0, "Sheet"); text(ax, x0 + 120, y0 + 3.8, f"{sheet} / {sheets}", weight="bold")
    text(ax, x0 + 150, y0 + 9.0, "Rev"); text(ax, x0 + 150, y0 + 3.8, REV, weight="bold")
    for yy in (12, 27, 38):
        line(ax, [(x0, y0 + yy), (x0 + w, y0 + yy)], lw=THIN, z=1.5)
    text(ax, x0 + 2, y0 + 23.6, title, weight="bold")
    text(ax, x0 + 2, y0 + 19.0, subtitle)
    text(ax, x0 + 2, y0 + 14.4, "CONCEPT · NOT FOR CONSTRUCTION · scale NTS · A3")
    text(ax, x0 + 2, y0 + 34.8, "Nordic Hyperscale DC Campus (fictional) · 30 MW IT · SE3", weight="bold")
    text(ax, x0 + 2, y0 + 30.2, "Portfolio D. Wu · public standards and [ASSUMED] data only")
    revs = revs or [("P1", "2026-10-24", "First concept issue"), (REV, DATE, "CALC-002/3/4 ratings, IEC symbols, ≥2.5 mm text")]
    yr = y0 + 38
    for i, (rv, d, desc) in enumerate(revs):
        if i:
            line(ax, [(x0, yr), (x0 + w, yr)], lw=THIN, z=1.5)
        text(ax, x0 + 2, yr + (LINE_H + 1) / 2, rv, weight="bold")
        text(ax, x0 + 13, yr + (LINE_H + 1) / 2, d)
        text(ax, x0 + 37, yr + (LINE_H + 1) / 2, desc)
        yr += LINE_H + 1
    box(ax, x0, y0, w, yr - y0, lw=1.2, fill="white", z=1)              # single uniform outline
    return yr   # top of the revision block


# ---------------------------------------------------------------- monochrome output (Rev P2)
# The sheet scripts still tag conductors with a voltage-level token (HV_C, MV_C, ...). Before export every
# artist is forced to pure black on white and the token is turned into a line-weight code, so nothing
# depends on colour:
#   conductors: 130 kV 1.4 pt heavy, 20 kV 1.0, LV / UPS / genset / BESS 0.7
#   busbars:    130 kV 4.2, 20 kV 3.2, LV 2.6, UPS / critical bus hollow (3.0 outline, white core)
#   protection / control signals thin dashed, interlocks thin dash-dot (unchanged line styles)
COND_LW = {"hv": 1.4, "mv": 1.0, "lv": 0.7}
BUS_W = {"hv": 4.2, "mv": 3.2, "lv": 2.6}
UPS_BUS_W, UPS_BUS_CORE = 3.0, 1.2
from matplotlib.colors import to_hex as _hex
_LEVEL = {_hex(HV_C): "hv", _hex(MV_C): "mv", _hex(UPS_C): "ups"}


def _bw(col):
    """Pure white stays white, transparent stays transparent, everything else becomes pure black."""
    from matplotlib.colors import to_rgba
    if isinstance(col, str) and col.lower() == "none":
        return col
    r, g, b, a = to_rgba(col)
    if a == 0:
        return col
    return (1, 1, 1, a) if min(r, g, b) > 0.97 else (0, 0, 0, a)


def monochrome(fig):
    from matplotlib.lines import Line2D
    for ax in fig.axes:
        for ln in list(ax.lines):
            lvl = _LEVEL.get(_hex(ln.get_color()), "lv")
            white = _bw(ln.get_color())[0] == 1
            ln.set_color(_bw(ln.get_color()))
            if white or ln.get_gid() == "keep" or ln.get_linestyle() not in ("-", "solid"):
                continue
            lw = ln.get_linewidth()
            if abs(lw - BUS_LW) < 1e-6:                                 # busbar
                if lvl == "ups":
                    ln.set_linewidth(UPS_BUS_W)
                    core = Line2D(*ln.get_data(), color="white", lw=UPS_BUS_CORE, zorder=ln.get_zorder() + 0.01,
                                  solid_capstyle="butt")
                    ax.add_line(core)
                else:
                    ln.set_linewidth(BUS_W[lvl])
            elif LW - 0.05 <= lw <= LW + 0.25:                           # power conductor / blade
                ln.set_linewidth(COND_LW.get(lvl, COND_LW["lv"]) + (lw - LW))
        for p in ax.patches:
            p.set_edgecolor(_bw(p.get_edgecolor()))
            if p.get_fill():
                p.set_facecolor(_bw(p.get_facecolor()))
        for t in ax.texts:
            t.set_color("black")


def save(fig, outdir, stem):
    monochrome(fig)
    os.makedirs(outdir, exist_ok=True)
    for ext, kw in (("svg", {}), ("pdf", {}), ("png", {"dpi": 200})):
        fig.savefig(os.path.join(outdir, f"{stem}.{ext}"), **kw)
    plt.close(fig)


# ---------------------------------------------------------------- horizontal switching devices (left -> right)
def breaker_h(ax, x, y, closed=True, c=INK, no_label=False):
    """Horizontal circuit breaker from (x, y) to (x + SW_H, y)."""
    h = SW_H
    line(ax, [(x, y), (x + 2, y)], c=c); line(ax, [(x + h - 2, y), (x + h, y)], c=c)
    tip = (x + h - 2.4, y + 1.6) if closed else (x + h - 3.4, y + 4.2)
    line(ax, [(x + 2, y), tip], c=c, lw=LW + 0.2)
    d = 1.1; xc = x + h - 2
    line(ax, [(xc - d, y - d), (xc + d, y + d)], c=c); line(ax, [(xc - d, y + d), (xc + d, y - d)], c=c)
    return x + h


def disconnector_h(ax, x, y, closed=True, c=INK):
    h = SW_H
    line(ax, [(x, y), (x + 2, y)], c=c); line(ax, [(x + h - 2, y), (x + h, y)], c=c)
    tip = (x + h - 2.4, y + 1.6) if closed else (x + h - 3.4, y + 4.2)
    line(ax, [(x + 2, y), tip], c=c, lw=LW + 0.2)
    line(ax, [(x + h - 2, y - 1.3), (x + h - 2, y + 1.3)], c=c, lw=LW + 0.2)
    return x + h


# ---------------------------------------------------------------- vertical bay builder
_H = {"CB": SW_H + 2, "DS": SW_H + 2, "SWD": SW_H + 2, "FU": 8, "SA": 11, "ES": 9, "VT": 19, "VTU": 12,
      "TX": 2.6 * R_TX + 3, "G": 14, "UPS": 25, "SBS": 11, "CONV": 11, "BAT": 9}


MINH = 0.0


def chain(ax, x, y, items, c=INK, lx=7.0, cl=None, minh=None):
    """Draw a vertical bay from y downwards. items: list of (kind, label_lines, opts).
    kinds: CB, DS, SWD, FU, CT, SA, ES, VT, VTU, TX, G, UPS, SBS, CONV, BAT, L (plain line, opts['h']).
    Labels are placed at x + lx (or opts['lx']), vertically centred on the item. Returns (y_end, centres)."""
    cen = {}
    global MINH
    _old, MINH = MINH, (minh if minh is not None else MINH)
    for kind, lab, o in items:
        o = o or {}
        cc = o.get("c", c)
        if kind == "L":
            h = o.get("h", 6)
        elif kind == "CT":
            h = o.get("cores", 1) * 2.6 + 2.6
        else:
            h = _H[kind]
        h = max(h, o.get("minh", 0 if kind == "L" else MINH), (block_h(lab, o.get("fs0")) + 1.0) if (lab and kind not in ("VT", "VTU")) else 0)
        yb = y - h
        mid = y - h / 2
        if kind == "L":
            line(ax, [(x, y), (x, yb)], c=cc)
            if o.get("bts"):
                line(ax, [(x, y), (x, yb)], c="white", lw=LW + 0.6, z=2.5)
                bts(ax, x, y, x, yb, c=cc)
        elif kind in ("CB", "DS", "SWD"):
            y0 = mid - SW_H / 2
            line(ax, [(x, y), (x, y0 + SW_H)], c=cc); line(ax, [(x, y0), (x, yb)], c=cc)
            {"CB": breaker, "DS": disconnector, "SWD": switch_disconnector}[kind](
                ax, x, y0, closed=o.get("closed", True), c=cc, **({"withdrawable": o.get("wd", False)} if kind == "CB" else {}))
        elif kind == "FU":
            line(ax, [(x, y), (x, mid + 3)], c=cc); fuse(ax, x, mid - 3, c=cc); line(ax, [(x, mid - 3), (x, yb)], c=cc)
        elif kind == "CT":
            line(ax, [(x, y), (x, yb)], c=cc)
            n = o.get("cores", 1)
            ct(ax, x, mid - (n - 1) * 1.3, cores=n, c=cc)
        elif kind in ("SA", "ES", "VT", "VTU"):
            line(ax, [(x, y), (x, yb)], c=cc)
            side = o.get("side", -1)
            yt = y - 1.5
            if kind == "SA":
                xe = arrester(ax, x, yt, side=side, c=cc)
            elif kind == "ES":
                earthing_switch(ax, x, yt, side=side, c=cc, closed=o.get("closed", False))
                xe = x + side * 6
            else:
                xe = vt(ax, x, yt, side=side, c=cc, fused=(kind == "VT"))
            if lab:   # label beside the tapped device, away from the conductor
                lines_text(ax, xe + side * 3.5 if side > 0 else xe - 3.5, yt + LINE_H / 2 - (2.5 if kind != "SA" else 1.5), lab,
                           c=cc, ha="left" if side > 0 else "right")
                lab = None
        elif kind == "TX":
            line(ax, [(x, y), (x, y - 1.5)], c=cc)
            yy = transformer(ax, x, y - 1.5, c1=o.get("c1", cc), c2=o.get("c2", cc))
            line(ax, [(x, yy), (x, yb)], c=o.get("c2", cc))
        elif kind == "G":
            yy = generator(ax, x, y - 1, c=cc)
            line(ax, [(x, yy), (x, yb)], c=cc)
        elif kind == "UPS":
            yy = ups(ax, x, y, c=cc, batt=o.get("batt", True), side=o.get("bside", -1))
            line(ax, [(x, yy), (x, yb)], c=cc)
        elif kind == "SBS":
            line(ax, [(x, y), (x, y - 1)], c=cc); yy = static_switch(ax, x, y - 1, c=cc); line(ax, [(x, yy), (x, yb)], c=cc)
        elif kind == "CONV":
            line(ax, [(x, y), (x, y - 1)], c=cc); yy = converter(ax, x, y - 1, o.get("kind", "dc/ac"), c=cc)
            line(ax, [(x, yy), (x, yb)], c=cc)
        elif kind == "BAT":
            yy = battery(ax, x, y, c=cc)
        if lab:
            dxl = o.get("lx", lx)
            ytop = mid + block_h(lab, o.get("fs0")) / 2
            lines_text(ax, x + dxl, ytop, lab, c=o.get("lc", cl or cc), first_bold=o.get("bold", False) or bool(o.get("fs0")),
                       ha="left" if dxl >= 0 else "right", fs0=o.get("fs0"))
        if o.get("key"):
            cen[o["key"]] = mid
        y = yb
    MINH = _old
    return y, cen
