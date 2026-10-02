// The room the bid box and a pill may take at the bid turn, per device: the layout's own numbers
// (trumpPillRoom, isBidHeadShown, the button metrics), the playspace's place in the window, the hands' rects,
// and the notice's words. Usage: node room.mjs <label> <width> <height> <dsf> [mobile]
import fs from "node:fs";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { waitReady, waitBotsTable } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/client.mjs";
const [label, wArg, hArg, dsfArg, mobileArg = ""] = process.argv.slice(2);
const OUT = `/tmp/wocg-bidlab/${label}`;
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const STATE = `const t = Y.wocg.Table.getCurrentTable(); if (!t || !t.game || !t.game.state) return null; const s = t.game.state; return { canBid: s.canBid ? s.canBid(t.getPlayerMe()) : null };`;
const DUMP = `
  const t = Y.wocg.Table.getCurrentTable(); const L = t.gameLayout;
  const r = (sel) => { const e = document.querySelector(sel); return e ? e.getBoundingClientRect().toJSON() : null; };
  const out = { vw: innerWidth, vh: innerHeight, mc: document.querySelector("#mainContainer").className, playspace: r("#playspace"), mainContainer: r("#mainContainer"), hands: {}, layout: {} };
  for (let i = 0; i < 4; i++) out.hands[i] = r("#spot-hand" + i);
  for (const k of ["actionButtonHeight", "actionButtonGap", "containerPadding", "bidMessageHeight", "isPlayspaceCompact", "isPlayspacePortrait", "isBidHeadShown", "playspaceWidth", "playspaceHeight", "trumpPillPadding", "trumpPickMinWidth", "playspaceCenter"]) { try { out.layout[k] = typeof L[k] === "function" ? L[k]() : L[k]; } catch (e) { out.layout[k] = "err " + e.message; } }
  try { out.room = L.trumpPillRoom(); } catch (e) { out.room = "err " + e.message; }
  out.box = r("#spot-bidBackdrop"); out.pass = r("#spot-passButton");
  const notice = document.querySelector(".piece.spotPrefix-message, #spot-message .piece, .notice");
  out.notice = notice ? { text: notice.textContent.trim().slice(0, 80), rect: notice.getBoundingClientRect().toJSON() } : null;
  out.messages = Array.from(document.querySelectorAll('[class*="spotPrefix-message"], [class*="spotPrefix-turnMessage"]')).map(e => ({ cls: e.className.slice(0, 120), text: e.textContent.trim().slice(0, 60), rect: e.getBoundingClientRect().toJSON() }));
  return out;`;
const b = new Browser({ profileDir: `/tmp/wocg-bidlab/profile-room-${label}`, viewport: { width: +wArg, height: +hArg, dsf: +dsfArg, mobile: mobileArg === "mobile" }, log: () => {} });
try {
  await b.launch();
  await b.navigate(`https://dev.worldofcardgames.com/bridge?lobby=1`);
  await b.evaluate(`try { localStorage.setItem("wocg.cardsPrompt.shown", "1"); } catch (e) {} return 1;`);
  await b.evaluate(waitReady());
  await b.evaluate(waitBotsTable());
  const t0 = Date.now();
  while (Date.now() - t0 < 60000) { const s = await b.evaluate(STATE).catch(() => null); if (s && s.canBid) break; await sleep(150); }
  await sleep(2200);
  const d = await b.evaluate(DUMP);
  fs.writeFileSync(`${OUT}/room.json`, JSON.stringify(d, null, 1));
  console.log(label, JSON.stringify({ vw: d.vw, vh: d.vh, mc: d.mc, playspace: d.playspace && [d.playspace.x, d.playspace.y, d.playspace.width, d.playspace.height], room: d.room, layout: d.layout, box: d.box && [d.box.x, d.box.y, d.box.width, d.box.height], pass: d.pass && [d.pass.x, d.pass.y, d.pass.width, d.pass.height], hands: Object.fromEntries(Object.entries(d.hands).map(([k, v]) => [k, v && [Math.round(v.x), Math.round(v.y), Math.round(v.width), Math.round(v.height)]])) }));
  console.log("  messages", JSON.stringify(d.messages));
  await b.evaluate(`try { Y.wocg.Comm.send("table.leave", {}); } catch (e) {} return 1;`).catch(() => {});
} catch (e) { console.log("ERROR", e.stack || e.message); } finally { await b.close(); }
