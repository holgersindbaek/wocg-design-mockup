// The logo's white outline box in logo.png and in frames at rest and around the hand-off: scale and offset per frame.
import fs from "node:fs"; import os from "node:os"; import path from "node:path"; import { fileURLToPath } from "node:url";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { serve } from "./serve.mjs";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const srv = await serve(HERE);
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "logo-exit-measure2-"));
const b = new Browser({ profileDir, viewport: { width: 800, height: 600, dsf: 1 } });
try {
  await b.launch();
  await b.navigate(srv.url + "/measure.html");
  const png = await b.evaluate(`
    const load = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
    const img = await load("logo.png"); const c = document.createElement("canvas"); c.width = img.width; c.height = img.height;
    const g = c.getContext("2d"); g.drawImage(img, 0, 0); const d = g.getImageData(0, 0, c.width, c.height).data; const W = c.width, H = c.height;
    const bb = (test) => { let x0 = W, y0 = H, x1 = -1, y1 = -1; for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const i = (y * W + x) * 4; if (test(d, i)) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } } return { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 }; };
    return { white: bb((d, i) => d[i + 3] >= 200 && d[i] > 225 && d[i + 1] > 225 && d[i + 2] > 225), orange: bb((d, i) => d[i + 3] >= 200 && d[i] > 200 && d[i + 1] > 90 && d[i + 1] < 215 && d[i + 2] < 90) };
  `);
  console.log("logo.png white", JSON.stringify(png.white), "orange", JSON.stringify(png.orange));
  const times = [0.5 / 30, 1.5 / 30, 2.5 / 30, 10.5 / 30]; for (let k = 44; k <= 50; k++) times.push((k + 0.5) / 30);
  const r = await b.evaluate("return await window.__frames(" + JSON.stringify(times) + ")", { timeout: 120000 });
  for (const f of r.out) {
    const w = f.white; const sx = w.w / png.white.w, sy = w.h / png.white.h;
    // where logo.png's top-left corner would sit at that scale
    const ox = w.x - png.white.x * sx, oy = w.y - png.white.y * sy;
    console.log("frame", Math.floor(f.t * 30), "white", JSON.stringify(w), "scale", sx.toFixed(4), sy.toFixed(4), "png origin", ox.toFixed(1), oy.toFixed(1), "centre", (ox + 626 * sx).toFixed(1), (oy + 206.5 * sy).toFixed(1));
  }
} finally { await b.close(); await srv.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }
