/* The Euchre logo exit lab's harness.
 *
 * Every tile plays Khang's 13 Oct render (active.webm) until the jack has sunk
 * behind the word (frame 48, 1.60 s). At that frame the video is swapped for a
 * scene the lab draws itself: the video's own last frame as the background
 * (bg.png) and, on top, Khang's Spine skeleton drawn by the Spine web runtime
 * (spine-player.js), playing one exit animation. The skeleton, its atlas and
 * the exits come inlined in spine-data.js, which build-spine.mjs makes from
 * Khang's export and exits/*.mjs; the same skeleton goes to Khang as
 * for-khang/euchre-logo-exits.json, so what a tile shows is what he opens.
 *
 * One WebGL renderer draws every tile: a seek sets the skeleton to the exit's
 * pose at time t, renders it at full scene size and copies the picture onto the
 * tile's own 2D canvas. The jack's slots are hidden on the skeleton, since the
 * video has already played the jack. The skeleton's own banner background is
 * drawn (under bg.png's 3 px margins), so additive light blends on the felt
 * inside the canvas as it does in Spine.
 */
(function () {
  "use strict";

  var D = window.EUCHRE_EXITS;
  var PARTS = (function () {
    var s = document.currentScript && document.currentScript.src;
    return s ? s.slice(0, s.lastIndexOf("/") + 1) : "euchre-logo-exit-lab-parts/";
  })();
  var SCENE = { w: 1920, h: 1447 };
  var FPS = 30;
  var HANDOFF_FRAME = 48;
  var HOLD_MS = 900;
  var HIDDEN = ["hair_R", "arm_U_R", "arm_D_R", "body", "arm_L", "hand_R", "choker", "head", "mouth", "bread_R", "bread_L", "eye_R", "eye_L", "eyebrow_R", "eyebrow_L", "hair_L", "crown"];
  var params = new URLSearchParams(location.search);
  var SHOTS = params.get("shots") === "1";
  var speed = 1, loop = true;
  var size = Number(params.get("size")) || 480;
  var tiles = [];

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

  // --- the one renderer ---
  var glCanvas = document.createElement("canvas");
  glCanvas.width = SCENE.w; glCanvas.height = SCENE.h;
  var context = new spine.ManagedWebGLRenderingContext(glCanvas, { alpha: true, premultipliedAlpha: false, preserveDrawingBuffer: true, antialias: true });
  var renderer = new spine.SceneRenderer(glCanvas, context, true);
  var skeleton = null, state = null;
  var loaded = new Promise(function (res, rej) {
    var am = new spine.AssetManager(context, "");
    am.setRawDataURI("skeleton.json", "data:application/json;base64," + btoa(unescape(encodeURIComponent(D.json))));
    am.setRawDataURI("skeleton.atlas", "data:text/plain;base64," + btoa(D.atlas));
    Object.keys(D.images).forEach(function (n) { am.setRawDataURI(n, D.images[n]); });
    am.loadTextureAtlas("skeleton.atlas");
    am.loadJson("skeleton.json");
    (function tick() {
      if (!am.isLoadingComplete()) return requestAnimationFrame(tick);
      if (am.hasErrors()) return rej(new Error("the skeleton did not load: " + JSON.stringify(am.getErrors())));
      try {
        var data = new spine.SkeletonJson(new spine.AtlasAttachmentLoader(am.require("skeleton.atlas"))).readSkeletonData(am.require("skeleton.json"));
        skeleton = new spine.Skeleton(data);
        state = new spine.AnimationState(new spine.AnimationStateData(data));
        HIDDEN.forEach(function (n) { var s = skeleton.findSlot(n); if (s) { s.data.attachmentName = null; s.setAttachment(null); } });
        res();
      } catch (e) { rej(e); }
    })();
  });

  function draw(tile, t) {
    if (!skeleton) return;
    skeleton.setToSetupPose();
    state.clearTracks();
    state.setAnimation(0, tile.def.animation, false);
    state.update(t / 1000);
    state.apply(skeleton);
    skeleton.updateWorldTransform(spine.Physics ? spine.Physics.update : undefined);
    var gl = context.gl;
    gl.viewport(0, 0, SCENE.w, SCENE.h);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    var cam = renderer.camera;
    cam.position.x = 0; cam.position.y = 0;
    cam.viewportWidth = SCENE.w; cam.viewportHeight = SCENE.h; cam.zoom = 1;
    renderer.begin();
    renderer.drawSkeleton(skeleton, false);
    renderer.end();
    var c = tile.canvas, ctx = tile.ctx;
    ctx.clearRect(0, 0, c.width, c.height);
    ctx.drawImage(glCanvas, 0, 0, c.width, c.height);
    tile.t = t;
  }

  function makeTile(def, number) {
    var tile = { def: def, t: 0 };
    var fig = el("figure", "tile");
    fig.dataset.slug = def.slug;
    fig.id = "x-" + def.id;
    var stageEl = el("div", "stage");
    var video = el("video");
    video.muted = true; video.playsInline = true; video.preload = SHOTS ? "none" : "auto";
    video.src = PARTS + "active.webm";
    var sceneEl = el("div", "scene");
    var bg = el("img", "bg");
    bg.src = PARTS + "bg.png"; bg.draggable = false;
    var canvas = el("canvas", "draw");
    sceneEl.append(bg, canvas);
    stageEl.append(video, sceneEl);
    var cap = el("figcaption");
    var head = el("div", "head");
    head.append(el("span", "num", def.video ? "Now" : String(number)), el("b", null, def.name));
    cap.appendChild(head);
    if (def.summary) cap.appendChild(el("p", "sum", def.summary));
    if (def.spine) { var sp = el("p", "spine"); sp.append(el("b", null, "In Spine: "), def.spine); cap.appendChild(sp); }
    if (!def.video) cap.appendChild(el("p", "file", "exits/" + def.slug + ".mjs, animation " + def.animation));
    var bar = el("div", "bar");
    var btn = el("button", "play", "Play");
    var range = el("input"); range.type = "range"; range.min = 0; range.step = 1; range.value = 0;
    var time = el("span", "time", "");
    bar.append(btn, range, time);
    fig.append(stageEl, cap, bar);

    var duration = def.video ? 2000 : def.duration;
    range.max = duration;
    time.textContent = def.video ? "" : (duration / 1000).toFixed(2) + " s";
    tile.el = fig; tile.stageEl = stageEl; tile.sceneEl = sceneEl; tile.video = video; tile.canvas = canvas; tile.ctx = canvas.getContext("2d"); tile.bg = bg; tile.duration = duration;

    var raf = 0, stateName = "still", holdTimer = 0, cancelFrame = null;
    function showVideo() { sceneEl.style.visibility = "hidden"; video.style.visibility = "visible"; }
    function showScene() { video.style.visibility = "hidden"; sceneEl.style.visibility = "visible"; }
    function setTime(t) { range.value = t; time.textContent = (t / 1000).toFixed(2) + " s"; }
    function stop() {
      if (raf) cancelAnimationFrame(raf); raf = 0;
      if (holdTimer) clearTimeout(holdTimer); holdTimer = 0;
      if (cancelFrame) cancelFrame(); cancelFrame = null;
      if (!video.paused) video.pause();
      stateName = "still";
      btn.textContent = "Play";
    }
    function still() { stop(); showVideo(); video.currentTime = 0; setTime(0); }
    function afterHold() { holdTimer = setTimeout(function () { holdTimer = 0; if (loop) play(); else still(); }, HOLD_MS); }
    function startExit() {
      showScene();
      stateName = "exit";
      var t0 = performance.now();
      function frame(now) {
        var t = (now - t0) * speed;
        if (t >= duration) { draw(tile, duration); setTime(duration); raf = 0; stateName = "hold"; afterHold(); return; }
        draw(tile, t); setTime(t);
        raf = requestAnimationFrame(frame);
      }
      draw(tile, 0);
      raf = requestAnimationFrame(frame);
    }
    function armHandoff() {
      var target = HANDOFF_FRAME / FPS - 0.002, done = false;
      if (video.requestVideoFrameCallback) {
        var id = video.requestVideoFrameCallback(function cb(now, meta) {
          if (done) return;
          if (meta.mediaTime >= target) { done = true; video.pause(); startExit(); return; }
          id = video.requestVideoFrameCallback(cb);
        });
        cancelFrame = function () { done = true; video.cancelVideoFrameCallback(id); };
      } else {
        var poll = requestAnimationFrame(function tick() {
          if (done) return;
          if (video.currentTime >= target) { done = true; video.pause(); startExit(); return; }
          poll = requestAnimationFrame(tick);
        });
        cancelFrame = function () { done = true; cancelAnimationFrame(poll); };
      }
    }
    function play() {
      stop();
      btn.textContent = "Stop";
      showVideo();
      video.currentTime = 0;
      video.playbackRate = speed;
      stateName = "video";
      var p = video.play();
      if (p && p.catch) p.catch(function () {});
      if (def.video) {
        var onEnd = function () { video.removeEventListener("ended", onEnd); stateName = "hold"; afterHold(); };
        video.addEventListener("ended", onEnd);
        cancelFrame = function () { video.removeEventListener("ended", onEnd); };
        var vraf = requestAnimationFrame(function tick() { if (stateName !== "video") return; setTime(Math.round(video.currentTime * 1000)); vraf = requestAnimationFrame(tick); });
        return;
      }
      armHandoff();
    }
    btn.addEventListener("click", function () { if (stateName === "still") play(); else still(); });
    range.addEventListener("input", function () {
      stop();
      var t = Number(range.value);
      if (def.video) { video.currentTime = t / 1000; showVideo(); setTime(t); return; }
      showScene(); draw(tile, t); setTime(t);
    });

    tile.play = play; tile.still = still; tile.stop = stop;
    tile.show = function (t) { stop(); if (def.video) return null; showScene(); t = clamp(t, 0, duration); draw(tile, t); setTime(t); return duration; };
    tile.setSize = function (w) {
      var h = Math.round(w * SCENE.h / SCENE.w), dpr = Math.min(2, window.devicePixelRatio || 1);
      stageEl.style.width = w + "px"; stageEl.style.height = h + "px";
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      canvas.style.width = w + "px"; canvas.style.height = h + "px";
      if (sceneEl.style.visibility === "visible") draw(tile, tile.t);
    };
    tile.setSize(size);
    showVideo();
    return tile;
  }

  function build() {
    if (SHOTS) { var navEl = document.querySelector("nav"); if (navEl) navEl.style.display = "none"; }
    var grid = document.getElementById("tiles");
    var list = [{ video: true, id: "now", slug: "now", name: "Khang's current exit (13 Oct)", summary: "The render as delivered: the jack swells, sinks down behind the word, and the word shrinks to a point above its centre, fading at the end.", spine: "What his active animation does today: the logo bone scales to zero towards the jack's vanishing point, the slot's alpha fading over the last frames." }];
    var n = 0;
    D.exits.forEach(function (e) { list.push(e); });
    list.forEach(function (def) {
      var number = def.video ? 0 : (/^00-/.test(def.slug) ? 0 : ++n);
      var tile = makeTile(def, number);
      tiles.push(tile);
      grid.appendChild(tile.el);
    });
    var nav = document.getElementById("exit-links");
    if (nav) list.forEach(function (def) { var a = el("a", null, def.video ? "Now" : def.name); a.href = "#x-" + def.id; nav.appendChild(a); });

    document.querySelectorAll("[data-speed]").forEach(function (b) {
      b.addEventListener("click", function () {
        speed = Number(b.dataset.speed);
        document.querySelectorAll("[data-speed]").forEach(function (o) { o.classList.toggle("on", o === b); });
        tiles.forEach(function (t) { t.video.playbackRate = speed; });
      });
    });
    document.querySelectorAll("[data-size]").forEach(function (b) {
      b.addEventListener("click", function () {
        size = Number(b.dataset.size);
        document.querySelectorAll("[data-size]").forEach(function (o) { o.classList.toggle("on", o === b); });
        tiles.forEach(function (t) { t.setSize(size); });
      });
      b.classList.toggle("on", Number(b.dataset.size) === size);
    });
    var loopBox = document.getElementById("loop");
    if (loopBox) { loopBox.checked = loop; loopBox.addEventListener("change", function () { loop = loopBox.checked; }); }
    var all = document.getElementById("play-all");
    if (all) all.addEventListener("click", function () { tiles.forEach(function (t) { t.play(); }); });
    var stopAll = document.getElementById("stop-all");
    if (stopAll) stopAll.addEventListener("click", function () { tiles.forEach(function (t) { t.still(); }); });

    window.LAB = {
      tiles: tiles,
      skeleton: function () { return skeleton; }, state: function () { return state; },
      list: function () { return tiles.filter(function (t) { return !t.def.video; }).map(function (t) { return { slug: t.def.slug, id: t.def.id, name: t.def.name, duration: t.duration, animation: t.def.animation }; }); },
      show: function (slug, t) {
        var tile = tiles.filter(function (x) { return x.def.slug === slug || x.def.id === slug; })[0];
        if (!tile) throw new Error("no exit " + slug);
        return tile.show(t);
      },
      setSize: function (w) { size = w; tiles.forEach(function (t) { t.setSize(w); }); },
      // one frame of an exit as a PNG data URL, w px wide: the background and the skeleton at time t (shots.mjs)
      frame: function (slug, t, w) {
        var tile = tiles.filter(function (x) { return x.def.slug === slug || x.def.id === slug; })[0];
        if (!tile || tile.def.video) throw new Error("no exit " + slug);
        draw(tile, clamp(t, 0, tile.duration));
        var c = document.createElement("canvas");
        c.width = w; c.height = Math.round(w * SCENE.h / SCENE.w);
        var ctx = c.getContext("2d");
        ctx.drawImage(tile.bg, 0, 0, c.width, c.height);
        ctx.drawImage(glCanvas, 0, 0, c.width, c.height);
        return c.toDataURL("image/png");
      },
      ready: Promise.all([loaded].concat(tiles.map(function (t) {
        return t.bg.complete ? Promise.resolve() : new Promise(function (res) { t.bg.onload = res; t.bg.onerror = res; });
      }))).then(function () { window.LAB.isReady = true; return true; })
    };
    window.LAB.ready.catch(function (e) {
      var p = el("p", "err", "The skeleton did not load: " + (e && e.message));
      document.getElementById("tiles").before(p);
      console.error(e);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();
