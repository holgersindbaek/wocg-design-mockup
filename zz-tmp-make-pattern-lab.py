# -*- coding: utf-8 -*-
import io, os, re
D = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3"
src = io.open(D + "/game.html", encoding="utf-8").read()

def cut(text, start_marker, end_marker, replacement, once=True):
    i = text.index(start_marker)
    j = text.index(end_marker, i) + len(end_marker)
    return text[:i] + replacement + text[j:]

# ---- 1. head: title and the note ----
i = src.index("<title>"); j = src.index("</title>") + len("</title>")
src = src[:i] + "<title>Pattern lab &middot; the new wallpapers on the table, one key at a time</title>" + src[j:]

if True:
    i = src.index("<!--"); j = src.index("-->", i) + 3
    src = src[:i] + """<!--
  The pattern lab. The table is game.html (the settled seated table, laid out by the port of the
  game's own layout engine); the felt under it is one of the new patterns from ~/Downloads/Patterns.

    left / right   the pattern before, the pattern after
    up             choose this one (a tick shows bottom right)
    down           un-choose it
    [ and ]        the repeat, smaller and larger (tiles only); 0 puts it back
    f              all / tiles only / full images only / chosen only
    g and G        the next group, the group before
    Home / End     the first pattern, the last one. Anything added later is at the end.
    v              the table's spotlight and vignette off and on
    e              the export sheet: the chosen list, to copy
    h              this help

  Where you are, the filter and the repeat you set are kept in localStorage, so a reload
  opens on the same pattern; the chosen list is kept there too and comes out of the export sheet.

  The assets are pattern-assets/ (gitignored; zz-tmp-build-patterns.py rebuilds them from
  ~/Downloads/Patterns). A tile is a 1536x1536 master drawn at the repeat the HUD shows, so every
  rung of the ladder up to 768 is exact on a retina screen. A full image is a 2560x1600 centre crop,
  which is all a landscape table ever shows of an A3 sheet. 183 tiles, 94 full images.

  The HUD's "ships" figure is what the site would have to send at the repeat now set: twice the
  repeat in pixels, so a big repeat is a big file. Today's wallpapers are 10 to 20 KB.

  What the site needs for each kind (both are small changes, neither exists yet):
    a tile        ship it at twice the chosen repeat (a 255px repeat wants a 512x512 jpg) and write
                  that repeat as background-size. Theme.js swapWallpaper only writes a size for
                  green-felt and arkadium-felt today and gives every other wallpaper "inherit", so
                  a wallpaper's repeat is whatever its own pixel size happens to be; a 2x asset
                  needs C.WALLPAPERS to carry the repeat and Theme.js to write it.
    a full image  background-size: cover, no-repeat, centred, and one asset about 1920px wide.
                  That wants a flag on the item (cover: true) which swapWallpaper reads.
-->""" + src[j:]

# ---- 2. felt vars ----
src = src.replace(
  '    --felt: url("green-felt.jpg");\n    --felt-size: 100px 100px;',
  '    --felt: url("green-felt.jpg");\n    --felt-size: 100px 100px;\n    --felt-pos: 0 0;\n    --felt-repeat: repeat;\n    --felt-bg: #327333;   /* the felt colour under the image, as base.scss has it */', 1)

src = src.replace(
  '    background: var(--felt) 0 0 / var(--felt-size) repeat;',
  '    background: var(--felt-bg) var(--felt) var(--felt-pos) / var(--felt-size) var(--felt-repeat);', 1)

# ---- 3. swap the sidebar CSS for the lab's own ----
LAB_CSS = """  /* ===== the pattern lab's own chrome ===== */
  .pl-arrow {
    position: fixed; top: 50%; transform: translateY(-50%); z-index: 9980;
    width: 56px; height: 96px; display: flex; align-items: center; justify-content: center;
    background: rgba(0, 0, 0, .28); color: #fff; font-size: 34px; line-height: 1; cursor: pointer;
    border: 0; border-radius: 12px; opacity: .55; transition: opacity .15s ease, background-color .15s ease;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; text-shadow: none;
  }
  .pl-arrow:hover { opacity: 1; background: rgba(0, 0, 0, .44); }
  .pl-prev { left: 10px; }
  .pl-next { right: calc(var(--ad-w) + 10px); }

  .pl-hud {
    position: fixed; right: calc(var(--ad-w) + 12px); bottom: 12px; z-index: 9990; width: 300px;
    padding: 12px 14px; border-radius: 12px; pointer-events: auto; cursor: default;
    background: rgba(255, 255, 255, .94); backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
    box-shadow: 0 2px 10px rgba(0, 0, 0, .3); color: #222; text-shadow: none;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  }
  .pl-hud .pl-name { font-size: 15px; font-weight: 700; line-height: 1.25; padding-right: 40px; }
  .pl-hud .pl-meta { font-size: 12px; color: #666; margin-top: 3px; }
  .pl-hud .pl-count { font-size: 12px; color: #666; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e5e5; display: flex; justify-content: space-between; }
  .pl-hud .pl-chosen { font-weight: 700; color: #2B8A3E; }
  .pl-hud .pl-warn { display: none; margin-top: 6px; font-size: 12px; font-weight: 700; color: #C92A2A; }
  .pl-hud.is-seamy .pl-warn { display: block; }
  .pl-tick {
    position: absolute; right: 12px; top: 10px; width: 30px; height: 30px; border-radius: 50%;
    background: #2B8A3E; color: #fff; font-size: 19px; line-height: 30px; text-align: center; font-weight: 700;
    opacity: 0; transform: scale(.6); transition: opacity .16s ease, transform .16s ease;
  }
  .pl-hud.is-on .pl-tick { opacity: 1; transform: scale(1); }
  .pl-bar { height: 3px; margin-top: 10px; border-radius: 2px; background: #e5e5e5; overflow: hidden; }
  .pl-bar i { display: block; height: 100%; background: #1665AD; }

  .pl-help {
    position: fixed; left: 12px; bottom: 12px; z-index: 9990; max-width: 330px; padding: 10px 12px; border-radius: 10px;
    background: rgba(255, 255, 255, .92); color: #333; text-shadow: none; font-size: 12px; line-height: 1.6;
    font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; box-shadow: 0 1px 6px rgba(0, 0, 0, .25);
  }
  .pl-help.is-off { display: none; }
  .pl-help b { display: inline-block; min-width: 74px; font-family: ui-monospace, Menlo, monospace; font-size: 11px; color: #111; }

  .pl-export {
    position: fixed; inset: 6vh 6vw; z-index: 9999; display: none; flex-direction: column; gap: 10px;
    padding: 18px; border-radius: 14px; background: #fff; color: #222; text-shadow: none;
    box-shadow: 0 8px 40px rgba(0, 0, 0, .45); font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  }
  .pl-export.is-on { display: flex; }
  .pl-export h2 { margin: 0; font-size: 17px; }
  .pl-export p { margin: 0; font-size: 13px; color: #666; }
  .pl-export textarea { flex: 1; width: 100%; font-family: ui-monospace, Menlo, monospace; font-size: 12px; line-height: 1.5; padding: 10px; border: 1px solid #ddd; border-radius: 8px; resize: none; }
  .pl-export .pl-row { display: flex; gap: 8px; align-items: center; }
  .pl-export button { font: inherit; font-size: 13px; font-weight: 600; padding: 8px 14px; border: 0; border-radius: 8px; background: #1665AD; color: #fff; cursor: pointer; }
  .pl-export button.ghost { background: #eee; color: #333; }
  .pl-export .grow { margin-left: auto; }
  body.pl-noveil::before, body.pl-noveil::after { display: none; }
"""
src = cut(src,
  "  /* ===== the options sidebar, as in index.html: hidden until you hover the bottom of the ad rail ===== */",
  "  .swhud small { font-weight: 500; color: #777; }\n",
  LAB_CSS)

# ---- 4. swap the sidebar markup for the lab's ----
LAB_HTML = """<button type="button" class="pl-arrow pl-prev" id="pl-prev" aria-label="The pattern before">&#8249;</button>
<button type="button" class="pl-arrow pl-next" id="pl-next" aria-label="The pattern after">&#8250;</button>

<div class="pl-hud" id="pl-hud">
  <div class="pl-tick">&#10003;</div>
  <div class="pl-name" id="pl-name">&nbsp;</div>
  <div class="pl-meta" id="pl-meta">&nbsp;</div>
  <div class="pl-warn">The edges do not meet: this one shows a seam when it repeats.</div>
  <div class="pl-count"><span id="pl-pos">&nbsp;</span><span>Chosen: <span class="pl-chosen" id="pl-num">0</span></span></div>
  <div class="pl-bar"><i id="pl-bar"></i></div>
</div>

<div class="pl-help" id="pl-help">
  <div><b>&#8592; &#8594;</b> the pattern before and after</div>
  <div><b>&#8593; / &#8595;</b> choose it / un-choose it</div>
  <div><b>[ ]</b> the repeat, smaller and larger &nbsp;<b>0</b> back to default</div>
  <div><b>f</b> all / tiles / full images / chosen &nbsp;<b>g G</b> the next group</div>
  <div><b>Home End</b> the first, the last. New patterns are always at the end</div>
  <div><b>v</b> spotlight off &nbsp;<b>e</b> export &nbsp;<b>h</b> hide this</div>
</div>

<div class="pl-export" id="pl-export">
  <h2>The patterns you chose</h2>
  <p>Copy this and paste it back to me. It carries the id, the name, the repeat you set and the file it came from.</p>
  <textarea id="pl-out" spellcheck="false"></textarea>
  <div class="pl-row">
    <button type="button" id="pl-copy">Copy</button>
    <button type="button" class="ghost" id="pl-download">Download .json</button>
    <button type="button" class="ghost" id="pl-clear">Clear every choice</button>
    <button type="button" class="ghost grow" id="pl-close">Close</button>
  </div>
</div>
"""
src = cut(src, '<div class="switchzone"></div>', '</div>\n\n<script>', LAB_HTML + "\n<script src=\"pattern-assets/patterns.js\"></script>\n<script>")

# ---- 5. swap the design-chooser JS for the lab's ----
LAB_JS = r"""/* ===== the design, fixed at what was settled (game.html's choosers are gone here) ===== */
var curFbtn = "yellow4", curTeam = "t20b", curMsg = "band", curPrad = "plates", curEdge = "plates";
var curDesign = "current";

function applyBody() {
  var cls = ["design-current", "fbtn-" + curFbtn, "team-" + curTeam, "prad-" + curPrad, "edge-" + curEdge, "msg-" + curMsg];
  if (LAYOUT) {
    var g = LAYOUT.g;
    if (g.compact) cls.push("ps-compact");
    if (g.small) cls.push("ps-small");
    cls.push(g.portrait ? "ps-portrait" : "ps-landscape");
    if (g.side) cls.push("ps-side");
    if (g.adWidth === 160) cls.push("ad160");
  }
  if (!VEIL) cls.push("pl-noveil");
  document.body.className = cls.join(" ");
}

/* ===== the patterns ===== */
/* The sizes the repeat steps through. 100 is the green felt's and 255 is what nearly every
   wallpaper on the site draws at today, so the ladder is built around those two and then goes
   past them. It stops at 768 because the tile master is 1536, which is exactly 768 at 2x:
   every rung is honest on a retina screen, none of them is an upscale. */
var SIZES = [64, 80, 100, 128, 160, 192, 224, 255, 288, 320, 384, 448, 512, 640, 768];
var FILTERS = [
  { key: "all",    label: "All",          test: function () { return true; } },
  { key: "tile",   label: "Tiles",        test: function (p) { return p.kind === "tile"; } },
  { key: "sheet",  label: "Full images",  test: function (p) { return p.kind === "sheet"; } },
  { key: "chosen", label: "Chosen",       test: function (p) { return !!chosen[p.id]; } }
];

var ALL = window.PATTERNS || [];
var LS = "wocgPatternLab.";
function load(key, fallback) {
  try { var v = localStorage.getItem(LS + key); return v == null ? fallback : JSON.parse(v); }
  catch (e) { return fallback; }
}
function save(key, value) { try { localStorage.setItem(LS + key, JSON.stringify(value)); } catch (e) {} }

var chosen = load("chosen", {});          /* id -> { at, repeat } */
var sizes  = load("sizes", {});           /* id -> repeat in CSS px */
var VEIL   = load("veil", true);          /* the table's spotlight and vignette */
var helpOn = load("help", true);
var filterIx = Math.max(0, FILTERS.map(function (f) { return f.key; }).indexOf(load("filter", "all")));
var list = ALL.slice();
var ix = 0;
var startAt = load("at", null);      /* the pattern we were on, by id, not by place in a list */
var preloaded = {};

function repeatOf(p) { return p.kind === "sheet" ? 0 : (sizes[p.id] || p.repeat || 255); }

/* What this pattern would weigh on the site at the repeat now set: the asset has to be twice the
   repeat for a retina screen, and the build weighed each tile at 512, 768, 1024 and 1536. */
function shipKb(p) {
  if (p.kind === "sheet") return p.kb;
  if (!p.ship) return p.kb;
  var want = repeatOf(p) * 2, keys = [512, 768, 1024, 1536], i;
  for (i = 0; i < keys.length; i++) if (want <= keys[i]) break;
  if (i === 0) return p.ship["512"];
  if (i >= keys.length) return p.ship["1536"];
  var lo = keys[i - 1], hi = keys[i];
  return Math.round(p.ship[String(lo)] + (p.ship[String(hi)] - p.ship[String(lo)]) * (want - lo) / (hi - lo));
}
function weight(kb) { return kb >= 1024 ? (kb / 1024).toFixed(1) + " MB" : kb + " KB"; }

function applyPattern() {
  var p = list[ix];
  if (!p) return;
  var root = document.documentElement.style;
  root.setProperty("--felt", 'url("pattern-assets/' + p.file + '")');
  if (p.kind === "sheet") {
    root.setProperty("--felt-size", "cover");
    root.setProperty("--felt-repeat", "no-repeat");
    root.setProperty("--felt-pos", "50% 50%");
  } else {
    var s = repeatOf(p);
    root.setProperty("--felt-size", s + "px " + s + "px");
    root.setProperty("--felt-repeat", "repeat");
    root.setProperty("--felt-pos", "0 0");
  }
  drawHud();
  preload(ix + 1); preload(ix + 2); preload(ix - 1);
  save("at", p.id);
  save("filter", FILTERS[filterIx].key);
}

function preload(i) {
  var p = list[i];
  if (!p || preloaded[p.id]) return;
  preloaded[p.id] = true;
  var im = new Image(); im.src = "pattern-assets/" + p.file;
}

function drawHud() {
  var p = list[ix], hud = document.getElementById("pl-hud");
  if (!p) {
    document.getElementById("pl-name").textContent = "Nothing in this filter";
    document.getElementById("pl-meta").textContent = FILTERS[filterIx].label;
    document.getElementById("pl-pos").textContent = "0 / 0";
    return;
  }
  var kind = p.kind === "sheet" ? "Full image" : (p.cut ? "Tile, cut from a photo" : "Tile");
  var size = p.kind === "tile" ? (" · repeat " + repeatOf(p) + "px") : " · cover";
  document.getElementById("pl-name").textContent = p.name;
  document.getElementById("pl-meta").textContent = p.group + " · " + kind + size + " · ships " + weight(shipKb(p));
  document.getElementById("pl-pos").textContent = (ix + 1) + " / " + list.length + (filterIx ? " · " + FILTERS[filterIx].label : "");
  document.getElementById("pl-num").textContent = Object.keys(chosen).length;
  document.getElementById("pl-bar").style.width = (100 * (ix + 1) / Math.max(1, list.length)) + "%";
  hud.classList.toggle("is-on", !!chosen[p.id]);
  // wrapH and wrapV are the honest measure, in grey levels the wrap is off by. The older ratio is
  // only a fallback: it divides by the interior variation, so a banded plaid makes it explode on a
  // mismatch nobody can see.
  var seamy = p.wrapH != null ? Math.max(p.wrapH, p.wrapV) > 6 : (p.seamH > 2 || p.seamV > 2);
  hud.classList.toggle("is-seamy", p.kind === "tile" && seamy);
}

function go(step) {
  if (!list.length) return;
  ix = (ix + step + list.length) % list.length;
  applyPattern();
}

function choose(on) {
  var p = list[ix];
  if (!p) return;
  if (on) chosen[p.id] = { at: Date.now(), repeat: repeatOf(p) };
  else delete chosen[p.id];
  save("chosen", chosen);
  if (FILTERS[filterIx].key === "chosen" && !on) { setFilter(filterIx); return; }
  drawHud();
}

function stepSize(dir) {
  var p = list[ix];
  if (!p || p.kind !== "tile") return;
  var cur = repeatOf(p), i = 0;
  while (i < SIZES.length - 1 && SIZES[i] < cur) i++;
  if (dir === 0) delete sizes[p.id];
  else sizes[p.id] = SIZES[Math.min(SIZES.length - 1, Math.max(0, i + dir))];
  save("sizes", sizes);
  if (chosen[p.id]) { chosen[p.id].repeat = repeatOf(p); save("chosen", chosen); }
  applyPattern();
}

function setFilter(i, wantId) {
  var here = wantId || (list[ix] && list[ix].id);
  filterIx = (i + FILTERS.length) % FILTERS.length;
  list = ALL.filter(FILTERS[filterIx].test);
  if (!list.length) { list = ALL.slice(); filterIx = 0; }
  var at = -1;
  for (var k = 0; k < list.length; k++) if (list[k].id === here) { at = k; break; }
  ix = at < 0 ? 0 : at;
  applyPattern();
}

function jumpGroup(dir) {
  if (!list.length) return;
  var here = list[ix].group, i = ix;
  for (var n = 0; n < list.length; n++) {
    i = (i + dir + list.length) % list.length;
    if (list[i].group !== here) {
      if (dir < 0) {                                  /* walk back to that group's first one */
        var g = list[i].group;
        while (list[(i - 1 + list.length) % list.length].group === g) i = (i - 1 + list.length) % list.length;
      }
      ix = i; applyPattern(); return;
    }
  }
}

function exportText() {
  var out = ALL.filter(function (p) { return chosen[p.id]; }).map(function (p) {
    return { id: p.id, name: p.name, group: p.group, kind: p.kind,
             repeat: p.kind === "tile" ? (chosen[p.id].repeat || repeatOf(p)) : null,
             file: p.file, src: p.src };
  });
  return JSON.stringify({ chosen: out.length, patterns: out }, null, 2);
}

function showExport(on) {
  var box = document.getElementById("pl-export");
  if (on) document.getElementById("pl-out").value = exportText();
  box.classList.toggle("is-on", on);
}

/* ===== the keys ===== */
document.addEventListener("keydown", function (e) {
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  if (e.target && /^(INPUT|TEXTAREA)$/.test(e.target.tagName)) return;
  var k = e.key;
  if (k === "Escape") { showExport(false); return; }
  if (k === "Home") { e.preventDefault(); if (list.length) { ix = 0; applyPattern(); } return; }
  if (k === "End")  { e.preventDefault(); if (list.length) { ix = list.length - 1; applyPattern(); } return; }
  if (k === "ArrowLeft")  { e.preventDefault(); go(-1); return; }
  if (k === "ArrowRight") { e.preventDefault(); go(1); return; }
  if (k === "ArrowUp")    { e.preventDefault(); choose(true); return; }
  if (k === "ArrowDown")  { e.preventDefault(); choose(false); return; }
  if (k === "[") { e.preventDefault(); stepSize(-1); return; }
  if (k === "]") { e.preventDefault(); stepSize(1); return; }
  if (k === "0") { e.preventDefault(); stepSize(0); return; }
  if (k === "f" || k === "F") { e.preventDefault(); setFilter(filterIx + 1); return; }
  if (k === "g") { e.preventDefault(); jumpGroup(1); return; }
  if (k === "G") { e.preventDefault(); jumpGroup(-1); return; }
  if (k === "v" || k === "V") { e.preventDefault(); VEIL = !VEIL; save("veil", VEIL); applyBody(); return; }
  if (k === "h" || k === "H") { e.preventDefault(); helpOn = !helpOn; save("help", helpOn); document.getElementById("pl-help").classList.toggle("is-off", !helpOn); return; }
  if (k === "e" || k === "E") { e.preventDefault(); showExport(!document.getElementById("pl-export").classList.contains("is-on")); return; }
});

document.getElementById("pl-prev").addEventListener("click", function () { go(-1); });
document.getElementById("pl-next").addEventListener("click", function () { go(1); });
document.getElementById("pl-hud").addEventListener("click", function () { choose(!chosen[list[ix] && list[ix].id]); });
document.getElementById("pl-close").addEventListener("click", function () { showExport(false); });
document.getElementById("pl-copy").addEventListener("click", function () {
  var t = document.getElementById("pl-out"); t.select();
  try { document.execCommand("copy"); } catch (err) {}
  if (navigator.clipboard) navigator.clipboard.writeText(t.value).catch(function () {});
  this.textContent = "Copied"; var b = this; setTimeout(function () { b.textContent = "Copy"; }, 1200);
});
document.getElementById("pl-download").addEventListener("click", function () {
  var a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([exportText()], { type: "application/json" }));
  a.download = "chosen-patterns.json"; a.click();
});
document.getElementById("pl-clear").addEventListener("click", function () {
  if (!window.confirm("Clear every choice?")) return;
  chosen = {}; save("chosen", chosen); showExport(true); drawHud();
});
document.getElementById("pl-help").classList.toggle("is-off", !helpOn);

"""
src = cut(src, "/* ===== design options ===== */", "})();\n\nrender();", LAB_JS + "render();")

# the tail hook, and the first paint of the pattern
src = src.replace(
  'window.__gameLab = { STATE: STATE,',
  'setFilter(filterIx, startAt);\nwindow.__patternLab = { ALL: ALL, get list() { return list; }, get chosen() { return chosen; }, exportText: exportText };\nwindow.__gameLab = { STATE: STATE,', 1)

io.open(D + "/pattern-lab.html", "w", encoding="utf-8").write(src)
print("written:", len(src), "bytes")
for bad in ["switchbar", "swtoggle", "buildSel", "design-toggle", "sel-msg", "lastSel"]:
    if bad in src: print("  !! still mentions", bad, src.count(bad))
