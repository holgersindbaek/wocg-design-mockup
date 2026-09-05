# -*- coding: utf-8 -*-
"""Assemble open-tables-anim-lab.html out of the real index.html styles, so the tiles in the
   lab are the same tiles: the same avatar SVG filters, the same nameplate shadows, the same felt."""
import re, io, os
D = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3"
src = io.open(os.path.join(D, "index.html"), encoding="utf-8").read()

body_class = re.search(r'<body class="([^"]*)"', src).group(1)
styles = re.findall(r'<style[^>]*>.*?</style>', src, re.S)
# the tile block is scoped to the section id; the lab needs many scopes, so the id becomes a class.
# It is tripled so the rules keep beating the .lobbyscope rules they were written to beat.
styles = [x.replace("#openTablesTop", ".otscope.otscope.otscope") for x in styles]
k = src.find('<svg width="0" height="0" style="position:absolute"')
svgdefs = src[k:src.find("</svg>", k) + 6]
fonts = re.findall(r'<link[^>]+rel="preload"[^>]+>', src)[:0]

LAB_CSS = u"""
<style>
  /* ===== lab chrome ===== */
  body.animlab { padding: 28px 24px 120px !important; background: #f9f6f2 !important; }
  .animlab h1 { font-size: 22px; margin: 0 0 4px; font-family: "BuloRounded", Verdana, sans-serif; }
  .animlab p.note { font-size: 13px; color: #8a857c; margin: 0 0 22px; max-width: 980px; line-height: 1.5; }
  .animlab p.note b, .animlab .desc b { color: #141414; }
  .animlab code { font-family: ui-monospace, Menlo, monospace; font-size: 12px; background: #fff; padding: 0 4px;
    border-radius: 4px; box-shadow: inset 0 0 0 1px #d2cfca; }
  .asec { margin: 0 0 46px; max-width: 1160px; }
  .asec > h2 { font-size: 17px; margin: 26px 0 4px; padding-top: 16px; border-top: 1px solid #e9e4db;
    font-family: "BuloRounded", Verdana, sans-serif; }
  .asec .desc { font-size: 13px; color: #8a857c; margin: 0 0 14px; max-width: 980px; line-height: 1.5; }
  .abar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 14px; }
  .abtn { font-family: inherit; font-size: 13px; font-weight: bold; color: #333; background: #fff;
    border: 1px solid #ddd; border-radius: 8px; corner-shape: squircle; padding: 6px 12px; cursor: pointer; }
  .abtn:hover { background: #f4eee5; }
  .abtn.on { box-shadow: inset 0 0 0 2px #1665AD; border-color: #1665AD; color: #1665AD; }
  .abtn.go { background: #C0EB75; border-color: #a7d155; color: #3c6207; }
  .alab { font-size: 11.5px; color: #8a857c; margin-right: 2px; }
  .meter { font-size: 11.5px; color: #4e4d4c; font-family: ui-monospace, Menlo, monospace;
    background: #fff; border-radius: 6px; box-shadow: inset 0 0 0 1px #e4e0d9; padding: 4px 9px; min-width: 250px; }
  .meter b { color: #141414; }
  .meter .bad { color: #B52626; }
  .meter .good { color: #4F800B; }

  /* the variation cards */
  .vcard { background: #fff; border-radius: 14px; corner-shape: squircle;
    box-shadow: 0 0 0 1px #e4e0d9, 0 1px 2px rgba(60,45,25,.05), 0 3px 8px rgba(60,45,25,.09);
    padding: 14px 16px 16px; margin: 0 0 16px; }
  .vcard h3 { font-size: 14.5px; margin: 0 0 3px; font-family: "BuloRounded", Verdana, sans-serif; }
  .vcard h3 .tag { font-size: 10.5px; font-weight: bold; padding: 1px 7px; border-radius: 10px;
    background: #f4eee5; color: #4e4d4c; margin-left: 7px; vertical-align: 1px; }
  .vcard h3 .tag.now { background: #FFDBD9; color: #B52626; }
  .vcard h3 .tag.pick { background: #C0EB75; color: #4F800B; }
  .vcard .vnote { font-size: 12.5px; color: #8a857c; margin: 0 0 10px; line-height: 1.45; }
  .vcard .vnote b { color: #141414; }
  .vstage { max-width: 560px; }
  .vstage .ltGrid { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .vwide .vstage { max-width: 100%; }
  .vwide .vstage .ltGrid { grid-template-columns: repeat(3, minmax(0,1fr)); }
  /* the slot holds its own height so the leaving tile can lie over the arriving one without moving anything */
  .animlab .lobbyscope { padding: 0; margin: 0; max-width: none; }
  /* the slot holds the tile's own 4:3 whatever is inside it. Without this, a variation that lifts its
     leaving tile out of flow before the new one arrives collapses the row and everything below jumps. */
  .ltSlot { position: relative; aspect-ratio: 4 / 3; }
  .ltGrid.clickable .ltCard { cursor: pointer; }
  .ltSlot > .ltCard.leaving { position: absolute; inset: 0; z-index: 2; }

  /* the compare rig */
  .cmp2 { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; align-items: start; }
  .cmp2 .vcard { margin: 0; }

  /* The .ltSwap block that drives a seat change lives in index.html now, and this lab extracts
     index.html's stylesheet, so it is not repeated here. What IS repeated is .ltRoll, the clipper
     the OLD swap used before it was replaced: it is kept so the side-by-side comparison is fair. */
  .lobbyscope .player .ltRoll { position: absolute; inset: 0; overflow: hidden;
    border-radius: inherit; corner-shape: inherit; }
  .lobbyscope .player .ltRoll .playerName { position: absolute; inset: 0; padding: 0; }

  /* the seat rig: a real hoverable seat beside the ones a button drives */
  .seatrig { display: flex; gap: 10px; flex-wrap: wrap; }
  .seatpen { width: 200px; background-color: #327333; background-image: url("green-felt.jpg");
    background-size: 150px 150px; border-radius: 14px; corner-shape: squircle; padding: 26px 0 34px;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.22); position: relative; }
  .seatpen .cap { position: absolute; left: 0; right: 0; top: 6px; text-align: center; font-size: 11px;
    font-weight: bold; color: rgba(255,255,255,.85); text-shadow: 0 1px 2px rgba(0,0,0,.5); }
  .seatpen .player { position: relative; margin: 0 auto; }
</style>
"""

BODY = u"""
<h1>Open tables &middot; the vanish and the arrival</h1>
<p class="note">
  The tiles here are the real tiles: this page borrows <b>index.html</b>'s own stylesheet, its avatar edge
  filter and its nameplate shadows, so anything that stutters here stutters there. Everything that made the
  tile itself vanish has been taken out: what is left holds the <b>felt perfectly still</b> and changes only
  what sits on it. (Settled earlier and no longer shown: the avatars keep their edge filter and their
  shadows all the way through a change, because dropping them costs two full re-rasters and produced the
  worst frames, as well as making the shadows switch on late.)
</p>

<div class="asec">
  <h2>One &middot; a seat changing hands</h2>
  <p class="desc">
    The seat on the left is a plain open seat: <b>hover it</b>. The middle seat runs the old copy, written by
    hand as JavaScript keyframes. The right seat runs the new one, which adds a class that the hover's own
    CSS block answers, so it cannot drift from the hover again. Run them and watch all three together.
  </p>
  <div class="abar">
    <button class="abtn go" id="swapRun">Run both</button>
    <button class="abtn" id="swapRunNew">Run the new one only</button>
    <span class="alab" id="swapNote"></span>
  </div>
  <div class="lobbyscope otscope">
    <div class="seatrig">
      <div class="seatpen"><span class="cap">hover me &middot; the real thing</span><div id="penHover"></div></div>
      <div class="seatpen"><span class="cap">old &middot; hand written keyframes</span><div id="penOld"></div></div>
      <div class="seatpen"><span class="cap">new &middot; the hover's own rules</span><div id="penNew"></div></div>
    </div>
  </div>
</div>

<div class="asec" id="secContents">
  <h2>Two &middot; the felt stays still</h2>
  <p class="desc">
    A different idea altogether: the table never moves. The green 4:3 felt stays exactly where it is and
    only <b>the things on it</b> change, so it reads as players getting up and new players sitting down at
    the same table rather than one table being swapped for another. Nothing here blurs, moves or fades the
    tile itself, so there is no layout shift and nothing to reserve. Click a single tile to run it alone.
  </p>
  <div class="abar">
    <button class="abtn go" id="runContents">Run every one</button>
    <span style="width:10px"></span>
    <span class="alab">Speed</span>
    <button class="abtn" data-rate="0.25">quarter</button>
    <button class="abtn" data-rate="0.5">half</button>
    <button class="abtn on" data-rate="1">full</button>
  </div>
  <div id="contentVariants"></div>
</div>

<div class="asec">
  <h2>Three &middot; two at a time</h2>
  <p class="desc">Pick two and run them together on wider tiles, which is how they will really be seen.</p>
  <div class="abar">
    <span class="alab">Left</span><select id="cmpA"></select>
    <span class="alab">Right</span><select id="cmpB"></select>
    <button class="abtn go" id="cmpRun">Run both</button>
  </div>
  <div class="cmp2" id="cmpWrap"></div>
</div>
"""

JS = u"""
<script>
/* the avatar edge filter and shadow the homepage wears by default (avedge-lum-soft, avsh-ghostramp),
   rebuilt here because index.html builds it at runtime and this lab borrows only its stylesheet */
(function () {
  var defs = document.querySelector("svg defs");
  var f = document.createElementNS("http://www.w3.org/2000/svg", "filter");
  f.setAttribute("id", "avatarEdge-lum-soft");
  f.setAttribute("x", "-2%"); f.setAttribute("y", "-2%");
  f.setAttribute("width", "104%"); f.setAttribute("height", "104%");
  f.setAttribute("color-interpolation-filters", "sRGB");
  f.innerHTML = '<feMorphology in="SourceAlpha" operator="erode" radius="1" result="eroded"/>' +
    '<feComposite in="SourceAlpha" in2="eroded" operator="out" result="ring"/>' +
    '<feFlood flood-color="#737373" flood-opacity="0.55"/>' +
    '<feComposite in2="ring" operator="in" result="ringInk"/>' +
    '<feBlend in="ringInk" in2="SourceGraphic" mode="luminosity"/>';
  defs.appendChild(f);
  var st = document.createElement("style");
  st.textContent = "body.avedge-lum-soft .lobbyscope .player img { filter: url(#avatarEdge-lum-soft) var(--avshadow); }";
  document.head.appendChild(st);
})();

(function () {
  var reduced = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var RATE = 1;

  /* the pool a signed-in player draws from is mostly people, as the real avatar picker is, with the
     animals and aliens mixed through it the way a real table looks */
  var PEOPLE = [
    ["Marge", "WomanGirl2.svg", 97], ["carl52", "ManMan3.svg", 91], ["Vera", "WomanScientist.svg", 99],
    ["Duckling", "AnimalCat.svg", 96], ["BobK", "ManCowboy.svg", 100], ["wendy_h", "WomanBusinesswoman.svg", 93],
    ["north4th", "ManGeek2.svg", 88], ["PragueJoe", "AnimalCow.svg", 98], ["mollyb", "WomanCowgirl.svg", 100],
    ["GinTonic", "ManChef.svg", 95], ["Carol", "WomanSuperGirl2.svg", 90], ["Hank", "AnimalBeaver.svg", 80],
    ["cardShark52", "AlienBlue.svg", 99], ["moonshot", "ManMan3.svg", 92], ["Rosie", "WomanGirl2.svg", 94],
    ["Tilly", "AnimalFox.svg", 86], ["dealer_dan", "ManChef.svg", 97], ["Pip", "AnimalButterfly.svg", 91]
  ];
  var GAMES = [
    ["hearts", "Hearts", "Ends at 100"], ["spades", "Spades", "Plays to 500"], ["euchre", "Euchre", "Plays to 10"],
    ["pinochle", "Pinochle", "Plays to 150"], ["ginrummy", "Gin Rummy", "Plays to 100"],
    ["canasta", "Canasta", "Plays to 5,000"], ["rummy", "Rummy", "Plays to 500"]
  ];
  function pick(a) { return a[Math.floor(Math.random() * a.length)]; }

  function seatHtml(i, person, bot) {
    if (!person && !bot) {
      return '<div class="player playernumber' + i + ' isEmpty"><img width="32" height="32" src="avatarEmpty.png" alt="">' +
        '<div class="playerNameContainer"><p class="playerName">Empty</p></div></div>';
    }
    if (bot) {
      return '<div class="player playernumber' + i + ' isBot seatAvailable"><img width="32" height="32" src="AlienMartian.svg" alt="">' +
        '<div class="playerNameContainer"><p class="playerName">Bot Ada</p><span class="playerBadge isBot"></span></div></div>';
    }
    var b = person[2] >= 70 ? '<span class="completionBadge' + (person[2] === 100 ? " is100" : "") + '">' +
      (person[2] === 100 ? "" : person[2]) + "</span>" : "";
    return '<div class="player playernumber' + i + '"><img width="32" height="32" src="' + person[1] + '" alt="">' +
      '<div class="playerNameContainer"><p class="playerName">' + person[0] + "</p>" + b + "</div></div>";
  }
  function buildCard(game) {
    game = game || pick(GAMES);
    var roll = Math.random(), mins = 0, started = false, bot = -1;
    if (roll < 0.3) { started = true; mins = 3 + Math.floor(Math.random() * 40); bot = 2; }
    else if (roll < 0.45) { started = true; mins = 5 + Math.floor(Math.random() * 50); }
    var howMany = started ? 3 : 1 + Math.floor(Math.random() * 2);
    var chosen = [], pool = PEOPLE.slice();
    while (chosen.length < howMany && pool.length) chosen.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
    var fill = {};
    [1, 0, 2, 3].forEach(function (idx) {
      if (bot === idx) { fill[idx] = "bot"; return; }
      if (chosen.length) fill[idx] = chosen.shift();
    });
    function cell(i) { return seatHtml(i, fill[i] === "bot" ? null : fill[i], fill[i] === "bot"); }
    var t = started ? (mins < 60 ? mins + " min" : Math.floor(mins / 60) + "h " + (mins % 60) + "m") : "0 min";
    var card = document.createElement("div");
    card.className = "ltCard";
    card.innerHTML = '<div class="tableListing ' + game[0] + ' players4"><div class="header"><div class="playersContainer">' +
      '<div class="spacer30"></div>' + cell(1) + '<div class="spacer30"></div>' +
      cell(0) + '<div class="spacer20"></div>' + cell(2) +
      '<div class="spacer30"></div>' + cell(3) + '<div class="spacer30"></div>' +
      '<img class="ltArt art-' + game[0] + '" src="' + game[0] + '_logo.png" alt="' + game[1] + '">' +
      '<div class="ltTime"><svg class="ltRing" viewBox="0 0 16 16" aria-hidden="true">' +
      '<circle cx="8" cy="8" r="7" fill="none" stroke="#fff" stroke-width="2"/>' +
      (started ? '<path d="M8 8V1A7 7 0 0 1 15 8z" fill="#fff"/>' : "") + "</svg><span>" + t + "</span></div>" +
      "</div></div></div>";
    return card;
  }
  /* the join preview, exactly as index.html arms it */
  function armSeat(seat) {
    if (seat.classList.contains("joinable")) return;
    seat.classList.add("joinable");
    var you = document.createElement("img");
    you.className = "seatYou"; you.src = "WomanSuperGirl2.svg"; you.alt = "";
    you.width = 32; you.height = 32;
    var plate = seat.querySelector(".playerNameContainer");
    seat.insertBefore(you, plate);
    var roll = document.createElement("div");
    roll.className = "plateRoll";
    roll.appendChild(seat.querySelector(".playerName"));
    var join = document.createElement("p");
    join.className = "playerName pnJoin"; join.textContent = "Join";
    roll.appendChild(join);
    plate.insertBefore(roll, plate.firstChild);
  }
  function armCard(card) { card.querySelectorAll(".player.isEmpty, .player.isBot").forEach(armSeat); }

  /* ══════════════ the seat swap ══════════════ */

  /* OLD: the animation written out again by hand in JavaScript. This is what is in index.html today. */
  function swapSeatOld(seat, src, name, done) {
    var img = seat.querySelector("img:not(.seatYou):not(.ltGhost)");
    if (!img) { if (done) done(); return; }
    seat.querySelectorAll(".ltGhost").forEach(function (g) { g.remove(); });
    var ghost = document.createElement("img");
    ghost.className = "ltGhost"; ghost.src = src; ghost.alt = ""; ghost.width = 32; ghost.height = 32;
    /* no z-index: the nameplate is position:absolute with z-index auto, so a stand-in that claims a
       z-index paints OVER the plate, which the hover never does. Without one, DOM order decides and
       the plate, which comes later, stays on top exactly as it does on hover. */
    ghost.style.cssText = "position:absolute;left:50%;top:0;pointer-events:none";
    img.parentNode.insertBefore(ghost, img.nextSibling);
    img.animate([{ opacity: 1, transform: "scale(1)" }, { opacity: 0, transform: "scale(.88)" }],
      { duration: 140 / RATE, easing: "cubic-bezier(0.32,0,0.67,0)", fill: "forwards" });
    var rise = ghost.animate([{ transform: "translateX(-50%) scale(.86)" }, { transform: "translateX(-50%) scale(1)" }],
      { duration: 320 / RATE, delay: 200 / RATE, easing: "cubic-bezier(0.22,1,0.36,1)", fill: "both" });
    ghost.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 120 / RATE, delay: 200 / RATE, easing: "linear", fill: "both" });
    var plate = seat.querySelector(".playerNameContainer");
    var cur = plate.querySelector(".playerName:not(.pnJoin)");
    var clip = document.createElement("div");
    /* .plateRoll only gets its overflow:hidden under .joinable or .ltSwap, and this seat has
       neither, so the old name slid straight out of the plate. .ltRoll carries its own clipping,
       which is the class the old index.html code actually used. */
    clip.className = "ltRoll";
    var next = document.createElement("p");
    next.className = "playerName"; next.textContent = name;
    next.style.cssText = "position:absolute;inset:0;padding:0";
    cur.parentNode.insertBefore(clip, cur);
    clip.appendChild(cur); clip.appendChild(next);
    cur.animate([{ transform: "translateY(0)" }, { transform: "translateY(100%)" }],
      { duration: 220 / RATE, delay: 120 / RATE, easing: "cubic-bezier(.22,1,.36,1)", fill: "both" });
    next.animate([{ transform: "translateY(-100%)" }, { transform: "translateY(0)" }],
      { duration: 220 / RATE, delay: 120 / RATE, easing: "cubic-bezier(.22,1,.36,1)", fill: "both" });
    rise.onfinish = function () {
      img.getAnimations().forEach(function (a) { a.cancel(); });
      img.src = src; ghost.remove();
      cur.getAnimations().forEach(function (a) { a.cancel(); });
      cur.textContent = name;
      clip.parentNode.insertBefore(cur, clip); clip.remove();
      if (done) done();
    };
  }

  /* NEW: no keyframes at all. The seat is given the classes the hover's own CSS answers, so the
     motion IS the hover: the sitting face fades and shrinks to .88 over 140ms, and the arriving one
     is laid over it and rises from .86 over 320ms after the hover's 200ms wait, while the plate rolls. */
  function swapSeatNew(seat, src, name, done) {
    var plate = seat.querySelector(".playerNameContainer");
    var face = seat.querySelector("img:not(.seatYou)");
    if (!face || reduced) {
      if (face) face.src = src;
      var p = plate.querySelector(".playerName:not(.pnJoin)"); if (p) p.textContent = name;
      if (done) done(); return;
    }
    /* back to rest first, hovered or not: a hovered seat has already played this very animation, so
       starting from where it left off is what made a nameplate click look broken. Muted for the one
       frame it takes, so the reset itself is never seen. */
    var stale = seat.querySelector("img.seatYou");
    seat.classList.add("ltReset");
    if (stale) stale.remove();
    seat.classList.remove("joinable", "ltSwap", "ltGo");
    /* the arriving face goes where the hover puts your avatar, on a fresh element every time so no
       half-finished hover state can ride along */
    var inc = document.createElement("img");
    inc.className = "seatYou"; inc.alt = ""; inc.width = 32; inc.height = 32;
    inc.src = src;
    seat.insertBefore(inc, plate);
    /* the arriving name goes where the hover rolls "Join" */
    var cur = plate.querySelector(".playerName:not(.pnJoin)");
    var roll = plate.querySelector(".plateRoll");
    if (!roll) {
      roll = document.createElement("div");
      roll.className = "plateRoll";
      plate.insertBefore(roll, plate.firstChild);
      roll.appendChild(cur);
    }
    var nxt = roll.querySelector(".pnJoin");
    if (!nxt) { nxt = document.createElement("p"); nxt.className = "playerName pnJoin"; roll.appendChild(nxt); }
    nxt.textContent = name;

    /* the resting state is painted while still muted, then the muting comes off with nothing changed,
       and only then does .ltGo make the change. Unmuted, adding .ltSwap started a 220ms transition
       sending the incoming name from 0 to translateY(-100%), so .ltGo only reversed a journey that had
       barely begun and the new name simply sat in the plate while the old one slid through it. */
    seat.classList.add("ltSwap");
    void seat.offsetWidth;
    seat.classList.remove("ltReset");
    void seat.offsetWidth;
    seat.classList.add("ltGo");

    /* the last leg is the arriving face's rise, so the hand over waits for that animation by name */
    inc.addEventListener("animationend", function onEnd(e) {
      if (e.animationName !== "seatYouIn") return;
      inc.removeEventListener("animationend", onEnd);
      face.src = src;
      var ready = face.decode ? face.decode()["catch"](function () {}) : Promise.resolve();
      ready.then(function () {
        cur.textContent = name;
        /* .lobbyscope .player img carries transition: transform 80ms ease-in-out. Dropping .ltGo
           releases the real face from scale(.88), and that base transition then springs it back to
           scale(1) over 80ms just as the stand-in vanishes at scale(1): the bounce. Mute it for the
           one frame the hand over takes. */
        face.style.transition = "none";
        seat.classList.remove("ltSwap", "ltGo");
        /* the unwind happens before the flush, so the one forced layout measures the DOM that will
           actually be painted rather than a half-dismantled plate that never appears */
        if (roll.parentNode) { roll.parentNode.insertBefore(cur, roll); roll.remove(); }
        inc.remove();
        void face.offsetWidth;
        face.style.transition = "";
        if (done) done();
      });
    });
  }

  /* ══════════════ the frame meter ══════════════ */
  function measure(ms, out) {
    var worst = 0, longs = 0, n = 0, last = performance.now(), stop = last + ms;
    (function step(t) {
      var d = t - last; last = t; n++;
      if (n > 2) { if (d > worst) worst = d; if (d > 20) longs++; }
      if (t < stop) requestAnimationFrame(step);
      else if (out) {
        var cls = worst > 33 ? "bad" : (worst > 20 ? "" : "good");
        out.innerHTML = 'worst frame <b class="' + cls + '">' + worst.toFixed(1) + 'ms</b> &middot; ' +
          longs + ' long of ' + n + ' &middot; ' + Math.round(ms) + 'ms run';
      }
    })(last);
  }

  /* ══════════════ the tile variations ══════════════ */
  /* ══════════════ the felt stays still: recipes ══════════════
     Each of these animates only the contents of the tile. Where stagger is set, every seat, the game
     art and the time move on their own beat, that many milliseconds apart. */
  var CONTENT_VARIANTS = [
    { id: "c3", name: "Clean handover", totalMs: 340,
      note: "No overlap at all. The old set goes out completely, then the new one comes up in its place, so the two never share the felt and nothing is ever seen through anything else. The shortest of the set.",
      out: { d: 150, dl: 0, e: "cubic-bezier(.32,0,.67,0)", kf: [{ opacity: 1, transform: "scale(1)" }, { opacity: 0, transform: "scale(.96)" }] },
      inn: { d: 190, dl: 150, e: "cubic-bezier(.22,1,.36,1)", kf: [{ opacity: 0, transform: "scale(.96)" }, { opacity: 1, transform: "scale(1)" }] } },

    { id: "c6", name: "One clears, four dealt", tag: "best scored", totalMs: 600,
      inMode: "seats", inStep: 38,
      note: "Asymmetric on purpose. The old table leaves in a single quiet beat, then the new game's art comes up and the new players are dealt into their seats one at a time. All the movement is spent on the arrival, which is the half that is actually news.",
      out: { d: 190, dl: 0, e: "cubic-bezier(.32,0,.67,0)", kf: [{ opacity: 1, transform: "scale(1)" }, { opacity: 0, transform: "scale(.97)" }] },
      inn: { d: 260, dl: 150, e: "cubic-bezier(.22,1,.36,1)", kf: [{ opacity: 0, transform: "translateY(10px) scale(.94)" }, { opacity: 1, transform: "translateY(0) scale(1)" }] } },

    { id: "c7", name: "Round the table", tag: "see the note", totalMs: 555,
      outMode: "seats", inMode: "seats", outStep: 35, inStep: 35,
      note: "Every seat on its own beat, thirty-five milliseconds apart. It is the most literal reading of people getting up one by one. <b>The caution:</b> a single seat changing hands already has its own animation, and that fires far more often than a whole table turning over. Four staggered seats say that smaller sentence four times, so the rarer, bigger event can read as four copies of the smaller one.",
      out: { d: 180, dl: 0, e: "cubic-bezier(.32,0,.67,0)", kf: [{ opacity: 1, transform: "translateY(0) scale(1)" }, { opacity: 0, transform: "translateY(6px) scale(.92)" }] },
      inn: { d: 260, dl: 120, e: "cubic-bezier(.22,1,.36,1)", kf: [{ opacity: 0, transform: "translateY(8px) scale(.92)" }, { opacity: 1, transform: "translateY(0) scale(1)" }] } },

    { id: "c8", name: "Into the felt", totalMs: 450, promote: true,
      controls: true, blur: 7, drift: 0, dur: 1,
      note: "The dispersal, applied to the contents alone: they swell and blur away while the felt stays perfectly sharp behind them, and the new set gathers up from .90 with no blur of its own. Two things were done to the lag. The leaving box is <b>promoted to its own layer</b> before it starts, which took it from about 41 frames a second back to 60. Then the blur was given <b>its own even ramp</b> instead of riding the fade's ease-in curve, which had it sitting near zero for half the leg and then rocketing. Dial the radius below: heavier reads as smeary on the nameplate text long before it costs a frame.",
      out: { d: 240, dl: 0, e: "cubic-bezier(.32,0,.67,0)",
        blurTo: function (v) { return v.blur; }, blurEase: "linear",
        kf: [{ opacity: 1, transform: "scale(1)" }, { opacity: 0, transform: "scale(1.08)" }] },
      inn: { d: 320, dl: 130, e: "cubic-bezier(.22,1,.36,1)", kf: [{ opacity: 0, transform: "scale(.90)" }, { opacity: 1, transform: "scale(1)" }] } }
  ];

  /* the things that sit ON the felt, gathered into the beats a recipe asks for */
  function groupsOf(box, mode) {
    var els = [].slice.call(box.querySelectorAll(".player, .ltArt, .ltTime, .ltMarks"));
    if (!els.length || !mode || mode === "none") return [[box]];
    if (mode === "seats") return els.map(function (e) { return [e]; });
    var keyed = els.map(function (e) {
      var r = e.getBoundingClientRect();
      return { e: e, k: mode === "bands" ? Math.round(r.top / 30) : Math.round(r.left / 24) };
    });
    keyed.sort(function (a, b) { return a.k - b.k; });
    var out = [], last = null;
    keyed.forEach(function (o) {
      if (last === null || o.k !== last) { out.push([o.e]); last = o.k; }
      else out[out.length - 1].push(o.e);
    });
    return out;
  }
  function runBeats(groups, spec, step, v) {
    var last = null;
    groups.forEach(function (g, i) {
      g.forEach(function (el) {
        /* A blur on the same curve as the fade sits near zero for half the leg and then rockets, and
           that acceleration reads as a hitch even at a steady sixty frames. Given its own animation it
           can climb evenly while the opacity and the scale keep the curve they want. */
        if (spec.blurTo !== undefined) {
          el.animate([{ filter: "blur(0px)" }, { filter: "blur(" + (typeof spec.blurTo === "function" ? spec.blurTo(v) : spec.blurTo) + "px)" }],
            { duration: spec.d * (v && v.dur || 1) / RATE, delay: spec.dl * (v && v.dur || 1) / RATE,
              easing: spec.blurEase || "linear", fill: "both" });
        }
        last = el.animate(spec.kfFor ? spec.kfFor(el, i, v) : spec.kf,
          { duration: spec.d * (v && v.dur || 1) / RATE, delay: (spec.dl + i * step) * (v && v.dur || 1) / RATE,
        easing: spec.e, fill: "both" });
      });
    });
    return last;
  }
  /* ══════════════ the felt stays still ══════════════
     Only what sits on the felt changes. .playersContainer is already position:absolute inside the
     .header, so the arriving one is simply appended and lands exactly over the leaving one; the two
     are then animated past each other and the leaving one is dropped. The tile itself is never
     touched, so there is nothing to blur, nothing to reserve and nothing that can shift. */
  function swapContents(slot, v) {
    var card = slot.querySelector(".ltCard");
    if (!card || card.getAttribute("data-busy")) return;
    card.setAttribute("data-busy", "1");
    var listing = card.querySelector(".tableListing");
    var header = card.querySelector(".header");
    var oldBox = header.querySelector(".playersContainer");
    var game = pick(GAMES);
    var fresh = buildCard(game);
    var newBox = fresh.querySelector(".playersContainer");
    header.appendChild(newBox);
    armCard(newBox);
    /* Neither set is touchable while the change runs. The arriving one is appended last, so it paints
       on top and hit-tests first from the very first frame, and an element at opacity 0 still takes
       the pointer: without this, a mouse resting on the tile hovers an invisible seat and fires the
       join preview on a table that is not on screen yet. */
    oldBox.style.pointerEvents = "none";
    newBox.style.pointerEvents = "none";
    /* A recipe that blurs MUST say so, and the box must be promoted before it starts. Without the hint
       the container is not on its own layer, so every frame of the blur re-rasters the whole subtree,
       four SVG-filtered avatars and their shadows included, into a fresh padded texture. Measured on
       presented frames: 26.4ms per frame without it, 16.6ms with it, at the very same 10px radius,
       which is the same figure as no blur at all. The radius barely matters once it is promoted. */
    if (v.promote) { oldBox.style.willChange = "filter, transform, opacity"; newBox.style.willChange = "transform, opacity"; }

    var outStep = v.outStep || 0, inStep = v.inStep || 0;
    var outGroups = groupsOf(oldBox, v.outMode);
    var inGroups = groupsOf(newBox, v.inMode);
    runBeats(outGroups, v.out, outStep, v);
    var last = runBeats(inGroups, v.inn, inStep, v);

    var finish = function () {
      oldBox.remove();
      /* the game class lives on the shared .tableListing, and .tableListing.isTeamGame recolours the
         playernumber1 and playernumber3 plates. Setting it while the old contents are still on the
         felt would recolour the LEAVING plates mid-exit, so it waits until they are gone. */
      listing.className = "tableListing " + game[0] + " players4";
      newBox.getAnimations({ subtree: true }).forEach(function (a) { a.cancel(); });
      newBox.style.pointerEvents = "";
      newBox.style.willChange = "";   /* the hint is for the change only; left on it just costs memory */
      card.removeAttribute("data-busy");
    };
    if (last) last.onfinish = finish; else setTimeout(finish, 40);
  }
  function totalContents(v) { return Math.round(v.totalMs * (v.dur || 1)); }

  function fillGrid(grid, n) {
    grid.innerHTML = "";
    for (var i = 0; i < n; i++) {
      var slot = document.createElement("div");
      slot.className = "ltSlot";
      var c = buildCard(GAMES[i % GAMES.length]);
      slot.appendChild(c); armCard(c);
      grid.appendChild(slot);
    }
  }
  /* every tile in the lab is its own trigger: click one and only that one changes, which is the
     only way to watch a single tile closely. Clicking a seat's nameplate changes that seat instead. */
  function changeSeat(card, seat) {
    if (!seat || !card) return;
    if (seat.classList.contains("isEmpty") || seat.classList.contains("isBot")) {
      var taken = [].slice.call(card.querySelectorAll(".player:not(.isEmpty):not(.isBot) .playerName:not(.pnJoin)"))
        .map(function (n) { return n.textContent.trim(); });
      var free = PEOPLE.filter(function (p) { return taken.indexOf(p[0]) === -1; });
      if (free.length) sitOn(seat, pick(free));
    } else {
      standFrom(seat);
    }
  }
  function armClicks(grid, run) {
    grid.addEventListener("click", function (e) {
      var slot = e.target.closest(".ltSlot");
      if (!slot) return;
      var card = slot.querySelector(".ltCard");
      var plate = e.target.closest(".playerNameContainer");
      if (plate) { changeSeat(card, plate.closest(".player")); return; }
      /* the game art always changes the seat at the top of the felt: the easy way to watch one seat
         change over and over without a pointer sitting on it running the hover first. Found by where
         it actually sits rather than by its number. */
      if (e.target.closest(".ltArt")) {
        var seats = [].slice.call(card.querySelectorAll(".playersContainer .player"));
        seats.sort(function (a, b) { return a.getBoundingClientRect().top - b.getBoundingClientRect().top; });
        changeSeat(card, seats[0]);
        return;
      }
      run(slot);
    });
    grid.classList.add("clickable");
  }
  /* the seat change, using the page's own swap so the lab and the homepage cannot drift */
  function sitOn(seat, person) {
    var plate = seat.querySelector(".playerNameContainer");
    var bb = plate.querySelector(".playerBadge.isBot");
    if (bb) bb.remove();
    seat.classList.remove("isEmpty", "isBot", "seatAvailable");
    swapSeatNew(seat, person[1], person[0], function () {
      if (person[2] >= 70) {
        var b = document.createElement("span");
        b.className = "completionBadge" + (person[2] === 100 ? " is100" : "");
        b.textContent = person[2] === 100 ? "" : person[2];
        plate.appendChild(b);
      }
    });
  }
  function standFrom(seat) {
    var b = seat.querySelector(".completionBadge");
    if (b) b.remove();
    swapSeatNew(seat, "avatarEmpty.png", "Empty", function () {
      seat.classList.add("isEmpty");
      armSeat(seat);
    });
  }

  /* ── section two: the seat rig ── */
  function penSeat(host, person) {
    host.innerHTML = seatHtml(0, person, false);
    var seat = host.querySelector(".player");
    seat.style.cssText = "height:74px;flex-basis:auto;max-width:none;width:120px";
    return seat;
  }
  var hoverSeat = penSeat(document.getElementById("penHover"), PEOPLE[0]);
  hoverSeat.classList.add("isEmpty");
  hoverSeat.querySelector("img").src = "avatarEmpty.png";
  hoverSeat.querySelector(".playerName").textContent = "Empty";
  armSeat(hoverSeat);
  var oldSeat = penSeat(document.getElementById("penOld"), PEOPLE[0]);
  var newSeat = penSeat(document.getElementById("penNew"), PEOPLE[0]);
  var swapN = 0;
  function runSwaps(bothOfThem) {
    var p = PEOPLE[(++swapN) % PEOPLE.length];
    if (bothOfThem) swapSeatOld(oldSeat, p[1], p[0]);
    swapSeatNew(newSeat, p[1], p[0]);
    document.getElementById("swapNote").textContent = "→ " + p[0];
  }
  document.getElementById("swapRun").onclick = function () { runSwaps(true); };
  document.getElementById("swapRunNew").onclick = function () { runSwaps(false); };

  /* ── section four: the felt stays still ── */
  var cwrap = document.getElementById("contentVariants");
  CONTENT_VARIANTS.forEach(function (v) {
    var card = document.createElement("div");
    card.className = "vcard";
    card.innerHTML = "<h3>" + v.name + (v.tag ? ' <span class="tag ' + v.tag + '">' + v.tag + "</span>" : "") +
      ' <span class="tag">' + totalContents(v) + 'ms</span></h3>' +
      '<p class="vnote">' + v.note + "</p>" +
      '<div class="abar"><button class="abtn go">Run</button><span class="meter">no run yet</span></div>' +
      '<div class="lobbyscope otscope"><div class="vstage"><div class="ltGrid"></div></div></div>';
    cwrap.appendChild(card);
    var grid = card.querySelector(".ltGrid"), meter = card.querySelector(".meter");
    if (v.controls) {
      var bar = document.createElement("div");
      bar.className = "abar";
      function row(label, key, vals, suffix) {
        var h = '<span class="alab">' + label + '</span>';
        vals.forEach(function (n) {
          h += '<button class="abtn ctl' + (v[key] === n ? " on" : "") + '" data-k="' + key + '" data-v="' + n + '">' +
            n + (suffix || "") + "</button>";
        });
        return h + '<span style="width:14px"></span>';
      }
      bar.innerHTML = row("Blur", "blur", [0, 3, 5, 7, 10, 14], "px") +
                      '<span class="alab">Length</span>' +
                      '<button class="abtn ctl" data-k="dur" data-v="0.7">short</button>' +
                      '<button class="abtn ctl on" data-k="dur" data-v="1">as set</button>' +
                      '<button class="abtn ctl" data-k="dur" data-v="1.4">long</button>';
      card.insertBefore(bar, card.querySelector(".abar"));
      bar.addEventListener("click", function (e) {
        var b = e.target.closest("button.ctl");
        if (!b) return;
        var k = b.getAttribute("data-k");
        bar.querySelectorAll('button.ctl[data-k="' + k + '"]').forEach(function (x) { x.classList.remove("on"); });
        b.classList.add("on");
        v[k] = parseFloat(b.getAttribute("data-v"));
        card.querySelector("h3 .tag:last-child").textContent = totalContents(v) + "ms";
      });
    }
    fillGrid(grid, 2);
    function runIt() {
      grid.querySelectorAll(".ltSlot").forEach(function (s) { swapContents(s, v); });
      measure(totalContents(v) / RATE + 160, meter);
    }
    /* bind by class, not by position: the dial's buttons come before Run in the card */
    card.querySelector("button.go").onclick = runIt;
    armClicks(grid, function (slot) {
      swapContents(slot, v);
      measure(totalContents(v) / RATE + 160, meter);
    });
    v._grid = grid; v._meter = meter;
  });
  document.querySelectorAll("[data-rate]").forEach(function (b) {
    b.onclick = function () {
      document.querySelectorAll("[data-rate]").forEach(function (x) { x.classList.remove("on"); });
      b.classList.add("on"); RATE = parseFloat(b.getAttribute("data-rate"));
    };
  });
  document.getElementById("runContents").onclick = function () {
    CONTENT_VARIANTS.forEach(function (v) {
      v._grid.querySelectorAll(".ltSlot").forEach(function (s) { swapContents(s, v); });
      measure(totalContents(v) / RATE + 160, v._meter);
    });
  };

  /* ── section five: two at a time ── */
  var selA = document.getElementById("cmpA"), selB = document.getElementById("cmpB");
  CONTENT_VARIANTS.forEach(function (v) {
    [selA, selB].forEach(function (s) {
      var o = document.createElement("option"); o.value = v.id; o.textContent = v.name; s.appendChild(o);
    });
  });
  /* default to the current favourite against the softest one, whatever ids exist */
  function haveId(id) { return CONTENT_VARIANTS.some(function (v) { return v.id === id; }); }
  selA.value = haveId("c6") ? "c6" : CONTENT_VARIANTS[0].id;
  selB.value = haveId("c9") ? "c9" : CONTENT_VARIANTS[CONTENT_VARIANTS.length - 1].id;
  var cmpWrap = document.getElementById("cmpWrap");
  function cmpBuild() {
    cmpWrap.innerHTML = "";
    [selA.value, selB.value].forEach(function (id) {
      var v = CONTENT_VARIANTS.filter(function (x) { return x.id === id; })[0];
      var c = document.createElement("div");
      c.className = "vcard";
      c.innerHTML = '<h3>' + v.name + ' <span class="tag">' + totalContents(v) + 'ms</span></h3>' +
        '<div class="abar"><span class="meter">no run yet</span></div>' +
        '<div class="lobbyscope otscope"><div class="vstage"><div class="ltGrid"></div></div></div>';
      cmpWrap.appendChild(c);
      var g = c.querySelector(".ltGrid");
      fillGrid(g, 2);
      v._cgrid = g; v._cmeter = c.querySelector(".meter");
      armClicks(g, function (slot) {
        swapContents(slot, v);
        measure(totalContents(v) / RATE + 160, v._cmeter);
      });
    });
  }
  selA.onchange = selB.onchange = cmpBuild;
  cmpBuild();
  document.getElementById("cmpRun").onclick = function () {
    [selA.value, selB.value].forEach(function (id) {
      var v = CONTENT_VARIANTS.filter(function (x) { return x.id === id; })[0];
      v._cgrid.querySelectorAll(".ltSlot").forEach(function (s) { swapContents(s, v); });
      measure(totalContents(v) / RATE + 160, v._cmeter);
    });
  };
})();
</script>
"""

out = u"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Open tables &middot; the vanish and the arrival</title>
""" + u"\n".join(styles) + LAB_CSS + u"""
</head>
<body class="__BODYCLASS__ animlab">
__SVGDEFS__
__BODY__
__JS__
</body>
</html>
"""
out = (out.replace("__BODYCLASS__", body_class + " avedge-lum-soft avsh-ghostramp")
          .replace("__SVGDEFS__", svgdefs)
          .replace("__BODY__", BODY)
          .replace("__JS__", JS))
io.open(os.path.join(D, "open-tables-anim-lab.html"), "w", encoding="utf-8").write(out)
print("wrote open-tables-anim-lab.html  %.0f KB" % (len(out) / 1024.0))
