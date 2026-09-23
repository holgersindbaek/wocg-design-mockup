// Builds elements that match each recoloured rule on the dev game page and reads what they draw, flag on and off.
const { chromium } = require('/Users/holgersindbaek/.npm/_npx/705bc6b22212b352/node_modules/playwright');
const BASE = 'https://dev.worldofcardgames.com';
function probePage() {
  const root = document.createElement('div');
  root.id = 'wmProbe';
  root.style.cssText = 'position:absolute;left:-2000px;top:0;width:600px';
  const main = document.getElementById('mainContainer') || document.body;
  main.appendChild(root);
  const add = (html, parent) => { const d = document.createElement('div'); d.innerHTML = html; const el = d.firstElementChild; (parent || root).appendChild(el); return el; };
  const file = (el, pseudo) => { const m = /url\("?([^")]*)"?\)/.exec(getComputedStyle(el, pseudo || null).backgroundImage); return m ? m[1].replace(/.*\/assets\//, '').replace(/\?.*/, '') : 'none'; };
  const css = (el, prop, pseudo) => getComputedStyle(el, pseudo || null)[prop];
  const out = {};
  // images drawn by CSS
  out.hintArrow = file(add('<div class="piece hint-suggested-hiding"></div>'), '::before');
  out.hintArrowUp = file(add('<div class="piece hint-suggested-hiding-below"></div>'), '::before');
  out.sortChip = file(add('<div class="piece chip left"></div>'));
  out.crownChip = file(add('<div class="piece chip spotPrefix-support"></div>'));
  out.likedChip = file(add('<div class="piece chip spotPrefix-playerLiked"></div>'));
  out.moreTab = file(add('<div class="piece chip spotPrefix-playerMore"></div>'), '::before');
  out.leavingChip = file(add('<div class="piece chip spotPrefix-leaving"></div>'));
  out.dealer = file(add('<div class="piece chip spotPrefix-dealerChip"></div>'));
  out.rays = file(add('<div class="piece spotPrefix-handOverBackground"></div>'), '::after');
  out.sun = file(add('<div class="piece spot-shotImage sun"></div>'));
  out.moon = file(add('<div class="piece spot-shotImage moon"></div>'));
  out.slam = file(add('<div class="piece spot-shotImage slam"></div>'));
  out.hintSeat = file(add('<div class="piece button spotPrefix-hintButton"></div>'));
  out.chatSeatOpen = file(add('<div class="piece button spotPrefix-chatButton active"></div>'));
  const pill = add('<div class="chromePill"><div class="pillCell tableCell active"></div><div class="pillCell leaveCell"></div></div>');
  out.tablePillOpen = file(pill.children[0]); out.leavePill = file(pill.children[1], '::before');
  const modal = add('<div class="wmModal"><span class="playerBadge isLiked"></span><span class="playerBadge isBot"></span><span class="completionBadge"></span><span class="completionBadge is100"></span><div class="ldAwardBar isGold"><span class="ldAwardBadge"></span></div></div>');
  out.likedBadge = file(modal.children[0]); out.botBadge = file(modal.children[1]); out.cleanMeld = file(modal.children[2]); out.highRep = file(modal.children[3]);
  out.goldTrophy = file(modal.querySelector('.ldAwardBadge'));
  let tlb = document.getElementById('tableListingsBox'), made = false;
  if (!tlb) { tlb = add('<div id="tableListingsBox"></div>'); made = true; }
  const opt = add('<div class="wmProbeTlb tableListingsBoxContent"><div class="tableListings"><div class="tableListing"><div class="content"><div class="contentMiddle"><span class="option"></span><span class="option active"></span></div></div></div></div></div>', tlb);
  out.tickOff = file(opt.querySelectorAll('.option')[0]); out.tickOn = file(opt.querySelectorAll('.option')[1]);
  opt.remove(); if (made) tlb.remove();
  // colours drawn in code
  const timer = add('<div class="piece spotPrefix-timer"><svg><circle></circle></svg></div>');
  const timerRed = add('<div class="piece spotPrefix-timer red"><svg><circle></circle></svg></div>');
  const num = add('<div class="piece spotPrefix-timerText"></div>');
  out.timer = [css(timer, 'backgroundColor'), (/inset[^,]*|rgb\([^)]*\) 0px 0px 0px 4px inset/.exec(css(timer, 'boxShadow')) || [''])[0], css(timer.querySelector('circle'), 'stroke'), css(num, 'color')].join(' | ');
  out.timerRed = [css(timerRed, 'backgroundColor'), (/rgb\([^)]*\) 0px 0px 0px 4px inset/.exec(css(timerRed, 'boxShadow')) || [''])[0], css(timerRed.querySelector('circle'), 'stroke')].join(' | ');
  const game = document.body.getAttribute('data-active-game');
  document.body.setAttribute('data-active-game', 'canasta');
  const tab = add('<div class="piece spot-cardText1"></div>'), wild = add('<div class="piece spot-cardText2" data-has-wild-card="true"></div>');
  const only = add('<div class="piece spot-cardText3" data-has-only-wild-card="true"></div>');
  const star = add('<div class="piece spot-cardText4" data-is-canasta="true"><svg><path class="canastaCompleteStarPath"></path></svg></div>');
  const starWild = add('<div class="piece spot-cardText5" data-is-canasta="true" data-has-wild-card="true"><svg><path class="canastaCompleteStarPath"></path></svg></div>');
  out.countTab = css(tab, 'color') + ' on ' + css(tab, 'backgroundColor');
  out.countTabWild = css(wild, 'color') + ' on ' + css(wild, 'backgroundColor');
  out.countTabOnlyWild = css(only, 'color') + ' on ' + css(only, 'backgroundColor');
  out.canastaStar = css(star.querySelector('path'), 'fill') + ' on ' + css(star, 'backgroundColor');
  out.canastaStarWild = css(starWild.querySelector('path'), 'fill') + ' on ' + css(starWild, 'backgroundColor');
  if (game === null) document.body.removeAttribute('data-active-game'); else document.body.setAttribute('data-active-game', game);
  const drop = document.querySelector('#userBar .friendsIcon .friendsDropdown');
  if (drop) {
    const fr = add('<div class="friendItem"><button class="friendMessageBtn"><svg></svg><span class="unreadBadge hasBubble">2</span></button><button class="friendInviteBtn"><svg></svg></button><button class="friendInviteBtn invited"><svg class="inviteSuccessIcon"></svg></button></div>', drop);
    const more = add('<div class="wmProbeFriends"><button class="friendsSearchBtn"><svg></svg></button><button class="conversationBack"></button><button class="conversationSendBtn"><svg></svg></button><button class="conversationSendBtn" disabled><svg></svg></button></div>', drop);
    const [msg, inv, sent] = fr.children;
    out.message = css(msg, 'backgroundColor') + ' ring ' + css(msg, 'boxShadow') + ' glyph ' + css(msg.querySelector('svg'), 'fill') + ' corner ' + (css(msg, 'cornerShape') || 'n/a');
    out.unreadDot = css(msg.querySelector('.unreadBadge'), 'backgroundColor');
    out.invite = css(inv, 'backgroundColor') + ' glyph ' + css(inv.querySelector('svg'), 'color');
    out.inviteSent = css(sent, 'backgroundColor') + ' glyph ' + css(sent.querySelector('svg'), 'color');
    out.search = css(more.children[0], 'backgroundColor') + ' glyph ' + css(more.children[0].querySelector('svg'), 'fill');
    out.back = css(more.children[1], 'backgroundColor');
    out.send = css(more.children[2], 'backgroundColor') + ' glyph ' + css(more.children[2].querySelector('svg'), 'fill');
    out.sendOff = css(more.children[3], 'backgroundColor') + ' glyph ' + css(more.children[3].querySelector('svg'), 'fill');
    fr.remove(); more.remove();
  } else out.friends = 'no friends dropdown on the page';
  const stars = add('<div class="gameRatingStar"><svg><path class="gameRatingStarEmptyPath"></path><path class="gameRatingStarFullPath"></path></svg></div>');
  out.rateStars = css(stars.querySelector('.gameRatingStarEmptyPath'), 'fill') + ' / ' + css(stars.querySelector('.gameRatingStarFullPath'), 'fill');
  const ok = add('<div class="wmSettings"><div class="wmFormHost"><div class="successRow visible"><svg class="successTick"></svg>Saved</div></div></div>');
  out.successLine = css(ok.querySelector('.successRow'), 'color') + ' tick ' + css(ok.querySelector('.successTick'), 'verticalAlign');
  root.remove();
  return out;
}
(async () => {
  const b = await chromium.launch();
  const res = {};
  try {
    for (const flag of ['1', '0']) {
      const ctx = await b.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1440, height: 900 } });
      const p = await ctx.newPage();
      await p.goto(BASE + '/hearts?lobby=' + flag, { waitUntil: 'domcontentloaded', timeout: 90000 });
      await p.waitForTimeout(5000);
      res[flag] = await p.evaluate(probePage);
      await ctx.close();
    }
  } finally { await b.close(); }
  for (const k of Object.keys(res['1'])) console.log(k.padEnd(18), 'ON ', res['1'][k], '\n' + ''.padEnd(18), 'OFF', res['0'][k]);
})();
