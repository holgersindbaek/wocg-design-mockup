#!/usr/bin/env python3
"""Builds pile-count-lab.html from template.html and the captured tables.

  python3 pile-count-lab-parts/build.py [--from /tmp/pile-lab/out]

--from copies fresh captures (capture.mjs's output: <scene>@<viewport>.json/.png/-bare.png) into
pile-count-lab-parts/captures/ first. The shots go next to the lab as JPEGs in pile-count-lab/; the
PNGs need not stay (only the JSON does), since a build without them keeps the JPEGs it finds.

capture.mjs runs against the dev site through the visual sweep's browser and replays:
  node pile-count-lab-parts/capture.mjs desktop,iphone-portrait,iphone-landscape \
    games/cribbage/your-discardToCrib,games/cribbage/your-playCard,games/rummy/your-pick,games/canasta/your-pick
"""
import json, os, re, shutil, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CAPTURES = os.path.join(HERE, "captures")
SHOTS = os.path.join(ROOT, "pile-count-lab")

# The tables the lab offers, in order: label, the capture's scene name, and the deck the gauge measures.
SCENES = [
    ("cribbage-start", "Cribbage · the deal", "cribbage_your-discardToCrib", 52),
    ("cribbage-cut", "Cribbage · after the cut", "cribbage_your-playCard", 52),
    ("canasta", "Canasta · stock and discard", "canasta_your-pick", 108),
    ("rummy", "Rummy · stock and discard", "rummy_your-pick", 52),
    ("handfoot", "Hand & Foot · round count too", "handfoot_your-pick", 270),
    ("crazyeights", "Crazy eights · side seats close", "crazyeights_your-playOrPick", 52),
    ("ginrummy", "Gin rummy · stock on the right", "ginrummy_your-pick", 52),
]
VIEWPORTS = ["desktop", "iphone-portrait", "iphone-landscape"]

if "--from" in sys.argv:
    src = sys.argv[sys.argv.index("--from") + 1]
    os.makedirs(CAPTURES, exist_ok=True)
    for name in os.listdir(src):
        if re.search(r"@(desktop|iphone-portrait|iphone-landscape)(-bare)?\.(json|png)$", name):
            shutil.copy2(os.path.join(src, name), os.path.join(CAPTURES, name))

os.makedirs(SHOTS, exist_ok=True)
data = {"scenes": {}}
for sid, label, cap, deck in SCENES:
    shots = {}
    for vp in VIEWPORTS:
        base = os.path.join(CAPTURES, f"{cap}@{vp}")
        if not os.path.exists(base + ".json"):
            continue
        d = json.load(open(base + ".json"))
        files = {}
        for kind, suffix in (("img", ""), ("bare", "-bare")):
            out = f"{sid}@{vp}{suffix}.jpg"
            # A fresh capture's PNG becomes the lab's JPEG; without one the JPEG already there is kept.
            if os.path.exists(base + suffix + ".png"):
                Image.open(base + suffix + ".png").convert("RGB").save(os.path.join(SHOTS, out), quality=90, subsampling=0)
            elif not os.path.exists(os.path.join(SHOTS, out)):
                sys.exit(f"missing {base + suffix}.png and {out}: run capture.mjs, then build with --from")
            files[kind] = "pile-count-lab/" + out
        piles = []
        for p in d["piles"]:
            piles.append({
                "spot": p["spot"], "rect": p["rect"], "faceUp": p["faceUp"],
                "count": p["count"], "chip": p["chip"],
                "radius": float(str(p["radius"] or "8").replace("px", "")),
            })
        shots[vp] = {"view": d["view"], "compact": d["compact"], "piles": piles, **files}
    data["scenes"][sid] = {"label": label, "deck": deck, "shots": shots}

# The play demo: Hand & Foot with every pile count, the round chip and the tabs above the name plates
# taken out (capture-play.mjs), and the tab icons from the site's images.
PLAY = os.path.join(HERE, "captures-play")
SITE_IMAGES = os.path.join(ROOT, "..", "..", "Programming", "wocg", "worldofcardgames", "static", "images")
ICONS = ["crown.svg", "playerLiked.svg", "playerMore.svg", "playerLeaving.svg", "sortArrowLeft.svg", "sortArrowRight.svg"]
data["play"] = {}
for vp in VIEWPORTS:
    base = os.path.join(PLAY, f"handfoot-play@{vp}")
    if not os.path.exists(base + ".json"):
        continue
    d = json.load(open(base + ".json"))
    out = f"play-handfoot@{vp}.jpg"
    if os.path.exists(base + "-bare.png"):
        Image.open(base + "-bare.png").convert("RGB").save(os.path.join(SHOTS, out), quality=90, subsampling=0)
    d["bare"] = "pile-count-lab/" + out
    data["play"][vp] = d
os.makedirs(os.path.join(SHOTS, "icons"), exist_ok=True)
for icon in ICONS:
    src = os.path.join(SITE_IMAGES, icon)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(SHOTS, "icons", icon))

html = open(os.path.join(HERE, "template.html")).read()
html = html.replace("/*DATA*/null/*END*/", json.dumps(data, separators=(",", ":")))
open(os.path.join(ROOT, "pile-count-lab.html"), "w").write(html)
print("built pile-count-lab.html:", ", ".join(f"{k} ({len(v['shots'])} screens)" for k, v in data["scenes"].items()), "| play:", ", ".join(data["play"].keys()))
