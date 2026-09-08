# Carry the avatar border into the emotion animations: handoff

Written 2026-09-08 for a fresh session. Everything you need is here; you should not need the chat
history. Read `AVATAR-BORDERS-HANDOVER.md` first for the border rules themselves, and section 13 of
`AVATAR-STUDY.md` for how they were arrived at.

## 1. The job

The avatars now carry a faint border drawn into the SVG (v9). The emotion animations do not, so when
a player wins, thinks or loses, the avatar swaps from the bordered still to an unbordered animation
and the border pops off. Close that gap: write the pass that puts the same border into the 473
Lottie files, and give Holger a way to watch it.

Holger's words for the test, verbatim:

> The way we test it is that when I hover over an avatar in the design, then you load the lotties.
> When I click an avatar then you play one of the lottie files and cycle through it. Remove the
> hover effect on the avatar for now.

## 2. It is already proved possible; here is the mechanism

Do not re-derive this. `zz-tmp-lottie-borders.py` in this repo is a working proof, rendered through
the site's own `lottie_light.min.js`.

Every emotion file is **one shape per layer**, the paths in the **same 160-unit space as the SVG**
under a 10x layer scale, and the files **already use track mattes** (`tt` / `td`), which the shipped
`lottie_light.min.js` supports. So, for a shape S:

1. Copy S's layer twice and put both copies directly above S in the `layers` array (index order is
   top first, so a lower index draws on top).
2. The first copy is the matte: `td = 1`, keep the fill, name it `ab-matte`.
3. The second copy is the line: `tt = 1` (alpha matte), **remove the fill**, insert a stroke item
   before the group's `tr`:
   `{"ty":"st","c":{"a":0,"k":[0,0,0,1]},"o":{"a":0,"k":15},"w":{"a":0,"k":8},"lc":2,"lj":2}`
   (width 8 = twice the 4-unit border, so the half outside the shape is what the matte removes).
4. Both copies stroke and matte **the same path object**, so when the path is animated the border
   morphs with it. Nothing is baked and nothing drifts. Proved on `ManBusinessman_win.json`, where
   the mouth morphs through the win and the border follows it.

Cost measured on that file: raw 40.5 -> 88.0 KB, but **gzipped only 5.5 -> 6.1 KB**, because the
duplicated geometry compresses away. Over the 473 files that is roughly 2.7 -> 3.0 MB on the wire.

## 3. Where everything is

| thing | path |
|---|---|
| the proof and its notes | `zz-tmp-lottie-borders.py` (this repo) |
| the SVG border generator | `zz-tmp-build-avatar-borders.py` (`--base`, `--min`, `--out=DIR`) |
| its per-shape decisions | `game-assets/avatars-bordered-v9/decisions.json` |
| the bordered SVGs (v9, svgo'd) | `game-assets/avatars-bordered-v9/` (664 files) |
| v8, kept as a comparison | `game-assets/avatars-bordered/` |
| the plain source SVGs | `game-assets/avatars/` (665) |
| **the Lottie files (not in this repo)** | `<wocg>/worldofcardgames/static/pieces/avatar/classic/*.json` (473) |
| the player the site ships | `<wocg>/worldofcardgames/static/js/lottie_light.min.js`, and a copy already sits at `avatar-lab/lottie_light.min.js` |
| the lab to test in | `avatar-borders-lab.html` |
| the border rules in words | `AVATAR-BORDERS-HANDOVER.md` section 5 |

`<wocg>` = `/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg`.

Repo: `https://github.com/holgersindbaek/wocg-design-mockup.git`, branch `main`. Recent commits:
`eed5a1b` (v8), `281a076` (v9), `bef727b` (svgo + the Lottie proof).

## 4. What to build

### A. The pass

Write it as `zz-tmp-build-avatar-lottie.py` (grow the proof, or start from it). Read the JSONs from
the app folder, write bordered copies into `game-assets/avatars-lottie-v9/` in **this** repo. Do not
write into the app; Holger swaps the app files himself later.

Decisions the proof left open, in the order they matter:

1. **Shapes already inside a matte pair are skipped** by the proof (3 of 14 in the test file). They
   need the border nested inside the pair they belong to, not wrapped around it. This is the main
   piece of real work.
2. **Which shapes get a border, and on which side.** The SVG rule decides per edge and cuts the line
   where the neighbour owns it. In Lottie a cut would be another matte and its geometry *would* be
   baked, so do not try to carry the cuts. Give the line to the shape that owns most of that edge,
   whole. Match a Lottie shape to its SVG part **by fill hex** (the palettes are identical; that is
   how the earlier round matched them) and read the owner and the opacity out of `decisions.json`.
   Where a fill appears on several parts, fall back to bordering the shape inside itself.
3. **The mouth is stroked heavier**, 35% instead of 15%, same as the SVG. `decisions.json` does not
   flag it, but the v9 SVGs do: the mouth uses `class="abl abm"`. Read the flag from the SVG.
4. Skip what the SVG skips: ink, translucent shapes, line art, anything under 10 units.

### B. The test in the lab

In `avatar-borders-lab.html`, on the avatar picker (`.sm .pk.avs .pi`, rendered around line 1718,
already click-wired at line 1918):

- **Remove the hover effect.** It is one rule, line 335:
  `.sm .pk .pi:not(.on):hover { transform: scale(1.04); }`. Delete it or neutralise it.
- **On hover**: load that avatar's three emotion files (`<Name>_win`, `_think`, `_lose`). Load once
  and cache; do not reload on every mouseover.
- **On click**: play one of them in place of the still, and cycle on each further click
  (win -> think -> lose -> win). Read Holger's "cycle through it" that way; if he meant play all
  three back to back, it is a two-line change, so ask him once it runs.
- Fall back to the still image when an avatar has no animation (32 of the 190 base avatars have
  none; `WomanWoman21` has only two of the three).
- Keep the existing "Border inside the drawing" knob meaningful: the still and the animation should
  both follow it, so the animation folder needs a plain option too (just use the untouched app JSON).

## 5. The traps

1. **`fetch`/XHR does not work from `file://`.** Holger opens these labs by double-clicking, as
   `file:///Users/.../avatar-borders-lab.html`, and Chrome gives a `file://` page the origin `null`,
   so fetching a neighbouring `.json` fails silently. The proof got round it by inlining the JSON
   into the page, which will not scale to 473 files. **Ship each animation as a `.js` file that
   assigns a global** (`window.AB_LOTTIE["ManBusinessman_win"] = {...}`) and load it with an injected
   `<script>` tag: script tags are not subject to CORS, so this works from `file://` and keeps the
   hover-to-load behaviour. Serving the folder over `python3 -m http.server` also works but changes
   how Holger opens the lab; do not assume he will.
2. **Layer order.** The `layers` array is top first. The matte source must sit directly above the
   layer it mattes. Put the pair at the shape's own index so the border draws over its own shape and
   under whatever is above it.
3. **`ind` must stay unique**, and copies keep their `parent`, so they follow the same null layers
   that drive the animation. The proof handles both.
4. **Do not touch a layer that already has `tt` or `td`** until you have solved trap 1 in section 4A;
   wrapping a matte pair the naive way breaks the pair.
5. **The 30 placeholder avatars** are a raster PNG in an SVG wrapper (one dog repeated under 30
   names). They have no shapes, no border and no animation. Leave them.
6. **Verify in the site's own player**, `lottie_light.min.js`, not a newer lottie-web. It is a light
   build; masks and mattes are in it, expressions are not.

## 6. How to know it is right

- Render the same frame from the plain and the bordered JSON side by side through `lottie_light`,
  as the proof does, at frames 0 / 40 / 75 at least. The border must be inside every shape, must not
  cross a shape's own shading, and must not thicken where two shapes meet.
- Step the mouth frames on a `_win` file and check the border tracks the morph.
- Put the bordered still (`avatars-bordered-v9/<Name>.svg`) beside frame 0 of the bordered animation.
  They should read as the same drawing. Any edge that has a line in one and not the other is a bug in
  the matching in 4A.2.
- Measure gzipped size, not raw. Raw roughly doubles and that is fine.

## 7. Git rules for this repo

Commit with an explicit pathspec, never `git commit -a`, and push after every commit. Other sessions
own `index.html`, `about-lab.html`, `open-tables-slide-lab.html`, `game-settings.html` and the
untracked `game-*.html` / `GAME-*-STUDY.md` files: never commit, revert or clean them.
`game-settings.html` currently has two uncommitted default changes of mine (it opens on the Design
tab, on v9); leave them uncommitted.

Yours to commit: `avatar-borders-lab.html`, `AVATAR-STUDY.md`, `AVATAR-BORDERS-HANDOVER.md`, this
file, `zz-tmp-build-avatar-*.py`, `zz-tmp-lottie-borders.py`, `zz-avatar-svgo.config.mjs`,
`game-assets/avatars-bordered*/`, and the new `game-assets/avatars-lottie-v9/`.
