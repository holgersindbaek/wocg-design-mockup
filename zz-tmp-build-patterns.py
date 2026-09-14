import os, re, json, random, io, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiler import make_tile
from PIL import Image

SRC = "/Users/holgersindbaek/Downloads/Patterns"
OUT = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3/pattern-assets"
TILE_PX  = 1536          # exported tile: 2x the biggest repeat the lab offers (768)
SHEET_W  = 2560          # exported sheet: a 16:10 centre crop, which is all a landscape table ever shows
SHIP_AT  = [512, 768, 1024, 1536]   # what the file weighs at each 2x ship size, for the HUD
random.seed(7)

# folder -> (group label, slug, kind, default repeat in CSS px)
GROUPS = {
  "":                                            ("Odds",              "odds",     "auto",  384),
  "20-Felt-Texture-HQ":                          ("Felt, close up",    "felthq",   "cut",   384),
  "Felt Textures":                               ("Felt",              "feltpk",   "cut",   384),
  "paper_canvas_textures 2":                     ("Paper and canvas",  "paper",    "cut",   384),
  "CD_patterns_color":                           ("Christmas dreams",  "xmas",     "tile",  512),
  "CD_patterns_color/vivid":                     ("Christmas dreams",  "xmas",     "tile",  512),
  "Ditsy-Pastel-Flowers-Seamless-Patter":        ("Ditsy pastel",      "ditsy",    "tile",  512),
  "Seasonal-Botanical-Seamless-Pattern/PNG files": ("Seasonal botanical", "season", "tile",  512),
  "warmy_yuletide_seamlss_patterns":             ("Warm yuletide",     "yule",     "tile",  512),
  "15-Fabric-Texture-Seamless-Patterns":         ("Fabric textures",   "fabric",   "tile",  384),
  "70-Arts-Crafts-seamless-pattern":             ("Arts and crafts",   "arts",     "tile",  512),
  "Chambray-Seamless-Texture-Pattern":           ("Chambray",          "chambray", "tile",  384),
  "Green-Denim-Texture-Digital-Papers":          ("Green denim",       "denim",    "tile",  384),
  "Seamless Linen Textures":                     ("Linen",             "linen",    "tile",  384),
  "Seamless-16-Dark-Plain-Wood-Textures":        ("Dark wood",         "darkwood", "tile",  448),
  "Seamless-Fabric-Patterns-Colorful":           ("Colourful fabric",  "fabcol",   "tile",  448),
  "Seamless-Red-WOOD-Textures-Dark-jpg":         ("Red wood",          "redwood",  "tile",  448),
  "Watercolor-Painted-Texture-Paper":            ("Watercolour paper", "water",    "tile",  512),
  "Mineral Coast Imprint Vol2/Jpeg backgrounds": ("Mineral coast",     "mineral",  "sheet", 0),
  "TERRAFOLD/Earth-tone Backgrounds":            ("Terrafold earth",   "terra",    "sheet", 0),
  "TERRAFOLD/Sediment Layers":                   ("Terrafold sediment","sediment", "sheet", 0),
}
SKIP = {"25% Off Coupon.png", "FREE TEE.png", "many_thanks_for_your_purchase.jpg"}
SKIP_WORDS = ("transparent bg",)                 # the same pattern again with the background cut out
NAMES = {"IMG_8448 2": "Green card cloth"}
# one file that does not belong to its folder's group: (group name, slug, kind, repeat)
MOVE = {"Patterns/IMG_8448 2.jpg": ("Green card cloth", "cloth", "cut", 384)}

def seam(im):
    """how much worse the wrap edge is than an ordinary neighbouring pair: 1.0 = seamless"""
    g = im.convert("L"); w,h = g.size; px = g.load()
    col = lambda x: [px[x,y] for y in range(0,h,max(1,h//400))]
    row = lambda y: [px[x,y] for x in range(0,w,max(1,w//400))]
    mad = lambda a,b: sum(abs(p-q) for p,q in zip(a,b))/len(a)
    n = min(24, w-3, h-3)
    ih = sum(mad(col(x),col(x+1)) for x in random.sample(range(1,w-2),n))/n
    iv = sum(mad(row(y),row(y+1)) for y in random.sample(range(1,h-2),n))/n
    return round(mad(col(0),col(w-1))/max(ih,.5),2), round(mad(row(0),row(h-1))/max(iv,.5),2)

def label(fname, slug, n):
    stem = os.path.splitext(fname)[0]
    if stem in NAMES: return NAMES[stem]
    if (re.fullmatch(r"[\d\s()]+", stem) or re.match(r"^PB0363", stem)
            or re.fullmatch(r"Background \(\d+\)|Design \(\d+\)", stem)
            or re.fullmatch(r"IMG[_ ]?\d+( \d+)?", stem)
            or re.fullmatch(r"Felt_Texture \(\d+\)", stem)
            or re.fullmatch(r"\d+_paper_texture", stem)
            or re.fullmatch(r"CD_patterns_color_\d+(_\w+)?", stem)
            or re.fullmatch(r"warmy_yuletide_patterns_\d+", stem)
            or re.fullmatch(r"JPG \(\d+\)", stem)
            or re.fullmatch(r"\d+ Seasonal floral Seamless pattern", stem)):
        return None
    return stem.replace("_"," ").strip()

os.makedirs(OUT + "/tiles", exist_ok=True)
os.makedirs(OUT + "/sheets", exist_ok=True)

# Anything already in the manifest keeps its id and its file. New pictures take the next free
# number in their group. Without this, one new file in a folder renumbers the rest and every
# pick made in the lab would silently point at a different picture.
OLD = {}
mpath = OUT + "/patterns.js"
if os.path.exists(mpath):
    txt = io.open(mpath, encoding="utf-8").read()
    txt = txt[txt.index("=") + 1:].rstrip().rstrip(";")
    for it in json.loads(txt):
        OLD[it["src"]] = it
counters = {}
for it in OLD.values():
    g, n = it["id"].rsplit("-", 1)
    counters[g] = max(counters.get(g, 0), int(n))
items = []
kept = 0
for root, dirs, files in os.walk(SRC):
    rel = os.path.relpath(root, SRC).replace("./","")
    if rel == ".": rel = ""
    if rel not in GROUPS: continue
    relkey = rel
    gname, gslug, kind, repeat = GROUPS[rel]
    for f in sorted(files, key=lambda s: (len(s), s)):
        if f in SKIP or not f.lower().endswith((".jpg",".jpeg",".png")): continue
        if any(w in f.lower() for w in SKIP_WORDS): continue
        src = os.path.join(root, f)
        rel = os.path.relpath(src, os.path.dirname(SRC))
        im = Image.open(src); W,H = im.size
        if im.mode in ("RGBA", "LA", "P"):
            try:
                if im.convert("RGBA").getchannel("A").getextrema()[0] < 250: continue
            except Exception: pass
        square = 0.95 <= W/H <= 1.05
        if kind == "auto": kind = "tile" if square else "cut"
        if kind == "tile" and not square: continue
        if rel in MOVE: gname, gslug, kind, repeat = MOVE[rel]
        old = OLD.get(rel)
        if old and os.path.exists(os.path.join(OUT, old["file"])):
            num = int(old["id"].rsplit("-", 1)[1])
            old["name"] = label(f, gslug, num) or "%s #%d" % (gname, num)
            old["repeat"] = repeat                     # the group default can move; a pick's own size is kept in the lab
            old["group"] = gname
            items.append(old); kept += 1               # built already and picked from already: the file is left alone
            gname, gslug, kind, repeat = GROUPS[relkey]
            continue
        if old:
            slug = old["id"]; n = int(slug.rsplit("-", 1)[1])
        else:
            counters[gslug] = counters.get(gslug, 0) + 1
            n = counters[gslug]
            slug = "%s-%02d" % (gslug, n)
        target = TILE_PX if kind in ("tile", "cut") else SHEET_W
        if kind != "cut":
            im.draft("RGB", (max(1,W//8), max(1,H//8)) if min(W,H)//8 >= target else (max(1,W//4), max(1,H//4)) if min(W,H)//4 >= target else (max(1,W//2), max(1,H//2)) if min(W,H)//2 >= target else (W,H))
            im = im.convert("RGB")
        sh, sv = seam(im.resize((512,512), Image.LANCZOS)) if kind == "tile" else (None, None)
        ship = None
        if kind == "cut":
            out = make_tile(src, n=TILE_PX)
            path = "tiles/%s.jpg" % slug
            ship = {}
            for nn in SHIP_AT:
                b = io.BytesIO()
                (out if nn == TILE_PX else out.resize((nn, nn), Image.LANCZOS)).save(b, "JPEG", quality=82, optimize=True, progressive=True)
                ship[str(nn)] = round(len(b.getvalue()) / 1024)
            sh, sv = seam(out.resize((512, 512), Image.LANCZOS))
        elif kind == "tile":
            out = im.resize((TILE_PX, TILE_PX), Image.LANCZOS)
            path = "tiles/%s.jpg" % slug
            ship = {}
            for nn in SHIP_AT:                     # what it would weigh shipped at that pixel size
                b = io.BytesIO()
                (out if nn == TILE_PX else out.resize((nn, nn), Image.LANCZOS)).save(b, "JPEG", quality=82, optimize=True, progressive=True)
                ship[str(nn)] = round(len(b.getvalue()) / 1024)
        else:
            w, h = im.size                          # a landscape 16:10 band out of the middle of the sheet
            ch = int(round(w * 10 / 16))
            if ch <= h: im = im.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch))
            else:
                cw = int(round(h * 16 / 10)); im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
            out = im.resize((SHEET_W, round(SHEET_W * 10 / 16)), Image.LANCZOS)
            path = "sheets/%s.jpg" % slug
        out.save(os.path.join(OUT, path), "JPEG", quality=(78 if kind == "sheet" else 82), optimize=True, progressive=True)
        items.append({
            "id": slug, "kind": ("tile" if kind == "cut" else kind), "cut": (kind == "cut"),
            "group": gname, "file": path,
            "name": label(f, gslug, n) or "%s #%d" % (gname, n),
            "repeat": repeat, "seamH": sh, "seamV": sv, "ship": ship,
            "src": rel,
            "srcW": W, "srcH": H,
            "kb": round(os.path.getsize(os.path.join(OUT, path))/1024)
        })
        print(slug, kind, "%dx%d"%(W,H), "->", items[-1]["kb"], "KB", "seam", sh, sv, flush=True)
        gname, gslug, kind, repeat = GROUPS[relkey]

# The order the lab walks them in. Anything added later belongs at the end of this list, never in
# the middle: the lab resumes by id, but a person walking the list needs one place to start.
order = ["fabric","linen","denim","chambray","fabcol","arts","water","darkwood","redwood","odds",
         "mineral","terra","sediment",
         "felthq","feltpk","paper","cloth",
         "xmas","ditsy","season","yule"]
items.sort(key=lambda x: (order.index(x["id"].rsplit("-",1)[0]), int(x["id"].rsplit("-",1)[1])))
with open(OUT + "/patterns.js", "w") as fh:
    fh.write("/* built by zz-tmp-build-patterns.py from ~/Downloads/Patterns; do not edit by hand */\n")
    fh.write("window.PATTERNS = " + json.dumps(items, indent=0, ensure_ascii=False) + ";\n")
tiles = [i for i in items if i["kind"]=="tile"]; sheets = [i for i in items if i["kind"]=="sheet"]
print("\nDONE: %d tiles, %d sheets, %d total (%d kept untouched)" % (len(tiles), len(sheets), len(items), kept))
print("tiles  %.1f MB (avg %d KB)" % (sum(i["kb"] for i in tiles)/1024, sum(i["kb"] for i in tiles)/max(1,len(tiles))))
print("sheets %.1f MB (avg %d KB)" % (sum(i["kb"] for i in sheets)/1024, sum(i["kb"] for i in sheets)/max(1,len(sheets))))
bad = [i for i in tiles if (i["seamH"] or 0) > 2 or (i["seamV"] or 0) > 2]
print("tiles with a visible seam (ratio > 2):", len(bad), [i["id"] for i in bad])
