// The colour maths the lab's scripts share: the same functions as ../oklch.js and the page.
function hexToRgb(h) { h = h.replace('#', ''); if (h.length === 3) h = h.replace(/./g, '$&$&'); const n = parseInt(h, 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => v / 255); }
function lin(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
function gam(c) { return c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055; }
function rgbToOklab(r, g, b) {
  const R = lin(r), G = lin(g), B = lin(b);
  const l = 0.4122214708 * R + 0.5363325363 * G + 0.0514459929 * B, m = 0.2119034982 * R + 0.6806995451 * G + 0.1073969566 * B, s = 0.0883024619 * R + 0.2817188376 * G + 0.6299787005 * B;
  const l_ = Math.cbrt(l), m_ = Math.cbrt(m), s_ = Math.cbrt(s);
  return [0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_, 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_, 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_];
}
function oklabToRgb(L, a, b) {
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b, m_ = L - 0.1055613458 * a - 0.0638541728 * b, s_ = L - 0.0894841775 * a - 1.2914855480 * b;
  const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
  return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s].map(gam);
}
function ok(hex) { const p = hexToRgb(hex), o = rgbToOklab(p[0], p[1], p[2]); const C = Math.hypot(o[1], o[2]); let h = Math.atan2(o[2], o[1]) * 180 / Math.PI; if (h < 0) h += 360; return { L: o[0], C, h }; }
function inGamut(rgb) { return rgb.every((v) => v >= -0.0005 && v <= 1.0005); }
function rgbHex(rgb) { return '#' + rgb.map((v) => Math.round(Math.min(1, Math.max(0, v)) * 255).toString(16).padStart(2, '0')).join('').toUpperCase(); }
// oklch.js --to: hold L and h, cut the chroma 3% a step until the colour fits
function to(L, C, h) { const rad = h * Math.PI / 180; let c = C, rgb; for (let i = 0; i < 60; i++) { rgb = oklabToRgb(L, c * Math.cos(rad), c * Math.sin(rad)); if (inGamut(rgb)) break; c *= 0.97; } return rgbHex(rgb); }
function maxC(L, h) { let lo = 0, hi = 0.5; const rad = h * Math.PI / 180; for (let i = 0; i < 40; i++) { const mid = (lo + hi) / 2; if (inGamut(oklabToRgb(L, mid * Math.cos(rad), mid * Math.sin(rad)))) lo = mid; else hi = mid; } return lo; }
// color-mix(in srgb, A pct%, B)
function mix(a, pct, b) { const p = hexToRgb(a), q = hexToRgb(b); return rgbHex(p.map((v, i) => v * pct / 100 + q[i] * (100 - pct) / 100)); }
// the CSS Color 4 gamut mapping the catalog tiles were made with (_fp-catalog.scss)
function css4(L, C, h) {
  const rad = h * Math.PI / 180;
  const rgbOf = (c) => oklabToRgb(L, c * Math.cos(rad), c * Math.sin(rad));
  const clip = (rgb) => rgb.map((v) => Math.min(1, Math.max(0, v)));
  const dist = (rgb, c) => { const o = rgbToOklab(rgb[0], rgb[1], rgb[2]); return Math.hypot(o[0] - L, o[1] - c * Math.cos(rad), o[2] - c * Math.sin(rad)); };
  if (inGamut(rgbOf(C))) return rgbHex(rgbOf(C));
  let lo = 0, hi = C, loIn = true, clipped = clip(rgbOf(C));
  if (dist(clipped, C) < 0.02) return rgbHex(clipped);
  while (hi - lo > 0.0001) {
    const c = (lo + hi) / 2;
    if (loIn && inGamut(rgbOf(c))) { lo = c; continue; }
    clipped = clip(rgbOf(c)); const e = dist(clipped, c);
    if (e < 0.02) { if (0.02 - e < 0.0001) return rgbHex(clipped); loIn = false; lo = c; } else hi = c;
  }
  return rgbHex(clip(rgbOf(lo)));
}
function lumi(hex) { const p = hexToRgb(hex).map(lin); return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]; }
function contrast(a, b) { const x = lumi(a), y = lumi(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
// Law 1: a grey's warm twin keeps its depth at the paper's hue 82; under L .45 a grey is an ink, kept neutral
function warmTwin(hex) { const o = ok(hex); if (o.L < 0.45) return to(o.L, 0, 82); return to(o.L, o.L > 0.75 ? 0.005 + 0.10 * (1 - o.L) : 0.02, 82); }
// the plates' deep ink: 89% of what the hue can hold at L .415
function deepInk(h) { return to(0.415, maxC(0.415, h) * 0.89, h); }
module.exports = { hexToRgb, ok, to, maxC, mix, css4, lumi, contrast, warmTwin, deepInk };
