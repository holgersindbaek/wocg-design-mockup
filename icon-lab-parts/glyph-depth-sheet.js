// Draws glyph-depth.png: the friends panel's plate buttons at real size, one row per glyph depth (23 Sep 2026).
//   node icon-lab-parts/glyph-depth-sheet.js
const fs = require('fs');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const DIR = '/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3/icon-lab-parts/';
const { squirclePath, squircleRadius } = require(DIR + 'build.js');
const C = require(DIR + 'colour.js');
const rd = (f) => fs.readFileSync(DIR + 'inline/' + f, 'utf8');
const num = (t, k) => { const m = new RegExp('\\s' + k + '="([^"]*)"').exec(t); return m ? parseFloat(m[1]) : null; };
function squircle(svg) {
  return svg.replace(/<rect\b([^>]*?)\/>/g, (m, a) => { const x = num(a, 'x') || 0, y = num(a, 'y') || 0, w = num(a, 'width'), h = num(a, 'height'), r = num(a, 'rx');
    if (!w || !h || !r || r >= Math.min(w, h) / 2 - 0.01 || w < 12) return m;
    return '<path d="' + squirclePath(x, y, w, h, squircleRadius(r, w, h), [1, 1, 1, 1]) + '"' + a.replace(/\s(?:x|y|width|height|rx|ry)="[^"]*"/g, '') + '/>'; });
}
const recolour = (svg, map) => svg.replace(/(#[0-9A-Fa-f]{6})\b/g, (h) => map[h.toUpperCase()] || h);
const plateG = { '#A9E34B': '#B2DD9B', '#66A80F': '#8CC36D' }, plateGH = { '#A9E34B': '#A7D092', '#66A80F': '#8CC36D' };
const plateB = { '#A5D8FF': '#ABD2FF', '#63B4F2': '#83B5EF' }, tray = { '#DEE2E6': '#E4DDD0', '#ADB5BD': '#C9C0AE' };
const rows = [
  ['As built (the site today)', null],
  ['Now: the plates’ text inks, L .42', { g: '#305812', b: '#124F7E', t: '#4E4D4C' }],
  ['Between, L .48', { g: '#3E6C1D', b: C.to(0.48, 0.12, 250), t: '#5E574B' }],
  ['The link inks, L .50 to .54', { g: '#468115', b: '#1971C2', t: '#67635C' }],
];
(async () => {
  const b = await chromium.launch();
  try {
    const uri = (s) => 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s);
    const img = (s, w) => '<img src="' + uri(s) + '" style="width:' + w + 'px;height:' + w + 'px;display:block">';
    let html = '';
    for (const [label, ink] of rows) {
      let cells;
      if (!ink) cells = [img(rd('message.svg'), 24), img(rd('message--hover.svg'), 24), img(rd('invite.svg'), 24), img(rd('send.svg'), 32), img(rd('friendsSearch.svg'), 24)];
      else cells = [
        img(squircle(recolour(rd('message.svg'), Object.assign({ '#5C940D': ink.g }, plateG))), 24),
        img(squircle(recolour(rd('message--hover.svg'), Object.assign({ '#4F800B': ink.g }, plateGH))), 24),
        img(squircle(recolour(rd('invite.svg'), Object.assign({ '#1971C2': ink.b }, plateB))), 24),
        img(squircle(recolour(rd('send.svg'), Object.assign({ '#1971C2': ink.b }, plateB))), 32),
        img(squircle(recolour(rd('friendsSearch.svg'), Object.assign({ '#868E96': ink.t }, tray))), 24)];
      html += '<div style="display:flex;align-items:center;gap:10px;height:44px"><div style="width:230px;font:12px Verdana;color:#333">' + label +
        (ink ? '<div style="font:10px Menlo;color:#777">' + ink.g + ' ' + ink.b + ' ' + ink.t + '</div>' : '') + '</div>' +
        '<div style="display:flex;align-items:center;gap:8px;background:#fff;padding:6px 10px;border-radius:8px;box-shadow:inset 0 0 0 1px #e6e0d6">' + cells.join('') + '</div></div>';
    }
    const p = await (await b.newContext({ viewport: { width: 480, height: 44 * rows.length + 20 }, deviceScaleFactor: 4 })).newPage();
    await p.setContent('<body style="margin:0;padding:10px;background:#F9F6F2">' + html + '</body>');
    await p.waitForTimeout(400);
    await p.screenshot({ path: DIR + 'glyph-depth.png' });
  } finally { await b.close(); }
})();
