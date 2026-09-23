// Captures table shots for the pile-count lab through the visual sweep's own browser and replays:
// per scene and viewport, one shot as the site draws it and one with the count chips hidden, plus
// the piles' rects, their counts and the card corner radius.
//   node /tmp/pile-lab/capture.mjs <viewport,...> <sceneId,...>
import fs from "node:fs";
import path from "node:path";
const SWEEP = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep";
const { Browser } = await import(SWEEP + "/lib/browser.mjs");
const { buildScenes, VIEWPORTS } = await import(SWEEP + "/lib/scenes.mjs");
const client = await import(SWEEP + "/lib/client.mjs");

const [vpArg, sceneArg] = process.argv.slice(2);
const BASE = "https://dev.worldofcardgames.com";
const OUT = "/tmp/pile-lab/out";
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const { scenes } = buildScenes({ root: path.resolve(SWEEP, "../.."), fixturesDir: SWEEP + "/fixtures", speed: "20x" });
const chosen = sceneArg.split(",").map((id) => scenes.find((s) => s.id === id)).filter(Boolean);

const CHIPS = [".spotPrefix-stockPileCount", ".spotPrefix-discardPileCount", ".spotPrefix-stockCount", ".spotPrefix-roundCount"];
// Each pile's spot and its count's spot; gin rummy's face-up pile (upCard) has no count of its own,
// but the lab needs it to know which side of the stock faces out.
const PILES = { stockPile: "stockPileCount", discardPile: "discardPileCount", stock: "stockCount", upCard: null };

const DUMP = `
  const rect = (n) => { const b = n.getBoundingClientRect(); return [+b.left.toFixed(2), +b.top.toFixed(2), +b.width.toFixed(2), +b.height.toFixed(2)]; };
  const out = { piles: [], chips: [], view: [innerWidth, innerHeight] };
  const piles = ${JSON.stringify(PILES)};
  Object.keys(piles).forEach((spot) => {
    const cards = [...document.querySelectorAll(".piece.card.spot-" + spot)].filter((n) => getComputedStyle(n).opacity !== "0" && n.getBoundingClientRect().width > 0);
    if (!cards.length) return;
    // the top card is the one drawn last (highest z)
    cards.sort((a, b) => (+getComputedStyle(a).zIndex || 0) - (+getComputedStyle(b).zIndex || 0));
    const top = cards[cards.length - 1];
    const bg = top.querySelector(".background");
    const chip = piles[spot] ? document.querySelector(".piece.spot-" + piles[spot]) : null;
    out.piles.push({
      spot, rect: rect(top), cards: cards.length,
      faceUp: !/back/.test((bg && getComputedStyle(bg).backgroundImage) || ""),
      radius: bg ? getComputedStyle(bg).borderTopLeftRadius : null,
      count: chip ? (chip.textContent || "").trim() : null,
      chip: chip ? rect(chip) : null,
    });
  });
  document.querySelectorAll(${JSON.stringify(CHIPS.join(","))}).forEach((n) => out.chips.push({ cls: [...n.classList].filter((c) => c.startsWith("spot")).join(" "), rect: rect(n), text: (n.textContent || "").trim() }));
  out.compact = document.querySelector("#mainContainer").classList.contains("playspace-compact");
  return out;
`;
// Only the piles' own counts are hidden; the round count (Hand & Foot) stays, as a neighbour.
const PILE_CHIPS = [".spotPrefix-stockPileCount", ".spotPrefix-discardPileCount", ".spotPrefix-stockCount"];
const HIDE = `const s = document.createElement("style"); s.id = "hideChips"; s.textContent = ${JSON.stringify(PILE_CHIPS.join(",") + " { visibility: hidden !important; }")}; document.head.appendChild(s); return true;`;

for (const vp of vpArg.split(",")) {
  const viewport = VIEWPORTS[vp];
  const profileDir = fs.mkdtempSync("/tmp/pile-lab/profile-");
  const browser = new Browser({ profileDir, viewport, log: (m) => console.log("[" + vp + "] " + m) });
  try {
    await browser.launch();
    await browser.setCookie({ name: "wocg-bookmark-tip-displayed", value: "true", domain: "dev.worldofcardgames.com", path: "/" });
    await browser.navigate(BASE + "/");
    await browser.evaluate(client.waitReady(30000));
    for (const scene of chosen) {
      await browser.navigate(BASE + scene.url);
      await browser.evaluate(client.waitReady(30000));
      const rr = await browser.evaluate(client.replay({ messages: scene.replay.messages, gapMs: 30 }));
      if (!rr.table) { console.log("no table for " + scene.id); continue; }
      if (scene.before) await browser.evaluate(client.run(scene.before));
      await sleep(1800);
      const name = scene.id.replace(/^games\//, "").replace(/\//g, "_") + "@" + vp;
      const dump = await browser.evaluate(DUMP);
      await browser.screenshot(path.join(OUT, name + ".png"));
      await browser.evaluate(HIDE);
      await sleep(300);
      await browser.screenshot(path.join(OUT, name + "-bare.png"));
      fs.writeFileSync(path.join(OUT, name + ".json"), JSON.stringify(dump, null, 1));
      console.log("[" + vp + "] " + name + " piles " + dump.piles.map((p) => p.spot + ":" + p.count + (p.faceUp ? "^" : "")).join(" "));
      const errs = browser.takeErrors();
      if (errs.length) console.log("[" + vp + "] page errors: " + JSON.stringify(errs).slice(0, 600));
    }
  } finally {
    await browser.close();
    fs.rmSync(profileDir, { recursive: true, force: true });
  }
}
