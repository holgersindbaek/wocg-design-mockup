// Captures the round-counter options for the pile-count lab: the Hand & Foot table on dev through the
// sweep's replay, one shot per option and screen, each option put into the live score board by script
// and taken out again before the next. Writes rounds-<option>@<viewport>.png and rounds@<viewport>.json.
//   node pile-count-lab-parts/capture-rounds.mjs [outDir]
import fs from "node:fs";
import path from "node:path";
const SWEEP = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep";
const { Browser } = await import(SWEEP + "/lib/browser.mjs");
const { buildScenes, VIEWPORTS } = await import(SWEEP + "/lib/scenes.mjs");
const client = await import(SWEEP + "/lib/client.mjs");
const OUT = process.argv[2] || "/tmp/pile-lab/rounds";
fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const { scenes } = buildScenes({ root: path.resolve(SWEEP, "../.."), fixturesDir: SWEEP + "/fixtures", speed: "20x" });
const scene = scenes.find((s) => s.id === "games/handfoot/your-pick");

// Every option hides the round chip by the stock (today's place) and tags what it adds with .rv, so
// the next option starts from the site's own board.
const RESET = `document.querySelectorAll(".rv").forEach((n) => n.remove()); document.querySelectorAll(".rvHide").forEach((n) => n.classList.remove("rvHide")); return true;`;
const BASE_CSS = `
  .rvHide { visibility: hidden !important; }
  #scoreBoard tr.rvHead td, #scoreBoard tr.rvFoot td { color: var(--ink-label, #4e4d4c); }
  /* a row above the board: the team row under it keeps the line it had as the first row */
  #scoreBoard tr.rvHead td { box-shadow: inset 0 -1px 0 0 var(--color-border-strong) !important; }
  #scoreBoard tr.rvHead + tr td { box-shadow: inset -1px 0 0 0 var(--color-border-strong), inset 0 -1px 0 0 var(--color-border-strong); }
  #scoreBoard tr.rvHead + tr td:last-child { box-shadow: inset 0 -1px 0 0 var(--color-border-strong); }
  #scoreBoard tr.rvFoot td { box-shadow: inset 0 1px 0 0 var(--color-border-strong) !important; }
  .rvTab { position: absolute; z-index: -1; bottom: 100%; left: 12px; padding: 0 8px; background: var(--paper-band, #f4eee5);
    box-shadow: 0 0 0 1px var(--line-felt, #393939); border-radius: 12px 12px 0 0; corner-shape: squircle;
    font-weight: bold; color: var(--ink, #141414); white-space: nowrap; display: flex; align-items: center; gap: 4px; }
  #mainContainer.playspace-compact .rvTab { left: 8px; padding: 0 6px; border-radius: 8px 8px 0 0; }
  /* hanging from the board's bottom edge, centred; its top ring line hides under the board's */
  .rvTab.under { top: 100%; bottom: auto; left: 50%; transform: translateX(-50%); border-radius: 0 0 12px 12px; line-height: 1; padding-top: 2px; box-sizing: border-box; }
  #mainContainer.playspace-compact .rvTab.under { left: 50%; border-radius: 0 0 8px 8px; padding-top: 0; }
  .rvDot { width: 6px; height: 6px; border-radius: 50%; corner-shape: round; box-shadow: inset 0 0 0 1px var(--ink-label, #4e4d4c); }
  .rvDot.on { background: var(--ink, #141414); box-shadow: none; }
`;
const PREP = `const s = document.createElement("style"); s.id = "rvStyle"; s.textContent = ${JSON.stringify(BASE_CSS)}; document.head.appendChild(s); return true;`;
const HIDE_CHIP = `document.querySelectorAll(".spotPrefix-roundCount").forEach((n) => n.classList.add("rvHide"));`;
const row = (cls, text, where) => `
  const t = document.querySelector("#scoreBoard"); const tr = document.createElement("tr"); tr.className = "title rv ${cls}";
  const td = document.createElement("td"); td.colSpan = 6; td.textContent = ${JSON.stringify(text)}; tr.appendChild(td);
  ${where === "top" ? "t.insertBefore(tr, t.firstElementChild);" : "t.appendChild(tr);"}`;
const tab = (inner, cls) => `
  const w = document.querySelector("#scoreBoardWrapper"); const d = document.createElement("div"); d.className = "rv rvTab ${cls || ""}";
  const compact = document.querySelector("#mainContainer").classList.contains("playspace-compact");
  d.style.height = (compact ? 16 : 24) + "px"; d.style.fontSize = (compact ? 11 : 13) + "px"; d.innerHTML = ${JSON.stringify(inner)}; w.appendChild(d);`;

const OPTIONS = {
  today: "",
  head: HIDE_CHIP + row("rvHead", "Round 1 of 4", "top"),
  foot: HIDE_CHIP + row("rvFoot", "Round 1 of 4", "bottom"),
  tab: HIDE_CHIP + tab("Round 1/4"),
  under: HIDE_CHIP + tab("Round 1/4", "under"),
  dots: HIDE_CHIP + tab('<i class="rvDot on"></i><i class="rvDot"></i><i class="rvDot"></i><i class="rvDot"></i>'),
  notice: HIDE_CHIP + `Y.wocg.Table.getCurrentTable().showMessage("Round 1 of 4. Your first meld needs 50 points.", { duration: 600000, skipPrefix: true });`,
};

// node capture-rounds.mjs [outDir] [option,...]: only the options named (all when none).
const ONLY = process.argv[3] ? process.argv[3].split(",") : null;
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
    await b.evaluate(PREP);
    const rects = {};
    for (const [name, js] of Object.entries(OPTIONS).filter(([n]) => !ONLY || ONLY.includes(n))) {
      await b.evaluate(RESET);
      if (js) await b.evaluate(js + " return true;");
      await sleep(name === "notice" ? 700 : 200);
      rects[name] = await b.evaluate(`const r = (n) => { if (!n) return null; const x = n.getBoundingClientRect(); return [Math.round(x.left), Math.round(x.top), Math.round(x.width), Math.round(x.height)]; };
        return { board: r(document.querySelector("#scoreBoardWrapper")), tab: r(document.querySelector(".rvTab")), notice: r(document.querySelector(".spot-messageBox")) };`);
      await b.screenshot(path.join(OUT, `rounds-${name}@${vp}.png`));
    }
    const view = await b.evaluate("return [innerWidth, innerHeight, document.querySelector('#mainContainer').classList.contains('playspace-compact')];");
    fs.writeFileSync(path.join(OUT, `rounds@${vp}.json`), JSON.stringify({ view: [view[0], view[1]], compact: view[2], rects }, null, 1));
    console.log(vp, JSON.stringify(rects.tab), "errors", JSON.stringify(b.takeErrors()).slice(0, 300));
  } finally { await b.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }
}
