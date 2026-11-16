/* Technical handbook 3D viewer: loads an Onshape glTF export, groups bodies into parts by name,
   and offers an exploded view, a clickable parts list, X-ray and assembly steps.
   Units metres; Onshape exports Z up, so the model is turned to three.js's Y up. */
(function () {
  "use strict";

  function partKey(name) {
    // the loader turns spaces into "_" and appends "_1", "_2" to repeated names
    return (name || "").replace(/_\d+$/, "").replace(/_/g, " ").trim();
  }

  window.TDViewer = function (opts) {
    var wrap = opts.wrap, canvas = wrap.querySelector("canvas");
    var listEl = opts.list, stepsEl = opts.steps, slider = opts.slider, xrayBtn = opts.xray, resetBtn = opts.reset, status = opts.status;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var renderer;
    try { renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true }); } catch (e) { status.textContent = "3D view needs WebGL, which this browser has turned off."; return; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    var scene = new THREE.Scene();
    scene.background = new THREE.Color(opts.background != null ? opts.background : 0xe9eaec).convertSRGBToLinear();
    var camera = new THREE.PerspectiveCamera(32, 1, 0.01, 100);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8f99, 0.9));
    var key = new THREE.DirectionalLight(0xffffff, 1.3); key.position.set(-2, 4, 3); scene.add(key);
    var fill = new THREE.DirectionalLight(0xffffff, 0.55); fill.position.set(3, 1.5, -2); scene.add(fill);

    var root = new THREE.Group(); scene.add(root);
    var parts = {}, order = [], centre = new THREE.Vector3(), size = 1, explode = 0, xray = false, focus = null;
    var grid;

    new THREE.GLTFLoader().load(opts.model, function (gltf) {
      var model = gltf.scene;
      model.rotation.x = -Math.PI / 2;
      root.add(model);
      root.updateMatrixWorld(true);
      var all = new THREE.Box3().setFromObject(model);
      all.getCenter(centre);
      size = all.getSize(new THREE.Vector3()).length();
      // one entry per body (top-level node), grouped into parts by name
      model.children.slice().forEach(function (node) {
        var k = partKey(node.name) || "Unnamed part";
        if (opts.rename && opts.rename[k]) k = opts.rename[k];
        var box = new THREE.Box3().setFromObject(node);
        var c = box.getCenter(new THREE.Vector3());
        var vol = box.getSize(new THREE.Vector3());
        node.userData.home = node.position.clone();
        // explode along the line from the assembly centre, in the node's parent (Z-up) frame
        var dirWorld = c.clone().sub(centre);
        var inv = new THREE.Matrix4().copy(model.matrixWorld).invert();
        var a = centre.clone().applyMatrix4(inv), b = c.clone().applyMatrix4(inv);
        node.userData.dir = b.sub(a);
        node.userData.enclosure = box.containsPoint(centre) && (vol.x * vol.y * vol.z) > 0.12 * Math.pow(size / 1.8, 3);
        node.traverse(function (o) {
          if (!o.isMesh) return;
          o.material = o.material.clone();
          if (o.material.color) o.material.color.convertSRGBToLinear();   // Onshape writes sRGB colour values
          o.material.transparent = true;
          o.userData.baseEmissive = o.material.emissive ? o.material.emissive.clone() : null;
        });
        if (!parts[k]) { parts[k] = { nodes: [], name: k }; order.push(k); }
        parts[k].nodes.push(node);
        if (dirWorld.length() < 1e-6) node.userData.dir.set(0, 0, 0);
      });
      // floor grid under the model (left out for print renders)
      if (!opts.noGrid) {
      grid = new THREE.GridHelper(Math.max(1, size * 2.5), 20, 0xb9bcc2, 0xd3d5d9);
      grid.position.y = all.min.y - 0.001;
      scene.add(grid);
      }
      buildList();
      buildSteps();
      fitCamera();
      status.textContent = "";
      wrap.classList.add("ready");
      if (opts.initialExplode) setExplode(opts.initialExplode, false);
    }, undefined, function () { status.textContent = "The 3D model couldn't load. Open this page through the local server (see the handbook home page)."; });

    // ---------- parts list ----------
    function buildList() {
      if (!listEl) return;
      listEl.innerHTML = "";
      order.slice().sort(function (a, b) { return a.localeCompare(b); }).forEach(function (k) {
        var li = document.createElement("li");
        var b = document.createElement("button");
        b.type = "button";
        b.innerHTML = "<span></span><em></em>";
        b.querySelector("span").textContent = k;
        b.querySelector("em").textContent = parts[k].nodes.length > 1 ? "×" + parts[k].nodes.length : "";
        b.addEventListener("mouseenter", function () { highlight([k], true); });
        b.addEventListener("mouseleave", function () { highlight(focus, false); });
        b.addEventListener("click", function () {
          var on = !(focus && focus.length === 1 && focus[0] === k);
          setFocus(on ? [k] : null);
          listEl.querySelectorAll("button").forEach(function (x) { x.classList.remove("on"); });
          if (on) b.classList.add("on");
        });
        parts[k].button = b;
        li.appendChild(b); listEl.appendChild(li);
      });
    }

    // ---------- assembly steps ----------
    function buildSteps() {
      if (!stepsEl || !opts.stepDefs) return;
      var btns = stepsEl.querySelectorAll("[data-step]");
      btns.forEach(function (btn) {
        btn.addEventListener("click", function () {
          var def = opts.stepDefs[+btn.dataset.step];
          var re = new RegExp(def.parts, "i");
          var keys = order.filter(function (k) { return re.test(k); });
          var already = btn.classList.contains("on");
          btns.forEach(function (x) { x.classList.remove("on"); });
          if (already) { setFocus(null); return; }
          btn.classList.add("on");
          if (explode < 0.55) setExplode(0.6, true);
          setFocus(keys);
          wrap.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" });
        });
      });
    }

    function each(keys, fn) { (keys || []).forEach(function (k) { if (parts[k]) parts[k].nodes.forEach(function (n) { n.traverse(function (o) { if (o.isMesh) fn(o, n); }); }); }); }
    function highlight(keys, hover) {
      order.forEach(function (k) { each([k], function (o) { if (o.userData.baseEmissive) o.material.emissive.copy(o.userData.baseEmissive); }); });
      if (keys) each(keys, function (o) { if (o.material.emissive) o.material.emissive.setRGB(hover ? 0.55 : 0.35, hover ? 0.42 : 0.3, 0); });
    }
    function applyOpacity() {
      order.forEach(function (k) {
        var dim = focus && focus.indexOf(k) < 0;
        each([k], function (o, n) {
          var op = 1;
          if (xray || (n.userData.enclosure && explode > 0.05)) op = n.userData.enclosure ? Math.max(0.12, 1 - explode * 1.6) : 1;
          if (xray && n.userData.enclosure) op = 0.12;
          if (dim) op = Math.min(op, 0.1);
          o.material.opacity = op;
          o.material.depthWrite = op > 0.5;
        });
      });
    }
    function setFocus(keys) { focus = keys && keys.length ? keys : null; highlight(focus, false); applyOpacity(); }

    // ---------- exploded view ----------
    var target = 0;
    function setExplode(v, animate) { target = v; slider.value = String(Math.round(v * 100)); if (!animate || reduce) { explode = v; place(); } }
    function place() {
      order.forEach(function (k) {
        parts[k].nodes.forEach(function (n) {
          var spread = n.userData.enclosure ? 0 : 1.5;
          n.position.copy(n.userData.home).addScaledVector(n.userData.dir, explode * spread);
        });
      });
      applyOpacity();
    }
    slider.addEventListener("input", function () { setExplode(+slider.value / 100, false); });
    if (xrayBtn) xrayBtn.addEventListener("click", function () { xray = !xray; xrayBtn.setAttribute("aria-pressed", String(xray)); applyOpacity(); });
    if (resetBtn) resetBtn.addEventListener("click", function () {
      setFocus(null); setExplode(0, true); yaw = 0.6; pitch = 0.32; zoom = 1;
      if (listEl) listEl.querySelectorAll("button").forEach(function (x) { x.classList.remove("on"); });
      if (stepsEl) stepsEl.querySelectorAll("[data-step]").forEach(function (x) { x.classList.remove("on"); });
    });

    // ---------- camera ----------
    var yaw = opts.yaw != null ? opts.yaw : 0.6, pitch = opts.pitch != null ? opts.pitch : 0.32, zoom = opts.zoom || 1, dragging = false, lx = 0, ly = 0;
    function fitCamera() { place(); }
    canvas.addEventListener("pointerdown", function (e) { dragging = true; lx = e.clientX; ly = e.clientY; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      yaw -= (e.clientX - lx) * 0.008; pitch = Math.max(-0.2, Math.min(1.35, pitch + (e.clientY - ly) * 0.006));
      lx = e.clientX; ly = e.clientY;
    });
    canvas.addEventListener("pointerup", function () { dragging = false; });
    canvas.addEventListener("pointercancel", function () { dragging = false; });
    canvas.addEventListener("wheel", function (e) { e.preventDefault(); zoom = Math.max(0.35, Math.min(2.5, zoom * (e.deltaY > 0 ? 1.08 : 0.93))); }, { passive: false });
    function resize() {
      var w = canvas.clientWidth, h = canvas.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    }
    window.addEventListener("resize", resize); resize();
    var visible = true;
    if ("IntersectionObserver" in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; }).observe(canvas);
    var last = performance.now();
    function frame(now) {
      requestAnimationFrame(frame);
      if (!visible) { last = now; return; }
      var dt = Math.max(0, Math.min(0.05, (now - last) / 1000)); last = now;
      if (Math.abs(target - explode) > 0.001) { explode += (target - explode) * Math.min(1, dt * 6); place(); }
      var span = size * (1 + explode * 1.2);
      var dist = (span / (2 * Math.tan(camera.fov * Math.PI / 360))) * zoom * (camera.aspect < 1 ? 1.5 : 1.05);
      camera.position.set(centre.x + Math.sin(yaw) * Math.cos(pitch) * dist, centre.y + Math.sin(pitch) * dist, centre.z + Math.cos(yaw) * Math.cos(pitch) * dist);
      camera.lookAt(centre);
      renderer.render(scene, camera);
    }
    requestAnimationFrame(frame);
  };
})();
