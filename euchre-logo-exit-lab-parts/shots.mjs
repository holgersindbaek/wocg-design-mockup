// Dumps an exit's frames from the lab as a contact sheet, so a move can be judged without a screen.
//
//   node shots.mjs [--exit <slug or id> ...] [--fps 20] [--width 480] [--cols 8]
//
// Writes shots/<slug>/<ms>.png per frame (the background and the skeleton drawn by the lab's own renderer, LAB.frame)
// and shots/<slug>.png as the sheet (each frame stamped with its time), and prints one line per exit with its duration
// and the sheet's path. Without --exit it dumps every built exit.
// Runs Chrome for Testing headless (with the GPU, for WebGL) over the lab served from WoCG-3; video decoding is
// skipped in shots mode and the page needs its fonts from the folder above.
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
const num = (k, d) => { const i = args.indexOf("--" + k); return i > -1 ? Number(args[i + 1]) : d; };
const only = []; args.forEach((a, i) => { if (a === "--exit") only.push(args[i + 1]); });
const fps = num("fps", 20), width = num("width", 480), cols = num("cols", 8);
const FONT = "/System/Library/Fonts/Helvetica.ttc";

const srv = await serve(ROOT);
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "logo-exit-shots-"));
const b = new Browser({ profileDir, viewport: { width: Math.max(1200, width + 80), height: 1000, dsf: 1 }, gpu: true });
try {
  await b.launch();
  await b.navigate(srv.url + "/euchre-logo-exit-lab.html?shots=1&size=" + width);
  await b.evaluate("await LAB.ready; return true", { timeout: 60000 });
  const list = await b.evaluate("return LAB.list()");
  const errs = b.takeErrors();
  if (errs.length) console.log("page errors:", errs.map((e) => e.text).join(" | "));
  const wanted = only.length ? list.filter((x) => only.includes(x.slug) || only.includes(x.id)) : list;
  if (!wanted.length) { console.log("no such exit; built exits:", list.map((x) => x.slug).join(", ")); process.exit(1); }
  for (const x of wanted) {
    const dir = path.join(HERE, "shots", x.slug);
    fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    const times = []; for (let k = 0; k * 1000 / fps < x.duration; k++) times.push(Math.floor(k * 1000 / fps)); times.push(x.duration);
    let k = 0;
    for (const t of times) {
      const url = await b.evaluate(`return LAB.frame(${JSON.stringify(x.slug)}, ${t}, ${width})`);
      fs.writeFileSync(path.join(dir, String(k++).padStart(3, "0") + "-" + String(t).padStart(4, "0") + ".png"), Buffer.from(url.split(",")[1], "base64"));
    }
    const rows = Math.ceil(times.length / cols);
    const sheet = path.join(HERE, "shots", x.slug + ".png");
    const label = fs.existsSync(FONT) ? `,drawtext=fontfile=${FONT}:text='%{eif\\:min(n*1000/${fps}\\,${x.duration})\\:d} ms':x=10:y=10:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=6` : "";
    const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-framerate", "1", "-pattern_type", "glob", "-i", path.join(dir, "*.png"), "-vf", `pad=iw+6:ih+6:3:3:color=#f6f2ea${label},tile=${cols}x${rows}`, sheet]);
    if (r.status !== 0) console.log("ffmpeg failed for", x.slug, String(r.stderr));
    const pe = b.takeErrors();
    console.log(x.slug.padEnd(12), String(x.duration).padStart(5), "ms", String(times.length).padStart(3), "frames", sheet, pe.length ? " page errors: " + pe.map((e) => e.text).join(" | ") : "");
  }
} finally { await b.close(); await srv.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }
process.exit(0);
