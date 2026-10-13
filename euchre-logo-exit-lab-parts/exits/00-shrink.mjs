// Khang's own shrink, rebuilt from the hand-off frame as Spine keys: a check that the hand-off is seamless.
// Measured from the 13 Oct video, frames 48 to 56: the word's width 1145, 1026, 903, 779, 660, 546, 449, 361, 298 px
// (scale 0.968 down to 0.252), its centre rising towards the jack's vanishing point, the last frames fading.
export default {
  id: "shrink",
  name: "Khang's shrink, rebuilt",
  summary: "The lab's copy of the current exit from the hand-off frame on: if this tile looks like the one before it, the hand-off is right.",
  spine: "What the active animation already does: scale on logo2 towards the vanishing point, alpha on the logo slot.",
  build(tl, ctx) {
    const s = [0.968, 0.868, 0.764, 0.659, 0.558, 0.462, 0.380, 0.305, 0.252, 0.17, 0.08, 0];
    const h = ctx.handoff, p = ctx.pivot;
    // the bone slides towards the pivot as it shrinks, so the word's centre follows Khang's path
    const scale = s.map((k, i) => [i / 30, k, k]);
    const translate = s.map((k, i) => { const f = k / h.scale; return [i / 30, p.x + (h.translate[0] - p.x) * f, p.y + (h.translate[1] - p.y) * f]; });
    tl.bone("logo2").scale(scale).translate(translate);
    tl.slot("logo").alpha([[0, 1], [7 / 30, 1], [11 / 30, 0]]);
  }
};
