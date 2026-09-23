// Draws all-versions.png: close-ups of the Hearts table's main icons in every version, one row per
// version in the switcher's order and numbered as the switcher numbers them, sharp on a retina screen.
// Run it after the build. Give the switcher's numbers to draw only those versions, into
// versions-<numbers>.png:
//
//   node icon-lab-parts/versions-sheet.js
//   node icon-lab-parts/versions-sheet.js 7 9 10 11 12
//
// Each crop is taken at six device pixels to a table pixel and drawn three times its size on a sheet
// rendered at two device pixels to a CSS pixel, so no pixel is scaled. Uses Playwright's own Chromium,
// never the system Chrome.
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const versions = require('./versions.js');

const VIEWER = pathToFileURL(path.join(__dirname, '..', 'icon-lab-table.html')).href;
const ONLY = process.argv.slice(2).map(Number);
const OUT = path.join(__dirname, ONLY.length ? 'versions-' + ONLY.join('-') + '.png' : 'all-versions.png');
const K = 3, DPR = 2;
// [name, x, y, width, height] in the 1440 by 900 table
const REGIONS = [['bell', 968, 16, 40, 40], ['friends', 1008, 16, 40, 40], ['info', 56, 16, 40, 40], ['hint', 303, 843, 42, 42],
  ['chat', 759, 843, 42, 42], ['crown', 28, 394, 34, 28], ['star', 364, 46, 32, 28], ['door', 1042, 394, 36, 28]];
const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;');

(async () => {
  const all = [{ id: 'built', title: 'As built' }].concat(versions).map((v, i) => Object.assign({ n: i + 1 }, v));
  const pick = ONLY.length ? all.filter((v) => ONLY.includes(v.n)) : all;
  if (pick.length !== (ONLY.length || all.length)) throw new Error('no version numbered ' + ONLY.filter((n) => !all.some((v) => v.n === n)).join(', '));
  const browser = await chromium.launch();
  try {
    const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: K * DPR })).newPage();
    const rows = [];
    for (const v of pick) {
      await page.goto(VIEWER + '#v=' + v.id);
      await page.waitForTimeout(1500);
      await page.addStyleTag({ content: '#corner, #toast { display: none !important; }' });
      const cells = [];
      for (const [, x, y, width, height] of REGIONS) {
        const png = await page.screenshot({ clip: { x, y, width, height } });
        cells.push('<img src="data:image/png;base64,' + png.toString('base64') + '" style="width:' + width * K + 'px;height:' + height * K + 'px">');
      }
      rows.push('<div class="row"><div class="name"><b>' + v.n + '</b>' + esc(v.title) + '</div>' + cells.join('') + '</div>');
    }
    const html = '<style>body{margin:0;padding:16px 20px;background:#2a2a2a;color:#eee;font:15px/19px Verdana,sans-serif}' +
      '.row{display:flex;gap:12px;align-items:center;margin:0 0 12px}.head{display:flex;gap:12px;margin:0 0 8px;color:#bbb}' +
      '.name{width:190px;flex:none;display:flex}.name b{flex:none;width:26px;color:#fff}</style>' +
      '<div class="head"><div class="name"></div>' + REGIONS.map(([n, , , w]) => '<div style="width:' + w * K + 'px">' + n + '</div>').join('') + '</div>' +
      rows.join('');
    const sheet = await (await browser.newContext({ viewport: { width: 1300, height: 400 }, deviceScaleFactor: DPR })).newPage();
    await sheet.setContent(html);
    await sheet.waitForTimeout(300);
    await sheet.screenshot({ path: OUT, fullPage: true });
    console.log('saved', OUT, pick.length, 'versions');
  } finally { await browser.close(); }
})().catch((e) => { console.error(e); process.exit(1); });
