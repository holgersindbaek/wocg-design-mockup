// Checks the built icon lab and the art it draws.
//
//   node icon-lab-parts/check.js            the page: errors, broken images, Lottie players, screenshots
//   node icon-lab-parts/check.js --png      every shipped PNG against the vector the lab draws for it
//
// Uses Playwright's own Chromium (never the system Chrome), opened on the page from disk, the way
// Holger opens it. Screenshots go to /tmp/wocg-icon-lab/.
const fs = require('fs');
const path = require('path');
const PW = '/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright';
const { chromium } = require(PW);

const HERE = __dirname;
const ROOT = path.join(HERE, '..');
const OUT = '/tmp/wocg-icon-lab';
fs.mkdirSync(OUT, { recursive: true });

async function checkPng(browser) {
  const inv = require('./inventory.js');
  const pairs = [];
  inv.categories.forEach((c) => c.icons.forEach((ic) => ic.states.forEach((st) => {
    if (!st.file || !/\.png$/.test(st.file)) return;
    const vec = path.join(HERE, 'sketch', st.vector || st.file.replace(/\.png$/, '.svg'));
    if (!fs.existsSync(vec)) { console.log('no vector ' + (ic.id + '/' + st.key).padEnd(34) + ' the page draws the PNG and cannot recolour it'); return; }
    pairs.push({ id: ic.id + '/' + st.key, png: 'data:image/png;base64,' + fs.readFileSync(path.join(ROOT, 'static/images', st.file)).toString('base64'),
      svg: 'data:image/svg+xml;base64,' + fs.readFileSync(vec).toString('base64') });
  })));
  const page = await browser.newPage();
  await page.setContent('<html><body></body></html>');
  const res = await page.evaluate(async (pairs) => {
    const load = (src) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error('load')); i.src = src; });
    const px = (img, w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); x.drawImage(img, 0, 0, w, h); return x.getImageData(0, 0, w, h).data; };
    const out = [];
    for (const p of pairs) {
      const a0 = await load(p.png), w = a0.naturalWidth, h = a0.naturalHeight, a = px(a0, w, h), b = px(await load(p.svg), w, h);
      let sum = 0, n = 0;
      for (let i = 0; i < a.length; i += 4) { const aa = a[i + 3] / 255, ba = b[i + 3] / 255; if (aa < .02 && ba < .02) continue; n++;
        let d = 0; for (let k = 0; k < 3; k++) d += Math.abs(a[i + k] * aa - b[i + k] * ba); sum += (d + Math.abs(a[i + 3] - b[i + 3])) / 4; }
      out.push({ id: p.id, mean: +(sum / Math.max(1, n)).toFixed(1) });
    }
    return out;
  }, pairs);
  res.forEach((r) => console.log((r.mean <= 3 ? 'same  ' : r.mean <= 10 ? 'close ' : 'DIFF  ') + r.id.padEnd(34) + ' mean difference ' + r.mean + ' of 255'));
}

async function checkPage(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1480, height: 1000 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto('file://' + path.join(ROOT, 'icon-lab.html'));
  // the overview first, with the details closed as a visitor finds them
  await page.evaluate(() => { localStorage.removeItem('wocgIconLab'); localStorage.removeItem('wocgIconLabScratch'); });
  await page.reload();
  await page.waitForTimeout(1200);
  const ov = await page.evaluate(() => ({ rows: document.querySelectorAll('.ovlabel').length, cells: document.querySelectorAll('.ovcell img').length,
    broken: [...document.querySelectorAll('.ovcell img')].filter((i) => !i.naturalWidth).length, detailsOpen: document.getElementById('details').open }));
  console.log('overview:', JSON.stringify(ov));
  await page.locator('#overview').screenshot({ path: path.join(OUT, 'overview.png') });
  // then the details, open
  await page.evaluate(() => localStorage.setItem('wocgIconLab', JSON.stringify({ details: true })));
  await page.reload();
  await page.waitForTimeout(1500);
  const facts = await page.evaluate(() => {
    const imgs = [...document.querySelectorAll('#main img')];
    const broken = imgs.filter((i) => !i.complete || i.naturalWidth === 0).length;
    const lots = [...document.querySelectorAll('.lot')];
    const drawn = lots.filter((l) => l.querySelector('svg')).length;
    const fonts = [...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family + ' ' + f.weight);
    return { cards: document.querySelectorAll('.icard').length, imgs: imgs.length, broken, lottie: lots.length, lottieDrawn: drawn,
      swatches: document.querySelectorAll('.pc').length, sections: [...document.querySelectorAll('section.sec')].map((s) => s.id), fonts: [...new Set(fonts)] };
  });
  console.log(JSON.stringify(facts, null, 1));
  // a scratch change must reach the palette, the cards and the bar
  const scratch = await page.evaluate(() => {
    localStorage.setItem('wocgIconLabScratch', JSON.stringify({ global: { '#212529': '#4E4D4C' }, icon: {}, state: {} }));
    localStorage.setItem('wocgIconLab', JSON.stringify({ ver: 'scratch', compare: true, nums: false, felt: 'green-felt.jpg', details: true }));
    return true;
  });
  await page.reload(); await page.waitForTimeout(1200);
  const after = await page.evaluate(() => ({ split: document.querySelectorAll('.pc .sw b').length, changedChips: document.querySelectorAll('.chip.changed').length,
    bar: document.querySelector('#bar .count') && document.querySelector('#bar .count').textContent, rows: document.querySelectorAll('.srow').length }));
  console.log('scratch:', JSON.stringify(after));
  await page.evaluate(() => { localStorage.removeItem('wocgIconLabScratch'); localStorage.setItem('wocgIconLab', JSON.stringify({ details: true })); });
  await page.reload(); await page.waitForTimeout(1500);
  const secs = await page.evaluate(() => [...document.querySelectorAll('section.sec')].map((s) => { const r = s.getBoundingClientRect(); return { id: s.id, y: r.top + scrollY, h: r.height }; }));
  const full = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.setViewportSize({ width: 1480, height: Math.min(full, 30000) });
  await page.waitForTimeout(800);
  for (const s of secs) {
    const h = Math.min(s.h, 7000);
    await page.screenshot({ path: path.join(OUT, s.id + '.png'), clip: { x: 0, y: s.y, width: 1480, height: h } });
  }
  await page.evaluate(() => { localStorage.removeItem('wocgIconLab'); localStorage.removeItem('wocgIconLabScratch'); });
  console.log('screenshots in', OUT, '(' + secs.length + ' sections and the overview)');
  console.log(errors.length ? 'ERRORS:\n  ' + errors.join('\n  ') : 'no errors');
  await ctx.close();
}

(async () => {
  const browser = await chromium.launch();
  try {
    if (process.argv.includes('--png')) await checkPng(browser); else await checkPage(browser);
  } finally { await browser.close(); }
})();
