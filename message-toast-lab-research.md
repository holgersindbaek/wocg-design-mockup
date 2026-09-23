# Message box and toast lab: research and design brief

Written 23 Sep 2026 by the research workflow for `message-toast-lab.html`. Read-only research; line numbers are for the tree on that day.


---

# Report: message-box

## Table message box (`.spot-messageBox`): full report for the animation and toast lab

**Scope and method.** I read the code and then measured it on the dev server (`https://dev.worldofcardgames.com`, `body.wm` on). The browser was a guest session in Chrome for Testing with a temp profile, always closed in a `finally`. The probe scripts, JSON output and screenshots are in `/tmp/msgbox-probe/`, outside the repo. I changed no repo file.

**Line references.** Table.js and pieces.scss lines are for HEAD `2c8378bd3`. While I worked, another session changed `Table.js` heavily in the working tree (diff +1989 lines). The message code in that diff is the same, but the lines move:
- +2 for HEAD lines 990 to 1750
- +21 for 2928 to 4931
- +27 at 5141
- +922 from about 6400 on

pieces.scss has one uncommitted message-box change: the 16/20 rule at every size (working tree 2562-2565). `_wocg-tokens.scss` in the working tree also takes `.spot-messageBox` out of `$wm-token-roots`.

---

### 1. Lifecycle (Table.js)

**Create.** `createMessageBox` (1285-1290) makes a `div.piece.classic.text.spot-messageBox.spotPrefix-messageBox`. It appends it to **`#mainContainer`**, next to `#playspace`, not inside it, then calls `resizeAndPositionMessageBox`.
- It runs once in the table constructor (990), after `resizeAllSpots` (982), so the plates already have their places.
- `renderMessage` builds it again if it is missing (3094-3099).
- `renderMessage` (3094) and `hideMessage` (3184) find the box with the **global** `Y.one(".spot-messageBox")`, not with `this.messageBox`.

**Show.** `showMessage` (3067-3081) runs `normalizeMessageArgs` (2945-2977):
- duration defaults to **5 s**
- category defaults to `"important"`
- prefix is `alert` when `resync`, `none` when `skipPrefix`, and `notice` otherwise

Then:
- `shouldSuppressMessage` (3011-3019) applies the Game prompts setting (`User.js:52`, default 2). Mode 0 suppresses `hint` and `status` messages. Mode 1 suppresses `status` only.
- `shouldDelayMessage` (3021-3024) is true only for `timing === "delayed"`, and **no caller passes that** (grep). So `scheduleMessage`, `getMessageDelay` and `isScheduledMessageCurrent` (3026-3065) never run today. `clearScheduledMessage` (2979-2986) is still called from `showMessage`, `hideMessage()`, `phaseExcludeHandler` (3634), `phaseStopHandler` (3651), `playerTurnStopHandler` (4727) and `destroy`.

`renderMessage` (3083-3167) then does this, in order:
1. It returns if `this.destroyed` (3087).
2. While a table error shows, a non-error message is not drawn. It is only stored in `messageBeforeTableError`, and only the latest one is kept (3088-3091).
3. **Same text and inline opacity ≠ 0 means return early** (3100). The lifespan timer does **not** restart.
4. It calls `hideMessage(text)` (3102). This does nothing in practice, because it only acts when the current text equals the new text and the box is visible, and step 3 already returned in that case.
5. `stopMessageBoxAnimation` (2928-2937) stops the Sequence and runs `Y.Transition.cancel`, which cancels the WAAPI `__propsAnim`.
6. It sets `innerHTML`:
   - `alert` gives `<strong>Label:</strong> <span>text</span>` plus the class `resync`
   - otherwise `<span>text</span>` and the class `resync` is removed
7. It adds the buttons:
   - `buttonText` and `extraButtonText` are raw HTML with click listeners (3122-3133)
   - `buttons[]` are built nodes with an optional `.long`/`.short` pair (3135-3144)
8. It sets `display:block` and `pointer-events:auto`, then runs a Sequence of one opacity step to **1, 160 ms, linear** (3146-3156).
9. It restarts `lifespanTimer = new Timer(duration)`, which calls `hideMessage(text)` when it ends (3158-3164).

**Hide.** `hideMessage(matchText)` (3170-3211):
- Without `matchText` it clears the scheduled message.
- During a table error, `hideMessage()` only drops the stored message. A match on the stored text also only drops it.
- Otherwise, if there is no `matchText`, or it equals the current text and the box is visible:
  1. stop the lifespan timer
  2. set `pointer-events:none`
  3. cancel the running animation
  4. run a Sequence of one opacity step to **0, 160 ms, linear**, with a `cb` meant to set `display:none` and clear `currentMessageText` and `currentMessage`

**Confirmed defect: the hide callback never runs.**
- `Y.Transition.Sequence.prototype.next` (Transition.js:804-831) calls `run(Object.merge(base.clone(config), { cb: this.next.bind(this) }))` (828).
- `Object.merge` (Object.js:28-40) replaces the config's own `cb`.
- Measured result after a hide or after the lifespan ends: inline `display:block`, opacity 0, `pointer-events:none`, and `currentMessageText` and `currentMessage` **still set**.
- The commit `84b208b09` ("Prevent hidden table messages blocking clicks") worked around what this defect causes. It did not fix the defect.

What this causes:
- **A stale message comes back.** `showTableError` saves `this.currentMessage` as `messageBeforeTableError` (9878-9880), even when that message expired long ago. `hideTableError` then draws it again with its full original duration (9943-9945). Measured: "Spades broken!" expired, a tip ran for 600 ms, and then "Spades broken!" faded back in. Also measured: a hidden "Alert: out of sync" came back after a tip.
- **The games' `display === "block"` tests are always true** once any message has shown:
  - `hearts-game.js:296`
  - `pinochle-game.js:211, 1562`
  - `pinochledd-game.js:1321`
  - `ginrummy-game.js:2617`
  - `cribbage-game-ui.js:1210`
- `showOrHideTableMessage` reads `currentMessage.scope` after the message has hidden (1563).

**Transition engine facts that explain the snaps.** `run` (Transition.js:215ff) is WAAPI:
- The start value comes from `getStyleAsNumber("opacity")`, which is the inline value, or the computed value when inline is empty (yui3 `dom-style.js:96-116`).
- The final value is written inline **at once** (`setFinalDirectStyle`, 211-213 and 488), then `element.animate([from,to])` runs (491).

So:
- **A text swap while showing** has no animation. Inline opacity is already 1, so from and to are both 1 and no animation is made. `innerHTML` changes at once, and the box jumps to its new size (auto width and height, fixed left and top). Measured: 198×44 became 200×64 in one frame.
- **Hide, then show within 160 ms** (this includes the same text): the fade-out starts, is cancelled, the box **snaps to 0**, and the new text fades in 0→1 over 160 ms. Measured: 1.00 → 0.90 → 0.79 → **0.00** → 0.10 … 1.00. The same happens with the same text, because inline opacity is already "0".
- **Hide during a show**: inline opacity is already "1", so the box snaps to 1 and then fades 1→0. This is from the code, and the snap in the case above confirms the same mechanism.
- **Same text while showing**: early return, nothing changes, and the timer does not restart.

**Table errors and tips.**
- The module-level `showTableError` (719-724) runs only when `pollingSuggested()` is true, which means the game started, it is not a tutorial, and the game is not over.
- `Table.prototype.showTableError(msg, duration, type="notice")` (9875-9930):

| Case | Label | Paper | Timing |
|---|---|---|---|
| `"Lost internet"` | "Notice:" (alert), `.resync` | red | After `C.TABLE_POLL_INTERVAL` (10 s), becomes "Error:" with "Connection problem" (or "Lost internet" when `navigator.onLine===false`) and a red **Reload game** button (9891-9914) |
| `type "tip"` | "Tip:" (prefix none) | band paper | as given |
| any other type, including the default | "Notice:" or the type name, `.resync` | **red** `--plate-red #fcbcb4` (pieces.scss:1441-1445) | as given |

- The beta notice (458) is therefore red.
- The box itself gets duration DAY. A given `duration` hides it later through `hideTableError` (9925-9929), guarded by a nonce.
- `hideTableError` (9935-9949) draws the stored message again or hides the error.
- The beta notice (458) and the bookmark tip (464, 8 s, once a month by cookie) call the table directly, 1 s after the table is created.

**Destroy** (9956ff, message part 10008-10021):
- It stops the lifespan timer, clears the scheduled message, nulls the current message, and removes the box at once with no fade.
- The playspace fades over `SCREEN_TRANSITION_DURATION` = 160 ms (wocg.js:341), unless `immediate`.
- `tableErrorText` and the 10 s "Lost internet" escalation timer are not cleared. They are harmless, because `renderMessage` checks `destroyed`.

**Lobby-to-table switch.**
- The default variant is `"ink"`, a same-document View Transition (`LobbyTableSwitch.js:57`, 177-212). The whole flip, including table create, runs inside the update callback.
- The waiting notice or the countdown renders during create (`tableStateChangedHandler(true)` at 1007), so its 160 ms fade runs live under the transition. A solo bots table shows no notice.
- `tablePieces` excludes the box on purpose (290-296, comment 283-289: "the message box comes and goes on its own"). The filter never matters, because it only queries `#playspace` and the box is not there. `tableExtras` (338-345) does not include it either.
- On leave during the switch, `GameSelectors.js:361` calls `destroyCurrentTable(null, true)`, so the snapshot covers the box's instant removal. `LobbyTableSwitch.js:135` calls it with `false`.

---

### 2. Geometry

**Placement code** (`resizeAndPositionMessageBox`, 1296-1363). It runs only on create (1289) and on `Table.resize` (9133). It **does not run per message**.
- `gutter = Y.wocg.playspaceGutter()` gives 16, or 8 when the board is compact (wocg.js:752-755). The side-bar layout is off under `wm` (wocg.js:906-907).
- `left = playspace.left + gutter`. `top = playspace.top + (rowTop ?? gutter)`. `marginTop` is set to 0, which overrides the CSS `margin-top`.
- `rowTop = topChromeRowTop` (173-177). It is null unless `body.wm`. Otherwise it is `Layout.topPlayerRowTop` (Layout.js:780-785):
  - normally `topPlayerNamePlateTop` = max(plate bottom − plate height, gutter + plate height + 8) (769-778)
  - on a narrow portrait board, `narrowPortraitTopPlayerNamePlateTop` = gutter + avatar size (787-789)
- The cap is found like this:
  1. Clear `max-width` and `min-width` and read the CSS max (320, or 160 on a small portrait board), the min (80) and the horizontal padding.
  2. Find the nearest name plate that is right of the box and in the top half of the playspace.
  3. `maxWidth = floor(plateLeft − boxLeft − gutter − padding)`.
  4. If it is ≥ the CSS max, keep the CSS max.
  5. If it is < 80: under `wm` it clamps to 80. With the flag off, the function stops and keeps the CSS values.
  6. If `rowTop` is set and `maxWidth < 140`, add `narrowCap`. The buttons then show their `.short` words (pieces.scss:1463-1479).

**CSS** (pieces.scss:1400-1491):

| Property | Value |
|---|---|
| paper | `var(--paper-band)` #f4eee5 |
| shadow | `--shadow-low` (inset 1px #393939 ring and 0 0 8px rgba(0,0,0,.24)) |
| radius | `--radius-lg` |
| padding | 12 |
| size | `width/height:auto !important`, min 80, max 320 |
| z-index | 4800 |
| resting state | `opacity:0; display:none` |
| compact board | padding 8, 16/20, margin-top 8 (1426-1431) |
| small portrait | max 160 (1433-1435) |
| `data-platform=mobile` | top = safe area (1437-1439) |
| buttons | full width, 8 gap (1452-1491) |
| type under `wm` | small board 14/18 (2564-2567, committed); **16/20 everywhere else** (working tree only). HEAD still has 20/24 on a large board. |

`--radius-lg` is 16 with the squircle and 8 without it, and 12 or 6 when the window is ≤640 in either dimension (`_variables.scss:43, 197, 217, 236`). The global squircle rule is at base.scss:254-264.

**Measured, hearts, 4 seats, `body.wm`, ads on:**

| | Desktop 1200×800 | iPhone landscape 750×340 | iPhone portrait 390×664 |
|---|---|---|---|
| `#mainContainer` classes | `playspace-landscape` | `compact small landscape` | `compact small portrait` |
| playspace rect | [0,0,864,800] (336 ad rail) | [0,0,590,340] (160 rail) | [0,100,390,564] (100 px top banner) |
| gutter / rowTop | 16 / 72 | 8 / 48 | 8 / 76 |
| box left, top | 16, 72 | 8, 48 | 8, 176 |
| N plate (nearest top plate) | [232,72,400,40] | [154,48,283,32] | [151,176,88,32] |
| cap (content max-width) | **176** (box 200) | **122** (box 138), narrowCap | **119** (box 135), narrowCap |
| padding / type / radius | 12 / 16px/20px / 16 | 8 / 14/18 / 12 | 8 / 14/18 / 12 |
| button height, font | 32, **20px** (larger than the 16px text) | 24, 16px | 24, 16px |
| pills | [16,16,120,40], [728,16,120,40] | [8,8,96,32], [486,8,96,32] | [8,108,96,32], [286,108,96,32] |

**Box sizes by message (w×h):**

| Message | Desktop | Landscape | Portrait |
|---|---|---|---|
| "Hearts broken!" | 121×44 | 101×34 | 101×34 |
| one-line hint | 191–198×44 | 138×52 | 135×52 |
| countdown | 200×64 | 138×70 | 135×70 |
| rematch | 200×84 | 138×106 | 135×106 |
| pause | 200×104 | 138×106 | 135×124 |
| waiting (public, 2 buttons) | 200×124 | 138×116 | 135×116 |
| waiting (private, 2 buttons) | 200×144 | 138×134 | 135×134 |
| redeal, 1 button | 200×124 | 138×120 | 135×120 |
| tip | 200×84 | 138×88 | 135×88 |
| Reload error | 200×84 | 138×84 | 135×84 |

**Collisions measured with the private waiting notice:**
- **Landscape:** the box ends at y 182. It covers the W avatar [34,119,54,54] and 10 px of the W plate (top 172). See `shot-landscape-hearts-shotwait.png`.
- **Desktop:** it covers the top 30 px of the W fan (the cards start at y 186).
- **Portrait:** it covers 20 px of the W fan and 3 px of the N fan.

---

### 3. Real messages

Durations come from the code, and from live measurement where marked. "Buttons" means the box carries buttons. Tutorials are left out.

| # | Text (as rendered) | Where | Duration | Buttons | How often it changes |
|---|---|---|---|---|---|
| 1 | "Table **#12** starts when full." (flag off: "…will start when full. Invite friends or start with bots.") | 1560-1657 (the `wm` wording is commit `ff366168c`) | DAY, scope table | **Start with bots** (short "Add bots") and **Invite players** | Drawn again when players join or leave (same text returns early) |
| 2 | "Private table **name** starts when full." (+ " Bots are off for this table.") | same | DAY | the same two | same |
| 3 | "Table **#12** continues when full." / "…Bots allowed if all players agree." | same | DAY | **Continue with bots** / Invite | same |
| 4 | "…Redeal vote closes in 28 seconds." | 1633-1635 | DAY | **Vote to redeal** (short "Redeal") | The number is fixed when drawn and does not count down |
| 5 | "This table is for chatting only." | 1618 | DAY | maybe Start with bots | rare |
| 6 | "Table is full. Game will start in **10 seconds**." → … → "**1 second**" → "Dealing cards..." | 1496-1512 | DAY | none | **rewritten every 1 s** for 10 s; ticks sound at 3, 2, 1 |
| 7 | "Game is starting." | 1748 | DAY | none | once |
| 8 | "Waiting for Tin Man to bid." (status) | spades-game.js:104 (also pinochle:402, twentynine:448, bridge:313) | turn length (measured 30.8 s) | none | **every ~0.75-0.85 s** in bot bidding (measured), hidden at turn stop (spades:176) |
| 9 | "Waiting for EVE to play." (status) | crazyeights-game-event-handler.js:179 (also cribbage-ui:1127, sheepshead:137, bridge:328) | turn length (25 s measured) | none | **swapped in place every ~1.7 s** (measured), never hidden at turn stop |
| 10 | "Play a card from your hand." (hint) | crazyeights-click-handler:42, pinochle:460, cribbage-ui:1124 | turn time left or 25 s (measured 25 s at a solo table, where your turn lasts 604800000 ms) | none | each of your turns |
| 11 | "Select 3 cards to pass left." (hint, phase) | hearts-game.js:158 | phase length | none | once a hand |
| 12 | "Waiting for other players to pass." | hearts-game.js:168, 300 | phase time left | none | once a hand |
| 13 | "No passing this round." | hearts-game.js:65 | meant to be 2 s (`C.hearts.NO_PASS_MESSAGE_DURATION`), really **5 s**: `this` inside the `setTimeout` function is `window` | none | every 4th hand |
| 14 | "Hearts broken!" / "Spades broken!" | hearts:639, spades:331 | default 5 s (measured 5000) | none | once a hand |
| 15 | "Cards will be redealt." / "All players passed. Cards will be redealt." | spades:533, sheepshead:468 | 2 × fold duration | none | rare |
| 16 | "Round complete! Next round starting..." | 5141 (animations mode not "All") | `HAND_OVER_DURATION` 4 s | none | each hand |
| 17 | "Choose a suit. Whoever holds that Ace is your secret partner." | sheepshead:153 | turn | none | per hand |
| 18 | "The Queen of Spades was removed. One of the remaining Queens will become the Old Maid!" | oldmaid:276 | 5 s | none | once a game |
| 19 | "Contract: … by X. Y is dummy." | bridge-game-ui.js:338 | 4 s | none | per hand |
| 20 | "**12 points for your hand.**<br>**Fifteen (5♣10♦):** 2 points<br>…" (up to about 8 lines) | cribbage-game-ui.js:629-637 | DAY, skipPrefix | none | replaced step by step in the show phase |
| 21 | "**Tin Man** wants a rematch. Click **Play Again** within **12 seconds** to join." | 6436-6450 | DAY | none | **rewritten every 1 s** |
| 22 | "Rematch didn't happen. Click **Play again** to find another table." | 6407 | DAY | none | once |
| 23 | "Game is paused. It will resume automatically in **4:59** or when a player clicks **Resume**." | 9364-9390 | DAY | none | **rewritten every 1 s**, up to 5 min |
| 24 | "A player requested to pause the game. 1 of 2 votes needed to pause." | 9443-9451 | 6 s | none | per vote |
| 25 | **Alert:** "Your view of the table is out of sync with the server and is being reset." (red) | 1086-1090 | 8 s | none | rare |
| 26 | **Tip:** "Enjoying the game? Bookmark us with **⌘ + D** or tap ★ in your browser!" | 464 | 8 s | none | once a month |
| 27 | **Notice:** "You're playing an early beta…" (red) | 458 | 8 s | none | per table, beta games only |
| 28 | **Notice:** "Connection problem, reconnecting..." → **Error:** "Connection problem" (red) | 9891-9914 | until it recovers | **Reload game** (red) | escalates after 10 s |

**The turn hint is not in the box.** "Hint: Try the highlighted move." is a **toast** (`showTurnHintNotice` 4102-4114, 6.4 s, `noticeKey:"turnHint"`). It was measured about 30 s into your turn. The "hint" category inside the box is only the prompt text.

---

### 4. How often the box is replaced while it shows

There are three patterns, all at one fixed anchor. `left` and `top` never move, and the box grows right and down.

1. **Swap in place.** Rendering new text while the box shows gives no transition and an instant resize. This happens with:
   - countdown, rematch and pause: once a second
   - "Waiting for X to play." in crazy eights: every ~1.7 s, measured 4365 → 6018 → 7762 → 9489 ms, ending on "Play a card…"
   - the same pattern per turn in cribbage, sheepshead, bridge, gin rummy, rummy, canasta and hand & foot
   - the waiting notice when its buttons change
2. **Hide, then show 2-5 ms later, which blinks.** The game hides at turn stop and the next turn start renders at once. Games: spades (bids), pinochle (`playerTurnStopHandler` 475-477, every stop), euchre:404, twentynine:1294, three-five-eight:390, gin rummy:1934, pinochledd:734. Measured (spades): hide at 7682 and render at 7686, so the old text goes from 1.00 to **0.00 in one frame** and the new one fades in over 160 ms, about every 0.8 s for each bot bid.
3. **Enter from hidden and exit by lifespan.** 160 ms linear opacity each way, with no movement.

**Conclusion for the lab:** a separate **swap** motion for consecutive messages at the same anchor would help. For example, cross-fade the text and move the width and height between sizes. Pattern 2 should join the same path: a hide followed by a show within about one frame to 200 ms should become one swap, not exit plus enter.

The enter and exit must also stop snapping when interrupted. Today the snap comes from inline-final plus cancel. The fix is to read the computed opacity as the start value, or to use persistent WAAPI animations. The countdown and rematch ticks change only the number, so a digit-only change could get a lighter motion than a whole-text swap.

---

### 5. Stacking (measured computed z-index)

- In normal play neither `#mainContainer` (`position:relative`, z auto) nor `#playspace` (z auto, opacity 1, no transform) makes a stacking context. The box (**4800**, `--z-game-table`, pieces.scss:1419) therefore competes directly with the pieces.

**Under the box:**
- cards 3000-3201 (hand 3000 + index, own hand 3200, Layout.js:1461-1464)
- play spot 3099
- deal deck 3098-3139
- a lifted hand gets +400 (Spot.js:623), which stays under 4800
- tutorial Next and the pass spot 3800
- avatars 4000-4002, plates 4001, names and scores 4002
- seat buttons (Hint and Chat) 4003
- timers 4002-4003

**Over the box:**
- **Chat bubbles:** chat spot 8951 (Layout.js:2505), text 7600
- **Game over and hand over:** `.playspace.endModalActive` is z 8900 (base.scss:440-442), so the whole playspace rises above the box. The panel is 9600 and its background 9100. A rematch message in the box therefore sits under the faint game-over wheel.
- **Meld overlay:** playspace 9300 plus a 9299 scrim (base.scss:444-460), so the box goes under the veil.
- **Pills and their panels:** `.chromePill` and `.chromePillRight` are **9975** (TableBar.scss:1540, 1626, 1763), children of `#mainContainer`. The Table panel hangs 8 px under the left pill and covers the box at [16,72].
- **Toast:** `#NoticeContainer` is `position:fixed`, **z 10001** (Notice.scss:3-12), a child of `<body>`. `#Notice` is z auto inside it.

**Toast against the box (measured):**

| Viewport | Toast | Box | Result |
|---|---|---|---|
| Desktop | [159,16,547,48], ends at 64 | top 72 | 8 px gap; the toast covers the N avatar |
| Landscape | [22,8,547,48], ends at 56 | top 48 | **8 px overlap** over the box, and it covers both pills and the N plate (`shot-landscape-hearts-toast.png`) |
| Portrait | [16,8,358,68] | top 176 | the toast sits over the 100 px top ad banner, not the felt; no overlap |

The toast is 16/20 type, padding 14px 26px, radius 20. The container width is the playspace width (864 / 590 / 390).

**Motion references for the lab** (not message-box code):
- **On-table panels** (hand over and game over, `createSpotGroupAnimation` at Table.js 5120-5128 and 6031-6039, `Animation.js:21-26, 180-195`):
  - panel: opacity 0→1, scale .96→1, translateY 8→0, 240 ms, `ease-out-2` = cubic-bezier(.33,1,.68,1)
  - items: 160 ms, staggered 160 ms, scale .96, y 4
  - exit: 160 ms, scale .98, y 6, `ease-in`
- **Big modals** (Modals.scss:67-104): panel 260 ms cubic-bezier(.2,.7,.2,1) from opacity 0, translateY +12px, scale .98; scrim 220 ms `ease-out`; animation off under reduced motion.
- **Toast** (`_wm-notices.scss:73-91`): 260 ms in, 190 ms out, 120 ms linear under reduced motion.
- **Message box:** no reduced-motion rule.

**Evidence files:**
- `/tmp/msgbox-probe/out-*-geometry.json`
- `out-desktop-hearts-lifecycle.json`
- `out-desktop-{spades,crazy-eights}-cadence.json`
- `out-*-hearts-{shotwait,toast}.json`
- `shot-{desktop,landscape,portrait}-hearts-{shotwait,toast}.png`

────────────────────────────────────────

**Question:** How does the table message box work end to end: its lifecycle, geometry per viewport, real messages, how often it is replaced, and its stacking against the other pieces?

**Answer:** *The box fades 160 ms linear each way, swaps text with no motion, and has a confirmed defect: its hide callback never runs.*

The engine writes the final ***inline opacity*** first, so an interrupted fade ***snaps*** to 0 or 1. Bot bidding in spades gives a blink every 0.8 s. Crazy eights swaps text ***in place*** every 1.7 s. The Sequence drops the hide's `cb`, so the box stays ***display:block*** and an expired message can ***come back*** after a tip or error clears.

Measured caps are ***176 / 122 / 119 px*** on desktop, landscape and portrait. At 750×340 a tall notice covers the W avatar. The box sits at z 4800: above cards and plates, below chat bubbles, pills, the end-modal layer and the toast (10001). The toast already overlaps the box by 8 px at 750×340.

**Next step:** In the lab, add a distinct swap motion that also covers a hide followed by a show in the same frame, and show that interruptions do not snap.

---

# Report: toast

# Toast (#Notice) and how it meets the table: research report

Repo root: `/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg`. All paths below are under `worldofcardgames/`, unless marked otherwise.

**Caveat: another session is editing files while this report is written.** `static/js/wocg/Table.js` grew from about 10.2k to 11.1k lines during this session (mtime 11:57). `static/scss/pieces.scss` and `_wocg-tokens.scss` also changed: `.spot-messageBox` left `$wm-token-roots` (now `_wocg-tokens.scss:24`), and the new `_classic-table.scss:86` draws master's box at flag-off. The Table.js line numbers below were re-checked after that change. If they drift again, search by function name.

**How I measured.** A headless Chrome for Testing probe ran from `~/Library/Caches/ms-playwright/chromium-1243`, through the sweep's own `scripts/visual-sweep/lib/browser.mjs`, and closed in a `finally`. It loaded the compiled `static/css/*.css` in `dustData.js` order, with BuloRounded loaded. The harness is in `/tmp/toastprobe/` (`run.mjs`, `frame.html`, `composite.html`). Composites of the real toast drawn over the sweep's table shots are in `/tmp/toastprobe/comp/`: `desk-short.png`, `desk-long.png`, `desk-choose-hint.png`, `land-short.png`, `land-long.png`, `land-choose-hint.png`, `port-short.png`, `port-long.png` and `port-choose-hint.png`. No repo or lab file was touched, and no browser is left running.

---

## 1. Notice.js (`static/js/Notice.js`, 304 lines, no uncommitted changes)

**Constants**
- `DEFAULT_DURATION = 3200` (:10), `IN_DURATION = 260` (:14), `OUT_DURATION = 190` (:15).
- `TYPES = info/success/warning/error` (:16).
- The CSS carries the same 260 and 190 figures (`_wm-notices.scss:78,84`). The two must be kept in step by hand.

**DOM**
- `#NoticeContainer` is created with `display:none` (:34).
- `#Notice.wmNotice.info` carries `role="status"` and `aria-live="polite"` (:38), and never `aria-modal` (comment :35-37, because PageReset reads that attribute).
- Children are `strong.label` (:39) and `span.message.selectable` (:40).
- Both are appended to `<body>` at domready (:43, :295).

**Options**
- `normalizeOptions` (:49-57) accepts a string or an object, defaults the type to info, and defaults the label to "" (:55).
- Other fields are `message`, `messageHtml`, `duration` (a number, or `false` for sticky; no caller uses `false`) and `noticeKey` (free-form, carried to `Notice:hidden`).
- `message` and `messageHtml` both write HTML. YUI `setContent` is `setHTML` (`static/yui3/node-base/node-base.js:239-268`). Notice.js:99-100 only differs in naming.

**The queue: one pending slot, the latest wins**
- `showHandler` (:59-75). Before init it stores the options as pending. If a toast is visible, arriving or leaving, it sets `pendingOptions = options` (this overwrites any earlier pending toast) and calls `hideNotice(showPending)`.
- So a new toast does **not** wait out the old toast's time. The old toast is cut at once (190 ms leave), then the new one arrives.
- Three rapid toasts: the middle one is dropped.

**Show** (`showNotice`, :89-119)
- It calls `updatePosition()` (:97), sets the label and message, sets both nodes to `display:block`, and removes `wmIn` (:103).
- The hide timer is `duration + IN_DURATION` (:105).
- A forced reflow (`offsetWidth`, :112) comes before `addClass("wmIn")` (:113).
- A 260 ms timer then clears `showing` (:114-118).

**Hide** (`hideNotice`, :121-143)
- It removes `wmIn`, and after `OUT_DURATION` it calls `finishHide` (:145-161).
- `finishHide` sets `display:none`, fires `Notice:hidden` with the hidden options (:157), then runs the callback or the pending toast.

**Life cycles** (from the start of the arrival)
- Default toast: the leave starts at 3460 ms and the toast is gone at 3650 ms.
- Turn hint (6400): 6660 and 6850 ms.
- Shutdown and pool toasts (8000): 8260 and 8450 ms.

**Dismiss**
- `notice.on("click", hideHandler)` (:41). `hideHandler` also clears the pending toast (:77-80).
- The cursor is a pointer (`_wm-notices.scss:53`).
- `ModalError.js:170-176` fires `Notice:hide` whenever an error dialog opens.

**`updatePosition`** (:189-196)
- `top` = the menu bar's real bottom (`getTopBarBottom`, :256-267). It returns 0 when `#menuBarContainer` is `display:none` or `visibility:hidden`, or when `rect.bottom <= 0` (the bar is scrolled away).
- `paddingTop` = `safeAreaTop()` + the gutter (:198-215). `Y.wocg.safeAreaTop` reads `--safe-area-inset-top` (`static/js/wocg.js:917-922`). `Y.wocg.playspaceGutter` is 16, or 8 when the playspace is compact, or the side-layout gutter (`wocg.js:752-755`).
- `left` is 0. `width` = `clientWidth - rightRailAdWidth()` (:217-243 → `wocg.js:762-787`). The rail width is 0 for supporters, 0 for the portrait top banner (`#ad.mobile`/`.mobileTop`) and 0 when the ad is hidden.
- It runs on every show, on `window:resized` (with a second pass after 250 ms, :273-281), on `ad:removed` and on `theme:changed` (:296-298).
- **It does not run when a table is created or left**, and not on scroll. The position is frozen at show time (see §5).

**Compact class**
- `.compact` follows `Y.wocg.isPlayspaceCompact()` (:245-254; `wocg.js:738-750`, breakpoints 640/480 at `wocg.js:13-16`).
- **It has no visible effect today.** The legacy `#Notice.compact` gives 16/20 (`Notice.scss:35-38`), and `#Notice.wmNotice.compact` also forces 16/20 (`_wm-notices.scss:97-100`).

**Public API and events**
- `Y.Notice = {show, hide, isVisible, getCurrentOptions}` (:286-293).
- Events: `Notice:show`, `Notice:hide` and `Notice:hidden`.
- Table listens to `Notice:hidden` (`Table.js:11017` → `noticeHiddenHandler` :4154-4158, which calls `clearTurnHint()` when `noticeKey === "turnHint"`).
- **Consequence:** any other toast that replaces a turn hint also wipes the hint's card arrows.

## 2. Styles and stacking

**Legacy `static/scss/Notice.scss`** (still loaded; `Notice.css` is in the `dustData.js:16` manifest)
- `#NoticeContainer` (:3-12): `position:fixed; top:0; left:0; z-index:var(--z-auth); width:100%; padding-top:calc(safe-area + gutter); pointer-events:none; box-sizing:border-box`. JS overwrites top, padding and width inline.
- `#Notice` (:14-47): `width:fit-content; margin:0 auto` (centred), `min-height:32px`, `box-sizing:border-box`, `pointer-events:auto`, `overflow-wrap:break-word`, `.message{display:inline}`, `.label{bold; margin-right:4}`.
- The wm sheet overrides its `text-align:center`, radius, paper and padding.

**`static/scss/_wm-notices.scss`** (imported at `Modals.scss:824`; Modals.css comes later in the manifest)
- `.wmNotice` frame at the lobby (:31-34): ring `0 0 0 1px var(--line)` (#d2cfca, outside), drop `var(--lift), 0 8px 20px rgba(0,0,0,.18)`.
- At a table, `body[data-table="true"] .wmNotice` (:36-39): ring `inset 0 0 0 1px var(--color-table-edge)` (#393939 under the token roots, `_wocg-tokens.scss` block), drop `0 0 8px 0 rgba(0,0,0,.24)`. The probe confirmed this is the same computed box-shadow as the message box's `--shadow-low`.
- `#Notice.wmNotice` (:52-79):
  - `max-width:min(640px, calc(100% - 32px))`, `padding:14px 26px`, `border-radius:var(--radius-panel)` (20px, `_wm-tokens.scss:8`), `corner-shape:squircle`.
  - Paper `--paper-band` #f4eee5, font `--font-ui`, size `--type-body` 16 on `--type-body-line` 20 (`_wm-tokens.scss:52-53`), `text-align:left`.
  - Rest state: `opacity:0; transform:translateY(-10px) scale(.96); transform-origin:center top`. Leave: 190 ms `cubic-bezier(.32,0,.67,0)`.
  - `.wmIn` (:81-85): `opacity:1; transform:none` over 260 ms `cubic-bezier(.22,1,.36,1)`.
  - Reduced motion (:87-93): no transform, opacity 120 ms linear.
- **The types have no style.** No rule anywhere distinguishes info, success, warning or error. `GAME-MODALS-PORT.md:25` and `DESIGN-GUIDE.md:717` (2026-09-09) say the toast "keeps a coloured left edge for warning, success and error". That edge is not built: `git log` shows no such rule in `_wm-notices.scss` or `Notice.scss`.
- **The toast is not gated on `body.wm`.** `.wmNotice` is a token root (`_wocg-tokens.scss:24`, `_wm-tokens.scss:6`). `FLAG-OFF-PARITY.md:92,136` records D3 "Toast ... SHARED (Holger 2026-09-23)". Any lab change to Notice.js or `_wm-notices.scss` reaches flag-off unless it is gated.

**z-index** (`static/scss/_variables.scss:176-186`)
- The toast container is fixed at `--z-auth` **10001**.
- The message box is `position:absolute` inside `#mainContainer` at `--z-game-table` **4800** (`pieces.scss:1420`).
- Chrome pills and their panels: `.chromePill` at `--z-panel` 9975 (`TableBar.scss:1537-1541`).
- Score board: `#scoreBoardWrapper` at 3999 (`base.scss:492-500`).
- Others: chat bubbles 7600, bars 7000, `#ad` 9200 (`AdWidget.scss:12`; 9598 under `endModalActive`, :409-410), `.wmModal` 9999 and its backdrop 9996.
- Ties at 10001 (`.wmTopmost`, `Modals.scss:48`; `ModalError.scss:7`; BoxForm auth panels) go by DOM order. The container is appended at domready, so later dialogs paint over it.
- The unused `--z-notice` 9205 tier is read only by `ModalTablePreview.scss:111`.
- **Result: the toast paints above every table piece, the pills, the rail and every normal modal with its scrim.** Its box takes pointer events, so a toast over a pill or an avatar eats the first tap, and that tap dismisses it.

## 3. Every caller (80 call sites; `static/js/…`)

"Table" means the toast can fire while a table is on screen. Duration is 3200 unless noted.

| Call site | Text | Type | Table |
|---|---|---|---|
| wocg/Table.js:4127 (`showTurnHintNotice` :4123) | label "Hint:" + server hint in HTML, e.g. "Pass your aces and trump, but keep your pinochle." plus " Hints can be disabled under settings." the first time (:4215-4221). 6400 ms (:22), `noticeKey:"turnHint"` | info | **YES** |
| wocg/Table.js:626 | "Connecting to server, please wait..." (Watch while disconnected) | info | YES |
| wocg/Table.js:674 | "The table you were watching has closed." | info | YES (the view then goes to the lobby) |
| wocg/Table.js:681 | "This table can't be watched." / "…no longer available to watch." / "…maximum number of spectators." | warning | YES |
| wocg/Table.js:4946 | "No available seats." (the message box's Invite players button) | warning | **YES** |
| wocg/Table.js:10254 | "Game was just paused. You can resume in N second(s)." | warning | YES |
| wocg/TableBar.js:175 | "Can't chat with bots." (the chat seat button, :1024-1039) | warning | YES |
| wocg/TableBar.js:783, :1194 | "Game can't be paused." | warning | YES |
| wocg/TableBar.js:1170 | "Comment has been flagged and will be manually reviewed." | success | YES |
| wocg/TableBar.js:1203 | "Game will pause if all players agree. Use Resume to cancel your request." | info | **YES** |
| wocg/TableBar.js:1342, :1378, :1398 | Multiplayer blocked: "You're currently banned from multiplayer games." / the practice message / "Multiplayer is disabled on VPN or proxy connections. Turn off your VPN to play with other people." / "The server may be down. Please try again in a few minutes." | warning | YES (Play dropdown) |
| wocg/TableBar.js:1349 | "Finish a {Game} practice game against bots before joining a multiplayer table." (`User.js:3982-3986`) | warning | YES |
| wocg/TableBar.js:1452 | "No hint available right now." (the Hint seat button, :1042-1046) | info | YES |
| ModalInvitePlayers.js:423, :430, :434, :455 | "No available seats." / "Can't invite more players. Limit reached." / the server's text or "Could not send invite." | warn / warn / warn / error | YES (over the modal) |
| ModalGameOptions.js:481 | "You have to select at least one option for number of players." | warning | YES (Host table from the Play dropdown) |
| wocg/User.js:786, :794, :800, :806 | "You're not at a table." / "No available seats." ×2 / the limit message (Friends panel) | warning | YES |
| wocg/User.js:1589, :2153 | Invite failure / "Failed to send message." or the server's text | error | YES (pill panels) |
| wocg/User.js:3810 | "You were signed out because your account signed in somewhere else." (640 ms after init, plus a sign-in dialog) | warning | Possible at page load |
| wocg/User.js:3860, :3865 | "Your email is now X." / the server's error | success / error | Rarely (the confirm-link page) |
| wocg/ProfileBox.js:476, :489, :548, :818 | The server's message / "Could not load subscription page. Please try again." | error | YES (Settings at a table) |
| AdWidget.js:735, :743 | "Subscription link is not configured yet." / "Login or register to hide ads." | error / warn | YES (the rail's Hide ads) |
| wocg/PageReset.js:495 via :587 and :719 | "Refreshing..." / "Loading the next game..." (the playspace fades, :492-507) | info | **YES** |
| wocg/PageReset.js:1214 | "Refresh complete. Play can continue." (on `table:created` after a reset load, :1186-1214; muted under 2 s, :57) | success | **YES (table load)** |
| wocg/ShutdownNotice.js:52 | "The server goes down for maintenance {in about N minutes \| in less than a minute \| …}. It comes straight back." 8000 ms (:22). Said again after a disconnect, because `disconnectedHandler` clears the time (:66-74) | warning | **YES, any time** |
| wocg/PoolInactiveNotice.js:43 | "Update ready. Reload to apply." (or the server's text). 8000 ms. Muted while a game is in progress (:26-39) | info | YES between games, game over, tutorial |
| wocg/StandingTables.js:237 | The `RESULT_MESSAGES` (:44-53) or "That didn't go through. Please try again." (from the game-over "Keep this table") | info if "exists", else warning | YES |
| wocg/FooterBar.js:242 | "Opening your email app. If nothing happens, email holger@worldofcardgames.com." (from `GameRating.js:467` at game over, and `.mailToLink`) | info | YES |
| wocg/TableListingsBar.js:1147, :1155, :130 | Connecting / blocked / practice (Browse tables at a table) | info / warn / warn | YES |
| ModalTablePreview.js:439 | "Someone else took that seat. You're still first in line for the next one." | info | While watching a table (the queue survives a spectator `table.create`, :558-566) |
| ModalTablePreview.js:446-454 | "Your seat offer expired." / "The table you were waiting on is gone." / "You can't join the waiting list for that table." / "That table's waiting list is full." / "Your place in the waiting list was lost." | warning | While watching |
| wocg/GameSelector.js:379 (`requireConnection` :377-383) | "Connecting to server, please wait..." | info | YES (Host, Join private and Ranked from the table's Play dropdown: :569, :771, :782) |
| wocg/GameSelector.js:576, :773 | Ranked blocked (:426-445, e.g. "You must complete 10 games to play ranked games.") / host blocked | warning | YES |
| wocg/GameSelector.js:394, :468, :654 | Practice required or multiplayer blocked, **and a solo bots table starts on the same click** (:463-473, :648-657) | warning | **Carries into the new table** |
| wocg/GameSelector.js:456 | "You can't start a new game right now, the server is shutting down soon." | warning | Lobby |
| wocg/GameSelector.js:240, :248 | Ad-block gate subscribe messages | info / warn | At game start |
| wocg/GameSelectors.js:455 | "You can press <b>Command + D</b> or tap ★ in your browser to bookmark World of Card Games." (in `gameSelectorsShowHandler` :318; desktop, 3 or more games, once a year) | info | During the table-to-lobby switch |
| wocg/LobbyWidgets.js:361, 369, 380, 465, 696, 878, 922, 1178, 1361, 1961, 2664 | Connecting / blocked / practice | — | Lobby only |
| wocg/LobbyWidgets.js:2255 | "Connecting..." (`showDealModal`, reachable from the account menu) | info | Possible |
| wocg/FrontpageTables.js:623, 631, 653, 1240 | Connecting / blocked / practice | — | Lobby only |

No caller exists in `static/js/wocg/game/*` or in the dust inline scripts.

**Longest texts at a table:**
- "Multiplayer is disabled on VPN or proxy connections. Turn off your VPN to play with other people." (97 characters).
- "Finish a Double Deck Pinochle practice game against bots before joining a multiplayer table." (about 93).
- The first-time pinochle hint (about 90 with its label).

## 4. Where the toast lands at a table

**The menu bar is hidden at a table under the redesign.**
- `body.wm[data-table='true'] #menuBarContainer {display:none !important}` (`static/scss/MenuBar.scss:21-23`). `Y.wocg.userBarHeight()` returns 0 (`wocg.js:965-969`).
- So `getTopBarBottom()` is 0, and the toast's top = safe area + gutter: **y=16 on desktop, y=8 on phones** (Safari in the browser reports 0 for the safe area). The native app adds its top inset.
- At flag-off the classic 32px bar stays, so the top is 48.
- The toast is centred in `viewport − rail`, which is the playspace's own column. So it is always centred over the top (N) player.

**Table geometry, measured on the sweep shots** (hearts, 4 seats, `scripts/visual-sweep/out/latest/shots`, CSS px, x..x / y..y)

| | Desktop 1200×800 (rail 336) | iPhone landscape 750×340 (rail 160) | iPhone portrait 390×664 (100px top banner ad) |
|---|---|---|---|
| Left pill | 16..136 / 16..56 (three 40px cells) | 8..104 / 8..40 | 8..104 / 108..140 |
| Right pill | 728..848 / 16..56 | 486..582 / 8..40 | 286..382 / 108..140 |
| N plate | 232..632 / 72..112 | 154..437 / 44..76 | 151..239 / 176..208 |
| N avatar | about 390..474 / 18..99 | about 272..320 / 22..70 | above the plate, about 110..175 |
| Message box (row) | 16..216 / 72..168 (3-line countdown) | 8..146 / 44..114 | 8..144 / 176..246 |
| Score board | 743..848 / 72..130 | 471..582 / 44..88 | 271..382 / 176..220 |
| Free space under the box to the W hand in play | box bottom 142, W fan top 194 (**about 52px**) | about 96 to 106 (**about 10px**) | 226 to 293 (about 67px) |

**Toast boxes measured in Chrome** (x, y, w, h)

| Text | 1200×800 | 1440×900 | 1024×768 | 750×340 | 390×664 |
|---|---|---|---|---|---|
| "The table you were watching has closed." | 276,16,312,48 | 396,16,312,48 | 188,16,312,48 | 139,8,312,48 | 39,8,312,48 |
| "No hint available right now." | 317,16,230,48 | — | — | 180,8,230,48 | 80,8,230,48 |
| "Game will pause if all players agree…" | 174,16,516,48 | 294,16,516,48 | 86,16,516,48 | 37,8,516,48 | 16,8,358,68 (2 lines) |
| Shutdown line | 137,16,591,48 | 257,16,591,48 | 49,16,591,48 | 16,8,558,68 | 16,8,358,68 |
| VPN line / long hint / DD pinochle practice | 112,16,640,68 | 232,16,640,68 | 24,16,640,68 | 16,8,558,68 | 16,8,358,68 (VPN: 88, 3 lines) |
| "Hint: Pass the Q♠ and high hearts. Hints can be disabled…" | 171,16,521,48 | — | — | 34,8,521,48 | 16,8,358,68 |

**What the toast covers**
- **Desktop 1200, short toast:** the N avatar's head (y 18..64), with 8px clear above the N plate. It misses both pills. In play it also covers the N hand's card backs (the fan runs y 0..125).
- **Desktop 1200, long toast (2 lines, 16..84):**
  - 24px of the left pill's Play cell and 24px of the right pill's Activity cell.
  - The top 12px of the N plate.
  - The top 12px of the message box (x 112..216).
  - A sliver of the score board (x 743..752, y 72..84).
  - See `desk-long.png`.
- **1440×900:** the long toast covers only the N plate's top 12px. The pills are clear (the right pill is at 968..1088).
- **1024×768** (derived; pills by the same gutter rule): the long toast (24..664) covers nearly all of both pills (16..136 and 552..672), plus the top 12px of the N plate, the message box and the score board.
- **Landscape phone, short toast (8..56):** the top 12px of the **whole N plate** (154..437), the N "…" chat bubble (164..191 / 24..40), the N avatar and a 6×12 corner of the message box (`land-short.png`).
- **Landscape phone, long toast (8..76):** cells 1 to 3 of the left pill (from x 16), right-pill cells up to x 574, the **entire N plate**, the top 32px of the message box and the top 32px of the score board (`land-long.png`, `land-choose-hint.png`).
- **Portrait phone with ads:** the toast lands **on the 100px top banner ad** (`#ad.mobileTop` at z 9200, `AdWidget.scss:211-216`; banner size from `wocg.js:624-625`). `getTopBarBottom` ignores the banner. This may be an ad-obscuring policy problem; see `APS-READINESS.md`. Screenshot: `port-long.png`.
- **Portrait phone without ads** (supporter; derived by shifting 100px): the pills sit at 8..40.
  - The short toast (39..351) covers left-pill cells 2 and 3 and right-pill cells 1 and 2.
  - 2 lines (8..76) cover both pills and the N avatar, and reach the N plate row (76).
  - 3 lines (8..96) cover the top 20px of the N plate, the message box and the score board.

## 5. Real collisions between the toast and the message box

The message box's own timing:
- `renderMessage` fades in over 160 ms linear (`Table.js:3104-3183`, transition :3169-3176, lifespan timer :3180).
- `hideMessage` fades out over 160 ms (:3191-3230).
- Delayed prompts appear at `min(5 s, duration − 10 s)` (:3047-3052).

1. **Turn hint toast over the turn or phase prompt.** This is the most frequent case. The prompt ("Select 3 cards to pass left.") is up from 5 s.
   - The auto hint fires at `hintDuration − 10 s + 1 s` (`Table.js:4168-4186`, called from :3641 and :3847).
   - Solo table: `SOLO_GAME_HINT_DELAY` 30 s (`shared/C.js:97`; `node-venue/Table.js:786-788`), so both boxes are up from 30.0 s to 36.9 s.
   - Multiplayer: 2 s after the turn clock appears (`MULTIPLAYER_TURN_HINT_DELAY`, `node-venue/Table.js:22, 790-793`), so both stay up until the turn ends.
   - The Hint seat button (`TableBar.js:1042-1046, 1448-1454`) shows the hint or "No hint available right now." at any time.
   - Both are "what to do" channels: the message box also carries `category:"hint"` prompts (:3025-3031).
   - The toast sits top-centre while the hint's arrows sit on your hand at the bottom.
   - Any other toast replaces the hint and clears its arrows (`Notice:hidden` → :4154-4158).
   - Composites: `desk-choose-hint.png`, `land-choose-hint.png`.
2. **Pause.**
   - The Pause click fires the toast "Game will pause if all players agree…" (`TableBar.js:1200-1206`). In the same second the server's vote makes the box say "You requested to pause the game. 1 of N votes needed to pause." for 6 s (`Table.js:10366-10374`). The two say the same thing for about 3.4 s.
   - Resume during the cooldown fires the toast (:10248-10256) while the box holds "Game is paused. It will resume automatically…" (:10288, :10409, `base.DAY`).
3. **A message with buttons.**
   - The waiting message "Table #N starts when full." carries **Start with bots / Invite players** (`Table.js:1611-1623`, `base.DAY`).
   - Invite players on a table that just filled fires "No available seats." (:4943-4949). The invite modal's toasts (`ModalInvitePlayers.js:423-455`) and the Friends-panel invite toasts (`User.js:786-806, 1589`) also fire while this box is up.
   - "Can't chat with bots." also appears during a bots table's prompts.
4. **Connection.**
   - `showTableError("Lost internet")` puts "**Notice:** Connection problem, reconnecting..." in the box, and it later becomes **Error** with a Reload game button (`Table.js:10797-10830`).
   - If the player then taps Browse, Host, Join private or Ranked, the toast says "Connecting to server, please wait..." (`TableListingsBar.js:1146-1148`, `GameSelector.js:377-383`).
   - PageReset's "Refreshing..." fades `#playspace` only (`PageReset.js:503-505`). The message box lives in `#mainContainer`, outside the playspace (`Table.js:1287-1290`), so it stays visible under the toast.
   - **Correction to the brief:** no "Connecting to server" toast fires by itself at table load. Every such toast answers a user action made while disconnected.
5. **Table load.**
   - (a) "Refresh complete. Play can continue." fires on `table:created` after a reset (`PageReset.js:1186-1214`), just as the resynced prompt or countdown renders.
   - (b) Practice or multiplayer-blocked toast plus a solo table from one click (`GameSelector.js:463-473, 648-657`). The toast was placed for the lobby, at the 56px wm bar bottom (`_wm-chrome.scss:19-21`) + 16, so y=72. `updatePosition` never re-runs at table create, so for up to 3.46 s the toast floats **on the table's top row at y≈72**, the same row as the "Table is full. Game will start in N seconds." box and the N plate.
   - The reverse case: "The table you were watching has closed." (placed at y=16 with no bar) stays at 16 over the returning lobby's 56px menu bar.
   - (c) "You were signed out because…" (`User.js:3808-3812`), 640 ms after init.
   - (d) After a reconnect, the maintenance toast (8 s) arrives again while "Connection problem" clears.
6. **Game over and between games:** StandingTables (`:237`), FooterBar mailTo (`:242`) and PoolInactive (8 s).

## 6. Every visual difference between the two boxes

Measured under body.wm at a table in Chrome.

| Property | Toast `#Notice.wmNotice` | Message box `.spot-messageBox` |
|---|---|---|
| Paper | `--paper-band` #f4eee5 (`_wm-notices.scss:58`) | Same (`pieces.scss:1407`). Error variant `.resync` uses `--plate-red` (:1440-1444) |
| Ring and shadow on felt | inset 1px #393939 + `0 0 8px rgba(0,0,0,.24)` (`_wm-notices.scss:36-39`) | `--shadow-low`, **the same computed value** (`pieces.scss:1408`, `_wocg-tokens.scss` `--shadow-low`) |
| Ring off the felt | outside 1px `--line` + lift + `0 8px 20px .18` (:31-34) | n/a |
| Radius | 20px `--radius-panel` everywhere (:56) | `--radius-lg` (`pieces.scss:1410`): 16 desktop and 12 phone in Chrome (`_variables.scss:193-199, 231-239`); **8 and 6 in Safari/iOS** (`_variables.scss:43, 211-219`). Worst iPhone mismatch: 20 against 6 |
| Corner shape | squircle (:57) | squircle through the global rule (`base.scss:254-263`) |
| Padding | 14px 26px everywhere (:55) | 12 (`pieces.scss:1412`); **8 when compact** (:1428-1429) |
| Type | 16/20 everywhere, `.compact` too (:61-62, :97-100) | 16/20 under wm (`pieces.scss:2562-2567`); **14/18 on `playspace-small`**, both phone orientations (:2569-2574). Master is 20/24 (:1421-1422) |
| One-line height | 48 | 44 on desktop, 34 on a phone |
| Font and ink | `--font-ui` BuloRounded, `--ink` #141414 | Same (body font `base.scss:29`) |
| Width | fit-content, centred, ≤ min(640, container − 32) (:54; `Notice.scss:15-19`); min-height 32 | left-anchored, min 80 / max 320 (`pieces.scss:1415-1416`), 160 on a small portrait (:1434-1436), JS cap short of the nearest top plate (`Table.js:1298-1357`, `narrowCap` under 140, short button words `pieces.scss:1471`). Actual: 200 desktop, 138 landscape, 136 portrait |
| Position | fixed to the viewport, top-centre, `pointer-events` on the box | absolute in `#mainContainer` at the playspace's left + gutter, on the top player's row (`topChromeRowTop` `Table.js:173-177`; `Layout.js:774-794`) |
| z | 10001 | 4800 |
| Label | `.label` bold with 4px margin, hidden when empty (:103-109); only "Hint:" uses it | `<strong>Notice:</strong>` / `Error:` prefix in the `.resync` variant (`Table.js` renderMessage prefix branch) |
| Type colours | none (the planned edge is not built) | normal paper, or red `.resync` |
| Motion | 260 ms in on `(.22,1,.36,1)` with Y −10 and scale .96; 190 ms out on `(.32,0,.67,0)`; reduced-motion branch | 160 ms linear opacity (Y.Transition), **no reduced-motion branch**, text swapped with no animation |
| Interaction | the whole box dismisses on click; text selectable (`.selectable`) | buttons inside; `pointerEvents` toggled (`Table.js:2960-2964`) |
| Accessibility | `role=status`, `aria-live=polite` | none |

**Layout facts for the lab**
- The message box's column is only 136-200px wide. A toast moved into that slot with its current 26px sides leaves 84-148px for text, so "The table you were watching has closed." would take 3 or 4 lines on a phone.
- "Below the message box" leaves about 52px on desktop and **about 10px on a landscape phone** before the W hand.
- `GAME-CHROME-PORT.md:844-866` already records a tall notice running into the W fan at 1024×768.

────────────────────────────────────────

**Question:** How does the toast work, and how does it meet the table's message box at a table?

**Answer:** *At a table the toast sits top-centre over the top player, above everything, and several real situations put it on screen with the message box.*

The ***menu bar is hidden*** at a table, so the toast sits at y=16 on desktop and y=8 on a phone. It is ***frozen at show time***: it does not move when a table is created or left. It covers the N avatar, the top pills and part of the N plate, and on a portrait phone it covers the ***top banner ad***. The most frequent overlaps are the turn hint, the pause flow, and the practice-blocked toast that carries into a new solo table. The type colours are not built. The toast is ***shared at flag-off***, so any lab change reaches players without the flag unless it is gated.

---

# Report: motion

# Motion vocabulary report: message box and toast lab

**Paths.** All paths are relative to the repo root `/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/`.
- `js/` means `worldofcardgames/static/js/`.
- `scss/` means `worldofcardgames/static/scss/`.
- The labs folder is `/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3/`.

**Caveat about line numbers.** Another session is editing three files while I work: `js/wocg/Table.js`, `scss/pieces.scss` and `scss/base.scss` (mtime 11:56–11:57 today). The work is flag-off parity: `showHandOverModalClassic` is at Table.js:5577 and `showGameOverModalClassic` at :6785. The Table.js line numbers below come from a snapshot at 11:59, and lines moved between my greps. Search by function name when a number is off. The message box logic did not change during the session.

---

## 0. Findings in short

1. The site has **five named curves**. The drawn guide names them EASE, SETTLE, SHARP, ENTER and INK (the `MO` object at the top of `Design/WoCG-3/design-guide-parts/13-motion.html`). The table's JS engine adds its own named easings (`js/Transition.js:13-28`).
2. Today the **message box is a plain linear fade**: 160ms each way, no travel (Table.js:3167-3177 and :3215-3230). It is the only redesigned surface that does not use the SETTLE / SHARP pair.
3. The message box ignores `prefers-reduced-motion`, the Animations setting and `?animationSpeed`. Only the debug param `?animSpeed` changes its speed.
4. **A bug that is also on master.** The callback of `hideMessage` never runs. After the first hide, the box stays `display:block` at opacity 0, and `currentMessageText` is not cleared. Details in section 5.
5. **The toast and the ModalShell dialogs are shared with flag-off** (FLAG-OFF-PARITY.md:92-94, :134-138). The message box look (T4, :50) and the game over, hand over and meld panels (T10, T11) go behind the flag.
6. Each of Holger's ideas already has a precedent on the site:
   - "Moving in from the side" matches the **side swap** (F3). The box stands on the left gutter.
   - "What the big modals do" matches the **modal rise** (F4).
   - "What the on-table game modals do" matches the **table panel rise** (F6). The chat bubble is its smallest member.
   - "The toast" matches the **drop from an edge** (F1).
   - A plain fade that belongs to the design is **ink takes** (F11).
   - "The toast below the box" can use **feed** (F13) or **FLIP** (F17).

---

## 1. Curves and tokens

| Name (drawn guide) | Curve | Durations in use | Meaning | Where |
|---|---|---|---|---|
| EASE (thumb) | `cubic-bezier(.645,.045,.355,1)` | 220ms; opacity part 110ms linear | a thumb that travels, a box that changes height, the checkbox tick | `scss/_wm-tokens.scss:68-69` (`--motion-speed`, `--motion-ease`); `scss/_wm-shared.scss:688-689` (`--bar-speed`, `--bar-ease`); `scss/_wm-leaderboard.scss:34-35`; `scss/_wm-dialogs.scss:174,192,225` |
| SETTLE (arrive) | `cubic-bezier(.22,1,.36,1)` | 260ms, often after a 150ms wait; tooltip transform 220; roll 220; mark 260; seat avatar 320; dropup 400; FLIP 300 | something that arrives and settles | `scss/_wm-notices.scss:84`; `scss/CustomTooltip.scss:47`; `js/wocg/FrontpageTables.js:36-46`; `js/wocg/LobbyTableSwitch.js:47`; `scss/_wm-settings.scss:395` |
| SHARP (leave) | `cubic-bezier(.32,0,.67,0)` | 190ms | something that leaves | `scss/_wm-notices.scss:78`; `FrontpageTables.js:38`; `LobbyTableSwitch.js:48`; `scss/_fp-hero.scss:259,294`. It is identical to the engine's `ease-in-2` (`js/Transition.js:18`). |
| ENTER (panel or page) | `cubic-bezier(.2,.7,.2,1)` | 260ms modal panel; 240ms settings page | a panel or a page that enters | `scss/Modals.scss:72`; `scss/_wm-settings.scss:72` |
| INK | `cubic-bezier(.25,.46,.45,.94)` | 340 (the capsule 520), seam sweep 400, puff 420 | reveal by opacity plus blur, no travel | `scss/_fp-reveal.scss:73,85`; `js/wocg/FrontpageSeams.js:502`; `LobbyTableSwitch.js:49,496` |

**Other curves in use**
- CSS keyword `ease-out`: the modal scrim over 220ms (`Modals.scss:68`), the settings page as it leaves over 200ms (`_wm-settings.scss:67`), the overlay scrollbar over 200ms (`Modals.scss:128`).
- `linear`: the message box (160ms), the piece fade (320ms, `js/wocg/Piece.js:666-677`, `shared/C.js:185`), the scoreboard (160ms, `Table.js` `showScoreboard` :1411), the tooltip opacity (.1s).
- The JS engine's named easings (`js/Transition.js:13-28`):

| Easing | Curve | Note |
|---|---|---|
| `ease-in` | (.11,0,.5,0) | table panel exit |
| `ease-out` | (.5,1,.89,1) | |
| `ease-in-out` | (.45,0,.55,1) | deal and play |
| `ease-in-2` | (.32,0,.67,0) | same as SHARP |
| `ease-out-2` | (.33,1,.68,1) | the **default** when no easing is given (`Transition.js:236`); the table's "settle" |
| `ease-in-out-2` | (.65,0,.35,1) | close to EASE |
| `ease-in-3`, `ease-out-3`, `ease-in-out-3` | (.5,0,.75,0), (.25,1,.5,1), (.76,0,.24,1) | |
| `ease-in-out-1-4` | (.5,0,.5,1) | |
| `ease-cup` | (.333,0,.667,1) | the game over title |

- Legacy tokens: `--duration-micro` 80ms and `--duration-normal` 160ms (`scss/_variables.scss:188-190`). `_wocg-tokens.scss` has no motion token.
- The guide's summaries: DESIGN-GUIDE.md:60 (cheat sheet) and :586-603 (section 9 Motion).

**Duration ladder:** 24 (colour) · 80 (press, tooltip out) · 110 · 120 (reduced-motion fallback) · 150 (wait before an arrival) · 160 (legacy fade) · 190 · 200 · 220 · 240 · 260 · 320 · 340 · 400 · 520.

---

## 2. Big modals (`.wmModal`)

**Open** (`ModalShell.show`, `js/wocg/ModalShell.js:598-623`)
- The root gets `.wmOpen` and `display:block` at opacity 1 at once (:608-620). CSS runs the entrance.
- **Scrim:** `wmScrimIn` over 220ms, `ease-out`, fill `both`. The background goes from rgba(0,0,0,0) to `--scrim` (.48). `backdrop-filter` goes from blur(0) to blur(4px) (`Modals.scss:67-69`, :75-87; tokens `_wm-tokens.scss:22-23`).
- **Panel:** `wmPanelIn` over 260ms, ENTER, fill `both`.
  - Opacity 0→1.
  - Transform `translate(-50%, calc(-50% + 12px)) scale(.98)` → `translate(-50%,-50%) scale(1)` (`Modals.scss:71-73`, :89-99).
  - No `transform-origin` is set, so the panel scales from its centre. The panel centres itself with the same transform (:141-152).
- **Reduced motion:** both animations are `none` (`Modals.scss:101-104`). `.modalInstant` also skips them (the instant path of ProfileBox, `js/wocg/ProfileBox.js:2359-2361`).
- **Phone (≤560px):** the same keyframes, with the panel 16px lower. It stays centred, not a bottom sheet, since 22 Sep (`Modals.scss:790-808`). This replaces the "rises 16px from the edge" entry of 14 Sep (DESIGN-GUIDE.md:739).

**Close** (`ModalShell.close`, `ModalShell.js:625-650`)
- The code adds `.modalClosing`, but no wm rule uses it.
- `Y.Transition` then fades the **whole root** from opacity 1 to 0 over 160ms (:640-648). No easing is given, so it gets `ease-out-2` (`Transition.js:236`).
- Nothing travels. The scrim and the panel fade together.
- Because JS runs the close, it has no reduced-motion branch, and `?animSpeed` changes it.

**Settings box.** It opens the same way (`ProfileBox.js:2354-2366`). It closes with `Y.Transition` opacity over 160ms (`ProfileBox.js:2408`).

**Auth boxes** (`.wmAuth`; `web/dust/common/auth_modals.dust:20,95`, `password_modals.dust:10,41`). They never get `.wmOpen`. The whole layer fades with `opacity var(--duration-normal)` (160ms, `ease-in-out`) (`scss/_wm-auth.scss:21-32`). No panel rise.

**Who uses ModalShell** (search for `ModalShell(` in `js/`): ModalConfirm, ModalError, ModalInput, ModalProgress, ModalBlockReason, ModalGameOptions, ModalInvitePlayers, ModalTablePreview, ModalLegalConsentScreen, ModalPlayerProfile, ProfileBox, StatsBox, LobbyWidgets and CardsPrompt. CardsPrompt is a big modal on the table: it opens at a player's first deal against bots (`js/wocg/CardsPrompt.js:3-6`, :67).

**Legacy entrance, still live for old markup and unchanged from master** (`scss/ModalEntrance.scss`)
- Enter: `modalPanelEnter` over 220ms `cubic-bezier(.16,1,.3,1)`. Opacity reaches 1 at 32%. Transform goes from `translate3d(0,20px,0) scale(.98)` to none. Origin `center calc(50% - 24px)` (:1-24, :151-165).
- Exit: 160ms `cubic-bezier(.4,0,1,1)` to +12px and .98 (:32-51, :167-182).
- Reduced motion: :99-148.
- GAME-MODALS-PORT.md:164 lists what still depends on it: the FAQ box, the table listings, ModalRules and ModalWebview.

**Inside the modal**
- **Tray thumb.** `left`, `width`, `top` and `height` travel over 220ms EASE; opacity takes 110ms linear (`Modals.scss:584-604`). The white ink copy moves its `clip-path` over 220 EASE (:610-621). The dividers fade over 220 EASE (:665). The first placement does not slide (`.wmStill`, :630-631; `ModalShell.js:160-167`, :193-198). `placeTrayThumb` divides out the panel's .98 entrance scale (`ModalShell.js:170-181`).
- **Settings page turn** (`ProfileBox.js:211-301`):
  1. The old page leaves: opacity to 0 over 200ms `ease-out`, while the thumb travels (`_wm-settings.scss:65-68`).
  2. After `thumbTravelMs()` (this reads `--motion-speed`, 220; `ProfileBox.js:380-388`), the box height moves over 220 EASE (`Modals.scss:165`; `growBox` at `ProfileBox.js:353-376`, which waits 220+40).
  3. Meanwhile the new page is held at opacity .001 with `will-change` (`_wm-settings.scss:60-63`).
  4. Then `wmPageRise` runs over 240ms ENTER: opacity 0→1 and translateY(10px)→none (:71-86; `PAGE_ENTER_MS` at `ProfileBox.js:35`).
  5. Reduced motion removes all of this (:88-96).
- **Mark pop** (`wmMarkIn`). Scale .4→1 and opacity 0→1 over 260ms SETTLE, with no overshoot. It runs only when the pick changed (`_wm-settings.scss:382-396`; `js/wocg/MenuBar.js:274-279`). Reduced motion: none (:398-400).
- **Checkbox** (`_wm-dialogs.scss:158-231`; decision DESIGN-GUIDE.md:746).
  - Pick: the fill lands at once, then the tick stroke draws over 220 EASE after 40ms.
  - Unpick: the fill and the tick fade together over 220 EASE, and the tick shrinks to .4 as it goes.
  - Press: the box alone scales to .9 over 80ms `ease-out`.
- **Scrollbar.** Opacity over 200ms `ease-out`; it hides 900ms after the scroll stops (`Modals.scss:110-139`; `ModalShell.js:249-257`).
- **Waiting bar.** translateX from -100% to 260% over 1.4s `ease-in-out`, looping (`_wm-dialogs.scss:24-41`).

---

## 3. On-table game panels (spot system, JS on the Web Animations API)

**The engine: `Y.Animation.createSpotGroupAnimation`** (`js/Animation.js:138-314`)
- **Enter:** each piece starts at opacity 0, scale S and translateY +Y (so it sits below its place). After its delay, it runs to opacity 1, scale 1 and y 0 over duration D with the easing (`Animation.js:180-199`).
- `y` and `marginTop` both run on the native `translate` property (`Transition.js:295-307`, :404-414). `scale` is the native `scale` property (`Transition.js:99-102`).
- The origin is the piece's default, its centre. Only the title groups set `center center` explicitly.
- **Exit (`hide()`):** opacity→0, scale→exitScale, y→+exitMarginTop, so the piece sinks. It uses exitDuration and exitEasing. The spots are removed after exitDuration + exitBuffer (`Animation.js:272-298`).

**Presets** (`Animation.js:12-66`)

| Preset | Panel | Items | Exit |
|---|---|---|---|
| default | 240ms, .96, +8px | 80ms, delay 160, stagger 16, .94, +6px | 160ms, .98, +6px, then +60 buffer |
| inlineChoiceRow | 160, .98, +4 | 160, delay 0, stagger 16, .96, +4 | 160, .98, +4 |
| singleAction | 160, .98, +4 | 160, delay 0, stagger 0, .96, +4 | 160, .98, +4 |
| reviewPanel | 240, .98, +8 | 240, delay 160, stagger 16, .98, +8 | 160, .98, +8 |

- Every enter uses `ease-out-2` (.33,1,.68,1). Every exit uses `ease-in` (.11,0,.5,0) (`Transition.js:15,19`).
- **Default preset:** bid and suit choosers in spades, pinochle, pinochledd, twentynine, threefiveeight, bridge and sheepshead.
- **singleAction / inlineChoiceRow:** action buttons in hearts, euchre, cribbage, canasta, handfoot, rummy, ginrummy and crazyeights; also `Tutorial.js:30` and the tram button (Table.js :5008, :5040).
- **reviewPanel:** the Pinochle panels (`pinochle-game.js:83`).

**Hand over** (wm path, `showHandOverModal`, Table.js:5141; config at :5147)
- **Veil and panel:** one group, delay 0, 240ms, .96, +8px, `ease-out-2` (:5279). The veil is black 48% with a 4px blur (`pieces.scss:931-938`). Because the full-board veil is in the panel group, it also scales from .96 and rises 8px.
- **Title:** delay 240, 240ms, .96, 0px.
- **Rows:** start at 480ms, 40ms apart (:5283), each 160ms, .96, +4px.
- **Round number:** delay 800 (:5287).
- **Wheel:** a `::after` with `gameOverSvgFadeIn` (240ms `ease-out`, to opacity .16) plus `gameOverSpin` (40s linear, looping) (`pieces.scss:424-447`, :456-491).
- **Leave (new today, uncommitted, "Holger, 23 Sep 2026", Table.js:5262-5276):** under the redesign the panel and the veil fade out with `removeSpotPieces(..., {exit:"fade", fadeDuration:240})`. This is `Piece.fadeOut`: opacity to 0 over 240ms linear (`Piece.js:675-677`). The fade starts at HAND_OVER_DURATION − 100 − 240 − 256ms. Flag-off still cuts at HAND_OVER_DURATION − 100.
- **When Animations is not All:** there is no panel. The **message box** shows "Hand complete! Next hand starting..." for HAND_OVER_DURATION instead (Table.js:5168). The message box is the quiet stand-in for this panel.

**Game over** (wm path, `showGameOverModal`, Table.js:6373; config at :6499)
- The same panel group: 0 / 240 / .96 / +8 (:6549).
- The title text grows from scale .45 to 1 over 320ms `ease-cup`, starting at 200ms (:6582; GAME-OVER-PORT.md:72-73).
- Rows start at 480 and are 40ms apart (:6597). The controls start 80ms after the last row (:6602).
- **Leave:** the whole table goes. The playspace fades to opacity 0 over `SCREEN_TRANSITION_DURATION`, 160ms (Table.js:10975; `js/wocg.js:341`).

**Pinochle meld and subtotals panels** (`js/wocg/game/pinochle/pinochle-game.js:1025-1037`, :1324-1341; pinochledd is the same)
- They use the reviewPanel preset.
- The scrim is `.playspace.meldOverlayActive::before`: black 48%, a 4px blur, z 9299 (`base.scss:444-460`). It has **no transition**. It appears at once on show (:1025) and disappears at once 220ms after the hide starts (the 160 exit plus the 60 buffer, :1334-1340).

**Chat bubble** (`js/wocg/piece/chatBubble.js:19-21`, :176-212)
- In: opacity 0→1, scale .96→1, translateY +4→0, over 160ms `ease-out-2`.
- Out: opacity→0, scale .98, +4px, over 160ms `ease-in`.
- It uses the same material as the message box (`pieces.scss:1246-1257`).
- No reduced-motion branch.

**Other table fades**
- The playspace fades in over 160ms `ease-out-2` (Table.js:1014-1019).
- The table bar and the chat log fade over 240ms (`shared/C.js:156`; `js/wocg/TableBar.js:681,909,1068,1113`).

---

## 4. Other motion on the site

**The toast** (`#Notice.wmNotice`, `scss/_wm-notices.scss:52-93`)
- At rest or leaving: opacity 0, `translateY(-10px) scale(.96)`, origin `center top`. The transition is 190ms SHARP on both opacity and transform.
- `.wmIn`: opacity 1, transform none, over 260ms SETTLE.
- Reduced motion: no transform, opacity over 120ms linear.
- JS (`js/Notice.js`): IN is 260 and OUT is 190 (:14-15). The hold is duration + 260 (:105). Only one toast shows at a time; a new one waits for the old one to leave (:68-72, :145-160). The default duration is 3200 (:10).
- It is a CSS transition, so `?animSpeed` does not change it.

**The tooltip `#wtip`** (`scss/CustomTooltip.scss:25-48`, :95-102)
- At rest: opacity 0, `visibility:hidden`, `translateY(5px) scale(.96)`, origin `center bottom`.
- Out: opacity .08s linear, transform .08s `ease`, visibility after .08s.
- In (`.on`): transform .22s SETTLE, opacity .1s linear.
- `.below`: ∓5px, origin `center top`.
- The first hover waits 250ms. For 350ms after a tip closes, the next one opens at once (`js/wocg/FrontpageTooltip.js:26-27`, :124).
- **It has no reduced-motion rule.**

**Lobby-to-table View Transition** (fixed in code to "ink", `js/wocg/LobbyTableSwitch.js:53-57`)
- The old root runs `lttInkLifts`: opacity 1→0 and blur 0→4px over 190 SHARP.
- The new root runs `lttInkTakes`: opacity 0→1 and blur 4→0 over 260 SETTLE after 150 (`scss/LobbyTableSwitch.scss:56-64`, :92-98).
- The ad rail cross-fades over 260 SETTLE after 150 (:188-199).
- Reduced motion: a plain 160ms linear fade (:218-231; JS :187).
- Variants built but not used: dissolve (:76-88), through-felt (:100-108), into-felt (:110-120).
- Pieces deal onto the felt (the tile variant, or a direct game URL): from opacity 0, `translate 0 10px`, scale .94, over 260 SETTLE. Slots are 40 + seat×80 + piece×22 (:41-44, :298-300, :358-386).
- Pieces get up on Leave: opacity→0, +10px, .97, over 190 SHARP, 30ms per seat (:396-402).
- Puff: opacity→0, scale 1.03, blur 8px, over 420 INK (:493-497).
- The message box is excluded from the deal (:294).

**Frontpage**
- **Open-table turnover** (lab c6 "One clears, four dealt", `open-tables-anim-lab.html:3701-3705`; code `js/wocg/FrontpageTables.js:30-39`, :781-790):
  - The old contents go to opacity 0 and scale .97 over 190 SHARP.
  - The new elements come from opacity 0, `translateY(10px) scale(.94)`, over 260 SETTLE, with delay 150 + i×38.
  - FLIP reorder: 300 SETTLE (:821-837).
  - Skipped under reduced motion or in a hidden tab (:50-51, :87-90).
- **Side swap** (count and Play; clock and Join / Watch) (`FrontpageTables.js:40-46`; `scss/_fp-hero.scss:214-217`, :254-260, :292-302):
  - Out: `translateX(-10px) scale(.97)` over 190 SHARP.
  - In: from `translateX(-10px) scale(.94)` over 260 SETTLE after 150.
  - Reduced motion: opacity over 120ms linear, no transform (:316-319).
- **Felt tile fading to blank (.56):** opacity over 260 SETTLE (`scss/_wm-shared.scss:651-663`).
- **Seat swap and join preview** (`_wm-shared.scss:286-365`):
  - The old avatar goes to opacity 0 and scale .88 over 140 SHARP.
  - Your avatar runs `fpSeatYouIn`, scale .86→1, over 320 SETTLE after 200.
  - The name plate rolls translateY ±100% over 220 SETTLE after 120 or 200.
- **Badge** (`scss/_fp-open-tables.scss:230-276`):
  - The digits roll over 220 SETTLE after 120.
  - A fresh badge: opacity 200 linear and scale .8→1 over 260 SETTLE, both after 140.
  - A badge that goes: translateY(8px) over 190.
- **Games-bar dropup ("printer feed")** (`scss/_fp-catalog.scss:137-150`, :186, :305-329, :413-421; reduced motion :423-437):
  - Open: `max-height` 0→137px over 400ms SETTLE after 80, origin `50% 100%`.
  - Close: 240ms `cubic-bezier(.5,0,.8,.4)`.
  - The Play button squares its top corners over 80ms, and restores them over 100ms after 220.
- **Ink takes** (`scss/_fp-reveal.scss:59-183`; reduced motion :190-207):
  - Opacity with a 4px blur resolving over 340 INK.
  - The capsule alone takes 6px over 520.
  - The games-bar cells are 30ms apart (`--gbi`). The user corner comes in at 0, 45 and 90ms.
  - This is guide principle 13, "No fake motion" (DESIGN-GUIDE.md:82).
- **Hero heading swap** (`js/wocg/FrontpageHero.js:500-526`):
  - The old line rises to -14px with a 4px blur and fades over 520ms (.4,0,.6,1).
  - The new line comes from +16px with a 4px blur over 640ms (.2,.8,.2,1) after 120.
  - Reduced motion: a cut (:44-46).
- Capsule odometer: .75s `cubic-bezier(.22,1.1,.34,1)`, a slight overshoot (`_fp-hero.scss:425-429`).
- Seam mark lands: from -14px and .9, a squash (1.06,.94) at 70%, over 320ms `ease-out`. The seam sweeps its `clip-path` out from the centre over 400 INK (`js/wocg/FrontpageSeams.js:73-74`, :437-458, :490-511).
- Tile hover: only the shadow changes, over .18s `ease` (`_fp-hero.scss:90`, :97-101).

**Cards (the curves only)**

| Motion | Values | Where |
|---|---|---|
| Deal | 240ms, cards 64ms apart, `ease-in-out` | `shared/C.js:115-116`; Table.js:7843 |
| Play | 640ms, `ease-in-out` | `C.js:134-135`; `hearts-game.js:556` |
| Move and flip | flip 480 of an 800 move, `ease-in-out` or `ease-in-out-1-4` | `C.js:133,136` |
| Lift | scale 1.08; half the time `ease-in`, then `ease-out` | `Piece.js:76`, :696-697, :739-778 |
| Cleanup | 560ms, `ease-in-2` | `C.js:139-140` |
| Piece fade | 320ms, linear | `Piece.js:666-677` |

---

## 5. The message box today (checked in the code)

- **Build and place.** It is built in `#mainContainer` (`createMessageBox`, Table.js:1287). It sits at the playspace's top-left gutter, or on the top row (`resizeAndPositionMessageBox`, :1298-1362). Placement reads style values only. No code reads the box's rect.
- **CSS.** Opacity 0, `display:none`, no transition (`pieces.scss:1400-1426`). Under `body.wm` the type is 16/20, and 14/18 on a small playspace (`pieces.scss:2562-2572`).
- **Show** (`renderMessage`, :3104). The code sets `display:block` and pointer-events on, then runs a one-step `Y.Transition.Sequence`: opacity→1 over 160ms linear (:3167-3177). The lifespan is a Timer (:3180), 5s by default (`normalizeMessageArgs`, :2982).
- **Hide** (`hideMessage`, :3191). The code turns pointer-events off, then fades opacity→0 over 160ms linear. Its `cb` is meant to set `display:none` and clear the message state (:3215-3230).
- **The text changes while the box shows.** `hideMessage(newText)` does nothing, because the text differs. The code cancels the animation and swaps `innerHTML`. The opacity 1→1 run has nothing to animate (`Transition.js:243-246`). The result is a **hard cut**.
- **The same text arrives while the box shows.** The function returns early, and the **lifespan timer is not refreshed** (:3121).
- **A new message arrives during a fade.** `Transition.run` writes the target value inline before it animates (`Transition.js:488`), and `cancel()` drops the animation (:111-114). So a cancelled hide **jumps to opacity 0** and then fades up over 160ms. A cancelled show jumps to 1.
- **The bug (same on master).**
  - `Sequence.next` passes every step through `Object.merge(clone(config), {cb: this.next})` (`Transition.js:828,837`).
  - `Object.merge` overwrites keys that already exist (`js/Object.js:28-38`). I checked this in node: the `cb` becomes `next`.
  - So the hide callback never runs. After the first hide, the box stays `display:block` at opacity 0, and `currentMessageText` and `currentMessage` stay set.
  - Some games test "is the box showing?" with `display == "block"`: `hearts-game.js:296`, `ginrummy-game.js:2617`, `pinochle-game.js:211` and :1562, `cribbage-game-ui.js:1210`. They get `true` after a hide.
  - I found this by reading the code and by the node check. I did not run it in a browser.
- **Other code that uses its state:** the games above also read `lifespanTimer.getTimeLeft()`. Table.js hides the box at :1565, :1641 and :10869. `showTableError` holds a message back behind an error (:3109; `hideMessage` :3194-3204).

---

## 6. Animation settings and speed scaling

- **The user setting "Animations"** (`animationsMode`): 0 Off, 1 Vital (the tray shows "Scores only"), 2 All. The default is 2 (`shared/C.js:1234-1239`; `ProfileBox.js:117`, :1043-1052; `User.js:51`, :5562-5569). What each level turns on:
  - Off skips the deal animation (Table.js:57-69).
  - 1 or higher runs the score-change animation (Table.js:2736).
  - Only 2 runs the confetti (`Animation.js:107-109`), the floaters (:733), the party preload (Table.js:1048), the hand over panel (otherwise the message box line, :5168) and the notification lottie (`User.js:2560-2565`).
  - **It does not touch** the modals, the toast, the tooltip, the spot panels, the chat bubble or the message box.
- **`?animationSpeed=`** is a debug URL param, not a user setting. It scales the C constants in the `TOP_LEVEL_ANIMATION_TIMINGS` list and the `GAME_ANIMATION_TIMING_PATTERNS` (`js/wocg.js:22-78`, :121-192). `Y.wocg.scaleAnimationTime` has no callers (:447). The message box uses a literal 160, so this param does not scale it.
- **`?animSpeed=`** is a debug param that divides every `Y.Transition` duration and delay (`Transition.js:42-55`, :222, :235). It reaches the message box, the chat bubble, the spot panels and the modal close. It does not reach CSS motion.
- **`prefers-reduced-motion`**
  - The CSS families honour it: `Modals.scss:101`, `_wm-notices.scss:87`, `_wm-settings.scss:88,398`, the `_fp-*` partials and `LobbyTableSwitch`.
  - The `Y.Transition` code paths never check it: there is no match in `Transition.js`, `Animation.js`, `Table.js`, `Piece.js`, `chatBubble.js`, `ModalShell.js` or `Notice.js`.
  - The guide says every family must answer it (DESIGN-GUIDE.md:601).
  - The game over wheel still turns under reduced motion. GAME-OVER-HANDOVER.md:112,118 already raised this and asked to "wire the site's Animations setting to the same static state".

**Recommendation for a new message box motion**
- **Always show the box.** It is feedback, like the toast, not decoration.
- **Under `prefers-reduced-motion`,** use the toast's fallback: no travel, opacity over 120ms linear (`_wm-notices.scss:87-93`).
- **Also drop the travel at Animations = Off (optional).** The box is the stand-in for the hand over panel when Animations is not All (Table.js:5168), so it should stay quiet at those settings. Keep the fade.
- **If the motion stays in JS, add a reduced-motion check.** The toast does its motion in CSS with a `wmIn` class instead.

---

## 7. Named motion families (reusable by name)

| # | Family | Spec | Reduced motion | Where | Fit for this lab |
|---|---|---|---|---|---|
| F1 | **Drop from an edge** | in: opacity 0 plus `translateY(-10px) scale(.96)` → none, origin at the edge it hangs from, 260 SETTLE; out: back to the start, 190 SHARP | opacity 120 linear | toast `_wm-notices.scss:75-93` | the toast; a box that hangs under the top row |
| F2 | **Anchor pop** | ±5px and .96 toward the anchor, origin at the arrow's edge; in: transform 220 SETTLE and opacity 100 linear; out: 80ms | none today | tooltip `CustomTooltip.scss:25-48` | a box that points at a seat |
| F3 | **Side swap** | out: `translateX(-10px) scale(.97)` 190 SHARP; in: from `translateX(-10px) scale(.94)` 260 SETTLE after 150 | opacity 120 linear | `_fp-hero.scss:254-302`; `FrontpageTables.js:40-46` | **"in from the side".** The box stands on the left gutter (Table.js:1306-1307). The site leaves and arrives on the same side. |
| F4 | **Modal rise** | scrim 220 `ease-out` (alpha and blur); panel opacity 0, +12px, .98 → 260 ENTER; close: the whole layer fades over 160 | entrance none | `Modals.scss:67-104`; `ModalShell.js:640` | "like the big modals" |
| F5 | **Page rise** | out: opacity 200 `ease-out`; in: opacity 0 and +10px → 240 ENTER, after the thumb (220) and the box height (220+40) | none | `_wm-settings.scss:60-96` | new content in the same box, one step at a time |
| F6 | **Table panel rise** | opacity 0, .96 or .98, +8 or +4px (from below) → 240 or 160 `ease-out-2`; staggered items; exit sinks +6 or +8px and .98 over 160 `ease-in` | none (a gap) | `Animation.js:12-298`; chat bubble +4 / .96 / 160 | **"like the on-table game modals"**; the most native choice for a table piece |
| F7 | **Deal in / get up** | opacity 0, `translate 0 10px`, .94 → 260 SETTLE, staggered 38ms or by seat; leave 190 SHARP to +10px and .97 | skipped | `FrontpageTables.js:35-39`; `LobbyTableSwitch.js:298-402` | box and toast arriving as a pair |
| F8 | **Clear in place** | opacity→0 and scale .97 over 190 SHARP | skipped | `OUT_KF` in `FrontpageTables.js:35` | pairs with F7 for a text change |
| F9 | **Roll** | old `translateY(0→100%)`, new from -100% → 0, 220 SETTLE after 120, inside a window with `overflow:hidden` | none | `_wm-shared.scss:309-330`; `_fp-open-tables.scss:230-250` | **the text changes while the box stays** |
| F10 | **Headline rise-settle** | old -14px with a 4px blur, 520 (.4,0,.6,1); new from +16px with a 4px blur, 640 (.2,.8,.2,1) after 120 | cut | `FrontpageHero.js:500-526` | a text change, slower than F9 |
| F11 | **Ink takes / ink lifts / puff** | opacity plus a 4px blur, no travel; takes 340 INK (or 260 SETTLE after 150); lifts 190 SHARP; puff adds scale 1.03 and blur 8 over 420 INK | none / 160 linear fade | `_fp-reveal.scss:59-74`; `LobbyTableSwitch.scss:56-98` | a fade with no travel that belongs to the design (principle 13) |
| F12 | **Plain fade** (legacy) | message box 160 linear; piece 320 linear; screen retire 160; scoreboard 160 linear; table bar / chat log 240 `ease-out-2`; auth 160 `ease-in-out` | none | see sections 3 and 5 | **today's box**; the control |
| F13 | **Feed** (unroll from an edge) | `max-height` 0→h over 400 SETTLE after 80, origin at the source edge; back 240 (.5,0,.8,.4); the source squares its corners | none | `_fp-catalog.scss:305-329` | **the toast feeding out under the box** |
| F14 | **Thumb travel / box height** | geometry 220 EASE, opacity 110 linear; first placement lands | — | `Modals.scss:165,584-631` | a shared slot that changes height when the toast docks |
| F15 | **Mark pop** | scale .4→1 plus opacity, 260 SETTLE, no overshoot | none | `_wm-settings.scss:382-396` | a small badge or count |
| F16 | **Grow on a curve** | scale .45→1, 320 `ease-cup` | — | game over title, Table.js:6582 | no |
| F17 | **FLIP reorder** | translate from the old slot → none, 300 SETTLE | skipped | `FrontpageTables.js:821-837` | **push the box or the toast aside when the other one arrives** |
| F18 | **Press / colour** | scale .98 over 80 `ease-out`; colour over 24ms `ease-out` | — | DESIGN-GUIDE.md:591-592 | the box's buttons |

**Ambient motion. Do not use it for messages:** the wheel spin (40s), the turn-hint arrow blink (`pieces.scss:1878-1954`), the LIVE ring (750ms), the waiting bar (1.4s) and the odometer overshoot.

---

## 8. Where the docs and the code disagree

- DESIGN-GUIDE.md:590 says the games bar uses `--thspd` and `--thease` at `_wm-shared.scss:561`. The code has `--bar-speed` and `--bar-ease` at `_wm-shared.scss:688-689`. Only the leaderboard has `--lb-thspd` and `--lb-thease` (`_wm-leaderboard.scss:34-35`).
- Section 9 of the guide and `13-motion.html` have no table families: no table panel rise, no chat bubble, no message box, no modal close.
- **Two "settle" curves:** SETTLE (.22,1,.36,1) in CSS and `ease-out-2` (.33,1,.68,1) in the table engine.
- **Two "leave" curves:** SHARP (.32,0,.67,0) and the table exit `ease-in` (.11,0,.5,0).
- **Three entrances for one veil:**
  - The modal scrim fades alpha and blur over 220.
  - The game over and hand over veil rises and scales with the panel (Table.js:5279, :6549).
  - The meld scrim cuts (`base.scss:444-460`).
- LOBBY-TABLE-TRANSITION.md:3-4 still says the switch awaits a pick. The code is fixed to "ink" (`LobbyTableSwitch.js:53-57`), as the guide log says (DESIGN-GUIDE.md:720).
- The tooltip has no reduced-motion rule, although the guide says every family has one (:601).

---

## 9. Constraints for the lab builders

- **Flag.** The toast and the tooltip are SHARED with flag-off (FLAG-OFF-PARITY.md:94). If "the toast docks under the message box" is built on the shared toast, flag-off changes too, unless the change is gated on `body.wm`.
- **Transforms.** The guide says nothing the table layout measures may carry a transform (DESIGN-GUIDE.md:601, :703). The layout does not measure the box's rect, so a transform on the box is allowed. `Transition.js` animates the individual `translate` and `scale` properties, so they combine with a CSS `transform`.
- **Timers.** Notice.js holds the toast for duration + 260 and sets `display:none` 190ms after the hide starts (`Notice.js:105`, :140-142). Five games read the box's `display` and its lifespan timer (section 5). A new version must keep those meanings, or fix the bug and the games that depend on it.
- **Earlier labs to reuse:**
  - `Design/WoCG-3/game-notice-lab.html`: the message box's materials. Its section 4, "Other forms and places", includes a toast form (:284-291).
  - `game-notices-lab.html`: the toast.
  - `open-tables-anim-lab.html` (:3695-3719): where the arrive and leave pair came from (c3, c6, c7, c8).
  - `design-guide-parts/13-motion.html`: the `MO` curve names and the replay pattern.

────────────────────────────────────────

**Question:** Which animations does the site already use, and which could the message box and toast lab reuse?

**Answer:** *The site has five named curves and about eighteen motion families, and each of Holger's ideas has a precedent.*

The redesign moves on ***SETTLE*** (260ms in) and ***SHARP*** (190ms out). Panels enter on ***ENTER***, and data appears by ***ink takes***. Today the message box is a plain 160ms linear fade that ignores reduced motion and the Animations setting. The closest precedents are the ***side swap*** for "from the side", the ***modal rise*** and the ***table panel rise*** for the two modal ideas, and ***feed*** or ***FLIP*** for a toast under the box.

There is also a bug on master: the box never returns to `display:none` after a hide, and five games read that value. Another session was editing `Table.js`, `pieces.scss` and `base.scss` during this work, so some line numbers can move.

---

# Report: lab-recipe

# Message box and toast lab: build research

Read-only pass. I changed nothing in the repo or in `Design/WoCG-3`. Headless Chrome was not run. The one live check was a single GET to `https://dev.worldofcardgames.com/`, which returned 200.

## 0. Key findings first

1. **`site.css` is stale.** It was built Sep 22 23:34:48, at wocg `67f48802c`. That hash is stated in `settings-row-lab.html:15-16` and `:328`; `site.css` has no header. It lacks today's rule `body.wm #mainContainer .spot-messageBox {16px/20px}` (pieces.scss:2563-2567, uncommitted). The only messageBox type rule it has is the phone rule at `site.css:12919-12922` (14/18). The base rule still gives `var(--font-size-md)` = 20px/24px (`site.css:12054-12074`, `:3328`, `:3333`).
2. **A rebuild picks up other sessions' unfinished SCSS.** At the time of reading, 7 SCSS files were modified and one was untracked: `AdWidget`, `CustomTooltip`, `Modals` (+110 lines), `_wm-read`, `_wocg-tokens`, `base`, `pieces`, plus the new `_classic-table.scss`. HEAD also moved during this session (`ff366168c`, `2c8378bd3`).
   - Most important for this lab: the uncommitted `_wocg-tokens.scss` change removes `.spot-messageBox` from `$wm-token-roots`.
   - After that lands, the box reads its tokens only through `body.wm`.
   - Flag-off (`body:not(.wm)`) repaints it in master's blue (`_classic-table.scss:86-98`).
   - So in the lab, the box must sit inside a `.site.wm` root.
3. **Use the real site CSS inside iframes, not the `game.html` copy.** Draw each viewport as an iframe at its real size, with `site.css` + `guide-fonts.css` (the `settings-row-lab.html` pattern).
   - The table labs (`game-chrome-lab`, `game-notices-lab`, `game-modals-lab`) use a hand-styled copy of `game.html` with old tokens. For example, the message box there is `--team1-bg`, 20/24, at `game-chrome-lab.html:194-200`. The toast there is a hand copy at `game-notices-lab.html:7813-7838`. Both break Holger's rule "never hand-style a site piece".
4. **Geometry measured from sweep shots** (run `20260922-161216`, Hearts `notice-tip`, box outer edge, ±1px):

   | Frame | Box left | Box top | Box size (w×h) | Notes |
   |---|---|---|---|---|
   | Desktop 1200×800 | 16 | 72 | 200×120 | cap 175 |
   | Landscape 750×340 | 8 | 44 | 138×88 | `narrowCap` |
   | Portrait 390×664 | 8 | 176 | 135×88 | `narrowCap`, 100px top ad above |

   So the box is a narrow column on every size. It is capped by the top plate (Table.js:1296-1363).
   - **Stacking the toast under it collides with the West seat.** The seat's fan or avatar starts at about y 192 (desktop), y 125 (landscape) and y 290 (portrait). The box bottoms are about 192, 132 and 264.
5. **Today's toast probably overlaps things on a table under the redesign (not verified live; no sweep scene fires a toast).** With the menu bar hidden, `#NoticeContainer` top is 0 (`MenuBar.scss:21-23`, `Notice.js:256-267`). The toast then lands at y=16 (8 on compact).
   - On desktop the pills are at about x 16-136 and 728-848, y 16-56. The container is 864 wide. A toast wider than about 576 covers the pills.
   - In portrait the container is 390 wide, with no rail. The toast sits over the 100px top banner ad (`#ad.mobileTop`, `AdWidget.scss:211-215`) and over both pills.
   - This is a strong argument for Holger's "in the message box place".
6. **The box cannot animate height or width.** `.piece.spot-messageBox` has `height:auto !important; width:auto !important` (pieces.scss:1413-1414). WAAPI and CSS animations lose to author `!important`. Animate a transform (FLIP), `clip-path`, or an inner wrapper instead.

## 1. How the recent labs are built

### settings-row-lab.html (newest; the pattern to copy)
- **Header comment** (`:7-22`): Holger's quotes with dates, "How it is drawn", the `site.css` build and hash, stand-ins, and keys.
- **Parent page**: links only `guide-fonts.css`, never `site.css` (`:24`). Its own chrome is hand CSS (`:25-101`), so no `:not(.site *)` guard is needed.
- **Page top**:
  - `h1` + `.sub` quoting Holger in `<q>` (`:113-117`).
  - A `.panel.rec` recommendation with a green ring and a `.pill` "Recommendation" (`:119-138`, CSS `:39-41`).
  - A "Questions for you" panel (`:139-152`).
  - An "At a glance" table filled live from frame reports, with the recommended row as `tr.is-rec` (`:156-164`, `drawGlance` `:1245-1265`).
- **Sticky `.knobs` bar** with a `.seg` segmented chooser (`:166-172`, CSS `:59-66`).
- **Bands**: one `section.band` per option (`:174-326`). Each has `h2` "A: name", a plain `.what` sentence, a `.pc` Good / Not so good list and a `.why` line. Numbers and CSS sit in `details.css > summary + pre` (`:196`, CSS `:88-91`).
- **Footer** `p.made`: "Drawn with site.css (rebuilt …)" (`:328-333`).
- **Frames** (`:1180-1210`):
  - `frameDoc(cfg)` returns a srcdoc string with `<base href="document.baseURI">`, then `guide-fonts.css` + `site.css` links, `FRAME_CSS` + option CSS, and `<div id="root" class="site wm frameRoot">`.
  - The frame script is injected as `CFG` + `MODEL` JSON with `<` escaped as `\u003c`, followed by `frameMain.toString()` (`:1182-1189`).
  - The iframe gets its width from cfg and `scrolling=no` (`:1192-1210`).
- **Option CSS** is scoped under `.optX` on the frame root. "Take .optX away and it is the CSS that would ship" (`:17-19`, `:390-418`, `:618`).
- **Protocol**: `postMessage(…, "*")` both ways with `{lab:"rowlab", kind}`.
  - Parent to frame: `set` (`:1297-1303`), heard in the frame at `:1137-1146`.
  - Frame to parent: `report` with measurements (`:1075-1078`) and `tab` (`:1117`). The parent listens at `:1282-1295` and resizes the iframe to the reported height.
- **Keys**: 1-4 pick the page (`:1322-1326`). State lives in `location.hash` via `history.replaceState` (`:1178`, `:1307`).
- **Frame chrome** (`FRAME_CSS` `:623-634`): `html, body {margin:0; overflow:hidden}`. It neutralises the scrim and panel for a modal. A table frame does not need that.

### game-chrome-lab.html (the table as a hand copy; do not copy its pieces)
- Built from `game.html` by `zz-tmp-build-chrome-lab.py`. It has its own layout engine: `layoutTable` `:1448`, `render` `:1621`, message box placement `:1670-1678`.
- It uses its own fonts via relative `@font-face` (`:29-33`). These are **blocked from file://**.
- Choosers are `[value, label]` arrays. Holger's pick carries a ★ `\u2605` prefix: `MNOTES` `:2150-2156` ("★ Smaller type… type14"), `curMnote` `:2175`, body class `mnote-type14` `:943`.
- Body classes: `ps-compact` / `ps-small` / `ps-portrait` (`:2596-2602`).
- A slide-in `.switchbar` (`:1146-1170`, markup `:1269-1291`) and a key HUD `flashHud` (`:2629-2633`).
- Keys (`:2634-2663`): `x` today vs current, `z` / `⌘Z` flip the last chooser, `↑↓` step the chooser.
- BroadcastChannel sync across windows (`:2254-2264`).
- `game-chrome-sizes.html` iframes this lab at desktop, iPhone landscape and portrait, and iPad:
  - scales the phones with `transform` (`:77-83`);
  - draws the safe-area insets, notch and home bar (`:55-73`);
  - sets `bare=1` to hide the chrome.

### game-notices-lab / game-modals-lab / game-felt-lab (about 3.4MB each)
- Generated by `zz-tmp-build-modals-lab.py` from `zz-tmp-modals-parts/` + `game.html` (`py:1-5`, sets at `:138-141`). "Do not edit the built file by hand."
- The size comes from base64 fonts (`notices:13-14`) and `window.LOTTIE_DATA` (1.78MB, `:10221`).
- "Today" is the compiled CSS scoped under `#oldLayer`. "New" is a hand copy (`.sm.neo.toast .box` `:7813-7838`, `toastBox` `:11666-11672`).
- One full-window `#stage`. `f` swaps to a 390×844 phone stage (`:944-946`). A caption card `#cap` shows keys (`:950-960`, `:12786-12790`).
- Keys (`:12807-12820`): `←→` walk items, `↑↓` / `x` old vs new, `[ ]` variants, `m` modal on/off, `c` caption, `p` player, `r` replay, `f` frame. `?m=&d=&v=` in the URL.

### open-tables-anim-lab.html (the animation lab; built by `zz-tmp-build-anim-lab.py`)
- **Variants as data**: `{id, name, tag, totalMs, note, out:{d,dl,e,kf}, inn:{…}, outStep/inStep, controls}` (`py:391-433`).
- They run with WAAPI `el.animate(kf, {duration: d/RATE, delay: dl/RATE, easing, fill:"both"})` (`py:435-450`).
- **Controls**:
  - `.abtn.go` "Run" on each card, "Run every one", "Run both" with two `<select>`s for a side-by-side compare (`py:99-146`, `:596-700`).
  - Speed buttons `data-rate` 0.25 / 0.5 / 1 ("quarter / half / full") set a global `RATE` (`py:131-134`, `:175`, `:648-652`).
  - Per-card dials (Blur, Length) (`py:608-631`).
  - A rAF frame meter, "worst frame … ms" (`py:372-385`).
- **Cards**: `.vcard` with `h3` + `.tag` (ms, "best scored", "pick", "now") + `.vnote` plain words (`py:43-54`).

### dark-lab.html (DOM snapshot of the real dev page)
- `zz-tmp-dark-snap.mjs` drives dev through `scripts/visual-sweep/lib/browser.mjs` (Chrome for Testing) and `client.mjs`.
  - Browser `:9`, `EXTRACT` `:11-24`: it removes script, style, link, iframe and hidden nodes except `#ad`, and returns `body.innerHTML`, the body attrs, the html class and the URL roots.
  - `capture` `:46-60`, with `try/finally close` `:59-72`.
- `zz-tmp-build-dark-lab.mjs` `prep()` (`:23-31`) rewrites `assets/` to `static/` in src, href and `url(&quot;…)`, and strips runtime inline states.
- The snapshot goes into `<template>` and is cloned into a `div.site wm …` root that carries the body attrs (`dark-lab-parts/lab.html:141-142`, `frame()` `:251-257`).

### colour-lab.html (felt drawn with site.css, pieces placed by hand)
- `felt(inner,h,w)` = `<div class="site wm" data-table="true"><div id="mainContainer" class="unselectable" style="height:…"><div class="playspace" style="opacity:1">…` (`:229`, `:252-259`).
- Pieces use real classes with inline geometry, e.g. `.piece.classic.text.spotPrefix-namePlate` (`:589-596`).
- Its fonts are relative `@font-face` and are blocked from file:// (`:11-17`). It is "not yet rebuilt" (handoff:32).

### Drawn guide fragments that already hold the real toast markup
- `13-motion.html:461-470`: toast motion demo, `#NoticeContainer style="position:static;padding-top:0"`.
- `03-shape.html:209-210`, `11-panels.html:373-387`, `08-cards.html:538-539`.
- `01-roots.html:11,54,130` measures `.spot-messageBox` as a token root. That card will go red once the `_wocg-tokens` change lands.

## 2. site.css

- **Build**: `build-site-css.js`.
  - Compiles `worldofcardgames/static/scss` with `sass --no-source-map --style expanded` into `/tmp/wocg-site-css`. Stderr is hidden (`:17`).
  - Reads the sheet list from `dustData.js` `css = css.concat([...])` (dustData.js:16; parsed at `build:11-14`), with the YUI reset first (`:69`).
  - Scopes selectors (`:22-34`): `:where(.site)` prefix; `body` / `html` become `:where(.site):is(div)`; `:root` becomes `:where(.site):is(.site)`.
  - Drops `@font-face`. Points urls at `static/`, a symlink to `worldofcardgames/static`.
  - Inlines only mask art (6 files now, listed in `guide-assets.js`).
  - Writes `site.css`, `guide-fonts.css` (BuloRounded 400/700, GLCA 500, Gelica 500 as data URIs, `:111-123`) and `guide-assets.js`.
- **Sheets**: 37 in site order (`site.css` section markers).
  - `Notice.css` at `:8214` (the `#NoticeContainer` base, `:8404-8447`).
  - `pieces.css` at `:10812` (box `:12054-12127`, phone type `:12919`).
  - `Modals.css` at `:23572`, which `@import`s `_wm-notices` (Modals.scss:824). The toast rules are at `site.css:24751-24805`.
  - **pieces.scss: yes. _wm-notices.scss: yes, through Modals.**
- **Staleness**:
  - Needs a rebuild for pieces.scss:2563-2567. That rule is uncommitted, mtime 11:32.
  - Also picks up the committed `MenuBar.scss` and `base.scss` changes since `67f48802c` (the `12a5259a6` "bar's hiding moves behind the flag").
  - Also picks up the in-flight `_wocg-tokens` and `_classic-table` changes.
- **Command (do not run until you want to; it rewrites 3 tracked files in the Design repo and restyles every lab that links site.css):**
  ```
  cd /Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3 && node build-site-css.js
  ```
  - Needs `sass` (`/opt/homebrew/bin/sass` 1.89.2 is present).
  - Expect: `site.css … KB from 37 sheets, 6 svg urls inlined` and `guide-fonts.css … 4 faces`, and no `missing` lines.
  - Check the result: `grep -n 'is(div).wm #mainContainer .spot-messageBox {' site.css` should show the 16px/20px block just before the `.playspace-small` 14/18 block.
  - The full guide loop, if the guide should follow: handoff:88-91.
- **Useful token values** (desktop, then compact or under 640):

  | Token | Desktop | Compact / under 640 | Source |
  |---|---|---|---|
  | `--paper-band` | #f4eee5 | same | |
  | `--space-container` | 12 | 8 padding (compact) | |
  | `--space-viewport-gutter` | 16 | 8 | site.css:3480-3496 |
  | `--radius-lg` (squircle) | 16 | 12 | `:3465-3471`, `:3498-3507`; global squircle `:9857-9860` |
  | `--radius-panel` | 20 | same | `:23628` |
  | `--type-body` / line | 16 / 20 | same | `:23649-23650` |
  | `--z-game-table` | 4800 | same | |
  | `--z-auth` | 10001 | same | |

  - On the felt, `--shadow-low` = `inset 0 0 0 1px var(--color-table-edge), 0 0 8px rgba(0,0,0,.24)` (`:17133`).
  - The toast on a table uses the same frame: `body[data-table=true] .wmNotice` (`_wm-notices.scss:36-39`).

## 3. file:// traps and how the labs handle them

- Chrome blocks `@font-face` sources and CSS `mask` images on a file:// page, and shows no error (memory note; handoff:61-66, 255-256).
  - Fix: link `guide-fonts.css`, whose faces are data URIs, in every frame document.
  - The build inlines mask art into `site.css`.
  - Background images and `<img>` load from disk. The felt `static/pieces/wallpaper/fabrics/green-felt.jpg` loads through the symlink.
- The older labs are not honest from file://. `game-chrome-lab`, `colour-lab`, `open-tables-anim-lab` and `hero-tile-play-lab` use relative `@font-face`. Only `game-notices-lab` and `modals` inline base64 faces.
- Avatars, plates and backs in the table labs:
  - relative files: `game-assets/avatars/<Name>.svg` as `<img>` (`game-chrome-lab.html:1650-1652`), card faces as `background-image:url(game-assets/cards/<id>.png)` (`:1606-1611`), `game-assets/ui/dealer.png`, `green-felt.jpg`;
  - avatar outline from an inline SVG filter `avatarLine1` (`game-notices-lab.html:12708`);
  - hand-CSS plates;
  - lottie from inlined JSON plus `game-assets/lib/lottie_light.min.js`.
  - In a snapshot, avatars and cards come as site markup with `static/…` paths. The body-level SVG `<filter>` defs must survive, and `EXTRACT` keeps them because they are not `display:none`.
- If a check server is used, serve `.css` as `text/css` (handoff:252-254). Always also open the page from a file:// URL.

## 4. Lab UI conventions to follow

- **Plain words**: title plus a `.sub` quoting Holger, with date and `<q>`. Each option leads with one plain sentence (`.what`) and a short Good / Not so good list. Numbers, curves, CSS and measurements sit in one `<details>`.
  - From the memory note "design-artefacts-plain-words": use plain titles, no class names in prose, sentence case, no em dashes or semicolons (handoff:286).
- **Recommendation**: `.panel.rec` + `.pill` "Recommendation", `tr.is-rec` in the glance table, and a ★ prefix on the chooser label.
- **Questions for you** panel. Holger answers in chat.
- **Keys**, from the table labs:
  - `r` replay, `x` today vs chosen, `←/→` walk options, `↑/↓` step the chooser in focus, `[ ]` sub-variants, `z` flip back;
  - show them in a caption `.keys b` (`game-notices-lab.html:957-958`) and flash a HUD on use.
  - The anim lab has Speed quarter / half / full. settings-row reserves 1-4.
- **State** in `location.hash`.
- **Footer** `p.made` naming the build, the scene source and the stand-ins.

## 5. The real markup for the two pieces

**Message box.** Table.js:1286 creates it. It is appended to `#mainContainer` (`:1288`). Placement is at `:1296-1363`. Content and show logic is at `:3083-3167`.
```html
<div class="piece classic text spot-messageBox spotPrefix-messageBox [narrowCap] [resync]"
     style="left:16px; top:72px; margin-top:0px; max-width:175px; display:block; opacity:1; pointer-events:auto">
  <span>Pass three cards to the left.</span></div>
```
- **Tip**: `<span><strong>Tip:</strong> Enjoying the game? …</span>` (Table.js:9915-9917).
- **Alert**: class `resync` + `<strong>Notice:</strong> <span>…</span>` (`:3107-3110`, `:9918-9920`).
- **Buttons**, as in the waiting message (`:1579-1621`): "Table **#12** starts when full." + `<div class="button blue"><span class="long">Start with bots</span><span class="short">Add bots</span></div><div class="button blue inviteLink">Invite players</div>`.
- **CSS defaults**: `opacity:0; display:none` (pieces.scss:1424-1425). Set both inline, as Table.js does.

**Today's box motion.**
- Show: WAAPI opacity 0→1, 160ms linear (Table.js:3146-3156; Y.Transition is `element.animate`, Transition.js:471-491).
- Hide: 1→0, 160ms linear, then `display:none` (`:3192-3208`).
- A text change while showing is an instant `innerHTML` swap (`:3100-3116`).

**Toast.** Notice.js builds it at `:34-43` and shows it at `:89-119`. The container is appended to `body`, so in the lab it goes as a child of the `.site` root div.
```html
<div id="NoticeContainer" style="display:block; top:0px; padding-top:16px; left:0px; width:864px">
  <div id="Notice" class="wmNotice info [compact] wmIn" role="status" aria-live="polite" style="display:block">
    <strong class="label"></strong><span class="message selectable">No available seats.</span></div></div>
```
- The turn hint uses `label:"Hint:"` + `messageHtml`, for 6.4s (Table.js:22, 4101-4113).
- `padding-top` = safe area + gutter (16, or 8 on compact). `width` = viewport minus rail: desktop 864, landscape 590, portrait 390 (Notice.js:189-243).
- Motion: in 260ms `cubic-bezier(.22,1,.36,1)`, out 190ms `(.32,0,.67,0)`, from `translateY(-10px) scale(.96)`, origin center top. Reduced motion gives 120ms linear opacity (`_wm-notices.scss:75-93`).
- Queue: one at a time (Notice.js:68-72, 116-118, 160). Default 3200ms plus the 260ms arrival (`:10`, `:105`).

## 6. Motion vocabulary to offer as variants (all real, with sources)

- **Big modal**: panel `wmPanelIn` 260ms `(.2,.7,.2,1)`, from opacity 0, `+12px`, `scale(.98)`. Scrim `wmScrimIn` 220ms ease-out (Modals.scss:67-99). This keyframe carries the centring `translate(-50%,-50%)`, so do not reuse it as is.
  - Master's un-centred version is `modalPanelEnter` 220ms `(.16,1,.3,1)`, from `translate3d(0,20px,0) scale(.98)`, with opacity done at 32% (ModalEntrance.scss:151-165). The exit is at `:167-182`.
- **On-table felt panels** (`Y.Animation.createSpotGroupAnimation`, Animation.js:12-70, 179-201, 272-289):
  - panel 240ms `ease-out-2` = `cubic-bezier(.33,1,.68,1)` (Transition.js:19), from opacity 0, `translateY(+8)`, `scale(.96)` (`reviewPanel` uses .98);
  - items start after 160ms, stagger 16ms;
  - exit 160ms `ease-in` = `(.11,0,.5,0)`, to `scale(.98)`, `y +6/8`.
- **Settings page rise**: `wmPageRise` 240ms `(.2,.7,.2,1)`, from `translateY(10px)`, after a 200ms ease-out leave (`_wm-settings.scss:65-87`). site.css keeps keyframe names global, so a variant can say `animation: wmPageRise …`.
- **Anim lab recipes**: "Clean handover" is out 150ms `(.32,0,.67,0)` to `scale(.96)`, then in 190ms `(.22,1,.36,1)` (`py:391-395`).
- **Slide from the side**: `#mainContainer` is `overflow:hidden` on a table, so a slide from off-left is clipped at the felt edge.

## 7. BUILD RECIPE: `Design/WoCG-3/message-toast-lab.html`

### Files
- `message-toast-lab.html` (the lab).
- `zz-tmp-message-toast-snap.mjs` (scene capture; the `zz-tmp-*` naming convention).
- `message-toast-lab-parts/snap-{desktop,iphone-landscape,iphone-portrait}.html` and `.json`.
- Optional: `zz-tmp-build-message-toast-lab.mjs`, which inlines the snaps into `<template>`s (as `zz-tmp-build-dark-lab.mjs` does). Otherwise the lab `fetch`es nothing, because fetch is blocked from file://.

### Step 0: rebuild site.css (command in section 2)
Record the wocg HEAD and "plus uncommitted work" in the header, because the tree is in flux.

### Step 1: the felt scene
**Choose A (preferred) or B (fallback).**

**A. DOM snapshot of a real bots Hearts table.** Dev answered 200 today.
- Copy `zz-tmp-dark-snap.mjs`. Import `Browser` (browser.mjs, Chrome for Testing, `findChrome` `:13-22`), `* as client`, and `VIEWPORTS` from `scripts/visual-sweep/lib/scenes.mjs:19-25`.
- For each viewport, use its own `profileDir`, such as `/tmp/mtlab/<vp>`. Then:
  - `navigate(".../hearts")`, `evaluate(client.waitReady())`. Optionally `ensureLogin` with the sweep account for that viewport (`sweep.mjs:66ff`).
  - `evaluate(client.waitBotsTable())` (client.mjs:166-178).
- **Measure what the site computes.** Evaluate:
  - `currentTable().showTableError("x", 60000, "tip")`, wait 400ms, and read `.spot-messageBox` `style` + `className` + `getBoundingClientRect()`;
  - then `Y.wocg.Table.hideTableError()`;
  - then `Y.fire("Notice:show",{message:"No available seats.",duration:false})` and read `#NoticeContainer` style, `#Notice` class and rect;
  - then `Y.fire("Notice:hide")`.
  - Also read the rects of `#chromePill`, `#chromePillRight`, `#scoreBoardWrapper`, `#ad`, and seat 1's avatar and namePlate pieces, for collision reports.
- Run `EXTRACT` (dark-snap `:11-24`) and keep `bodyAttrs` + `htmlClass`. Write the files, then `prep()` (`assets/` becomes `static/`; check the printed url roots).
- End with `b.close()` in `finally`. See the memory note on profile restore: close over CDP and wait between runs.
- In the frame, the root is `<div id="root" class="site wm <body classes minus fp>" data-table="true" data-active-game="hearts" …other body attrs>` followed by the snapshot.

**B. No dev: a pixel backdrop plus live pieces.**
- Copy the clean sweep shots `games__hearts__your-play@{desktop,iphone-landscape,iphone-portrait}.png` from `scripts/visual-sweep/out/20260922-161216/shots/`. They have no message box (checked). Copy them into `message-toast-lab-parts/`, because `out/` runs are pruned and `latest` moves.
- Paint the shot as `#mainContainer`'s background at CSS size: `background: url(…) 0 0 / 1200px 800px`, and so on.
- Place the live box and toast with the geometry from section 0.4 and section 5.
- The judged pieces stay real `site.css` markup. The felt is the real page as pixels.

### Step 2: the frame document (settings-row `frameDoc` pattern)
```js
function frameDoc(cfg){ const j=o=>JSON.stringify(o).replace(/</g,"\\u003c");
 return '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><base href="'+document.baseURI.replace(/"/g,"&quot;")+'">'+
 '<meta name="viewport" content="width=device-width, initial-scale=1">'+
 '<link rel="stylesheet" href="guide-fonts.css"><link rel="stylesheet" href="site.css">'+
 '<style>html,body{margin:0;overflow:hidden;background:#327333}</style><style>'+OPTION_CSS+'</style></head><body>'+
 '<div id="root" class="site wm '+cfg.rootClass+'" data-table="true" data-active-game="hearts">'+cfg.snapshotHTML+
 '<div id="NoticeContainer" style="display:none"><div id="Notice" class="wmNotice info'+(cfg.compact?' compact':'')+'" role="status"><strong class="label"></strong><span class="message selectable"></span></div></div>'+
 '</div><script>var CFG='+j(cfg)+';('+frameMain.toString()+')();<\/script></body></html>'; }
```
- `#mainContainer` carries the playspace classes:
  - desktop: `playspace-landscape`;
  - landscape: `playspace-compact playspace-small playspace-landscape`;
  - portrait: `playspace-compact playspace-small playspace-portrait`.
  - Breakpoints: compact when the short side is 640 or less, small when it is 480 or less (playspace_layout_projection.dust:5-8, wocg.js:851-870). A snapshot already has these classes.
- Do not set `data-platform="mobile"`. That is the native app, and it moves the box to the safe-area top (pieces.scss:1437-1439).
- Iframe sizes: 1200×800, 750×340, 390×664, at real size.
  - Lay out desktop on row 1 and the two phones side by side on row 2 (1164 wide).
  - Offer "Fit" with `transform: scale()` on the iframe, as `game-chrome-sizes.html:77-83` does. Media queries still see the real frame width.
  - Optionally draw the sweep viewer's device outline (`VIEWPORTS[..].frame`), but add no insets inside the frame.

### Step 3: frame engine (`frameMain`)
- Hold refs to `box` (created as in section 5 and appended to `#mainContainer`) and `nc` / `toast`. Keep a `VARIANTS` table of `{in:{kf,d,dl,e}, out:{…}, change:{…}}`, as the anim lab does.
- Keep one `PLACEMENTS` table for the toast:
  - `today`: the container at top, centred in viewport minus rail;
  - `below`: `top = box.bottom + gutter`, `left = box.left`. Offer width modes "box column" or "own width, capped short of the score board";
  - `inplace`: box `left` / `top` when no box is showing.
  - The frame computes these from live rects, with the gutter from the 640 media rule.
- **Scripts** (scenarios):
  1. box arrives, text changes, box leaves;
  2. toast alone;
  3. toast while the box shows;
  4. box arrives while a toast shows;
  5. two toasts queued;
  6. waiting message with two buttons, plus a toast.
- **Build every step up front as one timeline**: `el.animate(kf,{duration:d, delay:t0+dl, easing, fill:"both"})`.
  - Then slow motion is `getAnimations().forEach(a => a.playbackRate = rate)`, and a scrubber is `pause()` + `currentTime = t`.
  - Keep "today" honest: the box uses a WAAPI opacity 160 linear (the same engine the site uses). The toast toggles `.wmIn`. Its `CSSTransition` shows in `document.getAnimations()`, so rate and seek work on it too.
  - For non-today toast variants set `transition:none` inline.
  - Scale any `setTimeout` (lifespan, `display:none`) by `1/rate`, or replace it with `visibility` / opacity fills.
- **Report to the parent**: `{lab:"mtlab", kind:"report", id, rects, touches:["left pill","West seat cards","top ad"], totalMs}`. Use rect intersection against the snapshot's pieces.
- **Listen**: `{kind:"set", anim, place, scenario}`, `{kind:"play", at}` (schedule `at - Date.now()` so all frames start together), `{kind:"rate", r}`, `{kind:"seek", t}`, `{kind:"pause"}`.

### Step 4: the parent page
- Parent CSS only (no `site.css`). Order on the page:
  - `h1` "The message box and the toast" + `.sub`: "You said on 23 Sep: <q>I think that we should play around with the animation we use for the message box…</q>";
  - `.panel.rec` + "Questions for you";
  - an "At a glance" table (option by frame: total time and what it touches, filled from reports);
  - a sticky `.knobs` bar with two `.seg` choosers (How it moves, Where the toast goes), plus Scenario, Replay, Speed (quarter / half / full), Pause, a scrubber, and Fit or Real size;
  - the three frames;
  - one card per option: plain sentence, Good / Not so good, `details` holding durations, curves, distances, the `.optX` CSS and the source file:line;
  - `p.made`.
- Keys: `r` replay, `space` pause, `←→` next or previous motion, `↑↓` next or previous placement, `x` today vs pick, `[ ]` scenario, `s` cycle speed, `f` fit. Flash a HUD, as in `game-chrome-lab.html:2629-2633`.
- Hash state: `#anim=B,place=below,sc=3`.
- Compare mode (optional): "Run both" with two option selects, each with its own 3 frames, as in the anim lab `py:662-700`.

### Step 5: check
- Serve the folder on a `127.0.0.1` port with `text/css`. Load it headless with Chrome for Testing, close in `finally`, and take a screenshot per frame.
- Then open it from `file://` and confirm the BuloRounded face and the felt.

## 8. Pitfalls (consolidated)

1. The root must be a `div` with class `site wm`. `body`-level selectors become `:where(.site):is(div)` (build `:22-34`). The toast container must be inside the root, not `#mainContainer`.
2. The reset paints the root white (`site.css:4-7`). The felt comes from `[data-table=true] #mainContainer` (`site.css:9786-9795`, `height:100vh`), so the frame html and body need `margin:0; overflow:hidden`.
3. Real-size iframes are required.
   - `@media (max-width:640px),(max-height:640px)` flips the gutter and radii.
   - `#NoticeContainer` is `position:fixed` in the frame viewport.
   - `#Notice`, `#mainContainer` and `#playspace` ids would collide in one document.
4. Box `!important` height and width (section 0.6). Box default `display:none; opacity:0`. Toast `opacity:0` + transform until `.wmIn`. Container `pointer-events:none`, while the toast is clickable and a click hides it.
5. The two pieces differ on phones:
   - type: toast 16/20 even when compact (`_wm-notices.scss:95-100`), box 14/18 (pieces.scss:2571-2574);
   - padding: 14/26 against 12 (8 compact);
   - radius: 20 against 16 (12 on phones);
   - max width: `min(640, 100%-32)` against the plate cap of about 135-200;
   - z-index: 10001 against 4800.
   - Any "play well together" option has to pick one of each.
6. Collisions to measure and show: the pills, the West seat, the top banner ad in portrait, and the score board.
7. `site.css` rebuild captures shared-tree changes. `.spot-messageBox` is leaving the token roots, so the box must be under `.wm`.
8. Reduced motion: if Holger's Mac has Reduce Motion on, the real toast drops to a 120ms fade and the wm panels to none. Detect `matchMedia('(prefers-reduced-motion: reduce)')` and say so on the page.
9. Blur: no `backdrop-filter` scrims, because they crashed Holger's Chrome (handoff:247-251). If a "big modal" variant brings a scrim, use flat `rgba(0,0,0,.48)`.
10. Many iframes each parse the 1MB `site.css`. settings-row carries 33 frames, so it is fine, but prefer one live stage of 3 frames plus an optional compare pair.
11. The snapshot is inert: no scripts, lottie is frozen on one frame, canvas is empty. Keep the body-level SVG defs. Check the URL roots after `prep()`.
12. The handoff mentions `wmSheetIn` (handoff:177-178, 216-218), but it no longer exists in any SCSS (grep found none).
13. The Design repo tracks `site.css`, `guide-fonts.css` and `guide-assets.js`. Rebuilding modifies them for every lab. `settings-row-lab.html` and the new lab are untracked. Do not commit there unless asked.

## 9. Not verified
- Toast placement on a live table under the redesign in any viewport (no sweep scene fires a toast). The overlaps in section 0.5 come from geometry.
- Whether a Hearts-table snapshot renders cleanly under `site.css` inside a srcdoc frame (not tried; read-only brief).
- Same-origin `contentWindow` calls into srcdoc frames from file://. settings-row uses `postMessage("*")`, so use that.

────────────────────────────────────────

**Question:** How should the message box and toast lab be built the way Holger's recent labs are built, and what scene markup can it borrow?

**Answer:** *Build it as three real-size iframes that use the site's own stylesheet, with one shared timeline that all frames follow.*

Copy the frame and messaging pattern from ***settings-row-lab.html***. Draw the felt from a ***DOM snapshot*** of a dev Hearts table, using the dark-lab scripts, or from clean sweep screenshots as a fallback. Put the ***real markup*** for both pieces on top. Do not reuse the hand-styled `game.html` table. Rebuild `site.css` first, because it lacks today's 16/20 box rule and the tree is changing under other sessions. The measured geometry shows the box is a narrow column. A toast under it would hit the West seat, and today's toast likely covers the pills and the portrait top ad.

**Next step:** Rebuild `site.css`, then run the snapshot capture against dev for the three viewports before you write the lab page.

---

# Design: how the message box comes, goes and changes

Eight ways for the message box to come and go, and five ways for its words to change while it stays on screen. Holger picks one of each, separately.

How it comes and goes: Today (the plain 160ms fade, kept as the baseline, with its snaps), Soft fade (the same fade on the site's own arrive and leave curves), Slides in from the side (a short slide of one gutter), Slides out of the felt's edge (the whole box comes out from behind the left edge like a drawer, with no fade), Rises like the table panels (the hand over panel's rise), Rises like the big dialogs (the dialog rise, with no dark sheet), Drops in like the toast (the toast's own drop), and Unrolls downward (the games bar's paper feed, turned to go down).

When the words change: Instant (today), Words fade and return, Words fade and the box glides, Words roll down, and Only the number turns.

Recommendation: Drops in like the toast, with Only the number turns. The box and the toast already use the same paper and the same frame. If the toast moves into the box's place, the two must also move the same way, or one place will show two kinds of motion. The drop is short (10px), so a status line that comes every turn does not pull the eye. The countdown, rematch and pause clocks change every second. A whole-box change every second flickers, but a rolling number does not. Every other change glides the box to its new size, so buttons that come and go no longer make the box jump. The runner-up is Slides in from the side, which is the most literal answer to "moving in from the side".

Every new option also fixes two faults that Today keeps. An interrupted fade no longer snaps to fully on or fully off. The box really goes away after it leaves: today it stays display:block at opacity 0, and an old message can come back after a tip. The bot-bid blink (a hide and a show 4ms apart) becomes one word change. Reduced motion and Animations Off both get a 120ms fade with no travel. Two ideas are left out on purpose. A spring is out because the site never overshoots (_wm-shared.scss:344, "No overshoot"). The ink-takes blur is out because on small words a blur looks out of focus for a third of a second, on a box that can change every second. Everything is scoped to body.wm, so flag-off keeps master's fade.

Verified in source for this brief: Table.js:3104-3232 (renderMessage and hideMessage, both 160ms linear), pieces.scss:1400-1491 and 2562-2574, _wm-notices.scss:75-93, Animation.js:12-66 and 180-289, Transition.js:13-28 and 488, Modals.scss:67-104 and 158-165, ModalShell.js:640-648, chatBubble.js:19-22 and 176-212, _fp-hero.scss:254-319, _fp-catalog.scss:318-326 and 413-421, _wm-shared.scss:307-355, base.scss:148-151 (#mainContainer overflow:hidden at a table). The six display === 'block' reads are at hearts:296, pinochle:211 and 1565, pinochledd:1324, ginrummy:2617 and cribbage-ui:1210.


## today: Today: a plain fade

The box fades in and out over a sixth of a second at an even pace. If a new message comes while it fades, it first jumps to fully off or fully on.

- Precedent: Today's code: Table.js:3165-3177 (show, Y.Transition opacity to 1, 160ms linear) and 3215-3230 (hide, to 0, 160ms linear). The snap comes from Transition.js:488, which writes the final value inline before it animates. The hide callback is lost because Transition.js:828 merges cb: next over it (Object.js:28-40).
- Enter: display:block, then opacity 0 to 1 over 160ms linear (WAAPI through Y.Transition). No transform. The final opacity 1 is written inline first, and the animation starts from the old inline value.
- Exit: pointer-events:none at once, then opacity 1 to 0 over 160ms linear. display stays block and currentMessage stays set, because the Sequence drops the hide's cb.
- Swap: The content is replaced with no animation, and the box jumps to its new size (measured 198x44 to 200x64 in one frame). A hide followed by a show 2-5ms later (spades bids, pinochle, euchre, twentynine, three-five-eight, gin rummy, pinochledd) blinks: 1.00 to 0.00 in one frame, then 160ms back up. The same text while showing returns early and does not restart the lifespan timer.
- Per viewport: The same on every viewport. There is no travel, so the box crosses nothing.
- Reduced motion: None. Today the box ignores prefers-reduced-motion and the Animations setting.
- Risks: Kept only as the baseline. It keeps the snap on interruption, the blink during bot bids, and the stuck display:block. Because of that, an expired message can come back after a tip or an error clears (measured with 'Spades broken!'). The six games that test display === 'block' always get true after the first message.

```css
/* Today, reproduced honestly. The lab drives this option the way Y.Transition does (Transition.js:215-491), not with the state classes:
   show(): el.style.display = 'block'; var from = parseFloat(el.style.opacity !== '' ? el.style.opacity : getComputedStyle(el).opacity);
           el.style.opacity = '1'; cancel the last animation; if (from !== 1) anim = el.animate([{opacity: from}, {opacity: 1}], {duration: 160, easing: 'linear'});
   hide(): var from = parseFloat(el.style.opacity || '0'); el.style.opacity = '0'; cancel the last animation;
           if (from !== 0) anim = el.animate([{opacity: from}, {opacity: 0}], {duration: 160, easing: 'linear'});
           display stays 'block' and the current message stays set (the lost cb).
   So a show during a hide starts from the inline '0' (a snap to 0), and a hide during a show starts from the inline '1' (a snap to 1).
   No reduced-motion branch and no Animations branch. The rule below only lets the swap chooser glide the size under Today as well. */
.opt-today .piece.spot-messageBox {
  transition: width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1);
}
```


## soft-fade: Soft fade

The same fade, but on the curves the rest of the new site uses. It comes up quickly and settles, and it leaves a little faster than it came.

- Precedent: The toast's pair of curves: _wm-notices.scss:75-85 (in 260ms cubic-bezier(.22,1,.36,1), out 190ms cubic-bezier(.32,0,.67,0)), here on opacity alone. DESIGN-GUIDE.md section 9 names them 'arriving and settling' and 'leaving, sharp'.
- Enter: opacity 0 to 1 over 260ms cubic-bezier(.22,1,.36,1). No transform. The .mbIn class runs it after display:block and one offsetWidth read.
- Exit: opacity 1 to 0 over 190ms cubic-bezier(.32,0,.67,0). display:none at 190ms.
- Swap: The arrival does not run again. The words change inside the box by the swap chooser, and the size glide uses the width and height 220ms entries in .mbIn. A show that arrives while the box leaves turns the fade round from its current opacity, with no snap, and then runs the swap.
- Per viewport: The same on every viewport. There is no travel.
- Reduced motion: Opacity only, 120ms linear both ways (the toast's fallback, _wm-notices.scss:87-93). Animations Off gets the same through .mbCalm.
- Risks: The settle curve reaches about three quarters of full opacity in the first 70ms, so the arrival reads as a quick soft pop, not a ramp. The sharp leave holds most of its opacity for about 90ms and then goes. This is the smallest change in the set, so Holger may only see a difference when an interruption no longer snaps.

```css
/* State classes, the same for every option except Today:
   .mbIn   showing (the arrival runs on this class's transition)
   .mbOut  leaving (the leave runs on this class's transition)
   .mbCalm reduced motion or Animations Off: opacity only, 120ms linear
   Driver (it replaces the Y.Transition Sequence in Table.js renderMessage / hideMessage):
   show: clear the leave timer. If the box has .mbIn or .mbOut it is on screen, so run the chosen swap mode and do not replay the arrival.
         Otherwise set the content (words and buttons inside one <div class='mbBody'>).
         Toggle .mbCalm from matchMedia('(prefers-reduced-motion: reduce)').matches || Y.wocg.User.getAnimationsMode() === 0.
         Remove .mbOut. If display is not 'block', set display:block and read offsetWidth once. Add .mbIn. pointer-events:auto.
   hide: remove .mbIn, add .mbOut, pointer-events:none. After the option's leave time (its longest .mbOut transition):
         display:none, remove .mbOut, clear currentMessageText and currentMessage (the step today's Sequence drops).
   A show that lands while the box leaves turns the leave round from where it is: no snap and no blink.
   Never write inline opacity or transform on the box. Clear Today's inline opacity when the lab switches away from it.
   In the lab, wait on Promise.all(box.getAnimations().map(a => a.finished)) instead of timers, and ignore the rejection when a show cancels the leave. That keeps slow motion and the scrubber true.
   Leave time for this option: 190ms. */
.opt-soft-fade .piece.spot-messageBox {
  opacity: 0;
  transition: none;
}
.opt-soft-fade .piece.spot-messageBox.mbIn {
  opacity: 1;
  transition: opacity 260ms cubic-bezier(.22,1,.36,1),
              width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1),
              background-color 160ms linear;
}
.opt-soft-fade .piece.spot-messageBox.mbOut {
  opacity: 0;
  transition: opacity 190ms cubic-bezier(.32,0,.67,0);
}
.opt-soft-fade .piece.spot-messageBox.mbCalm,
.opt-soft-fade .piece.spot-messageBox.mbCalm.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
.opt-soft-fade .piece.spot-messageBox.mbCalm.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear, background-color 120ms linear; }
@media (prefers-reduced-motion: reduce) {
  .opt-soft-fade .piece.spot-messageBox,
  .opt-soft-fade .piece.spot-messageBox.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
  .opt-soft-fade .piece.spot-messageBox.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear; }
}
```


## side-slide: Slides in from the side

The box slides a short way in from the left, the side it lives on, while it fades in. It leaves the same way it came.

- Precedent: The front page's side swap: _fp-hero.scss:254-302 (the count leaves with translateX(-10px) scale(.97) over 190ms cubic-bezier(.32,0,.67,0), and the Play button arrives from translateX(-10px) scale(.94) over 260ms cubic-bezier(.22,1,.36,1)). Also FrontpageTables.js:40-46. The scale is left out here so it reads as a pure slide.
- Enter: opacity 0 to 1 and transform translateX(calc(-1 * var(--space-viewport-gutter))) to none, both 260ms cubic-bezier(.22,1,.36,1). The gutter is 16px on a desktop and 8px on a phone (_variables.scss:35, 213, 228), so the box starts exactly at the felt's left edge. No scale.
- Exit: opacity to 0 and transform to translateX(-gutter), both 190ms cubic-bezier(.32,0,.67,0). It leaves toward the side it came from, as the side swap does. display:none at 190ms.
- Swap: The slide does not run again. The words change by the swap chooser, and the size glide uses the width and height entries in .mbIn. A show that arrives while the box leaves turns it round from where it is and slides it back into place.
- Per viewport: Desktop (box at 16,72): 16px of travel, from x 0 to 16. iPhone landscape (8,44-48) and portrait (8,176): 8px of travel, from x 0 to 8, which may be too small to read as a slide. If so, the lab can try 16px on phones too. The first 8px then start behind the felt's edge (#mainContainer overflow:hidden, base.scss:148-151) while the box is still almost clear. The box never passes the North plate on its right (7px gap in portrait), because the travel only goes left.
- Reduced motion: No slide: opacity only, 120ms linear both ways. Animations Off gets the same through .mbCalm.
- Risks: Sideways motion on the left edge pulls the eye more than a fade does, and the box can come and go every turn. On phones the 8px slide may not be seen. If the toast later takes the box's place, the toast would have to slide in from the side too, and that is new for the toast.

```css
/* Driver and state classes: see opt-soft-fade. Leave time: 190ms. */
.opt-side-slide .piece.spot-messageBox {
  opacity: 0;
  transform: translateX(calc(-1 * var(--space-viewport-gutter, 16px)));
  transition: none;
}
.opt-side-slide .piece.spot-messageBox.mbIn {
  opacity: 1;
  transform: none;
  transition: opacity 260ms cubic-bezier(.22,1,.36,1), transform 260ms cubic-bezier(.22,1,.36,1),
              width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1),
              background-color 160ms linear;
}
.opt-side-slide .piece.spot-messageBox.mbOut {
  opacity: 0;
  transform: translateX(calc(-1 * var(--space-viewport-gutter, 16px)));
  transition: opacity 190ms cubic-bezier(.32,0,.67,0), transform 190ms cubic-bezier(.32,0,.67,0);
}
.opt-side-slide .piece.spot-messageBox.mbCalm,
.opt-side-slide .piece.spot-messageBox.mbCalm.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
.opt-side-slide .piece.spot-messageBox.mbCalm.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear, background-color 120ms linear; }
@media (prefers-reduced-motion: reduce) {
  .opt-side-slide .piece.spot-messageBox,
  .opt-side-slide .piece.spot-messageBox.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
  .opt-side-slide .piece.spot-messageBox.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear; }
}
```


## edge-drawer: Slides out of the felt's edge

The whole box slides out from behind the left edge of the felt, like a drawer, and slides back when it is done. It does not fade.

- Precedent: New. It uses the side swap's curves (_fp-hero.scss:254-302), and the felt's own clip does the reveal (#mainContainer overflow:hidden at a table, base.scss:148-151).
- Enter: transform translateX(calc(-100% - var(--space-viewport-gutter) - 12px)) to none over 300ms cubic-bezier(.22,1,.36,1). opacity stays 1 the whole time. The extra 12px keeps the box's 8px shadow off the felt at the start. #mainContainer clips the box until it crosses the felt's left edge.
- Exit: transform to translateX(calc(-100% - gutter - 12px)) over 220ms cubic-bezier(.32,0,.67,0), opacity stays 1. display:none at 220ms.
- Swap: The slide does not run again. The words change by the swap chooser. A show that arrives while the box leaves turns it round where it is: the solid box stops partway out and slides back in.
- Per viewport: The travel is the box's width plus the gutter plus 12px: about 228px on desktop (200px box), 158px on iPhone landscape (138px box) and 155px in portrait (135px box). The ad rail is on the right, so the left edge is always the window's edge. In the native app in landscape, the box comes out from the notch side. A tall notice (private waiting, 200x144) moves a lot of paper sideways.
- Reduced motion: No slide: the box is already in place, and opacity goes 0 to 1 and back over 120ms linear. Animations Off gets the same through .mbCalm.
- Risks: This is the largest motion in the set, so it is the most noticeable for a status line that comes every turn. With no fade, an interrupted leave shows the solid box stopping partway and coming back. It depends on #mainContainer staying overflow:hidden: if a later layout drops that, the box would show off the window's edge. In the lab the snapshot must keep that rule, or the drawer shows outside the felt.

```css
/* Driver and state classes: see opt-soft-fade. Leave time: 220ms. The base opacity is 1 here, so .mbCalm must set it to 0. */
.opt-edge-drawer .piece.spot-messageBox {
  opacity: 1;
  transform: translateX(calc(-100% - var(--space-viewport-gutter, 16px) - 12px));
  transition: none;
}
.opt-edge-drawer .piece.spot-messageBox.mbIn {
  transform: none;
  transition: transform 300ms cubic-bezier(.22,1,.36,1),
              width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1),
              background-color 160ms linear;
}
.opt-edge-drawer .piece.spot-messageBox.mbOut {
  transform: translateX(calc(-100% - var(--space-viewport-gutter, 16px) - 12px));
  transition: transform 220ms cubic-bezier(.32,0,.67,0);
}
.opt-edge-drawer .piece.spot-messageBox.mbCalm,
.opt-edge-drawer .piece.spot-messageBox.mbCalm.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
.opt-edge-drawer .piece.spot-messageBox.mbCalm.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear, background-color 120ms linear; }
@media (prefers-reduced-motion: reduce) {
  .opt-edge-drawer .piece.spot-messageBox,
  .opt-edge-drawer .piece.spot-messageBox.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
  .opt-edge-drawer .piece.spot-messageBox.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear; }
}
```


## panel-rise: Rises like the table panels

The box rises a little and grows to full size while it fades in, the way the hand over and game over panels come onto the felt. It sinks a little as it fades out.

- Precedent: The on-table panels: Animation.js:12-27 defaults (panel 240ms, scale .96, +8px, ease-out-2. Exit 160ms, scale .98, +6px, ease-in), run for the hand over at Table.js:5147. The curves are at Transition.js:15 and 19. The chat bubble (chatBubble.js:19-22, 176-212) is the same family at 160ms and +4px, on the same paper as the box.
- Enter: opacity 0 to 1 and transform translateY(8px) scale(.96) to none, both 240ms cubic-bezier(.33,1,.68,1) (the engine's ease-out-2). transform-origin is the centre, as the engine's pieces use.
- Exit: opacity to 0 and transform to translateY(6px) scale(.98), both 160ms cubic-bezier(.11,0,.5,0) (the engine's ease-in). display:none at 160ms.
- Swap: The rise does not run again. The words change by the swap chooser. A show that arrives while the box leaves lifts it back from wherever it has sunk to.
- Per viewport: The values are the same everywhere. The 6px sink points at the West seat. On an iPhone landscape only about 10px separate the box from the West hand, so the leaving box ends about 4px from it, at almost zero opacity. Scaling from the centre moves the edges inward, so the portrait box never reaches the North plate 7px to its right.
- Reduced motion: No rise and no scale: opacity only, 120ms linear both ways. Animations Off gets the same through .mbCalm.
- Risks: At this size it is hard to tell apart from the big dialogs' rise, so the lab should show the two side by side. The ease-in leave keeps almost full opacity for most of its 160ms and then drops, which can look like a cut. It makes a one-line status feel like a panel.

```css
/* Driver and state classes: see opt-soft-fade. Leave time: 160ms. */
.opt-panel-rise .piece.spot-messageBox {
  opacity: 0;
  transform: translateY(8px) scale(.96);
  transform-origin: 50% 50%;
  transition: none;
}
.opt-panel-rise .piece.spot-messageBox.mbIn {
  opacity: 1;
  transform: none;
  transition: opacity 240ms cubic-bezier(.33,1,.68,1), transform 240ms cubic-bezier(.33,1,.68,1),
              width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1),
              background-color 160ms linear;
}
.opt-panel-rise .piece.spot-messageBox.mbOut {
  opacity: 0;
  transform: translateY(6px) scale(.98);
  transition: opacity 160ms cubic-bezier(.11,0,.5,0), transform 160ms cubic-bezier(.11,0,.5,0);
}
.opt-panel-rise .piece.spot-messageBox.mbCalm,
.opt-panel-rise .piece.spot-messageBox.mbCalm.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
.opt-panel-rise .piece.spot-messageBox.mbCalm.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear, background-color 120ms linear; }
@media (prefers-reduced-motion: reduce) {
  .opt-panel-rise .piece.spot-messageBox,
  .opt-panel-rise .piece.spot-messageBox.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
  .opt-panel-rise .piece.spot-messageBox.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear; }
}
```


## modal-rise: Rises like the big dialogs

The box rises a little further and more gently, the way the big dialogs open, but with no dark sheet behind it. It leaves by fading only.

- Precedent: The big dialogs: Modals.scss:71-73 and 89-99 (wmPanelIn, 260ms cubic-bezier(.2,.7,.2,1), from opacity 0, +12px, scale .98). The close is ModalShell.js:640-648: the whole layer goes to opacity 0 over 160ms on the engine's default ease-out-2. The scrim (Modals.scss:67-69) is left out, because the box never stops play.
- Enter: opacity 0 to 1 and transform translateY(12px) scale(.98) to none, both 260ms cubic-bezier(.2,.7,.2,1). transform-origin is the centre. The dialog's own keyframe carries translate(-50%,-50%) for its centring, so it is not reused as it is.
- Exit: opacity to 0 over 160ms cubic-bezier(.33,1,.68,1), with no travel. display:none at 160ms, and the transform goes back to its start while the box is hidden.
- Swap: The rise does not run again. The words change by the swap chooser. A show that arrives while the box leaves fades it back up where it stands, because this leave has no travel.
- Per viewport: 12px on every viewport. On a phone a one-line box is 34px tall, so the rise is a third of its height and looks bigger than on desktop. On an iPhone landscape a tall notice starts 12px lower, over more of the West avatar, while it is still faint.
- Reduced motion: No rise and no scale: opacity only, 120ms linear both ways. Animations Off gets the same through .mbCalm.
- Risks: Without the dark sheet it loses most of what makes it look like a dialog, so it can look like a slower copy of the table panels' rise. The flat fade-out does not answer the rise. No table piece uses the dialog curve yet, so it brings a third arrival curve to the felt.

```css
/* Driver and state classes: see opt-soft-fade. Leave time: 160ms. */
.opt-modal-rise .piece.spot-messageBox {
  opacity: 0;
  transform: translateY(12px) scale(.98);
  transform-origin: 50% 50%;
  transition: none;
}
.opt-modal-rise .piece.spot-messageBox.mbIn {
  opacity: 1;
  transform: none;
  transition: opacity 260ms cubic-bezier(.2,.7,.2,1), transform 260ms cubic-bezier(.2,.7,.2,1),
              width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1),
              background-color 160ms linear;
}
.opt-modal-rise .piece.spot-messageBox.mbOut {
  opacity: 0;
  transform: none;
  transition: opacity 160ms cubic-bezier(.33,1,.68,1);
}
.opt-modal-rise .piece.spot-messageBox.mbCalm,
.opt-modal-rise .piece.spot-messageBox.mbCalm.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
.opt-modal-rise .piece.spot-messageBox.mbCalm.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear, background-color 120ms linear; }
@media (prefers-reduced-motion: reduce) {
  .opt-modal-rise .piece.spot-messageBox,
  .opt-modal-rise .piece.spot-messageBox.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
  .opt-modal-rise .piece.spot-messageBox.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear; }
}
```


## toast-drop: Drops in like the toast (recommended)

The box drops a little from the row above it and settles, exactly the way the toast arrives. It lifts back up as it fades out.

- Precedent: The toast: _wm-notices.scss:75-85 (from translateY(-10px) scale(.96), origin centre top, in 260ms cubic-bezier(.22,1,.36,1), out 190ms cubic-bezier(.32,0,.67,0)). The origin moves to the box's own top-left corner, because the box hangs from the left end of the top row, under the Table pill.
- Enter: opacity 0 to 1 and transform translateY(-10px) scale(.96) to none, both 260ms cubic-bezier(.22,1,.36,1). transform-origin: left top.
- Exit: opacity to 0 and transform to translateY(-10px) scale(.96), both 190ms cubic-bezier(.32,0,.67,0). display:none at 190ms.
- Swap: The drop does not run again. The words change by the swap chooser, and the size glide uses the width and height entries in .mbIn. A show that arrives while the box leaves turns it round from where it is and drops it back down, with no snap. If the toast takes the box's place (the other half of the lab), the toast should use this same pair so the two are one motion.
- Per viewport: Desktop: it starts 10px higher at y 62, 6px under the pills (they end at y 56). iPhone landscape: it starts at about y 34-38, so its first frames tuck under the pills (they end at y 40, z 9975 over the box's 4800), and it seems to come out from under the pill row. iPhone portrait: it starts at y 166, 26px under the pills and well below the 100px top ad. The .96 scale from the top-left corner pulls the right edge in by only 5-8px, away from the North plate.
- Reduced motion: No drop and no scale: opacity only, 120ms linear both ways, the same fallback the toast has. Animations Off gets the same through .mbCalm.
- Risks: If the toast stays top-centre instead of taking the box's place, both can drop at the same time in two places. On a landscape phone the pills cover the top of the box for its first frames. This is intended, but it should be judged by eye. The drop is small, so next to Today it looks almost as quiet as the soft fade. This applies to every new option: once the box really goes back to display:none, the six games that test display === 'block' (hearts:296, pinochle:211 and 1565, pinochledd:1324, ginrummy:2617, cribbage-ui:1210) change behaviour. The real change should give Table.js one isMessageShowing() (it has .mbIn) and switch them to it.

```css
/* Driver and state classes: see opt-soft-fade. Leave time: 190ms. */
.opt-toast-drop .piece.spot-messageBox {
  opacity: 0;
  transform: translateY(-10px) scale(.96);
  transform-origin: left top;
  transition: none;
}
.opt-toast-drop .piece.spot-messageBox.mbIn {
  opacity: 1;
  transform: none;
  transition: opacity 260ms cubic-bezier(.22,1,.36,1), transform 260ms cubic-bezier(.22,1,.36,1),
              width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1),
              background-color 160ms linear;
}
.opt-toast-drop .piece.spot-messageBox.mbOut {
  opacity: 0;
  transform: translateY(-10px) scale(.96);
  transition: opacity 190ms cubic-bezier(.32,0,.67,0), transform 190ms cubic-bezier(.32,0,.67,0);
}
.opt-toast-drop .piece.spot-messageBox.mbCalm,
.opt-toast-drop .piece.spot-messageBox.mbCalm.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
.opt-toast-drop .piece.spot-messageBox.mbCalm.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear, background-color 120ms linear; }
@media (prefers-reduced-motion: reduce) {
  .opt-toast-drop .piece.spot-messageBox,
  .opt-toast-drop .piece.spot-messageBox.mbOut { opacity: 0; transform: none; transition: opacity 120ms linear; }
  .opt-toast-drop .piece.spot-messageBox.mbIn { opacity: 1; transform: none; transition: opacity 120ms linear; }
}
```


## feed: Unrolls downward

The box unrolls downward from its top edge, like paper from a printer, so the words appear line by line. It rolls back up when it leaves.

- Precedent: The games bar's drop-up, the 'printer feed': _fp-catalog.scss:318-326 and 413-421 (max-height 0 to the paper's height over 400ms cubic-bezier(.22,1,.36,1). Back over 240ms cubic-bezier(.5,0,.8,.4)). Here it goes downward and is shortened to 320ms.
- Enter: max-height 0 to var(--mb-h) over 320ms cubic-bezier(.22,1,.36,1) with overflow:hidden, and opacity 0 to 1 over the first 100ms linear. --mb-h is the content height, measured by JS once per show. The paper's top edge stays put and its bottom edge moves down.
- Exit: max-height to 0 over 240ms cubic-bezier(.5,0,.8,.4), and opacity to 0 over 100ms linear after 140ms. display:none at 240ms.
- Swap: The unroll does not run again. Set --mb-h again before every swap, or taller new words are clipped. When the paper grows, the max-height line (320ms settle) and the height glide (220ms) run together, and the height glide leads. A show that arrives while the box leaves unrolls it again from its current height.
- Per viewport: The unroll length is the box's height: 34-52px for a one-line status on a phone, 44px on desktop, 116-144px for the waiting notices, and about 180px for the cribbage score list. The time is always 320ms, so a tall notice unrolls faster. Nothing moves sideways, so the North plate and the pills are never crossed.
- Reduced motion: No unroll: max-height none, opacity only, 120ms linear both ways. Animations Off gets the same through .mbCalm.
- Risks: The box is content-box, so max-height 0 still leaves the padding. It starts as an empty 24px band (16px on a phone), and the 100ms fade hides this. It needs one layout read per show and per swap for --mb-h. max-height animates in layout, not on the compositor, but that is cheap for one small box. overflow:hidden stays on while the box shows. This is the one option that could push a toast docked under the box downward as it unrolls, but only if the toast half places the toast in the same flow or follows the box's bottom edge each frame.

```css
/* Driver and state classes: see opt-soft-fade, plus one measurement. After the content is set and before .mbIn is added, and again on every swap:
   box.style.setProperty('--mb-h', (box.scrollHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom)) + 'px').
   Leave time: 240ms. */
.opt-feed .piece.spot-messageBox {
  opacity: 0;
  max-height: 0;
  overflow: hidden;
  transition: none;
}
.opt-feed .piece.spot-messageBox.mbIn {
  opacity: 1;
  max-height: var(--mb-h, 320px);
  transition: max-height 320ms cubic-bezier(.22,1,.36,1), opacity 100ms linear,
              width 220ms cubic-bezier(.645,.045,.355,1), height 220ms cubic-bezier(.645,.045,.355,1),
              background-color 160ms linear;
}
.opt-feed .piece.spot-messageBox.mbOut {
  opacity: 0;
  max-height: 0;
  transition: max-height 240ms cubic-bezier(.5,0,.8,.4), opacity 100ms linear 140ms;
}
.opt-feed .piece.spot-messageBox.mbCalm,
.opt-feed .piece.spot-messageBox.mbCalm.mbOut { opacity: 0; max-height: none; transition: opacity 120ms linear; }
.opt-feed .piece.spot-messageBox.mbCalm.mbIn { opacity: 1; max-height: none; transition: opacity 120ms linear, background-color 120ms linear; }
@media (prefers-reduced-motion: reduce) {
  .opt-feed .piece.spot-messageBox,
  .opt-feed .piece.spot-messageBox.mbOut { opacity: 0; max-height: none; transition: opacity 120ms linear; }
  .opt-feed .piece.spot-messageBox.mbIn { opacity: 1; max-height: none; transition: opacity 120ms linear; }
}
```


## Swap modes


### cut: Instant (today)

The new words replace the old ones in one frame, and the box jumps to its new size. This is what the table does now.

No motion. Table.js replaces the box's innerHTML and appends the buttons in one step (Table.js:3128-3162). The width and height jump in the same frame (measured 198x44 to 200x64 on desktop). With Today, a show during a leave counts as a new arrival, so the spades bot bids blink. With the new options, a show during a leave still turns the box round smoothly, and only the words cut. Calm: the same.


### dip: Words fade and return

The paper stays where it is. The old words fade out quickly, the box snaps to its new size while it is empty, and the new words fade in.

Table.js puts the words and the buttons in one inner wrapper, <div class='mbBody'>, so they can change without the paper. The .button rules at pieces.scss:1452-1491 are descendant rules, so they still match.
CSS:
.swap-dip .piece.spot-messageBox .mbBody { transition: opacity 160ms cubic-bezier(.22,1,.36,1); }
.swap-dip .piece.spot-messageBox .mbBody.mbDim { opacity: 0; transition: opacity 90ms cubic-bezier(.32,0,.67,0); }
Steps: add .mbDim. At 90ms replace the wrapper's content. The paper jumps to its new size now, while it is empty. On the next frame remove .mbDim. Total 250ms. A second change inside the 90ms only replaces the content that waits (the latest wins). Calm: 60ms out and 120ms in, both linear.


### glide: Words fade and the box glides

The old words fade out, the paper stretches or shrinks smoothly to its new size, and the new words fade in as it lands. When buttons come or go, the height glides the same way.

The words fade as in the dip. The paper moves between sizes on the settings box's height line, 220ms cubic-bezier(.645,.045,.355,1) (Modals.scss:165, --motion-speed and --motion-ease). Every option's .mbIn transition list already carries width and height at those values.
CSS:
.swap-glide .piece.spot-messageBox.mbGliding { overflow: hidden; }
.swap-glide .piece.spot-messageBox .mbBody { transition: opacity 160ms cubic-bezier(.22,1,.36,1) 60ms; }
.swap-glide .piece.spot-messageBox .mbBody.mbDim { opacity: 0; transition: opacity 90ms cubic-bezier(.32,0,.67,0); }
Steps: 1. Read the old content size w0 and h0 (clientWidth and clientHeight minus the padding). The box is content-box, and mixing the two makes the height step by the padding, as Modals.scss:158-162 found. 2. Add .mbDim. 3. At 90ms replace the content and read the new size w1 and h1. Set width and height inline to w0 and h0 with style.setProperty(prop, value, 'important'), which beats width and height auto !important at pieces.scss:1413-1414. Read offsetWidth, then set w1 and h1 the same way. The transition runs because CSS transitions outrank !important (WAAPI animations do not, so do not use them here). Add .mbGliding, and give .mbBody an inline width of w1 so the new words do not rewrap on each frame. 4. Remove .mbDim. The new words fade in from 150ms and land with the paper at 310ms. 5. On the height transitionend (or at 310ms), remove the inline sizes, .mbGliding and the body width. Most messages sit at the width cap (176, 122 or 119px of content), so the height is usually what moves: 44 to 64 for a countdown, or 144 to 64 when the waiting notice becomes the countdown and its buttons go. Calm: the same as the dip's calm, so the size jumps inside the fade.


### roll: Words roll down

The old words slide down out of the box and the new words come down from above, the way a name rolls on a seat plate. The paper glides to its new size at the same time.

This is the roll that the seat plates and the table badge use (_wm-shared.scss:307-330 and 348-355, _fp-open-tables.scss:230-250: the old goes to translateY(100%), and the new comes from -100%). The paper glides as in the glide.
CSS:
.swap-roll .piece.spot-messageBox.mbGliding { overflow: hidden; }
.swap-roll .piece.spot-messageBox .mbBody { transition: transform 220ms cubic-bezier(.22,1,.36,1); }
.swap-roll .piece.spot-messageBox .mbBody.mbOld { position: absolute; }
.swap-roll .piece.spot-messageBox .mbBody.mbFromAbove { transform: translateY(calc(-100% - var(--mb-pad, 12px))); transition: none; }
.swap-roll .piece.spot-messageBox .mbBody.mbOld.mbGo { transform: translateY(calc(100% + var(--mb-pad, 12px))); }
Steps: set --mb-pad to the box's top padding (12, or 8 on a compact board). Make the old wrapper .mbOld, with inline top and left at the padding corner and its old width. Insert the new wrapper with .mbFromAbove. Start the paper glide as in the glide. Read offsetWidth, then remove .mbFromAbove from the new wrapper and add .mbGo to the old one. Remove the old wrapper at 220ms. There is no fade. Calm: the same as the dip's calm.


### tick: Only the number turns

When only a number changes, as in the countdown, the rematch clock or the pause clock, just that number rolls to the next one and the other words stay still. Any other change uses 'Words fade and the box glides'. Recommended.

When only the numbers change, only the changed number rolls, downward, as the table badge's digits do (_fp-open-tables.scss:230-250, 220ms cubic-bezier(.22,1,.36,1)). Any other change runs the glide.
CSS:
.swap-tick .piece.spot-messageBox .mbNum { display: inline-block; position: relative; overflow: hidden; vertical-align: top; font-variant-numeric: tabular-nums; }
.swap-tick .piece.spot-messageBox .mbNum i { display: block; font-style: normal; transition: transform 220ms cubic-bezier(.22,1,.36,1); }
.swap-tick .piece.spot-messageBox .mbNum .mbNumOld { position: absolute; left: 0; top: 0; }
.swap-tick .piece.spot-messageBox .mbNum .mbNumNew { transform: translateY(-100%); }
.swap-tick .piece.spot-messageBox .mbNum.mbGo .mbNumOld { transform: translateY(100%); }
.swap-tick .piece.spot-messageBox .mbNum.mbGo .mbNumNew { transform: none; }
Steps: when Table.js renders, it wraps each run of digits (and an m:ss clock such as 4:59) in <span class='mbNum'>. On a change, compare the old and new text with every digit run replaced by #. If they match, then for each .mbNum whose value changed, put <i class='mbNumOld'>old</i><i class='mbNumNew'>new</i> inside it, read offsetWidth, and add .mbGo. At 220ms leave only the new number in the span and remove .mbGo. The new number stays in the flow, so '10' to '9' narrows the window once. Tabular figures keep '9' to '8' still, if BuloRounded has them (the front page asks for them at _fp-hero.scss:221). If the texts do not match (for example '2 seconds' to '1 second', or the last step to 'Dealing cards...'), run the glide. The lab should show which steps fall back. Calm: the number is replaced with no roll.


## Controls (motion half)

This half needs the following in the sticky knobs bar and on the frames. The toast half keeps its own chooser, which the recipe puts on the up and down keys.

1. Chooser 'How it comes and goes': eight options in this order. Today, Soft fade, Slides in from the side, Slides out of the felt's edge, Rises like the table panels, Rises like the big dialogs, Drops in like the toast (Recommendation pill), Unrolls downward. The left and right arrow keys step through them. The pick sets .opt-<id> on each frame root (div.site.wm).

2. Chooser 'When the words change': five modes, independent of chooser 1. Instant, Words fade and return, Words fade and the box glides, Words roll down, Only the number turns (Recommendation pill). Keys 1 to 5 pick them. The pick sets .swap-<id> on each frame root.

3. Message kinds: one scripted scene per chip. Each scene uses the real texts and the real rhythm, and plays in all three frames (1200x800, 750x340, 390x664) on one clock. Lifespans can be shortened, and the chip says so.
(a) Comes and goes: 'Hearts broken!' stays 1.5s and leaves.
(b) Table fills: the waiting notice 'Table #12 starts when full.' with Start with bots and Invite players (Add bots on a narrow box) shows for 1.5s. Then it becomes 'Table is full. Game will start in 10 seconds.' and ticks each second to '1 second', then 'Dealing cards...', then it leaves. This scene shows the buttons going (144 to 64px on desktop) and the ticks.
(c) Bot bids: 'Waiting for Tin Man to bid.', then EVE, then Buzz. Each is hidden and shown again 4ms later, every 0.8s (spades-game.js:104 and 176).
(d) Turn status: 'Waiting for EVE to play.' changes in place every 1.7s and ends on 'Play a card from your hand.' (crazy eights).
(e) Tip then trouble: the bookmark tip on band paper for 2s, then red 'Notice: Connection problem, reconnecting...', then 'Error: Connection problem' with the red Reload game button, then it clears.
(f) Long words: the cribbage score list, up to 8 lines, changed step by step.
(g) Interruptions: a leave 80ms after an arrival starts, an arrival 80ms after a leave starts, and the same message sent again while it leaves. Today snaps here, and the other options turn round smoothly.

4. Playback: Replay (r), Pause (space), and speeds 1x, 1/2 and 1/5 (slow motion x5), with s to cycle. Add a scrubber over the scene's timeline. Run every step as CSS transitions or WAAPI on each frame's document timeline, then set playbackRate and currentTime through document.getAnimations(). Run the lab's own timers (lifespans, the end of a leave, the 4ms bid gap, the 90ms dip) on the same scaled clock, so slow motion and scrubbing stay true. Today's option must go through its own WAAPI emulation (see its css note), so its snaps show at every speed.

5. Toggles:
- Calm: adds .mbCalm, which plays the reduced-motion and Animations Off version. Turn it on, with a label, when matchMedia('(prefers-reduced-motion: reduce)') matches on Holger's Mac.
- A show during a leave is a change: on by default. When it is off, a show during a leave counts as a new arrival, which brings the blink back.
- Ghost (g): a dashed outline where the box rests, so the travel shows in slow motion.
- Loop.

6. Compare (x): plays Today and the pick in two stacked rows of the three frames at the same time.

7. Readouts for each frame: the total time, the worst frame (a rAF meter as in open-tables-anim-lab), and what the box passes over while it moves. Get the last one from rect checks on every frame against the left and right pills, the North plate, the West seat and the portrait top ad.

---

# Design: where the toast goes

Brief for the placement half of the message box and toast lab: how the toast and the table's message box play together. It gives five placements, eight timed events drawn from real play, and the controls. The recommendation is B, "Stacked in the box's column, two boxes". It is Holger's idea at its simplest. The two pieces keep their own lives, share one style and one column, and the toast glides into the freed place.

What I checked in the source (read-only, nothing edited):
- Notice.js: a new toast does not wait out the old one's time. The old toast is cut at once (190ms leave), then the new one arrives (260ms). Only the latest pending toast survives (showHandler :59-75).
- Notice.js places the container only on show, resize, ad:removed and theme:changed (:189-196, :296-298). It never places it at table create or leave.
- At a table the menu bar is hidden, so the toast's top is the gutter: 16 on desktop, 8 on a phone.
- _wm-notices.scss: the toast has radius 20, padding 14/26 and 16/20 type even when compact (:52-100). The same file says "16px is the smallest size the design writes running text at".
- pieces.scss: the box has `width/height:auto !important` (:1413-1414), so its size cannot be animated directly. The working tree has 16/20 at every size and 14/18 on playspace-small (:2562-2574).
- Table.js resizeAndPositionMessageBox (:1298-1365) writes left, top and the plate cap on the box itself. It reads the box's own `left` to work out the cap. Its comment records Holger's rule from 13 Sep: the box "never moves for its height".
- TableBar.js:1335: when a toast stops a Play-panel action, the Play dropdown stays open. That panel hangs 8px under the left pill with min-width 200, over the box's column.
- The turn hint toast clears on any table action (Table.js:4100-4110).
- Five games read `messageBox.getStyle('display')`, for example cribbage-game-ui.js:1210 and ginrummy-game.js:2617.

A defect that blocks every column option: hideMessage's callback never runs, because Y.Transition.Sequence replaces `cb`. The box therefore stays `display:block` at opacity 0 after its first hide. In a CSS-flow column the freed place would never close. The lab must model the fixed behaviour and say so in its footer. The real build must fix that callback first.

The lab has two axes. "How it moves" (the other half) sets the box's arrive, leave and swap motion. "Where the toast goes" (this half) sets the placement. In B, C and D the toast in the column arrives and leaves with the same motion as the box, so the two read as one set. A keeps today's toast motion. E mirrors it from below.

Measured geometry to use, each piece given as [x, y, width, height]:

| | Desktop 1200×800 (336px ad rail) | Phone landscape 750×340 (160px rail) | Phone portrait 390×664 (100px top banner) |
|---|---|---|---|
| Box anchor | 16,72 | 8,48 | 8,176 (8,76 with ads off) |
| Cap (content / outer) | 176 / 200 | 122 / 138 | 119 / 135 |
| N plate | [232,72,400,40] | [154,48,283,32] | [151,176,88,32] |
| Pills | [16,16,120,40], [728,16,120,40] | [8,8,96,32], [486,8,96,32] | [8,108,96,32], [286,108,96,32] |
| W seat | fan top about 186-194 | avatar [34,119,54,54], plate [8,172,106,32] | fan top about 290, plate [8,389,70,32] |
| Top of your own hand | about 620 | about 255 | about 543 |

Questions for Holger, to put on the lab page:
1. On a phone, should a toast in the column read 14/18 like the box, or keep 16/20?
2. Should the toast be at least as wide as the box, or keep its own width?
3. Should the rare landscape case that overflows fall back to today's place?
4. May the toast cover an open Play panel, or should it stand under the panel?

Evidence files outside the repo: /tmp/msgbox-probe (geometry JSON and shots) and /tmp/toastprobe/comp (composites).


## A: Today: top centre

The toast stays where it is today. It sits at the top of the table, centred over the top player, on its own. The message box and the toast never take notice of each other.

**Rules.** All sizes: the container spans the viewport minus the right ad rail. Its top is the safe area plus the gutter, because the menu bar is hidden at a table. The toast is centred, fit-content, max-width min(640px, container - 32px), type 16/20 at every size, padding 14px 26px, radius --radius-panel 20, band paper, felt ring and shadow (the same computed shadow as the box). z is 10001. The message box does not change the toast's place. The toast does not change the box's place.

Desktop 1200x800: container 0..864, toast top 16. One line is 48 tall (16..64). The longest toasts (VPN line, long hint) are 640 wide and 2 lines (112..752 x 16..84).

Phone landscape 750x340: container 0..590, top 8, max 558 wide. One line is 8..56. Two lines are 8..76 (for example, the shutdown line is 16..574).

Phone portrait 390x664: container 0..390, top 8, max 358 wide. It is often 2 lines (8..76), and the VPN line is 3 lines (8..96). With ads on, the toast lands on the 100px top banner (#ad.mobileTop). With ads off, it lands on the pill row (8..40) and the N avatar.

The box is unchanged at its anchor: 16,72 / 8,48 / 8,176.

Lab switch 'Toast style' (A and E only): today's style, or the table's style (radius --radius-lg, padding 12/8, 16/20 and 14/18 on phones).

**Choreography.** Every event uses today's motion.
- Arrive: from opacity 0 and translateY(-10px) scale(.96), origin centre top, to none, 260ms cubic-bezier(.22,1,.36,1).
- Leave: back to the start, 190ms cubic-bezier(.32,0,.67,0).
- A new toast cuts the old one: the old one leaves over 190ms, then the new one arrives over 260ms.
- The box runs its own motion from the other axis. Nothing moves for the other piece.

By event:
- E1: the toast drops in at top centre and leaves there.
- E2: the one-line hint covers the N avatar's head on desktop. On the landscape phone it covers both pills, the top 8px of the N plate and the top 8px of the pass prompt. On the portrait phone it sits on the banner ad in 2 lines.
- E3: the pause toast and the vote message say the same thing at two places for 3.1s.
- E4 to E6: the box changes under a toast that holds still.
- E7: the second toast replaces the first at top centre.
- E8: the VPN line covers these:
  - Desktop: 24px of both pills, the top 12px of the N plate and of the waiting box.
  - Phone landscape: both pills, the whole N plate and the top 28px of the box.
  - Phone portrait: the banner ad.

**Style.** The two boxes stay different, as today. They share paper, ring, shadow, font and ink. They differ in these ways:
- radius: 20 against 16 on desktop and 12 on a phone (in Safari without the squircle, 20 against 8 and 6)
- padding: 14/26 against 12/8
- type on phones: 16/20 against 14/18
- width: up to 640 against a 135-200 column

The 'Toast style' switch shows how A looks with the table's style. It stays a separate piece in a separate place.

**Implementation.** Nothing changes. Notice.js keeps #NoticeContainer as a child of <body> at z 10001.

If A is kept, fix three known defects anyway, each gated on body.wm:
- Start the container below #ad.mobileTop on a portrait phone.
- Run updatePosition on table:created and table destroy, so a toast shown in the lobby does not float on the table's top row at y≈72.
- Consider holding the toast clear of the pills at desktop widths.

**Risks.** - It covers the pills. The first tap on a covered pill dismisses the toast instead of opening the pill.
- It covers the N avatar and the N plate. On the landscape phone it also covers the top of the box.
- On the portrait phone with ads, it lands on the top banner ad, which can count as covering an ad (see APS-READINESS.md).
- Its place is fixed when it shows, so a toast from the lobby floats on the table's top row for up to 3.46s.
- The table has two paper voices in two styles at two ends of the felt.
- The hint toast sits far from the hand its arrows point at.


## B: Stacked in the box's column, two boxes (recommended)

At a table the toast joins the message box in its corner. If the box shows, the toast hangs just under it, like a second card in the same stack. If there is no box, the toast takes the box's place. When the box goes, the toast slides up into its place. When a box comes, the toast slides down to make room.

**Rules.** Column anchor: the box's own place, unchanged. It comes from resizeAndPositionMessageBox: left = playspace left + gutter, top = playspace top + the top player's row. The box always owns the top slot, because it never moves for the toast.

Per frame:
- Desktop 1200x800: anchor 16,72. Cap 176 content, 200 outer. Padding 12, type 16/20, radius 16.
- Phone landscape 750x340: anchor 8,48. Cap 122 content, 138 outer. Padding 8, type 14/18, radius 12.
- Phone portrait 390x664: anchor 8,176 with the 100px banner, or 8,76 with ads off. CSS max 160, plate cap 119 content, 135 outer. Padding 8, type 14/18, radius 12.

No box: the toast's top-left corner sits on the anchor.

Box showing: the toast's top = the box's bottom + 8px on every size. The gap is the box's own button gap, not the 16px gutter, so the two read as one stack. The left edges are flush at the anchor.

Width:
- max-width = the box's cap, the same number the box gets.
- min-width = the box's current outer width while the box shows (knob 'Toast width: at least the box's' is the pick; the other choice is 'its own': fit-content, min 80).
- Text is left-aligned.

Floor: the stack's bottom must stay one gutter above the top of your own hand at rest. That is about 604 on desktop, 247 on the landscape phone and 535 on the portrait phone. Measure the bottom hand's top card in the snapshot. If the toast would cross the floor, it shows in today's place (A) for that one showing, and the overlay marks 'fallback'.

Open pill panel (optional scene switch): if a left-pill panel is open over the column, the toast stands 8px under the panel's bottom at the anchor's left, and the floor still applies.

z: the toast keeps 10001, so it stays over the pill panels and modals as today. The box keeps 4800.

Lobby and flag-off: today's place.

Expected sizes, so the lab can check its measurements:
- Desktop: one line 44, the hint 3 lines 84, the VPN line 4 lines 104.
- Phones: one line 34, the hint 4 lines 88, the VPN line 5 lines 106.

Stack bottoms:

| Event | Desktop | Phone landscape | Phone portrait |
|---|---|---|---|
| E2 | 72..116 box + 124..208 toast. Grazes the W fan top. | 48..100 + 108..196. Covers the W avatar and 24px of the W plate. | 176..228 + 236..324. Covers about 34px of the W fan. |
| E8 | 72..216 + 224..328 | the floor fails (190..296 > 247), so it falls back to A | 176..310 + 318..424. Covers the W fan and the top of the W plate. |

**Choreography.** General rules:
- The toast arrives and leaves with the box's motion (the 'How it moves' pick). When that pick is 'Today', the toast in the column uses today's toast motion anchored at its top-left: from opacity 0 and translateY(-10px) scale(.96), origin left top, 260ms (.22,1,.36,1). It leaves over 190ms (.32,0,.67,0).
- Glide down to make room: FLIP on the individual `translate` property, 300ms (.22,1,.36,1), the site's FLIP reorder from FrontpageTables.js:821-837. It starts when the box renders. The box's own arrival starts 80ms later, so it lands in a place that is mostly clear.
- Glide up into a freed place: the same 300ms curve. It starts 200ms after the box's hide began (the hold), and only if no message came back in that time. A hide followed by a show within 200ms is a swap, not a leave.
- Follow a box that changes size: the toast moves by the box's height change, with the box's own resize duration and curve. It cuts if the box cuts.
- A toast that is leaving never glides.
- If the box and the toast both leave within 100ms of each other, nothing glides.
- Reduced motion: glides are cuts, and arrivals fade over 120ms linear.

By event:
- E1: the toast arrives on the anchor (16,72 / 8,48 / 8,176) and leaves there.
- E2:
  - t=1200: the hint arrives under the prompt. Its top is 124 on desktop and 108 on the phones.
  - t=4600: the hint leaves in place. In the same frame the box swaps to 'Waiting for other players to pass.' and grows about 20px on desktop. The leaving toast does not follow.
  - t=5400: the box leaves alone.
- E3:
  - t=0: the pause toast arrives on the anchor.
  - t=350: the box renders. The toast glides down by the box height + 8 (92 on desktop), and the box arrives in the top slot from t=430.
  - t=3460: the toast leaves from its lower slot.
  - t=6350: the box leaves.
- E4:
  - t=2000: the maintenance toast arrives under 'Hearts broken!'. Its top is 124 on desktop and 90 on the phones, and it stretches to at least the box's width.
  - t=5000: the box leaves.
  - t=5200: the toast glides up to the anchor, 52px on desktop and 42 on the phones.
  - t=10260: the toast leaves from the anchor.
- E5:
  - t=1500: 'No available seats.' arrives under the waiting box at 224, 190 and 318. It is as wide as the box: 200, 138 and 135.
  - t=1900: the box shrinks to the countdown (-80 on desktop, -64 on the phones). The toast follows up by the same amount on the box's resize curve.
  - The ticks at 2900, 3900 and 4900 do not change the height, so nothing moves.
  - t=4960: the toast leaves.
- E6:
  - t=300: the toast arrives under the status line.
  - The hide-then-show pairs at 800 and 1600 are swaps, so the toast holds perfectly still.
  - t=2400: the box leaves for real.
  - t=2600: the toast glides up to the anchor.
  - t=3760: the toast leaves.
- E7:
  - t=1000: the first toast arrives under the red box.
  - t=1600: it leaves in place.
  - t=1790: the second toast arrives in the same slot. Nothing else moves.
  - t=6000: the red box leaves. The toast is already gone, so there is no glide.
- E8:
  - Desktop and portrait: the toast arrives under the waiting box, as wide as the box.
  - Phone landscape: the floor rule fires and the toast drops in at today's place (A).

**Style.** When a toast is in the column at a table, it takes the box's style:
- radius --radius-lg: 16 on desktop, 12 on phones
- padding var(--space-container): 12, or 8 on a compact board
- type 16/20, and 14/18 on playspace-small
- the same band paper, --shadow-low ring and ink

The toast's 'Hint:' label is already a bold prefix, like the box's 'Tip:' and 'Notice:'. Width is 'at least the box's', so the stack has one clean left edge and never steps inward. The gap is 8.

The only difference left is the red connection box, which stays red over a paper toast. The toast type colours are not built, so a warning toast is plain paper.

The result is two cards from one kit, stacked.

Lab knobs:
- Phone type: 14/18 (the pick) or 16/20. The guide says 16 is the smallest running text, but Holger chose 14/18 for the box on 10 Sep.
- Gap: 8 (the pick) or the gutter (16/8).
- Width: at least the box's (the pick) or its own.

**Implementation.** 1. Fix the defect first. The hideMessage callback must run (Transition.js Sequence drops `cb`), so the box really goes display:none and clears currentMessage. Delay that display:none to max(end of the exit, 200ms after the hide began). Then the 200ms hold comes free from layout, and a show inside the hold cancels it. Check the five games that read display === 'block' (hearts:296, pinochle:211 and 1562, pinochledd:1321, ginrummy:2617, cribbage-ui:1210). With the fix they only see 'block' while a message shows.

2. Table.js owns the column.
   - createMessageBox builds `div.spot-noticeColumn` in #mainContainer when Y.wocg.wantsTableChrome() is true, and puts the box inside it.
   - resizeAndPositionMessageBox writes left, top and max-width on the column instead of on the box. It reads the column's left for the plate cap.
   - CSS, all under body.wm: `.spot-noticeColumn {position:absolute; z-index:auto; display:flex; flex-direction:column; align-items:flex-start; gap:8px; pointer-events:none}`.
   - `.spot-noticeColumn > .spot-messageBox {position:relative; left:auto; top:auto; margin:0}`.
   - z-index:auto makes no stacking context, so the box keeps 4800 and the toast keeps 10001 as flex items.
   - At flag-off there is no column, and the box stays absolute as on master.

3. Notice.js gets a dock.
   - Table fires `Notice:dock` with the column on create (wm only) and `Notice:undock` on destroy.
   - When docked, showNotice appends #Notice into the column before it shows. It reparents only while the toast is hidden, so the aria-live region is not moved mid-message.
   - The toast gets a `docked` class that carries the table style: `body.wm .spot-noticeColumn > #Notice.wmNotice {border-radius:var(--radius-lg); padding:var(--space-container); max-width:100%}`, with 14/18 under #mainContainer.playspace-small.
   - On undock it goes back to #NoticeContainer and today's place.
   - The lobby never docks, so it keeps today's place under the menu bar.
   - The toast is shared at flag-off (D3), so every new rule is keyed to body.wm plus the dock.

4. FLIP.
   - A ResizeObserver on the box, plus the box's show and hide, records the toast's top before the change and reads it after layout. It then plays `toast.animate([{translate:'0 dYpx'},{translate:'0 0'}], {duration, easing})`.
   - It uses the individual translate property, so it composes with the wmIn transform.
   - Down or up: 300ms SETTLE. Resize: the box's own resize timing.
   - While the toast shows, min-width is set from the box's offsetWidth.

5. Floor.
   - Before a docked show, measure the toast in the column (visibility hidden).
   - If column top + box height + 8 + toast height > the bottom hand's resting top (from Layout) - gutter, show in #NoticeContainer at today's place instead.
   - With a left-pill panel open, stack under the panel.

6. Carry-over. If a toast is showing when the dock arrives (a practice-blocked toast plus a new solo table), move it into the column with a FLIP from its fixed rect (300ms SETTLE). This replaces today's toast floating at y≈72.

7. Ad rail and banner: not involved. The column lives inside the playspace's left edge, so the portrait banner is never covered.

8. Notice:hidden still reaches noticeHiddenHandler, so the turn-hint arrows clear as today.

**Risks.** - The column is narrow (135-200px). Long toasts wrap to 4-5 lines and cover the top of the W seat (avatar, fan, plate) for 3-8s.
- On the landscape phone, a long toast under the waiting message fails the floor and falls back to today's place, so B has a second look in that rare case.
- It cannot ship without the hide-callback fix, and that fix changes what five games see when they test the box's display.
- The Play panel stays open after a blocked click (TableBar.js:1335) and hangs over the column. The toast either covers the panel's first rows, or stands under the panel, which is taller and may hit the floor.
- The toast has two homes on the site: the column at a table, and top centre in the lobby.
- The toast is shared at flag-off, so any rule that escapes the body.wm gate changes master's look.
- 14/18 on phones goes below the guide's 16px floor for running text.
- The hint toast still sits far from the cards its arrows point at.


## C: Stacked in the box's column, one card

The toast becomes the lower part of the message box. There is one card with one frame, and a thin line between the box's words and the toast's words. The card grows downward when a toast joins and shrinks back when it goes. With no message, the card holds only the toast.

**Rules.** The anchor, cap, floor, fallback and z are the same as B.

The card's top-left corner sits on the box's anchor: 16,72 / 8,48 / 8,176 (8,76 with ads off).

Card width = the widest section, up to the cap (200 / 138 / 135 outer). A wide toast under a short message widens the whole card.

Sections:
- The message section is on top and the toast section is below, always.
- Each section has the box's padding: 12, or 8 compact.
- Between them is a 1px divider in --line #d2cfca, the width of the card inside the ring.

Outer radius: --radius-lg, 16 on desktop and 12 on phones. One --shadow-low ring goes round the whole card.

Type: 16/20 on desktop and 14/18 on phones for both sections.

The floor counts the whole card. On the landscape phone in E8 the toast leaves the card and shows in today's place.

**Choreography.** General rules:
- The card's top-left corner never moves.
- Growing: the card's paper edge moves down, by clip-path inset on the card's paper layer, 260ms SETTLE. The new section's words ink in: opacity 0 to 1 over 160ms linear, after 100ms. The divider fades in with them.
- Shrinking: the words ink out over 120ms linear, then the edge moves up over 190ms SHARP.
- Words that must change place glide with a FLIP translate, 300ms SETTLE.
- A width change moves the right edge over 220ms cubic-bezier(.645,.045,.355,1), the site's EASE.
- Reduced motion: cuts, with a 120ms fade.

By event:
- E1: the card arrives holding only the toast's words, with the box's arrival motion, and leaves with its exit.
- E2:
  - t=1200: the card grows under 'Select 3 cards to pass left.'. The divider comes, then the hint's words.
  - t=4600: the hint section folds up while the message words swap.
  - t=5400: the card leaves.
- E3:
  - t=0: a card with the pause toast's words.
  - t=350: the card grows by the message section at its top. The toast's words glide down 92px (desktop) and the vote message inks in above the divider.
  - t=3460: the lower section folds away.
- E4:
  - t=5000: 'Hearts broken!' inks out.
  - t=5200: the toast's words glide up to the top of the card, the divider fades and the bottom edge rises in step.
- E5:
  - t=1500: the toast section grows under the two buttons.
  - t=1900: the top section shrinks to the countdown. The toast's words and the bottom edge rise by 80px (desktop) or 64px (phones), in step.
- E6: the top section swaps in place while the bottom holds still. At t=2600 the top section is gone and the toast's words glide up.
- E7:
  - The top section is red and the bottom is paper, inside one ring.
  - t=1600: the lower section's words ink out.
  - t=1790: the bottom edge follows the new height and the second toast's words ink in.
- E8: as B. On the landscape phone the toast shows in today's place.

**Style.** There is one card, so the style is shared by construction: one paper, one ring, one outer radius, one padding and one type size.

The divider on the same paper is the guide's 'divider on the same paper' (3.3). It is what tells the table's state from the passing remark.

The red connection box is the hard case. A red section over a paper section inside one ring. The lab should show it, because it is the moment the one-card idea looks least like one card.

**Implementation.** This is B's column plus a new wrapper `.spot-noticeCard` that owns the paper, ring, radius and clip. The box and the docked toast become unpainted sections inside it, in rules gated on body.wm.

- The wrapper's paper is a pseudo-element or an inner layer. Its clip-path or height is animated, because the box's own width and height are !important.
- `:has(> #Notice.wmIn)` draws the divider.
- Notice.js docks into the card instead of into a column.
- The FLIP, floor, fallback and hide-callback fix are the same as B.

It costs more than B. One painted element now carries two lifecycles and two timers. Every change to either one must move the shared edge, and the red variant needs its own section paint.

**Risks.** - It is the most code, and there are two lifecycles on one element.
- It mixes red and paper in one ring.
- Under the waiting message's buttons, the toast section can read as part of the message or as a third button row.
- A click dismisses only the lower section, which is not obvious on one card.
- A wide toast under a short message makes the box itself widen. The box was meant never to move.
- The box must lose its own paint inside the card, which is new gating work next to master's classic box.
- All of B's risks apply: the narrow column, the W seat, the landscape fallback and the open Play panel.


## D: The box speaks the toast

At a table the toast has no box of its own. Its words go into the message box for the toast's time, then the box's own words come back. If the box has buttons or is the red connection box, the toast stands under it as in B.

**Rules.** The place and size are exactly the box's own, at every size: anchor 16,72 / 8,48 / 8,176, cap 200 / 138 / 135 outer, padding 12 or 8, type 16/20 or 14/18, radius 16 or 12.

The toast's words and its bold 'Hint:' label render inside the box.

Fallback to B when the box shows buttons (the waiting message, redeal, Reload game) or is the red .resync box: the toast then stands 8px under it with B's rules, floor included.

Hold: while the box speaks the toast, messages that arrive or change are held, and the latest one wins. Each keeps its own timer from its arrival. If its time runs out during the toast, it does not come back.

The toast's time is Notice.js's: duration + 260ms.

A click on the box while it speaks the toast ends the toast, as a click on today's toast does.

Lobby: today's place.

**Choreography.** General rules:
- The box's words step aside and the toast's words step in with the 'How it moves' swap motion. The box resizes with that swap.
- At the end, the latest held message steps back with the same swap. If no message is left, the box leaves with its exit.
- If there was no box, the box arrives carrying the toast.

By event:
- E1: the box arrives in its place saying 'Can't chat with bots.' and leaves at t=3460.
- E2:
  - t=1200: 'Select 3 cards to pass left.' swaps to 'Hint: Pass the Q♠ and high hearts…'. The prompt is gone while the hint speaks.
  - t=4600: it swaps to 'Waiting for other players to pass.'.
  - t=5400: the box leaves.
- E3:
  - t=0: the box arrives with the pause toast.
  - t=350: the vote message is held.
  - t=3460: it swaps to 'You requested to pause the game. 1 of 2 votes needed to pause.'.
  - t=6350: the box leaves.
- E4:
  - t=2000: 'Hearts broken!' swaps to the maintenance line.
  - t=5000: 'Hearts broken!' runs out underneath.
  - t=10260: the box leaves.
- E5, E7 and E8: the box has buttons or is red, so the toast behaves as in B.
- E6:
  - t=300: 'Waiting for [W bot] to bid.' swaps to 'Can't chat with bots.'.
  - The bid updates at 800 and 1600 and the real hide at 2400 are held.
  - t=3760: the box leaves, because no message is left. The toast never makes the box blink.

**Style.** Nothing to unify. The toast is the box for its time: the box's radius, padding, type, width and paper.

In the fallback cases it takes B's docked style.

**Implementation.** Notice.js, when docked, hands the options to Table (`table.speakNotice(options)`) instead of drawing #Notice.

Table reuses the path that showTableError already uses. The table error takes the box and stores the message behind it (messageBeforeTableError), then gives the box back (hideTableError). That store is the same one that today brings back an expired message, so the hide-callback fix is required.

The box needs role=status and aria-live=polite while it speaks the toast. It must fire Notice:hidden with the toast's options at the end, so the turn-hint arrows clear.

The fallback means D needs all of B's column code as well.

**Risks.** - It hides the table's state while it speaks: the pass prompt for 6.4s during the hint, a live countdown or pause timer, and bid status.
- Buttons would vanish, hence the fallback. So D has two looks, and still costs B's code.
- The held-message store is the one that today brings back stale messages.
- One box with two voices makes it unclear what the table's state is.
- Click-to-dismiss on the box competes with the box's own links.


## E: Near your hand

The toast stands centred just above your own cards, where you act, and the message box stays at the top. The two never meet. The hint appears right above the cards its arrows point at.

**Rules.** The toast is centred on your own plate's centre: x = 432 on desktop, about 295 on the landscape phone and 195 on the portrait phone.

Its bottom edge = the resting top of your own hand's cards - gutter: about 604 on desktop, 247 on the landscape phone and 535 on the portrait phone. Measure the bottom hand's top card. With no hand (a spectator), use the top of the bottom plate - gutter.

Width: fit-content, max-width min(480px, playspace width - 2 x gutter). That is 480 on desktop and landscape, and 374 on portrait.

Style: from the 'Toast style' switch. The default is the table's: radius --radius-lg, padding 12/8, 16/20 on desktop and 14/18 on phones.

z: 10001.

Expected VPN line:
- Desktop: 2 lines, about 536..604.
- Phone landscape: 2 lines, about 179..247, over the bottom of the trick (138..210).
- Phone portrait: 3 lines, about 447..535, clear.

The box stays at its anchor and never interacts.

Lobby: today's place.

**Choreography.** General rules:
- Arrive rising from below: from opacity 0 and translateY(+10px) scale(.96), origin bottom centre, to none, 260ms SETTLE.
- Leave back down: 190ms SHARP.
- A new toast cuts the old one: 190ms, then 260ms.
- Nothing glides. The box and the toast never move for each other.
- Reduced motion: a 120ms fade.

By event:
- E1: the toast rises above your hand and sinks away.
- E2: the hint rises right above your cards. At t=4600 it sinks while the box swaps at the top. The overlay marks where hearts' Pass button would stand.
- E3: the pause toast is at the bottom and the vote message is at the top. The same news appears at both ends.
- E4 and E5: the box leaves or shrinks at the top while nothing moves at the bottom.
- E6: at t=2400 the overlay marks where the bid chooser opens, which is not drawn.
- E7: the second toast replaces the first at the bottom.
- E8: the VPN line in 2 or 3 lines. The landscape frame reports the trick overlap.

**Style.** The two are never stacked, so they only need to look like one kit on the felt. With the default table style they share radius, padding and type. The toast keeps its own width, because it has room.

**Implementation.** Notice.js asks Table for a hand anchor: `{centerX, bottom}` from Layout's bottom seat (hand top at rest, or the plate top when there is no hand). It is docked on table create under body.wm and undocked on destroy.

The container is anchored by its bottom (`bottom` set from the playspace height), centred on centerX, and keeps z 10001.

Games with a meld row above your hand (canasta, hand and foot, rummy, gin rummy) need the anchor above the melds. Spot panels (choosers, Pass and action buttons) sit in the same band, so the anchor would have to step above them when they show.

The lobby keeps today's place.

**Risks.** - It covers the trick on the landscape phone.
- At z 10001 it covers choosers and action buttons that stand above your hand, such as the hearts Pass button, the spades bid chooser and the cribbage and gin action rows.
- There is no free band in meld games.
- A lifted card rises into it.
- A toast that answers a click on a top pill appears at the other end of the table.
- Spectators and tutorials need another anchor.
- It does not do what Holger asked. It is here as the strong alternative.


## Events


### E1: A toast with no message

Scene: Hearts mid-hand, your turn, no message box.
- t=0: toast 'Can't chat with bots.' shows (type warning, 3200ms). You tapped the chat button by your plate.
- t=260: the toast is settled.
- t=3460: the toast starts to leave.
- t=3650: the toast is gone.
- End: t=4200.

Long-text switch: 'Game will pause if all players agree. Use Resume to cancel your request.'


### E2: The turn hint joins the pass prompt

Scene: Hearts, passing phase.
- t=0: message 'Select 3 cards to pass left.' shows. It is a phase prompt and stays.
- t=1200: toast shows with label 'Hint:' and text 'Pass the Q♠ and high hearts. Hints can be disabled under settings.' (6400ms, noticeKey turnHint).
- t=4600: you press Pass. The toast starts to leave, because the hint clears on a table action. In the same frame the message swaps to 'Waiting for other players to pass.'.
- t=4790: the toast is gone.
- t=5400: the phase ends and the message hides.
- End: t=6000.


### E3: A message arrives while a toast is up (the pause)

Scene: Hearts mid-hand, no message box.
- t=0: toast 'Game will pause if all players agree. Use Resume to cancel your request.' shows (info, 3200ms). You pressed Pause.
- t=350: message 'You requested to pause the game. 1 of 2 votes needed to pause.' shows (6000ms).
- t=3460: the toast starts to leave.
- t=3650: the toast is gone.
- t=6350: the message hides.
- End: t=7000.


### E4: The message leaves while a toast is under it

Scene: Hearts mid-hand.
- t=0: message 'Hearts broken!' shows (5000ms).
- t=2000: toast 'The server goes down for maintenance in about ten minutes. It comes straight back.' shows (warning, 8000ms).
- t=5000: the message's time is up and it hides.
- t=5200: the hold ends with no new message, so the message's place is free and the column closes up.
- t=10260: the toast starts to leave.
- t=10450: the toast is gone.
- End: t=11000.


### E5: The message changes size while a toast is under it

Scene: Hearts private table, waiting, one seat open.
- t=0: message 'Private table <b>Friday night</b> starts when full.' shows with the buttons 'Start with bots' (short 'Add bots') and 'Invite players'. It stays.
- t=1500: you press Invite players just as the last seat fills. Toast 'No available seats.' shows (warning, 3200ms).
- t=1900: the message swaps to 'Table is full. Game will start in <b>10 seconds</b>.'. The buttons go and the box shrinks.
- t=2900: '…<b>9 seconds</b>.'
- t=3900: '…<b>8 seconds</b>.'
- t=4900: '…<b>7 seconds</b>.'
- t=4960: the toast starts to leave.
- t=5150: the toast is gone.
- End: t=5600.


### E6: Bots bid while a toast is up (the blink)

Scene: the Hearts table played as Spades bidding. Use the scene's W, N and E bot names.
- t=0: message 'Waiting for [W bot] to bid.' shows (status).
- t=300: toast 'Can't chat with bots.' shows (warning, 3200ms).
- t=800: the message hides.
- t=804: message 'Waiting for [N bot] to bid.' shows. This is the game's hide-then-show, and it must read as one swap.
- t=1600: the message hides.
- t=1604: message 'Waiting for [E bot] to bid.' shows.
- t=2400: the message hides for real, because it is your bid. The bid chooser opens but is not drawn.
- t=2600: the message's place is free.
- t=3760: the toast starts to leave.
- t=3950: the toast is gone.
- End: t=4500.


### E7: Two toasts in a row over the red connection box

Scene: Hearts mid-hand, connection lost.
- t=0: red message (class resync) '<strong>Notice:</strong> Connection problem, reconnecting...' shows. It stays.
- t=1000: toast 'Connecting to server, please wait...' shows (info, 3200ms). You tapped Browse tables.
- t=1600: you tapped the Hint button, which asks for the toast 'No hint available right now.'. The first toast starts to leave.
- t=1790: the first toast is gone and the second starts to arrive.
- t=2050: the second toast is settled.
- t=5250: the second toast starts to leave.
- t=5440: the second toast is gone.
- t=6000: the connection is back and the red message hides.
- End: t=6600.


### E8: The tallest stack: waiting message with buttons plus the longest toast

Scene: Hearts private table, waiting.
- t=0: message 'Private table <b>Friday night</b> starts when full.' shows with 'Start with bots' / 'Add bots' and 'Invite players'. It stays.
- t=1000: toast 'Multiplayer is disabled on VPN or proxy connections. Turn off your VPN to play with other people.' shows (warning, 3200ms). You tapped Join table in the Play panel. The panel stays open, because a notice stopped the action (TableBar.js:1335).
- t=4460: the toast starts to leave.
- t=4650: the toast is gone.
- End: t=5200.

Text switch: 'Finish a Hearts practice game against bots before joining a multiplayer table.'

This event shows the floor fallback on the landscape phone and the W seat overlap on the other two frames. Play it with the portrait frame's ads on and off.


## Controls (placement half)

This is the placement half of the lab. It sits next to the motion half's 'How it moves' chooser, and both use one timeline.

Choosers, in the sticky knobs bar:
- 'Where the toast goes', a segmented chooser: A Today: top centre / ★ B In the box's column, two boxes / C In the box's column, one card / D The box speaks the toast / E Near your hand. The ★ marks the recommendation.
- 'Event': E1 to E8, with plain names.
- Replay.
- Speed: quarter, half and full, which sets playbackRate on every animation.
- Pause and a scrubber: pause() plus currentTime.
- Fit or Real size, for the frames.

Sub-knobs, shown only where they apply:
- 'Toast width' (B, C): at least the box's ★, or its own.
- 'Gap' (B): 8 ★, or the gutter (16/8).
- 'Phone type' (B, C, D, E): 14/18 like the box ★, or 16/20.
- 'Toast style' (A, E): today's, or the table's ★.
- 'Long text' (E1, E8): switches to the alternative string.
- 'Ads' (portrait frame): on or off. It moves the playspace top and the box anchor between 176 and 76.
- 'Play panel open' (optional scene switch): opens the left pill's Play dropdown from the snapshot, to show B's under-the-panel rule.
- 'Reduced motion preview'. The page also says so if the Mac has Reduce Motion on.

Frames: three real-size iframes, drawn with site.css: desktop 1200x800 on row 1, then iPhone landscape 750x340 and portrait 390x664 side by side on row 2. Every event plays in all three at once. The portrait frame is the 'phone portrait case'.

Overlay (key 'o'):
- It outlines what the toast touches: left pill, right pill, N plate, N avatar, score board, W seat (avatar, plate, cards), your own hand, the trick, the top banner ad, the open panel.
- It draws the floor line, one gutter above your own hand.
- It labels 'fallback' when B, C or D sends a toast to today's place.

At a glance table: one row per placement, one column per frame. For the current event it lists what the toast touches, the lowest stack bottom in px, and whether the fallback fired. The ★ row is marked as the recommendation.

Keys:
- ↑ / ↓: step the placement.
- ← / →: step the motion (the other half).
- [ and ]: the previous or next event.
- r: replay.
- space: pause.
- s: cycle the speed.
- x: flip between Today (A with today's motion) and the current pick.
- o: the overlay.
- f: fit.
- c: compare mode, which shows two placements side by side, each with its own three frames.

Flash a small HUD on each key.

State lives in the hash, for example `#place=B&ev=E4&w=min&gap=8&ptype=14&ads=1&anim=…`.

Build note: before it builds an event's timeline, the frame lays out every state of that event off-screen (visibility hidden) to measure the box and toast heights. The FLIP distances, the hold (200ms after a hide with no new show), the floor test and the fallback are then known up front. Scrubbing and slow motion work on every piece.

Model the fixed hide callback: the box goes display:none after its exit and the hold. The footer says this differs from the live site today.