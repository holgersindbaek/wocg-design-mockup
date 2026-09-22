// Assembles design-audit.html from head.html, the NN-*.html fragments (in number order) and the contents menu.
// This is the agents' page: every rule the written guide states, drawn and measured against it. Holger's own page is
// design-guide.html, built by assemble.js. Run: node design-guide-parts/assemble-audit.js
const fs = require('fs'), path = require('path');
const DIR = path.resolve(__dirname, '..'), PARTS = __dirname;
const head = fs.readFileSync(path.join(PARTS, 'head.html'), 'utf8');
const frags = fs.readdirSync(PARTS).filter(f => /^(0[1-9]|1[0-4])-[a-z]+\.html$/.test(f)).sort();  // the fourteen sections; 99-* are builders' throwaways
if (!frags.length) { console.error('no fragments'); process.exit(1); }
const secs = frags.map(f => {
  const html = fs.readFileSync(path.join(PARTS, f), 'utf8');
  const m = html.match(/<section[^>]*\bid="([^"]+)"[^>]*>\s*<h2>([^<]*)<\/h2>/);
  if (!m) { console.error('no section head in', f); process.exit(1); }
  return { file: f, id: m[1], title: m[2].trim(), html };
});
const toc = `<nav id="toc">
  <div class="tt">The design audit</div>
${secs.map(s => `  <a href="#${s.id}">${s.title}</a>`).join('\n')}
  <div class="labs"><div class="lb">The other pages</div><a href="design-guide.html">The design guide</a><a href="colour-lab.html">The colour scheme, the colour reference</a><a href="colour-candidates-lab.html">Colour candidates still open</a><a href="colour-scroll-lab.html">Scroll lab, the felt and paper scenes</a></div>
</nav>`;
const intro = `<div class="page">

  <h1>The design audit</h1>
  <p class="lede">Every rule <code>DESIGN-GUIDE.md</code> states, drawn with the site's own markup and its own stylesheet and measured against what the guide says. This page is for keeping the written guide honest, not for reading: Holger's page is <a href="design-guide.html">the design guide</a>. A card where the site and the guide disagree opens itself and says so in red, and its section takes a red dot in the contents.</p>

  <div class="legend">
    <span class="li">Most pieces are built, agree with the guide and wear no tag.</span>
    <span class="li"><span class="tag call">guide's call</span> <b>the guide asks for something the site does not draw yet</b></span>
    <span class="li"><span class="tag open">open</span> waiting on a decision from you</span>
    <span class="li"><span class="tag stale">stale</span> the site has moved past the guide, so the guide is what gets fixed</span>
    <span class="li" id="sqsup"></span>
  </div>
  <script>document.getElementById('sqsup').textContent = CSS.supports('corner-shape', 'squircle') ? '' : 'This browser cannot draw the squircle corners, so every rounded corner here falls back to a plain arc.';</script>
`;
const outro = `
</div>
<script>
(function(){var links=[].slice.call(document.querySelectorAll('#toc a[href^="#"]'));var secs=links.map(function(a){return document.querySelector(a.getAttribute('href'));});
  function mark(){var y=window.scrollY+120,cur=0;secs.forEach(function(s,i){if(s&&s.offsetTop<=y)cur=i;});links.forEach(function(a,i){a.classList.toggle('on',i===cur);});}
  window.addEventListener('scroll',mark,{passive:true});window.addEventListener('resize',mark);mark();})();
</script>
</body>
</html>
`;
const page = head + '\n' + toc + '\n' + intro + '\n' + secs.map(s => s.html.trim()).join('\n\n') + '\n' + outro;
fs.writeFileSync(path.join(DIR, 'design-audit.html'), page);
console.log('design-audit.html', Math.round(page.length / 1024), 'KB,', secs.length, 'sections:', secs.map(s => s.id).join(' '));
