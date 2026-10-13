# Euchre logo exits, for Spine 4.2

This is your 13 Oct export of the Euchre skeleton with one extra animation, `exit_sink-8`: the way Holger wants
the word EUCHRE to leave once the jack has sunk behind it. It starts from the pose your 13 Oct render has at
1.60 s, the first frame with the jack gone, and replaces the shrink that follows it there. A reference render of
the whole move (your run-up and this exit) is beside this file, at normal and at quarter speed.

## Open it

1. In Spine 4.2.43 or later: File > Import Data, choose `euchre-exit-sink-8.json`, into a new project.
2. The images are in `images/` beside it (the JSON's images path points there): your own attachment images
   unpacked from the atlas.
3. Save the project. To bring the animation into your own project, use File > Import Project on that saved
   project and choose the animation; it keys only `logo2` (translate, scale) and the `logo` slot (alpha), which
   your project has.
4. In your active animation, find the frame where the jack is fully behind the word (1.60 s in the 13 Oct render),
   delete your word keys from there on, and paste `exit_sink-8`'s keys at that frame: its frame 0 is the pose
   your word already has there (logo2 translate -0.26, 64.68, scale 0.968), so nothing jumps.
   The word is gone 0.27 s later; the animation can end there.
5. Export as before (JSON, atlas, PNG) and a video render; Holger needs the export for the site.

## What was added

Nothing but the animations: no new bones, slots or images. The skeleton is your export as it was.

## The animations

The animation starts from the pose your 13 Oct render has at 1.60 s (frame 48), the first frame with the jack gone:
`logo2` translate -0.26, 64.68 and scale 0.968 (keys at 0). Paste the keys after your jack move
so they continue from there. The shine `light_1` is keyed invisible.

- `exit_sink-8` (0.27 s): Sink, fading, 8 frames. The same move in eight frames: the top after two frames, a 55 px sink. Gone 0.27 s after the jack. In Spine: On logo2: translate and scale keyed per frame along two cubics that start at the speeds the word has when the jack is gone (centre rising 24 px a frame, scale falling 0.1 a frame) and end 55 px lower at scale 0.1 after 8 frames, scale y 30% under scale x by the end; the logo slot's alpha 1 at frame 0 to 0 at frame 8 on an ease-in.
