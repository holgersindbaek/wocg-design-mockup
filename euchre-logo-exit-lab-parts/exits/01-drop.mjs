// Drop: a heavy sign whose nail just gave. The word takes the jack's impact with a squash, hops a touch, tips to one
// side and falls out through the bottom of the frame under gravity.
export default {
  id: "drop",
  name: "Drop",
  summary: "The word squashes under the jack's impact, hops a little, tips and falls straight out through the bottom of the tile, tilting as it goes.",
  spine: "All on logo2: a squash-and-hop in scale and translate over the first five frames, then translate Y falls past the frame bottom with an ease-in (gravity) while rotate tips it about 16 degrees on the way; no other bone or slot.",
  duration: 15 / 30,
  build(tl, ctx) {
    const [hx, hy] = ctx.handoff.translate, hs = ctx.handoff.scale;
    const f = (n) => n / 30;
    tl.bone("logo2")
      .translate([
        [0, hx, hy, "outQuad"],
        [f(2), hx, hy - 14, "outCubic"],
        [f(5), hx, hy + 40, "inQuad"],
        [f(15), hx + 40, hy - 1120]
      ])
      .scale([
        [0, hs, hs, "outQuad"],
        [f(2), hs * 1.07, hs * 0.86, "outCubic"],
        [f(5), hs * 0.96, hs * 1.06, "inOutQuad"],
        [f(8), hs, hs, "inQuad"],
        [f(15), hs * 0.97, hs * 1.04]
      ])
      .rotate([
        [0, 0, "outCubic"],
        [f(5), 3, "inQuad"],
        [f(15), -16]
      ]);
  }
};
