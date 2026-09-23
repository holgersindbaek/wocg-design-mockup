// The colour versions of the icons. Each one is a row in the overview and a button in the details' bar.
//
// The first ones are made by make-versions.js from the colour rules (versions-made.js). Versions saved
// by hand go in SAVED below, last, so the older ones keep their place.
//
// A version maps an icon colour (as built, upper-case hex) to a new one, at three reaches.
// The narrowest reach wins:
//   global  every icon:                 { "#212529": "#4E4D4C" }
//   icon    one icon, all its states:   { "tableMenu": { "#74C0FC": "#ABD2FF" } }
//   state   one state of one icon:      { "tableMenu/hover": { "#228BE6": "#5E574B" } }
//
// "Copy as a version" in the lab gives your scratch in this shape. Paste it into SAVED, give it a title
// and a sentence, then run `node icon-lab-parts/build.js`.
const SAVED = [
];

module.exports = require('./versions-made.js').concat(SAVED);
