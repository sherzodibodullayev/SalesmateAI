/* ---------------------------------------------------------------------------
   Site chrome: sticky masthead, mobile nav, scroll reveal, the market chart,
   and the floating agent shell.

   The chat client itself lives in chat.js and drives both the panel here and
   the /demo page — the panel deliberately carries the same element ids.
   ------------------------------------------------------------------------- */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- masthead ---------------------------------------------------------- */
  /* Transparent over the sky, frosted once the page has moved. The threshold
     is small on purpose: the pill has to earn its background before the hero
     type scrolls under it, or the two collide mid-transition. */

  var masthead = document.getElementById('masthead');
  if (masthead) {
    var stick = function () {
      masthead.classList.toggle('is-stuck', window.scrollY > 24);
    };
    stick();
    window.addEventListener('scroll', stick, { passive: true });
  }

  /* --- mobile nav -------------------------------------------------------- */

  var toggle = document.getElementById('navtoggle');
  var nav = document.getElementById('nav');
  if (toggle && nav) {
    var setNav = function (open) {
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
    };

    toggle.addEventListener('click', function () {
      setNav(toggle.getAttribute('aria-expanded') !== 'true');
    });

    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') setNav(false);
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setNav(false);
    });

    // Tapping anywhere else closes it. Without this the menu covers the page
    // and the only way out is the toggle, which is now behind the panel.
    document.addEventListener('click', function (e) {
      if (!nav.contains(e.target) && !toggle.contains(e.target)) setNav(false);
    });
  }

  /* --- scroll reveal ----------------------------------------------------- */

  var revealables = [].slice.call(document.querySelectorAll('.reveal'));

  function revealAll() {
    revealables.forEach(function (el) { el.classList.add('is-in'); });
  }

  if (reduced || !('IntersectionObserver' in window)) {
    revealAll();
  } else {
    // Failsafe: if the observer never fires, show everything anyway. A page
    // that stays blank is a far worse failure than one that skips an animation.
    setTimeout(revealAll, 4000);

    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        seen.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });

    // Stagger siblings so a row of cards arrives as one gesture, not three.
    var groups = {};
    revealables.forEach(function (el) {
      var key = el.parentNode.className || 'root';
      groups[key] = (groups[key] || 0) + 1;
      el.style.transitionDelay = Math.min(groups[key] - 1, 4) * 90 + 'ms';
      seen.observe(el);
    });
  }

  /* --- the market chart -------------------------------------------------- */
  /* Three metrics over the same five analyst firms. Bars are scaled to the
     largest value in the metric being shown, not to a fixed ceiling — the
     forecast column spans 68 to 222, and a shared axis would flatten the
     growth column into nothing. */

  var bench = document.getElementById('bench');
  if (bench) {
    var rows = [].slice.call(bench.querySelectorAll('.bench__row'));

    var draw = function (metric) {
      var values = rows.map(function (r) {
        return parseFloat(r.getAttribute('data-v-' + metric)) || 0;
      });
      var max = Math.max.apply(null, values) || 1;

      rows.forEach(function (row, i) {
        // Floor at 4% so the smallest bar is still visibly a bar.
        var pct = Math.max(4, (values[i] / max) * 100);
        row.querySelector('.bench__fill').style.width = pct + '%';
        row.querySelector('.bench__val').textContent = row.getAttribute('data-l-' + metric);
      });
    };

    bench.querySelectorAll('.bench__tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        bench.querySelectorAll('.bench__tab').forEach(function (t) { t.classList.remove('is-on'); });
        tab.classList.add('is-on');
        draw(tab.getAttribute('data-metric'));
      });
    });

    // Bars fill on the way in rather than on load, so the animation is seen.
    var start = function () { draw('cagr'); };
    if (reduced || !('IntersectionObserver' in window)) {
      start();
    } else {
      var watch = new IntersectionObserver(function (entries) {
        if (!entries[0].isIntersecting) return;
        start();
        watch.disconnect();
      }, { threshold: 0.25 });
      watch.observe(bench);
    }
  }

  /* --- floating agent ---------------------------------------------------- */
  /* The panel holds the same element ids as the /demo page, so chat.js is the
     only chat client on the site. This just opens and closes the shell. */

  var fab = document.getElementById('chatfab');
  var panel = document.getElementById('chatpanel');
  if (fab && panel) {
    var setPanel = function (open) {
      panel.hidden = !open;
      fab.setAttribute('aria-expanded', String(open));
      fab.classList.toggle('is-open', open);
      document.body.classList.toggle('chat-open', open);
      if (open) {
        // A restored thread was measured while the panel was hidden, so it has
        // no scroll position yet — land on the newest message, not the top of
        // last week's conversation.
        var thread = document.getElementById('thread');
        if (thread) thread.scrollTop = thread.scrollHeight;

        // Let the panel paint before focusing, or iOS scrolls the page instead.
        requestAnimationFrame(function () {
          var input = document.getElementById('input');
          if (input && window.innerWidth > 720) input.focus();
        });
      }
    };

    fab.addEventListener('click', function () { setPanel(panel.hidden); });

    var closeBtn = document.getElementById('chatclose');
    if (closeBtn) closeBtn.addEventListener('click', function () { setPanel(false); fab.focus(); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) { setPanel(false); fab.focus(); }
    });

    // Every "talk to the agent" link in the page body opens the panel instead
    // of navigating away — the whole pitch is that the agent is right here.
    // /demo stays reachable from the masthead and for anyone landing on it.
    document.querySelectorAll('main a[href="/demo"]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        setPanel(true);
      });
    });
  }

  /* --- in-page anchors, offset for the floating masthead ----------------- */

  document.querySelectorAll('a[data-scroll]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var target = document.querySelector(link.getAttribute('href').replace(/^\//, ''));
      if (!target) return;
      e.preventDefault();
      var top = target.getBoundingClientRect().top + window.scrollY - 92;
      window.scrollTo({ top: top, behavior: reduced ? 'auto' : 'smooth' });
    });
  });
})();
