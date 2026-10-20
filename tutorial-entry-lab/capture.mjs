// Run: node tutorial-entry-lab/capture.mjs   (from Design/WoCG-3; dev must be up; writes into tutorial-entry-lab/)
// Copies what tutorial-entry-lab.html needs off dev, in WebKit (the app's WKWebView engine) with an iPhone user agent,
// as the iPhone Air draws the Canasta app (420 by 912, safe area 68 on top, 2x):
//   home.jpg, home-full.jpg      the app home's first screen and the whole page (capture.json has the sections' boxes)
//   home-play.jpg                the home with the Play pill's menu open
//   home-rules.jpg               the How to play box the menu's Rules row opens
//   tutorial-1.jpg, -2.jpg       the tutorial in the app: its first line, and four Nexts later
//   table.jpg                    a solo table after the deal
//   table-panel.jpg, -rules.jpg  the table's Table panel, and its Rules box
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DIR = path.dirname(new URL(import.meta.url).pathname);
const DEV = "https://dev.worldofcardgames.com";
const GAME = "canasta";
const HOME = `${DEV}/?platform=mobile&platform-gameid=${GAME}&apphome=1`;
const UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148";
const W = 420, H = 912, SAFE = 68;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const npx = execSync("ls -d ~/.npm/_npx/*/node_modules/playwright 2>/dev/null | head -1", { shell: "/bin/zsh" }).toString().trim();
if (!npx) throw new Error("no playwright in the npx cache: run npx playwright@1.63.0 install webkit");
const { webkit } = createRequire(import.meta.url)(npx);

const P = (n, u, avatar, extra) => Object.assign({ n, u, avatar, completionRate: 95, nFinishedGames: 30 }, extra || {});
const TABLES = [
  { id: `${GAME}-9001`, gameid: GAME, seats: 4, seatsRemaining: 1, openSeatPositions: [3], started: true, age: 12, e: [], ranked: false,
    players: [P(0, "PorchPete", "AnimalBeaver"), P(1, "PeachyPam", "AnimalCat"), P(2, "TractorTed", "AnimalBird", { isBot: true })] },
  { id: `${GAME}-9002`, gameid: GAME, seats: 4, seatsRemaining: 2, openSeatPositions: [2, 3], started: false, age: 0, e: [], ranked: true,
    players: [P(0, "QuicktoPlay", "AnimalChicken"), P(1, "zshell", "AnimalBee", { isLiked: true })] }
];
const R = `(e) => { if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; }`;

async function openHome(browser) {
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: UA, ignoreHTTPSErrors: true });
  await page.goto(HOME, { timeout: 60000 });
  await page.evaluate((t) => document.body.style.setProperty("--ah-safe-top", t + "px"), SAFE);
  for (let t = 0; t < 10000; t += 250) {
    if (await page.evaluate(() => !!document.querySelector("#ahGrid .ahTile") || !!(window.Y && window.Y.wocg && window.Y.wocg.User && document.querySelector("#ahGrid")))) break;
    await sleep(250);
  }
  await page.evaluate(([tables, game]) => window.Y.fire("comm:lobby.recommendations", { openCounts: { [game]: 7 }, tables }), [TABLES, GAME]);
  await sleep(2600);
  return page;
}
const shot = (page, name, full) => page.screenshot({ path: path.join(DIR, name), type: "jpeg", quality: 84, fullPage: !!full });

const browser = await webkit.launch();
const out = {};
try {
  let page = await openHome(browser);
  await shot(page, "home.jpg");
  await shot(page, "home-full.jpg", true);
  out.home = await page.evaluate(`(() => { const R = ${R}; return {
    page: [document.documentElement.scrollWidth, document.documentElement.scrollHeight],
    top: R(document.getElementById("ahTop")), doors: R(document.querySelector(".ahDoors") || document.getElementById("ahJoin").parentNode),
    capsule: R(document.getElementById("ahCapsule")),
    secs: Array.from(document.querySelectorAll(".ahSec")).map((s) => ({ id: s.id, rect: R(s) })), foot: R(document.getElementById("ahFoot")),
    pillL: R(document.getElementById("chromePill")), pillR: R(document.getElementById("chromePillRight")) }; })()`);

  await page.click("#chromePill .playCell");
  await sleep(1200);
  await shot(page, "home-play.jpg");
  out.playMenu = await page.evaluate(`(() => { const R = ${R}; const rows = Array.from(document.querySelectorAll("#chromePill .homeCard *")).filter((e) => e.children.length === 0 && e.textContent.trim());
    return rows.map((e) => ({ text: e.textContent.trim(), rect: R(e) })); })()`);
  await page.close();

  page = await openHome(browser);
  await page.evaluate((g) => window.Y.wocg.FooterBar.gameHelpClickHandler(null, g), GAME);
  await sleep(2600);
  await shot(page, "home-rules.jpg");
  await page.close();

  page = await openHome(browser);
  await page.evaluate((g) => window.Y.fire("comm:table.create", { gameid: g, tutorial: true }), GAME);
  await sleep(6000);
  await shot(page, "tutorial-1.jpg");
  for (let i = 0; i < 4; i++) {
    const next = await page.$("text=Next");
    if (next) await next.click().catch(() => {});
    await sleep(2600);
  }
  await shot(page, "tutorial-2.jpg");
  await page.close();

  page = await openHome(browser);
  await page.click("#ahSolo");
  await sleep(14000);
  await shot(page, "table.jpg");
  out.table = await page.evaluate(`(() => { const R = ${R}; return { pillL: R(document.getElementById("chromePill")), pillR: R(document.getElementById("chromePillRight")),
    notice: R(document.querySelector("#noticePanel")), tableCell: R(document.querySelector("#chromePill .tableCell")) }; })()`);
  await page.click("#chromePill .tableCell");
  await sleep(1400);
  await shot(page, "table-panel.jpg");
  out.panel = await page.evaluate(`(() => { const R = ${R}; const p = document.querySelector("#tableInfo, .tableInfo"); return { panel: R(p),
    buttons: Array.from(document.querySelectorAll(".tableInfoActions .infoBtn")).map((b) => ({ text: b.textContent.trim(), rect: R(b) })) }; })()`);
  const rules = await page.$(".tableInfoActions .rulesRow");
  if (rules) await rules.click();
  await sleep(2600);
  await shot(page, "table-rules.jpg");
  await page.close();

  fs.writeFileSync(path.join(DIR, "capture.json"), JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
} finally {
  await browser.close();
}
