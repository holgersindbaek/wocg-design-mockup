// Loads every recoloured Lottie with the site's own player on dev, beside master's, and reads the colours it draws.
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const FILES = ['images/menuActivityNotification.json', 'images/menuActivityNotificationTransition.json', 'images/menuActivityNotificationHover.json',
  'images/menuActivityNotificationHoverTransition.json', 'images/menuFriendsNotification.json', 'images/menuFriendsNotificationTransition.json',
  'images/menuFriendsNotificationHover.json', 'images/menuFriendsNotificationHoverTransition.json', 'images/gameOverHeader.json', 'images/handOverHeader.json',
  'pieces/medal/classic/1.json', 'pieces/medal/classic/2.json', 'pieces/medal/classic/3.json', 'pieces/medal/classic/4.json', 'pieces/medal/classic/5.json', 'pieces/medal/classic/6.json'];
(async () => {
  const b = await chromium.launch();
  try {
    const ctx = await b.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1200, height: 1400 }, deviceScaleFactor: 2 });
    const p = await ctx.newPage();
    const errors = [];
    p.on('pageerror', (e) => errors.push(e.message));
    await p.goto('https://dev.worldofcardgames.com/hearts?lobby=1', { waitUntil: 'domcontentloaded', timeout: 90000 });
    await p.waitForTimeout(5000);
    const res = await p.evaluate(async (files) => {
      const L = window.lottie || window.bodymovin;
      if (!L) return { error: 'no lottie player on the page' };
      const grid = document.createElement('div');
      grid.id = 'lottieProbe';
      grid.style.cssText = 'position:fixed;inset:0;z-index:99999;background:#f9f6f2;display:grid;grid-template-columns:repeat(4,1fr);gap:6px;padding:8px;overflow:auto';
      document.body.appendChild(grid);
      const load = (path) => new Promise((res) => {
        const cell = document.createElement('div');
        cell.style.cssText = 'height:150px;background:#fff;border-radius:8px;display:flex;flex-direction:column;align-items:center;font:10px Verdana';
        const box = document.createElement('div'); box.style.cssText = 'width:100%;height:130px';
        cell.appendChild(box); cell.appendChild(document.createTextNode(path.replace(/.*\//, '')));
        grid.appendChild(cell);
        const anim = L.loadAnimation({ container: box, renderer: 'svg', loop: false, autoplay: false, path: Y.wocg.buildAssetImageURL(path) });
        let done = false;
        const finish = (ok) => { if (done) return; done = true;
          try { anim.goToAndStop(Math.max(0, anim.totalFrames - 1), true); } catch (e) {}
          const cols = new Set(); box.querySelectorAll('path').forEach((pa) => { ['fill', 'stroke'].forEach((a) => { const v = pa.getAttribute(a); if (v && /rgb/.test(v)) cols.add(v.replace(/\s/g, '')); }); });
          res({ path, ok, frames: anim.totalFrames, colours: [...cols].slice(0, 12) }); };
        anim.addEventListener('DOMLoaded', () => setTimeout(() => finish(true), 150));
        anim.addEventListener('data_failed', () => finish(false));
        setTimeout(() => finish(false), 8000);
      });
      const out = [];
      for (const f of files) { out.push(await load(f)); out.push(await load(Y.wocg.iconAssetPath(f))); }
      return out;
    }, FILES);
    if (res.error) { console.log(res.error); return; }
    for (let i = 0; i < res.length; i += 2) {
      const a = res[i], n = res[i + 1];
      console.log((n.path).padEnd(52), n.ok ? 'draws' : 'FAILED', n.frames + ' frames', '\n   master:', a.colours.join(' '), '\n   new:   ', n.colours.join(' '));
    }
    await p.screenshot({ path: '/tmp/wocg-verify/lottie.png', fullPage: false });
    console.log('page errors:', errors.slice(0, 3).join(' | ') || 'none');
  } finally { await b.close(); }
})();
