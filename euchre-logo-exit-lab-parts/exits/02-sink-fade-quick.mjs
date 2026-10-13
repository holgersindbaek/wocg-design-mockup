// The same sink in ten frames: the curves bend harder, so the top comes after two and a half frames and the word is
// gone a third of a second after the jack; the fade bites earlier.
import { SINKS, sinkKeys } from "./_sink.mjs";
const K = SINKS.quick;
export default {
  id: "sink-fade-quick",
  name: "Sink, fading, quick (10 frames)",
  summary: "The same move in ten frames: the rise runs out after two and a half frames, the sink is shorter (65 px) and the shrink keeps its arriving pace all the way, with the fade biting earlier. Gone 0.33 s after the jack.",
  spine: "As the fourteen-frame sink with the cubics over ten frames, ending 65 px lower at scale 0.1; the logo slot's alpha 1 to 0 over the ten frames on an ease-in.",
  build(tl, ctx) {
    sinkKeys(tl, ctx, K);
    tl.slot("logo").alpha([[0, 1, [0.4, 0.15, 0.65, 0.8]], [K.N / 30, 0]]);
  }
};
