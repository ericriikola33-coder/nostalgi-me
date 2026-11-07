# nostalgi.me

Retrohörnet på nätet: året du föddes, quiz och artiklar om förr.

- `site/` – den publicerade sajten (Cloudflare Pages, output directory `site`, inget byggkommando).
- `src/` – källfiler: årsfakta (`data.txt`), artiklar (`pages/content`), byggskript.

Bygga om sajten:

```
python3 -I src/build.py src/original-index.html src/data.txt site/index.html
python3 -I src/pages/gen.py src/pages site
python3 -I src/adsense.py site 9723217552460349
python3 -I src/goatcounter.py site nostalgime
python3 -I src/shop.py site "https://riikola.gumroad.com/"   # tomt = dold
```

## Publicering

Varje push till `main` publicerar mappen `site/` till Cloudflare Pages-projektet `nostalgi`
(nostalgi.me) via GitHub Actions (`.github/workflows/deploy.yml`). Nyckeln ligger som
repository secret `CLOUDFLARE_API_TOKEN`.
