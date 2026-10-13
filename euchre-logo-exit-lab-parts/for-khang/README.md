# Euchre logo exits, for Spine 4.2

This is your 13 Oct export of the Euchre skeleton with 4 extra animations: your own shrink of the word
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
- `exit_sink-fade` (0.47 s): Sink, fading (14 frames). The pick so far: the word keeps the rise it already has, slows to a soft top about 40 px up, then sinks away faster and faster while it shrinks, flattens a little and fades from the first frame. Gone 0.47 s after the jack. In Spine: On logo2: translate and scale keyed per frame along two cubics that start at the speeds the word has when the jack is gone (centre rising 24 px a frame, scale falling 0.1 a frame) and end 75 px lower at scale 0.12, scale y 30% under scale x by the end; the logo slot's alpha 1 at frame 0 to 0 at frame 14 on an ease-in.
- `exit_sink-fade-quick` (0.33 s): Sink, fading, quick (10 frames). The same move in ten frames: the rise runs out after two and a half frames, the sink is shorter (65 px) and the shrink keeps its arriving pace all the way, with the fade biting earlier. Gone 0.33 s after the jack. In Spine: As the fourteen-frame sink with the cubics over ten frames, ending 65 px lower at scale 0.1; the logo slot's alpha 1 to 0 over the ten frames on an ease-in.
- `exit_sink-fade-snap` (0.23 s): Sink, fading, snap (7 frames). The same move in seven frames: the rise runs out after a frame and a half, the word sinks 50 px while the shrink speeds up past its arriving pace, and the fade is quick. Gone 0.23 s after the jack. In Spine: As the fourteen-frame sink with the cubics over seven frames, ending 50 px lower at scale 0.1; the logo slot's alpha 1 to 0 over the seven frames on a light ease-in.
- `exit_sink-fade-blink` (0.17 s): Sink, fading, blink (5 frames). The same move in five frames: the rise runs out inside the first frame, the word collapses and sinks 35 px while the fade takes most of it. Gone 0.17 s after the jack. In Spine: As the fourteen-frame sink with the cubics over five frames, ending 35 px lower at scale 0.08; the logo slot's alpha 1 to 0 over the five frames, nearly linear.
