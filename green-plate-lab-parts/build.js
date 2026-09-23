// Writes ../green-plate-lab.html: versions of the light green plate to choose from (Holger, 23 Sep 2026: the
// green plate reads a little teal and should be a bit more green). page.html holds the page; this inlines the
// colour maths and the icon art, so the page opens from disk.
//   node green-plate-lab-parts/build.js
const fs = require('fs');
const path = require('path');
const HERE = __dirname, ROOT = path.join(HERE, '..'), ICONS = path.join(ROOT, 'icon-lab-parts');
const { squirclePath, squircleRadius } = require(path.join(ICONS, 'build.js'));
const read = (f) => fs.readFileSync(f, 'utf8');

// the friends panel's buttons take the squircle at twice their round radius (ICON-COLOURS.md 9)
const num = (t, k) => { const m = new RegExp('\\s' + k + '="([^"]*)"').exec(t); return m ? parseFloat(m[1]) : null; };
function squircle(svg) {
  return svg.replace(/<rect\b([^>]*?)\/>/g, (m, a) => { const x = num(a, 'x') || 0, y = num(a, 'y') || 0, w = num(a, 'width'), h = num(a, 'height'), r = num(a, 'rx');
    if (!w || !h || !r || r >= Math.min(w, h) / 2 - 0.01 || w < 12) return m;
    return '<path d="' + squirclePath(x, y, w, h, squircleRadius(r, w, h), [1, 1, 1, 1]) + '"' + a.replace(/\s(?:x|y|width|height|rx|ry)="[^"]*"/g, '') + '/>'; });
}
// the art goes into the page as markup, so its ids and comments come out
const clean = (svg) => svg.replace(/<\?xml[^>]*>/g, '').replace(/<!--[\s\S]*?-->/g, '').replace(/<(title|desc)>[\s\S]*?<\/\1>/g, '')
  .replace(/\s(id|data-name)="[^"]*"/g, '').replace(/>\s+</g, '><').trim();
const inline = (f) => clean(read(path.join(ICONS, 'inline', f)));
const sketch = (f) => clean(read(path.join(ICONS, 'sketch', f)));
const ART = {
  message: squircle(inline('message.svg')),
  messageHover: squircle(inline('message--hover.svg')),
  messageUnread: squircle(inline('message--unread.svg')),
  invite: squircle(inline('invite.svg')),
  canasta: inline('canastaStar.svg'),
  canastaMixed: inline('canastaStar--mixed.svg'),
  chat: sketch('chatMenu.svg'),
  badge: sketch('highReputationBadge.svg'),
};
const colour = read(path.join(ICONS, 'colour.js'));
const page = read(path.join(HERE, 'page.html'))
  .replace('/*@@COLOUR@@*/', () => colour)
  .replace('/*@@ART@@*/', () => JSON.stringify(ART).replace(/<\//g, '<\\/'));
fs.writeFileSync(path.join(ROOT, 'green-plate-lab.html'), page);
console.log('green-plate-lab.html:', Math.round(page.length / 1024), 'KB,', Object.keys(ART).length, 'pieces of art');
