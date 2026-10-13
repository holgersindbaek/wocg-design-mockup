# Euchre logo exits, for Spine 4.2

This is your 13 Oct export of the Euchre skeleton with 3 extra animations: your own shrink of the word
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
- `exit_sink` (0.47 s): Sink. The word keeps the rise it already has, slows to a soft top about 40 px up, then sinks away faster and faster while it shrinks and flattens a little, and fades over the last six frames. One curve for the move, one for the size, so there is no turn to feel. In Spine: On logo2: translate and scale keyed per frame along two cubics that start at the speeds the word has when the jack is gone (centre rising 24 px a frame, scale falling 0.1 a frame) and end 115 px lower at scale 0.12, scale y 30% under scale x by the end; the logo slot's alpha 1 to 0 over the last six frames.
- `exit_sink-fade` (0.47 s): Sink, fading from the start. The same sink, but the word starts to fade the moment the jack is gone, on a gentle ease-in: still mostly there at the top of its rise, half gone as it sinks, gone at the end. In Spine: As Sink, with the logo slot's alpha keyed 1 at frame 0 to 0 at frame 14 on an ease-in curve.
- `exit_up` (0.40 s): Up and away. No turn at all: the word goes on shrinking towards its top edge, where the jack went under, its centre rising all the way and slowing as it gets small, and it fades out over the last five frames. In Spine: On logo2: scale 0.968 to 0.1 on one ease-out over twelve frames, translate on the same curve so the word's top edge stays put (the centre rises 190 px); the logo slot's alpha 1 to 0 over the last five frames.
