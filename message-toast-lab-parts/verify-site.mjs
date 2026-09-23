// Checks the notice column on the dev site (MESSAGE-TOAST.md in the wocg repo): the notice's motion, its word
// and number changes, and the toast docked under it, at desktop and both iPhone sizes, then the classic path
// with the flag off. Chrome for Testing through the sweep's driver, a throwaway guest profile per size, closed in
// a finally. Run: node verify-site.mjs [desktop,landscape,portrait] [--flag-off]
import fs from "node:fs";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import * as client from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/client.mjs";

const BASE = "https://dev.worldofcardgames.com";
const UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1";
const SIZES = {
  desktop: { width: 1200, height: 800, dsf: 1 },
  landscape: { width: 750, height: 340, dsf: 1, mobile: true, userAgent: UA, platform: "iPhone" },
  portrait: { width: 390, height: 664, dsf: 1, mobile: true, userAgent: UA, platform: "iPhone" }
};
const only = process.argv[2] ? process.argv[2].split(",") : Object.keys(SIZES);
const flagOff = process.argv.includes("--flag-off");
const SHOTS = "/tmp/notice-verify-shots";
fs.mkdirSync(SHOTS, { recursive: true });

// Runs inside the page
const H = `
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const T = () => Y.wocg.Table.getCurrentTable();
const boxEl = () => document.querySelector(".spot-messageBox");
const boxY = () => Y.one(".spot-messageBox");
const colEl = () => document.querySelector(".noticeColumn");
const toastEl = () => document.getElementById("Notice");
const r = (el) => { if (!el) return null; const q = el.getBoundingClientRect(); return { x: Math.round(q.left * 10) / 10, y: Math.round(q.top * 10) / 10, w: Math.round(q.width * 10) / 10, h: Math.round(q.height * 10) / 10, b: Math.round(q.bottom * 10) / 10 }; };
const tx = (el) => { const t = getComputedStyle(el).transform; return t === "none" ? 0 : Math.round(new DOMMatrix(t).m41); };
function frames(ms, fn) {
  return new Promise((res) => { const out = []; const t0 = performance.now(); (function f() { out.push(Object.assign({ t: Math.round(performance.now() - t0) }, fn())); if (performance.now() - t0 < ms) requestAnimationFrame(f); else res(out); })(); });
}
async function clear() {
  if (Y.Notice) Y.Notice.hide();
  if (T().tableErrorText) T().hideTableError();
  T().hideMessage();
  await sleep(700);
}
const BUTTONS = [{ text: "Start with bots", shortText: "Add bots", className: "blue" }, { text: "Invite players", className: "blue inviteLink" }];
`;

const SCENARIOS = {
  // The notice comes out of the edge, rests, goes back in, and leaves the layout
  enterLeave: `
    await clear();
    T().showMessage("Hearts broken!", { duration: 900 });
    const s = await frames(1500, () => { const b = boxEl(); return { d: getComputedStyle(b).display, tx: tx(b), op: getComputedStyle(b).opacity }; });
    const rest = s.find((x) => x.t >= 450);
    return { startTx: s[1].tx, restTx: rest.tx, restDisplay: rest.d, endDisplay: s[s.length - 1].d, state: boxY().noticeState, current: T().currentMessageText,
      pass: s[1].tx < -50 && rest.tx === 0 && rest.d === "block" && s[s.length - 1].d === "none" && T().currentMessageText === null };
  `,
  // A hide and a show 4ms apart (the bot bids) read as one change of words: the box never leaves the layout
  botBids: `
    await clear();
    T().showMessage("Waiting for Tin Man to bid.", { duration: 60000 });
    await sleep(600);
    const run = frames(1300, () => { const b = boxEl(); return { d: getComputedStyle(b).display, tx: tx(b), old: b.querySelectorAll(".noticeOld").length, text: b.querySelector(".noticeBody:not(.noticeOld)").textContent }; });
    T().hideMessage();
    await sleep(4);
    T().showMessage("Waiting for EVE to bid.", { duration: 60000 });
    const s = await run;
    const minTx = Math.min.apply(null, s.map((x) => x.tx));
    return { everNone: s.some((x) => x.d === "none"), minTx, sawOld: s.some((x) => x.old > 0), endText: s[s.length - 1].text, endTx: s[s.length - 1].tx,
      pass: !s.some((x) => x.d === "none") && s[s.length - 1].text.indexOf("EVE") >= 0 && s[s.length - 1].tx === 0 };
  `,
  // The countdown's number rolls alone, from the top, and the words stay
  countdown: `
    await clear();
    T().showMessage("Table is full. Game will start in <b>10 seconds</b>.", { duration: 60000, scope: "table" });
    await sleep(600);
    const w0 = boxEl().getBoundingClientRect().width;
    T().showMessage("Table is full. Game will start in <b>9 seconds</b>.", { duration: 60000, scope: "table" });
    const s = await frames(950, () => { const b = boxEl(); const reel = b.querySelector(".noticeReel"); const strip = b.querySelector(".noticeReelStrip");
      return { reel: !!reel, down: !!(strip && strip.classList.contains("noticeDown")), old: b.querySelectorAll(".noticeOld").length, w: Math.round(b.getBoundingClientRect().width), text: b.textContent }; });
    const widths = s.map((x) => x.w);
    let jump = 0; for (let i = 1; i < widths.length; i++) jump = Math.max(jump, Math.abs(widths[i] - widths[i - 1]));
    const end = s[s.length - 1];
    return { sawReel: s.some((x) => x.reel), rolledDown: s.some((x) => x.down), wordsSwapped: s.some((x) => x.old > 0), endReel: end.reel, endText: end.text, w0: Math.round(w0), wEnd: end.w, maxWidthStepPerFrame: jump,
      pass: s.some((x) => x.reel && x.down) && !s.some((x) => x.old > 0) && !end.reel && end.text.indexOf("9 seconds") >= 0 };
  `,
  // Other words blur out and in where they stand, and the paper glides to its new size
  words: `
    await clear();
    T().showMessage("Waiting for R2-D2 to play.", { duration: 60000 });
    await sleep(600);
    T().showMessage("Play a card from your hand, the highest heart if you can.", { duration: 60000 });
    const s = await frames(1000, () => { const b = boxEl(); return { old: b.querySelectorAll(".noticeOld").length, inlineW: b.style.width, h: Math.round(b.getBoundingClientRect().height), text: b.querySelector(".noticeBody:not(.noticeOld)").textContent }; });
    const heights = s.map((x) => x.h); let jump = 0; for (let i = 1; i < heights.length; i++) jump = Math.max(jump, Math.abs(heights[i] - heights[i - 1]));
    const end = s[s.length - 1];
    return { sawOld: s.some((x) => x.old > 0), glided: s.some((x) => x.inlineW), endOld: end.old, endInline: end.inlineW, hStart: heights[0], hEnd: end.h, maxHeightStepPerFrame: jump, endText: end.text,
      pass: s.some((x) => x.old > 0) && end.old === 0 && !end.inlineW && end.text.indexOf("Play a card") === 0 };
  `,
  // A toast with no notice takes the notice's place and the notice's look
  toastAlone: `
    await clear();
    Y.fire("Notice:show", { message: "Can't chat with bots.", type: "warning", duration: 1400 });
    await sleep(500);
    const t = toastEl(), c = colEl(), cs = getComputedStyle(t), bs = getComputedStyle(boxEl());
    const out = { inColumn: t.parentNode === c, toast: r(t), column: r(c), font: cs.fontSize + "/" + cs.lineHeight, boxFont: bs.fontSize + "/" + bs.lineHeight, shadow: cs.boxShadow, boxShadow: bs.boxShadow, radius: cs.borderRadius, boxRadius: bs.borderRadius, padding: cs.padding, boxPadding: bs.padding, tx: tx(t) };
    await sleep(1600);
    out.goneDisplay = getComputedStyle(t).display; out.visible = Y.Notice.isVisible();
    out.pass = out.inColumn && Math.abs(out.toast.y - out.column.y) <= 1 && out.font === out.boxFont && out.shadow === out.boxShadow && out.padding === out.boxPadding && out.tx === 0 && out.goneDisplay === "none" && !out.visible;
    return out;
  `,
  // A toast under a notice: 8px down, at least as wide
  toastUnder: `
    await clear();
    T().showMessage("Hearts broken!", { duration: 60000 });
    await sleep(500);
    Y.fire("Notice:show", { message: "The server goes down for maintenance in about ten minutes. It comes straight back.", type: "warning", duration: 60000 });
    await sleep(600);
    const b = r(boxEl()), t = r(toastEl());
    const out = { box: b, toast: t, gap: Math.round((t.y - b.b) * 10) / 10, sameLeft: Math.abs(t.x - b.x) <= 1, atLeastAsWide: t.w >= b.w - 1, inColumn: toastEl().parentNode === colEl() };
    out.pass = out.inColumn && Math.abs(out.gap - 8) <= 1 && out.sameLeft && out.atLeastAsWide;
    return out;
  `,
  // A notice arrives over a toast: the toast glides down, then stands 8px under the notice
  noticeOverToast: `
    await clear();
    Y.fire("Notice:show", { message: "Game will pause if all players agree. Use Resume to cancel your request.", duration: 60000 });
    await sleep(600);
    const y0 = r(toastEl()).y;
    T().showMessage("You requested to pause the game. 1 of 2 votes needed to pause.", { duration: 60000 });
    const s = await frames(700, () => ({ ty: r(toastEl()).y, bx: tx(boxEl()) }));
    let jump = 0; for (let i = 1; i < s.length; i++) jump = Math.max(jump, Math.abs(s[i].ty - s[i - 1].ty));
    const b = r(boxEl()), t = r(toastEl());
    const out = { toastStartY: y0, firstFrameY: s[0].ty, maxStepPerFrame: Math.round(jump), gap: Math.round((t.y - b.b) * 10) / 10, boxTx: tx(boxEl()) };
    out.pass = Math.abs(s[0].ty - y0) <= 2 && Math.abs(out.gap - 8) <= 1 && out.boxTx === 0 && jump < 40;
    return out;
  `,
  // The notice leaves from above a toast: the toast glides up into its place
  noticeLeavesOverToast: `
    await clear();
    T().showMessage("Hearts broken!", { duration: 900 });
    await sleep(400);
    Y.fire("Notice:show", { message: "The server goes down for maintenance in about ten minutes. It comes straight back.", type: "warning", duration: 60000 });
    await sleep(350);
    const w0 = r(toastEl()).w;
    const s = await frames(1100, () => ({ ty: r(toastEl()).y, tw: r(toastEl()).w, d: getComputedStyle(boxEl()).display }));
    let jump = 0; for (let i = 1; i < s.length; i++) jump = Math.max(jump, Math.abs(s[i].ty - s[i - 1].ty));
    const c = r(colEl()), end = s[s.length - 1];
    const out = { startY: s[0].ty, endY: end.ty, columnY: c.y, maxStepPerFrame: Math.round(jump), widthBefore: w0, widthAfter: end.tw, boxDisplay: end.d };
    out.pass = end.d === "none" && Math.abs(end.ty - c.y) <= 1 && jump < 40 && end.tw >= w0 - 1;
    return out;
  `,
  // The tallest stack: the waiting notice with its buttons and the longest toast; it may not reach your cards
  floor: `
    await clear();
    T().showMessage("Private table <b>Friday night</b> starts when full.", { duration: 60000, buttons: BUTTONS });
    await sleep(600);
    Y.fire("Notice:show", { message: "Multiplayer is disabled on VPN or proxy connections. Turn off your VPN to play with other people.", type: "warning", duration: 60000 });
    await sleep(600);
    const t = toastEl(), docked = t.parentNode === colEl();
    const floor = T().noticeFloor();
    const out = { docked, toast: r(t), column: r(colEl()), floor: Math.round(floor), columnBottom: r(colEl()).b };
    out.pass = docked ? out.columnBottom <= floor + 1 : (t.parentNode.id === "NoticeContainer" && getComputedStyle(t.parentNode).display === "block");
    return out;
  `,
  // The red connection box with a toast under it
  redBox: `
    await clear();
    T().showMessage("Connection problem, reconnecting...", { duration: 60000, prefix: "alert", prefixLabel: "Notice" });
    await sleep(500);
    Y.fire("Notice:show", { message: "Connecting to server, please wait...", duration: 60000 });
    await sleep(600);
    const b = r(boxEl()), t = r(toastEl());
    const out = { red: boxEl().classList.contains("resync"), gap: Math.round((t.y - b.b) * 10) / 10, boxBg: getComputedStyle(boxEl()).backgroundColor, toastBg: getComputedStyle(toastEl()).backgroundColor };
    out.pass = out.red && Math.abs(out.gap - 8) <= 1 && out.boxBg !== out.toastBg;
    return out;
  `,
  // Reduced motion or Animations Off: a fade, nothing travels
  calm: `
    await clear();
    const keep = Y.wocg.calmTableMotion; Y.wocg.calmTableMotion = () => true;
    try {
      T().showMessage("Hearts broken!", { duration: 500 });
      const s = await frames(900, () => { const b = boxEl(); return { tx: tx(b), op: parseFloat(getComputedStyle(b).opacity), d: getComputedStyle(b).display }; });
      const moved = s.some((x) => x.tx !== 0 && x.d !== "none");
      const faded = s.some((x) => x.op > 0 && x.op < 1);
      return { moved, faded, endDisplay: s[s.length - 1].d, pass: !moved && faded && s[s.length - 1].d === "none" };
    } finally { Y.wocg.calmTableMotion = keep; }
  `,
  // A table error hides the notice and gives back only a message still showing (the stale message bug)
  staleMessage: `
    await clear();
    T().showMessage("Spades broken!", { duration: 400 });
    await sleep(900);
    T().showTableError("Enjoying the game? Bookmark us!", 600, "tip");
    await sleep(1300);
    const b = boxEl();
    return { display: getComputedStyle(b).display, text: b.textContent, pass: getComputedStyle(b).display === "none" };
  `,
  // Leaving the table with a toast up: the toast goes back to its own place and the column goes
  leave: `
    await clear();
    Y.fire("Notice:show", { message: "No hint available right now.", duration: 60000 });
    await sleep(500);
    const wasDocked = toastEl().parentNode === colEl();
    return { wasDocked };
  `
};

async function runSize(name) {
  const v = SIZES[name];
  const b = new Browser({ profileDir: "/tmp/notice-verify-" + name, viewport: v, log: () => {} });
  fs.rmSync("/tmp/notice-verify-" + name, { recursive: true, force: true });
  const out = { size: name, results: {} };
  try {
    await b.launch();
    await b.navigate(BASE + "/hearts" + (flagOff ? "?lobby=0" : ""), { timeout: 60000 });
    const t = await b.evaluate(client.waitBotsTable(), { timeout: 90000 });
    out.table = t.table;
    if (!t.table) throw new Error("no bots table");
    out.wm = await b.evaluate(`return document.body.classList.contains("wm")`);
    if (flagOff) {
      out.results = await b.evaluate(H + `
        const res = {};
        res.column = !!colEl();
        await clear();
        T().showMessage("Hearts broken!", { duration: 60000 });
        await sleep(400);
        T().hideMessage();
        await sleep(500);
        res.afterHide = { display: getComputedStyle(boxEl()).display, current: T().currentMessageText };
        T().showMessage("Waiting for Tin Man to bid.", { duration: 60000 });
        await sleep(300);
        T().hideMessage(); await sleep(4);
        T().showMessage("Waiting for EVE to bid.", { duration: 60000 });
        await sleep(600);
        res.afterBlink = { display: getComputedStyle(boxEl()).display, opacity: getComputedStyle(boxEl()).opacity, text: boxEl().textContent };
        Y.fire("Notice:show", { message: "Can't chat with bots.", duration: 60000 });
        await sleep(500);
        res.toastParent = toastEl().parentNode.id;
        res.pass = !res.column && res.afterHide.display === "none" && res.afterHide.current === null && res.afterBlink.display === "block" && res.afterBlink.opacity === "1" && res.afterBlink.text.indexOf("EVE") >= 0 && res.toastParent === "NoticeContainer";
        return res;
      `, { timeout: 60000 });
    } else {
      for (const [id, code] of Object.entries(SCENARIOS)) {
        try {
          out.results[id] = await b.evaluate(H + code, { timeout: 60000 });
        } catch (e) {
          out.results[id] = { error: String(e.message || e).slice(0, 300), pass: false };
        }
        if (id === "floor" || id === "toastUnder" || id === "countdown") {
          const s = await b.send("Page.captureScreenshot", { format: "png" });
          fs.writeFileSync(SHOTS + "/" + name + "-" + id + ".png", Buffer.from(s.data, "base64"));
        }
      }
      // leave the table with the toast up
      await b.evaluate(client.leaveTable(), { timeout: 30000 });
      await new Promise((res) => setTimeout(res, 1500));
      // A game page deals a new solo table at once: the toast moves from the old table's column to the new one's
      out.results.leave.after = await b.evaluate(`const t = document.getElementById("Notice"); const cols = document.querySelectorAll(".noticeColumn"); return { parentClass: t.parentNode.className || t.parentNode.id, columns: cols.length, inNewColumn: cols.length === 1 && t.parentNode === cols[0], visible: Y.Notice.isVisible(), table: !!Y.wocg.Table.getCurrentTable() };`);
      const a = out.results.leave.after;
      out.results.leave.pass = out.results.leave.wasDocked && a.columns === 1 && (a.table ? a.inNewColumn : a.parentClass === "NoticeContainer");
      // The lobby keeps the toast under the menu bar
      await b.navigate(BASE + "/", { timeout: 60000 });
      await b.evaluate(client.waitReady(30000), { timeout: 40000 });
      out.results.lobby = await b.evaluate(`
        const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
        const table = !!(Y.wocg.Table.getCurrentTable && Y.wocg.Table.getCurrentTable());
        Y.fire("Notice:show", { message: "No available seats.", duration: 3000 });
        await sleep(600);
        const t = document.getElementById("Notice"), q = t.getBoundingClientRect(), c = t.parentNode.getBoundingClientRect();
        const res = { table, parent: t.parentNode.id, containerDisplay: getComputedStyle(t.parentNode).display, x: Math.round(q.left), w: Math.round(q.width), containerW: Math.round(c.width), y: Math.round(q.top), column: !!document.querySelector(".noticeColumn") };
        res.centred = Math.abs((q.left + q.width / 2) - (c.left + c.width / 2)) <= 2;
        res.pass = !table && res.parent === "NoticeContainer" && res.containerDisplay === "block" && res.centred && !res.column;
        return res;
      `, { timeout: 30000 });
    }
    out.errors = b.takeErrors().filter((e) => !/favicon|ERR_|net::/.test(e.text));
  } catch (e) {
    out.fatal = String(e.message || e);
  } finally {
    await b.close();
  }
  return out;
}

const all = [];
for (const name of only) {
  const r = await runSize(name);
  all.push(r);
  console.log("== " + name + (flagOff ? " (flag off)" : "") + " wm=" + r.wm + (r.fatal ? " FATAL " + r.fatal : ""));
  if (flagOff) console.log("  ", JSON.stringify(r.results));
  else for (const [id, res] of Object.entries(r.results)) console.log("  " + (res.pass ? "PASS" : "FAIL") + " " + id.padEnd(22) + JSON.stringify(Object.fromEntries(Object.entries(res).filter(([k]) => k !== "pass"))).slice(0, 420));
  if (r.errors && r.errors.length) console.log("   errors:", JSON.stringify(r.errors).slice(0, 800));
}
fs.writeFileSync("/tmp/notice-verify.json", JSON.stringify(all, null, 1));
