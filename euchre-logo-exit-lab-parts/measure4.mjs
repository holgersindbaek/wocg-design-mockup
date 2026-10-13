// Khang's own shrink, frame by frame (48 to 59 of active.webm): the word's white-outline box, its centre, its scale
// against logo.png, and how far it has faded (the brightest white left in it against the felt).
import fs from "node:fs"; import os from "node:os"; import path from "node:path"; import { fileURLToPath } from "node:url";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { serve } from "./serve.mjs";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const srv = await serve(HERE);
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "logo-exit-measure4-"));
const b = new Browser({ profileDir, viewport: { width: 800, height: 600, dsf: 1 } });
try {
  await b.launch();
  await b.navigate(srv.url + "/measure.html");
  const r = await b.evaluate(`
    const load = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
    const bg = await load("bg.png");
    const v = document.createElement("video"); v.muted = true; v.preload = "auto"; v.src = "active.webm"; document.body.appendChild(v);
    await new Promise((res, rej) => { v.onloadeddata = res; v.onerror = () => rej(new Error("video failed")); });
    const W = v.videoWidth, H = v.videoHeight;
    const cb = document.createElement("canvas"); cb.width = W; cb.height = H; cb.getContext("2d").drawImage(bg, 0, 0);
    const B = cb.getContext("2d").getImageData(0, 0, W, H).data;
    const c = document.createElement("canvas"); c.width = W; c.height = H; const g = c.getContext("2d");
    const out = [];
    for (let k = 44; k <= 59; k++) {
      await new Promise((res) => { v.onseeked = res; v.currentTime = (k + 0.5) / 30; });
      g.drawImage(v, 0, 0);
      const D = g.getImageData(0, 0, W, H).data;
      // the window the word can be in after the jack is gone
      const X0 = 300, X1 = 1620, Y0 = 600, Y1 = 1120;
      const bb = (test) => { let x0 = W, y0 = H, x1 = -1, y1 = -1, n = 0; for (let y = Y0; y < Y1; y++) for (let x = X0; x < X1; x++) { const i = (y * W + x) * 4; if (test(i)) { n++; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } } return n ? { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1, n } : null; };
      const white = bb((i) => D[i] > 225 && D[i + 1] > 225 && D[i + 2] > 225);
      const diff60 = bb((i) => Math.abs(D[i] - B[i]) > 60 || Math.abs(D[i + 1] - B[i + 1]) > 60 || Math.abs(D[i + 2] - B[i + 2]) > 60);
      const diff25 = bb((i) => Math.abs(D[i] - B[i]) > 25 || Math.abs(D[i + 1] - B[i + 1]) > 25 || Math.abs(D[i + 2] - B[i + 2]) > 25);
      let bright = 0; for (let y = Y0; y < Y1; y++) for (let x = X0; x < X1; x++) { const i = (y * W + x) * 4; const m = Math.min(D[i], D[i + 1], D[i + 2]); if (m > bright) bright = m; }
      // the strongest red-channel excess over the felt (the orange body), as a second fade gauge
      let orange = 0; for (let y = Y0; y < Y1; y++) for (let x = X0; x < X1; x++) { const i = (y * W + x) * 4; const e = D[i] - B[i]; if (e > orange) orange = e; }
      out.push({ k, white, diff60, diff25, bright, orange });
    }
    return out;
  `, { timeout: 180000 });
  const PNG_WHITE = { x: 35, y: 9, w: 1182, h: 341 };
  for (const f of r) {
    const w = f.white; let s = "", cx = "", cy = "";
    if (w) { const sx = w.w / PNG_WHITE.w; s = sx.toFixed(3); const ox = w.x - PNG_WHITE.x * sx, oy = w.y - PNG_WHITE.y * sx; cx = (ox + 626 * sx).toFixed(1); cy = (oy + 206.5 * sx).toFixed(1); }
    const d = f.diff60, d2 = f.diff25;
    console.log("frame", f.k, "white", w ? [w.x, w.y, w.w, w.h].join(",") : "-", "scale", s || "-", "centre", cx && cy ? cx + "," + cy : "-",
      "| diff60", d ? [d.x, d.y, d.w, d.h].join(",") + " c=" + (d.x + d.w / 2).toFixed(0) + "," + (d.y + d.h / 2).toFixed(0) : "-",
      "| diff25", d2 ? [d2.x, d2.y, d2.w, d2.h].join(",") + " c=" + (d2.x + d2.w / 2).toFixed(0) + "," + (d2.y + d2.h / 2).toFixed(0) : "-", "| bright", f.bright, "orange+", f.orange);
  }
} finally { await b.close(); await srv.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }
