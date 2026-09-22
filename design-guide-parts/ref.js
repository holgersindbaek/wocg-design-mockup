// Draws the system reference from ref-spec.js. Every value is read live off a .site root through site.css, so this
// page says what the site is, not what someone wrote down. Two roots are probed: the page (body.wm) and the modal
// kit (.wmModal), because the modal declares tokens the page has no name for.
(function () {
  var SITE, MODAL;

  function probes() {
    var host = document.createElement('div');
    host.style.cssText = 'position:absolute;left:-9999px;top:0;width:600px;height:0;overflow:hidden;visibility:hidden;pointer-events:none';
    // The shared root, not the frontpage: body.fp overrides a few tokens with lighter copies of its own
    // (--liftshadow is .04/.06 there and .05/.09 everywhere else), and the shared value is the one to state.
    host.innerHTML = '<div class="site wm"><div class="wmModal wmOpen modalInstant"><div class="wmPanel">' +
      '<div class="wmBox"></div></div></div></div>';
    document.body.appendChild(host);
    SITE = host.querySelector('.site');
    MODAL = host.querySelector('.wmModal');
  }

  function rootFor(item) { return item.root === 'modal' ? MODAL : SITE; }

  // a token's computed value, or a literal written in the spec
  function val(item, key) {
    var v = item[key || 'value'];
    if (v) return v;
    var t = item.token || item[key];
    return t ? getComputedStyle(rootFor(item)).getPropertyValue(t).trim() : '';
  }
  function colourOf(item, tokenOrLiteral) {
    if (!tokenOrLiteral) return '';
    if (tokenOrLiteral.slice(0, 2) !== '--') return tokenOrLiteral;
    return getComputedStyle(rootFor(item)).getPropertyValue(tokenOrLiteral).trim();
  }
  // the hex the guide writes, through Lab so a color-mix() resolves the way it does on the site
  function shown(item, expr) {
    if (!expr) return '';
    var resolved = expr.slice(0, 2) === '--' ? Lab.resolve(rootFor(item), 'var(' + expr + ')') : Lab.hex(expr);
    return Lab.hex(resolved);
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  // ---------------------------------------------------------------------------
  // the drawings, one per kind
  // ---------------------------------------------------------------------------
  var draw = {
    colour: function (item) {
      var a = el('i', 'sw');
      a.style.background = item.value || colourOf(item, item.token);
      return a;
    },
    button: function (item) {
      var b = el('i', 'sw btn', 'Button');
      b.style.background = colourOf(item, item.fill);
      b.style.boxShadow = 'inset 0 0 0 1px ' + colourOf(item, item.ring);
      b.style.color = colourOf(item, item.ink);
      if (item.outline) b.style.textShadow = ['-1px -1px 0 ', '1px -1px 0 ', '-1px 1px 0 ', '1px 1px 0 ']
        .map(function (o) { return o + colourOf(item, item.ring); }).join(', ');
      return b;
    },
    plate: function (item) {
      var b = el('i', 'sw plate', 'Aa 12');
      b.style.background = colourOf(item, item.fill);
      b.style.color = colourOf(item, item.ink);
      return b;
    },
    face: function (item) {
      var b = el('i', 'sw face', 'Hearts and Spades');
      b.style.fontFamily = item.face === 'display' ? 'GLCA, Georgia, serif' : 'BuloRounded, Verdana, sans-serif';
      b.style.fontWeight = item.face === 'display' ? 500 : 700;
      return b;
    },
    size: function (item) {
      var b = el('i', 'sw size', 'Hearts');
      b.style.fontFamily = item.face === 'display' ? 'GLCA, Georgia, serif' : 'BuloRounded, Verdana, sans-serif';
      b.style.fontSize = item.size;
      b.style.lineHeight = item.line;
      b.style.fontWeight = item.weight || 400;
      return b;
    },
    corner: function (item) {
      var b = el('i', 'sw corner');
      b.style.borderRadius = item.value;
      b.style.cornerShape = item.round ? 'round' : 'squircle';
      return b;
    },
    line: function (item) {
      var b = el('i', 'sw lineart');
      var edge = colourOf(item, '--edge'), rule = colourOf(item, '--rule'), hair = colourOf(item, '--hairline');
      if (item.form === 'inset') b.style.boxShadow = 'inset 0 0 0 1px ' + edge;
      if (item.form === 'border') { b.style.border = '1px solid ' + edge; b.style.borderRadius = '999px'; b.style.cornerShape = 'round'; }
      if (item.form === 'outside') b.style.boxShadow = '0 0 0 1px rgba(0,0,0,.30)';
      if (item.form === 'focus') b.style.boxShadow = 'inset 0 0 0 1px ' + colourOf({ root: 'modal' }, '--faint');
      if (item.form === 'divider') {
        b.style.boxShadow = 'inset 0 0 0 1px ' + edge;
        var r = el('i', 'divline'); r.style.background = hair; b.appendChild(r);
      }
      if (item.form === 'border' || item.form === 'outside') b.style.background = '#fff';
      void rule;
      return b;
    },
    shadow: function (item) {
      var b = el('i', 'sw shadow');
      b.style.boxShadow = item.value || colourOf(item, item.token);
      return b;
    },
    gap: function (item) {
      var b = el('i', 'sw gap');
      b.style.gap = item.value;
      b.appendChild(el('i')); b.appendChild(el('i'));
      return b;
    },
    height: function (item) {
      var b = el('i', 'sw height');
      var bar = el('i'); bar.style.height = item.value; b.appendChild(bar);
      return b;
    },
    width: function (item) {
      var b = el('i', 'sw width');
      var bar = el('i');
      bar.style.width = Math.max(4, Math.round(parseInt(item.value, 10) / 1160 * 100)) + '%';
      b.appendChild(bar);
      return b;
    }
  };

  // what the meta line prints as the handle and the value
  function handle(item, kind) {
    if (kind === 'button' || kind === 'plate') {
      var parts = [(item.fill.slice(0, 2) === '--' ? item.fill : 'literal') + ' ' + shown(item, item.fill)];
      if (item.ring) parts.push('ring ' + shown(item, item.ring));
      if (item.ink) parts.push('ink ' + shown(item, item.ink));
      return parts.join('  ·  ');
    }
    if (kind === 'face') return item.weights;
    if (kind === 'size') return item.size + ' / ' + item.line + (item.weight === 700 ? ' bold' : '');
    if (kind === 'corner' || kind === 'gap' || kind === 'height' || kind === 'width') return item.value;
    if (kind === 'line') return { inset: 'inset 0 0 0 1px --edge', border: '1px solid --edge',
      outside: '0 0 0 1px rgba(0,0,0,.30)', focus: 'inset 0 0 0 1px --faint',
      divider: 'border-bottom 1px --hairline' }[item.form];
    if (kind === 'shadow') return (item.token || 'literal') + '  ·  ' + Lab.hex(item.value || colourOf(item, item.token));
    return (item.token || 'literal') + '  ·  ' + shown(item, item.token || item.value);
  }

  function render(section, groups) {
    var host = document.querySelector('[data-spec="' + section + '"]');
    if (!host) return;
    groups.forEach(function (g) {
      var kind = g.kind || 'colour';
      host.appendChild(el('h3', 'gname', g.group));
      if (g.note) host.appendChild(el('p', 'gnote', g.note));
      var grid = el('div', 'tks k-' + kind);
      g.items.forEach(function (item) {
        var row = el('div', 'tk');
        var art = el('div', 'tkart');
        art.appendChild(draw[kind](item));
        row.appendChild(art);
        var meta = el('div', 'tkmeta');
        var name = item.name || item.value, code = handle(item, kind);
        meta.appendChild(el('span', 'tkname', name));
        if (code && code !== name) meta.appendChild(el('code', 'tkval', code));   // a gap's name is its value
        meta.appendChild(el('span', 'tkuse', item.use));
        row.appendChild(meta);
        grid.appendChild(row);
      });
      host.appendChild(grid);
    });
  }

  function start() {
    if (!document.querySelector('[data-spec]')) return;   // the audit page loads this file too
    probes();
    Object.keys(window.Spec).forEach(function (k) { render(k, window.Spec[k]); });
    // the pieces section is real markup, so it only needs the plain-words pass Lab already does
    var n = document.querySelectorAll('.tk').length;
    var out = document.getElementById('refcount');
    if (out) out.textContent = n + ' values';
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
