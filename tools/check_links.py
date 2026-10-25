"""Check every link in the site HTML and the Markdown READMEs: relative links must point to an existing file
(and #anchors to an existing id); external links are listed, not fetched. Optional: --base http://127.0.0.1:8765/
also requests every relative link from a running local server.  Run from the repository root."""
import os, re, sys, urllib.parse, urllib.request
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else None


class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.links, self.ids = [], set()
    def handle_starttag(self, tag, a):
        a = dict(a)
        if "id" in a: self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k): self.links.append(a[k])


def parse(path):
    if path.endswith(".html"):
        p = P(); p.feed(open(path, encoding="utf-8").read()); return p.links, p.ids
    txt = open(path, encoding="utf-8").read()
    txt = re.sub(r"```.*?```", "", txt, flags=re.S)
    return re.findall(r"\]\(([^)\s]+)\)", txt), set()


files = [os.path.join(d, f) for d, _, fs in os.walk(ROOT) if ".git" not in d and ".venv" not in d
         for f in fs if f.endswith(".html") or f == "README.md"]
ok = bad = 0; ext = set(); idcache = {}
for f in sorted(files):
    links, ids = parse(f); idcache[f] = ids
    for l in links:
        if l.startswith(("http://", "https://", "mailto:")):
            ext.add(l); continue
        u = urllib.parse.urlparse(l); target = os.path.normpath(os.path.join(os.path.dirname(f), urllib.parse.unquote(u.path))) if u.path else f
        good = os.path.exists(target)
        if good and u.fragment and target.endswith(".html"):
            good = u.fragment in parse(target)[1]
        if good and base and f.endswith(".html"):
            rel = os.path.relpath(target, ROOT).replace(os.sep, "/")
            try: good = urllib.request.urlopen(base + rel, timeout=10).status == 200
            except Exception: good = False
        if good: ok += 1
        else: bad += 1; print("BROKEN", os.path.relpath(f, ROOT), "->", l)
print(f"files {len(files)}, relative links OK {ok}, broken {bad}, external (not fetched) {len(ext)}")
for e in sorted(ext): print("  external:", e)
sys.exit(1 if bad else 0)
