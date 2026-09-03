# Signed-in hero greeting: the spec

Decided 2 September 2026. Reference implementation: `welcome-lab.html`, section "Final" (the shared code block starts at
`/* ===== the decided signed-in copy system`), and the `final` signed-in copy variant in `index.html`. This document is the
source of truth for the site build; when the site code is written, copy this file into the wocg repo next to
`FRONTPAGE-REDESIGN.md`.

The guest hero ("Play card games" plus the weekday-and-hour tail) is a separate system and is not covered here.

## 1. What the column shows

```
Evening PiLady10            <- line one: hour word + name (see 3 for the fallback ladder)
the cards are waiting       <- line two: one of eight card-room lines, drawn per visit (see 4)

Good to see you again! Sneak in a hand before anyone notices. We won't say a word.
                            <- subtitle: an opener (see 5) and a clause (see 6), one paragraph that wraps on its own

[ LIVE · 1,214 playing · 143 tables ]    <- the live capsule, unchanged
```

Type: headline in the display serif (Gelica Medium 38px in the mockup, line-height 1.15), two lines, no full stops and no
commas anywhere in the headline. Subtitle 16px body face, ONE paragraph with no forced line break. Its max-width is the
headline budget from section 3 (the widest of the eight second lines, about 372px in the mockup's font), not the guest
subtitle's 416px: the guest subtitle is bold-heavy and breaks early on its own, and the regular-weight member subtitle
needs the narrower box to break in the same place. Opener plus clause run 80 to 95 characters so the paragraph fills about
two lines. Nothing in the column is ever wider than the widest headline line. Capsule 28px below.

Nothing in the hero mentions friends, leaderboards, rank, Elo, the daily challenge or deal, stats, streaks, last night, or
seats open. Those live in the zones below the hero.

## 2. The hour word

Local time of the visitor's device.

| Hours (local) | Word |
| --- | --- |
| 05:00 to 11:59 | Morning |
| 12:00 to 16:59 | Afternoon |
| 17:00 to 04:59 | Evening |

Evening is also the late-night word; "Good night" sounds like goodbye. Note: lobby-build's `greetingWord()` currently
switches to evening at 18:00; align it to 17:00 (or change this table), but use one boundary everywhere.

## 3. Line one: the name ladder

Line one must never be wider than the widest possible line two. Measure in pixels, in the headline's own computed font
(`font-weight font-size font-family` of the H1/H2 element), with `canvas.measureText` or an offscreen span. Never count
characters: "WMWM" is twice the width of "illi".

```
budget  = max( width(line) for line in POOL )          // about 370px in Gelica Medium 38px
if width(hour + " " + name) <= budget  -> "Afternoon PiLady10"     (hour word + name)
else if width("Hi " + name) <= budget  -> "Hi cardShark52"         ("Hi" + name)
else                                    -> "Good afternoon"        (hour word alone; the name stays in the top bar)
```

Guide values at 38px: the hour word holds names of about 9 characters after "Afternoon" and about 11 after "Morning" or
"Evening"; "Hi" holds about 15. Usernames are 3 to 20 characters (`C.MAX_USERNAME_LENGTH = 20`; letters, digits, spaces,
underscores, hyphens; at least two thirds letters), so the third rung is needed for the long tail.

Rules:
- Use the username exactly as the top bar shows it. No case changes, no trimming, no ellipsis.
- Line one is `white-space: nowrap`; names may contain spaces.
- Measure after the web font has loaded (`document.fonts.ready`), or measure with the fallback font and re-run once the
  font arrives. The lab does the second; do not let the page flash between rungs more than once.
- When the third rung is used, the subtitle opener carries the name instead (see 5).

## 4. Line two: the pool

Eight lines, drawn once per page load, never re-drawn on a re-render or a poll within the visit:

```
the table is set
the cards are waiting
your seat is saved
the deck is shuffled
the table is yours
the cards are dealt
your chair is warm
the game is on
```

Remember the last line shown (localStorage `wocg-pool-last` in the mockup) and skip it, so two visits in a row never
repeat. The pool does not depend on the hour or the weekday.

## 5. Subtitle line one: the opener

Everyday openers, drawn per visit, skipping the last one shown:

```
Good to see you again
Good to see you
Lovely to have you back
Glad you came by
There you are
Nice to see you again
Look who's here
Always good to see you
```

Return openers (see 7):

```
Good to see you again, stranger
Well, look who's back
Good to have you back
```

- The "again" and "back" openers are only for someone the site has seen before (has a previous visit or a finished
  game). A brand-new account draws from "Good to see you", "Glad you came by", "There you are", "Look who's here".
- Punctuation after the opener follows the clause: an exclamation mark before an any-hour clause, a full stop before an
  hour clause or a return clause. Never an em dash.
- The name joins the opener only when line one had to drop it (rung three): `Nice to see you again, spades_grandma_62!`.
  Otherwise the opener has no name; the headline already said it.

## 6. Subtitle line two: the clause

Five groups. The lab keeps these lists in `COZY`.

Each clause is two short sentences, so the subtitle reaches about two lines at 416px.

Any hour:
```
Pull up a chair and stay a while. The cards are patient, and so are we.
Shoes off, cards up, no rush. Nobody here is watching the clock.
One quick hand, you say. That's what everyone says, and nobody minds.
Sneak in a hand before anyone notices. We won't say a word.
Have fun. That's the only house rule, and it's an easy one to keep.
Any chair you like. They're all comfy, and the good one is free.
Don't show them your cards. Everything else is fair game.
No dress code, no clock, no hurry. Just cards and good company.
The kettle's on and so is the game. Take whichever you like first.
```

Morning:
```
Coffee in one hand, cards in the other. The day can wait a hand.
Cards before chores. We won't tell, and the chores will keep.
A fresh pot and a fresh deck. Not a bad way to start the day.
```

Afternoon:
```
A hand of cards fixes most afternoons. This one looks no different.
A hand of cards beats a nap. Well, just about, and you can nap after.
The afternoon is better with cards in it. Ask anyone at the tables.
```

Evening (also late night):
```
One last hand before bed? Go on, the cards won't tell.
Slippers on, cards out, nowhere to be. The evening is all yours.
A calm one to close the night. The lamp stays on as long as you like.
```

Return (see 7):
```
It's been quiet without you. Everything is right where you left it.
We left the light on. And the kettle, in case you were wondering.
Sit down, it's like you never left. Nothing here has changed a bit.
```

Drawing a clause:
1. On a return view, draw from the return group. Otherwise flip a coin: heads draws from the current hour's group, tails
   from the any-hour group.
2. Skip any clause whose FIRST sentence contains the noun of line two (chair, cards, table, deck, seat, game), so
   "your chair is warm" never sits directly over "Pull up a chair and stay a while." If every candidate is skipped, ignore
   the rule.
3. Skip the clause shown last time.
4. Draw once per page load and keep it for the visit.

## 7. The return view

Condition: the visitor's previous visit was 14 or more days ago (lobby-build already has this as `welcomeBackActive()`,
`WELCOME_BACK_ABSENCE`, consumed on the first table sit). Applies to the first hero render of that session only; every
later render in the session is the everyday case. Line one and line two of the headline do not change on a return; only
the subtitle does (return opener plus return clause). Never state how long she was away.

## 8. Data the site needs

| Piece | Source |
| --- | --- |
| Username | `Y.wocg.User.getUsername()`, as displayed in the top bar |
| Hour word | the device clock, local hours |
| Seen before | a previous `lastSeen`, or `User.getFinishedGames() > 0` |
| Return | `welcomeBackActive()` on lobby-build (previous visit 14+ days ago) |
| Last shown line, opener, clause | localStorage, three keys, plain strings |
| Headline font | computed style of the headline element |

No server call is needed beyond what the page already has. Guests never see this; their hero is the SEO headline.

## 9. Randomness and stability

- One draw per page load for line two, the opener and the clause, seeded once and reused by every re-render (the mockup
  seeds `COZY_SEED` at load). Polls and switcher changes must not reshuffle the greeting under the visitor.
- A reload is a new visit and may draw again, subject to the skip-last rules.
- With eight lines, eight openers and nine any-hour clauses, a daily player meets each line about once a week and each
  opener-clause pair rarely; that is the intended feel.

## 10. Edge cases

- Font not loaded yet: see 3. Prefer rendering the greeting after `document.fonts.ready`; the headline is a client-side
  swap for signed-in visitors anyway (the H1 in the HTML stays the guest headline for search engines).
- Narrow viewports: the same budget rule holds because line two sets the column width at every size; re-measure on
  resize only if the headline font size changes with the viewport.
- A name that is a common word ("Nobody", "Dealer") still reads correctly because the name is never a sentence subject.
- Names with a trailing space or double spaces cannot exist (validation), so no trimming is needed.
- Late night uses the Evening word and the Evening clauses; there is no separate late group by design.
- The "Daily status" switcher in the mockup is an earlier round and is off by default ("Copy as written"); it is not part
  of this spec.
