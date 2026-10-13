// The word's white-outline box in a frame: the same test measure2.mjs ran on the video, for a lab frame.
//   node bbox.mjs <png> [<png> ...]
import fs from "node:fs"; import os from "node:os"; import path from "node:path"; import { fileURLToPath } from "node:url";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { serve } from "./serve.mjs";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const srv = await serve(HERE);
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "logo-exit-bbox-"));
const b = new Browser({ profileDir, viewport: { width: 800, height: 600, dsf: 1 } });
try {
  await b.launch();
  await b.navigate(srv.url + "/measure.html");
  for (const f of process.argv.slice(2)) {
    const rel = path.relative(HERE, path.resolve(f));
    const r = await b.evaluate(`
      const load = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
      const img = await load(${JSON.stringify(rel)}); const W = img.width, H = img.height;
      const c = document.createElement("canvas"); c.width = W; c.height = H; const g = c.getContext("2d"); g.drawImage(img, 0, 0);
      const d = g.getImageData(0, 0, W, H).data;
      let x0 = W, y0 = H, x1 = -1, y1 = -1;
      for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const i = (y * W + x) * 4; if (d[i] > 225 && d[i + 1] > 225 && d[i + 2] > 225) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } }
      return { W, H, white: x1 < 0 ? null : { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 } };
    `);
    console.log(path.basename(f), r.W + "x" + r.H, "white", JSON.stringify(r.white));
  }
} finally { await b.close(); await srv.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }
