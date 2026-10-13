# Euchre logo exits, for Spine 4.2

This is your 13 Oct export of the Euchre skeleton with 10 extra animations, one per way the word EUCHRE
can leave after the jack has sunk into it, plus `exit_shrink`, a copy of your own shrink that the lab used to check
that its hand-off from your render is exact. Holger picks one; this file shows how it moves.

## Open it

1. In Spine 4.2.43 or later: File > Import Data, choose `euchre-logo-exits.json`, into a new project.
2. The images are in `images/` beside it (the JSON's images path points there): your own attachment images
   unpacked from the atlas, plus the six letters.
3. Save the project. To bring one animation into your own project, use File > Import Project on that saved
   project and choose the animation; the bones and slots it keys (below) must exist there by the same names.

## What was added

- Bones `letter_E1`, `letter_U`, `letter_C`, `letter_H`, `letter_R`, `letter_E2` under `logo2`, each at its
  letter's centre, with slots of the same names right after `logo` in the draw order and attachments
  `logo_E1` ... `logo_E2`. The letter images are cut from the flattened word along the dark seam between
  letters, so together they draw the word exactly; a letter on its own shows a cut edge where it touched its
  neighbour. For the real thing, cut each letter from the vector source with its full outline.
- Bone `wipe` under `logo2` with a clipping slot `wipe` just before `logo` (end: letter_E2), a rectangle around
  the word that clips the word and the letters; it has no attachment in the setup pose and the wipe exit keys it
  on. For that to work, your closing circle `mask2` now ends at `crown` instead of `logo` (a clip cannot start
  inside another clip's range), so in active_1 the circle no longer clips the word.

## The animations

Every exit starts from the pose your 13 Oct render has at 1.60 s (frame 48), the first frame with the jack gone:
`logo2` translate -0.26, 64.68 and scale 0.968 (keys at 0). Paste an exit's keys after your
jack move so they continue from there. The shine `light_1` is keyed invisible unless the exit uses it.

- `exit_shrink` (0.37 s): Khang's shrink, rebuilt. The lab's copy of the current exit from the hand-off frame on: if this tile looks like the one before it, the hand-off is right. In Spine: What the active animation already does: scale on logo2 towards the vanishing point, alpha on the logo slot.
- `exit_drop` (0.50 s): Drop. The word squashes under the jack's impact, hops a little, tips and falls straight out through the bottom of the tile, tilting as it goes. In Spine: All on logo2: a squash-and-hop in scale and translate over the first five frames, then translate Y falls past the frame bottom with an ease-in (gravity) while rotate tips it about 16 degrees on the way; no other bone or slot.
- `exit_dealt` (0.43 s): Dealt away. The word draws back a touch, then shoots off to the right like a dealt card: leaning into the travel, lifting slightly, gone past the edge of the tile. In Spine: All on logo2: translate X pulls back 80 px over four frames and then eases in hard to 1900 px right, shear Y leans the word into the travel (back a little on the wind-up, forward about 24 degrees in flight), a small translate Y lift, a 5 degree rotate and a slight horizontal stretch; no other bone or slot.
- `exit_flip` (0.43 s): Card flip. The word stretches up for a beat, then flips over about its middle like a card turned face down: it thins to an edge as it lifts, and the edge snaps away. In Spine: Scale and translate on logo2 only: a four-frame anticipation (scale Y 1.12, up 14), an eased-in turn of scale Y to 0.03 over seven frames while scale X grows to 1.08 and the bone rises to 70, then scale X to 0 in two frames.
- `exit_spin` (0.60 s): Spin toss. The word crouches and tilts for a beat, then is tossed up towards where the jack went: it spins two full turns, grows a touch as it leaves the hand, and shrinks to nothing at the vanishing point. In Spine: Rotate, translate and scale on logo2: a four-frame wind-up (rotate -12, down 18, squash to 1.0 x 0.92), then rotate to +708 over 14 frames with a mild ease-out, translate to the pivot with an out-back ease, and scale popping to 1.04 before easing in to 0.
- `exit_letters-drop` (0.77 s): Letters drop. The letters fall out one after another, left to right: each hops up a little, then drops through the bottom of the frame with a tilt. In Spine: Per-letter bones under logo2 (the letters cut from the vector art): on each, translate y up a little and then down past the frame with a rotate on the way, two frames apart per letter; the logo slot swaps to the letter slots at frame 0.
- `exit_letters-pop` (0.73 s): Letters pop. The letters pop one by one like bubbles, from the middle of the word outwards: each pulls in a touch, swells, and snaps to nothing. In Spine: Per-letter bones under logo2 (the letters cut from the vector art): scale each 1 to 0.92, up to 1.3, then to 0 in two frames, with the letter slot's alpha to 0 on the last frame; one letter every three frames from the middle out.
- `exit_letters-tumble` (0.70 s): Letters tumble. A ripple runs through the word from the left: each letter rears back, whips over sideways like a flip-board tile, flashes its mirror image as it topples onto the next letter, and is gone edge-on. Three frames later the next letter follows. In Spine: Per letter (the six letter bones and slots, the logo slot hidden at 0): one six-frame key set offset by three frames per letter, scale X 1 to 1.2 (rear back) to -0.85 (flipped past the edge) to 0 (edge-on, gone) with scale Y easing down to 0.75, rotate +10 then -50 degrees, translate 36 right and 26 down; the letters need redoing from the vector art so each stands alone.
- `exit_wipe` (0.40 s): Wipe. The word recoils a touch, then a slanted edge sweeps across it from the left, faster and faster, like a palm brushing it off the felt. The word slides a little with the brush and leans into it as it is taken. In Spine: The wipe clipping slot keyed on at 0 and its bone translated 1480 px in X with an ease-in (quad) over twelve frames, rotated -6 degrees so the edge slants a little more than the leaning strokes and scaled 1.3 in Y so the slanted rectangle still covers the word at 0; logo2 pulls back 22 px over two frames then slides 70 px right and shears Y to -16 degrees with the same ease-in.
- `exit_zoom` (0.43 s): Zoom past. The word dips back for a beat, then rushes at the viewer: it swells to five times its size in a third of a second and fades out as it overflows the frame, like a card flying past the camera. In Spine: All on logo2 and the logo slot: a scale dip to 0.88 over 3 frames, then scale to 5 with an ease-in over 10 frames and a slight roll, the slot's alpha fading over the last 6 frames.
- `exit_burst` (0.40 s): Light burst. The word swells and glows hot, then flashes white: an additive flare bursts over it and a halo of felt around it, the word is gone under the flash, and the glow dies away. In Spine: logo2 swells to 1.17 and puffs to 1.26; the logo slot tints hot amber on the swell, then its alpha drops to 0 in 2 frames under the flash; logo_mask's clip is keyed off so light_1 can spill; light_1 is moved to the word's centre, turned 81 degrees to lie along the word, scaled from 3 x 2 to 12 x 11 in 2 frames with its alpha to 1, then its alpha fades to 0 over 6 frames while it shrinks to 7 x 8 and warms to amber.
