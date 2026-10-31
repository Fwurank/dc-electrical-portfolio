"""DWU-DC-E-FIG-004-S (draft v0.1): storage layers on a log time axis, for Project 05 context.
All numbers come from Project 01 DB-001 Rev P2, Project 05 CALC-004 Rev P1a, or OCP Mt. Diablo v1.0.0."""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import sld_lib as L
from draft_frame import frame_and_title_draft

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "05-bess", "context")
STEM = "FIG-004S_storage_layers_block-v0.1-2026-10-29-en"
X0, X1, T0, T1 = 40.0, 400.0, -6.0, 5.5          # log10 seconds from 1 µs to ~3.6e5 s


def X(t):
    return X0 + (math.log10(t) - T0) / (T1 - T0) * (X1 - X0)


def bar(ax, t1, t2, y, name, lines, h=7.0):
    L.box(ax, X(t1), y - h / 2, X(t2) - X(t1), h, lw=1.6, z=3)
    L.text(ax, X(t1) + 1.5, y, name, weight="bold", z=6)
    L.lines_text(ax, X(t1), y - h / 2 - 0.6, lines)


def main():
    fig, ax = L.new_sheet()
    L.text(ax, 25, 278, "STORAGE AND SOURCE LAYERS vs TIME (campus of Projects 01 and 05)", fs=L.FS_TAG, weight="bold")
    L.text(ax, 25, 271.5, "Bar = time span the layer covers, from response time to end of energy at the stated load. Log scale.")
    rows = [
        (1e-6, 0.02, "Rack PSU capacitors", ["hold-up up to 20 ms (OCP Mt. Diablo v1.0.0) [Verified]"]),
        (5e-3, 30, "Supercap hybrid at 20 kV", ["23 kWh per 10 MW, < 10 ms: AI ripple 5.6 → 0.79 MW p-p (CALC-004) [Inference, model]"]),
        (0.02, 90, "Rack BBU", ["45–90 s at 100 % load (OCP spec) [Verified] · not in the Project 01 base design"]),
        (1e-3, 486, "Static UPS, LFP, per block", ["VFI online · 2 × 165 kWh: 5 min at Pr EoL, 8.1 min in N-1 (DB-001 P2)"]),
        (0.15, 7200, "Campus BESS 10 MW / 20 MWh", ["response ≈ 150 ms · 27 min at campus peak · not counted in redundancy (CALC-004)"]),
        (12, 86400, "Gensets, 1 per block, HVO100", ["on load ≈ 10–15 s (CALC-004) · 24 h fuel on site (DB-001 P2)"]),
    ]
    y = 255
    for t1, t2, n, ls in rows:
        bar(ax, t1, t2, y, n, ls)
        y -= 19
    # axis
    ya = 146
    L.line(ax, [(X0, ya), (X1, ya)], lw=1.2)
    for e, lab in ((-6, "1 µs"), (-3, "1 ms"), (-2, "10 ms"), (-1, "100 ms"), (0, "1 s"), (1, "10 s"), (math.log10(60), "1 min"),
                   (math.log10(600), "10 min"), (math.log10(3600), "1 h"), (math.log10(43200), "12 h"), (math.log10(86400), "24 h")):
        x = X(10 ** e)
        L.line(ax, [(x, ya), (x, ya - 2.5)], lw=L.THIN)
        L.line(ax, [(x, ya), (x, 262)], lw=0.3, ls=(0, (1, 3)), z=1)
        L.text(ax, x, ya - 4.5, lab, ha="center", va="top")
    # demands
    L.text(ax, 25, 132, "WHAT EACH TIMESCALE HAS TO COVER", weight="bold")
    dem = [
        (0.02, "ITI / PSU ride-through context ≈ 20 ms [Vendor claim]", 125),
        (0.5, "AI iteration ripple 0.1–2 Hz needs ≲ 10 ms response (CALC-004)", 118),
        (12, "grid → genset gap ≈ 10–15 s, bridged by UPS behind open-transition ATS", 111),
        (120, "AI ramp limit 3 MW/min (A): ≈ 11.4 MW but only 0.46 MWh (CALC-004)", 104),
        (43200, "Uptime Tier: ≥ 12 h fuel at N [Verified, Uptime Journal 2014]", 97),
    ]
    for t, s, yy in dem:
        x = X(t)
        L.line(ax, [(x, ya - 9), (x, yy + 2.5)], lw=L.THIN, ls=(0, (3, 1.5)))
        L.dot(ax, x, yy + 2.5, r=0.7)
        t_ = L.text(ax, x + 1.5 if x < 260 else x - 1.5, yy, s, ha="left" if x < 260 else "right")
        t_.set_bbox(dict(fc="white", ec="none", pad=0.6))
    L.lines_text(ax, 25, 88, [
        "READING THE CHART",
        "· No single layer covers 1 µs to 24 h. Fast layers have little energy; long layers respond slowly.",
        "· The campus BESS cannot replace the UPS (150 ms response, 20 kV, behind ATS) or the gensets (27 min) — CALC-004 §4.",
        "· AI ripple is a ms-to-s problem: capacitors / supercap, not a 20 kV BESS alone (5.6 MW p-p residual at 150 ms).",
        "· Labels: [Verified] = source opened 2026-10-29; (A) / model values = Project 05 assumptions; [Vendor claim] not a design value.",
        "Codes (pointers, [Unverified]): EN 50600-2-2 · IEC 62040 · ISO 8528-1 · IEC 62933-5-2.",
    ], first_bold=True)
    frame_and_title_draft(ax, "DWU-DC-E-FIG-004S", "Storage layers vs time (draft)",
                          "Context figure for Project 05 · block diagram, no ratings changed",
                          revdesc="Research draft, Project 05 context", project="Project 05 context (draft)")
    L.save(fig, OUT, STEM)


if __name__ == "__main__":
    main()
