const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 390, height: 844 } });
  const errs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await p.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await p.goto('file:///home/claude/nostalgi-site/index.html');

  // year search
  await p.fill('#yr', '1987');
  await p.click('#go');
  await p.click('#openall');
  const sec = await p.$$eval('#out .card', cs => cs.map(c => c.querySelector('h2') ? c.querySelector('h2').textContent + ': ' + c.querySelectorAll('li').length : ''));
  console.log('sections', sec);
  await p.screenshot({ path: '/home/claude/nostalgi-build/shot-search.png', fullPage: false });

  // out-of-range year
  await p.fill('#yr', '1930'); await p.click('#go');
  console.log('range msg:', await p.textContent('#status'));

  // group quiz
  await p.fill('#grp', '1975, 1992');
  await p.click('#qgo');
  await p.waitForSelector('#rv');
  console.log('Q:', await p.textContent('#qbox p'));
  await p.click('#rv');
  console.log('A year:', await p.textContent('#ans .year'));
  await p.fill('#gs', '1980'); await p.click('#gb');
  console.log('feedback:', await p.textContent('#fb'));

  // birthday quiz, 15 questions, one milestone
  await p.fill('#bname', 'Anna');
  await p.fill('#bborn', '1976');
  await p.click('#baddm');
  await p.fill('#bmiles .ml', 'tog studenten');
  await p.fill('#bmiles .my', '1995');
  await p.selectOption('#bcount', '15');
  await p.click('#bstart');
  for (let i = 0; i < 16; i++) {
    await p.waitForFunction(() => !document.getElementById('qgo').disabled);
    if (i < 15) {
      const t = await p.textContent('#qbox');
      if (!/Vilket år/.test(t)) console.log('bday problem at', i, t.slice(0, 120));
    }
    await p.click('#qgo');
  }
  await p.waitForTimeout(300);
  console.log('end:', (await p.textContent('#qbox')).slice(0, 80));

  // poster
  await p.fill('#yr', '1987'); await p.click('#go');
  await p.fill('#pstname', 'Eric'); await p.click('#pstgo');
  await p.waitForSelector('#pstout img', { timeout: 15000 });
  const dl = p.waitForEvent('download', { timeout: 5000 }).catch(() => null);
  await p.click('#pstdl');
  const d = await dl;
  console.log('download:', d ? d.suggestedFilename() : 'none');
  await p.screenshot({ path: '/home/claude/nostalgi-build/shot-poster.png', fullPage: false, clip: undefined });

  // no horizontal scroll
  console.log('scrollW', await p.evaluate(() => document.documentElement.scrollWidth));
  console.log('errors', errs);
  await b.close();
})();
