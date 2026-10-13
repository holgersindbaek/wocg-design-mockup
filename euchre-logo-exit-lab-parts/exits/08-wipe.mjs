// Wipe: a hand brushes the word off the felt, left to right. The word recoils a touch as the brush comes in, then
// a slanted clipping edge sweeps across it faster and faster; the word is dragged a little the same way and leans
// into the brush, so the edge is seen taking a moving word, not a still one.
// The wipe bone is a child of logo2, so the word's own slide and lean carry the rectangle with them: only the wipe
// bone's X moves the edge across the word, and the lean slants the edge along with the strokes.
export default {
  id: "wipe",
  name: "Wipe",
  summary: "The word recoils a touch, then a slanted edge sweeps across it from the left, faster and faster, like a palm brushing it off the felt. The word slides a little with the brush and leans into it as it is taken.",
  spine: "The wipe clipping slot keyed on at 0 and its bone translated 1480 px in X with an ease-in (quad) over twelve frames, rotated -6 degrees so the edge slants a little more than the leaning strokes and scaled 1.3 in Y so the slanted rectangle still covers the word at 0; logo2 pulls back 22 px over two frames then slides 70 px right and shears Y to -16 degrees with the same ease-in.",
  duration: 12 / 30,
  build(tl, ctx) {
    const [hx, hy] = ctx.handoff.translate, hs = ctx.handoff.scale;
    const f = (n) => n / 30;
    const w = ctx.wipe;
    tl.slot(w.slot).attachment([[0, w.attachment]]);
    tl.bone(w.bone)
      .scale([[0, 1, 1.3]])
      .rotate([[0, -6]])
      .translate([[0, 0, 0, "inQuad"], [f(12), 1480, 0]]);
    tl.bone("logo2")
      .translate([
        [0, hx, hy, "outCubic"],
        [f(2), hx - 22, hy, "inQuad"],
        [f(12), hx + 70, hy]
      ])
      .shear([
        [0, 0, 0, "outCubic"],
        [f(2), 0, 7, "inOutQuad"],
        [f(8), 0, -14, "linear"],
        [f(12), 0, -16]
      ])
      .scale([
        [0, hs, hs, "outCubic"],
        [f(2), hs * 0.99, hs * 1.01, "inQuad"],
        [f(12), hs * 1.05, hs * 0.97]
      ]);
  }
};
