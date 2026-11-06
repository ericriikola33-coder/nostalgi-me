"""Adds the GoatCounter snippet to every page. Usage: python3 -I goatcounter.py <site-dir> <code>"""
import pathlib, re, sys
SITE = pathlib.Path(sys.argv[1]); CODE = sys.argv[2]
assert re.fullmatch(r"[a-z0-9-]+", CODE)
SNIPPET = f'<script data-goatcounter="https://{CODE}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>\n'
n = 0
for f in SITE.rglob("*.html"):
    t = f.read_text(encoding="utf-8")
    if "data-goatcounter" in t:
        continue
    assert t.count("</head>") == 1, f
    f.write_text(t.replace("</head>", SNIPPET + "</head>"), encoding="utf-8"); n += 1
print("pages", n)
