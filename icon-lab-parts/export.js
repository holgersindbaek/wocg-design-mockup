// Writes version 13's icon files into the site, as redesign-only copies (Holger, 23 Sep 2026: "use these new icons
// everywhere"). The old look keeps master's files, so a copy goes beside them under the same name:
//   worldofcardgames/static/images/wm/<file>       the SVGs, the PNG icons as SVGs from their Sketch vectors, the Lottie
//   worldofcardgames/static/pieces/medal/wm/<n>.json   the place medals
// Each file takes the colour map of the state it draws in the lab (versions-made.js, version 13), so the site shows
// what icon-lab-all.html shows. Nothing existing is overwritten outside those two folders.
//   node icon-lab-parts/export.js
const fs = require('fs');
const path = require('path');
const C = require('./colour.js');
const V = require('./versions-made.js').find((v) => v.id === 'schemeinks');
if (!V) throw new Error('no version 13 (schemeinks) in versions-made.js');
const SITE = '/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/worldofcardgames/static';
const IMG = path.join(SITE, 'images'), OUT = path.join(IMG, 'wm'), MEDALS = path.join(SITE, 'pieces', 'medal'), OUT_MEDALS = path.join(MEDALS, 'wm');
const SKETCH = path.join(__dirname, 'sketch');

// [source, output name, the lab's icon/state]. A PNG icon ships as the SVG of its Sketch vector.
const SVGS = [
  ['menuActivity.svg', 'menuActivity/rest'], ['menuActivityHover.svg', 'menuActivity/hover'],
  ['menuActivityNotification.svg', 'menuActivity/note'], ['menuActivityNotificationHover.svg', 'menuActivity/noteHover'],
  ['menuFriends.svg', 'menuFriends/rest'], ['menuFriendsHover.svg', 'menuFriends/hover'], ['menuFriendsCount.svg', 'menuFriends/count'],
  ['menuFriendsCountHover.svg', 'menuFriends/countHover'], ['menuFriendsNotification.svg', 'menuFriends/note'],
  ['menuFriendsNotificationHover.svg', 'menuFriends/noteHover'],
  ['crown.svg', 'crown/rest'], ['playerLiked.svg', 'playerLiked/rest'], ['playerMore.svg', 'playerMore/rest'], ['playerLeaving.svg', 'playerLeaving/rest'],
  ['menuBurger.svg', 'menuBurger/rest'], ['menuClose.svg', 'menuClose/rest'],
  ['sortArrowLeft.svg', 'sortArrows/left'], ['sortArrowRight.svg', 'sortArrows/right'], ['dealer.svg', 'dealer/rest'], ['dealerSmall.svg', 'dealer/small'],
  ['likedBadge.svg', 'likedBadge/rest'], ['botBadge.svg', 'botBadge/rest'], ['highReputationBadge.svg', 'highReputationBadge/rest'],
  ['cleanMeldBadge.svg', 'cleanMeldBadge/rest'],
  ['hintArrowDown.svg', 'hintArrow/down'], ['hintArrowUp.svg', 'hintArrow/up'], ['hintArrowLeft.svg', 'hintArrow/left'], ['hintArrowRight.svg', 'hintArrow/right'],
  ['suitHeart.svg', 'suits/heart'], ['suitDiamond.svg', 'suits/diamond'], ['suitClub.svg', 'suits/club'], ['suitSpade.svg', 'suits/spade'],
  ['handOverBackground.svg', 'handOverBackground/rest'], ['shootTheMoon.svg', 'shootTheMoon/rest'], ['shootTheSun.svg', 'shootTheSun/rest'],
  ['slam.svg', 'slam/rest'],
  ['dailyChallengeGoldSmall.svg', 'dailyChallenge/gold'], ['dailyChallengeSilverSmall.svg', 'dailyChallenge/silver'],
  ['dailyChallengeBronzeSmall.svg', 'dailyChallenge/bronze'],
];
const PNGS = [
  ['tableMenu.png', 'tableMenu/rest'], ['tableMenuActive.png', 'tableMenu/active'], ['hintMenu.png', 'hintMenu/rest'], ['hintMenuHover.png', 'hintMenu/hover'],
  ['chatMenu.png', 'chatMenu/rest'], ['chatMenuHover.png', 'chatMenu/hover'], ['chatMenuActive.png', 'chatMenu/active'],
  ['checkmark.png', 'checkmark/on'], ['checkmarkDisabled.png', 'checkmark/off'],
];
// The Lottie files the lab does not list take the map of the state they belong to: the hover rings the hover
// state's, the header animations the still's. Medals 4 to 6 share the fourth medal's recipe and fill their
// number in #E67700, which the still does not draw: a medal's number is its outline's colour (make-versions.js)
const LOTTIES = [
  ['menuActivityNotification.json', 'menuActivity/note'], ['menuActivityNotificationTransition.json', 'menuActivity/note'],
  ['menuActivityNotificationHover.json', 'menuActivity/noteHover'], ['menuActivityNotificationHoverTransition.json', 'menuActivity/noteHover'],
  ['menuFriendsNotification.json', 'menuFriends/note'], ['menuFriendsNotificationTransition.json', 'menuFriends/note'],
  ['menuFriendsNotificationHover.json', 'menuFriends/noteHover'], ['menuFriendsNotificationHoverTransition.json', 'menuFriends/noteHover'],
  ['gameOverHeader.json', 'gameOverHeader/still'], ['handOverHeader.json', 'handOverHeader/still'],
];
const MEDAL_STATES = { 1: 'medals/first', 2: 'medals/second', 3: 'medals/third', 4: 'medals/fourth', 5: 'medals/fourth', 6: 'medals/fourth' };
const MEDAL_EXTRA = { 4: { '#E67700': '#9F6713' }, 5: { '#E67700': '#9F6713' }, 6: { '#E67700': '#9F6713' } };

const HEX_NAMED = { white: '#FFFFFF', black: '#000000' };
function normHex(v) {
  v = String(v).trim(); const l = v.toLowerCase(); if (HEX_NAMED[l]) return HEX_NAMED[l];
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(v); if (!m) return null;
  let h = m[1]; if (h.length === 3) h = h.replace(/./g, '$&$&'); return '#' + h.toUpperCase();
}
const mapOf = (key) => { const m = V.state[key]; if (!m) throw new Error('no map for ' + key); return m; };
// the lab's own recolour: a colour the map leaves alone keeps its text
const propOf = (a) => a.split(/[\s=:]/)[0].toLowerCase();
function recolourSvg(svg, map) {
  const swap = (v, a) => { const h = normHex(v); if (!h) return null; const t = map[propOf(a) + ':' + h] || map[h]; return t && t !== h ? t : null; };
  return svg.replace(/(\b(?:fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*")([^"]*)(")/gi, (m, a, v, b) => { const t = swap(v, a); return t ? a + t + b : m; })
    .replace(/(\b(?:fill|stroke|stop-color|flood-color)\s*:\s*)([^;"'}]+)/gi, (m, a, v) => { const t = swap(v, a); return t ? a + t : m; });
}
function svgColours(svg) {
  const out = new Set();
  svg.replace(/\b(?:fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*"([^"]*)"/gi, (m, v) => { const h = normHex(v); if (h) out.add(h); return m; });
  svg.replace(/\b(?:fill|stroke|stop-color|flood-color)\s*:\s*([^;"'}]+)/gi, (m, v) => { const h = normHex(v); if (h) out.add(h); return m; });
  return out;
}
const hex255 = (a) => '#' + a.slice(0, 3).map((v) => Math.round(Math.min(1, Math.max(0, v)) * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
function lottieWalk(data, fn) {
  (function walk(o) {
    if (Array.isArray(o)) { o.forEach(walk); return; }
    if (!o || typeof o !== 'object') return;
    if ((o.ty === 'fl' || o.ty === 'st') && o.c && Array.isArray(o.c.k)) {
      const k = o.c.k;
      if (typeof k[0] === 'number') fn(k);
      else k.forEach((kf) => { if (kf && Array.isArray(kf.s) && typeof kf.s[0] === 'number') fn(kf.s); if (kf && Array.isArray(kf.e) && typeof kf.e[0] === 'number') fn(kf.e); });
    }
    Object.keys(o).forEach((key) => walk(o[key]));
  })(data);
}
function recolourLottie(data, map) {
  const d = JSON.parse(JSON.stringify(data));
  lottieWalk(d, (a) => { const t = map[hex255(a)]; if (t) { const p = C.hexToRgb(t); a[0] = +p[0].toFixed(6); a[1] = +p[1].toFixed(6); a[2] = +p[2].toFixed(6); } });
  return d;
}
const lottieColours = (data) => { const out = new Set(); lottieWalk(data, (a) => out.add(hex255(a))); return out; };

fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(OUT_MEDALS, { recursive: true });
const report = [];
// a colour the map moves must be gone from the output; a colour it does not name must be one the lab keeps
function check(name, before, after, map) {
  const stale = [...after].filter((h) => map[h] && map[h] !== h);
  if (stale.length) throw new Error(name + ': still has ' + stale.join(' '));
  const kept = [...before].filter((h) => !map[h]);
  report.push(name.padEnd(46) + (kept.length ? 'keeps ' + kept.join(' ') : ''));
}
for (const [file, key] of SVGS) {
  const src = fs.readFileSync(path.join(IMG, file), 'utf8'), map = mapOf(key), out = recolourSvg(src, map);
  check('images/wm/' + file, svgColours(src), svgColours(out), map);
  fs.writeFileSync(path.join(OUT, file), out);
}
for (const [png, key] of PNGS) {
  const vector = path.join(SKETCH, png.replace(/\.png$/, '.svg')), src = fs.readFileSync(vector, 'utf8'), map = mapOf(key);
  const out = recolourSvg(src, map), name = png.replace(/\.png$/, '.svg');
  check('images/wm/' + name + ' (from ' + png + ')', svgColours(src), svgColours(out), map);
  fs.writeFileSync(path.join(OUT, name), out);
}
for (const [file, key] of LOTTIES) {
  const data = JSON.parse(fs.readFileSync(path.join(IMG, file), 'utf8')), map = mapOf(key), out = recolourLottie(data, map);
  check('images/wm/' + file, lottieColours(data), lottieColours(out), map);
  fs.writeFileSync(path.join(OUT, file), JSON.stringify(out));
}
for (let n = 1; n <= 6; n++) {
  const data = JSON.parse(fs.readFileSync(path.join(MEDALS, 'classic', n + '.json'), 'utf8'));
  const map = Object.assign({}, mapOf(MEDAL_STATES[n]), MEDAL_EXTRA[n] || {}), out = recolourLottie(data, map);
  check('pieces/medal/wm/' + n + '.json', lottieColours(data), lottieColours(out), map);
  fs.writeFileSync(path.join(OUT_MEDALS, n + '.json'), JSON.stringify(out));
}
console.log(report.join('\n'));
console.log('\n' + (SVGS.length + PNGS.length + LOTTIES.length) + ' files in images/wm, 6 medals in pieces/medal/wm');
