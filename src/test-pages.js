const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ROOT = '/home/claude/nostalgi-site';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 390, height: 844 } });
  const errs = [];
  p.on('pageerror', e => errs.push(p.url() + ' pageerror: ' + e.message));
  await p.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  const files = [];
  (function walk(d) { for (const f of fs.readdirSync(d)) { const q = path.join(d, f); fs.statSync(q).isDirectory() ? walk(q) : q.endsWith('.html') && files.push(q); } })(ROOT);
  const broken = [];
  for (const f of files) {
    await p.goto('file://' + f);
    const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    const hrefs = await p.$$eval('a[href]', as => as.map(a => a.getAttribute('href')));
    for (const h of hrefs) {
      if (/^(https?:|mailto:|#)/.test(h)) continue;
      const target = h === '/' ? path.join(ROOT, 'index.html') : path.resolve(path.dirname(f), h.split('#')[0]);
      if (!fs.existsSync(target)) broken.push(path.relative(ROOT, f) + ' -> ' + h);
    }
    const words = await p.evaluate(() => (document.querySelector('main') || document.body).innerText.split(/\s+/).length);
    console.log(path.relative(ROOT, f).padEnd(28), 'width', sw, 'words', words);
  }
  await p.goto('file://' + ROOT + '/artiklar/1980-talet.html');
  await p.screenshot({ path: '/home/claude/nostalgi-build/shot-article.png' });
  await p.goto('file://' + ROOT + '/index.html');
  await p.screenshot({ path: '/home/claude/nostalgi-build/shot-home.png' });
  await p.fill('#yr', '1994'); await p.click('#go'); await p.click('#openall');
  console.log('home search sections:', await p.$$eval('#out li', l => l.length));
  console.log('broken', broken, 'errors', errs);
  await b.close();
})();
