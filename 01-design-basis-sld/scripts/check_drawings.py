"""Drawing QA for the Rev P2 SLD set.

1. Printed text height: parses every <text> in the exported SVG (font size in SVG user units = pt, viewBox
   width = 420 mm sheet). It computes the em and cap height in mm at A3 and fails below 2.5 mm cap height.
   The DejaVu Sans cap height ratio is measured from the outline of the glyph 'H'.
2. Layout: re-draws each sheet, then checks text-text bbox overlaps and text crossings with any line or patch
   edge (bbox shrunk by 0.3 mm tolerance), plus text outside the drawing frame.
Usage: python check_drawings.py [--json out.json]
"""
import os, re, sys, json, importlib
import xml.etree.ElementTree as ET
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sld_lib
from sheets import SHEETS
DWG_MIN = 3.5   # drawing number cap height, mm: ISO 3098 standard height 3.5 (title block is one uniform 180 mm rectangle)
# SLD_CHECK_OUT lets the test suite re-draw into a temp folder instead of overwriting drawings/
DWG = os.environ.get("SLD_CHECK_OUT") or os.path.join(os.path.dirname(HERE), "drawings")


def cap_ratio():
    """Cap height / em measured from the outline of the glyph 'H' in the font actually used (DejaVu Sans)."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    e = TextPath((0, 0), "H", size=100, prop=FontProperties(family="DejaVu Sans")).get_extents()
    return e.height / 100.0


def svg_text_heights(svg_path, cap):
    root = ET.parse(svg_path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    mm_per_unit = sld_lib.A3_W / vb[2]
    out = []
    for el in root.iter():
        if not el.tag.endswith("text"):
            continue
        st = el.get("style", "")
        m = re.search(r"font(?:-size)?:\s*(?:[a-z ]*?)([\d.]+)px", st)
        if not m:
            continue
        size = float(m.group(1))
        sc = re.search(r"scale\(([\d.]+)", el.get("transform", ""))
        size *= float(sc.group(1)) if sc else 1.0
        s = "".join(el.itertext()).strip()
        out.append((size * mm_per_unit * cap, size * mm_per_unit, s))
    return out


def _seg_hits_box(p, q, b):
    x0, y0, x1, y1 = b
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
        else:
            t = qq / pp
            if pp < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


TEXT_GAP = 0.8   # mm, minimum horizontal clearance between two texts on the same line


def layout_issues(fig, tol=0.3):
    ax = fig.axes[0]
    r = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    boxes = []
    for t in ax.texts:
        if not t.get_text().strip():
            continue
        bb = inv.transform(t.get_window_extent(r).get_points())
        b = (bb[0][0] + tol, bb[0][1] + tol, bb[1][0] - tol, bb[1][1] - tol)
        boxes.append((b, t.get_text().replace("\n", " | ")[:40]))
    segs = []
    for ln in ax.lines:
        xy = ln.get_xydata()
        segs += [(tuple(xy[i]), tuple(xy[i + 1])) for i in range(len(xy) - 1)]
    for p in ax.patches:
        path = p.get_path().transformed(p.get_patch_transform())
        for poly in path.to_polygons(closed_only=False):
            segs += [(tuple(poly[i]), tuple(poly[i + 1])) for i in range(len(poly) - 1)]
    issues = []
    for i, (a, sa) in enumerate(boxes):
        for b, sb in boxes[i + 1:]:
            g = TEXT_GAP + 2 * tol     # texts must keep >= TEXT_GAP mm clear of each other
            if a[0] - g < b[2] and b[0] - g < a[2] and a[1] < b[3] and b[1] < a[3]:
                issues.append(("text/text", sa, sb))
        n = sum(_seg_hits_box(p, q, a) for p, q in segs)
        if n:
            issues.append(("text/line", sa, f"{n} segment(s)"))
        if a[0] < 0 or a[2] > sld_lib.A3_W or a[1] < 0 or a[3] > sld_lib.A3_H:
            issues.append(("off-sheet", sa, ""))
    return issues


def main():
    cap = cap_ratio()
    report = {"cap_ratio": cap, "sheets": {}}
    captured = {}
    orig = sld_lib.save
    def grab(fig, outdir, stem):
        captured[stem] = layout_issues(fig)
        orig(fig, outdir, stem)
    sld_lib.save = grab
    ok_all = True
    only = [a for a in sys.argv[1:] if not a.startswith("--") and not a.endswith(".json")]
    for modname, stem in SHEETS:
        if only and not any(o in stem for o in only):
            continue
        try:
            mod = importlib.import_module(modname)
        except ModuleNotFoundError:
            print(f"{stem:42s} MISSING"); ok_all = False; continue
        mod.save = grab
        mod.draw(DWG)
        h = svg_text_heights(os.path.join(DWG, stem + ".svg"), cap)
        caps = [c for c, _, _ in h]
        small = [(round(c, 2), s) for c, _, s in h if c < 2.5 - 1e-9]
        dn = [c for c, _, s in h if s.startswith("DWU-DC-E-SLD")]
        iss = captured[stem]
        ok = not small and not iss and (dn and min(dn) >= DWG_MIN)
        ok_all &= bool(ok)
        report["sheets"][stem] = {"n_text": len(h), "min_cap_mm": round(min(caps), 2), "max_cap_mm": round(max(caps), 2),
                                  "min_em_mm": round(min(e for _, e, _ in h), 2),
                                  "dwg_no_cap_mm": round(min(dn), 2) if dn else None,
                                  "below_2p5": small, "layout_issues": iss, "ok": bool(ok)}
        print(f"{stem:42s} texts {len(h):4d}  min cap {min(caps):.2f} mm  dwg-no cap {min(dn) if dn else 0:.2f} mm  "
              f"<2.5mm: {len(small)}  layout issues: {len(iss)}  {'OK' if ok else 'FAIL'}")
        for it in iss[:40]:
            print("     ", it)
    report["ok"] = bool(ok_all)
    if "--json" in sys.argv:
        json.dump(report, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1, ensure_ascii=False)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
