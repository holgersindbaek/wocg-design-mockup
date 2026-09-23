# python3 icon-lab-parts/compose-inline.py
#
# Writes the lab's code-drawn icons as plain SVG files with every colour written on the art,
# so the lab can recolour them. Paths are lifted from inline-source/, the site's own markup as the
# 23 Sep 2026 sweep extracted it (sweep/usage-inline.json says where each one lives). Colours are
# the ones the site's CSS paints. inline/experiencedBadge.svg is not made here: it is the
# WoCG-2.1.sketch vector with the shipped PNG's lime put back.
import re, os
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inline-source') + '/'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inline') + '/'
IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'images') + '/'
def inner(name):
    s = open(SRC + name).read()
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    s = re.sub(r'<style>.*?</style>', '', s, flags=re.S)
    m = re.search(r'<svg[^>]*>(.*)</svg>', s, flags=re.S)
    return m.group(1).strip()
def paths(name):
    return re.findall(r'\sd=["\']([^"\']+)["\']', open(SRC + name).read())
def svg(w, h, vb, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{vb}">{body}</svg>\n'
def btn(size, fill, ring, rx=6):
    # a square button with its 1px inset ring (box-shadow inset 0 0 0 1px), as the friends panel draws it
    return f'<rect x="0" y="0" width="{size}" height="{size}" rx="{rx}" fill="{fill}"/><rect x=".5" y=".5" width="{size-1}" height="{size-1}" rx="{rx-.5}" fill="none" stroke="{ring}"/>'
def put(name, text):
    open(OUT + name, 'w').write(text)
files = []
def w(name, text): put(name, text); files.append(name)

# the close cross of every dialog: a 4.4 black 30% under-stroke and a 2.2 white stroke
d = 'M3 3l10 10M13 3L3 13'
w('closeCross.svg', svg(20, 20, '0 0 16 16', f'<path d="{d}" stroke="#000000" stroke-opacity=".30" stroke-width="4.4" stroke-linecap="round" fill="none"/><path d="{d}" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" fill="none"/>'))

# the round i after a settings row title on a phone: the disc, its ring, the i
i_body = inner('rowInfoI.svg')
def info(disc, ring, ink):
    body = re.sub(r"fill='#[0-9a-fA-F]+'", f"fill='{ink}'", i_body)
    return svg(16, 16, '0 0 60 60', f'<circle cx="30" cy="30" r="28.125" fill="{disc}" stroke="{ring}" stroke-width="3.75"/>{body}')
w('infoI.svg', info('#F4EEE5', '#D2CFCA', '#4E4D4C'))
w('infoI--hover.svg', info('#D2CFCA', '#D2CFCA', '#4E4D4C'))
w('infoI--open.svg', info('#5E574B', '#484136', '#FFFFFF'))

# the pick mark on a picked tile in Settings > Design: a green squircle disc, a 1px dark line, the outlined tick
tick = 'M4.5 12.5l5 5 10-11'
def tickp(under, top, sc=1, off=0):
    t = f' transform="translate({off} {off}) scale({sc})"' if sc != 1 else ''
    return f'<g{t}><path d="{tick}" fill="none" stroke="{under}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="{tick}" fill="none" stroke="{top}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/></g>'
w('pickMark.svg', svg(20, 20, '0 0 24 24', f'<rect x=".6" y=".6" width="22.8" height="22.8" rx="8" fill="#43A038" stroke="#000000" stroke-opacity=".64" stroke-width="1.2"/>' + tickp('#347D2C', '#FFFFFF', .82, 2.16)))

# the seat-count checkbox in the table options dialog
w('seatCheck.svg', svg(24, 24, '0 0 24 24', btn(24, '#43A038', '#347D2C') + tickp('#347D2C', '#FFFFFF', 20/24, 2)))
w('seatCheck--off.svg', svg(24, 24, '0 0 24 24', btn(24, '#F9F6F2', '#D2CFCA')))

# the chevron at the end of a settings row that opens something
w('rowChevron.svg', svg(8, 12, '0 0 8 12', '<path d="M1.5 1l5 5-5 5" fill="none" stroke="#4E4D4C" stroke-width="1.8"/>'))

# the rating star: one path, painted by CSS
star = paths('star.svg')[0]
def starsvg(fill, stroke):
    return svg(32, 32, '0 0 32 32', f'<path d="{star}" fill="{fill}" stroke="{stroke}" fill-rule="evenodd" transform="matrix(-1 0 0 1 32 0)"/>')
w('ratingStar.svg', starsvg('#F5B81E', '#EF7F27'))
w('ratingStar--empty.svg', starsvg('#D2CFCA', '#9B9997'))
w('ratingStarGameOver.svg', starsvg('#FCC419', '#DD7200'))
w('ratingStarGameOver--empty.svg', starsvg('#CED4DA', '#868E96'))

# the canasta badge under a complete meld: a small pill with the star in place of the count
def canasta(bg, ink):
    return svg(26, 18, '0 0 26 18', f'<rect x="0" y="0" width="26" height="18" rx="5" fill="{bg}"/><rect x=".5" y=".5" width="25" height="17" rx="4.5" fill="none" stroke="#000000" stroke-opacity=".16"/>'
               f'<g transform="translate(5 1) scale(.5)"><path d="{star}" fill="{ink}" fill-rule="evenodd" transform="matrix(-1 0 0 1 32 0)"/></g>')
w('canastaStar.svg', canasta('#C0EB75', '#4F800B'))
w('canastaStar--mixed.svg', canasta('#FFE066', '#C96800'))

# the turn timer by a seated player: the yellow disc, its 4px ring, the draining arc, the seconds, the felt line
def timer(disc, ring, arc, ink, left=.65):
    off = 226.195 * (1 - left)
    return svg(34, 34, '0 0 85 85', f'<circle cx="42.5" cy="42.5" r="41.25" fill="#393939"/><circle cx="42.5" cy="42.5" r="40" fill="{disc}"/>'
               f'<circle cx="42.5" cy="42.5" r="35" fill="none" stroke="{ring}" stroke-width="10"/>'
               f'<circle cx="42.5" cy="42.5" r="36" fill="none" stroke="{arc}" stroke-width="8" stroke-dasharray="226.195" stroke-dashoffset="{off:.2f}" transform="rotate(-90 42.5 42.5)"/>'
               f'<text x="42.5" y="55" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="34" fill="{ink}">12</text>')
w('turnTimer.svg', timer('#FFE066', '#F4BD45', '#C96800', '#C96800'))
w('turnTimer--red.svg', timer('#FFA8A8', '#F67A7A', '#C92A2A', '#C92A2A', .2).replace('>12<', '>3<'))

# the clock on a table tile: before the deal, in play, and the full disc
for nm, src in [('tableClock--open.svg', 'tableClockRing--open.svg'), ('tableClock.svg', 'tableClockRing.svg'), ('tableClock--full.svg', 'tableClockRing--full.svg')]:
    body = inner(src).replace('"#fff"', '"#FFFFFF"')
    w(nm, svg(10, 10, '0 0 16 16', body))

# the marks in a table tile's corner
for nm, src in [('markRanked.svg', 'markRankedCrown.svg'), ('markPrivate.svg', 'markPrivateLock.svg'), ('markLimited.svg', 'markLimitedPerson.svg'), ('markHouseRule.svg', 'markHouseRule.svg')]:
    body = inner(src).replace('"#fff"', '"#FFFFFF"').replace("'#fff'", "'#FFFFFF'")
    w(nm, svg(18, 18, '0 0 18 18', body))
for nm, src, s in [('hostPlus.svg', 'hostPlus.svg', 11), ('inviteEnvelope.svg', 'inviteEnvelope.svg', 12)]:
    raw = open(SRC + src).read()
    vb = re.search(r'viewBox="([^"]+)"', raw).group(1)
    body = inner(src).replace('"#fff"', '"#FFFFFF"').replace('currentColor', '#FFFFFF')
    w(nm, svg(s, s, vb, body))

# the friends panel's buttons, each drawn with its button
def glyph(src, colour):
    raw = open(SRC + src).read()
    vb = re.search(r'viewBox="([^"]+)"', raw).group(1)
    body = inner(src)
    body = re.sub(r'fill="(?!none)[^"]*"', f'fill="{colour}"', body)
    body = body.replace('currentColor', colour)
    return vb, body
def withBtn(src, size, gsize, fill, ring, colour, rx=6):
    vb, body = glyph(src, colour)
    vbw = float(vb.split()[2]); sc = gsize / vbw; off = (size - gsize) / 2
    return svg(size, size, f'0 0 {size} {size}', btn(size, fill, ring, rx) + f'<g fill="{colour}" transform="translate({off} {off}) scale({sc})">{body}</g>')
w('friendsSearch.svg', withBtn('friendsSearchMagnifier.svg', 24, 24, '#DEE2E6', '#ADB5BD', '#868E96'))
w('friendsSearch--hover.svg', withBtn('friendsSearchMagnifier.svg', 24, 24, '#DEE2E6', '#ADB5BD', '#495057'))
w('friendsSearchClose.svg', withBtn('friendsSearchCloseCross.svg', 24, 24, '#DEE2E6', '#ADB5BD', '#868E96'))
w('friendsSearchClose--hover.svg', withBtn('friendsSearchCloseCross.svg', 24, 24, '#DEE2E6', '#ADB5BD', '#495057'))
w('send.svg', withBtn('sendArrow.svg', 32, 24, '#A5D8FF', '#63B4F2', '#1971C2'))
w('send--hover.svg', withBtn('sendArrow.svg', 32, 24, '#A5D8FF', '#63B4F2', '#1665AD'))
w('send--off.svg', withBtn('sendArrow.svg', 32, 24, '#DEE2E6', '#ADB5BD', '#868E96'))
w('invite.svg', withBtn('inviteAddPerson.svg', 24, 24, '#A5D8FF', '#63B4F2', '#1971C2'))
w('invite--hover.svg', withBtn('inviteAddPerson.svg', 24, 24, '#A5D8FF', '#63B4F2', '#1665AD'))
w('invite--sent.svg', withBtn('inviteSentCheck.svg', 24, 24, '#E9ECEF', '#ADB5BD', '#868E96'))
w('message.svg', withBtn('friendMessageBubble.svg', 24, 24, '#A9E34B', '#66A80F', '#5C940D'))
w('message--hover.svg', withBtn('friendMessageBubble.svg', 24, 24, '#A9E34B', '#66A80F', '#4F800B'))
m = open(OUT + 'message.svg').read()
badge = ('<g transform="translate(-6 -6)"><rect x="0" y="0" width="13" height="13" rx="6.5" fill="#F03E3E"/><rect x=".5" y=".5" width="12" height="12" rx="6" fill="none" stroke="#C92A2A"/>'
         '<text x="6.5" y="10" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-weight="bold" font-size="9" fill="#FFFFFF">2</text></g>')
w('message--unread.svg', m.replace('viewBox="0 0 24 24"', 'viewBox="-7 -7 31 31"').replace('width="24" height="24"', 'width="31" height="31"', 1).replace('</svg>', badge + '</svg>'))

# masks: the art's alpha filled with a CSS colour
def mask(file, colour, w_, h_):
    raw = open(IMG + file).read()
    raw = re.sub(r'<\?xml[^>]*\?>', '', raw); raw = re.sub(r'<title>.*?</title>', '', raw, flags=re.S)
    vb = re.search(r'viewBox="([^"]+)"', raw).group(1)
    body = re.search(r'<svg[^>]*>(.*)</svg>', raw, flags=re.S).group(1)
    body = re.sub(r'fill="(?!none)[^"]*"', f'fill="{colour}"', body)
    body = re.sub(r'stroke="(?!none)[^"]*"', f'stroke="{colour}"', body)
    return svg(w_, h_, vb, f'<g fill="{colour}">{body}</g>')
w('conversationBack.svg', mask('sortArrowLeft.svg', '#868E96', 24, 24))
w('conversationBack--hover.svg', mask('sortArrowLeft.svg', '#495057', 24, 24))
w('caret.svg', mask('arrowDown.svg', '#141414', 8, 7))
w('caret--tray.svg', mask('arrowDown.svg', '#4E4D4C', 8, 7))
w('caret--picked.svg', mask('arrowDown.svg', '#FFFFFF', 8, 7))
w('socialX.svg', mask('frontpage/social-x.svg', '#4E4D4C', 17, 17))
w('socialX--hover.svg', mask('frontpage/social-x.svg', '#000000', 17, 17))
w('socialFacebook.svg', mask('frontpage/social-facebook.svg', '#4E4D4C', 19, 19))
w('socialFacebook--hover.svg', mask('frontpage/social-facebook.svg', '#0866FF', 19, 19))
w('socialYouTube.svg', mask('frontpage/social-youtube.svg', '#4E4D4C', 22, 22))
w('socialYouTube--hover.svg', mask('frontpage/social-youtube.svg', '#FF0000', 22, 22))
xl = inner('socialXLegacy.svg').replace('currentColor', '#212529')
vbx = re.search(r'viewBox="([^"]+)"', open(SRC + 'socialXLegacy.svg').read()).group(1)
w('socialXOld.svg', svg(20, 20, vbx, f'<g fill="#212529">{xl}</g>'))

# glyphs set in type
def glyphText(ch, colour, size=20, fs=18, y=16, font='Arial, Helvetica, sans-serif'):
    return svg(size, size, f'0 0 {size} {size}', f'<text x="{size/2}" y="{y}" text-anchor="middle" font-family="{font}" font-weight="bold" font-size="{fs}" fill="{colour}">{ch}</text>')
w('glyphHeart.svg', glyphText('♥', '#F03E3E', 16, 15, 13))
w('glyphCheck.svg', glyphText('✔', '#43A038', 16, 14, 13))
w('glyphCheck--settings.svg', glyphText('✔', '#4F800B', 16, 14, 13))
w('glyphPinochleM.svg', glyphText('M', '#212529', 18, 16, 15))
print(len(files), 'files'); print(' '.join(files))

# the yellow 'play this day' triangle that leaks into the daily deal dialog: the caret turned -90 degrees, 14x16
raw = open(IMG + 'arrowDown.svg').read()
vb = re.search(r'viewBox="([^"]+)"', raw).group(1).split()
body = re.search(r'<svg[^>]*>(.*)</svg>', re.sub(r'<title>.*?</title>', '', raw, flags=re.S), flags=re.S).group(1)
body = re.sub(r'fill="(?!none)[^"]*"', 'fill="#FDC41B"', body)
vw, vh = float(vb[2]), float(vb[3])
w('dealDayPlay.svg', svg(14, 16, f'0 0 {vh} {vw}', f'<g fill="#FDC41B" transform="translate(0 {vw}) rotate(-90)">{body}</g>'))

# the movement chips' arrow, drawn in its chip (the chip fill and the arrow both recolour)
def chip(bg, ink, up):
    rot = f' transform="rotate(180 {vw/2} {vh/2})"' if up else ''
    b2 = re.sub(r'fill="(?!none)[^"]*"', f'fill="{ink}"', re.search(r'<svg[^>]*>(.*)</svg>', re.sub(r'<title>.*?</title>', '', raw, flags=re.S), flags=re.S).group(1))
    sc = 6 / vw
    return svg(16, 14, '0 0 16 14', f'<rect x="0" y="0" width="16" height="14" rx="5" fill="{bg}"/><rect x=".5" y=".5" width="15" height="13" rx="4.5" fill="none" stroke="#000000" stroke-opacity=".16"/>'
               f'<g transform="translate(5 {7 - vh * sc / 2:.2f}) scale({sc:.4f})"><g fill="{ink}"{rot}>{b2}</g></g>')
w('moveUp.svg', chip('#B2DD9B', '#305812', True))
w('moveDown.svg', chip('#FCBCB4', '#8B1A1A', False))
print('extra done')
