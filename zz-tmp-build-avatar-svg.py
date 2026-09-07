#!/usr/bin/env python3
"""Generate SVG-level variants of the capped man (the classic ManCowboy.svg): true inset borders on chosen shapes,
a deeper beard, a brim shadow, heavier feature strokes. Writes avatar-lab/ManCowboy-<variant>.svg and a variants.json."""
import re, json, os
SRC = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3/avatar-lab/ManCowboy.svg"
OUT = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3/avatar-lab"
src = open(SRC).read()
head = src[:src.index('<g id="Avatars">')]
body = src[src.index('<g id="Avatars">'):]
ELS = re.findall(r'<(?:path|ellipse|rect|circle)\b[^>]*?/>', body)
STYLES = dict(re.findall(r'\.(cls-\d+)\{([^}]*)\}', src))

def fill_of(el):
    c = re.search(r'class="([^"]+)"', el)
    m = re.search(r'fill:(#[0-9a-fA-F]{3,6})', STYLES.get(c.group(1), "")) if c else None
    return m.group(1) if m else None

def darken(hexc, k):
    h = hexc.lstrip("#"); h = "".join(ch * 2 for ch in h) if len(h) == 3 else h
    r, g, b = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % (round(r * (1 - k)), round(g * (1 - k)), round(b * (1 - k)))

def strip(el):
    el = re.sub(r'\s(id|class)="[^"]*"', "", el)
    return el

def inset(el, n, color, w):
    """the element, then a stroked copy of it clipped to itself: an inset border w units wide"""
    plain = strip(el)
    clip = '<clipPath id="ib%d">' % n + plain + '</clipPath>'
    stroke = plain[:-2] + ' fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" clip-path="url(#ib%d)"/>' % (color, w * 2, n)
    return el + clip + stroke

# the shapes, by index in draw order
CAP = [18, 25, 26, 3]      # crown, left panel, right panel, brim
BEARD = [16]
SHIRT = [27, 28, 32]       # left, right, centre panel
FUR = [0, 29, 30]          # the collar's three orange blobs
FACE = [4]
NECK = [2]
BROWS_STYLE = 'cls-13'

def build(name, borders=None, beard_fill=None, brim_shadow=False, brows=None, face_dark=None, note=""):
    """borders: {index: (color, width)}"""
    borders = borders or {}
    parts = []
    for i, el in enumerate(ELS):
        if i in borders:
            col, w = borders[i]
            parts.append(inset(el, i, col, w))
        else:
            parts.append(el)
    # rebuild the body: replace elements in order
    nb = body
    for i, el in enumerate(ELS):
        nb = nb.replace(el, "\x00%d\x00" % i, 1)
    for i, p in enumerate(parts):
        nb = nb.replace("\x00%d\x00" % i, p, 1)
    h = head
    if beard_fill:
        h = h.replace(".cls-9{fill:#d89c93;}", ".cls-9{fill:%s;}" % beard_fill)
    if face_dark:
        h = h.replace(".cls-3{fill:#fab3a7;}", ".cls-3{fill:%s;}" % face_dark)
    if brows:
        h = re.sub(r'(\.cls-13\{[^}]*stroke-width:)[\d.]+px', r'\g<1>%spx' % brows, h)
    if brim_shadow:
        face = strip(ELS[4])
        shadow = '<clipPath id="faceclip">' + face + '</clipPath><rect x="0" y="51.5" width="160" height="6" fill="#000" opacity="0.13" clip-path="url(#faceclip)"/>'
        # after the face (index 4) and its shade band (5), before the ear
        nb = nb.replace(ELS[6], shadow + ELS[6], 1)
    svg = h + nb
    fn = "ManCowboy-%s.svg" % name
    open(os.path.join(OUT, fn), "w").write(svg)
    return {"id": name, "file": fn, "note": note}

CAPB = "#911616"; BEARDB = "#b5776d"; SHIRTB = "#222238"; FURB = "#c6692a"; FACEB = "#e8ab9e"
V = []
V.append(build("v00-today", note="The file as it ships, with the frontpage's outline (the four 1px #252525 drop-shadows)."))
V.append(build("v01-cap", {i: (CAPB, 2) for i in CAP}, note="A 2-unit inset border on the cap in its own brim red #911616: the crown, the two side panels and the brim each get a darker inside edge, so the cap reads as a sewn object and its seams show."))
V.append(build("v02-beard", {i: (BEARDB, 2) for i in BEARD}, note="A 2-unit inset border on the beard in a deeper skin-brown #b5776d. Today the beard is #d89c93 on skin #fcc8bc, 1.4:1: at 48px it reads as a blush, not a beard."))
V.append(build("v03-shirt", {i: (SHIRTB, 2) for i in SHIRT}, note="A 2-unit inset border on the three shirt shapes in a deeper navy #222238: the neckline and the collar's V get a line; against the felt the outer edge still needs the outline."))
V.append(build("v04-three", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}}, note="The three together at 2 units (1.2px at 96, 0.6px at 48)."))
V.append(build("v05-three3", {**{i: (CAPB, 3) for i in CAP}, **{i: (BEARDB, 3) for i in BEARD}, **{i: (SHIRTB, 3) for i in SHIRT}}, note="The three together at 3 units (1.8px at 96, 0.9px at 48, 0.5px at 28): the width that still shows on the listing tiles."))
V.append(build("v06-fur", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}, **{i: (FURB, 2) for i in FUR}}, note="The three plus the collar's fur in its own darker orange #c6692a: the three blobs stop merging into one mass."))
V.append(build("v07-all", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}, **{i: (FURB, 2) for i in FUR}, **{i: (FACEB, 2) for i in FACE + NECK}}, note="Every major shape with an inset border in a darker tone of its own fill, the face and neck included (#e8ab9e): the drawn-line look across the whole figure."))
V.append(build("v08-beardfill", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}}, beard_fill="#cf8f85", note="The three borders and the beard's fill one step deeper (#cf8f85, 1.9:1 on the skin instead of 1.4:1), so the beard is a beard at 48px."))
V.append(build("v09-brim", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}}, brim_shadow=True, note="The three borders and a cast shadow under the cap: a 6-unit band at 13% black clipped to the face, so the cap sits on the head instead of beside it."))
V.append(build("v10-brows", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}}, brows=3.2, note="The three borders and the feature strokes (brows, eyelids) from 2.39 to 3.2 units, so the eyes hold at 48 and 28."))
V.append(build("v11-works", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}, **{i: (FURB, 2) for i in FUR}}, beard_fill="#cf8f85", brim_shadow=True, brows=3.2, note="The works: the four borders, the deeper beard, the brim shadow, the heavier strokes."))
auto = {}
for i, el in enumerate(ELS):
    f = fill_of(el)
    if f and i not in (12, 14, 31, 17, 21, 22, 23, 19, 20, 24, 9, 10, 11, 6):
        auto[i] = (darken(f, 0.28), 2)
V.append(build("v12-rule", auto, note="A rule instead of picks: every filled shape (except the eyes, the small marks and the teeth) gets a 2-unit inset border in its own fill darkened 28%. What a script could do to all 158 avatars."))
V.append(build("v13-ink", {i: ("#27273d", 1.5) for i in CAP + BEARD + SHIRT + FUR + FACE + NECK}, note="The comic version: a 1.5-unit inset border in the shared ink #27273d on every major shape. Shown to bound the range; expected to be too much."))
V.append(build("v14-facedark", {**{i: (CAPB, 2) for i in CAP}, **{i: (BEARDB, 2) for i in BEARD}, **{i: (SHIRTB, 2) for i in SHIRT}}, face_dark="#f3a696", note="The three borders and the face's shade band one step deeper (#f3a696), so the head has a lit and a shadow side at 48."))
json.dump(V, open("/tmp/avstudy/svg/variants.json", "w"), indent=1)
print("\n".join(v["file"] for v in V))
