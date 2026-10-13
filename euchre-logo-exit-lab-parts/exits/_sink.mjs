// The sink, shared by 01 and 02. At the hand-off the word is still rising from Khang's swell: its top holds while its
// bottom comes up (about 24 px a frame at the centre) and it shrinks a tenth a frame. This exit keeps both speeds and
// lets them run out: the word slows to a soft apex about 40 px up after three frames, then sinks away faster and
// faster, flattening a little as if settling into the felt, 115 px down by the end. Position and size follow one
// cubic each (Hermite: the start speeds are Khang's, the end speeds chosen), so nothing changes direction abruptly.
export const N = 14;
const Y0 = 909.68, V0 = -24, Y1 = 985, V1 = 6;        // the word's centre in scene px: start, start speed, end, end speed (px per frame)
const S0 = 0.968, DS0 = -0.1, S1 = 0.12, DS1 = -0.012; // its scale: the same four numbers
const FLATTEN = 0.3;                                   // scale y ends this much under scale x
function hermite(p0, m0, p1, m1, s) { const s2 = s * s, s3 = s2 * s; return (2 * s3 - 3 * s2 + 1) * p0 + (s3 - 2 * s2 + s) * m0 + (-2 * s3 + 3 * s2) * p1 + (s3 - s2) * m1; }
export function frame(i) {
  const s = i / N;
  const y = hermite(Y0, V0 * N, Y1, V1 * N, s), sx = hermite(S0, DS0 * N, S1, DS1 * N, s);
  return { centre: { x: 960.5, y }, scale: { x: sx, y: sx * (1 - FLATTEN * s * s) } };
}
export function sinkKeys(tl, ctx) {
  const keys = []; for (let i = 0; i <= N; i++) { const f = frame(i); keys.push(ctx.wordKeys(i / 30, f.scale, f.centre)); }
  tl.bone("logo2").scale(keys.map((k) => k.scale)).translate(keys.map((k) => k.translate));
}
