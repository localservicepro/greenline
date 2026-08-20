/* Greenline Services — shared site behaviour */
(function () {
  "use strict";

  /* Header scroll state (skipped on pages that force a solid header) */
  var header = document.querySelector('.site-header');
  if (header && !header.classList.contains('solid')) {
    var onScroll = function () {
      header.classList.toggle('scrolled', window.scrollY > 40);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* Services dropdown: hover on pointer devices, click everywhere */
  var dd = document.querySelector('.nav-dropdown');
  function closeDD() {
    if (!dd) return;
    dd.classList.remove('open');
    dd.querySelector('.nav-trigger').setAttribute('aria-expanded', 'false');
  }
  if (dd) {
    var trigger = dd.querySelector('.nav-trigger');
    var openDD = function () {
      dd.classList.add('open');
      trigger.setAttribute('aria-expanded', 'true');
    };
    if (window.matchMedia('(hover: hover)').matches) {
      // Pointer devices: hover opens it, focus opens it for keyboard users, and
      // activating the trigger goes to the services hub rather than fighting the
      // hover state by toggling it shut again.
      dd.addEventListener('mouseenter', openDD);
      dd.addEventListener('mouseleave', closeDD);
      dd.addEventListener('focusin', openDD);
      dd.addEventListener('focusout', function (e) {
        if (!dd.contains(e.relatedTarget)) closeDD();
      });
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        window.location.href = '/services/';
      });
    } else {
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        dd.classList.contains('open') ? closeDD() : openDD();
      });
    }
    document.addEventListener('click', function (e) {
      if (!dd.contains(e.target)) closeDD();
    });
  }

  /* Mobile nav */
  var burger = document.querySelector('.nav-burger');
  var scrim = document.querySelector('.scrim');
  function closeMobile() {
    document.body.classList.remove('mobile-open');
    if (burger) burger.setAttribute('aria-expanded', 'false');
    if (scrim) scrim.hidden = true;
  }
  if (burger && scrim) {
    burger.addEventListener('click', function () {
      var open = document.body.classList.toggle('mobile-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      scrim.hidden = !open;
    });
    scrim.addEventListener('click', closeMobile);
    document.querySelectorAll('.mobile-nav a').forEach(function (a) {
      a.addEventListener('click', closeMobile);
    });
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDD(); closeMobile(); }
  });

  /* Mobile services accordion */
  var accBtn = document.querySelector('.acc-btn');
  var accBody = document.querySelector('.acc-body');
  if (accBtn && accBody) {
    accBtn.addEventListener('click', function () {
      var open = accBody.classList.toggle('open');
      accBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      accBtn.querySelector('span').textContent = open ? '−' : '+';
    });
  }

  /* FAQ accordion */
  document.querySelectorAll('.faq-q').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var faq = btn.parentElement;
      var body = btn.nextElementSibling;
      var isOpen = faq.classList.toggle('open');
      body.classList.toggle('open', isOpen);
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  });

  /* Quote popup.
     Triggers carry data-quote-open. On the contact page there is no modal —
     the form lives in the hero — so the trigger falls back to scrolling there,
     and to /contact/ if the page has no form at all. */
  var modal = document.getElementById('quote-modal');
  var lastFocused = null;

  function focusables() {
    return Array.prototype.filter.call(
      modal.querySelectorAll('button, [href], input, select, textarea'),
      function (el) { return !el.disabled && el.offsetParent !== null; });
  }

  function openModal() {
    lastFocused = document.activeElement;
    modal.hidden = false;
    document.body.classList.add('modal-open');
    var first = modal.querySelector('input, select, textarea');
    if (first) first.focus();
  }

  function closeModal() {
    modal.hidden = true;
    document.body.classList.remove('modal-open');
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  document.querySelectorAll('[data-quote-open]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (modal) {
        e.preventDefault();
        openModal();
        return;
      }
      var inline = document.getElementById('quote');
      if (inline) {
        e.preventDefault();
        inline.scrollIntoView({ behavior: 'smooth', block: 'start' });
        var field = inline.querySelector('input, select, textarea');
        if (field) setTimeout(function () { field.focus({ preventScroll: true }); }, 450);
      }
      /* no modal and no inline form: let the href carry them to /contact/ */
    });
  });

  if (modal) {
    modal.querySelectorAll('[data-quote-close]').forEach(function (el) {
      el.addEventListener('click', closeModal);
    });
    modal.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { closeModal(); return; }
      if (e.key !== 'Tab') return;
      var items = focusables();
      if (!items.length) return;
      var first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    });
  }

  /* Before/after comparison slider.
     The wipe is driven by a real <input type="range">, so keyboard and
     assistive tech work without any extra handling. The track is a native
     scroll-snap container, so swipe and scroll work with JS disabled — the
     arrows and dots below are enhancement only. */
  document.querySelectorAll('.ba').forEach(function (ba) {
    var range = ba.querySelector('.ba-range');
    if (!range) return;
    var apply = function () { ba.style.setProperty('--pos', range.value + '%'); };
    range.addEventListener('input', apply);
    apply();
  });

  document.querySelectorAll('[data-ba-slider]').forEach(function (slider) {
    var track = slider.querySelector('[data-ba-track]');
    var prev = slider.querySelector('[data-ba-prev]');
    var next = slider.querySelector('[data-ba-next]');
    var dots = Array.prototype.slice.call(slider.querySelectorAll('[data-ba-go]'));
    var slides = Array.prototype.slice.call(slider.querySelectorAll('.ba-slide'));
    if (!track || !slides.length) return;

    function current() {
      var i = Math.round(track.scrollLeft / track.clientWidth);
      return Math.max(0, Math.min(slides.length - 1, i));
    }
    function goTo(i) {
      i = Math.max(0, Math.min(slides.length - 1, i));
      track.scrollTo({ left: i * track.clientWidth, behavior: 'smooth' });
    }
    function sync() {
      var i = current();
      dots.forEach(function (d, n) {
        d.classList.toggle('is-on', n === i);
        if (n === i) d.setAttribute('aria-current', 'true');
        else d.removeAttribute('aria-current');
      });
      if (prev) prev.disabled = i === 0;
      if (next) next.disabled = i === slides.length - 1;
    }

    if (prev) prev.addEventListener('click', function () { goTo(current() - 1); });
    if (next) next.addEventListener('click', function () { goTo(current() + 1); });
    dots.forEach(function (d) {
      d.addEventListener('click', function () { goTo(+d.getAttribute('data-ba-go')); });
    });

    var tick;
    track.addEventListener('scroll', function () {
      clearTimeout(tick);
      tick = setTimeout(sync, 90);
    }, { passive: true });
    window.addEventListener('resize', sync);
    sync();
  });

  /* Thank-you page: the default form action is a GET, so the visitor's details
     arrive in the query string. Clear them from the address bar once the page
     has settled, so lead data does not sit in browser history or leak through
     the referrer. The delay leaves analytics and tracking scripts time to read
     the URL first. Switching FORM_ACTION to a POST endpoint makes this moot. */
  if (window.location.pathname.indexOf('/thank-you') === 0 && window.location.search) {
    window.addEventListener('load', function () {
      setTimeout(function () {
        if (window.history.replaceState) {
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      }, 1500);
    });
  }

  /* The quote form is deliberately left alone.
     GoHighLevel's external tracking script captures the native submit event,
     so nothing here may call preventDefault() or otherwise block submission.
     Validation is handled by the browser via the `required` attributes, and
     the form's own action carries the visitor to /thank-you/. */
})();
