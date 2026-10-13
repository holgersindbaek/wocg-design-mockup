// Cuts logo.png (the word EUCHRE from Khang's Spine atlas) into its six letters along the dark seam between
// neighbouring letters, so a letter can leave on its own; the six together draw the word exactly as before.
//
//   node cut-letters.mjs
//
// Writes letters/logo_E1.png ... logo_E2.png (each cropped to its own pixels) and letters/letters.json with each
// letter's box in logo.png's pixels, which build-spine.mjs turns into Spine bones, slots and attachments.
import fs from "node:fs"; import os from "node:os"; import path from "node:path"; import { fileURLToPath } from "node:url";
import { Browser } from "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/scripts/visual-sweep/lib/browser.mjs";
import { serve } from "./serve.mjs";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const srv = await serve(HERE);
const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "logo-exit-cut-"));
const b = new Browser({ profileDir, viewport: { width: 800, height: 600, dsf: 1 } });
try {
  await b.launch();
  await b.navigate(srv.url + "/measure.html");
  const r = await b.evaluate(`
    const NAMES = ["E1", "U", "C", "H", "R", "E2"], VALLEYS = [232, 445, 634, 840, 1018], BAND = 48, SMOOTH = 6;
    const load = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; });
    const img = await load("logo.png"); const W = img.width, H = img.height;
    const c = document.createElement("canvas"); c.width = W; c.height = H; const g = c.getContext("2d"); g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, W, H).data;
    const A = (x, y) => d[(y * W + x) * 4 + 3], L = (x, y) => { const i = (y * W + x) * 4; return (d[i] * 299 + d[i + 1] * 587 + d[i + 2] * 114) / 1000; };
    // the darkest continuous path through the band around column v, over the rows the word covers
    const seam = (v) => {
      const x0 = v - BAND, n = 2 * BAND;
      let top = -1, bot = -1;
      for (let y = 0; y < H; y++) { let any = false; for (let x = x0; x < x0 + n; x++) if (A(x, y) >= 200) { any = true; break; } if (any) { if (top < 0) top = y; bot = y; } }
      const cost = (x, y) => A(x, y) >= 200 ? L(x, y) : 255;
      const rows = bot - top + 1, acc = new Float64Array(rows * n), back = new Int32Array(rows * n);
      for (let j = 0; j < n; j++) acc[j] = cost(x0 + j, top);
      for (let r = 1; r < rows; r++) for (let j = 0; j < n; j++) {
        let best = Infinity, arg = j;
        for (let dd = -2; dd <= 2; dd++) { const k = j + dd; if (k < 0 || k >= n) continue; const v2 = acc[(r - 1) * n + k] + SMOOTH * Math.abs(dd); if (v2 < best) { best = v2; arg = k; } }
        acc[r * n + j] = best + cost(x0 + j, top + r); back[r * n + j] = arg;
      }
      let j = 0; for (let k = 1; k < n; k++) if (acc[(rows - 1) * n + k] < acc[(rows - 1) * n + j]) j = k;
      const px = new Int32Array(H).fill(v);
      for (let r = rows - 1; r >= 0; r--) { px[top + r] = x0 + j; j = back[r * n + j]; }
      for (let y = 0; y < top; y++) px[y] = px[top]; for (let y = bot + 1; y < H; y++) px[y] = px[bot];
      return Array.from(px);
    };
    const seams = VALLEYS.map(seam);
    const out = [];
    let sum = null;
    for (let i = 0; i < NAMES.length; i++) {
      const left = i ? seams[i - 1] : null, right = i < seams.length ? seams[i] : null;
      const pc = document.createElement("canvas"); pc.width = W; pc.height = H; const pg = pc.getContext("2d");
      const id = pg.createImageData(W, H), p = id.data;
      let x0 = W, y0 = H, x1 = -1, y1 = -1;
      for (let y = 0; y < H; y++) { const l = left ? left[y] : -1, rt = right ? right[y] : W; for (let x = Math.max(0, l); x < rt; x++) { const k = (y * W + x) * 4; if (d[k + 3] === 0) continue; p[k] = d[k]; p[k + 1] = d[k + 1]; p[k + 2] = d[k + 2]; p[k + 3] = d[k + 3]; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } }
      pg.putImageData(id, 0, 0);
      const w = x1 - x0 + 1, h = y1 - y0 + 1;
      const cc = document.createElement("canvas"); cc.width = w; cc.height = h; cc.getContext("2d").drawImage(pc, x0, y0, w, h, 0, 0, w, h);
      out.push({ name: NAMES[i], file: "logo_" + NAMES[i] + ".png", x: x0, y: y0, w, h, seamTop: right ? right[0] : null, seamBottom: right ? right[H - 1] : null, png: cc.toDataURL("image/png") });
    }
    return { W, H, letters: out };
  `, { timeout: 120000 });
  const dir = path.join(HERE, "letters"); fs.mkdirSync(dir, { recursive: true });
  for (const l of r.letters) { fs.writeFileSync(path.join(dir, l.file), Buffer.from(l.png.split(",")[1], "base64")); delete l.png; }
  fs.writeFileSync(path.join(dir, "letters.json"), JSON.stringify({ logo: { w: r.W, h: r.H }, letters: r.letters }, null, 1));
  console.log(JSON.stringify(r.letters));
} finally { await b.close(); await srv.close(); fs.rmSync(profileDir, { recursive: true, force: true }); }
