// Draws our-hues-ladder.png: Open Color's tones as the icons are built, against the "Our hues" version
// (the icon ladder), per family, with each swatch's OKLCH numbers. Run it after make-versions.js:
//
//   node icon-lab-parts/ladder-sheet.js
//
// Uses Playwright's own Chromium, never the system Chrome.
const path = require('path');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const C = require('./colour.js');
const V = require('./versions-made.js').find((v) => v.id === 'ourhue');
const map = (state, hex) => (V.state[state] || {})[hex] || hex;
// [family, icon, [role, built hex, state]...]
const ROWS = [
  ['Yellow (bell, hint)', [['fill', '#FFD43B', 'menuActivity/rest'], ['line', '#F59F00', 'menuActivity/rest']]],
  ['Orange (friends, heads)', [['fill', '#FFC078', 'menuFriends/rest'], ['line', '#FD7E14', 'menuFriends/rest']]],
  ['Indigo (friends, bodies)', [['fill', '#91A7FF', 'menuFriends/rest'], ['line', '#4C6EF5', 'menuFriends/rest']]],
  ['Blue (table info)', [['fill', '#74C0FC', 'tableMenu/rest'], ['line', '#228BE6', 'tableMenu/rest'], ['glyph', '#1971C2', 'tableMenu/rest'], ['open', '#228BE6', 'tableMenu/active']]],
  ['Lime (chat)', [['fill', '#A9E34B', 'chatMenu/rest'], ['line', '#66A80F', 'chatMenu/rest'], ['glyph', '#5C940D', 'chatMenu/rest'], ['open', '#66A80F', 'chatMenu/hover']]],
];
const sw = (hex, role) => { const o = C.ok(hex); return '<div class="sw"><i style="background:' + hex + '"></i><b>' + role + '</b><span>L ' + o.L.toFixed(2) + ' C ' + o.C.toFixed(2) + '</span><span>h ' + Math.round(o.h) + '</span></div>'; };
const html = '<style>body{margin:0;padding:18px;background:#F9F6F2;font:13px/16px Verdana;color:#262626}h2{font:bold 15px Verdana;margin:0 0 10px}' +
  'table{border-collapse:collapse}td{padding:6px 10px;vertical-align:top;border-top:1px solid #E4DDD0}th{text-align:left;padding:0 10px 6px;color:#67635c;font-weight:normal}' +
  '.sws{display:flex;gap:8px}.sw{width:100px}.sw i{display:block;width:100px;height:34px;border-radius:6px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}.sw b{display:block;margin-top:3px;font-size:12px}.sw span{display:block;font-size:11px;color:#67635c}' +
  '.fam{width:170px;font-weight:bold}</style><h2>Open Color as built, and our hues (the icon ladder)</h2><table><tr><th></th><th>Open Color as built</th><th>Our hues</th></tr>' +
  ROWS.map(([name, roles]) => '<tr><td class="fam">' + name + '</td><td><div class="sws">' + roles.map(([r, h]) => sw(h, r)).join('') + '</div></td><td><div class="sws">' +
    roles.map(([r, h, st]) => sw(map(st, h), r)).join('') + '</div></td></tr>').join('') + '</table>';
(async () => {
  const b = await chromium.launch();
  try {
    const p = await (await b.newContext({ viewport: { width: 1180, height: 400 }, deviceScaleFactor: 2 })).newPage();
    await p.setContent(html); await p.waitForTimeout(200);
    await p.screenshot({ path: path.join(__dirname, 'our-hues-ladder.png'), fullPage: true });
  } finally { await b.close(); }
})();
