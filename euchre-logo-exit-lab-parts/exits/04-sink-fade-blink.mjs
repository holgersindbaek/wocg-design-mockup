// The same sink in five frames: the rise runs out inside the first frame, the word collapses and sinks 35 px while
// the fade takes most of it, gone a sixth of a second after the jack.
import { SINKS, sinkKeys } from "./_sink.mjs";
const K = SINKS.blink;
export default {
  id: "sink-fade-blink",
  name: "Sink, fading, blink (5 frames)",
  summary: "The same move in five frames: the rise runs out inside the first frame, the word collapses and sinks 35 px while the fade takes most of it. Gone 0.17 s after the jack.",
  spine: "As the fourteen-frame sink with the cubics over five frames, ending 35 px lower at scale 0.08; the logo slot's alpha 1 to 0 over the five frames, nearly linear.",
  build(tl, ctx) {
    sinkKeys(tl, ctx, K);
    tl.slot("logo").alpha([[0, 1, [0.3, 0.25, 0.55, 0.9]], [K.N / 30, 0]]);
  }
};
