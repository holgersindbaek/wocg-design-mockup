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

## 4. The generator as of v6 (commit 21c33a3)

- Measures every filled shape by rendering each alone in a grid (one headless screenshot), records fill, area and bounding box.
- Parts = shapes over 10 units (or over 6 units and near white, for teeth). Skipped: tiny, ink (L under .03), and "shade" (a shape wholly inside a bigger same-material shape's box).
- Same material = CIELAB test (under 32 L apart, same hue within 16 degrees, chroma within half, greys by lightness) plus boxes overlapping 30%.
- Output per part: the shape gets an id and its fill moves to a wrapper `<g fill>`; an inner line = `<use>` of the shape stroked 4 units, masked to the shape, with black dilated `<use>`s of its family and darker neighbours as stops; an outer band = 2-unit stroke masked to a darker neighbour under it, placed right after that neighbour.
- Numbers: 2,178 inner, raw +133%, gzipped +22% (4.1 to 5.0 KB per file).

### Why v6 still fails (diagnosis for v7)

Everything in v6 is decided from bounding boxes and draw order, never from what is actually visible:
- Blonde hair (L about 86) beside light skin (L 84) is under the 6 L "darker" threshold in both directions, and the hair is often drawn under the face, so neither side gets a line.
- The stops are the neighbour's whole geometry dilated, hidden parts included, so a lock of hair that runs under another lock cuts the visible lock's line: "only some of the hair gets a border".
- "Shade" is a box test, so a lock inside the big hair's box is skipped even where it lies over the face.

## 5. The plan for v7 (in progress in this session)

Decide from a label map, not boxes: render the avatar once with every shape in a unique flat id colour (`shape-rendering="crispEdges"`, no anti-aliasing, 4 px per unit), and once for real to sample each shape's effective colour. Then every visible edge between two shapes is known pixel by pixel, with the top shape (the one whose outline forms the edge) and the shape under it.

Rules per visible edge between a and b:
1. Background on one side: the piece keeps its inner line (the silhouette line; the coat sits outside it).
2. Same material (the CIELAB test): no line.
3. Lightness apart by more than a threshold (about 18 L): the line goes on the darker side.
4. Otherwise the line goes on the more saturated side (blonde beside skin, yellow shirt beside skin); if neither is clearly more saturated, on the piece on top.
5. Encoding: the line always follows the top piece's outline. Owner = top piece: its inner line, masked to the piece, with black cut polylines in the mask where the owner is someone else. Owner = the piece under: an outer band, the top piece's stroke outside the piece, masked to white polylines along those segments. Polylines come from the traced contour of the visible region, simplified; in the piece's own user space (undo ancestor transforms, which exist in the emotion files).
6. Both lines 2 units, black 15%. Placed right after the piece so later shapes cover them.

Verification: contact sheets of every base avatar (plain beside bordered) at 112 px on the felt, and a judge pass against the rules above.

## 6. The outline (coat) work pending

- `game1` (`#avatarLine1` in the settings lab): blur 0.55 + threshold reaches only about 0.75 px outside the silhouette. Fix: stdDeviation 1.0 and a threshold at the alpha of 1.0 px (about 0.16), verified by measuring the ring on a rendered disc at DPR 1 and 2.
- `front`: replace the four 32% drop-shadows with a solid 1px ring (same recipe, inked `#252525`) and keep the 8% white inner rim.
- Both live only in `game-settings-lab-3.html` (uncommitted, other session's file). If Holger picks one, the shipping version goes into `_variables.scss` / `body_open.dust` in the app repo as `AVATAR-STUDY.md` section 11 describes.

## 7. Open questions for Holger

- Which coat: the true 1px game line, or the pair (solid ring + 8% rim)?
- Threshold for "much lighter" (rule 3) and whether a white collar beside a face should put the line on the face (rule 3 says yes).
- Whether the silhouette line (rule 1) stays; it is faint under the coat.
- Lottie: the masked inset borders cannot be carried into the emotion animations; only plain centred strokes can (`lottie_strokes()`). Decide before shipping.
