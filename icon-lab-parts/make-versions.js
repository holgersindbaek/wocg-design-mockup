// Writes versions-made.js: the colour versions the overview compares, then rebuilds the page.
//
//   node icon-lab-parts/make-versions.js
//
// Every version keeps each icon its own colour (Holger, 23 Sep 2026: the icons should not all be one
// colour). A version is a recipe applied to each icon's parts. ROLES says what each colour does in each
// icon: the fill, the ring round it, the glyph on it, their deeper hover tones, the solid set a state
// with a white glyph takes, and the notice's red dot. A colour ROLES does not name stays as built (the
// badges' black outline, the play icon's cards).
const C = require('./colour.js');
const fs = require('fs');
const path = require('path');
const { assemble, write } = require('./build.js');

const W = '#FFFFFF', K = '#000000';
const R = (slot, role) => [slot, role];

// ---- what each colour does, per icon. `states` overrides `all` for one state.
const SOLID_BLUE = { '#228BE6': R('m', 'sfill'), '#1971C2': R('m', 'sring'), '#FFFFFF': R('m', 'sglyph') };
const SOLID_LIME = { '#66A80F': R('m', 'sfill'), '#5C940D': R('m', 'sring'), '#FFFFFF': R('m', 'sglyph') };
const INK = { all: { '#212529': R('ink', 'ink') } };
const GOLD = { fam: { m: 'gold' }, all: { '#FDC41B': R('m', 'fill'), '#E67700': R('m', 'ring') } };
const GREY_BTN = { fam: { g: 'grey' }, all: { '#DEE2E6': R('g', 'fill'), '#ADB5BD': R('g', 'ring'), '#868E96': R('g', 'glyph'), '#495057': R('g', 'glyphHover') } };
const DOT = { '#F03E3E': R('dot', 'fill'), '#C92A2A': R('dot', 'ring') };
const ROLES = {
  menuActivity: { fam: { y: 'yellow' }, all: Object.assign({ '#FFD43B': R('y', 'fill'), '#F59F00': R('y', 'ring'), '#FDC41B': R('y', 'fillHover'), '#E67700': R('y', 'ringHover') }, DOT) },
  menuFriends: { fam: { a: 'indigo', b: 'orange' }, all: Object.assign({
    '#91A7FF': R('a', 'fill'), '#4C6EF5': R('a', 'ring'), '#5C7CFA': R('a', 'fillHover'), '#3B5BDB': R('a', 'ringHover'),
    '#FFC078': R('b', 'fill'), '#FD7E14': R('b', 'ring'), '#FF922B': R('b', 'fillHover'), '#F76707': R('b', 'ringHover') }, DOT) },
  tableMenu: { fam: { m: 'blue' }, all: { '#74C0FC': R('m', 'fill'), '#228BE6': R('m', 'ring'), '#1971C2': R('m', 'glyph') }, states: { active: SOLID_BLUE, hover: SOLID_BLUE } },
  chatMenu: { fam: { m: 'lime' }, all: { '#A9E34B': R('m', 'fill'), '#66A80F': R('m', 'ring'), '#5C940D': R('m', 'glyph') }, states: { hover: SOLID_LIME, active: SOLID_LIME } },
  hintMenu: { fam: { m: 'yellow' }, all: { '#FFD43B': R('m', 'fill'), '#F59F00': R('m', 'ring'), '#D8D8D8': R('base', 'base') },
    states: { hover: { '#F59F00': R('m', 'fillHover'), '#E67700': R('m', 'ringHover'), '#D8D8D8': R('base', 'base') } } },
  playerLeaving: INK, playerMore: INK, sortArrows: INK, menuBurger: INK, menuClose: INK,
  crown: GOLD, playerLiked: GOLD,
  friendMessage: { fam: { m: 'lime' }, all: Object.assign({ '#A9E34B': R('m', 'fill'), '#66A80F': R('m', 'ring'), '#5C940D': R('m', 'glyph'), '#4F800B': R('m', 'glyphHover') }, DOT) },
  friendInvite: { fam: { m: 'blue', g: 'grey' }, all: { '#A5D8FF': R('m', 'fill'), '#63B4F2': R('m', 'ring'), '#1971C2': R('m', 'glyph'), '#1665AD': R('m', 'glyphHover'),
    '#E9ECEF': R('g', 'fill'), '#ADB5BD': R('g', 'ring'), '#868E96': R('g', 'glyph') } },
  send: { fam: { m: 'blue', g: 'grey' }, all: { '#A5D8FF': R('m', 'fill'), '#63B4F2': R('m', 'ring'), '#1971C2': R('m', 'glyph'), '#1665AD': R('m', 'glyphHover'),
    '#DEE2E6': R('g', 'fill'), '#ADB5BD': R('g', 'ring'), '#868E96': R('g', 'glyph') } },
  friendSearch: GREY_BTN, friendSearchClose: GREY_BTN,
  friendBack: { fam: { g: 'grey' }, all: { '#868E96': R('g', 'mark'), '#495057': R('g', 'markHover') } },
  likedBadge: { fam: { m: 'gold' }, all: { '#FFD43B': R('m', 'fill') } },
  botBadge: { fam: { g: 'grey' }, all: { '#AEB5BD': R('g', 'fill'), '#646E78': R('g', 'glyph') } },
  highReputationBadge: { fam: { m: 'lime' }, all: { '#A9E34B': R('m', 'fill'), '#5C940D': R('m', 'glyph') } },
  cleanMeldBadge: { fam: { m: 'lime' }, all: { '#A9E34B': R('m', 'fill') } },
  dealer: { all: { '#F8F9FA': R('paper', 'paper'), '#212529': R('ink', 'ink') } },
};

// ---- the rest of the icons (Holger, 23 Sep 2026: version 13, Scheme hues with green inks, for every
// icon). Only a version with `rest: true` reaches these, so the other versions stay as they were
// compared; an icon named here and in ROLES takes this recipe in such a version. Where the scheme
// already has the exact colour for the job, the icon takes it: the light plates for anything pale that
// carries a mark (the friends panel's buttons, the canasta chips, the turn timer), the medals' metals for
// the celebration art, the Go button's green and ring for the checks and the ribbons, the rating stars
// for the game over stars, the classic deck's own red and black for the suit confetti, and the table's
// yellow verb for the hint arrow (Law 4). What stays as built, and why, is in ICON-COLOURS.md.
// A role keyed "stroke:#hex" paints that colour only where it is a stroke: the timer's arc is the
// number's colour on the site, and here takes its own.
// the cup, the hand, the sun and the slam wear the gold medal: its rosette's #FCC419 and its outline's
// deep gold (Holger, 23 Sep 2026: "a little lighter, like the place medal"). The cup's star is the gold star,
// as the mixed canasta's is (24 Sep); until then it took the outline, as the medal's number does
const TROPHY = { fam: { y: 'medalGold', g: 'go', s: 'goldStar' }, all: { '#FDC41B': R('y', 'fill'), '#FCC419': R('y', 'fill'), '#F59E02': R('y', 'ring'), '#E67700': R('s', 'star'),
  '#60C400': R('g', 'fill'), '#5CBC00': R('g', 'fillHover'), '#4D9D00': R('g', 'ring'), '#4A9600': R('g', 'ring') } };
// a button on a light plate: the plate, its ring and its glyph in the link ink, and under the pointer the
// same plate with the glyph in the deep ink (Holger, 23 Sep 2026: the deep ink read almost black as a
// solid glyph at rest, so it is the hover's; 24 Sep: the plate keeps its colour under the pointer and only
// the glyph darkens). Words on a plate keep the deep ink
const onPlate = (slot, fill, ring, glyph, hoverGlyph) => ({ rest: { [fill]: R(slot, 'fill'), [ring]: R(slot, 'ring'), [glyph]: R(slot, 'mark') },
  hover: { [fill]: R(slot, 'fill'), [ring]: R(slot, 'ring'), [hoverGlyph]: R(slot, 'glyph') } });
const TRAY_BTN = { fam: { g: 'tray' }, all: onPlate('g', '#DEE2E6', '#ADB5BD', '#868E96', '#495057').rest, states: { hover: onPlate('g', '#DEE2E6', '#ADB5BD', '#868E96', '#495057').hover } };
const ROLES_REST = {
  // the friends panel (Holger, 23 Sep 2026: its light buttons take the light plates; 24 Sep: the invite, a
  // sent one too, and the send take the message's green plate, the blue and the solid green both gone): the
  // message, the invite and the send the green plate, as the chat is green; the search, its close and a
  // send with nothing typed the tray paper. Under the pointer every plate keeps its colour (onPlate)
  friendMessage: { fam: { m: 'plateGreen' }, all: Object.assign(onPlate('m', '#A9E34B', '#66A80F', '#5C940D', '#4F800B').rest, DOT),
    states: { hover: onPlate('m', '#A9E34B', '#66A80F', '#5C940D', '#4F800B').hover } },
  friendInvite: { fam: { m: 'plateGreen' }, all: Object.assign(onPlate('m', '#A5D8FF', '#63B4F2', '#1971C2', '#1665AD').rest, onPlate('m', '#E9ECEF', '#ADB5BD', '#868E96', '#495057').rest),
    states: { hover: onPlate('m', '#A5D8FF', '#63B4F2', '#1971C2', '#1665AD').hover } },
  send: { fam: { m: 'plateGreen', g: 'tray' }, all: Object.assign(onPlate('m', '#A5D8FF', '#63B4F2', '#1971C2', '#1665AD').rest, onPlate('g', '#DEE2E6', '#ADB5BD', '#868E96', '#495057').rest),
    states: { hover: onPlate('m', '#A5D8FF', '#63B4F2', '#1971C2', '#1665AD').hover } },
  friendSearch: TRAY_BTN, friendSearchClose: TRAY_BTN,
  friendBack: { fam: { g: 'tray' }, all: { '#868E96': R('g', 'glyph'), '#495057': R('g', 'glyphHover') } },
  checkmark: { fam: { g: 'go', k: 'grey' }, all: { '#64CD00': R('g', 'fill'), '#479100': R('g', 'ring'), '#CED4DA': R('k', 'fill'), '#868E96': R('k', 'ring') } },
  // the meld's count tab keeps its green and yellow, now the light plates, and its tab and the cards' edge
  // (Holger, 23 Sep 2026). The green star is a glyph in its plate's link ink; the yellow star is the gold star,
  // which reads yellow where the yellow's link ink read brown (24 Sep). The count in the same tab is words and
  // keeps the deep ink
  canastaStar: { fam: { n: 'plateGreen', m: 'plateYellow', s: 'goldStar' }, all: {},
    states: { natural: { '#C0EB75': R('n', 'fill'), '#4F800B': R('n', 'mark') }, mixed: { '#FFE066': R('m', 'fill'), '#C96800': R('s', 'star') } } },
  // the turn timer on the yellow and the red plate: the plate, the track (the faded ring) its ring a step
  // deeper, the number in the plate's ink, and the arc a lighter step of the family, so it reads over the
  // track without weighing on it (Holger, 23 Sep 2026: the arc was too dark, then the faded ring too light)
  turnTimer: { fam: { y: 'plateYellow', r: 'plateRed' }, all: {},
    states: { rest: { '#FFE066': R('y', 'fill'), '#F4BD45': R('y', 'track'), '#C96800': R('y', 'glyph'), 'stroke:#C96800': R('y', 'arc') },
      red: { '#FFA8A8': R('r', 'fill'), '#F67A7A': R('r', 'track'), '#C92A2A': R('r', 'glyph'), 'stroke:#C92A2A': R('r', 'arc') } } },
  hintArrow: { fam: { y: 'verb' }, all: { '#FFE852': R('y', 'fill') } },
  // the suits that burst from a played card, in the classic deck's own red and black
  suits: { fam: { r: 'deck' }, all: { '#EB1B28': R('r', 'red'), '#CE1823': R('r', 'red'), '#000000': R('r', 'black') } },
  gameOverHeader: TROPHY, handOverHeader: TROPHY, slam: TROPHY,
  shootTheSun: { fam: { y: 'medalGold', g: 'go' }, all: { '#FCC419': R('y', 'fill'), '#F59E02': R('y', 'ring'), '#60C400': R('g', 'fill') } },
  // the moon the silver medal, as the sun is the gold one
  shootTheMoon: { fam: { k: 'medalSilver', g: 'go' }, all: { '#CED4DA': R('k', 'fill'), '#868E96': R('k', 'ring'), '#60C400': R('g', 'fill') } },
  // the rays behind the hand over panel take the verb itself: the deeper step reads too loud for a ground
  handOverBackground: { fam: { y: 'verb' }, all: { '#FFE066': R('y', 'fill') } },
  // a medal's rosette is the fill, its ribbon the deeper fill, and its outline and number one line
  medals: { fam: { y: 'medalGold', k: 'medalSilver', o: 'medalBronze', f: 'medalFourth', b: 'blue' },
    all: { '#FCC419': R('y', 'fill'), '#F59F00': R('y', 'fillHover'), '#DD7200': R('y', 'ring'), '#AEB5BD': R('k', 'fill'), '#868E96': R('k', 'fillHover'), '#565F68': R('k', 'ring'),
      '#FF932A': R('o', 'fill'), '#F76707': R('o', 'fillHover'), '#C03D09': R('o', 'ring') },
    states: { fourth: { '#FFE066': R('f', 'fill'), '#F59F00': R('f', 'ring'), '#74C0FC': R('b', 'fill'), '#228BE6': R('b', 'ring') } } },
  ratingStarsGameOver: { fam: { s: 'star', e: 'starEmpty' }, all: { '#FCC419': R('s', 'fill'), '#DD7200': R('s', 'ring'), '#CED4DA': R('e', 'fill'), '#868E96': R('e', 'ring') } },
  dailyChallenge: { fam: { y: 'medalGold', k: 'medalSilver', o: 'medalBronze' }, all: { '#FDC41B': R('y', 'fill'), '#F59E02': R('y', 'ring'), '#AEB5BD': R('k', 'fill'), '#878E96': R('k', 'ring'),
    '#FF932A': R('o', 'fill'), '#F76706': R('o', 'ring') } },
  dealDayPlay: { fam: { y: 'gold' }, all: { '#FDC41B': R('y', 'fill') } },
};
// The light yellow plate's ink (Holger, 23 Sep 2026: the walnut #3D2B00 read too dark on the plate). The
// other plates write at L .415, 89% of what their hue holds there (Law 5); the yellow takes that depth at
// the hue the yellow button's inks walk to, 72.6, since yellow turns toward orange as it darkens (Law 2).
const YELLOW_INK = C.deepInk(72.6);
if (YELLOW_INK !== '#664411') throw new Error('the yellow plate ink moved: ' + YELLOW_INK);
// Its link ink, for a glyph on the plate (the canasta's mixed star; Holger, 23 Sep 2026): the link rung,
// L .543, at the same hue. The link recipe's C .149 clips there, so it takes 89% of what the hue holds
const YELLOW_LINK = C.to(0.543, C.maxC(0.543, 72.6) * 0.89, 72.6);
if (YELLOW_LINK !== '#94651E') throw new Error('the yellow plate link ink moved: ' + YELLOW_LINK);
// The light green plate, Holger's pick of 23 Sep 2026 (version 5 of green-plate-lab.html): hue 131 at C .13 by the
// plates' recipe (DESIGN-COLOUR 4.2), since #B2DD9B (hue 135, C .10) read a little teal on the warm paper. Its inks
// follow the hue: the deep ink at L .415, 89% of what the hue holds, and the link ink the link rung, which the
// screen holds at C .144 here
function lightPlate(h, c) {
  const fill = C.to(0.851, c, h);
  return { fill, fillHover: C.mix(fill, 94, K), ring: C.to(0.760, c * 1.3, h), glyph: C.to(0.415, C.maxC(0.415, h) * 0.89, h), mark: C.to(0.543, 0.149, h) };
}
const GREEN_PLATE = lightPlate(131, 0.13);
// The turn timer's track, the faded ring of the time gone: the plate's ring .05 deeper at its own hue and strength
// (Holger, 23 Sep 2026: "make the faded line a bit darker"; the ring itself read too close to the fill)
const deeper = (hex, dL) => { const o = C.ok(hex); return C.to(o.L - dL, o.C, o.h); };
// The light yellow plate, Holger's pick of 24 Sep 2026 (version 5 of yellow-plate-lab.html): hue 96 at C .135, lifted
// to L .88 as the yellow is (DESIGN-COLOUR 4.3), since #F4D576 (hue 92.2, C .12) read a little tan. The ring is L .79
// at the same hue and strength, the hover the plate 8% toward the deep orange
const YELLOW_FILL = C.to(0.88, 0.135, 96);
const YELLOW_PLATE = { fill: YELLOW_FILL, fillHover: C.mix(YELLOW_FILL, 92, '#E67700'), ring: C.to(0.79, 0.135, 96) };
if (YELLOW_PLATE.fill !== '#F2D767' || YELLOW_PLATE.ring !== '#D4BA47' || YELLOW_PLATE.fillHover !== '#F1CF5F') throw new Error('the yellow plate moved: ' + JSON.stringify(YELLOW_PLATE));
const TIMER_TRACK_YELLOW = deeper(YELLOW_PLATE.ring, 0.05), TIMER_TRACK_RED = deeper('#E8958C', 0.05);
// The gold star: a star on the light yellow plate (the mixed canasta) and in the game over cup. It weighs what the
// green canasta star weighs (3.23:1 on the yellow plate against its 3.16:1), one colour with no outline: an amber
// gold at L .57, hue 62, 95% of the strength the hue holds there (Holger, 24 Sep 2026, G3; S2, #D98B06 at L .70,
// read too light beside the green star, and the yellow's link ink #94651E read brown)
const GOLD_STAR = C.to(0.57, C.maxC(0.57, 62) * 0.95, 62);
if (GOLD_STAR !== '#AA6413') throw new Error('the gold star moved: ' + GOLD_STAR);
if (TIMER_TRACK_YELLOW !== '#C4AA34' || TIMER_TRACK_RED !== '#D7867D') throw new Error('the timer track moved: ' + TIMER_TRACK_YELLOW + ' ' + TIMER_TRACK_RED);
if (GREEN_PLATE.fill !== '#B0E084' || GREEN_PLATE.glyph !== '#375612' || GREEN_PLATE.mark !== '#507F0A') throw new Error('the green plate moved: ' + JSON.stringify(GREEN_PLATE));
// the scheme's own colours those roles take
const REST_PALETTES = {
  go: { fill: '#43A038', fillHover: '#3E9334', ring: '#347D2C', glyph: W, mark: W },
  star: { fill: '#F5B81E', ring: '#EF7F27' }, starEmpty: { fill: '#D2CFCA', ring: '#9B9997' },
  // the light plates (DESIGN-COLOUR 4.3): fill, hover, ring, deep ink and, as `mark`, the link ink a glyph
  // takes at rest. The arc is the turn timer's: the yellow walk's deepest step and the danger red, one step
  // lighter than the inks
  plateGreen: GREEN_PLATE,
  plateBlue: { fill: '#ABD2FF', fillHover: '#A3CCFB', ring: '#83B5EF', glyph: '#124F7E', mark: '#1971C2' },
  plateRed: { fill: '#FCBCB4', fillHover: '#EDB1A9', ring: '#E8958C', glyph: '#8B1A1A', arc: '#C92A2A', track: TIMER_TRACK_RED },
  plateYellow: { fill: YELLOW_PLATE.fill, fillHover: YELLOW_PLATE.fillHover, ring: YELLOW_PLATE.ring, glyph: YELLOW_INK, mark: YELLOW_LINK, arc: '#E67700', track: TIMER_TRACK_YELLOW },
  // the tray paper: --plate-tray, --line-tray and --ink-label, the tray cell's hover (--ot-hover, the
  // line), --ink-quiet for a glyph at rest and --ink under the pointer where only the mark changes
  tray: { fill: '#E4DDD0', fillHover: '#D9D2C4', ring: '#C9C0AE', glyph: '#4E4D4C', glyphHover: '#141414', mark: '#67635C' },
  // the classic deck's suits, measured from its card faces (static/pieces/card/classic)
  deck: { red: '#D51A22', black: '#0E0D0D' },
  // the three metals, so a medal reads gold, silver or bronze at a glance (Holger, 23 Sep 2026): the rosette,
  // the ribbon a step deeper, and the outline and number as one deep line. Gold is the yellow ladder's
  // #FCC419 and #FAB005 over a gold brown (--to .56 .115 70). Silver stays cool (hue 250, C .012 to .016),
  // as the game over panel's silver cell does: a metal, not a paper grey, so Law 1 does not reach it.
  // Bronze is a copper at hue 58 to 44 (--to .75 .11 58, .65 .12 50, .46 .10 44). The fourth to sixth
  // medal's rosette is the light yellow, so it never reads as the gold.
  medalGold: { fill: '#FCC419', fillHover: '#FAB005', ring: '#9F6713' },
  medalSilver: { fill: '#BEC5CC', fillHover: '#9BA2AA', ring: '#5D646C' },
  medalBronze: { fill: '#E29C65', fillHover: '#C97847', ring: '#854325' },
  medalFourth: { fill: YELLOW_PLATE.fill, ring: '#9F6713' },
  verb: { fill: '#FFD43B' },
  goldStar: { star: GOLD_STAR },
};

// the colours outside the families: the notice's red dot (a version may make its own), the ink of the
// door, more and sort marks, the dealer chip's paper and the hint bulb's base
const SPECIAL = { dot: { fill: '#C92A2A', ring: '#9D2121' }, ink: { ink: '#141414' }, paper: { paper: W }, base: { base: C.warmTwin('#D8D8D8') } };

// ---- deep lines. Of the first versions tried (warm greys, the plates' tones, the scheme's colours,
// pale like the catalog tiles, bold like the buttons; all dropped on 23 Sep 2026), Holger liked only the
// bold version's bell and hint: the colours a little darker, and the lines drawing the shape. Those two
// kept their fill and took their lines from yellow 7 to yellow 9, .20 deeper in OKLCH lightness than the
// fill. A deep version does that to every icon: each line sits a set depth under the icon's own fill,
// on the icon's own Open Color ramp, so a yellow line turns toward orange as the ramp and the scheme's
// yellow do (DESIGN-COLOUR Law 2), and a depth past step 9 keeps step 9's hue. The greys are the
// paper's warm greys (Law 1).
const OC = {
  yellow: ['#FFF9DB', '#FFF3BF', '#FFEC99', '#FFE066', '#FFD43B', '#FCC419', '#FAB005', '#F59F00', '#F08C00', '#E67700'],
  orange: ['#FFF4E6', '#FFE8CC', '#FFD8A8', '#FFC078', '#FFA94D', '#FF922B', '#FD7E14', '#F76707', '#E8590C', '#D9480F'],
  lime: ['#F4FCE3', '#E9FAC8', '#D8F5A2', '#C0EB75', '#A9E34B', '#94D82D', '#82C91E', '#74B816', '#66A80F', '#5C940D'],
  blue: ['#E7F5FF', '#D0EBFF', '#A5D8FF', '#74C0FC', '#4DABF7', '#339AF0', '#228BE6', '#1C7ED6', '#1971C2', '#1864AB'],
  indigo: ['#EDF2FF', '#DBE4FF', '#BAC8FF', '#91A7FF', '#748FFC', '#5C7CFA', '#4C6EF5', '#4263EB', '#3B5BDB', '#364FC7'],
  red: ['#FFF5F5', '#FFE3E3', '#FFC9C9', '#FFA8A8', '#FF8787', '#FF6B6B', '#FA5252', '#F03E3E', '#E03131', '#C92A2A'],
};
const RAMP = Object.fromEntries(Object.entries(OC).map(([k, r]) => [k, r.map((h) => C.ok(h))]));
RAMP.gold = RAMP.yellow;
// the colour at lightness L on a family's ramp, between its two nearest steps
function onRamp(fam, L) {
  if (fam === 'grey') return C.to(L, L > 0.75 ? 0.03 : 0.02, 84);
  const r = RAMP[fam];
  if (L >= r[0].L) return C.css4(L, r[0].C, r[0].h);
  for (let i = 0; i < r.length - 1; i++) {
    const a = r[i], b = r[i + 1];
    if (L <= a.L && L >= b.L) { const t = (a.L - L) / (a.L - b.L); return C.css4(L, a.C + (b.C - a.C) * t, a.h + (b.h - a.h) * t); }
  }
  const z = r[r.length - 1];
  return C.css4(L, z.C, z.h);
}
// A family's tones for one icon, made from the colours the icon was built with (`built(role)` gives the
// one it has for a role, if any). `fill` moves the fills down the ramp (0 keeps them), `line` and `glyph`
// say how far under its fill a line and a glyph sit, and `sline` the same for the solid set. A hover
// keeps the step it has as built, so the new lines do not weaken it; a solid set with no colour of its
// own takes the solid rung (L .627, Law 3).
const MARK_ONLY = { grey: '#DEE2E6' };
function deepAt(fam, o) {
  return (built) => {
    const L = (h) => C.ok(h).L, on = (l) => onRamp(fam, l);
    const own = (h) => (fam === 'grey' ? C.warmTwin(h) : h);
    const shift = (h) => (o.fill ? on(L(own(h)) - o.fill) : own(h));
    const step = (a, b, dflt) => (built(a) && built(b) ? L(built(a)) - L(built(b)) : dflt);
    const fill = shift(built('fill') || MARK_ONLY[fam]), F = L(fill);
    const fillHover = built('fillHover') ? shift(built('fillHover')) : on(F - 0.04), FH = L(fillHover);
    const glyph = on(F - o.glyph), mark = on(F - o.glyph);
    const sfill = built('sfill') ? shift(built('sfill')) : on(0.627);
    return { fill, ring: on(F - o.line), glyph, fillHover, ringHover: on(FH - o.line), glyphHover: on(L(glyph) - step('glyph', 'glyphHover', FH === F ? 0.04 : F - FH)),
      mark, markHover: on(L(mark) - step('mark', 'markHover', 0.06)), sfill, sring: on(L(sfill) - o.sline), sglyph: W };
  };
}
function families(make) {
  const f = {};
  ['yellow', 'gold', 'lime', 'blue', 'indigo', 'orange', 'grey'].forEach((k) => { f[k] = make(k); });
  return f;
}
function deepFamilies(o) { return families((k) => deepAt(k, o)); }
function deepDot(o) { const d = deepAt('red', o)((r) => (r === 'fill' ? '#F03E3E' : null)); return { fill: d.fill, ring: d.ring }; }
// Deep lines, fuller fills: the version the scheme versions start from
const V8 = { fill: 0.045, line: 0.20, glyph: 0.30, sline: 0.15 };

// ---- the scheme's hues and rungs. The plates, the buttons and the frontpage agree because, for each
// job, the scheme holds lightness and strength still and turns only the hue (DESIGN-COLOUR 3.1): the
// buttons at L .627 C .167, the plates at L .851 C .076, the catalog tiles on four rungs of their own.
// It keeps few hues: blue 252.2, green 141.6 (the light green at 135, Holger's pick), red 26.6, and the
// yellow walking to orange as it darkens, a ladder that holds the buttons' strength, C .167. Holger
// rejected light and solid families at every other hue (13 Sep). So the icons' indigo takes the blue and
// their lime the light green. Orange walks as the bronze medal's ramp, the same Open Color orange, does;
// yellow and gold are the scheme's yellow ladder already, and the greys its warm greys. The scheme
// versions start from Deep lines, fuller fills (version 8 when Holger asked for them, 23 Sep 2026).
const SCHEME_HUE = { blue: 252.2, indigo: 252.2, lime: 135, red: 26.6 };
const BUTTON_HUE = { blue: 252.2, indigo: 252.2, lime: 141.6 };
// a solid state is the scheme's button at the family's hue: the fill on the solid rung, its ring the
// 78% black mix and a white glyph (Laws 3 and 6)
function button(h) { const f = C.to(0.627, 0.167, h); return { sfill: f, sring: C.mix(f, 78, K), sglyph: W }; }
// Scheme hues: version 8's tones, each turned to its family's scheme hue at its own lightness and
// strength (Law 2), cut to fit the screen
function turnedAt(fam) {
  const deep = deepAt(fam, V8);
  if (SCHEME_HUE[fam] == null) return deep;
  return (built) => {
    const p = deep(built), out = {};
    Object.keys(p).forEach((k) => { const c = C.ok(p[k]); out[k] = p[k] === W ? W : C.to(c.L, c.C, SCHEME_HUE[fam]); });
    return BUTTON_HUE[fam] != null ? Object.assign(out, button(BUTTON_HUE[fam])) : out;
  };
}
function turnedDot() { const d = deepDot(V8); return { fill: C.to(C.ok(d.fill).L, C.ok(d.fill).C, SCHEME_HUE.red), ring: C.to(C.ok(d.ring).L, C.ok(d.ring).C, SCHEME_HUE.red) }; }
// Scheme rungs: the scheme's hues, and one lightness and strength per job, as the plates and the
// buttons share theirs. Version 8's depths land on rungs the scheme already has when the fill sits
// where version 8's blue fill did (L .737, blue's own ceiling there, C .135): the line .20 under it is
// the link ink's rung, L .543 C .149 (Law 5), and the glyph .30 under it the catalog tiles' ink, L .44
// C .15. A hover keeps the step it has as built. `room` lets fills and lines take the buttons' C .167
// where the hue can hold it (Proposal P's "more by eye", as Holger's light green did); blue stays at its
// ceiling. Orange takes its ramp's hue at each depth, so it keeps walking.
// `hues` and `buttons` hold each family at one hue (a family not named takes its ramp's hue at each
// depth, so orange keeps walking), and `fill` moves the whole ladder: the line and the glyph keep their
// distance under the fill, unless `glyph` sets the glyph's own depth.
const RUNG = { fill: [0.737, 0.135], line: [0.543, 0.149], glyph: [0.44, 0.15] };
function rungAt(fam, o) {
  if (fam === 'yellow' || fam === 'gold' || fam === 'grey') return deepAt(fam, V8);
  const hues = o.hues || SCHEME_HUE, buttons = o.buttons || hues;
  const FL = o.fill || RUNG.fill[0], LL = FL - (RUNG.fill[0] - RUNG.line[0]), GL = o.glyph || FL - (RUNG.fill[0] - RUNG.glyph[0]);
  const fillC = o.room ? 0.167 : RUNG.fill[1], lineC = o.room ? 0.167 : RUNG.line[1], GC = RUNG.glyph[1];
  return (built) => {
    const hue = (L) => (hues[fam] != null ? hues[fam] : C.ok(onRamp(fam, L)).h);
    const at = (L, c) => C.to(L, c, hue(L));
    const Lb = (h) => C.ok(h).L;
    const step = (a, b, dflt) => (built(a) && built(b) ? Lb(built(a)) - Lb(built(b)) : dflt);
    const fs = step('fill', 'fillHover', 0.04), gs = step('glyph', 'glyphHover', fs);
    return Object.assign({ fill: at(FL, fillC), fillHover: at(FL - fs, fillC), ring: at(LL, lineC), ringHover: at(LL - fs, lineC),
      glyph: at(GL, GC), glyphHover: at(GL - gs, GC), mark: at(GL, GC), markHover: at(GL - step('mark', 'markHover', 0.06), GC) },
      button(buttons[fam] != null ? buttons[fam] : hue(0.627)));
  };
}
// ---- our hues. The scheme versions trade the icons' Open Color hues for the scheme's few; these keep
// them and give them our touch instead (Holger, 23 Sep 2026). The scheme's method never picks a hue: it
// fixes how any hue is built, the way the catalog tiles build eighteen game colours on one ladder of their
// own. So each icon keeps its Open Color family, held at one hue as our blue and red are (Open Color's
// hues drift up to 13 degrees along a ramp): the blue at ours, 252.2, the indigo and the lime at their
// ramps' step 6. The orange and the yellow walk, as our yellow does. Every family then takes the icon
// ladder above at our strength, C .167, as far as the screen allows, and an open state is the button rung
// at the family's own hue.
const OWN_HUE = { blue: 252.2, indigo: C.ok('#4C6EF5').h, lime: C.ok('#82C91E').h, red: 26.6 };
// Scheme hues with the green of Our hues, lighter (Holger, 23 Sep 2026: Scheme hues is his favourite,
// but its chat reads too green; the chat of Our hues, lighter is the right green, with darker stripes).
// The lime family takes that green (L .80, C .167 at the lime's own hue, where Scheme hues has C .203)
// and its stripes, the glyph, at `glyph`. An open chat stays the scheme's green button.
function schemeHuesSofterLime(glyph) {
  return Object.assign(families(turnedAt), { lime: rungAt('lime', { hues: OWN_HUE, buttons: BUTTON_HUE, room: true, fill: 0.80, glyph }) });
}
// The second try (Holger, 23 Sep 2026: "try again" after 10 to 12). In Scheme hues the chat is drawn
// lighter than its neighbours (outline L .61 and stripes .50, where the table icon has .54 and .44) and
// its green is the strongest colour on the table. So the lime family takes the scheme's own light-green
// inks (DESIGN-COLOUR 4.3): the outline the link ink #468115 (L .54, as deep as the table icon's
// outline) and the stripes the plate ink #305812 (L .415, the depth of words on a coloured fill, Law 5).
// Only the fill moves, from the green of Our hues, lighter down to the scheme's light green plate.
const GREEN_INK = { line: '#468115', glyph: '#305812' };
// version 13 draws in the plate's inks as they are now (23 Sep 2026: the plate moved to hue 131); versions 14
// and 15 keep the inks they were compared with
const GREEN_INK_NOW = { line: GREEN_PLATE.mark, glyph: GREEN_PLATE.glyph };
function greenInksAt(fill, inks) {
  const ink = inks || GREEN_INK;
  return (built) => {
    const ok = (x) => C.ok(x), down = (x, dL) => C.to(ok(x).L - dL, ok(x).C, ok(x).h);
    const step = (a, b, dflt) => (built(a) && built(b) ? ok(built(a)).L - ok(built(b)).L : dflt);
    const fs = step('fill', 'fillHover', 0.04), gs = step('glyph', 'glyphHover', fs);
    return Object.assign({ fill, fillHover: down(fill, fs), ring: ink.line, ringHover: down(ink.line, fs),
      glyph: ink.glyph, glyphHover: down(ink.glyph, gs), mark: ink.glyph, markHover: down(ink.glyph, step('mark', 'markHover', 0.06)) },
      button(BUTTON_HUE.lime));
  };
}
function schemeHuesGreenInks(fill, inks) { return Object.assign(families(turnedAt), { lime: greenInksAt(fill, inks) }); }

// ---- new art, for what a colour cannot mend (Holger, 23 Sep 2026). A state's replacement is drawn in its
// new colours, from new/; `pad` is how far it draws past the icon's box, and `note` goes into the plan.
const NEW = (f) => fs.readFileSync(path.join(__dirname, 'new', f), 'utf8');
const TICK_NOTE = 'the letter ✔ becomes the pick mark’s tick, drawn, in the Go green `#43A038`, one green for both lines';
const NEW_ART = {
  'caret/picked': { svg: NEW('caret--picked.svg'), pad: 1, note: 'the white caret takes a 1px outline in the green’s ring `#347D2C`, as white does on every green (Law 5)' },
  'glyphHeart/rest': { svg: NEW('glyphHeart.svg'), note: 'the letter ♥ becomes the site’s own heart, drawn (the suit confetti’s shape, 10px wide), in the classic deck’s red `#D51A22`' },
  'glyphCheck/auth': { svg: NEW('glyphCheck.svg'), note: TICK_NOTE },
  'glyphCheck/settings': { svg: NEW('glyphCheck.svg'), note: TICK_NOTE },
};

const VERSIONS = [
  { id: 'deep', title: 'Deep lines',
    desc: 'Each icon keeps its fill, and its lines sit .20 deeper than the fill on the icon’s own colour ramp, as the bold version’s bell and hint went from yellow 7 to yellow 9. The glyphs sit deeper still.',
    family: deepFamilies({ line: 0.20, glyph: 0.30, sline: 0.15 }), special: { dot: deepDot({ line: 0.20, glyph: 0.30, sline: 0.15 }) } },
  { id: 'deepfill', title: 'Deep lines, fuller fills',
    desc: 'Deep lines, with every fill one step down its ramp as well, so the colours read a little darker.',
    family: deepFamilies(V8), special: { dot: deepDot(V8) } },
  { id: 'heavy', title: 'Heavy lines',
    desc: 'Deep lines taken a step further: the fills as built, the lines .28 under them and the glyphs .38.',
    family: deepFamilies({ line: 0.28, glyph: 0.38, sline: 0.20 }), special: { dot: deepDot({ line: 0.28, glyph: 0.38, sline: 0.20 }) } },
  { id: 'schemerung', title: 'Scheme rungs',
    desc: 'Scheme hues, and one depth and strength per job, as the plates and the buttons share theirs: every fill at L .737 C .135, where the blue fill sat already, every line on the link ink’s rung and every glyph on the catalog tiles’ ink. The notice dot is the danger red.',
    family: families((k) => rungAt(k, { buttons: BUTTON_HUE })), special: { dot: SPECIAL.dot } },
  { id: 'schemeroom', title: 'Scheme rungs, stronger',
    desc: 'Scheme rungs, with the fills and lines as strong as the buttons (C .167) where the hue has room: the green and the orange. The blue stays at the most it can hold at that depth.',
    family: families((k) => rungAt(k, { buttons: BUTTON_HUE, room: true })), special: { dot: SPECIAL.dot } },
  { id: 'schemehue', title: 'Scheme hues',
    desc: 'Deep lines, fuller fills, with each icon turned to the scheme’s own hue at its own depth: the table and the friends’ bodies to the blue of the plates and buttons, the chat to the light green. An open state is the scheme’s blue or green button. Yellow, gold and orange were on the scheme’s yellow walk and the bronze medal’s ramp already.',
    family: families(turnedAt), special: { dot: turnedDot() } },
  { id: 'ourhue', title: 'Our hues',
    desc: 'Open Color’s hues with our touch. Each icon keeps its Open Color family, held at one hue as our blue and red are (the blue at ours), with the orange and the yellow walking as our yellow does. Every family sits on one ladder: fills at L .737, lines on the link ink’s rung, glyphs on the catalog ink’s, all at our strength (C .167) as far as the screen allows. The yellows keep their lift.',
    family: families((k) => rungAt(k, { hues: OWN_HUE, room: true })), special: { dot: SPECIAL.dot } },
  { id: 'ourhuelight', title: 'Our hues, lighter',
    desc: 'Our hues with the ladder a step lighter: fills at L .80, where version 8’s warm fills sat, with the lines and glyphs .19 and .30 under them. The warm colours stay as bright as in version 8; the blue and the indigo get paler, since a screen cannot make them strong that light.',
    family: families((k) => rungAt(k, { hues: OWN_HUE, room: true, fill: 0.80 })), special: { dot: SPECIAL.dot } },
  { id: 'schemechat44', title: 'Scheme hues, dark stripes',
    desc: 'Scheme hues, with the softer green of Our hues, lighter on the chat and the other lime icons (C .167 at the lime’s own hue, where Scheme hues has C .203), and the chat’s stripes a step darker, at L .44, the depth of the frontpage tiles’ titles.',
    family: schemeHuesSofterLime(0.44), special: { dot: turnedDot() } },
  { id: 'schemechat38', title: 'Scheme hues, darker stripes',
    desc: 'The same, with the stripes at L .38, between the plates’ text (L .415) and the yellow button’s (L .30).',
    family: schemeHuesSofterLime(0.38), special: { dot: turnedDot() } },
  { id: 'schemechat32', title: 'Scheme hues, darkest stripes',
    desc: 'The same, with the stripes at L .32, near the yellow button’s own dark text.',
    family: schemeHuesSofterLime(0.32), special: { dot: turnedDot() } },
  { id: 'schemeinks', title: 'Scheme hues, green inks',
    desc: 'Scheme hues, with the chat and the other lime icons drawn in the scheme’s own green inks: the outline the light green’s link ink #507F0A (L .54, as deep as the table icon’s outline) and the stripes its plate ink #375612 (L .415, the depth of words on a coloured fill). The fill is the green of Our hues, lighter. The inks follow the light green plate, at hue 131 since 23 Sep (they were #468115 and #305812).',
    family: Object.assign(schemeHuesGreenInks('#97D357', GREEN_INK_NOW), { red: turnedAt('red') }, REST_PALETTES), special: { dot: turnedDot() }, rest: true,
    art: NEW_ART },
  { id: 'schemeinksoft', title: 'Scheme hues, green inks, softer',
    desc: 'The same, with a softer green fill: L .82 and C .13, where Our hues, lighter has L .80 and C .167.',
    family: schemeHuesGreenInks(C.to(0.82, 0.13, OWN_HUE.lime)), special: { dot: turnedDot() } },
  { id: 'schemeinkplate', title: 'Scheme hues, green plate',
    desc: 'The same, with the fill the scheme’s light green plate, #B2DD9B (L .851, C .10), Holger’s pick of 14 Sep. Every colour of the chat is then one the scheme already has.',
    family: schemeHuesGreenInks('#B2DD9B'), special: { dot: turnedDot() } },
];

const data = assemble();
const BY = Object.fromEntries(data.icons.map((i) => [i.id, i]));
const colours = (svg) => [...new Set((svg.match(/(?:fill|stroke|stop-color)\s*=\s*"(#[0-9A-Fa-f]{3,6}|white|black)"/gi) || [])
  .map((m) => { let v = m.split('"')[1].toLowerCase(); if (v === 'white') return W; if (v === 'black') return K; v = v.slice(1); if (v.length === 3) v = v.replace(/./g, '$&$&'); return '#' + v.toUpperCase(); }))];

const out = VERSIONS.map((v) => {
  const ver = { id: v.id, title: v.title, desc: v.desc, global: {}, icon: {}, state: {} };
  if (v.art) {
    Object.keys(v.art).forEach((k) => { const [id, key] = k.split('/'); if (!BY[id] || !BY[id].states.some((st) => st.key === key)) throw new Error(v.id + ': new art for no state ' + k); });
    ver.art = v.art;
  }
  const table = v.rest ? Object.assign({}, ROLES, ROLES_REST) : ROLES;
  Object.keys(table).forEach((id) => {
    const ic = BY[id]; if (!ic) throw new Error('no icon ' + id);
    const roles = table[id];
    // a family given as a function makes its tones from the colours this icon was built with
    const builtOf = (slot) => (role) => {
      const find = (m) => m && Object.keys(m).find((h) => m[h][0] === slot && m[h][1] === role);
      return find(roles.all) || Object.values(roles.states || {}).map(find).find(Boolean) || null;
    };
    const pal = (slot) => {
      if (roles.fam && roles.fam[slot]) {
        const p = (v.iconFamily && v.iconFamily[id] && v.iconFamily[id][slot]) || v.family[roles.fam[slot]];
        return typeof p === 'function' ? p(builtOf(slot)) : p;
      }
      return (v.special && v.special[slot]) || SPECIAL[slot];
    };
    ic.states.forEach((st) => {
      const map = {};
      colours(st.svg).forEach((h) => {
        const r = (roles.states && roles.states[st.key] && roles.states[st.key][h]) || roles.all[h];
        if (!r) return;
        const p = pal(r[0]); const t = p && p[r[1]];
        if (!t) throw new Error(v.id + ': ' + id + '/' + st.key + ' has no ' + r[1] + ' for ' + r[0]);
        if (t !== h) map[h] = t;
      });
      // a role that names its property ("stroke:#hex") paints the colour where that property carries it. It
      // is written even when it keeps the colour, since the colour's plain role may move it elsewhere
      Object.entries(Object.assign({}, roles.all, roles.states && roles.states[st.key])).forEach(([k, r]) => {
        const m = /^([a-z-]+):(#[0-9A-F]{6})$/.exec(k); if (!m) return;
        if (!new RegExp('\\b' + m[1] + '\\s*[=:]\\s*"?' + m[2], 'i').test(st.svg)) return;
        const p = pal(r[0]); const t = p && p[r[1]];
        if (!t) throw new Error(v.id + ': ' + id + '/' + st.key + ' has no ' + r[1] + ' for ' + r[0]);
        map[k] = t;
      });
      if (Object.keys(map).length) ver.state[id + '/' + st.key] = map;
    });
    // an icon's animations follow the state they belong to (the page resolves them by lt.state)
  });
  return ver;
});

const file = path.join(__dirname, 'versions-made.js');
fs.writeFileSync(file, '// Written by make-versions.js. Do not edit by hand: change the recipe there and run it again.\nmodule.exports = ' + JSON.stringify(out, null, 1) + ';\n');
out.forEach((v) => console.log(v.id.padEnd(8), Object.keys(v.global).length, 'global,', Object.keys(v.state).length, 'states'));
write();
