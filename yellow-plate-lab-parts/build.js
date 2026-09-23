// Writes ../yellow-plate-lab.html: versions of the light yellow plate to choose from (Holger, 24 Sep 2026: the
// yellow plate should be a bit more yellow, like the green plate). page.html holds the page; this inlines the colour
// maths, the icon lab's art and the site's face, so the page opens from disk.
//   node yellow-plate-lab-parts/build.js
const fs = require('fs');
const path = require('path');
const HERE = __dirname, ROOT = path.join(HERE, '..'), ICONS = path.join(ROOT, 'icon-lab-parts');
const read = (f) => fs.readFileSync(f, 'utf8');
// the art goes into the page as markup, so its comments and Sketch titles come out
const clean = (svg) => svg.replace(/<\?xml[^>]*>/g, '').replace(/<!--[\s\S]*?-->/g, '').replace(/<(title|desc)>[\s\S]*?<\/\1>/g, '')
  .replace(/\s(data-name)="[^"]*"/g, '').replace(/>\s+</g, '><').trim();
const ART = {
  timer: read(path.join(ICONS, 'inline', 'turnTimer.svg')),
  tabMixed: clean(read(path.join(ICONS, 'inline', 'canastaStar--mixed.svg'))),
  tabNatural: clean(read(path.join(ICONS, 'inline', 'canastaStar.svg'))),
  medal: clean(read(path.join(ICONS, 'sketch', '4.svg'))),
};
for (const k of ['#F4BD45', '#FFE066', 'stroke="#C96800"', 'fill="#C96800">8<', 'stroke-dashoffset="70.215"'])
  if (!ART.timer.includes(k)) throw new Error('the timer art changed: no ' + k);
// the site's face, from guide-fonts.css as data: a page from disk may not load a font file
const faces = read(path.join(ROOT, 'guide-fonts.css')).split('@font-face').slice(1).filter((f) => /BuloRounded/.test(f)).map((f) => '@font-face' + f.trim()).join('\n');
const page = read(path.join(HERE, 'page.html'))
  .replace('/*@@FACES@@*/', () => faces)
  .replace('/*@@COLOUR@@*/', () => read(path.join(ICONS, 'colour.js')))
  .replace('/*@@ART@@*/', () => JSON.stringify(ART).replace(/<\//g, '<\\/'));
fs.writeFileSync(path.join(ROOT, 'yellow-plate-lab.html'), page);
console.log('yellow-plate-lab.html:', Math.round(page.length / 1024), 'KB');
