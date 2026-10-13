# Note to Khang (draft, 13 Oct 2026)

Send with `euchre-exit-sink-8-for-khang.zip` (the folder `for-khang/` zipped: the Spine JSON, the images, a README,
and two reference renders).

---

Hi Khang,

The new jack move is great. I like how he sinks down behind the word. The way the word leaves after that is not
quite right yet: it goes up for a moment, then turns and shrinks away, and that turn feels like a small jolt.

I have attached the exit I want instead. It keeps the motion the word already has when the jack goes under and
lets it run out: the word slows to a soft top, then sinks a little while it shrinks, flattens a touch, and fades
from the first frame. It is gone 8 frames after the jack is fully behind it. Have a look at reference-sink-8.mp4,
and the quarter-speed one to see the curve.

In the zip:

- euchre-exit-sink-8.json is your 13 Oct export with one extra animation, exit_sink-8. File > Import Data in
  Spine 4.2 opens it as a new project; the images are beside it. Then Import Project brings the animation into
  your own file. It only keys logo2 (translate and scale) and the logo slot (alpha).
- In your active animation, go to the frame where the jack is fully behind the word (1.60 s in your 13 Oct
  render), delete the word's keys from there on, and paste exit_sink-8's keys at that frame. Its first frame is
  the pose the word already has there, so nothing jumps. The word is gone 8 frames later, and the animation can
  end there.
- The README in the zip has the numbers.

When it is in, please send the export as before (JSON, atlas, PNG) and a video render. I need the export for the
site. And please use the same exit for the Hearts word and for the games that follow, so they all leave the same
way.

Thanks!
Holger
