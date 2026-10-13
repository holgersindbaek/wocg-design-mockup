// Zoom past: the jack's impact pushes the word back a touch (the wind-up), then it springs at the viewer, growing
// five times in a third of a second and fading as it fills the frame, as if it flew past the camera.
export default {
  id: "zoom",
  name: "Zoom past",
  summary: "The word dips back for a beat, then rushes at the viewer: it swells to five times its size in a third of a second and fades out as it overflows the frame, like a card flying past the camera.",
  spine: "All on logo2 and the logo slot: a scale dip to 0.88 over 3 frames, then scale to 5 with an ease-in over 10 frames and a slight roll, the slot's alpha fading over the last 6 frames.",
  duration: 13 / 30,
  build(tl, ctx) {
    const h = ctx.handoff, f = 1 / ctx.fps;
    tl.bone("logo2")
      .scale([[0, h.scale, h.scale, "out"], [3 * f, 0.88, 0.88, "inQuad"], [13 * f, 5, 5]])
      .rotate([[0, 0, "out"], [3 * f, 2, "inQuad"], [13 * f, -7]]);
    tl.slot("logo").alpha([[0, 1], [7 * f, 1, "in"], [13 * f, 0]]);
  }
};
