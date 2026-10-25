"""Collect every assumption of projects 01-04 into one CSV (ASSUMPTIONS_REGISTER_ALL.csv).

Sources:
* 01: the tables in DB-001 Rev P2 §3 (site, assumed), §8 (equipment ratings, Rev P2; sized in CALC-002/003/004)
  and §8.1 (network data, assumed).
* 02: every code line tagged [ASSUMED] in dcsizing/ (tables.py holds the reference data).
* 03: the scprot.campus.Data and scprot.earthing.EarthingData defaults, and every [ASSUMED] code line.
* 04: bessdc.assumptions.register(), exported as results/assumptions_register.csv. Each value has a
  PUBLIC / ASSUMED / PROJECT tag and its source.
Run from the repository root:  python tools/build_assumptions_register.py
"""
import csv, dataclasses, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = {k: os.path.join(ROOT, v) for k, v in {"01": "01-design-basis-sld", "02": "02-load-sizing",
                                             "03": "03-shortcircuit-protection", "04": "04-bess"}.items()}
rows = []


def add(project, group, name, value, tag, note, source):
    rows.append(dict(project=project, group=group, name=name, value=value, tag=tag, note=note, source=source))


# ---- 01: markdown tables in §3, §8, §8.1
md = open(os.path.join(P["01"], "docs", "01_Design_Basis.md"), encoding="utf-8").read()
TAG01 = {"## 3. Site assumptions": "ASSUMED (A)", "## 8. Equipment ratings": "PROJECT rating (Rev P2, checked in CALC-00x)",
         "### 8.1 Network data": "ASSUMED (A)"}
for sec in TAG01:
    block = md.split(sec, 1)[1].split("\n#", 1)[0]
    lines = [l for l in block.splitlines() if l.startswith("|")][2:]
    for l in lines:
        cells = [c.strip().replace("**", "") for c in l.strip("|").split("|")]
        if cells[0].startswith("Results"):
            continue  # calculated results, not an assumption
        add("01", sec.lstrip("# ").split("(")[0].strip(), cells[0], " | ".join(cells[1:]), TAG01[sec],
            "", "01-design-basis-sld/docs/01_Design_Basis.md")


# ---- 02/03: tagged code lines
def scan(project, pkg_dir):
    for fn in sorted(os.listdir(pkg_dir)):
        if not fn.endswith(".py"):
            continue
        for i, line in enumerate(open(os.path.join(pkg_dir, fn), encoding="utf-8"), 1):
            if "ASSUMED" in line and "ASSUMED /" not in line and "ASSUMED data only" not in line:
                txt = re.sub(r"\s+", " ", line.strip())
                add(project, fn, f"line {i}", "", "ASSUMED", txt[:220],
                    os.path.relpath(os.path.join(pkg_dir, fn), ROOT) + f":{i}")


scan("02", os.path.join(P["02"], "dcsizing"))

sys.path.insert(0, P["03"])
from scprot import campus, earthing  # noqa: E402
for cls, grp in ((campus.Data, "campus.Data"), (earthing.EarthingData, "earthing.EarthingData")):
    for f in dataclasses.fields(cls):
        default = f.default if f.default is not dataclasses.MISSING else f.default_factory()
        add("03", grp, f.name, default, "ASSUMED (DB-001 §8.1 / CALC-002)", "",
            f"03-shortcircuit-protection/scprot/{grp.split('.')[0]}.py")
scan("03", os.path.join(P["03"], "scprot"))

# ---- 04: structured register
reg = os.path.join(P["04"], "results", "assumptions_register.csv")
for r in csv.DictReader(open(reg, encoding="utf-8")):
    add("04", r["group"], r["name"], r["value"], r["tag"], r["note"], r["source"])

out = os.path.join(ROOT, "ASSUMPTIONS_REGISTER_ALL.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
from collections import Counter
print(out, len(rows), "rows", dict(Counter(r["project"] for r in rows)))
