# -*- coding: utf-8 -*-
"""The picker thumbnails.
   A weave is shown at the size the table draws it, because its grain is the thing being judged.
   A pattern is shown at half that, so its motif reads without one flower filling the tile.
   A seasonal one is shown whole: they are drawn far bolder than the rest, and contrast does not
   catch that (the ditsy florals measure busier and look right), so this follows the eye.
   The window is laid out on a 240px canvas, the 120px the picker scales it to at 2x, and only its middle
   is written: the 67px a tile is at its widest, at 2x (Holger, 8 Oct 2026: "Make smaller wallpaper
   thumbnails"). The picker draws it at 67px (_wm-settings.scss), so every pixel shown is the one it was
   before, at a third of the bytes. A full image is drawn whole into the tile, so it is written at 134px.
   They go to tile/ rather than over thumb/, so a browser holding an old thumbnail cannot draw it at the
   new size."""
import json, os, subprocess
from PIL import Image

BASE, THUMB, WINDOW = "static/pieces/wallpaper", 240, 120
SHOWN = 134                    # the widest a tile draws, 67px, at 2x
WHOLE_TILE_GROUPS = {"seasonal"}

items = json.loads(subprocess.run(["node", "-e", """
const C=require("./shared/C.js");const out=[];
C.WALLPAPERS.forEach(g=>g.items.forEach(i=>out.push({id:g.id+"/"+i.id,group:g.id,size:i.size||0,cover:!!i.cover,motif:!!i.motif})));
C.WALLPAPERS_LEGACY.forEach(g=>g.items.forEach(i=>{ if(!out.some(o=>o.id===g.id+"/"+i.id)) out.push({id:g.id+"/"+i.id,group:g.id,size:0,cover:false,motif:true}); }));
console.log(JSON.stringify(out));"""], capture_output=True, text=True).stdout)

total = 0
for it in items:
    src = Image.open(os.path.join(BASE, it["id"])).convert("RGB")
    out = os.path.join(BASE, "tile", os.path.splitext(it["id"])[0] + ".jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if it["cover"]:
        w, h = src.size; s = min(w, h)
        canvas = src.crop(((w-s)//2, (h-s)//2, (w-s)//2+s, (h-s)//2+s)).resize((SHOWN, SHOWN), Image.LANCZOS)
    else:
        repeat = it["size"] or src.size[0]
        if not it["motif"]:            window = WINDOW
        elif it["group"] in WHOLE_TILE_GROUPS: window = repeat
        else:                          window = max(WINDOW, round(repeat / 2))
        tile_px = max(8, round(repeat * (THUMB / window)))
        tile = src.resize((tile_px, tile_px), Image.LANCZOS)
        if tile_px >= THUMB:
            o = (tile_px - THUMB) // 2
            canvas = tile.crop((o, o, o + THUMB, o + THUMB))
        else:
            canvas = Image.new("RGB", (THUMB, THUMB))
            for y in range(0, THUMB, tile_px):
                for x in range(0, THUMB, tile_px): canvas.paste(tile, (x, y))
        o = (THUMB - SHOWN) // 2
        canvas = canvas.crop((o, o, o + SHOWN, o + SHOWN))
    canvas.save(out, "JPEG", quality=74, optimize=True, progressive=True)
    total += os.path.getsize(out)
print("thumbnails rewritten:", len(items), "| %.2f MB" % (total / 2**20))
