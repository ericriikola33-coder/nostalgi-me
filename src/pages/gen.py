"""Builds the content pages, navigation, sitemap and robots.txt for nostalgi.me.
Usage: python3 -I gen.py <pages-dir> <site-dir>   (site-dir already holds index.html)"""
import html, pathlib, re, sys

PAGES = pathlib.Path(sys.argv[1]); SITE = pathlib.Path(sys.argv[2])
BASE = "https://nostalgi.me/"
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Shrikhand&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">')
ICON = '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 106%22%3E%3Cpath d=%22M10 100 A90 90 0 0 1 190 100 Z%22 fill=%22%23c8563f%22/%3E%3Cpath d=%22M50 100 A50 50 0 0 1 150 100 Z%22 fill=%22%23f2c66e%22/%3E%3C/svg%3E">'
NAV = [("index.html", "Året du föddes"), ("artiklar/index.html", "Artiklar"), ("om.html", "Om"), ("kontakt.html", "Kontakt")]
FOOT = [("index.html", "Startsida"), ("artiklar/index.html", "Artiklar"), ("om.html", "Om nostalgi.me"), ("kontakt.html", "Kontakt"), ("integritetspolicy.html", "Integritet och cookies")]

def clean(u):
    """Cloudflare Pages serves om.html at /om and artiklar/index.html at /artiklar/."""
    u = re.sub(r"index\.html$", "", u)
    return re.sub(r"\.html$", "", u)

def rel(target, here):
    depth = here.count("/")
    return "../" * depth + target

def nav(here):
    links = "".join(f'<a class="l" href="{rel(p, here)}"' + (' aria-current="page"' if p == here or (p == "artiklar/index.html" and here.startswith("artiklar/")) else "") + f'>{t}</a>' for p, t in NAV)
    return f'<header class="site-nav"><div class="in"><a class="logo" href="{rel("index.html", here)}">nostalgi</a>{links}</div></header>'

def foot(here):
    links = "".join(f'<a href="{rel(p, here)}">{t}</a>' for p, t in FOOT)
    return (f'<footer class="site-foot"><div class="in"><nav aria-label="Sidfot">{links}</nav>'
            '<div>© 2026 nostalgi.me · Innehållet är till för nöjes skull och kan innehålla fel.</div></div></footer>')

def inline(s):
    s = html.escape(s, quote=False)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{m.group(2)}"' + (' rel="noopener"' if m.group(2).startswith("http") else "") + f'>{m.group(1)}</a>', s)

def body_html(lines):
    out, para, ul = [], [], []
    def flush():
        if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para.clear()
        if ul: out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in ul) + "</ul>"); ul.clear()
    for ln in lines:
        if not ln.strip(): flush(); continue
        if ln.startswith("## "): flush(); out.append(f"<h2>{inline(ln[3:])}</h2>"); continue
        if ln.startswith("- "): para and flush(); ul.append(ln[2:]); continue
        para.append(ln.strip())
    flush(); return "\n".join(out)

def page(here, title, desc, main):
    return f'''<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · nostalgi.me</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{BASE}{clean(here)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
{ICON}
{FONTS}
<link rel="stylesheet" href="{rel('style.css', here)}">
</head>
<body>
{nav(here)}
<main class="article">
{main}
</main>
{foot(here)}
</body>
</html>
'''

def parse(f):
    meta, body, in_body = {}, [], False
    for ln in f.read_text(encoding="utf-8").splitlines():
        if not in_body and re.match(r"^(path|group|title|desc|h1|lead):", ln):
            k, v = ln.split(":", 1); meta[k] = v.strip(); continue
        in_body = True; body.append(ln)
    return meta, body

written = []
articles = []
for f in sorted((PAGES / "content").glob("*.txt")):
    m, body = parse(f)
    here = m["path"]
    main = f'<h1>{inline(m["h1"])}</h1>\n<p class="lead">{inline(m["lead"])}</p>\n{body_html(body)}'
    if here.startswith("artiklar/"):
        articles.append(m)
        main += (f'\n<div class="box"><strong>Sök ditt år</strong><p style="margin:6px 0 12px">Vill du veta mer om ett särskilt år? Skriv in det och se musik, händelser, priser och quiz.</p>'
                 f'<a class="btn" href="{rel("index.html", here)}#search">Till årssökningen</a></div>')
    if here == "integritetspolicy.html":
        main += '\n<p class="updated">Senast uppdaterad: november 2026.</p>'
    out = SITE / here; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(here, m["title"], m["desc"], main), encoding="utf-8"); written.append(here)

ORDER = ["barnprogram", "bilar-och-mopeder", "leksaker", "godis-och-mat", "tv-och-radio", "telefoner", "semester-och-noje", "hemmet", "visste-du-att"]
decades = [m for m in articles if m.get("group", "decade") == "decade"]
themes = sorted([m for m in articles if m.get("group") == "tema"], key=lambda m: ORDER.index(m["path"][9:-5]) if m["path"][9:-5] in ORDER else 99)

def card_text(m):
    t = m["title"]
    return t.split(": ", 1)[1][0].upper() + t.split(": ", 1)[1][1:] if ": " in t else m["desc"].split(". ")[0].rstrip(".")

# links between articles, within each group
for group in (decades, themes):
  for i, m in enumerate(group):
    articles = group
    p = SITE / m["path"]; t = p.read_text(encoding="utf-8")
    prev_a = articles[i - 1] if i > 0 else None; next_a = articles[i + 1] if i + 1 < len(articles) else None
    links = []
    if prev_a: links.append(f'<a href="{prev_a["path"].split("/")[1]}">← {prev_a["h1"]}</a>')
    links.append('<a href="index.html">Alla artiklar</a>')
    if next_a: links.append(f'<a href="{next_a["path"].split("/")[1]}">{next_a["h1"]} →</a>')
    t = t.replace("</main>", f'<nav class="more" aria-label="Fler artiklar" style="display:flex;flex-wrap:wrap;gap:10px 20px;justify-content:space-between">{"".join(links)}</nav>\n</main>')
    p.write_text(t, encoding="utf-8")

# article index
def cards(group):
    return '<div class="cards">' + "".join(f'<a href="{m["path"].split("/")[1]}"><strong>{m["h1"]}</strong><span>{html.escape(card_text(m))}</span></a>' for m in group) + "</div>"
main = ('<h1>Artiklar</h1>\n<p class="lead">Hur var det att leva förr? Här berättar vi om musiken, prylarna, modet och händelserna som präglade varje årtionde, och om sakerna som många av oss minns från barndomen.</p>\n'
        '<h2>Minnen och kuriosa</h2>' + cards(themes) + '\n<h2 style="margin-top:36px">Årtionde för årtionde</h2>' + cards(decades))
(SITE / "artiklar").mkdir(exist_ok=True)
(SITE / "artiklar/index.html").write_text(page("artiklar/index.html", "Artiklar om förr", "Barnprogram, bilar, leksaker, godis och kuriosa från förr, och hur det var att leva i Sverige under varje årtionde från 1950-talet.", main), encoding="utf-8")
written.append("artiklar/index.html")

# 404
(SITE / "404.html").write_text(page("404.html", "Sidan finns inte", "Sidan kunde inte hittas.",
    '<h1>Hoppsan!</h1><p class="lead">Den här sidan verkar ha försvunnit i tidsmaskinen.</p><a class="btn" href="/">Till startsidan</a>'), encoding="utf-8")

# nav + footer on the main tool page
idx = SITE / "index.html"; t = idx.read_text(encoding="utf-8")
if "site-nav" not in t:
    t = t.replace('<link href="https://fonts.googleapis.com/css2?family=Shrikhand&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">',
                  '<link href="https://fonts.googleapis.com/css2?family=Shrikhand&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">\n<link rel="stylesheet" href="style.css">\n<link rel="canonical" href="https://nostalgi.me/">', 1)
    t = t.replace('<body>\n<div class="band">', '<body>\n' + nav("index.html") + '\n<div class="band">', 1)
    t = t.replace('\n<script>', '\n' + foot("index.html") + '\n<script>', 1)
    home_cards = '<div class="cards">' + "".join(f'<a href="artiklar/{m["path"].split("/")[1]}"><strong style="font-size:1.15rem">{m["h1"]}</strong><span>{html.escape(card_text(m))}</span></a>' for m in themes[:6]) + "</div>"
    t = t.replace('<div id="etsyfoot"></div>', '<section style="margin-top:40px"><p class="qtitle">Minnen och kuriosa</p><p class="sub" style="margin:6px 0 0">Barnprogram, bilar, leksaker och godis från förr. <a href="artiklar/index.html">Alla artiklar</a></p>' + home_cards + '</section>\n<div id="etsyfoot"></div>', 1)
    assert t.count("site-nav") >= 1 and t.count("site-foot") >= 1
idx.write_text(t, encoding="utf-8")

# robots + sitemap
(SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
urls = ["index.html"] + written
sm = "".join(f"<url><loc>{BASE}{clean(u)}</loc></url>\n" for u in dict.fromkeys(urls))
(SITE / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + sm + "</urlset>\n", encoding="utf-8")
(SITE / "style.css").write_text((PAGES / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
print("written", written)
