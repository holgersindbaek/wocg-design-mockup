// Captures the Hand & Foot table for the lab's play demo: the dev table through the sweep's replay at
// each screen, with the pile counts, the round chip and every tab above a name plate taken out, and the
// rects of the piles, the name plates, the score board and the tabs that stood there.
//   node pile-count-lab-parts/capture-play.mjs [outDir]
import fs from "node:fs";
import path from "node:path";
const SWEEP = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep";
const { Browser } = await import(SWEEP + "/lib/browser.mjs");
const { buildScenes, VIEWPORTS } = await import(SWEEP + "/lib/scenes.mjs");
const client = await import(SWEEP + "/lib/client.mjs");
const OUT = process.argv[2] || "/tmp/pile-lab/play";
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const { scenes } = buildScenes({ root: path.resolve(SWEEP, "../.."), fixturesDir: SWEEP + "/fixtures", speed: "20x" });
const scene = scenes.find((s) => s.id === "games/handfoot/your-pick");

const TAB_PREFIXES = ["selectedSuit", "showMeldsButton", "sortButton", "playerMore", "playerLiked", "support", "leaving"];
const HIDE = [".spotPrefix-stockPileCount", ".spotPrefix-discardPileCount", ".spotPrefix-stockCount", ".spotPrefix-roundCount", "#scoreBoardWrapper > .boardTab"]
  .concat(TAB_PREFIXES.map((p) => ".piece.chip.spotPrefix-" + p));
const DUMP = `
  const rect = (n) => { const b = n.getBoundingClientRect(); return [+b.left.toFixed(2), +b.top.toFixed(2), +b.width.toFixed(2), +b.height.toFixed(2)]; };
  const vis = (n) => n.getBoundingClientRect().width > 0 && getComputedStyle(n).display !== "none" && getComputedStyle(n).visibility !== "hidden" && getComputedStyle(n).opacity !== "0";
  const out = { view: [innerWidth, innerHeight], compact: document.querySelector("#mainContainer").classList.contains("playspace-compact"), piles: [], plates: [], tabs: [] };
  for (const spot of ["stockPile", "discardPile"]) {
    const cards = [...document.querySelectorAll(".piece.card.spot-" + spot)].filter((n) => getComputedStyle(n).opacity !== "0" && n.getBoundingClientRect().width > 0);
    if (!cards.length) continue;
    cards.sort((a, b) => (+getComputedStyle(a).zIndex || 0) - (+getComputedStyle(b).zIndex || 0));
    const top = cards[cards.length - 1], chip = document.querySelector(".piece.spot-" + spot + "Count");
    out.piles.push({ spot, rect: rect(top), cards: cards.length, count: chip ? chip.textContent.trim() : null, chip: chip ? rect(chip) : null });
  }
  document.querySelectorAll(".piece.spotPrefix-namePlate").forEach((n) => {
    if (!vis(n)) return;
    const seat = +([...n.classList].find((c) => /^spot-namePlate\\d+$/.test(c)) || "spot-namePlate0").replace("spot-namePlate", "");
    const cs = getComputedStyle(n);
    const layout = Y.wocg.Table.getCurrentTable().gameLayout;
    const blocks = ["avatar", "dealerChip"].map((p) => document.getElementById("spot-" + p + seat)).filter(Boolean).map(rect);
    out.plates.push({ seat, rect: rect(n), team2: n.classList.contains("team2"), bg: cs.backgroundColor, radius: cs.borderTopLeftRadius,
      rightEdge: !!layout.isRightEdgePlayerPosition(layout.getPlayerSpotPosition(seat)), blocks });
  });
  document.querySelectorAll(${JSON.stringify(TAB_PREFIXES.map((p) => ".piece.chip.spotPrefix-" + p).join(","))}).forEach((n) => {
    if (!vis(n)) return;
    out.tabs.push({ cls: [...n.classList].filter((c) => /^spot/.test(c) || /^id-/.test(c)).join(" "), rect: rect(n), text: n.textContent.trim() });
  });
  const board = document.querySelector("#scoreBoardWrapper");
  out.board = board ? rect(board) : null;
  const round = document.querySelector(".piece.spotPrefix-roundCount");
  out.round = round ? { rect: rect(round), text: round.textContent.trim() } : null;
  return out;
`;
const HIDE_CSS = `const s = document.createElement("style"); s.textContent = ${JSON.stringify(HIDE.join(",") + " { visibility: hidden !important; }")}; document.head.appendChild(s); return true;`;

for (const vp of ["desktop", "iphone-portrait", "iphone-landscape"]) {
  const profileDir = fs.mkdtempSync("/tmp/pile-lab/profile-");
  const b = new Browser({ profileDir, viewport: VIEWPORTS[vp], log: () => {} });
  try {
    await b.launch();
    await b.setCookie({ name: "wocg-bookmark-tip-displayed", value: "true", domain: "dev.worldofcardgames.com", path: "/" });
    await b.navigate("https://dev.worldofcardgames.com" + scene.url);
    await b.evaluate(client.waitReady(30000));
    await b.evaluate(client.replay({ messages: scene.replay.messages, gapMs: 30 }));
    await sleep(1800);
    const dump = await b.evaluate(DUMP);
    await b.screenshot(path.join(OUT, `handfoot-play@${vp}.png`));
    await b.evaluate(HIDE_CSS);
    await sleep(300);
    await b.screenshot(path.join(OUT, `handfoot-play@${vp}-bare.png`));
    fs.writeFileSync(path.join(OUT, `handfoot-play@${vp}.json`), JSON.stringify(dump, null, 1));
    console.log(vp, "piles", dump.piles.map((p) => p.spot + ":" + p.count).join(" "), "plates", dump.plates.map((p) => p.seat).join(","), "tabs", JSON.stringify(dump.tabs.map((t) => t.cls + " " + t.text)), "board", JSON.stringify(dump.board), "errors", JSON.stringify(b.takeErrors()).slice(0, 200));
  } finally { await b.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }
}
