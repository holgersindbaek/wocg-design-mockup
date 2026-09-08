#!/usr/bin/env python3
"""Carry the v9 avatar border into the 473 emotion Lottie files.

The still avatars carry a faint border drawn into the SVG (v9, `zz-tmp-build-avatar-borders.py`).
The emotion animations did not, so a win/think/lose swapped the border off for two seconds. This
pass puts the same line into the animations, with no baked geometry, so it survives the movement.

    usage: zz-tmp-build-avatar-lottie.py [--out=DIR] [--js] [--jobs=N] [--limit=N] [names...]

    --out=DIR   folder under game-assets/ to write into (default avatars-lottie-v9)
    --js        also write the lab copies, game-assets/<out>/js/<Name>_<emo>.js, which assign
                window.AB_LOTTIE["<Name>_<emo>"]; a lab opened from file:// cannot fetch JSON
    --jobs=N    worker processes (default 8)
    names       avatar names (ManBusinessman) or file stems (ManBusinessman_win); default all

THE MECHANISM
-------------
A track matte or a layer mask can clip a stroke to the shape it belongs to, so a stroke of twice
the border width leaves exactly the inner half: an inset line. Both the clip and the stroke carry
THE SAME path object, so an animated path morphs the border with it. Nothing is baked and nothing
drifts. The only constant this pass computes is the group transform, and no group transform in the
set is animated (0 of 19,536), so that is exact rather than approximate.

Per bordered unit, one of two forms:

  self-mask   one layer: the layer cloned, pruned to that unit, fills removed, a stroke inserted
              where the fill was, and one additive mask carrying the unit's own path in layer
              space. Used when the unit has a single outer path that can be written as a mask.
              A layer that was already matted keeps its tt/tp, so the line is clipped twice.
  matte pair  two layers: an `ab-matte` clone (td=1, fill kept, opacity forced to 100) and an
              `ab-line` clone (tt=1, tp=the matte) . Used when the unit's shape cannot be written
              as a mask (several outer paths, an animated ellipse, an animated group transform).

Never more than ONE additive mask on a layer: lottie renders several as children of one clipPath
and Chrome does not reliably union those (measured 6,741 px kept where the union is 9,459).

WIDTHS
------
The v9 SVGs stroke `.abl` at 4 units and mask away the outer half, so the line the eye sees is
**2 units** in the 160-unit box. A Lottie comp here is 1600 = 160 x 10, so the stroke has to
render 40 comp units wide, and a stroke's width is measured in the space of the `it` array it sits
in. Hence w = 40 / S, with S the scale from that space to the comp. S is 10 for 80% of the groups
but runs from 1 to 12, so a fixed 4 would be ten times wrong on the files drawn at 1600 units.

WHICH UNITS GET A LINE
----------------------
Every Lottie unit is matched to the SVG part the border generator decided about, on geometry:
the unit's path through its transform chain, divided by 10, against the SVG element's bounding box
and area, at the best of 13 sampled frames, one-to-one by Hungarian assignment with the paint as a
loose gate. That reaches 78% of units and is right on 99.5% of them (735 pairs rendered and
compared). A unit with no part falls back to the generator's own gate read off the unit, which
agrees with it on 96% of matched pairs. Fill hex alone would decide only 13%.

The line is always drawn INSIDE the unit. v9 also draws an outer band onto the piece below, where
the neighbour owns the edge but this piece covers it; that cut cannot be carried into Lottie
without baking geometry, so those 16% of parts get their line one border-width in from where the
still puts it. That is the trade the handoff asks for ("give the line to the shape that owns most
of that edge, whole").

The mouth is stroked at 35% instead of 15%, read from the built v9 SVG (`class="abl abm"`, or
`style="stroke-opacity:.35"` where svgo inlined the rule).

Skipped, as the SVG rule skips them: no fill, translucent, line art (a near-black fill that is
small), under 10 units across, a matte source (it is never drawn; its visible twin gets the line),
and any layer carrying a shape modifier (tm/rd/pb/rp/zz) whose drawn geometry is not the raw path.
"""
import os, re, sys, json, copy, math, subprocess, tempfile, collections
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image
from skimage import measure as skm
try:
    from scipy.optimize import linear_sum_assignment
    HUNGARIAN = True
except Exception:
    HUNGARIAN = False

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.normpath(os.path.join(HERE, "..", "..", "Programming", "wocg"))
LOT = os.path.join(APP, "worldofcardgames", "static", "pieces", "avatar", "classic")
CHROME = "/opt/homebrew/bin/chromium"
LOOK_TMP = "/tmp/ablottie/look/"
LOOK = os.environ.get("AB_LOOK", "2")            # "1" decide everything from the animation's own
                                                 # render, "2" only the shapes the still cannot reach
SVG = os.path.join(HERE, "game-assets", "avatars")
BOR = os.path.join(HERE, "game-assets", "avatars-bordered-v9")
OUT = os.path.join(HERE, "game-assets", "avatars-lottie-v9")

W_UNITS = 4.0          # the v9 stroke width in the 160-unit box; the clip keeps the inner 2
DO_BAND = os.environ.get("AB_BAND", "1") == "1"   # carry v9's outer band onto the piece below
BAND_RATIO = float(os.environ.get("AB_BAND_RATIO", "2"))  # only where the band is the shape's main line
DO_CUT = os.environ.get("AB_CUT", "0") == "1"     # cut the line where a neighbour owns it
DO_TWIN = os.environ.get("AB_TWIN", "0") == "1"   # let an unmatched shape copy a matched twin
OP, MOUTH_OP = 15, 35  # black, per cent
COMP_PER_UNIT = 10.0   # a 1600-unit comp over the 160-unit drawing
FRAMES = 13            # frames sampled for the match and for the scale
DE = 12.0              # the paint gate, CIE76; lets the two regraded files through
CAP = 6.0              # a unit and a part further apart than this are not a pair
INTRINSIC_MIN_DIM = 30 # a shape with no part is only stroked when it is this big
GEOM = ("sh", "el", "rc", "sr")
MODIFIERS = ("tm", "rd", "pb", "rp", "zz")      # change the drawn geometry; we cannot clip to it
IGNORED = ("mm",)                               # lottie_light has no merge-paths modifier at all
STYLES = ("fl", "st", "gf", "gs", "no")


# ---------------------------------------------------------------- affine, 2x3 as (m00,m01,m02,m10,m11,m12)

IDM = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)

def mmul(A, B):
    a00, a01, a02, a10, a11, a12 = A
    b00, b01, b02, b10, b11, b12 = B
    return (a00*b00 + a01*b10, a00*b01 + a01*b11, a00*b02 + a01*b12 + a02,
            a10*b00 + a11*b10, a10*b01 + a11*b11, a10*b02 + a11*b12 + a12)

def mapply(M, pts):
    m00, m01, m02, m10, m11, m12 = M
    return [(m00*x + m01*y + m02, m10*x + m11*y + m12) for x, y in pts]

def mpoint(M, p):
    m00, m01, m02, m10, m11, m12 = M
    return [m00*p[0] + m01*p[1] + m02, m10*p[0] + m11*p[1] + m12]

def mvec(M, p):
    """a direction, so the translation is left out: bezier handles are relative to their vertex"""
    return [M[0]*p[0] + M[1]*p[1], M[3]*p[0] + M[4]*p[1]]

def mscale(M):
    """the geometric mean of the scales this matrix applies, rotation and skew allowed for"""
    det = M[0]*M[4] - M[1]*M[3]
    return math.sqrt(abs(det))


# ---------------------------------------------------------------- lottie property sampling

def _f(v):
    return float(v[0]) if isinstance(v, list) else float(v)

def _ease(kf, f):
    o, i = kf.get("o"), kf.get("i")
    if not o or not i:
        return f
    try:
        x1, y1 = _f(o["x"]), _f(o["y"]); x2, y2 = _f(i["x"]), _f(i["y"])
    except Exception:
        return f
    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = (lo + hi) / 2
        x = 3*(1-mid)**2*mid*x1 + 3*(1-mid)*mid**2*x2 + mid**3
        if x < f: lo = mid
        else: hi = mid
    t = (lo + hi) / 2
    return 3*(1-t)**2*t*y1 + 3*(1-t)*t**2*y2 + t**3

def _lerp_shape(A, B, f):
    out = {"c": A.get("c", False)}
    for k in ("i", "o", "v"):
        a, b = A.get(k) or [], B.get(k) or []
        if len(a) != len(b): out[k] = a
        else: out[k] = [[a[j][0] + (b[j][0]-a[j][0])*f, a[j][1] + (b[j][1]-a[j][1])*f] for j in range(len(a))]
    return out

def val(prop, t):
    """an animated or static lottie property at frame t"""
    if prop is None: return None
    if not isinstance(prop, dict): return prop
    if not prop.get("a"): return prop.get("k")
    kfs = prop["k"]
    if not kfs: return None
    if t <= kfs[0].get("t", 0): return kfs[0].get("s")
    for a, b in zip(kfs, kfs[1:]):
        ta, tb = a.get("t", 0), b.get("t", 0)
        if ta <= t <= tb:
            sa = a.get("s"); sb = a.get("e", b.get("s"))
            if sa is None: return sb
            if sb is None or tb == ta: return sa
            f = _ease(a, (t - ta) / (tb - ta))
            if sa and isinstance(sa[0], dict):
                return [_lerp_shape(sa[0], sb[0] if sb and isinstance(sb[0], dict) else sa[0], f)]
            try:
                return [sa[i] + (sb[i] - sa[i]) * f for i in range(min(len(sa), len(sb)))]
            except TypeError:
                return sa
    last = kfs[-1]
    return last.get("s", last.get("e"))

def is_animated(prop):
    return isinstance(prop, dict) and bool(prop.get("a"))

def trmat(p, a, s, r, sk=0.0, sa=0.0):
    """translate(p) . rotate(r) . skew . scale(s) . translate(-a), as lottie composes them.

    No transform in the 473 files carries a skew, so it is refused rather than approximated."""
    if sk: raise Unsupported("skew")
    th = math.radians(r or 0)
    cos, sin = math.cos(th), math.sin(th)
    sx = (s[0] if s else 100) / 100.0
    sy = (s[1] if s and len(s) > 1 else (s[0] if s else 100)) / 100.0
    m00, m01 = cos*sx, -sin*sy
    m10, m11 = sin*sx,  cos*sy
    ax, ay = (a[0], a[1]) if a else (0, 0)
    px, py = (p[0], p[1]) if p else (0, 0)
    return (m00, m01, px - (m00*ax + m01*ay), m10, m11, py - (m10*ax + m11*ay))

def group_matrix(tr, t):
    if tr is None: return IDM
    return trmat(val(tr.get("p"), t), val(tr.get("a"), t), val(tr.get("s"), t),
                 val(tr.get("r"), t) or 0, val(tr.get("sk"), t) or 0, val(tr.get("sa"), t) or 0)

def layer_matrix(L, t):
    ks = L.get("ks", {})
    if "px" in ks or "py" in ks:
        px, py = val(ks.get("px"), t), val(ks.get("py"), t)
        p = [px[0] if isinstance(px, list) else px, py[0] if isinstance(py, list) else py]
    else:
        p = val(ks.get("p"), t) or [0, 0]
        if isinstance(p, dict): p = [0, 0]
    a = val(ks.get("a"), t) or [0, 0]
    s = val(ks.get("s"), t) or [100, 100]
    r = val(ks.get("r"), t) or 0
    if isinstance(r, list): r = r[0]
    return trmat(p, a, s, r)

def chain_matrix(L, t, by_ind):
    M = layer_matrix(L, t)
    par, seen = L.get("parent"), 0
    while par is not None and seen < 20:
        P = by_ind.get(par)
        if P is None: break
        M = mmul(layer_matrix(P, t), M)
        par = P.get("parent"); seen += 1
    return M


# ---------------------------------------------------------------- geometry sampling

def _bez(p0, p1, p2, p3, n=8):
    t = np.linspace(0, 1, n + 1)[1:]
    mt = 1 - t
    x = mt**3*p0[0] + 3*mt**2*t*p1[0] + 3*mt*t**2*p2[0] + t**3*p3[0]
    y = mt**3*p0[1] + 3*mt**2*t*p1[1] + 3*mt*t**2*p2[1] + t**3*p3[1]
    return list(zip(x, y))

KAPPA = 0.5522847498307936

def el_path(el, t):
    p = val(el.get("p"), t) or [0, 0]; s = val(el.get("s"), t) or [0, 0]
    rx, ry = s[0]/2.0, s[1]/2.0; cx, cy = p[0], p[1]
    return {"i": [[-rx*KAPPA, 0], [0, -ry*KAPPA], [rx*KAPPA, 0], [0, ry*KAPPA]],
            "o": [[rx*KAPPA, 0], [0, ry*KAPPA], [-rx*KAPPA, 0], [0, -ry*KAPPA]],
            "v": [[cx, cy-ry], [cx+rx, cy], [cx, cy+ry], [cx-rx, cy]], "c": True}

def rc_path(rc, t):
    p = val(rc.get("p"), t) or [0, 0]; s = val(rc.get("s"), t) or [0, 0]
    r = val(rc.get("r"), t) or 0
    hw, hh = s[0]/2.0, s[1]/2.0; cx, cy = p[0], p[1]
    r = min(r, hw, hh)
    if r <= 0:
        v = [[cx+hw, cy-hh], [cx+hw, cy+hh], [cx-hw, cy+hh], [cx-hw, cy-hh]]
        return {"i": [[0, 0]]*4, "o": [[0, 0]]*4, "v": v, "c": True}
    k = r*KAPPA
    v, i, o = [], [], []
    for px, py, ix, iy, ox, oy in [
            (cx+hw,   cy-hh+r, 0, -k, 0, 0), (cx+hw,   cy+hh-r, 0, 0, 0, k),
            (cx+hw-r, cy+hh,   k,  0, 0, 0), (cx-hw+r, cy+hh,   0, 0, -k, 0),
            (cx-hw,   cy+hh-r, 0,  k, 0, 0), (cx-hw,   cy-hh+r, 0, 0, 0, -k),
            (cx-hw+r, cy-hh,  -k,  0, 0, 0), (cx+hw-r, cy-hh,   0, 0, k, 0)]:
        v.append([px, py]); i.append([ix, iy]); o.append([ox, oy])
    return {"i": i, "o": o, "v": v, "c": True}

def sh_path(it, t):
    k = val(it.get("ks"), t)
    if isinstance(k, list) and k and isinstance(k[0], dict): k = k[0]
    return k if isinstance(k, dict) else None

def item_path(it, t):
    ty = it.get("ty")
    if ty == "sh": return sh_path(it, t)
    if ty == "el": return el_path(it, t)
    if ty == "rc": return rc_path(it, t)
    return None

def path_points(pth, n=8):
    if not pth: return []
    v = pth.get("v") or []
    if not v: return []
    io = pth.get("i") or [[0, 0]]*len(v)
    oo = pth.get("o") or [[0, 0]]*len(v)
    closed = pth.get("c", False)
    pts = [tuple(v[0])]
    for j in (range(len(v)) if closed else range(len(v)-1)):
        j2 = (j+1) % len(v)
        pts += _bez((v[j][0], v[j][1]), (v[j][0]+oo[j][0], v[j][1]+oo[j][1]),
                    (v[j2][0]+io[j2][0], v[j2][1]+io[j2][1]), (v[j2][0], v[j2][1]), n)
    return pts

def sr_points(it, t, n=8):
    p = val(it.get("p"), t) or [0, 0]
    orr = val(it.get("or"), t) or 0; ir = val(it.get("ir"), t) or 0
    pt = int(val(it.get("pt"), t) or 5); sy = it.get("sy", 1)
    rot = math.radians(val(it.get("r"), t) or 0)
    m = pt*2 if sy == 1 else pt
    return [(p[0]+ (orr if (j % 2 == 0 or sy != 1) else ir)*math.cos(rot - math.pi/2 + j*2*math.pi/m),
             p[1]+ (orr if (j % 2 == 0 or sy != 1) else ir)*math.sin(rot - math.pi/2 + j*2*math.pi/m))
            for j in range(m+1)]

def geom_points(it, t, n=8):
    if it.get("ty") == "sr": return sr_points(it, t, n)
    return path_points(item_path(it, t), n)

def polyarea(pts):
    if len(pts) < 3: return 0.0
    x = np.array([p[0] for p in pts]); y = np.array([p[1] for p in pts])
    return 0.5*float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

def bbox_of(subs):
    allp = [q for sp in subs for q in sp]
    if not allp: return None, 0.0
    xs = [q[0] for q in allp]; ys = [q[1] for q in allp]
    return (min(xs), min(ys), max(xs), max(ys)), sum(abs(polyarea(sp)) for sp in subs)


# ---------------------------------------------------------------- the Lottie side: units

def hexof(style, t):
    if style is None: return None
    c = val(style.get("c"), t)
    if not c: return None
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v*255)))) for v in c[:3])

def lottie_units(doc, t=0.0, n=8):
    """Every paintable unit: the level of a shape tree that holds geometry and a style.

    The uid is "L<layer index>/<group index>[/...]" and is what matchparts.py used, so the
    measured hit rates apply. A level that holds a style but whose geometry sits in nested groups
    (the merge-paths family) is emitted too, with `deep` set; the matcher never saw those, so they
    always fall back to the intrinsic gate."""
    by_ind = {L.get("ind"): L for L in doc["layers"]}
    out = []
    for li, L in enumerate(doc["layers"]):
        if L.get("ty") != 4: continue
        LM = chain_matrix(L, t, by_ind)
        lo = val(L.get("ks", {}).get("o"), t)
        if isinstance(lo, list): lo = lo[0]

        def walk(items, M, gpath, gnames, gop):
            geoms = [x for x in items if x.get("ty") in GEOM]
            fills = [x for x in items if x.get("ty") == "fl"]
            strokes = [x for x in items if x.get("ty") == "st"]
            grs = [x for x in items if x.get("ty") == "gr"]
            trs = [x for x in items if x.get("ty") == "tr"]
            GM, go = M, 100
            if trs:
                GM = mmul(M, group_matrix(trs[-1], t))
                go = val(trs[-1].get("o"), t)
                if isinstance(go, list): go = go[0]
            op = gop * ((go if go is not None else 100) / 100.0)
            deep = []
            if fills and not geoms:
                deep = deep_geoms(items, GM, t)
            if (geoms and (fills or strokes)) or deep:
                if geoms:
                    subs, gitems = [], []
                    for g in geoms:
                        subs.append(mapply(GM, geom_points(g, t, n)))
                        gitems.append(g)
                else:
                    subs = [d[1] for d in deep]; gitems = [d[0] for d in deep]
                subs = [[(x/COMP_PER_UNIT, y/COMP_PER_UNIT) for x, y in sp] for sp in subs]
                bbox, area = bbox_of(subs)
                f = fills[0] if fills else None
                s0 = strokes[0] if strokes else None
                fo = val(f.get("o"), t) if f else None
                if isinstance(fo, list): fo = fo[0]
                out.append({
                    "uid": "L%d%s" % (li, "".join("/%d" % g for g in gpath)),
                    "layer_idx": li, "layer_ind": L.get("ind"), "layer_nm": L.get("nm"),
                    "gpath": tuple(gpath), "gname": gnames[-1] if gnames else None,
                    "tt": L.get("tt"), "td": L.get("td"), "tp": L.get("tp"),
                    "fill": hexof(f, t), "stroke": hexof(s0, t),
                    "fill_opacity": fo, "layer_opacity": lo, "group_opacity": op,
                    "ngeom": len(gitems), "deep": bool(deep),
                    "subpaths": subs, "bbox": bbox, "area": area,
                })
            for gi, g in enumerate(grs):
                walk(g.get("it", []), GM, gpath + [gi], gnames + [g.get("nm")], op)

        def deep_geoms(items, M, tt):
            """geometry that a style at this level paints but that lives in nested groups"""
            got = []
            for x in items:
                if x.get("ty") != "gr": continue
                sub = x.get("it", [])
                if any(y.get("ty") in STYLES for y in sub): continue
                trs = [y for y in sub if y.get("ty") == "tr"]
                GM = mmul(M, group_matrix(trs[-1], tt)) if trs else M
                for y in sub:
                    if y.get("ty") in GEOM: got.append((y, mapply(GM, geom_points(y, tt, n))))
                    elif y.get("ty") == "gr": got += deep_geoms([y], GM, tt)
            return got

        top = L.get("shapes", [])
        loose = [x for x in top if x.get("ty") != "gr"]
        if loose and any(x.get("ty") in GEOM for x in loose):
            walk(loose, LM, [-1], [L.get("nm")], 1.0)
        for gi, g in enumerate([x for x in top if x.get("ty") == "gr"]):
            walk(g.get("it", []), LM, [gi], [g.get("nm")], 1.0)
    return out


# ---------------------------------------------------------------- the SVG side

EL = re.compile(r'<(?:path|ellipse|rect|circle|polygon|polyline)\b[^>]*?/>', re.S)
TAG = re.compile(r'<(/?)([a-zA-Z][\w:-]*)((?:"[^"]*"|[^>])*?)(/?)>', re.S)
NUM = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')
SVG_TF = re.compile(r'(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)')

def split_body(s):
    if '<g id="Avatars">' in s: cut = s.index('<g id="Avatars">')
    else:
        m = re.search(r'</defs>', s)
        cut = m.end() if m else s.index('>', s.index('<svg')) + 1
    return s[:cut], s[cut:]

def styles_of(s):
    out = {}
    for css in re.findall(r'<style[^>]*>(.*?)</style>', s, re.S):
        for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', css):
            body = re.sub(r'\s+', '', body)
            for one in sel.split(","):
                m = re.fullmatch(r'\.([\w-]+)', one.strip())
                if m: out[m.group(1)] = (out.get(m.group(1), "") + ";" + body).strip(";")
    return out

def elem_props(e, styles):
    c = re.search(r'class="([^"]+)"', e)
    st = styles.get(c.group(1), "") if c else ""
    d = dict(kv.split(":", 1) for kv in st.split(";") if ":" in kv)
    for k in ("fill", "stroke", "opacity", "fill-opacity"):
        m = re.search(r'\s%s="([^"]*)"' % k, e)
        if m: d[k] = m.group(1)
    fill = d.get("fill", "#000")
    fill = None if fill == "none" or fill.startswith("url") else fill
    stroke = d.get("stroke")
    stroke = None if not stroke or stroke == "none" else stroke
    return {"fill": fill, "stroke": stroke, "opacity": ("opacity" in d or "fill-opacity" in d)}

NAMED = {"snow": "#fffafa", "white": "#ffffff", "black": "#000000", "red": "#ff0000"}

def norm_hex(h):
    if not h: return None
    h = h.strip().lower()
    if h.startswith("#"):
        h = h[1:]
        if len(h) == 3: h = "".join(c*2 for c in h)
        if len(h) == 8: h = h[:6]
        return "#" + h if len(h) == 6 else None
    m = re.match(r'rgb\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)', h)
    if m: return "#%02x%02x%02x" % tuple(int(round(float(v))) for v in m.groups())
    return NAMED.get(h)

def svg_matrix(text):
    M = IDM
    for fn, args in SVG_TF.findall(text or ""):
        v = [float(x) for x in NUM.findall(args)]
        if fn == "matrix" and len(v) == 6: T = (v[0], v[2], v[4], v[1], v[3], v[5])
        elif fn == "translate": T = (1, 0, v[0] if v else 0, 0, 1, v[1] if len(v) > 1 else 0)
        elif fn == "scale":
            sx = v[0] if v else 1; sy = v[1] if len(v) > 1 else sx
            T = (sx, 0, 0, 0, sy, 0)
        elif fn == "rotate":
            th = math.radians(v[0] if v else 0); c, s2 = math.cos(th), math.sin(th)
            T = (c, -s2, 0, s2, c, 0)
            if len(v) >= 3:
                T = mmul((1, 0, v[1], 0, 1, v[2]), mmul(T, (1, 0, -v[1], 0, 1, -v[2])))
        elif fn == "skewX": T = (1, math.tan(math.radians(v[0] if v else 0)), 0, 0, 1, 0)
        elif fn == "skewY": T = (1, 0, 0, math.tan(math.radians(v[0] if v else 0)), 1, 0)
        else: continue
        M = mmul(M, T)
    return M

def _arc(p0, rx, ry, rot, laf, sf, p1, n=16):
    if rx == 0 or ry == 0: return [p1]
    rot = math.radians(rot)
    dx2, dy2 = (p0[0]-p1[0])/2, (p0[1]-p1[1])/2
    x1 = math.cos(rot)*dx2 + math.sin(rot)*dy2
    y1 = -math.sin(rot)*dx2 + math.cos(rot)*dy2
    rx, ry = abs(rx), abs(ry)
    lam = x1*x1/(rx*rx) + y1*y1/(ry*ry)
    if lam > 1: rx *= math.sqrt(lam); ry *= math.sqrt(lam)
    num = rx*rx*ry*ry - rx*rx*y1*y1 - ry*ry*x1*x1
    den = rx*rx*y1*y1 + ry*ry*x1*x1
    co = math.sqrt(max(0.0, num/den)) * (-1 if laf == sf else 1)
    cxp, cyp = co*rx*y1/ry, -co*ry*x1/rx
    cx = math.cos(rot)*cxp - math.sin(rot)*cyp + (p0[0]+p1[0])/2
    cy = math.sin(rot)*cxp + math.cos(rot)*cyp + (p0[1]+p1[1])/2
    def ang(ux, uy, vx, vy):
        d = max(-1, min(1, (ux*vx+uy*vy)/(math.hypot(ux, uy)*math.hypot(vx, vy))))
        a = math.acos(d)
        return -a if ux*vy - uy*vx < 0 else a
    th1 = ang(1, 0, (x1-cxp)/rx, (y1-cyp)/ry)
    dth = ang((x1-cxp)/rx, (y1-cyp)/ry, (-x1-cxp)/rx, (-y1-cyp)/ry)
    if not sf and dth > 0: dth -= 2*math.pi
    if sf and dth < 0: dth += 2*math.pi
    out = []
    for k in range(1, n+1):
        th = th1 + dth*k/n
        out.append((math.cos(rot)*rx*math.cos(th) - math.sin(rot)*ry*math.sin(th) + cx,
                    math.sin(rot)*rx*math.cos(th) + math.cos(rot)*ry*math.sin(th) + cy))
    return out

def d_points(d, n=8):
    toks = re.findall(r'([MmZzLlHhVvCcSsQqTtAa])|([-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?)', d)
    subs, cur = [], []
    cx = cy = sx = sy = 0.0
    px = py = None
    cmd = None
    i = 0
    def take(k):
        nonlocal i
        vals = []
        while len(vals) < k and i < len(toks):
            a, b = toks[i]
            if a: break
            vals.append(float(b)); i += 1
        return vals if len(vals) == k else None
    while i < len(toks):
        a, b = toks[i]
        if a: cmd = a; i += 1
        if cmd is None: i += 1; continue
        rel = cmd.islower(); C = cmd.upper()
        if C == 'M':
            v = take(2)
            if v is None: break
            cx, cy = (cx+v[0], cy+v[1]) if rel else (v[0], v[1])
            if cur: subs.append(cur)
            cur = [(cx, cy)]; sx, sy = cx, cy; px = py = None
            cmd = 'l' if rel else 'L'
        elif C == 'L':
            v = take(2)
            if v is None: break
            cx, cy = (cx+v[0], cy+v[1]) if rel else (v[0], v[1]); cur.append((cx, cy)); px = py = None
        elif C == 'H':
            v = take(1)
            if v is None: break
            cx = cx+v[0] if rel else v[0]; cur.append((cx, cy)); px = py = None
        elif C == 'V':
            v = take(1)
            if v is None: break
            cy = cy+v[0] if rel else v[0]; cur.append((cx, cy)); px = py = None
        elif C == 'C':
            v = take(6)
            if v is None: break
            if rel: v = [v[0]+cx, v[1]+cy, v[2]+cx, v[3]+cy, v[4]+cx, v[5]+cy]
            cur += _bez((cx, cy), (v[0], v[1]), (v[2], v[3]), (v[4], v[5]), n)
            px, py = v[2], v[3]; cx, cy = v[4], v[5]
        elif C == 'S':
            v = take(4)
            if v is None: break
            if rel: v = [v[0]+cx, v[1]+cy, v[2]+cx, v[3]+cy]
            c1 = (2*cx-px, 2*cy-py) if px is not None else (cx, cy)
            cur += _bez((cx, cy), c1, (v[0], v[1]), (v[2], v[3]), n)
            px, py = v[0], v[1]; cx, cy = v[2], v[3]
        elif C == 'Q':
            v = take(4)
            if v is None: break
            if rel: v = [v[0]+cx, v[1]+cy, v[2]+cx, v[3]+cy]
            cur += _bez((cx, cy), (cx+2/3*(v[0]-cx), cy+2/3*(v[1]-cy)),
                        (v[2]+2/3*(v[0]-v[2]), v[3]+2/3*(v[1]-v[3])), (v[2], v[3]), n)
            px, py = v[0], v[1]; cx, cy = v[2], v[3]
        elif C == 'T':
            v = take(2)
            if v is None: break
            if rel: v = [v[0]+cx, v[1]+cy]
            q = (2*cx-px, 2*cy-py) if px is not None else (cx, cy)
            cur += _bez((cx, cy), (cx+2/3*(q[0]-cx), cy+2/3*(q[1]-cy)),
                        (v[0]+2/3*(q[0]-v[0]), v[1]+2/3*(q[1]-v[1])), (v[0], v[1]), n)
            px, py = q; cx, cy = v[0], v[1]
        elif C == 'A':
            v = take(7)
            if v is None: break
            ex, ey = (cx+v[5], cy+v[6]) if rel else (v[5], v[6])
            cur += _arc((cx, cy), v[0], v[1], v[2], v[3], v[4], (ex, ey), n)
            cx, cy = ex, ey; px = py = None
        elif C == 'Z':
            cur.append((sx, sy)); cx, cy = sx, sy
            if cur: subs.append(cur)
            cur = []; px = py = None
            i += 1 if not a else 0
            continue
        else:
            i += 1
    if cur: subs.append(cur)
    return subs

def elem_points(e, n=8):
    tag = re.match(r'<(\w+)', e).group(1)
    at = dict(re.findall(r'([\w:-]+)="([^"]*)"', e))
    if tag == "path": return d_points(at.get("d", ""), n)
    if tag in ("circle", "ellipse"):
        cx, cy = float(at.get("cx", 0)), float(at.get("cy", 0))
        rx = ry = float(at.get("r", 0)) if tag == "circle" else 0
        if tag == "ellipse": rx, ry = float(at.get("rx", 0)), float(at.get("ry", 0))
        th = np.linspace(0, 2*math.pi, 4*n+1)
        return [list(zip(cx + rx*np.cos(th), cy + ry*np.sin(th)))]
    if tag == "rect":
        x, y = float(at.get("x", 0)), float(at.get("y", 0))
        w, h = float(at.get("width", 0)), float(at.get("height", 0))
        return [[(x, y), (x+w, y), (x+w, y+h), (x, y+h), (x, y)]]
    if tag in ("polygon", "polyline"):
        v = [float(x) for x in NUM.findall(at.get("points", ""))]
        pts = list(zip(v[0::2], v[1::2]))
        return [pts + [pts[0]] if tag == "polygon" and pts else pts]
    return []

def svg_parts(name, n=8):
    """the drawable elements of a plain avatar SVG, in the order decisions.json indexes them"""
    f = os.path.join(SVG, name + ".svg")
    if not os.path.exists(f): f = os.path.join(SVG, name + "2.svg")
    s = open(f).read()
    _, body = split_body(s)
    styles = styles_of(s)
    out, stack, idx = [], [IDM], 0
    for m in TAG.finditer(body):
        close, tag, attrs, selfclose = m.groups()
        if close:
            if len(stack) > 1: stack.pop()
            continue
        tr = re.search(r'transform="([^"]*)"', attrs)
        M = mmul(stack[-1], svg_matrix(tr.group(1))) if tr else stack[-1]
        if tag in ("path", "ellipse", "rect", "circle", "polygon", "polyline"):
            e = m.group(0)
            p = elem_props(e, styles)
            subs = [mapply(M, sp) for sp in elem_points(e, n)]
            bbox, area = bbox_of(subs)
            idm = re.search(r'\sid="([^"]*)"', e)
            out.append({"i": idx, "id": idm.group(1) if idm else None,
                        "fill": norm_hex(p["fill"]), "stroke": norm_hex(p["stroke"]),
                        "opacity": p["opacity"], "bbox": bbox, "area": area})
            idx += 1
        if not selfclose: stack.append(M)
    return out

_DEC = None

def part_runs(name):
    """{part index: (inner, band, bare, free)} outline lengths in units, from the generator's audit.

    inner  in@bg and in@N: the line v9 draws inside this part, which is the line this pass draws
    band   out:N: v9 draws this one OUTSIDE the part, onto the darker piece below it, because the
           line belongs on the darker side of the seam. Drawn inside instead it lands on the
           lighter side, which is exactly what the rule avoids: white teeth on a dark mouth come
           out ringed in grey. So a band is never a reason to stroke a part.
    bare   none@N: v9 deliberately leaves this stretch alone, because the two are one material (a
           face and its shading) or because the neighbour draws its own line along it
    free   far@N (a black line on a dark piece that cannot be seen) and hidden outline, which the
           layer order covers anyway

    A whole-shape stroke cannot cut the bare stretches without baking the cut geometry, so a part
    is only stroked when the line v9 draws inside it is at least as long as the line v9 leaves off
    it. Measured over the 9,877 bordered parts, that holds the line the still does not draw down to
    8% of the true line and the band drawn on the wrong side to 7%, against 10% and 18% for a rule
    that counts the band as a reason to stroke."""
    global _DEC
    if _DEC is None:
        _DEC = json.load(open(os.path.join(BOR, "decisions.json")))
    ent = _DEC.get(name + ".svg") or _DEC.get(name + "2.svg") or {}
    out = {}
    for k, v in ent.items():
        if v.get("runs") is None: continue
        t = collections.Counter()
        nb = collections.defaultdict(collections.Counter)
        for tag, ln in v["runs"]:
            kind = tag.split("@")[0].split(":")[0]
            t[kind] += ln
            who = tag.partition("@")[2] or (tag.split(":")[1] if tag.startswith("out:") else "")
            if who and who != "bg": nb[int(who)][kind] += ln
        out[int(k)] = (t["in"], t["out"], t["none"], t["far"], dict(nb))
    return out

def top_neighbour(nb, kind):
    """the neighbour this part shares the most of `kind` with, and how much of that kind it is"""
    if not nb: return None, 0.0
    tot = sum(c.get(kind, 0.0) for c in nb.values())
    if tot <= 0: return None, 0.0
    n = max(nb, key=lambda j: nb[j].get(kind, 0.0))
    return n, nb[n].get(kind, 0.0) / tot


_USE = re.compile(r'<use\b[^>]*/?>')

def v9_flags(name):
    """{part index: {"inner", "outer", "mouth"}} read from the built v9 SVG.

    svgo's inlineStyles rewrites a .abm rule that matches one element into an inline style, so both
    spellings have to be read: 155 elements carry the class, 121 the style."""
    path = os.path.join(BOR, name + ".svg")
    if not os.path.exists(path): path = os.path.join(BOR, name + "2.svg")
    out = {}
    if not os.path.exists(path): return out
    s = open(path).read()
    for u in _USE.findall(s):
        h = re.search(r'href="#ab(\d+)"', u)
        m = re.search(r'mask="url\(#(a[mo])\d+\)"', u)
        if not h or not m: continue
        r = out.setdefault(int(h.group(1)), {"inner": False, "outer": False, "mouth": False})
        r["outer" if m.group(1) == "ao" else "inner"] = True
        cl = re.search(r'\bclass="([^"]*)"', u)
        st = re.search(r'\bstyle="([^"]*)"', u)
        if (cl and "abm" in cl.group(1).split()) or (st and "stroke-opacity:.35" in st.group(1).replace(" ", "")):
            r["mouth"] = True
    return out


# ---------------------------------------------------------------- colour

def _lin(v): return v/12.92 if v <= 0.04045 else ((v+0.055)/1.055)**2.4

def lab_of(h):
    if not h: return None
    r, g, b = (int(h[1:3], 16)/255.0, int(h[3:5], 16)/255.0, int(h[5:7], 16)/255.0)
    r, g, b = _lin(r), _lin(g), _lin(b)
    X = (0.4124*r + 0.3576*g + 0.1805*b)/0.95047
    Y = 0.2126*r + 0.7152*g + 0.0722*b
    Z = (0.0193*r + 0.1192*g + 0.9505*b)/1.08883
    f = lambda v: v**(1/3) if v > 0.008856 else 7.787*v + 16/116
    return (116*f(Y) - 16, 500*(f(X)-f(Y)), 200*(f(Y)-f(Z)))

def dE(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))

def lum(h):
    r, g, b = (int(h[1:3], 16)/255.0, int(h[3:5], 16)/255.0, int(h[5:7], 16)/255.0)
    return 0.2126*_lin(r) + 0.7152*_lin(g) + 0.0722*_lin(b)


# ---------------------------------------------------------------- matching

def paint_key(o):
    if o.get("fill"): return ("f", o["fill"])
    if o.get("stroke"): return ("s", o["stroke"])
    return None

def frame_grid(d, k=FRAMES):
    ip, op = int(d.get("ip", 0)), int(d.get("op", 60))
    if op <= ip or k <= 1: return [ip]
    return sorted(set(int(round(ip + (op-ip)*i/(k-1))) for i in range(k)))

def units_over(d, frames):
    seq, idx = [], {}
    for f in frames:
        for u in lottie_units(d, f):
            if u["uid"] not in idx:
                idx[u["uid"]] = len(seq)
                seq.append({"uid": u["uid"], "meta": u, "bb": [], "ar": []})
            e = seq[idx[u["uid"]]]
            e["bb"].append(u["bbox"]); e["ar"].append(u["area"])
    return seq

def modal_offset(seq, parts, abin=0.02, obin=0.25):
    votes = collections.Counter()
    pk = collections.defaultdict(list)
    for p in parts:
        k = paint_key(p)
        if k and p["bbox"] and p["area"] > 0: pk[k].append(p)
    for e in seq:
        k = paint_key(e["meta"])
        if not k: continue
        for bb, ar in zip(e["bb"], e["ar"]):
            if not bb or ar <= 0: continue
            uc = ((bb[0]+bb[2])/2, (bb[1]+bb[3])/2)
            for p in pk.get(k, ()):
                if abs(ar-p["area"]) > abin*max(ar, p["area"]): continue
                pc = ((p["bbox"][0]+p["bbox"][2])/2, (p["bbox"][1]+p["bbox"][3])/2)
                votes[(round((uc[0]-pc[0])/obin), round((uc[1]-pc[1])/obin))] += math.sqrt(ar)
    if not votes: return []
    return [((d[0]*obin, d[1]*obin), round(nv, 1)) for d, nv in votes.most_common(6)]

def geo_cost(e, p, off):
    best = None
    for fi, (bb, ar) in enumerate(zip(e["bb"], e["ar"])):
        if not bb or not p["bbox"]: continue
        d0 = bb[0]-off[0]-p["bbox"][0]; d1 = bb[1]-off[1]-p["bbox"][1]
        d2 = bb[2]-off[0]-p["bbox"][2]; d3 = bb[3]-off[1]-p["bbox"][3]
        c = (abs(d0)+abs(d1)+abs(d2)+abs(d3))/4.0
        a = abs(ar - p["area"]) / max(ar, p["area"], 1e-6)
        v = c + 20.0*a
        if best is None or v < best[0]: best = (v, c, a, ((d0+d2)/2, (d1+d3)/2), fi)
    return best

_LABC = {}
def labc(h):
    if h not in _LABC: _LABC[h] = lab_of(h)
    return _LABC[h]

def paint_ok(ku, kp, de=DE):
    if ku is None or kp is None or ku[0] != kp[0]: return False
    if ku[1] == kp[1]: return True
    a, b = labc(ku[1]), labc(kp[1])
    return a is not None and b is not None and dE(a, b) <= de

def assign(seq, parts, off, names, name_bonus=2.0, cap=CAP):
    n, m = len(seq), len(parts)
    BIG = 1e6
    C = np.full((n, m), BIG); G = np.full((n, m), np.nan)
    DX = np.full((n, m), np.nan); DY = np.full((n, m), np.nan)
    for i, e in enumerate(seq):
        ku = paint_key(e["meta"])
        if not ku: continue
        for j, p in enumerate(parts):
            if not paint_ok(ku, paint_key(p)): continue
            r = geo_cost(e, p, off)
            if r is None: continue
            G[i, j] = r[0]; DX[i, j] = r[3][0]; DY[i, j] = r[3][1]
            C[i, j] = max(0.0, r[0] - name_bonus) if (names[i] and p["id"] == names[i]) else r[0]
    if not (HUNGARIAN and n and m): return {}, G
    sq = max(n, m)
    S = np.full((sq, sq), BIG); S[:n, :m] = C
    ri, ci = linear_sum_assignment(S)
    out = {}
    for a, b in zip(ri, ci):
        if a < n and b < m and C[a, b] <= cap:
            out[a] = (int(b), float(C[a, b]), float(G[a, b]), float(DX[a, b]), float(DY[a, b]))
    return out, G

def _score(a):
    tight = sum(1 for v in a.values() if v[2] < 0.5)
    return (-(2*tight + len(a)), sum(v[1] for v in a.values()))

def match_units(doc, svg_name, parts=None, frames=None):
    """[(uid, part index or None, method)] plus the sequence and the offset used"""
    parts = svg_parts(svg_name) if parts is None else parts
    frames = frame_grid(doc) if frames is None else frames
    seq = units_over(doc, frames)
    per_layer = collections.Counter(e["meta"]["layer_idx"] for e in seq)
    names = []
    for e in seq:
        m = e["meta"]
        names.append(m["gname"] if (per_layer[m["layer_idx"]] > 1 and m["gname"]) else (m["layer_nm"] or m["gname"]))
    cands = modal_offset(seq, parts) or [((0.0, 0.0), 0)]
    if (0.0, 0.0) not in [c[0] for c in cands]: cands.append(((0.0, 0.0), 0))
    best = None
    for off, _sup in cands:
        a, _G = assign(seq, parts, off, names)
        k = _score(a)
        if best is None or k < best[0]: best = (k, off, a)
    key, off, a = best
    for _ in range(3):
        tight = [(v[3], v[4]) for v in a.values() if v[2] < 1.0]
        if len(tight) < 3: break
        dx = float(np.median([t[0] for t in tight])); dy = float(np.median([t[1] for t in tight]))
        if abs(dx) < 0.02 and abs(dy) < 0.02: break
        no = (round((off[0]+dx)*4)/4, round((off[1]+dy)*4)/4)
        a2, _G = assign(seq, parts, no, names)
        k2 = _score(a2)
        if k2 <= key: key, off, a = k2, no, a2
        else: break
    rows = []
    for i, e in enumerate(seq):
        v = a.get(i)
        if v is None: rows.append((e["uid"], None, "none"))
        else: rows.append((e["uid"], v[0], "geom-exact" if v[2] < 0.5 else ("geom-close" if v[2] < 1.5 else "geom-loose")))
    return rows, seq, off


# ---------------------------------------------------------------- the gate

def share_duplicates(parts, flags, runs):
    """Give every copy of a repeated shape the decision the drawn copy got.

    Several of these drawings hold the same shape twice, a visible copy and one that a later shape
    covers, and the generator borders only the copy it can see. The match is geometric, so it lands
    on whichever copy it likes, and on OtherVolcano_win that left 76 of 87 shapes reading their
    answer off a hidden twin: 38 bordered parts in the still, 5 lines in the animation. Parts with
    the same fill and the same bounding box now share the answer of whichever of them the generator
    saw the most of."""
    groups = collections.defaultdict(list)
    for p in parts:
        if not p["bbox"]: continue
        groups[(p["fill"], p["stroke"], tuple(round(x, 1) for x in p["bbox"]))].append(p["i"])
    f2, r2 = dict(flags), dict(runs)
    shared = 0
    for idx in groups.values():
        if len(idx) < 2: continue
        best, seen = None, -1.0
        for i in idx:
            if i not in flags: continue
            vis = sum(runs.get(i, (0, 0, 0, 0))[:4])
            if vis > seen: best, seen = i, vis
        if best is None: continue
        for i in idx:
            if i == best: continue
            if i not in flags or sum(runs.get(i, (0, 0, 0, 0))[:4]) < seen:
                f2[i] = flags[best]
                if best in runs: r2[i] = runs[best]
                shared += 1
    return f2, r2, shared


def intrinsic_is_part(meta, areas, bboxes):
    """the generator's own gate read off a Lottie unit, for a unit with no SVG part.

    Plus one rule the generator's gate does not carry: the shape has to be big. Counted over all
    13,365 parts the generator judged, a part 30 units or more across owns an inside line 53 to 64%
    of the time whatever its colour, and a smaller one only 18 to 47%. Small shapes are the ones
    whose line the still draws onto the piece below, where it does not show, and guessing wrong on
    them is the loudest way to be wrong: the grey rim that appeared on six white robot teeth. The
    generator's own floor is 10 units, which is the right floor for a part it can cut the line on;
    it is the wrong floor for a whole-shape stroke placed on a guess."""
    fill = meta.get("fill")
    if not fill: return False
    if meta.get("fill_opacity") not in (None, 100): return False
    if meta.get("group_opacity", 1) < 0.99: return False
    if (meta.get("layer_opacity") or 100) < 99.5: return False
    bbs = [b for b in bboxes if b]
    dim = max((max(b[2]-b[0], b[3]-b[1]) for b in bbs), default=0.0)
    amax = max(areas) if areas else 0.0
    if dim < INTRINSIC_MIN_DIM: return False
    if lum(fill) < 0.03 and (dim < 24 or amax < 250): return False
    return True


# ---------------------------------------------------------------- emitting the border

class Unsupported(Exception):
    pass

def _find_tr(items):
    for n, x in enumerate(items):
        if x.get("ty") == "tr": return n
    return None

def _descend(shapes, gpath):
    """the it array a gpath names, plus the chain of groups above it"""
    if gpath == (-1,): return shapes, []
    grs = [x for x in shapes if x.get("ty") == "gr"]
    if not grs or gpath[0] >= len(grs): raise Unsupported("gpath")
    node = grs[gpath[0]]
    chain = [node]
    for g in gpath[1:]:
        sub = [x for x in node.get("it", []) if x.get("ty") == "gr"]
        if g >= len(sub): raise Unsupported("gpath")
        node = sub[g]; chain.append(node)
    return node["it"], chain

def _clone_chain(shapes, gpath, rebuild):
    """a shapes array holding only the group chain gpath, with `rebuild(it)` at the leaf"""
    if gpath == (-1,): return rebuild(shapes)
    out = []
    grs_seen = -1
    for x in shapes:
        if x.get("ty") != "gr": continue
        grs_seen += 1
        if grs_seen != gpath[0]: continue
        g = copy.deepcopy(x)
        g["it"] = _clone_inner(x["it"], gpath[1:], rebuild)
        out.append(g)
    if not out: raise Unsupported("gpath")
    return out

def _clone_inner(items, gpath, rebuild):
    if not gpath: return rebuild(items)
    out = []
    grs_seen = -1
    for x in items:
        if x.get("ty") == "gr":
            grs_seen += 1
            if grs_seen == gpath[0]:
                g = copy.deepcopy(x)
                g["it"] = _clone_inner(x["it"], gpath[1:], rebuild)
                out.append(g)
        elif x.get("ty") == "tr":
            out.append(copy.deepcopy(x))
    if not out: raise Unsupported("gpath")
    return out

def stroke_item(op, w):
    return {"ty": "st", "c": {"a": 0, "k": [0, 0, 0, 1], "ix": 3}, "o": {"a": 0, "k": op, "ix": 4},
            "w": w, "lc": 2, "lj": 2, "ml": 4, "bm": 0,
            "nm": "ab", "mn": "ADBE Vector Graphic - Stroke", "hd": False}

def _geom_indices(items, keep):
    """items rebuilt to hold only the geometry objects in `keep` (by identity), plus the tr"""
    out = []
    for x in items:
        if x.get("ty") in GEOM:
            if any(x is k for k in keep): out.append(copy.deepcopy(x))
        elif x.get("ty") == "tr":
            out.append(copy.deepcopy(x))
    return out

def contains(a, b, slack=0.5):
    """bbox a contains bbox b"""
    return (a[0] - slack <= b[0] and a[1] - slack <= b[1]
            and a[2] + slack >= b[2] and a[3] + slack >= b[3])

def outer_geoms(items, t):
    """the geometry of a level, minus any path whose box lies inside another's.

    lottie_light has no merge-paths modifier, so a (gr,gr,mm,fl,tr) group paints the plain
    non-zero union of its sub-paths and the inner ones show no edge. Stroking them would draw a
    line the drawing does not have."""
    geoms = [x for x in items if x.get("ty") in GEOM]
    boxes = []
    for g in geoms:
        bb, _ = bbox_of([geom_points(g, t)])
        boxes.append(bb)
    keep = []
    for i, g in enumerate(geoms):
        if boxes[i] is None: continue
        if any(j != i and boxes[j] is not None and contains(boxes[j], boxes[i])
               and not contains(boxes[i], boxes[j]) for j in range(len(geoms))):
            continue
        keep.append(g)
    return geoms, keep

def mask_from(item, M, t, inv=False):
    """one mask carrying the item's own path, moved into layer space.

    `inv` turns it inside out, which is how the band onto the piece below is drawn: the stroke is
    kept only OUTSIDE the shape, and a track matte to a copy of that piece keeps it only where the
    piece is. Both clips carry real animated paths, so nothing is baked.

    The group transforms are static everywhere in the set, so this is an exact change of frame,
    not a bake: an animated path keeps all its keyframes and the border morphs with it."""
    ty = item.get("ty")
    if ty in ("el", "rc"):
        for k in ("p", "s", "r"):
            if is_animated(item.get(k)): raise Unsupported("animated " + ty)
        pt = {"a": 0, "k": xform_path(el_path(item, t) if ty == "el" else rc_path(item, t), M), "ix": 1}
    elif ty == "sh":
        k = item["ks"]
        if not k.get("a"):
            pt = {"a": 0, "k": xform_path(k["k"], M), "ix": 1}
        else:
            kfs = copy.deepcopy(k["k"])
            for kf in kfs:
                for side in ("s", "e"):
                    if kf.get(side) and isinstance(kf[side][0], dict):
                        kf[side][0] = xform_path(kf[side][0], M)
            pt = {"a": 1, "k": kfs, "ix": 1}
    else:
        raise Unsupported(ty or "?")
    return {"inv": bool(inv), "mode": "a", "pt": pt, "o": {"a": 0, "k": 100, "ix": 3},
            "x": {"a": 0, "k": 0, "ix": 4}, "nm": "ab-out" if inv else "ab-self"}

def xform_path(p, M):
    return {"i": [mvec(M, x) for x in p["i"]], "o": [mvec(M, x) for x in p["o"]],
            "v": [mpoint(M, x) for x in p["v"]], "c": p.get("c", True)}

def layer_has_modifier(layer):
    def walk(items):
        for x in items:
            if x.get("ty") in MODIFIERS: return True
            if x.get("ty") == "gr" and walk(x.get("it", [])): return True
        return False
    return walk(layer.get("shapes", []))

def group_matrix_to_layer(shapes, gpath, t):
    """the matrix that carries a unit's own coordinates into layer space, and its scale"""
    if gpath == (-1,): return IDM
    M = IDM
    grs = [x for x in shapes if x.get("ty") == "gr"]
    node = grs[gpath[0]]
    trs = [y for y in node["it"] if y.get("ty") == "tr"]
    if trs:
        if any(is_animated(trs[-1].get(k)) for k in ("p", "a", "s", "r", "sk", "sa")):
            raise Unsupported("animated group tr")
        M = mmul(M, group_matrix(trs[-1], t))
    for g in gpath[1:]:
        node = [y for y in node["it"] if y.get("ty") == "gr"][g]
        trs = [y for y in node["it"] if y.get("ty") == "tr"]
        if trs:
            if any(is_animated(trs[-1].get(k)) for k in ("p", "a", "s", "r", "sk", "sa")):
                raise Unsupported("animated group tr")
            M = mmul(M, group_matrix(trs[-1], t))
    return M

def scale_times(doc, layer, by_ind):
    """the frames where the scale of this layer or of anything above it changes, plus midpoints"""
    ip = int(max(layer.get("ip", doc.get("ip", 0)), doc.get("ip", 0)))
    op = int(min(layer.get("op", doc.get("op", 60)), doc.get("op", 60)))
    if op <= ip: ip, op = int(doc.get("ip", 0)), int(doc.get("op", 60))
    ts = {ip, op}
    L, seen = layer, 0
    while L is not None and seen < 20:
        s = L.get("ks", {}).get("s")
        if isinstance(s, dict) and s.get("a"):
            for k in s.get("k", []): ts.add(int(k.get("t", 0)))
        L = by_ind.get(L.get("parent")); seen += 1
    ts = sorted(t for t in ts if ip <= t <= op) or [ip, op]
    out = []
    for a, b in zip(ts, ts[1:]):
        out.append(a)
        n = min(6, max(1, (b - a) // 6))
        for j in range(1, n): out.append(a + (b - a) * j // n)
    out.append(ts[-1])
    return sorted(set(out))

def unit_scales(doc, layer, gpath, by_ind):
    """[(frame, the scale from the unit's own space to the comp)] over the clip.

    A layer that scales carries its stroke with it, so a width fixed in the layer's own space is
    drawn at whatever that scale happens to be. On ManChef_win the arm's chain runs from 2.35 to
    8.96 and a single number is nearly three times wrong at one end. The width is therefore a
    curve, sampled here and written as an animated property, so the line is 2 units at every
    frame."""
    G = group_matrix_to_layer(layer.get("shapes", []), gpath, 0.0)
    gs = mscale(G)
    out = []
    for t in scale_times(doc, layer, by_ind):
        s = mscale(chain_matrix(layer, t, by_ind)) * gs
        if s > 1e-6: out.append((t, s))
    if not out: raise Unsupported("scale 0 throughout")
    return out

def width_prop(samples, k=1.0):
    """the stroke width: one number when the scale holds still, a curve when it does not.

    `k` thins the line on a shape too narrow to hold it: a 2-unit inset from both sides of a
    5-unit stripe leaves a solid bar, which is what the still avoids by cutting the line."""
    ws = [(t, W_UNITS * COMP_PER_UNIT * k / s) for t, s in samples]
    med = float(np.median([w for _, w in ws]))
    lo, hi = min(w for _, w in ws), max(w for _, w in ws)
    if hi / lo < 1.10:
        return {"a": 0, "k": round(med, 4), "ix": 5}, med
    kfs = []
    for n, (t, w) in enumerate(ws):
        kf = {"t": t, "s": [round(w, 4)]}
        if n < len(ws) - 1:
            kf["i"] = {"x": [0.833], "y": [0.833]}
            kf["o"] = {"x": [0.167], "y": [0.167]}
        kfs.append(kf)
    return {"a": 1, "k": kfs, "ix": 5}, med

def make_line(layer, gpath, keep, op, w, mask, matte_ind, ind, tt=1, nm="ab-line"):
    """the ab-line layer: the unit's own paths, no fill, one stroke, clipped"""
    L = copy.deepcopy(layer)
    L["nm"] = nm
    for k in ("td", "tt", "tp", "hasMask", "masksProperties"): L.pop(k, None)
    def rebuild(items):
        out = _geom_indices(items, keep)
        idx = _find_tr(out)
        out.insert(len(out) if idx is None else idx, stroke_item(op, w))
        return out
    L["shapes"] = _clone_chain(layer.get("shapes", []), gpath, rebuild)
    if mask is not None:
        L["hasMask"] = True
        L["masksProperties"] = [mask]
    if matte_ind is not None:
        L["tt"] = tt; L["tp"] = matte_ind
    L["ind"] = ind
    return L

def fully_opaque(prop):
    """an opacity property that is 100 at every frame"""
    if prop is None: return True
    def one(v):
        if v is None: return True
        return (v[0] if isinstance(v, list) else v) == 100
    if prop.get("a"):
        return all(one(k.get("s")) and one(k.get("e")) for k in prop.get("k", []))
    return one(prop.get("k"))

def split_pieces(items, gpath=()):
    """Cut a shape tree into the pieces that can be moved into layers of their own.

    A line layer sits above the layer it belongs to, so it paints over everything in that layer,
    including the shapes that were covering the piece it lines. On a layer that draws the whole
    avatar (12 groups in ManBusinessman_win) that puts the face's outline over the hair. Splitting
    the layer into one layer per piece, in the same order, restores the paint order: a piece's line
    goes directly above its own piece and under every piece that was above it.

    A level is only split when it holds nothing but groups and its own transform. A level that also
    carries a style or a path paints its children itself, so cutting it would drop the paint."""
    grs = [x for x in items if x.get("ty") == "gr"]
    others = [x for x in items if x.get("ty") not in ("gr", "tr")]
    trs = [x for x in items if x.get("ty") == "tr"]
    if not grs or others:
        return [(copy.deepcopy(items), gpath)]
    if trs and not fully_opaque(trs[-1].get("o")):
        return [(copy.deepcopy(items), gpath)]      # a translucent group composites as one
    out = []
    for gi, g in enumerate(grs):
        for sub, gp in split_pieces(g.get("it", []), gpath + (gi,)):
            ng = copy.deepcopy(g); ng["it"] = sub
            out.append(([ng] + copy.deepcopy(trs), gp))
    return out

def rebuild_layer(layer, groups, ind_from):
    """The layer cut open only where a line has to go in, with the lines in place.

    Returns [layers] in paint order, or None when nothing needs cutting. `groups` is
    [(gpath, [line layers])]. A line has to draw over its own piece and under every piece that was
    above it, so the layer is flushed as one piece up to that point, then the lines, then the rest:
    one cut per line, not one per group. The first piece keeps the layer's ind so anything parented
    to it still resolves.

    A layer that is ever less than fully opaque is never cut: lottie flattens a layer's shapes and
    then applies the layer opacity, so two pieces at 50% show through each other where the one
    layer did not. 340 of the 8,095 shape layers fade, and ManBoy_lose is one of them."""
    if not fully_opaque(layer.get("ks", {}).get("o")) or layer.get("bm"):
        return None, ind_from
    pieces = split_pieces(layer.get("shapes", []))
    at = collections.defaultdict(list)
    for gp, ls in groups:
        k = 0
        for n, (_s, pgp) in enumerate(pieces):
            if gp[:len(pgp)] == pgp: k = n; break
        at[k] += ls
    if len(pieces) < 2 or sorted(at) == [0]:
        return None, ind_from                 # one block of lines above the whole layer is enough
    out, buf = [], []
    def flush():
        if not buf: return
        P = copy.deepcopy(layer)
        P["shapes"] = list(buf)
        out.append(P)
        del buf[:]
    for k, (shapes, _gp) in enumerate(pieces):
        if k in at:
            flush()
            out += at[k]
        buf += shapes
    flush()
    first = True
    for x in out:
        if x.get("nm") in ("ab-line", "ab-matte"): continue
        if first: x["ind"] = layer.get("ind"); first = False
        else: ind_from += 1; x["ind"] = ind_from
    return out, ind_from

def make_matte(layer, gpath, geoms, fill, ind):
    """the ab-matte layer: the unit as it paints, kept opaque, never drawn itself"""
    M = copy.deepcopy(layer)
    M["nm"] = "ab-matte"
    for k in ("tt", "tp", "hasMask", "masksProperties"): M.pop(k, None)
    M["td"] = 1
    def rebuild(items):
        out = _geom_indices(items, geoms)
        idx = _find_tr(out)
        out.insert(len(out) if idx is None else idx, copy.deepcopy(fill))
        return out
    M["shapes"] = _clone_chain(layer.get("shapes", []), gpath, rebuild)
    M.setdefault("ks", {})["o"] = {"a": 0, "k": 100, "ix": 11}
    M["ind"] = ind
    return M


# ---------------------------------------------------------------- looking at the animation itself
#
# The border generator does not read the drawing out of the file, it renders it: one page per SVG
# holding a label map (every shape in a flat id colour), the drawing as it is, and every shape on
# its own. From those it knows, at every point of every outline, which shape is visible outside it,
# and it decides the line from the two colours as seen. Borrowing those decisions across to the
# animation is what goes wrong: the neighbour a run names is an SVG element, and carrying it over a
# geometric match puts the line in the wrong place often enough to be worse than not drawing it.
#
# So the animation is rendered and read the same way. Every neighbour is then a Lottie shape by
# construction, which is what lets the line be cut where the neighbour owns it, and drawn as a band
# onto the piece below, without baking any geometry.

LOOK_S = 3                       # pixels per unit in the 160-unit box, as the generator uses
LOOK_PX = 160 * LOOK_S
LOOK_COLS = 8
T_L, T_C, T_GREY, T_GREY_L = 18, 8, 10, 22
SPREAD, K_LO, K_HI, T_LO, T_HI = 0.09, 0.45, 1.0, 0.0, 0.40
PALE_L, LIGHT_L, MARK_AREA, MARK_RING, MARK_DE = 88, 75, 0.5, 0.75, 24
INK_DIM, INK_AREA = 24, 250
DARK_L, FAR = 25, 40
MOUTH_RING, MOUTH_AREA, MOUTH_L = 0.6, 0.06, 12
MIN_DIM, MIN_RUN = 10, 2.0

def idcol(i):
    """id colours 8 apart per channel: a screenshot drifts by a level or two through the profile"""
    return [0.0, ((i // 32) * 8) / 255.0, ((i % 32) * 8 + 4) / 255.0, 1.0]

def decode_labels(lm):
    g = np.rint(lm[..., 1] / 8).astype(int)
    b = np.rint((lm[..., 2] - 4) / 8).astype(int)
    return np.where(lm[..., 3] > 0, g * 32 + b, -1)

def _paint_here(items, col):
    for x in items:
        if x.get("ty") in ("fl", "st"):
            x["c"] = {"a": 0, "k": list(col), "ix": 3}

def _unit_items(items):
    """the unit's own contents: its geometry and styles, minus any nested group that paints itself"""
    out = []
    for x in items:
        if x.get("ty") == "gr":
            if any(y.get("ty") in STYLES for y in x.get("it", [])): continue
        out.append(copy.deepcopy(x))
    return out

def label_doc(doc, units):
    d = copy.deepcopy(doc)
    for n, u in enumerate(units):
        try:
            items, _c = _descend(d["layers"][u["layer_idx"]].get("shapes", []), u["gpath"])
        except Unsupported:
            continue
        _paint_here(items, idcol(n))
    return d

def alone_doc(doc, u):
    """the unit on its own, in white, with everything else emptied but the transforms left alone"""
    d = copy.deepcopy(doc)
    for i, L in enumerate(d["layers"]):
        if L.get("ty") != 4 or L.get("td"): continue
        if i != u["layer_idx"]:
            L["shapes"] = []
            continue
        try:
            L["shapes"] = _clone_chain(L.get("shapes", []), u["gpath"], _unit_items)
        except Unsupported:
            L["shapes"] = []
            continue
        L.pop("tt", None); L.pop("tp", None)      # its own outline, not the part a matte leaves
        try:
            items, _c = _descend(L["shapes"], u["gpath"])
            _paint_here(items, [1.0, 1.0, 1.0, 1.0])
        except Unsupported:
            pass
    return d

def look_page(doc, units, frame, out_html):
    cells = [label_doc(doc, units), doc] + [alone_doc(doc, u) for u in units]
    mounts = "".join('<div class=m id="m%d"></div>' % i for i in range(len(cells)))
    js = "".join('lottie.loadAnimation({container:document.getElementById("m%d"),renderer:"svg",loop:false,'
                 'autoplay:false,animationData:D[%d]}).goToAndStop(%d,true);' % (i, i, frame)
                 for i in range(len(cells)))
    data = json.dumps(cells, separators=(",", ":")).replace("\\", "\\\\").replace("</", "<\\/")
    html = ('<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:transparent}'
            '.g{display:grid;grid-template-columns:repeat(%d,%dpx)}.m{width:%dpx;height:%dpx}'
            '.m svg{shape-rendering:crispEdges}</style><div class=g>%s</div>'
            '<script src="file://%s/avatar-lab/lottie_light.min.js"></script>'
            '<script>var D=%s;%s</script>') % (LOOK_COLS, LOOK_PX, LOOK_PX, LOOK_PX, mounts, HERE, data, js)
    open(out_html, "w").write(html)
    return len(cells)

def look_shoot(html, png, cells, tries=3):
    """Chromium drops a page now and then under load, and a missing render used to fall back to a
    guess in silence. Retry, then say so."""
    rows = (cells + LOOK_COLS - 1) // LOOK_COLS
    for n in range(tries):
        try:
            if os.path.exists(png): os.remove(png)
        except OSError:
            pass
        try:
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--default-background-color=00000000", "--force-color-profile=srgb",
                            "--force-device-scale-factor=1", "--virtual-time-budget=25000",
                            "--window-size=%d,%d" % (LOOK_COLS * LOOK_PX, rows * LOOK_PX),
                            "--user-data-dir=" + tempfile.mkdtemp(),
                            "--screenshot=" + png, "file://" + html],
                           capture_output=True, timeout=600)
        except subprocess.TimeoutExpired:
            continue
        if os.path.exists(png) and os.path.getsize(png) > 1000: return
    raise Unsupported("the render page did not come back after %d tries" % tries)

# ---------------------------------------------------------------- the generator's own rules

def _lin(v): return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def lab3(r, g, b):
    r, g, b = _lin(r), _lin(g), _lin(b)
    X = (0.4124*r + 0.3576*g + 0.1805*b) / 0.95047
    Y = 0.2126*r + 0.7152*g + 0.0722*b
    Z = (0.0193*r + 0.1192*g + 0.9505*b) / 1.08883
    t = lambda v: v ** (1/3) if v > 0.008856 else 7.787*v + 16/116
    return (116*t(Y) - 16, math.hypot(500*(t(X)-t(Y)), 200*(t(Y)-t(Z))),
            math.degrees(math.atan2(200*(t(Y)-t(Z)), 500*(t(X)-t(Y)))) % 360)

def dE3(a, b):
    La, Ca, Ha = a; Lb, Cb, Hb = b
    aa, ab = Ca*math.cos(math.radians(Ha)), Ca*math.sin(math.radians(Ha))
    ba, bb = Cb*math.cos(math.radians(Hb)), Cb*math.sin(math.radians(Hb))
    return math.sqrt((La-Lb)**2 + (aa-ba)**2 + (ab-bb)**2)

def one_step(A, B):
    k = [b/a for a, b in zip(A, B) if a >= 24]
    if len(k) >= 2 and max(k)-min(k) <= SPREAD and K_LO <= sum(k)/len(k) <= K_HI: return True
    t = [(a-b)/(255-b) for a, b in zip(A, B) if b <= 231]
    return len(t) >= 2 and max(t)-min(t) <= SPREAD and T_LO <= sum(t)/len(t) <= T_HI

def same_material(ca, cb, ra, rb):
    La, Ca, _ = ca; Lb, Cb, _ = cb
    ga, gb = Ca < T_GREY, Cb < T_GREY
    if ga and gb: return abs(La-Lb) <= T_GREY_L
    if ga != gb: return False
    if dE3(ca, cb) < 3: return True
    A, B = (ra, rb) if sum(ra) >= sum(rb) else (rb, ra)
    return one_step(A, B)

def owns(a, b, a_on_top):
    La, Ca, _ = a; Lb, Cb, _ = b
    ga, gb = Ca < T_GREY, Cb < T_GREY
    if ga != gb: return La < Lb
    if abs(La-Lb) > T_L: return La < Lb
    if abs(Ca-Cb) > T_C: return Ca > Cb
    return a_on_top

def analyse_look(png, units):
    """The generator's own analysis, run on the animation's render.

    Returns one record per unit: the colour it is SEEN in, its size, and its outline cut into runs
    of one decision each, exactly as `decisions.json` records them for the SVGs, except that the
    neighbour a run names is a Lottie unit and not an SVG element."""
    im = np.asarray(Image.open(png).convert("RGBA")).astype(int)
    N = len(units)
    def cell(n):
        r, c = divmod(n, LOOK_COLS)
        return im[r*LOOK_PX:(r+1)*LOOK_PX, c*LOOK_PX:(c+1)*LOOK_PX]
    lm, real = cell(0), cell(1)
    label = decode_labels(lm)
    bad = (lm[..., 3] > 0) & ((label < 0) | (label >= N))
    label[bad] = -2
    for _ in range(3):                          # anti-aliased seams take a neighbour's label
        ys, xs = np.nonzero(label == -2)
        if not len(ys): break
        for y, x in zip(ys, xs):
            nb = label[max(0, y-1):y+2, max(0, x-1):x+2].ravel(); nb = nb[nb >= 0]
            if len(nb): label[y, x] = np.bincount(nb).argmax()
    label[label == -2] = -1
    masks = [cell(2+i)[..., 3] > 0 for i in range(N)]

    colour, seen, dim, area = {}, {}, {}, {}
    for i in range(N):
        ys, xs = np.nonzero(masks[i])
        dim[i] = (max(xs.max()-xs.min(), ys.max()-ys.min()) + 1)/LOOK_S if len(xs) else 0
        area[i] = float(masks[i].sum())/(LOOK_S*LOOK_S)
        vis = label == i
        if vis.sum() < 4: continue
        er = vis & np.roll(vis,1,0) & np.roll(vis,-1,0) & np.roll(vis,1,1) & np.roll(vis,-1,1)
        px = real[er if er.sum() >= 4 else vis]
        med = np.median(px[:, :3], axis=0)/255
        colour[i] = lab3(*med); seen[i] = tuple(float(v)*255 for v in med)

    ring, bb, cy = {}, {}, {}
    for i in range(N):
        v = label == i
        if v.any():
            out = (np.roll(v,1,0) | np.roll(v,-1,0) | np.roll(v,1,1) | np.roll(v,-1,1)) & ~v
            n = float(out.sum()); nb = label[out]; nb = nb[nb >= 0]
            c = np.bincount(nb, minlength=N).astype(float) if (n and nb.size) else None
            ring[i] = {int(j): c[j]/n for j in np.nonzero(c)[0]} if c is not None else {}
        else:
            ring[i] = {}
        ys, xs = np.nonzero(masks[i])
        if len(ys): bb[i] = (ys.min(), ys.max()); cy[i] = float(ys.mean())

    def mouth_of(i):
        if i not in colour or i not in cy: return None
        r = ring.get(i, {})
        if not r: return None
        j, share = max(r.items(), key=lambda kv: kv[1])
        if share < MOUTH_RING or j not in colour or j not in bb: return None
        if area[i] > MOUTH_AREA*area[j]: return None
        y0, y1 = bb[j]
        if cy[i] < (y0+y1)/2: return None
        if colour[i][0] >= PALE_L or colour[i][0] <= colour[j][0] - MOUTH_L: return j
        return None

    def one_material(i, j):
        if same_material(colour[i], colour[j], seen[i], seen[j]): return True
        if mouth_of(i) == j or mouth_of(j) == i: return False
        for a, b in ((i, j), (j, i)):
            if not (colour[a][0] >= PALE_L and colour[a][1] < T_GREY): continue
            if area[a] >= MARK_AREA*area[b]: continue
            if ring.get(a, {}).get(b, 0) >= MARK_RING: return True
            if colour[b][0] >= LIGHT_L and dE3(colour[a], colour[b]) < MARK_DE: return True
        return False

    def is_part(i):
        u = units[i]
        if not u["fill"] or i not in colour: return False
        if u["fill_opacity"] not in (None, 100): return False
        if u.get("group_opacity", 1) < 0.99 or (u.get("layer_opacity") or 100) < 99.5: return False
        if lum(u["fill"]) < 0.03 and not (dim[i] >= INK_DIM and area[i] >= INK_AREA): return False
        return dim[i] >= MIN_DIM or (dim[i] >= 6 and colour[i][0] > 92)

    def material(i):
        if i < 0 or i not in colour: return None
        u = units[i]
        if not u["fill"] and not u["stroke"]: return None
        if dim[i] < 6: return None
        return colour[i]

    out = {}
    for i in range(N):
        rec = {"fill": units[i]["fill"], "dim": round(dim[i], 1), "area": round(area[i], 1),
               "colour": [round(c, 1) for c in colour.get(i, (0, 0, 0))],
               "part": bool(is_part(i)), "mouth": False, "runs": []}
        out[i] = rec
        if not rec["part"]: continue
        rec["mouth"] = bool(mouth_of(i) is not None)
        runs = []
        for cont in skm.find_contours(masks[i].astype(float), 0.5):
            if len(cont) < 6: continue
            dec = []
            for y, x in cont:
                y0, x0 = int(math.floor(y)), int(math.floor(x))
                y1, x1 = min(LOOK_PX-1, int(math.ceil(y))), min(LOOK_PX-1, int(math.ceil(x)))
                cand = {(y0, x0), (y0, x1), (y1, x0), (y1, x1)}
                ins = [c for c in cand if masks[i][c]]; outs = [c for c in cand if not masks[i][c]]
                if not ins or not outs: dec.append("hidden"); continue
                if not any(label[c] == i for c in ins): dec.append("hidden"); continue
                nbs = [label[c] for c in outs]; nb = max(set(nbs), key=nbs.count)
                m = material(nb)
                if m is None: dec.append("in@bg"); continue
                if one_material(i, nb): dec.append("none@%d" % nb); continue
                if min(colour[i][0], m[0]) < DARK_L and dE3(colour[i], m) > FAR:
                    dec.append("far@%d" % nb); continue
                if owns(colour[i], m, i > nb): dec.append("in@%d" % nb); continue
                dec.append(("out:%d" % nb) if any(masks[nb][c] for c in ins) else "none@%d" % nb)
            r = []
            for k, v in enumerate(dec):
                if r and r[-1][0] == v: r[-1][2] = k+1
                else: r.append([v, k, k+1])
            def run_units(rr):
                return sum(np.hypot(*(cont[k+1]-cont[k])) for k in range(rr[1], min(rr[2], len(cont))-1))/LOOK_S
            for _ in range(4):
                changed = False; k = 0
                while k < len(r) and len(r) > 1:
                    if run_units(r[k]) < MIN_RUN:
                        prev = r[k-1] if k > 0 else None
                        nxt = r[k+1] if k+1 < len(r) else None
                        target = prev if (prev and (not nxt or run_units(prev) >= run_units(nxt))) else nxt
                        if target is prev: prev[2] = r[k][2]
                        else: nxt[1] = r[k][1]
                        del r[k]; changed = True; continue
                    k += 1
                if not changed: break
            for v, a, b in r:
                if b - a < 2: continue
                runs.append([v, round(float(run_units([v, a, b])), 1)])
        rec["runs"] = runs
    return out

def look_frames(doc, n=3):
    """the frames to read the drawing at.

    One frame is not enough: a shape the hand covers at the middle of a think is hidden there and
    would lose its line for the whole clip. The runs are summed over these, so a stretch of outline
    that the shape owns at any of them counts."""
    ip, op = int(doc.get("ip", 0)), int(doc.get("op", 60))
    if op <= ip: return [ip]
    return sorted(set(int(round(ip + (op - ip) * i / (n - 1) * 0.98)) for i in range(n)))

def look_at(doc, stem, frames=None, keep=False):
    """render the animation the way the generator renders an SVG, at each frame, and read it"""
    os.makedirs(LOOK_TMP, exist_ok=True)
    if frames is None: frames = look_frames(doc)
    if isinstance(frames, int): frames = [frames]
    units = lottie_units(doc, float(frames[0]))
    merged = None
    for fr in frames:
        html = os.path.join(LOOK_TMP, "%s_%d.html" % (stem, fr))
        png = os.path.join(LOOK_TMP, "%s_%d.png" % (stem, fr))
        n = look_page(doc, units, fr, html)
        look_shoot(html, png, n)
        if not os.path.exists(png): raise Unsupported("the render page did not come back")
        rec = analyse_look(png, units)
        if not keep:
            for f in (html, png):
                try: os.remove(f)
                except OSError: pass
        if merged is None:
            merged = {i: dict(r, runs=list(r["runs"])) for i, r in rec.items()}
            continue
        for i, r in rec.items():
            m = merged[i]
            m["part"] = m["part"] or r["part"]
            m["mouth"] = m["mouth"] or r["mouth"]
            m["dim"] = max(m["dim"], r["dim"]); m["area"] = max(m["area"], r["area"])
            if r["area"] > 0 and not m["colour"][0]: m["colour"] = r["colour"]
            # the frame where this shape shows the most of its own outline, not the sum: a shape
            # that a hand covers at two frames of three would otherwise read as hidden all through
            if _seen_outline(r["runs"]) > _seen_outline(m["runs"]): m["runs"] = list(r["runs"])
    return units, merged

def _seen_outline(runs):
    return sum(ln for tag, ln in runs if tag != "hidden")

def look_all(doc, stem):
    """{uid: what the render says about this shape}: whether it owns an inside line, whether it is
    a mouth, and which shape its line would be cut by or banded onto. The neighbours are Lottie
    shapes, which is the whole point: the still names its neighbours as SVG elements and carrying
    those across the match puts the band in the wrong place."""
    units, rec = look_at(doc, stem)
    out = {}
    for i, u in enumerate(units):
        r = rec.get(i)
        if not r: continue
        t = collections.Counter(); nb = collections.defaultdict(collections.Counter)
        for tag, ln in r["runs"]:
            kind = tag.split("@")[0].split(":")[0]
            t[kind] += ln
            who = tag.partition("@")[2] or (tag.split(":")[1] if tag.startswith("out:") else "")
            if who and who != "bg": nb[int(who)][kind] += ln
        cut = top_neighbour(dict(nb), "none")[0]
        band = top_neighbour(dict(nb), "out")[0]
        out[u["uid"]] = {"part": bool(r["part"]), "mouth": bool(r["mouth"]), "in": t["in"], "out": t["out"],
                         "none": t["none"],
                         "cut": units[cut]["uid"] if cut is not None else None,
                         "band": units[band]["uid"] if band is not None else None}
    return out

def look_unmatched(doc, stem, rows):
    """{uid: (stroke it, is it a mouth)} for the shapes the still could not be matched to.

    The size rule these otherwise fall back on is right 53 to 64% of the time. Reading the drawing
    itself is right by construction: it says what lies around the shape, so the generator's own
    material and ownership rules apply, and the answer is about the animation and not about a still
    that may not hold this shape at all."""
    want = {uid for uid, part, _m in rows if part is None}
    if not want: return {}
    try:
        units, rec = look_at(doc, stem)
    except Exception:
        return {}
    out = {}
    for i, u in enumerate(units):
        if u["uid"] not in want: continue
        r = rec.get(i)
        if not r or not r["part"]:
            out[u["uid"]] = (False, False); continue
        t = collections.Counter()
        for tag, ln in r["runs"]: t[tag.split("@")[0].split(":")[0]] += ln
        out[u["uid"]] = (t["in"] > 0 and t["in"] >= t["none"], r["mouth"])
    return out


# ---------------------------------------------------------------- the pass over one file

def border_file(doc, svg_name, stats=None):
    """add the border to a loaded animation, in place. Returns the per-unit audit."""
    stats = collections.Counter() if stats is None else stats
    frames = frame_grid(doc)
    by_ind = {L.get("ind"): L for L in doc["layers"]}
    layers = doc["layers"]
    t0 = frames[len(frames)//2]
    if LOOK == "1":
        # the animation is rendered and read the way the generator reads an SVG, so every
        # neighbour a run names is a Lottie shape and the answer is about this drawing, not the still
        units, rec = look_at(doc, svg_name, look_frames(doc))
        seq = [{"meta": u, "ar": [0.0], "bb": [u["bbox"]]} for u in units]
        ent = {u["uid"]: e for u, e in zip(units, seq)}
        unit_of_part = {i: u["uid"] for i, u in enumerate(units)}
        rows, flags, runs, area_of = [], {}, {}, {}
        for i, u in enumerate(units):
            r = rec[i]
            t = collections.Counter(); nb = collections.defaultdict(collections.Counter)
            for tag, ln in r["runs"]:
                kind = tag.split("@")[0].split(":")[0]
                t[kind] += ln
                who = tag.partition("@")[2] or (tag.split(":")[1] if tag.startswith("out:") else "")
                if who and who != "bg": nb[int(who)][kind] += ln
            runs[i] = (t["in"], t["out"], t["none"], t["far"], dict(nb))
            area_of[i] = r["area"]
            if r["part"] and (t["in"] > 0 or t["out"] > 0):
                flags[i] = {"inner": t["in"] > 0, "outer": t["out"] > 0, "mouth": r["mouth"]}
            rows.append((u["uid"], i, "looked"))
        stats["looked-at"] += len(units)
    else:
        parts = svg_parts(svg_name)
        flags, runs, shared = share_duplicates(parts, v9_flags(svg_name), part_runs(svg_name))
        stats["decisions-shared-with-a-twin"] += shared
        area_of = {p["i"]: p["area"] for p in parts}
        rows, seq, off = match_units(doc, svg_name, parts, frames)
        ent = {e["meta"]["uid"]: e for e in seq}
        unit_of_part = {}
        for (uid, part, _m) in rows:
            if part is not None and part not in unit_of_part: unit_of_part[part] = uid
        seen = {}
        if LOOK == "2":
            try:
                seen = look_all(doc, svg_name)
            except Exception as ex:
                stats["THE RENDER FAILED"] += 1
                print("look failed on %s: %s" % (svg_name, ex), file=sys.stderr)
        if LOOK == "2" and any(p is None for _u, p, _m in rows):
            # a shape the still cannot reach is guessed at by size, which is right about three
            # times in five. Render the animation and read that shape the way the generator reads
            # an SVG instead: it knows what lies around it, so it can answer properly.
            look = {u: (v["part"] and v["in"] > 0 and v["in"] >= v["none"], v["mouth"])
                    for u, v in seen.items()}
            stats["read-off-the-render"] += sum(1 for _u, p, _m in rows if p is None)
        else:
            look = {}

    # a shape that the still and the animation both hold twice: when only one copy was matched,
    # the other is the same piece of drawing and takes the same answer
    twin = {}
    matched = [(uid, p) for uid, p, _m in rows if p is not None]
    for uid, part, _m in rows:
        if not DO_TWIN: break
        if part is not None: continue
        a = ent[uid]["meta"]
        if not a["bbox"] or not a["fill"]: continue
        for uid2, p2 in matched:
            b = ent[uid2]["meta"]
            if b["fill"] != a["fill"] or not b["bbox"]: continue
            if max(abs(x - y) for x, y in zip(a["bbox"], b["bbox"])) > 1.5: continue
            twin[uid] = p2; break

    decided = {}
    for (uid, part, method) in rows:
        e = ent[uid]; meta = e["meta"]
        if part is None and uid in twin:
            part, method = twin[uid], "same shape as a matched twin"
        if part is None and uid in look:
            want, mouth = look[uid]
            cut, band_to = None, None
            method = "read off the render" if want else "the render says it owns no line"
        elif part is None:
            want = intrinsic_is_part(meta, e["ar"], e["bb"])
            mouth, cut, band_to = False, None, None
            method = "intrinsic" if want else "intrinsic-skip"
        else:
            f = flags.get(part)
            want = bool(f)
            mouth = bool(f and f["mouth"])
            inner, band, bare, _far, nb = runs.get(part, (1.0, 0.0, 0.0, 0.0, {}))
            cut = top_neighbour(nb, "none")[0] if bare > 0 else None
            band_to = top_neighbour(nb, "out")[0] if band > BAND_RATIO * bare else None
            if band_to is not None and uid in seen and seen[uid]["band"]:
                band_to = seen[uid]["band"]        # a uid, not an SVG part: matte_for takes both
            if want and not mouth:
                # the mouth is exempt: v9 draws two thirds of the mouth lines as a band onto the
                # face, and the smile is the one place the border is meant to be seen
                if inner <= 0 and not (DO_BAND and band_to is not None):
                    want = False
                    method = "the still draws this line outside the shape"
                elif inner > 0 and inner < bare and not (DO_CUT and cut is not None and cut in unit_of_part):
                    want = False
                    method = "mostly not its line"
        decided[uid] = {"part": part, "method": method, "want": want, "mouth": mouth,
                        "cut": cut, "band_to": band_to,
                        "fill": meta["fill"], "gpath": meta["gpath"], "layer": meta["layer_idx"]}

    next_ind = max((L.get("ind", 0) for L in layers), default=0)
    before = collections.defaultdict(list)
    extra = []
    mattes = {}
    audit = {}

    def matte_for(part_index):
        """a hidden copy of a neighbouring shape, so a line can be cut by it or clipped onto it"""
        nonlocal next_ind
        uid = part_index if isinstance(part_index, str) else unit_of_part.get(part_index)
        if uid is None or uid not in ent: return None
        if uid in mattes: return mattes[uid]
        m = ent[uid]["meta"]
        L = layers[m["layer_idx"]]
        if L.get("td") or layer_has_modifier(L) or m["deep"]: 
            mattes[uid] = None; return None
        try:
            items, _c = _descend(L.get("shapes", []), m["gpath"])
            geoms = [x for x in items if x.get("ty") in GEOM]
            fl = [x for x in items if x.get("ty") == "fl"]
            if not geoms or not fl:
                mattes[uid] = None; return None
            next_ind += 1
            md = make_matte(L, m["gpath"], geoms, fl[0], next_ind)
            md["nm"] = "ab-nbr"
            extra.append(md)
            mattes[uid] = md["ind"]
            return md["ind"]
        except Unsupported:
            mattes[uid] = None; return None

    for e in seq:
        meta = e["meta"]
        uid = meta["uid"]
        d = decided[uid]
        if not d["want"]:
            stats["skip-not-a-part"] += 1
            audit[uid] = dict(d, done=None, why="not a part")
            continue
        layer = layers[meta["layer_idx"]]
        if layer.get("td"):
            stats["skip-matte-source"] += 1
            audit[uid] = dict(d, done=None, why="matte source, never drawn")
            continue
        if not meta["fill"]:
            stats["skip-no-fill"] += 1
            audit[uid] = dict(d, done=None, why="no fill")
            continue
        if layer_has_modifier(layer):
            stats["skip-modifier"] += 1
            audit[uid] = dict(d, done=None, why="shape modifier on the layer")
            continue
        gpath = meta["gpath"]
        try:
            items, _chain = _descend(layer.get("shapes", []), gpath)
            geoms, keep = outer_geoms(items, t0)
            if meta["deep"]:
                stats["skip-deep"] += 1
                audit[uid] = dict(d, done=None, why="the style paints geometry in nested groups")
                continue
            if not keep:
                stats["skip-no-geometry"] += 1
                audit[uid] = dict(d, done=None, why="no outer path")
                continue
            fills = [x for x in items if x.get("ty") == "fl"]
            if not fills:
                stats["skip-no-fill-item"] += 1
                audit[uid] = dict(d, done=None, why="no fill item at this level")
                continue
            k = 1.0
            part = d["part"]
            if part in runs and area_of.get(part):
                visible = sum(runs[part][:4])
                if visible > 0:
                    minor = 2.0 * area_of[part] / visible        # the width of the strip, roughly
                    k = min(1.0, 0.7 * minor / W_UNITS)          # the inset keeps under 35% of it
            wprop, w = width_prop(unit_scales(doc, layer, gpath, by_ind), k)
            if k < 1.0: stats["thinned-on-a-narrow-shape"] += 1
            if wprop.get("a"): stats["width-follows-the-scale"] += 1
            op = MOUTH_OP if d["mouth"] else OP
            mask = inv_mask = None
            if len(keep) == 1:
                try:
                    GM = group_matrix_to_layer(layer.get("shapes", []), gpath, t0)
                    mask = mask_from(keep[0], GM, t0)
                    inv_mask = mask_from(keep[0], GM, t0, inv=True)
                except Unsupported:
                    mask = inv_mask = None
            made = []
            inner = runs.get(part, (1.0,))[0] if part in runs else 1.0
            free = not layer.get("tt")          # the track matte slot, if the layer is not matted
            if mask is not None:
                if inner > 0 or d["mouth"]:
                    cut_ind = matte_for(d["cut"]) if (DO_CUT and free and d["cut"] is not None) else None
                    tp = cut_ind if cut_ind is not None else (layer.get("tp") if layer.get("tt") else None)
                    next_ind += 1
                    made.append(make_line(layer, gpath, keep, op, wprop, mask, tp, next_ind,
                                          tt=2 if cut_ind is not None else 1))
                    stats["self-mask"] += 1
                    if cut_ind is not None: stats["cut-by-its-neighbour"] += 1
                if DO_BAND and free and inv_mask is not None and d["band_to"] is not None:
                    onto = matte_for(d["band_to"])
                    if onto is not None:
                        next_ind += 1
                        made.append(make_line(layer, gpath, keep, op, wprop, inv_mask, onto, next_ind,
                                              tt=1, nm="ab-band"))
                        stats["band-onto-the-piece-below"] += 1
                if not made:
                    stats["skip-nothing-to-draw"] += 1
                    audit[uid] = dict(d, done=None, why="nothing left to draw")
                    continue
                before[meta["layer_idx"]].append((gpath, made))
                audit[uid] = dict(d, done="self-mask", w=round(w, 3), op=op,
                                  band=any(x["nm"] == "ab-band" for x in made),
                                  cut=bool(d["cut"] is not None and any(x.get("tt") == 2 for x in made)))
            else:
                if layer.get("tt"):
                    stats["skip-matted-pair"] += 1
                    audit[uid] = dict(d, done=None, why="a matted unit that cannot be written as a mask")
                    continue
                next_ind += 1
                mat = make_matte(layer, gpath, geoms, fills[0], next_ind)
                next_ind += 1
                line = make_line(layer, gpath, keep, op, wprop, None, mat["ind"], next_ind)
                before[meta["layer_idx"]].append((gpath, [line, mat]))
                stats["matte-pair"] += 1
                audit[uid] = dict(d, done="matte-pair", w=round(w, 3), op=op)
        except Unsupported as ex:
            stats["skip-unsupported"] += 1
            audit[uid] = dict(d, done=None, why=str(ex))

    out = []
    for i, L in enumerate(layers):
        groups = before.get(i)
        if not groups:
            out.append(L); continue
        rebuilt = None
        if not L.get("td"):
            rebuilt, next_ind = rebuild_layer(L, groups, next_ind)
        if not rebuilt:
            for _gp, ls in groups: out += ls
            out.append(L)
            stats["layers-kept-whole"] += 1
            continue
        out += rebuilt
        stats["layers-cut"] += 1
        stats["pieces"] += sum(1 for x in rebuilt if x.get("nm") not in ("ab-line", "ab-matte"))
    doc["layers"] = out + extra
    return audit, stats


# ---------------------------------------------------------------- validation

def validate(doc):
    L = doc["layers"]
    errs = []
    inds = [x.get("ind") for x in L]
    dup = [k for k, v in collections.Counter(inds).items() if v > 1]
    if dup: errs.append("duplicate ind %s" % dup)
    by = {x.get("ind"): x for x in L}
    for x in L:
        if x.get("tt") and x.get("td"): errs.append("ind %s has both tt and td" % x.get("ind"))
        if x.get("tt"):
            if "tp" not in x: errs.append("ind %s has tt and no tp" % x.get("ind"))
            else:
                m = by.get(x["tp"])
                if m is None: errs.append("ind %s tp=%s dangling" % (x.get("ind"), x["tp"]))
                elif not m.get("td"): errs.append("ind %s tp=%s is not a matte source" % (x.get("ind"), x["tp"]))
        if x.get("parent") is not None and x["parent"] not in by:
            errs.append("ind %s parent %s missing" % (x.get("ind"), x["parent"]))
        mp = x.get("masksProperties") or []
        if x.get("hasMask") and not mp: errs.append("ind %s hasMask with no mask" % x.get("ind"))
        if len([m for m in mp if m["mode"] == "a"]) > 1:
            errs.append("ind %s has more than one additive mask" % x.get("ind"))
        for m in mp:
            if m["o"]["k"] != 100 or m["x"]["k"] != 0:
                errs.append("ind %s mask would force a <mask> element" % x.get("ind"))
    return errs


# ---------------------------------------------------------------- the driver

def js_wrap(name, doc):
    body = json.dumps(doc, separators=(",", ":"))
    body = body.replace("\\", "\\\\").replace("</", "<\\/")
    return 'window.AB_LOTTIE=window.AB_LOTTIE||{};window.AB_LOTTIE["%s"]=%s;\n' % (name, body)

SHAPE_DROP = ("ix", "mn", "ln", "cl", "np", "cix", "nm", "bm")

def slim(o):
    """the lab copy: the same drawing, 16% smaller on disk, and pixel for pixel the same.

    Only the author-time keys After Effects writes on shape items go: `ix`, `mn`, `nm`, `bm`, and
    `hd` where it is false. The player reads none of them (checked by render: 0 differing pixels).
    Layers keep everything, since the lab reads their `nm` to strip the border back off for the
    plain option and resolves mattes and parents through `ind`. Rounding the numbers would take
    another 5% and was dropped: it moves every edge by a fraction of a pixel, and rounding a colour
    channel moves a whole face by a level or two."""
    if isinstance(o, list): return [slim(x) for x in o]
    if isinstance(o, dict):
        keep_all = isinstance(o.get("ty"), int) or "layers" in o     # a layer, or the comp itself
        return {k: slim(v) for k, v in o.items()
                if not (not keep_all and k in SHAPE_DROP) and not (k == "hd" and v is False)}
    return o

def run_one(args):
    stem, out_dir, want_js = args
    src = os.path.join(LOT, stem + ".json")
    doc = json.load(open(src))
    audit, stats = border_file(doc, stem)
    errs = validate(doc)
    dst = os.path.join(out_dir, stem + ".json")
    json.dump(doc, open(dst, "w"), separators=(",", ":"))
    if want_js:
        jsdir = os.path.join(out_dir, "js")
        open(os.path.join(jsdir, stem + ".js"), "w").write(js_wrap(stem, slim(doc)))
    return stem, dict(stats), errs, os.path.getsize(src), os.path.getsize(dst), audit


def main(argv):
    global OUT
    args = argv[1:]
    want_js = "--js" in args
    jobs = 8
    limit = None
    for a in args:
        if a.startswith("--out="): OUT = os.path.join(HERE, "game-assets", a.split("=", 1)[1])
        if a.startswith("--jobs="): jobs = int(a.split("=", 1)[1])
        if a.startswith("--limit="): limit = int(a.split("=", 1)[1])
    names = [a for a in args if not a.startswith("--")]
    stems = sorted(f[:-5] for f in os.listdir(LOT) if f.endswith(".json"))
    if names:
        keep = set(names)
        stems = [s for s in stems if s in keep or s.rsplit("_", 1)[0] in keep]
    if limit: stems = stems[:limit]
    os.makedirs(OUT, exist_ok=True)
    if want_js: os.makedirs(os.path.join(OUT, "js"), exist_ok=True)

    total = collections.Counter()
    audits = {}
    bad = []
    raw_in = raw_out = 0
    payload = [(s, OUT, want_js) for s in stems]
    if jobs > 1 and len(stems) > 1:
        with ProcessPoolExecutor(jobs) as ex:
            results = list(ex.map(run_one, payload, chunksize=4))
    else:
        results = [run_one(p) for p in payload]
    for stem, stats, errs, a, b, audit in results:
        total.update(stats)
        audits[stem] = audit
        raw_in += a; raw_out += b
        if errs: bad.append((stem, errs))
    json.dump(audits, open(os.path.join(OUT, "borders.json"), "w"))
    print("files %d   raw %.1f -> %.1f MB" % (len(stems), raw_in/1048576, raw_out/1048576))
    for k in sorted(total): print("  %-24s %d" % (k, total[k]))
    if bad:
        print("STRUCTURE ERRORS in %d files" % len(bad))
        for s, e in bad[:10]: print("  %s: %s" % (s, e[:3]))
    else:
        print("  structure                validated clean")


if __name__ == "__main__":
    main(sys.argv)
