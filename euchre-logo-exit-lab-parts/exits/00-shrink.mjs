// Khang's own shrink, rebuilt from the hand-off frame as Spine keys: the reference the variations are judged against.
// Measured from the 13 Oct video frame by frame (measure4.mjs), frames 48 to 59: the word's scale, its centre in the
// frame (it rises for two frames, then sinks while it eases out) and its fade over the last four frames.
const FRAMES = [
  // scale, centre x, centre y (scene px), alpha
  [0.969, 960.5, 909.3, 1], [0.868, 961.0, 883.4, 1], [0.764, 962.5, 858.9, 1], [0.659, 963.5, 865.2, 1],
  [0.558, 964.0, 877.3, 1], [0.462, 965.0, 892.2, 1], [0.380, 965.5, 910.0, 1], [0.305, 966.5, 927.3, 1],
  [0.252, 967.0, 941.8, 1], [0.220, 967.0, 948.0, 0.75], [0.200, 967.0, 954.0, 0.25], [0.190, 967.0, 957.0, 0]
];
export default {
  id: "shrink",
  name: "Khang's shrink, rebuilt",
  summary: "The current exit from the hand-off frame on, as measured from his render: the word rises for two frames, then sinks and eases out while it fades. If this tile looks like the one before it, the hand-off is right.",
  spine: "What the active animation already does: scale and translate on logo2, alpha on the logo slot over the last four frames.",
  build(tl, ctx) {
    const keys = FRAMES.map((f, i) => ctx.wordKeys(i / 30, f[0], { x: f[1], y: f[2] }));
    tl.bone("logo2").scale(keys.map((k) => k.scale)).translate(keys.map((k) => k.translate));
    tl.slot("logo").alpha(FRAMES.map((f, i) => [i / 30, f[3]]));
  }
};
