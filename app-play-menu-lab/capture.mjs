// Run: node app-play-menu-lab/capture.mjs   (from Design/WoCG-3; dev must be up; writes into app-play-menu-lab/)
// Copies what app-play-menu-lab.html needs off dev, in WebKit (the app's WKWebView engine) with an iPhone user agent,
// as the iPhone Air draws the Euchre app (420 by 912, safe area 68 on top, 2x). The Professor's peek (TutorialPeek.js,
// on dev at every launch) is sent away with Not now before each shot. The tables and counts are dev's own.
//   home.jpg            the app home's first screen, every menu shut
//   home-play.jpg       the Play pill's menu open (head: the game and its open tables, then the six rows)
//   home-activity.jpg   the right pill's Activity panel open (its head strip is what the header ideas reuse)
//   home-account.jpg    the right pill's account panel open (its "Profile" head)
//   home-rules.jpg      the How to play box the Rules row opens
// No board shot: dev has no /euchre-leaderboard (the daily job writes the game boards on the server only), and dev's
// /leaderboards page in the app's web sheet logs the home out ("The site is open somewhere else").
//   capture.json        the boxes of the pills, the two menus, their heads and rows
//   styles.json         the computed look of both menus and their parts
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DIR = path.dirname(new URL(import.meta.url).pathname);
const DEV = "https://dev.worldofcardgames.com";
const GAME = "euchre";
const HOME = `${DEV}/?platform=mobile&platform-gameid=${GAME}&apphome=1`;
const UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148";
const W = 420, H = 912, SAFE = 68;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const npx = execSync("ls -d ~/.npm/_npx/*/node_modules/playwright 2>/dev/null | head -1", { shell: "/bin/zsh" }).toString().trim();
if (!npx) throw new Error("no playwright in the npx cache: run npx playwright@1.63.0 install webkit");
const { webkit } = createRequire(import.meta.url)(npx);

const R = `(e) => { if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }`;
const LOOK = `(sels) => { const keys = ["font","fontSize","fontWeight","lineHeight","color","backgroundColor","backgroundImage","borderRadius","boxShadow","padding","margin","border","borderBottom","width","height","gap","textAlign","cornerShape"];
  const out = {}; for (const s of sels) { const e = document.querySelector(s); if (!e) { out[s] = null; continue; }
  const cs = getComputedStyle(e), r = e.getBoundingClientRect(), o = { rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], text: (e.textContent || "").trim().replace(/\\s+/g, " ").slice(0, 80) };
  keys.forEach((k) => { o[k] = cs[k]; }); out[s] = o; } return out; }`;

async function openHome(browser) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: UA, ignoreHTTPSErrors: true });
  await page.goto(HOME, { timeout: 60000 });
  await page.evaluate((t) => document.body.style.setProperty("--ah-safe-top", t + "px"), SAFE);
  for (let t = 0; t < 12000; t += 250) {
    if (await page.evaluate(() => !!(window.Y && window.Y.wocg && window.Y.wocg.TableBar && document.querySelector("#chromePill.homeMode")))) break;
    await sleep(250);
  }
  // The peek comes 900ms after the launch; wait it out, then send it away
  for (let t = 0; t < 6000; t += 250) {
    if (await page.$(".ahPeekNo")) break;
    await sleep(250);
  }
  const no = await page.$(".ahPeekNo");
  if (no) { await no.click().catch(() => {}); await sleep(900); }
  await page.evaluate(() => document.querySelectorAll(".ahPeek").forEach((n) => n.remove()));
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1200);
  return page;
}
const shot = (page, name) => page.screenshot({ path: path.join(DIR, name), type: "jpeg", quality: 86 });

const browser = await webkit.launch();
const out = {}, styles = {};
try {
  let page = await openHome(browser);
  await shot(page, "home.jpg");
  out.home = await page.evaluate(`(() => { const R = ${R}; return { pillL: R(document.getElementById("chromePill")), pillR: R(document.getElementById("chromePillRight")),
    cells: Array.from(document.querySelectorAll("#chromePillRight #userBar > li")).map((c) => ({ cls: c.className, rect: R(c) })) }; })()`);

  await page.click("#chromePill .playCell");
  await sleep(1200);
  // The head's count comes when the venue answers (TableBar askOpenCounts)
  await sleep(1500);
  await shot(page, "home-play.jpg");
  out.play = await page.evaluate(`(() => { const R = ${R}; const d = document.querySelector("#chromePill .playDropdown");
    return { menu: R(d), head: R(d.querySelector(".playHead")), game: R(d.querySelector(".playGame")), open: R(d.querySelector(".playOpen")),
      card: R(d.querySelector(".homeCard")), rows: Array.from(d.querySelectorAll(".homeCard > li")).map((e) => ({ text: e.textContent.trim(), rect: R(e) })),
      html: d.outerHTML.slice(0, 2000) }; })()`);
  styles.play = await page.evaluate(`(${LOOK})(["#chromePill", "#chromePill .playCell", "#chromePill .playDropdown", "#chromePill .playHead", "#chromePill .playGame",
    "#chromePill .playOpen", "#chromePill .homeCard", "#chromePill .homeCard > li", "#chromePill .homeCard > li:nth-child(2)"])`);
  await page.close();

  page = await openHome(browser);
  await page.click("#chromePillRight .activityIcon");
  await sleep(1400);
  await shot(page, "home-activity.jpg");
  out.activity = await page.evaluate(`(() => { const R = ${R}; const d = document.querySelector("#chromePillRight .activityDropdown");
    return d && { menu: R(d), head: R(d.querySelector(".activityHeader")), title: R(d.querySelector(".activityTitle")), count: R(d.querySelector(".activityCount")),
      content: R(d.querySelector(".activityDropdownContent")), html: d.outerHTML.slice(0, 1600) }; })()`);
  styles.activity = await page.evaluate(`(${LOOK})(["#chromePillRight .activityDropdown", "#chromePillRight .activityHeader", "#chromePillRight .activityTitle",
    "#chromePillRight .activityCount", "#chromePillRight .activityDropdownContent", "#chromePillRight .activityEmpty", "#chromePillRight .activityItem"])`);
  await page.close();

  page = await openHome(browser);
  await page.click("#chromePillRight .userAvatarContainer");
  await sleep(1400);
  await shot(page, "home-account.jpg");
  out.account = await page.evaluate(`(() => { const R = ${R}; const d = document.querySelector("#chromePillRight .userDropdown");
    return d && { menu: R(d), head: R(d.querySelector(".mphead")), items: Array.from(d.querySelectorAll(".dropdownItem")).filter((e) => e.getClientRects().length).map((e) => ({ text: e.textContent.trim(), rect: R(e) })) }; })()`);
  styles.account = await page.evaluate(`(${LOOK})(["#chromePillRight .userDropdown", "#chromePillRight .userDropdown .mphead", "#chromePillRight .userDropdown .dropdownItem"])`);
  await page.close();

  page = await openHome(browser);
  await page.evaluate((g) => window.Y.wocg.FooterBar.gameHelpClickHandler(null, g), GAME);
  await sleep(2600);
  await shot(page, "home-rules.jpg");
  await page.close();

  fs.writeFileSync(path.join(DIR, "capture.json"), JSON.stringify(out, null, 1));
  fs.writeFileSync(path.join(DIR, "styles.json"), JSON.stringify(styles, null, 1));
  console.log(JSON.stringify({ play: out.play && out.play.rows, activity: out.activity && out.activity.head, account: out.account && out.account.items }));
} finally {
  await browser.close();
}
