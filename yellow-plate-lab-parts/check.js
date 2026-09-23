// Checks ../yellow-plate-lab.html in Playwright's own Chromium: no errors or failed loads, the face, every version
// drawn with its own plate, and 2x screenshots of each section in /tmp/wocg-yellow-lab/.
//   node yellow-plate-lab-parts/check.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const C = require('../icon-lab-parts/colour.js');
const PAGE = 'file://' + path.join(__dirname, '..', 'yellow-plate-lab.html');
const OUT = '/tmp/wocg-yellow-lab';
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const errors = [];
  const b = await chromium.launch();
  try {
    const p = await (await b.newContext({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 })).newPage();
    p.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    p.on('pageerror', (e) => errors.push('page: ' + e.message));
    p.on('requestfailed', (r) => errors.push('load: ' + r.url() + ' ' + (r.failure() || {}).errorText));
    await p.goto(PAGE);
    await p.evaluate(() => localStorage.clear());
    await p.reload();
    await p.evaluate(() => document.fonts.ready);
    const fonts = await p.evaluate(() => ['400', '700'].map((w) => document.fonts.check(w + ' 12px BuloRounded')));
    if (!fonts.every(Boolean)) errors.push('BuloRounded did not load: ' + fonts);
    const n = await p.evaluate(() => ({ cells: document.querySelectorAll('.yp-cell').length, cards: document.querySelectorAll('#ypCards .yp-card').length, own: document.querySelectorAll('#ypOwn .yp-card').length }));
    if (n.cells !== 9 || n.cards !== 9 || n.own !== 1) errors.push('drawn: ' + JSON.stringify(n));
    // each card's plate chip wears its own version's fill, and version 1 is today's plate
    const fills = await p.evaluate(() => [...document.querySelectorAll('#ypCards .yp-card')].map((c) => getComputedStyle(c.querySelectorAll('.yp-chip')[1]).backgroundColor));
    const want = [92.2, 96, 100].flatMap((h) => [0.12, 0.135, 0.15].map((c) => C.to(0.88, c, h)));
    const rgb = (x) => 'rgb(' + C.hexToRgb(x).map((v) => Math.round(v * 255)).join(', ') + ')';
    fills.forEach((f, i) => { if (f !== rgb(want[i])) errors.push('version ' + (i + 1) + ' plate ' + f + ', expected ' + rgb(want[i])); });
    if (want[0] !== '#F4D576') errors.push('version 1 is not today\'s plate: ' + want[0]);
    await p.locator('section').nth(0).screenshot({ path: path.join(OUT, '1-grid.png') });
    await p.locator('#ypCards .yp-card').nth(0).screenshot({ path: path.join(OUT, '2-card-1.png') });
    await p.locator('#ypCards .yp-card').nth(4).screenshot({ path: path.join(OUT, '2-card-5.png') });
  } catch (e) {
    errors.push('check: ' + e.message);
  } finally { await b.close(); }
  console.log(errors.length ? errors.join('\n') : 'no errors');
  console.log('screenshots in ' + OUT);
})();
