#!/usr/bin/env python3
"""Proof that the avatar border can be carried into the emotion animations.

The question was whether the one-sided inset border of the SVGs can exist in the Lottie files the
table plays. It can, and it needs no baked geometry, so it survives the animation:

  * every emotion file is one shape per layer, the paths in the same 160-unit space as the SVG under
    a 10x layer scale, and the files already use track mattes, which the site's own lottie_light
    build supports (layer masks are also in that build but no shipped file uses them)
  * so for a shape S: copy its layer twice, directly above S. The first copy is the matte (td = 1),
    the second is S stroked at twice the border width with no fill (tt = 1, an alpha matte). The
    matte cuts the outer half of the stroke away, which leaves an inset line.
  * both copies stroke and matte THE SAME path, so when the path is animated (the mouth morphs on a
    win) the border morphs with it. Nothing is baked, nothing drifts.

Measured on ManBusinessman_win.json, 5 shapes bordered: raw 40.5 -> 88.0 KB, but gzipped only
5.5 -> 6.1 KB, since the duplicated geometry compresses away. Over the 473 emotion files that is
about 2.7 -> 3.0 MB on the wire.

Not done here, and what a real pass still needs:
  * the shapes already inside a matte pair (3 of 14 in this file) are skipped; they need the border
    nested inside the pair they belong to
  * which side of an edge owns the line: this proof strokes every shape inside itself. The SVG rule
    decides per edge and cuts the line where the neighbour owns it. In Lottie a cut would be another
    matte, and its geometry WOULD be baked, so the honest version is to give the line to the owner
    shape whole and drop the per-run cuts, which is most of the length and none of the drift.
  * the mouth's heavier stroke is matched here by hand (the white and the red get 35%)

usage: zz-tmp-lottie-borders.py IN.json OUT.json
"""
import json, copy, sys

W, OP, MOUTH_OP = 4.0, 15, 35


def border(d, mouth_fills=("#ffffff",)):
    layers = d["layers"]
    ind = max(L.get("ind", 0) for L in layers)
    out, n = [], 0
    for L in layers:
        if L.get("ty") != 4 or L.get("tt") or L.get("td"):
            out.append(L); continue
        it = L["shapes"][0].get("it", [])
        fl = [x for x in it if x.get("ty") == "fl"]
        sh = [x for x in it if x.get("ty") == "sh"]
        if not fl or not sh:
            out.append(L); continue
        col = fl[0]["c"]["k"]
        hexc = "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in col[:3])
        op = MOUTH_OP if hexc in mouth_fills else OP
        M = copy.deepcopy(L); ind += 1; M["ind"] = ind; M["nm"] = "ab-matte"; M["td"] = 1
        B = copy.deepcopy(L); ind += 1; B["ind"] = ind; B["nm"] = "ab-line"; B["tt"] = 1
        bit = B["shapes"][0]["it"]
        for x in list(bit):
            if x.get("ty") == "fl": bit.remove(x)
        tr = [x for x in bit if x.get("ty") == "tr"][0]
        bit.insert(bit.index(tr), {"ty": "st", "c": {"a": 0, "k": [0, 0, 0, 1]}, "o": {"a": 0, "k": op},
                                   "w": {"a": 0, "k": W * 2}, "lc": 2, "lj": 2, "nm": "ab",
                                   "mn": "ADBE Vector Graphic - Stroke", "hd": False})
        out += [M, B, L]; n += 1
    d["layers"] = out
    return n


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    d = json.load(open(src))
    n = border(d)
    json.dump(d, open(dst, "w"), separators=(",", ":"))
    print("shapes bordered:", n)
