// Checks message-toast-lab.html the way it was checked when it was built: opened from disk in Chrome for Testing
// (the visual sweep's own driver, a throwaway profile, closed in a finally), driven through its own hash, keys and
// postMessage protocol (window.__mtlab).
//
// Run: node message-toast-lab-parts/check.mjs <step> [hash]
//   types      the box's and the toast's computed type, fonts, the felt, and the stack in B at rest
//   selftest   every event with every motion and placement, off the clock (SWAP=tick by default; one swap per run,
//              because ~/bin/reap-headless-chrome.sh ends any headless browser older than five minutes)
//   speed      quarter speed and pause hold the script and every transition in every frame
//   shots      the screenshots, into /tmp/mtlab-shots/
import fs from "node:fs";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";

const LAB = "file://" + new URL("../message-toast-lab.html", import.meta.url).pathname;
const OUT = "/tmp/mtlab-shots";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const step = process.argv[2] || "types";
const hash = process.argv[3] || "";
fs.mkdirSync(OUT, { recursive: true });
fs.rmSync("/tmp/mtlab-check-profile", { recursive: true, force: true });
const b = new Browser({ profileDir: "/tmp/mtlab-check-profile", viewport: { width: 1500, height: 1400, dsf: 1 }, log: () => {} });
const failed = [];

async function open(h) {
  await b.navigate("about:blank");            // a new hash alone is a same-document navigation, with no load event
  await b.navigate(LAB + (h ? "#" + h : ""));
  return b.evaluate(`
    const t0 = Date.now();
    while (Date.now() - t0 < 60000) {
      const s = window.__mtlab && window.__mtlab.state();
      if (s && Object.keys(s.ready).length === 3 && Object.values(s.ready).every((g) => g === s.gen)) return { ms: Date.now() - t0, fonts: s.fonts, prepass: s.prepass };
      await new Promise((r) => setTimeout(r, 100));
    }
    return { timeout: true };
  `, { timeout: 70000 });
}
const probe = () => b.evaluate(`return await window.__mtlab.probe();`);
const at = async (t) => { await b.evaluate(`window.__mtlab.pause(true); window.__mtlab.seek(${t}); return 1;`); await sleep(350); };
async function clip(which, file) {
  const sel = which === 0 ? "#row1 figure .fwrap" : "#row2 figure:nth-child(" + which + ") .fwrap";
  const r = await b.evaluate(`const e = document.querySelector(${JSON.stringify(sel)}); e.scrollIntoView({ block: "center" }); await new Promise((r) => setTimeout(r, 150));
    const q = e.getBoundingClientRect(); return { x: q.x + scrollX, y: q.y + scrollY, width: q.width, height: q.height };`);
  const s = await b.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { ...r, scale: 1 } });
  fs.writeFileSync(file, Buffer.from(s.data, "base64"));
  console.log("  " + file);
}

const STEPS = {
  async types() {
    for (const h of ["ev=E4&p=B", "ev=E1&x=1", "ev=E1&p=A&ts=table"]) {
      console.log(h, JSON.stringify(await open(h)));
      await at(h.includes("E4") ? 3000 : 1000);
      for (const [id, d] of Object.entries(await probe())) {
        console.log(" ", id.padEnd(9), "fonts", d.fonts, "| box", d.box.font, d.box.rect.map(Math.round).join(","), "| toast", d.toast.where, d.toast.font, d.toast.rect.map(Math.round).join(","),
          d.col ? "| column gap " + d.col.gap : "", "| plates", d.plates, "cards", d.cards, "| floor", d.floor, "(the live hand top less the gutter; this felt's hand top " + d.handTopHere + ")", "| errors", d.errors.length);
      }
    }
  },
  async selftest() {
    console.log(JSON.stringify(await open(hash || "ev=E4")));
    // MOTIONS=a,b narrows the run, since nine motions under one swap mode outlast the reaper's five minutes
    const motions = process.env.MOTIONS ? JSON.stringify(process.env.MOTIONS.split(",")) : "undefined";
    const r = await b.evaluate(`return await window.__mtlab.selftest({ swaps: [${JSON.stringify(process.env.SWAP || "tick")}], motions: ${motions} });`, { timeout: 280000 });
    for (const [id, d] of Object.entries(r)) { console.log(id, "runs", d.runs, "ms", d.ms, "problems", d.problems.length); d.problems.slice(0, 20).forEach((p) => console.log("   ", p)); }
  },
  async speed() {
    console.log(JSON.stringify(await open("ev=E4&p=B")));
    const snap = async () => { const w = Date.now(); const p = await probe(); return { w, p }; };
    await b.evaluate(`window.__mtlab.setSpeed("0.25"); window.__mtlab.seek(1950); window.__mtlab.pause(false); return 1;`);
    await sleep(300);
    const a = await snap(); await sleep(600); const c = await snap();
    for (const id of Object.keys(a.p)) console.log("quarter", id, "vt +" + (c.p[id].vt - a.p[id].vt).toFixed(1) + "ms in " + (c.w - a.w) + "ms", "| transitions", a.p[id].anims.map((x) => x.target + ":" + x.prop + "@" + x.ct.toFixed(0)).join(" "), "->", c.p[id].anims.map((x) => x.target + ":" + x.prop + "@" + x.ct.toFixed(0)).join(" "));
    await b.evaluate(`window.__mtlab.pause(true); return 1;`);
    await sleep(200);
    const d = await snap(); await sleep(700); const e = await snap();
    for (const id of Object.keys(d.p)) console.log("paused ", id, "vt", d.p[id].vt.toFixed(1), "->", e.p[id].vt.toFixed(1), "| toast opacity", d.p[id].toast.opacity, "->", e.p[id].toast.opacity, "| transitions", d.p[id].anims.map((x) => x.ct.toFixed(1)).join(","), "->", e.p[id].anims.map((x) => x.ct.toFixed(1)).join(","));
  },
  async shots() {
    await open("ev=E4&p=B&m=toast-drop&s=tick&fit=1");
    await at(3000);
    await b.evaluate(`window.scrollTo(0, 0); return 1;`);
    await b.screenshot(OUT + "/page-rest.png", { full: true });
    console.log("  " + OUT + "/page-rest.png");
    await b.evaluate(`document.getElementById("stage").scrollIntoView(); window.scrollBy(0, -260); return 1;`);
    await at(5260);
    await b.screenshot(OUT + "/E4-B-stage-midglide.png");
    console.log("  " + OUT + "/E4-B-stage-midglide.png");
    await open("ev=E4&p=B&m=toast-drop&s=tick&fit=0");
    await at(5260);
    for (const [i, n] of [[0, "desktop"], [1, "landscape"], [2, "portrait"]]) await clip(i, OUT + "/E4-B-" + n + "-midglide.png");
    await at(6000);
    for (const [i, n] of [[0, "desktop"], [1, "landscape"], [2, "portrait"]]) await clip(i, OUT + "/E4-B-" + n + "-rest.png");
    await open("ev=E8&p=B&m=toast-drop&s=tick&fit=0");
    await at(2000);
    await clip(2, OUT + "/E8-B-portrait-ads.png");
    await clip(1, OUT + "/E8-B-landscape-fallback.png");
    await open("ev=E8&p=B&m=toast-drop&s=tick&fit=0&ads=0");
    await at(2000);
    await clip(2, OUT + "/E8-B-portrait-noads.png");
    await open("ev=M2&p=B&m=toast-drop&s=tick&fit=0");
    await at(2530);
    for (const [i, n] of [[0, "desktop"], [1, "landscape"], [2, "portrait"]]) await clip(i, OUT + "/M2-tick-" + n + "-midtick.png");
    await open("ev=E4&p=B&m=toast-drop&s=tick&fit=0&ov=1");
    await at(3000);
    await clip(1, OUT + "/E4-B-landscape-overlay.png");
  }
};

try {
  await b.launch();
  b.on("Network.loadingFailed", (p) => failed.push(p.errorText));
  b.on("Network.responseReceived", (p) => { if (p.response.status >= 400) failed.push(p.response.status + " " + p.response.url); });
  await STEPS[step]();
  console.log("console errors", JSON.stringify(b.takeErrors()));
  console.log("failed loads", JSON.stringify(failed));
} finally {
  await b.close();
}
