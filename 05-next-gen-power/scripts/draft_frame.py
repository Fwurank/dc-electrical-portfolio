"""Draft title block for research drafts (v0.1). Same geometry as sld_lib.frame_and_title (portfolio Rev P2),
but with draft revision, date and the required review wording. sld_lib.py itself is an unmodified copy."""
import sld_lib as L

STATUS = "CONCEPT / DRAFT — requires review by a licensed electrical engineer"


def frame_and_title_draft(ax, dwg_no, title, subtitle, sheet=1, sheets=1, rev="v0.1", date="2026-10-29",
                          revdesc="Research draft", project="Project 05 (draft)"):
    L.box(ax, 20, 10, 390, 277, lw=1.4)
    for i in range(8):
        xm = 20 + (i + 0.5) * 390 / 8
        L.text(ax, xm, 290.5, str(i + 1), ha="center"); L.text(ax, xm, 6.2, str(i + 1), ha="center")
    for j, c in enumerate("FEDCBA"):
        ym = 10 + (j + 0.5) * 277 / 6
        L.text(ax, 15, ym, c, ha="center"); L.text(ax, 414.5, ym, c, ha="center")
    x0, y0, w = 230, 10, 180
    L.line(ax, [(x0 + 118, y0), (x0 + 118, y0 + 12)], lw=L.THIN)
    L.line(ax, [(x0 + 148, y0), (x0 + 148, y0 + 12)], lw=L.THIN)
    L.text(ax, x0 + 2, y0 + 9.0, "Drawing no.")
    L.text(ax, x0 + 2, y0 + 3.8, dwg_no, fs=L.FS_DWG, weight="bold")
    L.text(ax, x0 + 120, y0 + 9.0, "Sheet"); L.text(ax, x0 + 120, y0 + 3.8, f"{sheet} / {sheets}", weight="bold")
    L.text(ax, x0 + 150, y0 + 9.0, "Rev"); L.text(ax, x0 + 150, y0 + 3.8, rev, weight="bold")
    for yy in (12, 27, 38):
        L.line(ax, [(x0, y0 + yy), (x0 + w, y0 + yy)], lw=L.THIN, z=1.5)
    L.text(ax, x0 + 2, y0 + 23.6, title, weight="bold")
    L.text(ax, x0 + 2, y0 + 19.0, subtitle)
    L.text(ax, x0 + 2, y0 + 14.4, STATUS)
    L.text(ax, x0 + 2, y0 + 34.8, "Nordic Hyperscale DC Campus (fictional) · 30 MW IT · SE3", weight="bold")
    L.text(ax, x0 + 2, y0 + 30.2, f"Portfolio D. Wu · {project} · public sources, scale NTS · A3")
    yr = y0 + 38
    L.text(ax, x0 + 2, yr + (L.LINE_H + 1) / 2, rev, weight="bold")
    L.text(ax, x0 + 13, yr + (L.LINE_H + 1) / 2, date)
    L.text(ax, x0 + 37, yr + (L.LINE_H + 1) / 2, revdesc)
    yr += L.LINE_H + 1
    L.box(ax, x0, y0, w, yr - y0, lw=1.2, fill="white", z=1)
    return yr
