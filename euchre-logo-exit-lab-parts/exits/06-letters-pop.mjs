// Letters pop: each letter swells like a bubble and then snaps to nothing, one at a time. The sequence spreads from
// the middle of the word outwards: C, H, U, R, E, E.
const F = 1 / 30;
const STAGGER = 3 * F, INHALE = 2 * F, SWELL = 3 * F, POP = 2 * F;
const ORDER = ["C", "H", "U", "R", "E1", "E2"];

export default {
  id: "letters-pop",
  name: "Letters pop",
  summary: "The letters pop one by one like bubbles, from the middle of the word outwards: each pulls in a touch, swells, and snaps to nothing.",
  spine: "Per-letter bones under logo2 (the letters cut from the vector art): scale each 1 to 0.92, up to 1.3, then to 0 in two frames, with the letter slot's alpha to 0 on the last frame; one letter every three frames from the middle out.",
  duration: (ORDER.length - 1) * STAGGER + INHALE + SWELL + POP,
  build(tl, ctx) {
    tl.slot("logo").attachment([[0, null]]);
    ctx.letters.forEach((l) => {
      const t0 = ORDER.indexOf(l.name) * STAGGER, t1 = t0 + INHALE, t2 = t1 + SWELL, t3 = t2 + POP;
      tl.slot(l.slot).attachment([[0, l.attachment]]).alpha([[0, 1], [t3 - F, 1], [t3, 0]]);
      tl.bone(l.bone).scale([...hold(t0, [1, 1], "inQuad"), [t1, 0.92, 0.92, "outQuad"], [t2, 1.3, 1.3, "inCubic"], [t3, 0, 0]]);
    });
  }
};

function hold(t, vals, ease) { return t > 0 ? [[0, ...vals], [t, ...vals, ease]] : [[0, ...vals, ease]]; }
