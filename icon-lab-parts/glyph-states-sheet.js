// Draws glyph-states.png: the light plate buttons in every state, and the canasta tabs, once per glyph ink
// (23 Sep 2026). The follow-up to glyph-depth.png: row 4 there (the link inks) also darkens the plate under
// the pointer, and the message glyph drops to 2.74:1 on the green hover. Each cell prints glyph:fill.
// Holger picked the last button row and the last canasta row (23 Sep 2026). Each row names its own ink, so
// the sheet stays true when version 13 moves.
//   node icon-lab-parts/glyph-states-sheet.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const HERE = __dirname, ROOT = path.join(HERE, '..');
const { squirclePath, squircleRadius } = require('./build.js');
const C = require('./colour.js');
const V13 = require('./versions-made.js').find((v) => v.id === 'schemeinks');
const rd = (f) => fs.readFileSync(path.join(HERE, 'inline', f), 'utf8');
const num = (t, k) => { const m = new RegExp('\\s' + k + '="([^"]*)"').exec(t); return m ? parseFloat(m[1]) : null; };
function squircle(svg) {
  return svg.replace(/<rect\b([^>]*?)\/>/g, (m, a) => { const x = num(a, 'x') || 0, y = num(a, 'y') || 0, w = num(a, 'width'), h = num(a, 'height'), r = num(a, 'rx');
    if (!w || !h || !r || r >= Math.min(w, h) / 2 - 0.01 || w < 12) return m;
    return '<path d="' + squirclePath(x, y, w, h, squircleRadius(r, w, h), [1, 1, 1, 1]) + '"' + a.replace(/\s(?:x|y|width|height|rx|ry)="[^"]*"/g, '') + '/>'; });
}
const recolour = (svg, map) => svg.replace(/(#[0-9A-Fa-f]{6})\b/g, (h) => map[h.toUpperCase()] || h);

// the buttons: file, version 13's state, the glyph's hex as built, the ink family, and whether it is a hover
const BTN = [
  ['Message', 'message.svg', 'friendMessage/rest', '#5C940D', 'g', 0, 24],
  ['hover', 'message--hover.svg', 'friendMessage/hover', '#4F800B', 'g', 1, 24],
  ['Invite', 'invite.svg', 'friendInvite/rest', '#1971C2', 'b', 0, 24],
  ['hover', 'invite--hover.svg', 'friendInvite/hover', '#1665AD', 'b', 1, 24],
  ['sent', 'invite--sent.svg', 'friendInvite/sent', '#868E96', 't', 0, 24],
  ['Send', 'send.svg', 'send/rest', '#1971C2', 'b', 0, 32],
  ['hover', 'send--hover.svg', 'send/hover', '#1665AD', 'b', 1, 32],
  ['off', 'send--off.svg', 'send/off', '#868E96', 't', 0, 32],
  ['Search', 'friendsSearch.svg', 'friendSearch/rest', '#868E96', 't', 0, 24],
  ['hover', 'friendsSearch--hover.svg', 'friendSearch/hover', '#495057', 't', 1, 24],
];
const DEEP = { g: '#305812', b: '#124F7E', t: '#4E4D4C' }, LINK = { g: '#468115', b: '#1971C2', t: '#67635C' };
const ROWS = [
  ['As built (the site today)', null],
  ['The deep inks (version 13 until 23 Sep)', (fam) => DEEP[fam]],
  ['Row 4 as drawn: the link inks, also under the pointer', (fam) => LINK[fam]],
  ['Row 4, and the deep ink under the pointer (picked)', (fam, hover) => (hover ? DEEP : LINK)[fam]],
];
// the canasta tabs: a meld's count and a complete canasta's star share one tab and one ink on the site
// (spot-cardText and .canastaCompleteStarPath, pieces.scss:1846-1965)
const TAB = { natural: ['#B2DD9B', '#305812', '#468115'], mixed: ['#F4D576', '#664411', '#94651E'] };
const TAB_ROWS = [['The star in the count’s deep ink (version 13 until 23 Sep)', 1], ['The star in the link ink, the count in the deep ink (picked)', 2]];
const tabPath = (fill, ink, n) => '<svg width="26" height="18" viewBox="0 0 26 18"><path d="M0 0H26V10A8 8 0 0 1 18 18H8A8 8 0 0 1 0 10Z" fill="' + fill + '"/>' +
  '<path d="M.5 .5H25.5V10A7.5 7.5 0 0 1 18 17.5H8A7.5 7.5 0 0 1 .5 10Z" fill="none" stroke="#252525"/>' +
  '<text x="13" y="13.2" text-anchor="middle" font-family="BuloRounded" font-weight="700" font-size="12" fill="' + ink + '">' + n + '</text></svg>';

(async () => {
  const uri = (s) => 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s);
  const cell = (svg, w, ratio, head) => '<div class="c"><div class="h">' + head + '</div><div class="i" style="height:32px"><img src="' + uri(svg) + '" style="width:' + w + 'px;height:' + w + 'px"></div>' +
    '<div class="n' + (ratio < 3 ? ' bad' : '') + '">' + ratio.toFixed(2) + '</div></div>';
  let html = '';
  for (const [label, pick] of ROWS) {
    const cells = BTN.map(([head, file, state, glyph, fam, hover, w]) => {
      let svg = rd(file), map = {};
      if (pick) {
        map = Object.assign({}, V13.state[state]);
        const ink = pick(fam, hover);
        if (ink) map[glyph] = ink;
        svg = squircle(recolour(svg, map));
      }
      const src = /<rect\b[^>]*fill="(#[0-9A-Fa-f]{6})"/.exec(rd(file));
      const fill = map[src[1].toUpperCase()] || src[1];
      return cell(svg, w, C.contrast(map[glyph] || glyph, fill), head);
    });
    html += '<div class="row"><div class="l">' + label + '</div><div class="card">' + cells.join('') + '</div></div>';
  }
  html += '<div class="gap"></div>';
  for (const [label, k] of TAB_ROWS) {
    const cells = [];
    for (const kind of ['natural', 'mixed']) {
      const [fill, deep] = TAB[kind], star = TAB[kind][k];
      const base = rd(kind === 'natural' ? 'canastaStar.svg' : 'canastaStar--mixed.svg');
      const map = Object.assign({}, V13.state['canastaStar/' + kind]);
      map[kind === 'natural' ? '#4F800B' : '#C96800'] = star;
      cells.push('<div class="c"><div class="h">count</div><div class="i">' + tabPath(fill, deep, kind === 'natural' ? 6 : 5) + '</div><div class="n">' + C.contrast(deep, fill).toFixed(2) + '</div></div>');
      cells.push('<div class="c"><div class="h">canasta</div><div class="i"><img src="' + uri(recolour(base, map)) + '" style="width:26px;height:18px"></div><div class="n' + (C.contrast(star, fill) < 3 ? ' bad' : '') + '">' + C.contrast(star, fill).toFixed(2) + '</div></div>');
    }
    html += '<div class="row"><div class="l">' + label + '</div><div class="card felt">' + cells.join('') + '</div></div>';
  }
  const faces = fs.readFileSync(path.join(ROOT, 'guide-fonts.css'), 'utf8').split('@font-face').slice(1).filter((f) => /BuloRounded/.test(f)).map((f) => '@font-face' + f).join('\n');
  const felt = 'data:image/jpeg;base64,' + fs.readFileSync(path.join(ROOT, 'static/pieces/wallpaper/fabrics/green-felt.jpg')).toString('base64');
  const css = faces + 'body{margin:0;padding:10px;background:#F9F6F2;font:12px Verdana;color:#333;width:max-content}' +
    '.row{display:flex;align-items:center;gap:12px;margin-bottom:6px}.l{width:190px;line-height:15px}' +
    '.card{display:flex;align-items:flex-end;gap:10px;background:#fff;padding:6px 10px;border-radius:8px;box-shadow:inset 0 0 0 1px #e6e0d6}' +
    '.card.felt{background:url(' + felt + ') center/400px;box-shadow:none}.card.felt .h,.card.felt .n{color:#fff}' +
    '.c{display:flex;flex-direction:column;align-items:center;width:40px}.h{font:10px Verdana;color:#777;height:13px}' +
    '.i{display:flex;align-items:center;justify-content:center;height:32px}.n{font:10px Menlo;color:#777}.n.bad{color:#C92A2A;font-weight:bold}.card.felt .n.bad{color:#FFA8A8}.gap{height:6px}';
  const b = await chromium.launch();
  try {
    const p = await (await b.newContext({ viewport: { width: 900, height: 400 }, deviceScaleFactor: 2 })).newPage();
    await p.setContent('<html><head><style>' + css + '</style></head><body>' + html + '</body></html>');
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(400);
    await p.locator('body').screenshot({ path: path.join(HERE, 'glyph-states.png') });
  } finally { await b.close(); }
})();
