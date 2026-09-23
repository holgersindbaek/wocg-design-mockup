// Captures the felt for message-toast-lab.html from the real dev site: a Hearts bots table mid-hand at the three
// sizes the sweep shoots (desktop 1200x800, iPhone landscape 750x340, iPhone portrait 390x664 with and without the
// 100px top ad band), as static HTML with the live message box and the toast taken out. On the same live page it
// measures what Table.js and Notice.js write: the message box's inline left, top, max-width, min-width and
// narrowCap for real messages, the toast's container and box, and the rects of the pieces the lab reports against.
//
// Run: node message-toast-lab-parts/capture.mjs [desktop landscape portrait portrait-noads]
// Writes message-toast-lab-parts/snap-<vp>.html and snap-<vp>.json, and a live screenshot to /tmp/mtlab/live-<vp>.png.
// Chrome for Testing only, through the visual sweep's own driver, closed in a finally, with a throwaway profile.
import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import * as client from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/client.mjs";
import { VIEWPORTS } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/scenes.mjs";

const HERE = path.dirname(new URL(import.meta.url).pathname);
const BASE = "https://dev.worldofcardgames.com";
const HOST = "dev.worldofcardgames.com";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const vp = (v) => ({ width: v.width, height: v.height, dsf: 1, mobile: !!v.mobile, platform: v.platform, userAgent: v.userAgent });
const SIZES = {
  "desktop": { viewport: vp(VIEWPORTS["desktop"]), query: "" },
  "landscape": { viewport: vp(VIEWPORTS["iphone-landscape"]), query: "" },
  "portrait": { viewport: vp(VIEWPORTS["iphone-portrait"]), query: "" },
  "portrait-noads": { viewport: vp(VIEWPORTS["iphone-portrait"]), query: "?hideAds=1" }
};

// The messages measured on the live box, written the way their callers write them
const BTN_BOTS = '<div class="button blue"><span class="long">Start with bots</span><span class="short">Add bots</span></div>';
const BTN_INVITE = '<div class="button blue inviteLink">Invite players</div>';
const MESSAGES = [
  { id: "broken", text: "Hearts broken!" },
  { id: "pass", text: "Select 3 cards to pass left." },
  { id: "countdown", text: "Table is full. Game will start in <b>10 seconds</b>." },
  { id: "pauseVote", text: "You requested to pause the game. 1 of 2 votes needed to pause." },
  { id: "waitPublic", text: "Table <b>#12</b> starts when full.", buttonText: BTN_BOTS, extraButtonText: BTN_INVITE },
  { id: "waitPrivate", text: "Private table <b>Friday night</b> starts when full.", buttonText: BTN_BOTS, extraButtonText: BTN_INVITE },
  { id: "cribbage", text: "<strong>14 points for your hand.</strong><br><strong>Fifteen (4♣5♥6♦):</strong> 2 points<br><strong>Fifteen (4♣5♥6♠):</strong> 2 points<br><strong>Fifteen (5♥J♦):</strong> 2 points<br><strong>Pair (6♦6♠):</strong> 2 points<br><strong>Run (4♣5♥6♦):</strong> 3 points<br><strong>Run (4♣5♥6♠):</strong> 3 points", skipPrefix: true },
  { id: "alert", text: "Connection problem, reconnecting...", prefix: "alert", prefixLabel: "Notice" },
  { id: "reload", text: "Connection problem", prefix: "alert", prefixLabel: "Error", buttons: [{ text: "Reload game", className: "red" }] }
];
const TOASTS = [
  { id: "short", message: "Can't chat with bots." },
  { id: "hint", label: "Hint:", message: "Pass the Q♠ and high hearts. Hints can be disabled under settings.", messageHtml: "Pass the Q♠ and high hearts. Hints can be disabled under settings." },
  { id: "vpn", message: "Multiplayer is disabled on VPN or proxy connections. Turn off your VPN to play with other people." }
];

const MEASURE = `
const t = currentTable();
if (t.stopTurnHintTimer) t.stopTurnHintTimer();
if (t.clearTurnHint) t.clearTurnHint({ immediate: true });
Y.fire("Notice:hide");
await sleep(400);
const R = (e) => { const r = e.getBoundingClientRect(); return [+r.x.toFixed(2), +r.y.toFixed(2), +r.width.toFixed(2), +r.height.toFixed(2)]; };
const boxEl = () => document.querySelector(".spot-messageBox");
function readBox() {
  const b = boxEl(), cs = getComputedStyle(b);
  return { cls: b.className, inline: { left: b.style.left, top: b.style.top, maxWidth: b.style.maxWidth, minWidth: b.style.minWidth, marginTop: b.style.marginTop },
    rect: R(b), font: cs.fontSize + "/" + cs.lineHeight, padding: cs.paddingTop + " " + cs.paddingLeft, radius: cs.borderTopLeftRadius,
    html: b.innerHTML };
}
const msgs = ${JSON.stringify(MESSAGES)};
const box = {};
for (const m of msgs) {
  const o = { duration: 120000 };
  if (m.buttonText) { o.buttonText = m.buttonText; o.buttonHandler = function () {}; }
  if (m.extraButtonText) { o.extraButtonText = m.extraButtonText; o.extraButtonHandler = function () {}; }
  if (m.buttons) o.buttons = m.buttons;
  if (m.skipPrefix) o.skipPrefix = true;
  if (m.prefix) { o.prefix = m.prefix; o.prefixLabel = m.prefixLabel; }
  t.showMessage(m.text, o);
  await sleep(320);
  box[m.id] = readBox();
  t.hideMessage();
  await sleep(260);
}
// The bookmark tip goes through showTableError, as the page does it (Table.js:464)
t.showTableError("Enjoying the game? Bookmark us with <b>⌘ + D</b> or tap ★ in your browser!", 0, "tip");
await sleep(320);
box.tip = readBox();
t.hideTableError();
await sleep(260);
// hideTableError draws again the message that was up before the tip, even though that one was hidden long ago: the
// "Connection problem" box above comes back. Record it, then hide it for good.
const cameBack = boxEl().style.display === "block" && boxEl().style.opacity === "1" ? boxEl().textContent : null;
t.hideMessage();
await sleep(300);
// After a hide: what the defect leaves on the box (Table.js hideMessage's cb is dropped by Y.Transition.Sequence)
const b = boxEl();
const afterHide = { display: b.style.display, opacity: b.style.opacity, pointerEvents: b.style.pointerEvents, computedDisplay: getComputedStyle(b).display,
  currentMessageText: t.currentMessageText, hasCurrentMessage: !!t.currentMessage };
const toast = {};
for (const o of ${JSON.stringify(TOASTS)}) {
  Y.fire("Notice:show", Object.assign({ duration: false }, o));
  await sleep(450);
  const c = document.querySelector("#NoticeContainer"), n = document.querySelector("#Notice"), cs = getComputedStyle(n);
  toast[o.id] = { container: { top: c.style.top, paddingTop: c.style.paddingTop, left: c.style.left, width: c.style.width }, cls: n.className,
    rect: R(n), font: cs.fontSize + "/" + cs.lineHeight, padding: cs.paddingTop + " " + cs.paddingLeft, radius: cs.borderTopLeftRadius, fontFamily: cs.fontFamily };
  Y.fire("Notice:hide");
  await sleep(320);
}
return { box, afterHide, cameBack, toast, gutter: Y.wocg.playspaceGutter(), rail: Y.wocg.rightRailAdWidth ? Y.wocg.rightRailAdWidth() : null,
  compact: Y.wocg.isPlayspaceCompact ? Y.wocg.isPlayspaceCompact() : null, safeTop: Y.wocg.safeAreaTop ? Y.wocg.safeAreaTop() : null };
`;

// Plays the human seat until the hand is under way: the pass (when there is one) and two cards, then waits until the
// bots are adding to a trick with every card face up and still, and takes the snapshot and the rects in that same step.
const SNAP = `
const t = currentTable(), g = t.game, hand = t.getSpot("hand0"), play = t.getSpot("play");
const t0 = Date.now();
let played = 0, passed = false;
// every card in the trick face up and still: a card on its way is drawn at its end place with its back still showing
function trickAtRest() {
  const els = play.pieces.map((p) => p.node && p.node._node).filter(Boolean);
  const back = els.some((e) => (e.innerHTML + (e.getAttribute("style") || "")).indexOf("pieces/back/") > -1);
  const busy = document.getAnimations().some((a) => a.playState === "running" && a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest("#playspace"));
  return !back && !busy;
}
while (Date.now() - t0 < 90000) {
  const mine = hand.clickHandlers && hand.clickHandlers.length;
  if (!passed && hand.pullOutOnClick && g.passButtonClickHandler && hand.pieces.length === 13) {
    hand.pulledPieces = hand.pieces.slice(0, 3);
    g.passButtonClickHandler();
    passed = true;
    await sleep(1500);
    continue;
  }
  if (mine) {
    const p = hand.pieces.find((x) => x.selectable);
    if (p) { hand.clickHandlers[0].call(hand.clickHandlerScopes[0], hand, p); played++; await sleep(900); continue; }
  }
  if (played >= 2 && play.pieces.length >= 2 && !mine && trickAtRest()) break;
  await sleep(60);
}
if (t.stopTurnHintTimer) t.stopTurnHintTimer();
const playedInfo = { played, passed, trick: play.pieces.length, hand: hand.pieces.length, ms: Date.now() - t0 };

// No await from here on: the copy is taken in the same step as the check above
const R = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
const union = (els) => {
  els = els.filter((e) => e && e.getClientRects().length);
  if (!els.length) return null;
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  els.forEach((e) => { const r = e.getBoundingClientRect(); x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); });
  return [Math.round(x0), Math.round(y0), Math.round(x1 - x0), Math.round(y1 - y0)];
};
const spotEls = (id) => { const s = t.getSpot(id); return s ? s.pieces.map((p) => p.node && p.node._node).filter(Boolean) : []; };
const one = (s) => { const e = document.querySelector(s); return e && e.getClientRects().length ? R(e) : null; };
const names = {};
t.players.forEach((p, i) => { names[t.getSpotNum(i)] = p.username; });
const handEls = spotEls("hand0").filter((e) => e.getClientRects().length);
const rects = {
  pillL: one("#chromePill"), pillR: one("#chromePillRight"), score: one("#scoreBoardWrapper"), ad: one("#ad"), playspace: one("#playspace"),
  plateN: union(spotEls("namePlate2")), plateW: union(spotEls("namePlate1")), plateE: union(spotEls("namePlate3")), plateS: union(spotEls("namePlate0")),
  avatarN: union(spotEls("avatar2")), avatarW: union(spotEls("avatar1")), avatarE: union(spotEls("avatar3")), avatarS: union(spotEls("avatar0")),
  cardsN: union(spotEls("hand2")), cardsW: union(spotEls("hand1")), cardsE: union(spotEls("hand3")), hand: union(handEls),
  handTop: handEls.length ? Math.round(Math.min(...handEls.map((e) => e.getBoundingClientRect().top))) : null,
  trick: union(spotEls("play")), hintButton: union(spotEls("hintButton")), chatButton: union(spotEls("chatButton"))
};
// Mark what is not drawn on the live page, then work on a copy so the live page stays whole
const KILL = ["script", "noscript", "style", "link", "iframe", ".wmModal", ".wmNotice", "#NoticeContainer", "#wtip", ".customTooltip", "#cookieConsentContainer", ".cc-window", ".spot-messageBox", "#raptive-sticky-footer-ad", ".helpBox"];
let marked = 0;
for (const e of document.body.querySelectorAll("*")) {
  if (!e.isConnected) continue;
  const cs = getComputedStyle(e);
  if (cs.display === "none" && !e.closest("#ad")) { e.setAttribute("data-mtlab-hidden", "1"); marked++; }
}
const copy = document.body.cloneNode(true);
document.querySelectorAll("[data-mtlab-hidden]").forEach((e) => e.removeAttribute("data-mtlab-hidden"));
copy.querySelectorAll("[data-mtlab-hidden]").forEach((e) => e.remove());
for (const s of KILL) copy.querySelectorAll(s).forEach((e) => e.remove());
const roots = new Set();
for (const e of copy.querySelectorAll("[src],[srcset],[href],[style*='url(']")) {
  for (const a of ["src", "srcset", "href"]) { const v = e.getAttribute(a); if (v && !/^(#|javascript:|mailto:)/.test(v)) roots.add(a + " " + v.replace(/[^/]*$/, "")); }
  const st = e.getAttribute("style") || ""; (st.match(/url\\(([^)]+)\\)/g) || []).forEach((u) => roots.add("style " + u.replace(/[^/]*\\)$/, "")));
}
const attrs = {};
for (const a of document.body.attributes) if (a.name !== "id") attrs[a.name] = a.value;
const mc = document.querySelector("#mainContainer");
return { playedInfo, html: copy.innerHTML, bodyAttrs: attrs, htmlClass: document.documentElement.className, roots: [...roots].sort(), marked, rects, names,
  mainContainerClass: mc.className, fontsLoaded: document.fonts.status, bulo: document.fonts.check("16px BuloRounded"),
  viewport: [innerWidth, innerHeight] };
`;

async function capture(name) {
  const cfg = SIZES[name];
  const profileDir = "/tmp/mtlab/profile-" + name;
  fs.rmSync(profileDir, { recursive: true, force: true });
  const b = new Browser({ profileDir, viewport: cfg.viewport, log: (m) => console.log("  " + m) });
  try {
    await b.launch();
    await b.setCookie({ name: "wocg-bookmark-tip-displayed", value: "true", domain: HOST, path: "/" });
    await b.navigate(BASE + "/" + cfg.query);
    await b.evaluate(client.waitReady(30000));
    // A new guest sees the cards prompt at the first deal against bots; it is said once per device
    await b.evaluate(`localStorage.setItem("wocg.cardsPrompt.shown", "1"); return true;`);
    await b.navigate(BASE + "/hearts" + cfg.query);
    const ready = await b.evaluate(client.waitReady(30000));
    const table = await b.evaluate(client.waitBotsTable());
    console.log(name + ": " + JSON.stringify(ready) + " " + JSON.stringify(table));
    if (!table.table) throw new Error("the bots table did not appear");
    // client.run puts the sweep's page helpers (sleep, currentTable) in front; each step returns before its tail
    const measured = await b.evaluate(client.run(MEASURE), { timeout: 90000 });
    console.log(name + ": measured " + Object.keys(measured.box).length + " messages, " + Object.keys(measured.toast).length + " toasts; gutter " + measured.gutter + ", rail " + measured.rail);
    const snap = await b.evaluate(client.run(SNAP), { timeout: 120000 });
    const played = snap.playedInfo;
    console.log(name + ": played " + JSON.stringify(played));
    await b.screenshot("/tmp/mtlab/live-" + name + ".png");
    fs.writeFileSync(path.join(HERE, "snap-" + name + ".html"), snap.html);
    const meta = { captured: new Date().toISOString(), wocgHead: execSync("git -C /Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg rev-parse --short HEAD").toString().trim(), url: BASE + "/hearts" + cfg.query, viewport: cfg.viewport, bodyAttrs: snap.bodyAttrs, htmlClass: snap.htmlClass,
      mainContainerClass: snap.mainContainerClass, names: snap.names, rects: snap.rects, roots: snap.roots, fontsLoaded: snap.fontsLoaded, bulo: snap.bulo,
      box: measured.box, afterHide: measured.afterHide, cameBack: measured.cameBack, toast: measured.toast, gutter: measured.gutter, rail: measured.rail, compact: measured.compact,
      safeTop: measured.safeTop, played, errors: b.takeErrors() };
    fs.writeFileSync(path.join(HERE, "snap-" + name + ".json"), JSON.stringify(meta, null, 1));
    console.log(name + ": " + Math.round(snap.html.length / 1024) + " KB, body " + JSON.stringify(snap.bodyAttrs) + ", names " + JSON.stringify(snap.names));
    console.log(name + ": url roots\n  " + snap.roots.join("\n  "));
    try { await b.evaluate(client.leaveTable()); } catch {}
  } finally {
    await b.close();
  }
}

const which = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(SIZES);
fs.mkdirSync("/tmp/mtlab", { recursive: true });
for (const name of which) {
  await capture(name);
  await sleep(1500);
}
