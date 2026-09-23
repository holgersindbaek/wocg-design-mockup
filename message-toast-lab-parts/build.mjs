// Assembles message-toast-lab.html from message-toast-lab-parts/: the shell (lab.html) and the four felt snapshots
// that capture.mjs took from the dev site, with their measured numbers. Run: node message-toast-lab-parts/build.mjs
import fs from "node:fs";
import path from "node:path";

const P = path.dirname(new URL(import.meta.url).pathname);
const DIR = path.dirname(P);
const read = (f) => fs.readFileSync(path.join(P, f), "utf8");
const SIZES = ["desktop", "landscape", "portrait", "portrait-noads"];

// Cuts one element (and everything inside it) out of an HTML string, by its id
function cutById(html, id) {
  const open = html.search(new RegExp('<(div|span|nav|ul)\\b[^>]*\\bid="' + id + '"'));
  if (open < 0) return html;
  const tag = html.slice(open + 1).match(/^\w+/)[0];
  const re = new RegExp("<" + tag + "\\b|</" + tag + ">", "g");
  re.lastIndex = open;
  let depth = 0, end = -1;
  for (let m; (m = re.exec(html));) {
    depth += m[0][1] === "/" ? -1 : 1;
    if (!depth) { end = m.index + m[0].length; break; }
  }
  return end < 0 ? html : html.slice(0, open) + html.slice(end);
}

// The snapshot's asset paths are the dev server's assets/ route, which is the static folder the ./static symlink
// points at. The party particles ("Hearts broken!" throws hearts) are frozen mid-flight in a snapshot, so they go.
function prep(html) {
  html = cutById(html, "party-js-container");
  return html
    .replace(/(src|href)="assets\//g, '$1="static/')
    .replace(/url\(&quot;assets\//g, "url(&quot;static/")
    // a lottie mask in one avatar was frozen with a NaN matrix; the live page could not apply it either, and the frame's
    // console would say so on every load
    .replace(/ transform="matrix\([^"]*NaN[^"]*\)"/g, "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/\n\s*/g, "\n");
}

let out = read("lab.html");
const metas = {};
for (const s of SIZES) {
  const html = prep(read("snap-" + s + ".html"));
  if (/<script\b/i.test(html)) throw new Error(s + ": the snapshot still holds a script");
  out = out.replace("<!--SNAP:" + s + "-->", () => html);
  const m = JSON.parse(read("snap-" + s + ".json"));
  delete m.roots;
  metas[s] = m;
}
const head = metas.desktop.wocgHead || "unknown";
out = out.replace("/*BRIEFS*/null", () => JSON.stringify(JSON.parse(read("briefs.json"))).replace(/</g, "\\u003c"));
out = out.replace("/*META*/null", () => JSON.stringify(metas).replace(/</g, "\\u003c"));
out = out.split("%%WOCG_HEAD%%").join(head);
out = out.split("%%CAPTURED%%").join(metas.desktop.captured.slice(0, 16).replace("T", " ") + " UTC");
fs.writeFileSync(path.join(DIR, "message-toast-lab.html"), out);
console.log("message-toast-lab.html " + Math.round(out.length / 1024) + " KB, wocg " + head);
