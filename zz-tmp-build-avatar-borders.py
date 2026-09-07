#!/usr/bin/env python3
"""The faint border on every avatar (avatar-svg-lab.html, the softer set's row 13), as a rule:
   a 2-unit centred stroke, black at 15%, on the PARTS of each drawing. Skipped: tiny shapes (under 10 units:
   eyes, dots, marks), the ink (fills darker than L .03), and SHADING (a shape whose fill is a near tone,
   under 1.35:1 but not identical, of a bigger shape of the same hue that contains it).
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
    dec = {}
    for e in els:
        if e["area"] == 0 or max(e["x1"] - e["x0"], e["y1"] - e["y0"]) < 10: dec[e["i"]] = "tiny"; continue
        if lum(e["fill"]) < 0.03: dec[e["i"]] = "ink"; continue
        hs, ss = hue(e["fill"]); shade = False
        for t in els:
            if t is e or t["area"] <= e["area"] * 1.2: continue
            r = ratio(e["fill"], t["fill"])
            if r >= 1.35 or r < 1.02: continue            # a different tone, but near: shading. Identical: a part.
            ht, st = hue(t["fill"])
            if ss > 0.08 and st > 0.08 and hdiff(hs, ht) > 30: continue
            ix = max(0, min(e["x1"], t["x1"] + 4) - max(e["x0"], t["x0"] - 4)); iy = max(0, min(e["y1"], t["y1"] + 4) - max(e["y0"], t["y0"] - 4))
            ea = max(1, (e["x1"] - e["x0"]) * (e["y1"] - e["y0"]))
            if ix * iy / ea >= 0.8: shade = True; break
        dec[e["i"]] = "shade" if shade else "stroke"
    return dec

def write(f, dec):
    s = open(SRC + f).read(); head, body = split(s)
    nb = body
    for e in EL.findall(body):
        pass
    els = EL.findall(body)
    for i, e in enumerate(els):
        if dec.get(i) == "stroke":
            nb = nb.replace(e, e[:-2] + ' stroke="#000" stroke-opacity="%s" stroke-width="%s" stroke-linejoin="round"/>' % (OP, W), 1)
    open(OUT + f, "w").write(head + nb)

if __name__ == "__main__":
    files = sorted(f for f in os.listdir(SRC) if f.endswith(".svg"))
    by = measure(files)
    decisions = {}; counts = {"stroke": 0, "shade": 0, "tiny": 0, "ink": 0}
    for f in files:
        dec = decide(by.get(f, [])); decisions[f] = dec
        for v in dec.values(): counts[v] += 1
        write(f, dec)
    json.dump(decisions, open(OUT + "decisions.json", "w"), indent=0)
    grow = [(os.path.getsize(SRC + f), os.path.getsize(OUT + f)) for f in files]
    print("files", len(files), counts, "size +%d bytes, mean +%.1f%%" % (sum(b - a for a, b in grow), 100 * sum(b / a - 1 for a, b in grow) / len(grow)))
