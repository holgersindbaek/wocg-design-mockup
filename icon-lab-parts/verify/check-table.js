// A live Hearts bots table on dev, flag on and off: which file each icon draws, the timer's colours, failures.
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const BASE = 'https://dev.worldofcardgames.com';
const OUT = '/tmp/wocg-verify/';
const probe = () => {
  const bg = (sel, pseudo) => { const e = document.querySelector(sel); if (!e) return null; const cs = getComputedStyle(e, pseudo || null); const m = /url\("?([^")]*)"?\)/.exec(cs.backgroundImage); return m ? m[1].replace(/.*\/assets\//, '').replace(/\?.*/, '') : cs.backgroundImage; };
  const t = document.querySelector('.piece.spotPrefix-timer'), tt = document.querySelector('.piece.spotPrefix-timerText');
  const about = document.querySelector('image[href*="botBadge"]');
  return {
    tablePill: bg('.chromePill .pillCell.tableCell'), leavePill: bg('.chromePill .pillCell.leaveCell', '::before'),
    hintSeat: bg('.piece.button.spotPrefix-hintButton'), chatSeat: bg('.piece.button.spotPrefix-chatButton'),
    sortLeft: bg('.piece.chip.spotPrefix-sortButton.left', '::before') || bg('.piece.chip.left'),
    more: bg('.piece.chip.spotPrefix-playerMore', '::before') || bg('.piece.chip.spotPrefix-playerMore'),
    hintArrow: bg('.piece.hint-suggested', '::before'),
    timer: t ? { bg: getComputedStyle(t).backgroundColor, shadow: getComputedStyle(t).boxShadow.slice(0, 120), arc: getComputedStyle(t.querySelector('circle')).stroke, num: tt ? getComputedStyle(tt).color : null, red: t.classList.contains('red') } : null,
    aboutBadgeVisible: about ? about.getBoundingClientRect().width > 0 && getComputedStyle(about.closest('svg')).visibility !== 'hidden' && !!about.closest('svg').offsetParent : 'none',
  };
};
async function run(b, flag) {
  const ctx = await b.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  const fails = [], wm = new Set();
  p.on('response', (r) => { const u = r.url(); if (/\/images\/wm\/|\/medal\/wm\//.test(u)) { wm.add(u.replace(/.*\/assets\//, '').replace(/\?.*/, '')); if (r.status() >= 400) fails.push(u + ' ' + r.status()); } });
  p.on('requestfailed', (r) => { if (/\/wm\//.test(r.url())) fails.push(r.url() + ' ' + (r.failure() || {}).errorText); });
  await p.goto(BASE + '/hearts?lobby=' + flag, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await p.waitForTimeout(4000);
  const front = await p.evaluate(probe);
  console.log('GAME PAGE flag=' + flag, 'about badge visible:', front.aboutBadgeVisible);
  await p.evaluate(() => Y.wocg.GameSelectors.getGameSelector('hearts').playBotsClickHandler(null));
  await p.waitForTimeout(6000);
  for (const t of ['Got it', 'OK']) { const btn = p.getByRole('button', { name: t }); if (await btn.count()) await btn.first().click().catch(() => {}); }
  let got = null;
  for (let i = 0; i < 30; i++) {
    await p.waitForTimeout(1500);
    got = await p.evaluate(probe);
    if (got.timer && got.hintSeat) break;
  }
  console.log('TABLE flag=' + flag, JSON.stringify(got, null, 1));
  await p.screenshot({ path: OUT + 'table-' + flag + '.png' });
  console.log('  wm files loaded:', [...wm].sort().join(', ') || 'none');
  console.log('  wm failures:', fails.join(' | ') || 'none');
  await ctx.close();
}
(async () => {
  const b = await chromium.launch();
  try { await run(b, '1'); await run(b, '0'); } finally { await b.close(); }
})();
