// Checks the two chooser labs headless (Chrome for Testing, never the user's Chrome): every frame draws, no page
// error, today's pieces in the lab have the computed styles the dev site gave them (the captures in
// /tmp/wocg-bidlab, when present), and a bid can be made. Pictures go to /tmp/chooser-lab-check/.
//   node chooser-lab-parts/check.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..");
const OUT = "/tmp/chooser-lab-check";
const CAPS = "/tmp/wocg-bidlab";
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const KEYS = ["background-color", "box-shadow", "border-radius", "color", "font-size", "font-weight", "line-height"];
const report = { bid: {}, suit: {} };

// The computed styles of the pieces in one frame, keyed by spot (or, for the pill, by suit)
const STYLES = (cardIndex, frameIndex, keys) => `
  const card = document.querySelectorAll('#clCards .cl-card')[${cardIndex}];
  const frame = card.querySelectorAll('.cl-frame')[${frameIndex}];
  const pick = (cs, ks) => Object.fromEntries(ks.map((k) => [k, cs.getPropertyValue(k)]));
  const out = {};
  frame.querySelectorAll('.piece').forEach((e) => {
    const spot = (e.className.match(/\\bspot-([\\w]+)/) || [])[1];
    const id = (e.className.match(/\\bid-([\\w]+)/) || [])[1];
    out[spot + (spot && spot.startsWith('suitSelector') ? ':' + id : '')] = { cs: pick(getComputedStyle(e), ${JSON.stringify(keys)}),
      after: pick(getComputedStyle(e, '::after'), ['background-color', 'box-shadow', 'border-radius', 'width', 'height', 'left', 'opacity', 'mask-image']),
      cls: e.className };
  });
  return out;`;

function compare(label, lab, dev, keys) {
  const bad = [];
  for (const [spot, want] of Object.entries(dev)) {
    const got = lab[spot];
    if (!got) { bad.push(spot + ": missing in the lab"); continue; }
    for (const k of keys) {
      const a = String(got.cs[k]).replace(/\s+/g, " "), b = String(want[k]).replace(/\s+/g, " ");
      if (a !== b) bad.push(`${spot} ${k}: lab ${a} | dev ${b}`);
    }
  }
  console.log(`${label}: ${Object.keys(dev).length} pieces compared, ${bad.length} differences`);
  bad.slice(0, 30).forEach((x) => console.log("   ", x));
  return bad;
}

function devStyles(file, keyOf) {
  if (!fs.existsSync(file)) return null;
  const d = JSON.parse(fs.readFileSync(file, "utf8"));
  const out = {};
  for (const p of d.pieces) if (!p.spotEl) out[keyOf(p)] = Object.fromEntries(KEYS.map((k) => [k, p.cs[k]]));
  return out;
}

async function frameShot(b, file, cardIndex, frameIndex, pad = 0) {
  const r = await b.evaluate(`const f = document.querySelectorAll('#clCards .cl-card')[${cardIndex}].querySelectorAll('.cl-frame-box')[${frameIndex}];
    f.scrollIntoView({ block: 'center' }); await new Promise((r) => setTimeout(r, 120)); const r = f.getBoundingClientRect(); return { x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height };`);
  const s = await b.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: r.x - pad, y: r.y - pad, width: r.w + 2 * pad, height: r.h + 2 * pad, scale: 1 } });
  fs.writeFileSync(file, Buffer.from(s.data, "base64"));
}

const clickIn = (cardIndex, frameIndex, selector) => `
  const f = document.querySelectorAll('#clCards .cl-card')[${cardIndex}].querySelectorAll('.cl-frame')[${frameIndex}];
  const e = f.querySelector(${JSON.stringify(selector)});
  if (!e) return 'no ' + ${JSON.stringify(selector)};
  e.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  await new Promise((r) => setTimeout(r, 300));
  return f.querySelector('.cl-said').textContent + ' | ' + Array.from(f.querySelectorAll('.piece.button')).map((x) => x.textContent + (x.classList.contains('disabled') ? ' (off)' : '') + ' ' + x.style.fontSize).join(', ');`;

const setSwitch = (label, text) => `
  const ctl = Array.from(document.querySelectorAll('.cl-ctl')).find((c) => c.firstChild.textContent.trim() === ${JSON.stringify(label)});
  const b = Array.from(ctl.querySelectorAll('button')).find((x) => x.textContent.trim() === ${JSON.stringify(text)});
  b.click(); await new Promise((r) => setTimeout(r, 400)); return document.querySelectorAll('#clCards .cl-frame').length;`;

const b = new Browser({ profileDir: OUT + "/profile", viewport: { width: 1440, height: 1000, dsf: 2 }, log: () => {} });
try {
  await b.launch();

  // ----- the bid lab -----
  await b.navigate("file://" + path.join(ROOT, "bid-chooser-lab.html"));
  await sleep(1500);
  await b.evaluate(`document.querySelector('.cl-head').style.position = 'static'; return 1;`);
  const info = await b.evaluate(`return { frames: document.querySelectorAll('#clCards .cl-frame').length, pieces: document.querySelectorAll('#clCards .piece').length,
    fonts: document.fonts.check('700 20px "BuloRounded"'), sheets: Array.from(document.styleSheets).map((s) => { try { return (s.href || 'inline').split('/').pop() + ':' + s.cssRules.length; } catch (e) { return 'blocked ' + s.href; } }) };`);
  console.log("bid lab", JSON.stringify(info));
  const errs = b.takeErrors ? b.takeErrors() : [];
  if (errs.length) console.log("page errors", JSON.stringify(errs).slice(0, 2000));
  // today's box against the dev site, per screen (frames are desktop, phone, side in card 0)
  for (const [name, fi, cap] of [["desktop", 0, "desk"], ["phone", 1, "phone"], ["side", 2, "side"]]) {
    const dev = devStyles(`${CAPS}/${cap}/dump.json`, (p) => p.spot);
    if (!dev) { console.log("no capture for", name); continue; }
    const lab = await b.evaluate(STYLES(0, fi, KEYS));
    report.bid[name] = compare(`today's bid box, ${name}`, lab, dev, KEYS);
  }
  await b.screenshot(`${OUT}/bid-page.png`, { full: true });
  for (let c = 0; c < 4; c++) for (let fi = 0; fi < 3; fi++) await frameShot(b, `${OUT}/bid-v${c}-${["desktop", "phone", "side"][fi]}.png`, c, fi, 0);
  // a bid in version 1 (one chooser), desktop: level 3, hearts, then the button
  console.log("v1 level 3:", await b.evaluate(clickIn(1, 0, ".id-level3")));
  console.log("v1 hearts:", await b.evaluate(clickIn(1, 0, ".id-heart")));
  await frameShot(b, `${OUT}/bid-v1-desktop-3h.png`, 1, 0, 0);
  console.log("v1 bid:", await b.evaluate(clickIn(1, 0, ".spot-bidSend")));
  await frameShot(b, `${OUT}/bid-v1-desktop-sent.png`, 1, 0, 0);
  // the same in version 2 (two choosers) on the phone, and version 3 (one row)
  console.log("v2 phone level 2:", await b.evaluate(clickIn(2, 1, ".id-level2")));
  console.log("v2 phone NT:", await b.evaluate(clickIn(2, 1, ".id-notrump")));
  await frameShot(b, `${OUT}/bid-v2-phone-2nt.png`, 2, 1, 0);
  console.log("v3 side level 4:", await b.evaluate(clickIn(3, 2, ".id-level4")));
  console.log("v3 side spades:", await b.evaluate(clickIn(3, 2, ".id-spade")));
  await frameShot(b, `${OUT}/bid-v3-side-4s.png`, 3, 2, 0);
  // the white mark with no lines, and a bid to beat
  console.log("switch:", await b.evaluate(setSwitch("Picked cell", "White card")), await b.evaluate(setSwitch("Lines between cells", "Off")), await b.evaluate(setSwitch("Bid to beat", "2")));
  console.log("v1 level 2 after 2h:", await b.evaluate(clickIn(1, 0, ".id-level2")));
  console.log("v1 spades:", await b.evaluate(clickIn(1, 0, ".id-spade")));
  await frameShot(b, `${OUT}/bid-v1-desktop-white-2s.png`, 1, 0, 0);
  await frameShot(b, `${OUT}/bid-v2-desktop-white.png`, 2, 0, 0);
  // the whole table
  console.log("table:", await b.evaluate(setSwitch("Around it", "The whole table")));
  for (let c = 0; c < 4; c++) for (let fi = 0; fi < 3; fi++) await frameShot(b, `${OUT}/bid-table-v${c}-${["desktop", "phone", "side"][fi]}.png`, c, fi, 0);

  // ----- the suit lab -----
  await b.navigate("file://" + path.join(ROOT, "suit-chooser-lab.html"));
  await sleep(1500);
  await b.evaluate(`document.querySelector('.cl-head').style.position = 'static'; return 1;`);
  console.log("suit lab", JSON.stringify(await b.evaluate(`return { frames: document.querySelectorAll('#clCards .cl-frame').length, pieces: document.querySelectorAll('#clCards .piece').length };`)));
  // today's pill against the dev site's Crazy Eights pill (the game's own suit picker) with hearts picked
  const devPill = (() => {
    const f = `${CAPS}/pilldesk/dump-heart.json`;
    if (!fs.existsSync(f)) return null;
    const d = JSON.parse(fs.readFileSync(f, "utf8"));
    const out = {};
    for (const p of d.pieces) if (!p.spotEl) out[p.spot.startsWith("suitSelector") ? "suit:" + p.id : p.spot] = { cs: Object.fromEntries(KEYS.map((k) => [k, p.cs[k]])), after: p.after, x: p.rect.x };
    return out;
  })();
  console.log("suit today hearts:", await b.evaluate(clickIn(0, 0, ".id-heart")));
  const labPill = await b.evaluate(STYLES(0, 0, KEYS));
  const labOrder = await b.evaluate(`return Array.from(document.querySelectorAll('#clCards .cl-card')[0].querySelectorAll('.cl-frame')[0].querySelectorAll('.piece.trumpPillCell')).sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left).map((c) => (c.className.match(/\\bid-(\\w+)/) || [])[1]).join(', ');`);
  console.log("suit lab order, left to right:", labOrder);
  if (devPill) {
    const devOrder = Object.entries(devPill).filter(([k]) => k.startsWith("suit:")).sort((a, b) => a[1].x - b[1].x).map(([k]) => k.slice(5)).join(", ");
    console.log("dev pill order, left to right:", devOrder);
    const lab = {};
    for (const [k, v] of Object.entries(labPill)) { const id = (v.cls.match(/\bid-(\w+)/) || [])[1]; lab[k.startsWith("suitSelector") ? "suit:" + id : k] = v; }
    const keys = ["trumpPill", "trumpPick", "suit:club", "suit:diamond", "suit:spade", "suit:heart"];
    const bad = [];
    if (labOrder !== devOrder) bad.push(`order: lab ${labOrder} | dev ${devOrder}`);
    for (const key of keys) {
      const L = lab[key], D = devPill[key];
      if (!L || !D) { bad.push(key + " missing"); continue; }
      for (const k of KEYS) if (String(L.cs[k]) !== String(D.cs[k])) bad.push(`${key} ${k}: lab ${L.cs[k]} | dev ${D.cs[k]}`);
      for (const k of ["background-color", "box-shadow", "border-radius", "width", "height", "left"]) if (D.after && D.after.content !== "none" && String(L.after[k]) !== String(D.after[k])) bad.push(`${key} ::after ${k}: lab ${L.after[k]} | dev ${D.after[k]}`);
      if (D.after && /url\(/.test(D.after["mask-image"] || "") && !/url\("data:/.test(L.after["mask-image"])) bad.push(`${key} mask: lab ${String(L.after["mask-image"]).slice(0, 60)}`);
    }
    console.log(`today's suit pill, desktop: ${keys.length} pieces compared, ${bad.length} differences`);
    bad.forEach((x) => console.log("   ", x));
    report.suit.desktop = bad;
  }
  await b.evaluate(setSwitch("Suits", "Four suits"));
  await b.screenshot(`${OUT}/suit-page.png`, { full: true });
  const suitCards = await b.evaluate(`return document.querySelectorAll('#clCards .cl-card').length;`);
  for (let c = 0; c < suitCards; c++) for (let fi = 0; fi < 2; fi++) await frameShot(b, `${OUT}/suit-v${c}-${["desktop", "phone"][fi]}.png`, c, fi, 0);
  await b.evaluate(setSwitch("Size", "2x"));
  for (let c = 0; c < suitCards; c++) await frameShot(b, `${OUT}/suit-v${c}-desktop-2x.png`, c, 0, 0);
  const errs2 = b.takeErrors ? b.takeErrors() : [];
  if (errs2.length) console.log("page errors", JSON.stringify(errs2).slice(0, 2000));
} catch (e) {
  console.log("ERROR", e.stack || e.message);
} finally {
  await b.close();
}
