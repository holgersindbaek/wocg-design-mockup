// Sink: the word's rise runs out into a soft apex, then it sinks away, flattening a touch, and fades over the last six
// frames. The curves are in _sink.mjs.
import { N, sinkKeys } from "./_sink.mjs";
export default {
  id: "sink",
  name: "Sink",
  summary: "The word keeps the rise it already has, slows to a soft top about 40 px up, then sinks away faster and faster while it shrinks and flattens a little, and fades over the last six frames. One curve for the move, one for the size, so there is no turn to feel.",
  spine: "On logo2: translate and scale keyed per frame along two cubics that start at the speeds the word has when the jack is gone (centre rising 24 px a frame, scale falling 0.1 a frame) and end 115 px lower at scale 0.12, scale y 30% under scale x by the end; the logo slot's alpha 1 to 0 over the last six frames.",
  build(tl, ctx) {
    sinkKeys(tl, ctx);
    tl.slot("logo").alpha([[0, 1], [8 / 30, 1, "inQuad"], [N / 30, 0]]);
  }
};
