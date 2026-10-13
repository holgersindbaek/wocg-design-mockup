// Khang's shrink smoothed: one straight line from the hand-off to where his word vanishes (6 px right, 42 px down),
// the scale and the move on the same curve so the word never changes direction, his ease-out kept, and his fade over
// the last four frames.
const END = { scale: 0.19, x: 967, y: 952 };
const EASE = [0.35, 0.4, 0.7, 0.9];
export default {
  id: "smooth",
  name: "Smooth",
  summary: "The same shrink on one straight line: the word sinks to where Khang's vanishes, easing out as it goes, and fades over the last four frames. No change of direction on the way.",
  spine: "On logo2, two keys each for scale (0.968 to 0.19) and translate, both on the same curve, 11 frames; the logo slot's alpha 1 to 0 over the last four frames.",
  build(tl, ctx) {
    const a = ctx.wordKeys(0, ctx.handoff.scale, ctx.handoffCentre), b = ctx.wordKeys(11 / 30, END.scale, END);
    tl.bone("logo2").scale([[...a.scale, EASE], b.scale]).translate([[...a.translate, EASE], b.translate]);
    tl.slot("logo").alpha([[0, 1], [7 / 30, 1], [8 / 30, 0.75], [9 / 30, 0.4], [10 / 30, 0.12], [11 / 30, 0]]);
  }
};
