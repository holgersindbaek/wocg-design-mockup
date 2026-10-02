// Writes ../bid-chooser-lab.html and ../suit-chooser-lab.html (Holger, 2 Oct 2026). The first tries Bridge's bid box
// as a chooser like the suit pill; the second tries the suit pill with the picked suit as a dialog's white card.
//   node chooser-lab-parts/build.js
//
// Both pages draw the site's own pieces with the site's own CSS. The shared ../site.css is older than the tree (and
// another session holds it uncommitted), so this build compiles its own copy: ../build-site-css.js runs in a temp
// folder, and the result goes to chooser-lab-parts/site.css with its image addresses pointed one folder up. The suit
// pill draws its suits through a custom property that a mask reads (--trump-pill-suit), which build-site-css.js does
// not inline; Chrome will not load a mask from disk on a file:// page, so this build inlines those as well.
//
// The facts the bid lab draws from the dev site are in captured.json, table-*.jpg: today's bid box (its markup, as
// the site wrote it), the free room on the table, and the table behind the box. capture.mjs and room.mjs took them
// on 2 Oct 2026 (dev, lobby-build, Bridge bots table, first bid turn); run them again after a layout change.
const fs = require('fs'), path = require('path'), os = require('os'), cp = require('child_process');
const HERE = __dirname, ROOT = path.join(HERE, '..');
const STATIC = path.join(ROOT, 'static'); // a symlink to worldofcardgames/static
const read = (f) => fs.readFileSync(f, 'utf8');

function siteCss() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'chooser-lab-css-'));
  try {
    const src = read(path.join(ROOT, 'build-site-css.js'));
    const patched = src.replace("const TMP = '/tmp/wocg-site-css';", 'const TMP = ' + JSON.stringify(path.join(tmp, 'sass')) + ';');
    if (patched === src) throw new Error('build-site-css.js: its TMP line moved');
    fs.writeFileSync(path.join(tmp, 'build-site-css.js'), patched);
    for (const f of ['BuloRounded-Regular.woff2', 'BuloRounded-Bold.woff2', 'Gelica-Medium.woff2']) fs.symlinkSync(path.join(ROOT, f), path.join(tmp, f));
    cp.execSync('node build-site-css.js', { cwd: tmp, stdio: 'pipe' });
    return read(path.join(tmp, 'site.css'));
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

function dataUri(rel) {
  const file = path.join(STATIC, rel.replace(/^static\//, '').replace(/\?.*$/, ''));
  const type = { '.svg': 'image/svg+xml', '.png': 'image/png' }[path.extname(file).toLowerCase()];
  if (!type || !fs.existsSync(file)) return null;
  return 'data:' + type + ';base64,' + fs.readFileSync(file).toString('base64');
}

let css = siteCss();
const viaVar = new Set();
css.replace(/(?:-webkit-)?mask(?:-image)?\s*:[^;{}]*/g, (d) => {
  (d.match(/var\((--[\w-]+)/g) || []).forEach((v) => viaVar.add(v.slice(4)));
  return d;
});
let inlined = 0;
css = css.replace(/(--[\w-]+)\s*:\s*url\("([^"]+)"\)/g, (m, name, rel) => {
  if (!viaVar.has(name)) return m;
  const d = dataUri(rel);
  if (!d) return m;
  inlined++;
  return name + ': url("' + d + '")';
});
css = css.replace(/url\((['"]?)static\//g, 'url($1../static/');
fs.writeFileSync(path.join(HERE, 'site.css'), '/* Written by chooser-lab-parts/build.js from the wocg tree; do not edit. */\n' + css);

const SUITS = {};
for (const s of ['club', 'diamond', 'heart', 'spade']) SUITS[s] = dataUri('static/images/wm/suit' + s[0].toUpperCase() + s.slice(1) + '.svg');
const fill = (page) => read(path.join(HERE, page))
  .replace('/*@@LABCSS@@*/', () => read(path.join(HERE, 'lab.css')))
  .replace('/*@@LABJS@@*/', () => read(path.join(HERE, 'lab.js')))
  .replace('/*@@SUITS@@*/', () => JSON.stringify(SUITS))
  .replace('/*@@CAPTURED@@*/', () => read(path.join(HERE, 'captured.json')).replace(/<\//g, '<\\/'));
for (const [page, out] of [['bid-page.html', 'bid-chooser-lab.html'], ['suit-page.html', 'suit-chooser-lab.html']]) {
  const html = fill(page);
  fs.writeFileSync(path.join(ROOT, out), html);
  console.log(out + ':', Math.round(html.length / 1024), 'KB');
}
console.log('chooser-lab-parts/site.css:', Math.round(css.length / 1024), 'KB,', inlined, 'mask urls in custom properties inlined');
