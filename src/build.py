import json, re, sys, pathlib

SRC = pathlib.Path(sys.argv[1])
DATA = pathlib.Path(sys.argv[2])
OUT = pathlib.Path(sys.argv[3])

# ---- parse data ----
data = {}
cur = None
keymap = {"m": "musik", "i": "idrottare", "h": "handelser", "k": "konstigt"}
for line in DATA.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    if line.startswith("@"):
        cur = int(line[1:]); data[cur] = {}
        continue
    k, v = line.split(":", 1)
    data[cur][keymap[k.strip()]] = [x.strip() for x in v.split("|") if x.strip()]

html = SRC.read_text(encoding="utf-8")

# ---- strip the artifact wrapper ----
start = html.index("<!DOCTYPE html>")
html = html[start:]
end = html.index("</html>") + len("</html>")
html = html[:end] + "\n"

def rep(old, new, count=1):
    global html
    n = html.count(old)
    assert n == count, (old[:60], n)
    html = html.replace(old, new)

def rep_between(a, b, new):
    """Replace text from marker a (inclusive) up to marker b (exclusive)."""
    global html
    i = html.index(a); j = html.index(b, i)
    html = html[:i] + new + html[j:]

# ---- head: description ----
rep('<title>Året du föddes</title>',
    '<title>Året du föddes · nostalgi.me</title>\n'
    '<meta name="description" content="Skriv ditt födelseår och se musik, idrott, händelser, priser och kuriosa från året. Med födelsedagsquiz och retroposter.">\n'
    '<meta property="og:title" content="Året du föddes · nostalgi.me">\n'
    '<meta property="og:description" content="Musik, händelser, priser och quiz för året du föddes.">\n'
    '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 106%22%3E%3Cpath d=%22M10 100 A90 90 0 0 1 190 100 Z%22 fill=%22%23c8563f%22/%3E%3Cpath d=%22M50 100 A50 50 0 0 1 150 100 Z%22 fill=%22%23f2c66e%22/%3E%3C/svg%3E">')

# ---- year limits ----
FIRST, LAST = min(data), max(data)
rep('min="1900" max="2025"', f'min="{FIRST}" max="{LAST}"')
rep('if (!y || y < 1900 || y > 2025) { $("status").textContent = "Skriv ett årtal mellan 1900 och 2025."; return; }',
    f'if (!y || y < {FIRST} || y > {LAST}) {{ $("status").textContent = "Skriv ett årtal mellan {FIRST} och {LAST}."; return; }}')
rep('filter(n => n >= 1900 && n <= 2025)', f'filter(n => n >= {FIRST} && n <= {LAST})')
rep('if (!(born >= 1900 && born <= 2025)) { $("bmsg").textContent = "Fyll i vilket år " + name + " föddes (mellan 1900 och 2025)."; return; }',
    f'if (!(born >= {FIRST} && born <= {LAST})) {{ $("bmsg").textContent = "Fyll i vilket år " + name + " föddes (mellan {FIRST} och {LAST})."; return; }}')
rep('if (yy >= 1900 && yy <= 2025) near.push', 'if (DATA[yy]) near.push')
rep('.filter(it => it.label && it.year >= 1900 && it.year <= 2025)', '.filter(it => it.label && DATA[it.year])')
rep('<p class="sub" style="margin:4px 0 6px">Andra händelser i livet, blir bonusfrågor (valfritt):</p>',
    f'<p class="sub" style="margin:4px 0 6px">Andra händelser i livet, blir bonusfrågor (valfritt, år {FIRST}–{LAST}):</p>')

# ---- sections: only what the static data covers ----
rep_between('const sections = [', '\n];', 'const sections = [\n'
    '  ["musik","Musik och låtar"],\n'
    '  ["idrottare","Stora idrottsögonblick"],\n'
    '  ["handelser","Historiska händelser"],\n'
    '  ["konstigt","Kuriosa och udda nyheter"]')
rep('Skriv ett årtal och öppna en ruta i taget: pengarnas värde, villapriser, musik, idrottare, händelser och lite konstigheter.',
    'Skriv ett årtal och öppna en ruta i taget: pengarnas värde, villapriser, musik, idrott, händelser och lite kuriosa.')

# ---- remove the AI runtime ----
rep_between('let sampleP = null;', 'function errMsg(',
    'const DATA = ' + json.dumps({str(k): v for k, v in data.items()}, ensure_ascii=False, separators=(",", ":")) + ';\n'
    'async function ensureAI(){ return true; }\n\n')

rep_between('function fetchYear(y){', 'function fetchSec(){',
    'function fetchYear(y){\n'
    '  if (run && run.y === y) return Promise.resolve();\n'
    '  run = { y, done: true, err: null };\n'
    '  const d = DATA[y] || {};\n'
    '  sections.forEach(([k]) => { if (d[k] && d[k].length) cache[k] = { text: d[k].join("\\n"), done: true }; });\n'
    '  renderAll();\n'
    '  return Promise.resolve();\n'
    '}\n')
rep('(run && run.done ? "Inget svar för den här rutan. Tryck på Sök igen." : "Laddar …")',
    '"Inga uppgifter för det här året ännu."')

rep_between('async function makeQuestion(y, ctx){', 'let cur = null, nextQ',
    'async function makeQuestion(y, ctx){\n'
    '  const d = DATA[y];\n'
    '  if (!d) throw { code: "nodata" };\n'
    '  const all = [...(d.handelser || []), ...(d.idrottare || []), ...(d.konstigt || [])];\n'
    '  if (!all.length) throw { code: "nodata" };\n'
    '  const used = new Set([...askedFor(y), ...(sessionAsked[y] || [])]);\n'
    '  let pool = all.filter(t => !used.has(t.slice(0, 90)));\n'
    '  if (!pool.length) { pool = all; sessionAsked[y] = []; try { const a = JSON.parse(localStorage.getItem("nostalgi_asked") || "{}"); delete a[y]; localStorage.setItem("nostalgi_asked", JSON.stringify(a)); } catch (e) {} }\n'
    '  const item = pool[Math.floor(Math.random() * pool.length)];\n'
    '  (sessionAsked[y] = sessionAsked[y] || []).push(item.slice(0, 90));\n'
    '  rememberAsked(y, item);\n'
    '  const fraga = item.replace(/[.!]?$/, ".") + " Vilket år hände detta?";\n'
    '  return { y, d: { fraga, datum: "", forklaring: "" }, ctx };\n'
    '}\n\n')
rep('const THEMES = ["sport", "musik", "film och tv", "teknik och prylar", "mode och trender", "mat och dryck", "vetenskap och rymden", "politik och samhälle", "kuriosa och udda nyheter", "något som hände i Sverige", "leksaker, spel och fritid", "kungligheter och kändisar"];\n', '')
rep('if (!yrs.length) return 1950 + Math.floor(Math.random()*75);',
    'if (!yrs.length) { const ks = Object.keys(DATA); return +ks[Math.floor(Math.random() * ks.length)]; }')
rep('$("qbox").innerHTML = \'<p class="sub" style="margin:10px 0 0">Hittar på en fråga …</p>\';',
    '$("qbox").innerHTML = \'<p class="sub" style="margin:10px 0 0">Hämtar en fråga …</p>\';', 2)
rep('((e && e.code === "unavailable") ? "AI-funktionen är inte tillgänglig här." : errMsg(e, "Ny fråga"))',
    '((e && e.code === "nodata") ? "Det finns inga frågor för de årtalen ännu. Prova andra år." : errMsg(e, "Ny fråga"))')
rep('((e && e.code === "unavailable") ? "AI-funktionen är inte tillgänglig här." : errMsg(e, "Nästa fråga"))',
    '((e && e.code === "nodata") ? "Det finns inga frågor för det året ännu. Tryck på Nästa fråga." : errMsg(e, "Nästa fråga"))')
# a missing year in the birthday queue should be skipped, not stall the quiz
rep('    if (!q) q = await makeQuestion(ctx.year, ctx);\n    if (bday !== b) return;',
    '    if (!q) q = await makeQuestion(ctx.year, ctx);\n    if (bday !== b) return;')

# ---- poster download without the claude runtime ----
rep_between('      try {\n        const dl = await claude.use("downloads");', '    });\n  } catch (e) {',
    '      try {\n'
    '        const blob = await new Promise(r => c.toBlob(r, "image/png"));\n'
    '        const a = document.createElement("a");\n'
    '        a.href = URL.createObjectURL(blob);\n'
    '        a.download = "nostalgi-" + y + (name ? "-" + name.toLowerCase().replace(/[^a-z0-9åäö]+/gi, "-") : "") + ".png";\n'
    '        document.body.appendChild(a); a.click(); a.remove();\n'
    '        setTimeout(() => URL.revokeObjectURL(a.href), 4000);\n'
    '        msg.textContent = "Klart! Hittar du inte filen: håll fingret på bilden och välj Spara bild.";\n'
    '      } catch (e) {\n'
    '        msg.textContent = "Det gick inte att ladda ner. Håll fingret på bilden och välj Spara bild.";\n'
    '      }\n')
rep('$("pststatus").textContent = "Samlar ihop året …";\n    if (await ensureAI()) { try { await fetchYear(y); } catch (e) {} }',
    '$("pststatus").textContent = "Samlar ihop året …";\n    await fetchYear(y);')
rep('  ensureAI().then(ok => { if (ok && year === y) prefetchAll(y); });\n', '  prefetchAll(y);\n')

assert "claude." not in html, "runtime call left"
assert "sample(" not in html
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print("years", FIRST, LAST, len(data), "bytes", len(html.encode()))
