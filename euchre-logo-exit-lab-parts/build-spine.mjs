// Builds the Spine file with the exits and the lab's data from Khang's export and the exits/ modules.
//
//   node build-spine.mjs
//
// Reads khang/ (the 13 Oct Spine 4.2 export: euchre.json, euchre.atlas.txt, euchre.png, euchre_2.png), letters/ (cut-letters.mjs)
// and every exits/*.mjs. Adds to Khang's skeleton: a bone and slot per letter with the cut letter as its attachment
// (hidden in the setup pose), a `wipe` bone and clipping slot in front of the word that clips the word and the
// letters (no attachment in the setup pose), and one animation per exit named exit_<id>. Writes
//   spine-data.js                      the skeleton, atlas and images inlined for the lab (file://)
//   for-khang/euchre-logo-exits.json   the skeleton for Spine: Import Data makes a project of it
//   for-khang/images/*.png             every attachment's image, so the imported project is whole
//   for-khang/README.md                how to open it and what each animation is
//
// An exit module exports default { id, name, summary, spine, duration?, light?, build(tl, ctx) }:
//   id         short, [a-z0-9-]; the animation is exit_<id> and the tile anchors on it
//   name       the tile's title; summary: a sentence or two on what the viewer sees
//   spine      one sentence to Khang: which bones and keys do it, and anything he needs to redo (per-letter art)
//   duration   seconds until the felt is empty; otherwise the last key
//   light      true when the exit keys light_1 itself (the additive shine); otherwise it is kept invisible
//   build(tl, ctx)   fills a Timeline (spine-keys.mjs) given ctx:
//     ctx.handoff      { translate: [x, y], scale }   logo2's keys at t=0, the pose at the hand-off frame
//     ctx.handoffCentre  { x, y }  the word's centre at the hand-off, in scene px (1920 x 1447, y down)
//     ctx.wordKeys(time, scale, { x, y })  -> { scale: [t, s, s], translate: [t, x, y] }: logo2's keys that put the
//                      word's centre at that point of the frame (scene px) at that scale; add an ease as a 4th/5th item
//     ctx.pivot        { x, y }  the point Khang's shrink pulls the word to, in logo2's local space (its setup pose)
//     ctx.word         { x, y, width, height }  the logo attachment's box in logo2's local space (y up)
//     ctx.letters      (with --letters, else [])  [{ name, bone, slot, attachment, x, y, width, height }], left to right; x, y
//                      are each letter bone's position in logo2's local space (the letter's centre); the attachment
//                      sits at the bone's origin. Keying letters: hide the word (slot logo attachment null at 0) and
//                      show each letter slot's attachment at 0, then move the letter bones.
//     ctx.wipe         (with --letters, else null)  { bone, slot, attachment, rect: { x0, y0, x1, y1 } }  the clipping rectangle that
//                      shows what is inside it once its attachment is keyed on; move or scale the bone to wipe.
//     ctx.fps          30
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL, fileURLToPath } from "node:url";
import { Timeline } from "./spine-keys.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const K = path.join(HERE, "khang");
const OUT = path.join(HERE, "for-khang");
const skel = JSON.parse(fs.readFileSync(path.join(K, "euchre.json"), "utf8"));
const atlasText = fs.readFileSync(path.join(K, "euchre.atlas.txt"), "utf8");
const lettersInfo = JSON.parse(fs.readFileSync(path.join(HERE, "letters", "letters.json"), "utf8"));

// the measured hand-off (measure2.mjs): logo.png (the atlas region, 1252 x 413, whitespace stripped by 7 left and
// 5 top from the 1266 x 424 attachment image) drawn at scale 0.968 with its top-left at scene px (354.1, 709.3),
// in a 1920 x 1447 frame whose centre is Spine's origin (y up)
const SCENE = { w: 1920, h: 1447 };
const HAND = { x: 354.1, y: 709.3, scale: 0.968, trimLeft: 7, trimTop: 5 };
const PIVOT_PX = { x: 960, y: 670 };
const logoAtt = skel.skins[0].attachments.logo.logo;          // { x: -9.29, y: -55, width: 1266, height: 424 }
const logo2 = skel.bones.find((b) => b.name === "logo2");     // { x: 9.32, y: -197.62 } under root
const toSpine = (px, py) => ({ x: px - SCENE.w / 2, y: SCENE.h / 2 - py });

const centrePx = { x: HAND.x - HAND.trimLeft * HAND.scale + logoAtt.width / 2 * HAND.scale, y: HAND.y - HAND.trimTop * HAND.scale + logoAtt.height / 2 * HAND.scale };
const centre = toSpine(centrePx.x, centrePx.y);
const boneWorld = { x: centre.x - logoAtt.x * HAND.scale, y: centre.y - logoAtt.y * HAND.scale };
const handoff = { translate: [round(boneWorld.x - logo2.x), round(boneWorld.y - logo2.y)], scale: HAND.scale };
const pivotWorld = toSpine(PIVOT_PX.x, PIVOT_PX.y);
const pivot = { x: round(pivotWorld.x - logo2.x), y: round(pivotWorld.y - logo2.y) };

// letters: boxes in logo.png px -> the attachment image's px -> logo2's local space (the letter's centre)
const letters = lettersInfo.letters.map((l) => {
  const cxImg = l.x + l.w / 2 + HAND.trimLeft, cyImg = l.y + l.h / 2 + HAND.trimTop;
  return {
    name: l.name, bone: "letter_" + l.name, slot: "letter_" + l.name, attachment: "logo_" + l.name, file: l.file,
    x: round(logoAtt.x + (cxImg - logoAtt.width / 2)), y: round(logoAtt.y - (cyImg - logoAtt.height / 2)), width: l.w, height: l.h
  };
});
const wipe = { bone: "wipe", slot: "wipe", attachment: "wipe", rect: { x0: -700, y0: -310, x1: 700, y1: 210 } };
const WITH_LETTERS = process.argv.includes("--letters");

// --- the skeleton additions ---
const out = JSON.parse(JSON.stringify(skel));
out.skeleton.images = "./images/";
out.skeleton.audio = "";
if (WITH_LETTERS) {
  letters.forEach((l) => out.bones.push({ name: l.bone, parent: "logo2", x: l.x, y: l.y }));
  out.bones.push({ name: wipe.bone, parent: "logo2" });
  const logoIndex = out.slots.findIndex((s) => s.name === "logo");
  out.slots.splice(logoIndex + 1, 0, ...letters.map((l) => ({ name: l.slot, bone: l.bone })));
  out.slots.splice(logoIndex, 0, { name: wipe.slot, bone: wipe.bone });
  const skin = out.skins[0].attachments;
  // Khang's closing circle (mask2, the iris of active_1) clips every slot up to the word; a clip cannot start inside
  // another's range, so the circle then ends at the jack's last slot and the wipe can clip the word and the letters.
  skin.mask2.mask2.end = "crown";
  letters.forEach((l) => { skin[l.slot] = {}; skin[l.slot][l.attachment] = { width: l.width, height: l.height }; });
  const R = wipe.rect;
  skin[wipe.slot] = {}; skin[wipe.slot][wipe.attachment] = { type: "clipping", end: letters[letters.length - 1].slot, vertexCount: 4, vertices: [R.x0, R.y0, R.x0, R.y1, R.x1, R.y1, R.x1, R.y0] };
}

// --- the exits ---
const files = fs.readdirSync(path.join(HERE, "exits")).filter((f) => /\.mjs$/.test(f)).sort();
const exits = [];
for (const f of files) {
  let mod;
  try { mod = (await import(pathToFileURL(path.join(HERE, "exits", f)).href + "?t=" + Date.now())).default; }
  catch (e) { console.log("skip " + f + ": it does not load: " + (e && e.message)); continue; }
  if (!mod || !mod.id || !mod.build) { console.log("skip " + f + ": no default export with id and build"); continue; }
  const tl = new Timeline();
  try { mod.build(tl, { handoff, handoffCentre: { x: centrePx.x, y: centrePx.y }, wordKeys, pivot, word: { x: logoAtt.x, y: logoAtt.y, width: logoAtt.width, height: logoAtt.height }, letters: WITH_LETTERS ? letters : [], wipe: WITH_LETTERS ? wipe : null, fps: 30 }); }
  catch (e) { console.log("skip " + f + ": build threw: " + (e && e.stack || e)); continue; }
  if (!tl.bones.logo2 || !tl.bones.logo2.translate) tl.bone("logo2").translate([[0, handoff.translate[0], handoff.translate[1]]]);
  if (!tl.bones.logo2.scale) tl.bone("logo2").scale([[0, handoff.scale, handoff.scale]]);
  if (!mod.light && !(tl.slots.light_1 && tl.slots.light_1.rgba)) tl.slot("light_1").alpha([[0, 0]]);
  const animation = "exit_" + mod.id;
  out.animations[animation] = tl.toJSON();
  const duration = Math.round((mod.duration || tl.end()) * 1000);
  exits.push({ slug: f.replace(/\.mjs$/, ""), id: mod.id, name: mod.name, summary: mod.summary || "", spine: mod.spine || "", animation, duration });
  console.log("exit " + animation.padEnd(22) + String(duration).padStart(5) + " ms  " + f);
}

// --- the lab's data: Khang's atlas (both pages, the banner background included so additive light blends on it
// inside the WebGL canvas) and a page per letter ---
const dataUrl = (file, type) => "data:" + type + ";base64," + fs.readFileSync(file).toString("base64");
let atlas = atlasText.trimEnd() + "\n";
const images = { "euchre.png": dataUrl(path.join(K, "euchre.png"), "image/png"), "euchre_2.png": dataUrl(path.join(K, "euchre_2.png"), "image/png") };
if (WITH_LETTERS) for (const l of letters) {
  atlas += "\n" + l.file + "\nsize:" + l.width + "," + l.height + "\nfilter:Linear,Linear\n" + l.attachment + "\nbounds:0,0," + l.width + "," + l.height + "\n";
  images[l.file] = dataUrl(path.join(HERE, "letters", l.file), "image/png");
}
const data = { json: JSON.stringify(out), atlas, images, exits, handoff, pivot };
writeAtomic(path.join(HERE, "spine-data.js"), "// made by build-spine.mjs: Khang's skeleton with the exits, inlined for file://\nwindow.EUCHRE_EXITS = " + JSON.stringify(data) + ";\n");

// --- Khang's folder ---
fs.mkdirSync(path.join(OUT, "images"), { recursive: true });
writeAtomic(path.join(OUT, "euchre-logo-exits.json"), JSON.stringify(out));
if (WITH_LETTERS) for (const l of letters) fs.copyFileSync(path.join(HERE, "letters", l.file), path.join(OUT, "images", l.file));
else for (const l of letters) fs.rmSync(path.join(OUT, "images", l.file), { force: true });
unpackAtlas();
fs.writeFileSync(path.join(OUT, "README.md"), readme());
const zipped = spawnSync("zip", ["-q", "-r", "-X", path.join(HERE, "euchre-logo-exits-for-khang.zip"), "for-khang"], { cwd: HERE });
if (zipped.status !== 0) console.log("could not zip for-khang: " + String(zipped.stderr).trim());
console.log("wrote spine-data.js and for-khang/ with " + exits.length + " exits; hand-off keys logo2 translate " + handoff.translate.join(", ") + " scale " + handoff.scale + "; pivot " + pivot.x + ", " + pivot.y);

function round(v) { return Math.round(v * 100) / 100; }
// logo2's scale and translate keys that put the word's centre at a point of the frame (scene px) at a scale
function wordKeys(time, scale, centre) {
  const c = toSpine(centre.x, centre.y);
  return { scale: [time, scale, scale], translate: [time, round(c.x - logoAtt.x * scale - logo2.x), round(c.y - logoAtt.y * scale - logo2.y)] };
}
function writeAtomic(file, text) { fs.writeFileSync(file + ".tmp", text); fs.renameSync(file + ".tmp", file); }

// every region of Khang's atlas as its own image, the stripped whitespace put back, so Import Data finds them all
function unpackAtlas() {
  const pages = atlasText.split(/\n(?=\S+\.png\n)/).map((s) => s.trim()).filter(Boolean);
  for (const page of pages) {
    const lines = page.split("\n");
    const file = lines[0];
    const src = path.join(K, file);
    if (!fs.existsSync(src)) continue;
    let i = 1; while (i < lines.length && /^\w+:/.test(lines[i])) i++;
    while (i < lines.length) {
      const name = lines[i++]; const props = {};
      while (i < lines.length && /^\w+:/.test(lines[i])) { const [k, v] = lines[i++].split(":"); props[k] = v.split(",").map(Number); }
      const [x, y, w, h] = props.bounds; const rot = props.rotate && props.rotate[0] === 90;
      const filters = [rot ? "crop=" + h + ":" + w + ":" + x + ":" + y + ",transpose=2" : "crop=" + w + ":" + h + ":" + x + ":" + y];
      if (props.offsets) { const [ox, oy, ow, oh] = props.offsets; filters.push("pad=" + ow + ":" + oh + ":" + ox + ":" + (oh - oy - h) + ":color=black@0.0"); }
      const dest = path.join(OUT, "images", name + ".png");
      const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-i", src, "-vf", filters.join(","), "-pix_fmt", "rgba", dest]);
      if (r.status !== 0) console.log("could not unpack " + name + ": " + String(r.stderr).trim());
    }
  }
}

function readme() {
  const real = exits.filter((e) => !/^00-/.test(e.slug)).length;
  const rows = exits.map((e) => "- `" + e.animation + "` (" + (e.duration / 1000).toFixed(2) + " s): " + e.name + ". " + e.summary + (e.spine ? " In Spine: " + e.spine : "")).join("\n");
  return `# Euchre logo exits, for Spine 4.2

This is your 13 Oct export of the Euchre skeleton with ${real} extra animation${real === 1 ? "" : "s"}: your own shrink of the word
EUCHRE after the jack has sunk into it, varied. \`exit_shrink\` is your shrink as it is in the 13 Oct render, rebuilt
from measurements of the video (the lab used it to check that its hand-off from your render is exact); the others
are the variations. Holger picks one; this file shows how it moves.

## Open it

1. In Spine 4.2.43 or later: File > Import Data, choose \`euchre-logo-exits.json\`, into a new project.
2. The images are in \`images/\` beside it (the JSON's images path points there): your own attachment images
   unpacked from the atlas, plus the six letters.
3. Save the project. To bring one animation into your own project, use File > Import Project on that saved
   project and choose the animation; the bones and slots it keys (below) must exist there by the same names.

${WITH_LETTERS ? `## What was added

- Bones \`letter_E1\`, \`letter_U\`, \`letter_C\`, \`letter_H\`, \`letter_R\`, \`letter_E2\` under \`logo2\`, each at its
  letter's centre, with slots of the same names right after \`logo\` in the draw order and attachments
  \`logo_E1\` ... \`logo_E2\`. The letter images are cut from the flattened word along the dark seam between
  letters, so together they draw the word exactly; a letter on its own shows a cut edge where it touched its
  neighbour. For the real thing, cut each letter from the vector source with its full outline.
- Bone \`wipe\` under \`logo2\` with a clipping slot \`wipe\` just before \`logo\` (end: letter_E2), a rectangle around
  the word that clips the word and the letters; it has no attachment in the setup pose and the wipe exit keys it
  on. For that to work, your closing circle \`mask2\` now ends at \`crown\` instead of \`logo\` (a clip cannot start
  inside another clip's range), so in active_1 the circle no longer clips the word.

` : `## What was added

Nothing but the animations: no new bones, slots or images. The skeleton is your export as it was.

`}## The animations

Every exit starts from the pose your 13 Oct render has at 1.60 s (frame 48), the first frame with the jack gone:
\`logo2\` translate ${handoff.translate.join(", ")} and scale ${handoff.scale} (keys at 0). Paste an exit's keys after your
jack move so they continue from there. The shine \`light_1\` is keyed invisible unless the exit uses it.

${rows}
`;
}
