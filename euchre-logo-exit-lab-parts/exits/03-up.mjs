// Up and away: the word never turns. It keeps shrinking towards its own top edge, where the jack's crown went under,
// its centre rising as it goes, slowing as it gets small, and fades out over the last five frames.
const N = 12;
const TOP = 718, Y0 = 909.68, S0 = 0.968, S1 = 0.1;
const EASE = [0.33, 0.52, 0.67, 0.92]; // starts at Khang's speed (a tenth a frame), eases out
export default {
  id: "up",
  name: "Up and away",
  summary: "No turn at all: the word goes on shrinking towards its top edge, where the jack went under, its centre rising all the way and slowing as it gets small, and it fades out over the last five frames.",
  spine: "On logo2: scale 0.968 to 0.1 on one ease-out over twelve frames, translate on the same curve so the word's top edge stays put (the centre rises 190 px); the logo slot's alpha 1 to 0 over the last five frames.",
  build(tl, ctx) {
    const at = (s) => ({ x: 960.5, y: TOP + (Y0 - TOP) * (s / S0) });
    const a = ctx.wordKeys(0, S0, at(S0)), b = ctx.wordKeys(N / 30, S1, at(S1));
    tl.bone("logo2").scale([[...a.scale, EASE], b.scale]).translate([[...a.translate, EASE], b.translate]);
    tl.slot("logo").alpha([[0, 1], [7 / 30, 1, "inQuad"], [N / 30, 0]]);
  }
};
