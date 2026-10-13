// Renders the whole move as a video for Khang: his run-up from active.webm (frames 0 to 47) and the lab's exit from
// the hand-off on, at normal speed and at quarter speed, into for-khang/.
//
//   node reference-clip.mjs <slug or id> [--hold 24]
//
// Run build-spine.mjs first (the exit must be in spine-data.js); run build-spine.mjs again afterwards so the zip
// carries the renders. --hold: frames of empty felt held at the end (default 24).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { serve } from "./serve.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const args = process.argv.slice(2);
const slug = args.find((a) => !a.startsWith("--") && args[args.indexOf(a) - 1] !== "--hold");
if (!slug) { console.error("usage: node reference-clip.mjs <slug or id> [--hold 24]"); process.exit(2); }
const hold = (() => { const i = args.indexOf("--hold"); return i > -1 ? Number(args[i + 1]) : 24; })();
const HANDOFF_FRAME = 48, FPS = 30, W = 1920, H = 1447;
const work = fs.mkdtempSync(path.join(os.tmpdir(), "logo-exit-ref-"));

const v = spawnSync("ffmpeg", ["-v", "error", "-y", "-i", path.join(HERE, "active.webm"), "-frames:v", String(HANDOFF_FRAME), path.join(work, "v%03d.png")]);
if (v.status !== 0) throw new Error("ffmpeg could not read the video: " + v.stderr);

const srv = await serve(ROOT);
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "logo-exit-ref-profile-"));
const b = new Browser({ profileDir, viewport: { width: 1200, height: 900, dsf: 1 }, gpu: true });
let exit, frames = [];
try {
  await b.launch();
  await b.navigate(srv.url + "/euchre-logo-exit-lab.html?shots=1");
  await b.evaluate("await LAB.ready; return true", { timeout: 60000 });
  exit = (await b.evaluate("return LAB.list()")).find((x) => x.slug === slug || x.id === slug);
  if (!exit) throw new Error("no exit " + slug);
  const n = Math.round(exit.duration / 1000 * FPS);
  for (let k = 0; k <= n; k++) {
    const url = await b.evaluate(`return LAB.frame(${JSON.stringify(exit.slug)}, ${k * 1000 / FPS}, ${W})`);
    const f = path.join(work, "e" + String(k).padStart(3, "0") + ".png");
    fs.writeFileSync(f, Buffer.from(url.split(",")[1], "base64"));
    frames.push(f);
  }
} finally { await b.close(); await srv.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }

const list = [];
for (let k = 1; k <= HANDOFF_FRAME; k++) list.push(path.join(work, "v" + String(k).padStart(3, "0") + ".png"));
list.push(...frames);
for (let k = 0; k < hold; k++) list.push(frames[frames.length - 1]);
const OUT = path.join(HERE, "for-khang");
fs.mkdirSync(OUT, { recursive: true });
const base = "reference-" + exit.animation.replace(/^exit_/, "").replace(/_/g, "-");
for (const [name, speed] of [[base + ".mp4", 1], [base + "-quarter-speed.mp4", 0.25]]) {
  const txt = list.map((f) => "file '" + f + "'\nduration " + (1 / FPS / speed).toFixed(6)).join("\n") + "\nfile '" + list[list.length - 1] + "'\n";
  const lf = path.join(work, "list-" + speed + ".txt");
  fs.writeFileSync(lf, txt);
  const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lf, "-vf", "crop=" + W + ":" + (H - 1) + ":0:0,format=yuv420p", "-r", String(FPS), "-c:v", "libx264", "-crf", "18", "-movflags", "+faststart", path.join(OUT, name)]);
  if (r.status !== 0) throw new Error("ffmpeg failed: " + r.stderr);
  console.log("wrote for-khang/" + name + " (" + list.length + " frames at " + (speed === 1 ? "normal" : "quarter") + " speed)");
}
fs.rmSync(work, { recursive: true, force: true });
