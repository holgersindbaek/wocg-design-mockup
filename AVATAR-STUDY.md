# Avatar study: the same faces, better on the felt

6 to 7 September 2026. Lab: `avatar-lab.html` (75 tiles, each a 300 by 300 felt table with four avatars at their seats, at the in-game size).
Study of the site's avatars as they are drawn on the table and in the lists: what a small, render-time change can do to make them more distinctive and more legible, without touching the art. The redesign mockup's open-table avatars (`index.html`, the inner rim and the outer ghost ring decided on 6 September) are the starting point and one of the references.

## The decision

Open, for Holger. The study's recommendation (section 10) is one coat, one number pair and three state coats: the mockup's own structure with the rim raised from 8% to 35% (2px at the 96px seat) and the ring from 32% to 60%, plus the pack rule for size, the yellow-and-leather turn ring, the 45% empty chair and the greyed absent seat. The quiet fallback is 25% and 45%. The one alternative worth an A/B is the self-lit rim (the edge in the face's own colour, lifted) with the same 60% ring.

## The short answer

- **Keep the structure the mockup chose on 6 September, change the numbers.** A light rim inside the silhouette and a dark line outside is the only structure that holds on the felt (where only light separates the 43 dark-edged faces) and on paper and the light wallpapers (where only dark does). At 8% the rim is below measurement: white at 8 to 15% over the art's ink lands at the felt's own lightness, a dead zone, so the mockup measures like today on the felt (edge below 3:1 on .37 of the silhouette against .38) and worse than today on khaki (93 against 143). At 35% inside (1px at 28 and 48, 2px at 96) and black at 60% outside, the share under 3:1 falls to .05 on the felt and .00 on paper, and the lab's weakest face rises from 77 to 133 on the felt, from 41 to 111 on the twelve hard cases, from 93 to 152 on khaki. It is one SVG def and one drop-shadow string, it reaches the emotion SVGs, the Lottie frames and the legacy PNGs alike, and it rendered the same in Chromium and Firefox.
- **The quiet version is 25% and 45%** (tile 16): the first pair that beats today on every ground (115, 82, 127) without a visible line on the light faces. The choice between 14 and 16 is a taste call to make on the live table, not in the lab.
- **The alternative with the most drawn character is the self-lit rim** (tile 35): the eroded ring keeps the face's own colour, pushed lighter (55% of the colour plus 45% white), with the same 60% black line outside. Dark edges get a strong rim, white bodies get none, so no chalk line on skin or on the robots; its numbers match the double keyline (151, 132, 158). It is the tile to A/B against 14.
- **Do not put anything behind the face on the felt.** Discs, chips, slates and team plates separate by brute force and are the loudest objects in the lab; they hide the free silhouette that only cardgames.io shares among card sites; a mid-green plate is 1.5:1 against the felt and hurts the dark faces. A rounded paper square is right for the picker and the profile only.
- **Size and baseline are the other half of "one family".** People are busts that fill the frame, animals are floating heads 15 to 20% smaller, robots have empty tops. A per-pack scale and drop (animals to 148 tall and a 6-unit bottom gap, robots and aliens to 152) as a CSS transform on the container makes the twelve read as one set, with no art edit and no clipping of the emotion frames. It is a generated table, so ship the keyline first and the table second.
- **States on the ring, not on new objects.** Your turn: 2px of the button's `#FFD75A` with a 1px `#5C3A00` line outside (5.9:1 on the felt, 9.5:1 on paper). The empty chair at 45% with a full ink ring. An absent player at 90% greyscale and 75% opacity. Bots framed exactly like humans: no product in the census does otherwise, and 95% of tables are bots.
- **Not worth doing:** drawn outlines alone (a paper treatment; 54 on the felt), the stickers (a decal, 18% wider at 28px), the ground-adaptive pair (a 93-wallpaper table for a khaki result the plain keyline beats), the tone filters (1 to 3 points, taste), the specular rim light (a gloss, and a lighting primitive per Lottie frame), `backdrop-filter` (a read-back per seat), and every art-level edit (7 to 8 files per avatar and no reach into Lottie).

## 1. The avatars today

| Property | Value |
|---|---|
| Files | `static/pieces/avatar/classic/`: 190 base SVGs (viewBox 0 0 160 160), each with `_win`, `_think`, `_lose` SVGs and three Lottie JSONs (1600 by 1600, 60fps) for the emotions, plus a 480px PNG. 158 are live; 31 ids in `C.AVATARS_REMOVED_IDS` are placeholders that render as the tambourine dog (and load as legacy PNGs in the game); the 16 robots are the bots' faces and hidden from the picker. A `legacy/` folder holds the older glossy full-body PNGs behind the "Use legacy avatars" option. |
| Art | Six stock packs: Avatar Users 2 and Old People (79 people), Animals avatar (37), Robot Avatars (17), Monsters (9 aliens), Christmas and Halloween (16 "Other"). Flat fills, no gradients, no silhouette outline. One dark ink, `#27273d`, draws the eyes, mouths and feature strokes in 128 of the 158 (all people, 26 animals, 14 robots, all aliens); Other uses `#181f45`; 11 animals use a navy family (`#2e3140`, `#334353`, `#3e4e60`) for ink and body alike. |
| Framing | People are busts cut flat at the shoulders by the viewBox: they touch the frame's bottom (bottom gap 0 for all 79), 148 to 160 tall, and their silhouette approximates a rounded square. Animals are floating heads: median height 131, bottom gap median 21 (max 37), so they read 15 to 20% smaller on the same seat. Robots, aliens and Other touch the bottom but carry big top gaps (median 17 to 22, RobotGirl4 44) and heads about 25% wider than people; the Other pack's faces are 25% smaller. |
| Edge | The edge lightness is a lottery: 40 avatars have a mostly light edge, 12 a mostly ink edge, and 29 have more than 30% of their edge under 1.5:1 against the felt (RobotNeutral .93, WomanWoman4 .77, WomanWoman15 .70, WomanWoman16 .69, RobotBoy9 .68, ManGeek .66, AnimalPenguin .59, AnimalCow .59). |
| Default | New players get AnimalDogTambourine, the third most saturated file in the set, floating 12 units above the base. Bots wear RobotBoy and RobotGirl; 95% of games are played against bots, so robots sit at nearly every table. |
| Recipe on the table | `pieces.scss`: the image gets four 1px `drop-shadow`s in `--color-drop-shadow` `#252525` (an opaque outline that misses the diagonals), the container an 8px ambient at 24%. Seat size from `Layout.js`: typically 96px on desktop, 68 compact. During an emotion the Lottie `<svg>` replaces the image under the same selector. |
| Recipe elsewhere | The same four drop-shadows, pasted in 11 SCSS blocks across 7 files: the frontpage table listings (about 60px, on the felt header), the table-preview modal, the hand-over and game-over plates (72 by 80, on white), the shot avatar (80, on white), the invite-AI button (32 by 35), the menu bar (28, on `#f8f9fa`), the profile modal (48, white), the friends and activity lists (32), the avatar picker (about 149px cells, a `background-image` span, selected adds four 4px `#5C940D` shadows). No crop anywhere: the natural silhouette is shown. |
| The mockup | `index.html` open-table seats (about 63px): a true 1px INNER rim (the alpha eroded by 1px, the ring inked white at 8%, laid over the art: `#avatarEdge-litrim8`) plus an OUTER ghost ring (four 1px black drop-shadows at 32%) and an all-around ambient (3px at 20%, 9px at 18%). The menu-bar avatar (28px) wears a mid-grey rim in luminosity blend; the invitee faces are 28px circle crops with a 2px `#C0EB75` ring and a 1px .64 black inset ring. |

Contrast of the inks and the grounds (WCAG 2):

| Pair | Ratio |
|---|---|
| `#27273d` (the art's ink) on the felt `#1e5c1d` | 1.80 |
| `#252525` (today's outline) on the felt | 1.90 |
| black at 32% (the mockup's ghost ring) on the felt | 1.49 |
| black at 60% on the felt | 2.03 |
| pure black on the felt | 2.60 |
| white on the felt | 8.07 |
| white at 8% over the ink, on the felt | 1.41 |
| white at 35% over the ink, on the felt | 1.73 |
| `#27273d` on the paper `#f9f6f2` | 13.5 |
| black at 32% on the paper | 2.23 |
| black at 60% on the paper | 5.63 |
| white on the paper | 1.08 |
| `#FFD75A` (the button) on the felt | 5.89 |
| `#5C3A00` (the button's leather) on the paper | 9.46 |

## 2. Why the felt is the problem

The felt sits at relative luminance .080 (its 5th to 95th percentile is .073 to .088, nearly flat). Nothing dark can separate a dark edge from it: pure black tops out at 2.6:1, today's 1px `#252525` reaches 1.9:1, the mockup's 32% ghost ring 1.5:1, and the art's own ink 1.8:1. WCAG 1.4.11 asks 3:1 for a graphical object's edge, and older eyes need more, not less: contrast sensitivity at the spatial frequencies of a 1px line falls two to three times from the 20s to the 70s, and further at low luminance, which the felt is. So on the default table only a LIGHT element at the edge can separate the 43 dark-edged faces. On paper and on the light wallpapers (about 40% of the 93 files) it is the other way round: white is 1.08:1 on paper and a dark line is needed. No single colour works on both (`#888` is 2.3:1 on the felt and 3.3:1 on paper; `#a0a0a0` 3.1 and 2.4). That is why the answer has the structure the mockup already chose, a light rim inside and a dark line outside, and why the numbers on that structure matter more than the structure.

The lens yellowing of older eyes cuts blue, so the light rim should be white or warm white, never a blue or grey tint. Under the deutan simulation the felt turns olive and the reds and greens collapse, but every rim in the lab still separates, because a rim is a luminance step and colour vision deficiency spares luminance.

## 3. The mockup's decided pair, measured

The 6 September pair does the right thing in the wrong amount. White at 8 to 15% over the art's ink lands at the felt's own lightness (1.1 to 1.4:1), a dead zone: the rim can only ever show against the 32% ghost ring next to it, which is itself 1.5:1 on the felt. Three independent measurements in this study agree:

- The perception lens's share of silhouette edge under 3:1: today .38, the mockup .37, identical at 96, 48 and 28px. At 25% the share starts to move (.24); at 35% inside with black at 60% outside it falls to .05 on the felt and .00 on paper, with no face above .01, and it holds on the `_win`, `_think` and `_lose` variants.
- The edge ideator's per-recipe sweep: rim at 12% .34, at 15% .33, at 25% .24 (and the paper score gets worse because the 32% ring is 2.2:1 there); rim 15% with the ring at 45% brings paper back to .02 and the felt to .29.
- The lab's own edge step (section 6): the weakest face on the felt at 96px is the cowboy's hat, 33 for the art alone, 58 for the game today, 77 for the mockup, 84 for the rim at 15%, 100 at 25%, 107 for the self-lit rim and 133 for the 35/60 double keyline.

The aged-eye simulation (a yellowed lens, 65% contrast, 1px blur) makes the point visible: RobotNeutral and the gorilla vanish into the cloth under today's recipe and under the mockup's alike.

## 4. Where a coat has to hold

Every avatar context on the site, with its size and ground, is in the inventory above. A coat has to hold at 28, 32, 48, about 60, 72 by 80, 80, 96 and about 149px; on the felt, on the arkadium felt, on about 60 wallpapers (60% as dark as the felt or darker, 7 of 75 with a mean lightness above .5), and on the paper contexts (the menu bar, the profile modal, the lists, the picker, the end-of-hand plates). It has to compose with the hover and selected drop-shadow stacks, leave the legacy PNGs alone (they carry a baked outline and gloss), reach the Lottie `<svg>` during an emotion, and exist on every page including the tutorial and the Arkadium embed.

Only a render-time coat meets all of that. An art-level edit costs 7 to 8 files per avatar (base SVG, PNG, three emotion SVGs, three Lottie JSONs at 1600 by 1600), 1,106 to 1,264 files for the live set, and a path edit does not reach the Lottie layers at all: for the two seconds of a win animation the face would drop to whatever the CSS fakes. The art ideator generated every art-level edit on the real files (a duplicated silhouette group with `vector-effect: non-scaling-stroke` for a constant 1 device-px keyline, an in-file erode rim, a baked die-cut sticker, a viewBox normalisation, an under-chin shade, a palette snap) and found that each is matched by a render-time fake at every size, and that a baked 2-unit stroke is 1.2px at 96 but 0.35px at 28: worse than today's constant 1px filter. So the lab is render-time only, and section 11 lists the two art-level jobs that are still worth doing for other reasons (the placeholder dog, the two inks).

## 5. What the room does (competitor census)

25 products, 19 verified from live CSS, screens or App Store captures. The full table is in the research notes; the counts:

- Circle crop: 13 of 25, mostly for photo avatars (CardzMania, Pogo, VIP Games, Zynga Poker, Spades Plus, Board Game Arena chat, Discord, Game Center, Xbox, Nintendo, Duolingo, Clash Royale profile, Hearthstone's frame). Free silhouette: 5 (cardgames.io, Kahoot, Among Us, Fall Guys, Jackbox); among card sites only cardgames.io, so WoCG's uncropped faces are a differentiator. Rounded square: 3 (VIP Spades, chess.com, Slack). No avatar in play at all: 5 (Trickster, lichess, playingcards.io, Tabletopia, Clash Royale in battle).
- Of the four dark-felt card products with avatars (Pogo, Zynga Poker, Spades Plus, VIP Games) all four use a LIGHT ring, 2 to 4px, about 4 to 5% of the diameter: white, gold or a metal bevel. None uses a dark line alone.
- Two-tone edges (light plus dark) on busy or variable grounds: Pogo's bevel, Zynga's white ring with a dark glow, CardzMania's white disc with a red active ring, Nintendo's ring on a disc.
- The three products with a free silhouette that own their art pipeline bake the outline in (cardgames.io about 1.5px in a darker skin tone, Among Us a navy line 4 to 5% of the figure, Clash Royale's troops). Every other product does it as an overlay, a frame or a filter.
- Five products put status on the ring: Zynga's turn arc, Spades Plus's timer arc, CardzMania's red active ring, chess.com's green selected outline, Discord's status notch.
- Nine attach the nameplate to the avatar as one object (VIP Spades's slab in the ring colour, Pogo's panel, the Zynga and Spades Plus pills). WoCG's blue and red slabs already overlap the chin.
- Nobody frames bots weaker than humans (chess.com, Pogo's animals, cardgames.io's Mike, Bill and Lisa).
- Size ladders: chess.com 24 to 160, Board Game Arena 32 to 184, Discord 32 to 80; seat avatars on card tables cluster at 48 to 90px, list and header avatars at 28 to 40.

Lessons the lab took from it: keep the silhouette, keep the light-inside dark-outside pair, make the light rim stronger as the face gets smaller, reuse the ring for the turn state, normalise the scale with a transform rather than a crop, and give the bots the same frame as the humans.

## 6. The lab and its measurement

Every tile is a 300 by 300 table on `green-felt.jpg` at 100px with four faces at their seats: the tambourine dog at the bottom (you), PiLady10's Supergirl at the top (your partner), a bot's white robot on the left and BobK the cowboy on the right (the opponents), with the game's nameplates over the chins (40px at the 96px face, light blue for our side, light red for theirs, a 1px `#343A40` ring and the 8px ambient). The four were picked to span the set: a floating orange animal head, a grey-haired bust, a white robot with a 76% light edge, and a dark hat whose edge is the felt's own lightness. The Set switcher swaps in twelve hard cases (the white fuzz, the felt-dark RobotNeutral, the near-black penguin, WomanWoman4 whose skin and hair match the felt, the panda, the fox, the scientist, the hooded geek, the sheep, RobotGirl3, the koala and the empty chair), the four faces' win, think and lose variants, and the four legacy PNGs. Size: 96 (the table), 68 (compact), 48 (the listing), 28 (the menu bar). Context: the faces alone, with the nameplates, or over the opponent's hand. State: rest, the open-seat hover, your turn. Sight: the three colour-vision matrices, greyscale, a 4px blur, an aged eye, daylight. Ground: the felt and nine wallpapers and the paper.

Every coat is a CSS rule on the face's image or its container (`.av`, `.av img`, `.av::before`, `.av::after`) and, where needed, an SVG filter in the page's `<defs>`: an eroded inner rim, a dilated outer outline, a blurred-and-thresholded soft outline, a sticker (a white band and a dark hairline), a self rim (the eroded ring keeps the art's own colours, pushed lighter or darker), a gradient light through `feImage`, a specular rim light, a gamma curve. Filter radii are CSS px, so a 1px rim is 1px at every size and 2 device px on a 2x screen.

The measurement: `shots.py` renders every tile at 2x in headless Chromium in 32 states (16 with the faces alone for the numbers, 16 with the nameplates for the judges' sheets), renders the same tiles as black silhouettes for the masks, and for every face takes the luminance step across the contour (the largest minus the smallest luminance in a 6px window centred on each contour pixel, 0 to 255). Each tile reports the weakest face's lower quartile ("min") and the mean over the faces. Under about 24 the edge is not there; 40 and up reads at a glance; very high values (150 and up) come from white bands or bright plates and are not automatically good. The lab shows the numbers under every tile for the ground, size and set chosen.

## 7. The families, measured

The weakest face's edge step (lower quartile, 0 to 255) on the felt at 96px, on the twelve hard cases at 96px, on the khaki wallpaper at 96px, and at 28px on the felt. Today and the mockup first; then the best and the typical tile of each family. The full table for every tile and state is under the tiles in the lab.

| Tile | felt 96 | the twelve | khaki 96 | felt 28 | aged eye |
|---|---|---|---|---|---|
| 1 the art alone | 33 | 15 | 32 | 63 | 11 |
| 2 the game today | 58 | 31 | 143 | 96 | 15 |
| 4 the mockup's pair (rim 8%, ghost .32) | 77 | 41 | 93 | 119 | 15 |
| 6 rim 15% | 84 | 50 | 95 | 125 | 17 |
| 7 rim 25% | 100 | 71 | 97 | 138 | 20 |
| 8 rim 8% + ghost .45 | 87 | 51 | 124 | 128 | 15 |
| 16 rim 25% + ring .45 | 115 | 82 | 127 | 146 | 25 |
| 14 double keyline: rim 35% (2px at 96) + black .60 | 133 | 111 | 152 | 164 | 29 |
| 18 by the ground (14 on dark, ink pair on light) | 133 | 111 | 111 | 164 | 29 |
| 20 drawn outline, ink 100% | 54 | 24 | 133 | 92 | 15 |
| 21 drawn outline, black 60% | 74 | 45 | 113 | 111 | 15 |
| 26 white keyline outside | 108 | 108 | 49 | 108 | 24 |
| 27 sticker (white band 2px + hairline) | 200 | 200 | 134 | 200 | 50 |
| 29 two-tone (grey rim in, white line out) | 161 | 154 | 86 | 164 | 33 |
| 30 self-lit rim (own colour lifted 35%) + ghost .32 | 107 | 71 | 117 | 172 | 22 |
| 35 self-lit rim, strong + black .60 | 151 | 132 | 158 | 173 | 24 |
| 36 luminosity rim to one grey + black .60 | 147 | 143 | 151 | 152 | 24 |
| 31 self-shade rim (own colour darkened) | 47 | 32 | 81 | 50 | 14 |
| 37 dark disc behind | 79 | 41 | 87 | 121 | 17 |
| 38 paper chip behind | 168 | 170 | 168 | 138 | 37 |
| 43 ink slate tile | 126 | 99 | 134 | 157 | 26 |
| 44 cream chip with the leather ring | 125 | 133 | 125 | 136 | 29 |
| 45 moss coin | 119 | 73 | 117 | 150 | 18 |
| 47 contact shadow + ghost .22 | 52 | 33 | 79 | 99 | 13 |
| 48 light halo + ghost .32 | 62 | 50 | 106 | 99 | 8 |
| 50 team halo | 76 | 66 | 96 | 101 | 13 |
| 52 cloth well | 117 | 92 | 98 | 151 | 23 |
| 57 the pack rule + the pair | 77 | 39 | 93 | 119 | 15 |
| 58 the pack rule + the double keyline | 133 | 111 | 152 | 164 | 29 |
| 63 lightness buckets + the double keyline | 133 | 111 | 152 | 164 | 23 |
| 64 rim light from above + the double keyline | 180 | 112 | 168 | 237 | 40 |

What the numbers say, family by family:

- **The decided pair, adjusted.** The mockup's pair is a real gain over today on the felt (77 against 58) and a loss on the light wallpapers (93 against 143), because the 32% ring is 1.5:1 on khaki where today's opaque outline is 5:1 or more. Turning the rim up moves the felt and the twelve (15% gives 84 and 50, 25% gives 100 and 71); turning the ring up moves the khaki (45% gives 124). Both at once, the 25/45 pair, is the first tile that beats today on every ground (115 felt, 82 twelve, 127 khaki). The perception lens's 35/60 double keyline (2px rim at 96) is the strongest of the family on every count (133, 111, 152), and the one that starts to show as a line. The ground-adaptive tile gains nothing over it: its ink branch on khaki (111) is weaker than the plain black ring (152), so a per-wallpaper table buys nothing.
- **Drawn outlines.** A dilated outline in the art's ink or in black is a paper treatment: 133 on khaki at full ink, but 54 on the felt and 24 on the twelve, worse than the mockup and no better than today, because the outline is the felt's own lightness. The 60% black outline is the mockup's ghost ring closed at the diagonals: 74 on the felt, 113 on khaki, a small even gain over the four drop-shadows. None of them helps the dark faces.
- **Light edges and stickers.** A white keyline outside is the mirror image: 108 everywhere on the felt (the twelve included), 49 on khaki. The sticker pins the metric at 200 on every dark ground because the white band is the edge, and its hairline holds khaki at 134; the two-tone (grey rim in, white line out) is close behind on the felt (161) and weak on khaki (86). These are the strongest separators and the largest changes of character.
- **Self rims.** The rim in the art's own colour, lifted, gives 107 on the felt and 172 at 28px with the 32% ring, and 151, 132 and 158 with the strong lift and the 60% ring: the second-strongest family after the stickers, with no foreign colour in the drawing. The luminosity rim (every edge pulled to one grey) is its equal on the numbers (147, 143, 151) and the most even across the twelve, at the cost of a grey line on the white faces. The self-SHADE rim (the colour darkened) is the one that looks most like the packs' own shading and the one the metric punishes hardest (47, 32): on the felt a darker edge is no edge.
- **Behind the face.** The light plates (paper chip 168, cream chip 125, slate 126) separate by brute force and are the loudest objects in the lab; the dark disc and the squircle pocket (79, 80) are no better than the pair on the felt and hurt the dark faces (41 on the twelve). The moss coin sits between (119 felt, 73 twelve). The team plate is the Pogo look.
- **Under and around.** Shadows, halos and spotlights do not make an edge: the contact shadow (52), the light halo (62), the spotlight (64) and the team halo (76) all sit at or under the mockup on the felt; the cloth well (117) is the exception because it darkens the felt right at the edge of the light faces.
- **Normalising the set.** The pack rule changes size and baseline, not the edge, so it scores as its coat (77 with the pair, 133 with the keyline). It is the one tile that changes what the table looks like as a set rather than what one face looks like.
- **Tone.** Contrast, saturation and warmth move the edge by 1 to 3 points; they are taste. The lightness buckets lift the two darkest faces without touching the rest (the twelve at 111 with the keyline). The rim light from above scores highest of all non-sticker tiles (180, 237 at 28px, 40 under the aged eye) because the specular highlight lands exactly on the top edge, and it is unmistakably a bevel.
- **States.** The state coats ride on the pair, so their resting numbers are the pair's; what they change is one seat. The gold line for your own face fails on the light wallpapers (21 on khaki: gold on khaki is nothing), which is the argument for the yellow-plus-leather turn ring over a single gold line.

## 8. The panel

Six judges were planned, two per lens (craft and taste; legibility and sight; robustness and the table as a whole), each reading the face sheets of five to seven states for all ten sections, then three skeptics per leader. **One judge finished; the other five and all thirty skeptic passes failed on the account's session limit** (it resets at 4am Copenhagen time) and are to be resumed from the same run, with the finished judge cached. What follows is the one finished lens, the robustness judge (a front-end engineer's reading of 82 sheets across the felt, khaki, clouds, the black fabric, the pumpkin, the stress set and the hover state), and the study's own reading of the sheets, kept apart.

The robustness judge's scores (0 to 10, 5 = no better than today and the mockup):

| # | tile | score | what the judge saw |
|---|---|---|---|
| 14 | double keyline 35 / .60 | 9 | The one coat that held on all five grounds: the robot's dome on khaki and clouds, the grey hair on black, both on pumpkin, the dark faces on the felt. One def plus drop-shadows; the same result on the legacy PNGs and the emotion frames. Downside: the 2px rim at 96 is a frosted edge on the white robot. |
| 16 | rim 25 / ring .45 | 8 | The quiet keyline; the same single def, less loud. "My pick if 14 is judged too heavy." |
| 35 | self-lit rim, strong + .60 | 8 | Holds all five grounds with one colour mix and a black hairline; dark edges get a strong rim, white bodies none, so no chalk line on the robot. |
| 17 | rim 15 / ring .45 | 7 | Holds the light grounds with the ring; the felt stress score (60) is borderline for the gorilla. Cheap, one rule. |
| 36 | luminosity rim + .60 | 7 | Holds everywhere, but the grey rim is a visible frame on the white robot and the panda, and one more blend primitive for Safari to get right. |
| 58 | the pack rule + the keyline | 7 | Tile 14's edge with the pack rule: the best-looking stress row. The edge part is one def; the rule is a table. |
| 73 | the empty chair at 45% | 7 | Reads on khaki and the felt; opacity plus the same filter, one class. |
| 74 | away: grey and faded | 7 | Plain CSS on one seat; reads as absent on all five grounds. |
| 8 | rim 8 / ring .45 | 6 | Pure drop-shadow, no SVG filter: the cheapest fix for khaki and clouds; the dark faces on the felt stay where they are. |
| 21 | drawn outline, black 60% | 6 | Today's outline done properly, closed at the diagonals and see-through; still no light element for the dark faces. |
| 27, 28 | the stickers | 6 | Technically the most robust coat and one def, but on khaki the white band merges with the ground and at 48 on clouds it is a frame a sixth of the face; 150 frames in the picker. |
| 4 | the mockup | 5 | The scale's middle: the 8% rim is invisible, the 32% ring a soft grey halo on khaki; the robot's dome nearly vanishes on clouds at 48. |
| 1 | the art alone | 2 | The floor. |

Rejected outright by that judge: `quietground` (a compositing read-back per seat, a Safari prefix, only the iframe's own content in the Arkadium embed), `feltcoin` (a green disc on every wallpaper that is not the felt), `keywhite` (loses the robot on khaki and clouds), `dilleather` and `ringleather` (a brown line that merges into khaki and pumpkin and stains the robots), `rimlight` (a lighting primitive per avatar, per Lottie frame, per picker cell; Firefox is slow with it), `emptyghost` (nearly invisible on khaki), `tomb` and `shelf` (depend on the plate; a mystery slab elsewhere), `seatring` (peeks out above the head only), `spot`, `glow`, `teamhalo` (edge numbers below the mockup on two grounds), `warm` (sepia turns the white robot cream), `megold` (a gold line vanishes on the yellow dog on khaki), `adaptive` (a lightness class for 93 wallpapers for a khaki result that tile 14 beats with one rule), `dilink15` (blurry at 48, does not scale).

The judge's cross-cutting observations:

- Only the coats that put a light element inside and a dark line outside in one def (14, 16, 35, 36) held on all five grounds. Every single-sided coat failed one ground: dark lines fail on the black fabric and on the felt's dark faces, white lines fail on khaki and clouds.
- The white robot is the test case for the light wallpapers: at 48 on khaki and clouds its dome disappears under the mockup, rim 15, rim 25, the white keyline, the self-lit rim without a ring, the glow, the spotlight and the team halo. Only a dark outer line saves it.
- The behind-the-face frames have identical numbers on every ground because they hide the ground: robustness by removal, at the cost of the silhouette.
- Several tiles are the same picture: `pairnoamb`, `paircontact` and `baseline`; `ref-game` and `inktoday`; `toplight`, `warmgamma`, `bottomshade` and `botsquiet` are visually the mockup at 96.
- Every per-avatar table (54 to 58, 63) buys evenness of size, not edge; the edge gain in 58 and 63 is the keyline they carry. Ship the keyline first and the table later.
- All the SVG-filter coats rendered the same on the legacy PNGs and the emotion frames, so a filter on the seat container covers the image, the emotion SVG and the Lottie canvas alike; the two exceptions with a real per-frame cost are `backdrop-filter` and the lighting primitive.
- A def can scale on its own if the morphology radius is set in `objectBoundingBox` units (the 1px rim at 48 becomes 2px at 96 without a second def); below 48 that would thin the rim under 1px, so keep CSS px there.
- Two of the four principal files are not what their ids say: the classic `ManCowboy.svg` is a bearded man in a red backwards cap and `WomanSuperGirl2.svg` a grey-haired woman with glasses; the legacy PNGs under the same ids are the cowboy and the blonde. (The judge also reported the turn and hover states as not rendered; they are, on the `-normal-turn` and `-normal-hover` sheets, with the yellow ring and the lift on the bottom seat. The metrics under those tiles are the resting numbers, which is what the judge saw.)

The study's own reading of the sheets (the author, from the felt at 96 and 48, the twelve, the emotions, khaki, the aged eye and 28px), kept separate from the judge:

- On the twelve, the mockup's pair loses the gorilla, RobotNeutral and the hooded geek into the cloth; the 25% rim gives them a faint edge, 35% a clear one. At 96 the 2px rim of tile 14 is visible as a pale line on the grey hair and the robot's dome, which is the "frosted" objection; tile 16's 1px at 25% is not, and it still separates the three dark faces, less.
- The self-lit rim (30, 35) is the coat that looks most like the packs' own drawing: the fuzz gets a pale blue edge, the fox a pale tan, the dog a pale gold, the skin a highlight. With the 32% ring it leaves the gorilla weak; with the 60% ring (35) it reads on the twelve as well as 14 and without any white on the white faces. The luminosity rim (36) is the evenest and the least like the art: a grey line on the panda and the sheep.
- The stickers make decals; the chips and slates make cards; the moss coin makes poker chips. All three change what the avatar is.
- At 28px every 1px rim looks alike; the difference is the ring: 45 to 60% reads, 32% does not, on paper especially.
- Under the aged eye everything collapses to the same soft blur; the pairs with the 60% ring keep a shape where the mockup keeps none.
- The pack rule is the one tile that changes the table as a set: the dog, the koala and the sheep grow into the people's size and sit on the plate; nothing clips in the win and think frames.

## 9. What the skeptics said about the leaders

The thirty skeptic passes (three per leader: craft, legibility, implementation) did not run; they are queued with the rest of the panel. The objections the study itself can raise, for the record:

- **14, the 35/60 keyline:** the 2px rim at 96 is a pale line on the light faces (the robot's dome, the grey hair); on skin it is the "chalk" the perception lens warned about above 45%. Fix: 1px at 35% up to 68px, 2px only at 88px and above, and try 30% at 2px before 35%.
- **16, the 25/45 keyline:** the gorilla and RobotNeutral are separated but not by much (82 on the twelve); under the aged eye it is close to the mockup. Fix: none inside the pair; if the twelve matter more than the light faces, take 14.
- **35, the self-lit rim:** the mix is a `feComponentTransfer` on the eroded ring, one more primitive than 14, and its effect depends on the face's colour, so two players' rims differ in strength; on the all-ink gorilla the rim lands at 2.3:1, under the 3:1 target. Fix: none needed for the numbers; the objection is consistency of look, which is also its charm.
- **58, the pack rule:** a 158-entry table of (scale, dy) to generate from the alpha bboxes and keep; the hover scale and the emotion frames must compose with it; two avatars (RobotGirl4, AnimalAlligator) would need 1.3 and are capped. Fix: generate the table once in a maintenance script from the classic folder; put the transform on the container, not on the filtered image (WebKit rasterises a transformed filtered element soft during the transition).
- **72, the turn ring:** yellow on the yellow dog and the blondes; another use of the button's colour. Fix: the leather line outside carries it on yellow faces; keep it to one seat.
- **73, the empty chair at 45%:** on the light wallpapers only the ring shows, an outline of a chair. That is arguably right.

## 10. Recommendation

One default coat for every avatar on every ground, three state coats, and one set-level rule, all render-time, in the order to ship them.

1. **The default coat (tile 14, with 16 as the quiet setting):** the mockup's structure at measured strengths. The def, once, in `body_open.dust`:

   ```
   <filter id="avatarRim" x="-2%" y="-2%" width="104%" height="104%" color-interpolation-filters="sRGB">
     <feMorphology in="SourceAlpha" operator="erode" radius="1" result="eroded"/>
     <feComposite in="SourceAlpha" in2="eroded" operator="out" result="ring"/>
     <feFlood flood-color="#ffffff" flood-opacity="0.35"/>
     <feComposite in2="ring" operator="in" result="rim"/>
     <feBlend in="rim" in2="SourceGraphic" mode="normal"/>
   </filter>
   ```
   and a second def `avatarRim2` with `radius="2"` for boxes of 88px and up (the seat on desktop, the picker cells). The image:
   ```
   filter: url(#avatarRim) drop-shadow(1px 0 rgba(0,0,0,.60)) drop-shadow(-1px 0 rgba(0,0,0,.60)) drop-shadow(0 1px rgba(0,0,0,.60)) drop-shadow(0 -1px rgba(0,0,0,.60)) drop-shadow(0 0 3px rgba(0,0,0,.20)) drop-shadow(0 0 9px rgba(0,0,0,.18));
   ```
   The quiet setting is `flood-opacity="0.25"` and `.45` on the four shadows. The two numbers are one CSS custom property each, so the choice can be made on the live table. The 8px ambient on the seat container goes; the hover ambient above replaces it. Legacy PNGs and the 31 placeholder ids get the drop-shadows only, no rim. The mockup's Avatar edge switcher should get these two as options (`keyline3560`, `keyline2545`) so the frontpage can be judged with them; `index.html` was not edited in this study because it carries another session's uncommitted changes.
2. **The A/B alternative (tile 35):** the same drop-shadows, and a rim def whose ring keeps the art's colour lifted: replace the flood with `<feComposite in="SourceGraphic" in2="ring" operator="in" result="ringArt"/><feComponentTransfer in="ringArt" result="lit"><feFuncR type="linear" slope="0.55" intercept="0.45"/><feFuncG .../><feFuncB .../></feComponentTransfer>` merged over the source. Same numbers as 14, no white on skin or white bodies, a rim that looks painted.
3. **The states (72, 73, 74):** the active seat's ring becomes 2px `#FFD75A` with a 1px `#5C3A00` line outside (a dilate 2 and a dilate 3 in one def, merged under the art); the empty chair gets `feFuncA slope .45` with a 1px `#27273d` ring at 55%; a dropped or sitting-out player gets `grayscale(.9) contrast(.9)` and `opacity: .75`. Bots keep the default coat.
4. **The pack rule (tile 57 or 58), second:** a generated table of (scale, dy) per avatar id from the alpha bboxes (animals `clamp(148/h, 1, 1.12)` and a drop to a 6-unit bottom gap; robots, aliens and Other `clamp(152/h, 1, 1.08)`; people 1), applied as `transform` on the seat container with `transform-origin: 50% 100%`. Judge it on the live table before keeping it; it is the one change that alters the set, not the edge.
5. **Elsewhere:** the picker and the profile may take the rounded paper square (tile 42) as a frame; the invitee circles keep their 2px green ring; the frontpage listings and the menu bar take the default coat unchanged (the 60% ring is 5.6:1 on paper, the white rim invisible there, which is correct).

What not to do: plates on the felt, stickers on the table, gold lines, a per-wallpaper lightness table, `backdrop-filter`, lighting primitives, tone filters, and any edit to the SVG or Lottie files for the edge.

What to measure after shipping: the same edge-step harness on live screenshots of the seat, the listing and the menu bar, on the felt and on khaki; and a look at the twelve on a real 1x Windows screen, where a 1px rim is one device pixel.

## 11. Implementation notes

- Structure: two CSS custom properties and one inline SVG def, mirroring the mockup's `url(#rim) var(--avshadow)` chain: `--avatar-rim: url(#avatarRim)` and `--avatar-shadow-felt` / `--avatar-shadow-paper` in `_variables.scss`, referenced from the 11 blocks that now paste the four drop-shadows. The hover and selected stacks append their extra shadows after the variables.
- The def lives once in `web/dust/common/body_open.dust` (dust comments only, no `//` inside scripts) so it reaches the frontpage, the game, the tutorial and the Arkadium embed. `x="-2%" y="-2%" width="104%" height="104%"` for a rim, `-10%` and `120%` for anything that paints outside; `color-interpolation-filters="sRGB"` always.
- Rim radius 1 (1 CSS px) from 28 to 96px; radius 2 for the picker cells at about 149px (a second def) and, if the 35% rim is chosen, at the 96px seat.
- Legacy PNGs and the 31 removed ids: shadow only, no rim (they carry a baked outline and gloss). Today only the in-game seat exempts them; `TableListingsBar.js` ignores the option.
- Move the listing's hover `scale(1.12)` from the filtered image to a wrapper: a transform on a `url()`-filtered element rasterises soft in WebKit during the transition.
- No `will-change` on avatar pieces; never transition the `filter` property; keep the largest blur at 9px. `feMorphology` on four to eight seats is cheap as long as the filter is static; only one seat animates at a time. `backdrop-filter` (the quiet-ground candidate) forces a compositing layer with a read-back per seat: fine for a table, not for the picker or the listings.
- Emotion variants grow the silhouette by up to 30 units sideways (the men's thumbs-up) and 25 upward (the robots), never downward; any ring, plate or clip must leave that room, or use `overflow: visible`.
- Test matrix before deploy: 28, 32, 48, 60, 72 by 80, 80, 96, 68 and 149px; the felt, the arkadium felt, one light wallpaper, `#f8f9fa` and white; Chromium, Safari 17+, Firefox. The lab's recipes were rendered in Chromium and Firefox in this study; Safari was not exercised.

## 12. Found on the way (not the edge, but in the same files)

- The classic folder's file names are scrambled for some ids (the sheep is stored as `AnimalSeahorse.svg`; `AnimalSheep.svg` is a placeholder dog; `ManCowboy.svg` is a bearded man in a red cap and `WomanSuperGirl2.svg` a grey-haired woman with glasses, while the legacy PNGs under those ids are the cowboy and the blonde; `AnimalPenguinConfused.svg` is a gorilla), and the 31 removed ids are dog placeholders at 480 by 480. A player with one of those ids is a glossy full-body PNG at the table and the tambourine dog in the frontpage listings: two faces for one person. The art ideator proposes a one-time remap of the 31 to the nearest live avatar (twelve have no same-species match), with a notice in the picker, and deleting 217 dead files.
- Two fallback avatar ids (`player1`, `m1`) do not exist as files; `WomanWoman21` has no `_think.json`, which stalls that seat's emotion queue for the session.
- The Other pack's ink `#181f45` differs from the shared `#27273d` by L .006; a find-and-replace across 16 avatars times 7 files (and the Lottie colour arrays) would make all line work one ink. Housekeeping, not a visible change.
- Aliens and robots are about 30% more saturated than people; a pack-level `saturate(.92)` closes half the gap. Low gain, and the robots are the bots' identity; left alone.

## Appendix: how the lab was made

- `avatar-lab.html` carries its data inline: `REFERENCE` (5 tiles), `CANDIDATES` (70), `SETS` (the faces with their measured width, height, bottom gap and lightness bucket), `GROUNDS`, and the filter builders (`innerRim`, `outline`, `softOutline`, `outlineRim`, `sticker`, `selfRim`, `topLight`, `rimLight`, `gammaCurve`). A candidate's `css` and `svg` use the token `ID`, replaced by its id at build time, so every tile's rules and filters are scoped to `.t-<id>`.
- The harness: `#shots=1,size=48,ground=khaki,set=stress,ctx=plates,mask=1` in the URL lays the tiles out on a fixed 324px pitch, four across, with the captions hidden; `mask=1` renders black silhouettes on white. `window.__avLab` exposes the state, the tiles and the sets.
- `shots.py` (in `/tmp/avstudy/`, not in the repo) drives headless Chromium: `--dump-dom` for the tile order and the seat geometry, `--screenshot` at `--force-device-scale-factor=2` for the sheets and the masks; PIL for the contour metric; the per-section face sheets (one row per tile, one zoomed face per seat) are what the panel judged.
- The research behind the tiles: four lenses (perception and craft; the codebase; the art set; a competitor census) and four ideators (edge only; behind and under; art-level edits and their render-time fakes; tone, colour and state), each with its own renders and measurements. Their notes are summarised in sections 1 to 5 and 11 to 12.
- `avatar-lab/` holds the 32 assets the lab needs (the four faces with their emotion variants, the twelve hard cases, the four legacy PNGs), copied from the repo; `AnimalSheep.svg` here is the repo's `AnimalSeahorse.svg`.
