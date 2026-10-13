// The same sink in seven frames: the top after a frame and a half, the shrink speeding up past its arriving pace, and
// the word gone under a quarter of a second after the jack.
import { SINKS, sinkKeys } from "./_sink.mjs";
const K = SINKS.snap;
export default {
  id: "sink-fade-snap",
  name: "Sink, fading, snap (7 frames)",
  summary: "The same move in seven frames: the rise runs out after a frame and a half, the word sinks 50 px while the shrink speeds up past its arriving pace, and the fade is quick. Gone 0.23 s after the jack.",
  spine: "As the fourteen-frame sink with the cubics over seven frames, ending 50 px lower at scale 0.1; the logo slot's alpha 1 to 0 over the seven frames on a light ease-in.",
  build(tl, ctx) {
    sinkKeys(tl, ctx, K);
    tl.slot("logo").alpha([[0, 1, [0.35, 0.2, 0.6, 0.85]], [K.N / 30, 0]]);
  }
};
