# Euchre logo exits, for Spine 4.2

This is your 13 Oct export of the Euchre skeleton with 2 extra animations: your own shrink of the word
EUCHRE after the jack has sunk into it, varied. `exit_shrink` is your shrink as it is in the 13 Oct render, rebuilt
from measurements of the video (the lab used it to check that its hand-off from your render is exact); the others
are the variations. Holger picks one; this file shows how it moves.

## Open it

1. In Spine 4.2.43 or later: File > Import Data, choose `euchre-logo-exits.json`, into a new project.
2. The images are in `images/` beside it (the JSON's images path points there): your own attachment images
   unpacked from the atlas, plus the six letters.
3. Save the project. To bring one animation into your own project, use File > Import Project on that saved
   project and choose the animation; the bones and slots it keys (below) must exist there by the same names.

## What was added

Nothing but the animations: no new bones, slots or images. The skeleton is your export as it was.

## The animations

Every exit starts from the pose your 13 Oct render has at 1.60 s (frame 48), the first frame with the jack gone:
`logo2` translate -0.26, 64.68 and scale 0.968 (keys at 0). Paste an exit's keys after your
jack move so they continue from there. The shine `light_1` is keyed invisible unless the exit uses it.

- `exit_shrink` (0.37 s): Khang's shrink, rebuilt. The current exit from the hand-off frame on, as measured from his render: the word rises for two frames, then sinks and eases out while it fades. If this tile looks like the one before it, the hand-off is right. In Spine: What the active animation already does: scale and translate on logo2, alpha on the logo slot over the last four frames.
- `exit_smooth` (0.37 s): Smooth. The same shrink on one straight line: the word sinks to where Khang's vanishes, easing out as it goes, and fades over the last four frames. No change of direction on the way. In Spine: On logo2, two keys each for scale (0.968 to 0.19) and translate, both on the same curve, 11 frames; the logo slot's alpha 1 to 0 over the last four frames.
- `exit_smooth-fade` (0.37 s): Smooth, fading from the start. The same straight-line shrink, but the word starts to fade the moment it starts to shrink: half there at half size, gone where Khang's vanishes. In Spine: As Smooth, with the logo slot's alpha keyed 1 at frame 0 to 0 at frame 11 on a gentle ease-in, so the fade runs through the whole shrink.
