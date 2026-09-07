#!/usr/bin/env python3
"""The faint border on every avatar, decided from what is VISIBLE and from how the artwork is shaded (v8).

The line: 2 units (in the 160-unit box), black at 15%, on one side of every edge where two materials meet.

What counts as ONE material (no line): this artwork shades a piece by turning its own colour up or down,
so a shade is the piece's colour times one multiplier and a highlight is it screened by one amount. Two
colours are one material when a single multiplier (0.45 to 0.97) or a single screen (0.03 to 0.55) takes
one to the other on every channel, the channels agreeing within 0.09. Two greys are one material up to 22 L
apart (every grey is a multiple of every other one, so the ratio says nothing). A grey beside a colour is
always a change of material, except a pale mark lying inside a coloured piece (a shine on a lens).
The old test compared hue and lightness alone, which merged brown hair with tan skin and split a lens
from its own shine.

Which side of an edge, once the two are different materials:
  1. the background (the silhouette): the part keeps its inner line, the coat sits outside it
  2. one side grey (chroma under 10), the other coloured: the coloured side owns the line, unless the grey
     is darker by more than 18 L (white or grey hair beside a face: the line goes on the face)
  3. both coloured or both grey, more than 18 L apart: the darker side owns it
  4. otherwise the more saturated side, and if neither is, the piece on top
  5. nothing is drawn when the owner is too dark to show a line (under 25 L) and the seam already reads on
     its own (over 40 apart in CIE76): black hair beside skin needs no help
The line follows the top piece's outline: its own inner line where it owns the edge, an outer band on the
piece under it where that piece owns it AND this piece lies on it. Hidden outline gets nothing. Tiny shapes
(under 10 units), translucent shapes and line art are never bordered; a dark fill is line art only when it
is small (under 24 units across or 250 square units), so hair drawn in near-black is a piece.

How: one headless page per file renders (a) the whole drawing with every shape in a unique flat id colour and
no anti-aliasing, (b) the drawing as it is, (c) every shape alone. The full outline of each part is traced
from (c); at every point of it (a) says whether the point is visible and what lies just outside; (b) gives
each shape's colour as seen. Runs of the same decision along the outline become polylines in the border's
mask: the inner line is a stroked <use> of the shape masked to the shape minus black cut polylines; the outer
band is the same stroke masked to white polylines minus the shape. Both are placed right after the shape so
later shapes cover them.
Reads game-assets/avatars/*.svg, writes game-assets/avatars-bordered/*.svg and decisions.json next to them.
Usage: zz-tmp-build-avatar-borders.py [--base] [names...]   (--base: only files without _win/_think/_lose)"""
import re, os, json, subprocess, math, sys, base64
import numpy as np
from PIL import Image
from skimage import measure as skm
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "game-assets", "avatars") + "/"
OUT = os.path.join(HERE, "game-assets", "avatars-bordered") + "/"
TMP = "/tmp/avstudy/v7/render/"
CHROME = "/opt/homebrew/bin/chromium"
S = 3; PX = 160 * S; COLS = 8
W, OP, CUT = 4, 0.15, 5
T_L, T_C, T_GREY = 18, 8, 10
SPREAD, K_LO, K_HI, T_LO, T_HI = 0.09, 0.45, 1.0, 0.0, 0.55   # what counts as one turn of the tone (1.0 = the same colour)
T_GREY_L = 22                       # two greys are one material up to this far apart in lightness
PALE_L, LIGHT_L, MARK_AREA, MARK_RING, MARK_DE = 88, 75, 0.5, 0.75, 24
                                    # a near-white mark on a light piece is a shine on it, not a piece of its own
INK_DIM, INK_AREA = 24, 250         # a dark fill this big is a piece (hair), not line art
DARK_L, FAR = 25, 40                # a line the owner cannot show, on a seam that already reads, is not drawn
MIN_DIM, MIN_RUN, TOL = 10, 2.0, 0.5
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)

EL = re.compile(r'<(?:path|ellipse|rect|circle|polygon|polyline)\b[^>]*?/>', re.S)
def split(s):
    if '<g id="Avatars">' in s: cut = s.index('<g id="Avatars">')
    else:
        m = re.search(r'</defs>', s); cut = m.end() if m else s.index('>', s.index('<svg')) + 1
    return s[:cut], s[cut:]
def styles_of(s):
    """the class rules, in source order; a grouped selector (.a,.b{...}) feeds every class it names"""
    out = {}
    for css in re.findall(r'<style[^>]*>(.*?)</style>', s, re.S):
        for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', css):
            body = re.sub(r'\s+', '', body)
            for one in sel.split(","):
                m = re.fullmatch(r'\.([\w-]+)', one.strip())
                if m: out[m.group(1)] = (out.get(m.group(1), "") + ";" + body).strip(";")
    return out
def props(e, styles):
    """what the element paints: fill hex or None, stroke hex or None, the stroke props, clip-path, fill-rule, opacity"""
    c = re.search(r'class="([^"]+)"', e); st = styles.get(c.group(1), "") if c else ""
    d = dict(kv.split(":", 1) for kv in st.split(";") if ":" in kv)
    for k in ("fill", "stroke", "stroke-width", "clip-path", "fill-rule", "stroke-linecap", "stroke-linejoin", "opacity", "fill-opacity"):
        m = re.search(r'\s%s="([^"]*)"' % k, e)
        if m: d[k] = m.group(1)
    fill = d.get("fill", "#000"); fill = None if fill == "none" or fill.startswith("url") else fill
    stroke = d.get("stroke"); stroke = None if not stroke or stroke == "none" else stroke
    return {"fill": fill, "stroke": stroke, "sw": d.get("stroke-width", "1"), "clip": d.get("clip-path"), "rule": d.get("fill-rule"),
            "cap": d.get("stroke-linecap"), "join": d.get("stroke-linejoin"), "opacity": ("opacity" in d or "fill-opacity" in d)}
def strip(e):
    return re.sub(r'\s(id|class|fill|stroke|stroke-width|opacity|fill-opacity|stroke-opacity|style|shape-rendering)="[^"]*"', "", e)[:-2]
def core_of(e, p):
    """the element without its class, its clip and fill rule kept as attributes"""
    c = strip(e)
    if p["clip"]: c += ' clip-path="%s"' % p["clip"]
    if p["rule"]: c += ' fill-rule="%s"' % p["rule"]
    return c
def labelled(e, p, col):
    c = core_of(e, p) + ' shape-rendering="crispEdges" fill="%s"' % (col if p["fill"] else "none")
    if p["stroke"]:
        c += ' stroke="%s" stroke-width="%s"' % (col, p["sw"])
        if p["cap"]: c += ' stroke-linecap="%s"' % p["cap"]
        if p["join"]: c += ' stroke-linejoin="%s"' % p["join"]
    return c + "/>"

def rgb(h):
    from PIL import ImageColor
    return tuple(v / 255 for v in ImageColor.getrgb(h)[:3])
def lin(v): return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
def lum(h):
    r, g, b = rgb(h); return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
def lab(r, g, b):
    """CIELAB (D65) of an sRGB triple in 0..1: L, C, H"""
    r, g, b = lin(r), lin(g), lin(b)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047; Y = 0.2126 * r + 0.7152 * g + 0.0722 * b; Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    L = 116 * t(Y) - 16; A = 500 * (t(X) - t(Y)); B = 200 * (t(Y) - t(Z))
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360
def hdiff(a, b):
    d = abs(a - b); return min(d, 360 - d)
def dE(a, b):
    """CIE76 between two (L, C, H)"""
    La, Ca, Ha = a; Lb, Cb, Hb = b
    aa, ab = Ca * math.cos(math.radians(Ha)), Ca * math.sin(math.radians(Ha))
    ba, bb = Cb * math.cos(math.radians(Hb)), Cb * math.sin(math.radians(Hb))
    return math.sqrt((La - Lb) ** 2 + (aa - ba) ** 2 + (ab - bb) ** 2)
def one_step(A, B):
    """B is A darkened by one multiplier (a shade) or A lightened by one screen (a tint)"""
    k = [b / a for a, b in zip(A, B) if a >= 24]
    if len(k) >= 2 and max(k) - min(k) <= SPREAD and K_LO <= sum(k) / len(k) <= K_HI: return True
    t = [(a - b) / (255 - b) for a, b in zip(A, B) if b <= 231]
    return len(t) >= 2 and max(t) - min(t) <= SPREAD and T_LO <= sum(t) / len(t) <= T_HI
def same_material(ca, cb, ra, rb):
    """one material = one colour with the tone turned up or down; (L, C, H) and the sRGB seen"""
    La, Ca, _ = ca; Lb, Cb, _ = cb
    ga, gb = Ca < T_GREY, Cb < T_GREY
    if ga and gb: return abs(La - Lb) <= T_GREY_L      # every grey is a multiple of every other one
    if ga != gb: return False                          # a grey beside a colour is a change of material
    if dE(ca, cb) < 3: return True                     # the same colour twice
    A, B = (ra, rb) if sum(ra) >= sum(rb) else (rb, ra)
    return one_step(A, B)
def owner(a, b, a_on_top):
    """which of the two colours (L, C, H) owns the line: True = a"""
    La, Ca, _ = a; Lb, Cb, _ = b
    ga, gb = Ca < T_GREY, Cb < T_GREY
    if ga != gb:
        Lg, Lc = (La, Lb) if ga else (Lb, La)
        grey_owns = Lg < Lc - T_L
        return grey_owns if ga else not grey_owns
    if abs(La - Lb) > T_L: return La < Lb
    if abs(Ca - Cb) > T_C: return Ca > Cb
    return a_on_top

def uri(svg): return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
def idcol(i):
    """id colours 8 apart per channel (screenshots drift by a level or two through the colour profile)"""
    return '#00%02x%02x' % ((i // 32) * 8, (i % 32) * 8 + 4)
def decode(lm):
    g = np.rint(lm[..., 1] / 8).astype(int); b = np.rint((lm[..., 2] - 4) / 8).astype(int)
    return np.where(lm[..., 3] > 0, g * 32 + b, -1)
def page(f):
    """write the render page for one file: the label map, the drawing, every shape alone; return the parsed pieces"""
    s = open(SRC + f).read(); head, body = split(s); styles = styles_of(s)
    spans = [(m.start(), m.end()) for m in EL.finditer(body)]; els = [body[a:b] for a, b in spans]
    P = [props(e, styles) for e in els]
    hd = re.sub(r'<svg ', '<svg width="%d" height="%d" ' % (PX, PX), head, count=1)
    parts = []; last = 0
    for i, (a, b) in enumerate(spans):
        parts.append(body[last:a]); parts.append(labelled(els[i], P[i], idcol(i))); last = b
    parts.append(body[last:]); lab_svg = hd + "".join(parts)
    real_svg = hd + body
    cells = [lab_svg, real_svg] + [hd + '<g>' + labelled(els[i], P[i], '#ffffff') + '</g></svg>' for i in range(len(els))]
    html = '<html><head><style>body{margin:0}.g{display:grid;grid-template-columns:repeat(%d,%dpx)}img{width:%dpx;height:%dpx;display:block}</style></head><body><div class="g">%s</div></body></html>' % (COLS, PX, PX, PX, "".join('<img src="%s">' % uri(c) for c in cells))
    open(TMP + f + ".html", "w").write(html)
    return {"file": f, "head": head, "body": body, "spans": spans, "els": els, "P": P, "cells": len(cells)}
def shoot(info):
    rows = (info["cells"] + COLS - 1) // COLS
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000", "--force-color-profile=srgb", "--force-device-scale-factor=1",
                    "--window-size=%d,%d" % (COLS * PX, rows * PX), "--virtual-time-budget=10000", "--screenshot=" + TMP + info["file"] + ".png", "file://" + TMP + info["file"] + ".html"], capture_output=True, timeout=300)
    return info

def simplify(pts, tol):
    """Douglas-Peucker on an (n,2) array"""
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; ab = b - a; n = np.hypot(*ab)
    if n == 0: d = np.hypot(*(pts - a).T)
    else: d = np.abs(np.cross(ab, pts - a)) / n
    i = int(np.argmax(d))
    if d[i] > tol: return np.vstack([simplify(pts[:i + 1], tol)[:-1], simplify(pts[i:], tol)])
    return np.array([a, b])
def fmt(pts):
    return " ".join("%.1f,%.1f" % (x, y) for y, x in pts)

def analyse(info):
    """decide per part; return {i: {"in": [polylines to cut], "out": [polylines to keep], "runs": [...]}} plus the audit"""
    im = np.asarray(Image.open(TMP + info["file"] + ".png").convert("RGBA")).astype(int)
    def cell(n):
        r, c = divmod(n, COLS); return im[r * PX:(r + 1) * PX, c * PX:(c + 1) * PX]
    N = len(info["els"]); P = info["P"]
    lm = cell(0); real = cell(1)
    label = decode(lm)
    bad = (lm[..., 3] > 0) & ((label < 0) | (label >= N))
    label[bad] = -2
    for _ in range(3):                       # unknown colours (anti-aliased seams) take a neighbour's label
        ys, xs = np.nonzero(label == -2)
        if not len(ys): break
        for y, x in zip(ys, xs):
            nb = label[max(0, y - 1):y + 2, max(0, x - 1):x + 2].ravel(); nb = nb[nb >= 0]
            if len(nb): label[y, x] = np.bincount(nb).argmax()
    label[label == -2] = -1
    masks = [cell(2 + i)[..., 3] > 0 for i in range(N)]
    colour = {}; dim = {}; seen = {}; area = {}
    for i in range(N):
        ys, xs = np.nonzero(masks[i]); dim[i] = (max(xs.max() - xs.min(), ys.max() - ys.min()) + 1) / S if len(xs) else 0
        area[i] = float(masks[i].sum()) / (S * S)
        vis = label == i
        if vis.sum() < 4: continue
        er = vis & np.roll(vis, 1, 0) & np.roll(vis, -1, 0) & np.roll(vis, 1, 1) & np.roll(vis, -1, 1)
        px = real[er if er.sum() >= 4 else vis]
        med = np.median(px[:, :3], axis=0) / 255
        colour[i] = lab(*med); seen[i] = tuple(float(v) * 255 for v in med)
    ring = {}
    for i in range(N):
        v = label == i                       # what lies around the part where it can be seen
        if not v.any(): ring[i] = {}; continue
        out = (np.roll(v, 1, 0) | np.roll(v, -1, 0) | np.roll(v, 1, 1) | np.roll(v, -1, 1)) & ~v
        n = float(out.sum())
        nb = label[out]; nb = nb[nb >= 0]
        if not n or not nb.size: ring[i] = {}; continue
        c = np.bincount(nb, minlength=N).astype(float)
        ring[i] = {int(j): c[j] / n for j in np.nonzero(c)[0]}
    def one_material(i, j):
        """one material, or a near-white shine lying on a light piece (the shine on a lens, on a cheek)"""
        if same_material(colour[i], colour[j], seen[i], seen[j]): return True
        for a, b in ((i, j), (j, i)):
            if not (colour[a][0] >= PALE_L and colour[a][1] < T_GREY): continue
            if area[a] >= MARK_AREA * area[b]: continue
            if ring.get(a, {}).get(b, 0) >= MARK_RING: return True          # it lies inside that piece
            if colour[b][0] >= LIGHT_L and dE(colour[a], colour[b]) < MARK_DE: return True
        return False
    def is_part(i):
        p = P[i]
        if not p["fill"] or p["opacity"] or i not in colour: return False
        if lum(p["fill"]) < 0.03 and not (dim[i] >= INK_DIM and area[i] >= INK_AREA): return False
        return dim[i] >= MIN_DIM or (dim[i] >= 6 and colour[i][0] > 92)
    def material(i):
        """the colour a neighbour shows; None for nothing (background, tiny, unseen)"""
        if i < 0 or i not in colour: return None
        if not P[i]["fill"] and not P[i]["stroke"]: return None
        if dim[i] < 6: return None
        return colour[i]
    result = {}; audit = {}
    for i in range(N):
        if i in colour and not is_part(i):
            audit[i] = {"colour": [round(c, 1) for c in colour[i]], "fill": P[i]["fill"], "dim": round(dim[i], 1),
                        "area": round(area[i], 1), "runs": None}
        if not is_part(i): continue
        contours = skm.find_contours(masks[i].astype(float), 0.5)
        cuts, keeps, runs = [], [], []
        for cont in contours:
            if len(cont) < 6: continue
            dec = []
            for y, x in cont:
                y0, x0 = int(math.floor(y)), int(math.floor(x)); y1, x1 = min(PX - 1, int(math.ceil(y))), min(PX - 1, int(math.ceil(x)))
                cand = {(y0, x0), (y0, x1), (y1, x0), (y1, x1)}
                inside = [c for c in cand if masks[i][c]]; outside = [c for c in cand if not masks[i][c]]
                if not inside or not outside: dec.append("hidden"); continue
                if not any(label[c] == i for c in inside): dec.append("hidden"); continue
                nbs = [label[c] for c in outside]; nb = max(set(nbs), key=nbs.count)
                m = material(nb)
                if m is None: dec.append("in@bg"); continue
                if one_material(i, nb): dec.append("none@%d" % nb); continue
                if min(colour[i][0], m[0]) < DARK_L and dE(colour[i], m) > FAR:
                    dec.append("far@%d" % nb); continue   # the dark side cannot show a line and the seam already reads
                if owner(colour[i], m, i > nb): dec.append("in@%d" % nb); continue
                # the neighbour owns the line. A band onto it only when this shape lies ON it; where the two
                # merely abut, the neighbour traces the same edge itself and draws its own inner line there.
                dec.append(("out:%d" % nb) if any(masks[nb][c] for c in inside) else "none@%d" % nb)
            # runs, short ones merged into the longer neighbour
            def to_runs(d):
                r = []
                for k, v in enumerate(d):
                    if r and r[-1][0] == v: r[-1][2] = k + 1
                    else: r.append([v, k, k + 1])
                return r
            def step_len(a, b): return float(np.hypot(*(cont[min(b, len(cont) - 1)] - cont[a]))) if b > a else 0
            def run_units(r): return sum(np.hypot(*(cont[k + 1] - cont[k])) for k in range(r[1], min(r[2], len(cont)) - 1)) / S
            r = to_runs(dec)
            for _ in range(4):
                changed = False; k = 0
                while k < len(r) and len(r) > 1:
                    if run_units(r[k]) < MIN_RUN:
                        prev, nxt = (r[k - 1] if k > 0 else None), (r[k + 1] if k + 1 < len(r) else None)
                        target = prev if (prev and (not nxt or run_units(prev) >= run_units(nxt))) else nxt
                        if target is prev: prev[2] = r[k][2]
                        else: nxt[1] = r[k][1]
                        del r[k]; changed = True; continue
                    k += 1
                if not changed: break
            for v, a, b in r:
                pts = cont[a:b]
                if len(pts) < 2: continue
                runs.append([v, round(float(run_units([v, a, b])), 1)])
                if v.split("@")[0] == "in" or v == "hidden": continue
                poly = simplify(pts / S, TOL)
                cuts.append(fmt(poly))
                if v.startswith("out"): keeps.append(fmt(poly))
        inner = any(v.split("@")[0] == "in" for v, _ in runs)
        if inner or keeps:
            result[i] = {"cuts": cuts, "keeps": keeps, "inner": inner}
        nbrs = {}
        ai = float(masks[i].sum())
        for v, _ in runs:
            tag = v.partition("@")[2] or (v.split(":")[1] if v.startswith("out:") else "")
            if not tag or tag == "bg": continue
            nb = int(tag)
            if nb in nbrs or nb >= N: continue
            inter = float((masks[i] & masks[nb]).sum()); an = float(masks[nb].sum())
            nbrs[nb] = [round(inter / ai, 2) if ai else 0, round(inter / an, 2) if an else 0]
        audit[i] = {"colour": [round(c, 1) for c in colour[i]], "fill": P[i]["fill"], "dim": round(dim[i], 1),
                    "area": round(ai / (S * S), 1), "nbrs": nbrs, "runs": runs}
    return result, audit

def write(info, result):
    head, body, spans, els, P = info["head"], info["body"], info["spans"], info["els"], info["P"]
    if result:
        css = '<style>.abl{fill:none;stroke:#000;stroke-opacity:%s;stroke-width:%d;stroke-linejoin:round}.abc,.abk{fill:none;stroke:#000;stroke-width:%d;stroke-linecap:round;stroke-linejoin:round}.abk{stroke:#fff}</style>' % (OP, W, CUT)
        k = head.index('>', head.index('<svg')) + 1; head = head[:k] + css + head[k:]
    parts = []; last = 0
    for i, (a, b) in enumerate(spans):
        parts.append(body[last:a]); last = b
        if i not in result: parts.append(els[i]); continue
        r = result[i]; core = core_of(els[i], P[i]) + ' id="ab%d"/>' % i
        rep = '<g fill="%s">%s</g>' % (P[i]["fill"], core)
        M = 'maskUnits="userSpaceOnUse" x="-40" y="-40" width="240" height="240"'
        if r["inner"]:
            cutp = "".join('<polyline class="abc" points="%s"/>' % c for c in r["cuts"])
            rep += '<mask id="am%d" %s><use href="#ab%d" fill="#fff"/>%s</mask>' % (i, M, i, cutp)
            rep += '<use class="abl" href="#ab%d" mask="url(#am%d)"/>' % (i, i)
        if r["keeps"]:
            keepp = "".join('<polyline class="abk" points="%s"/>' % c for c in r["keeps"])
            rep += '<mask id="ao%d" %s>%s<use href="#ab%d" fill="#000"/></mask>' % (i, M, keepp, i)
            rep += '<use class="abl" href="#ab%d" mask="url(#ao%d)"/>' % (i, i)
        parts.append(rep)
    parts.append(body[last:])
    open(OUT + info["file"], "w").write(head + "".join(parts))

if __name__ == "__main__":
    args = sys.argv[1:]; base = "--base" in args; names = [a for a in args if not a.startswith("--")]
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".svg") and (not base or "_" not in f) and (not names or f[:-4] in names))
    files = [f for f in files if f != "EmptyChair.svg"]
    infos = [page(f) for f in files]
    with ThreadPoolExecutor(6) as ex: infos = list(ex.map(shoot, infos))
    decisions = {}; n_in = n_out = 0; grow = []
    for info in infos:
        result, audit = analyse(info)
        write(info, result); decisions[info["file"]] = audit
        n_in += sum(1 for r in result.values()); n_out += sum(1 for r in result.values() if r["keeps"])
        grow.append((os.path.getsize(SRC + info["file"]), os.path.getsize(OUT + info["file"])))
    json.dump(decisions, open(OUT + "decisions.json", "w"))
    print("files", len(files), "bordered parts", n_in, "with outer bands", n_out, "size mean +%.1f%%" % (100 * sum(b / a - 1 for a, b in grow) / len(grow)))
