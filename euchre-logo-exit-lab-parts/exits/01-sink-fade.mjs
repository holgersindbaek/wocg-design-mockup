// Sink, fading from the start, fourteen frames: the one Holger picked on 13 Oct. The word keeps the rise it already
// has, slows to a soft top about 40 px up, then sinks away faster and faster while it shrinks, flattens a little and
// fades on a gentle ease-in from the first frame.
import { SINKS, sinkKeys } from "./_sink.mjs";
const K = SINKS.easy;
export default {
  id: "sink-fade",
  name: "Sink, fading (14 frames)",
  summary: "The pick so far: the word keeps the rise it already has, slows to a soft top about 40 px up, then sinks away faster and faster while it shrinks, flattens a little and fades from the first frame. Gone 0.47 s after the jack.",
  spine: "On logo2: translate and scale keyed per frame along two cubics that start at the speeds the word has when the jack is gone (centre rising 24 px a frame, scale falling 0.1 a frame) and end 75 px lower at scale 0.12, scale y 30% under scale x by the end; the logo slot's alpha 1 at frame 0 to 0 at frame 14 on an ease-in.",
  build(tl, ctx) {
    sinkKeys(tl, ctx, K);
    tl.slot("logo").alpha([[0, 1, [0.45, 0.05, 0.7, 0.75]], [K.N / 30, 0]]);
  }
};
