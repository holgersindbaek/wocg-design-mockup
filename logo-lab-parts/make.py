#!/usr/bin/env python3
"""The logo lab, rounds 4 and 5: B1, how the small line talks to the big one, and the fan in the middle.

Holger, 25 Sep 2026, after the board of logos: "I still like GLCA Medium (B1 today) the best. Pacifico over
Fraunces is interesting as well. I don't know if we can somehow make the top part of the logotype interact in an
interesting way with the bottom part, kind of like what we do with the handwritten top part. It doesn't need to
be a different font though. It could be something simpler, just something that makes it a bit more interesting
and cohesive."

Earlier rounds: 1 drew sixteen variations (Bariol, GLCA, Bulo; stacked and re-marked); 2 kept B1 (GLCA Medium on
both lines) and grew the fan against the words, and Holger picked the words at 85% of the fan in mixed case;
3 is the board (logo-references.html). LOGO.md has the record.

This writes, from this folder's copy of the current logo (Logo-Text@1x.svg) and the fonts:

  ../logo-lab.html          B1 at 85% with the small line treated seventeen ways, each drawn at 64px and in the
                            site's menubar at a desktop width and at a phone's
  ../logo-lab-bar.html      the menubar drawn by site.css; the page shows it in iframes (?v=<id>, &h=40)
  ../logo-lab-check.html    the agent's check: every outlined flat line drawn over the browser's own text
  ../logo-lab-out/<id>.svg  every version as a file, its type outlined, so it opens anywhere with no font
  marks.json                the marks' boxes, measured from pixels in headless Chrome

    python3 logo-lab-parts/make.py             build (measures the marks first if marks.json is missing)
    python3 logo-lab-parts/make.py --measure   measure the marks again, then build

The type is shaped here: advance widths plus the font's own pair kerning (GPOS pair adjustment, or the kern
table), plus tracking; a line can then be laid on an arc or tilted. No GSUB is applied, so a script with
contextual alternates (Pacifico) may differ from the browser; the check page shows it.
"""
import base64
import copy
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WOCG = Path('/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/worldofcardgames')
OUT = ROOT / 'logo-lab-out'
STATIC = ROOT / 'logo-lab-static'
BAR_IMAGES = [('images/logo.png', 'logo.png'), ('images/menuActivity.svg', 'menuActivity.svg'), ('images/menuFriends.svg', 'menuFriends.svg'),
              ('images/wm/menuBurger.svg', 'wm-menuBurger.svg'), ('images/wm/menuClose.svg', 'wm-menuClose.svg'), ('pieces/avatar/classic/WomanGirl2.svg', 'WomanGirl2.svg')]
SRC = HERE / 'Logo-Text@1x.svg'
MARKS_JSON = HERE / 'marks.json'
CHROME = Path.home() / 'Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'

INK = '#141414'        # --ink
QUIET = '#67635c'      # --ink-quiet
RED = '#d51a22'        # the deck's red (DESIGN-COLOUR.md 24)
PAPER = '#f9f6f2'      # --paper-page
OLD_INK = '#252525'    # the current art's outline
OLD_RED = '#EB1B28'    # the current art's red
WHITE = '#ffffff'

SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'
ET.register_namespace('', SVG_NS)
ET.register_namespace('xlink', XLINK_NS)


def q(tag):
    return '{%s}%s' % (SVG_NS, tag)


# ---------------------------------------------------------------------------------------------------------------
# the faces
# ---------------------------------------------------------------------------------------------------------------

FACES = {
    # key: the file the outlines come from, the file the check page embeds, the CSS family the check page declares
    'bariol-700': dict(file=ROOT / 'fonts/bariol/bariol_bold-webfont.ttf', web=ROOT / 'fonts/bariol/bariol_bold-webfont.woff2', family='LabBariol', weight=700, label='Bariol Bold'),
    'bariol-400': dict(file=ROOT / 'fonts/bariol/bariol_regular-webfont.ttf', web=ROOT / 'fonts/bariol/bariol_regular-webfont.woff2', family='LabBariol', weight=400, label='Bariol Regular'),
    'glca-500': dict(file=WOCG / 'static/fonts/GLCA-Medium.woff', web=WOCG / 'static/fonts/GLCA-Medium.woff2', family='LabGLCA', weight=500, label='GLCA Medium (the title face)'),
    'glca-600': dict(file=ROOT / 'Gelica-SemiBold.woff2', web=ROOT / 'Gelica-SemiBold.woff2', family='LabGLCA', weight=600, label='GLCA SemiBold'),
    'glca-400': dict(file=WOCG / 'static/fonts/GLCA-Regular.woff', web=WOCG / 'static/fonts/GLCA-Regular.woff2', family='LabGLCA', weight=400, label='GLCA Regular'),
    'bulo-700': dict(file=ROOT / 'fonts/BuloRounded-Bold.ttf', web=ROOT / 'fonts/BuloRounded-Bold.woff2', family='LabBulo', weight=700, label='Bulo Rounded Bold (the interface face)'),
    'bulo-900': dict(file=ROOT / 'fonts/BuloRounded-Black.woff', web=ROOT / 'fonts/BuloRounded-Black.woff2', family='LabBulo', weight=900, label='Bulo Rounded Black'),
    'pacifico-400': dict(file=ROOT / 'fonts/google/Pacifico-Regular.ttf', web=ROOT / 'fonts/google/Pacifico-Regular.ttf', family='LabPacifico', weight=400, label='Pacifico'),
    'courgette-400': dict(file=ROOT / 'fonts/google/Courgette-Regular.ttf', web=ROOT / 'fonts/google/Courgette-Regular.ttf', family='LabCourgette', weight=400, label='Courgette'),
}


def fmt(v, nd=2):
    s = '%.*f' % (nd, v)
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def round_path(d, nd=2):
    return re.sub(r'-?\d+\.\d+(?:e-?\d+)?', lambda m: fmt(float(m.group()), nd), d)


class Face:
    def __init__(self, key, spec):
        self.key = key
        self.spec = spec
        self.font = TTFont(str(spec['file']))
        self.upm = self.font['head'].unitsPerEm
        self.cmap = self.font.getBestCmap()
        self.gs = self.font.getGlyphSet()
        self.hmtx = self.font['hmtx']
        os2 = self.font['OS/2']
        cap = getattr(os2, 'sCapHeight', 0)
        xh = getattr(os2, 'sxHeight', 0)
        # some fonts carry nonsense here (Courgette says 301 of 2048), so an implausible value is measured instead
        self.cap = cap if 0.4 * self.upm < cap < 0.95 * self.upm else self.ink_of('H')[3]
        self.xh = xh if 0.25 * self.upm < xh < 0.8 * self.upm else self.ink_of('x')[3]
        self._pairs = {}
        self._lookups = self._load_pairpos()
        self._kern = self._load_kern_table()

    # -- kerning -------------------------------------------------------------------------------------------------
    def _load_kern_table(self):
        d = {}
        if 'kern' in self.font:
            for st in self.font['kern'].kernTables:
                kt = getattr(st, 'kernTable', None)
                if kt:
                    d.update(kt)
        return d

    def _load_pairpos(self):
        out = []
        if 'GPOS' not in self.font:
            return out
        for lookup in self.font['GPOS'].table.LookupList.Lookup:
            subs = []
            for st in lookup.SubTable:
                if lookup.LookupType == 9:
                    if st.ExtensionLookupType != 2:
                        continue
                    st = st.ExtSubTable
                elif lookup.LookupType != 2:
                    continue
                subs.append(st)
            if subs:
                out.append(subs)
        return out

    @staticmethod
    def _pair_in(st, left, right):
        if left not in st.Coverage.glyphs:
            return None
        if st.Format == 1:
            i = st.Coverage.glyphs.index(left)
            for pvr in st.PairSet[i].PairValueRecord:
                if pvr.SecondGlyph == right:
                    return getattr(pvr.Value1, 'XAdvance', 0) if pvr.Value1 else 0
            return None
        c1 = st.ClassDef1.classDefs.get(left, 0)
        c2 = st.ClassDef2.classDefs.get(right, 0)
        rec = st.Class1Record[c1].Class2Record[c2]
        return getattr(rec.Value1, 'XAdvance', 0) if rec.Value1 else 0

    def kern(self, left, right):
        key = (left, right)
        if key in self._pairs:
            return self._pairs[key]
        v = 0
        if self._lookups:
            for subs in self._lookups:
                for st in subs:
                    k = self._pair_in(st, left, right)
                    if k is not None:
                        v += k
                        break
        elif self._kern:
            v = self._kern.get(key, 0)
        self._pairs[key] = v
        return v

    # -- shaping -------------------------------------------------------------------------------------------------
    def glyphs(self, text):
        return [self.cmap.get(ord(ch), '.notdef') for ch in text]

    def shape(self, text, tracking_em=0.0, extra_units=0.0):
        """Glyph names and x positions in font units. tracking and extra come after every glyph but the last."""
        names = self.glyphs(text)
        xs = []
        x = 0.0
        for i, g in enumerate(names):
            if i:
                x += self.kern(names[i - 1], g)
            xs.append(x)
            x += self.hmtx[g][0]
            if i < len(names) - 1:
                x += tracking_em * self.upm + extra_units
        return names, xs, x

    def draw_t(self, pen, names, transforms):
        for g, t in zip(names, transforms):
            self.gs[g].draw(TransformPen(pen, t))

    def path_t(self, names, transforms):
        pen = SVGPathPen(self.gs)
        self.draw_t(pen, names, transforms)
        return round_path(pen.getCommands())

    def bounds_t(self, names, transforms):
        pen = BoundsPen(self.gs)
        self.draw_t(pen, names, transforms)
        return pen.bounds

    def ink_of(self, ch):
        pen = BoundsPen(self.gs)
        self.gs[self.cmap[ord(ch)]].draw(pen)
        return pen.bounds


FACE = {}


def face(key):
    if key not in FACE:
        FACE[key] = Face(key, FACES[key])
    return FACE[key]


# ---------------------------------------------------------------------------------------------------------------
# the marks, cut out of the current art
# ---------------------------------------------------------------------------------------------------------------

def ser(el):
    s = ET.tostring(el, encoding='unicode')
    return re.sub(r'\sxmlns(:xlink)?="[^"]*"', '', s)


def load_source():
    root = ET.parse(SRC).getroot()
    defs = root.find(q('defs'))
    logo = root.find('.//%s[@id="Logo"]' % q('g'))
    text = root.find('.//%s[@id="World-of-Card-Games"]' % q('g'))
    return root, defs, logo, text


def flatten(g, ink=INK, red=RED, card=WHITE):
    """No shadow, no gradient: white cards with the ink's outline, the pips in the ink and the deck's red."""
    for el in g.iter():
        if 'filter' in el.attrib:
            del el.attrib['filter']
        f = el.get('fill')
        if f and f.startswith('url(#linearGradient'):
            el.set('fill', card)
        elif f == '#000000':
            el.set('fill', ink)
        elif f == OLD_RED:
            el.set('fill', red)
        if el.get('stroke') == OLD_INK:
            el.set('stroke', ink)
    return g


def rename_masks(g, suffix):
    for el in g.iter():
        for k in ('id', 'mask'):
            v = el.get(k)
            if v and 'mask-' in v:
                el.set(k, re.sub(r'mask-(\d+)', lambda m: 'mask-%s%s' % (m.group(1), suffix), v))
    return g


def polygon_to_path(points):
    nums = [float(n) for n in re.split(r'[\s,]+', points.strip()) if n]
    pts = list(zip(nums[0::2], nums[1::2]))
    return 'M' + ' L'.join('%s,%s' % (fmt(x, 3), fmt(y, 3)) for x, y in pts) + ' Z'


def pip_paths(logo):
    """The four pips as drawn on the fan's cards: d and its box."""
    cards = {g.get('id'): g for g in logo.iter(q('g')) if (g.get('id') or '').startswith('small_')}
    out = {}
    for name, card, pid in [('spade', 'small_spade_1', 'Spade-small'), ('heart', 'small_heart_1', 'Heart-small'),
                            ('club', 'small_clover_1', 'Clover-small'), ('diamond', 'small_diamond_1', 'Diamond-small')]:
        for el in cards[card].iter():
            if el.get('id') == pid:
                d = el.get('d') or polygon_to_path(el.get('points'))
                bp = BoundsPen(None)
                parse_path(d, bp)
                out[name] = dict(d=d, box=bp.bounds)
                break
    return out


def build_marks(logo):
    marks = {}
    fan = copy.deepcopy(logo)
    fan.set('id', 'mark-fan')
    marks['fan'] = fan

    flat = rename_masks(flatten(copy.deepcopy(logo)), 'f')
    flat.set('id', 'mark-flat')
    marks['flat'] = flat

    parent = {c: p for p in logo.iter() for c in p}
    cards = {g.get('id'): g for g in logo.iter(q('g')) if (g.get('id') or '').startswith('small_')}
    holder = parent[cards['small_heart_1']]
    rot = parent[parent[parent[holder]]]

    def subset(ids, mid):
        g = ET.Element(q('g'), {'id': mid, 'transform': rot.get('transform')})
        h = ET.SubElement(g, q('g'), {'transform': holder.get('transform')})
        for i in ids:
            h.append(flatten(copy.deepcopy(cards[i])))
        return g

    marks['two'] = subset(['small_clover_1', 'small_heart_1'], 'mark-two')
    marks['one'] = subset(['small_heart_1'], 'mark-one')

    # the four suits as one square tile: spade heart / club diamond, each fitted to its cell by eye
    pips = pip_paths(logo)
    suits = ET.Element(q('g'), {'id': 'mark-suits'})
    cell, gap = 100.0, 14.0
    for i, (name, colour, fit) in enumerate([('spade', INK, 90), ('heart', RED, 88), ('club', INK, 92), ('diamond', RED, 86)]):
        x0, y0, x1, y1 = pips[name]['box']
        w, h = x1 - x0, y1 - y0
        f = fit / max(w, h)
        cx = (i % 2) * (cell + gap) + cell / 2
        cy = (i // 2) * (cell + gap) + cell / 2
        ET.SubElement(suits, q('path'), {'d': pips[name]['d'], 'fill': colour,
                                         'transform': 'translate(%s,%s) scale(%s)' % (fmt(cx - (x0 + w / 2) * f, 3), fmt(cy - (y0 + h / 2) * f, 3), fmt(f, 5))})
    marks['suits'] = suits

    # the letter fan: the corner index of each card (the A and its small pip) becomes the first letter of a word
    lf = copy.deepcopy(logo)
    lf.set('id', 'mark-letterfan')
    glca = face('glca-500')
    for card_id, letter in (('small_spade_1', 'W'), ('small_diamond_1', 'O'), ('small_clover_1', 'C'), ('small_heart_1', 'G')):
        g = next(x for x in lf.iter(q('g')) if x.get('id') == card_id)
        a = next(x for x in g if x.get('id') == 'A')
        small = next(x for x in g if (x.get('id') or '').endswith('-small'))
        bp = BoundsPen(None)
        parse_path(a.get('d'), bp)
        ax0, ay0, ax1, ay1 = bp.bounds
        fill = a.get('fill')
        g.remove(a)
        g.remove(small)
        gname = glca.cmap[ord(letter)]
        gb = BoundsPen(glca.gs)
        glca.gs[gname].draw(gb)
        gx0, gy0, gx1, gy1 = gb.bounds
        sc = (ay1 - ay0) * 1.3 / (gy1 - gy0)
        t = Transform(sc, 0, 0, -sc, ax0 - gx0 * sc, ay0 + gy1 * sc)
        ET.SubElement(g, q('path'), {'d': glca.path_t([gname], [t]), 'fill': fill})
    marks['letterfan'] = rename_masks(lf, 'l')
    return marks


def sketch_marks(pips):
    """Stand-ins for an illustrator's marks: the simplest shapes that carry each idea, so the size and the
    silhouette can be judged beside the words before anyone draws for real. A 200-unit box each."""
    def el(tag, **a):
        return ET.Element(q(tag), {k.replace('_', '-'): str(v) for k, v in a.items()})
    def sub(parent, tag, **a):
        return ET.SubElement(parent, q(tag), {k.replace('_', '-'): str(v) for k, v in a.items()})
    def pip(g, name, cx, cy, h, fill):
        x0, y0, x1, y1 = pips[name]['box']
        f = h / (y1 - y0)
        sub(g, 'path', d=pips[name]['d'], fill=fill,
            transform='translate(%s,%s) scale(%s)' % (fmt(cx - (x0 + (x1 - x0) / 2) * f, 3), fmt(cy - (y0 + (y1 - y0) / 2) * f, 3), fmt(f, 5)))
    def face(g, cx, cy, eye_dx, eye_dy, r, smile_w, smile_dy, smile_drop, stroke, colour):
        sub(g, 'circle', cx=fmt(cx - eye_dx), cy=fmt(cy + eye_dy), r=r, fill=colour)
        sub(g, 'circle', cx=fmt(cx + eye_dx), cy=fmt(cy + eye_dy), r=r, fill=colour)
        sub(g, 'path', d='M%s,%s Q%s,%s %s,%s' % (fmt(cx - smile_w / 2), fmt(cy + smile_dy), fmt(cx), fmt(cy + smile_dy + smile_drop), fmt(cx + smile_w / 2), fmt(cy + smile_dy)),
            fill='none', stroke=colour, stroke_width=stroke, stroke_linecap='round')
    m = {}
    # a happy card: one tilted card with a face and a heart in its corner
    g = el('g', id='mark-happycard')
    inner = sub(g, 'g', transform='rotate(-8 100 100)')
    sub(inner, 'rect', x=40, y=16, width=120, height=168, rx=12, fill=WHITE, stroke=INK, stroke_width=12)
    pip(inner, 'heart', 62, 42, 24, RED)
    face(inner, 100, 100, 22, -14, 9, 52, 18, 28, 12, INK)
    m['happycard'] = g
    # a smiling heart: the ace of hearts' pip as a face
    g = el('g', id='mark-smileheart')
    pip(g, 'heart', 100, 98, 180, RED)
    face(g, 100, 90, 26, -14, 11, 68, 20, 34, 14, WHITE)
    m['smileheart'] = g
    # a joker's cap: three points, three bells
    g = el('g', id='mark-jokercap')
    sub(g, 'path', d='M32,150 C18,124 4,86 14,46 C42,68 62,92 72,116 C80,70 90,36 100,10 C110,36 120,70 128,116 C138,92 158,68 186,46 C196,86 182,124 168,150 Z', fill=INK)
    for cx, cy in ((14, 46), (100, 10), (186, 46)):
        sub(g, 'circle', cx=cx, cy=cy, r=14, fill=RED)
    sub(g, 'rect', x=26, y=140, width=148, height=30, rx=15, fill=RED)
    m['jokercap'] = g
    # two friends: two cards leaning together, each with a face
    g = el('g', id='mark-friends')
    back = sub(g, 'g', transform='rotate(10 130 104)')
    sub(back, 'rect', x=86, y=30, width=96, height=136, rx=10, fill=WHITE, stroke=INK, stroke_width=11)
    face(back, 134, 92, 17, -10, 7, 40, 14, 20, 10, INK)
    front = sub(g, 'g', transform='rotate(-10 70 104)')
    sub(front, 'rect', x=18, y=34, width=96, height=136, rx=10, fill=WHITE, stroke=INK, stroke_width=11)
    face(front, 66, 96, 17, -10, 7, 40, 14, 20, 10, INK)
    m['friends'] = g
    # a king card: a crown sitting on an upright card with a heart
    g = el('g', id='mark-kingcard')
    inner = sub(g, 'g', transform='rotate(-5 100 110)')
    sub(inner, 'rect', x=42, y=52, width=116, height=150, rx=12, fill=WHITE, stroke=INK, stroke_width=12)
    sub(inner, 'path', d='M52,52 L52,14 L76,34 L100,4 L124,34 L148,14 L148,52 Z', fill=INK)
    pip(inner, 'heart', 100, 128, 60, RED)
    m['kingcard'] = g
    return m


def hidden_defs(defs, marks):
    """One hidden svg holding the source's defs and the given marks, for <use> from the page's inline drawings."""
    d = copy.deepcopy(defs)
    for k in marks:
        d.append(copy.deepcopy(marks[k]))
    return '<svg xmlns="%s" xmlns:xlink="%s" width="0" height="0" style="position:absolute;width:0;height:0" aria-hidden="true">%s</svg>' % (SVG_NS, XLINK_NS, ser(d))


def measure_marks(defs, marks):
    """The tight box of every mark as drawn: Chrome renders each on a transparent 2500-unit canvas at 1000px and
    the painted pixels are scanned. getBBox is no use here, it counts the geometry the masks hide."""
    from PIL import Image
    span, px = 2500.0, 1000
    boxes = {}
    tmp = Path('/tmp/logolab')
    tmp.mkdir(exist_ok=True)
    for k, g in marks.items():
        el = copy.deepcopy(g)
        del el.attrib['id']
        svg = tmp / ('measure-%s.svg' % k)
        svg.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="%s" xmlns:xlink="%s" viewBox="-500 -500 %d %d" width="%d" height="%d">%s%s</svg>'
                       % (SVG_NS, XLINK_NS, span, span, px, px, ser(defs), ser(el)))
        shot = tmp / ('measure-%s.png' % k)
        subprocess.run([str(CHROME), '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--default-background-color=00000000',
                        '--window-size=%d,%d' % (px, px), '--screenshot=%s' % shot, svg.as_uri()], capture_output=True, text=True, timeout=120)
        im = Image.open(shot).convert('RGBA')
        alpha = im.getchannel('A').point(lambda a: 255 if a > 24 else 0)
        bb = alpha.getbbox()
        if not bb:
            raise SystemExit('measure: nothing painted for ' + k)
        unit = span / px
        boxes[k] = dict(x=-500 + bb[0] * unit, y=-500 + bb[1] * unit, w=(bb[2] - bb[0]) * unit, h=(bb[3] - bb[1]) * unit)
    MARKS_JSON.write_text(json.dumps(boxes, indent=1))
    return boxes


# ---------------------------------------------------------------------------------------------------------------
# the layout
# ---------------------------------------------------------------------------------------------------------------

S = 100.0  # the big line's font size in the design space; every size below is a share of it
RULE = 5.0  # a hairline's thickness in those units (0.7px on the 32px bar)


def glyph_transforms(sh):
    """One affine per glyph, at the origin: flat, tilted about the line's centre, or laid along an arc."""
    s = sh['s']
    ln = sh['ln']
    flats = [Transform(s, 0, 0, -s, x * s, 0) for x in sh['xs']]
    arc = ln.get('arc')
    rot = ln.get('rot')
    if arc:
        W = sh['adv'] * s
        down = arc < 0
        rise = abs(arc) * W
        R = (W * W / 4 + rise * rise) / (2 * rise)
        cx, cy = W / 2, R - rise
        L = 2 * R * math.asin(min(1.0, (W / 2) / R))
        out = []
        for g, x in zip(sh['names'], sh['xs']):
            adv = sh['face'].hmtx[g][0] * s
            mid = (x * s + adv / 2) * (L / W)
            th = (mid - L / 2) / R
            px, py = cx + R * math.sin(th), cy - R * math.cos(th)
            ux, uy = math.cos(th), math.sin(th)
            if down:
                py, uy = -py, -uy
            out.append(Transform(s * ux, s * uy, s * uy, -s * ux, px - ux * adv / 2, py - uy * adv / 2))
        if rot:
            x0, y0, x1, y1 = sh['ink_flat']
            cxr, cyr = (x0 + x1) / 2, (y0 + y1) / 2
            r = Transform().translate(cxr, cyr).rotate(math.radians(-rot)).translate(-cxr, -cyr)
            out = [r.transform(t) for t in out]
        return out
    if rot:
        x0, y0, x1, y1 = sh['ink_flat']
        cxr, cyr = (x0 + x1) / 2, (y0 + y1) / 2
        r = Transform().translate(cxr, cyr).rotate(math.radians(-rot)).translate(-cxr, -cyr)
        return [r.transform(t) for t in flats]
    return flats


def finish(sh):
    s = sh['s']
    flat = [Transform(s, 0, 0, -s, x * s, 0) for x in sh['xs']]
    sh['ink_flat'] = sh['face'].bounds_t(sh['names'], flat)
    sh['t0'] = glyph_transforms(sh)
    sh['ink'] = sh['face'].bounds_t(sh['names'], sh['t0'])


SUIT_COLOUR = {'spade': INK, 'club': INK, 'heart': RED, 'diamond': RED}


def real_carded_line(sh, pips):
    """A word-initial on a playing card. cardStyle 'real' adds a suit pip in two corners and colours the letter
    like its suit; 'plain' keeps a card's shape with no suit. cardIndex repeats the letter small in the top-left
    and bottom-right corners, as a card's rank; cardPair puts a second card behind ('white' or 'red'). The cards
    count toward the line's height."""
    f, s, ln = sh['face'], sh['s'], sh['ln']
    style = ln.get('cardStyle', 'real')
    angles = list(ln.get('angles', [-9, 7, -6, 10]))
    suits = list(ln.get('suits', ['spade', 'heart', 'club', 'diamond']))
    cap = f.cap * s
    hc = ln.get('cardHeight', 1.5) * cap
    ratio = 0.714 if style == 'plain' else 0.72
    pad_x, pad_y, trail, stroke = 0.10 * cap, 0.16 * cap, ln.get('cardTrail', 0.16) * cap, ln.get('cardStroke', 0.05) * cap
    names, text = sh['names'], sh['text']
    starts = [i for i, ch in enumerate(text) if ch != ' ' and (i == 0 or text[i - 1] == ' ')][ln.get('skip', 0):]
    pen = 0.0
    transforms, cards, boxes_, colours = [], [], [], {}
    ai = 0
    for i, g in enumerate(names):
        adv = f.hmtx[g][0] * s
        kern = f.kern(names[i - 1], g) * s if i else 0.0
        pen += kern
        if i in starts:
            ang = angles[ai % len(angles)]
            suit = suits[ai % len(suits)]
            ai += 1
            gb = BoundsPen(f.gs)
            f.gs[g].draw(gb)
            gx0, gy0, gx1, gy1 = gb.bounds
            gw, gh = (gx1 - gx0) * s, (gy1 - gy0) * s
            wc = ratio * hc
            k = min(1.0, (wc - 2 * pad_x) / gw, (hc - 2 * pad_y) / gh)
            if k < 0.85:
                k = 0.85
                wc = gw * k + 2 * pad_x
            r = math.radians(ang)
            hw = (wc * abs(math.cos(r)) + hc * abs(math.sin(r))) / 2
            hh = (wc * abs(math.sin(r)) + hc * abs(math.cos(r))) / 2
            pair = ln.get('cardPair')
            lead_in = 0.1 * wc if pair else 0.0
            cx = pen + lead_in + hw
            cy = -cap / 2
            sg = s * k
            gx = cx - ((gx0 + gx1) / 2) * sg
            gy = cy + ((gy0 + gy1) / 2) * sg
            flat = Transform(sg, 0, 0, -sg, gx, gy)
            rot = Transform().translate(cx, cy).rotate(math.radians(-ang)).translate(-cx, -cy)
            transforms.append(rot.transform(flat))
            card = dict(cx=cx, cy=cy, w=wc, h=hc, angle=ang, rx=(0.06 if style == 'plain' else 0.07) * wc, stroke=stroke, pips=[], index=[], pair=None)
            if style == 'real':
                ph = 0.17 * hc
                padc = 0.085 * hc
                px0, py0, px1, py1 = pips[suit]['box']
                pf = ph / (py1 - py0)
                pw = (px1 - px0) * pf
                for (ccx, ccy, flip) in ((cx - wc / 2 + padc + pw / 2, cy - hc / 2 + padc + ph / 2, False),
                                         (cx + wc / 2 - padc - pw / 2, cy + hc / 2 - padc - ph / 2, True)):
                    card['pips'].append(dict(name=suit, cx=ccx, cy=ccy, flip=flip,
                                             place='translate(%s,%s) scale(%s)' % (fmt(ccx - (px0 + (px1 - px0) / 2) * pf, 3), fmt(ccy - (py0 + (py1 - py0) / 2) * pf, 3), fmt(pf, 5))))
                colours[i] = SUIT_COLOUR[suit]
            if ln.get('cardIndex'):
                si = sg * 0.3
                iw, ih = (gx1 - gx0) * si, (gy1 - gy0) * si
                padc = 0.075 * hc
                for (icx, icy, flip) in ((cx - wc / 2 + padc + iw / 2, cy - hc / 2 + padc + ih / 2, False),
                                         (cx + wc / 2 - padc - iw / 2, cy + hc / 2 - padc - ih / 2, True)):
                    t = Transform(si, 0, 0, -si, icx - ((gx0 + gx1) / 2) * si, icy + ((gy0 + gy1) / 2) * si)
                    if flip:
                        t = Transform().translate(icx, icy).rotate(math.pi).translate(-icx, -icy).transform(t)
                    card['index'].append(rot.transform(t))
            if pair:
                card['pair'] = dict(dx=-0.11 * wc, dy=-0.07 * hc, angle=ang - 8, fill=RED if pair == 'red' else WHITE)
                boxes_.append((cx - hw - 0.14 * wc, cy - hh - 0.12 * hc, cx + hw, cy + hh))
            cards.append(card)
            colours.setdefault(i, INK)
            boxes_.append((cx - hw - stroke / 2, cy - hh - stroke / 2, cx + hw + stroke / 2, cy + hh + stroke / 2))
            pen = cx + hw + trail
        else:
            transforms.append(Transform(s, 0, 0, -s, pen, 0))
            pen += adv + ln.get('tracking', 0.0) * f.upm * s
    sh['t0'] = transforms
    sh['initials'] = starts
    sh['initial_colours'] = colours
    sh['cards'] = cards
    ink = f.bounds_t(names, transforms)
    for b in boxes_:
        ink = (min(ink[0], b[0]), min(ink[1], b[1]), max(ink[2], b[2]), max(ink[3], b[3]))
    sh['ink'] = ink
    sh['adv'] = pen / s


def enlarge_initials(sh, k):
    """The first glyph of every word drawn k times its size on the same baseline; the rest of the word moves along."""
    f, s = sh['face'], sh['s']
    names, text = sh['names'], sh['text']
    starts = {i for i, ch in enumerate(text) if ch != ' ' and (i == 0 or text[i - 1] == ' ')}
    out, extra = [], 0.0
    for i, (g, x) in enumerate(zip(names, sh['xs'])):
        if i in starts:
            out.append(Transform(s * k, 0, 0, -s * k, x * s + extra, 0))
            extra += f.hmtx[g][0] * s * (k - 1)
        else:
            out.append(Transform(s, 0, 0, -s, x * s + extra, 0))
    sh['t0'] = out
    sh['ink'] = f.bounds_t(names, out)
    sh['adv'] = sh['adv'] + extra / s


def swash_shape(x0, x1, y, cap, depth=0.42, thick=0.05):
    """A tapered stroke under a line of words: a shallow bowl from under the first letter to under the last,
    thickest in the middle, pointed at both ends. Returns an SVG path in the line's own coordinates."""
    W = x1 - x0
    P = [(x0 - 0.02 * W, y + 0.18 * cap), (x0 + 0.28 * W, y + depth * cap), (x0 + 0.74 * W, y + depth * cap), (x1 + 0.03 * W, y + 0.06 * cap)]
    def bez(t):
        u = 1 - t
        return (u**3 * P[0][0] + 3 * u * u * t * P[1][0] + 3 * u * t * t * P[2][0] + t**3 * P[3][0],
                u**3 * P[0][1] + 3 * u * u * t * P[1][1] + 3 * u * t * t * P[2][1] + t**3 * P[3][1])
    n = 48
    pts = [bez(i / n) for i in range(n + 1)]
    left, right = [], []
    for i, (px, py) in enumerate(pts):
        ax, ay = pts[max(i - 1, 0)]
        bx, by = pts[min(i + 1, n)]
        tx, ty = bx - ax, by - ay
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        w = thick * cap * math.sin(math.pi * i / n) ** 0.7
        left.append((px + nx * w / 2, py + ny * w / 2))
        right.append((px - nx * w / 2, py - ny * w / 2))
    poly = left + right[::-1]
    return 'M' + ' L'.join('%s,%s' % (fmt(a), fmt(b)) for a, b in poly) + ' Z'


def layout_badge(v, boxes, pips):
    """The small line arched over the mark, the big line under it: the oldest badge there is. For square places."""
    small, big = shape_line(v['lines'][0]), shape_line(v['lines'][1])
    b = boxes[v['mark']]
    f = MH / b['h']
    mw = b['w'] * f
    parts = []
    x0, y0, x1, y1 = small['ink']
    sw = x1 - x0
    total_w = max(sw, mw, big['ink'][2] - big['ink'][0])
    ox = (total_w - sw) / 2 - x0
    oy = -(y1) - v.get('gapTop', 0.06) * MH
    parts.append(dict(kind='line', sh=small, transforms=[Transform().translate(ox, oy).transform(t) for t in small['t0']], box=(x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
    mx0 = (total_w - mw) / 2
    parts.append(dict(kind='mark', mark=v['mark'], transform='translate(%s,%s) scale(%s)' % (fmt(mx0 - b['x'] * f, 3), fmt(-b['y'] * f, 3), fmt(f, 5)), box=(mx0, 0, mx0 + mw, MH)))
    x0, y0, x1, y1 = big['ink']
    bw = x1 - x0
    ox = (total_w - bw) / 2 - x0
    oy = MH + v.get('gap', 0.12) * MH - y0
    parts.append(dict(kind='line', sh=big, transforms=[Transform().translate(ox, oy).transform(t) for t in big['t0']], box=(x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    m = 0.03 * (ys1 - ys0)
    vb = (xs0 - m, ys0 - m, (xs1 - xs0) + 2 * m, (ys1 - ys0) + 2 * m)
    return dict(parts=parts, vb=vb, block=(total_w, ys1 - ys0), shaped=[small, big], ratio=vb[2] / vb[3], pips=pips)

def shape_line(ln):
    f = face(ln['face'])
    text = ln['text'].upper() if ln.get('caps') else ln['text']
    s = S * ln.get('size', 1.0) / f.upm
    names, xs, adv = f.shape(text, ln.get('tracking', 0.0))
    sh = dict(face=f, text=text, names=names, xs=xs, adv=adv, s=s, ln=ln, extra=0.0)
    finish(sh)
    return sh


def width(box):
    return box[2] - box[0]


def carded_line(sh):
    """The first glyph of every word goes on its own small tilted card. Rewrites the line's transforms, adds the
    cards (line-local: centre, size, angle) and widens the ink box to hold them."""
    f, s, ln = sh['face'], sh['s'], sh['ln']
    angles = list(ln.get('angles', [-7, 6, -6, 8]))
    cap = f.cap * s
    px_, py_ = ln.get('cardPad', (0.16, 0.13))
    pad_x, pad_y, trail, stroke = px_ * cap, py_ * cap, ln.get('cardTrail', 0.14) * cap, ln.get('cardStroke', 0.06) * cap
    names, text = sh['names'], sh['text']
    starts = [i for i, ch in enumerate(text) if ch != ' ' and (i == 0 or text[i - 1] == ' ')]
    pen = 0.0
    transforms, cards, boxes_ = [], [], []
    ai = 0
    for i, g in enumerate(names):
        adv = f.hmtx[g][0] * s
        kern = f.kern(names[i - 1], g) * s if i else 0.0
        pen += kern
        if i in starts:
            ang = angles[ai % len(angles)]
            ai += 1
            gb = BoundsPen(f.gs)
            f.gs[g].draw(gb)
            gx0, gy0, gx1, gy1 = gb.bounds
            w = (gx1 - gx0) * s + 2 * pad_x
            h = (gy1 - gy0) * s + 2 * pad_y
            r = math.radians(ang)
            hw = (w * abs(math.cos(r)) + h * abs(math.sin(r))) / 2
            hh = (w * abs(math.sin(r)) + h * abs(math.cos(r))) / 2
            cx = pen + hw
            cy = -((gy0 + gy1) / 2) * s
            gx = cx - ((gx0 + gx1) / 2) * s  # the glyph origin that centres it on the card
            flat = Transform(s, 0, 0, -s, gx, 0)
            rot = Transform().translate(cx, cy).rotate(math.radians(-ang)).translate(-cx, -cy)
            transforms.append(rot.transform(flat))
            cards.append(dict(cx=cx, cy=cy, w=w, h=h, angle=ang, rx=0.12 * h, stroke=stroke))
            boxes_.append((cx - hw - stroke / 2, cy - hh - stroke / 2, cx + hw + stroke / 2, cy + hh + stroke / 2))
            pen = cx + hw + trail
        else:
            transforms.append(Transform(s, 0, 0, -s, pen, 0))
            pen += adv + ln.get('tracking', 0.0) * f.upm * s
    sh['t0'] = transforms
    sh['initials'] = starts
    sh['cards'] = cards
    ink = f.bounds_t(names, transforms)
    for b in boxes_:
        ink = (min(ink[0], b[0]), ink[1], max(ink[2], b[2]), ink[3])
    sh['ink'] = ink
    sh['adv'] = pen / s


def layout(v, boxes, pips):
    """Shape and stack the lines, add rules, pips or a ribbon, place the mark."""
    shaped = [shape_line(ln) for ln in v['lines']]
    for sh in shaped:
        if sh['ln'].get('initials'):
            real_carded_line(sh, pips) if sh['ln'].get('cardStyle') in ('real', 'plain') else carded_line(sh)
        elif sh['ln'].get('bigInitials'):
            enlarge_initials(sh, sh['ln']['bigInitials'])

    fixed = [width(sh['ink']) for sh in shaped if not sh['ln'].get('justify')]
    target = max(fixed) if fixed else max(width(sh['ink']) for sh in shaped)
    for sh in shaped:
        if sh['ln'].get('justify'):
            gaps = len(sh['names']) - 1
            extra = (target - width(sh['ink'])) / sh['s'] / gaps
            names, xs, adv = sh['face'].shape(sh['text'], sh['ln'].get('tracking', 0.0), extra)
            sh.update(names=names, xs=xs, adv=adv, extra=extra)
            finish(sh)

    block_w = max(width(sh['ink']) for sh in shaped)
    big = shaped[-1]
    cap_b = big['face'].cap * big['s']
    extras = []
    y = 0.0
    for i, sh in enumerate(shaped):
        if i:
            y += v.get('gap', 0.14) * cap_b
        x0, y0, x1, y1 = sh['ink']
        align = sh['ln'].get('align', v.get('align', 'left'))
        if align == 'center':
            ox = (block_w - (x1 - x0)) / 2 - x0
        elif align == 'right':
            ox = block_w - (x1 - x0) - x0
        elif align == 'indent':
            # the small line starts where the big line's second letter starts (past a first letter's card)
            bigl = shaped[-1]
            ox = (bigl['t0'][1].dx - bigl['ink'][0]) - x0
        else:
            ox = -x0
        oy = y - y0
        sh['ox'], sh['oy'] = ox, oy
        sh['T'] = [Transform().translate(ox, oy).transform(t) for t in sh['t0']]
        sh['box'] = (x0 + ox, y0 + oy, x1 + ox, y1 + oy)
        cap_s = sh['face'].cap * sh['s']
        bottom = oy if sh['ln'].get('bottom') == 'baseline' else y1 + oy
        for c in sh.get('cards', []):
            cx, cy = c['cx'] + ox, c['cy'] + oy
            r = math.radians(c['angle'])
            hw = (c['w'] * abs(math.cos(r)) + c['h'] * abs(math.sin(r))) / 2
            hh = (c['w'] * abs(math.sin(r)) + c['h'] * abs(math.cos(r))) / 2
            if c.get('pair'):
                pr = c['pair']
                pcx, pcy = cx + pr['dx'], cy + pr['dy']
                extras.append(dict(kind='rect', role='card', box=(pcx - hw, pcy - hh, pcx + hw, pcy + hh), rx=c['rx'], fill=pr['fill'], stroke=INK, stroke_width=c['stroke'],
                                   cx=pcx, cy=pcy, angle=pr['angle'], rect=(pcx - c['w'] / 2, pcy - c['h'] / 2, c['w'], c['h']),
                                   transform='rotate(%s %s %s)' % (fmt(-pr['angle']), fmt(pcx), fmt(pcy))))
            extras.append(dict(kind='rect', role='card', box=(cx - hw, cy - hh, cx + hw, cy + hh), rx=c['rx'], fill=WHITE, stroke=INK, stroke_width=c['stroke'],
                               cx=cx, cy=cy, angle=c['angle'], rect=(cx - c['w'] / 2, cy - c['h'] / 2, c['w'], c['h']),
                               transform='rotate(%s %s %s)' % (fmt(-c['angle']), fmt(cx), fmt(cy))))
            for pp in c.get('pips', []):
                turn = 'rotate(%s %s %s) ' % (fmt(-c['angle']), fmt(cx), fmt(cy))
                if pp['flip']:
                    turn += 'rotate(180 %s %s) ' % (fmt(pp['cx'] + ox), fmt(pp['cy'] + oy))
                extras.append(dict(kind='pip', name=pp['name'], box=(cx - hw, cy - hh, cx + hw, cy + hh),
                                   transform=turn + 'translate(%s,%s) ' % (fmt(ox, 3), fmt(oy, 3)) + pp['place']))
            for t in c.get('index', []):
                idx = sorted(sh['initials'])[sh['cards'].index(c)]
                extras.append(dict(kind='glyph', sh=sh, names=[sh['names'][idx]], transforms=[Transform().translate(ox, oy).transform(t)],
                                   box=(cx - hw, cy - hh, cx + hw, cy + hh), colour=sh.get('initial_colours', {}).get(idx, INK)))
        if sh['ln'].get('swash') and sh is shaped[-1]:
            x0b, y0b, x1b, y1b = sh['box']
            extras.append(dict(kind='shape', d=swash_shape(x0b, x1b, oy, cap_s), colour=sh['ln']['swash'] if isinstance(sh['ln']['swash'], str) else INK,
                               box=(x0b - 0.03 * (x1b - x0b), oy, x1b + 0.04 * (x1b - x0b), oy + 0.5 * cap_s)))
        if sh['ln'].get('ribbon'):
            pad_x, pad_y = 0.55 * cap_s, 0.32 * cap_s
            rect = (sh['box'][0] - pad_x, sh['box'][1] - pad_y, sh['box'][2] + pad_x, sh['box'][3] + pad_y)
            extras.append(dict(kind='rect', box=rect, role='ribbon', rx=(rect[3] - rect[1]) / 2))
            sh['box'] = rect
            bottom = rect[3]
        if sh['ln'].get('rules'):
            ry = oy - 0.5 * sh['face'].xh * sh['s']
            gap_r = 0.5 * cap_s
            left_end, right_start = 0.0, block_w
            if sh['ln']['rules'] == 'pips':
                ph = 0.8 * cap_s
                for name, cx in (('spade', ph * 0.55), ('heart', block_w - ph * 0.55)):
                    px0, py0, px1, py1 = pips[name]['box']
                    f = ph / (py1 - py0)
                    w = (px1 - px0) * f
                    extras.append(dict(kind='pip', name=name, box=(cx - w / 2, ry - ph / 2, cx + w / 2, ry + ph / 2),
                                       transform='translate(%s,%s) scale(%s)' % (fmt(cx - (px0 + (px1 - px0) / 2) * f, 3), fmt(ry - (py0 + (py1 - py0) / 2) * f, 3), fmt(f, 5))))
                left_end, right_start = ph * 1.1 + 0.3 * cap_s, block_w - ph * 1.1 - 0.3 * cap_s
            extras.append(dict(kind='rect', role='rule', box=(left_end, ry - RULE / 2, sh['box'][0] - gap_r, ry + RULE / 2), rx=0))
            extras.append(dict(kind='rect', role='rule', box=(sh['box'][2] + gap_r, ry - RULE / 2, right_start, ry + RULE / 2), rx=0))
        y = bottom
    block_top = min(min(sh['box'][1] for sh in shaped), min((e['box'][1] for e in extras), default=0.0))
    block_bot = y
    block_h = block_bot - block_top

    mark = v.get('mark')
    parts = []
    mx = 0.0
    if mark:
        b = boxes[mark]
        mh = block_h * v.get('markScale', 1.0)
        f = mh / b['h']
        mw = b['w'] * f
        gap = v.get('markGap', 0.14) * (mh if v.get('gapOf') == 'mark' else block_h)
        my = block_top + (block_h - mh) / 2 + v.get('markNudge', 0.0) * block_h
        mx = mw + gap
        parts.append(dict(kind='mark', mark=mark, transform='translate(%s,%s) scale(%s)' % (fmt(-b['x'] * f, 3), fmt(my - b['y'] * f, 3), fmt(f, 5)),
                          box=(0, my, mw, my + mh)))
    shift = Transform().translate(mx, 0)
    for e in extras:
        e2 = dict(e)
        e2['box'] = (e['box'][0] + mx, e['box'][1], e['box'][2] + mx, e['box'][3])
        if e['kind'] == 'pip':
            e2['transform'] = 'translate(%s,0) ' % fmt(mx, 3) + e['transform']
        if e.get('rect'):
            x, y, w, h = e['rect']
            e2['rect'] = (x + mx, y, w, h)
            e2['transform'] = 'rotate(%s %s %s)' % (fmt(-e['angle']), fmt(e['cx'] + mx), fmt(e['cy']))
        if e['kind'] == 'glyph':
            e2['transforms'] = [shift.transform(t) for t in e['transforms']]
        if e['kind'] == 'shape':
            e2['transform'] = 'translate(%s,0)' % fmt(mx, 3)
        parts.append(e2)
    for sh in shaped:
        T = [shift.transform(t) for t in sh['T']]
        box = (sh['box'][0] + mx, sh['box'][1], sh['box'][2] + mx, sh['box'][3])
        init = set(sh.get('initials', []))
        if init:
            keep = [i for i in range(len(sh['names'])) if i not in init]
            parts.append(dict(kind='line', sh=sh, names=[sh['names'][i] for i in keep], transforms=[T[i] for i in keep], box=box))
            for i in sorted(init):
                parts.append(dict(kind='line', sh=sh, names=[sh['names'][i]], transforms=[T[i]], box=box, onCard=True, colour=sh.get('initial_colours', {}).get(i, INK)))
        else:
            parts.append(dict(kind='line', sh=sh, transforms=T, box=box))

    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    m = v.get('margin', 0.03) * (ys1 - ys0)
    vb = (xs0 - m, ys0 - m, (xs1 - xs0) + 2 * m, (ys1 - ys0) + 2 * m)
    return dict(parts=parts, vb=vb, block=(block_w, block_h), shaped=shaped, ratio=vb[2] / vb[3], pips=pips)


MH = 100.0  # the mark's height in the middle layout; the words are set by their capital height as a share of it


def capsize(share):
    """The font size (as a share of S) that gives GLCA capitals this share of the mark's height."""
    f = face('glca-500')
    return share * MH / (f.cap / f.upm) / S


def layout_middle(v, boxes, pips):
    """World of to the left of the mark and Card Games to its right, on one baseline, the capitals centred on the mark."""
    left, right = shape_line(v['lines'][0]), shape_line(v['lines'][1])
    b = boxes[v['mark']]
    f = MH / b['h']
    mw = b['w'] * f
    cap_r = right['face'].cap * right['s']
    baseline = MH / 2 + cap_r / 2
    gap = v.get('markGap', 0.38) * cap_r
    parts = []
    x0, y0, x1, y1 = left['ink']
    ox, oy = -x0, baseline
    parts.append(dict(kind='line', sh=left, transforms=[Transform().translate(ox, oy).transform(t) for t in left['t0']], box=(x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
    x = x1 + ox + gap
    parts.append(dict(kind='mark', mark=v['mark'], transform='translate(%s,%s) scale(%s)' % (fmt(x - b['x'] * f, 3), fmt(-b['y'] * f, 3), fmt(f, 5)), box=(x, 0, x + mw, MH)))
    x += mw + gap
    x0, y0, x1, y1 = right['ink']
    ox, oy = x - x0, baseline
    parts.append(dict(kind='line', sh=right, transforms=[Transform().translate(ox, oy).transform(t) for t in right['t0']], box=(x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    m = 0.03 * (ys1 - ys0)
    vb = (xs0 - m, ys0 - m, (xs1 - xs0) + 2 * m, (ys1 - ys0) + 2 * m)
    return dict(parts=parts, vb=vb, block=(xs1 - xs0, MH), shaped=[left, right], ratio=vb[2] / vb[3], pips=pips)


def parse_svg_transform(text):
    """translate(a,b) rotate(t) rotate(t cx cy) scale(k) chains, composed as SVG applies them."""
    T = Transform()
    for op, args in re.findall(r'(\w+)\(([^)]*)\)', text):
        nums = [float(n) for n in re.split(r'[\s,]+', args.strip()) if n]
        if op == 'translate':
            T = T.transform(Transform().translate(nums[0], nums[1] if len(nums) > 1 else 0.0))
        elif op == 'rotate':
            if len(nums) == 3:
                T = T.transform(Transform().translate(nums[1], nums[2]).rotate(math.radians(nums[0])).translate(-nums[1], -nums[2]))
            else:
                T = T.transform(Transform().rotate(math.radians(nums[0])))
        elif op == 'scale':
            T = T.transform(Transform().scale(nums[0], nums[1] if len(nums) > 1 else nums[0]))
    return T


def fan_card_corners(marks, card_id):
    """A fan card's four corners (its own top-left, top-right, bottom-right, bottom-left) in the mark's units."""
    g = marks['fan']
    parent = {c: p for p in g.iter() for c in p}
    card = next(x for x in g.iter(q('g')) if x.get('id') == card_id)
    rect = next(x for x in card if x.tag == q('rect'))
    chain, node = [], card
    while node is not None:
        if node.get('transform'):
            chain.append(node.get('transform'))
        node = parent.get(node)
    T = Transform()
    for t in reversed(chain):
        T = T.transform(parse_svg_transform(t))
    x, y, w, h = (float(rect.get(k)) for k in ('x', 'y', 'width', 'height'))
    return [T.transformPoint(pt) for pt in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]


FAN_CARDS = (('spade', 'small_spade_1'), ('diamond', 'small_diamond_1'), ('second', 'small_clover_1'), ('front', 'small_heart_1'))


def fan_cards(boxes, marks):
    """Every fan card's corners in the layout's units (the fan 100 tall), keyed back to front."""
    b = boxes['fan']
    f = MH / b['h']
    return {k: [((x - b['x']) * f, (y - b['y']) * f) for x, y in fan_card_corners(marks, cid)] for k, cid in FAN_CARDS}


def follow_curve(small, big, x_extra=0.0, curve=1.0):
    """The small line laid along the big line's bowl: on the concentric circle one line-space nearer the bowl's
    centre, starting at the same x as the big line, its letters turned as the big line's are at that point. So
    the two lines are the same curve and the same turn, and the small line, being shorter, rides the falling
    part of it. curve > 1 bends the small line more: its circle shrinks by that factor, kept tangent to the
    concentric one at the start, so it begins at the same point in the same direction and turns faster from
    there. Called after the flat stacking, which gives the lines' distance at the start."""
    ln = big['ln']
    W = big['adv'] * big['s']
    rise = abs(ln['arc']) * W
    R = (W * W / 4 + rise * rise) / (2 * rise)
    L = 2 * R * math.asin(min(1.0, (W / 2) / R))
    d = big['oy'] - small['oy']
    Rp = R - d
    ths = -math.asin(W / (2 * Rp))
    Rp = R - d * math.cos(ths)
    ths = -math.asin(W / (2 * Rp))
    cx, cy = W / 2, -(R - rise)
    R2 = Rp / curve
    cx, cy = cx + (Rp - R2) * math.sin(ths), cy + (Rp - R2) * math.cos(ths)
    x_shift = big['ink_flat'][0] - small['ink_flat'][0] + x_extra
    sm = small['s']
    out = []
    for g, x in zip(small['names'], small['xs']):
        adv = small['face'].hmtx[g][0] * sm
        th = ths + (x * sm + adv / 2 + x_shift) * (L / W) / R2
        px, py = cx + R2 * math.sin(th), cy + R2 * math.cos(th)
        ux, uy = math.cos(th), -math.sin(th)
        out.append(Transform(sm * ux, sm * uy, sm * uy, -sm * ux, px - ux * adv / 2, py - uy * adv / 2))
    small['t0'] = out
    small['ink'] = small['face'].bounds_t(small['names'], out)
    small['ox'], small['oy'] = big['ox'], big['oy']
    small['followed'] = dict(d=d, start_y=cy + R2 * math.cos(ths), end_y=py, slope=math.degrees(-ths), end_slope=math.degrees(-th))


def stem_right(f, gname, share=0.5):
    """The right side of a letter's upright stem, in glyph units: the outline's rightmost crossing of the line at
    half the x-height, where a d or an f has nothing but its stem."""
    from fontTools.pens.recordingPen import RecordingPen
    pen = RecordingPen()
    f.gs[gname].draw(pen)
    y = share * f.xh
    best = [None]

    def seg(a, b):
        if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
            t = (y - a[1]) / (b[1] - a[1])
            x = a[0] + t * (b[0] - a[0])
            best[0] = x if best[0] is None else max(best[0], x)

    def bez(points, n=24):
        out = []
        for i in range(n + 1):
            t = i / n
            P = list(points)
            while len(P) > 1:
                P = [((1 - t) * P[k][0] + t * P[k + 1][0], (1 - t) * P[k][1] + t * P[k + 1][1]) for k in range(len(P) - 1)]
            out.append(P[0])
        return out

    def run(pts):
        for a, b in zip(pts, pts[1:]):
            seg(a, b)

    cur = start = None
    for op, args in pen.value:
        if op == 'moveTo':
            cur = start = args[0]
        elif op == 'lineTo':
            seg(cur, args[0])
            cur = args[0]
        elif op == 'curveTo':
            run(bez([cur] + list(args)))
            cur = args[-1]
        elif op == 'qCurveTo':
            offs, end = list(args[:-1]), args[-1]
            prev = cur
            for i, c in enumerate(offs):
                mid = ((c[0] + offs[i + 1][0]) / 2, (c[1] + offs[i + 1][1]) / 2) if i < len(offs) - 1 else end
                run(bez([prev, c, mid]))
                prev = mid
            if not offs:
                seg(prev, end)
            cur = end
        elif op in ('closePath', 'endPath'):
            if cur is not None and start is not None:
                seg(cur, start)
            cur = None
    return best[0]


def first_ink(sh):
    """The first letter's leftmost ink point, at the letter's mid height, in the line's own coordinates."""
    x0, y0, x1, y1 = sh['face'].bounds_t([sh['names'][0]], [sh['t0'][0]])
    return x0, (y0 + y1) / 2


def layout_block(v, boxes, pips, marks, ref):
    """Both lines flush left as one block, as in 1a, turned as one on 12a.3's line and at 12a.3's size, to the
    right of the fan and centred on the front card. The big line's capitals are capShare of the fan's height
    (12a.3's own share unless the row says otherwise, times size). angle is the block's lean, clockwise. The block
    turns about the midpoint of its left edge, and that point is set on the front card's centre height (place
    'card') or on the midpoint of the card's right edge (place 'edge'). The gap to the fan is measured as the
    keepers measure it, from the fan's box to the leftmost ink (gapFrom 'fan'), or from the card's right edge at
    the block's centre height to the block's left edge (gapFrom 'edge')."""
    tl, tr, br, bl = fan_cards(boxes, marks)['front']
    shaped = [shape_line(ln) for ln in v['lines']]
    big = shaped[-1]
    cap_b = big['face'].cap * big['s']
    y = 0.0
    for i, sh in enumerate(shaped):
        if i:
            y += v.get('gap', 0.14) * cap_b
        x0, y0, x1, y1 = sh['ink']
        sh['ox'], sh['oy'] = -x0, y - y0
        y = y1 + sh['oy']
    angle = v.get('angle', 4)
    if v.get('follow'):
        x_extra = 0.0
        if v.get('startAlign'):
            # the two lines' starts on one line that leans like the card's right edge (so both starts sit the same
            # distance from the card) or square to the lines' own direction at their start
            small_, big_ = shaped[0], shaped[-1]
            dy = (first_ink(big_)[1] + big_['oy']) - (first_ink(small_)[1] + small_['oy'])
            if v['startAlign'] == 'card':
                # the starts on a line leaning like the card's edge, or a share of the way from the block's own vertical to it
                tilt = (math.degrees(math.atan2(tr[0] - br[0], br[1] - tr[1])) - angle) * v.get('startLean', 1.0)
            else:
                W_ = big_['adv'] * big_['s']
                rise_ = abs(big_['ln']['arc']) * W_
                tilt = math.degrees(math.asin(W_ / (2 * ((W_ * W_ / 4 + rise_ * rise_) / (2 * rise_)))))
            x_extra = dy * math.tan(math.radians(tilt))
        follow_curve(shaped[0], shaped[-1], x_extra, v.get('smallCurve', 1.0))
    block_h, block_w = y, max(width(sh['ink']) for sh in shaped)
    k = v.get('capShare', ref['capShare']) * v.get('size', 1.0) * MH / cap_b
    if v.get('anchor') == 'starts':
        sC, sW = first_ink(shaped[-1]), first_ink(shaped[0])
        A = ((sC[0] + shaped[-1]['ox'] + sW[0] + shaped[0]['ox']) / 2, (sC[1] + shaped[-1]['oy'] + sW[1] + shaped[0]['oy']) / 2)
    else:
        A = (0.0, block_h / 2)
    R0 = Transform().rotate(math.radians(angle)).scale(k).translate(-A[0], -A[1])
    corners = [R0.transformPoint(pt) for pt in ((0, 0), (block_w, 0), (block_w, block_h), (0, block_h))]
    b = boxes['fan']
    f = MH / b['h']
    mw = b['w'] * f
    gap = v.get('markGap', 0.16) * MH
    edge_x = lambda yy: tr[0] + (yy - tr[1]) * (br[0] - tr[0]) / (br[1] - tr[1])
    if v.get('place') == 'line':
        # the anchor on the front card's centre line carried on past its edge, the gap measured from the edge at that
        # height; gapAt 'big' measures it to the big line's start instead, so the small line can move without moving it
        mx, my = (tl[0] + tr[0] + br[0] + bl[0]) / 4, (tl[1] + tr[1] + br[1] + bl[1]) / 4
        lean = (tr[1] - tl[1]) / (tr[0] - tl[0])
        offx, offy = 0.0, 0.0
        if v.get('gapAt') == 'big':
            sC = first_ink(shaped[-1])
            offx, offy = R0.transformPoint((sC[0] + shaped[-1]['ox'], sC[1] + shaped[-1]['oy']))
        cy = my
        for _ in range(8):
            ax = edge_x(cy + offy) + gap - offx
            cy = my + (ax - mx) * lean + v.get('nudge', 0.0) * MH
    else:
        cy = (tr[1] + br[1]) / 2 if v.get('place') == 'edge' else (tl[1] + tr[1] + br[1] + bl[1]) / 4
        cy += v.get('nudge', 0.0) * MH
        if v.get('gapFrom') == 'edge':
            ax = edge_x(cy) + gap
        else:
            ax = mw + gap - min(pt[0] for pt in corners)
    R = Transform().translate(ax, cy).transform(R0)
    starts = [R.transformPoint((first_ink(sh)[0] + sh['ox'], first_ink(sh)[1] + sh['oy'])) for sh in (shaped[0], shaped[-1])]
    start_gaps = [pt[0] - edge_x(pt[1]) for pt in starts]
    parts = [dict(kind='mark', mark='fan', transform='translate(%s,%s) scale(%s)' % (fmt(-b['x'] * f, 3), fmt(-b['y'] * f, 3), fmt(f, 5)), box=(0, 0, mw, MH))]
    for sh in shaped:
        T = [R.transform(Transform().translate(sh['ox'], sh['oy']).transform(t)) for t in sh['t0']]
        sh['k'] = k
        sh['T_final'] = T
        parts.append(dict(kind='line', sh=sh, transforms=T, box=sh['face'].bounds_t(sh['names'], T), nocheck=True))
    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    m = 0.03 * (ys1 - ys0)
    vb = (xs0 - m, ys0 - m, (xs1 - xs0) + 2 * m, (ys1 - ys0) + 2 * m)
    big, small = shaped[-1], shaped[0]
    n = len(big['text'].split(' ')[0])
    word = big['face'].bounds_t(big['names'][:n], big['T_final'][:n])
    sm = small['face'].bounds_t(small['names'], small['T_final'])
    fit = dict(small_x0=sm[0], small_x1=sm[2], word_x0=word[0], word_x1=word[2])
    return dict(parts=parts, vb=vb, block=(block_w * k, block_h * k), shaped=shaped, ratio=vb[2] / vb[3], pips=pips, startGaps=start_gaps, anchorAt=(ax, cy), fit=fit)


def layout_wave(v, boxes, pips, marks, ref):
    """The words on one wave with the cards. A sine leaves the front card's top-right corner at the card's own lean
    (waveSlope, degrees; the card's ten unless the row says otherwise), dips to a trough under the words (trough:
    where along the words, 0.5 the middle) and rises again; to the left of the corner it runs back along the
    card's top edge, within a unit. The two lines are parallel offsets of that curve, set inside a band as tall
    as the card, so the band's top edge is the card's top edge carried on and its bottom edge the card's bottom
    edge carried on. Card Games starts markGap from the card's right edge; both starts sit on one line square to
    the wave, which at the start is the card's lean. showGuides draws the band's two edges in red."""
    cards = fan_cards(boxes, marks)
    tl, tr, br, bl = cards['front']
    b = boxes['fan']
    f = MH / b['h']
    mw = b['w'] * f
    shaped = [shape_line(ln) for ln in v['lines']]
    big, small = shaped[-1], shaped[0]
    cap_b = big['face'].cap * big['s']
    y = 0.0
    for i, sh in enumerate(shaped):
        if i:
            y += v.get('gap', 0.14) * cap_b
        x0, y0, x1, y1 = sh['ink']
        sh['ox'], sh['oy'] = -x0, y - y0
        y = y1 + sh['oy']
    block_h = y
    k = v.get('capShare', ref['capShare']) * v.get('size', 1.0) * MH / cap_b
    band = math.hypot(bl[0] - tl[0], bl[1] - tl[1])
    margin = (band - block_h * k) / 2
    lean = math.degrees(math.atan2(tr[1] - tl[1], tr[0] - tl[0]))
    slope = math.tan(math.radians(v.get('waveSlope') or lean))
    gap = v.get('markGap', 0.16) * MH
    edge_x = lambda yy: tr[0] + (yy - tr[1]) * (br[0] - tr[0]) / (br[1] - tr[1])
    offsets = [margin + (sh['oy'] - 0.0) * k for sh in shaped]  # each baseline's distance below the band's top edge

    def build(x_trough):
        lam = 4 * (x_trough - tr[0])
        A = slope * lam / (2 * math.pi)
        xs = [tl[0] + i * 0.5 for i in range(int((tr[0] + 900 - tl[0]) / 0.5))]
        pts, ths = [], []
        for x in xs:
            ph = 2 * math.pi * (x - tr[0]) / lam
            pts.append((x, tr[1] + A * math.sin(ph)))
            ths.append(math.atan(A * (2 * math.pi / lam) * math.cos(ph)))
        curves = {}
        for d in set(offsets + [0.0, band]):
            op = [(px - d * math.sin(th), py + d * math.cos(th)) for (px, py), th in zip(pts, ths)]
            cum = [0.0]
            for (ax, ay), (bx, by) in zip(op, op[1:]):
                cum.append(cum[-1] + math.hypot(bx - ax, by - ay))
            curves[d] = (op, cum)
        return dict(lam=lam, A=A, xs=xs, pts=pts, ths=ths, curves=curves)

    def at(curve, s_):
        op, cum = curve
        j = max(0, min(len(cum) - 2, next((i for i in range(len(cum) - 1) if cum[i + 1] > s_), len(cum) - 2)))
        t = (s_ - cum[j]) / (cum[j + 1] - cum[j]) if cum[j + 1] > cum[j] else 0.0
        return (op[j][0] + t * (op[j + 1][0] - op[j][0]), op[j][1] + t * (op[j + 1][1] - op[j][1])), j, t

    def place(sh, d, s0, W):
        op, cum = W['curves'][d]
        sm, kk = sh['s'], k
        T = []
        for g, x in zip(sh['names'], sh['xs']):
            adv = sh['face'].hmtx[g][0] * sm * kk
            (px, py), j, t = at((op, cum), s0 + x * sm * kk + adv / 2)
            th = W['ths'][j] + t * (W['ths'][min(j + 1, len(W['ths']) - 1)] - W['ths'][j])
            ux, uy = math.cos(th), math.sin(th)
            T.append(Transform(sm * kk * ux, sm * kk * uy, sm * kk * uy, -sm * kk * ux, px - ux * adv / 2, py - uy * adv / 2))
        return T

    def section_s(W, x_guide):
        """The arc length, on every offset curve, of the cross-section through the guide point at x_guide."""
        j = max(0, min(len(W['xs']) - 1, int((x_guide - W['xs'][0]) / 0.5)))
        return {d: W['curves'][d][1][j] for d in W['curves']}

    x_trough = v.get('troughX') or tr[0] + gap + 150.0
    x_start = tr[0] + gap
    for _ in range(6):
        W = build(x_trough)
        for _ in range(6):
            sec = section_s(W, x_start)
            T_big = place(big, offsets[-1], sec[offsets[-1]] + big['ox'] * 0 - 0.0, W)
            cx0, cy0 = first_ink(dict(face=big['face'], names=big['names'], t0=T_big))
            x_start += gap - (cx0 - edge_x(cy0))
        sec = section_s(W, x_start)
        T_big = place(big, offsets[-1], sec[offsets[-1]], W)
        bx0, _, bx1, _ = big['face'].bounds_t(big['names'], T_big)
        x_trough = bx0 + v.get('trough', 0.5) * (bx1 - bx0)
    parts = [dict(kind='mark', mark='fan', transform='translate(%s,%s) scale(%s)' % (fmt(-b['x'] * f, 3), fmt(-b['y'] * f, 3), fmt(f, 5)), box=(0, 0, mw, MH))]
    start_gaps = []
    for sh, d in zip(shaped, offsets):
        # every line's ink starts on the cross-section through the start, so the starts sit square to the wave
        T = place(sh, d, sec[d] + (big['ink_flat'][0] * big['s'] - sh['ink_flat'][0] * sh['s']) * k / (big['s'] * 0 + 1) * 0 + (big['ink_flat'][0] - sh['ink_flat'][0]) * k, W)
        sh['k'] = k
        sh['T_final'] = T
        sx, sy = first_ink(dict(face=sh['face'], names=sh['names'], t0=T))
        start_gaps.append(sx - edge_x(sy))
        parts.append(dict(kind='line', sh=sh, transforms=T, box=sh['face'].bounds_t(sh['names'], T), nocheck=True))
    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    if v.get('showGuides'):
        # the band's edges: over the cards' top corners, along the front card's edges, then the wave to past the words
        end_x = xs1 + 30
        top = [cards['spade'][0], cards['diamond'][0], cards['second'][0], tl] + [pt for pt in W['pts'] if tl[0] <= pt[0] <= end_x]
        bot_op = W['curves'][band][0]
        bot = [cards['spade'][3], bl] + [pt for pt, gx in zip(bot_op, W['xs']) if tl[0] <= gx <= end_x]
        for pts_ in (top, bot):
            parts.append(dict(kind='stroke', d='M' + ' L'.join('%s,%s' % (fmt(x_, 2), fmt(y_, 2)) for x_, y_ in pts_), box=(xs0, ys0, xs1, ys1)))
    m = 0.03 * (ys1 - ys0)
    vb = (xs0 - m, ys0 - m, (xs1 - xs0) + 2 * m, (ys1 - ys0) + 2 * m)
    n = len(big['text'].split(' ')[0])
    word = big['face'].bounds_t(big['names'][:n], big['T_final'][:n])
    smb = small['face'].bounds_t(small['names'], small['T_final'])
    fit = dict(small_x0=smb[0], small_x1=smb[2], word_x0=word[0], word_x1=word[2])
    wave = dict(trough_x=x_trough, depth=W['A'], lam=W['lam'], slope=math.degrees(math.atan(slope)), margin=margin, band=band, text=(bx0, bx1))
    return dict(parts=parts, vb=vb, block=(xs1 - xs0, block_h * k), shaped=shaped, ratio=vb[2] / vb[3], pips=pips, startGaps=start_gaps, anchorAt=(x_trough, tr[1] + W['A']), fit=fit, wave=wave)


CHARS = {}   # key: dict(w, h, b64) for the figures cut from the apps' logos, logo-lab-parts/chars/<key>.webp


def load_chars():
    from PIL import Image
    for q in sorted((HERE / 'chars').glob('*.webp')):
        im = Image.open(q)
        CHARS[q.stem] = dict(w=im.size[0], h=im.size[1], b64=b64(q))
    return CHARS


def layout_swap(v, base):
    """The base row's words as they are, with a figure in the fan's place: the picture scaled to the fan's height,
    its right edge where the fan's box ended, so the words keep their distance from the mark."""
    img = CHARS[v['image']]
    w = MH * img['w'] / img['h']
    mw = next(p for p in base['parts'] if p['kind'] == 'mark')['box'][2]
    parts = [dict(kind='image', image=v['image'], box=(mw - w, 0.0, mw, MH))] + [p for p in base['parts'] if p['kind'] not in ('mark', 'stroke')]
    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    m = 0.03 * (ys1 - ys0)
    vb = (xs0 - m, ys0 - m, (xs1 - xs0) + 2 * m, (ys1 - ys0) + 2 * m)
    lay = dict(base)
    lay.update(parts=parts, vb=vb, ratio=vb[2] / vb[3])
    return lay


TODAY = {}   # today's logotype: the source's outlined Bariol paths and where they sit against the fan


def load_today(text_group, boxes):
    """The words of the logo as the site draws it now: the source file's outlined paths, their box, the capital
    height (the W's), and their place against the fan's box, all in the source's units."""
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.svgLib.path import parse_path
    g = copy.deepcopy(text_group)
    del g.attrib['transform']
    box, cap = None, None
    for el in g.iter():
        d = el.get('d')
        if not d:
            continue
        if 'fill' in el.attrib:
            del el.attrib['fill']
        bp = BoundsPen(None)
        parse_path(d, bp)
        b = bp.bounds
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        if cap is None:
            cap = b[3] - b[1]
    tx, ty = (float(x) for x in re.findall(r'[-\d.]+', text_group.get('transform')))
    fan = boxes['fan']
    TODAY.update(paths=''.join(ser(el) for el in g), box=box, cap=cap, origin=(tx - (fan['x'] + fan['w']), ty - fan['y']), fan_h=fan['h'])
    return TODAY


def layout_today_swap(v, boxes):
    """A figure in the fan's place, with the words of the logo as the site draws it now: the figure scaled to the
    fan's height with its right edge where the fan's box ended, and the words at today's size, distance and height
    against the mark, so only the mark changes."""
    img = CHARS[v['image']]
    mk = MH * v.get('markScale', 1.0)                      # the figure's height against the fan's 100
    w = mk * img['w'] / img['h']
    b = boxes['fan']
    mw = b['w'] * MH / b['h']
    f = MH / TODAY['fan_h']
    x0, y0, x1, y1 = TODAY['box']
    # the words at today's size, today's distance from the mark's box, and centred on the mark as they are on the fan
    ox = mw + TODAY['origin'][0] * f
    oy = TODAY['origin'][1] * f + (mk - MH) / 2
    parts = [dict(kind='image', image=v['image'], box=(mw - w, 0.0, mw, mk)),
             dict(kind='todaytext', transform='translate(%s,%s) scale(%s)' % (fmt(ox, 3), fmt(oy, 3), fmt(f, 5)), box=(ox + x0 * f, oy + y0 * f, ox + x1 * f, oy + y1 * f))]
    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    # today's logo file carries air above and below its art (the art is 0.844 of logo.png), so the fan stands 27px
    # tall in the bar's 32; a row asks for that air with todayAir, else it takes the lab's 3% margin and fills the bar
    mv = ((1 / 0.844 - 1) / 2 if v.get('todayAir') else 0.03) * (ys1 - ys0)
    mh = 0.03 * (ys1 - ys0)
    vb = (xs0 - mh, ys0 - mv, (xs1 - xs0) + 2 * mh, (ys1 - ys0) + 2 * mv)
    return dict(parts=parts, vb=vb, block=(xs1 - xs0, ys1 - ys0), shaped=[], ratio=vb[2] / vb[3], pips=None, capPx=TODAY['cap'] * f * 32 / vb[3], figurePx=(mk * 32 / vb[3], w * 32 / vb[3]))


def layout_any(v, boxes, pips, marks, ref):
    return layout_wave(v, boxes, pips, marks, ref) if v.get('layout') == 'wave' else layout_block(v, boxes, pips, marks, ref)


def render(lay, mode, defs=None, marks=None, ink=INK):
    """mode 'inline': <use> the page's shared marks. mode 'file': a self-contained svg with the mark embedded.
    ink WHITE gives the version for dark grounds: every word white, the ribbon white with words in the ink."""
    dark = ink != INK
    vb = lay['vb']
    body = []
    for p in lay['parts']:
        k = p['kind']
        if k == 'mark':
            if mode == 'inline':
                body.append('<use href="#mark-%s" transform="%s"/>' % (p['mark'], p['transform']))
            else:
                g = copy.deepcopy(marks[p['mark']])
                del g.attrib['id']
                g.set('transform', p['transform'])
                body.append(ser(g))
        elif k == 'rect':
            if p.get('rect'):
                x, y, w, h = p['rect']
                body.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="%s" transform="%s"/>'
                            % (fmt(x), fmt(y), fmt(w), fmt(h), fmt(p['rx']), p['fill'], p['stroke'], fmt(p['stroke_width']), p['transform']))
            else:
                x0, y0, x1, y1 = p['box']
                body.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' % (fmt(x0), fmt(y0), fmt(x1 - x0), fmt(y1 - y0), fmt(p['rx']), ink))
        elif k == 'pip':
            fill = ink if dark or p['name'] in ('spade', 'club') else RED
            body.append('<path d="%s" transform="%s" fill="%s"/>' % (lay['pips'][p['name']]['d'], p['transform'], fill))
        elif k == 'glyph':
            body.append('<path fill="%s" d="%s"/>' % (p.get('colour', INK), p['sh']['face'].path_t(p['names'], p['transforms'])))
        elif k == 'todaytext':
            body.append('<g transform="%s" fill="%s">%s</g>' % (p['transform'], ink if dark else OLD_INK, TODAY['paths']))
        elif k == 'image':
            x0, y0, x1, y1 = p['box']
            href = ('data:image/webp;base64,' + CHARS[p['image']]['b64']) if mode == 'file' else 'logo-lab-parts/chars/%s.webp' % p['image']
            body.append('<image href="%s" x="%s" y="%s" width="%s" height="%s"/>' % (href, fmt(x0), fmt(y0), fmt(x1 - x0), fmt(y1 - y0)))
        elif k == 'stroke':
            body.append('<path fill="none" stroke="%s" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" d="%s"/>' % (RED if not dark else ink, p['d']))
        elif k == 'shape':
            fill = ink if dark else p.get('colour', INK)
            body.append('<path fill="%s" d="%s" transform="%s"/>' % (fill, p['d'], p.get('transform', '')))
        else:
            sh = p['sh']
            ln = sh['ln']
            if p.get('onCard'):
                fill = p.get('colour', INK)
            elif ln.get('ribbon'):
                fill = INK if dark else PAPER
            elif ln.get('colour') and not dark:
                fill = ln['colour']
            else:
                fill = ink
            body.append('<path fill="%s" d="%s"/>' % (fill, sh['face'].path_t(p.get('names', sh['names']), p['transforms'])))
    view = 'viewBox="%s %s %s %s"' % tuple(fmt(x, 2) for x in vb)
    if mode == 'inline':
        return '<svg %s>%s</svg>' % (view, ''.join(body))
    needs_defs = any(p['kind'] == 'mark' and p['mark'] in ('fan', 'flat', 'letterfan') for p in lay['parts'])
    d = ser(defs) if needs_defs and defs is not None else ''
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="%s" xmlns:xlink="%s" %s width="%s" height="%s">%s%s</svg>\n'
            % (SVG_NS, XLINK_NS, view, fmt(vb[2], 2), fmt(vb[3], 2), d, ''.join(body)))


def mark_file(kind, marks, boxes, defs, pad=0.04):
    """A mark on its own, square, for the favicon and app icon study."""
    b = boxes[kind]
    side = max(b['w'], b['h']) * (1 + 2 * pad)
    ox = (side - b['w']) / 2 - b['x']
    oy = (side - b['h']) / 2 - b['y']
    g = copy.deepcopy(marks[kind])
    del g.attrib['id']
    g.set('transform', 'translate(%s,%s)' % (fmt(ox, 3), fmt(oy, 3)))
    d = ser(defs) if kind in ('fan', 'flat') else ''
    return '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="%s" xmlns:xlink="%s" viewBox="0 0 %s %s" width="%s" height="%s">%s%s</svg>\n' % (
        SVG_NS, XLINK_NS, fmt(side, 2), fmt(side, 2), fmt(side, 2), fmt(side, 2), d, ser(g))


# ---------------------------------------------------------------------------------------------------------------
# the variations: B1 at 85%, the small line treated seventeen ways
# ---------------------------------------------------------------------------------------------------------------

def L(text, f, size=1.0, caps=False, tracking=0.0, justify=False, align=None, **kw):
    d = dict(text=text, face=f, size=size, caps=caps, tracking=tracking, justify=justify)
    if align:
        d['align'] = align
    d.update(kw)
    return d


BIG = L('Card Games', 'glca-500', 1.0)
WORDS_AT = 85  # the words' height as a share of the fan's, Holger's pick from round 2


def V(num, name, vid, title, lead, small, gap=0.14, big=None, family=None, **kw):
    v = dict(id=vid, num=num, name=name, title=title, lead=lead, lines=[small, big or BIG], gap=gap, family=family or num.split('.')[0] if not num.startswith('N') else 'N',
             mark='fan', markScale=100.0 / WORDS_AT, markGap=0.16, gapOf='mark')
    v.update(kw)
    return v


FAMILIES = [
    dict(key='1a', title='1 Plain, the first pick; 1a Bolder World of; and 1a a bit less wide', lead='Row 1 is the lab\u2019s first logo, B1 as Holger picked it in round 2: GLCA Medium on both lines, World of at 56% of the big line, the words at 85% of the fan\u2019s height. 1a puts the small line in SemiBold; 1a.5 is 1a with the words at 78% of the fan.'),
    dict(key='12a', title='12a Bowl, and 12a.3', lead='Card Games curving down under World of; in 12a.3 the big line is turned four degrees so it falls away from the front card\u2019s corner. Kept as they are.'),
    dict(key='12f', title='12f.3 Arc onto the words', lead='World of in SemiBold on a gentle arc, the gap closed so the arc\u2019s ends rest on the C and the s. Kept as it is.'),
    dict(key='N', title='N2 A bit wider still, as it was', lead='The closest so far: World of in GLCA SemiBold on a circle tangent to Card Games\u2019 bowl at the start and four fifths its size, its f\u2019s stem three past the d\u2019s, both starts on the card\u2019s lean, Card Games 16 from the card\u2019s edge, the block level on the card\u2019s centre line, the gap between the lines 0.40 of the capitals. Kept for the comparison.'),
    dict(key='O', title='O The words on one wave with the cards', lead='Holger, with a sketch of two red lines: the wavy one is better, but can it feel even more like a wave; if you drew a helping line through the cards and the text, would that make it feel more connected, part of the same wave? So: a sine leaves the front card\u2019s top-right corner at the card\u2019s own lean, dips to a trough under the words and rises again, and to the left of the corner it runs back along the card\u2019s top edge. Both lines are parallel offsets of that one curve, inside a band as tall as the card, so the band\u2019s top edge is the card\u2019s top edge carried on and its bottom edge the card\u2019s bottom edge carried on. Nothing else changes from N2: the size, the weight, the air between the lines, the starts, the gap to the card. One row draws the helping lines.'),
    dict(key='P', title='P The apps\u2019 characters as the mark, with today\u2019s logotype', lead='Holger: the character alone, no cards; the bottom with the same black line as the rest of the character; every character facing away from the words; and the character about 30% bigger against the words, then 15% bigger again, then 10% more, then 20% smaller, with the words at the size they have today. So the queen of Pinochle, the jack of Euchre, the queen of Gin Rummy, the king of Rummy and the joker of Canasta each stand in the fan\u2019s place at 1.32 times the fan\u2019s height, their right edge where the fan\u2019s box ended, with today\u2019s outlined Bariol Bold words at today\u2019s size and distance, centred on the mark; these rows are drawn and barred at the height that keeps the words at today\u2019s size, so the logo stands taller than today\u2019s 32px on the bar. Each character is read off its own layer in the app icon\u2019s Photoshop source with psd-tools, without the card layers and without the group\u2019s drop shadow; its white sticker outline is a stroke on its own group and comes with it. The illustrator\u2019s straight cut at the bottom is finished with rounded corners at 7% of the height, the black line at the thickness of the character\u2019s own line art, and the white outline outside it, so the bottom edge reads like every other edge. The jack and the joker face the words as drawn and are mirrored; the king and the two queens face away as drawn.')
]

SB = L('World of', 'glca-600', 0.56)  # 1a's small line
BOWL = dict(align='center', arc=-0.05)


def H(num, name, vid, title, lead, **kw):
    v = dict(id=vid, num=num, name=name, title=title, lead=lead, family='H', layout='block', mark='fan', follow=True,
             lines=[SB, L('Card Games', 'glca-500', 1.0, arc=-0.05)], gap=0.30, angle=4,
             startAlign='card', anchor='starts', place='line', markGap=0.16)
    v.update(kw)
    return v


def J(num, name, vid, title, lead, **kw):
    d = dict(family='J', gap=0.40, smallCurve=1.5, startLean=0.5)
    d.update(kw)
    return H(num, name, vid, title, lead, **d)


def K(num, name, vid, title, lead, **kw):
    d = dict(family='K', angle=2, startLean=1.0, gapAt='big')
    d.update(kw)
    return J(num, name, vid, title, lead, **d)


def L0(num, name, vid, title, lead, **kw):
    d = dict(family='L', angle=0)
    d.update(kw)
    return K(num, name, vid, title, lead, **d)


def M(num, name, vid, title, lead, **kw):
    d = dict(family='M', smallCurve=1.25, fitTo='word')
    d.update(kw)
    return L0(num, name, vid, title, lead, **d)


def P(num, name, vid, title, lead, image, **kw):
    v = dict(id=vid, num=num, name=name, title=title, lead=lead, family='P', layout='todayswap', image=image, markScale=1.3 * 1.15 * 1.10 * 0.8)
    v.update(kw)
    return v


def O(num, name, vid, title, lead, **kw):
    v = dict(id=vid, num=num, name=name, title=title, lead=lead, family='O', layout='wave', mark='fan',
             lines=[SB, L('Card Games', 'glca-500', 1.0)], gap=0.40, markGap=0.16, trough=0.5, fitTo='stems', fitPast=3.0)
    v.update(kw)
    return v


VARIATIONS = [
    V('1', 'Plain', '01-plain', 'B1 as picked in round 2', 'GLCA Medium on both lines, World of at 56% of the big line, the words at 85% of the fan: the first logo of the lab, and the base of every row after it.', L('World of', 'glca-500', 0.56), family='1a'),
    V('1a', 'Bolder World of', '01a-bolder', 'The small line in GLCA SemiBold', 'World of a weight up, so the small line holds its own against Card Games.', SB),
    V('1a.5', 'A bit less wide', '01a5-narrower', '1a with the words at 78% of the fan', 'The same lockup with the words a little smaller against the fan, so the whole is a little narrower.', SB, family='1a', markScale=100.0 / 78),
    V('12a', 'Bowl', '12a-bowl', 'Card Games curves down, World of stays straight', 'The big line dips like a smile under a straight small line.', L('World of', 'glca-500', 0.52, align='center'), big=L('Card Games', 'glca-500', 1.0, **BOWL), gap=0.14),
    V('12a.3', 'Falling from the card', '12a3-falling', 'The bowl turned four degrees, World of straight', 'The big line starts up by the front card\u2019s corner and falls away to the right, then rises.', L('World of', 'glca-500', 0.52, align='center'), big=L('Card Games', 'glca-500', 1.0, rot=-4, **BOWL), gap=0.14, markNudge=0.04),
    V('12f.3', 'Onto the words', '12f3-hug', 'The bold arc pulled down onto Card Games', 'World of in SemiBold on a gentle arc, the gap closed, so the arc\u2019s ends rest on the C and the s.', L('World of', 'glca-600', 0.52, align='center', arc=0.09), gap=0.02, family='12f'),
    M('N2', 'A bit wider still', 'n2-wider', 'World of on its own circle, the f\u2019s stem three past the d\u2019s', 'As Holger saw it.', family='N', fitTo='stems', fitPast=3.0),
    O('O1', 'One wave', 'o1-wave', 'The words on the wave that leaves the card\u2019s corner at the card\u2019s lean, the trough at the middle of the words', 'The band\u2019s top edge is the front card\u2019s top edge carried on as a sine; World of hangs under it and Card Games sits over the bottom edge, the card\u2019s bottom edge carried on. The wave leaves the corner at ten degrees, dips 18 of the fan\u2019s 100 by the middle of the words, and rises at ten degrees again by their end.'),
    O('O2', 'One wave, the helping lines drawn', 'o2-wave-lines', 'O1 with the band\u2019s two edges drawn in red', 'The construction, as in the sketch: one line over the cards\u2019 corners and along the front card\u2019s top edge into the wave, one along the card\u2019s bottom edge into the same wave a card\u2019s height lower.', showGuides=True),
    O('O3', 'The trough later', 'o3-trough-later', 'O1 with the trough at six tenths of the words', 'The wave falls longer and rises shorter, so the trough sits under the G, as the top line of the sketch has it. A later trough on the same slope is also a deeper one.', trough=0.62),
    O('O4', 'A deeper wave', 'o4-deeper', 'O1 leaving the corner at fourteen degrees instead of the card\u2019s ten', 'The same trough, a steeper fall into it and a steeper rise out, so the words dip more; the wave no longer lies on the card\u2019s top edge but leaves its corner a little more steeply than the edge.', waveSlope=14.0),
    O('O5', 'The trough earlier', 'o5-trough-earlier', 'O1 with the trough at four tenths of the words', 'The wave falls shorter and rises longer, so the trough sits under the r, as the bottom line of the sketch has it.', trough=0.38),
    P('P1', 'The queen of Pinochle', 'p1-pinochle-queen', 'Pinochle\u2019s queen in the fan\u2019s place, with today\u2019s words', 'The black-haired queen with her spade sceptre, as drawn, facing away from the words.', 'pinochle'),
    P('P2', 'The jack of Euchre', 'p2-euchre-jack', 'Euchre\u2019s jack in the fan\u2019s place, with today\u2019s words', 'The curly jack with his staff, mirrored to face away from the words.', 'euchre'),
    P('P3', 'The queen of Gin Rummy', 'p3-ginrummy-queen', 'Gin Rummy\u2019s queen in the fan\u2019s place, with today\u2019s words', 'The fair queen with her heart sceptre, as drawn, facing away from the words.', 'ginrummy'),
    P('P4', 'The king of Rummy', 'p4-rummy-king', 'Rummy\u2019s king in the fan\u2019s place, with today\u2019s words', 'The king of spades with his sword, as drawn, facing away from the words.', 'rummy'),
    P('P5', 'The joker of Canasta', 'p5-canasta-joker', 'Canasta\u2019s joker in the fan\u2019s place, with today\u2019s words', 'The joker in his cap, mirrored to face away from the words.', 'canasta'),
]
TODAY_W32 = 170  # logo.png, 510x96, drawn at 32px


# ---------------------------------------------------------------------------------------------------------------
# the pages
# ---------------------------------------------------------------------------------------------------------------

def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode('ascii')


def fonts_css():
    seen = set()
    out = []
    for key, spec in FACES.items():
        k = (spec['family'], spec['weight'])
        if k in seen:
            continue
        seen.add(k)
        ext = Path(spec['web']).suffix.lstrip('.')
        kind = {'woff2': 'woff2', 'woff': 'woff', 'ttf': 'truetype', 'otf': 'opentype'}[ext]
        out.append('@font-face { font-family: "%s"; font-weight: %d; font-style: normal; src: url(data:font/%s;base64,%s) format("%s"); }'
                   % (spec['family'], spec['weight'], ext, b64(spec['web']), kind))
    return '\n'.join(out)


def cap_px(lay, sh, h):
    """The cap height of a shaped line, in px, when the whole logo is h px tall."""
    return sh['face'].cap * sh['s'] * sh.get('k', 1.0) * h / lay['vb'][3]


ROW = '''
<section class="ll-row" id="%(id)s">
  <div class="ll-row-name"><span class="ll-num">%(num)s</span><h2>%(name)s</h2><span class="ll-sub">%(title)s</span></div>
  <div class="ll-row-head">
    <div class="ll-draw">%(svg)s</div>
    <div class="ll-row-words"><p>%(lead)s</p><span>%(note)s</span></div>
  </div>
  <div class="ll-pair">
    <iframe class="ll-bar" data-v="%(vkey)s" data-h="%(h)s" src="logo-lab-bar.html?v=%(vkey)s" width="940" height="57" loading="lazy" scrolling="no" title="The bar at a desktop width"></iframe>
    <iframe class="ll-bar" data-v="%(vkey)s" data-h="%(h)s" src="logo-lab-bar.html?v=%(vkey)s" width="390" height="57" loading="lazy" scrolling="no" title="A phone"></iframe>
  </div>
</section>'''


TODAY_FAN_PX = 32 * 0.844        # the fan's height on the bar today: logo.png's art is 0.844 of the 32px file
TODAY_DRAW_UNITS = 900 / 862.5 * MH   # the today row's drawing is 900 file units tall for the fan's 862.5


def row(v, lay, svg):
    if v.get('layout') == 'todayswap':
        # drawn and barred so that today's words keep today's size: the drawing and the bar grow with the mark
        units = lay['vb'][3]
        bar_h = TODAY_FAN_PX * units / MH
        draw_h = 64 * units / TODAY_DRAW_UNITS
        svg = svg.replace('<svg ', '<svg style="height:%spx" ' % fmt(draw_h, 0), 1)
        note = ('On the bar: %s px tall (today 32) and %s px wide (today 170), the figure %s px tall and %s px wide, the capitals %s px tall as today. On a phone: %s px wide. File: logo-lab-out/%s.svg'
                % (fmt(bar_h, 0), fmt(lay['ratio'] * bar_h, 0), fmt(lay['figurePx'][0] * bar_h / 32, 0), fmt(lay['figurePx'][1] * bar_h / 32, 0), fmt(lay['capPx'] * bar_h / 32, 0), fmt(lay['ratio'] * bar_h * 24 / 32, 0), v['id']))
        return ROW % dict(id=v['id'], vkey=v['id'], num=v['num'], name=escape(v['name']), title=escape(v['title']), lead=escape(v['lead']), note=escape(note), svg=svg, h=fmt(bar_h, 0))
    small, big = lay['shaped'][0], lay['shaped'][-1]
    if len(lay['shaped']) == 1:
        note = ('On the bar: %s px wide (today 170), the capitals %s px tall. On a phone: %s px wide. File: logo-lab-out/%s.svg'
                % (fmt(lay['ratio'] * 32, 0), fmt(cap_px(lay, big, 32), 0), fmt(lay['ratio'] * 24, 0), v['id']))
    elif v.get('layout') == 'middle':
        note = ('On the bar: %s px wide (today 170), World of\u2019s capitals %s px tall, Card Games\u2019 %s px. On a phone: %s px wide. File: logo-lab-out/%s.svg'
                % (fmt(lay['ratio'] * 32, 0), fmt(cap_px(lay, small, 32), 0), fmt(cap_px(lay, big, 32), 0), fmt(lay['ratio'] * 24, 0), v['id']))
    elif v.get('layout') in ('block', 'wave', 'swap'):
        note = ('On the bar: %s px wide (today 170), the fan %s px tall, the big line\u2019s capitals %s px tall, the small line\u2019s %s px. On a phone: %s px wide. File: logo-lab-out/%s.svg'
                % (fmt(lay['ratio'] * 32, 0), fmt(MH * 32 / lay['vb'][3], 0), fmt(cap_px(lay, big, 32), 0), fmt(cap_px(lay, small, 32), 0), fmt(lay['ratio'] * 24, 0), v['id']))
    else:
        note = ('On the bar: %s px wide (today 170), the big line\u2019s capitals %s px tall, the small line\u2019s %s px. On a phone: %s px wide. File: logo-lab-out/%s.svg'
                % (fmt(lay['ratio'] * 32, 0), fmt(cap_px(lay, big, 32), 0), fmt(cap_px(lay, small, 32), 0), fmt(lay['ratio'] * 24, 0), v['id']))
    return ROW % dict(id=v['id'], vkey=v['id'], num=v['num'], name=escape(v['name']), title=escape(v['title']), lead=escape(v['lead']), note=escape(note), svg=svg, h='32')


def today_row(text_group):
    """Row 0: the logo as the bar draws it now. The drawing is the source art; the bars draw the site's logo.png."""
    svg = ('<svg viewBox="0 190 5464 900"><use href="#mark-fan" transform="translate(-102,0)"/><g transform="translate(1246.9,288)">%s</g></svg>'
           % ''.join(ser(el) for el in text_group))
    return ROW % dict(id='00-today', vkey='today', num='0', name='Today', title='The logo as it is', svg=svg, h='32',
                      lead='The fan and World of Card Games on one line in Bariol Bold, as the bar draws it now.',
                      note='On the bar: 170 px wide, its capitals about 9 px tall. On a phone: 128 px wide. File: the site\u2019s static/images/logo.png')


def toc_html(variations):
    return ''.join('<a href="#%s"><span class="ll-num">%s</span>%s</a>' % (v['id'], v['num'], escape(v['name'])) for v in variations)


def grouped(rows_by_id):
    out = []
    for fam in FAMILIES:
        out.append('<h2 class="ll-fam" id="fam-%s">%s</h2><p class="ll-desc">%s</p>' % (fam['key'], escape(fam['title']), escape(fam['lead'])))
        out += [rows_by_id[v['id']] for v in VARIATIONS if v['family'] == fam['key']]
    return ''.join(out)


def page_html(rows_html, defs, marks, toc):
    return PAGE % dict(defs=hidden_defs(defs, {k: marks[k] for k in ('fan', 'happycard', 'smileheart', 'jokercap', 'friends', 'kingcard')}), rows=rows_html, toc=toc, css=CSS, js=JS)


def check_html(rows):
    return CHECK % dict(fonts=fonts_css(), rows=''.join(rows))


CHECK_ROW = ('<div class="row"><b>%s line %s</b> <span class="d" data-adv="%s"></span><svg %s width="%s" height="%s">'
             '<path fill="#000" opacity=".55" d="%s"/>'
             '<text x="%s" y="%s" font-family="%s" font-weight="%d" font-size="%s" letter-spacing="%s" fill="#d51a22" opacity=".55">%s</text></svg></div>')


# ---------------------------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------------------------

def main():
    root, defs, logo, text_group = load_source()
    marks = build_marks(logo)
    pips = pip_paths(logo)
    marks.update(sketch_marks(pips))
    if '--measure' in sys.argv or not MARKS_JSON.exists():
        boxes = measure_marks(defs, marks)
        print('measured:', {k: (round(b['w']), round(b['h'])) for k, b in boxes.items()})
    else:
        boxes = json.loads(MARKS_JSON.read_text())
    boxes['letterfan'] = boxes['fan']

    OUT.mkdir(exist_ok=True)
    for old in OUT.glob('*.svg'):
        old.unlink()
    (OUT / 'mark-fan.svg').write_text(mark_file('fan', marks, boxes, defs))
    # the bar page's images, copied from the site so the page works online where the static symlink does not exist
    STATIC.mkdir(exist_ok=True)
    for src, name in BAR_IMAGES:
        (STATIC / name).write_bytes((WOCG / 'static' / src).read_bytes())

    # 12a.3's text size, the big line's capitals as a share of the fan's height, for the rows built on it
    lay_ref = layout(next(v for v in VARIATIONS if v['num'] == '12a.3'), boxes, pips)
    mark_ref = next(p for p in lay_ref['parts'] if p['kind'] == 'mark')['box']
    big_ref = lay_ref['shaped'][-1]
    ref = dict(capShare=big_ref['face'].cap * big_ref['s'] / (mark_ref[3] - mark_ref[1]))
    print('12a.3 capitals: %.3f of the fan' % ref['capShare'])

    load_chars()
    load_today(text_group, boxes)
    rows = {}
    check_rows = []
    lays = {}
    for v in VARIATIONS:
        if v.get('layout') == 'todayswap':
            lay = layout_today_swap(v, boxes)
            lays[v['id']] = lay
            (OUT / ('%s.svg' % v['id'])).write_text(render(lay, 'file', defs, marks))
            (OUT / ('%s-white.svg' % v['id'])).write_text(render(lay, 'file', defs, marks, ink=WHITE))
            rows[v['id']] = row(v, lay, render(lay, 'inline'))
            print('%-22s %3s px on the bar, the figure %s px tall and %s px wide, the capitals %s px' % (v['id'], fmt(lay['ratio'] * 32, 0), fmt(lay['figurePx'][0], 0), fmt(lay['figurePx'][1], 0), fmt(lay['capPx'], 1)))
            continue
        if v.get('swapOf'):
            lay = layout_swap(v, lays[v['swapOf']])
            lays[v['id']] = lay
            (OUT / ('%s.svg' % v['id'])).write_text(render(lay, 'file', defs, marks))
            (OUT / ('%s-white.svg' % v['id'])).write_text(render(lay, 'file', defs, marks, ink=WHITE))
            rows[v['id']] = row(v, lay, render(lay, 'inline'))
            print('%-22s %3s px on the bar, the figure %s px wide' % (v['id'], fmt(lay['ratio'] * 32, 0), fmt(MH * 32 / lay['vb'][3] * CHARS[v['image']]['w'] / CHARS[v['image']]['h'], 0)))
            continue
        if v.get('fitTo') in ('word', 'stems'):
            # World of sized so that it ends over the end of Card ('word': the f's ink on the d's ink; 'stems': the right
            # side of the f's stem on the right side of the d's stem), its start left where the start rule puts it
            v['lines'] = [dict(v['lines'][0]), v['lines'][1]]
            for _ in range(8):
                lay = layout_any(v, boxes, pips, marks, ref)
                f_ = lay['fit']
                if v['fitTo'] == 'stems':
                    small, big = lay['shaped'][0], lay['shaped'][-1]
                    n = len(big['text'].split(' ')[0])
                    xd = big['T_final'][n - 1].transformPoint((stem_right(big['face'], big['names'][n - 1]), 0.5 * big['face'].xh))[0]
                    xf = small['T_final'][-1].transformPoint((stem_right(small['face'], small['names'][-1]), 0.5 * small['face'].xh))[0]
                    have, want = xf - f_['small_x0'], xd + v.get('fitPast', 0.0) - f_['small_x0']
                    f_.update(f_stem=xf, d_stem=xd)
                else:
                    have, want = f_['small_x1'] - f_['small_x0'], f_['word_x1'] - f_['small_x0']
                if abs(have - want) < 0.05:
                    break
                v['lines'][0]['size'] *= want / have
            print('%-22s World of fitted to Card: size %.3f of the big line (was 0.56); it starts %.1f right of the C and ends %.1f right of the d'
                  % (v['id'], v['lines'][0]['size'], f_['small_x0'] - f_['word_x0'], f_['small_x1'] - f_['word_x1']))
            if 'f_stem' in f_:
                print('%-22s the f\'s stem ends %.2f right of the d\'s stem; the f\'s hook reaches %.1f past its stem' % (v['id'], f_['f_stem'] - f_['d_stem'], f_['small_x1'] - f_['f_stem']))
        lay = (layout_any(v, boxes, pips, marks, ref) if v.get('layout') in ('block', 'wave') else layout_badge(v, boxes, pips) if v.get('layout') == 'badge'
               else layout_middle(v, boxes, pips) if v.get('layout') == 'middle' else layout(v, boxes, pips))
        if lay.get('fit') and not v.get('fitTo'):
            f_ = lay['fit']
            print('%-22s World of starts %.1f right of the C and ends %.1f right of the d' % (v['id'], f_['small_x0'] - f_['word_x0'], f_['small_x1'] - f_['word_x1']))
        lays[v['id']] = lay
        (OUT / ('%s.svg' % v['id'])).write_text(render(lay, 'file', defs, marks))
        (OUT / ('%s-white.svg' % v['id'])).write_text(render(lay, 'file', defs, marks, ink=WHITE))
        rows[v['id']] = row(v, lay, render(lay, 'inline'))
        for p in lay['parts']:
            if p['kind'] != 'line':
                continue
            sh = p['sh']
            ln = sh['ln']
            if ln.get('arc') or ln.get('rot') or ln.get('initials') or ln.get('bigInitials') or p.get('onCard') or p.get('nocheck'):
                continue  # the browser cannot draw these flat, so the flat shaping is checked through the other rows
            px = S * ln.get('size', 1.0)
            spacing = (ln.get('tracking', 0.0) * sh['face'].upm + sh['extra']) * sh['s']
            spec = FACES[ln['face']]
            x0, y0, x1, y1 = p['box']
            ox, oy = p['transforms'][0].dx - sh['xs'][0] * sh['s'], p['transforms'][0].dy
            vb = 'viewBox="%s %s %s %s"' % (fmt(x0 - 4), fmt(y0 - 4), fmt(x1 - x0 + 8), fmt(y1 - y0 + 8))
            check_rows.append(CHECK_ROW % (
                v['id'], sh['text'], fmt(sh['adv'] * sh['s'], 3), vb, fmt(x1 - x0 + 8), fmt(y1 - y0 + 8),
                sh['face'].path_t(sh['names'], p['transforms']),
                fmt(ox, 3), fmt(oy, 3), spec['family'], spec['weight'], fmt(px), fmt(spacing, 3), escape(sh['text'])))
        if lay.get('startGaps'):
            print('%-22s World of starts %.1f right of the card\'s edge, Card Games %.1f; the block\'s midpoint at y %.1f of the fan\'s 100'
                  % (v['id'], lay['startGaps'][0], lay['startGaps'][1], lay['anchorAt'][1]))
        if lay.get('wave'):
            wv = lay['wave']
            print('%-22s the wave: leaves the corner at %.1f degrees, the trough %.1f below the corner at x %.0f (%.2f of the words), the band %.1f with %.1f of air above and below the words'
                  % (v['id'], wv['slope'], wv['depth'], wv['trough_x'], (wv['trough_x'] - wv['text'][0]) / (wv['text'][1] - wv['text'][0]), wv['band'], wv['margin']))
        fl = lay['shaped'][0].get('followed')
        if fl:
            print('%-22s World of on the curve: %.1f above Card Games at the start, %.1f at its end; falling %.1f degrees at the start, %.1f at its end (before the block\'s turn)'
                  % (v['id'], -fl['start_y'], -fl['end_y'], fl['slope'], fl['end_slope']))
        print('%-22s %3s px on the bar, big capitals %2s px, small %s px'
              % (v['id'], fmt(lay['ratio'] * 32, 0), fmt(cap_px(lay, lay['shaped'][-1], 32), 0), fmt(cap_px(lay, lay['shaped'][0], 32), 0)))

    today = ('<h2 class="ll-fam" id="fam-0">0 Today</h2><p class="ll-desc">The logo as the site draws it now: the fan and World of Card Games on one line in Bariol Bold, 32px tall on the bar. Every row below is measured against it.</p>'
             + today_row(text_group))
    toc = '<a href="#00-today"><span class="ll-num">0</span>Today</a>' + toc_html(VARIATIONS)
    (ROOT / 'logo-lab.html').write_text(page_html(today + grouped(rows), defs, marks, toc))
    (ROOT / 'logo-lab-bar.html').write_text(BAR)
    (ROOT / 'logo-lab-check.html').write_text(check_html(check_rows))
    print('wrote logo-lab.html (%d KB), logo-lab-bar.html, logo-lab-check.html, %d files in logo-lab-out/'
          % ((ROOT / 'logo-lab.html').stat().st_size // 1024, len(list(OUT.glob('*.svg')))))


# ---------------------------------------------------------------------------------------------------------------
# the page's own chrome. Every class starts with ll-, which site.css never declares.
# ---------------------------------------------------------------------------------------------------------------

CSS = r'''
  :root { --ll-paper: #f9f6f2; --ll-band: #f4eee5; --ll-ink: #141414; --ll-label: #4e4d4c; --ll-quiet: #67635c; --ll-line: #d2cfca; --ll-soft: #ebe7de; }
  html, body { margin: 0; }
  body { background: var(--ll-paper); color: var(--ll-ink); font: 16px/24px "BuloRounded", "Verdana", sans-serif; -webkit-font-smoothing: antialiased; }
  .ll-head { position: sticky; top: 0; z-index: 5; display: flex; align-items: center; flex-wrap: wrap; gap: 8px 20px; padding: 12px 28px 10px; background: rgba(249, 246, 242, .96); box-shadow: 0 1px 0 var(--ll-line); }
  .ll-head h1 { margin: 0; font: 500 26px/32px "GLCA", Georgia, serif; }
  .ll-head p { margin: 0; color: var(--ll-label); font-size: 14px; line-height: 20px; max-width: 900px; }
  .ll-switches { margin-left: auto; display: flex; gap: 8px; }
  .ll-switches button { border: 0; border-radius: 16px; padding: 5px 14px; cursor: pointer; font: 700 14px/20px "BuloRounded", Verdana, sans-serif; background: #e4ddd0; color: var(--ll-ink); box-shadow: inset 0 0 0 1px #c9c0ae; }
  .ll-switches button.on { background: var(--ll-ink); color: #fff; box-shadow: none; }
  .ll-page { padding: 8px 28px 96px; }
  .ll-fam { font: 500 30px/36px "GLCA", Georgia, serif; margin: 44px 0 6px; }
  .ll-desc { color: var(--ll-label); font-size: 14px; line-height: 20px; max-width: 900px; margin: 0 0 4px; }
  .ll-row { margin: 0; padding: 26px 0 32px; border-top: 1px solid var(--ll-line); }
  .ll-row:first-of-type { border-top: 0; padding-top: 14px; }
  .ll-row-name { display: flex; align-items: center; gap: 12px; margin: 0 0 14px; }
  .ll-row-name h2 { margin: 0; font: 500 26px/32px "GLCA", Georgia, serif; }
  .ll-row-name .ll-sub { color: var(--ll-quiet); font-size: 14px; line-height: 20px; padding-top: 4px; }
  .ll-num { display: inline-flex; align-items: center; justify-content: center; min-width: 30px; height: 26px; padding: 0 9px; border-radius: 13px; background: var(--ll-ink); color: #fff; font: 700 14px/26px "BuloRounded", Verdana, sans-serif; box-sizing: border-box; }
  .ll-toc { display: flex; flex-wrap: wrap; gap: 8px 10px; margin: 14px 0 10px; font-size: 14px; }
  .ll-toc a { display: inline-flex; align-items: center; gap: 7px; color: var(--ll-ink); text-decoration: none; padding: 3px 11px 3px 3px; border-radius: 16px; background: #fff; box-shadow: inset 0 0 0 1px var(--ll-line); font-weight: 700; }
  .ll-toc a:hover { background: var(--ll-band); }
  .ll-toc .ll-num { min-width: 24px; height: 20px; font-size: 12px; line-height: 20px; padding: 0 7px; border-radius: 10px; }
  .ll-row-head { display: flex; align-items: center; gap: 18px; margin: 0 0 10px; }
  .ll-draw { flex: none; display: flex; align-items: center; height: 88px; padding: 0 14px; background: var(--ll-band); border-radius: 10px; corner-shape: squircle; }
  .ll-draw svg { height: 64px; width: auto; display: block; }
  .ll-row-words p { margin: 0 0 2px; font-size: 14px; line-height: 20px; color: var(--ll-label); max-width: 760px; }
  .ll-row-words span { font-size: 12px; line-height: 16px; color: var(--ll-quiet); }
  .ll-pair { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-start; }
  .ll-bar { display: block; border: 0; border-radius: 8px; background: var(--ll-band); box-shadow: inset 0 0 0 1px var(--ll-line); }
  .ll-zoom .ll-pair { transform: scale(2); transform-origin: 0 0; margin-bottom: 69px; flex-wrap: nowrap; }
  .ll-files { margin: 28px 0 0; font-size: 13px; line-height: 18px; color: var(--ll-quiet); max-width: 900px; }
  .ll-files code { font: 12px/16px ui-monospace, Menlo, monospace; }
'''

JS = r'''
(function () {
  // three switches: today's logo in every bar (to compare), the logo 40px tall instead of 32 (the bar is 56),
  // and the bars at twice their size
  var today = false, tall = false, zoom = false;
  var bToday = document.getElementById('llToday'), bTall = document.getElementById('llTall'), bZoom = document.getElementById('llZoom');
  function paint() {
    bToday.textContent = today ? 'Showing today’s logo in the bars' : 'Show today’s logo in the bars';
    bToday.classList.toggle('on', today);
    bTall.textContent = tall ? 'Logo 40px tall in the bars' : 'Logo 32px tall in the bars';
    bTall.classList.toggle('on', tall);
    bZoom.textContent = zoom ? 'Bars at 2x' : 'Bars at 1x';
    bZoom.classList.toggle('on', zoom);
    document.body.classList.toggle('ll-zoom', zoom);
    document.querySelectorAll('iframe.ll-bar').forEach(function (f) {
      // a row may ask for its own height (the figure rows keep today's words at today's size, so they stand taller);
      // the 40px switch scales every row by the same 1.25
      var base = today ? 32 : parseInt(f.getAttribute('data-h') || '32', 10);
      var h = tall ? Math.round(base * 1.25) : base;
      var want = 'logo-lab-bar.html?v=' + (today ? 'today' : f.getAttribute('data-v')) + (h !== 32 ? '&h=' + h : '');
      if (f.getAttribute('src') !== want) f.setAttribute('src', want);
    });
  }
  bToday.addEventListener('click', function () { today = !today; paint(); });
  bTall.addEventListener('click', function () { tall = !tall; paint(); });
  bZoom.addEventListener('click', function () { zoom = !zoom; paint(); });
  paint();
})();
'''

PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<!-- Generated by logo-lab-parts/make.py. Edit make.py, then run it. -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The logo: B1, the small line &middot; lab</title>
<link rel="stylesheet" href="guide-fonts.css">
<style>
%(css)s
</style>
</head>
<body>
%(defs)s
<header class="ll-head">
  <h1>The logo: the words on one wave with the cards</h1>
  <p>Holger, 28 Sep, with a sketch: the wavy one is better, but can it feel even more like a wave; if you drew a helping line through the cards and the text, would that help it feel more connected, part of the same wave? So: the two lines on one sine that leaves the front card&rsquo;s corner at the card&rsquo;s own lean and runs back along its top edge, inside a band as tall as the card, five ways: the trough at the middle, the helping lines drawn, the trough later, a deeper wave, the trough earlier. N2 is kept as it was. Then, at his next word, the apps&rsquo; characters as the mark: the queen of Pinochle, the jack of Euchre, the queen of Gin Rummy, the king of Rummy and the joker of Canasta, each alone without the cards, read off its Photoshop layer with no shadow, its bottom finished with rounded corners and the black line, facing away from the words, at 1.32 times the fan&rsquo;s height beside the words of the logo the site uses now, at their size today. The keepers stay as they are. Every row has a number and a name (say &ldquo;O3&rdquo;). Each row: the logo at 64px, then the site&rsquo;s bar at a desktop width with the logo 32px tall, and a phone with it 24px tall.</p>
  <div class="ll-switches"><button id="llToday" type="button"></button><button id="llTall" type="button"></button><button id="llZoom" type="button"></button></div>
</header>
<main class="ll-page">
  <nav class="ll-toc">%(toc)s</nav>
%(rows)s
  <p class="ll-files">Every row is a file: <code>logo-lab-out/12-arc.svg</code>, <code>10-rules.svg</code> and so on, with a <code>-white</code> copy for dark grounds. The type is outlined, so they need no font. The switch for 40px shows what the bar could draw if the logo were allowed more of its 56px.</p>
</main>
<script>
%(js)s
</script>
</body>
</html>
'''

BAR = r'''<!DOCTYPE html>
<html lang="en">
<head>
<!-- Generated by logo-lab-parts/make.py. The site's menubar, drawn by site.css, with a logo picked by ?v=<id> (today: logo.png); &h=40 draws it 40px tall. -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="guide-fonts.css">
<link rel="stylesheet" href="site.css">
<style>
  html, body { margin: 0; background: #f4eee5; overflow: hidden; }
  /* the burger and its cross from the tracked copies, so the page works online, where the static symlink does not exist */
  #root { --wm-icon-menuBurger: url("logo-lab-static/wm-menuBurger.svg"); --wm-icon-menuClose: url("logo-lab-static/wm-menuClose.svg"); }
</style>
</head>
<body>
<div class="site wm" id="root">
  <nav id="menuBarContainer" class="mbcenter" aria-label="Main navigation">
    <a id="menuLogoContainer" href="#"><img src="logo-lab-static/logo.png" alt="World of Card Games" width="170" height="32" /></a>
    <div id="menuIconContainer" data-wocg-press-release="true"><span>Games</span></div>
    <ul id="menuBar">
      <li class="mclink mgames"><span>Games<span class="mtri" aria-hidden="true"></span></span></li>
      <li class="mclink"><a href="#">Rules</a></li>
      <li class="mclink"><a href="#">Leaderboards</a></li>
      <li><a href="#">Hearts</a></li>
      <li><a href="#">Spades</a></li>
    </ul>
    <div id="userBarContainer">
      <ul id="userBar">
        <li class="activityIcon displayInline"><img class="activityIconImg loaded" src="logo-lab-static/menuActivity.svg" alt="Activity" width="40" height="32" /></li>
        <li class="friendsIcon displayInline"><img class="friendsIconImg loaded" src="logo-lab-static/menuFriends.svg" alt="Friends" width="40" height="32" /></li>
        <li class="userAvatarContainer displayInline loggedIn">
          <span class="avFoot"><img class="userAvatar loaded" src="logo-lab-static/WomanGirl2.svg" alt="User avatar" width="24" height="24" /></span>
          <span class="userName">Ann</span>
        </li>
      </ul>
    </div>
  </nav>
</div>
<script>
  var q = new URLSearchParams(location.search), v = q.get('v') || 'today', h = parseInt(q.get('h') || '0', 10);
  var img = document.querySelector('#menuLogoContainer img');
  if (v !== 'today') { img.removeAttribute('width'); img.removeAttribute('height'); img.src = 'logo-lab-out/' + v + '.svg'; }
  // logo-lab-static/ holds copies of the bar's images from worldofcardgames/static, made by make.py
  if (h) {
    // the site draws the logo 32px tall, 24 under 860px; this scales both by the same share
    var s = document.createElement('style');
    s.textContent = '#menuLogoContainer img { height: ' + h + 'px !important; } @media (max-width: 860px) { #menuLogoContainer img { height: ' + Math.round(h * 24 / 32) + 'px !important; } }';
    document.head.appendChild(s);
  }
</script>
</body>
</html>
'''

CHECK = r'''<!DOCTYPE html>
<html lang="en">
<head>
<!-- Generated by logo-lab-parts/make.py. The agent's check: every outlined flat line (black) over the browser's own text (red). One dark shape means they agree. -->
<meta charset="UTF-8">
<style>
%(fonts)s
body { margin: 16px; font: 13px/18px Menlo, monospace; background: #fff; }
.row { margin: 0 0 10px; }
.row b { display: inline-block; min-width: 260px; }
.row .d { color: #67635c; }
.row svg { display: block; margin-top: 2px; }
</style>
</head>
<body>
<pre id="out"></pre>
%(rows)s
<script>
document.fonts.ready.then(function () {
  var lines = [];
  document.querySelectorAll('.row').forEach(function (r) {
    var t = r.querySelector('text'), want = parseFloat(r.querySelector('.d').getAttribute('data-adv'));
    var got = t.getComputedTextLength() - parseFloat(t.getAttribute('letter-spacing') || 0);
    var diff = got - want;
    r.querySelector('.d').textContent = 'shaped ' + want.toFixed(2) + '  browser ' + got.toFixed(2) + '  diff ' + diff.toFixed(2);
    lines.push({ line: r.querySelector('b').textContent, want: +want.toFixed(2), got: +got.toFixed(2), diff: +diff.toFixed(2) });
  });
  document.getElementById('out').textContent = JSON.stringify(lines);
});
</script>
</body>
</html>
'''

if __name__ == '__main__':
    main()
