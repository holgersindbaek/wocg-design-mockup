// Builds r5-pieces.html, the reference's last section: one example of every piece the design draws.
//
// Nothing here is hand-styled. Each piece is lifted out of the audit fragments as the site's own markup, and it is
// the site's own compiled stylesheet that draws it, so a piece is pixel-identical to the real page and a change to a
// value in sections 1 to 4 shows up in it. What is dropped in the lift is the audit's apparatus: the numeric rule
// sentence and the measurement table. The card scripts come across whole, because some pieces are built by a script
// on the site too (the games bar, the dropup, a tray's thumb); the reference page neuters Lab.table and Lab.note so
// those scripts draw the piece and print nothing.
//
// Run: node design-guide-parts/build-pieces.js
const fs = require('fs'), path = require('path');
const PARTS = __dirname;

// group, the plain name, the fragment, the audit card's title, and the line that says what to look at
const PIECES = [
  ['Buttons and links', 'The buttons', '05-buttons.html', 'The kit on the frontpage',
    'Every button the lobby uses, in each colour and both sizes. The first one hovers and presses for real.'],
  ['Buttons and links', 'The buttons in a dialog', '05-buttons.html', 'The kit in a modal, the actions',
    'The same fills inside a box, flatter, with no drop under them.'],
  ['Buttons and links', 'The quiet, the dangerous and the done', '05-buttons.html', 'The quiet button, the danger pair and the inert pill',
    'The button that does not commit you, the red pair for something you cannot undo, and the flat pill for an invite already sent.'],
  ['Buttons and links', 'The yellow button', '05-buttons.html', 'The yellow button, on the felt',
    'The button that names what to do next: Play on a tile, Join and Watch on a table. Over the felt it wears the table\u2019s own line instead, which the table tile below shows.'],
  ['Buttons and links', 'What a button does when you touch it', '05-buttons.html', 'Hover, press and disabled',
    'Point at the first button to see the hover. A press shrinks it very slightly. A button that cannot be used fades.'],
  ['Buttons and links', 'Two buttons at the foot of a dialog', '05-buttons.html', 'Two buttons in a box, the foot',
    'How a pair of buttons shares the width at the bottom of a modal.'],
  ['Buttons and links', 'Links', '05-buttons.html', 'Links',
    'A link in running text, and the quieter links in the menu, the panels and the footer. Point at one to see its underline.'],
  ['Buttons and links', 'The menu that opens from a Play button', '05-buttons.html', "The catalog's dropup",
    'The sheet that comes out of the top of a game tile.'],

  ['Fields and trays', 'A text field', '06-fields.html', 'The field',
    'The box you type in. Click into it to see the focus ring.'],
  ['Fields and trays', 'A field on white, and one with an error', '06-fields.html', 'The field on a white card, and a bad one',
    'On a white card the field changes its paper so it still reads. A field with a problem turns its ring red.'],
  ['Fields and trays', 'The small search field', '06-fields.html', 'The search field, at 26',
    'The smaller field that sits in a table head, on a leaderboard page.'],
  ['Fields and trays', 'The tray', '06-fields.html', 'The tray, in a modal and on a white card',
    'Picking one option out of a few. Click a cell and the green thumb travels to it.'],
  ['Fields and trays', 'The checkbox', '06-fields.html', 'The checkbox',
    'Picking several options at once. Click a box and the tick draws itself in; click again and box and tick fade.'],
  ['Fields and trays', 'The settings tabs', '06-fields.html', 'The settings tabs',
    'The same tray one size up, across the top of the settings box.'],
  ['Fields and trays', 'The games bar', '06-fields.html', 'The games bar',
    'The row of games at the top of the lobby, each with the number playing. Click one and the thumb travels.'],

  ['The small marks', 'The tag', '07-chips.html', 'The tag',
    'The small label on the What’s new row and on the changelog page.'],
  ['The small marks', 'The rating up and down chips', '07-chips.html', 'The movement chips',
    'A rank or rating that moved, each with its arrow. Up is green, down is red.'],
  ['The small marks', 'The presence dots', '07-chips.html', 'Dots',
    'The round mark that says someone is online, and the live dot in the hero.'],
  ['The small marks', 'The player count on a tile', '07-chips.html', 'The count chip on a tile',
    'The number of people playing, written over the tile’s own art.'],
  ['The small marks', 'The marks at a seat', '07-chips.html', 'Badges on a seat',
    'The bot mark, the finished badge and the daily challenge number at a player’s plate.'],

  ['Containers', 'The white card', '08-cards.html', 'The white card, in a modal and on a page',
    'The plain container, in a dialog and on a page.'],
  ['Containers', 'A game tile', '08-cards.html', 'The game tile, hero and catalog',
    'The tile for a game, large in the hero and small in the catalog. Point at one to see it rise.'],
  ['Containers', 'A table tile', '08-cards.html', 'The felt tile',
    'A table in play, with its seats and the people at them.'],
  ['Containers', 'The other cards', '08-cards.html', 'The other paper cards, the photo and the quote avatar',
    'The leaderboard card, the quote card and the picture card.'],
  ['Containers', 'The modal box', '08-cards.html', 'The modal box',
    'A dialog, over the darkened page behind it.'],
  ['Containers', 'The panels that float', '08-cards.html', 'The floating containers, geometry',
    'A dropdown panel, the toast and the notices, and how each is put together.'],

  ['Lists and tables', 'The table in a lobby card', '09-tables.html', 'The compact card table',
    'The leaderboard on the lobby card: tight rows on alternating paper.'],
  ['Lists and tables', 'The table in a dialog', '09-tables.html', 'The stats table in a modal',
    'A stats table in a dialog, with your own row in bold.'],
  ['Lists and tables', 'A settings row', '09-tables.html', 'Settings rows',
    'A row with its title, a line of explanation and its control at the right.'],
  ['Lists and tables', 'A row with a person', '09-tables.html', 'People rows',
    'The row the invite, profile and table lists are built from.'],
  ['Lists and tables', 'A table on a page', '09-tables.html', 'The page table',
    'The bigger table, on a leaderboard page or inside an article.'],
  ['Lists and tables', 'The What’s new rows', '09-tables.html', 'The changelog rows',
    'The entries on the frontpage, and the same rhythm on the changelog page.'],

  ['Lines and dividers', 'A divider in three places', '03-shape.html', 'Dividers',
    'Where a line parts two regions of one colour: a tray in a dialog, the rows of a leaderboard card, and the footer above its legal line. Between two rows of one white card it is the soft line, on the band and the canvas it is the line, and a tray draws the tray line. A divider is a line under a row, not the ring a box is drawn with.'],
  ['Lines and dividers', 'The plain dividing line', '10-heads.html', "The plain rule and the bar's strip",
    'The line the footer draws, and the strip that hangs under the menu bar.'],
  ['Lines and dividers', 'The line a box is drawn with', '03-shape.html', 'Rings: the inset 1px line',
    'The line that draws a container, laid inside its own box. It is a border, not a divider, and it is never the line used between rows.'],
  ['Lines and dividers', 'A real border', '03-shape.html', 'Borders: a real 1px line',
    'The few places that draw a true border rather than a ring laid inside the box.'],
  ['Lines and dividers', 'The rings drawn outside, and the focus ring', '03-shape.html', 'Rings drawn outside, and the focus ring',
    'The two rings that sit outside their box, and the field you are typing in, whose line darkens rather than thickens.'],
  ['Lines and dividers', 'The line over tile art', '03-shape.html', 'The line over tile art',
    'A picture takes a darkened rim rather than the page\u2019s own line, so it reads on any art under it.'],

  ['Headings and rules', 'The section title with the seam', '10-heads.html', 'The seam title',
    'A heading set into a line that runs across the window, with the suit marks along it.'],
  ['Headings and rules', 'The headings on a page', '10-heads.html', 'Heads on a page',
    'The page title, the section headings and the sub-headings, with the space each one keeps.'],
  ['Headings and rules', 'A heading in a dialog', '10-heads.html', "A card's section head in a modal",
    'The heading that parts one card from the next in a dialog.'],

  ['The chrome', 'The menu bar', '12-chrome.html', 'The bar',
    'The bar across the top of every page.'],
  ['The chrome', 'The games panel', '11-panels.html', 'The games panel',
    'The panel that opens from the menu bar: five columns of games. Point at a link to see its underline.'],
  ['The chrome', 'Your corner of the bar', '11-panels.html', 'The user cluster and its three dropdowns',
    'The bell, the friends icon, your avatar and name, and the three menus they open.'],
  ['The chrome', 'The tooltip', '11-panels.html', 'The tooltip',
    'One tooltip serves the whole site. Point at the word to see it, and note the pause before it comes.'],
  ['The chrome', 'The notice', '11-panels.html', 'The notice on the lobby and on the felt',
    'The one notice the site draws, the toast, on paper and over the felt.'],
  ['The chrome', 'The footer', '12-chrome.html', 'The footer',
    'The four columns, the legal line and the social marks. Point at a mark to see it take its own colour.'],
  ['The chrome', 'The ad column', '12-chrome.html', 'The ad rail',
    'The fixed column down the right of the frontpage, with its wallpaper and the Hide ads button.'],

  ['At the table', 'The avatars', '11-panels.html', 'Avatars off the felt and on it',
    'An avatar carries a thin dark line around its drawing, and stands differently at a table than on a page.']
];

// A well holding a modal takes the scrim as its ground, so a dialog stands on the darkened page the way it does
// on the site. Marked per demo, not per piece, because a piece like the white card has one demo in a dialog and
// one on a page. Nothing opts into the scrim's blur any more: the well paints a flat composite, and a blurred
// backdrop is a composited layer Chrome reads the page back into, which is what took the renderer down at 47 of
// them.
// Seven audit demos paint their own well inline with a copy of the canvas hex. Inline beats the stylesheet, so
// one of them stayed pale where its ground should have been the scrim, and all seven would keep an old hex if the
// canvas ever moved. The ground belongs to the well's own rule, so the declaration is taken out and the rest of
// the inline style (padding, flex) is left alone.
function stripWellPaint(html) {
  return html.replace(/(<div class="demo[^"]*"[^>]*style=")([^"]*)"/g, (m, head, style) => {
    const kept = style.split(';').filter(d => !/^\s*background(-color|-image)?\s*:/.test(d)).join(';').replace(/^;+|;+$/g, '');
    return head + kept + '"';
  });
}

// keep the first n demos of a lifted body, and the scripts and anything else around them
function keepDemos(html, n) {
  let out = '', i = 0, seen = 0;
  for (;;) {
    const at = html.indexOf('<div class="demo', i);
    if (at < 0) return out + html.slice(i);
    const b = block(html, at);
    out += html.slice(i, at);
    if (seen++ < n) out += b;
    i = at + b.length;
  }
}

const NOSCRIM = new Set(['A divider in three places']);

function markScrim(html, name) {
  if (NOSCRIM.has(name)) return html;
  let out = '', i = 0;
  for (;;) {
    const at = html.indexOf('<div class="demo', i);
    if (at < 0) { out += html.slice(i); return out; }
    let b = block(html, at);
    if (b.includes('wmModal')) b = b.replace('<div class="demo', '<div class="demo scrim');
    out += html.slice(i, at) + b;
    i = at + block(html, at).length;
  }
}

// A felt well paints the table's green behind the piece, but a .site root paints its own paper over it, so the
// piece ended up on a cream box inside a green band (Holger, 15 Sep: "cut off"). These two demos are frontpage
// content anyway, a game tile and a table listing, so they lose the felt and stand on the paper they stand on.
const NOFELT = new Set(['The yellow button']);

// Chrome that runs to the window's edge on the site: a band of ground either side of it would be a lie, so its
// well is flush and the piece touches, the way it touches the window.
// Some audit cards carry a second demo to prove an empty state, which without the audit's note just looks like a
// piece that failed to draw. Name the piece and how many of its demos to keep.
const KEEP = { 'The games bar': 1 };

const FLUSH = new Set(['The menu bar', 'The footer', 'The ad column', 'The section title with the seam',
  'The plain dividing line']);

// A piece that does not fit half the grid takes the whole row. The list is not a guess: /tmp/clip.js measures
// scrollWidth against clientWidth on every demo and reports what overflows, and these are what it reported.
const WIDE = new Set([
  'The menu bar', 'The footer', 'The games panel', 'The headings on a page', 'The section title with the seam',
  'Links', 'The settings tabs', 'The tag', 'The other cards', 'The modal box', 'The panels that float',
  'The table in a dialog', 'A settings row', 'The What\u2019s new rows', 'A heading in a dialog',
  'Your corner of the bar', 'The menu that opens from a Play button', 'The rating up and down chips',
  'The plain dividing line', 'A divider in three places'
]);

// ---------------------------------------------------------------------------
// lifting
// ---------------------------------------------------------------------------
// the block starting at i, matched on <div ...> / </div>
function block(s, i) {
  const re = /<div\b|<\/div>/g;
  re.lastIndex = i;
  let depth = 0, m;
  while ((m = re.exec(s))) {
    if (m[0] === '</div>') { depth--; if (!depth) return s.slice(i, m.index + 6); }
    else depth++;
  }
  throw new Error('unclosed div at ' + i);
}

const cache = {};
function fragment(file) {
  if (cache[file]) return cache[file];
  const s = fs.readFileSync(path.join(PARTS, file), 'utf8');
  const firstCard = s.indexOf('<div class="card"');
  // the helpers a fragment declares before its cards (window.B5, window.F6 and their kind)
  const pre = (s.slice(0, firstCard).match(/<script>[\s\S]*?<\/script>/g) || []).join('\n');
  return (cache[file] = { s, pre });
}

function pieceOf(file, title) {
  const { s } = fragment(file);
  const h = s.indexOf('<h3>' + title);
  if (h < 0) throw new Error('no card "' + title + '" in ' + file);
  const start = s.lastIndexOf('<div class="card"', h);
  const card = block(s, start);
  const wrap = '<div class="body">';
  const bodyBlock = block(card, card.indexOf(wrap));
  const body = bodyBlock.slice(wrap.length, -'</div>'.length);
  // drop the audit's apparatus: its title and its numeric rule sentence. Everything else, demos and scripts, carries.
  return body
    .replace(/<h3>[\s\S]*?<\/h3>\s*/, '')
    .replace(/<p class="rule-text">[\s\S]*?<\/p>\s*/g, '')
    .replace(/<p class="rl">[\s\S]*?<\/p>\s*/g, '')
    .trim();
}

// ---------------------------------------------------------------------------
// writing
// ---------------------------------------------------------------------------
const used = [];
for (const [, , file] of PIECES) if (!used.includes(file)) used.push(file);

const out = [
  '<section class="sec" id="pieces">',
  '<h2>5 Examples <button type="button" class="fold" id="foldPieces" aria-expanded="true" aria-controls="piecesBody">Hide</button></h2>',
  '<div class="rule"></div>',
  '<p class="seclead">Every piece the values above build, drawn with the site’s own markup and its own stylesheet. Change a value in a section above and it changes here, and on the site.</p>',
  '',
  '<script>',
  '/* The pieces are lifted from the audit whole, scripts and all, because some of them are built by a script on',
  '   the site too. These two write the audit’s measurements, which this page does not show, so they are given',
  '   somewhere detached to write to. */',
  'Lab.table = function () { return document.createElement("table"); };',
  'Lab.note = function () { return document.createElement("p"); };',
  '</script>',
  '',
  '<!-- the helpers the lifted scripts lean on, from the fragments they came out of -->'
];
for (const f of used) {
  const pre = fragment(f).pre;
  if (pre) out.push('<!-- ' + f + ' -->', pre);
}

let group = null;
for (const [g, name, file, title, lead] of PIECES) {
  if (g !== group) {
    if (group) out.push('</div>');
    else out.push('<div id="piecesBody">');
    out.push('', '<h3 class="gname">' + g + '</h3>', '<div class="grid g2">');
    group = g;
  }
  out.push('');
  out.push('  <div class="card' + (WIDE.has(name) ? ' wide' : '') + '"><div class="body">');
  out.push('    <h3>' + name + '</h3>');
  out.push('    <p class="lead">' + lead + '</p>');
  let markup = pieceOf(file, title);
  if (NOFELT.has(name)) markup = markup.replace(/class="demo felt"/g, 'class="demo"');
  if (FLUSH.has(name)) markup = markup.replace(/class="demo(?= |")/g, 'class="demo flush');
  markup = stripWellPaint(markup);
  markup = markScrim(markup, name);
  if (KEEP[name]) markup = keepDemos(markup, KEEP[name]);
  out.push('    ' + markup);
  out.push('  </div></div>');
}
out.push('</div>');          // the last group's grid
out.push('</div>');          // #piecesBody
// Holger asked to be able to fold the examples away. The choice sticks, because the page is long and he will
// want it the same way next time he opens it.
out.push('<script>',
  '(function () {',
  "  var btn = document.getElementById('foldPieces'), body = document.getElementById('piecesBody');",
  '  function set(open) {',
  '    body.hidden = !open;',
  "    btn.textContent = open ? 'Hide' : 'Show';",
  "    btn.setAttribute('aria-expanded', open ? 'true' : 'false');",
  "    try { localStorage.setItem('wocgGuideExamples', open ? '1' : '0'); } catch (e) {}",
  '  }',
  '  var saved = null;',
  "  try { saved = localStorage.getItem('wocgGuideExamples'); } catch (e) {}",
  "  set(saved !== '0');",
  "  btn.addEventListener('click', function () { set(body.hidden); });",
  '})();',
  '</script>');
out.push('</section>', '');

fs.writeFileSync(path.join(PARTS, 'r5-pieces.html'), out.join('\n'));
console.log('r5-pieces.html', PIECES.length, 'pieces from', used.length, 'fragments');
