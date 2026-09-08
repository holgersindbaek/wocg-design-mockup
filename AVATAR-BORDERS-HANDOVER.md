# Avatar borders and outline: handover

Status doc for the avatar work in this design repo (`Design/WoCG-3/`). Written 2026-09-07, brought to v8 the same evening, so a fresh session can continue without the chat history. Update it at the end of every session.

## 1. What Holger wants (the brief, in his words and in order)

1. Study the avatars on the felt table; use the frontpage's inner/outer border pair from the open-tables listing. Done: `avatar-lab.html`, `AVATAR-STUDY.md` sections 1 to 12.
2. Then the drawing itself, not the coat: darker inner borders on the pieces of the capped man so the pieces separate. Done: `avatar-svg-lab.html`, `AVATAR-STUDY.md` section 13.
3. The borders must be faint: "just separate the colours a bit more". Pick: black at 15%, 2 units wide (in the 160-unit box).
4. Apply it to every avatar as a chooser option in `game-settings-lab-3.html` ("Avatar borders" knob: plain / bordered). Done, folder `game-assets/avatars-bordered/`.
5. Where the border goes (this is the part still being tuned):
   - An inner border on each piece. The teeth get theirs outside.
   - Never a line between a piece and its own shading (a face and its shadow, hair and its highlight). Judge "same piece" by colour, not by lightness alone.
   - The line sits on the darker side of an edge: white or grey hair beside a face puts the line on the face, not in the hair.
   - Blonde hair must still get its border (7 Sept, 15:32: "the blonde hair is still not coloured"). Hair drawn in several pieces must be bordered as a whole, not only some of the locks.
6. The outline around the whole avatar (the coat, in the settings lab's "Avatar edge" knob):
   - He likes the game's outline as one true line, but it must render as a real 1px; the current `game1` is thinner than 1px.
   - The frontpage pair without its shadow "looks smoother" but its ring must be a solid colour, not the translucent 32% black.
7. Latest ask (7 Sept, 15:32): "do a deeper dive, figure out exactly how to do this properly and set up rules so it works on all of them".

## 2. Where everything is

| thing | path |
|---|---|
| the study text, all rounds | `AVATAR-STUDY.md` (section 13 has one bullet per round of the border work) |
| the coat lab (79 render-time coats) | `avatar-lab.html`, assets in `avatar-lab/` |
| the capped-man SVG lab | `avatar-svg-lab.html`, generators `zz-tmp-build-avatar-svg.py`, `zz-tmp-build-avatar-svg-soft.py` (also `lottie_strokes()`) |
| the set-wide border generator | `zz-tmp-build-avatar-borders.py` (reads `game-assets/avatars/*.svg`, writes `game-assets/avatars-bordered/*.svg` + `decisions.json`) |
| the chooser | `avatar-borders-lab.html`: the knobs are a section of their own, **The avatars** — `avborder` (bordered-v9 / bordered / plain) and `avedge` (game1 / game15 / gamein / game / front / frontamb). It opens on the Design tab, the Avatar page, on v9 with the game's true 1px outline. Hover or click the **Chooser** handle at the right edge; `z` flips the last knob, up and down step it. `game-settings-lab-3.html` is stale: it has no avatar knobs, no outline and points at the plain folder. |
| the published box | `game-settings.html` (another session's, tracked): the settled copy, chooser hidden and keyboard knobs off. Its defaults now open on the Design tab with the bordered avatars. Do not commit it. |
| the frontpage pair's source | `index.html` filter `#avatarEdge-litrim8` (erode 1px, white 8% rim) + `body.avsh-ghostramp32` (four 1px black 32% drop-shadows) |
| the emotion animations | `zz-tmp-build-avatar-lottie.py` writes `game-assets/avatars-lottie-v9/` (473 bordered JSONs, the copies the app would take), its `borders.json` audit, and `js/` for the lab. Written up in `AVATAR-LOTTIE-HANDOFF.md` |
| judging harness (not in git) | `/tmp/avjudge3/` : `shots.py NAME...` (one plate per avatar: plain, bordered, and a red map of where the line fell, plus 96 and 48px under the coat), `sheet.py OUT.png SIZE COLS names...` (contact sheet, plain beside bordered, coat on), `facts.py NAME...` (what the generator decided, in words), `ledger.py` (every edge in the set, flagging doubled, missing and partial ones), `material.py probe` (the shade/tint test on known pairs) |
| older scratch | `/tmp/avstudy/` : `v7/render/` (the generator's own render pages), earlier QA sheets |
| headless browser | `/opt/homebrew/bin/chromium --headless=new --screenshot=... --window-size=... --force-device-scale-factor=N`; Firefox headless also used for cross-checks |

## 3. Git rules for this repo

- Remote `https://github.com/holgersindbaek/wocg-design-mockup.git`, branch `main`. Commit with an explicit pathspec, never a bare `git commit -a`.
- Other sessions own: `index.html` (modified), `open-tables-slide-lab.html` (modified), and the untracked `game-settings-lab-3.html`, `game-assets/avatars/`, `game-assets/cards|decks|live|ui|wallpapers/`, `game-button-lab.html`, `game-*-lab.html`, `game.html`, `GAME-*-STUDY.md`, `TEAM-COLOUR-STUDY.md`. Never commit, revert or clean them. `game-settings-lab-3.html` has my knob edits in it but stays uncommitted; a backup of it is at `/tmp/avstudy/game-settings-lab-3.backup.html`.
- Mine, committed: `avatar-lab.html`, `avatar-lab/`, `avatar-svg-lab.html`, `AVATAR-STUDY.md`, `zz-tmp-build-avatar-*.py`, `game-assets/avatars-bordered/`, this file. Push after every commit.

## 4. The generator as of v9

`zz-tmp-build-avatar-borders.py`, usage `python3 zz-tmp-build-avatar-borders.py [--base] [names...]` (`--base` = the 189 files without `_win/_think/_lose`; the full set is 664 files and takes about four minutes). It writes `game-assets/avatars-bordered/*.svg` and `decisions.json` (per file, per part: its colour as seen in CIELAB and the runs along its outline with their decision and length in units).

How it decides, per file:
1. One headless Chromium page (`/tmp/avstudy/v7/render/<file>.html` and `.png`) with three kinds of `<img>`: the drawing with every shape in a flat id colour (`shape-rendering="crispEdges"`, `--force-color-profile=srgb`, ids 8 levels apart so the screenshot's colour drift cannot merge two shapes), the drawing as it is, and every shape alone. 3 px per unit, 8 cells per row.
2. The label map says which shape is visible at every pixel. The real render gives every shape's colour as seen (median of its interior pixels). The alone cells give every shape's full outline.
3. Parts = filled shapes over 10 units (or over 6 and near white, for teeth), not ink (L under .03), not translucent, not line art.
4. Each part's full outline is traced (`skimage.find_contours`); at every point: hidden (a later shape covers it), or the visible neighbour outside and the decision by the rules in section 5. Runs under 2 units merge into their longer neighbour; the rest become simplified polylines (tolerance 0.5 units).
5. Output per part: the shape keeps its geometry once with `id="abN"` and its fill on a wrapper `<g fill>`; the inner line is `<use class="abl" href="#abN" mask="url(#amN)">` where the mask is the shape in white plus black cut polylines (class `abc`, 5 units wide, round caps) where the part does not own the line; the outer band is the same stroke masked to white polylines (class `abk`) minus the shape in black. Both sit right after the shape so later shapes cover them. One `<style>` in the head defines the three classes.

Numbers: v9 is 664 files, gzipped +26% (4.4 to 5.5 KB); the base set is 2,328 bordered parts, 777 with outer
bands. v9 writes to `game-assets/avatars-bordered-v9/` (`--out=avatars-bordered-v9`); `game-assets/avatars-bordered/`
keeps v8, which the same script produced at commit `eed5a1b`. 30 of the
190 base files are a raster PNG in an SVG wrapper (one placeholder dog repeated), so they have no shapes to border.

Why v6 failed, for the record: it decided from bounding boxes and draw order, never from what was visible. Blonde beside light skin fell under its 6 L "darker" threshold in both directions; stops were a neighbour's whole geometry dilated, hidden parts included, so a lock under another lock cut the visible lock's line; "shade" was a box test.

## 5. The rules (as implemented in `same_material()`, `one_material()`, `owner()` and `analyse()`)

**Is it one material?** This artwork shades a piece by turning its own colour up or down, so a shade is the
piece's colour times one multiplier and a highlight is it screened by one amount. Measured on all 4,008
touching pairs in the set, real shades come in at a channel spread of 0.02 to 0.05 and real neighbours at
0.13 to 0.50, so the test separates cleanly:

1. the same colour twice (under 3 in CIE76): one material
2. both greys (chroma under 10): one material up to 22 L apart, since every grey is a multiple of every other
3. a grey beside a colour: a change of material, EXCEPT a near-white mark (L over 88) smaller than half its
   neighbour, either lying inside that neighbour (75% of its visible ring) or on a light piece (L over 75)
   under 24 apart in CIE76: that is a shine, not a piece. A mouth feature is never a shine (see below).
4. both coloured: one material when a single multiplier (0.45 to 1.0) or a single screen (0.0 to 0.40) carries
   one to the other on every channel, the channels agreeing within 0.09. A real highlight here screens by 0.24
   to 0.30; the bound was 0.55 in v8, which read a face's shaded half as its hair screened by 52%

**Which side?** Per visible edge between a part and its neighbour, once they are different materials:

1. the background (the silhouette): the part keeps its inner line, near-white included; the coat sits outside it
2. one side grey, the other coloured: the darker of the two owns it, with no margin. White hair is lighter than a
   face, so the face takes it; grey hair is darker, so the hair takes it. v8 gave the line to the coloured side
   unless the grey was 18 L darker, which put a grey hair 17.5 L darker than its face on the face
3. both coloured or both grey, more than 18 L apart: the darker side
4. otherwise the more saturated side, and failing that the piece drawn on top
5. nothing at all when the owner is under 25 L and the seam is already over 40 apart in CIE76: a black line on
   black hair cannot be seen, and pale skin beside it needs no help

**The mouth.** A part that lies inside a bigger piece (60% of its visible ring), covers under 6% of it, sits below
that piece's middle, and is either near-white or 12 L darker than it, is a mouth feature: never merged as a shine,
and stroked at 35% instead of 15% so the smile reads. 73 parts over 42 files. Mouths drawn in ink are dark already
and are left alone.

**Placement.** The line follows the top piece's outline: its own inner line where it owns the edge, an outer band
onto the piece under it where that piece owns it AND this piece lies on it (where the two merely abut, the
neighbour draws its own inner line, so no edge carries the line twice). Hidden outline gets nothing. Tiny shapes
(under 10 units), translucent shapes and line art are never bordered; a dark fill is line art only when it is
small (under 24 units across or 250 square units), so hair drawn in near-black is a piece.

Thresholds are the constants at the top of the script: `T_L, T_C, T_GREY = 18, 8, 10`,
`SPREAD, K_LO, K_HI, T_LO, T_HI = 0.09, 0.45, 1.0, 0.0, 0.55`, `T_GREY_L = 22`,
`PALE_L, LIGHT_L, MARK_AREA, MARK_RING, MARK_DE = 88, 75, 0.5, 0.75, 24`, `INK_DIM, INK_AREA = 24, 250`,
`DARK_L, FAR = 25, 40`,
`MOUTH_RING, MOUTH_AREA, MOUTH_L, MOUTH_OP = 0.6, 0.06, 12, 0.35`, `MIN_DIM, MIN_RUN, TOL = 10, 2.0, 0.5`, `W, OP, CUT = 4, 0.15, 5`.

Why v7 failed, for the record: its material test compared hue, chroma and lightness, which merged brown hair with
tan skin (the "only some of the hair gets a border" complaint) and split a spectacle lens from its own shine; it
read `.a,.b{fill:none}` as a rule for `.b` only, so a stroke-only shape in 213 of the 665 files was taken for a
black fill and painted black; it treated any fill under L .03 as line art, so hair in near-black got nothing; its
near-white silhouette exemption left white shirts and bodies unrimmed beside rimmed neighbours; and it banded onto
a neighbour even where the two merely abutted, so 71 edges carried the line twice.

## 6. The outline (coat), done in the settings lab on 7 Sept

- `game1` (`#avatarLine1`): blur 1.0 and a cut at alpha 0.16 (1.0 px outside the silhouette). Measured on a rendered disc: the old 0.55 blur gave a 0.6 px ring; this gives 1.0 to 1.2 px at DPR 1 and 2 (`/tmp/avstudy/ring/test.py`).
- `game15` (`#avatarLine15`): the same at 1.5 px, for the "bigger" comparison.
- `front` (`#avatarPairSolid`): the solid pair: the 1 px ring in solid `#252525` under the art, the 1 px inner rim at white 8% over it, no translucent shadows. `frontamb` keeps the frontpage's translucent pair with its ambient.
- All in `game-settings-lab-3.html` only (uncommitted, other session's file). If Holger picks one, the shipping version goes into `_variables.scss` / `body_open.dust` in the app repo as `AVATAR-STUDY.md` section 11 describes.

## 6b. The animations, done 8 September

All 473 emotion Lottie files now carry the same border, and it survives the movement. Per bordered
shape the pass adds one layer: the layer cloned, pruned to that shape, its fill replaced by a stroke,
and one additive mask carrying the shape's own path, which keeps the inner half of the stroke. The
stroke and the mask are the same path, so a morphing mouth morphs its border with it.

Three things the proof had wrong or left open, all settled by measurement: the stroke is 4 units wide
and not 8 (the v9 SVGs mask half of a 4-unit stroke away, so the line the eye sees is 2 units), the
width has to be divided by the scale from the shape's own space to the comp (10 for four fifths of
the groups, but 1 to 12 across the set), and a layer that holds several pieces has to be cut open at
the point where a line goes in or the line paints over the pieces that were covering it.

Which shapes get a line comes from two places. A Lottie shape is matched to its SVG part on
geometry, which reaches 78% of shapes and is right on 99.5% of them; fill hex, the first idea, would
decide 13%. The 3,508 shapes the still cannot reach, and every neighbour, are read off the
animation's OWN render: the pass renders each file the way the generator renders an SVG, a label map
with every shape in a flat id colour plus each shape alone, and runs the generator's own material
and ownership rules on it.

The per-edge cuts cannot be carried: lottie gives a layer two clips and both are area operations, so
a line is stroked whole or not at all. A shape is stroked when the line v9 draws INSIDE it is at
least as long as the line v9 leaves off it. The band v9 draws outside a shape, onto the darker piece
below, IS carried, by an inverted mask of the shape's own path plus a track matte to a hidden copy of
the neighbour; 1,292 of them. The mouth is exempt from the ownership rule, because two thirds of the
mouth lines in the still are bands and the smile is the one place the border is meant to be seen.

The test to judge it by is frame 0 of the animation against the BASE still, not the emotion still:
the table shows `ManCaveman.svg`, hides it and plays `ManCaveman_think.json` from frame 0, so that
is the pose the border has to match or it pops the moment the animation starts.

Cost: 2.71 to 3.72 MB gzipped over the 473 files, 5.9 to 8.0 KB each. The whole record, the traps and
what is still open are in `AVATAR-LOTTIE-HANDOFF.md`. `avatar-borders-lab.html` plays them: hover an
avatar to load its three files, click to play one, click again for the next.

## 7. Open questions for Holger

- Which coat: the true 1px game line (`game1`, or `game15` at 1.5px), or the solid pair (`front`: the ring in
  `#252525` and the rim at white 8%)?
- The silhouette line is 53% of everything the border draws. It sits just inside the coat and mostly reads as a
  slight thickening of it. Keep it, or let the coat do the outside alone and keep the border for the seams only?
  Cheap to try: it is one branch in `analyse()`.
- Lottie: settled. The masked inset border IS carried into the emotion animations, by a per-shape layer mask
  rather than a centred stroke. Section 6b. What is left is the outer band, the 130 merge-paths shapes and
  the 9% of the still's line that the whole-shape rule drops; all three are in `AVATAR-LOTTIE-HANDOFF.md` section 7.
- 30 of the 190 base avatars are a raster PNG in an SVG wrapper (one placeholder dog repeated under 30 names).
  They cannot take a border. Redraw them, or leave them?
