// Captures today's bid box in Spades, Twenty-Nine, Pinochle or Double Deck Pinochle on the dev site, for the many-bids
// lab: at the player's first bid turn on a bots table, the box's pieces as the site wrote them (outerHTML), their
// computed styles, the free room on the table and the table with the box hidden.
// Usage: node capture-bids.mjs <game> <label> <width> <height> <dsf> [mobile]
//   game: spades | twenty-nine | pinochle | double-deck-pinochle; output in /tmp/wocg-bidlab/<game>-<label>/
import fs from "node:fs";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { waitReady, waitBotsTable } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/client.mjs";

const [game, label, wArg, hArg, dsfArg, mobileArg = ""] = process.argv.slice(2);
const OUT = `/tmp/wocg-bidlab/${game}-${label}`;
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString().slice(11, 23), game, label, ...a);

const KEYS = ["background-color", "box-shadow", "border-radius", "color", "font-size", "font-weight", "line-height", "opacity", "filter"];
const BOX = `return Array.from(document.querySelectorAll('.piece[class*="spotPrefix-bid"]')).filter((e) => !e.className.includes('spotPrefix-bidValue'));`;
const READY = `const els = (() => { ${BOX} })(); const btns = els.filter((e) => e.className.includes('button'));
  return btns.length > 2 && btns.every((e) => getComputedStyle(e).opacity === '1') ? btns.length : 0;`;
const DUMP = `
  const t = Y.wocg.Table.getCurrentTable(), L = t.gameLayout;
  const pick = (cs, ks) => Object.fromEntries(ks.map((k) => [k, cs.getPropertyValue(k)]));
  const r = (sel) => { const e = document.querySelector(sel); return e ? e.getBoundingClientRect().toJSON() : null; };
  const els = (() => { ${BOX} })();
  const out = { vw: innerWidth, vh: innerHeight, mc: document.querySelector('#mainContainer').className, playspace: r('#playspace'), hands: {}, layout: {}, pieces: [] };
  for (let i = 0; i < t.numPlayers; i++) out.hands[i] = r('#spot-hand' + i);
  for (const k of ['actionButtonHeight', 'actionButtonGap', 'containerPadding', 'bidMessageHeight', 'isPlayspaceCompact', 'isPlayspacePortrait', 'playspaceWidth', 'playspaceHeight', 'playspaceCenter']) { try { out.layout[k] = typeof L[k] === 'function' ? L[k]() : L[k]; } catch (e) { out.layout[k] = 'err'; } }
  try { out.room = L.trumpPillRoom(); } catch (e) { out.room = null; }
  for (const e of els) {
    const spot = (e.className.match(/\\bspot-(\\w+)/) || [])[1];
    out.pieces.push({ spot: spot, html: e.outerHTML, rect: e.getBoundingClientRect().toJSON(), cs: pick(getComputedStyle(e), ${JSON.stringify(KEYS)}),
      after: pick(getComputedStyle(e, '::after'), ['content', 'background-color', 'mask-image', '-webkit-mask-image']) });
  }
  return out;`;

const b = new Browser({ profileDir: `/tmp/wocg-bidlab/profile-${game}-${label}`, viewport: { width: +wArg, height: +hArg, dsf: +dsfArg, mobile: mobileArg === "mobile" }, log: () => {} });
try {
  await b.launch();
  await b.navigate(`https://dev.worldofcardgames.com/${game}?lobby=1`);
  await b.evaluate(`try { localStorage.setItem("wocg.cardsPrompt.shown", "1"); } catch (e) {} return 1;`);
  log("ready", JSON.stringify(await b.evaluate(waitReady())));
  log("bots table", JSON.stringify(await b.evaluate(waitBotsTable())));
  const t0 = Date.now();
  let n = 0;
  while (Date.now() - t0 < 90000 && !(n = await b.evaluate(READY).catch(() => 0))) await sleep(200);
  if (!n) throw new Error("no bid box within 90 s");
  await sleep(1200);
  const d = await b.evaluate(DUMP);
  fs.writeFileSync(`${OUT}/dump.json`, JSON.stringify(d, null, 1));
  log("box", d.pieces.length, "pieces, room", JSON.stringify(d.room), "playspace", JSON.stringify(d.playspace && [d.playspace.x, d.playspace.y, d.playspace.width, d.playspace.height]));
  await b.screenshot(`${OUT}/full.png`);
  const u = d.pieces.reduce((a, p) => (a ? { l: Math.min(a.l, p.rect.left), t: Math.min(a.t, p.rect.top), r: Math.max(a.r, p.rect.right), b: Math.max(a.b, p.rect.bottom) } : { l: p.rect.left, t: p.rect.top, r: p.rect.right, b: p.rect.bottom }), null);
  const pad = 40;
  const s = await b.send("Page.captureScreenshot", { format: "png", clip: { x: Math.max(0, u.l - pad), y: Math.max(0, u.t - pad), width: u.r - u.l + 2 * pad, height: u.b - u.t + 2 * pad, scale: 1 } });
  fs.writeFileSync(`${OUT}/box.png`, Buffer.from(s.data, "base64"));
  await b.evaluate(`(() => { ${BOX} })().forEach((e) => e.style.visibility = 'hidden'); return 1;`);
  await sleep(200);
  await b.screenshot(`${OUT}/full-nobox.png`);
  await b.evaluate(`try { Y.wocg.Comm.send("table.leave", {}); } catch (e) {} return 1;`).catch(() => {});
} catch (e) {
  log("ERROR", e.stack || e.message);
} finally {
  await b.close();
}
