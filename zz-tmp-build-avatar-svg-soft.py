#!/usr/bin/env python3
"""Rounds two to four of the capped man's SVG edits (the softer set), and the Lottie stroke script.
Runs after zz-tmp-build-avatar-svg.py (whose parsing and helpers it reuses).
  s01-s08: insets at 1 unit / black 15% / contact bands (an inset kept only over the neighbour shapes) / a blurred shade / a hairline
  s09-s10: cast shadows (the neighbour's edge stroked and clipped to the shape it sits on)
  s11: the faint inset plus the collar
  s12-s13: a plain centred stroke attribute on the shapes (the form the Lottie files can carry)
  lottie_strokes(): the same rule on a Lottie JSON: a stroke item per shape group whose fill is one of the parts, tiny shapes skipped
"""
import re, json, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "zz-tmp-build-avatar-svg.py")).read().split("CAPB = ")[0])

def band(el, n, color, w, clip_els, blur=None, opacity=None, over=False):
    plain = strip(el)
    clip2 = '<clipPath id="ic%d">' % n + "".join(strip(c) for c in clip_els) + '</clipPath>'
    extra = (' opacity="%s"' % opacity if opacity else '') + (' filter="url(#soft%d)"' % n if blur else '')
    flt = ('<filter id="soft%d" x="-10%%" y="-10%%" width="120%%" height="120%%"><feGaussianBlur stdDeviation="%s"/></filter>' % (n, blur)) if blur else ''
    stroke = plain[:-2] + ' fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"%s/>' % (color, w * 2, extra)
    if over: return clip2 + flt + '<g clip-path="url(#ic%d)">' % n + stroke + '</g>'
    clip = '<clipPath id="ib%d">' % n + plain + '</clipPath>'
    return el + clip + clip2 + flt + '<g clip-path="url(#ic%d)"><g clip-path="url(#ib%d)">' % (n, n) + stroke + '</g></g>'

def attr_stroke(el, w, op):
    return el[:-2] + ' stroke="#000" stroke-opacity="%s" stroke-width="%s" stroke-linejoin="round"/>' % (op, w)

def write(name, parts, beard_fill=None):
    nb = body
    for i, el in enumerate(ELS): nb = nb.replace(el, "\x00%d\x00" % i, 1)
    for i, p in enumerate(parts): nb = nb.replace("\x00%d\x00" % i, p, 1)
    h = head.replace(".cls-9{fill:#d89c93;}", ".cls-9{fill:%s;}" % beard_fill) if beard_fill else head
    fn = os.path.join(OUT, "ManCowboy-%s.svg" % name); open(fn, "w").write(h + nb); return fn

FACE, NECK, FUR0 = 4, 2, 0
CAP = [18, 25, 26, 3]; BEARD = [16]; SHIRT = [27, 28, 32]; FUR = [0, 29, 30]
BEARD_D = "#cf8f85"

def soft(name, specs, casts=(), beard_fill=None):
    """specs: (index, color, width, clip_indices|None, blur, opacity); casts: (edge_index, onto_index, color, width, blur, opacity)"""
    parts = list(ELS)
    for (i, col, w, clips, blur, op) in specs:
        parts[i] = band(ELS[i], i, col, w, [ELS[c] for c in (clips or [i])], blur, op)
    for k, (ei, oi, col, w, blur, op) in enumerate(casts):
        parts[oi] = parts[oi] + band(ELS[ei], 100 + k, col, w, [ELS[oi]], blur, op, over=True)
    return write(name, parts, beard_fill)

def own(idxs, k, w, clips=None, blur=None, op=None): return [(i, darken(fill_of(ELS[i]), k), w, clips, blur, op) for i in idxs]
def black(idxs, w, clips=None, blur=None, op=None): return [(i, "#000000", w, clips, blur, op) for i in idxs]

if __name__ == "__main__":
    soft("s01-hint", own(CAP, .15, 1) + own(BEARD, .15, 1) + own(SHIRT, .15, 1))
    soft("s02-faint", black(CAP, 2, None, None, .15) + black(BEARD, 2, None, None, .15) + black(SHIRT, 2, None, None, .15))
    soft("s03-contact", own(CAP, .22, 2, [FACE]) + own(BEARD, .22, 2) + own(SHIRT, .22, 2, [NECK, FUR0]))
    soft("s04-shade", black(CAP, 3, [FACE], 1.2, .20) + black(BEARD, 3, None, 1.2, .16) + black(SHIRT, 3, [NECK, FUR0], 1.2, .20))
    soft("s05-hair", own(CAP, .32, 1, [FACE]) + own(BEARD, .32, 1) + own(SHIRT, .32, 1, [NECK, FUR0]))
    soft("s06-contact-beard", own(CAP, .22, 2, [FACE]) + own(BEARD, .22, 2) + own(SHIRT, .22, 2, [NECK, FUR0]), beard_fill=BEARD_D)
    soft("s07-shade-beard", black(CAP, 3, [FACE], 1.2, .20) + black(BEARD, 3, None, 1.2, .16) + black(SHIRT, 3, [NECK, FUR0], 1.2, .20), beard_fill=BEARD_D)
    soft("s08-both", own(CAP, .18, 1, [FACE]) + own(BEARD, .18, 1) + own(SHIRT, .18, 1, [NECK, FUR0]), beard_fill=BEARD_D)
    casts = [(i, FACE, "#000000", 3, 1.2, .20) for i in CAP] + [(i, NECK, "#000000", 3, 1.2, .22) for i in SHIRT]
    soft("s09-cast", black(BEARD, 3, None, 1.2, .14), casts=casts)
    soft("s10-cast-beard", black(BEARD, 3, None, 1.2, .14), casts=casts, beard_fill=BEARD_D)
    soft("s11-faint-fur", black(CAP + BEARD + SHIRT + FUR, 2, None, None, .15))
    parts = list(ELS)
    for i in CAP + BEARD + SHIRT + FUR: parts[i] = attr_stroke(ELS[i], 2, .15)
    write("s12-centred", parts); write("s13-centred-beard", parts, BEARD_D)
    print("softer set written")

# ---------- the Lottie side: the same rule on the emotion files ----------
PARTS = {"#db1b1b", "#c11a1a", "#ea3636", "#911616", "#d89c93", "#32314b", "#3e436d", "#e88032"}   # cap, beard, shirt, collar
def hexc(c): return "#%02x%02x%02x" % tuple(round(v * 255) for v in c[:3])
def lottie_strokes(J, width=2, opacity=15, min_size=10, parts=PARTS):
    """adds a stroke item before the fill of every shape group whose fill is one of the parts; skips groups under min_size units; returns the count"""
    def bbox(items):
        xs = []; ys = []
        for it in items:
            if it.get("ty") == "sh":
                k = it["ks"]["k"]; shapes = [k] if isinstance(k, dict) else [f["s"][0] for f in k if "s" in f]
                for sh in shapes:
                    for p in sh["v"]: xs.append(p[0]); ys.append(p[1])
        return (max(xs) - min(xs), max(ys) - min(ys)) if xs else (0, 0)
    n = 0
    def walk(items):
        nonlocal n
        i = 0
        while i < len(items):
            it = items[i]
            if it.get("ty") == "gr": walk(it.get("it", []))
            elif it.get("ty") == "fl" and not it["c"].get("a") and hexc(it["c"]["k"]) in parts and max(bbox(items)) >= min_size:
                items.insert(i, {"ty": "st", "c": {"a": 0, "k": [0, 0, 0, 1]}, "o": {"a": 0, "k": opacity}, "w": {"a": 0, "k": width}, "lc": 2, "lj": 2, "ml": 4, "bm": 0, "nm": "border", "hd": False})
                i += 1; n += 1
            i += 1
    for L in J["layers"]: walk(L.get("shapes", []))
    return n
