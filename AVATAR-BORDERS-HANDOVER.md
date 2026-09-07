# Avatar borders and outline: handover

Status doc for the avatar work in this design repo (`Design/WoCG-3/`). Written 2026-09-07 so a fresh session can continue without the chat history. Update it at the end of every session.

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
| the chooser | `game-settings-lab-3.html`: knobs `avborder` (plain/bordered) and `avedge` (game1/gamein/game/front/frontamb); `?page=look&sub=avatar&avborder=bordered` opens the picker with borders on; `z` flips the last knob, up/down step it |
| the frontpage pair's source | `index.html` filter `#avatarEdge-litrim8` (erode 1px, white 8% rim) + `body.avsh-ghostramp32` (four 1px black 32% drop-shadows) |
| scratch harness (not in git) | `/tmp/avstudy/` : `shots.py`, `all/` (measurements, QA sheets `qa-v6.png`), `v7/sheet.py` (contact sheets: `python3 sheet.py OUT.png SIZE COLS names...`) |
| headless browser | `/opt/homebrew/bin/chromium --headless=new --screenshot=... --window-size=... --force-device-scale-factor=N`; Firefox headless also used for cross-checks |

## 3. Git rules for this repo

- Remote `https://github.com/holgersindbaek/wocg-design-mockup.git`, branch `main`. Commit with an explicit pathspec, never a bare `git commit -a`.
- Other sessions own: `index.html` (modified), `open-tables-slide-lab.html` (modified), and the untracked `game-settings-lab-3.html`, `game-assets/avatars/`, `game-assets/cards|decks|live|ui|wallpapers/`, `game-button-lab.html`, `game-*-lab.html`, `game.html`, `GAME-*-STUDY.md`, `TEAM-COLOUR-STUDY.md`. Never commit, revert or clean them. `game-settings-lab-3.html` has my knob edits in it but stays uncommitted; a backup of it is at `/tmp/avstudy/game-settings-lab-3.backup.html`.
- Mine, committed: `avatar-lab.html`, `avatar-lab/`, `avatar-svg-lab.html`, `AVATAR-STUDY.md`, `zz-tmp-build-avatar-*.py`, `game-assets/avatars-bordered/`, this file. Push after every commit.

## 4. The generator as of v7 (commit a0fcffb and after)

`zz-tmp-build-avatar-borders.py`, usage `python3 zz-tmp-build-avatar-borders.py [--base] [names...]` (`--base` = the 189 files without `_win/_think/_lose`; the full set is 664 files and takes about four minutes). It writes `game-assets/avatars-bordered/*.svg` and `decisions.json` (per file, per part: its colour as seen in CIELAB and the runs along its outline with their decision and length in units).

How it decides, per file:
1. One headless Chromium page (`/tmp/avstudy/v7/render/<file>.html` and `.png`) with three kinds of `<img>`: the drawing with every shape in a flat id colour (`shape-rendering="crispEdges"`, `--force-color-profile=srgb`, ids 8 levels apart so the screenshot's colour drift cannot merge two shapes), the drawing as it is, and every shape alone. 3 px per unit, 8 cells per row.
2. The label map says which shape is visible at every pixel. The real render gives every shape's colour as seen (median of its interior pixels). The alone cells give every shape's full outline.
3. Parts = filled shapes over 10 units (or over 6 and near white, for teeth), not ink (L under .03), not translucent, not line art.
4. Each part's full outline is traced (`skimage.find_contours`); at every point: hidden (a later shape covers it), or the visible neighbour outside and the decision by the rules in section 5. Runs under 2 units merge into their longer neighbour; the rest become simplified polylines (tolerance 0.5 units).
5. Output per part: the shape keeps its geometry once with `id="abN"` and its fill on a wrapper `<g fill>`; the inner line is `<use class="abl" href="#abN" mask="url(#amN)">` where the mask is the shape in white plus black cut polylines (class `abc`, 5 units wide, round caps) where the part does not own the line; the outer band is the same stroke masked to white polylines (class `abk`) minus the shape in black. Both sit right after the shape so later shapes cover them. One `<style>` in the head defines the three classes.

Numbers for the base set: 2,370 bordered parts, 1,072 with outer bands, raw +51%, gzipped +23% (4.6 to 5.7 KB per file).

Why v6 failed, for the record: it decided from bounding boxes and draw order, never from what was visible. Blonde beside light skin fell under its 6 L "darker" threshold in both directions; stops were a neighbour's whole geometry dilated, hidden parts included, so a lock under another lock cut the visible lock's line; "shade" was a box test.

## 5. The rules (as implemented in `owner()` and `analyse()`)

Per visible edge between a part and its neighbour:
1. Background (the silhouette): the part keeps its inner line, except a near-white grey (L over 85, chroma under 10: white hair, a white shirt) which gets no grey line inside itself. The coat outside does the silhouette.
2. Same material (`same_material`: both greys within 20 L; otherwise under 32 L apart, hue within 16 degrees, chroma within half): no line.
3. One grey (chroma under 10), one coloured: the coloured side owns the line, unless the grey is darker by more than 18 L.
4. Both coloured or both grey, more than 18 L apart: the darker side.
5. Otherwise the more saturated side (chroma apart by more than 8); failing that the piece drawn on top.
6. Placement: the line follows the top piece's outline; owner = top piece gives its inner line, owner = the piece under gives an outer band from the top piece's outline onto it (white hair onto the face, teeth onto the mouth). Hidden outline gets nothing. Neighbours that are tiny (under 6 units) count as background.

Thresholds are the constants at the top of the script: `T_L, T_C, T_GREY = 18, 8, 10`, `MIN_DIM, MIN_RUN, TOL = 10, 2.0, 0.5`, `W, OP, CUT = 4, 0.15, 5`.

## 6. The outline (coat), done in the settings lab on 7 Sept

- `game1` (`#avatarLine1`): blur 1.0 and a cut at alpha 0.16 (1.0 px outside the silhouette). Measured on a rendered disc: the old 0.55 blur gave a 0.6 px ring; this gives 1.0 to 1.2 px at DPR 1 and 2 (`/tmp/avstudy/ring/test.py`).
- `game15` (`#avatarLine15`): the same at 1.5 px, for the "bigger" comparison.
- `front` (`#avatarPairSolid`): the solid pair: the 1 px ring in solid `#252525` under the art, the 1 px inner rim at white 8% over it, no translucent shadows. `frontamb` keeps the frontpage's translucent pair with its ambient.
- All in `game-settings-lab-3.html` only (uncommitted, other session's file). If Holger picks one, the shipping version goes into `_variables.scss` / `body_open.dust` in the app repo as `AVATAR-STUDY.md` section 11 describes.

## 7. Open questions for Holger

- Which coat: the true 1px game line, or the pair (solid ring + 8% rim)?
- Threshold for "much lighter" (rule 3) and whether a white collar beside a face should put the line on the face (rule 3 says yes).
- Whether the silhouette line (rule 1) stays; it is faint under the coat.
- Lottie: the masked inset borders cannot be carried into the emotion animations; only plain centred strokes can (`lottie_strokes()`). Decide before shipping.
