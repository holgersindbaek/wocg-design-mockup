// Captures today's Bridge bid box and a suit pill from the dev site: the markup with inline styles, the felt's
// paint, computed styles per piece, and screenshots. For the bid chooser and suit chooser labs.
// Usage: node capture.mjs <label> <bridge|pill> <width> <height> <dsf> [mobile]
import fs from "node:fs";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { waitReady, waitBotsTable } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/client.mjs";

const [label = "desk", what = "bridge", wArg = "1200", hArg = "800", dsfArg = "2", mobileArg = ""] = process.argv.slice(2);
const OUT = `/tmp/wocg-bidlab/${label}`;
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString().slice(11, 23), ...a);

const DUMP = (spotids) => `
  const t = Y.wocg.Table.getCurrentTable();
  const pick = (cs, keys) => Object.fromEntries(keys.map(k => [k, cs.getPropertyValue(k)]));
  const KEYS = ["position", "left", "top", "width", "height", "background-color", "background-image", "background-size", "background-position", "box-shadow", "border-radius", "color", "font-family", "font-size", "font-weight", "line-height", "opacity", "filter", "transform", "z-index", "padding", "text-align", "letter-spacing", "corner-shape"];
  const out = { body: document.body.className, html: document.documentElement.className, bodyData: Object.assign({}, document.body.dataset), vw: innerWidth, vh: innerHeight, dpr: devicePixelRatio, pieces: [] };
  const mc = document.querySelector("#mainContainer");
  out.mainContainer = { cls: mc.className, style: mc.getAttribute("style"), cs: pick(getComputedStyle(mc), KEYS) };
  const ps = document.querySelector("#playspace");
  out.playspace = ps && { cls: ps.className, style: ps.getAttribute("style"), cs: pick(getComputedStyle(ps), KEYS), rect: ps.getBoundingClientRect().toJSON(), parent: ps.parentElement && (ps.parentElement.id || ps.parentElement.className) };
  // what draws the felt under the box: the element stack at a point beside it
  const ids = ${JSON.stringify(spotids)};
  let union = null;
  for (const id of ids) {
    const sp = t.getSpot(id);
    const pieces = (sp && sp.pieces) || [];
    const spotEl = document.querySelector("#spot-" + id);
    for (const p of pieces) {
      const el = p.node.getDOMNode();
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const after = getComputedStyle(el, "::after");
      const before = getComputedStyle(el, "::before");
      out.pieces.push({ spot: id, id: p.getId && p.getId(), html: el.outerHTML, parent: el.parentElement && (el.parentElement.id || el.parentElement.className), rect: r.toJSON(), cs: pick(cs, KEYS),
        after: pick(after, ["content", "position", "left", "top", "width", "height", "background-color", "background-image", "box-shadow", "border-radius", "opacity", "mask-image", "-webkit-mask-image", "mask-size", "color"]),
        before: pick(before, ["content", "position", "left", "top", "width", "height", "background-color", "background-image", "opacity"]) });
      union = union ? { l: Math.min(union.l, r.left), t: Math.min(union.t, r.top), r: Math.max(union.r, r.right), b: Math.max(union.b, r.bottom) } : { l: r.left, t: r.top, r: r.right, b: r.bottom };
    }
    if (spotEl) out.pieces.push({ spot: id, spotEl: true, html: spotEl.outerHTML.slice(0, 400), rect: spotEl.getBoundingClientRect().toJSON() });
  }
  out.union = union;
  if (union) {
    const x = Math.max(2, union.l - 30), y = Math.round((union.t + union.b) / 2);
    out.stack = document.elementsFromPoint(x, y).slice(0, 8).map(e => ({ tag: e.tagName, id: e.id, cls: String(e.className).slice(0, 200), bg: getComputedStyle(e).backgroundImage.slice(0, 300), bgc: getComputedStyle(e).backgroundColor, bgs: getComputedStyle(e).backgroundSize, bgp: getComputedStyle(e).backgroundPosition, bga: getComputedStyle(e).backgroundAttachment, before: getComputedStyle(e, "::before").backgroundImage.slice(0, 300), after: getComputedStyle(e, "::after").backgroundImage.slice(0, 300), rect: e.getBoundingClientRect().toJSON() }));
  }
  // the layout's numbers
  const L = t.gameLayout;
  out.layout = {};
  for (const k of ["actionButtonHeight", "actionButtonGap", "containerPadding", "bidMessageHeight", "bidRankColumnCount", "bidBackdropColumnCount", "isPlayspaceCompact", "isPlayspacePortrait", "isBidHeadShown", "playspaceWidth", "playspaceHeight", "trumpPillPadding"]) {
    try { if (typeof L[k] === "function") out.layout[k] = L[k](); } catch (e) { out.layout[k] = "err " + e.message; }
  }
  try { out.layout.overlay7 = L.overlayWidthForButtonRow(7, L.actionButtonHeight()); out.layout.overlay5 = L.overlayWidthForButtonRow(5, L.actionButtonHeight()); out.layout.row7 = L.actionButtonRowWidth(7, L.actionButtonHeight()); } catch (e) {}
  return out;
`;

const STATE = `
  const t = Y.wocg.Table.getCurrentTable();
  if (!t || !t.game || !t.game.state) return null;
  const s = t.game.state;
  return { me: t.getPlayerMe(), phase: s.phase, canBid: s.canBid ? s.canBid(t.getPlayerMe()) : null, highBid: s.highBid, auction: (s.auction || []).length, backdrop: !!document.querySelector("#spot-bidBackdrop .piece, .spotPrefix-bidBackdrop") };
`;

async function waitState(b, pred, ms, every = 150) {
  const t0 = Date.now();
  let s = null;
  while (Date.now() - t0 < ms) {
    s = await b.evaluate(STATE).catch(() => null);
    if (s && pred(s)) return s;
    await sleep(every);
  }
  return null;
}

async function shotRect(b, file, u, pad = 40) {
  const sc = await b.evaluate(`return { x: scrollX, y: scrollY };`);
  const clip = { x: Math.max(0, u.l - pad) + sc.x, y: Math.max(0, u.t - pad) + sc.y, width: (u.r - u.l) + pad * 2, height: (u.b - u.t) + pad * 2, scale: 1 };
  const r = await b.send("Page.captureScreenshot", { format: "png", clip, captureBeyondViewport: false });
  fs.writeFileSync(file, Buffer.from(r.data, "base64"));
}

const viewport = { width: +wArg, height: +hArg, dsf: +dsfArg, mobile: mobileArg === "mobile" };
const b = new Browser({ profileDir: `/tmp/wocg-bidlab/profile-${label}`, viewport, log: () => {} });
try {
  await b.launch();
  const game = what === "bridge" ? "bridge" : "crazy-eights";
  await b.navigate(`https://dev.worldofcardgames.com/${game}?lobby=1`);
  await b.evaluate(`try { localStorage.setItem("wocg.cardsPrompt.shown", "1"); } catch (e) {} return 1;`);
  log("ready", JSON.stringify(await b.evaluate(waitReady())));
  log("bots table", JSON.stringify(await b.evaluate(waitBotsTable())));

  if (what === "bridge") {
    // My first bid turn; the bots bid before me if they deal first
    let s = await waitState(b, (s) => s.canBid, 60000);
    log("bid turn", JSON.stringify(s));
    await sleep(2200);
    const ids = ["bidBackdrop", "bidMessage", "bidRank0", "bidRank1", "bidRank2", "bidRank3", "bidRank4", "bidRank5", "bidRank6", "bidDenom0", "bidDenom1", "bidDenom2", "bidDenom3", "bidDenom4", "passButton", "doubleButton", "redoubleButton"];
    const d = await b.evaluate(DUMP(ids));
    fs.writeFileSync(`${OUT}/dump.json`, JSON.stringify(d, null, 1));
    await b.screenshot(`${OUT}/full.png`);
    if (d.union) await shotRect(b, `${OUT}/box.png`, d.union, 60);
    // the chosen level: click level 3 (or the first enabled) through the UI manager, then shoot again
    await b.evaluate(`const t = Y.wocg.Table.getCurrentTable(); const ui = t.game.ui; const lv = [3,2,4,1,5].find(l => !t.getSpot("bidRank" + (l - 1)).pieces[0].node.hasClass("disabled")); ui.handleRankClick(lv); return lv;`);
    await sleep(400);
    const d2 = await b.evaluate(DUMP(ids));
    fs.writeFileSync(`${OUT}/dump-level.json`, JSON.stringify(d2, null, 1));
    if (d2.union) await shotRect(b, `${OUT}/box-level.png`, d2.union, 60);
    // the felt alone: hide the box and shoot the same rect
    await b.evaluate(`document.querySelectorAll('[class*="spotPrefix-bid"], .spotPrefix-passButton, .spotPrefix-doubleButton, .spotPrefix-redoubleButton').forEach(e => e.style.visibility = "hidden"); return 1;`);
    await sleep(200);
    if (d.union) await shotRect(b, `${OUT}/felt.png`, d.union, 60);
    await b.screenshot(`${OUT}/full-nobox.png`);
  } else {
    // A suit pill on a Crazy Eights table, drawn by the site's own showTrumpPill
    await sleep(3000);
    await b.evaluate(`
      const t = Y.wocg.Table.getCurrentTable();
      const ui = t.game.ui || t.game;
      const anim = Y.Animation.createSpotGroupAnimation(t);
      t.showTrumpPill({ suits: ["club", "diamond", "heart", "spade"], unavailable: ["spade"], scope: t, cellHandler: (p) => t.pickTrumpPillSuit(p.getId()), pickHandler: () => {}, buttonText: "Choose suit", animation: anim });
      return 1;`);
    await sleep(1500);
    const ids = ["trumpPill", "suitSelector0", "suitSelector1", "suitSelector2", "suitSelector3", "trumpPick"];
    const d = await b.evaluate(DUMP(ids));
    fs.writeFileSync(`${OUT}/dump.json`, JSON.stringify(d, null, 1));
    await b.screenshot(`${OUT}/full.png`);
    if (d.union) await shotRect(b, `${OUT}/pill.png`, d.union, 60);
    await b.evaluate(`const t = Y.wocg.Table.getCurrentTable(); t.pickTrumpPillSuit("heart"); return 1;`);
    await sleep(600);
    const d2 = await b.evaluate(DUMP(ids));
    fs.writeFileSync(`${OUT}/dump-heart.json`, JSON.stringify(d2, null, 1));
    if (d2.union) await shotRect(b, `${OUT}/pill-heart.png`, d2.union, 60);
  }
  await b.evaluate(`try { Y.wocg.Comm.send("table.leave", {}); } catch (e) {} return 1;`).catch(() => {});
} catch (e) {
  log("ERROR", e.stack || e.message);
} finally {
  await b.close();
}
