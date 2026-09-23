// Checks ../turn-timer-lab.html in Playwright's own Chromium: no errors, the fonts, every version drawn, the
// live countdown ticking into the red, and 2x screenshots in /tmp/wocg-timer-lab/.
//   node turn-timer-lab-parts/check.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const PAGE = 'file://' + path.join(__dirname, '..', 'turn-timer-lab.html');
const OUT = '/tmp/wocg-timer-lab';
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const errors = [];
  const b = await chromium.launch();
  try {
    const p = await (await b.newContext({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 2 })).newPage();
    p.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
    p.on('pageerror', (e) => errors.push('page: ' + e.message));
    p.on('requestfailed', (r) => errors.push('load: ' + r.url() + ' ' + (r.failure() || {}).errorText));
    await p.goto(PAGE);
    await p.evaluate(() => document.fonts.ready);
    const fonts = await p.evaluate(() => ['400', '700'].map((w) => document.fonts.check(w + ' 18px BuloRounded')));
    if (!fonts.every(Boolean)) errors.push('BuloRounded did not load: ' + fonts);
    const n = await p.evaluate(() => ({ cards: document.querySelectorAll('.tt-card').length, timers: document.querySelectorAll('.tt-card svg').length }));
    if (n.cards !== 4 || n.timers !== 16) errors.push('drawn: ' + JSON.stringify(n));
    await p.locator('section').nth(0).screenshot({ path: path.join(OUT, '1-versions.png') });
    // the live timer: tick eight times, from 12 down to 4, which is red
    await p.evaluate(() => { for (let i = 0; i < 8; i++) window.ttTick(); });
    await p.waitForTimeout(700);
    const live = await p.evaluate(() => [...document.querySelectorAll('.tt-live')].map((l) => ({ n: l.querySelector('.tt-ink').textContent, arc: getComputedStyle(l.querySelector('.tt-arc')).stroke })));
    if (!live.every((x) => x.n === '4')) errors.push('the live timers did not tick: ' + JSON.stringify(live));
    if (live[1].arc !== 'rgb(201, 42, 42)') errors.push('the live timer is not red at 4 s: ' + live[1].arc);
    await p.keyboard.press('2');
    await p.locator('section').nth(0).screenshot({ path: path.join(OUT, '1-versions-2x.png') });
  } catch (e) {
    errors.push('check: ' + e.message);
  } finally { await b.close(); }
  console.log(errors.length ? errors.join('\n') : 'no errors');
  console.log('screenshots in ' + OUT);
})();
