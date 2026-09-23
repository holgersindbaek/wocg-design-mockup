// Captures a dealt Hearts table from the dev site, as the redesign draws it, into a static page the
// icon lab can recolour: table/hearts.html, with table/hearts-dev.png as the reference shot.
//
//   node icon-lab-parts/capture-table.js
//
// It signs in a throwaway dev account, replays the visual sweep's recorded Hearts deal with a person
// in every seat (scripts/visual-sweep: fixtures/hearts.json, the "your-play" state), then asks the
// table itself for the marks a player sees at a seat: the subscriber crown, the liked star and the
// leaving door (Hearts draws no dealer chip), and puts the hint arrow over one card. The page is saved with its
// scripts taken out, its CSSOM written into its style elements, and every asset URL pointed at the design
// folder's static/ symlink, so it opens from disk. The ad rail stays, in ad layout A (the two medium
// rectangles and the video docked at its foot, as a 1440 by 900 table shows them), with the stand-in ads
// the mockups use (adMedrec1.png, adMedrec2.png, adVideo.png) in its slots.
// Dev only. Uses Playwright's own Chromium, never the system Chrome.
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');

const HERE = __dirname;
const REPO = '/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg';
const SWEEP = path.join(REPO, 'scripts/visual-sweep');
const STATIC = path.join(REPO, 'worldofcardgames/static');
const BASE = 'https://dev.worldofcardgames.com';
const OUT = path.join(HERE, 'table');
const VIEW = { width: 1440, height: 900 };
const ACCOUNT = { username: 'IconLabDesk', password: 'Icon-Lab-Tester-1', email: 'icon-lab-desk@example.com' };
const wrap = (code) => '(async () => {\n' + code + '\n})()';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const client = await import(pathToFileURL(path.join(SWEEP, 'lib/client.mjs')).href);
  const scenes = await import(pathToFileURL(path.join(SWEEP, 'lib/scenes.mjs')).href);
  const fx = JSON.parse(fs.readFileSync(path.join(SWEEP, 'fixtures/hearts.json'), 'utf8'));
  const target = scenes.stateTargets(fx).find((t) => t.name === 'your-play');
  if (!target) throw new Error('the hearts fixture has no your-play state');
  const messages = scenes.humanize(target.messages);

  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext({ viewport: VIEW, ignoreHTTPSErrors: true, deviceScaleFactor: 1 });
    // ads_code.dust picks the rail's layout from this cookie; A is the two medium rectangles
    await ctx.addCookies([{ name: 'wocgAdLayoutPath', value: 'A', domain: 'dev.worldofcardgames.com', path: '/' }]);
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    const url = BASE + '/?animationSpeed=20x&lobby=1';
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    console.log('ready:', JSON.stringify(await page.evaluate(wrap(client.waitReady()))));
    const login = await page.evaluate(wrap(client.ensureLogin(ACCOUNT)));
    console.log('login:', JSON.stringify(login));
    if (login.status !== 'already') {
      await page.goto(url, { waitUntil: 'domcontentloaded' });
      console.log('ready again:', JSON.stringify(await page.evaluate(wrap(client.waitReady()))));
    }
    const r = await page.evaluate(wrap(client.replay({ messages, gapMs: 30 })));
    console.log('replay:', JSON.stringify(r));
    if (!r.table) throw new Error('the replayed table did not come up');

    // the marks a seat can carry, asked of the table itself
    const marks = await page.evaluate(wrap(`
      const sleep = (ms) => new Promise((res) => setTimeout(res, ms));
      const t = Y.wocg.Table.getCurrentTable();
      const done = [];
      const tryIt = (name, fn) => { try { fn(); done.push(name); } catch (e) { done.push(name + ' failed: ' + e.message); } };
      tryIt('supporter on seat 1', () => t.showSiteSupporter2(1));
      tryIt('liked on seat 2', () => t.showPlayerLiked(2));
      tryIt('leaving on seat 3', () => t.showPlayerLeaving(3));
      await sleep(1500);
      // the hint arrow over the third card of your hand
      const hand = [...document.querySelectorAll('#playspace .piece.card')].filter((e) => /hand0/.test(e.className) || (e.getBoundingClientRect().top > innerHeight * 0.6));
      const card = hand[2];
      if (card) { card.classList.add('hint-suggested'); card.style.setProperty('--turn-hint-arrow-left', (card.offsetWidth / 2) + 'px'); done.push('hint arrow on a card'); }
      return { done, hand: hand.length };
    `));
    console.log('marks:', JSON.stringify(marks));
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(OUT, 'hearts-dev.png') });

    // every CSS rule that paints an icon file, with its @media and @supports, so the lab can write a
    // recoloured twin of each (a hover or open state included). Read here, where the sheets are
    // same-origin; a page opened from disk may not read its own sheets.
    const rules = await page.evaluate(() => {
      const out = [];
      const walk = (list, conds) => {
        for (const r of list) {
          if (r.type === CSSRule.STYLE_RULE) {
            ['background-image', 'mask-image', '-webkit-mask-image'].forEach((prop) => {
              const v = r.style.getPropertyValue(prop);
              if (/images\/[A-Za-z0-9_@.-]+\.(png|svg)/.test(v)) out.push({ sel: r.selectorText, conds, prop, value: v, important: r.style.getPropertyPriority(prop) === 'important' });
            });
          } else if (r.type === CSSRule.MEDIA_RULE) walk(r.cssRules, conds.concat(['@media ' + r.conditionText]));
          else if (r.type === CSSRule.SUPPORTS_RULE) walk(r.cssRules, conds.concat(['@supports ' + r.conditionText]));
        }
      };
      for (const sh of document.styleSheets) { try { walk(sh.cssRules, []); } catch (e) {} }
      return out;
    });
    fs.writeFileSync(path.join(OUT, 'hearts-rules.json'), JSON.stringify(rules, null, 1));
    console.log('icon rules:', rules.length);

    // the page, made static
    const snap = await page.evaluate(({ base }) => {
      // CSSOM rules a script inserted are not in the markup: write them into their style element
      [...document.styleSheets].forEach((sh) => {
        const n = sh.ownerNode;
        if (!n || n.tagName !== 'STYLE') return;
        try {
          const text = [...sh.cssRules].map((r) => r.cssText).join('\n');
          if (text && text.length > (n.textContent || '').length) n.textContent = text;
        } catch (e) {}
      });
      const doc = document.documentElement.cloneNode(true);
      doc.querySelectorAll('base, script, noscript, iframe, link[rel=preload], link[rel=prefetch], link[rel=preconnect], link[rel=dns-prefetch], link[rel=modulepreload], link[rel=manifest], meta[http-equiv]').forEach((e) => e.remove());
      // the ads: the rail keeps the slots layout A fills at this size, each with a stand-in; the rest goes
      doc.querySelectorAll('[id^="google_ads"], .adsbygoogle, ins, [id^="AdThrive" i], [class^="adthrive" i], #raptive-sticky-footer-ad, #worldofcardgames_mobile_top_video').forEach((e) => e.remove());
      const standIn = { worldofcardgamescom_medrec_1: ['adMedrec1.png', 250], worldofcardgamescom_medrec_2: ['adMedrec2.png', 250], worldofcardgamescom_right_rail_video: ['adVideo.png', 169] };
      doc.querySelectorAll('#ad .raptive-display-ad').forEach((slot) => {
        const s = standIn[slot.id];
        if (!s) { slot.remove(); return; }
        slot.innerHTML = '';
        slot.style.removeProperty('display');
        const img = document.createElement('img');
        img.setAttribute('src', s[0]); img.setAttribute('alt', ''); img.setAttribute('width', '300'); img.setAttribute('height', String(s[1]));
        img.setAttribute('style', 'display:block;width:300px;height:' + s[1] + 'px;object-fit:cover');
        slot.appendChild(img);
      });
      const video = doc.querySelector('#RaptiveRightRailVideoAdContainer');
      if (video) video.style.removeProperty('display');
      doc.querySelectorAll('#ad .adLayoutSkyscraperRow').forEach((e) => { if (!e.children.length) e.remove(); });
      const sheets = [...doc.querySelectorAll('link[rel=stylesheet]')].map((l) => l.getAttribute('href'));
      return { html: '<!DOCTYPE html>\n' + doc.outerHTML, sheets, bodyClass: document.body.className, htmlClass: document.documentElement.className,
        attrs: [...document.body.attributes].map((a) => a.name + '=' + a.value) };
    }, { base: BASE });
    console.log('body:', snap.bodyClass, '|', snap.attrs.join(' '));
    if (!/\bad-layout-A\b/.test(snap.bodyClass)) throw new Error('the page is not in ad layout A: ' + snap.bodyClass);
    if (!/id="ad"/.test(snap.html) || !/adMedrec1\.png/.test(snap.html) || !/adVideo\.png/.test(snap.html)) throw new Error('the ad rail or its stand-ins are missing');
    console.log('sheets:', snap.sheets.join('\n  '));

    // every asset URL to a path under the design folder's static/ symlink
    const missing = new Set();
    // the dev site serves worldofcardgames/static at /assets/
    const local = (u) => {
      let p = u.replace(/^https?:\/\/dev\.worldofcardgames\.com/, '').replace(/^\//, '');
      if (!/^(assets|static)\//.test(p)) return null;
      p = p.split('#')[0].split('?')[0].replace(/^(assets|static)\//, '');
      if (fs.existsSync(path.join(STATIC, p))) return 'static/' + p;
      missing.add(p); return null;
    };
    let html = snap.html.replace(/(\s(?:src|href|xlink:href|poster)=")([^"]+)(")/g, (m, a, u, b) => { const l = local(u); return l ? a + l + b : m; })
      .replace(/(\ssrcset=")([^"]+)(")/g, (m, a, list, b) => a + list.split(',').map((part) => { const bits = part.trim().split(/\s+/); const l = local(bits[0]); return l ? [l].concat(bits.slice(1)).join(' ') : ''; }).filter(Boolean).join(', ') + b)
      .replace(/url\((&quot;|['"])?([^'")&]+)(&quot;|['"])?\)/g, (m, q1, u, q2) => { if (/^data:|^#/.test(u)) return m; const l = local(u); return l ? 'url(' + (q1 || '') + l + (q2 || '') + ')' : m; });
    // the fonts come inlined, since a browser blocks a font file opened from disk
    html = html.replace('</head>', '<link rel="stylesheet" href="guide-fonts.css">\n</head>');
    fs.writeFileSync(path.join(OUT, 'hearts.html'), html);
    console.log('saved', path.join(OUT, 'hearts.html'), Math.round(html.length / 1024) + ' KB');
    if (missing.size) console.log('not found on disk:\n  ' + [...missing].slice(0, 40).join('\n  '));
    console.log(errors.length ? 'page errors:\n  ' + errors.slice(0, 10).join('\n  ') : 'no page errors');
  } finally { await browser.close(); }
})().catch((e) => { console.error(e); process.exit(1); });
