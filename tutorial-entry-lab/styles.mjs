// Run: node tutorial-entry-lab/styles.mjs   (from Design/WoCG-3; dev must be up; writes tutorial-entry-lab/styles.json)
// The computed look of the app's pieces the lab draws again (the capsule, a door, a card and its head, a green button,
// the pills, the Play menu, the How to play box, the table's notice and Table panel), in WebKit as an iPhone sees them.
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DIR = path.dirname(new URL(import.meta.url).pathname);
const HOME = "https://dev.worldofcardgames.com/?platform=mobile&platform-gameid=canasta&apphome=1";
const UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const npx = execSync("ls -d ~/.npm/_npx/*/node_modules/playwright 2>/dev/null | head -1", { shell: "/bin/zsh" }).toString().trim();
const { webkit } = createRequire(import.meta.url)(npx);

const LOOK = `(sels) => { const keys = ["font","color","backgroundColor","backgroundImage","borderRadius","boxShadow","padding","border","width","height","textShadow","letterSpacing","gap"];
  const out = {}; for (const s of sels) { const e = document.querySelector(s); if (!e) { out[s] = null; continue; }
  const cs = getComputedStyle(e), r = e.getBoundingClientRect(), o = { rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], text: (e.textContent || "").trim().slice(0, 60) };
  keys.forEach((k) => { o[k] = cs[k]; }); out[s] = o; } return out; }`;

const browser = await webkit.launch();
const out = {};
try {
  const page = await browser.newPage({ viewport: { width: 420, height: 912 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: UA, ignoreHTTPSErrors: true });
  await page.goto(HOME, { timeout: 60000 });
  await page.evaluate(() => document.body.style.setProperty("--ah-safe-top", "68px"));
  await sleep(5000);
  out.home = await page.evaluate(`(${LOOK})(["body", "#ahSheet", "#ahCapsule", "#ahCapsule .ahDot", "#ahCapsule .ahLiveText", ".ahDoors", "#ahJoin", "#ahJoin .ahDl", "#ahJoin .ahDm",
    "#ahDeal", "#ahDeal .ahHead", "#ahDeal .ahHead h2", "#ahTablesSec .ahHead h2 small", "#ahDealPlay", "#ahDstat, .ahDstat", "#chromePill", "#chromePill .playCell", "#chromePillRight"])`);
  await page.click("#chromePill .playCell");
  await sleep(1200);
  out.menu = await page.evaluate(`(${LOOK})(["#chromePill .homeCard", "#chromePill .homeCard > *", "#chromePill .homeCard *:not(:has(*))", ".pillDropdown, #chromePill .dropdown", "#chromePill .ddHead, #chromePill .homeHead"])`);
  out.menuHtml = await page.evaluate(() => { const c = document.querySelector("#chromePill .homeCard"); return c ? c.parentNode.outerHTML.slice(0, 3000) : null; });
  await page.close();

  const p2 = await browser.newPage({ viewport: { width: 420, height: 912 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: UA, ignoreHTTPSErrors: true });
  await p2.goto(HOME, { timeout: 60000 });
  await sleep(5000);
  await p2.evaluate(() => window.Y.wocg.FooterBar.gameHelpClickHandler(null, "canasta"));
  await sleep(2600);
  out.help = await p2.evaluate(`(${LOOK})(["#ModalHelp .wmPanel", "#ModalHelp .wmBox", "#ModalHelp .wmTitle", "#ModalHelp .wmTxt", "#ModalHelp .wmLink", "#ModalHelp .wmClose", "#ModalHelp .wmBtn"])`);
  await p2.click("#ModalHelp .wmClose").catch(() => {});
  await sleep(800);
  await p2.click("#ahSolo");
  await sleep(14000);
  out.table = await p2.evaluate(`(() => { const n = Array.from(document.querySelectorAll("div")).find((d) => d.children.length < 3 && /Pick a card from the stock/.test(d.textContent) && d.getBoundingClientRect().width < 340);
    if (n) n.setAttribute("data-lab-notice", "1"); return (${LOOK})(["[data-lab-notice]", "#chromePill", "#chromePill .tableCell"]); })()`);
  out.noticeClass = await p2.evaluate(() => { const n = document.querySelector("[data-lab-notice]"); return n ? n.className + " / parent " + n.parentNode.className : null; });
  await p2.click("#chromePill .tableCell");
  await sleep(1400);
  out.panel = await p2.evaluate(`(${LOOK})(["#tableInfo", ".tableInfo", ".tableInfoActions .infoBtn", ".tableInfoActions .infoBug", ".infoTitle"])`);
  fs.writeFileSync(path.join(DIR, "styles.json"), JSON.stringify(out, null, 1));
  console.log("ok");
} finally {
  await browser.close();
}
