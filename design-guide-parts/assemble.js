// Assembles design-guide.html: the system reference. Every value the design is built from, once, with its handle and
// what it is used for, so one of them can be changed everywhere. Sections 1 to 4 are drawn by ref.js from ref-spec.js;
// section 5 is real markup, lifted from the audit fragments. The audit page (design-audit.html, assemble-audit.js) is
// the other half: every rule the written guide states, measured against it. Run: node design-guide-parts/assemble.js
const fs = require('fs'), path = require('path');
const DIR = path.resolve(__dirname, '..'), PARTS = __dirname;
const head = fs.readFileSync(path.join(PARTS, 'head.html'), 'utf8');

const SECS = [
  { id: 'colour', title: '1 Colour', lead: 'Every colour the design uses, once. A button is a fill, a ring one step darker and its ink: change the fill and the other two are rebuilt from it.' },
  { id: 'text', title: '2 Text', lead: 'The two fonts, and every size either of them is set at.' },
  { id: 'shape', title: '3 Corners, lines and shadows', lead: 'How round a thing is, how its edge is drawn, and how far it lifts off the page.' },
  { id: 'space', title: '4 Space and size', lead: 'Every gap, every row height, and how wide the page and the things that float over it are.' }
];

const piecesRaw = fs.readFileSync(path.join(PARTS, 'r5-pieces.html'), 'utf8');

// Every group and every card in Examples gets an id and a designation, so the nav can point at one and a
// click can put its name on the clipboard. They are written here rather than in build-pieces.js, so the
// fragments can be lifted again without having to carry them.
const slug = (t) => t.toLowerCase().replace(/[\u2018\u2019']/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
const attr = (t) => t.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
const groups = [];
let group = null;
const taken = {};
const pieces = piecesRaw.replace(
  /<h3 class="gname">([^<]*)<\/h3>|<div class="card([^"]*)"><div class="body">(\s*)<h3>([^<]*)<\/h3>/g,
  (m, gname, cls, gap, title) => {
    if (gname !== undefined) {
      group = { name: gname, id: 'ex-' + slug(gname), cards: [] };
      groups.push(group);
      return `<h3 class="gname" id="${group.id}">${gname}</h3>`;
    }
    const g = group || (group = { name: 'Examples', id: 'ex', cards: [] }, groups.push(group), group);
    let id = g.id + '-' + slug(title);
    if (taken[id]) id += '-' + (++taken[id]); else taken[id] = 1;
    g.cards.push({ title, id });
    const ref = `Examples \u203a ${g.name} \u203a ${title}`;
    return `<div class="card${cls}" id="${id}" data-ref="${attr(ref)}"><div class="body">${gap}<h3>${title}</h3>`;
  }
);

const toc = `<nav id="toc">
  <div class="tt">The design guide</div>
${SECS.map(s => `  <a class="top" href="#${s.id}">${s.title}</a>`).join('\n')}
  <a class="top" href="#pieces">5 Examples</a>
  <div class="extree">
${groups.map(g => `    <div class="exg" data-sec="${g.id}"><a class="grp" href="#${g.id}">${g.name}</a>
      <div class="exl">${g.cards.map(c => `<a class="leaf" href="#${c.id}">${c.title}</a>`).join('')}</div></div>`).join('\n')}
  </div>
  <div class="labs"><div class="lb">The other pages</div><a href="colour-lab.html">The colour scheme, in full</a><a href="design-audit.html">The audit: every rule measured</a><a href="colour-candidates-lab.html">Colour candidates still open</a></div>
</nav>`;

const intro = `<div class="page">

  <h1>The design guide</h1>
  <p class="lede">Everything the design is built from, on one page: <span id="refcount"></span> in all. Each row is the thing itself, drawn with the site's own stylesheet, then its handle and its value, then what it is used for. Point at any row and say what it should be instead, and it changes everywhere it is used. The last section, Examples, shows the pieces those values build, and folds away when you do not want it. Nothing here is a proposal: it is what the site draws today.</p>
`;

const secs = SECS.map(s => `<section class="sec" id="${s.id}">
<h2>${s.title}</h2>
<div class="rule"></div>
<p class="seclead">${s.lead}</p>
<div data-spec="${s.id}"></div>
</section>`).join('\n\n');

const index = JSON.stringify([].concat.apply([], groups.map(g => g.cards.map(c => ({ id: c.id, t: c.title, g: g.name })))));

const outro = `
</div>
<script>window.ExampleIndex = ${index};</script>
<script>
(function () {
  var top = [].slice.call(document.querySelectorAll('#toc a.top'));
  var secs = top.map(function (a) { return document.querySelector(a.getAttribute('href')); });
  var exgs = [].slice.call(document.querySelectorAll('#toc .exg'));
  var leaves = [].slice.call(document.querySelectorAll('#toc a.leaf'));
  var cards = leaves.map(function (a) { return document.querySelector(a.getAttribute('href')); });
  var pinned = null;

  function offset(el) { var y = 0; while (el) { y += el.offsetTop; el = el.offsetParent; } return y; }

  function mark() {
    var y = window.scrollY + 120, cur = 0, i;
    for (i = 0; i < secs.length; i++) { if (secs[i] && offset(secs[i]) <= y) cur = i; }
    top.forEach(function (a, n) { a.classList.toggle('on', n === cur); });

    // Inside Examples the tree follows the page: the group you are in opens, and its card is marked.
    var inPieces = top[cur] && top[cur].getAttribute('href') === '#pieces';
    var open = pinned;
    if (!open && inPieces) {
      exgs.forEach(function (g) {
        var h = document.getElementById(g.getAttribute('data-sec'));
        if (h && offset(h) <= y) open = g.getAttribute('data-sec');
      });
    }
    exgs.forEach(function (g) { g.classList.toggle('open', g.getAttribute('data-sec') === open); });
    var lead = -1;
    for (i = 0; i < cards.length; i++) { if (cards[i] && offset(cards[i]) <= y) lead = i; }
    leaves.forEach(function (a, n) { a.classList.toggle('on', inPieces && n === lead); });
  }

  // A group stays open once you pick it, until you pick another or scroll into a different one.
  document.querySelectorAll('#toc a.grp').forEach(function (a) {
    a.addEventListener('click', function () {
      var g = a.parentNode.getAttribute('data-sec');
      pinned = (pinned === g) ? null : g;
      setTimeout(mark, 0);
    });
  });
  window.addEventListener('scroll', function () { pinned = null; mark(); }, { passive: true });
  window.addEventListener('resize', mark);
  mark();

  // Click a card in Examples and its designation goes to the clipboard, so it can be named exactly.
  // Chrome calls a file:// page secure and offers navigator.clipboard, but the write can still be refused
  // there, so the old textarea way stands behind it.
  function put(text) {
    function byField() {
      var t = document.createElement('textarea');
      t.value = text; t.setAttribute('readonly', ''); t.style.position = 'fixed'; t.style.top = '-1000px';
      document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); } catch (e) {}
      document.body.removeChild(t);
    }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(byField);
        return;
      }
    } catch (e) {}
    byField();
  }

  var flashing = null;
  document.addEventListener('click', function (e) {
    var card = e.target.closest && e.target.closest('#pieces .card');
    if (!card || !card.getAttribute('data-ref')) return;
    // the demos inside a card are the point of it, so a click on one of their controls is theirs
    if (e.target.closest('a, button, input, select, textarea, label, summary, [role="button"], [contenteditable]')) return;
    put(card.getAttribute('data-ref') + '  (design-guide.html#' + card.id + ')');
    if (flashing) flashing.classList.remove('copied');
    card.classList.add('copied');
    flashing = card;
    setTimeout(function () { card.classList.remove('copied'); }, 1400);
  });

})();
</script>
<script src="design-guide-parts/exref.js"></script>
</body>
</html>
`;

const page = head + '\n' + toc + '\n' + intro + '\n' + secs + '\n\n' + pieces.trim() + '\n' + outro;
fs.writeFileSync(path.join(DIR, 'design-guide.html'), page);
console.log('design-guide.html', Math.round(page.length / 1024), 'KB,', SECS.length + 1, 'sections');
