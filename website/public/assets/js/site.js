/* Terminal 1 — site behaviour. Vanilla JS, no dependencies. */
(function () {
  'use strict';

  // The one place the repository URL lives. Every [data-repo] link is built from it.
  var REPO_URL = 'https://github.com/mmuhlariholdings/terminal-1';

  var MODEL_VIEWER_URL = 'https://cdn.jsdelivr.net/npm/@google/model-viewer@3.5.0/dist/model-viewer.min.js';

  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

  /* ---------- repository links ---------- */
  $$('[data-repo]').forEach(function (a) {
    a.href = REPO_URL + a.getAttribute('data-repo');
  });

  /* ---------- nav ---------- */
  var nav = $('.nav');
  var menuBtn = $('.nav__menu-btn');
  function setMenu(open) {
    nav.classList.toggle('is-open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
  }
  menuBtn.addEventListener('click', function () { setMenu(!nav.classList.contains('is-open')); });
  $$('.nav__links a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) { setMenu(false); menuBtn.focus(); }
  });

  /* ---------- reveal on scroll ---------- */
  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
    });
  }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 }) : null;
  $$('.reveal, .rm-row, .battery-meter').forEach(function (el) {
    if (io && !reduceMotion) io.observe(el); else el.classList.add('is-in');
  });

  /* ---------- statement: words light up as you scroll ---------- */
  var statement = $('[data-words]');
  var words = [];
  if (statement && !reduceMotion) {
    var split = function (node, extra) {
      Array.prototype.slice.call(node.childNodes).forEach(function (child) {
        if (child.nodeType === 3) {
          var frag = document.createDocumentFragment();
          child.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(part)); return; }
            var s = document.createElement('span');
            s.className = 'w' + (extra ? ' ' + extra : '');
            s.textContent = part;
            frag.appendChild(s);
            words.push(s);
          });
          node.replaceChild(frag, child);
        } else if (child.nodeType === 1) {
          split(child, child.classList.contains('hl') ? 'hl' : extra);
        }
      });
    };
    split(statement);
  }

  /* ---------- exploded stack ---------- */
  var explode = $('#explode');
  var stack = $('#stack');
  var plates = $$('.plate', stack);
  var legend = $$('#stack-legend li');
  var lastActive = -1;
  function setActiveLayer(n) {
    if (n === lastActive) return;
    lastActive = n;
    legend.forEach(function (li, i) { li.classList.toggle('is-active', i === n); });
    var layer = n >= 0 && legend[n] ? Number(legend[n].getAttribute('data-layer')) : -1;
    plates.forEach(function (p) { p.classList.toggle('is-active', Number(p.style.getPropertyValue('--i')) === layer); });
  }
  if (reduceMotion && stack) { stack.style.setProperty('--p', '1'); }

  /* ---------- scroll loop (one rAF per frame) ---------- */
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  }
  function update() {
    ticking = false;
    var vh = window.innerHeight;
    nav.classList.toggle('is-scrolled', window.scrollY > 8);

    if (words.length) {
      var r = statement.getBoundingClientRect();
      var p = clamp((vh * 0.82 - r.top) / (vh * 0.35 + r.height), 0, 1);
      var lit = Math.round(p * words.length);
      for (var i = 0; i < words.length; i++) words[i].classList.toggle('is-lit', i < lit);
    }

    if (explode && stack && !reduceMotion) {
      var er = explode.getBoundingClientRect();
      var ep;
      var sticky = window.matchMedia('(min-width: 901px)').matches;
      if (sticky) {
        ep = clamp(-er.top / Math.max(1, er.height - vh), 0, 1);
      } else {
        var st = $('.stack-stage').getBoundingClientRect();
        ep = clamp((vh - st.top) / (vh * 0.9), 0, 1);
      }
      var spread = clamp((ep - 0.05) / 0.55, 0, 1);
      spread = spread * spread * (3 - 2 * spread); // smoothstep
      stack.style.setProperty('--p', spread.toFixed(4));
      if (sticky) setActiveLayer(ep < 0.08 ? -1 : Math.min(legend.length - 1, Math.floor((ep - 0.08) / 0.84 * legend.length)));
      else setActiveLayer(-1);
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  update();

  /* ---------- terminal demo ---------- */
  var termBody = $('#term-body');
  var tabs = $$('.scene-tab');
  var clock = $('#term-clock');
  if (clock) {
    var tick = function () {
      var d = new Date();
      clock.textContent = 't1 · ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    };
    tick();
    setInterval(tick, 30000);
  }

  var esc = function (s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); };
  // A line is a string, or an array of [className, text] segments.
  var html = function (line) {
    if (typeof line === 'string') return esc(line);
    return line.map(function (seg) {
      return seg[0] ? '<span class="' + seg[0] + '">' + esc(seg[1]) + '</span>' : esc(seg[1]);
    }).join('');
  };
  var LOCAL = [['t-p', 't1 '], ['t-d', '~'], ['t-p', ' ❯ ']];
  var LOCAL_API = [['t-p', 't1 '], ['t-d', '~/api'], ['t-p', ' ❯ ']];
  var REMOTE = [['t-p', 'ops@build-01'], ['', ':'], ['t-d', '~'], ['', '$ ']];

  var SCENES = [
    [
      { prompt: LOCAL, cmd: 'ssh ops@build-01' },
      { out: [
        [['t-m', 'Linux build-01 6.1.0-28-amd64 x86_64 GNU/Linux']],
        [['t-m', 'Last login: Mon Nov 16 08:42:11 2026 from 10.0.4.17']]
      ], wait: 500 },
      { prompt: REMOTE, cmd: 'uptime' },
      { out: [' 09:41:07 up 41 days,  3:12,  1 user,  load average: 0.08, 0.11, 0.09'], wait: 250 },
      { prompt: REMOTE, cmd: 'systemctl is-active nginx' },
      { out: [[['t-p', 'active']]], wait: 250 },
      { prompt: REMOTE, cmd: 'tail -n 3 /var/log/nginx/access.log' },
      { out: [
        [['t-m', '10.0.4.17 - - [16/Nov/2026:09:40:58] '], ['', '"GET /healthz HTTP/1.1" '], ['t-p', '200']],
        [['t-m', '10.0.4.17 - - [16/Nov/2026:09:41:02] '], ['', '"GET /api/orders HTTP/1.1" '], ['t-p', '200']],
        [['t-m', '10.0.4.22 - - [16/Nov/2026:09:41:05] '], ['', '"POST /api/orders HTTP/1.1" '], ['t-p', '201']]
      ], wait: 300 },
      { prompt: REMOTE, cmd: '' }
    ],
    [
      { prompt: LOCAL, cmd: 'az login --use-device-code' },
      { out: [
        'To sign in, use a web browser to open the page',
        [['t-d', 'https://microsoft.com/devicelogin'], ['', ' and enter the code '], ['t-a', 'H4QK7ZP2W']],
        'to authenticate.'
      ], wait: 1600 },
      { out: [
        '',
        [['t-m', 'Retrieving tenants and subscriptions for the selection...']],
        '',
        [['t-b', 'No     Subscription name    Tenant']],
        [['t-m', '-----  -------------------  -----------------------']],
        [['t-p', '[1] *  Production           contoso.onmicrosoft.com']],
        '[2]    Staging              contoso.onmicrosoft.com',
        ''
      ], wait: 700 },
      { prompt: [['', 'Select a subscription and tenant (Enter for no changes): ']], cmd: '1' },
      { out: [
        '',
        [['t-m', 'Tenant: '], ['', 'contoso.onmicrosoft.com']],
        [['t-m', 'Subscription: '], ['', 'Production']]
      ], wait: 300 },
      { prompt: LOCAL, cmd: 'az group list -o table' },
      { out: [
        [['t-b', 'Name             Location     Status']],
        [['t-m', '---------------  -----------  ---------']],
        'rg-api-prod      uksouth      Succeeded',
        'rg-data-prod     uksouth      Succeeded'
      ], wait: 300 },
      { prompt: LOCAL, cmd: '' }
    ],
    [
      { prompt: LOCAL_API, cmd: 'claude' },
      { out: [
        [['t-c', '╭─────────────────────────────────────────────╮']],
        [['t-c', '│ '], ['t-c', '✻'], ['t-b', ' Welcome to Claude Code'], ['t-c', '                     │']],
        [['t-c', '│ '], ['t-m', '  cwd: ~/api'], ['t-c', '                                │']],
        [['t-c', '╰─────────────────────────────────────────────╯']],
        ''
      ], wait: 500 },
      { prompt: [['t-m', '> ']], cmd: 'the orders test fails on CI. can you take a look?' },
      { out: [''], wait: 500 },
      { out: [[['t-c', '● '], ['t-b', 'Read'], ['', '(tests/test_orders.py)']]], wait: 600 },
      { out: [[['t-c', '● '], ['t-b', 'Bash'], ['', '(pytest tests/test_orders.py -q)']], [['t-m', '  ⎿ '], ['t-a', '1 failed'], ['t-m', ', 11 passed']]], wait: 900 },
      { out: [[['t-c', '● '], ['', 'The fixture uses a fixed date that is now in the past.']], [['', '  Making it relative to today.']]], wait: 900 },
      { out: [[['t-c', '● '], ['t-b', 'Update'], ['', '(tests/conftest.py)'], ['t-m', '  +3 −1']]], wait: 700 },
      { out: [[['t-c', '● '], ['t-b', 'Bash'], ['', '(pytest -q)']], [['t-m', '  ⎿ '], ['t-p', '12 passed']]], wait: 800 },
      { out: [''], wait: 200 },
      { prompt: [['t-m', '> ']], cmd: '' }
    ]
  ];

  function finalLines(scene) {
    var lines = [];
    scene.forEach(function (step) {
      if (step.prompt) lines.push(html(step.prompt) + esc(step.cmd));
      if (step.out) step.out.forEach(function (l) { lines.push(html(l)); });
    });
    return lines;
  }

  var CURSOR = '<span class="t-cursor"></span>';
  var current = 0;
  var runId = 0;
  var termVisible = false;

  function selectTab(n) {
    tabs.forEach(function (t, i) {
      t.setAttribute('aria-pressed', String(i === n));
      var bar = $('.progress i', t);
      if (bar) bar.style.width = '0%';
    });
  }
  function setProgress(n, frac) {
    var bar = tabs[n] && $('.progress i', tabs[n]);
    if (bar) bar.style.width = (frac * 100).toFixed(1) + '%';
  }

  function sleep(ms, id) {
    return new Promise(function (resolve, reject) {
      var wait = function () {
        if (id !== runId) return reject('cancelled');
        if (!termVisible || document.hidden) return setTimeout(wait, 250);
        setTimeout(function () { id === runId ? resolve() : reject('cancelled'); }, ms);
      };
      wait();
    });
  }

  function play(n) {
    var id = ++runId;
    current = n;
    selectTab(n);
    var scene = SCENES[n];
    if (reduceMotion) {
      termBody.innerHTML = finalLines(scene).join('\n') + CURSOR;
      return;
    }
    var lines = [];
    var render = function (tail) { termBody.innerHTML = lines.join('\n') + (lines.length ? '\n' : '') + (tail || ''); };
    var i = 0;
    var next = function () {
      if (id !== runId) return;
      setProgress(n, i / scene.length);
      if (i >= scene.length) {
        return sleep(2600, id).then(function () { play((n + 1) % SCENES.length); }, function () {});
      }
      var step = scene[i++];
      if (step.prompt) {
        var head = html(step.prompt);
        var typed = '';
        var chars = Array.from(step.cmd);
        render(head + CURSOR);
        var k = 0;
        var typeChar = function () {
          if (k >= chars.length) {
            if (!step.cmd) { setProgress(n, 1); return next(); }
            return sleep(380, id).then(function () { lines.push(head + esc(typed)); render(); next(); }, function () {});
          }
          typed += chars[k++];
          render(head + esc(typed) + CURSOR);
          sleep(38 + Math.random() * 55, id).then(typeChar, function () {});
        };
        sleep(step.cmd ? 420 : 0, id).then(typeChar, function () {});
      } else if (step.out) {
        var j = 0;
        var outLine = function () {
          if (j >= step.out.length) return sleep(step.wait || 0, id).then(next, function () {});
          lines.push(html(step.out[j++]));
          render();
          sleep(55, id).then(outLine, function () {});
        };
        outLine();
      }
    };
    termBody.innerHTML = CURSOR;
    sleep(200, id).then(next, function () {});
  }

  if (termBody) {
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { play(i); });
    });
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) { termVisible = en[0].isIntersecting; }, { threshold: 0.15 }).observe(termBody.parentNode);
    } else termVisible = true;
    play(0);
  }

  /* ---------- keyboard nav-row demo ---------- */
  var navrow = $('.navrow');
  if (navrow && !reduceMotion && 'IntersectionObserver' in window) {
    var keys = $$('[data-key]', navrow);
    var seq = [0, 2, 2, 3, 1, 4];
    var step = 0;
    var timer = null;
    var pressOnce = function () {
      keys.forEach(function (k) { k.classList.remove('is-down', 'is-active'); });
      var k = keys[seq[step++ % seq.length]];
      k.classList.add(k.classList.contains('trackpad') ? 'is-active' : 'is-down');
      setTimeout(function () { k.classList.remove('is-down', 'is-active'); }, 520);
    };
    new IntersectionObserver(function (en) {
      if (en[0].isIntersecting && !timer) timer = setInterval(pressOnce, 900);
      else if (!en[0].isIntersecting && timer) { clearInterval(timer); timer = null; }
    }, { threshold: 0.5 }).observe(navrow);
  }

  /* ---------- 3D model (graceful when the .glb is not exported yet) ---------- */
  var stage = $('#model-stage');
  if (stage) {
    var mv = $('#model-viewer');
    var note = $('#model-note');
    var noteText = $('#model-note-text');
    var src = stage.getAttribute('data-src');
    var setState = function (state, text) {
      stage.setAttribute('data-state', state);
      if (text) noteText.textContent = text;
      note.hidden = state === 'ready';
    };
    var fallback = function () { setState('fallback', '3D model coming with the first CAD export'); };

    var loadScript = function () {
      return new Promise(function (resolve, reject) {
        if (window.customElements && customElements.get('model-viewer')) return resolve();
        var s = document.createElement('script');
        s.type = 'module';
        s.src = MODEL_VIEWER_URL;
        s.onerror = reject;
        document.head.appendChild(s);
        customElements.whenDefined('model-viewer').then(resolve);
        setTimeout(function () { reject('timeout'); }, 15000);
      });
    };

    var start = function () {
      fetch(src, { method: 'HEAD', cache: 'no-store' }).then(function (r) {
        var type = r.headers.get('content-type') || '';
        if (!r.ok || type.indexOf('text/html') !== -1) throw new Error('no model');
        setState('loading', 'Loading the 3D model…');
        return loadScript();
      }).then(function () {
        if (reduceMotion) mv.removeAttribute('auto-rotate');
        mv.addEventListener('load', function () {
          setState('ready');
          var anims = mv.availableAnimations || [];
          if (anims.length) {
            var name = anims.filter(function (a) { return /explod|layer/i.test(a); })[0] || anims[0];
            var btn = $('#explode-btn');
            $('#model-toolbar').hidden = false;
            btn.hidden = false;
            btn.addEventListener('click', function () {
              var on = btn.getAttribute('aria-pressed') !== 'true';
              btn.setAttribute('aria-pressed', String(on));
              mv.animationName = name;
              mv.timeScale = on ? 1 : -1;
              if (!on) mv.currentTime = mv.duration;
              mv.play({ repetitions: 1 });
            });
          }
        }, { once: true });
        mv.addEventListener('error', fallback, { once: true });
        mv.src = src;
      }).catch(fallback);
    };

    if ('IntersectionObserver' in window) {
      var mio = new IntersectionObserver(function (en) {
        if (en[0].isIntersecting) { mio.disconnect(); start(); }
      }, { rootMargin: '800px 0px' });
      mio.observe(stage);
    } else start();
  }
})();
