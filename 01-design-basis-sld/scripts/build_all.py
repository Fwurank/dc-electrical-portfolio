"""Build all deliverables (Rev P2): 8 SLD sheets (SVG/PDF/PNG), combined A3 SLD PDF, text-height /
layout check report, and the design-basis PDF with all sheets as appendix A."""
import os, re, subprocess, sys, base64, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DWG = os.path.join(ROOT, "drawings")
DOCS = os.path.join(ROOT, "docs")
sys.path.insert(0, HERE)
import matplotlib.pyplot as plt
from sheets import SHEETS

STEMS = [stem for _, stem in SHEETS]
for modname, _ in SHEETS:
    importlib.import_module(modname).draw(DWG); plt.close("all")
subprocess.run(["pdfunite"] + [os.path.join(DWG, s + ".pdf") for s in STEMS]
               + [os.path.join(DWG, "DWU-DC-E-SLD_concept_set_RevP2_A3.pdf")], check=True)
# text-height (>= 2.5 mm at A3) and overlap check on the exported sheets; fails the build on any issue
subprocess.run([sys.executable, os.path.join(HERE, "check_drawings.py"), "--json",
                os.path.join(DWG, "text_height_check.json")], check=True)

# ---- design basis: markdown -> HTML -> PDF (headless Chrome)
import markdown
md_text = open(os.path.join(DOCS, "01_Design_Basis.md"), encoding="utf-8").read()
md_text = re.sub(r"^---\n.*?\n---\n", "", md_text, flags=re.S)
html_body = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
imgs = ""
for s in STEMS:
    b64 = base64.b64encode(open(os.path.join(DWG, s + ".png"), "rb").read()).decode()
    imgs += f'<div class="sheet"><img src="data:image/png;base64,{b64}"/><p class="cap">{s}</p></div>'
css = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
@page landscape { size: A4 landscape; margin: 8mm; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 9pt; line-height: 1.38; color: #111; }
h1 { font-size: 17pt; color: #1f3b73; margin: 0 0 2pt 0; }
h2 { font-size: 12pt; color: #1f3b73; border-bottom: 1.2pt solid #1f3b73; padding-bottom: 2pt; margin-top: 14pt; }
h3 { font-size: 10pt; color: #333; margin-top: 10pt; }
h1 + h2 { border: none; font-size: 10.5pt; color: #444; margin-top: 0; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 8pt 0; font-size: 7.8pt; page-break-inside: avoid; }
th, td { border: 0.5pt solid #9aa5b8; padding: 2.5pt 4pt; vertical-align: top; text-align: left; }
th { background: #e9eef5; }
blockquote { border-left: 3pt solid #c8102e; background: #fbf3f3; margin: 6pt 0; padding: 4pt 8pt; font-size: 8.3pt; }
code { font-size: 8pt; }
.sheet { page: landscape; page-break-before: always; text-align: center; }
.sheet img { width: 100%; max-height: 180mm; object-fit: contain; }
.sheet { page-break-inside: avoid; }
.cap { font-size: 8pt; color: #555; margin: 2pt; }
.footer { font-size: 7pt; color: #777; }
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{html_body}{imgs}</body></html>"
html_path = os.path.join(DOCS, "01_Design_Basis.html")
open(html_path, "w", encoding="utf-8").write(html)
pdf_path = os.path.join(DOCS, "DWU-DC-E-DB-001_Design_Basis.pdf")
subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}", "file://" + html_path], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("built", pdf_path)
