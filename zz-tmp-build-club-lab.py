# -*- coding: utf-8 -*-
"""leaderboard-deal-lab.html: the leaderboard and the daily deal, six ways. Built from index.html's own stylesheet,
   markup and game-bar script, so every variant is the page's, only arranged differently. 5 September 2026."""
import re, io, os
D = "/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Design/WoCG-3"
src = io.open(os.path.join(D, "index.html"), encoding="utf-8").read()
body_class = re.search(r'<body class="([^"]*)"', src).group(1)
styles = "\n".join(re.findall(r'<style[^>]*>.*?</style>', src, re.S))

def between(s, start, end, inclusive_end=""):
    a = s.index(start); b = s.index(end, a + len(start)); return s[a:b] + inclusive_end
bar = between(src, '<div class="otFilter" id="ldFilter"', '\n      <div class="lobbycol">').rstrip()
board = between(src, '<div class="lobbyBoardCard" id="lobbyBoardCard">', '\n      </div>', '\n      </div>')
deal = between(src, '<div class="lobbyDealCard" id="lobbyDealCard">', '\n      </div>', '\n      </div>')
rows = between(src, '<div class="lbRows">', '\n        </div>', '\n        </div>')
foot = between(src, '<p class="lbFoot">', '</p>', '</p>')
chal = between(src, '<div class="ldChallenge">', '\n        </div>', '\n        </div>')
play = '<button type="button" class="button green ldPlay">Play daily challenge</button>'
script = between(src, 'function buildGameBar(host, onPick) {', '  document.addEventListener("DOMContentLoaded", function () {\n    buildGameBar(')
n = [0]
def abar():
    n[0] += 1
    return bar.replace('id="ldFilter"', 'id="bar%d"' % n[0])
def seam(heads):
    if not heads: return '<div class="labseam"></div>'
    if len(heads) == 1: return '<div class="labseam"><span class="pophead ttl" style="left:556px">%s</span></div>' % heads[0]
    return '<div class="labseam"><span class="pophead ttl" style="left:274px">%s</span><span class="pophead ttl" style="left:838px">%s</span></div>' % tuple(heads)
def card(inner): return '<div class="cardB">%s</div>' % inner
def tile(inner, cap=None): return '<div class="tileB">%s%s</div>' % ('<div class="cap">%s</div>' % cap if cap else '', inner)
def cols(a, b): return '<div class="cols">%s%s</div>' % (a, b)
V = []
V.append(("As the page has it", "Two heads in the seam, one game bar for both, two white cards with the table and the deal inside. The bar's reach is not obvious: each head owns a column, and the bar sits between the heads and their content.",
  seam(["Leaderboard", "Daily deal"]) + abar() + cols(card(board), card(deal))))
V.append(("Tiles, not cards", "The same heads and bar, but the table and the deal are tiles in their own right: the tile shell the game tiles wear (20px squircle, the edge ring, the lift), no white card around a grey panel. The leaderboard's header row and the deal's trophy strip take the grey.",
  seam(["Leaderboard", "Daily deal"]) + abar() + cols(tile(rows + foot), tile(chal + play))))
V.append(("One head, one bar, two captioned tiles", "One seam head for the pair, so the bar under it plainly serves both. Each tile then names itself in a caption strip, where the head used to be.",
  seam(["Leaderboard and daily deal"]) + abar() + cols(tile(rows + foot, "Leaderboard"), tile(chal + play, "Daily deal"))))
V.append(("One tile, the bar on top", "One seam head and one wide tile. The bar is the tile's own top row and the two halves sit under it with a line between them, so the bar can only mean one thing.",
  seam(["Leaderboard and daily deal"]) + '<div class="tileB onetile">' + abar() + '<div class="panes"><div class="pane">' + rows + foot + '</div><div class="vline"></div><div class="pane">' + chal + play + '</div></div></div>'))
V.append(("The bar is the head", "No head at all: the picked game names the section. The rule stays as the section's edge, the bar sits where a head would, and the two tiles carry captions.",
  seam([]) + abar() + cols(tile(rows + foot, "Leaderboard"), tile(chal + play, "Daily deal"))))
V.append(("Each its own bar", "The other way to be unambiguous: two heads, two tiles, and each tile carries its own bar in its top row. Nothing is shared, so nothing is unclear, at the cost of two bars.",
  seam(["Leaderboard", "Daily deal"]) + cols('<div class="tileB"><div class="inbar">' + abar() + '</div>' + rows + foot + '</div>', '<div class="tileB"><div class="inbar">' + abar() + '</div>' + chal + play + '</div>')))

LAB_CSS = u"""
<style>
  body.clublab { padding: 28px 24px 120px !important; background: #f9f6f2 !important; }
  .clublab h1 { font-size: 22px; margin: 0 0 6px; font-family: "BuloRounded", Verdana, sans-serif; }
  .clublab p.note { font-size: 13px; color: #8a857c; margin: 0 0 18px; max-width: 1000px; line-height: 1.55; }
  .clublab p.note b { color: #141414; }
  .vcard { background: #fff; border-radius: 14px; corner-shape: squircle;
    box-shadow: 0 0 0 1px #e4e0d9, 0 1px 2px rgba(60,45,25,.05), 0 3px 8px rgba(60,45,25,.09);
    padding: 15px 17px 20px; margin: 0 0 18px; max-width: 1160px; }
  .vcard h3 { font-size: 15px; margin: 0 0 3px; font-family: "BuloRounded", Verdana, sans-serif; }
  .vcard .vnote { font-size: 12.5px; color: #8a857c; margin: 0 0 14px; line-height: 1.5; max-width: 940px; }
  /* the stage is the page's column on the page's canvas */
  .clublab .lobbyscope { padding: 0; margin: 0; max-width: none; min-height: 0; }
  /* the page's .lobbyscope rules give it a min-height and no padding; the stage overrides them */
  .clublab .stage.lobbyscope { width: 1112px; padding: 24px 24px 32px; margin: 0 -24px; min-height: 0; background: var(--canvas, #f9f6f2); box-sizing: content-box; }
  /* a plain seam: the rule with the head standing in a gap of paper, 48px to the content as on the page (the suits are left out here) */
  .labseam { position: relative; height: 14px; margin: 0 0 48px; }
  .labseam::before { content: ""; position: absolute; left: -24px; right: -24px; top: 6.5px; height: 1px; background: #c9c0ae; }
  .labseam .ttl { position: absolute; top: 50%; transform: translate(-50%, -50%); margin: 0; font-size: 26px; line-height: 26px; padding: 0 14px; background: var(--canvas, #f9f6f2); white-space: nowrap; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .stage > .otFilter { margin: 0 0 16px; }
  /* the page's white card */
  .cardB { display: flex; flex-direction: column; padding: 12px; background: #fff; border-radius: 20px; corner-shape: squircle; box-shadow: var(--btnshadow); }
  .cardB .lobbyBoardCard, .cardB .lobbyDealCard { padding: 0; box-shadow: none; border-radius: 0; }
  /* the tile: the game tiles' own shell, and the table or the deal as its body */
  .tileB { display: flex; flex-direction: column; background: #fff; border-radius: 20px; corner-shape: squircle; overflow: hidden;
    box-shadow: inset 0 0 0 1px var(--edge, var(--panelline)), var(--liftshadow); }
  .tileB .cap { padding: 8px 12px; font-size: 16px; line-height: 24px; font-weight: bold; color: #212529; background: var(--canvas, #f9f6f2); border-bottom: 1px solid var(--edge, var(--panelline)); }
  .tileB .lbRows { border: 0; border-radius: 0; margin: 0; }
  .tileB .lbFoot { padding: 8px 12px 10px; }
  .tileB .ldChallenge { margin: 0; }
  .tileB .ldPanel { border: 0; border-radius: 0; background: #fff; }
  .tileB .ldAward { margin: 0; padding: 4px 12px 0; height: 56px; background: var(--canvas, #f9f6f2); }
  .tileB .ldAward .ldAwardBars { left: 12px; right: 12px; bottom: 8px; }
  .tileB .ldCal { border-radius: 0; }
  .tileB .ldCalHead { background: var(--canvas, #f9f6f2); }
  .tileB .ldPlay { width: calc(100% - 24px); margin: 12px; }
  /* one tile with the bar as its top row and two panes under it */
  .tileB.onetile { padding: 12px; overflow: visible; }
  .tileB.onetile .otFilter { margin: 0 0 12px; }
  .panes { display: grid; grid-template-columns: 1fr 1px 1fr; gap: 12px; }
  .vline { background: var(--edge, var(--panelline)); }
  .pane { display: flex; flex-direction: column; }
  .onetile .lbRows { border: 1px solid var(--edge, var(--panelline)); border-radius: var(--radius-md, 6px); }
  .onetile .lbFoot { padding: 4px 0 0; }
  .onetile .ldPanel { border: 1px solid var(--edge, var(--panelline)); border-radius: var(--radius-md, 6px); background: var(--canvas, #f9f6f2); }
  .onetile .ldAward { background: none; height: 48px; padding: 0 8px; margin-bottom: 8px; }
  .onetile .ldAward .ldAwardBars { left: 8px; right: 8px; bottom: 4px; }
  .onetile .ldCalHead { background: none; }
  .onetile .ldPlay { width: 100%; margin: 8px 0 0; }
  /* each tile with its own bar in its top row */
  .tileB .inbar { padding: 12px 12px 0; }
  .tileB .inbar .otFilter { margin: 0 0 12px; }
</style>
"""
parts = ['<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Leaderboard and daily deal &middot; six ways</title>\n',
  styles, LAB_CSS, '</head>\n<body class="%s clublab">\n' % body_class,
  '<h1>Leaderboard and daily deal &middot; six ways</h1>\n<p class="note">The page has two heads in the seam, one game bar under them and two white cards. Holger on 5 September: the table and the deal could be tiles of their own, without the white card around them, and a shared bar under two separate heads reads oddly. Six arrangements below, all built from the page\'s own markup, styles and bar script. The seams here are plain rules with the head in a gap; the suits are left out.</p>\n']
for i, (t, note, html) in enumerate(V, 1):
    parts.append('<div class="vcard" id="v%d"><h3>%d &middot; %s</h3><p class="vnote">%s</p><div class="stage lobbyscope">%s</div></div>\n' % (i, i, t, note, html))
parts.append('<script>\n' + script + '\n  document.addEventListener("DOMContentLoaded", function () { document.querySelectorAll(".otFilter").forEach(function (h) { buildGameBar(h, function () {}); }); });\n</script>\n</body>\n</html>\n')
out = "".join(parts)
io.open(os.path.join(D, "leaderboard-deal-lab.html"), "w", encoding="utf-8").write(out)
print("wrote leaderboard-deal-lab.html", len(out), "chars;", len(V), "variants")
