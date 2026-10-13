// Light burst: the word swells and heats up, then flashes white-hot and collapses into the light: the shine sprite
// flares up over it and its halo (its clip switched off so it spills onto the felt), the word dissolves under the
// flash, and the glow dies away, shrinking a little as it fades.
// light_1 is a child of logo2, so the word is hidden with the slot's alpha, not a scale to 0 (that would shrink the
// flare with it); the flare's scale keys are its own, with logo2's 1.2 on top.
export default {
  id: "burst",
  name: "Light burst",
  summary: "The word swells and glows hot, then flashes white: an additive flare bursts over it and a halo of felt around it, the word is gone under the flash, and the glow dies away.",
  spine: "logo2 swells to 1.17 and puffs to 1.26; the logo slot tints hot amber on the swell, then its alpha drops to 0 in 2 frames under the flash; logo_mask's clip is keyed off so light_1 can spill; light_1 is moved to the word's centre, turned 81 degrees to lie along the word, scaled from 3 x 2 to 12 x 11 in 2 frames with its alpha to 1, then its alpha fades to 0 over 6 frames while it shrinks to 7 x 8 and warms to amber.",
  duration: 12 / 30,
  light: true,
  build(tl, ctx) {
    const h = ctx.handoff, f = 1 / ctx.fps;
    tl.slot("logo_mask").attachment([[0, null]]);
    tl.bone("logo2").scale([[0, h.scale, h.scale, "outCubic"], [4 * f, 1.13, 1.13], [5 * f, 1.17, 1.17, "out"], [7 * f, 1.26, 1.26]]);
    tl.slot("logo").rgba([[0, "ffffffff", "outQuad"], [4 * f, "ffd27aff"], [5 * f, "fff6e0ff"], [7 * f, "fff6e000"]]);
    tl.bone("light_1")
      .translate([[0, 631, 43]])
      .rotate([[0, 81.28]])
      .scale([[0, 3, 2], [3 * f, 3, 2, "outCubic"], [5 * f, 12, 11, "out"], [6 * f, 13, 12, "outQuad"], [12 * f, 7, 8]]);
    tl.slot("light_1").rgba([[0, "ffffff00"], [3 * f, "ffffff00", "outQuad"], [5 * f, "ffffffff"], [6 * f, "ffffffff", "outQuad"], [9 * f, "fff0c080"], [12 * f, "ffb06000"]]);
  }
};
