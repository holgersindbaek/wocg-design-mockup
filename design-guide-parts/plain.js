// The plain words for each card: what the piece is, and what to look at. Holger reads this page to judge the
// design by eye, so a card leads with a sentence in plain words and the builder's title is replaced where it
// was jargon. Keyed by the section's id and by the title the fragment carries, so a card can move freely; a
// card with no entry here is reported by check-page.js as plainless.
window.PlainSections = {
 "roots": "Where the design's colours, paper and ink come from, and the switch that turns the new design on.",
 "type": "The two fonts, the sizes they come in, and what each size is used for.",
 "shape": "The corners, the lines around and between things, and the shadows they sit on.",
 "space": "The gaps between things, how wide a page is, how tall a control is, and what changes as the window narrows.",
 "buttons": "Every button and every link, in each colour and size, and what they do under the pointer.",
 "fields": "The boxes you type in, and the controls for picking one option out of a few, or several at once.",
 "chips": "The small marks: tags, the rating arrows, dots, counts and the badges at a seat.",
 "cards": "The containers: the white card, a game tile, a table tile, the modal box and the panels that float.",
 "tables": "Every table and list the site draws, from the tight one in a lobby card to the one on a leaderboard page.",
 "heads": "The headings, and the lines that part one part of a page from the next.",
 "panels": "The things that open over the page, the tooltip, the notices and the avatars.",
 "chrome": "The menu bar, the footer and the ad column: the frame every page sits in.",
 "motion": "How things move: the thumb, a press, arriving and leaving, and what happens if you ask for less motion.",
 "copy": "The words: what a button says, what a column is called, and the order the options sit in."
};

window.Plain = {
 "roots": {
  "The four roots and the shared palette": {
   "title": "Where every colour comes from",
   "lead": "One set of colours is handed to the frontpage, the reading pages, the modals and the notices. This card is the proof that they all get the same set, so nothing drifts apart."
  },
  "What each root gates": {
   "title": "What the frontpage switch changes",
   "lead": "The frontpage hides the old page body and runs the full height of the window. This is what is turned on and off when a page is the frontpage."
  },
  "The modal kit’s own tokens": {
   "title": "The modal's own settings",
   "lead": "A modal needs a few things the rest of the site has no name for: the box, its ring, the dark sheet behind it and its two widths."
  },
  "Page paper and the body’s own type": {
   "title": "The paper and ink a page starts with",
   "lead": "Before anything is drawn, a page is warm paper with the interface font and a near black ink. Look at whether the paper and the ink read right."
  },
  "The flag": {
   "title": "The switch that turns the redesign on",
   "lead": "Which pages get the new design, and how that choice is remembered. There is nothing to look at here. It is written down so the rule is not lost."
  }
 },
 "type": {
  "The two faces": {
   "lead": "The two fonts the site uses, one for the interface and one for headings. Look at whether they sit well together, and note that a missing weight falls back to another font."
  },
  "Cap heights match, not nominal sizes": {
   "title": "Why a heading is set smaller than it sounds",
   "lead": "The two fonts draw their capital letters at different heights, so a heading is set a little smaller to match the text under it. Look at whether a heading and its text feel the same size."
  },
  "The UI ladder": {
   "title": "The five sizes of interface text",
   "lead": "All interface text is one of five sizes. Look at whether the steps are far enough apart to read as different sizes."
  },
  "Off-ladder sizes that ship": {
   "title": "Five sizes that break the rule",
   "lead": "Five places use a size that is not one of the five. They are gathered here so you can say whether to keep them."
  },
  "Rules of the ladder": {
   "title": "What a heading never does",
   "lead": "No underline, no capitals, no letter spacing, and no page loads a font of its own. Look for a heading here that breaks it."
  },
  "The display scale": {
   "title": "The heading sizes",
   "lead": "The five sizes the heading font takes, from a page title down to a quote."
  },
  "Roles: running text and small print": {
   "title": "Text on a page",
   "lead": "Running text, a quiet line, a by-line, small print, and a modal's title and body. Look at whether the line that matters is the one that stands out."
  },
  "Roles: buttons, trays, tags and tables": {
   "title": "Text on the controls",
   "lead": "The words on buttons, trays, chips, tags and table rows. Look at whether a button's words carry the right weight beside a table's."
  },
  "Roles: the bar, the panels and the footer": {
   "title": "Text on the chrome",
   "lead": "The menu links, the games panel, the dropdowns and the footer. Look at whether the chrome stays quieter than the page it frames."
  }
 },
 "shape": {
  "The radius ladder, the 20 rung": {
   "title": "Corners: the big round, on boxes and tiles",
   "lead": "The largest corner in the design, on a modal box, a game tile, a table tile and the big cards."
  },
  "The radius ladder, the 16 rung": {
   "title": "Corners: the card round",
   "lead": "The white card inside a modal, and the notices, which take a smaller corner on a small window."
  },
  "The radius ladder, the 14 rung": {
   "title": "Corners: the tray round",
   "lead": "The games bar's track is one step rounder than the cells inside it, so the cells sit inside its curve."
  },
  "The radius ladder, the 12 rung: the controls": {
   "title": "Corners: the control round",
   "lead": "Every button, field, tray cell, checkbox and tooltip takes the same corner. Look at whether they read as one family."
  },
  "The radius ladder, the 12 rung: the literals": {
   "title": "Corners: the ones written by hand",
   "lead": "Four places write the same corner as a plain number instead of reading the shared one: the yellow buttons, the author photo, the quote avatars and the settings tiles."
  },
  "The radius ladder, the 8 rung and the round 6": {
   "title": "Corners: the small chip, and the one true arc",
   "lead": "A movement chip and a tag take a small corner. The progress bar is one of only three things in the design drawn with a real arc instead of a squircle."
  },
  "The radius ladder, round and none": {
   "title": "Corners: fully round, and none at all",
   "lead": "Dots, badges and the live capsule are circles. The ad rail and the full width bands have no corner at all."
  },
  "Rings: the inset 1px edge": {
   "title": "The thin line around a piece",
   "lead": "Most pieces are outlined by a hairline drawn just inside them. Look at whether the line is strong enough to hold the shape without being noticed."
  },
  "Borders: a real 1px line": {
   "title": "Where the line is a real border instead",
   "lead": "A few pieces draw a real border, because a line drawn inside a tight curve renders at about half strength."
  },
  "Rings drawn outside, and the focus ring": {
   "title": "Lines drawn outside the piece",
   "lead": "The modal box, a name plate on the felt and the author photo wear their line outside. A field you are typing in keeps its thin line and darkens it."
  },
  "The edge over tile art": {
   "title": "The line over a game tile's picture",
   "lead": "Art that runs to the edge would cover a line drawn beneath it, so the tile draws its line on top, softly."
  },
  "Dividers": {
   "title": "The line between two rows",
   "lead": "The line that parts two rows of the same colour is quieter than the line that bounds a piece. Look at whether it separates without cutting."
  },
  "Lift: light containers": {
   "title": "The shadow under a card or a panel",
   "lead": "The soft shadow every light container sits on. On the frontpage it is lighter, so it does not vanish against the coloured paper."
  },
  "Lift: tiles, and the hover": {
   "title": "The shadow under a tile, and on hover",
   "lead": "A game tile sits higher than a card, and rises further when you point at it."
  },
  "Lift: the modal’s card and its box": {
   "title": "The shadow inside a modal",
   "lead": "A white card in a modal takes half the usual shadow, and the box itself takes none: a shadow on a dark blurred sheet reads as a second edge."
  },
  "Lift: the solid buttons and the thumbs": {
   "title": "The shadow under a solid button",
   "lead": "The lobby's buttons and the green thumbs sit on a small drop. A button inside a modal has none."
  },
  "Lift: an avatar on the felt": {
   "title": "The shadow under an avatar at the table",
   "lead": "An avatar's shadow follows the drawing's own outline rather than its box, so it sits on the felt instead of floating over it."
  }
 },
 "space": {
  "The rhythm: 4, 6, 8 and 10": {
   "title": "The small gaps",
   "lead": "Where the four smallest gaps are used. Look for two pieces anywhere that feel too close or too far apart."
  },
  "The rhythm: 24, 28, 44 and 56": {
   "title": "The big gaps",
   "lead": "The page gutter, the space above a heading, and the space between one section and the next."
  },
  "The rhythm: 12, 16 and 18": {
   "title": "The middle gaps",
   "lead": "Inside a box, between two pieces, and the gap of every grid on the page."
  },
  "Columns: 1160 outer, 1112 inner": {
   "title": "How wide the page is",
   "lead": "The content stops at one width, and keeps the same distance from the window's edge everywhere on the site."
  },
  "The reading measure: 680 in a 728 column": {
   "title": "How wide a line of reading is",
   "lead": "A page of text is held to a column you can read without losing your line. Look at whether the lines feel the right length."
  },
  "The modal box, and the ad rail": {
   "title": "How wide a modal and the ad column are",
   "lead": "A modal is one of two widths, narrow or wide, and never touches the window's edge. The ad column keeps the sizes the ads need."
  },
  "Control heights: 56 and 40": {
   "title": "How tall: the big rows",
   "lead": "The menu bar, a corner notice, a leaderboard row, and a settings row carrying a second line."
  },
  "Control heights: 32": {
   "title": "How tall: a button and a field",
   "lead": "The everyday control height. Look at whether a button and a field standing side by side line up."
  },
  "Control heights: 28 and 24": {
   "title": "How tall: the small controls",
   "lead": "A tray and its cells, a small button, a checkbox and the games bar."
  },
  "Control heights: 20, 18 and 16": {
   "title": "How tall: the smallest pieces",
   "lead": "A badge on a seat, a name plate on a tile, a tag and a movement chip."
  },
  "The breakpoints, and what this window matches": {
   "title": "What changes as the window narrows",
   "lead": "The widths at which the design rearranges itself, and which of them your window is in right now."
  },
  "Four probe frames": {
   "title": "The same page at four widths",
   "lead": "The whole page drawn at 1200, 900, 700 and 480 wide. Look through each one for anything that breaks or crowds."
  }
 },
 "buttons": {
  "The kit on the frontpage": {
   "title": "The buttons on the frontpage",
   "lead": "Every button the lobby uses, in each colour and both sizes. Look at whether they rank right: the one you should press most should look like it."
  },
  "The kit in a modal, the actions": {
   "title": "The buttons inside a modal",
   "lead": "The same buttons in a dialog, flatter, with no drop under them."
  },
  "The tray, the danger pair and the inert pill": {
   "title": "The quiet one, the dangerous pair and the one already done",
   "lead": "The plain button, the red pair for something you cannot undo, and the flat pill for an invite that has already gone out."
  },
  "The yellow verb, on the felt": {
   "title": "The yellow button at the table",
   "lead": "The button that names what to do next in a game. Look at whether it stands out enough on the green felt."
  },
  "Hover, press and disabled": {
   "title": "What a button does when you touch it",
   "lead": "Point at the first button to see the hover. A press shrinks it very slightly. A button that cannot be used fades."
  },
  "Two buttons in a box, the foot": {
   "title": "Two buttons at the foot of a dialog",
   "lead": "How a pair of buttons shares the width at the bottom of a modal."
  },
  "Links": {
   "lead": "A link in running text, and the quieter links in the menu, the panels and the footer. Point at one to see its underline."
  },
  "The catalog's dropup": {
   "title": "The menu that opens from a Play button",
   "lead": "The sheet that comes out of the top of a game tile's Play button."
  }
 },
 "fields": {
  "The field": {
   "title": "A text field",
   "lead": "The box you type in, at rest and while focused. Click into it to see the focus ring."
  },
  "The field on a white card, and a bad one": {
   "title": "A field on a white card, and one with an error",
   "lead": "On a white card the field changes its paper so it still reads. A field with a problem turns its ring red and says what is wrong."
  },
  "The search field, at 26": {
   "title": "The small search field",
   "lead": "The smaller field that sits in a table head. The one that ships is the player search on a per-game leaderboard."
  },
  "The tray, in a modal and on a white card": {
   "title": "The tray: picking one of a few",
   "lead": "The control for choosing one option from two or three. Click a cell and the green thumb travels to it."
  },
  "The checkbox": {
   "title": "The checkbox, picked and not",
   "lead": "A box you can tick, the height of a small button, with its number after it. Click it and the tick draws itself in; click again and box and tick fade together."
  },
  "The settings tabs": {
   "title": "The settings tabs",
   "lead": "The same tray one size up, used as the tabs across the top of the settings box."
  },
  "The tray on a page": {
   "title": "The tray on a leaderboard page",
   "lead": "The per-game leaderboard draws its own copy of the tray. It should be impossible to tell apart from the one above."
  },
  "The games bar": {
   "title": "The games bar",
   "lead": "The row of games at the top of the lobby, each with the number of people playing. Click one and the thumb travels."
  },
  "The games bar in a modal": {
   "title": "The games bar inside a dialog",
   "lead": "The same bar in a modal, built from the same recipe rather than from a copy of it."
  }
 },
 "chips": {
  "The tag": {
   "lead": "The small label on the What's new row and on the changelog page."
  },
  "The movement chips": {
   "title": "The rating up and down chips",
   "lead": "How a rank or a rating that moved is shown, each with its arrow. Up is green, down is red."
  },
  "Dots": {
   "title": "The presence dots",
   "lead": "The small round mark that says someone is online, and the live dot in the hero."
  },
  "The count chip on a tile": {
   "title": "The player count on a game tile",
   "lead": "The number of people playing, written over the tile's own art."
  },
  "Badges on a seat": {
   "title": "The marks on a seat at the table",
   "lead": "The bot mark, the finished badge and the daily challenge number that sit at a player's plate."
  }
 },
 "cards": {
  "The white card, in a modal and on a page": {
   "title": "The white card",
   "lead": "The plain white card, in a modal and on a page. Look at whether the two read as the same card."
  },
  "The game tile, hero and catalog": {
   "title": "The game tile",
   "lead": "The tile for a game, large in the hero and small in the catalog. Point at one to see it rise."
  },
  "The felt tile": {
   "title": "The table tile",
   "lead": "A table in play, with its seats and the people at them. Look at whether you can read who is at the table at a glance."
  },
  "The other paper cards, the photo and the quote avatar": {
   "title": "The other cards",
   "lead": "The leaderboard card, the quote card and the picture card."
  },
  "The modal box": {
   "title": "The modal box",
   "lead": "The box a dialog is drawn in, over the darkened page behind it."
  },
  "The floating containers, geometry": {
   "title": "The panels that float over the page",
   "lead": "A dropdown panel, the toast and the notices, and how each one is put together."
  }
 },
 "tables": {
  "The compact card table": {
   "title": "The small table in a lobby card",
   "lead": "The leaderboard on the lobby card: tight rows on alternating paper."
  },
  "The stats table in a modal": {
   "title": "The table inside a modal",
   "lead": "A stats table in a dialog, with your own row in bold."
  },
  "Settings rows": {
   "title": "A settings row",
   "lead": "A row with its title, a line of explanation and its control at the right."
  },
  "People rows": {
   "title": "A row with a person in it",
   "lead": "The row the invite, profile and table lists are built from: an avatar, a name and a second line."
  },
  "The page table": {
   "title": "The table on a page",
   "lead": "The bigger table, used on a leaderboard page or inside an article."
  },
  "The changelog rows": {
   "title": "The What's new rows",
   "lead": "The entries on the frontpage's What's new, and the same rhythm on the changelog page."
  }
 },
 "heads": {
  "The seam title": {
   "title": "The section title with the seam",
   "lead": "A heading set into a line that runs across the window, with the suit marks spaced along it."
  },
  "The plain rule and the bar's strip": {
   "title": "The plain dividing line",
   "lead": "The line the footer draws, and the strip that hangs under the menu bar."
  },
  "Heads on a page": {
   "title": "The headings on a reading page",
   "lead": "The page title, the section headings and the sub-headings, each with the space it keeps."
  },
  "A card's section head in a modal": {
   "title": "A heading inside a modal",
   "lead": "The heading that parts one card from the next in a dialog."
  }
 },
 "panels": {
  "The games panel": {
   "lead": "The panel that opens from the menu bar: five columns of games. Point at a link to see its underline."
  },
  "The user cluster and its three dropdowns": {
   "title": "Your corner of the menu bar",
   "lead": "The bell, the friends icon, your avatar and your name, and the three menus they open."
  },
  "The tooltip": {
   "lead": "One tooltip serves the whole site. Point at the word to see it, and note the pause before it comes."
  },
  "The notices on the lobby and on the felt": {
   "title": "The notices",
   "lead": "The toast and the two corner notices, on the lobby and over the felt, including the shutdown warning that turns red near its end."
  },
  "Avatars off the felt and on it": {
   "title": "The avatars",
   "lead": "An avatar carries a thin dark line around its drawing, and stands differently at a table than it does on a page."
  }
 },
 "chrome": {
  "The bar": {
   "title": "The menu bar",
   "lead": "The bar across the top, with the logo centred and the links either side of it."
  },
  "The footer": {
   "lead": "The four columns, the legal line under them and the social marks. Point at a mark to see it take its own colour."
  },
  "The ad rail": {
   "title": "The ad column",
   "lead": "The fixed column down the right of the frontpage, with its wallpaper and the Hide ads button."
  }
 },
 "motion": {
  "A thumb travelling": {
   "title": "The green thumb travelling",
   "lead": "Click a cell and watch the thumb move and the words change colour underneath it."
  },
  "A control answering the pointer, and a press": {
   "title": "What a control does under the pointer",
   "lead": "Colour answers almost at once, and a press shrinks the piece very slightly. A modal's controls answer instantly instead."
  },
  "Arriving, leaving and entering": {
   "title": "Arriving and leaving",
   "lead": "How something settles when it arrives, and how it goes when it leaves. Leaving is quicker than arriving."
  },
  "Ink takes, and reduced motion": {
   "title": "How something loaded appears",
   "lead": "Anything waiting on data fades up from a blur rather than moving. If your computer is set to ask for less motion, all of it stops."
  }
 },
 "copy": {
  "What a button says": {
   "lead": "A button names what happens next. Read these and say whether any of them would puzzle you."
  },
  "Names and order": {
   "lead": "The words the site uses for the same thing everywhere, and the order options sit in."
  }
 }
};
