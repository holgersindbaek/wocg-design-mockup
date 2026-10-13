// Spin toss: a quick crouch and tilt, then the word is flicked up towards the point where the jack vanished,
// turning twice on the way and shrinking to nothing as it recedes.
export default {
  id: "spin",
  name: "Spin toss",
  summary: "The word crouches and tilts for a beat, then is tossed up towards where the jack went: it spins two full turns, grows a touch as it leaves the hand, and shrinks to nothing at the vanishing point.",
  spine: "Rotate, translate and scale on logo2: a four-frame wind-up (rotate -12, down 18, squash to 1.0 x 0.92), then rotate to +708 over 14 frames with a mild ease-out, translate to the pivot with an out-back ease, and scale popping to 1.04 before easing in to 0.",
  duration: 18 / 30,
  build(tl, ctx) {
    const [x, y] = ctx.handoff.translate, s = ctx.handoff.scale, p = ctx.pivot;
    tl.bone("logo2")
      .rotate([[0, 0, "outQuad"], [4 / 30, -12, [0.4, 0.5, 0.8, 0.9]], [18 / 30, 708]])
      .translate([[0, x, y, "outQuad"], [4 / 30, x, y - 18, "outBack"], [16 / 30, p.x, p.y], [18 / 30, p.x, p.y]])
      .scale([[0, s, s, "outQuad"], [4 / 30, 1.0, 0.92, "outQuad"], [7 / 30, 1.04, 1.04, "inQuad"], [18 / 30, 0, 0]]);
  }
};
