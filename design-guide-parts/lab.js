// The drawn guide's helpers. Loaded once in the head of design-guide.html; every fragment's inline script uses window.Lab.
// Ids repeat across demos (the site keys rules on #menuBar, #ad, #mainContainer ...), so a demo's script must measure
// with its own root's querySelector and never getElementById.
(function () {
  var COL = /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)/g;
  function hex1(r, g, b, a) {
    var h = function (n) { return Number(n).toString(16).padStart(2, '0'); };
    if (a !== undefined && a !== '' && Number(a) < 1) return 'rgba(' + r + ', ' + g + ', ' + b + ', ' + String(Number(a).toFixed(2)).replace(/^0/, '').replace(/0$/, '') + ')';
    return '#' + h(r) + h(g) + h(b);
  }
  var SRGB = /color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*(?:\/\s*([\d.]+%?))?\s*\)/g;
  function hexify(v) {
    return String(v == null ? '' : v)
      .replace(SRGB, function (m, r, g, b, a) { var c = function (x) { return Math.round(Number(x) * 255); }; if (a && /%$/.test(a)) a = Number(a.slice(0, -1)) / 100; return hex1(c(r), c(g), c(b), a); })
      .replace(COL, function (m, r, g, b, a) { return hex1(r, g, b, a); });
  }
  // one shadow layer the way the guide writes it: inset first, lengths, colour last, no trailing zero spread.
  // a filter's drop-shadow() layers take the same order inside their parentheses, with a trailing zero blur dropped
  function splitTop(s, sep) {
    var out = [], depth = 0, cur = '', i, c;
    for (i = 0; i < s.length; i++) {
      c = s.charAt(i);
      if (c === '(') depth++;
      if (c === ')') depth--;
      if (depth === 0 && (sep === ',' ? c === ',' : /\s/.test(c))) { if (cur.trim()) out.push(cur.trim()); cur = ''; continue; }
      cur += c;
    }
    if (cur.trim()) out.push(cur.trim());
    return out;
  }
  function shadowForm(v) {
    v = hexify(v);
    if (/drop-shadow\(/.test(v)) {
      return v.replace(/drop-shadow\(([^()]*(?:\([^()]*\)[^()]*)*)\)/g, function (m, inner) {
        var colour = '', lens = [];
        splitTop(inner, ' ').forEach(function (t) { if (/^(#|rgba?\()/.test(t)) colour = t; else lens.push(t === '0px' ? '0' : t); });
        if (lens.length === 3 && lens[2] === '0') lens.pop();
        return 'drop-shadow(' + lens.join(' ') + (colour ? ' ' + colour : '') + ')';
      });
    }
    return v.split(/,\s*(?![^(]*\))/).map(function (part) {
      part = part.trim();
      var m = part.match(/^(#[0-9a-f]{6}|rgba\([^)]*\))\s+(.+)$/i); if (m) part = m[2] + ' ' + m[1];
      var inset = false;
      if (/(^|\s)inset(\s|$)/.test(part)) { inset = true; part = part.replace(/(^|\s)inset(?=\s|$)/, '').trim(); }
      part = part.replace(/^(\S+ \S+ \S+) 0(?:px)?(?= |$)/, '$1');
      return (inset ? 'inset ' : '') + part;
    }).join(', ');
  }
  function norm(v) {
    var s = shadowForm(String(v).toLowerCase().trim().replace(/\s+/g, ' ').replace(/\s*,\s*/g, ', '));
    s = s.replace(/(^|[\s,(])(\d*\.?\d+)s(?=$|[\s,)])/g, function (m, p, n) { return p + Math.round(parseFloat(n) * 1000) + 'ms'; });
    s = s.replace(/(^|[\s,(])0\.(\d)/g, '$1.$2');
    s = s.replace(/(\d)\.0+(px|em|s|ms|%)/g, '$1$2').replace(/(\d+\.\d*?[1-9])0+(px|em|s|ms|%)/g, '$1$2').replace(/(^|\s)0px/g, '$10').replace(/\s*\/\s*/g, '/');
    s = s.replace(/"/g, '').replace(/'/g, '');
    return s;
  }
  // site.css scopes with :where(.site):is(div) for body and html, :where(.site):is(.site) for :root and a bare
  // :where(.site) prefix otherwise; a demo names a selector the short way (.site .x, .site.wm .x, .site.site.fp .x)
  function canon(sel) {
    return String(sel).replace(/:where\(\.site\):is\(div\):is\(div\)/g, '.site.site').replace(/:where\(\.site\):is\(div\)/g, '.site')
      .replace(/:where\(\.site\):is\(\.site\)/g, '.site').replace(/:where\(\.site\)/g, '.site').replace(/\s+/g, ' ').trim();
  }
  function selMatch(selectorText, want) {
    var w = canon(want);
    return String(selectorText).split(/,(?![^(]*\))/).some(function (x) { return canon(x) === w; });
  }
  // the last rule for the selector that declares the property (or the last rule at all when prop is not given).
  // A rule inside a width or height @media that does not match at the size the page is being read at is skipped:
  // the phone's own answer is not what a desk-width row is asking about, and reading it made the site's phone
  // steps look like faults (the notification panel's placement). Feature queries such as prefers-reduced-motion
  // are left alone, since a row that asks about them is asking for the rule inside.
  function findRule(sel, prop) {
    var out = null;
    for (var i = 0; i < document.styleSheets.length; i++) {
      var rules; try { rules = document.styleSheets[i].cssRules; } catch (e) { continue; }
      (function walk(list) {
        for (var j = 0; j < list.length; j++) {
          var r = list[j];
          if (r.media && /width|height/.test(r.media.mediaText) && !matchMedia(r.media.mediaText).matches) continue;
          if (r.cssRules && r.cssRules.length && !r.selectorText) { walk(r.cssRules); continue; }
          if (r.selectorText && selMatch(r.selectorText, sel) && (!prop || (r.style && r.style.getPropertyValue(prop)))) out = r;
        }
      })(rules);
    }
    return out;
  }
  // the card's padded body is where tables and notes go; a bare card takes them directly
  function host(card) { return (card && card.querySelector(':scope > .body')) || card; }

  // Holger reads this page to see the design, not to read measurements, so the rule and the numbers sit behind a
  // disclosure and only the drawing is in the open. A card whose measurements disagree with the guide opens itself,
  // which is the one thing he does want to catch at a glance.
  function panel(card) {
    var h = host(card), d = h.querySelector(':scope > details.det');
    if (!d) {
      d = document.createElement('details'); d.className = 'det';
      var sum = document.createElement('summary');
      sum.innerHTML = '<i class="ar"></i><span class="dl">The rule and the numbers</span>';
      d.appendChild(sum);
      var body = document.createElement('div'); body.className = 'detbody';
      d.appendChild(body);
      h.appendChild(d);
    }
    return d.querySelector(':scope > .detbody');
  }
  // a card's title without its tag
  function titleOf(card) {
    var h3 = card.querySelector(':scope > .body > h3') || card.querySelector('h3');
    if (!h3) return '';
    var c = h3.cloneNode(true);
    [].slice.call(c.querySelectorAll('.tag')).forEach(function (t) { t.parentNode.removeChild(t); });
    return c.textContent.replace(/\s+/g, ' ').trim();
  }
  // shadows print with the colour last, as the guide writes them
  function show(v) { return /(#[0-9a-f]{6}|rgba?\(|color\()/i.test(String(v)) && /\d(px)?\s+\d/.test(String(v)) ? shadowForm(v) : hexify(v); }
  var Lab = {
    hex: hexify,
    norm: norm,
    canon: canon,
    selMatch: selMatch,
    findRule: findRule,
    // computed value of a property on an element (or one of its pseudo-elements), colours as hex
    cs: function (el, prop, pseudo) { return el ? hexify(getComputedStyle(el, pseudo || null).getPropertyValue(prop).trim()) : '(no element)'; },
    // the colour an expression resolves to inside a root: a throwaway span is given it and read, which is how a
    // color-mix() token or a rule's var() is turned into the hex the guide writes
    resolve: function (root, expr) {
      if (!root) return '(no element)';
      var probe = document.createElement('span');
      probe.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden';
      probe.style.color = expr;
      root.appendChild(probe);
      var v = hexify(getComputedStyle(probe).color);
      probe.parentNode.removeChild(probe);
      return v;
    },
    // weight size/line, the way the role table writes it
    font: function (el) { if (!el) return '(no element)'; var c = getComputedStyle(el); return c.fontWeight + ' ' + c.fontSize + '/' + c.lineHeight; },
    // the file name of a background image
    img: function (el, prop) { var v = Lab.cs(el, prop || 'background-image'), m = v.match(/url\(["']?([^"')]+)/); return m ? m[1].replace(/^.*\//, '').replace(/\?.*$/, '') : v; },
    // the same for art the build inlined: a data url carries no file name, so it is looked up by the head of its base64
    assetName: function (el, prop) {
      var v = Lab.cs(el, prop || 'mask-image'), m = v.match(/url\(["']?([^"')]+)/);
      if (!m) return '(none)';
      var d = m[1];
      if (d.slice(0, 5) === 'data:') {
        return (window.Assets && window.Assets[d.slice(d.indexOf(',') + 1)]) || '(inlined, unknown)';
      }
      return d.replace(/^.*\//, '').replace(/\?.*$/, '');
    },
    // a tray's thumb and the white copy of its words, built and placed the way ModalShell.placeSegThumb does it:
    // the thumb goes in first, the copy of the cells last, and the copy is clipped to the thumb's box. The pick is a
    // class on a cell, which is all the site's own handlers set; a click moves it, and the thumb travels.
    seg: function (node, cls) {
      cls = cls || {};
      var c = { cell: cls.cell || 'wmCell', picked: cls.picked || 'wmPicked', thumb: cls.thumb || 'wmSegThumb', ink: cls.ink || 'wmSegInk', still: cls.still || 'wmStill' };
      if (!node || node.querySelector(':scope > .' + c.thumb)) return null;
      var thumb = document.createElement('i');
      thumb.className = c.thumb + ' ' + c.still;
      node.insertBefore(thumb, node.firstChild);
      var ink = document.createElement('span');
      ink.className = c.ink + ' ' + c.still;
      ink.setAttribute('aria-hidden', 'true');
      node.querySelectorAll(':scope > .' + c.cell).forEach(function (cell) {
        var copy = cell.cloneNode(true);
        copy.removeAttribute('role'); copy.removeAttribute('tabindex'); copy.removeAttribute('aria-checked'); copy.removeAttribute('aria-selected');
        ink.appendChild(copy);
      });
      node.appendChild(ink);
      function place() {
        var cell = node.querySelector(':scope > .' + c.cell + '.' + c.picked);
        if (!cell || !node.offsetWidth) {
          thumb.style.opacity = '0'; ink.style.clipPath = 'inset(0 100% 0 0)';
          thumb.classList.add(c.still); ink.classList.add(c.still); return;
        }
        var left = cell.offsetLeft, top = cell.offsetTop, w = cell.offsetWidth, h = cell.offsetHeight;
        thumb.style.left = left + 'px'; thumb.style.top = top + 'px'; thumb.style.width = w + 'px'; thumb.style.height = h + 'px'; thumb.style.opacity = '1';
        ink.style.clipPath = 'inset(' + top + 'px ' + (node.offsetWidth - left - w) + 'px ' + (node.offsetHeight - top - h) + 'px ' + left + 'px)';
        if (thumb.classList.contains(c.still)) { void thumb.offsetWidth; thumb.classList.remove(c.still); ink.classList.remove(c.still); }
      }
      node.addEventListener('click', function (e) {
        var cell = e.target.closest && e.target.closest('.' + c.cell);
        if (!cell || cell.closest('.' + c.ink) || cell.parentNode !== node) return;
        node.querySelectorAll(':scope > .' + c.cell).forEach(function (one) {
          var on = one === cell;
          one.classList.toggle(c.picked, on);
          if (one.hasAttribute('aria-checked')) one.setAttribute('aria-checked', on ? 'true' : 'false');
          if (one.hasAttribute('aria-selected')) one.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        place();
      });
      place();
      if (window.ResizeObserver) new window.ResizeObserver(place).observe(node);
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(place);
      return { place: place, thumb: thumb, ink: ink };
    },
    // a custom property read from an element (a token)
    token: function (el, name) { return el ? hexify(getComputedStyle(el).getPropertyValue(name).trim()) : '(no element)'; },
    // a value read straight from the CSSOM for a selector the page cannot compute (hover, focus, active); the last rule wins
    // el (optional) is the element whose tokens resolve any var(--x) in the rule's value; defaults to the first .site root
    rule: function (sel, prop, el) {
      var r = findRule(sel, prop); if (!r) return '';
      var v = r.style.getPropertyValue(prop).trim(), root = el || document.querySelector('.site');
      for (var i = 0; i < 4 && /var\(--/.test(v) && root; i++) {
        v = v.replace(/var\((--[a-z0-9-]+)(?:,\s*([^)]+))?\)/gi, function (m, name, fb) { var t = getComputedStyle(root).getPropertyValue(name).trim(); return t || fb || m; });
      }
      return hexify(v);
    },
    same: function (a, b) { return norm(a) === norm(b); },
    // rows: [{what, got, want, tag}]  tag: built (default) | call | open | stale | rule | note
    // built and rule turn red when got and want disagree; stale is red and named so the guide is what gets fixed;
    // call prints the guide's own invented value beside the measured one, never red; open prints the guide's open item.
    table: function (card, rows, title) {
      var t = document.createElement('table'); t.className = 'mtab';
      if (title) { var c = document.createElement('caption'); c.textContent = title; t.appendChild(c); }
      var hd = t.createTHead().insertRow();
      ['Property', 'Measured', 'Guide', ''].forEach(function (x) { var th = document.createElement('th'); th.textContent = x; hd.appendChild(th); });
      var body = t.createTBody();
      rows.forEach(function (r) {
        var tag = r.tag || 'built', tr = body.insertRow();
        var got = (r.got == null || r.got === '') ? '(none)' : show(r.got);
        var want = (r.want == null) ? '' : show(r.want);
        var bad = (tag === 'built' || tag === 'rule' || tag === 'stale') && want !== '' && !Lab.same(got, want);
        tr.insertCell().textContent = r.what;
        var g = tr.insertCell(); g.textContent = got; if (bad) g.className = 'mbad';
        tr.insertCell().textContent = want;
        var tc = tr.insertCell(); tc.className = 'mtag ' + tag;
        tc.textContent = { built: '', call: "guide's call", open: 'open', stale: 'stale', rule: 'from the rule', note: '' }[tag] || tag;
        if (bad) tr.setAttribute('data-bad', '1');
      });
      panel(card).appendChild(t); return t;
    },
    note: function (card, text) { var p = document.createElement('p'); p.className = 'rl'; p.textContent = text; panel(card).appendChild(p); return p; },
    // the card's own title, without its tag
    titleOf: titleOf,
    // every card with no plain-words line, for the headless report
    plainless: function () {
      return [].slice.call(document.querySelectorAll('.sec .card')).filter(function (c) { return !c.querySelector('.lead'); })
        .map(function (c) { var sec = c.closest('.sec'); return (sec ? sec.id : '?') + ': ' + (titleOf(c) || '(untitled)'); });
    },
    // every red row on the page, for the headless report
    bads: function () {
      return [].slice.call(document.querySelectorAll('tr[data-bad]')).map(function (tr) {
        var sec = tr.closest('.sec'), card = tr.closest('.card'), c = tr.cells, h = card && card.querySelector('h3');
        return { section: sec ? sec.id : '', demo: h ? h.textContent : '', what: c[0].textContent, got: c[1].textContent, want: c[2].textContent, tag: c[3].textContent };
      });
    }
  };
  // The probe mode. A card that has to measure a width this window cannot have serves the page to an
  // iframe with ?probe=1, and the frame shows one probe set and nothing else. ?set=<name> picks
  // .probeset[data-set="<name>"]; without it the first probe set in the page is the one shown. The page
  // is hidden rather than emptied, so nothing another section's script holds is taken out of the document.
  var probeSet = (location.search.match(/[?&]set=([a-z0-9-]+)/i) || [])[1] || '';
  window.PROBE = /(?:^|[?&])probe=1/.test(location.search);
  window.PROBE_SET = probeSet;
  if (window.PROBE) {
    document.addEventListener('DOMContentLoaded', function () {
      var set = probeSet ? document.querySelector('.probeset[data-set="' + probeSet + '"]') : document.querySelector('.probeset');
      [].slice.call(document.body.children).forEach(function (el) { el.style.display = 'none'; });
      document.body.style.padding = '0';
      document.body.style.background = '#f9f6f2';
      if (set) { document.body.appendChild(set); set.hidden = false; set.style.display = ''; }
    });
  }

  // The frames themselves: one well per width, each holding the page at that width, drawn down by scale.
  // onLoad(entry) is called for every frame once it has loaded, with { w, node, doc }.
  Lab.frames = function (host, widths, opts) {
    opts = opts || {};
    var scale = opts.scale || 0.4, H = opts.height || 900, set = opts.set ? '&set=' + opts.set : '';
    return widths.map(function (w) {
      var wrap = document.createElement('div');
      wrap.className = 'pf';
      wrap.style.width = Math.round(w * scale) + 'px';
      wrap.style.height = Math.round(H * scale) + 'px';
      var f = document.createElement('iframe');
      f.style.width = w + 'px';
      f.style.height = H + 'px';
      f.style.transform = 'scale(' + scale + ')';
      f.setAttribute('title', 'the page at ' + w + 'px');
      f.src = location.pathname + '?probe=1' + set;
      wrap.appendChild(f);
      host.appendChild(wrap);
      var entry = { w: w, node: f, height: H };
      if (opts.onLoad) f.addEventListener('load', function () { entry.doc = f.contentDocument; opts.onLoad(entry); });
      return entry;
    });
  };

  // Each card is given its plain-words line (and, where the builder's title was jargon, a plain title) from plain.js,
  // keyed by section and by the title the fragment carries. Then the rule text joins the numbers in the panel, and a
  // card that disagrees with the guide opens itself and says how many rows differ.
  function dress() {
    var plain = window.Plain || {}, secs = window.PlainSections || {};
    // Each section says in one line what is in it. The builder's own note, which names the guide's numbers and the
    // scopes the pieces are drawn in, moves behind a disclosure of its own.
    [].slice.call(document.querySelectorAll('.sec')).forEach(function (sec) {
      var lead = secs[sec.id]; if (!lead || sec.querySelector(':scope > .seclead')) return;
      var desc = sec.querySelector(':scope > .desc'), rule = sec.querySelector(':scope > .rule');
      var p = document.createElement('p'); p.className = 'seclead'; p.textContent = lead;
      (rule || sec.firstElementChild).insertAdjacentElement('afterend', p);
      if (!desc) return;
      var d = document.createElement('details'); d.className = 'det secdet';
      d.innerHTML = '<summary><i class="ar"></i><span class="dl">How this section is drawn</span></summary>';
      desc.parentNode.insertBefore(d, desc);
      d.appendChild(desc);
    });
    [].slice.call(document.querySelectorAll('.sec .card')).forEach(function (card) {
      var sec = card.closest('.sec'), map = plain[sec ? sec.id : ''] || {};
      var h3 = card.querySelector(':scope > .body > h3') || card.querySelector('h3');
      var entry = map[titleOf(card)];
      if (entry && h3) {
        if (entry.title) {
          var tags = [].slice.call(h3.querySelectorAll('.tag'));
          h3.textContent = entry.title + ' ';
          tags.forEach(function (t) { h3.appendChild(t); });
        }
        if (entry.lead) {
          var p = document.createElement('p'); p.className = 'lead'; p.textContent = entry.lead;
          h3.parentNode.insertBefore(p, h3.nextSibling);
        }
      }
      var body = card.querySelector('.detbody');
      var rt = host(card).querySelector(':scope > .rule-text');
      if (rt && body) body.insertBefore(rt, body.firstChild);
      var bad = card.querySelectorAll('tr[data-bad]').length;
      var det = card.querySelector('details.det');
      if (bad && det) {
        det.open = true;
        var chip = document.createElement('span'); chip.className = 'dbad';
        chip.textContent = bad === 1 ? 'one row differs from the guide' : bad + ' rows differ from the guide';
        det.querySelector('summary').appendChild(chip);
      }
    });
    [].slice.call(document.querySelectorAll('#toc a[href^="#"]')).forEach(function (a) {
      var sec = document.querySelector(a.getAttribute('href'));
      if (sec && sec.querySelector('tr[data-bad]')) a.insertAdjacentHTML('beforeend', '<span class="dot"></span>');
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', dress); else dress();

  // A card off the screen then stops rendering at all: 15,000 nodes, 120 filtered avatars and the felt scenes are
  // far more than a browser should hold live at once, and a page this tall took Chrome's renderer down. Each card
  // is given its own measured height as the placeholder, so nothing jumps as it scrolls. This runs on load and not
  // in the sheet, because a card that has not rendered cannot be measured and the fragments measure as they parse.
  function thin() {
    [].slice.call(document.querySelectorAll('.sec .card')).forEach(function (c) {
      var h = c.getBoundingClientRect().height;
      if (h < 1) return;
      c.style.containIntrinsicSize = 'auto ' + Math.round(h) + 'px';
      c.style.contentVisibility = 'auto';
    });
  }
  if (document.readyState === 'complete') thin(); else window.addEventListener('load', function () { setTimeout(thin, 120); });

  window.Lab = Lab;
})();
