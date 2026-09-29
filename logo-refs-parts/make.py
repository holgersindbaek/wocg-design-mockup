#!/usr/bin/env python3
"""Logos to learn from.

Holger, 25 Sep 2026, after picking B1 (the title face on both lines, the words at 85% of the fan): "I kind of
want to try out different classic and interesting fonts. Maybe we should start by trying to look at different
well-designed logos and classic logos to see how they accomplish something iconic. Maybe you can make a
collection of such icons?"

This writes ../logo-references.html: a board of logos that solved the problems ours has (a small line over a big
line, a mark beside warm words, card and game brands, type that is the brand), each drawn at 64px and at our
bar's 32px, with one sentence on what makes it work and one on what it says for us. It ends with the lessons
in one place and a strip of faces to try next, drawn live in "World of / Card Games".

The logo files come from Wikipedia: each brand's article names its logo in the infobox, and the file is fetched
once into ../logo-refs/. They are other people's trademarks, here for study only.

    python3 logo-refs-parts/make.py            build (fetches only what is missing)
    python3 logo-refs-parts/make.py --refetch  fetch every logo again
"""
import base64
import json
import re
import sys
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REFS = ROOT / 'logo-refs'
WOCG = Path('/Users/holgersindbaek/CloudDrive/HolgerSindbaek/WorldOfCardGames/Programming/wocg/worldofcardgames')
UA = {'User-Agent': 'wocg-logo-lab/1.0 (design research; holger@worldofcardgames.com)'}

# ---------------------------------------------------------------------------------------------------------------
# the board: slug, article, an explicit file when the article's own is wrong, and the two sentences
# ---------------------------------------------------------------------------------------------------------------

LESSONS = [
    ('world', '“World of”, and other game names in a stack',
     'Ours is not the first name that starts with a small "World of". These put the small words over the big name and let the game word take the size.'),
    ('stack', 'A small line over a big line',
     'Classic brands with two or three words in a stack. Look at how much smaller the small line is, how the lines line up, and whether a shape holds them.'),
    ('warm', 'A mark beside warm words',
     'Brands whose words are a soft or classic serif next to a small drawn mark. This is the family B1 belongs to.'),
    ('cards', 'Card and game brands',
     'What the card makers and the game sites did with the same subject.'),
    ('type', 'The type is the brand',
     'Logos where one face, well set, is the whole identity. The face gives the character; nothing else is needed.'),
    ('three', 'For the three directions',
     'Added 25 Sep for the three families the logo lab keeps: words on an arc, letters on cards, and the small things that make a plain wordmark a logo.'),
    ('faces', 'Small figures that work small',
     'Added 27 Sep for the illustrator: marks that are a face or a figure and still read at a favicon\u2019s size. What they share: one silhouette, two or three flat colours, and the mood carried by the mouth or the eyes.'),
    ('flow', 'The words as a continuation of the mark',
     'Added 29 Sep, after Holger\u2019s own logo (Q1 and Q2 in the logo lab), where the words fall from the front card on a bowl. Famous logos where the words carry on the mark, in four kinds: the words lean or run with the mark\u2019s motion (Nike to Balatro), the words sit on the mark\u2019s curve (Amazon to Pringles), the words are inside the mark\u2019s shape (Hot Wheels to Pizza Hut), and a letter is the mark (Goodwill to Hearthstone). The first kind is the closest to Q1.'),
]

BRANDS = [
    # -- world -------------------------------------------------------------------------------------------------
    dict(slug='world-of-warcraft', lesson='world', name='World of Warcraft (Classic)', article='World of Warcraft', file='World of Warcraft Classic logo.png'),
    dict(slug='world-of-tanks', lesson='world', name='World of Tanks Blitz', article='World of Tanks', file='WoT Blitz Logo.png'),
    dict(slug='wsop', lesson='world', name='World Series of Poker', article='World Series of Poker'),
    dict(slug='wpt', lesson='world', name='World Poker Tour', article='World Poker Tour'),
    dict(slug='disney-world', lesson='world', name='Walt Disney World', article='Walt Disney World', file='Walt Disney World Resort logo.svg'),
    dict(slug='wwf', lesson='world', name='WWF', article='World Wide Fund for Nature', file='WWF logo.svg'),
    # -- stack -------------------------------------------------------------------------------------------------
    dict(slug='land-rover', lesson='stack', name='Land Rover', article='Land Rover'),
    dict(slug='whole-foods', lesson='stack', name='Whole Foods Market', article='Whole Foods Market'),
    dict(slug='north-face', lesson='stack', name='The North Face', article='The North Face', file='The North Face logo.svg'),
    dict(slug='natgeo', lesson='stack', name='National Geographic', article='National Geographic', file='Natgeologo.svg'),
    dict(slug='barnes-noble', lesson='stack', name='Barnes & Noble', article='Barnes & Noble', file='Barnes & Noble logo.svg'),
    dict(slug='trader-joes', lesson='stack', name="Trader Joe's", article="Trader Joe's", file="Trader Joe's Logo.svg"),
    dict(slug='ben-jerrys', lesson='stack', name="Ben & Jerry's", article="Ben & Jerry's", file="Ben & Jerry's logo.svg"),
    dict(slug='sports-illustrated', lesson='stack', name='Sports Illustrated', article='Sports Illustrated', file='Sports Illustrated logo.svg'),
    dict(slug='dunkin', lesson='stack', name="Dunkin'", article="Dunkin'", file="Dunkin' logo.svg"),
    dict(slug='burger-king', lesson='stack', name='Burger King', article='Burger King'),
    dict(slug='levis', lesson='stack', name="Levi's", article='Levi Strauss & Co.', file="Levi's logo.svg"),
    dict(slug='home-depot', lesson='stack', name='The Home Depot', article='The Home Depot', file='TheHomeDepot.svg'),
    # -- warm --------------------------------------------------------------------------------------------------
    dict(slug='penguin', lesson='warm', name='Penguin Books', article='Penguin Books'),
    dict(slug='mailchimp', lesson='warm', name='Mailchimp', article='Mailchimp'),
    dict(slug='etsy', lesson='warm', name='Etsy', article='Etsy'),
    dict(slug='chobani', lesson='warm', name='Chobani', article='Chobani', file='Chobani logo.svg'),
    dict(slug='medium', lesson='warm', name='Medium', article='Medium (website)'),
    dict(slug='haagen-dazs', lesson='warm', name='Häagen-Dazs', article='Häagen-Dazs'),
    dict(slug='tiffany', lesson='warm', name='Tiffany & Co.', article='Tiffany & Co.', file='Tiffany & Co. logo.svg'),
    dict(slug='new-yorker', lesson='warm', name='The New Yorker', article='The New Yorker', file='The New Yorker logo.svg'),
    dict(slug='warby-parker', lesson='warm', name='Warby Parker', article='Warby Parker', file='Warby Parker logo.svg'),
    dict(slug='twinings', lesson='warm', name='Twinings', article='Twinings', file='Twinings logo.svg'),
    dict(slug='guinness', lesson='warm', name='Guinness', article='Guinness'),
    dict(slug='bass', lesson='warm', name='Bass', article='Bass Brewery'),
    dict(slug='lonely-planet', lesson='warm', name='Lonely Planet', article='Lonely Planet', file='Lonely Planet.svg'),
    # -- cards (Bicycle has no logo file on Wikipedia) -------------------------------------------------------
    dict(slug='cartamundi', lesson='cards', name='Cartamundi', article='Cartamundi', file='Cartamundi logo.svg'),
    dict(slug='piatnik', lesson='cards', name='Piatnik', article='Piatnik', file='Piatnik logo.svg'),
    dict(slug='uno', lesson='cards', name='Uno', article='Uno (card game)'),
    dict(slug='ravensburger', lesson='cards', name='Ravensburger', article='Ravensburger'),
    dict(slug='hasbro', lesson='cards', name='Hasbro', article='Hasbro'),
    dict(slug='nintendo', lesson='cards', name='Nintendo', article='Nintendo', file='Nintendo.svg'),
    dict(slug='chess-com', lesson='cards', name='Chess.com', article='Chess.com', file='Chess.com Logo.svg'),
    dict(slug='lichess', lesson='cards', name='Lichess', article='Lichess'),
    dict(slug='pokerstars', lesson='cards', name='PokerStars', article='PokerStars', file='PokerStars logo.svg'),
    dict(slug='pogo', lesson='cards', name='Pogo', article='Pogo.com', file='Pogo.com logo.svg'),
    dict(slug='mattel', lesson='cards', name='Mattel', article='Mattel'),
    # -- type --------------------------------------------------------------------------------------------------
    dict(slug='coca-cola', lesson='type', name='Coca-Cola', article='Coca-Cola', file='Coca-Cola logo.svg'),
    dict(slug='ford', lesson='type', name='Ford', article='Ford Motor Company', file='Ford logo flat.svg'),
    dict(slug='kelloggs', lesson='type', name="Kellogg's", article="Kellogg's", file="Kellogg's-Logo.svg"),
    dict(slug='vogue', lesson='type', name='Vogue', article='Vogue (magazine)', file='Vogue logo.svg'),
    dict(slug='wells-fargo', lesson='type', name='Wells Fargo', article='Wells Fargo'),
    dict(slug='easyjet', lesson='type', name='easyJet', article='EasyJet', file='EasyJet logo.svg'),
    dict(slug='sony', lesson='type', name='Sony', article='Sony', file='Sony logo.svg'),
    dict(slug='ibm', lesson='type', name='IBM', article='IBM', file='IBM logo.svg'),
    # -- three -------------------------------------------------------------------------------------------------
    dict(slug='harley', lesson='three', name='Harley-Davidson', article='Harley-Davidson'),
    dict(slug='budweiser', lesson='three', name='Budweiser', article='Budweiser'),
    dict(slug='hollister', lesson='three', name='Hollister Co.', article='Hollister Co.'),
    dict(slug='cah', lesson='three', name='Cards Against Humanity', article='Cards Against Humanity'),
    dict(slug='scrabble', lesson='three', name='Scrabble', article='Scrabble'),
    dict(slug='amazon', lesson='three', name='Amazon', article='Amazon (company)'),
    dict(slug='fedex', lesson='three', name='FedEx', article='FedEx'),
    dict(slug='gillette', lesson='three', name='Gillette', article='Gillette'),
    # -- faces -------------------------------------------------------------------------------------------------
    dict(slug='tocaboca', lesson='faces', name='Toca Boca', article='Toca Boca'),
    dict(slug='duolingo', lesson='faces', name='Duolingo', article='Duolingo'),
    dict(slug='pringles', lesson='faces', name='Pringles', article='Pringles'),
    dict(slug='wendys', lesson='faces', name="Wendy's", article="Wendy's"),
    dict(slug='reddit', lesson='faces', name='Reddit', article='Reddit', file='Reddit Logo Icon.svg'),
    dict(slug='twitterbird', lesson='faces', name='Twitter (2012)', article='Twitter', file='Logo of Twitter.svg'),
    dict(slug='michelin', lesson='faces', name='Michelin', article='Michelin'),
    dict(slug='kfc', lesson='faces', name='KFC', article='KFC', file='KFC logo.svg'),
    # -- flow (added 29 Sep): the words carry on the mark; `use` draws another card's file again ---------------
    # A: the words lean or run with the mark's motion
    dict(slug='nike', lesson='flow', name='Nike (1978)', article='Nike, Inc.', file='Nike logo 1978.svg'),
    dict(slug='puma', lesson='flow', name='Puma', article='Puma (brand)'),
    dict(slug='pepsi-1991', lesson='flow', name='Pepsi (1991)', article='Pepsi', file='Pepsi bi (1991).svg'),
    dict(slug='nascar', lesson='flow', name='NASCAR', article='NASCAR'),
    dict(slug='f1-old', lesson='flow', name='Formula 1 (1994)', article='Formula One', file='F1 logo.svg'),
    dict(slug='reebok', lesson='flow', name='Reebok', article='Reebok', file='Reebok 2019 logo.svg'),
    dict(slug='adidas', lesson='flow', name='Adidas', article='Adidas', file='Adidas Logo.svg'),
    dict(slug='speedo', lesson='flow', name='Speedo', article='Speedo'),
    dict(slug='greyhound', lesson='flow', name='Greyhound', article='Greyhound Lines'),
    dict(slug='twitter-2010', lesson='flow', name='Twitter (2010)', article='Twitter', file='Twitter 2010 logo.svg'),
    dict(slug='walmart', lesson='flow', name='Walmart', article='Walmart', file='Walmart logo.svg'),
    dict(slug='balatro', lesson='flow', name='Balatro', article='Balatro', file='Balatro (2023) logo black (SGDB 108829).png'),
    # B: the words sit on the mark's curve
    dict(slug='amazon-flow', lesson='flow', name='Amazon', use='amazon'),
    dict(slug='coca-cola-flow', lesson='flow', name='Coca-Cola', use='coca-cola'),
    dict(slug='skittles', lesson='flow', name='Skittles', article='Skittles (confectionery)'),
    dict(slug='sunkist', lesson='flow', name='Sunkist', article='Sunkist Growers, Incorporated'),
    dict(slug='paramount', lesson='flow', name='Paramount', article='Paramount Pictures', file='Paramount Pictures 2022 (Blue).svg'),
    dict(slug='crayola', lesson='flow', name='Crayola', article='Crayola'),
    dict(slug='dreamworks', lesson='flow', name='DreamWorks', article='DreamWorks Animation'),
    dict(slug='pringles-flow', lesson='flow', name='Pringles', use='pringles'),
    # C: the words inside the mark's shape
    dict(slug='hot-wheels', lesson='flow', name='Hot Wheels', article='Hot Wheels'),
    dict(slug='chupa-chups', lesson='flow', name='Chupa Chups', article='Chupa Chups'),
    dict(slug='lays', lesson='flow', name="Lay's", article="Lay's"),
    dict(slug='uno-flow', lesson='flow', name='Uno', use='uno'),
    dict(slug='burger-king-flow', lesson='flow', name='Burger King', use='burger-king'),
    dict(slug='pizza-hut', lesson='flow', name='Pizza Hut', article='Pizza Hut'),
    dict(slug='hearthstone', lesson='flow', name='Hearthstone', article='Hearthstone', file='Hearthstone 2016 logo.png'),
    # D: a letter is the mark
    dict(slug='goodwill', lesson='flow', name='Goodwill', article='Goodwill Industries'),
    dict(slug='gatorade', lesson='flow', name='Gatorade', article='Gatorade'),
    dict(slug='goodyear', lesson='flow', name='Goodyear', article='Goodyear Tire and Rubber Company'),
    dict(slug='tostitos', lesson='flow', name='Tostitos', article='Tostitos'),
    dict(slug='seven-eleven', lesson='flow', name='7-Eleven', article='7-Eleven'),
    dict(slug='toys-r-us', lesson='flow', name='Toys "R" Us', article='Toys "R" Us'),
    dict(slug='tour-de-france', lesson='flow', name='Tour de France', article='Tour de France', file='Tour de France logo.svg'),
    dict(slug='vans', lesson='flow', name='Vans', article='Vans'),
    dict(slug='subway', lesson='flow', name='Subway', article='Subway (restaurant)'),
]

# the two sentences per logo, written after the logos were seen; a missing entry shows the card with no words
def W(works, us):
    return dict(works=works, us=us)


WORDS = {
    'world-of-warcraft': W('WORLD in small capitals with OF tucked into it, over the big carved WARCRAFT. The small line is about half the big one, and it is plainer.',
                           'The plainest logo on this board is still the closest to our name. Note that the small line is plain where the big one is drawn.'),
    'world-of-tanks': W('WORLD OF TANKS as one small line over BLITZ in the same heavy condensed face, the shield above. The small line is about 40% of the big one.',
                        'One face in two sizes is enough when the two sizes differ a lot.'),
    'wsop': W('Four words in a stack, POKER the biggest, the small words in red so they read as a label, and the four suits as a base line.',
              'The game word takes the size. The small words can take a second colour instead of more height.'),
    'wpt': W('One tilted card and three letters. The full name is gone.',
             'Not our route: our name is the brand. But one card, drawn simply, reads at any size.'),
    'disney-world': W('A script Walt Disney over WORLD in plain capitals, with RESORT small under. The script has the character, the plain word does the reading.',
                      'Only one line should perform. The other stays plain.'),
    'wwf': W('The panda does the work. The three letters under it are small and plain.',
             'A strong mark lets the words shrink. That is the family you chose at 85%: the fan leads.'),
    'land-rover': W('Two words in the same capitals inside an oval. The oval makes the two lines one shape, and the shape is the mark.',
                    'A frame turns a stack into one object. We have a mark beside the words instead; a frame would be a bigger change.'),
    'whole-foods': W('WHOLE over FOODS in the same capitals, MARKET small under them, all in a green disc. The small word is about a third of the big ones.',
                     'A small word at a third reads as a label, not as a second title.'),
    'north-face': W('THE, NORTH and FACE in equal condensed capitals against the half dome, which is exactly as tall as the three lines.',
                    'Mark and words at one height read as one thing. B1 at 100% was this; you preferred the fan bigger, which is the WWF way.'),
    'natgeo': W('The yellow frame is the mark. NATIONAL and GEOGRAPHIC stand beside it in two lines of plain capitals, as tall as the frame.',
                'A mark that is a simple shape stays sharp at 16px. The fan cannot; a flat fan or one card could.'),
    'barnes-noble': W('One line of green serif capitals with a lighter ampersand and no mark: the voice of an old bookshop.',
                      'Spaced serif capitals read as established. It is B1 in capitals, which you found less cozy.'),
    'trader-joes': W('A chunky red serif with wide letters and no mark. The face alone says friendly and old-fashioned.',
                     'A soft slab or a fat serif carries warmth without a mark.'),
    'ben-jerrys': W('Bubbly hand-drawn letters on an arch inside a frame: the whole thing is one drawn object.',
                    'Hand-drawn warmth is a big commitment, and it does not shrink well. See the second plate.'),
    'sports-illustrated': W('Two words in a heavy slab serif, left-aligned, the second word wider. The block is the mark.',
                            'Two lines of different length that share a left edge still read as one block, which is what your sketch does.'),
    'dunkin': W('One word in fat rounded letters in two colours. The rebrand dropped Donuts and kept the voice.',
                'Rounded heavy letters are the cozy version of a sans, near Bulo Rounded’s territory.'),
    'burger-king': W('The words are the filling of a bun. The mark holds the two lines.',
                     'The 2020 logo went back to the 1969 one: flat, no gloss, round letters. The move a flat fan would make.'),
    'levis': W('The batwing holds the word, white on red. Shape and word are one.',
               'A coloured shape behind the words is the loudest option. The bar’s paper would not like it.'),
    'home-depot': W('A tilted square with stencil letters in a stack: hardware, not fashion.',
                    'The stack fits a square, which is what an app icon wants.'),
    'penguin': W('The penguin in an oval, drawn with the fewest lines that still say penguin, above PENGUIN in Gill Sans capitals.',
                 'A mark cut down to its silhouette reads at every size. The fan could be cut down the same way: fewer cards, no shadow.'),
    'mailchimp': W('Freddie’s head beside mailchimp in Cooper Light lowercase. A soft serif, lowercase and a friendly animal: cozy by every choice.',
                   'The closest cousin to what you liked in B1: a soft serif in lowercase beside a mark a little taller than the word.'),
    'etsy': W('One word in a soft heavy serif in orange. Rounded, friendly letter shapes.',
              'Warmth from the face alone. Our band wants a darker ink, but the face lesson stands.'),
    'chobani': W('CHOBANI in a custom serif with wide letters and light strokes, drawn to feel like old grocery lettering.',
                 'Wide light serif capitals feel cozy where narrow heavy ones feel formal. If capitals, this is the direction.'),
    'medium': W('Medium in a heavy display serif with strong contrast: bookish and modern at once.',
                'The heaviest serif on the board. At 32px it still reads because the counters stay open.'),
    'haagen-dazs': W('The name in a serif with a crown inside a burgundy frame: invented European heritage, and it works.',
                     'A frame plus a serif reads as heritage. At 32px the frame eats the words.'),
    'tiffany': W('Serif capitals, wide spacing, nothing else.',
                 'Spacing is what makes capitals feel expensive. Too much and the name falls apart when small.'),
    'new-yorker': W('The Irvin letters: a face drawn for one magazine, tall capitals with a hand-cut feel.',
                    'A face that belongs to one brand is the strongest logo there is. Ours could grow that way from GLCA with a few custom letters.'),
    'warby-parker': W('Light serif capitals, widely spaced, no mark: quiet confidence.',
                      'Too light for 32px on our band. See the second plate.'),
    'twinings': W('TWININGS in lettered serif capitals with OF LONDON small under it. The small line is a fifth of the big one.',
                  'A small line under the name works for a description. World of is part of the name, so it belongs above.'),
    'guinness': W('The harp above GUINNESS in spaced capitals. The mark is bigger than the word.',
                  'Mark over word is the square lockup: a good app icon, a poor bar logo.'),
    'bass': W('A red triangle and a script name: the first registered trademark in Britain, still a shape and a word.',
              'A shape that simple survives everything. Our fan has four cards, two colours, a shadow and a gradient.'),
    'lonely-planet': W('A blue globe of lines beside lowercase words in a friendly sans.',
                       'Lowercase beside a small round mark reads relaxed.'),
    'cartamundi': W('A mark made of card shapes and a lowercase name in a rounded sans.',
                    'The biggest card maker chose a card shape as its mark and lowercase for its name. The mark is no taller than the capital C.'),
    'piatnik': W('A heavy serif name in red with a black outline, and no mark.',
                 'The outline is what keeps it readable on any ground. On the felt our words need the same, or the white version the lab makes.'),
    'uno': W('The word tilted in a red ellipse with a yellow fill. The word is the mark.',
             'Not for a three-word name. But the tilt is worth noting: our fan already tilts.'),
    'ravensburger': W('The name set along the long side of a blue triangle: one shape, one word, made for a box corner.',
                      'A mark chosen for where it lives. Ours lives in a 32px bar and a 16px tab.'),
    'hasbro': W('The name in a rounded script on a smiling blue square.',
                'Friendly through roundness and a smile. The colour does a lot.'),
    'nintendo': W('The name in rounded slab serifs inside a racetrack, the same shape since the 1970s.',
                  'A soft serif in a simple frame lasts fifty years. The letters have a Cooper feel.'),
    'chess-com': W('A pawn beside Chess.com in a heavy rounded sans with an outline. The pawn is as tall as the capital.',
                   'The nearest site to ours in kind. Mark and word are one height, the word is heavy, and the outline sits on any colour.'),
    'lichess': W('A knight drawn in one continuous outline. The name is set apart.',
                 'An outline mark in the ink with no fill reads on paper and on felt alike.'),
    'pokerstars': W('A red spade replaces the o. The name is bold and the spade is the only colour.',
                    'A suit inside the word is a trick we could borrow once: a heart for the a in Card. Try it, then probably not.'),
    'pogo': W('Four fat rounded lowercase letters. The whole brand is the word’s shape.',
              'Rounded heavy lowercase is the cozy sans route. It needs a short name.'),
    'mattel': W('The name on a red seal with a serrated edge: a toy-box sticker.',
                'The seal is the mark. The word is plain.'),
    'coca-cola': W('A Spencerian script written in 1886 and never redrawn. The shape is known before it is read.',
                   'Script is the warmest voice and the least legible at 32px.'),
    'ford': W('A script in a blue oval, both from the 1900s.',
              'Script plus frame: heritage in one shape. At 32px the script survives because the word is short.'),
    'kelloggs': W('A red script with a big K: one word, one colour.',
                  'A script World of over a plain Card Games would borrow this warmth without asking the script to carry the name.'),
    'vogue': W('A high-contrast Didone in capitals: hairlines and heavy stems.',
               'The hairlines break at small sizes. See the second plate. Bodoni 72 is on the Mac if you want it in our words.'),
    'wells-fargo': W('WELLS over FARGO in Clarendon capitals in a red square: a stagecoach-era slab serif.',
                     'Clarendon is sturdy and warm at once, worth trying as the big line. Superclarendon is on the Mac.'),
    'easyjet': W('easyJet in Cooper Black, orange, lowercase e and capital J.',
                 'Cooper Black is the fattest cozy face; Cooper Light is what Mailchimp uses. Young Serif is the free cousin.'),
    'sony': W('SONY in a Clarendon-like slab, wide and spaced, unchanged since 1973.',
              'Wide slab capitals stay legible when small because the serifs hold the letters apart.'),
    'ibm': W('Three letters in a slab serif cut into eight stripes.',
             'A treatment, not a face, makes the logo. Not our route, but the slab under the stripes is Clarendon-like too.'),
    'harley': W('The name arches over the bar of the bar-and-shield. The shield is the mark; the arch is where the words live.',
                'Words that arch over a mark read as a badge at once: 12b and 12g.'),
    'budweiser': W('A bow tie with the name curving down across it.',
                   'A downward curve reads as a smile only while it is gentle; the bow tie\u2019s is steep and reads as a ribbon. 12a keeps ours shallow.'),
    'hollister': W('HOLLISTER arched in spaced capitals over a small seagull: a surf-shop badge.',
                   'Spaced capitals on an arc are the classic label line: 12c.'),
    'cah': W('The name set inside one black playing card. The card shape does the work.',
             'For 25: a card shape can carry the whole idea. Ours carry one letter each.'),
    'scrabble': W('The name spelt on letter tiles; the tiles are the mark.',
                  '25 is the same idea with cards for tiles: the letters are the pieces.'),
    'amazon': W('A plain lowercase word with one small thing under it: the arrow that smiles from a to z.',
                'One drawn stroke under a plain word is enough to make it a logo: 1f.'),
    'fedex': W('Two bold words and an arrow hidden in the space between the E and the x.',
               'The small thing can live in the spacing itself. 1c tightens ours so the word reads as one shape.'),
    'gillette': W('A bold sans with a razor cut through the G and the i.',
                  'A single cut in a letter is a logo touch; a card corner cut into the C would be ours, if we wanted one.'),
    'tocaboca': W('A mouth, open and happy, and nothing else. The wordmark stands beside it.',
                  'The mood is the mark. A face part reads at any size; the whole figure does not have to.'),
    'duolingo': W('An owl in one green, with big eyes: a figure that is really two circles and a beak.',
                  'A figure survives small when it is built from a few round shapes. The eyes do the work.'),
    'pringles': W('A face made of a moustache, two dots and a bow: three shapes on a disc.',
                  'Character from three strokes. A joker or a king could be this spare.'),
    'wendys': W('A girl\u2019s head with red braids in a circle, lines kept thick.',
                'A drawn head works small only with thick lines and a tight silhouette.'),
    'reddit': W('An alien\u2019s head with antenna and two eyes, one orange.',
                'Two eyes and a mouth on a simple head is the pattern; the antenna is what makes it Reddit\u2019s.'),
    'twitterbird': W('A bird in one shape, built from circles, no eye.',
                     'A figure with no face still has a mood: the bird looks up. A silhouette can carry the feeling.'),
    'michelin': W('Bibendum, a man of tyres, waving, in white with dark lines.',
                  'A hundred-year-old character that still works at a corner\u2019s size because it is stacked circles.'),
    'kfc': W('The Colonel\u2019s face: glasses, goatee, bow tie, in a few red and white shapes.',
             'A real face reduced to four features. A card king or jack could be reduced the same way.'),
    # -- flow (29 Sep) ----------------------------------------------------------------------------------------
    'nike': W('Runs with the mark: NIKE in a heavy italic sits over the swoosh, and the letters lean the way the swoosh rises, so the word and the tick are one movement to the right.',
              'Q1 does the same with two lines: the words take the front card\u2019s lean. Nike gets away with one word, which is why it reads at any size; our small line is the cost of two.'),
    'puma': W('Runs with the mark: the cat leaps off the last letter of PUMA, so the word is the ground the mark springs from, and the eye follows the jump back into the word.',
              'The mark touches the word. Ours keeps a gap between the card and the C; letting the card\u2019s corner reach the words would bind them the way Puma\u2019s paw binds the A.'),
    'pepsi-1991': W('Leans with the mark: PEPSI in italic capitals stands on the red band while the globe\u2019s white wave runs under it, and the word tilts the way the wave rises.',
                    'The nearest cousin to Q1: a mark with a lean and words leaning the same way. Pepsi keeps the words on one line and lets the band do the joining.'),
    'nascar': W('Leans with the mark: the coloured bars slant at the same angle as the italic word, so the bars read as the word\u2019s first letters, motion before the name.',
                'One angle everywhere. Q1\u2019s cards lean ten degrees and the bowl leaves the card at that angle too, which is what makes the words feel dealt from the fan.'),
    'f1-old': W('The word is the mark: the F and the red speed lines make a 1 in the gap between them, and the small Formula 1 underneath sits square.',
                'The famous case of the mark and the word being one shape. Ours is a picture beside words, so the join has to come from the line the words follow, as it does in Q1.'),
    'reebok': W('The mark under the word: the vector\u2019s slanted bars run under the wordmark like a ground line, their lean pointing the way the word reads.',
                'A leaning mark below the words works as an underline. Our fan stands beside the words, so the lean has to be carried by the words themselves.'),
    'adidas': W('The mark over the word: three bars rise as a slope over lowercase adidas, and the slope\u2019s lean is the mark\u2019s whole motion, the word plain beneath it.',
                'Plain words under a leaning mark; the lean stays in the mark. Q1 puts the lean in both, which is bolder and needs the two lines to agree.'),
    'speedo': W('The word ends in the mark: the red boomerang comes out of the o and flies on to the right, so the word has a tail.',
                'A tail after the last letter is the cheapest continuation there is. It is the reverse of ours: our words come out of the mark.'),
    'greyhound': W('Runs along the word: the dog stretches at full speed over the italic script, both going the same way, the script\u2019s slant matching the dog\u2019s.',
                   'A figure running the way the words read. If a character ever replaces the fan (the P rows), by this example it should run into the words, not away from them.'),
    'twitter-2010': W('The mark takes off from the word: the bird flies up and right off the last r of twitter, so the word launches it.',
                      'The word first, the mark last. Ours is the other order, and the continuation has to run from the card into the C.'),
    'walmart': W('The word ends in the mark: the yellow spark stands where a full stop would, and its six rays pick up the word\u2019s rounded strokes.',
                 'Simple and durable, but it is a mark that follows the words; ours leads with the fan, and the spark\u2019s job falls to the card\u2019s corner.'),
    'balatro': W('The letters are the mark: BALATRO is hand-cut with the A as a spade card and the O as a card back, tilted like a held hand, so the word is a fan of cards.',
                 'A card game that made the word into cards instead of putting cards beside the word. Round 6\u2019s letter cards (rows 21 to 29) were our try at this; Holger let them go.'),
    'amazon-flow': W('Sits on the mark\u2019s curve: the orange arrow smiles from a to z under the word, so the mark is drawn by the word\u2019s own length.',
                     'The curve is under the words, not beside them. Q1\u2019s bowl is the same idea turned: the curve carries the words instead of underlining them.'),
    'coca-cola-flow': W('Sits on the mark\u2019s curve: the white ribbon (the dynamic ribbon of 1969) sweeps under the script and picks up the C\u2019s swash, so the script and the ribbon are one wave.',
                        'A wave under a script is the classic version of what O1 tried in the lab: the words on one wave with the cards.'),
    'skittles': W('Sits on the mark\u2019s curve: the word arches over the rainbow, each letter standing on the arc, and the S and the s lean into its ends.',
                  'Words on an arc read as part of the arc. Our bowl is the same, only shallower and falling, and the falling is what says dealt.'),
    'sunkist': W('Sits on the mark\u2019s curve: the S\u2019s tail runs under the whole word as a swash, so the word is underlined by its own first letter.',
                 'The join can come from the word\u2019s first letter. Our C could do it: a swash from the C running back to the card.'),
    'paramount': W('Sits on the mark: the word lies across the mountain and the arc of stars rides over it, so the word is part of the landscape, not a caption.',
                   'Words inside the picture. If the fan ever grew to hold the words this is the reference; at bar size the words would be tiny.'),
    'crayola': W('Sits on the mark\u2019s curve: the word arches on the oval\u2019s smile inside the swoosh, the letters rising and falling with it.',
                 'A word on a smile inside a badge. The badge is what makes it an app icon; ours has no badge, which is right for the bar.'),
    'dreamworks': W('Under the mark\u2019s curve: the crescent moon arcs over the word, and the word sits square under its sweep, the boy\u2019s fishing line dropping into it.',
                    'The curve above and the words straight below: the calm version. Q1 chooses the livelier one, both lines bent.'),
    'pringles-flow': W('Sits on the mark\u2019s curve: the word bows under the face like a smile, so the mascot and the word share one expression.',
                       'The bowl under the face is Q1\u2019s bowl beside the cards, and Pringles proves it reads small: the word is on every can and app icon.'),
    'hot-wheels': W('Rides the mark: the words are set on the flame, the letters following its sweep up and out, so the word burns with it.',
                    'The strongest join of all: the words take the mark\u2019s shape. It costs legibility, which is why the flame is drawn wider than the words.'),
    'chupa-chups': W('Inside the mark: the two words fill the daisy, bent to its round, so the name is the flower\u2019s centre (Dal\u00ed drew it in 1969).',
                     'Words inside a mark make one shape and a fine app icon, and eat the words on a bar. Our fan is the wrong shape to hold two words.'),
    'lays': W('Inside the mark: the word sits on the red ribbon that crosses the sun, the ribbon curved so the word bows with it.',
              'A ribbon is the middle road: it carries the words on a curve and still keeps them off the picture. A card could be our ribbon.'),
    'uno-flow': W('Inside the mark: UNO sits on a tilted red oval, and the tilt gives the word the lean a thrown card has.',
                  'The tilt is the whole trick, and it is a card game\u2019s. Q1\u2019s words have the same lean without the oval, so the fan has to supply it.'),
    'burger-king-flow': W('Inside the mark: BURGER KING is the patty between two bun halves, so the words are what the mark is made of.',
                          'The words become the thing. Our version would be words between two cards; round 6 tried letters on cards and Holger let them go.'),
    'pizza-hut': W('Under the mark\u2019s shape: the red roof sits on the stacked words, and the words are drawn with the roof\u2019s tilt, the whole a little house.',
                   'Two lines with a lean under a shape that gives the lean a reason. Q1\u2019s reason is the card; Pizza Hut\u2019s is the roof.'),
    'goodwill': W('A letter is the mark: the g of goodwill, turned up, is the smiling half-face on the badge, so the word carries the mark inside it.',
                  'The mark hides in the word. For us that would be the C or the G as a card, which round 6 tried (rows 21 to 23).'),
    'gatorade': W('A letter is the mark: the lightning bolt cuts through the G, so the first letter is the mark and the rest of the name sits small above it.',
                  'One letter does the work and the word stays plain. If the fan ever goes, a C as a card is our version of the G.'),
    'goodyear': W('The mark inside the word: the winged foot stands in the middle of GOODYEAR between the two halves, so the word is split by its mark.',
                  'A mark in the middle of the word. Ours could put the fan between World of and Card Games, which round 5 tried and Holger let go.'),
    'tostitos': W('The mark inside the word: the two t\u2019s are two people sharing a chip over the i\u2019s dot, a bowl of salsa, so the letters act out the product.',
                  'Letters that act out the thing inside a plain word. Our A\u2019s on the cards are already letters on cards; the word is the other way round.'),
    'seven-eleven': W('The mark holds the word: ELEVEN runs across the big 7, so the small word is inside the big numeral.',
                      'A small word crossing a big mark. Our small line crosses nothing; it starts from the card\u2019s edge instead.'),
    'toys-r-us': W('A letter is the mark: the backwards R sits on its own blue star badge in the middle of the word, the odd letter as the logo.',
                   'One letter given a badge. Ours would be a card behind the C or the G, with the rest plain.'),
    'tour-de-france': W('The letters are the mark: the o of Tour is a wheel, the r the rider bent over it and the yellow sun the back wheel, so the word is a cyclist.',
                        'The word drawn as the thing, at a poster\u2019s size; small, the rider is a blob. A warning for anything that hides a figure in our letters.'),
    'vans': W('A letter is the mark: the V\u2019s right arm stretches over ANS as a line, so the first letter shelters the word.',
              'The first letter reaching over the rest is a join we have not tried: a C whose top runs on over ard as a card\u2019s edge.'),
    'subway': W('The letters carry the mark: the S and the Y end in arrows, one going out and one coming in, so the word moves both ways.',
                'Arrows on the first and last letters give a plain word motion. Ours gets its motion from the lean instead.'),
    'hearthstone': W('A letter is the mark: the second O is the hearthstone itself, a swirl of light, set in a hand-drawn word with a stone\u2019s texture.',
                     'A game logo that hides its mark in the word and pays for it at small sizes: on the bar the O is a smudge.'),
}


# ---------------------------------------------------------------------------------------------------------------
# fetching
# ---------------------------------------------------------------------------------------------------------------

def api(host, params):
    url = 'https://%s/w/api.php?%s' % (host, urllib.parse.urlencode(params))
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return json.load(r)


LOGO_FIELD = re.compile(r'\|\s*(?:logo|logo_image|image_logo|company_logo|logo1)\s*=\s*(?:\[\[)?\s*(?:File:|Image:)?\s*([^\n|\]}{]+?\.(?:svg|png|jpg|jpeg|gif|webp))', re.I)


def infobox_logo(article):
    try:
        d = api('en.wikipedia.org', dict(action='parse', page=article, prop='wikitext', redirects=1, format='json'))
        text = d['parse']['wikitext']['*']
    except Exception as e:
        return None
    m = LOGO_FIELD.search(text)
    return m.group(1).strip() if m else None


def page_image(article):
    d = api('en.wikipedia.org', dict(action='query', titles=article, prop='pageimages', piprop='name', pilicense='any', redirects=1, format='json'))
    for p in d['query']['pages'].values():
        name = p.get('pageimage')
        if name and ('logo' in name.lower() or name.lower().endswith('.svg')):
            return name.replace('_', ' ')
    return None


def file_url(name):
    d = api('en.wikipedia.org', dict(action='query', titles='File:' + name, prop='imageinfo', iiprop='url|mime', format='json'))
    for p in d['query']['pages'].values():
        info = (p.get('imageinfo') or [None])[0]
        if info:
            return info['url'], info['mime']
    return None, None


def fetch(brand, refetch):
    existing = list(REFS.glob(brand['slug'] + '.*'))
    if existing and not refetch:
        return existing[0], 'kept'
    for old in existing:
        old.unlink()
    candidates = [c for c in [brand.get('file'), infobox_logo(brand['article']), page_image(brand['article'])] if c]
    for name in candidates:
        url, mime = file_url(name)
        if not url:
            continue
        ext = {'image/svg+xml': 'svg', 'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/webp': 'webp'}.get(mime, 'bin')
        out = REFS / ('%s.%s' % (brand['slug'], ext))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                out.write_bytes(r.read())
        except Exception as e:
            continue
        return out, name
    return None, 'none of: ' + ', '.join(candidates) if candidates else 'no candidate'


# ---------------------------------------------------------------------------------------------------------------
# the page
# ---------------------------------------------------------------------------------------------------------------

def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode('ascii')


def own_fonts_css():
    faces = [
        ('LabGLCA', 500, WOCG / 'static/fonts/GLCA-Medium.woff2'),
        ('LabCanela', 500, ROOT / 'Canela-Medium.otf'),
        ('LabArgesta', 400, ROOT / 'Argesta-Headline.otf'),
        ('LabBariol', 700, ROOT / 'fonts/bariol/bariol_bold-webfont.woff2'),
        ('LabBulo', 900, ROOT / 'fonts/BuloRounded-Black.woff2'),
    ]
    out = []
    for fam, w, p in faces:
        if not p.exists():
            continue
        ext = p.suffix.lstrip('.')
        fmt = {'woff2': 'woff2', 'woff': 'woff', 'otf': 'opentype', 'ttf': 'truetype'}[ext]
        out.append('@font-face { font-family: "%s"; font-weight: %d; src: url(data:font/%s;base64,%s) format("%s"); }' % (fam, w, ext, b64(p), fmt))
    return '\n'.join(out)


# the faces to try next: label, css font-family, weight, where it comes from, the lesson it answers
FACES = [
    ('Soft and cozy serifs', [
        ('GLCA Medium (B1 today)', "'LabGLCA'", 500, 'ours'),
        ('Canela Medium', "'LabCanela'", 500, 'in the design folder'),
        ('Argesta Headline', "'LabArgesta'", 400, 'in the design folder'),
        ('Fraunces', "'Fraunces'", 500, 'Google, free'),
        ('Young Serif', "'Young Serif'", 400, 'Google, free; the Cooper feel'),
        ('Bree Serif', "'Bree Serif'", 400, 'Google, free; a friendly slab'),
        ('Superclarendon', "'Superclarendon'", 400, 'on the Mac; the Wells Fargo and Sony sturdiness'),
        ('American Typewriter', "'American Typewriter'", 400, 'on the Mac'),
    ]),
    ('Classic book faces', [
        ('Baskerville', "'Baskerville'", 600, 'on the Mac'),
        ('Hoefler Text', "'Hoefler Text'", 400, 'on the Mac'),
        ('Big Caslon', "'Big Caslon'", 500, 'on the Mac'),
        ('Iowan Old Style', "'Iowan Old Style'", 700, 'on the Mac'),
        ('Cochin', "'Cochin'", 700, 'on the Mac'),
        ('EB Garamond', "'EB Garamond'", 600, 'Google, free'),
        ('Libre Caslon Display', "'Libre Caslon Display'", 400, 'Google, free'),
        ('Newsreader', "'Newsreader'", 500, 'Google, free'),
        ('Playfair Display', "'Playfair Display'", 500, 'Google, free'),
        ('Bodoni 72', "'Bodoni 72'", 700, 'on the Mac; the Vogue voice'),
    ]),
    ('Friendly sans', [
        ('Bariol Bold (the logo today)', "'LabBariol'", 700, 'ours'),
        ('Bulo Rounded Black (the interface)', "'LabBulo'", 900, 'ours'),
        ('Gill Sans', "'Gill Sans'", 600, 'on the Mac; the Penguin face'),
        ('Futura', "'Futura'", 500, 'on the Mac'),
        ('Avenir', "'Avenir'", 700, 'on the Mac'),
        ('Optima', "'Optima'", 700, 'on the Mac'),
        ('Jost', "'Jost'", 500, 'Google, free; a Futura'),
        ('Nunito', "'Nunito'", 800, 'Google, free; rounded'),
        ('Fredoka', "'Fredoka'", 500, 'Google, free; rounded'),
    ]),
    ('A script for the small line', [
        ('Snell Roundhand over Baskerville', "'Snell Roundhand'|'Baskerville'", 400, 'on the Mac'),
        ('Pacifico over Fraunces', "'Pacifico'|'Fraunces'", 400, 'Google, free'),
        ('Kaushan Script over Big Caslon', "'Kaushan Script'|'Big Caslon'", 400, 'Google, free'),
    ]),
]

GOOGLE = ('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500&family=Young+Serif&family=Bree+Serif&family=EB+Garamond:wght@600'
          '&family=Libre+Caslon+Display&family=Newsreader:opsz,wght@6..72,500&family=Playfair+Display:wght@500&family=Jost:wght@500&family=Nunito:wght@800'
          '&family=Fredoka:wght@500&family=Pacifico&family=Kaushan+Script&display=swap')


def card(brand, path):
    w = WORDS.get(brand['slug'], {})
    src = 'logo-refs/' + path.name if path else ''
    img = '<img src="%s" alt="">' % src if path else '<span class="lr-missing">no file</span>'
    return '''
<section class="lr-card" id="%(slug)s">
  <div class="lr-plates"><span class="lr-plate lr-big">%(img)s</span><span class="lr-plate lr-bar">%(img)s</span></div>
  <div class="lr-words"><b>%(name)s</b>%(works)s%(us)s</div>
</section>''' % dict(slug=brand['slug'], img=img, name=escape(brand['name']),
                     works=('<p>%s</p>' % escape(w['works'])) if w.get('works') else '',
                     us=('<p class="lr-us">%s</p>' % escape(w['us'])) if w.get('us') else '')


def faces_strip():
    out = []
    for group, faces in FACES:
        cards = []
        for label, fam, weight, where in faces:
            top_fam, big_fam = (fam.split('|') + [fam])[:2]
            cards.append('<div class="lr-face"><div class="lr-lock"><img src="logo-lab-out/mark-fan.svg" alt="">'
                         '<span class="lr-lines"><span class="lr-small" style="font-family: %s, serif; font-weight: %s">World of</span>'
                         '<span class="lr-large" style="font-family: %s, serif; font-weight: %d">Card Games</span></span></div>'
                         '<div class="lr-face-name"><b>%s</b><span>%s</span></div></div>'
                         % (top_fam, 400 if '|' in fam else weight, big_fam, weight, escape(label), escape(where)))
        out.append('<h3>%s</h3><div class="lr-faces">%s</div>' % (escape(group), ''.join(cards)))
    return ''.join(out)


def build(paths):
    sections = []
    for key, title, lead in LESSONS:
        cards = ''.join(card(b, paths.get(b['slug'])) for b in BRANDS if b['lesson'] == key)
        sections.append('<h2 id="%s">%s</h2><p class="lr-desc">%s</p><div class="lr-grid">%s</div>' % (key, escape(title), escape(lead), cards))
    toc = ''.join('<a href="#%s">%s</a>' % (key, escape(title)) for key, title, _ in LESSONS) + '<a href="#lessons">The lessons</a><a href="#faces">Faces to try next</a>'
    return PAGE % dict(google=GOOGLE, fonts=own_fonts_css(), css=CSS, toc=toc, sections=''.join(sections), lessons=LESSONS_HTML, faces=faces_strip())


LESSONS_HTML = '''
<ol class="lr-lessons">
  <li><b>The small line is a label, not a second title.</b> Where a small line sits over a big one, it is a fifth to a half of the big line\u2019s height: Twinings a fifth, Whole Foods a third, World of Tanks Blitz two fifths, Warcraft a half. B1\u2019s is 56%, above all of them. At 40%, with the words at 85% of the fan, Card Games grows and the block stays the same height.</li>
  <li><b>One line performs, the other reads.</b> Disney puts the script on the small line and plain capitals on the big one; Kellogg’s and Coca-Cola are all performance and pay for it at small sizes. If Card Games is a serif, World of can be quieter: smaller, spaced, in the interface face, or a script.</li>
  <li><b>Mark and words: one height, or the mark clearly bigger.</b> The North Face and Chess.com make them one height; WWF, Guinness and Penguin make the mark bigger and the words smaller. Your 85% pick is the second family, and the in-between (B1 at 100%) is what looked wrong.</li>
  <li><b>A mark that survives 16px is simple.</b> Penguin, Bass, National Geographic and Cartamundi are silhouettes, a triangle, a frame, two card shapes. Our fan has four cards, a shadow and a gradient, and at the browser tab it is a blob. The flat fan, two cards or one card from round 1 are the simplified versions, at least for the favicon.</li>
  <li><b>Warm comes from the face.</b> Mailchimp, Etsy, Chobani, Nintendo, Trader Joe’s, Wells Fargo and Sony are soft serifs and slabs with rounded or heavy details, often lowercase. Capitals feel formal (Tiffany, Warby Parker, Barnes &amp; Noble), which is why the capitals version felt less cozy.</li>
  <li><b>Heavy enough for 32px.</b> Warby Parker and Vogue break on the band at 32px; Medium, Etsy and Sony hold. Whatever face we pick, the big line wants a medium to bold weight and open counters.</li>
  <li><b>A frame is the other way to be one shape.</b> Land Rover, Burger King, Nintendo and Häagen-Dazs. It makes an app icon easy and eats the words at bar size. Not for the bar; maybe for the icon.</li>
  <li><b>The words continue the mark by sharing its line.</b> Added 29 Sep. The famous joins are four: the words lean with the mark (Nike, Pepsi 1991, NASCAR, Puma), the words sit on the mark\u2019s curve (Amazon, Coca-Cola, Skittles, Pringles), the words are inside the mark (Hot Wheels, Chupa Chups, Uno, Burger King), or a letter is the mark (Goodwill, Gatorade, Goodyear, Tostitos). Q1 is the first kind with the second\u2019s curve: both lines on a bowl leaving the front card at the card\u2019s lean. What the first kind shares: one angle for mark and words, the words touching or nearly touching the mark, and the mark drawn simpler than the words.</li>
</ol>'''

CSS = r'''
  :root { --lr-paper: #f9f6f2; --lr-band: #f4eee5; --lr-ink: #141414; --lr-label: #4e4d4c; --lr-quiet: #67635c; --lr-line: #d2cfca; --lr-soft: #ebe7de; }
  html, body { margin: 0; }
  body { background: var(--lr-paper); color: var(--lr-ink); font: 16px/24px "BuloRounded", "Verdana", sans-serif; -webkit-font-smoothing: antialiased; }
  .lr-head { position: sticky; top: 0; z-index: 5; display: flex; align-items: center; flex-wrap: wrap; gap: 8px 20px; padding: 12px 28px 10px; background: rgba(249, 246, 242, .96); box-shadow: 0 1px 0 var(--lr-line); }
  .lr-head h1 { margin: 0; font: 500 26px/32px "GLCA", Georgia, serif; }
  .lr-head p { margin: 0; color: var(--lr-label); font-size: 14px; line-height: 20px; max-width: 980px; }
  .lr-page { padding: 8px 28px 96px; max-width: 1400px; }
  .lr-toc { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 14px 0 4px; font-size: 14px; }
  .lr-toc a { color: #1971c2; text-decoration: none; }
  .lr-toc a:hover { text-decoration: underline; }
  .lr-page h2 { font: 500 24px/30px "GLCA", Georgia, serif; margin: 36px 0 4px; }
  .lr-page h3 { font: 700 16px/22px "BuloRounded", Verdana, sans-serif; margin: 22px 0 8px; }
  .lr-desc { color: var(--lr-label); font-size: 14px; line-height: 20px; max-width: 900px; margin: 0 0 14px; }
  .lr-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 12px; }
  .lr-card { background: #fff; border-radius: 14px; corner-shape: squircle; box-shadow: inset 0 0 0 1px var(--lr-line); padding: 12px; display: grid; grid-template-columns: 200px 1fr; gap: 12px; align-items: start; }
  .lr-plates { display: grid; gap: 8px; }
  .lr-plate { display: flex; align-items: center; justify-content: center; border-radius: 8px; corner-shape: squircle; }
  .lr-big { height: 96px; background: #fff; box-shadow: inset 0 0 0 1px var(--lr-soft); padding: 8px; box-sizing: border-box; }
  .lr-big img { max-height: 80px; max-width: 180px; width: auto; height: auto; display: block; }
  .lr-bar { height: 56px; background: var(--lr-band); }
  .lr-bar img { height: 32px; max-width: 184px; width: auto; display: block; object-fit: contain; }
  .lr-missing { font-size: 12px; color: var(--lr-quiet); }
  .lr-words b { display: block; font-size: 15px; line-height: 20px; margin-bottom: 4px; }
  .lr-words p { margin: 0 0 6px; font-size: 13px; line-height: 18px; color: var(--lr-label); }
  .lr-words .lr-us { color: var(--lr-ink); }
  .lr-lessons { max-width: 900px; font-size: 15px; line-height: 22px; }
  .lr-lessons li { margin: 0 0 10px; }
  .lr-lessons b { color: var(--lr-ink); }
  .lr-faces { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; }
  .lr-face { background: #fff; border-radius: 12px; corner-shape: squircle; box-shadow: inset 0 0 0 1px var(--lr-line); padding: 12px 12px 8px; }
  .lr-lock { display: flex; align-items: center; gap: 10px; height: 76px; }
  .lr-lock img { height: 68px; width: auto; flex: none; }
  .lr-lines { display: flex; flex-direction: column; line-height: 1; color: var(--lr-ink); }
  .lr-small { font-size: 14px; margin-bottom: 5px; }
  .lr-large { font-size: 34px; }
  .lr-face-name { display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; margin-top: 6px; font-size: 12px; line-height: 16px; color: var(--lr-quiet); }
  .lr-face-name b { color: var(--lr-ink); font-size: 13px; }
'''

PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<!-- Generated by logo-refs-parts/make.py. Edit make.py, then run it. -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Logos to learn from &middot; lab</title>
<link rel="stylesheet" href="guide-fonts.css">
<link rel="stylesheet" href="%(google)s">
<style>
%(fonts)s
</style>
<style>
%(css)s
</style>
</head>
<body>
<header class="lr-head">
  <h1>Logos to learn from</h1>
  <p>Holger, 25 Sep: before trying faces, look at well-designed and classic logos and see how they get to something iconic. Each logo is drawn twice: large, and 32px tall as it would sit in our bar. Under each: what makes it work, and what it says for us. The lessons are gathered at the end, then a strip of faces to try next, drawn live in our own words.</p>
</header>
<main class="lr-page">
  <nav class="lr-toc">%(toc)s</nav>
%(sections)s
  <h2 id="lessons">The lessons</h2>
%(lessons)s
  <h2 id="faces">Faces to try next</h2>
  <p class="lr-desc">Every card is B1&rsquo;s lockup, the words at about 85%% of the fan, drawn live in the browser, with the small line at 40%% of the big one as the first lesson says (B1 today has 56%%). The Mac faces come from the system, the Google faces load from the web, and ours are embedded. Pick the ones worth building properly, in the bar, with outlined type.</p>
%(faces)s
</main>
</body>
</html>
'''


def main():
    REFS.mkdir(exist_ok=True)
    refetch = '--refetch' in sys.argv
    paths = {}
    for b in BRANDS:
        if b.get('use'):
            paths[b['slug']] = paths[b['use']]
            continue
        path, how = fetch(b, refetch)
        paths[b['slug']] = path
        print('%-20s %s' % (b['slug'], (path.name + '  <- ' + how) if path else 'MISSING  ' + how))
    (ROOT / 'logo-references.html').write_text(build(paths))
    print('wrote logo-references.html;', sum(1 for p in paths.values() if p), 'of', len(BRANDS), 'logos')


if __name__ == '__main__':
    main()
