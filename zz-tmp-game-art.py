#!/usr/bin/env python3
"""Cuts Khang's game art down to the files the frontpage draws.

The delivery is one folder per game holding four full-size PNGs: the logo on
transparent, the background on its own, the two composited into a banner, and a
square app icon. The frontpage wants the first two.

The banner is the third file's whole point: it says how big Khang drew each logo
against its own background, and the answer is not the same for two games. Hearts
takes 64% of the canvas width, Sergeant Major 54%, Hand & Foot 96%. Fitting every
logo into one box throws that away and makes them all look the same size, so the
sizes below are measured off the banners instead and the page draws each logo at
its own share of the tile.

    logos/<art>_logo@tile.webp  the hero and catalog tiles
    logos/<art>_logo@2x.png     the corner art on a felt table tile
    art/<art>_bg.jpg            the tile's background

<art> is the game id for sixteen of the eighteen games; Double Deck Pinochle and
Sergeant Major keep the mockup's own names, which the site already asks for.

    python3 zz-tmp-game-art.py            writes the files
    python3 zz-tmp-game-art.py --measure  re-derives the table below and prints it
"""

import os
import sys
from PIL import Image, ImageChops

SRC = os.path.expanduser("~/Downloads/World of Card games 4")
OUT = "/srv/wocg/worldofcardgames/static/images/frontpage"

# gameid, delivery folder, delivery file prefix, name the site asks for
GAMES = [
    ("hearts",         "Hearts",               "hearts",     "hearts"),
    ("spades",         "Spades",               "spades",     "spades"),
    ("euchre",         "Euchre",               "euchre",     "euchre"),
    ("bridge",         "Bridge",               "bridge",     "bridge"),
    ("pinochle",       "Pinochle",             "pinochle",   "pinochle"),
    ("pinochledd",     "Double Deck Pinochle", "ddpinochle", "ddpinochle"),
    ("whist",          "Whist",                "whist",      "whist"),
    ("twentynine",     "Twenty-Nine",          "29",         "twentynine"),
    ("threefiveeight", "Sergeant Major",       "358",        "sgtmajor"),
    ("sheepshead",     "Sheepshead",           "sheepshead", "sheepshead"),
    ("rummy",          "Rummy",                "rummy",      "rummy"),
    ("ginrummy",       "Gin Rummy",            "ginrummy",   "ginrummy"),
    ("handfoot",       "Hand&Foot",            "handfoot",   "handfoot"),
    ("canasta",        "Canasta",              "canasta",    "canasta"),
    ("cribbage",       "Cribbage",             "cribbage",   "cribbage"),
    ("crazyeights",    "Crazy Eights",         "crazy8",     "crazyeights"),
    ("gofish",         "Go Fish",              "gofish",     "gofish"),
    ("oldmaid",        "Old Maid",             "oldmaid",    "oldmaid"),
]

# Measured with --measure: the logo's width, height and centre on its own banner,
# as a percentage of the 1920x1440 canvas. The width is the number the tiles are
# sized from; the height is here so the page can reserve the right box, and the
# vertical centre because a handful of the logos are not on the middle line.
# The horizontal centre came back 49.4-50.1 for all eighteen, so they are centred.
BANNER = {
    "hearts":      {"w": 63.7, "h": 62.3, "cy": 50.0},
    "spades":      {"w": 64.4, "h": 62.2, "cy": 49.9},
    "euchre":      {"w": 66.0, "h": 64.7, "cy": 49.8},
    "bridge":      {"w": 62.5, "h": 66.0, "cy": 49.9},
    "pinochle":    {"w": 80.6, "h": 71.1, "cy": 50.1},
    "ddpinochle":  {"w": 86.7, "h": 72.8, "cy": 50.1},
    "whist":       {"w": 60.2, "h": 65.2, "cy": 51.6},
    "twentynine":  {"w": 82.9, "h": 49.1, "cy": 52.1},
    "sgtmajor":    {"w": 53.5, "h": 70.7, "cy": 49.4},
    "sheepshead":  {"w": 96.0, "h": 67.7, "cy": 48.8},
    "rummy":       {"w": 68.3, "h": 68.6, "cy": 50.0},
    "ginrummy":    {"w": 90.6, "h": 68.6, "cy": 48.4},
    "handfoot":    {"w": 95.8, "h": 63.8, "cy": 53.0},
    "canasta":     {"w": 75.4, "h": 65.6, "cy": 50.0},
    "cribbage":    {"w": 75.4, "h": 63.4, "cy": 52.6},
    "crazyeights": {"w": 76.5, "h": 58.5, "cy": 52.9},
    "gofish":      {"w": 69.6, "h": 65.1, "cy": 50.8},
    "oldmaid":     {"w": 79.2, "h": 70.6, "cy": 49.9},
}

# The widest a tile logo is ever drawn. Every game reaches 266 CSS px in a
# four-column catalog row; Hearts also holds the hero's big slot at 479.
CAT_TILE = 266
HERO_SLOT = {"hearts": 479}

# The felt tile's corner art is a badge, not the banner, so it is the banner
# share shrunk by one shared factor. 0.314 is the factor that leaves the average
# drawn width exactly where the fixed 44px height used to put it; Holger asked
# for the badge bigger than that, and settled on 0.34 after 0.40 and 0.36.
FELT_SHARE = 0.34
FELT_BOX = 360          # the widest art box, in the table-preview modal

BG_SIZE = (960, 720)    # the hero's widest slot is 479 CSS px, so this covers 2x
BG_QUALITY = 86


def logo_path(folder, prefix):
    for name in (prefix + "_logo.png", prefix + "_logo_logo.png"):
        path = os.path.join(SRC, folder, name)
        if os.path.exists(path):
            return path
    raise SystemExit("no logo for " + folder)


def load_logo(folder, prefix):
    """The delivered logo, trimmed to its own ink.

    Four games are delivered as <prefix>_logo_logo.png, and Crazy Eights is
    delivered on the full 1920x1440 canvas rather than trimmed, so both are
    normalised here instead of by hand.
    """
    im = Image.open(logo_path(folder, prefix)).convert("RGBA")
    return im.crop(im.getbbox())


def resize_rgba(im, width):
    """Downscale to a width, on premultiplied alpha.

    The transparent pixels around the lettering carry black, so resizing the
    colour channels on their own pulls that black into the white outline and
    leaves a grey fringe. PIL's RGBa mode multiplies the colour by the alpha
    first and divides it back out after, which keeps the outline white.
    """
    height = max(1, round(width * im.size[1] / im.size[0]))
    return im.convert("RGBa").resize((width, height), Image.LANCZOS).convert("RGBA")


def measure():
    """Fits each logo back onto its own banner and prints the BANNER table.

    Thresholding the banner against the background finds the lettering but loses
    the faintest of the drop shadow, which reads two or three percent small, so
    that answer is only the seed: the size and place that actually reproduce the
    banner are found by compositing. Runs at a quarter of the canvas and takes a
    few minutes.
    """
    import numpy as np
    W, H = 480, 360

    def error(bg, banner, logo, width, cx, cy):
        small = resize_rgba(logo, width)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(small, (round(cx - width / 2), round(cy - small.size[1] / 2)))
        out = Image.alpha_composite(bg, canvas).convert("RGB")
        return float(np.abs(np.asarray(out, np.int16) - banner).mean())

    for gameid, folder, prefix, art in GAMES:
        full_bg = Image.open(os.path.join(SRC, folder, prefix + "_bg.png")).convert("RGB")
        full_bn = Image.open(os.path.join(SRC, folder, prefix + "_banner.png")).convert("RGB")
        fw, fh = full_bg.size
        seed = ImageChops.difference(full_bg, full_bn).convert("L") \
            .point(lambda v: 255 if v > 6 else 0).getbbox()

        bg = full_bg.resize((W, H), Image.LANCZOS).convert("RGBA")
        banner = np.asarray(full_bn.resize((W, H), Image.LANCZOS), np.int16)
        logo = load_logo(folder, prefix)

        best = (None, round((seed[2] - seed[0]) / fw * W),
                (seed[0] + seed[2]) / 2 / fw * W, (seed[1] + seed[3]) / 2 / fh * H)
        best = (error(bg, banner, logo, best[1], best[2], best[3]),) + best[1:]
        for _ in range(4):
            for dw in range(-10, 11):
                e = error(bg, banner, logo, best[1] + dw, best[2], best[3])
                if e < best[0]: best = (e, best[1] + dw, best[2], best[3])
            for dx in range(-5, 6):
                for dy in range(-5, 6):
                    e = error(bg, banner, logo, best[1], best[2] + dx, best[3] + dy)
                    if e < best[0]: best = (e, best[1], best[2] + dx, best[3] + dy)
        e, width, cx, cy = best
        height = width * logo.size[1] / logo.size[0]
        print('    "%s":%s{"w": %.1f, "h": %.1f, "cy": %.1f},   # cx %.1f, residual %.2f' %
              (art, " " * max(1, 13 - len(art)), width / W * 100, height / H * 100,
               cy / H * 100, cx / W * 100, e))


def build():
    logos = os.path.join(OUT, "logos")
    art_dir = os.path.join(OUT, "art")
    os.makedirs(art_dir, exist_ok=True)

    print("%-14s %-13s %-13s %s" % ("game", "tile logo", "felt logo", "share of the tile"))
    for gameid, folder, prefix, name in GAMES:
        logo = load_logo(folder, prefix)
        share = BANNER[name]["w"] / 100

        tile = resize_rgba(logo, round(2 * max(CAT_TILE, HERO_SLOT.get(name, 0)) * share))
        tile.save(os.path.join(logos, name + "_logo@tile.webp"), quality=88, method=6)

        felt = resize_rgba(logo, round(2 * FELT_BOX * share * FELT_SHARE))
        felt.save(os.path.join(logos, name + "_logo@2x.png"), optimize=True)

        bg = Image.open(os.path.join(SRC, folder, prefix + "_bg.png")).convert("RGB")
        bg.resize(BG_SIZE, Image.LANCZOS).save(
            os.path.join(art_dir, name + "_bg.jpg"), "JPEG",
            quality=BG_QUALITY, optimize=True, progressive=True)

        print("%-14s %-13s %-13s tile %.1f%%  felt %.1f%%" %
              (name, "%dx%d" % tile.size, "%dx%d" % felt.size,
               BANNER[name]["w"], BANNER[name]["w"] * FELT_SHARE))


if __name__ == "__main__":
    measure() if "--measure" in sys.argv else build()
