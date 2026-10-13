// Sink, fading through: the same curves as Sink, with the fade running from the hand-off to the end.
import { N, sinkKeys } from "./_sink.mjs";
export default {
  id: "sink-fade",
  name: "Sink, fading from the start",
  summary: "The same sink, but the word starts to fade the moment the jack is gone, on a gentle ease-in: still mostly there at the top of its rise, half gone as it sinks, gone at the end.",
  spine: "As Sink, with the logo slot's alpha keyed 1 at frame 0 to 0 at frame 14 on an ease-in curve.",
  build(tl, ctx) {
    sinkKeys(tl, ctx);
    tl.slot("logo").alpha([[0, 1, [0.45, 0.05, 0.7, 0.75]], [N / 30, 0]]);
  }
};
