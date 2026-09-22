// Compiles the site's SCSS (lobby-build tree) and writes site.css: every rule scoped under .site, with
// body.fp / body.wm / html / :root rewritten onto that root, @font-face dropped (the labs declare their own),
// and asset URLs pointed at the ./static symlink, with mask art inlined. Also writes guide-fonts.css.
// Run: node build-site-css.js
const fs = require('fs'), path = require('path'), cp = require('child_process');
const WOCG = '/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/worldofcardgames/static';
const OUT = path.join(__dirname, 'site.css');
const TMP = '/tmp/wocg-site-css';
// The sheets in the order the site loads them (node-shared/dustData.js), the YUI reset first, so a tie between two
// sheets falls the same way in the lab as on the site.
const DUST = path.join(WOCG, '..', 'node-shared', 'dustData.js');
const ORDER = fs.readFileSync(DUST, 'utf8').match(/css = css\.concat\(\[([^\]]+)\]/);
if (!ORDER) throw new Error('dustData.js: the css list moved');
const SHEETS = ORDER[1].split(',').map(x => x.trim().replace(/^"|"$/g, '') + '.css');
const RESET = path.join(WOCG, 'yui3', 'cssreset', 'reset.css');
fs.rmSync(TMP, { recursive: true, force: true });
cp.execSync(`sass --no-source-map --style expanded "${WOCG}/scss":"${TMP}" 2>/dev/null`, { stdio: 'inherit' });

// Specificity is kept exact. Every rule is prefixed with :where(.site), which adds nothing; body and html become
// :where(.site):is(div), one type point, the same as the element they replaced (so the root must be a div);
// :root becomes :where(.site):is(.site), one class point. So a tie between two sheets falls as it does on the site.
const ROOT = ':where(.site):is(div)', ROOTC = ':where(.site):is(.site)';
function scopeSelector(sel) {
  let s = sel.trim();
  if (!s) return s;
  if (/^(from|to|\d+%)$/.test(s)) return s;                       // keyframe steps
  s = s.replace(/html:has\(body\.wm\)/g, ROOT + ':is(div).wm').replace(/html:has\(body\.fp\)/g, ROOT + ':is(div).fp');
  if (/^:where\(\.site\)/.test(s)) return s;                       // html:has(body.x) became the root itself
  if (/^:root\b/.test(s)) return s.replace(/^:root/, ROOTC);
  if (/^html\s+body\b/.test(s)) return s.replace(/^html\s+body/, ROOT + ':is(div)'); // html body.fp keeps its two type points
  if (/^html\b/.test(s)) return s.replace(/^html/, ROOT);
  if (/^body\b/.test(s)) return s.replace(/^body/, ROOT);          // body.fp -> root.fp, body[data-x] -> root[data-x]
  return ':where(.site) ' + s;
}
// splits a selector list at top-level commas only, so a list inside :has(), :is(), :where() or :not() stays whole
function splitTop(head) {
  const out = []; let depth = 0, cur = '';
  for (const ch of head) {
    if (ch === '(') depth++; else if (ch === ')') depth--;
    if (ch === ',' && depth === 0) { out.push(cur); cur = ''; } else cur += ch;
  }
  out.push(cur); return out;
}
function scopeCss(css) {
  // a small walker: copies the text, rewriting selector lists at rule starts; skips @font-face bodies whole.
  // Comments go first, so a comment between two rules never ends up inside a selector.
  css = css.replace(/\/\*[\s\S]*?\*\//g, '').replace(/@(charset|import|namespace)[^;{]*;/g, '');  // statement at-rules have no block
  let out = '', i = 0, n = css.length, stack = [];
  while (i < n) {
    // comments
    if (css.startsWith('/*', i)) { const e = css.indexOf('*/', i); i = e < 0 ? n : e + 2; continue; }
    const brace = css.indexOf('{', i), close = css.indexOf('}', i);
    if (brace < 0 && close < 0) { out += css.slice(i); break; }
    if (close >= 0 && (brace < 0 || close < brace)) { out += css.slice(i, close + 1); stack.pop(); i = close + 1; continue; }
    const head = css.slice(i, brace).trim();
    if (head.startsWith('@font-face')) { // skip the block
      let depth = 0, j = brace; for (; j < n; j++) { if (css[j] === '{') depth++; else if (css[j] === '}') { depth--; if (!depth) break; } }
      i = j + 1; continue;
    }
    if (head.startsWith('@')) { out += css.slice(i, brace + 1); stack.push(head.split(/\s+/)[0]); i = brace + 1; continue; }
    const parent = stack[stack.length - 1];
    const inKeyframes = parent === '@keyframes' || parent === '@-webkit-keyframes';
    const sels = splitTop(head).map(x => inKeyframes ? x.trim() : scopeSelector(x));
    out += (css.slice(i, brace).match(/^\s*/) || [''])[0] + sels.join(', ') + ' {';
    stack.push('rule'); i = brace + 1;
  }
  return out;
}
let all = '\n/* ---- yui3/cssreset/reset.css ---- */\n' + scopeCss(fs.readFileSync(RESET, 'utf8'));
for (const f of SHEETS) {
  const p = path.join(TMP, f); if (!fs.existsSync(p)) { console.log('missing', f); continue; }
  let css = fs.readFileSync(p, 'utf8').replace(/url\((['"]?)\.\.\//g, 'url($1static/');
  all += `\n/* ---- ${f} ---- */\n` + scopeCss(css);
}

// Chrome treats a file:// page as its own origin, so a mask image and a font are blocked when the guide is opened
// straight from disk: the movement chip loses its arrow and the whole page falls back to Verdana, with no error to
// show for it. Both are inlined, so the page tells the truth however it is opened.
const DATA = new Map();
function dataURI(rel) {
  if (DATA.has(rel)) return DATA.get(rel);
  const file = path.join(WOCG, rel.replace(/^static\//, '').replace(/\?.*$/, ''));
  let uri = null;
  if (fs.existsSync(file)) {
    const ext = path.extname(file).toLowerCase();
    const type = { '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2' }[ext];
    if (type) uri = 'data:' + type + ';base64,' + fs.readFileSync(file).toString('base64');
  }
  DATA.set(rel, uri); return uri;
}
// Only the art a mask points at: a background image loads from disk as it always did, and inlining every icon
// would treble the sheet.
const MASKED = new Set();
all.replace(/(?:-webkit-)?mask(?:-image)?\s*:[^;{}]*/g, d => { (d.match(/url\("([^"]+)"\)/g) || []).forEach(u => MASKED.add(u.slice(5, -2))); return d; });
let inlined = 0;
// An inlined mask loses its file name, which two cards measure, so the build also writes the names out keyed by
// the base64 itself (these files share an xml prolog, so a prefix would collide). Lab.assetName reads them back.
const names = {};
for (const rel of MASKED) {
  const d = dataURI(rel); if (!d) continue;
  names[d.slice(d.indexOf(',') + 1)] = rel.replace(/^.*\//, '').replace(/\?.*$/, '');
  all = all.split('url("' + rel + '")').join('url("' + d + '")'); inlined++;
}
fs.writeFileSync(path.join(__dirname, 'guide-assets.js'),
  '// The art inlined into site.css, by the head of its base64, so a card can still name the file it measures.\n' +
  '// Written by build-site-css.js.\nwindow.Assets = ' + JSON.stringify(names, null, 1) + ';\n');

// The faces the guide declares, as one sheet it can link. Kept out of head.html so that file stays readable.
// The site serves three, so the lab serves three: the Bulo black and the GLCA regular went on 22 Sep 2026, and a
// page that still declared them would tell the audit a weight is available that the site does not have.
const FACES = [
  ['BuloRounded', 400, 'BuloRounded-Regular.woff2'], ['BuloRounded', 700, 'BuloRounded-Bold.woff2'],
  ['GLCA', 500, 'Gelica-Medium.woff2'], ['Gelica', 500, 'Gelica-Medium.woff2']
];
let faces = '/* The site\'s faces, inlined so they load from a file:// page too. Written by build-site-css.js. */\n';
for (const [fam, weight, file] of FACES) {
  const abs = path.join(__dirname, file);
  if (!fs.existsSync(abs)) { console.log('missing font', file); continue; }
  faces += '@font-face { font-family: "' + fam + '"; src: url("data:font/woff2;base64,' +
    fs.readFileSync(abs).toString('base64') + '") format("woff2"); font-weight: ' + weight +
    '; font-style: normal; font-display: block; }\n';
}
fs.writeFileSync(path.join(__dirname, 'guide-fonts.css'), faces);

fs.writeFileSync(OUT, all);
console.log('site.css', Math.round(all.length / 1024), 'KB from', SHEETS.length, 'sheets,', inlined, 'svg urls inlined');
console.log('guide-fonts.css', Math.round(faces.length / 1024), 'KB,', FACES.length, 'faces');
