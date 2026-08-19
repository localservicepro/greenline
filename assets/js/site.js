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

  /* Quote form -> pre-filled email.
     Swap this for a real form endpoint (Formspree, Netlify Forms, etc.)
     once the domain and hosting are live. */
  document.querySelectorAll('form.quote-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      var get = function (k) { return (data.get(k) || '').toString().trim(); };
      var body = 'Name: ' + get('name')
        + '\nPhone: ' + get('phone')
        + '\nEmail: ' + get('email')
        + '\nSuburb: ' + get('suburb')
        + '\nService: ' + get('service')
        + '\n\nDetails:\n' + get('message');
      window.location.href = 'mailto:davidcoelho92@hotmail.com'
        + '?subject=' + encodeURIComponent('Quote request - ' + get('service') + ' - ' + get('suburb'))
        + '&body=' + encodeURIComponent(body);
    });
  });
})();
