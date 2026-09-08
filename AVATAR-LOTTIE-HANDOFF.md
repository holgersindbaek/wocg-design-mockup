# The avatar border in the emotion animations: what was built

Written 2026-09-08. This file was the brief for the job; it is now the record of it. Read
`AVATAR-BORDERS-HANDOVER.md` first for the border rules themselves, and section 13 of
`AVATAR-STUDY.md` for how they were arrived at.

## 1. The state

Done. All 473 emotion Lottie files carry the same faint border the v9 stills carry, and the lab has
the test Holger asked for.

- The pass: `zz-tmp-build-avatar-lottie.py`. One file, self contained, about a minute for the set.
- Its output: `game-assets/avatars-lottie-v9/*.json`, 473 files. **These are what goes into the app**,
  over `worldofcardgames/static/pieces/avatar/classic/*.json`. Nothing was written into the app.
- Its audit: `game-assets/avatars-lottie-v9/borders.json`, one entry per shape per file, saying what
  the pass decided and why. Useful when a shape looks wrong.
- The lab copies: `game-assets/avatars-lottie-v9/js/*.js`, the same files wrapped so a `file://` page
  can load them with a script tag. Only the lab uses these.
- The test: `avatar-borders-lab.html`. Hover an avatar and its three animations load. Click it and
  one plays in place of the still. Click again and it steps on, win to think to lose to win. The
  hover scale is off the avatars.

Holger's words for the test, which is what was built:

> The way we test it is that when I hover over an avatar in the design, then you load the lotties.
> When I click an avatar then you play one of the lottie files and cycle through it. Remove the
> hover effect on the avatar for now.

## 2. The mechanism, as it ended up

The proof (`zz-tmp-lottie-borders.py`) duplicated a whole layer twice, a track matte plus a stroked
copy. The pass does something smaller. Per bordered shape it adds **one** layer: the layer cloned,
pruned to that shape alone, its fill removed, a stroke put where the fill was, and one additive
layer mask carrying the shape's own path. The mask keeps the inner half of the stroke, which is the
inset line. The stroke and the mask are the same path, so an animated path morphs the border with
it. Nothing is baked.

Three things had to be got right, and each one was measured, not assumed.

**The width is 4, not 8.** The v9 SVGs stroke `.abl` at 4 units and mask away the outer half, so the
line the eye sees is **2 units** in the 160-unit box. The proof's `w: 8` draws a 4-unit line, twice
the still's. A comp here is 1600 over 160 units, so the stroke has to render 40 comp units wide, and
a stroke's width is measured in the space of the item list it sits in. So `w = 40 / S`, with `S` the
scale from that space to the comp. `S` is 10 for four fifths of the groups but runs from 1 to 12, so
a fixed 4 is ten times wrong on the 30 files whose paths are drawn at 1600 units. And `S` is not one
number per shape either: a layer that scales carries its stroke with it, so where the chain moves by
more than 10% the width is written as a curve (section 4). Measured on the renders: the drawn band
is 2.1 to 2.5 units, against 2.02 to 2.10 for the v9 SVGs.

**A layer mask, not the proof's matte pair.** One layer instead of two, and it is the only mechanism
that works on a shape whose layer is already matted, because a layer that carries `td` ignores its
own `tt` in this player. The mask path is the shape's path put through the group transforms, which
is an exact change of frame rather than a bake: **no group transform in the 473 files is animated**
(0 of 19,536), and an animated path keeps every keyframe. Never more than one additive mask on a
layer: lottie renders several as children of one `clipPath` and Chrome does not reliably union them.
The matte pair is still in the pass as the fallback for a shape whose outline cannot be written as a
single mask. It never fired on this set.

**A layer often has to be cut open.** 1,825 of the 8,095 shape layers hold more than one drawable
piece, and one of them draws the whole avatar. A line layer sits above the layer it belongs to, so
it paints over the pieces of that layer that were covering the shape: the face's outline ran straight
through the hair. The pass cuts the layer at the points where a line goes in, one cut per line rather
than one per piece, and the first piece keeps the layer's `ind` so anything parented to it still
resolves.

## 3. Which shapes get a line

Every Lottie shape is matched to the SVG part the border generator decided about, **on geometry**:
the shape's path through its transform chain, divided by 10, against the SVG element's bounding box
and area, at the best of 13 sampled frames, one to one by Hungarian assignment, with the paint as a
loose gate. That reaches 78% of shapes and is right on 99.5% of them, measured by rendering 735 pairs
and comparing the masks. Fill hex, which the brief proposed, would decide only 13%: 76% of shapes
share their fill with another shape in the same file. A shape with no part falls back to a gate read
off the shape itself.

Four rules on top of the generator's own decision, each one measured:

1. **A repeated shape shares the answer of the copy the generator could see.** Several of these
   drawings hold the same shape twice, a visible copy and one a later shape covers, and only the
   visible one is bordered. The match is geometric, so it lands on whichever copy it likes: on
   `OtherVolcano_win` that left 76 of 87 shapes reading their answer off a hidden twin, 38 bordered
   parts in the still against 5 lines in the animation. Parts with the same fill and the same
   bounding box now share the answer of whichever of them the generator saw the most of.
2. **The shape must own its line, and own it on the inside.** v9 cuts the line where the neighbour
   owns the edge or the two are one material, and it draws part of its line as a band OUTSIDE the
   shape, onto the darker piece below. Neither can be carried into an animation without baking the
   cut geometry. So a shape is stroked whole, and only when the line v9 draws **inside** it is at
   least as long as the line v9 deliberately leaves off it. A band is not a reason to stroke: drawn
   inside, it lands on the lighter side of the seam, which is exactly what the still's rule avoids.
   That is what put a crisp grey rim on six white robot teeth. Measured over the 9,877 bordered
   parts: this holds the line the still does not draw down to 8% of the true line and the band drawn
   on the wrong side to 7%, against 10% and 18% for a rule that counts the band.
3. **The mouth is exempt from rule 2, and is stroked at 35%.** Two thirds of the mouth lines in the
   still are bands onto the face, so rule 2 would take the smile off every avatar that has one, and
   the smile is the one place the border is meant to be seen. The flag is read from the built v9
   SVG; svgo rewrites the `.abm` class into an inline `stroke-opacity:.35` when it matches a single
   element, so both spellings are read. 158 mouth lines.
4. **A shape with no part is only stroked when it is big.** Counted over all 13,365 parts the
   generator judged, a part 30 units or more across owns an inside line 53 to 64% of the time
   whatever its colour, and a smaller one only 18 to 47%. The small ones are the shapes whose line
   the still draws onto the piece below, where it does not show. The generator's own floor of 10
   units is right for a part it can cut the line on and wrong for a whole-shape stroke placed on a
   guess.

And the line is thinned where it would swallow the shape. A 2-unit inset from both sides of a
5-unit scarf stripe leaves a solid bar, which the still avoids by cutting; the width is scaled down
so the inset keeps under 35% of the shape's width. 783 shapes.

Skipped, and why: a matte source (it is never drawn, and its visible twin gets the line), a layer
carrying a shape modifier (`tm`, `rd`, `pb`, `rp`, `zz`, whose drawn geometry is not the raw path),
a shape whose scale is 0 at every frame, and the merge-paths family, 64 shapes whose fill paints
geometry in nested groups. Lottie has no merge-paths modifier at all, so those groups already render
as a plain union and a stroke there draws sub-path edges the drawing does not have.

## 4. The two traps found while building it

**A layer that fades cannot be cut.** Lottie flattens a layer's shapes and then applies the layer
opacity, so two pieces at 50% show through each other where the one layer did not. 340 of the 8,095
shape layers fade. Cutting one moved the whole face out from behind the hair on `ManBoy_lose` at
frame 40. Those layers are now left whole, and so are the 9 groups with a translucent group
transform.

**A stroke width fixed in the layer's space does not follow an animated scale.** The layer carries
its stroke with it, so a shape whose parent chain scales from 2.35 to 8.96, as `ManChef_win`'s arm
does, draws its border nearly three times too wide at one end. 513 shapes sit on a chain that moves
more than 10%, and the width is written as a curve for those: sampled at every frame where anything
above them changes scale, plus midpoints, so the line is 2 units at every frame.

**Cutting a layer moves Chrome's antialiasing.** With the added layers hidden, a bordered file
renders pixel for pixel like the original on the files that were not cut, and within about 1% of it
on the files that were, all of it a one pixel fringe on edges. The share halves as the render doubles
in size (8.4% at 256px, 4.5% at 512, 2.1% at 1024, 1.2% at 2048), which is the signature of an edge
effect rather than a structural one. At the sizes an avatar is drawn, 96px and 68px, it is invisible.

## 5. The numbers

| | plain | bordered |
|---|---|---|
| raw | 23.5 MB | 39.9 MB (x1.70) |
| gzipped, which is what goes over the wire | 2.71 MB | 3.61 MB (+33%) |
| gzipped per file | 5.9 KB | 7.8 KB |
| layers | 10,014 | 18,599 (x1.86) |

5,051 shapes carry a line, over all 473 files. Every file got at least one. 158 of them are mouths,
at 35%. The brief guessed 2.7 to 3.0 MB on the wire; it is 3.61, because the proof it was measured
on bordered 5 shapes in one file and the real pass borders 11 per file.

The lab copies are 31.6 MB. They are the same drawings with the author-time keys After Effects
writes on shape items dropped (`ix`, `mn`, `nm`, `bm`, and `hd` where it is false), which is 16% off
and, checked by render, 0 differing pixels. Rounding the numbers would take another 5% and was not
done: it moves every edge by a fraction of a pixel and a rounded colour channel moves a whole face
by a level or two.

## 6. The lab test

`avatar-borders-lab.html`, one block at the end of the script plus four small edits above it.

- **The hover scale is off the avatars.** The rule is now `.sm .pk:not(.avs) .pi:not(.on):hover`, so
  the decks and the wallpapers still lift and the avatars do not.
- **Hover** loads the avatar's three animations, win first, once each. **Click** plays one in place of
  the still and the next click steps on. The animation ends by putting the still back, which is what
  the table does (`Table.js`, `onBeforePlay` hides the avatar, `onComplete` shows it).
- The player is injected on the first hover, from `avatar-lab/lottie_light.min.js`, and each animation
  by a script tag pointing at `game-assets/avatars-lottie-v9/js/<Name>_<emotion>.js`, which assigns
  `window.AB_LOTTIE[...]`. Script tags are not subject to CORS, so this works from `file://`, where
  `fetch` is refused.
- The renderer settings are the app's: `renderer: "svg"`, `preserveAspectRatio: "xMidYMax meet"`.
- **The border knob follows.** "plain" strips the `ab-line` layers back out of the same file, so the
  still and the animation always agree. There is no v8 animation set, so the v8 option plays the v9
  border.
- The coat and the picked green ring were written for `img` only, so an animated tile lost both. The
  twelve selectors now say `.pi :is(img,svg)`.
- The still is hidden with `visibility: hidden`, never `display: none`: the tile has no height of its
  own, it takes 67px from the image.
- `show()` empties the modal on every knob change, every tab click, `document.fonts.ready` and every
  resize, so it is wrapped to destroy anything playing first.

Driven headlessly from `file://` and checked: 141 tiles, no hover transform, the animation mounts at
1600x1600 in the tile, the still hides, the coat and the ring reach the `<svg>`, the three clicks
give three different animations, `plain` gives 0 border layers, and `WomanWoman21`, the one avatar
with no `_think`, skips it and plays `_lose`.

## 7. What was checked, and what is still open

The output was audited against the stills: 8,987 renders through the site's own player, a numeric
screen over all 473 files, then 60 avatars looked at by eye across every pack. Nothing is broken.
No shape vanished, no colour changed, nothing moved, no line is drawn outside a shape or floating in
empty space, and the line follows the movement with no drift on every file stepped through frame by
frame. Six defect classes came out of that audit; four of them are the rules in section 3 and the
width curve in section 4, which is why they are there. What is left:

- **The outer band.** v9 draws a fifth of its line as a band onto the piece below, and the pass does
  not draw it at all (except on a mouth). About 20% of the still's line is therefore missing, most
  visibly on the piece the still lines from the outside. Carrying it properly needs a second clip
  per shape, an inverted track matte to a copy of the neighbour, which is buildable (the player
  supports `tt: 2`) but needs the neighbour resolved from the SVG part index back to a Lottie shape.
- **A line where the still cuts it short.** The pass strokes a whole outline where the still stops at
  the edge the shape owns, so a shape can carry a line across a stretch the still leaves bare. It is
  held to 8% of the true line by the ownership rule, and it is the commonest remaining difference.
  `AlienLollipop_lose` is the loudest case, a dark bar down the middle of the body.
- **The 64 merge-paths shapes** get no line. Some are real pieces, a shirt for instance. Doing them
  needs the border nested inside the group that holds the fill, and a way to tell which sub-path is
  the visible outline.
- **A shape with no counterpart in the still is decided by a size rule**, which is right 53 to 64% of
  the time. The honest fix is to work out its neighbours from the Lottie itself, the way the SVG
  generator does from a render: one flat-colour render per file would give the label map and the
  ownership could then be decided the same way for matched and unmatched shapes alike.
- **Two files were regraded**: `OtherJackOLantern3` and `OtherJackOLantern4` are a different green in
  the animation than in the still. Not a border problem, but the two assets have diverged.
- Whether Holger wants the animations at all, given the border is still a proposal. Nothing has been
  put in the app.

## 8. How to run it again, and how to check it

```
python3 zz-tmp-build-avatar-lottie.py --out=avatars-lottie-v9 --js --jobs=8
```

Add names to do one avatar (`ManBusinessman`) or one file (`ManBusinessman_win`). `--js` also writes
the lab copies. It validates every file it writes: unique inds, no layer with both `tt` and `td`,
every `tt` with a `tp` that resolves to a matte source, every parent resolving, one additive mask per
layer.

The verification harness is not in this repo, it is under `/tmp/ablottie/`:
`render.py` (one frame through the site's own player), `compare.py` (two animations side by side with
a difference map), `sweep.py` (a whole folder in parallel, `--vs` to diff two folders),
`zoomvs.py` (the plain still, the v9 still, what v9 adds, the plain frame, the bordered frame and
what the pass adds, in one sheet: the most useful one), `labtest.py` (drives the lab headlessly from
`file://`). Rebuild them from `/tmp/ablottie/harness.md` if the folder is gone.

Frames worth looking at, the poses closest to the still: `_win` 44, `_lose` 40, `_think` 168.

## 9. Git rules for this repo

Commit with an explicit pathspec, never `git commit -a`, and push after every commit. Other sessions
own `index.html`, `about-lab.html`, `open-tables-slide-lab.html`, `game-settings.html` and the
untracked `game-*.html` / `GAME-*-STUDY.md` files: never commit, revert or clean them.

Mine: `avatar-borders-lab.html`, `AVATAR-STUDY.md`, `AVATAR-BORDERS-HANDOVER.md`, this file,
`zz-tmp-build-avatar-*.py`, `zz-tmp-lottie-borders.py`, `zz-avatar-svgo.config.mjs`,
`game-assets/avatars-bordered*/`, `game-assets/avatars-lottie-v9/`.
