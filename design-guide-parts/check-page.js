// Opens design-audit.html headless: reports page errors, missing assets, empty cards, and every red row; one screenshot per section.
// It also reads the guide's own words: the rows measure the code, but a card's rule text, a note, a plain lead or a
// reference row can keep a retired name or value and still pass green. Every source line is read for one, and the
// findings print under "prose". A line that has to keep a retired term carries the marker lint-keep.
// Usage: node design-guide-parts/check-page.js [file]   (default design-audit.html)
const path = require('path'), http = require('http'), fs = require('fs');
const pw = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const DIR = path.resolve(__dirname, '..'); const file = process.argv[2] || 'design-audit.html';
const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif' };
const srv = http.createServer((q, r) => { const p = path.join(DIR, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': mime[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); });
const RETIRED = ['#8a857c', '#d9d2c4', '#dad2c4', '--ink-soft', '--faint', '--muted', '--hairline', '--rule', '--edge', '--wm-paper', '--wm-ring',
  '--wm-accent', '--panelline', '--wm-leather', '--wm-kill-soft', '--line-overlay', '--lift-btn', 'font-weight: 900', '12px 900', 'corner notice',
  'green focus', 'segmented control', 'chooser', 'tick chip', 'soft ink', 'dark tray', 'quiet brown', 'tray button', 'hairline'];
function proseLint() {
  const files = fs.readdirSync(__dirname).filter(f => /^\d\d-.*\.html$|^head\.html$|^(plain|ref-spec|build-pieces)\.js$/.test(f)).sort();
  const out = [];
  for (const f of files) fs.readFileSync(path.join(__dirname, f), 'utf8').split('\n').forEach((ln, i) => {
    if (ln.includes('lint-keep')) return;
    const low = ln.toLowerCase(), hits = RETIRED.filter(t => low.includes(t));
    for (const t of hits) if (!hits.some(u => u !== t && u.includes(t))) out.push({ file: f, line: i + 1, term: t });
  });
  return out;
}
(async () => {
  await new Promise(res => srv.listen(0, '127.0.0.1', res)); const port = srv.address().port; let b;
  try {
    b = await pw.chromium.launch(); const p = await b.newPage({ viewport: { width: 1300, height: 900 }, deviceScaleFactor: 2 });
    const errs = [], cons = [], missing = [];
    p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') cons.push(m.text()); });
    p.on('response', r => { if (r.status() >= 400) missing.push(r.status() + ' ' + r.url().replace(/^http:\/\/[^/]+\//, '')); });
    await p.goto(`http://127.0.0.1:${port}/${file}`, { waitUntil: 'load' }); await p.waitForTimeout(800);
    const rep = await p.evaluate(() => {
      const out = { squircle: CSS.supports('corner-shape', 'squircle'), height: document.body.scrollHeight, sections: [] };
      for (const s of document.querySelectorAll('.sec')) {
        const cards = [...s.querySelectorAll('.card')];
        out.sections.push({ id: s.id, title: (s.querySelector('h2') || {}).textContent, top: s.offsetTop, cards: cards.length,
          empty: cards.filter(c => !c.querySelector('table.mtab tbody tr')).map(c => (c.querySelector('h3') || {}).textContent || '(untitled)'),
          nosite: cards.filter(c => !c.querySelector('.site')).map(c => (c.querySelector('h3') || {}).textContent || '(untitled)'),
          overflow: cards.filter(c => c.scrollWidth > c.clientWidth + 2).map(c => (c.querySelector('h3') || {}).textContent || '(untitled)') });
      }
      out.bads = window.Lab ? Lab.bads() : ['Lab missing'];
      out.plainless = window.Lab ? Lab.plainless() : [];
      return out;
    });
    fs.mkdirSync('/tmp/wocg-lab-check', { recursive: true });
    // One shot per section through the viewport: the page is far taller than Chromium's capture surface, so a
    // full-page clip of a late section comes back white. A section taller than 7000px is cut into -2, -3 ... slices.
    const secs = await p.$$('.sec');
    for (let i = 0; i < secs.length; i++) {
      const top = await secs[i].evaluate(e => e.getBoundingClientRect().top + window.scrollY);
      const height = await secs[i].evaluate(e => e.offsetHeight);
      for (let off = 0, n = 1; off < height; off += 7000, n++) {
        const h = Math.min(7000, height - off + 8);
        await p.setViewportSize({ width: 1300, height: Math.max(200, Math.ceil(h)) });
        await p.evaluate(y => window.scrollTo(0, y), top + off - 8); await p.waitForTimeout(150);
        await p.screenshot({ path: `/tmp/wocg-lab-check/design-audit-${rep.sections[i].id}${n > 1 ? '-' + n : ''}.png` });
      }
    }
    await p.setViewportSize({ width: 1300, height: 900 }); await p.evaluate(() => window.scrollTo(0, 0));
    await p.screenshot({ path: '/tmp/wocg-lab-check/design-audit.png', fullPage: true });
    console.log(JSON.stringify({ file, errors: errs, consoleErrors: cons, missingAssets: missing, prose: proseLint(), ...rep }, null, 1));
  } finally { if (b) await b.close(); srv.close(); }
})();
