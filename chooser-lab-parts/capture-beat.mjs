// Captures the Pinochle table for the many-bids lab's example "Someone bid 31" (Holger, 2 Oct 2026: "How do we deal
// with showing that people have bid 31 and you have to bid higher than that? Make an example of that."). A bots table
// on the dev site at the player's first bid turn, the right-hand player's plate set to "Bid 31" by the table's own
// updateHandScore (a plate showing a higher bid says Passed instead), the bid box hidden, and two pictures that differ
// only in the notice: none, as a chooser needs no question (Holger, 2 Oct 2026: "We don't need the What's your bid
// text right?"), and the bid to beat in words, "<name> bid 31.", written by the table's own showMessage.
// Usage: node capture-beat.mjs <label> <width> <height> <dsf> [mobile]
//   desktop 1200 800 1 | phone 390 664 2 mobile | side 844 390 2 mobile (the sizes capture-bids.mjs took)
// Output: /tmp/wocg-bidlab/beat-<label>/{plain,named}.png and dump.json, which the lab takes as
// table-pinochle-<label>-beat31-{plain,named}.jpg and captured-beat.json.
import fs from "node:fs";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { waitReady, waitBotsTable } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/client.mjs";

const [label, wArg, hArg, dsfArg, mobileArg = ""] = process.argv.slice(2);
const OUT = `/tmp/wocg-bidlab/beat-${label}`;
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (...a) => console.log(new Date().toISOString().slice(11, 23), label, ...a);

const BOX = `return Array.from(document.querySelectorAll('.piece[class*="spotPrefix-bid"]')).filter((e) => !e.className.includes('spotPrefix-bidValue'));`;
const READY = `const els = (() => { ${BOX} })(); const btns = els.filter((e) => e.className.includes('button'));
  return btns.length > 2 && btns.every((e) => getComputedStyle(e).opacity === '1') ? btns.length : 0;`;

// The right-hand player bids 31; a plate above it says Passed
const SET = `
  const t = Y.wocg.Table.getCurrentTable(), me = t.getPlayerMe();
  let right = -1, rx = -1;
  for (let p = 0; p < t.numPlayers; p++) {
    if (p === me) continue;
    const r = document.querySelector('#spot-hand' + t.getSpotNum(p)).getBoundingClientRect();
    if (r.left + r.width / 2 > rx) { rx = r.left + r.width / 2; right = p; }
  }
  const plates = {};
  for (let p = 0; p < t.numPlayers; p++) {
    if (p === me) continue;
    const piece = t.getPieces('handScore' + t.getSpotNum(p))[0];
    const was = piece.getText ? piece.getText() : '';
    const m = /Bid (\\d+)/.exec(was || '');
    if (p === right) t.updateHandScore(p, 'Bid 31');
    else if (m && +m[1] >= 31) t.updateHandScore(p, 'Passed');
    plates[t.getPlayerName(p)] = { was: was, now: piece.getText ? piece.getText() : '' };
  }
  (() => { ${BOX} })().forEach((e) => e.style.visibility = 'hidden');
  return { right: right, name: t.getPlayerName(right), plates: plates };`;

const NOTICE = (text) => `
  const t = Y.wocg.Table.getCurrentTable();
  t.hideMessage();
  await new Promise((r) => setTimeout(r, 400));
  if (${JSON.stringify(text)}) t.showMessage(${JSON.stringify(text)}, { duration: 600000, category: "important", scope: "table" });
  await new Promise((r) => setTimeout(r, 1800));
  const box = document.querySelector('.spot-messageBox');
  return box ? { text: box.textContent.trim(), rect: box.getBoundingClientRect().toJSON() } : null;`;

const DUMP = `
  const t = Y.wocg.Table.getCurrentTable(), L = t.gameLayout;
  const r = (sel) => { const e = document.querySelector(sel); return e ? e.getBoundingClientRect().toJSON() : null; };
  const out = { vw: innerWidth, vh: innerHeight, playspace: r('#playspace'), hands: {}, layout: {} };
  for (let i = 0; i < t.numPlayers; i++) out.hands[i] = r('#spot-hand' + i);
  for (const k of ['playspaceWidth', 'playspaceHeight', 'playspaceCenter']) { try { out.layout[k] = L[k](); } catch (e) {} }
  try { out.room = L.trumpPillRoom(); } catch (e) { out.room = null; }
  return out;`;

const b = new Browser({ profileDir: `/tmp/wocg-bidlab/profile-beat-${label}`, viewport: { width: +wArg, height: +hArg, dsf: +dsfArg, mobile: mobileArg === "mobile" }, log: () => {} });
try {
  await b.launch();
  await b.navigate("https://dev.worldofcardgames.com/pinochle?lobby=1");
  await b.evaluate(`try { localStorage.setItem("wocg.cardsPrompt.shown", "1"); } catch (e) {} return 1;`);
  log("ready", JSON.stringify(await b.evaluate(waitReady())));
  // The first visit's bookmark tip would stand under the notice in the pictures
  await b.evaluate(`await Promise.resolve(Y.wocg.setCookie("wocg-bookmark-tip-displayed", "true", { path: "/", domain: Y.wocg.DOMAIN, expires: new Date(Date.now() + 86400000) })); return 1;`);
  log("bots table", JSON.stringify(await b.evaluate(waitBotsTable())));
  const t0 = Date.now();
  let n = 0;
  while (Date.now() - t0 < 90000 && !(n = await b.evaluate(READY).catch(() => 0))) await sleep(200);
  if (!n) throw new Error("no bid box within 90 s");
  await sleep(1200);
  const set = await b.evaluate(SET);
  log("plates", JSON.stringify(set));
  const plain = await b.evaluate(NOTICE(""));
  await b.screenshot(`${OUT}/plain.png`);
  const named = await b.evaluate(NOTICE(set.name + " bid 31."));
  await b.screenshot(`${OUT}/named.png`);
  const dump = await b.evaluate(DUMP);
  fs.writeFileSync(`${OUT}/dump.json`, JSON.stringify({ set: set, notice: { plain: plain, named: named }, ...dump }, null, 1));
  log("notice", JSON.stringify(plain && plain.text), "|", JSON.stringify(named && named.text), "playspace", JSON.stringify(dump.playspace && [dump.playspace.x, dump.playspace.y, dump.playspace.width, dump.playspace.height]));
  await b.evaluate(`try { Y.wocg.Comm.send("table.leave", {}); } catch (e) {} return 1;`).catch(() => {});
} catch (e) {
  log("ERROR", e.stack || e.message);
} finally {
  await b.close();
}
