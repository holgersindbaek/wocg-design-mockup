// A use line in sections 1 to 4 names the pieces a value draws. Where Examples draws one of them,
// the name becomes a link to that card, and pointing at it shows that card's own demo in a box: the
// row says what a value is for, and this is how to see it without leaving the row (Holger, 22 Sep 2026).
//
// It is a file of its own rather than a block in assemble.js, because that script writes the page
// out of a template literal and every backslash in a regex would have to survive two passes.
(function () {
  var index = window.ExampleIndex || [];

  function norm(s) {
    return s.toLowerCase().replace(/[‘’]/g, "'").replace(/^(the|a|an)\s+/, '').trim();
  }

  var byKey = {};
  index.forEach(function (e) {
    var k = norm(e.t);
    if (!byKey[k]) byKey[k] = e;
    // a row says "a presence dot" where the card is called "The presence dots"
    var other = k.slice(-1) === 's' ? k.slice(0, -1) : k + 's';
    if (!byKey[other]) byKey[other] = e;
  });

  var keys = Object.keys(byKey)
    .filter(function (k) { return k.length > 2; })   // 'tag' is the shortest name a card has
    .sort(function (a, b) { return b.length - a.length; });

  function quote(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  var rx = keys.length
    ? new RegExp('(?:\\b(?:the|a|an)\\s+)?\\b(' + keys.map(quote).join('|') + ')\\b', 'gi')
    : null;

  function linkify(root) {
    if (!rx) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      var text = node.nodeValue, frag = null, last = 0, m;
      rx.lastIndex = 0;
      while ((m = rx.exec(text))) {
        var hit = byKey[norm(m[1])];
        if (!hit) continue;
        frag = frag || document.createDocumentFragment();
        frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        var a = document.createElement('a');
        a.className = 'exref';
        a.href = '#' + hit.id;
        a.setAttribute('data-ex', hit.id);
        a.textContent = m[0];
        frag.appendChild(a);
        last = m.index + m[0].length;
      }
      if (!frag) return;
      frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  var pop = null, hold = null;

  function show(a) {
    var card = document.getElementById(a.getAttribute('data-ex'));
    if (!card) return;
    if (!pop) {
      pop = document.createElement('div');
      pop.id = 'expop';
      // It hangs inside Examples rather than off the body: some of what draws a piece is
      // written under #pieces, and a clone outside that would lose it. It is fixed, so
      // where it hangs makes no difference to where it lands.
      (document.getElementById('pieces') || document.body).appendChild(pop);
    }
    var title = card.querySelector('h3');
    var demo = card.querySelector('.demo');
    pop.innerHTML = '';
    var head = document.createElement('div');
    head.className = 'exhead';
    head.textContent = title ? title.textContent : '';
    pop.appendChild(head);
    var body = document.createElement('div');
    body.className = 'exbody';
    pop.appendChild(body);
    pop.style.visibility = 'hidden';
    pop.style.display = 'block';
    if (demo) {
      // The ids come across with it. They are doubled while the box is up, which is untidy,
      // but some pieces are drawn by rules written at their own id and stripping them left
      // the box showing unstyled words. Nothing reads an id off the clone: it is inert.
      var clone = demo.cloneNode(true);
      // The clone has to keep the width it was laid out at, or it reflows to the box's
      // own width and a wide piece like the menu bar stacks into a column.
      var w = demo.offsetWidth, h = demo.offsetHeight, max = 616;
      clone.style.width = w + 'px';
      clone.style.maxWidth = 'none';
      clone.style.flex = '0 0 auto';
      // Some of what draws a piece is written as `.card .demo ...`, so the clone keeps that
      // chain around it or it comes out as unstyled words. The two wrappers are stripped of
      // the card's own paint, since the box draws that itself.
      var asCard = document.createElement('div');
      asCard.className = 'card';
      asCard.style.cssText = 'background:none;border:0;box-shadow:none;padding:0;margin:0;width:auto;overflow:visible';
      var asBody = document.createElement('div');
      asBody.className = 'body';
      asBody.style.cssText = 'padding:0;margin:0';
      asBody.appendChild(clone);
      asCard.appendChild(asBody);
      body.appendChild(asCard);
      // Fit the width, but never shrink past .6: a band the width of a page would go to
      // two fifths, where the words are there but nobody can read them. Past that the box
      // shows what it can and clips the rest.
      var scale = Math.max(0.6, Math.min(1, max / w));
      body.style.width = Math.round(Math.min(max, w * scale)) + 'px';
      if (scale < 1) {
        clone.style.transformOrigin = 'top left';
        clone.style.transform = 'scale(' + scale + ')';
        body.style.height = Math.round(Math.min(360, h * scale)) + 'px';
      } else if (h > 360) {
        body.style.height = '360px';
      }
    }
    var r = a.getBoundingClientRect(), box = pop.getBoundingClientRect();
    var left = Math.min(Math.max(8, r.left), window.innerWidth - box.width - 8);
    var top = r.bottom + 8;
    if (top + box.height > window.innerHeight - 8) top = Math.max(8, r.top - box.height - 8);
    pop.style.left = Math.round(left) + 'px';
    pop.style.top = Math.round(top) + 'px';
    pop.style.visibility = '';
  }

  function hide() {
    if (hold) { clearTimeout(hold); hold = null; }
    if (pop) pop.style.display = 'none';
  }

  document.addEventListener('mouseover', function (e) {
    var a = e.target.closest && e.target.closest('a.exref');
    if (!a) return;
    if (hold) clearTimeout(hold);
    hold = setTimeout(function () { show(a); }, 120);
  });
  document.addEventListener('mouseout', function (e) {
    if (e.target.closest && e.target.closest('a.exref')) hide();
  });
  window.addEventListener('scroll', hide, { passive: true });

  // ref.js draws the rows on domready, so the cells may not be there yet
  var tries = 0;
  (function ready() {
    var cells = document.querySelectorAll('.tkuse');
    if (!cells.length && tries++ < 100) { setTimeout(ready, 60); return; }
    cells.forEach(function (c) { linkify(c); });
  })();
})();
