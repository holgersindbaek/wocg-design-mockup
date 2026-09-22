// The design system, as a list. This is what design-guide.html draws: every value the design is built from, once,
// with its handle and what it is used for, so Holger can point at one and say change it everywhere.
// Values are never written here. ref.js reads each one live off a .site root through site.css, so the page cannot
// drift from the site. A `value` field is only given where the design writes a literal rather than a token.
window.Spec = {

  colour: [
    { group: 'Paper', note: 'What a surface is made of. Every page starts as the canvas.', items: [
      { token: '--canvas', name: 'Page paper', use: 'Every page, and the modal box' },
      { token: '--band', name: 'Band paper', use: 'The menu bar, the footer, a banded section, the notices, a table head row' },
      { token: '--surface', name: 'White', use: 'Cards, tiles, panels, dropdowns, fields, chips, the tooltip' },
      { value: '#327333', name: 'The felt', use: 'Behind a table: a table tile and the game table itself' }
    ] },
    { group: 'Ink', note: 'The five darknesses text is written in, from the title down to a timestamp.', items: [
      { token: '--ink', name: 'Ink', use: 'Titles, running text, names, figures, table cells' },
      { token: '--ink-soft', name: 'Soft ink', use: 'The menu links, dropdown items, the tooltip, a long answer' },
      { token: '--muted', name: 'Muted', use: 'The line under a title, an explainer, a table head, a tag' },
      { token: '--muted-soft', name: 'Soft muted', use: 'An empty list, the small bullets, a presence dot when off' },
      { token: '--faint', name: 'Faint', use: 'By-lines, timestamps, a quote attribution, the tooltip hint' }
    ] },
    { group: 'Lines', note: 'A border sits between two surfaces and is darker than both. A divider sits on one surface and is that surface one step down.', items: [
      { token: '--edge', name: 'Edge', use: 'The 1px line around a card, tile, field, chip, panel or dropdown' },
      { token: '--rule', name: 'Rule', use: 'A section seam, the line under the bar, the line over the footer, a tray on white' },
      { token: '--hairline', name: 'Hairline', use: 'The divider between two rows inside a white card' },
      { token: '--wm-seg-ring', name: 'Chooser ring', root: 'modal', use: 'Around a tray or the games bar, and between its cells' },
      { token: '--color-table-edge', name: 'Felt line', use: 'A name plate and a notice over the felt' },
      { value: 'rgba(0, 0, 0, .30)', name: 'Overlay ring', use: 'The modal box, and any paper floating over the felt or the dark sheet' }
    ] },
    { group: 'Buttons', note: 'Each button is a fill, a ring one step darker, a hover, and its ink. Change the fill and the rest should be rebuilt from it.', kind: 'button', items: [
      { fill: '--triogreen', ring: '--triogreenring', ink: '#ffffff', outline: true, name: 'Action green', use: 'Every go-ahead button, the tray thumb, a picked chip' },
      { fill: '--trioblue', ring: '--triobluering', ink: '#ffffff', outline: true, name: 'Blue', use: 'The second solid action: Manage, and its kind' },
      { fill: '--triolight', ring: '--triolightring', ink: '--triolightink', name: 'Light blue', use: 'A quiet action that reads like a link: See all, How to play' },
      { fill: '--wm-tray', ring: '--wm-tray-ring', ink: '--ink', name: 'Tray', use: 'Cancel, Close, Got it: the button that does not commit you' },
      { fill: '--wm-danger', ring: '--wm-danger-ring', ink: '#ffffff', outline: true, root: 'modal', name: 'Danger', use: 'Delete, Leave now, Cancel subscription' },
      { fill: '--trioredlight', ring: '#e8958c', ink: '#b52626', name: 'Soft danger', use: 'Delete account, Change password: serious, not final' },
      { fill: '#ffd43b', ring: '#f5af23', ink: '#3d2b00', name: 'Yellow verb', use: 'The table action: Play, Join, Watch, Accept' }
    ] },
    { group: 'Light plates', note: 'A pale fill with its own deep ink, used where a colour has to carry small words.', kind: 'plate', items: [
      { fill: '--triogreenlight', ink: '--triogreenlightink', name: 'Light green', use: 'A rating that went up, a seat plate' },
      { fill: '--trioredlight', ink: '#8b1a1a', name: 'Light red', use: 'A rating that went down, the red team' },
      { fill: '--triolight', ink: '--triolightink', name: 'Light blue', use: 'A name plate at the table' },
      { fill: '--wm-seg', ink: '--muted', name: 'Chooser paper', use: 'The track a tray or the games bar sits in, and a tag' }
    ] },
    { group: 'Accents', note: 'Two colours that only mark a rating.', items: [
      { token: '--p1', name: 'Star fill', use: 'A full rating star' },
      { token: '--p5', name: 'Star stroke', use: 'The line around a rating star' }
    ] }
  ],

  text: [
    { group: 'The two faces', note: 'One face for the interface, one for headings. No other font is loaded by any page.', kind: 'face', items: [
      { face: 'ui', weights: '400, 700 and 900', name: 'BuloRounded', use: 'Everything you click, read in a row, or type into' },
      { face: 'display', weights: '400 and 500', name: 'GLCA', use: 'Page titles, section heads, an h3, a quote' }
    ] },
    { group: 'Interface sizes', note: 'All interface text is one of five sizes. Nothing a dialog writes is under 14.', kind: 'size', items: [
      { size: '20px', line: '28px', weight: 700, name: '20', use: 'A tile title, a modal title, the lobby big button' },
      { size: '18px', line: '32px', weight: 700, name: '18', use: 'A big button, the settings tabs' },
      { size: '16px', line: '24px', weight: 400, name: '16', use: 'Running text, a small button, a tray cell, a table cell' },
      { size: '14px', line: '20px', weight: 400, name: '14', use: 'A by-line, small print, a name plate on a tile' },
      { size: '12px', line: '16px', weight: 700, name: '12', use: 'A tag, a rating movement chip' }
    ] },
    { group: 'Heading sizes', note: 'The display face takes five sizes, and no others.', kind: 'size', items: [
      { size: '38px', line: '1.15', face: 'display', weight: 500, name: '38', use: 'The hero title, and nothing else' },
      { size: '26px', line: '1.2', face: 'display', weight: 500, name: '26', use: 'A section head, and a seam title' },
      { size: '23px', line: '30px', face: 'display', weight: 500, name: '23', use: 'The about sub-head' },
      { size: '21px', line: '28px', face: 'display', weight: 500, name: '21', use: 'An h3 on a reading page' },
      { size: '19px', line: '26px', face: 'display', weight: 400, name: '19', use: 'A question, a quote, the letter' }
    ] }
  ],

  shape: [
    { group: 'Corners', note: 'Every corner is a squircle, not an arc, except the three noted. Five sizes, and round.', kind: 'corner', items: [
      { value: '20px', name: '20', use: 'A modal box, a game tile, a table tile, a leaderboard card, a dropdown panel' },
      { value: '16px', name: '16', use: 'A white card inside a modal, and the notices' },
      { value: '14px', name: '14', use: 'The games bar track, one step rounder than the cells inside it' },
      { value: '12px', name: '12', use: 'Every button, field, tray cell, chip, thumb and the tooltip' },
      { value: '8px', name: '8', use: 'A tag, and a rating movement chip' },
      { value: '999px', round: true, name: 'Round', use: 'Dots, badges, the live capsule, a progress bar' },
      { value: '0', name: 'None', use: 'The ad rail, and any band that runs the full width' }
    ] },
    { group: 'Lines', note: 'The same colours as above, in the three forms a line is drawn in.', kind: 'line', items: [
      { form: 'inset', name: 'Inside ring', use: 'The default: a card, tile, field, chip, tray or button' },
      { form: 'border', name: 'Real border', use: 'A fully round pill, a dropdown, a card whose text is padded in' },
      { form: 'outside', name: 'Outside ring', use: 'The modal box, a name plate on the felt, the author photo' },
      { form: 'focus', name: 'Focus ring', use: 'A field you are typing in: the same 1px line, darkened to --faint' },
      { form: 'divider', name: 'Divider', use: 'Between two rows of one colour' }
    ] },
    { group: 'Shadows', note: 'How far a thing lifts off the page. Five steps and one special.', kind: 'shadow', items: [
      { token: '--liftshadow', name: 'Container lift', use: 'Every light container: a card, a panel, a dropdown, the tooltip. The frontpage draws a lighter copy, .04 and .06' },
      { token: '--liftshadow-lg', name: 'Tile lift', use: 'A hero tile and a table tile, which sit higher than a card' },
      { token: '--wm-card-lift', root: 'modal', name: 'Half lift', use: 'A white card inside a modal' },
      { value: '0 2px 4px rgba(0, 0, 0, .06)', name: 'Button drop', use: 'The lobby buttons and both tray thumbs. A modal button has none' },
      { token: '--wm-lift', root: 'modal', name: 'Modal lift', use: 'The modal box over the dark sheet' }
    ] }
  ],

  space: [
    { group: 'Gaps', note: 'Every distance in the design is one of these. Nothing sits at 5, 7 or 15.', kind: 'gap', items: [
      { value: '4px', use: 'A field to its error line' },
      { value: '6px', use: 'Inside a chip, between the social marks' },
      { value: '8px', use: 'Where two hard edges meet' },
      { value: '10px', use: 'A sub-head to its text' },
      { value: '12px', use: 'Inside a box, and inside a card' },
      { value: '16px', use: 'Every grid on the page' },
      { value: '18px', use: 'Between the menu links' },
      { value: '24px', use: 'The page gutter, a settings row to its control, the footer columns' },
      { value: '28px', use: 'Above a heading' },
      { value: '44px', use: 'Between two blocks of reading' },
      { value: '56px', use: 'Between one section and the next' }
    ] },
    { group: 'Heights', note: 'How tall a row or a control is.', kind: 'height', items: [
      { value: '56px', use: 'The menu bar' },
      { value: '40px', use: 'A corner notice, a leaderboard row, a table row, a settings row with two lines' },
      { value: '32px', use: 'A button, a field, the live capsule, a panel head strip' },
      { value: '28px', use: 'A tray track, a settings row, a menu row' },
      { value: '24px', use: 'A small button, a tray cell, a chip, the yellow verb' },
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
