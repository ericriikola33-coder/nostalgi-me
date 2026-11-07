"""Sets the shop link on the start page (empty = hidden) and uses neutral shop wording.
Usage: python3 -I src/shop.py site "https://riikola.gumroad.com/"   (or "" to hide)"""
import pathlib, re, sys

SITE = pathlib.Path(sys.argv[1]); URL = sys.argv[2]
assert URL == "" or URL.startswith("https://"), "URL must be https or empty"
f = SITE / "index.html"
t = f.read_text(encoding="utf-8")
t, n = re.subn(r'const ETSY_URL = "[^"]*";', f'const ETSY_URL = "{URL}";', t)
assert n == 1, "shop constant not found"
for old, new in [("Fler retrotavlor i min Etsy-butik", "Fler retrotavlor i min butik"),
                 ("Se tavlorna i min Etsy-butik", "Se tavlorna i min butik"),
                 ("Till retrobutiken på Etsy", "Till retrobutiken")]:
    t = t.replace(old, new)
f.write_text(t, encoding="utf-8")
print("shop url:", URL or "(hidden)")
