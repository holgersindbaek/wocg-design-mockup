// Renders one or more fragments inside the lab's head, headless, and reports errors, empty measure tables and every red row.
// Usage: node design-guide-parts/check.js <id> [fragment.html ...]   (default fragment: design-guide-parts/NN-<id>.html)
// Writes _check-<id>.html at the folder root (gitignored) and /tmp/wocg-lab-check/<id>.png.
const path = require('path'), http = require('http'), fs = require('fs');
const pw = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const DIR = path.resolve(__dirname, '..');
const id = process.argv[2]; if (!id) { console.error('usage: check.js <id> [fragments]'); process.exit(1); }
let frags = process.argv.slice(3);
if (!frags.length) frags = fs.readdirSync(path.join(DIR, 'design-guide-parts')).filter(f => /^\d\d-.+\.html$/.test(f) && f.endsWith('-' + id + '.html')).map(f => path.join(DIR, 'design-guide-parts', f));
if (!frags.length) { console.error('no fragment for', id); process.exit(1); }
const head = fs.readFileSync(path.join(DIR, 'design-guide-parts/head.html'), 'utf8');
const body = frags.map(f => fs.readFileSync(f, 'utf8')).join('\n');
const page = head + '\n<div class="page">\n' + body + '\n</div>\n</body>\n</html>\n';
const out = path.join(DIR, '_check-' + id + '.html'); fs.writeFileSync(out, page);
const mime = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif' };
const srv = http.createServer((q, r) => { const p = path.join(DIR, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, { 'Content-Type': mime[path.extname(p)] || 'application/octet-stream' }); r.end(d); }); });
(async () => {
  await new Promise(res => srv.listen(0, '127.0.0.1', res)); const port = srv.address().port; let b;
  try {
    b = await pw.chromium.launch(); const p = await b.newPage({ viewport: { width: 1300, height: 900 }, deviceScaleFactor: 2 });
    const errs = [], cons = [], missing = [];
    p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') cons.push(m.text()); });
    p.on('response', r => { if (r.status() >= 400) missing.push(r.status() + ' ' + r.url().replace(/^http:\/\/[^/]+\//, '')); });
    await p.goto(`http://127.0.0.1:${port}/_check-${id}.html`, { waitUntil: 'load' }); await p.waitForTimeout(600);
    const rep = await p.evaluate(() => {
      const cards = [...document.querySelectorAll('.sec .card')];
      const empty = cards.filter(c => !c.querySelector('table.mtab tbody tr')).map(c => (c.querySelector('h3') || {}).textContent || '(untitled card)');
      const nosite = cards.filter(c => !c.querySelector('.site')).map(c => (c.querySelector('h3') || {}).textContent || '(untitled card)');
      return { squircle: CSS.supports('corner-shape', 'squircle'), sections: [...document.querySelectorAll('.sec')].map(s => s.id), cards: cards.length, empty, nosite, bads: window.Lab ? Lab.bads() : ['Lab missing'], plainless: window.Lab ? Lab.plainless() : [], height: document.body.scrollHeight };
    });
    fs.mkdirSync('/tmp/wocg-lab-check', { recursive: true });
    await p.screenshot({ path: `/tmp/wocg-lab-check/${id}.png`, fullPage: true });
    console.log(JSON.stringify({ page: out, shot: `/tmp/wocg-lab-check/${id}.png`, errors: errs, consoleErrors: cons, missingAssets: missing, ...rep }, null, 1));
  } finally { if (b) await b.close(); srv.close(); }
})();
