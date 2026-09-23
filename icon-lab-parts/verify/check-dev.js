// Verifies the version 13 icons on dev: flag on draws the wm copies, flag off draws master's files; no wm file fails.
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const BASE = 'https://dev.worldofcardgames.com';
const OUT = '/tmp/wocg-verify/';
async function run(b, flag) {
  const ctx = await b.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  const fails = [], wmLoads = new Set(), errors = [];
  p.on('requestfailed', (r) => fails.push(r.url() + ' ' + (r.failure() || {}).errorText));
  p.on('response', (r) => { if (/\/images\/wm\/|\/medal\/wm\//.test(r.url())) { wmLoads.add(r.url().replace(/.*\/assets\//, '').replace(/\?.*/, '') + ' ' + r.status()); if (r.status() >= 400) fails.push(r.url() + ' ' + r.status()); } });
  p.on('pageerror', (e) => errors.push(e.message));
  await p.goto(BASE + '/?lobby=' + flag, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await p.waitForTimeout(5000);
  const front = await p.evaluate(() => ({
    body: document.body.className.slice(0, 60),
    bell: [...document.querySelectorAll('#userBar .activityIcon > img')].map((i) => i.getAttribute('src').replace(/\?.*/, '')),
    friends: [...document.querySelectorAll('#userBar .friendsIcon > img')].map((i) => i.getAttribute('src').replace(/\?.*/, '')),
    token: getComputedStyle(document.body).getPropertyValue('--wm-icon-crown').trim(),
    helper: typeof Y !== 'undefined' && Y.wocg.iconAssetPath ? [Y.wocg.iconAssetPath('images/gameOverHeader.json'), Y.wocg.iconAssetPath('pieces/medal/classic/3.json'), Y.wocg.iconAssetPath('images/gameOverStar.svg')] : 'no helper',
  }));
  console.log('FRONT flag=' + flag, JSON.stringify(front));
  await p.screenshot({ path: OUT + 'front-' + flag + '.png', clip: { x: 900, y: 0, width: 540, height: 70 } });
  return { ctx, p, fails, wmLoads, errors };
}
(async () => {
  const b = await chromium.launch();
  try {
    for (const flag of ['1', '0']) {
      const r = await run(b, flag);
      console.log('  wm loads:', [...r.wmLoads].join(', ') || 'none');
      console.log('  failed:', r.fails.filter((f) => /wm\/|images\//.test(f)).join(' | ') || 'none');
      console.log('  page errors:', r.errors.slice(0, 3).join(' | ') || 'none');
      await r.ctx.close();
    }
  } finally { await b.close(); }
})();
