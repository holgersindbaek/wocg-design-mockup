// The sink's curves, shared by the sink exits. At the hand-off the word is still rising from Khang's swell: its top
// holds while its bottom comes up (about 24 px a frame at the centre) and it shrinks a tenth a frame. A sink keeps
// both speeds and lets them run out: the word slows to a soft apex, then sinks away faster and faster, flattening a
// little as if settling into the felt. Position and size follow one cubic each (Hermite: the start speeds are
// Khang's, the end point and end speeds chosen), so nothing changes direction abruptly. Fewer frames bend the same
// curves harder, which is how the quick versions get snappy without a jolt at the start.
const Y0 = 909.68, V0 = -24, S0 = 0.968, DS0 = -0.1;
export const SINKS = {
  //   frames: end centre y, end speed (px a frame), end scale, end scale speed, scale y under scale x at the end, the fade's ease
  14: { y1: 985, v1: 6, s1: 0.12, ds1: -0.012, flatten: 0.3, fade: [0.45, 0.05, 0.7, 0.75] },
  10: { y1: 975, v1: 8, s1: 0.10, ds1: -0.03, flatten: 0.3, fade: [0.4, 0.15, 0.65, 0.8] },
  8: { y1: 965, v1: 9.5, s1: 0.10, ds1: -0.03, flatten: 0.3, fade: [0.37, 0.18, 0.62, 0.83] },
  7: { y1: 960, v1: 10, s1: 0.10, ds1: -0.03, flatten: 0.3, fade: [0.35, 0.2, 0.6, 0.85] },
  6: { y1: 952, v1: 11, s1: 0.09, ds1: -0.04, flatten: 0.3, fade: [0.32, 0.22, 0.58, 0.88] },
  5: { y1: 945, v1: 12, s1: 0.08, ds1: -0.05, flatten: 0.3, fade: [0.3, 0.25, 0.55, 0.9] }
};
// one exit module per frame count: the sink over N frames with the fade from the first frame
export function sinkExit(N, note) {
  const k = Object.assign({ N }, SINKS[N]);
  return {
    id: "sink-" + N,
    name: "Sink, fading, " + N + " frames",
    summary: note + " Gone " + (N / 30).toFixed(2) + " s after the jack.",
    spine: "On logo2: translate and scale keyed per frame along two cubics that start at the speeds the word has when the jack is gone (centre rising 24 px a frame, scale falling 0.1 a frame) and end " + Math.round(k.y1 - 909.68) + " px lower at scale " + k.s1 + " after " + N + " frames, scale y 30% under scale x by the end; the logo slot's alpha 1 at frame 0 to 0 at frame " + N + " on an ease-in.",
    build(tl, ctx) {
      sinkKeys(tl, ctx, k);
      tl.slot("logo").alpha([[0, 1, k.fade], [N / 30, 0]]);
    }
  };
}
function hermite(p0, m0, p1, m1, s) { const s2 = s * s, s3 = s2 * s; return (2 * s3 - 3 * s2 + 1) * p0 + (s3 - 2 * s2 + s) * m0 + (-2 * s3 + 3 * s2) * p1 + (s3 - s2) * m1; }
export function frame(k, i) {
  const s = i / k.N;
  const y = hermite(Y0, V0 * k.N, k.y1, k.v1 * k.N, s), sx = hermite(S0, DS0 * k.N, k.s1, k.ds1 * k.N, s);
  return { centre: { x: 960.5, y }, scale: { x: sx, y: sx * (1 - k.flatten * s * s) } };
}
export function sinkKeys(tl, ctx, k) {
  const keys = []; for (let i = 0; i <= k.N; i++) { const f = frame(k, i); keys.push(ctx.wordKeys(i / 30, f.scale, f.centre)); }
  tl.bone("logo2").scale(keys.map((x) => x.scale)).translate(keys.map((x) => x.translate));
}
