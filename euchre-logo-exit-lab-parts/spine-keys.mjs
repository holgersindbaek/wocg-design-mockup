// Writes Spine 4.2 animation timelines (the JSON export format Spine imports back) from short key lists.
//
//   import { Timeline } from "./spine-keys.mjs";
//   const tl = new Timeline();
//   tl.bone("logo2").translate([[0, 0, 65.1], [0.3, 0, 900, "inCubic"]]);   // [time s, x, y, ease to the next key]
//   tl.bone("logo2").scale([[0, 0.968, 0.968], [0.2, 1.08, 1.08, "outBack"], [0.45, 0, 0, "inBack"]]);
//   tl.bone("logo2").rotate([[0, 0], [0.4, 720, "inQuad"]]);                  // [time, degrees, ease]
//   tl.bone("logo2").shear([[0, 0, 0], [0.2, -18, 0, "out"]]);                // [time, x deg, y deg, ease]
//   tl.slot("logo").alpha([[0, 1], [0.4, 0, "inQuad"]]);                      // [time, 0..1, ease]  (rgba white)
//   tl.slot("logo").rgba([[0, "ffffffff"], [0.2, "ffd060ff"], [0.4, "ffffff00"]]);
//   tl.slot("logo").attachment([[0, null]]); tl.slot("letter_U").attachment([[0, "logo_U"]]);
//   tl.toJSON()  ->  { bones: {...}, slots: {...} }
//
// Values are Spine's own: translate, rotate and shear are offsets from the setup pose, scale multiplies the setup
// scale (the bones here all have scale 1, so scale is absolute). Times are seconds and are snapped to the project's
// 30 fps frames, so the keys land on whole frames in Khang's dopesheet. An ease names the curve from a key to the
// next: a name from EASES, a CSS cubic-bezier array [x1, y1, x2, y2], "stepped", or nothing for linear. The last key
// needs none.

export const FPS = 30;

export const EASES = {
  linear: null,
  spine: [1 / 3, 0, 2 / 3, 1],                 // Spine's own default (its "ease in-out")
  inQuad: [0.11, 0, 0.5, 0], outQuad: [0.5, 1, 0.89, 1], inOutQuad: [0.45, 0, 0.55, 1],
  inCubic: [0.32, 0, 0.67, 0], outCubic: [0.33, 1, 0.68, 1], inOutCubic: [0.65, 0, 0.35, 1],
  inQuart: [0.5, 0, 0.75, 0], outQuart: [0.25, 1, 0.5, 1], inOutQuart: [0.76, 0, 0.24, 1],
  inQuint: [0.64, 0, 0.78, 0], outQuint: [0.22, 1, 0.36, 1],
  inExpo: [0.7, 0, 0.84, 0], outExpo: [0.16, 1, 0.3, 1], inOutExpo: [0.87, 0, 0.13, 1],
  inCirc: [0.55, 0, 1, 0.45], outCirc: [0, 0.55, 0.45, 1],
  inBack: [0.36, 0, 0.66, -0.56], outBack: [0.34, 1.56, 0.64, 1], inOutBack: [0.68, -0.6, 0.32, 1.6],
  in: [0.55, 0.06, 0.68, 0.19], out: [0.22, 0.61, 0.36, 1], inOut: [0.65, 0, 0.35, 1],
  snap: [0.9, 0, 0.1, 1]
};

export function snap(t) { return Math.round(t * FPS) / FPS; }

function bezier(ease) {
  if (ease == null || ease === "linear") return null;
  if (ease === "stepped") return "stepped";
  if (Array.isArray(ease)) return ease;
  if (!(ease in EASES)) throw new Error("unknown ease " + ease);
  return EASES[ease];
}

// One Spine curve array for a segment: four numbers per animated component, the two bezier control points in
// absolute time and value (Spine's JSON keeps them that way).
function curveFor(ease, t0, t1, from, to) {
  const b = bezier(ease);
  if (b === null) return undefined;
  if (b === "stepped") return "stepped";
  const out = [];
  for (let i = 0; i < from.length; i++) {
    out.push(round(t0 + (t1 - t0) * b[0]), round(from[i] + (to[i] - from[i]) * b[1]), round(t0 + (t1 - t0) * b[2]), round(from[i] + (to[i] - from[i]) * b[3]));
  }
  return out;
}
function round(v) { return Math.round(v * 10000) / 10000; }

// keys: [[time, ...components, ease?]...]; n components. Returns Spine's key objects.
function keysFor(keys, n, names, defaults) {
  if (!keys.length) throw new Error("no keys");
  const parsed = keys.map((k) => {
    const time = snap(k[0]);
    const comps = k.slice(1, 1 + n).map(Number);
    if (comps.length !== n || comps.some((v) => Number.isNaN(v))) throw new Error("a key needs " + n + " numbers: " + JSON.stringify(k));
    return { time, comps, ease: k[1 + n] };
  });
  parsed.sort((a, b) => a.time - b.time);
  return parsed.map((k, i) => {
    const o = {};
    if (k.time) o.time = round(k.time);
    names.forEach((nm, j) => { if (k.comps[j] !== defaults[j]) o[nm] = round(k.comps[j]); });
    if (i < parsed.length - 1) {
      const c = curveFor(k.ease, k.time, parsed[i + 1].time, k.comps, parsed[i + 1].comps);
      if (c !== undefined) o.curve = c;
    }
    return o;
  });
}

function hexToRgba(hex) {
  const h = hex.replace("#", "");
  if (h.length !== 8) throw new Error("rgba colours are rrggbbaa: " + hex);
  return [0, 2, 4, 6].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
}
function rgbaToHex(c) { return c.map((v) => Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).padStart(2, "0")).join(""); }

export class Timeline {
  constructor() { this.bones = {}; this.slots = {}; }
  bone(name) {
    const self = this;
    const tl = (this.bones[name] = this.bones[name] || {});
    return {
      translate(keys) { tl.translate = keysFor(keys, 2, ["x", "y"], [0, 0]); return this; },
      scale(keys) { tl.scale = keysFor(keys, 2, ["x", "y"], [1, 1]); return this; },
      rotate(keys) { tl.rotate = keysFor(keys, 1, ["value"], [0]); return this; },
      shear(keys) { tl.shear = keysFor(keys, 2, ["x", "y"], [0, 0]); return this; },
      bone(n) { return self.bone(n); }, slot(n) { return self.slot(n); }
    };
  }
  slot(name) {
    const self = this;
    const tl = (this.slots[name] = this.slots[name] || {});
    return {
      // [time, rrggbbaa, ease]
      rgba(keys) {
        const parsed = keys.map((k) => ({ time: snap(k[0]), comps: hexToRgba(k[1]), ease: k[2] })).sort((a, b) => a.time - b.time);
        tl.rgba = parsed.map((k, i) => {
          const o = {};
          if (k.time) o.time = round(k.time);
          o.color = rgbaToHex(k.comps);
          if (i < parsed.length - 1) {
            const c = curveFor(k.ease, k.time, parsed[i + 1].time, k.comps, parsed[i + 1].comps);
            if (c !== undefined) o.curve = c;
          }
          return o;
        });
        return this;
      },
      // [time, alpha 0..1, ease]: white with that alpha
      alpha(keys) { return this.rgba(keys.map((k) => [k[0], "ffffff" + Math.round(Math.max(0, Math.min(1, k[1])) * 255).toString(16).padStart(2, "0"), k[2]])); },
      // [time, attachment name or null]
      attachment(keys) {
        tl.attachment = keys.map((k) => { const o = {}; if (snap(k[0])) o.time = round(snap(k[0])); o.name = k[1]; return o; }).sort((a, b) => (a.time || 0) - (b.time || 0));
        return this;
      },
      bone(n) { return self.bone(n); }, slot(n) { return self.slot(n); }
    };
  }
  toJSON() {
    const out = {};
    if (Object.keys(this.slots).length) out.slots = this.slots;
    if (Object.keys(this.bones).length) out.bones = this.bones;
    return out;
  }
  // the last keyed time, in seconds
  end() {
    let t = 0;
    const scan = (group) => Object.values(group).forEach((tls) => Object.values(tls).forEach((keys) => keys.forEach((k) => { t = Math.max(t, k.time || 0); })));
    scan(this.bones); scan(this.slots);
    return t;
  }
}
