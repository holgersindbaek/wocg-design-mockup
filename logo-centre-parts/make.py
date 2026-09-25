#!/usr/bin/env python3
"""The centred-mark lab.

Holger, 25 Sep 2026: "Could you also try to create a bunch of versions where we have the icon centred, so we
have World of on one side and Card Games on the other? Maybe also create some new concepts for icons? Maybe a
globe or something? Make it in a new lab."

This writes ../logo-centre.html: ten marks (the fan as it is and nine new ideas drawn flat in the ink and the
deck's red, most of them around a globe), each on its own at the favicon sizes and on a felt plate, and each in
the centred lockup, World of | mark | Card Games, in three word styles, in the site's menubar at a desktop width
and at a phone's. Every lockup is a font-free SVG in ../logo-centre-out/. The type engine, the fan, the bar page
and the pixel measure of the marks come from logo-lab-parts/make.py.

    python3 logo-centre-parts/make.py             build (measures the marks first if marks.json is missing)
    python3 logo-centre-parts/make.py --measure   measure the marks again, then build
"""
import copy
import json
import math
import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'logo-lab-parts'))
import make as lab  # noqa: E402

from fontTools.misc.transform import Transform  # noqa: E402

OUT = ROOT / 'logo-centre-out'
MARKS_JSON = HERE / 'marks.json'
INK, RED, PAPER, WHITE = lab.INK, lab.RED, lab.PAPER, lab.WHITE
FELT = '#327333'
q, fmt, ser = lab.q, lab.fmt, lab.ser


# ---------------------------------------------------------------------------------------------------------------
# the marks: nine new ideas in a 200-unit box, drawn with the strokes the icons use (12 units is 1.9px at 32px)
# ---------------------------------------------------------------------------------------------------------------

def el(tag, **attrs):
    return ET.Element(q(tag), {k.replace('_', '-'): str(v) for k, v in attrs.items()})


def sub(parent, tag, **attrs):
    return ET.SubElement(parent, q(tag), {k.replace('_', '-'): str(v) for k, v in attrs.items()})


def group(mid, **attrs):
    return el('g', id=mid, **attrs)


def meridians(g, cx, cy, r, stroke, width, rx_share=0.46, parallels=(0.55,), clip=None):
    """A vertical meridian, the equator and a parallel above and below, inside a circle of radius r."""
    extra = {'clip-path': 'url(#%s)' % clip} if clip else {}
    common = dict(fill='none', stroke=stroke, stroke_width=width, stroke_linecap='round')
    e = sub(g, 'ellipse', cx=cx, cy=cy, rx=fmt(r * rx_share), ry=r, **common)
    line = sub(g, 'line', x1=fmt(cx - r), y1=cy, x2=fmt(cx + r), y2=cy, **common)
    for k, v in extra.items():
        e.set(k, v)
        line.set(k, v)
    for share in parallels:
        dy = r * share
        half = math.sqrt(max(0.0, r * r - dy * dy))
        for sign in (-1, 1):
            p = sub(g, 'line', x1=fmt(cx - half), y1=fmt(cy + sign * dy), x2=fmt(cx + half), y2=fmt(cy + sign * dy), **common)
            for k, v in extra.items():
                p.set(k, v)


def pip(g, pips, name, cx, cy, height, fill):
    x0, y0, x1, y1 = pips[name]['box']
    f = height / (y1 - y0)
    w = (x1 - x0) * f
    sub(g, 'path', d=pips[name]['d'], fill=fill,
        transform='translate(%s,%s) scale(%s)' % (fmt(cx - (x0 + (x1 - x0) / 2) * f, 3), fmt(cy - (y0 + (y1 - y0) / 2) * f, 3), fmt(f, 5)))


def card(g, cx, cy, w, h, rot=0, stroke=12, r=16):
    return sub(g, 'rect', x=fmt(cx - w / 2), y=fmt(cy - h / 2), width=w, height=h, rx=r, fill=WHITE, stroke=INK, stroke_width=stroke,
               transform='rotate(%s %s %s)' % (rot, cx, cy) if rot else '')


def new_marks(pips, lab_marks):
    m = {}
    # 1 globe: a white disc with the lines of a globe
    g = group('mark-globe')
    sub(g, 'circle', cx=100, cy=100, r=88, fill=WHITE, stroke=INK, stroke_width=12)
    meridians(g, 100, 100, 88, INK, 10)
    m['globe'] = g

    # 2 globe heart: the globe with a heart where a continent would be
    g = group('mark-globeheart')
    sub(g, 'circle', cx=100, cy=100, r=88, fill=WHITE, stroke=INK, stroke_width=12)
    meridians(g, 100, 100, 88, INK, 9, parallels=())
    pip(g, pips, 'heart', 118, 92, 70, RED)
    m['globeheart'] = g

    # 3 suit compass: a ring with the four suits at the points of the compass
    g = group('mark-compass')
    sub(g, 'circle', cx=100, cy=100, r=90, fill=WHITE, stroke=INK, stroke_width=11)
    for name, (cx, cy), fill in (('spade', (100, 52), INK), ('heart', (148, 100), RED), ('club', (100, 148), INK), ('diamond', (52, 100), RED)):
        pip(g, pips, name, cx, cy, 46, fill)
    m['compass'] = g

    # 4 world card: one card whose suit is the world
    g = group('mark-worldcard')
    inner = sub(g, 'g', transform='rotate(-8 100 100)')
    card(inner, 100, 100, 128, 176, stroke=12, r=18)
    sub(inner, 'circle', cx=100, cy=100, r=40, fill=WHITE, stroke=INK, stroke_width=9)
    meridians(inner, 100, 100, 40, INK, 7, parallels=())
    m['worldcard'] = g

    # 5 spade globe and 6 heart globe: a pip with the globe's lines cut into it
    for key, name, fill in (('spadeglobe', 'spade', INK), ('heartglobe', 'heart', RED)):
        g = group('mark-' + key)
        x0, y0, x1, y1 = pips[name]['box']
        f = 176 / (y1 - y0)
        tf = 'translate(%s,%s) scale(%s)' % (fmt(100 - (x0 + (x1 - x0) / 2) * f, 3), fmt(100 - (y0 + (y1 - y0) / 2) * f, 3), fmt(f, 5))
        cp = sub(g, 'clipPath', id='clip-' + key)
        sub(cp, 'path', d=pips[name]['d'], transform=tf)
        sub(g, 'path', d=pips[name]['d'], transform=tf, fill=fill)
        meridians(g, 100, 104 if name == 'spade' else 96, 88, PAPER, 9, rx_share=0.42, parallels=(0.5,), clip='clip-' + key)
        m[key] = g

    # 7 table: the world as a round felt table with a card at every seat
    g = group('mark-table')
    sub(g, 'circle', cx=100, cy=100, r=88, fill=FELT, stroke=INK, stroke_width=11)
    for ang in (0, 90, 180, 270):
        rad = math.radians(ang)
        cx, cy = 100 + 50 * math.sin(rad), 100 - 50 * math.cos(rad)
        card(g, cx, cy, 34, 48, rot=ang, stroke=8, r=7)
    m['table'] = g

    # 8 pinwheel: four cards turning about one point
    g = group('mark-pinwheel')
    for i, ang in enumerate((0, 90, 180, 270)):
        rad = math.radians(ang)
        cx, cy = 100 + 42 * math.sin(rad), 100 - 42 * math.cos(rad)
        card(g, cx, cy, 52, 74, rot=ang + 18, stroke=10, r=9)
    m['pinwheel'] = g

    # 9 two cards: the fan cut to its front two, flat (from the first round)
    m['two'] = copy.deepcopy(lab_marks['two'])
    m['fan'] = copy.deepcopy(lab_marks['fan'])
    return m


MARKS = [
    # key, number, name, one line
    ('fan', 0, 'Fan', 'The mark as it is, in the middle.'),
    ('globe', 1, 'Globe', 'A white disc with the lines of a globe. The world, drawn as simply as it can be.'),
    ('globeheart', 2, 'Globe heart', 'The globe with a red heart where a continent would be.'),
    ('compass', 3, 'Suit compass', 'A ring with the four suits at the points of the compass.'),
    ('worldcard', 4, 'World card', 'One card whose suit is the world.'),
    ('spadeglobe', 5, 'Spade globe', 'The spade with the globe’s lines cut into it.'),
    ('heartglobe', 6, 'Heart globe', 'The heart with the globe’s lines cut into it.'),
    ('table', 7, 'Table', 'The world as a round felt table with a card at every seat.'),
    ('pinwheel', 8, 'Pinwheel', 'Four cards turning about one point.'),
    ('two', 9, 'Two cards', 'The fan cut to its front two cards, flat, from the first round.'),
]

# the word styles: the mark is 100 units tall; the words are set by their capital height as a share of it
STYLES = [
    ('a', 'A', 'Even', 'World of and Card Games at the same size, their capitals half the mark’s height.',
     dict(left=dict(cap=0.5), right=dict(cap=0.5))),
    ('b', 'B', 'Small World of', 'World of at 70% of Card Games, both on one baseline.',
     dict(left=dict(cap=0.35), right=dict(cap=0.5))),
    ('c', 'C', 'Capitals', 'WORLD OF and CARD GAMES in small spaced capitals.',
     dict(left=dict(cap=0.4, caps=True, tracking=0.12), right=dict(cap=0.4, caps=True, tracking=0.12))),
]


# ---------------------------------------------------------------------------------------------------------------
# the centred lockup
# ---------------------------------------------------------------------------------------------------------------

MH = 100.0  # the mark's height in the design space


def word(text, spec):
    f = lab.face('glca-500')
    size = spec['cap'] * MH / (f.cap / f.upm) / lab.S  # the font size, as a share of lab.S, that gives this cap height
    return lab.shape_line(lab.L(text, 'glca-500', size, caps=spec.get('caps', False), tracking=spec.get('tracking', 0.0)))


def layout_centre(kind, style, boxes, pips):
    left, right = word('World of', style['left']), word('Card Games', style['right'])
    b = boxes[kind]
    f = MH / b['h']
    mw = b['w'] * f
    cap_r = right['face'].cap * right['s']
    baseline = MH / 2 + cap_r / 2
    gap = 0.38 * cap_r
    parts = []
    x = 0.0
    for sh in (left,):
        x0, y0, x1, y1 = sh['ink']
        ox, oy = x - x0, baseline
        T = [Transform().translate(ox, oy).transform(t) for t in sh['t0']]
        parts.append(dict(kind='line', sh=sh, transforms=T, box=(x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
        x = x1 + ox + gap
    parts.append(dict(kind='mark', mark=kind, transform='translate(%s,%s) scale(%s)' % (fmt(x - b['x'] * f, 3), fmt(-b['y'] * f, 3), fmt(f, 5)),
                      box=(x, 0, x + mw, MH)))
    x += mw + gap
    x0, y0, x1, y1 = right['ink']
    ox, oy = x - x0, baseline
    T = [Transform().translate(ox, oy).transform(t) for t in right['t0']]
    parts.append(dict(kind='line', sh=right, transforms=T, box=(x0 + ox, y0 + oy, x1 + ox, y1 + oy)))
    xs0 = min(p['box'][0] for p in parts)
    ys0 = min(p['box'][1] for p in parts)
    xs1 = max(p['box'][2] for p in parts)
    ys1 = max(p['box'][3] for p in parts)
    m = 0.03 * (ys1 - ys0)
    vb = (xs0 - m, ys0 - m, (xs1 - xs0) + 2 * m, (ys1 - ys0) + 2 * m)
    return dict(parts=parts, vb=vb, shaped=[left, right], ratio=vb[2] / vb[3], pips=pips, cap_r=cap_r)


def whiten(svg, kind):
    """The version for dark grounds. White-bodied marks keep their ink outlines, as the fan does on the felt; only
    the spade globe, a solid ink shape, turns white with its cut lines going to the ink."""
    if kind == 'spadeglobe':
        return svg.replace(INK, WHITE).replace(PAPER, INK)
    return svg


# ---------------------------------------------------------------------------------------------------------------
# the page
# ---------------------------------------------------------------------------------------------------------------

def icon_card(key, num, name, lead):
    sizes = ''.join('<span class="lc-fav"><img src="logo-centre-out/mark-%s.svg" width="%d" height="%d" alt=""><small>%d</small></span>' % (key, s, s, s) for s in (16, 24, 32, 48))
    return '''
<section class="lc-icon" id="icon-%(key)s">
  <div class="ll-row-name"><span class="ll-num">%(num)d</span><h2>%(name)s</h2></div>
  <p class="lc-lead">%(lead)s</p>
  <div class="lc-icon-row">
    <span class="lc-big"><img src="logo-centre-out/mark-%(key)s.svg" alt=""></span>
    <span class="lc-sizes">%(sizes)s</span>
    <span class="lc-plate lc-plate-felt"><img src="logo-centre-out/mark-%(key)s-white.svg" alt=""></span>
    <span class="lc-plate lc-plate-ink"><img src="logo-centre-out/mark-%(key)s-white.svg" alt=""></span>
  </div>
</section>''' % dict(key=key, num=num, name=escape(name), lead=escape(lead), sizes=sizes)


def lockup_row(key, num, name, draws, notes):
    return '''
<section class="ll-row" id="%(key)s">
  <div class="ll-row-name"><span class="ll-num">%(num)d</span><h2>%(name)s</h2><span class="ll-sub lc-note">%(notes)s</span></div>
  <div class="ll-row-head">%(draws)s</div>
  <div class="ll-pair">
    <iframe class="ll-bar" data-mark="%(key)s" width="940" height="57" loading="lazy" scrolling="no" title="The bar at a desktop width"></iframe>
    <iframe class="ll-bar" data-mark="%(key)s" width="390" height="57" loading="lazy" scrolling="no" title="A phone"></iframe>
  </div>
</section>''' % dict(key=key, num=num, name=escape(name), draws=draws, notes=notes)


def main():
    root, defs, logo, text_group = lab.load_source()
    lab_marks = lab.build_marks(logo)
    pips = lab.pip_paths(logo)
    marks = new_marks(pips, lab_marks)
    lab.MARKS_JSON = MARKS_JSON
    if '--measure' in sys.argv or not MARKS_JSON.exists():
        boxes = lab.measure_marks(defs, marks)
        print('measured:', {k: (round(b['w']), round(b['h'])) for k, b in boxes.items()})
    else:
        boxes = json.loads(MARKS_JSON.read_text())

    OUT.mkdir(exist_ok=True)
    for old in OUT.glob('*.svg'):
        old.unlink()
    icons, rows = [], []
    for key, num, name, lead in MARKS:
        svg = lab.mark_file(key, marks, boxes, defs)
        (OUT / ('mark-%s.svg' % key)).write_text(svg)
        (OUT / ('mark-%s-white.svg' % key)).write_text(whiten(svg, key))
        icons.append(icon_card(key, num, name, lead))
        draws, notes = [], []
        for skey, sletter, sname, slead, spec in STYLES:
            lay = layout_centre(key, spec, boxes, pips)
            vid = '%s-%s' % (key, skey)
            svg = lab.render(lay, 'file', defs, marks)
            (OUT / (vid + '.svg')).write_text(svg)
            (OUT / (vid + '-white.svg')).write_text(whiten(lab.render(lay, 'file', defs, marks, ink=WHITE), key))
            draws.append('<div class="ll-draw lc-draw" data-style="%s">%s</div>' % (skey, lab.render(lay, 'inline')))
            notes.append('%s: %s px on the bar, %s on a phone' % (sletter, fmt(lay['ratio'] * 32, 0), fmt(lay['ratio'] * 24, 0)))
            print('%-14s %s  %3s px on the bar' % (key, sletter, fmt(lay['ratio'] * 32, 0)))
        rows.append(lockup_row(key, num, name, ''.join(draws), escape(' · '.join(notes))))

    styles = ''.join('<button type="button" data-style="%s"><span class="ll-num">%s</span>%s</button>' % (skey, sletter, escape(sname)) for skey, sletter, sname, _, _ in STYLES)
    style_leads = ''.join('<p class="lc-style-lead" data-style="%s"><b>%s %s.</b> %s</p>' % (skey, sletter, escape(sname), escape(slead)) for skey, sletter, sname, slead, _ in STYLES)
    toc = ''.join('<a href="#%s"><span class="ll-num">%d</span>%s</a>' % (key, num, escape(name)) for key, num, name, _ in MARKS)
    page = PAGE % dict(defs=lab.hidden_defs(defs, marks), css=lab.CSS + CSS, js=JS, icons=''.join(icons), rows=''.join(rows), styles=styles, style_leads=style_leads, toc=toc)
    (ROOT / 'logo-centre.html').write_text(page)
    (ROOT / 'logo-centre-bar.html').write_text(lab.BAR.replace("'logo-lab-out/'", "'logo-centre-out/'").replace('Generated by logo-lab-parts/make.py', 'Generated by logo-centre-parts/make.py'))
    print('wrote logo-centre.html (%d KB), logo-centre-bar.html, %d files in logo-centre-out/' % ((ROOT / 'logo-centre.html').stat().st_size // 1024, len(list(OUT.glob('*.svg')))))


CSS = r'''
  .lc-icons { display: grid; grid-template-columns: repeat(auto-fill, minmax(560px, 1fr)); gap: 12px; margin: 0 0 12px; }
  .lc-icon { background: #fff; border-radius: 14px; corner-shape: squircle; box-shadow: inset 0 0 0 1px var(--ll-line); padding: 14px 16px 12px; }
  .lc-icon .ll-row-name { margin-bottom: 4px; }
  .lc-icon .ll-row-name h2 { font-size: 22px; line-height: 28px; }
  .lc-lead { margin: 0 0 10px; font-size: 14px; line-height: 20px; color: var(--ll-label); }
  .lc-icon-row { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
  .lc-big { display: inline-flex; align-items: center; justify-content: center; width: 120px; height: 120px; }
  .lc-big img { width: 112px; height: 112px; display: block; }
  .lc-sizes { display: inline-flex; align-items: flex-end; gap: 14px; }
  .lc-fav { display: inline-flex; flex-direction: column; align-items: center; gap: 4px; }
  .lc-fav img { display: block; }
  .lc-fav small { font-size: 11px; line-height: 14px; color: var(--ll-quiet); }
  .lc-plate { display: inline-flex; align-items: center; justify-content: center; width: 72px; height: 72px; border-radius: 17px; corner-shape: squircle; }
  .lc-plate img { width: 52px; height: 52px; display: block; }
  .lc-plate-felt { background: #327333 url("static/pieces/wallpaper/fabrics/green-felt.jpg") 0 0 / 100px 100px repeat; }
  .lc-plate-ink { background: var(--ll-ink); }
  .lc-styles { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 4px 0 6px; }
  .lc-styles button { display: inline-flex; align-items: center; gap: 8px; border: 0; border-radius: 16px; padding: 3px 12px 3px 3px; cursor: pointer; font: 700 14px/24px "BuloRounded", Verdana, sans-serif; background: #fff; color: var(--ll-ink); box-shadow: inset 0 0 0 1px var(--ll-line); }
  .lc-styles button.on { background: var(--ll-ink); color: #fff; box-shadow: none; }
  .lc-styles button.on .ll-num { background: #fff; color: var(--ll-ink); }
  .lc-styles .ll-num { min-width: 24px; height: 22px; font-size: 12px; line-height: 22px; padding: 0 7px; border-radius: 11px; }
  .lc-style-lead { margin: 0 0 14px; font-size: 14px; line-height: 20px; color: var(--ll-label); max-width: 900px; display: none; }
  .lc-draw { display: none; }
  body.lc-a .lc-draw[data-style=a], body.lc-b .lc-draw[data-style=b], body.lc-c .lc-draw[data-style=c] { display: flex; }
  body.lc-a .lc-style-lead[data-style=a], body.lc-b .lc-style-lead[data-style=b], body.lc-c .lc-style-lead[data-style=c] { display: block; }
  .ll-row-head { margin-bottom: 10px; }
  .ll-row-name { flex-wrap: wrap; }
  .ll-row-name h2 { white-space: nowrap; }
  .lc-note { flex: 1 1 360px; padding-top: 0; }
  .ll-page h2.lc-h { font: 500 26px/32px "GLCA", Georgia, serif; margin: 34px 0 6px; }
'''

JS = r'''
(function () {
  var pick = (new URLSearchParams(location.search).get('style') || 'a').toLowerCase();
  var style = ['a', 'b', 'c'].indexOf(pick) >= 0 ? pick : 'a', today = false, tall = false, zoom = false;
  var bToday = document.getElementById('llToday'), bTall = document.getElementById('llTall'), bZoom = document.getElementById('llZoom');
  var styleButtons = document.querySelectorAll('.lc-styles button');
  function paint() {
    document.body.className = 'lc-' + style + (zoom ? ' ll-zoom' : '');
    styleButtons.forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-style') === style); });
    bToday.textContent = today ? 'Showing today’s logo in the bars' : 'Show today’s logo in the bars';
    bToday.classList.toggle('on', today);
    bTall.textContent = tall ? 'Logo 40px tall in the bars' : 'Logo 32px tall in the bars';
    bTall.classList.toggle('on', tall);
    bZoom.textContent = zoom ? 'Bars at 2x' : 'Bars at 1x';
    bZoom.classList.toggle('on', zoom);
    document.querySelectorAll('iframe.ll-bar').forEach(function (f) {
      var want = 'logo-centre-bar.html?v=' + (today ? 'today' : f.getAttribute('data-mark') + '-' + style) + (tall ? '&h=40' : '');
      if (f.getAttribute('src') !== want) f.setAttribute('src', want);
    });
  }
  styleButtons.forEach(function (b) { b.addEventListener('click', function () { style = b.getAttribute('data-style'); paint(); }); });
  bToday.addEventListener('click', function () { today = !today; paint(); });
  bTall.addEventListener('click', function () { tall = !tall; paint(); });
  bZoom.addEventListener('click', function () { zoom = !zoom; paint(); });
  paint();
})();
'''

PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<!-- Generated by logo-centre-parts/make.py. Edit make.py, then run it. -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The logo: the mark in the middle &middot; lab</title>
<link rel="stylesheet" href="guide-fonts.css">
<style>
%(css)s
</style>
</head>
<body class="lc-a">
%(defs)s
<header class="ll-head">
  <h1>The logo: the mark in the middle</h1>
  <p>Holger, 25 Sep: try the icon centred, World of on one side and Card Games on the other, and try new ideas for the icon, a globe or something. Ten marks: the fan as it is and nine new ones. First each mark on its own, at the favicon sizes and on the felt and the ink. Then each in the centred lockup, in the site&rsquo;s bar at a desktop width (32px tall) and on a phone (24px), in three word styles you switch between. Refer to a version by mark and style, say &ldquo;5 Spade globe, B&rdquo;; a link can open on a style with <code>?style=b</code>.</p>
  <div class="ll-switches"><button id="llToday" type="button"></button><button id="llTall" type="button"></button><button id="llZoom" type="button"></button></div>
</header>
<main class="ll-page">
  <nav class="ll-toc">%(toc)s</nav>
  <h2 class="lc-h">The marks</h2>
  <div class="lc-icons">%(icons)s</div>
  <h2 class="lc-h">In the middle of the words</h2>
  <div class="lc-styles"><span style="font-size:14px;color:#4e4d4c;margin-right:4px">Word style:</span>%(styles)s</div>
  %(style_leads)s
%(rows)s
  <p class="ll-files">Every version is a file: <code>logo-centre-out/globe-a.svg</code> is 1 Globe in style A, <code>spadeglobe-c.svg</code> is 5 Spade globe in style C, each with a <code>-white</code> copy for dark grounds; <code>mark-globe.svg</code> is the mark alone. The type is outlined, so they need no font. The marks are drawn flat in the ink and the deck&rsquo;s red, the way the redesign&rsquo;s icons are.</p>
</main>
<script>
%(js)s
</script>
</body>
</html>
'''

if __name__ == '__main__':
    main()
