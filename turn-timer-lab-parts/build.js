// Writes ../turn-timer-lab.html: versions of the turn timer's ring (Holger, 23 Sep 2026: on the yellow the ring
// reads more orange than yellow, and the faded ring is not clear enough). The timer is the icon lab's drawing
// (icon-lab-parts/inline/turnTimer.svg, redrawn from a live timer on dev); page.html recolours it.
//   node turn-timer-lab-parts/build.js
const fs = require('fs');
const path = require('path');
const HERE = __dirname, ROOT = path.join(HERE, '..'), ICONS = path.join(ROOT, 'icon-lab-parts');
const read = (f) => fs.readFileSync(f, 'utf8');
const timer = read(path.join(ICONS, 'inline', 'turnTimer.svg'));
// the site's face, from guide-fonts.css as data, as the icon lab embeds it: a page from disk may not load a font file
const faces = read(path.join(ROOT, 'guide-fonts.css')).split('@font-face').slice(1).filter((f) => /BuloRounded/.test(f)).map((f) => '@font-face' + f.trim()).join('\n');
if (!/font-weight:\s*700/.test(faces)) throw new Error('guide-fonts.css has no bold BuloRounded');
for (const hex of ['#F4BD45', '#FFE066', 'stroke="#C96800"', 'fill="#C96800">8<', 'stroke-dashoffset="70.215"'])
  if (!timer.includes(hex)) throw new Error('the timer art changed: no ' + hex);
const colour = read(path.join(ICONS, 'colour.js'));
const page = read(path.join(HERE, 'page.html'))
  .replace('/*@@FACES@@*/', () => faces)
  .replace('/*@@COLOUR@@*/', () => colour)
  .replace('/*@@TIMER@@*/', () => JSON.stringify(timer).replace(/<\//g, '<\\/'));
fs.writeFileSync(path.join(ROOT, 'turn-timer-lab.html'), page);
console.log('turn-timer-lab.html:', Math.round(page.length / 1024), 'KB');
