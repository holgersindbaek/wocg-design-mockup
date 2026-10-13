// The smooth shrink with the fade from the start: the word begins to go transparent the moment it starts to shrink,
// so it is half gone at half size and gone where Khang's vanishes.
const END = { scale: 0.19, x: 967, y: 952 };
const EASE = [0.35, 0.4, 0.7, 0.9];
export default {
  id: "smooth-fade",
  name: "Smooth, fading from the start",
  summary: "The same straight-line shrink, but the word starts to fade the moment it starts to shrink: half there at half size, gone where Khang's vanishes.",
  spine: "As Smooth, with the logo slot's alpha keyed 1 at frame 0 to 0 at frame 11 on a gentle ease-in, so the fade runs through the whole shrink.",
  build(tl, ctx) {
    const a = ctx.wordKeys(0, ctx.handoff.scale, ctx.handoffCentre), b = ctx.wordKeys(11 / 30, END.scale, END);
    tl.bone("logo2").scale([[...a.scale, EASE], b.scale]).translate([[...a.translate, EASE], b.translate]);
    tl.slot("logo").alpha([[0, 1, [0.4, 0.2, 0.7, 0.8]], [11 / 30, 0]]);
  }
};
