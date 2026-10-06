# Signed-in hero greeting: the spec

Decided 2 September 2026. Reference implementation: `welcome-lab.html`, section "Final" (the shared code block starts at
`/* ===== the decided signed-in copy system`), and the `final` signed-in copy variant in `index.html`. This document is the
source of truth for the site build; when the site code is written, copy this file into the wocg repo next to
`FRONTPAGE-REDESIGN.md`.

The guest hero ("Play card games" plus the weekday-and-hour tail) is a separate system and is not covered here.

## 1. What the column shows

```
Evening PiLady10            <- line one: hour word + name (see 3 for the fallback ladder)
the cards are ready         <- line two: one of eight card-room lines, drawn per visit (see 4)

Good to see you again! Sneak in a hand before anyone notices. We won't say a word.
                            <- subtitle: an opener (see 5) and a clause (see 6), one paragraph that wraps on its own

[ LIVE · 1,214 playing · 143 tables ]    <- the live capsule, unchanged
```

Type: headline in the display serif (Gelica Medium 38px in the mockup, line-height 1.15), two lines, no full stops and no
commas anywhere in the headline. Subtitle 16px body face, ONE paragraph with no forced line break, max-width 320px.
That box holds about 46 to 48 characters of the regular body face per line, the same count as the guest subtitle's first
line ("Take tricks, build melds & play classics with", 46 characters, which renders at about 292px because of its bold
words inside a 416px box). Measured in BuloRounded 16px: "Good to see you again! Have fun. That's the only" is 309px and
"...the only house" is 352px, so 320px breaks after "only", as intended. Opener plus clause run 80 to 93 characters so the
paragraph fills two lines and never a third. Capsule 28px below.

The text column is fixed (Holger, 6 Oct 2026): **336px** (`TEXT_FIT` in `FrontpageHero.js`), the widest line the hero
sets. The scene's clearing is that column plus a gap to the tiles that closes as the page column narrows, 40px at a 1160
column and 16px at 800, where the hero stacks (`clearingFor` in `FrontpageHero.js`, mirrored by the `--clx` clamp in
`_fp-hero.scss`). It never follows the copy: the copy is fitted to it.
A greeting that ran wider moved the mosaic 14px right and the page under it 10.6px. So:
- Every headline line is at most **336px** as rendered. See 3 and 4.
- The subtitle is at most **two lines** at its 320px measure. A third line moved the headline 10.8px. See 5 and 6.

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

Line one must never be wider than the widest possible line two, and never wider than the 336px text column (see
1). Measure in pixels as the headline renders: its own computed font (`font-weight font-size font-family` of the H1/H2
element) AND its letter-spacing (-0.01em, -0.38px at 38px). `canvas.measureText` leaves the letter-spacing out unless the
context's `letterSpacing` is set from the computed style; without it the widest lines measure about 8px too wide (the
old "about 370px" was that error: "the cards are waiting" renders at 362px). An offscreen span inside the headline also
works, but only while the hero has a box. Never count characters: "WMWM" is twice the width of "illi".

```
budget  = min( max( width(line) for line in POOL ), 336 )   // 334px today: "the deck is shuffled"
if width(hour + " " + name) <= budget  -> "Evening PiLady10"       (hour word + name)
else if width("Hi " + name) <= budget  -> "Hi cardShark52"         ("Hi" + name)
else                                    -> "Good afternoon"        (hour word alone; the name stays in the top bar)
```

Guide values at 38px with the 334px budget: the hour word holds names of about 7 characters after "Afternoon" and about
9 after "Morning" or "Evening"; "Hi" holds about 14. Usernames are 3 to 20 characters (`C.MAX_USERNAME_LENGTH = 20`;
letters, digits, spaces, underscores, hyphens; at least two thirds letters), so the third rung is needed for the long tail.

Rules:
- Use the username exactly as the top bar shows it. No case changes, no trimming, no ellipsis.
- Line one is `white-space: nowrap`; names may contain spaces.
- Measure after the web font has loaded (`document.fonts.ready`), or measure with the fallback font and re-run once the
  font arrives. The lab does the second; do not let the page flash between rungs more than once.
- When the third rung is used, the subtitle opener carries the name instead, if the subtitle stays at two lines (see 5).

## 4. Line two: the pool

Eight lines, drawn once per page load, never re-drawn on a re-render or a poll within the visit:

```
the table is set
the cards are ready
your seat is saved
the deck is shuffled
the table is yours
the cards are dealt
your chair is warm
the game is on
```

Remember the last line shown (localStorage `wocg-pool-last` in the mockup) and skip it, so two visits in a row never
repeat. The pool does not depend on the hour or the weekday.

Every line must render at 336px or less (see 1). "the cards are ready" replaced "the cards are waiting" (362px) on
6 Oct 2026; the words are Holger's to change. As a guard for future copy, line two is drawn only from the lines that
measure 336px or less.

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
- The name joins only if the subtitle still fits two lines (see 6, step 5). A long name often does not: measured on dev,
  a 20-character name stays in about 1 draw in 20 and a 16-character name in about half. When it is left out, it is
  still in the top bar.

## 6. Subtitle line two: the clause

Five groups. The lab keeps these lists in `COZY`.

Each clause is two short sentences, so the subtitle reaches about two lines at its 320px measure, and never more (step 5).

Any hour:
```
Pull up a chair and stay a while. The cards are patient, so are we.
Shoes off, cards up, no rush. Nobody here is watching the clock.
One quick hand, you say. That's what everyone says. Nobody minds.
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
A hand of cards beats a nap. Well, just about, and the nap can wait.
The afternoon is better with cards in it. Ask anyone at the tables.
```

Evening (also late night):
```
One last hand before bed? Go on, the cards won't tell.
Slippers on, cards out, nowhere to be. The evening is all yours.
A calm game to close the night. The lamp stays on as long as you like.
```

Return (see 7):
```
It's been quiet without you. Everything's where you left it.
We left the light on. And the kettle, just in case.
Sit down, it's like you never left. Nothing here changed.
```

Drawing a clause:
1. On a return view, draw from the return group. Otherwise flip a coin: heads draws from the current hour's group, tails
   from the any-hour group.
2. Skip any clause whose FIRST sentence contains the noun of line two (chair, cards, table, deck, seat, game), so
   "your chair is warm" never sits directly over "Pull up a chair and stay a while." If every candidate is skipped, ignore
   the rule.
3. Skip the clause shown last time.
   Tie short phrasal verbs with a non-breaking space so the wrap never splits them ("Go&nbsp;on").
4. Draw once per page load and keep it for the visit.
5. Keep the subtitle at two lines at its 320px measure. Measure the rendered paragraph (its height against two
   line-heights) before the frame paints; never count characters. If the opener plus the drawn clause makes three lines,
   try the other clauses of the same group (after rules 2 and 3) in turn and show the first that makes two. If none does
   and the opener carries the name, leave the name out and try again from the drawn clause. If still none does (only a
   column narrower than the measure), show the drawn clause without the name. The clause shown is the one remembered for
   rule 3. The choice is deterministic, so a re-render in the same visit shows the same subtitle.

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
- Narrow viewports: the text column is the same 336px at every width the hero is side by side (only the gap to the
  tiles narrows), so the 336px rule holds at every size. Stacked (a narrow column) the headline is smaller (30px, 26px on a phone), and line one is still never
  wider than the widest line two; the ladder is not re-run on a resize.
- A greeting rendered while the lobby is hidden (at a table) measures the headline from computed styles, and fits the
  subtitle when the hero has a box again, before that frame paints.
- A name that is a common word ("Nobody", "Dealer") still reads correctly because the name is never a sentence subject.
- Names with a trailing space or double spaces cannot exist (validation), so no trimming is needed.
- Late night uses the Evening word and the Evening clauses; there is no separate late group by design.
- The "Daily status" switcher in the mockup is an earlier round and is off by default ("Copy as written"); it is not part
  of this spec.
