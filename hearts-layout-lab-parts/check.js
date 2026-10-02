// Opens the lab in Playwright's own Chromium (never the system Chrome), reads the measured strips for every state and
// ad setting, and shoots each phone at 100% for a look. node hearts-layout-lab-parts/check.js [--shots]
const path = require('path');
const fs = require('fs');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const HERE = __dirname, LAB = path.join(HERE, '..', 'hearts-layout-lab.html'), OUT = path.join(HERE, 'measure');
const SHOTS = process.argv.includes('--shots');
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1500, height: 1000 }, deviceScaleFactor: 2 });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    await page.goto('file://' + LAB, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(800);
    const click = async (id, v) => { await page.click('#' + id + ' label[data-v="' + v + '"]'); await page.waitForTimeout(250); };
    const readSummary = () => page.evaluate(() => [...document.querySelectorAll('#summary tr')].map((tr) => [...tr.children].map((td) => td.textContent).join(' | ')).join('\n'));
    const broken = await page.evaluate(() => [...document.images].filter((i) => i.loading !== 'lazy' && (!i.complete || !i.naturalWidth)).map((i) => i.getAttribute('src')));
    console.log('broken images:', broken.length ? broken.slice(0, 10) : 'none');
    for (const ads of ['today', 'none']) {
      await click('ads', ads);
      for (const st of ['pass', 'play', 'wait', 'tram', 'full']) {
        await click('state', st);
        console.log('\n== ads ' + ads + ' · state ' + st + '\n' + await readSummary());
      }
    }
    await click('ads', 'today'); await click('state', 'full');
    // the 4 cards state: per version the trick's size and place, its smallest clearance to any drawn box (16 wanted) and
    // the smallest gap between its cards (8 wanted)
    const clearance = () => page.evaluate(() => {
      const out = [];
      document.querySelectorAll('.version.on').forEach((v) => {
        const tbl = v.querySelector('.phone > .screen > .tbl'), tr = tbl.getBoundingClientRect(), zoom = tr.width / 393;
        const rect = (el) => { const r = el.getBoundingClientRect(); const b = [(r.left - tr.left) / zoom, (r.top - tr.top) / zoom, (r.right - tr.left) / zoom, (r.bottom - tr.top) / zoom]; return el.classList.contains('av') ? window.hlVisibleBox(el, b) : b; }; // an avatar counts by its visible art, as the fitter does
        const gap = (a, b) => Math.max(Math.max(b[0] - a[2], a[0] - b[2]), Math.max(b[1] - a[3], a[1] - b[3]));
        const tricks = [...tbl.querySelectorAll('.card.trick')].map(rect);
        const others = [...tbl.querySelectorAll('[data-m]')].filter((el) => !el.classList.contains('trick'));
        let min = Infinity, what = '';
        tricks.forEach((t) => others.forEach((el) => { const r = rect(el); if (!(r[2] > r[0] && r[3] > r[1])) return; const g = gap(t, r); if (g < min) { min = g; what = el.className.split(' ').slice(0, 2).join('.'); } }));
        const between = []; for (let i = 0; i < tricks.length; i++) for (let j = i + 1; j < tricks.length; j++) between.push(gap(tricks[i], tricks[j]));
        const xs = tricks.map((t) => (t[0] + t[2]) / 2), ys = tricks.map((t) => (t[1] + t[3]) / 2), c = tricks[0];
        out.push([v.querySelector('h2').firstChild.textContent.trim(), c ? Math.round(c[2] - c[0]) + ' × ' + Math.round(c[3] - c[1]) : '–', ((Math.min(...xs) + Math.max(...xs)) / 2).toFixed(1), ((Math.min(...ys) + Math.max(...ys)) / 2).toFixed(1), min.toFixed(1), what, Math.min(...between).toFixed(1)].join(' | '));
      });
      return out.join('\n');
    });
    for (const seats of ['bots', 'people']) {
      await click('seats', seats);
      console.log('\n== trick clearance · ' + seats + ' · 4 cards\nVersion | Trick card | cx | cy | Clearance | To | Between\n' + await clearance());
    }
    await click('seats', 'bots');
    if (SHOTS) {
      await click('scale', '100');
      for (const seats of ['bots', 'people']) {
        await click('seats', seats);
        for (const st of (seats === 'bots' ? ['pass', 'full'] : ['wait', 'tram'])) {
          await click('state', st);
          await page.waitForTimeout(1000); // the state's card faces load on first use; the first phone's shot must not race them
          const phones = await page.$$('.version.on .phone'), ids = await page.$$eval('.version.on', (els) => els.map((e) => e.id));
          for (let i = 0; i < phones.length; i++) {
            await phones[i].scrollIntoViewIfNeeded();
            if (i === 0) { await phones[0].screenshot(); await page.waitForTimeout(300); } // the first shot after a re-render can catch the paint half done; warm up
            await phones[i].screenshot({ path: path.join(OUT, 'lab-' + ids[i] + '-' + seats + '-' + st + '.png') });
          }
        }
      }
      await click('seats', 'bots'); await click('state', 'full');
      await page.keyboard.down('t');
      const ph = await page.$$('.version.on .phone');
      const ovIds = await page.$$eval('.version.on', (els) => els.map((e) => e.id));
      for (const id of ['v12', 'v15']) { const i = ovIds.indexOf(id); if (i >= 0) { await ph[i].scrollIntoViewIfNeeded(); await ph[i].screenshot({ path: path.join(OUT, 'lab-ovl-' + id + '.png') }); } }
      await page.keyboard.up('t');
      await click('scale', '78');
      await page.setViewportSize({ width: 5200, height: 1120 });
      await page.evaluate(() => { document.querySelector('#row').scrollIntoView(); });
      await page.waitForTimeout(400);
      const rowEl = await page.$('#row');
      await rowEl.screenshot({ path: path.join(OUT, 'lab-row.png') });
      await page.setViewportSize({ width: 1500, height: 1000 });
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: path.join(OUT, 'lab-top.png'), fullPage: false });
    }
    console.log('\npage errors:', errors.length ? errors : 'none');
  } finally { await browser.close(); }
})().catch((e) => { console.error(e); process.exit(1); });
