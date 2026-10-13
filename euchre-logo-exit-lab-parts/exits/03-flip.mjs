// Card flip: the word stretches up for a beat, then turns over about its middle like a card laid face down.
// Scale Y runs to a thin edge while the word lifts and widens a touch towards the camera; the edge then snaps away.
export default {
  id: "flip",
  name: "Card flip",
  summary: "The word stretches up for a beat, then flips over about its middle like a card turned face down: it thins to an edge as it lifts, and the edge snaps away.",
  spine: "Scale and translate on logo2 only: a four-frame anticipation (scale Y 1.12, up 14), an eased-in turn of scale Y to 0.03 over seven frames while scale X grows to 1.08 and the bone rises to 70, then scale X to 0 in two frames.",
  duration: 13 / 30,
  build(tl, ctx) {
    const [x, y] = ctx.handoff.translate, s = ctx.handoff.scale;
    tl.bone("logo2")
      .scale([[0, s, s, "outQuad"], [4 / 30, 0.97, 1.12, "inQuad"], [11 / 30, 1.08, 0.03, "outQuad"], [13 / 30, 0, 0.03]])
      .translate([[0, x, y, "outQuad"], [4 / 30, x, y + 14, "inOutQuad"], [11 / 30, x, y + 70, "outQuad"], [13 / 30, x, y + 80]]);
  }
};
