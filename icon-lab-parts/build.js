// Writes ../icon-lab.html from page.html, inventory.js and versions.js.
//
//   node icon-lab-parts/build.js
//
// Every icon is inlined as SVG text (and every animated one as its Lottie JSON), so the
// page recolours them in the browser and still works when it is opened straight from disk.
// Where the site ships an icon as SVG, the page draws that very file. Where the site ships
// a PNG, it draws the vector the PNG was exported from (sketch/, exported with sketchtool
// from Design/WoCG-2.2.sketch; `node icon-lab-parts/check.js --png` compares the two pixel by pixel).
const fs = require('fs');
const path = require('path');

const HERE = __dirname;
const ROOT = path.join(HERE, '..');
const IMG = path.join(ROOT, 'static', 'images');
const inv = require('./inventory.js');

function read(p) { return fs.readFileSync(p, 'utf8'); }
function cleanSvg(txt) {
  txt = txt.replace(/<\?xml[^>]*\?>\s*/g, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<title>[\s\S]*?<\/title>\s*/g, '')
    .replace(/<desc>[\s\S]*?<\/desc>\s*/g, '')
    .replace(/\s+\n/g, '\n');
  if (!/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/.test(txt)) txt = txt.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
  return txt.trim();
}
// A drawn-in-code icon that writes a number (the turn timer) needs the site's face inside the SVG itself: an
// SVG shown as an image cannot reach the page's fonts. The faces come from guide-fonts.css, as data.
let FACES = null;
function withFaces(svg) {
  if (!/BuloRounded/.test(svg)) return svg;
  if (!FACES) {
    const css = read(path.join(ROOT, 'guide-fonts.css'));
    FACES = {};
    css.split('@font-face').slice(1).forEach((f) => { const w = (/font-weight:\s*(\d+)/.exec(f) || [])[1]; if (/BuloRounded/.test(f) && w) FACES[w] = '@font-face' + f.trim(); });
  }
  const w = /font-weight="(?:bold|700)"/.test(svg) ? '700' : '400';
  return svg.replace(/<svg\b[^>]*>/, (m) => m + '<style>' + FACES[w] + '</style>');
}
function svgSize(txt) {
  const w = /<svg[^>]*\swidth="([\d.]+)(?:px)?"/.exec(txt), h = /<svg[^>]*\sheight="([\d.]+)(?:px)?"/.exec(txt);
  if (w && h) return [+w[1], +h[1]];
  const vb = /viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"/.exec(txt);
  return vb ? [+vb[1], +vb[2]] : [24, 24];
}

// The icons and their art, as the page gets them. make-versions.js reads this too.
function assemble() {
const problems = [];
const icons = [];
const categories = inv.categories.map((cat) => {
  const ids = [];
  cat.icons.forEach((def) => {
    const files = [], formats = new Set();
    const states = def.states.map((st) => {
      let svg, src;
      if (st.inline) { src = path.join(HERE, 'inline', st.inline); files.push('drawn in code: ' + st.inline.replace(/\.svg$/, '')); formats.add('drawn in code'); }
      else if (st.sketch) { src = path.join(HERE, 'sketch', st.sketch); files.push('Sketch: ' + st.sketch.replace(/\.svg$/, '')); }
      else if (/\.svg$/.test(st.file)) { src = path.join(IMG, st.file); files.push(st.file); formats.add('svg'); }
      else if (/\.png$/.test(st.file)) {
        src = path.join(HERE, 'sketch', st.vector || st.file.replace(/\.png$/, '.svg'));
        files.push(st.file); formats.add('png');
        if (!fs.existsSync(src)) {
          // no vector for this PNG: the page draws the PNG itself and cannot recolour it
          const png = path.join(IMG, st.file);
          if (!fs.existsSync(png)) { problems.push(def.id + '/' + st.key + ': no PNG at ' + png); return null; }
          const [w, h] = st.size || def.size || [24, 24];
          return { key: st.key, label: st.label, svg: '', png: 'static/images/' + st.file, w, h, real: st.real, ground: st.ground, flip: !!st.flip, css: st.css || '' };
        }
      }
      if (!src || !fs.existsSync(src)) { problems.push(def.id + '/' + st.key + ': no art at ' + src); return null; }
      svg = cleanSvg(read(src));
      if (st.inline) svg = withFaces(svg);
      const [w, h] = st.size || def.size || svgSize(svg);
      return { key: st.key, label: st.label, svg, w, h, real: st.real, ground: st.ground, flip: !!st.flip, css: st.css || '', keep: st.keep || [], png: /\.png$/.test(st.file || '') ? 'static/images/' + st.file : '' };
    }).filter(Boolean);
    const lottie = (def.lottie || []).map((lt) => {
      const p = path.join(IMG, lt.file);
      if (!fs.existsSync(p)) { problems.push(def.id + ': no Lottie at ' + p); return null; }
      const data = JSON.parse(read(p));
      files.push(lt.file); formats.add('animated');
      return { key: lt.key, label: lt.label, state: lt.state, holdEnd: !!lt.holdEnd, w: lt.size ? lt.size[0] : data.w, h: lt.size ? lt.size[1] : data.h, data };
    }).filter(Boolean);
    if (!states.length && !lottie.length) { problems.push(def.id + ': nothing to draw'); return; }
    const size = def.size || (states[0] ? [states[0].w, states[0].h] : [lottie[0].w, lottie[0].h]);
    icons.push({
      id: def.id, name: def.name, cat: cat.id, states, lottie, size,
      grounds: def.grounds || ['band'], stage: def.stage || (def.grounds || ['band'])[0],
      where: def.where || [], note: def.note || '', flag: cat.sketchOnly ? 'sketch' : (def.flag || 'both'), sketchOnly: !!cat.sketchOnly || !!def.sketchOnly,
      wide: !!def.wide, realStates: def.realStates || 1, files: [...new Set(files)], formats: [...formats], source: def.source || '',
      siteSize: def.siteSize || null, sizeNote: def.sizeNote || '',
    });
    ids.push(def.id);
  });
  return { id: cat.id, title: cat.title, desc: cat.desc || '', fold: !!cat.fold, icons: ids };
});

return { icons, categories, overview: inv.overview || [], grounds: inv.grounds, wallpapers: inv.wallpapers, problems };
}

function write() {
  delete require.cache[require.resolve('./versions.js')];
  const versions = require('./versions.js');
  const a = assemble();
  const data = { built: new Date().toISOString().slice(0, 10), icons: a.icons, categories: a.categories, overview: a.overview,
    grounds: a.grounds, wallpapers: a.wallpapers, versions };
  const page = read(path.join(HERE, 'page.html'));
  const json = JSON.stringify(data).replace(/<\//g, '<\\/');
  fs.writeFileSync(path.join(ROOT, 'icon-lab.html'), page.replace('/*@@DATA@@*/', () => 'window.LAB = ' + json + ';'));
  console.log('icon-lab.html:', a.icons.length, 'icons in', a.categories.length, 'groups,', versions.length, 'versions,',
    Math.round(json.length / 1024) + ' KB of data');
  if (a.problems.length) { console.log('PROBLEMS:\n  ' + a.problems.join('\n  ')); process.exitCode = 1; }
  writeTable(a, versions);
  writeAll(a, versions);
}

// ../icon-lab-all.html: every icon the redesign draws, in its groups, old and new. z switches the page
// between the colours the site has today and the picked version (Holger, 23 Sep 2026). The folded groups
// (the old look, the files the site never shows, the drawings only in Sketch) stay off it: no version
// changes them. The new art is recoloured here, with the version's maps, as the lab's pages do in the
// browser: the narrowest reach wins (one state, then one icon, then every icon).
const ALL_PICK = 'schemeinks';
// The friends panel's buttons are boxes with round corners today. In the new colours they take the
// redesign's squircle corner, as `corner-shape: squircle` draws it: each corner a quarter of
// |x|^4 + |y|^4 = 1 (Holger, 23 Sep 2026). A squircle turns later than an arc, so it takes twice the round
// radius, as the tokens do (6px round, 12px squircle), and never more than half the side. The pick mark,
// the seat count box and the movement chips are squircles on the site already, so their art is drawn so.
// The canasta chip keeps its tab (Holger, 23 Sep 2026: "the same border radius and such").
const SQUIRCLES = new Set(['friendMessage', 'friendInvite', 'friendSearch', 'friendSearchClose', 'send']);
const squircleRadius = (r, w, h) => Math.min(2 * r, w / 2, h / 2);
function squirclePath(x, y, w, h, r, round) {
  const N = 12, pts = [];
  const corner = (cx, cy, from) => {
    for (let i = 0; i <= N; i++) {
      const t = (from + 90 * i / N) * Math.PI / 180, c = Math.cos(t), sn = Math.sin(t);
      pts.push([cx + r * Math.sign(c) * Math.sqrt(Math.abs(c)), cy + r * Math.sign(sn) * Math.sqrt(Math.abs(sn))]);
    }
  };
  if (round[0]) corner(x + r, y + r, 180); else pts.push([x, y]);
  if (round[1]) corner(x + w - r, y + r, 270); else pts.push([x + w, y]);
  if (round[2]) corner(x + w - r, y + h - r, 0); else pts.push([x + w, y + h]);
  if (round[3]) corner(x + r, y + h - r, 90); else pts.push([x, y + h]);
  return 'M' + pts.map((p) => +p[0].toFixed(3) + ' ' + +p[1].toFixed(3)).join('L') + 'Z';
}
// every rounded rect that is the icon's box (not a dot or a pill, at least half the icon's width), and every
// path that names its box in data-box ("x y w h r" and which corners are round: top left, top right, bottom
// right, bottom left)
function squircle(svg, size) {
  const num = (t, k) => { const m = new RegExp('\\s' + k + '="([^"]*)"').exec(t); return m ? parseFloat(m[1]) : null; };
  return svg.replace(/<rect\b([^>]*?)(\/?)>(<\/rect>)?/g, (m, attrs) => {
    const x = num(attrs, 'x') || 0, y = num(attrs, 'y') || 0, w = num(attrs, 'width'), h = num(attrs, 'height'), r = num(attrs, 'rx') || num(attrs, 'ry');
    if (!w || !h || !r || r >= Math.min(w, h) / 2 - 0.01 || w < size[0] / 2) return m;
    const rest = attrs.replace(/\s(?:x|y|width|height|rx|ry)="[^"]*"/g, '');
    return '<path d="' + squirclePath(x, y, w, h, squircleRadius(r, w, h), [1, 1, 1, 1]) + '"' + rest + '/>';
  }).replace(/<path\b([^>]*?)\sdata-box="([^"]+)"([^>]*?)\sd="[^"]*"/g, (m, a, box, b) => {
    const v = box.split(/\s+/).map(Number);
    return '<path' + a + ' data-box="' + box + '"' + b + ' d="' + squirclePath(v[0], v[1], v[2], v[3], squircleRadius(v[4], v[2], v[3]), v.slice(5, 9)) + '"';
  });
}
// the felt under a felt icon: the lab's first wallpaper, the table's green felt
const FELT = { css: "#1E5B1C url('static/pieces/wallpaper/fabrics/green-felt.jpg') 0 0/100px 100px repeat" };
const HEX_NAMED = { white: '#FFFFFF', black: '#000000' };
function normHex(v) {
  v = String(v).trim(); const l = v.toLowerCase(); if (HEX_NAMED[l]) return HEX_NAMED[l];
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(v); if (!m) return null;
  let h = m[1]; if (h.length === 3) h = h.replace(/./g, '$&$&'); return '#' + h.toUpperCase();
}
// a colour the version leaves alone keeps its text, so an icon no version touches comes out identical.
// fn gets the colour and the property that paints it (fill, stroke), since a map may name a colour on one
// property only: "stroke:#C96800" is the turn timer's arc, where the number is the same colour as a fill.
const propOf = (a) => a.split(/[\s=:]/)[0].toLowerCase();
function recolourSvg(svg, fn) {
  const swap = (v, a) => { const h = normHex(v); if (!h) return null; const t = fn(h, propOf(a)); return t === h ? null : t; };
  return svg.replace(/(\b(?:fill|stroke|stop-color|flood-color|lighting-color)\s*=\s*")([^"]*)(")/gi, (m, a, v, b) => { const t = swap(v, a); return t ? a + t + b : m; })
    .replace(/(\b(?:fill|stroke|stop-color|flood-color)\s*:\s*)([^;"'}]+)/gi, (m, a, v) => { const t = swap(v, a); return t ? a + t : m; });
}
function writeAll(a, versions) {
  const ver = versions.find((v) => v.id === ALL_PICK);
  if (!ver) { console.log('icon-lab-all.html: no version ' + ALL_PICK); process.exitCode = 1; return; }
  const n = versions.indexOf(ver) + 2;
  const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const uri = (svg) => 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
  const to = (id, key) => (hex, prop) => {
    const st = ver.state[id + '/' + key];
    if (st && prop && st[prop + ':' + hex]) return st[prop + ':' + hex];
    if (st && st[hex]) return st[hex];
    const ic = ver.icon[id]; if (ic && ic[hex]) return ic[hex];
    return (ver.global && ver.global[hex]) || hex;
  };
  let icons = 0, changed = 0;
  const groups = a.categories.filter((c) => !c.fold).map((cat) => {
    const cards = cat.icons.map((id) => {
      const ic = a.icons.find((i) => i.id === id);
      // an old-look-only state stays off; a mirrored or softened view of a real one stays on
      const states = ic.states.filter((st) => st.real !== false || st.flip || st.css);
      // every state at the size the site draws it (the pegs at their board's scale)
      const k = ic.siteSize ? ic.siteSize[0] / ic.size[0] : 1;
      let changes = false;
      // states on the same ground share one tile; a hover state hides until the page shows hovers
      const tiles = [];
      states.forEach((st) => {
        const g = st.ground || ic.stage;
        if (!tiles.length || tiles[tiles.length - 1].g !== g) tiles.push({ g, imgs: [] });
        const hover = /hover/i.test(st.key);
        const style = 'width:' + +(st.w * k).toFixed(1) + 'px;height:' + +(st.h * k).toFixed(1) + 'px;' + (st.flip ? 'transform:scaleX(-1);' : '') + (st.css || '');
        const tip = esc(st.label) + (hover ? ' (hover)' : '');
        const cls = hover ? ' hv' : '';
        // a version may redraw a state (ver.art): new art in its new colours, `pad` px bigger on every side
        // where it draws past the icon's box (an outline), laid out at the icon's own size
        const art = ver.art && ver.art[id + '/' + st.key];
        let imgs;
        if (!st.svg) imgs = '<img class="b' + cls + '" src="' + esc(st.png) + '" alt="" title="' + tip + '" style="' + style + '">';
        else {
          let nu = art ? art.svg : recolourSvg(st.svg, to(id, st.key));
          if (!art && SQUIRCLES.has(id)) nu = squircle(nu, ic.size);
          const pad = (art && art.pad) || 0;
          const nuStyle = pad ? 'width:' + +(st.w * k + 2 * pad).toFixed(1) + 'px;height:' + +(st.h * k + 2 * pad).toFixed(1) + 'px;margin:-' + pad + 'px;' + (st.css || '') : style;
          if (nu === st.svg) imgs = '<img class="b' + cls + '" src="' + uri(st.svg) + '" alt="" title="' + tip + '" style="' + style + '">';
          else {
            changes = true;
            imgs = '<img class="o' + cls + '" src="' + uri(st.svg) + '" alt="" title="' + tip + '" style="' + style + '">' +
              '<img class="n' + cls + '" src="' + uri(nu) + '" alt="" title="' + tip + (art ? ', new art' : '') + '" style="' + nuStyle + '">';
          }
        }
        tiles[tiles.length - 1].imgs.push({ html: imgs, hover });
      });
      const html = tiles.map((t) => {
        const gr = t.g === 'felt' ? FELT : a.grounds[t.g] || a.grounds.band;
        const onlyHover = t.imgs.every((x) => x.hover);
        return '<div class="ground' + (onlyHover ? ' hv' : '') + '" style="background:' + esc(gr.css || gr.color) + '">' + t.imgs.map((x) => x.html).join('') + '</div>';
      }).join('');
      icons++; if (changes) changed++;
      return '<div class="icon"><div class="tiles">' + html + '</div><div class="cap"><b>' + esc(ic.name) + '</b><code>' + esc(id) + '</code>' +
        (ic.sizeNote ? '<i>' + esc(ic.sizeNote) + '</i>' : '') + (changes ? '' : '<span class="tag">stays</span>') + '</div></div>';
    });
    return '<section><h2>' + esc(cat.title) + '</h2><div class="cards">' + cards.join('') + '</div></section>';
  });
  const folded = a.categories.filter((c) => c.fold);
  const footer = 'Not on this page, since no version changes them: ' + folded.map((c) => esc(c.title.replace(/^./, (x) => x.toLowerCase())) + ' (' + c.icons.length + ')').join(', ') +
    '. The animations are in the lab, <a href="icon-lab.html">icon-lab.html</a>, under Show the details.';
  const html = read(path.join(HERE, 'all-page.html'))
    .replace('/*@@PICK@@*/', () => esc(n + ', ' + ver.title))
    .replace('/*@@COUNT@@*/', () => changed + ' of these ' + icons + ' icons change.')
    .replace('<!--@@GROUPS@@-->', () => groups.join('\n'))
    .replace('/*@@FOOTER@@*/', () => footer);
  fs.writeFileSync(path.join(ROOT, 'icon-lab-all.html'), html);
  console.log('icon-lab-all.html:', icons, 'icons,', changed, 'change in', ver.title);
}

// The captured Hearts table (capture-table.js), with the icon art, the icon rules and the versions put
// in, so it repaints its own icons: icon-lab-table-frame.html. It always stands in a frame of 1440 by 900,
// driven by postMessage: in the lab page, and in the viewer icon-lab-table.html (table-view.html), which
// scales the frame to the window and keeps the version switcher.
function writeTable(a, versions) {
  const snap = path.join(HERE, 'table', 'hearts.html');
  if (!fs.existsSync(snap)) return;
  const rules = JSON.parse(read(path.join(HERE, 'table', 'hearts-rules.json')));
  const files = {}, svgs = {};
  inv.categories.forEach((cat) => cat.icons.forEach((def) => def.states.forEach((st) => {
    if (!st.file) return;
    const f = st.file.split('/').pop();
    if (files[f]) return;
    const ic = a.icons.find((i) => i.id === def.id), s2 = ic && ic.states.find((x) => x.key === st.key);
    if (!s2 || !s2.svg) return;
    files[f] = [def.id, st.key];
    svgs[def.id + '/' + st.key] = s2.svg;
  })));
  const data = { files, svgs, rules, versions: versions.map((v) => ({ id: v.id, title: v.title, global: v.global, icon: v.icon, state: v.state })) };
  const json = JSON.stringify(data).replace(/<\//g, '<\\/');
  const html = read(snap).replace('<head>', () => '<head>\n<!-- Generated by icon-lab-parts/build.js from table/hearts.html (captured by capture-table.js). -->')
    .replace(/<\/body>/i, () => '<script>window.ICONLAB_TABLE = ' + json + ';</script>\n<script>' + read(path.join(HERE, 'table-scene.js')) + '</script>\n</body>');
  fs.writeFileSync(path.join(ROOT, 'icon-lab-table-frame.html'), html);
  const list = JSON.stringify(versions.map((v) => ({ id: v.id, title: v.title }))).replace(/<\//g, '<\\/');
  fs.writeFileSync(path.join(ROOT, 'icon-lab-table.html'), read(path.join(HERE, 'table-view.html')).replace('/*VERSIONS*/', () => list));
  console.log('icon-lab-table-frame.html:', Object.keys(files).length, 'icon files,', rules.length, 'icon rules; icon-lab-table.html:', versions.length + 1, 'versions');
}

module.exports = { assemble, write, squirclePath, squircleRadius, SQUIRCLES };
if (require.main === module) write();
