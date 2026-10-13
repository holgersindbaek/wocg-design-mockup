// Dealt away: the word is a card flicked across the table. A short pull-back, then it shoots off to the right with
// a forward lean and a little lift, and is gone past the frame edge.
export default {
  id: "dealt",
  name: "Dealt away",
  summary: "The word draws back a touch, then shoots off to the right like a dealt card: leaning into the travel, lifting slightly, gone past the edge of the tile.",
  spine: "All on logo2: translate X pulls back 80 px over four frames and then eases in hard to 1900 px right, shear Y leans the word into the travel (back a little on the wind-up, forward about 24 degrees in flight), a small translate Y lift, a 5 degree rotate and a slight horizontal stretch; no other bone or slot.",
  duration: 13 / 30,
  build(tl, ctx) {
    const [hx, hy] = ctx.handoff.translate, hs = ctx.handoff.scale;
    const f = (n) => n / 30;
    tl.bone("logo2")
      .translate([
        [0, hx, hy, "outCubic"],
        [f(4), hx - 80, hy - 8, "inQuart"],
        [f(13), hx + 1900, hy + 60]
      ])
      .shear([
        [0, 0, 0, "outCubic"],
        [f(4), 0, 9, "inQuad"],
        [f(8), 0, -24, "linear"],
        [f(13), 0, -24]
      ])
      .rotate([
        [0, 0, "outCubic"],
        [f(4), 2.5, "inQuad"],
        [f(13), -5]
      ])
      .scale([
        [0, hs, hs, "outCubic"],
        [f(4), hs * 0.97, hs * 1.03, "inQuad"],
        [f(13), hs * 1.12, hs * 0.94]
      ]);
  }
};
