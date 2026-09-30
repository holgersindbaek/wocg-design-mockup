#!/usr/bin/env python3
"""The settled logo (Holger, 30 Sep 2026), cut to every size the site ships.

The sources in src/ are Holger's exports: favicon.svg (the fan with the big heart, for the browser's tiny icon),
logo_icon.svg (the fan as drawn, for app-sized icons) and logo.svg (the fan with World of Card Games), each with
a @3x PNG. This writes into the wocg repo:

  static/images/logo.svg, logo.png (374x96, the whole logo canvas at the old file's height), logoIcon.png (1280 square)
  web/public/favicon.ico (16, 24, 32, 48, 64), favicon.svg, worldofcardgames.jpg (the share image, 1200x630)
  web/public/favicons/favicon-*.png (from the favicon art, transparent), apple-touch-icon-*.png (the fan on the
  site's band paper, opaque, as iOS wants; 180 added), mstile-*.png (transparent, at the old files' pixel sizes)

    python3 make.py
"""
import pathlib, shutil
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / 'src'
WOCG = pathlib.Path('/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/worldofcardgames')
IMAGES = WOCG / 'static/images'
PUBLIC = WOCG / 'web/public'
FAVICONS = PUBLIC / 'favicons'
PAPER_BAND = (244, 238, 229)   # --paper-band #f4eee5, the menubar's paper
PAPER_PAGE = (249, 246, 242)   # --paper-page #f9f6f2

def art(name):
    """The @3x export cropped to its ink (alpha over 8), so every fit works from the art, not the canvas."""
    im = Image.open(SRC / (name + '@3x.png')).convert('RGBA')
    box = im.getchannel('A').point(lambda v: 255 if v > 8 else 0).getbbox()
    return im.crop(box)

def fit(src, w, h, margin=0.0, bg=None):
    """src scaled to sit inside w x h with a margin (a share of the shorter side) around it, centred, on a clear
    canvas or an opaque colour."""
    m = round(min(w, h) * margin)
    iw, ih = w - 2 * m, h - 2 * m
    s = min(iw / src.width, ih / src.height)
    sw, sh = max(1, round(src.width * s)), max(1, round(src.height * s))
    im = src.resize((sw, sh), Image.LANCZOS)
    out = Image.new('RGBA', (w, h), (bg + (255,)) if bg else (0, 0, 0, 0))
    out.alpha_composite(im, ((w - sw) // 2, (h - sh) // 2))
    return out if bg is None else out.convert('RGB')

def main():
    favicon, icon, logo = art('favicon'), art('logo_icon'), art('logo')
    written = []
    def save(im, path, **kw):
        path.parent.mkdir(parents=True, exist_ok=True)
        im.save(path, **kw); written.append(path)

    # the logo: the SVG for the bar, the PNG at the old file's height, the square icon
    shutil.copy(SRC / 'logo.svg', IMAGES / 'logo.svg'); written.append(IMAGES / 'logo.svg')
    canvas = Image.open(SRC / 'logo@3x.png').convert('RGBA')          # the whole export, its own air kept
    save(canvas.resize((round(canvas.width * 96 / canvas.height), 96), Image.LANCZOS), IMAGES / 'logo.png', optimize=True)
    save(fit(icon, 1280, 1280, margin=0.08), IMAGES / 'logoIcon.png', optimize=True)

    # the browser's icon: the favicon art, transparent
    shutil.copy(SRC / 'favicon.svg', PUBLIC / 'favicon.svg'); written.append(PUBLIC / 'favicon.svg')
    for n in (16, 32, 96, 128, 196):
        save(fit(favicon, n, n), FAVICONS / ('favicon-%dx%d.png' % (n, n) if n != 128 else 'favicon-128.png'), optimize=True)
    frames = [fit(favicon, n, n) for n in (16, 24, 32, 48, 64)]
    frames[-1].save(PUBLIC / 'favicon.ico', format='ICO', append_images=frames[:-1], sizes=[(f.width, f.height) for f in frames]); written.append(PUBLIC / 'favicon.ico')

    # the home-screen icons: the fan on the band's paper, opaque, since iOS paints a clear icon black
    for n in (57, 60, 72, 76, 114, 120, 144, 152, 180):
        save(fit(icon, n, n, margin=0.07, bg=PAPER_BAND), FAVICONS / ('apple-touch-icon-%dx%d.png' % (n, n)), optimize=True)

    # the Windows tiles: transparent on the tile colour, at the pixel sizes the old files had
    for name, w, h in (('mstile-70x70', 128, 128), ('mstile-144x144', 144, 144), ('mstile-150x150', 270, 270), ('mstile-310x150', 558, 270), ('mstile-310x310', 558, 558)):
        save(fit(icon, w, h, margin=0.14), FAVICONS / (name + '.png'), optimize=True)

    # the share image: the logo on the page's paper
    share = Image.new('RGB', (1200, 630), PAPER_PAGE)
    lg = fit(logo, 900, 400)
    share.paste(lg, ((1200 - lg.width) // 2, (630 - lg.height) // 2), lg)
    save(share, PUBLIC / 'worldofcardgames.jpg', quality=90, optimize=True, progressive=True)

    for p in written:
        im = Image.open(p) if p.suffix != '.svg' else None
        print('%-90s %s' % (str(p.relative_to(WOCG)), ('%s %dx%d' % (im.mode, im.width, im.height) + (' sizes ' + str(sorted(im.ico.sizes())) if p.suffix == '.ico' else '')) if im else '%d bytes' % p.stat().st_size))

if __name__ == '__main__':
    main()
