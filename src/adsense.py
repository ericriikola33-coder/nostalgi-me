"""Adds the AdSense snippet to every page and writes ads.txt. Usage: python3 -I adsense.py <site-dir> <pub-id digits>"""
import pathlib, sys
SITE = pathlib.Path(sys.argv[1]); PUB = sys.argv[2]
assert PUB.isdigit() and len(PUB) == 16
SNIPPET = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-{PUB}" '
           'crossorigin="anonymous"></script>\n')
n = 0
for f in SITE.rglob("*.html"):
    t = f.read_text(encoding="utf-8")
    if "adsbygoogle.js" in t:
        continue
    assert t.count("</head>") == 1, f
    f.write_text(t.replace("</head>", SNIPPET + "</head>"), encoding="utf-8"); n += 1
(SITE / "ads.txt").write_text(f"google.com, pub-{PUB}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
print("pages", n)
