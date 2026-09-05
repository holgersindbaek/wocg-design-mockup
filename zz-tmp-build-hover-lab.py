# -*- coding: utf-8 -*-
"""open-tables-hover-lab.html, narrowed to one treatment: the clock hands over to the invitation.
   The hand over runs the table change's own recipe (index.html dealtInto, "One clears, four dealt"),
   with the four-seat stagger collapsed to the single element. Static: nothing updates but the hover."""
import re, io, os
D = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3"
src = io.open(os.path.join(D, "index.html"), encoding="utf-8").read()

body_class = re.search(r'<body class="([^"]*)"', src).group(1)
styles = re.findall(r'<style[^>]*>.*?</style>', src, re.S)
# the tile block is scoped to the section id; the lab needs its own scope, so the id becomes a class,
# tripled so the rules keep beating the .lobbyscope rules they were written to beat
styles = [x.replace("#openTablesTop", ".otscope.otscope.otscope") for x in styles]
k = src.find('<svg width="0" height="0" style="position:absolute"')
svgdefs = src[k:src.find("</svg>", k) + 6]

LAB_CSS = u"""
<style>
  /* ===== lab chrome ===== */
  body.hoverlab { padding: 28px 24px 120px !important; background: #f9f6f2 !important; }
  .hoverlab h1 { font-size: 22px; margin: 0 0 6px; font-family: "BuloRounded", Verdana, sans-serif; }
  .hoverlab p.note { font-size: 13px; color: #8a857c; margin: 0 0 10px; max-width: 1000px; line-height: 1.55; }
  .hoverlab p.note b { color: #141414; }
  .hoverlab .datum { display: inline-flex; align-items: baseline; gap: 7px; font-size: 12.5px;
    background: #fff; border-radius: 8px; corner-shape: squircle; box-shadow: inset 0 0 0 1px #e4e0d9;
    padding: 7px 11px; margin: 0 8px 22px 0; color: #4e4d4c; }
  .hoverlab .datum b { font-size: 15px; color: #141414; font-family: ui-monospace, Menlo, monospace; }
  .hoverlab code { font-family: ui-monospace, Menlo, monospace; font-size: 12px; background: #fff;
    padding: 0 4px; border-radius: 4px; box-shadow: inset 0 0 0 1px #d2cfca; }

  .vcard { background: #fff; border-radius: 14px; corner-shape: squircle;
    box-shadow: 0 0 0 1px #e4e0d9, 0 1px 2px rgba(60,45,25,.05), 0 3px 8px rgba(60,45,25,.09);
    padding: 15px 17px 20px; margin: 0 0 18px; max-width: 1160px; }
  .vcard h3 { font-size: 15px; margin: 0 0 3px; font-family: "BuloRounded", Verdana, sans-serif; }
  .vcard .vnote { font-size: 12.5px; color: #8a857c; margin: 0 0 12px; line-height: 1.5; max-width: 940px; }
  .vcard .vnote b { color: #141414; }
  .hoverlab .lobbyscope { padding: 0; margin: 0; max-width: none; }
  /* the homepage lays these three across a 1112px column, so a tile is 344px. The lab matches, or a
     caption that fits on the page would be judged in a box it never has to live in. */
  .vstage .ltGrid { grid-template-columns: repeat(3, minmax(0,1fr)); max-width: 1112px; }
  .stateRow { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); max-width: 1112px;
    gap: 40px; margin: 0 0 7px; }
  .stateRow span { font-size: 11px; font-weight: bold; letter-spacing: .04em; text-transform: uppercase;
    color: #b3ada2; }
  .abar { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 14px 0 0; }
  .abtn { font-family: inherit; font-size: 13px; font-weight: bold; color: #333; background: #fff;
    border: 1px solid #ddd; border-radius: 8px; corner-shape: squircle; padding: 6px 12px; cursor: pointer; }
  .abtn:hover { background: #f4eee5; }
  .alab { font-size: 11.5px; color: #8a857c; margin-right: 2px; }

  /* ===== the invitation ===== */
  /* The invitation goes in the clock's own parent, not in a layer of its own. .playersContainer is
     inset inside .header, so a layer pinned to the header's bottom put the text 12px low and the two
     would have swapped across a visible step. Same parent, same box, same slot. It carries the clock's
     whole recipe minus the max-width, because the invitation needs more room than a time does. */
  .otscope .ltCard .hvClock { position: absolute; z-index: 3; left: 0; bottom: 0;
    display: inline-flex; align-items: center; height: 20px; line-height: 20px;
    font-size: 14px; font-weight: bold; color: #fff; white-space: nowrap; opacity: 0;
    pointer-events: none;
    text-shadow: -1px -1px 0 rgba(0,0,0,.32), 1px -1px 0 rgba(0,0,0,.32),
                 -1px 1px 0 rgba(0,0,0,.32), 1px 1px 0 rgba(0,0,0,.32); }
  /* the hand over is driven by the Web Animations API with dealtInto's own keyframes, so nothing here
     may transition: a CSS transition would fight the animation the moment one is cancelled on reversal */
  .otscope .ltCard .ltTime, .otscope .ltCard .hvClock { transition: none !important; }
  .otscope .ltCard { cursor: pointer; }
</style>
"""

BODY = u"""
<h1>Open tables &middot; the clock becomes the invitation</h1>
<p class="note">
Hover any tile. The time in the bottom left clears and the invitation is dealt in behind it, on the
<b>same recipe the table change uses</b>: one beat out on the leaving curve, then after 150ms the new
text rises in on the arriving curve. Moving off runs it the other way.
<b>Nothing here updates or swaps</b> &mdash; the tables are frozen, so the only thing that moves is the hover.
</p>
<p class="note">
Three states, because each needs different words: a table <b>waiting</b> for players, a table
<b>in play</b> where a bot can be taken over, and the <b>placeholder</b> you sit at to host your own.
</p>
<div class="datum"><b>51.5%</b> of joins today came from clicking a seat</div>
<div class="datum"><b>48.5%</b> came from the &ldquo;Join table&rdquo; button &mdash; which this tile does not have</div>
<p class="note" style="margin-bottom:26px">
Measured on 9,777 <code>Click Table Listings Item</code> events in the last 24 hours, split on
<code>seatType</code>, which production only fills in when a seat was clicked. Roughly half of everyone
reaches for a button today, which is what this treatment has to answer for.
</p>

<div class="vcard">
  <h3>The clock becomes the invitation</h3>
  <p class="vnote">
    The time rolls out and the invitation rolls in, in the clock's own ghost text. New words, no new
    furniture, and nothing is covered: the seats, the art and the marks all stay exactly where they are.
    The hand over is <code>dealtInto</code>'s pair of curves with the four-seat stagger collapsed to one
    element &mdash; <b>190ms out</b> on <code>cubic-bezier(.32,0,.67,0)</code>, then <b>260ms in</b> after
    a <b>150ms</b> wait on <code>cubic-bezier(.22,1,.36,1)</code>, rising 10px from <code>scale(.94)</code>.
  </p>
  <p class="vnote">
    Every tile you can join says <b>Join table</b>, the bot seat included: taking a bot's hand is still
    joining that table, and one phrase everywhere is one phrase to learn. Only the host tile says
    something else, because it is the only one that is not a join. Its wording is still open, so it has
    its own switcher below.
  </p>
  <div class="stateRow"><span>Waiting &middot; two seats free</span><span>In play &middot; a bot to take over</span><span>Placeholder &middot; sit to host</span></div>
  <div class="lobbyscope otscope"><div class="vstage"><div class="ltGrid"></div></div></div>
  <div class="abar">
    <span class="alab">The host tile says</span>
    <button type="button" class="abtn" data-words="0">Host a table</button>
    <button type="button" class="abtn" data-words="1">Sit to host</button>
    <button type="button" class="abtn" data-words="2">Click to host</button>
    <button type="button" class="abtn" data-words="3">New table</button>
    <span class="alab" style="margin-left:14px">Speed</span>
    <button type="button" class="abtn" data-rate="1">1&times;</button>
    <button type="button" class="abtn" data-rate="0.35">Slow</button>
  </div>
</div>
"""

JS = u"""
<script>
/* the avatar edge filter and shadow the homepage wears by default, rebuilt here because index.html
   builds it at runtime and this lab borrows only its stylesheet */
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
  var YOU = "WomanSuperGirl2.svg";
  var rate = 1;

  /* ── the table change's own recipe, lifted from index.html dealtInto ──
     There the leaving container clears in one beat and the four arriving seats are dealt in at
     150 + i * 38ms. One element means i = 0, so the stagger disappears and the 150ms wait remains:
     the felt is empty for that moment, exactly as it is when a table turns over. */
  var OUT_KF = [{ opacity: 1, transform: "scale(1)" },
                { opacity: 0, transform: "scale(.97)" }];
  var IN_KF  = [{ opacity: 0, transform: "translateY(10px) scale(.94)" },
                { opacity: 1, transform: "translateY(0) scale(1)" }];
  function outOpts() { return { duration: 190 / rate, easing: "cubic-bezier(.32,0,.67,0)", fill: "both" }; }
  function inOpts()  { return { duration: 260 / rate, delay: 150 / rate,
                                easing: "cubic-bezier(.22,1,.36,1)", fill: "both" }; }

  /* Cancelling is only ever done here because the hover reversed mid-flight; a held fill from the
     previous direction would otherwise win. dealtInto deliberately never cancels at rest, and neither
     does this: the last animation of each hand over stays held, so both texts keep their layers. */
  function handOver(leaving, arriving) {
    leaving.getAnimations().forEach(function (a) { a.cancel(); });
    arriving.getAnimations().forEach(function (a) { a.cancel(); });
    leaving.animate(OUT_KF, outOpts());
    arriving.animate(IN_KF, inOpts());
  }

  /* Every table you can join says the same thing, whether the free seat is empty or a bot's: taking a
     bot's hand is still joining that table, and one phrase on every tile is one phrase to learn. Only
     the host placeholder says something else, because it is the only one that is not a join. */
  var JOIN = "Join table";
  var HOST_WORDS = ["Host a table", "Sit to host", "Click to host", "New table"];
  var wordSet = 0;

  /* three fixed tables, one per state. Fixed, not random: nothing in this lab changes on its own. */
  var TABLES = [
    { game: ["hearts", "Hearts", "Ends at 100"], mins: 0, key: "wait",
      seats: [["Marge", "WomanGirl2.svg", 97], null, ["carl52", "ManMan3.svg", 91], null] },
    { game: ["spades", "Spades", "Plays to 500"], mins: 12, key: "bot",
      seats: [["Duckling", "AnimalCat.svg", 96], ["Vera", "WomanScientist.svg", 99], "bot",
              ["Hank", "AnimalBeaver.svg", 80]] },
    { game: ["canasta", "Canasta", "Your rules"], mins: -1, key: "host",
      seats: [null, null, null, null] }
  ];

  function seatHtml(i, who) {
    if (who === "bot") {
      return '<div class="player playernumber' + i + ' isBot seatAvailable">' +
        '<img width="32" height="32" src="AlienMartian.svg" alt="">' +
        '<div class="playerNameContainer"><p class="playerName">Bot Ada</p>' +
        '<span class="playerBadge isBot"></span></div></div>';
    }
    if (!who) {
      return '<div class="player playernumber' + i + ' isEmpty">' +
        '<img width="32" height="32" src="avatarEmpty.png" alt="">' +
        '<div class="playerNameContainer"><p class="playerName">Empty seat</p></div></div>';
    }
    var b = who[2] >= 70 ? '<span class="completionBadge' + (who[2] === 100 ? " is100" : "") + '">' +
      (who[2] === 100 ? "" : who[2]) + '</span>' : "";
    return '<div class="player playernumber' + i + '"><img width="32" height="32" src="' + who[1] + '" alt="">' +
      '<div class="playerNameContainer"><p class="playerName">' + who[0] + '</p>' + b + '</div></div>';
  }

  function buildCard(t) {
    var g = t.game, started = t.mins > 0, placeholder = t.mins < 0;
    var label = placeholder ? "Sit to host" : (started ? t.mins + " min" : "0 min");
    var card = document.createElement("div");
    card.className = "ltCard" + (placeholder ? " isNew" : "");
    card.setAttribute("data-key", t.key);
    card.innerHTML = '<div class="tableListing ' + g[0] + ' players4"><div class="header">' +
      '<div class="playersContainer">' +
      '<div class="spacer30"></div>' + seatHtml(1, t.seats[1]) + '<div class="spacer30"></div>' +
      seatHtml(0, t.seats[0]) + '<div class="spacer20"></div>' + seatHtml(2, t.seats[2]) +
      '<div class="spacer30"></div>' + seatHtml(3, t.seats[3]) + '<div class="spacer30"></div>' +
      '<img class="ltArt art-' + g[0] + '" src="' + g[0] + '_logo@2x.png" alt="' + g[1] + '">' +
      '<div class="ltTime"><svg class="ltRing" viewBox="0 0 16 16" aria-hidden="true">' +
      '<circle cx="8" cy="8" r="7" fill="none" stroke="#fff" stroke-width="2"/>' +
      (started ? '<path d="M8 8V1A7 7 0 0 1 15 8z" fill="#fff"/>' : '') +
      '</svg><span>' + label + '</span></div>' +
      '</div></div></div>';
    return card;
  }

  /* the join preview, armed exactly as index.html arms it */
  function armSeat(seat) {
    if (seat.classList.contains("joinable")) return;
    seat.classList.add("joinable");
    var you = document.createElement("img");
    you.className = "seatYou"; you.src = YOU; you.alt = "";
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

  function armInvitation(card) {
    var clock = card.querySelector(".ltTime");
    var txt = document.createElement("span");
    txt.className = "hvClock";
    txt.textContent = invitationFor(card);
    /* straight into the clock's parent, so the two share one coordinate space */
    clock.parentNode.insertBefore(txt, clock.nextSibling);
    card.addEventListener("mouseenter", function () { handOver(clock, txt); });
    card.addEventListener("mouseleave", function () { handOver(txt, clock); });
  }

  function invitationFor(card) {
    return card.getAttribute("data-key") === "host" ? HOST_WORDS[wordSet] : JOIN;
  }

  var grid = document.querySelector(".ltGrid");
  TABLES.forEach(function (t) {
    var card = buildCard(t);
    grid.appendChild(card);
    /* the placeholder's seats stay plain, as they do on the page */
    if (!card.classList.contains("isNew")) {
      card.querySelectorAll(".player.isEmpty, .player.isBot").forEach(armSeat);
    }
    armInvitation(card);
  });

  document.querySelectorAll(".abtn").forEach(function (b) {
    b.addEventListener("click", function () {
      if (b.hasAttribute("data-rate")) { rate = +b.getAttribute("data-rate"); return; }
      wordSet = +b.getAttribute("data-words");
      document.querySelectorAll(".ltCard").forEach(function (c) {
        c.querySelector(".hvClock").textContent = invitationFor(c);
      });
    });
  });
})();
</script>
"""

out = u"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Open tables &middot; the clock becomes the invitation</title>
""" + u"\n".join(styles) + LAB_CSS + u"""
</head>
<body class="__BODYCLASS__ hoverlab">
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
io.open(os.path.join(D, "open-tables-hover-lab.html"), "w", encoding="utf-8").write(out)
print("wrote open-tables-hover-lab.html  %.0f KB" % (len(out) / 1024.0))
