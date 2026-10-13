// Letters tumble: a wave runs through the word left to right. Each letter in turn rears back, then whips over to
// the right, flipping through its own edge (scale X past zero flashes its mirror) as it topples onto its neighbour,
// and is gone edge-on. Three frames later the next letter goes, so the word is turned away in a ripple.
export default {
  id: "letters-tumble",
  name: "Letters tumble",
  summary: "A ripple runs through the word from the left: each letter rears back, whips over sideways like a flip-board tile, flashes its mirror image as it topples onto the next letter, and is gone edge-on. Three frames later the next letter follows.",
  spine: "Per letter (the six letter bones and slots, the logo slot hidden at 0): one six-frame key set offset by three frames per letter, scale X 1 to 1.2 (rear back) to -0.85 (flipped past the edge) to 0 (edge-on, gone) with scale Y easing down to 0.75, rotate +10 then -50 degrees, translate 36 right and 26 down; the letters need redoing from the vector art so each stands alone.",
  duration: 21 / 30,
  build(tl, ctx) {
    const f = (n) => n / 30;
    const STAGGER = 3;
    tl.slot("logo").attachment([[0, null]]);
    ctx.letters.forEach((l, i) => {
      const b = i * STAGGER;
      tl.slot(l.slot).attachment([[0, l.attachment]]);
      tl.bone(l.bone)
        .scale([
          [0, 1, 1],
          [f(b), 1, 1, "outQuad"],
          [f(b + 2), 1.2, 0.94, "inQuad"],
          [f(b + 4), -0.85, 0.9, "outQuad"],
          [f(b + 6), 0, 0.75]
        ])
        .rotate([
          [0, 0],
          [f(b), 0, "outQuad"],
          [f(b + 2), 10, "inQuad"],
          [f(b + 4), -30, "linear"],
          [f(b + 6), -50]
        ])
        .translate([
          [0, 0, 0],
          [f(b), 0, 0, "outQuad"],
          [f(b + 2), -18, 2, "inQuad"],
          [f(b + 4), 18, -8, "linear"],
          [f(b + 6), 36, -26]
        ]);
    });
  }
};
