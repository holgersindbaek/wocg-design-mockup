// Letters drop: the letters leave left to right, each with a little hop up before it falls out through the bottom of
// the frame, tilting as it goes. Two frames between letters; the word is gone in 0.8 s.
const F = 1 / 30;
const STAGGER = 2 * F, HOP = 4 * F, FALL = 9 * F;

export default {
  id: "letters-drop",
  name: "Letters drop",
  summary: "The letters fall out one after another, left to right: each hops up a little, then drops through the bottom of the frame with a tilt.",
  spine: "Per-letter bones under logo2 (the letters cut from the vector art): on each, translate y up a little and then down past the frame with a rotate on the way, two frames apart per letter; the logo slot swaps to the letter slots at frame 0.",
  duration: 5 * STAGGER + HOP + FALL,
  build(tl, ctx) {
    tl.slot("logo").attachment([[0, null]]);
    ctx.letters.forEach((l, i) => {
      const t0 = i * STAGGER, t1 = t0 + HOP, t2 = t1 + FALL;
      const dir = i % 2 ? -1 : 1;
      tl.slot(l.slot).attachment([[0, l.attachment]]);
      tl.bone(l.bone)
        .translate([...hold(t0, [0, 0], "outQuad"), [t1, 0, 80, "inCubic"], [t2, dir * 50, -900]])
        .rotate([...hold(t0, [0], "outQuad"), [t1, -dir * 8, "inQuad"], [t2, dir * 36]]);
    });
  }
};

function hold(t, vals, ease) { return t > 0 ? [[0, ...vals], [t, ...vals, ease]] : [[0, ...vals, ease]]; }
