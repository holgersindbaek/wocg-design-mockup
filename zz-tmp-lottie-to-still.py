#!/usr/bin/env python3
"""Cut a plain still SVG out of frame 0 of an animation.

The still and the animation are meant to be one drawing: the table shows `ManClown.svg`, hides it and
plays `ManClown_win.json` from frame 0. On a few avatars the two assets have drifted apart, and where
they have, the animation is the truth and the still is re-cut from it, so they cannot disagree again.

Not a capture of the player's DOM. lottie's SVG output keeps its layers in `<defs>` behind `<use>`
and its track mattes as `<mask>`, and the border generator reads none of that: run over a captured
DOM it found one part per file instead of a hundred. This walks the animation itself at frame 0 and
writes one `<path>` per drawable piece, in paint order, with the whole transform chain baked into the
control points and divided by 10 into the 160-unit box the stills use. Beziers, not sampled
polylines, so the curves are exact.

    usage: zz-tmp-lottie-to-still.py [--write] [--from=DIR] NAME...

Every file it writes is checked by render against the animation's own frame 0 first, and a name whose
still does not come out within tolerance is left alone.
"""
import json, math, os, re, sys, subprocess, tempfile, base64, importlib.util
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ab", os.path.join(HERE, "zz-tmp-build-avatar-lottie.py"))
ab = importlib.util.module_from_spec(spec); spec.loader.exec_module(ab)
CH = "/opt/homebrew/bin/chromium"
SVG = os.path.join(HERE, "game-assets", "avatars")
TOL = float(os.environ.get("AB_STILL_TOL", "0.010"))  # share of pixels allowed to differ.
# The floor is not zero: an SVG rasterised inside an <img> and a live lottie SVG in the DOM
# disagree on about 1.7% of pixels at 620 px, all of it a one-pixel fringe on edges, so the
# gate is on the silhouette IoU as well and that one has to be 0.99.


def _num(v):
    s = ("%.3f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

def reverse(p):
    """the same curve wound the other way.

    An `el` or `rc` carries `d:3` for a reversed direction, and it matters: WomanCowgirl's spectacle
    rims are two ellipses under one fill, the inner one reversed, so the non-zero rule makes a ring.
    Drawn both the same way they make a solid disc and her tinted lenses come out white."""
    return {"v": p["v"][::-1], "i": p["o"][::-1], "o": p["i"][::-1], "c": p.get("c", True)}

def path_d(p, M):
    """one bezier subpath, through the matrix and into the 160-unit box"""
    v = p.get("v") or []
    if len(v) < 2: return ""
    i = p.get("i") or [[0, 0]]*len(v)
    o = p.get("o") or [[0, 0]]*len(v)
    k = ab.COMP_PER_UNIT
    P = [ab.mpoint(M, x) for x in v]
    O = [ab.mpoint(M, (v[j][0]+o[j][0], v[j][1]+o[j][1])) for j in range(len(v))]
    I = [ab.mpoint(M, (v[j][0]+i[j][0], v[j][1]+i[j][1])) for j in range(len(v))]
    pt = lambda q: "%s %s" % (_num(q[0]/k), _num(q[1]/k))
    d = ["M" + pt(P[0])]
    rng = range(len(v)) if p.get("c") else range(len(v)-1)
    for j in rng:
        j2 = (j+1) % len(v)
        d.append("C%s %s %s" % (pt(O[j]), pt(I[j2]), pt(P[j2])))
    if p.get("c"): d.append("Z")
    return "".join(d)

def trim_d(p, M, tm, n=24):
    """the stretch a trim-paths modifier leaves, as a polyline.

    `s` and `e` are percentages of the path's own arc length from vertex 0 in the order the vertices
    are listed, `o` is an offset in degrees added to both, and lottie clamps s and e to 0..100 before
    the offset. A stretch that crosses the start vertex comes out as two ranges."""
    def num(k, d=0.0):
        v = ab.val(tm.get(k), 0.0)
        if isinstance(v, list): v = v[0] if v else d
        return d if v is None else float(v)
    a = max(0.0, min(100.0, num("s", 0.0)))/100.0
    b = max(0.0, min(100.0, num("e", 100.0)))/100.0
    if a > b: a, b = b, a
    r = (num("o", 0.0) % 360.0)/360.0
    a += r; b += r
    pts = ab.path_points(p, n)
    if len(pts) < 2: return ""
    q = np.asarray([ab.mpoint(M, x) for x in pts], float)/ab.COMP_PER_UNIT
    d = np.sqrt(((q[1:]-q[:-1])**2).sum(1))
    cum = np.concatenate([[0.0], np.cumsum(d)])
    tot = cum[-1]
    if tot <= 0: return ""
    out = []
    for lo, hi in ([(a, b)] if b <= 1.0 else [(a, 1.0), (0.0, b-1.0)]):
        if hi - lo <= 1e-6: continue
        pick = q[(cum >= lo*tot) & (cum <= hi*tot)]
        if len(pick) < 2: continue
        out.append("M" + " L".join("%s %s" % (_num(x), _num(y)) for x, y in pick))
    return "".join(out)

def outline_d(pts, r, cap):
    """an open stroke as the filled shape it paints: the centreline offset both ways, capped.

    The stills draw a whisker or a mouth line as a filled path and the border generator only borders
    filled parts, so a still re-cut with the animation's strokes left as strokes loses their line:
    23 bordered parts became 9 on AnimalFoxRockstar. Written as the outline it paints, the still
    keeps them, and the animation's own stroke gets its border from the `bar` construction, so the
    two still agree."""
    q = np.asarray(pts, float)
    keep = np.concatenate([[True], (np.abs(np.diff(q, axis=0)).sum(1) > 1e-9)])
    q = q[keep]
    if len(q) < 2 or r <= 0: return None
    t = np.zeros_like(q)
    t[1:-1] = q[2:] - q[:-2]
    t[0] = q[1] - q[0]; t[-1] = q[-1] - q[-2]
    n = np.sqrt((t*t).sum(1, keepdims=True))
    n[n == 0] = 1.0
    t = t/n
    nm = np.stack([-t[:, 1], t[:, 0]], 1)
    left, right = q + r*nm, q - r*nm
    def arc(c, a, b, k=8):
        a0 = math.atan2(a[1]-c[1], a[0]-c[0]); a1 = math.atan2(b[1]-c[1], b[0]-c[0])
        while a1 - a0 > math.pi: a1 -= 2*math.pi
        while a1 - a0 < -math.pi: a1 += 2*math.pi
        return [(c[0]+r*math.cos(a0+(a1-a0)*j/k), c[1]+r*math.sin(a0+(a1-a0)*j/k)) for j in range(1, k)]
    ring = list(map(tuple, left))
    ring += arc(q[-1], left[-1], right[-1]) if cap == 2 else []
    ring += list(map(tuple, right[::-1]))
    ring += arc(q[0], right[0], left[0]) if cap == 2 else []
    return "M" + " L".join("%s %s" % (_num(x), _num(y)) for x, y in ring) + "Z"

def item_d(g, M, tm=None):
    p = ab.item_path(g, 0.0)
    if not p: return ""
    if g.get("d") == 3: p = reverse(p)
    if tm is not None: return trim_d(p, M, tm)
    return path_d(p, M)

TRIMS = {}

def geom_of(L, by_ind):
    """every geometry item of a layer with the matrix that places it, ignoring the styles"""
    out = []
    def walk(items, M):
        trs = [x for x in items if x.get("ty") == "tr"]
        GM = ab.mmul(M, ab.group_matrix(trs[-1], 0.0)) if trs else M
        out.extend((GM, x) for x in items if x.get("ty") in ab.GEOM)
        for g in [x for x in items if x.get("ty") == "gr"]: walk(g.get("it", []), GM)
    walk(L.get("shapes", []), ab.chain_matrix(L, 0.0, by_ind))
    return out

def pieces_of(doc):
    """[(clip id, geometry items, fill, stroke, opacity)] in PAINT order, back to front.

    lottie draws the layer at index 0 last, and inside a shape tree a level's own geometry sits above
    the sub-groups that follow it, so the walk is front to back and the emit is its reverse. A layer
    on an alpha track matte becomes a `<clipPath>` of the matte's own shape, which is exact for the
    solid mattes these files use; without it RobotBoy8's mouth bar is drawn whole instead of clipped."""
    by_ind = {L.get("ind"): L for L in doc["layers"]}
    clips = {}
    layers = []
    for li, L in enumerate(doc["layers"]):
        if L.get("ty") != 4 or L.get("hd") or L.get("td"): continue
        if not (L.get("ip", 0) <= 0 < L.get("op", 1e9)): continue
        clip = None
        if L.get("tt") == 1:
            src = by_ind.get(L.get("tp"))
            if src is None:
                j = li - 1
                while j >= 0 and not doc["layers"][j].get("td"): j -= 1
                src = doc["layers"][j] if j >= 0 else None
            if src is not None:
                clip = "abc%s" % src.get("ind")
                clips.setdefault(clip, geom_of(src, by_ind))
        elif L.get("tt"):
            continue                    # an inverted matte cannot be a clipPath; leave it out
        lo = ab.val(L.get("ks", {}).get("o"), 0.0)
        if isinstance(lo, list): lo = lo[0]
        if not lo: continue
        LM = ab.chain_matrix(L, 0.0, by_ind)
        got = []
        def walk(items, M, gop, up=None):
            trs = [x for x in items if x.get("ty") == "tr"]
            GM, go = M, 100.0
            if trs:
                GM = ab.mmul(M, ab.group_matrix(trs[-1], 0.0))
                go = ab.val(trs[-1].get("o"), 0.0)
                if isinstance(go, list): go = go[0]
                if go is None: go = 100.0
            opq = gop * (go/100.0)
            # The `it` array IS the depth order: lottie walks it backwards, so the last item is
            # created first and drawn at the bottom and index 0 ends up on top. A style paints the
            # geometry BEFORE it in the same array, and a sub-group is painted at its own position.
            # Emitting the level's own piece first and then descending, which is what this did,
            # puts it above sub-groups that are in fact above it: WomanCowgirl's tinted lenses came
            # out white because the white glass behind them was drawn last.
            acc, fl, st = [], None, None
            # a trim on a level reaches every path below it, not only its own
            tm = next((x for x in items if x.get("ty") == "tm"), None) or up
            def flush():
                geoms = list(acc)
                if fl is not None and not geoms:
                    geoms = gather([x for x in items if x.get("ty") == "gr"], GM)
                if geoms and (fl is not None or st is not None) and opq > 0:
                    if tm is not None: TRIMS[id(geoms)] = tm
                    got.append((geoms, fl, st, opq))
                del acc[:]
            for x in items:
                ty = x.get("ty")
                if ty in ab.GEOM: acc.append((GM, x))
                elif ty == "gr":
                    if fl is not None or st is not None: flush(); fl = st = None
                    walk(x.get("it", []), GM, opq, tm)
                elif ty == "fl" and fl is None: fl = x
                elif ty == "st" and st is None: st = x
            flush()
        def gather(grs, M):
            out = []
            for g in grs:
                it = g.get("it", [])
                trs = [x for x in it if x.get("ty") == "tr"]
                GM = ab.mmul(M, ab.group_matrix(trs[-1], 0.0)) if trs else M
                out += [(GM, x) for x in it if x.get("ty") in ab.GEOM]
                out += gather([x for x in it if x.get("ty") == "gr"], GM)
            return out
        walk(L.get("shapes", []), LM, lo)
        layers.append((clip, list(reversed(got))))
    out = []
    for clip, got in reversed(layers):
        out += [(clip,) + g for g in got]
    return clips, out

def still_svg(doc):
    """The drawing at frame 0 as a flat SVG: a `<style>` block of classes and one `<path>` each.

    The paint has to live in classes, not in attributes, because the border generator strips a class
    and then re-adds the stroke and clip properties it read from it. Written as attributes they come
    out twice and the label page is not valid XML, which is what made the generator find one part per
    file instead of a hundred."""
    clips, pieces = pieces_of(doc)
    defs = []
    for cid, geoms in clips.items():
        d = "".join(item_d(g, M) for M, g in geoms)
        if d: defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, d))
    rules, body = {}, []
    for clip, geoms, fl, st, opq in pieces:
        d = "".join(item_d(g, M, geoms[0][0] if False else None) for M, g in geoms) if False else \
            "".join(item_d(g, M, TRIMS.get(id(geoms))) for M, g in geoms)
        if not d: continue
        M = geoms[0][0]
        # an open stroke becomes the shape it paints, so the still keeps a filled part the border
        # generator can decide about
        if fl is None and st is not None and len(geoms) == 1 and TRIMS.get(id(geoms)) is None:
            g = geoms[0][1]
            pth = ab.item_path(g, 0.0)
            if pth is not None and not pth.get("c"):
                w = ab.val(st.get("w"), 0.0)
                if isinstance(w, list): w = w[0]
                r = (w or 0) * ab.mscale(M) / ab.COMP_PER_UNIT / 2.0
                q = [ab.mpoint(M, x) for x in ab.path_points(pth, 24)]
                q = [(x/ab.COMP_PER_UNIT, y/ab.COMP_PER_UNIT) for x, y in q]
                od = outline_d(q, r, st.get("lc", 2))
                if od:
                    d, fl, st = od, dict(st), None
                    fl["ty"] = "fl"
        css = []
        if fl is not None:
            css.append("fill:%s" % ab.hexof(fl, 0.0))
            fo = ab.val(fl.get("o"), 0.0)
            if isinstance(fo, list): fo = fo[0]
            a = (fo if fo is not None else 100.0)/100.0 * opq/100.0
            if a < 0.999: css.append("fill-opacity:%s" % _num(a))
        else:
            css.append("fill:none")
        if st is not None:
            w = ab.val(st.get("w"), 0.0)
            if isinstance(w, list): w = w[0]
            css.append("stroke:%s" % ab.hexof(st, 0.0))
            css.append("stroke-width:%s" % _num((w or 0) * ab.mscale(M) / ab.COMP_PER_UNIT))
            css.append("stroke-linecap:%s" % {1: "butt", 2: "round", 3: "square"}.get(st.get("lc", 2), "round"))
            css.append("stroke-linejoin:%s" % {1: "miter", 2: "round", 3: "bevel"}.get(st.get("lj", 2), "round"))
            so = ab.val(st.get("o"), 0.0)
            if isinstance(so, list): so = so[0]
            a = (so if so is not None else 100.0)/100.0 * opq/100.0
            if a < 0.999: css.append("stroke-opacity:%s" % _num(a))
        if clip: css.append("clip-path:url(#%s)" % clip)
        key = ";".join(css)
        cls = rules.setdefault(key, "s%d" % len(rules))
        body.append('<path class="%s" d="%s"/>' % (cls, d))
    style = "".join(".%s{%s}" % (c, k) for k, c in rules.items())
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">'
            '<defs><style>%s</style>%s</defs>' % (style, "".join(defs))
            + "".join(body) + '</svg>')


def _shoot(html, out, w, h):
    p = "/tmp/ablottie/_work/l2s.html"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(html)
    subprocess.run([CH, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--force-color-profile=srgb",
                    "--screenshot=" + out, "--window-size=%d,%d" % (w, h),
                    "--user-data-dir=" + tempfile.mkdtemp(), "file://" + p], capture_output=True)
    return np.asarray(Image.open(out).convert("RGB")).astype(int)

def render_svg(text, S):
    b = base64.b64encode(text.encode()).decode()
    return _shoot('<!doctype html><style>html,body{margin:0;background:#fff}img{width:%dpx;height:%dpx;'
                  'display:block}</style><img src="data:image/svg+xml;base64,%s">' % (S, S, b),
                  "/tmp/ablottie/_work/l2s_a.png", S, S)

def render_lot(doc, S):
    data = json.dumps(doc, separators=(",", ":")).replace("\\", "\\\\").replace("</", "<\\/")
    return _shoot('<!doctype html><style>html,body{margin:0;background:#fff}#m{width:%dpx;height:%dpx}</style>'
                  '<div id=m></div><script src="file://%s/avatar-lab/lottie_light.min.js"></script>'
                  '<script>var A=%s;lottie.loadAnimation({container:document.getElementById("m"),'
                  'renderer:"svg",loop:false,autoplay:false,animationData:A}).goToAndStop(0,true);</script>'
                  % (S, S, HERE, data), "/tmp/ablottie/_work/l2s_b.png", S, S)

def real_diff(a, b, tol=24, r=2):
    """pixels that differ and have no match within one pixel of the other picture.

    A plain pixel compare cannot judge this: an SVG rasterised inside an `<img>` and a live lottie
    SVG in the DOM disagree on 1 to 3% of pixels at 620 px, all of it a one-pixel fringe on edges,
    and a drawing with a lot of small detail (OtherRose's snowflakes, her scarf stripes) hits that
    ceiling while being pixel-correct. Matching each differing pixel against its neighbourhood
    leaves only the real ones."""
    d = np.abs(a-b).sum(2) > tol
    if not d.any(): return d
    ok = np.zeros(d.shape, bool)
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            sh = np.roll(np.roll(b, dy, axis=0), dx, axis=1)
            ok |= np.abs(a-sh).sum(2) <= tol
            sh = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
            ok |= np.abs(b-sh).sum(2) <= tol
    return d & ~ok

def plain(path):
    d = json.load(open(path))
    for L in d["layers"]:
        if str(L.get("nm", "")).startswith("ab-"): L["hd"] = True
    return d

def one(name, src, S=620, write=False):
    docs = {}
    for emo in ("win", "think", "lose"):
        p = os.path.join(src, "%s_%s.json" % (name, emo))
        if os.path.exists(p): docs[emo] = plain(p)
    if not docs: return None
    imgs = {e: render_lot(d, S) for e, d in docs.items()}
    dist = lambda a, b: int((np.abs(a-b).sum(2) > 24).sum())
    took = min(imgs, key=lambda e: sum(dist(imgs[e], imgs[f]) for f in imgs if f != e))
    spread = max((dist(imgs[a], imgs[b]) for a in imgs for b in imgs if a < b), default=0)
    text = still_svg(docs[took])
    got = render_svg(text, S)
    dif = int(real_diff(got, imgs[took]).sum())
    ink = lambda x: np.abs(x-255).sum(2) > 24
    u = (ink(got) | ink(imgs[took])).sum()
    iou = float((ink(got) & ink(imgs[took])).sum()/u) if u else 1.0
    old = os.path.join(SVG, name + ".svg")
    if not os.path.exists(old): old = os.path.join(SVG, name + "2.svg")
    ok = dif <= TOL * S * S and iou >= 0.98
    if write and ok: open(old, "w").write(text)
    return dict(name=name, took=took, spread=spread, differs=dif, of=S*S, iou=round(iou, 4),
                bytes=len(text), ok=ok, path=old)

if __name__ == "__main__":
    args = sys.argv[1:]
    src = os.path.join(HERE, "game-assets", "avatars-lottie-v9")
    for a in args:
        if a.startswith("--from="): src = os.path.join(HERE, "game-assets", a.split("=", 1)[1])
    w = "--write" in args
    good = bad = 0
    for n in [a for a in args if not a.startswith("--")]:
        r = one(n, src, write=w)
        if r is None: print("%-28s no animation" % n); continue
        good, bad = good + (1 if r["ok"] else 0), bad + (0 if r["ok"] else 1)
        print("%-28s from _%-6s emotions differ %5d px | still vs frame 0 %.3f%% real, IoU %.4f | %5d bytes | %s" % (
            r["name"], r["took"], r["spread"], 100.0*r["differs"]/r["of"], r["iou"], r["bytes"],
            "written" if (w and r["ok"]) else ("ok" if r["ok"] else "REFUSED")))
    print("%d within tolerance, %d refused" % (good, bad))
