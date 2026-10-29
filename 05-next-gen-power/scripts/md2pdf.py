"""Markdown -> HTML -> PDF with headless Chrome. Usage: md2pdf.py in.md out.pdf [a4|a4l|a3l] [font_pt] [footer text]
With a footer text, the PDF is printed through Playwright with that text and "page N of M" on every page."""
import sys, subprocess, markdown, pathlib, tempfile
src, out = sys.argv[1], sys.argv[2]
size = {"a4": "A4", "a4l": "A4 landscape", "a3l": "A3 landscape"}[sys.argv[3] if len(sys.argv) > 3 else "a4"]
fs = sys.argv[4] if len(sys.argv) > 4 else "9.5"
import re
txt = pathlib.Path(src).read_text()
# bare URLs -> autolinks, so underscores in URLs are not read as emphasis and links stay clickable
txt = re.sub(r"(?<![<(])(https?://[^\s<>|]+?)([.,;]?)(?=\s|$)", r"<\1>\2", txt, flags=re.M)
body = markdown.markdown(txt, extensions=["tables", "sane_lists"])
css = f"""@page {{ size: {size}; margin: 10mm 10mm 12mm 10mm; }}
body {{ font-family: 'DejaVu Sans', sans-serif; font-size: {fs}pt; color: #000; line-height: 1.28; }}
h1 {{ font-size: 1.45em; margin: 0 0 4px 0; border-bottom: 1.5px solid #000; }}
h2 {{ font-size: 1.2em; margin: 10px 0 3px 0; break-after: avoid; page-break-after: avoid; }} a {{ color: #000; }} h3 {{ font-size: 1.05em; margin: 8px 0 2px 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 4px 0; page-break-inside: auto; }}
th, td {{ border: 0.6px solid #000; padding: 2px 4px; vertical-align: top; text-align: left; }}
th {{ background: #e8e8e8; }} tr {{ page-break-inside: avoid; }}
p, li {{ margin: 2px 0; }} ul, ol {{ margin: 2px 0 2px 18px; padding: 0; }}
code {{ font-size: 0.95em; }}"""
# keep a heading with a short following block (Chrome ignores break-after: avoid)
body = re.sub(r"(<h2>(?:(?!</h2>).)*</h2>\s*<(p|ol)>.*?</\2>)", lambda m: f'<div style="break-inside: avoid">{m.group(1)}</div>' if len(m.group(1)) < 2500 else m.group(1), body, flags=re.S)
html = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
    f.write(html); h = f.name
footer = sys.argv[5] if len(sys.argv) > 5 else ""
if footer:
    from playwright.sync_api import sync_playwright
    ft = ("<div style='width:100%; font-family: DejaVu Sans, sans-serif; font-size:7pt; color:#000; padding:0 10mm; "
          "display:flex; justify-content:space-between'><span>" + footer + "</span>"
          "<span>Page <span class='pageNumber'></span> of <span class='totalPages'></span></span></div>")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = b.new_page(); pg.goto(pathlib.Path(h).as_uri()); pg.wait_for_load_state("networkidle")
        pg.pdf(path=out, prefer_css_page_size=True, display_header_footer=True,
               header_template="<span></span>", footer_template=ft)
        b.close()
else:
    subprocess.run(["google-chrome", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", h], check=True, capture_output=True)
print(out)
