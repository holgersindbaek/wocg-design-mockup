// The chooser labs' drawing kit: a frame that is a real table root (the site's body classes on a div, the felt,
// the playspace), and the site's own pieces in it, written as the table writes them (Table.createPiece, the button
// and suitSelector pieces, Table.showTrumpPill, Table.pickTrumpPillSuit). site.css paints all of them.
window.CL = (function () {
  // A phone's viewport sets these tokens through a media query (max-width or max-height 640px), which a desktop
  // window never meets, so a phone's frame sets them itself. The table's compact class does the rest.
  const PHONE_TOKENS = { '--space-viewport-gutter': '8px', '--shadow-modal': '0 0 16px rgba(0,0,0,0.4)', '--radius-sm': '4px',
    '--radius-md': '8px', '--radius-lg': '12px', '--radius-xl': '20px' };
  const DEVICES = {
    desktop: { key: 'desktop', name: 'Desktop', H: 40, G: 8, P: 2, pad: 12, compact: false, btnMax: 20, tokens: null,
      mc: 'unselectable playspace-landscape', picture: 'chooser-lab-parts/table-desktop.jpg' },
    phone: { key: 'phone', name: 'Phone', H: 32, G: 8, P: 2, pad: 12, compact: true, btnMax: 18, tokens: PHONE_TOKENS,
      mc: 'unselectable playspace-compact playspace-small playspace-portrait', picture: 'chooser-lab-parts/table-phone.jpg' },
    side: { key: 'side', name: 'Phone on its side', H: 32, G: 8, P: 2, pad: 12, compact: true, btnMax: 18, tokens: PHONE_TOKENS,
      mc: 'unselectable playspace-compact playspace-small playspace-landscape', picture: 'chooser-lab-parts/table-side.jpg' },
  };
  const SIGN = { club: '♣', diamond: '♦', heart: '♥', spade: '♠' };

  function el(tag, cls, style, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (style) e.setAttribute('style', style);
    if (html != null) e.innerHTML = html;
    return e;
  }

  // A table root w x h. With a picture, the felt is the dev table as it was captured, and the playspace stands
  // where it stood (psX, psY, psW, psH); without one, the felt is the site's own green felt.
  function frame(dev, w, h, opts) {
    opts = opts || {};
    const root = el('div', 'site wm classic' + (opts.rootClass ? ' ' + opts.rootClass : ''),
      'display:block;position:relative;margin:0;padding:0;min-height:0;min-width:0;width:' + w + 'px;height:' + h + 'px;background:none;overflow:hidden;font-size:16px;line-height:normal;');
    root.dataset.activeGame = opts.game || 'bridge';
    root.dataset.table = 'true';
    if (dev.tokens) for (const k in dev.tokens) root.style.setProperty(k, dev.tokens[k]);
    const felt = opts.picture
      ? 'background-color:rgb(50, 115, 51);background-image:url("' + opts.picture + '");background-repeat:no-repeat;background-size:' + w + 'px ' + h + 'px;background-position:0px 0px;'
      : 'background-color:rgb(50, 115, 51);background-image:url("static/pieces/wallpaper/fabrics/green-felt.jpg");background-repeat:repeat;background-size:100px 100px;background-position:0px 0px;';
    const mc = el('div', dev.mc, 'position:relative;width:' + w + 'px;height:' + h + 'px;overflow:hidden;' + felt);
    mc.id = 'mainContainer';
    const ps = el('div', 'playspace unselectable ' + (opts.game || 'bridge'),
      'position:absolute;opacity:1;left:' + (opts.psX || 0) + 'px;top:' + (opts.psY || 0) + 'px;width:' + (opts.psW || w) + 'px;height:' + (opts.psH || h) + 'px;');
    ps.id = 'playspace';
    mc.appendChild(ps);
    root.appendChild(mc);
    return { root: root, mc: mc, ps: ps, dev: dev };
  }

  function place(e, b) {
    e.style.left = b.x + 'px';
    e.style.top = b.y + 'px';
    e.style.width = b.w + 'px';
    e.style.height = b.h + 'px';
  }

  function piece(f, cls, b, z) {
    const e = el('div', 'piece classic ' + cls, 'opacity:1;z-index:' + (z || 8001) + ';');
    place(e, b);
    f.ps.appendChild(e);
    return e;
  }

  // A table button as piece/button.js writes it: the word in a centred line the button's height
  function button(f, spot, b, html, opts) {
    opts = opts || {};
    const e = piece(f, 'id-' + (opts.id || spot + '0') + ' button spot-' + spot + ' spotPrefix-' + spot.replace(/\d+$/, '') + (opts.onBackdrop ? ' onBackdrop' : ''), b);
    e.style.lineHeight = b.h + 'px';
    e.appendChild(el('div', null, 'text-align:center;height:' + b.h + 'px;line-height:' + b.h + 'px;', html));
    setEnabled(e, !opts.disabled);
    return e;
  }

  function setEnabled(e, on) {
    e.classList.toggle('disabled', !on);
    e.classList.toggle('clickable', on);
  }

  function setWord(e, html) {
    e.firstChild.innerHTML = html;
  }

  // FitText.fit as a button uses it: the largest size, up to the table's own (20 on a desktop, 18 on a phone), at
  // which the bold word is narrower than the button less 8 and lower than the button
  function fitSize(f, e) {
    const w = e.offsetWidth, h = e.offsetHeight;
    const sz = el('span', 'sizer', 'font-weight:bold;white-space:nowrap;', e.firstChild.innerHTML);
    f.mc.appendChild(sz);
    let s = f.dev.btnMax;
    for (; s > 6; s--) {
      sz.style.fontSize = s + 'px';
      if (sz.offsetWidth < w - 8 && sz.offsetHeight < h) break;
    }
    sz.remove();
    return s;
  }

  // Under the redesign a row of buttons prints its words at the smallest size any of them fits (button.js fitRow)
  function fit(f, buttons, asRow) {
    const sizes = buttons.map((e) => fitSize(f, e));
    const row = Math.min.apply(null, sizes);
    buttons.forEach((e, i) => { e.style.fontSize = (asRow ? row : sizes[i]) + 'px'; });
  }

  // A pill's cells in the track b (one row, a button's height), as Table.showTrumpPill lays them: a cell per suit a
  // tray's 2px in, shared out on whole pixels (Layout.createTrumpPillCellSpot). A cell is a suit or carries text
  // (cl-textCell, a proposal). base numbers the spots, so two rows in one frame do not share a spot id.
  function pillCells(f, b, cells, base) {
    const P = f.dev.P;
    const inner = b.w - 2 * P;
    const edge = (i) => Math.round((i * inner) / cells.length);
    return cells.map(function (c, i) {
      const cls = 'id-' + c.id + ' suitSelector spot-suitSelector' + ((base || 0) + i) + ' spotPrefix-suitSelector trumpPillCell' +
        (i ? ' trumpPillRule' : '') + (c.text ? ' cl-textCell' : '') + ' clickable';
      const e = piece(f, cls, { x: b.x + P + edge(i), y: b.y + P, w: edge(i + 1) - edge(i), h: b.h - 2 * P });
      e.style.lineHeight = (b.h - 2 * P) + 'px';
      e.style.fontSize = '29px';
      e.textContent = c.text || SIGN[c.id] || '';
      return e;
    });
  }

  // One pill cell in a box of its own width (a stepper's arrow or value, a slider's arrow). A cell with art draws it as
  // the pill draws a suit: the drawing as a mask in the cell's ink (--trump-pill-suit, --trump-pill-ink)
  function cell(f, b, id, n, opts) {
    opts = opts || {};
    const cls = 'id-' + id + ' suitSelector spot-suitSelector' + n + ' spotPrefix-suitSelector trumpPillCell' +
      (opts.rule ? ' trumpPillRule' : '') + (opts.text != null ? ' cl-textCell' : '') + ' clickable';
    const e = piece(f, cls, b);
    e.style.lineHeight = b.h + 'px';
    e.style.fontSize = '29px';
    if (opts.text != null) e.textContent = opts.text;
    if (opts.art) {
      e.style.setProperty('--trump-pill-suit', 'url("' + opts.art + '")');
      e.style.setProperty('--trump-pill-ink', 'var(--ink)');
    }
    return e;
  }

  // The site's own suit pill: the paper (its ::after is the thumb) and its cells
  function pill(f, b, cells, base) {
    const paper = piece(f, 'id-simple backdrop spot-trumpPill spotPrefix-trumpPill', b, 8000);
    paper.style.setProperty('--trump-cells', cells.length);
    return { paper: paper, cells: pillCells(f, b, cells, base), box: b };
  }

  // Table.pickTrumpPillSuit: the thumb slides under the picked cell (the first pick lands there), the lines beside it
  // go. -1 clears the pick (the thumb fades).
  function pickPill(p, index) {
    p.cells.forEach(function (c, i) {
      c.classList.toggle('selected', i === index);
      c.classList.toggle('afterPicked', index > -1 && index === i - 1);
    });
    if (index < 0) {
      p.paper.classList.remove('picked');
      return;
    }
    const first = !p.paper.classList.contains('picked');
    if (first) p.paper.classList.add('still');
    p.paper.style.setProperty('--trump-pick', index);
    p.paper.classList.add('picked');
    if (first) {
      p.paper.getBoundingClientRect();
      p.paper.classList.remove('still');
    }
  }

  // A cell no tap can pick, as showTrumpPill fades it
  function fadeCell(c, faded) {
    c.classList.toggle('unselectable', faded);
    c.classList.toggle('clickable', !faded);
  }

  // Relative luminance contrast, for the numbers behind a version's disclosure
  function lum(hex) {
    const v = hex.replace('#', '').match(/../g).map((x) => parseInt(x, 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)));
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2];
  }
  function contrast(a, b) {
    const x = lum(a), y = lum(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  }

  // A row of lab switches: [{label, key, options: [[value, text], ...]}] over a settings object
  function switches(holder, defs, S, onChange) {
    defs.forEach(function (d) {
      const box = el('span', 'cl-ctl', null, d.label);
      const seg = el('span', 'cl-seg');
      d.options.forEach(function (o) {
        const btn = el('button', S[d.key] === o[0] ? 'cl-on' : '', null, o[1]);
        btn.type = 'button';
        btn.addEventListener('click', function () {
          S[d.key] = o[0];
          seg.querySelectorAll('button').forEach((x) => x.classList.toggle('cl-on', x === btn));
          onChange(d.key);
        });
        seg.appendChild(btn);
      });
      box.appendChild(seg);
      holder.appendChild(box);
    });
  }

  return { DEVICES, SIGN, el, frame, place, piece, button, setEnabled, setWord, fit, pillCells, cell, pill, pickPill, fadeCell, contrast, switches };
})();
