// The design system, as a list. This is what design-guide.html draws: every value the design is built from, once,
// with its handle and what it is used for, so Holger can point at one and say change it everywhere.
// Values are never written here. ref.js reads each one live off a .site root through site.css, so the page cannot
// drift from the site. A `value` field is only given where the design writes a literal rather than a token.
window.Spec = {

  colour: [
    { group: 'Paper', note: 'What a surface is made of. Every page starts as the canvas.', items: [
      { token: '--paper-page', name: 'Page paper', use: 'Every page, and the modal box' },
      { token: '--paper-band', name: 'Band paper', use: 'The menu bar, the footer, a banded section, the notices, a table head row' },
      { token: '--paper-card', name: 'Card paper', use: 'Cards, tiles, panels, dropdowns, fields, chips, the tooltip' },
      { value: '#327333', name: 'The felt', use: 'Behind a table: a table tile and the game table itself' }
    ] },
    { group: 'Ink', note: 'What text is written in: everything, the quiet line under it, and a link.', items: [
      { token: '--ink', name: 'Ink', use: 'Every word: titles, running text, names, figures, table cells, a sub-line under a title, an explainer, a placeholder' },
      { token: '--ink-quiet', name: 'Quiet ink', use: 'By-lines, timestamps, a quote attribution, the tooltip hint, an empty list' },
      { token: '--plate-blue-ink', name: 'Link ink', use: 'Every text link on paper, and its underline on the frontpage. Its token is named for the blue plate, but a name plate writes in the deeper team ink below' }
    ] },
    { group: 'Labels and marks', note: 'Not text: what a label on a thing, and what a mark that is not a line, is drawn in.', items: [
      { token: '--ink-label', name: 'Label ink', use: 'A tag, a field\u2019s label, a group label, a table\u2019s second figure' },
      { token: '--ink-mark', name: 'Mark', use: 'The ring of the dot that says someone is away, and the empty rating star\u2019s outline' }
    ] },
    { group: 'Lines', note: 'A border sits between two surfaces and is darker than both. A divider sits on one surface and is that surface one step down.', items: [
      { token: '--line', name: 'Line', use: 'Every 1px line the page draws: around a card, tile, field, chip, panel or dropdown, and along a section seam, under the bar and over the footer' },
      { token: '--line-soft', name: 'Soft line', use: 'The divider between two rows inside a white card' },
      { token: '--line-warm', name: 'Warm line', use: 'The quiet button\u2019s paper and the catalog menu\u2019s lattice: the rung the line stood on until 22 Sep, a warmer and lighter grey than the line' },
      { token: '--line-tray', name: 'Tray line', use: 'Around a tray or the games bar, and between its cells' },
      { token: '--color-table-edge', name: 'Felt line', use: 'A name plate and a notice over the felt' },
      { value: 'rgba(0, 0, 0, .30)', name: 'Overlay ring', use: 'The modal box, and any paper floating over the felt or the dark sheet' }
    ] },
    { group: 'Buttons', note: 'Each button is a fill, a ring one step darker, a hover, and its ink. Change the fill and the rest should be rebuilt from it.', kind: 'button', items: [
      { fill: '--btn-green', ring: '--btn-green-ring', ink: '#ffffff', outline: true, name: 'Green', use: 'Every go-ahead button, the tray thumb, a picked checkbox' },
      { fill: '--btn-blue', ring: '--btn-blue-ring', ink: '#ffffff', outline: true, name: 'Blue', use: 'The second solid action: Manage, and its kind' },
      { fill: '--btn-quiet', ring: '--btn-quiet-ring', ink: '--ink', root: 'modal', name: 'Quiet', use: 'Cancel, Close, Got it: the button that does not commit you, when no filled button stands beside it' },
      { fill: '--btn-danger', ring: '--btn-danger-ring', ink: '#ffffff', outline: true, root: 'modal', name: 'Danger', use: 'Delete, Leave now, Cancel subscription' },
      { fill: '--btn-quiet-dark', ring: '--btn-quiet-dark-ring', ink: '#ffffff', outline: true, name: 'Quiet dark', use: 'The quiet button beside a filled one (Cancel beside Host, Watch game beside Join table), and the way back rather than the thing to do: the game over panel\u2019s Leave and Chat, Back to table, a picked block reason' },
      { fill: '#ffd43b', ring: '#f5af23', ink: '#3d2b00', name: 'Yellow', use: 'The table action: Play, Join, Watch, Accept' }
    ] },
    { group: 'Light plates', note: 'A pale fill with its own deep ink, used where a colour has to carry small words.', kind: 'plate', items: [
      { fill: '--plate-blue', ink: '--color-team1-ink', name: 'Blue plate', use: 'A name plate at the table, in the ink the table writes its names in' },
      { fill: '--plate-red', ink: '--color-team2-ink', name: 'Red plate', use: 'A rating that went down, the red team' },
      { fill: '--plate-green', ink: '--plate-green-ink', name: 'Green plate', use: 'A rating that went up: the movement chip and .rankUp. The icons on it: the Message button in the friends panel, a meld\u2019s count and the complete canasta\u2019s star' },
      { fill: '#f2d767', ring: '#d4ba47', ink: '#664411', name: 'Yellow plate', use: 'The turn timer, a meld\u2019s count with wild cards and the canasta star on it, and the rosette of medals 4 to 6: a pale yellow that carries small words in its own deep ink, as deep as the other plates\u2019 inks. Never a button on the felt, where the yellow button owns yellow' },
      { fill: '--plate-tray', hover: '--plate-tray-hover', ink: '--ink-label', name: 'Tray paper', use: 'The track a tray or the games bar sits in, and a tag. A cell under the pointer takes the hover, one small step under the tray' }
    ] },
    { group: 'Accents', note: 'Colours that only mark something: a rating, a place, a star, a notice, a suit. The icons draw in them (ICON-COLOURS.md).', items: [
      { token: '--star-fill', name: 'Star fill', use: 'A full rating star, on the band and in the game over panel' },
      { token: '--star-stroke', name: 'Star stroke', use: 'The line around a rating star' },
      { value: '#fcc419', name: 'Gold', use: 'The first place medal, the daily deal\u2019s gold trophy, the game over cup, the hand, the sun and the slam. Its ribbon is #fab005 and its line #9f6713' },
      { value: '#bec5cc', name: 'Silver', use: 'The second place medal, the silver trophy and the moon: a cool metal, not a paper grey. Its ribbon is #9ba2aa and its line #5d646c' },
      { value: '#e29c65', name: 'Bronze', use: 'The third place medal and the bronze trophy. Its ribbon is #c97847 and its line #854325' },
      { value: '#aa6413', name: 'Gold star', use: 'A star on the yellow plate or on the gold: the mixed canasta\u2019s star and the star in the game over cup' },
      { value: '#dd3030', name: 'Notice dot', use: 'The dot on the bell and on Friends, and on a conversation with unread messages. Its ring is #89060f' },
      { value: '#d51a22', name: 'Suit red', use: 'The hearts and diamonds that burst from a played card, and a friend\u2019s heart on the board: the classic deck\u2019s red' },
      { value: '#0e0d0d', name: 'Suit black', use: 'The clubs and spades that burst from a played card: the classic deck\u2019s black' }
    ] }
  ],

  text: [
    { group: 'The two faces', note: 'One face for the interface, one for headings, three files between them. No other font is loaded by any page.', kind: 'face', items: [
      { face: 'ui', weights: '400 and 700', name: 'BuloRounded', use: 'Everything you click, read in a row, or type into, and the about letter' },
      { face: 'display', weights: '500', name: 'GLCA', use: 'Page titles, section heads, an h3, a quote' }
    ] },
    { group: 'Interface sizes', note: 'All interface text is one of five sizes. Nothing a dialog writes is under 14.', kind: 'size', items: [
      { size: '20px', line: '28px', weight: 700, name: '20', use: 'A tile title, a modal title, the lobby big button' },
      { size: '18px', line: '32px', weight: 700, name: '18', use: 'A big button, the settings tabs' },
      { size: '16px', line: '24px', weight: 400, name: '16', use: 'Running text, a small button, a tray cell, a table cell' },
      { size: '14px', line: '20px', weight: 400, name: '14', use: 'A by-line, small print, a name plate on a tile' },
      { size: '12px', line: '16px', weight: 700, name: '12', use: 'A tag, a rating movement chip' }
    ] },
    { group: 'Heading sizes', note: 'The display face takes four sizes, and no others: three for headings and one for prose.', kind: 'size', items: [
      { size: '38px', line: '1.15', face: 'display', weight: 500, name: '38', use: 'The hero title, and nothing else' },
      { size: '26px', line: '1.2', face: 'display', weight: 500, name: '26', use: 'A section head, and a seam title' },
      { size: '21px', line: '28px', face: 'display', weight: 500, name: '21', use: 'An h3 anywhere: a reading page, the band, the about zone; the FAQ question' },
      { size: '19px', line: '1.45', face: 'display', weight: 500, name: '19', use: 'Display prose, never a heading: a quote card, a blockquote' }
    ] }
  ],

  shape: [
    { group: 'Corners', note: 'Every corner is a squircle, not an arc, except the three noted. Two sizes, the tray’s pair, round, and none.', kind: 'corner', items: [
      { value: '20px', name: '20', use: 'Every box: a modal box, a game tile, a table tile, a leaderboard card, a dropdown panel, a picture, a reading page box and the notices' },
      { value: '12px', name: '12', use: 'Every control and everything inside a box: a button, field, checkbox, the tooltip, and the white card in a modal' },
      { value: '14px', cell: '10.5px', name: 'Tray', use: 'Every tray and the games bar. The track is 14 and its cells and thumb are 10.5, so the 2px gap between them holds round the corner as it does along a side. Where the browser draws no squircle the pair is 8 and 6' },
      { value: '999px', round: true, name: 'Round', use: 'Dots, badges, the live capsule, and anything so small that half its height is the corner: a chip at 8, the waiting bar at 6, the award strip at 4' },
      { value: '0', name: 'None', use: 'The ad rail, and any band that runs the full width' }
    ] },
    { group: 'Lines', note: 'The colours are in the Lines group under Colour; this is the five forms a 1px line is drawn in. Which colour a divider takes depends on the surface it sits on, not on the form.', kind: 'line', items: [
      { form: 'inset', name: 'Inside ring', use: 'The default: a card, tile, field, checkbox, tray or button' },
      { form: 'border', name: 'Real border', use: 'A fully round pill, a dropdown, a card whose text is padded in' },
      { form: 'outside', name: 'Outside ring', use: 'The modal box, a name plate on the felt, the author photo' },
      { form: 'focus', name: 'Focus ring', use: 'A field you are typing in: the same 1px line, darkened to --ink-mark, the mark grey' },
      { form: 'divider', name: 'Divider', use: 'Between two rows of one colour, in that surface\u2019s own divider colour: --line-soft on white, --line on the band and the canvas, --line-tray inside a tray' }
    ] },
    { group: 'Shadows', note: 'How far a thing lifts off the page. Four steps.', kind: 'shadow', items: [
      { token: '--lift', name: 'Container lift', use: 'Every light container: a card, a panel, a dropdown, the tooltip. The frontpage draws a lighter copy, .04 and .06' },
      { token: '--lift-lg', name: 'Tile lift', use: 'A hero tile and a table tile, which sit higher than a card' },
      { token: '--lift-card', root: 'modal', name: 'Half lift', use: 'A white card inside a modal' },
      { value: '0 2px 4px rgba(0, 0, 0, .06)', name: 'Button drop', use: 'The lobby buttons and both tray thumbs. A modal button has none' }
    ] }
  ],

  space: [
    { group: 'Gaps', note: 'Every distance in the design is one of these. Nothing sits at 5, 7 or 15.', kind: 'gap', items: [
      { value: '4px', use: 'A field to its error line' },
      { value: '6px', use: 'Inside a chip, between the social marks' },
      { value: '8px', use: 'Where two hard edges meet' },
      { value: '10px', use: 'A sub-head to its text' },
      { value: '12px', use: 'Inside a box, inside a card, and a settings row’s words to a control that drops under them' },
      { value: '16px', use: 'Every grid on the page' },
      { value: '18px', use: 'Between the menu links' },
      { value: '24px', use: 'The page gutter, a settings row to its control, the footer columns' },
      { value: '28px', use: 'Above a heading' },
      { value: '44px', use: 'Between two blocks of reading' },
      { value: '56px', use: 'Between one section and the next' }
    ] },
    { group: 'Heights', note: 'How tall a row or a control is.', kind: 'height', items: [
      { value: '56px', use: 'The menu bar' },
      { value: '40px', use: 'A leaderboard row, a table row, the least a settings row with two lines stands' },
      { value: '34px', use: 'A field: the button\u2019s 32 plus the 2px its ring takes' },
      { value: '32px', use: 'A button, the live capsule, a panel head strip, a compact table row' },
      { value: '28px', use: 'A tray track, the least a settings row stands, a menu row' },
      { value: '26px', use: 'The search field in a table head: the small control\u2019s 24 plus the 2px its ring takes' },
      { value: '24px', use: 'A small button, a tray cell, a checkbox, the yellow button' },
      { value: '20px', use: 'A badge at a seat' },
      { value: '18px', use: 'A name plate on a tile' },
      { value: '16px', use: 'A tag, and a rating movement chip' }
    ] },
    { group: 'Widths', note: 'How wide the page and the things that float over it are.', kind: 'width', items: [
      { value: '1160px', name: 'The page', use: 'A section stops here, with 24px either side, so the content column is 1112' },
      { value: '680px', name: 'Reading', use: 'A column of text you read, inside a 728 box' },
      { value: '400px', name: 'Modal, narrow', use: 'A question, a confirmation' },
      { value: '640px', name: 'Modal, wide', use: 'Settings, stats, a list of people' },
      { value: '336px', name: 'Ad column', use: 'The fixed column on the frontpage, 160 on a narrow window' }
    ] }
  ]
};
