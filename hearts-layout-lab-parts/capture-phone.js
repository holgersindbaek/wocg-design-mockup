// Captures today's Hearts table (the redesign, lobby-build) from the dev site at a phone's size, in the
// states the layout lab draws, and measures every piece on it: hearts-layout-lab-parts/measure/<view>-<state>.json
// and .png. Adapted from icon-lab-parts/capture-table.js. It replays the visual sweep's recorded Hearts deal
// (scripts/visual-sweep/fixtures/hearts.json) with the sweep's own bots at the seats, so the table is the one the
// sweep shot on 24 Sep. Dev only. Uses Playwright's own Chromium, never the system Chrome, and closes it in a finally.
//
//   node hearts-layout-lab-parts/capture-phone.js [view ...]     views: app (393x852), safe (393x759), safari (390x664)
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');

const HERE = __dirname;
const REPO = '/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg';
const SWEEP = path.join(REPO, 'scripts/visual-sweep');
const BASE = 'https://dev.worldofcardgames.com';
const OUT = path.join(HERE, 'measure');
const UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';
const VIEWS = { app: { width: 393, height: 852 }, safe: { width: 393, height: 759 }, safari: { width: 390, height: 664 },
  // the app's own page (?platform=mobile) with the redesign forced on as scripts/gameplay-video/capture.mjs does for the
  // store preview, window.ReactNativeWebView present as in the Expo app (so the site shows its ads, AdWidget.isAdRemoved), and the
  // iPhone's safe-area insets (59 over, 34 under) written where the site reads env()
  appframe: { width: 393, height: 852, platform: true, insets: [59, 0, 34, 0] } };
const WM_ON = 'window.__wocgFp=true; var o=new MutationObserver(function(){if(document.body){document.body.classList.add("wm");o.disconnect();}}); o.observe(document,{childList:true,subtree:true}); document.addEventListener("DOMContentLoaded",function(){document.body.classList.add("wm");});';
const INSETS = (i) => 'window.ReactNativeWebView = window.ReactNativeWebView || { postMessage: function () {} };' +
  'var __ins = function () { var r = document.documentElement; if (!r) return; r.style.setProperty("--safe-area-inset-top", "' + i[0] + 'px"); r.style.setProperty("--safe-area-inset-right", "' + i[1] + 'px"); r.style.setProperty("--safe-area-inset-bottom", "' + i[2] + 'px"); r.style.setProperty("--safe-area-inset-left", "' + i[3] + 'px"); };' +
  '__ins(); var __io = new MutationObserver(function () { if (document.documentElement) { __ins(); __io.disconnect(); } }); __io.observe(document, { childList: true }); document.addEventListener("DOMContentLoaded", __ins);'
const STATES = ['your-choose', 'your-play', 'mid-trick', 'their-turn'];
const ACCOUNT = { username: 'IconLabDesk', password: 'Icon-Lab-Tester-1', email: 'icon-lab-desk@example.com' };
const wrap = (code) => '(async () => {\n' + code + '\n})()';

const MEASURE = `
  const pick = (cs, keys) => { const o = {}; keys.forEach((k) => { o[k] = cs.getPropertyValue(k); }); return o; };
  const KEYS = ['font-family','font-size','font-weight','line-height','color','background-color','background-image','background-size','background-position','border-radius','box-shadow','opacity','transform','z-index','padding','width','height','text-align','letter-spacing','border','outline','visibility','display'];
  const box = (el) => { const r = el.getBoundingClientRect(); return { x: +r.left.toFixed(2), y: +r.top.toFixed(2), w: +r.width.toFixed(2), h: +r.height.toFixed(2) }; };
  const one = (el, deep) => {
    const cs = getComputedStyle(el);
    const o = { tag: el.tagName.toLowerCase(), id: el.id || undefined, cls: el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className, box: box(el), style: pick(cs, KEYS), text: (el.innerText || '').trim().slice(0, 80) || undefined };
    if (el.tagName === 'IMG') o.src = el.getAttribute('src');
    if (deep) o.children = [...el.children].filter((c) => getComputedStyle(c).display !== 'none').map((c) => one(c, deep - 1));
    return o;
  };
  const vis = (el) => { const cs = getComputedStyle(el); const r = el.getBoundingClientRect(); return cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > 0 && r.width > 0 && r.height > 0; };
  const t = Y.wocg.Table.getCurrentTable();
  const pieces = [...document.querySelectorAll('#playspace .piece')].filter(vis).map((el) => one(el, 2));
  const spots = {};
  Object.keys(t.spots).forEach((id) => { const n = document.getElementById('spot-' + id); if (n) spots[id] = { box: box(n), pieces: t.spots[id].pieces.length, z: getComputedStyle(n).zIndex }; });
  const named = {};
  ['#playspace', '#mainContainer', '#menuBar', '#chromePill', '#chromePillRight', '#scoreBoardWrapper', '#scoreBoard', '#tableBarContainer', '#userBar', '#topAd', '#mobileTopAd', '.adTop', '#raptive-sticky-footer-ad', '#worldofcardgames_mobile_top_video', '#ad', '.noticeColumn', '#mainContainer .spot-messageBox', '#gameSelectorContainer', '#footer', 'body'].forEach((sel) => {
    const el = document.querySelector(sel); if (el) named[sel] = one(el, sel === '#chromePill' || sel === '#chromePillRight' || sel === '#scoreBoardWrapper' || sel === '#mainContainer .spot-messageBox' ? 3 : 0);
  });
  const adEls = [...document.querySelectorAll('[id*="ad" i], [class*="ad-" i], [class*="Ad" ]')].filter((el) => vis(el) && el.getBoundingClientRect().height > 20 && el.getBoundingClientRect().height < 200 && /ad/i.test(el.id + ' ' + el.className)).slice(0, 12).map((el) => ({ id: el.id, cls: String(el.className).slice(0, 80), box: box(el) }));
  const layout = t.gameLayout || t.layout;
  const L = layout ? {
    playerNamePlateHeight: layout.playerNamePlateHeight && layout.playerNamePlateHeight(),
    playerAvatarSize: layout.playerAvatarSize && layout.playerAvatarSize(),
    avatarSize: layout.avatarSize && layout.avatarSize(),
    playerScorePlateHeight: layout.playerScorePlateHeight && layout.playerScorePlateHeight(),
    actionButtonHeight: layout.actionButtonHeight && layout.actionButtonHeight(),
    responsiveGutter: layout.responsiveGutter && layout.responsiveGutter(),
    compact: layout.isPlayspaceCompact && layout.isPlayspaceCompact(), small: layout.isPlayspaceCompact && layout.isPlayspaceCompact('small'), portrait: layout.isPlayspacePortrait && layout.isPlayspacePortrait(),
    playspaceCenter: layout.playspaceCenter && layout.playspaceCenter(),
    tableRoundChipSize: layout.tableRoundChipSize && layout.tableRoundChipSize(),
    handPullOut: layout.handPullOut && layout.handPullOut()
  } : null;
  const html = document.documentElement, b = document.body;
  return { view: [innerWidth, innerHeight], dpr: devicePixelRatio, bodyClass: b.className, mainClass: document.getElementById('mainContainer') && document.getElementById('mainContainer').className,
    playspaceWH: [Y.wocg.playspaceWidth(), Y.wocg.playspaceHeight()], adSize: Y.wocg.getAdSize && Y.wocg.getAdSize(), showTopAd: Y.wocg.showTopAd && Y.wocg.showTopAd(), topAdOffset: Y.wocg.getTopAdOffset && Y.wocg.getTopAdOffset(), stickyFooter: Y.wocg.showStickyFooterAd && Y.wocg.showStickyFooterAd(),
    safe: { top: Y.wocg.safeAreaTop(), bottom: Y.wocg.safeAreaBottom() }, userBarHeight: Y.wocg.userBarHeight && Y.wocg.userBarHeight(), belowOverflow: Y.wocg.belowViewportRenderOverflow(),
    cssVars: ['--space-container','--space-item-gap','--paper-page','--line','--radius-lg','--radius-md','--shadow-low-outer','--plate-blue','--felt'].reduce((o, k) => { o[k] = getComputedStyle(html).getPropertyValue(k).trim() || getComputedStyle(b).getPropertyValue(k).trim(); return o; }, {}),
    layout: L, named, adEls, spots, pieces, players: t.players && t.players.map((p) => ({ name: p.name || p.username, avatar: p.avatar, bot: p.bot || p.isBot })), hand: t.spots.hand0 && t.spots.hand0.pieces.map((p) => p.card || p.id || p.cardid || (p.node && p.node.getAttribute('data-card'))) };
`;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const client = await import(pathToFileURL(path.join(SWEEP, 'lib/client.mjs')).href);
  const scenes = await import(pathToFileURL(path.join(SWEEP, 'lib/scenes.mjs')).href);
  const fx = JSON.parse(fs.readFileSync(path.join(SWEEP, 'fixtures/hearts.json'), 'utf8'));
  const targets = scenes.stateTargets(fx);
  const wanted = process.argv.slice(2).filter((a) => VIEWS[a]);
  const views = wanted.length ? wanted : ['app', 'safe', 'safari'];

  const browser = await chromium.launch();
  try {
    for (const viewName of views) {
      const view = VIEWS[viewName];
      const ctx = await browser.newContext({ viewport: view, ignoreHTTPSErrors: true, deviceScaleFactor: 3, isMobile: true, hasTouch: true, userAgent: UA, screen: view });
      const page = await ctx.newPage();
      if (view.platform) await page.addInitScript(WM_ON + INSETS(view.insets));
      const errors = [];
      page.on('pageerror', (e) => errors.push(e.message));
      const url = BASE + (view.platform ? '/?platform=mobile&platform-gameid=hearts&animationSpeed=20x&lobby=1' : '/?animationSpeed=20x&lobby=1');
      try {
        for (const stateName of STATES) {
          const target = targets.find((t) => t.name === stateName);
          if (!target) { console.log('no state', stateName); continue; }
          await page.goto(url, { waitUntil: 'domcontentloaded' });
          await page.evaluate(wrap(client.waitReady()));
          const login = await page.evaluate(wrap(client.ensureLogin(ACCOUNT)));
          if (login.status !== 'already') { await page.goto(url, { waitUntil: 'domcontentloaded' }); await page.evaluate(wrap(client.waitReady())); }
          // the fixture's bots keep their names: this is the bots table the sweep shot
          const r = await page.evaluate(wrap(client.replay({ messages: target.messages, gapMs: 30 })));
          if (!r.table) throw new Error('the replayed table did not come up for ' + stateName);
          await page.waitForTimeout(1200);
          const m = await page.evaluate(wrap(MEASURE));
          m.state = stateName; m.viewName = viewName; m.login = login.status; m.replay = r; m.errors = errors.slice(0, 5);
          fs.writeFileSync(path.join(OUT, viewName + '-' + stateName + '.json'), JSON.stringify(m, null, 1));
          await page.screenshot({ path: path.join(OUT, viewName + '-' + stateName + '.png') });
          console.log(viewName, stateName, 'pieces', m.pieces.length, 'playspace', JSON.stringify(m.named['#playspace'] && m.named['#playspace'].box), 'compact', m.layout && m.layout.compact, 'small', m.layout && m.layout.small, 'plate', m.layout && m.layout.playerNamePlateHeight, 'avatar', m.layout && m.layout.playerAvatarSize);
        }
      } finally { await ctx.close(); }
    }
  } finally { await browser.close(); }
})().catch((e) => { console.error(e); process.exit(1); });
