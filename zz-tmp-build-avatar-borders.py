#!/usr/bin/env python3
"""The faint border on every avatar, as a rule: a 2-unit INNER border, black at 15%, on every PART of the drawing
   (a stroked reference to the shape, masked to the shape), an OUTER border on the teeth (small near-white shapes low
   in the face, stroked under the shape), and no border between a part and its own shades. Skipped: tiny shapes (under 10 units:
   eyes, dots, marks), the ink (fills darker than L .03), and SHADING: overlapping shapes whose colours differ only
   in lightness (the same Lab hue within 16 degrees, a similar chroma, under 32 L apart) are one material, a base with
   its shadows and highlights, and only the largest of them is stroked; a change of hue or chroma (grey hair beside
   skin, blonde beside skin) is a new material, so the lines fall where materials meet and never inside one.
   Reads game-assets/avatars/*.svg, measures every filled shape by rendering it alone (one headless Chromium
   screenshot for the whole set), writes game-assets/avatars-bordered/*.svg and a decisions.json next to them.
   The same rule for a Lottie file is lottie_strokes() in zz-tmp-build-avatar-svg-soft.py."""
import re, os, json, subprocess, colorsys, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "game-assets", "avatars") + "/"
OUT = os.path.join(HERE, "game-assets", "avatars-bordered") + "/"
TMP = "/tmp/avstudy/all/"
CHROME = "/opt/homebrew/bin/chromium"
W, OP = 2, 0.15
CELL, COLS = 64, 60
os.makedirs(OUT, exist_ok=True); os.makedirs(TMP, exist_ok=True)

EL = re.compile(r'<(?:path|ellipse|rect|circle|polygon|polyline)\b[^>]*?/>', re.S)
def split(s):
    """head (everything before the drawing), body; works for the cls- and the st- exports"""
    if '<g id="Avatars">' in s: cut = s.index('<g id="Avatars">')
    else:
        m = re.search(r'</defs>', s); cut = m.end() if m else s.index('>', s.index('<svg')) + 1
    return s[:cut], s[cut:]
def styles_of(s):
    return {k: re.sub(r'\s+', '', v) for k, v in re.findall(r'\.([\w-]+)\s*\{([^}]*)\}', s)}
def fill_of(e, styles):
    c = re.search(r'class="([^"]+)"', e); st = styles.get(c.group(1), "") if c else ""
    if 'fill:none' in st: return None
    m = re.search(r'fill:(#[0-9a-fA-F]{3,6})', st) or re.search(r'fill="(#[0-9a-fA-F]{3,6})"', e)
    return m.group(1) if m else None

def rgb(h):
    h = h.lstrip('#'); h = "".join(c * 2 for c in h) if len(h) == 3 else h
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
def lum(h):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h); return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
def ratio(a, b):
    la, lb = lum(a), lum(b); return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)
def hue(h):
    r, g, b = rgb(h); hh, s, v = colorsys.rgb_to_hsv(r, g, b); return hh * 360, s
def hdiff(a, b):
    d = abs(a - b); return min(d, 360 - d)
def lab(h):
    """CIELAB (D65) of a hex colour"""
    import math
    r, g, b = rgb(h)
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047; Y = 0.2126 * r + 0.7152 * g + 0.0722 * b; Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    L = 116 * t(Y) - 16; A = 500 * (t(X) - t(Y)); B = 200 * (t(Y) - t(Z))
    return L, A, B, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360

def measure(files):
    """render every filled shape alone in one grid; return {file: [{i, fill, area, x0, y0, x1, y1}]}"""
    cells, index = [], []
    for f in files:
        s = open(SRC + f).read(); head, body = split(s); styles = styles_of(s)
        for i, e in enumerate(EL.findall(body)):
            fill = fill_of(e, styles)
            if not fill: continue
            svg = re.sub(r'<svg ', '<svg width="%d" height="%d" ' % (CELL, CELL), head, count=1) + '<g>' + e + '</g></svg>'
            cells.append('<div class="c">' + svg + '</div>'); index.append({"file": f, "i": i, "fill": fill})
    rows = (len(cells) + COLS - 1) // COLS
    html = '<html><head><style>body{margin:0;background:#fff}.g{display:grid;grid-template-columns:repeat(%d,%dpx)}.c{width:%dpx;height:%dpx}.c svg{display:block}</style></head><body><div class="g">' % (COLS, CELL, CELL, CELL) + "".join(cells) + '</div></body></html>'
    open(TMP + "elements.html", "w").write(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", "--window-size=%d,%d" % (COLS * CELL, rows * CELL), "--virtual-time-budget=8000", "--screenshot=" + TMP + "elements.png", "file://" + TMP + "elements.html"], capture_output=True, timeout=300)
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(TMP + "elements.png").convert("RGB")).astype(int)
    mask = im.min(axis=2) < 245
    k = 160 / CELL
    by = {}
    for n, ix in enumerate(index):
        r, c = divmod(n, COLS); tile = mask[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
        ys, xs = np.nonzero(tile)
        if len(xs): ix.update({"area": int(len(xs) * k * k), "x0": int(xs.min() * k), "x1": int(xs.max() * k), "y0": int(ys.min() * k), "y1": int(ys.max() * k)})
        else: ix.update({"area": 0, "x0": 0, "x1": 0, "y0": 0, "y1": 0})
        by.setdefault(ix["file"], []).append(ix)
    return by

def decide(els):
    """per shape: 'in' (an inner border: a part), 'out' (an outer border: the teeth), 'shade', 'tiny' or 'ink';
       families: overlapping shapes of one material (the same Lab hue and chroma, lightness apart) share one border,
       drawn on the family's largest member and masked away where it meets the others"""
    dec = {}; fam_of = {}
    live = [e for e in els if e["area"] > 0 and lum(e["fill"]) >= 0.03]
    ys = [e["y1"] for e in live] or [160]; ytop = min(e["y0"] for e in live) if live else 0; ybot = max(ys)
    def dim(e): return max(e["x1"] - e["x0"], e["y1"] - e["y0"])
    teeth = [e for e in live if lab(e["fill"])[0] > 92 and 6 <= dim(e) < 30 and (e["y0"] + e["y1"]) / 2 > ytop + 0.55 * (ybot - ytop)]
    parts = [e for e in live if dim(e) >= 10 and e not in teeth]
    for e in els:
        if e in teeth: dec[e["i"]] = "out"
        elif e not in parts: dec[e["i"]] = "ink" if (e["area"] > 0 and lum(e["fill"]) < 0.03) else "tiny"
    parent = {id(e): id(e) for e in parts}
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def same_material(a, b):
        La, Aa, Ba, Ca, Ha = lab(a["fill"]); Lb, Ab, Bb, Cb, Hb = lab(b["fill"])
        if abs(La - Lb) > 32: return False
        if Ca < 9 and Cb < 9: pass
        elif Ca < 9 or Cb < 9: return False
        else:
            if hdiff(Ha, Hb) > 16: return False
            if abs(Ca - Cb) / max(Ca, Cb) > 0.5: return False
        ix = max(0, min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])); iy = max(0, min(a["y1"], b["y1"]) - max(a["y0"], b["y0"]))
        small = min(max(1, (a["x1"] - a["x0"]) * (a["y1"] - a["y0"])), max(1, (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])))
        return ix * iy / small >= 0.3
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            if same_material(a, b): parent[find(id(a))] = find(id(b))
    families = {}
    for e in parts: families.setdefault(find(id(e)), []).append(e)
    for fam in families.values():
        base = max(fam, key=lambda e: e["area"])
        for e in fam:
            dec[e["i"]] = "in" if e is base else "shade"
            fam_of[e["i"]] = [x["i"] for x in fam if x is not e]
    return dec, fam_of

def write(f, dec, fam_of):
    """the shape keeps its geometry once, with an id and its fill on a wrapper; the border is a <use> of it:
       inner = a 4-unit stroke on the reference, masked to the shape (and away from its own shades);
       outer (teeth) = a 2-unit stroke on the reference drawn under the shape"""
    s = open(SRC + f).read(); head, body = split(s); styles = styles_of(s)
    els = EL.findall(body); nb = body
    for i, e in enumerate(els):
        d = dec.get(i)
        if d not in ("in", "out", "shade"): continue
        fill = fill_of(e, styles)
        if not fill: continue
        c = re.search(r'class="([^"]+)"', e)
        if c and "opacity" in styles.get(c.group(1), ""): continue
        core = re.sub(r'\s(id|class)="[^"]*"', "", e)
        core = core[:-2] + ' id="ab%d"/>' % i
        shape = '<g fill="%s">' % fill + core + '</g>'
        if d == "shade": rep = shape
        elif d == "out":
            rep = '<use href="#ab%d" fill="none" stroke="#000" stroke-opacity="%s" stroke-width="%s" stroke-linejoin="round"/>' % (i, OP, W) + shape
        else:
            others = "".join('<use href="#ab%d" fill="#000" stroke="#000" stroke-width="%s" stroke-linejoin="round"/>' % (k, W * 2) for k in fam_of.get(i, []))
            mask = '<mask id="am%d" maskUnits="userSpaceOnUse" x="0" y="0" width="160" height="160"><use href="#ab%d" fill="#fff"/>%s</mask>' % (i, i, others)
            rep = shape + mask + '<use href="#ab%d" fill="none" stroke="#000" stroke-opacity="%s" stroke-width="%s" stroke-linejoin="round" mask="url(#am%d)"/>' % (i, OP, W * 2, i)
        nb = nb.replace(e, rep, 1)
    open(OUT + f, "w").write(head + nb)

if __name__ == "__main__":
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".svg"))
    by = measure(files)
    decisions = {}; counts = {"in": 0, "out": 0, "shade": 0, "tiny": 0, "ink": 0}
    for f in files:
        dec, fam_of = decide(by.get(f, [])); decisions[f] = dec
        for v in dec.values(): counts[v] += 1
        write(f, dec, fam_of)
    json.dump(decisions, open(OUT + "decisions.json", "w"), indent=0)
    grow = [(os.path.getsize(SRC + f), os.path.getsize(OUT + f)) for f in files]
    print("files", len(files), counts, "size +%d bytes, mean +%.1f%%" % (sum(b - a for a, b in grow), 100 * sum(b / a - 1 for a, b in grow) / len(grow)))
