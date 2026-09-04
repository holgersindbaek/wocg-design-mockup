# Front page type scale: the spec

Decided 4 September 2026. Reference implementation: `index.html` (the WoCG-3 front page mockup). This document is the
source of truth for every font size on the redesigned front page; when the site code is written, copy it into the wocg
repo next to `FRONTPAGE-REDESIGN.md` and turn section 6 into variables.

Two faces are in play. BuloRounded is the UI face (menu, body, buttons, tile text, tables). Gelica Medium is the display
face (the hero title and the section heads in the dividers). Everything else on the page is image, not type.

## 1. The two faces do not measure alike

Measured in Chrome with `canvas.measureText` at 100px. Ratios are fractions of the nominal font size.

| Face | Cap height | x-height |
| --- | --- | --- |
| BuloRounded Bold (700) | 0.648 | 0.498 |
| BuloRounded Regular (400) | 0.648 | 0.485 |
| Gelica Medium (500) | 0.683 | 0.507 |

Gelica's caps are 5.4 percent taller than Bulo's at the same nominal size; its x-height is only 2 percent taller. So a
Gelica size looks like a Bulo size about 5 percent larger when capitals lead (titles, heads), and about the same size in
running lowercase. Rule: to make Gelica match a Bulo step by cap height, set it at 0.95 of that step. Never compare the two
faces by nominal pixels.

## 2. The UI ladder (BuloRounded)

The live site's ladder is the conventional web UI scale. Its steps up to 24 are Tailwind's text sizes; 32 is a two-rem
Bootstrap step that Tailwind does not have. It arrived in `static/scss/_variables.scss` on 11 May 2026 ("Polish in-game
layout sizing") with no stated source. Line heights sit on a 4px grid except 18.

| Step (Tailwind name) | px | Live variable | Cap height | Used on the front page |
| --- | --- | --- | --- | --- |
| xs | 12 | `--font-size-xxxs` | 7.8 | completion badges, small labels, dropup sub-lines |
| sm | 14 | `--font-size-xxs` | 9.1 | tile chips (900), player names (700), time, dropup actions, leaderboard rows |
| base | 16 | `--font-size-xs` | 10.4 | menu links (700), body, hero subtitle, tile subtitles, capsule, footer, small buttons |
| lg | 18 | `--font-size-sm` | 11.7 | Play label on the tile, Join table / Play solo in the dropup |
| xl | 20 | `--font-size-md` | 13.0 | tile titles (700), big buttons (Play daily challenge) |
| 2xl | 24 | `--font-size-lg` | 15.6 | not used on the front page since 4 September (was the section heads) |
| 3xl | 30 | none | 19.4 | not used |
| (2rem) | 32 | `--font-size-xl` | 20.7 | not used on the front page |
| 4xl | 36 | none | 23.3 | not used |

All Bulo text on the page sits on this ladder. Keep it that way: a new UI size is one of these steps or it needs a reason
written here.

## 3. The display scale (Gelica Medium)

Two sizes, both chosen by cap height against their neighbours, not by the ladder.

| Element | Nominal | Cap height | Bulo size with the same caps | Where it is set in `index.html` |
| --- | --- | --- | --- | --- |
| Hero title | 38 | 26.0 | 40 | `.heroarea h3` and `.sceneTxt h3` (line-height 1.15) |
| Section heads in the dividers | 26 | 17.8 | 27.4 | `.divhead .ttl` (font-size and line-height), `headMetrics(... " 26px " ...)` and `base = (26 - ...)` in `prepareSectionHeads` |

The cap ladder down the page is therefore 13.0 (tile title) to 17.8 (head) to 26.0 (hero): steps of 1.37 and 1.46. At the
old 24 the head's cap was 16.4, only 3px above the tile titles and 10px below the hero, so the heads hugged the tiles.

History: the hero was 40 and dropped to 38 on 20 August 2026 because Gelica runs large. Tile titles rose from 16.5 to 20 on
18 August so they lead the tile; the subtitle dropped from 20 to 16 the same day. The Play label dropped from 20 to 18 on
4 September so the title is the tile's only 20. The heads went from 24 to 26 on 4 September.

### Why 26 and not 24, 28 or 30

Rendered at 22, 24, 26, 28 and 30 in the real layout (1119px wide, retina) and judged by a five-lens panel (hierarchy,
printer's chapter head, reader, page rhythm, robustness), a chair and two skeptics:

- 22 and 24: the head sits within 2 to 3px of cap over the bold tile titles; reads as a label, not a rank.
- 26: the cap ladder is nearly even; every seam keeps all its suit marks; the rule stub beside the widest head
  ("Trick-taking games", 231px) is 23px; on the double seam the inner stubs are 24 and 28px. Panel pick (medium confidence).
- 28: best pure hierarchy, but the stubs shrink to about 10px, marks survive today's heads by 1 to 3px, and seven heads at
  73 percent of the hero's cap get heavy down the page. Fragile.
- 30: drops marks on the Trick-taking seam (6 to 4) and on the double seam (4 to 2). Rejected.

Two judges wanted 28, two wanted to keep 24, one chose 26; the chair chose 26; one skeptic called it arguable, one said 24.

### The seam constraint that comes with 26

A suit mark is dropped when its 20px slot would come within 8px of the head's opening (text plus the 4px pad). Measured
with longer heads:

| Head on the double seam | at 24 | at 26 |
| --- | --- | --- |
| September challenge (19 letters) | keeps all 4 marks, 15px stub | drops 1 mark |
| Monthly leaderboard + September challenge | keeps all 4 | drops 2 |
| Rummy & Canasta games (catalog seam) | drops the inner pair | drops the inner pair |

So 26 needs one of: the seam slides the neighbouring mark outward instead of dropping it (preferred), or a content rule of
about 18 letters for heads on the double seam and 21 on catalog seams. Note that the divider default is moving to equal
cells across the window, which makes mark positions depend on the window width for every size; slide-before-drop helps
regardless of size. The pad beside the head is a fixed 4px; making it em-based (about 0.2em) keeps it in step if the head
size changes again.

## 4. Tailwind with Gelica compensated, side by side

If the display face is ever put on the UI ladder, use the compensated column, not the nominal one.

| Tailwind step | Bulo px | Gelica px, cap-matched | Cap height | Front page today |
| --- | --- | --- | --- | --- |
| xs | 12 | 11.4 | 7.8 | Bulo 12 |
| sm | 14 | 13.3 | 9.1 | Bulo 14 |
| base | 16 | 15.2 | 10.4 | Bulo 16 |
| lg | 18 | 17.1 | 11.7 | Bulo 18 |
| xl | 20 | 19.0 | 13.0 | Bulo 20 |
| 2xl | 24 | 22.8 | 15.6 | (heads were Gelica 24, cap 16.4) |
| 3xl | 30 | 28.5 | 19.4 | heads are Gelica 26, cap 17.8, between 2xl and 3xl |
| 4xl | 36 | 34.2 | 23.3 | hero is Gelica 38, cap 26.0, between 4xl and 5xl |
| 5xl | 48 | 45.5 | 31.1 | |

Strict Tailwind would put the heads at 23 or 28.5 and the hero at 34 or 45.5. 23 is smaller than the 24 that felt small;
28.5 is the fragile size above; 45.5 breaks the two-line hero in its 312px column; 34 with 28.5 heads leaves a cap ratio of
1.2 between head and hero. Tailwind's top end (24, 30, 36, 48) is too coarse and uneven for three display levels, which is
why the display scale is kept separate.

## 5. The one-formula alternative

A major third scale (ratio 1.25 from 16) fits every size on the page within a pixel or two, and it is a true ratio all the
way up. If one formula is ever wanted, this is the one to declare.

| Modular 1.25 | Live ladder | Front page display |
| --- | --- | --- |
| 12.8 | 12 | |
| 16 | 16 | 16 |
| 20 | 20 | 20 tile title |
| 25 | 24 | 26 section head |
| 31.25 | 32 | |
| 39 | | 38 hero |

14 and 18 are its half steps. Declaring it means either nudging 26 to 25 and 38 to 39, or accepting the rounding as the
grid concession that 24 and 32 already are.

## 6. What the site build needs

- Keep the UI ladder as it is in `_variables.scss`.
- Add two display variables: `--font-size-display-hero: 38px` and `--font-size-display-head: 26px`, both Gelica Medium,
  with the compensation rule from section 1 in a comment.
- The head builder must read its size from one place; today `index.html` repeats 26 in the CSS rule, the canvas metrics
  call and the baseline formula.
- The plain `.pophead` (24px, shown only in divider modes that do not put the head in the rule) should follow the display
  head size, or be retired with those modes.
- Open items: slide-before-drop for the suit marks, the em-based pad, and a name for the display steps in the ladder.

## 7. How to add or change a size

1. Decide which face sets it. UI text takes a ladder step from section 2.
2. For display type, pick the size by cap height against its two neighbours (section 3), then check the seam furniture:
   rule stubs beside the widest head at or above 20px, no dropped marks on today's heads and on the longest monthly head.
3. Render it in the real layout at the real window width before judging; the renders and measurements above came from
   `/tmp/wocg-tint/cdp-shots.mjs` and `cdp-heads.mjs` (headless Chromium over the DevTools protocol), which are easy to rebuild.
4. Write the decision and the numbers here.
