// The captured Hearts table's own script (build.js puts it into icon-lab-table-frame.html, after the data
// in window.ICONLAB_TABLE). It repaints the table's icons with a colour version:
//  - every site CSS rule that paints an icon (captured with its @media and @supports, a hover or open
//    state included) gets a twin with the same selector whose background-image is the recoloured art;
//  - every <img> of an icon (the bell and the friends icon in the pill) gets the recoloured art.
// The table always stands in a frame 1440 by 900, the size it was captured at, so its own layout and
// media queries stay as the game drew them: in the lab page's table, or in the viewer icon-lab-table.html,
// which scales the frame to the window and keeps the version switcher. Either one drives it with
// postMessage({ iconlab: true, id, ver }); a message without `ver` names one of the versions built in.
// The left and right arrow keys and z, pressed while the table has the focus, go to the parent, which
// steps through the versions or flips between As built and the latest pick.
(function () {
  'use strict';
  var D = window.ICONLAB_TABLE;
  if (!D) return;
  // opened on its own, the table goes to its viewer
  if (window.top === window) { location.replace('icon-lab-table.html' + location.hash); return; }

  var NAMED = { white: '#FFFFFF', black: '#000000' };
  function normHex(v) {
    v = String(v).trim(); var l = v.toLowerCase(); if (NAMED[l]) return NAMED[l];
    var m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(v); if (!m) return null;
    var h = m[1]; if (h.length === 3) h = h.replace(/./g, '$&$&'); return '#' + h.toUpperCase();
  }
  var ATTR = /(\b(?:fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*")([^"]*)(")/gi;
  var STYLE = /(\b(?:fill|stroke|stop-color|flood-color)\s*:\s*)([^;"'}]+)/gi;
  function recolour(svg, fn) {
    return svg.replace(ATTR, function (m, a, v, b) { var h = normHex(v); return h ? a + fn(h) + b : m; })
      .replace(STYLE, function (m, a, v) { var h = normHex(v); return h ? a + fn(h) : m; });
  }
  function resolver(ver, id, key) {
    return function (hex) {
      if (!ver) return hex;
      var s = ver.state && ver.state[id + '/' + key]; if (s && s[hex]) return normHex(s[hex]);
      var i = ver.icon && ver.icon[id]; if (i && i[hex]) return normHex(i[hex]);
      var g = ver.global && ver.global[hex]; return g ? normHex(g) : hex;
    };
  }
  function dataUri(svg) { return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg); }
  // a file named by its master path or by the redesign's copy under images/wm/ (the site since 23 Sep 2026)
  function fileOf(s) { var m = /images\/(?:wm\/)?([A-Za-z0-9_@.-]+\.(?:png|svg))/.exec(s || ''); return m && D.files[m[1]] ? m[1] : null; }
  function builtIn(id) { for (var i = 0; i < D.versions.length; i++) if (D.versions[i].id === id) return D.versions[i]; return null; }

  var style = document.createElement('style');
  style.id = 'iconlabVersion';
  document.head.appendChild(style);
  var imgs = [].slice.call(document.querySelectorAll('img')).filter(function (e) { return fileOf(e.getAttribute('src')); });
  imgs.forEach(function (e) { e.__ilSrc = e.getAttribute('src'); });

  var cache = {};
  function art(file, ver, vid) {
    var key = vid + '|' + file;
    if (cache[key] !== undefined) return cache[key];
    var p = D.files[file], svg = p && D.svgs[p[0] + '/' + p[1]];
    return (cache[key] = svg ? dataUri(recolour(svg, resolver(ver, p[0], p[1]))) : null);
  }
  // a url the rule kept, written from the document rather than from static/css/
  function fromSheet(u) { return u.replace(/^(\.\.\/)+/, 'static/'); }

  function apply(vid, ver) {
    cache = {};
    if (!ver) {
      style.textContent = '';
      imgs.forEach(function (e) { e.setAttribute('src', e.__ilSrc); });
      return;
    }
    var css = [];
    D.rules.forEach(function (r) {
      if (r.prop !== 'background-image') return; // a mask takes its colour from CSS, not from its art
      var hit = false;
      var v = r.value.replace(/url\((['"]?)([^'")]*)\1\)/g, function (m, q, u) {
        var f = fileOf(u), a = f && art(f, ver, vid);
        if (a) { hit = true; return 'url("' + a + '")'; }
        return 'url("' + fromSheet(u) + '")';
      });
      if (!hit) return;
      var rule = r.sel + '{background-image:' + v + ' !important}';
      r.conds.slice().reverse().forEach(function (c) { rule = c + '{' + rule + '}'; });
      css.push(rule);
    });
    style.textContent = css.join('\n');
    imgs.forEach(function (e) { var f = fileOf(e.__ilSrc), a = f && art(f, ver, vid); e.setAttribute('src', a || e.__ilSrc); });
  }

  apply('built', null);
  window.addEventListener('message', function (e) {
    var d = e.data;
    if (!d || !d.iconlab) return;
    apply(d.id, d.ver || (d.id === 'built' ? null : builtIn(d.id)));
  });
  document.addEventListener('keydown', function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
    var flip = (e.key === 'z' || e.key === 'Z') && !e.repeat;
    if (!d && !flip) return;
    e.preventDefault();
    try { window.parent.postMessage(flip ? { iconlabFlip: true } : { iconlabStep: d }, '*'); } catch (err) {}
  });
  try { window.parent.postMessage({ iconlabReady: true }, '*'); } catch (err) {}
})();
