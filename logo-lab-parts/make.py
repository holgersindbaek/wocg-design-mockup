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
    return marks


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
        rise = arc * W
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
            out.append(Transform(s * ux, s * uy, s * uy, -s * ux, px - ux * adv / 2, py - uy * adv / 2))
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


def layout(v, boxes, pips):
    """Shape and stack the lines, add rules, pips or a ribbon, place the mark."""
    shaped = [shape_line(ln) for ln in v['lines']]

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
        else:
            ox = -x0
        oy = y - y0
        sh['ox'], sh['oy'] = ox, oy
        sh['T'] = [Transform().translate(ox, oy).transform(t) for t in sh['t0']]
        sh['box'] = (x0 + ox, y0 + oy, x1 + ox, y1 + oy)
        cap_s = sh['face'].cap * sh['s']
        bottom = oy if sh['ln'].get('bottom') == 'baseline' else y1 + oy
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
        parts.append(e2)
    for sh in shaped:
        parts.append(dict(kind='line', sh=sh, transforms=[shift.transform(t) for t in sh['T']],
                          box=(sh['box'][0] + mx, sh['box'][1], sh['box'][2] + mx, sh['box'][3])))

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
            x0, y0, x1, y1 = p['box']
            body.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' % (fmt(x0), fmt(y0), fmt(x1 - x0), fmt(y1 - y0), fmt(p['rx']), ink))
        elif k == 'pip':
            fill = ink if dark or p['name'] in ('spade', 'club') else RED
            body.append('<path d="%s" transform="%s" fill="%s"/>' % (lay['pips'][p['name']]['d'], p['transform'], fill))
        else:
            sh = p['sh']
            ln = sh['ln']
            if ln.get('ribbon'):
                fill = INK if dark else PAPER
            elif ln.get('colour') and not dark:
                fill = ln['colour']
            else:
                fill = ink
            body.append('<path fill="%s" d="%s"/>' % (fill, sh['face'].path_t(sh['names'], p['transforms'])))
    view = 'viewBox="%s %s %s %s"' % tuple(fmt(x, 2) for x in vb)
    if mode == 'inline':
        return '<svg %s>%s</svg>' % (view, ''.join(body))
    needs_defs = any(p['kind'] == 'mark' and p['mark'] in ('fan', 'flat') for p in lay['parts'])
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


def V(num, name, vid, title, lead, small, gap=0.14, **kw):
    v = dict(id='%02d-%s' % (num, vid), num=num, name=name, title=title, lead=lead, lines=[small, BIG], gap=gap,
             mark='fan', markScale=100.0 / WORDS_AT, markGap=0.16, gapOf='mark')
    v.update(kw)
    return v


VARIATIONS = [
    V(1, 'Plain', 'plain', 'B1 as you picked it', 'GLCA Medium on both lines, the words at 85% of the fan, the small line at 56% of the big one.', L('World of', 'glca-500', 0.56)),
    V(2, 'Label', 'label', 'The small line at 40%', 'The board\u2019s first lesson: the small line as a label. Card Games grows to fill the same height.', L('World of', 'glca-500', 0.40), gap=0.18),
    V(3, 'Light', 'light', 'A lighter small line', 'World of in GLCA Regular over Card Games in Medium. The same face with less weight.', L('World of', 'glca-400', 0.56)),
    V(4, 'Red', 'red', 'The small line in the deck\u2019s red', 'World of takes the red of the hearts in the fan.', L('World of', 'glca-500', 0.56, colour=RED)),
    V(5, 'Quiet', 'quiet', 'The small line in the quiet ink', 'World of steps back a shade, as a by-line does on the site.', L('World of', 'glca-500', 0.56, colour=QUIET)),
    V(6, 'Capitals', 'capitals', 'Spaced capitals', 'WORLD OF in small spaced capitals, the Twinings and Whole Foods way.', L('World of', 'glca-500', 0.40, caps=True, tracking=0.14), gap=0.2),
    V(7, 'Spread', 'spread', 'Capitals spread to the width', 'WORLD OF spread across the full width of Card Games, so the two lines make one block.', L('World of', 'glca-500', 0.40, caps=True, tracking=0.06, justify=True), gap=0.2),
    V(8, 'Centred', 'centred', 'Centred', 'World of centred over Card Games instead of flush left.', L('World of', 'glca-500', 0.56, align='center')),
    V(9, 'Signature', 'signature', 'Flush right', 'World of ends where Card Games ends, like a signature.', L('World of', 'glca-500', 0.56, align='right')),
    V(10, 'Rules', 'rules', 'Between two rules', 'World of centred between two hairlines that run to the edges of Card Games.', L('World of', 'glca-500', 0.5, align='center', rules='plain'), gap=0.18),
    V(11, 'Suits', 'suits', 'Rules with a spade and a heart', 'The same hairlines, ending in a spade and a heart taken from the fan\u2019s cards.', L('World of', 'glca-500', 0.5, align='center', rules='pips'), gap=0.18),
    V(12, 'Arc', 'arc', 'On a gentle arc', 'World of set on a slight curve, like a label.', L('World of', 'glca-500', 0.52, align='center', arc=0.08), gap=0.16),
    V(13, 'Bow', 'bow', 'On a stronger arc', 'The same with more curve.', L('World of', 'glca-500', 0.52, align='center', arc=0.16), gap=0.16),
    V(14, 'Stamp', 'stamp', 'Tilted like a stamp', 'World of turned six degrees, rising to the right.', L('World of', 'glca-500', 0.56, rot=6), gap=0.18),
    V(15, 'Ribbon', 'ribbon', 'On a ribbon', 'World of in the paper colour on a small ribbon in the ink.', L('World of', 'glca-500', 0.46, ribbon=True), gap=0.22),
    V(16, 'Pacifico', 'pacifico', 'Pacifico over GLCA', 'The script you pointed at, over Card Games in GLCA. The f\u2019s tail reaches down toward the big line.', L('World of', 'pacifico-400', 0.5, bottom='baseline'), gap=0.34),
    V(17, 'Courgette', 'courgette', 'A calmer script over GLCA', 'Courgette, a rounder and quieter script, over Card Games in GLCA.', L('World of', 'courgette-400', 0.52, bottom='baseline'), gap=0.3),
    dict(id='18-middle', num=18, name='Middle', title='The fan in the middle, even words', layout='middle', mark='fan',
         lead='World of to the left of the fan and Card Games to its right, at one size, their capitals half the fan\u2019s height.',
         lines=[L('World of', 'glca-500', capsize(0.5)), L('Card Games', 'glca-500', capsize(0.5))]),
    dict(id='19-middle-small', num=19, name='Middle small', title='The fan in the middle, World of smaller', layout='middle', mark='fan',
         lead='The same, with World of at 70% of Card Games, both on one baseline.',
         lines=[L('World of', 'glca-500', capsize(0.35)), L('Card Games', 'glca-500', capsize(0.5))]),
    dict(id='20-middle-capitals', num=20, name='Middle capitals', title='The fan in the middle, spaced capitals', layout='middle', mark='fan',
         lead='WORLD OF and CARD GAMES in small spaced capitals either side of the fan.',
         lines=[L('World of', 'glca-500', capsize(0.4), caps=True, tracking=0.12), L('Card Games', 'glca-500', capsize(0.4), caps=True, tracking=0.12)]),
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
    return sh['face'].cap * sh['s'] * h / lay['vb'][3]


ROW = '''
<section class="ll-row" id="%(id)s">
  <div class="ll-row-name"><span class="ll-num">%(num)s</span><h2>%(name)s</h2><span class="ll-sub">%(title)s</span></div>
  <div class="ll-row-head">
    <div class="ll-draw">%(svg)s</div>
    <div class="ll-row-words"><p>%(lead)s</p><span>%(note)s</span></div>
  </div>
  <div class="ll-pair">
    <iframe class="ll-bar" data-v="%(vkey)s" src="logo-lab-bar.html?v=%(vkey)s" width="940" height="57" loading="lazy" scrolling="no" title="The bar at a desktop width"></iframe>
    <iframe class="ll-bar" data-v="%(vkey)s" src="logo-lab-bar.html?v=%(vkey)s" width="390" height="57" loading="lazy" scrolling="no" title="A phone"></iframe>
  </div>
</section>'''


def row(v, lay, svg):
    small, big = lay['shaped'][0], lay['shaped'][-1]
    if v.get('layout') == 'middle':
        note = ('On the bar: %s px wide (today 170), World of\u2019s capitals %s px tall, Card Games\u2019 %s px. On a phone: %s px wide. File: logo-lab-out/%s.svg'
                % (fmt(lay['ratio'] * 32, 0), fmt(cap_px(lay, small, 32), 0), fmt(cap_px(lay, big, 32), 0), fmt(lay['ratio'] * 24, 0), v['id']))
    else:
        note = ('On the bar: %s px wide (today 170), the big line\u2019s capitals %s px tall, the small line\u2019s %s px. On a phone: %s px wide. File: logo-lab-out/%s.svg'
                % (fmt(lay['ratio'] * 32, 0), fmt(cap_px(lay, big, 32), 0), fmt(cap_px(lay, small, 32), 0), fmt(lay['ratio'] * 24, 0), v['id']))
    return ROW % dict(id=v['id'], vkey=v['id'], num=str(v['num']), name=escape(v['name']), title=escape(v['title']), lead=escape(v['lead']), note=escape(note), svg=svg)


def today_row(text_group):
    """Row 0: the logo as the bar draws it now. The drawing is the source art; the bars draw the site's logo.png."""
    svg = ('<svg viewBox="0 190 5464 900"><use href="#mark-fan" transform="translate(-102,0)"/><g transform="translate(1246.9,288)">%s</g></svg>'
           % ''.join(ser(el) for el in text_group))
    return ROW % dict(id='00-today', vkey='today', num='0', name='Today', title='The logo as it is', svg=svg,
                      lead='The fan and World of Card Games on one line in Bariol Bold, as the bar draws it now.',
                      note='On the bar: 170 px wide, its capitals about 9 px tall. On a phone: 128 px wide. File: the site\u2019s static/images/logo.png')


def toc_html(variations):
    items = ['<a href="#00-today"><span class="ll-num">0</span>Today</a>']
    items += ['<a href="#%s"><span class="ll-num">%d</span>%s</a>' % (v['id'], v['num'], escape(v['name'])) for v in variations]
    return ''.join(items)


def page_html(rows, defs, marks, toc):
    return PAGE % dict(defs=hidden_defs(defs, {'fan': marks['fan']}), rows=''.join(rows), toc=toc, css=CSS, js=JS)


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
    if '--measure' in sys.argv or not MARKS_JSON.exists():
        boxes = measure_marks(defs, marks)
        print('measured:', {k: (round(b['w']), round(b['h'])) for k, b in boxes.items()})
    else:
        boxes = json.loads(MARKS_JSON.read_text())

    OUT.mkdir(exist_ok=True)
    for old in OUT.glob('*.svg'):
        old.unlink()
    (OUT / 'mark-fan.svg').write_text(mark_file('fan', marks, boxes, defs))
    # the bar page's images, copied from the site so the page works online where the static symlink does not exist
    STATIC.mkdir(exist_ok=True)
    for src, name in BAR_IMAGES:
        (STATIC / name).write_bytes((WOCG / 'static' / src).read_bytes())

    rows = []
    check_rows = []
    for v in VARIATIONS:
        lay = layout_middle(v, boxes, pips) if v.get('layout') == 'middle' else layout(v, boxes, pips)
        (OUT / ('%s.svg' % v['id'])).write_text(render(lay, 'file', defs, marks))
        (OUT / ('%s-white.svg' % v['id'])).write_text(render(lay, 'file', defs, marks, ink=WHITE))
        rows.append(row(v, lay, render(lay, 'inline')))
        for p in lay['parts']:
            if p['kind'] != 'line':
                continue
            sh = p['sh']
            ln = sh['ln']
            if ln.get('arc') or ln.get('rot'):
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
        print('%-12s %3s px on the bar, big capitals %2s px, small %s px'
              % (v['id'], fmt(lay['ratio'] * 32, 0), fmt(cap_px(lay, lay['shaped'][-1], 32), 0), fmt(cap_px(lay, lay['shaped'][0], 32), 0)))

    rows.insert(0, today_row(text_group))
    (ROOT / 'logo-lab.html').write_text(page_html(rows, defs, marks, toc_html(VARIATIONS)))
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
      var want = 'logo-lab-bar.html?v=' + (today ? 'today' : f.getAttribute('data-v')) + (tall ? '&h=40' : '');
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
  <h1>The logo: B1, the small line</h1>
  <p>Holger, 25 Sep: GLCA Medium stays. Can World of talk to Card Games in a more interesting, cohesive way, without a second face? Seventeen answers, all B1 with the words at 85%% of the fan, after the logo as it is today, and then three with the fan in the middle of the words. Every row has a number and a name to refer to it by (say &ldquo;4 Red&rdquo; or &ldquo;12 Arc&rdquo;). Each row: the logo at 64px, then the site&rsquo;s bar at a desktop width with the logo 32px tall, and a phone with it 24px tall.</p>
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
