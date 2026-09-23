// Checks ../green-plate-lab.html in Playwright's own Chromium: no errors or failed loads, every version's
// movement chip painted by site.css in that version's plate and deep ink, the two switches, and 2x
// screenshots of each section in /tmp/wocg-green-lab/.
//   node green-plate-lab-parts/check.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const C = require('../icon-lab-parts/colour.js');
const PAGE = 'file://' + path.join(__dirname, '..', 'green-plate-lab.html');
const OUT = '/tmp/wocg-green-lab';
const rgb = (hex) => 'rgb(' + C.hexToRgb(hex).map((v) => Math.round(v * 255)).join(', ') + ')';
const fam = (h, c) => ({ fill: C.to(0.851, c, h), deep: C.to(0.415, C.maxC(0.415, h) * 0.89, h) });
const VERSIONS = [];
[135, 131, 127].forEach((h) => [0.10, 0.13, 0.16].forEach((c) => VERSIONS.push({ h, c })));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const errors = [];
  const b = await chromium.launch();
  try {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 });
    const p = await ctx.newPage();
    p.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    p.on('pageerror', (e) => errors.push('page: ' + e.message));
    p.on('requestfailed', (r) => errors.push('load: ' + r.url() + ' ' + (r.failure() || {}).errorText));
    await p.goto(PAGE);
    await p.evaluate(() => { localStorage.clear(); });
    await p.reload();
    await p.evaluate(() => document.fonts.ready);
    const fonts = await p.evaluate(() => ['400', '700'].map((w) => document.fonts.check(w + ' 12px BuloRounded')));
    if (!fonts.every(Boolean)) errors.push('BuloRounded did not load: ' + fonts);
    const counts = await p.evaluate(() => ({ cells: document.querySelectorAll('.gp-cell').length, cards: document.querySelectorAll('#gpCards .gp-card').length, own: document.querySelectorAll('#gpOwn .gp-card').length }));
    if (counts.cells !== 9 || counts.cards !== 9 || counts.own !== 1) errors.push('counts: ' + JSON.stringify(counts));

    // the chips: site.css paints each with the version's plate and deep ink, and draws the arrow
    const chipOf = (inks) => p.evaluate(() => [...document.querySelectorAll('#gpCards .gp-card')].map((card) => {
      const up = card.querySelector('.lbUp'), cs = getComputedStyle(up), before = getComputedStyle(up, '::before');
      return { n: card.dataset.n, bg: cs.backgroundColor, ink: cs.color, radius: cs.borderRadius, arrow: before.maskImage || before.webkitMaskImage, font: cs.fontFamily };
    }));
    let chips = await chipOf();
    chips.forEach((ch, i) => {
      const f = fam(VERSIONS[i].h, VERSIONS[i].c);
      if (ch.bg !== rgb(f.fill)) errors.push('version ' + ch.n + ' chip fill ' + ch.bg + ', expected ' + rgb(f.fill));
      if (ch.ink !== rgb(f.deep)) errors.push('version ' + ch.n + ' chip ink ' + ch.ink + ', expected ' + rgb(f.deep));
      // site.css carries the arrow as the file's url or inlined as data
      if (!ch.arrow || ch.arrow === 'none') errors.push('version ' + ch.n + ' chip has no arrow');
      if (ch.radius !== '8px') errors.push('version ' + ch.n + ' chip radius ' + ch.radius);
    });
    if (chips[0].bg !== rgb('#B2DD9B')) errors.push('version 1 is not the 14 Sep plate');
    // the site's own token (site.css) is the pick, version 5
    const token = await p.evaluate(() => getComputedStyle(document.querySelector('.site.fp')).getPropertyValue('--plate-green').trim());
    if (token !== '#b0e084' || chips[4].bg !== rgb('#B0E084')) errors.push('the site token ' + token + ' is not version 5');
    // the arrow's mask file loads (a broken url fails silently in a mask)
    const arrowOk = await p.evaluate(() => new Promise((res) => { const i = new Image(); i.onload = () => res(true); i.onerror = () => res(false); i.src = 'static/images/arrowDown.svg'; }));
    if (!arrowOk) errors.push('static/images/arrowDown.svg does not load');

    await p.locator('section').nth(0).screenshot({ path: path.join(OUT, '1-grid.png') });
    await p.locator('#gpCards .gp-card').nth(0).screenshot({ path: path.join(OUT, '2-card-1.png') });
    await p.locator('#gpCards .gp-card').nth(4).screenshot({ path: path.join(OUT, '2-card-5.png') });

    // i keeps today's inks for every version
    await p.keyboard.press('i');
    chips = await chipOf();
    if (chips[8].ink !== rgb('#305812')) errors.push('i did not give the 14 Sep deep ink: ' + chips[8].ink);
    await p.locator('#gpCards .gp-card').nth(8).screenshot({ path: path.join(OUT, '2-card-9-today-inks.png') });
    await p.keyboard.press('i');
    // 2 doubles the pieces
    await p.keyboard.press('2');
    const zoom = await p.evaluate(() => getComputedStyle(document.querySelector('.gp-z')).zoom);
    if (String(zoom) !== '2') errors.push('2 did not zoom the pieces: ' + zoom);
    await p.locator('section').nth(0).screenshot({ path: path.join(OUT, '1-grid-2x.png') });
    await p.keyboard.press('2');
    // your own follows the sliders
    await p.evaluate(() => { const h = document.getElementById('gpHue'); h.value = '129'; h.dispatchEvent(new Event('input')); });
    const own = await p.evaluate(() => getComputedStyle(document.querySelector('#gpOwn .lbUp')).backgroundColor);
    if (own !== rgb(C.to(0.851, 0.1, 129))) errors.push('your own did not follow the hue slider: ' + own);
    await p.locator('section').nth(2).screenshot({ path: path.join(OUT, '3-own.png') });
    // 5: the chosen versions beside the red plate, with both inks
    const red = await p.evaluate(() => [...document.querySelectorAll('#gpRed .gp-pair')].map((row) => ({ n: row.dataset.n,
      up: getComputedStyle(row.querySelector('.lbUp')).backgroundColor, down: getComputedStyle(row.querySelector('.lbDown')).backgroundColor })));
    if (red.map((r) => r.n).join() !== '1,5,8') errors.push('section 5 rows: ' + red.map((r) => r.n));
    red.forEach((r) => {
      const v = VERSIONS[+r.n - 1];
      if (r.up !== rgb(fam(v.h, v.c).fill)) errors.push('section 5 version ' + r.n + ' up chip ' + r.up);
      if (r.down !== rgb('#FCBCB4')) errors.push('section 5 version ' + r.n + ' down chip ' + r.down);
    });
    await p.locator('section').nth(4).screenshot({ path: path.join(OUT, '5-red.png') });
    await p.keyboard.press('i');
    await p.locator('section').nth(4).screenshot({ path: path.join(OUT, '5-red-today-inks.png') });
    await p.keyboard.press('i');
  } catch (e) {
    errors.push('check: ' + e.message);
  } finally { await b.close(); }
  console.log(errors.length ? errors.join('\n') : 'no errors');
  console.log('screenshots in ' + OUT);
})();
