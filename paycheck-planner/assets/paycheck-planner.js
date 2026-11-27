/* Paycheck Planner pages: GA4 events (the site's existing GA4 tag only, via window.gtag from _includes/ga4.html).
   buy_click and begin_checkout on Buy buttons are sent by the site-wide listener in _includes/ga4.html for every
   a[href^="https://buy.stripe.com/"], so every Buy button here is a plain Stripe link. This file adds:
   view_item (sales and bundle pages), sign_up (sample page), and generate_lead (sales and bundle signup). It does not rewrite links on load. On click only, section 1b appends client_reference_id (with the source page) and the page's utm_* to the Stripe link; in QA mode (cdk_qa) it records the click but does not open Stripe.
   There is no purchase event: Stripe's hosted confirmation screen never returns to this site, so nothing here can see a purchase. No other scripts, no cookies. */
(function () {
  'use strict';
  var PRODUCTS = {
    planner: { item_id: 'paycheck-planner', item_name: 'Paycheck Planner', price: 14.99, item_category: 'digital download' },
    bundle: { item_id: 'paycheck-planner-plus-bundle', item_name: 'Paycheck Planner Plus Bundle', price: 39.00, item_category: 'digital download' }
  };
  var page = document.body.getAttribute('data-pp-page') || '';

  function send(name, params) {
    if (typeof window.gtag !== 'function') return false;
    try { window.gtag('event', name, params); return true; } catch (err) { return false; }
  }
  function item(key, listId) {
    var p = PRODUCTS[key];
    return { item_id: p.item_id, item_name: p.item_name, item_category: p.item_category, item_list_id: listId, price: p.price, quantity: 1 };
  }

  // 1. view_item on the sales page (and the bundle page).
  if (page === 'sales') {
    send('view_item', { currency: 'USD', value: PRODUCTS.planner.price, items: [item('planner', 'paycheck-planner'), item('bundle', 'paycheck-planner')] });
  } else if (page === 'bundle') {
    send('view_item', { currency: 'USD', value: PRODUCTS.bundle.price, items: [item('bundle', 'paycheck-planner-bundle')] });
  }

  // 1a-0. Light video: video[data-pp-video][data-src] ships with preload="none" and no source, so the poster paints first.
  // The MP4 is attached only when the element is near the viewport (IntersectionObserver; load-event fallback if that
  // API is missing) and never when the visitor prefers reduced motion. No JS: the poster stays.
  function attachOneVideo(v) {
    var src = v.getAttribute('data-src');
    if (!src) return;
    v.removeAttribute('data-src');
    v.src = src; v.load();
    var pr = v.play(); if (pr && pr.catch) pr.catch(function () {});
  }
  function attachVideos() {
    try {
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      var nodes = document.querySelectorAll('video[data-pp-video][data-src]');
      if (!nodes.length) return;
      if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
          Array.prototype.forEach.call(entries, function (en) {
            if (!en.isIntersecting) return;
            io.unobserve(en.target);
            attachOneVideo(en.target);
          });
        }, { root: null, rootMargin: '200px 0px', threshold: 0 });
        Array.prototype.forEach.call(nodes, function (v) { io.observe(v); });
      } else {
        Array.prototype.forEach.call(nodes, attachOneVideo);
      }
    } catch (err) {}
  }
  if (document.readyState === 'complete') { setTimeout(attachVideos, 0); } else { window.addEventListener('load', function () { setTimeout(attachVideos, 0); }); }

  // 1a. Reduced motion: video[data-pp-video] shows its poster only (no autoplay, no loop) when the visitor prefers reduced motion.
  try {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      Array.prototype.forEach.call(document.querySelectorAll('video[data-pp-video]'), function (v) {
        v.removeAttribute('autoplay'); v.removeAttribute('loop'); v.pause();
      });
    }
  } catch (err) {}

  // 1c. Mobile sticky Buy bar (checkout audit 1127). #pp-sticky ships hidden; it shows whenever the hero Buy button
  // (#pp-buy-planner) is not fully on screen (small phones, in-app browsers, or after scrolling), and hides while it is. CSS hides it at 760px and wider. No JS or no
  // IntersectionObserver: the bar stays hidden and the in-page Buy buttons still work.
  try {
    var stickyBar = document.getElementById('pp-sticky');
    var heroBuy = document.getElementById('pp-buy-planner');
    if (stickyBar && heroBuy && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        var show = entries[0].intersectionRatio < 0.99;
        stickyBar.hidden = !show;
        document.body.classList.toggle('pp-has-sticky', show);
      }, { root: null, threshold: [0, 0.99, 1] }).observe(heroBuy);
    }
  } catch (err) {}

  // 1b. Buy attribution (progressive enhancement). The href in the HTML stays the plain Payment Link. On click only:
  // (a) a window CAPTURE listener runs before the site-wide GA listener in _includes/ga4.html and stores an opaque random id in
  //     data-client-ref and calls gtag('set', { client_reference_id }) so the site-wide buy_click and begin_checkout events that follow in
//     _includes/ga4.html (left unchanged) carry it; those events still read the plain href;
  // (b) a window BUBBLE listener runs after GA and only then appends client_reference_id and any utm_* from the page URL to the
  //     link, so the browser navigates to the enhanced URL. No PII, no cookies, no storage. The id starts with qa_ when the
  //     existing cdk_qa localStorage flag is on, so QA clicks stay separable from buyers.
  //     The id is <pp|qa>_<source page>_<24 hex>, source page one of home, sales, bundle, sample, other (from the URL path), at most
  //     34 characters of [a-z0-9_], inside Stripe's client_reference_id limit (200 characters; letters, digits, dashes, underscores).
  //     Checkout audit 1127: when the click looks automated, ax_ is added before the hex (<pp|qa>_<page>_ax_<24 hex>, at most 37
  //     characters). Automated means any of: the click event is not trusted (script click), navigator.webdriver is true (browser
  //     automation, including our own Playwright QA), the user agent names a known crawler or headless browser, or the click came
  //     less than 2 seconds after the page loaded. The same reason goes to GA as pp_suspect. Real visitors are unchanged.
  // (c) QA mode (cdk_qa=1): GA still records buy_click and begin_checkout exactly as for a buyer (the GA listener runs first and is
  //     unchanged), but the bubble listener cancels the navigation, so a QA click never opens or creates a Stripe Checkout session,
  //     and shows a small QA-only notice next to the button. Real visitors (no cdk_qa flag) are unchanged.
  var UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
  var refId = '';
  var suspect = '';
  var loadedAt = Date.now();
  var buyAt = 0;
  var BOT_UA = /bot|crawl|spider|slurp|headless|lighthouse|inspectiontool|mediapartners|facebookexternalhit|bingpreview|preview|scanner|python|curl|wget/i;
  function suspectReason(e) {
    try {
      if (e && e.isTrusted === false) return 'untrusted_click';
      if (window.navigator && window.navigator.webdriver) return 'webdriver';
      if (BOT_UA.test(String((window.navigator && window.navigator.userAgent) || ''))) return 'bot_ua';
      if (Date.now() - loadedAt < 2000) return 'fast_click';
    } catch (err) {}
    return '';
  }
  function newRef(e) {
    if (refId) return refId;
    suspect = suspectReason(e);
    var hex = '';
    try {
      var buf = new Uint8Array(12); window.crypto.getRandomValues(buf);
      for (var i = 0; i < buf.length; i++) hex += ('0' + buf[i].toString(16)).slice(-2);
    } catch (err) {
      while (hex.length < 24) hex += Math.floor(Math.random() * 16).toString(16);
    }
    var qa = false;
    try { qa = window.localStorage.getItem('cdk_qa') === '1'; } catch (err) {}
    refId = (qa ? 'qa_' : 'pp_') + sourcePage() + '_' + (suspect ? 'ax_' : '') + hex;
    return refId;
  }
  function sourcePage() {
    var path = '/';
    try { path = String(window.location.pathname || '/').replace(/index\.html$/, ''); } catch (err) {}
    if (path.charAt(path.length - 1) !== '/') path += '/';
    if (path === '/') return 'home';
    if (path === '/paycheck-planner/') return 'sales';
    if (path === '/paycheck-planner/bundle/') return 'bundle';
    if (path === '/paycheck-planner/sample/') return 'sample';
    return 'other';
  }
  function qaNotice(a, ref) {
    var id = (a.id || 'pp-buy') + '-qa-note';
    var n = document.getElementById(id);
    if (!n) {
      n = document.createElement('p');
      n.id = id;
      n.className = 'pp-qa-note';
      n.setAttribute('role', 'status');
      n.setAttribute('data-pp-qa-note', '');
      n.style.cssText = 'margin:.5rem 0;padding:.4rem .6rem;border:1px dashed #8a6d00;background:#fff8e1;color:#4a3b00;font-size:.85rem;';
      a.insertAdjacentElement('afterend', n);
    }
    n.textContent = 'QA mode: Stripe checkout was not opened. Buy click recorded as test traffic (' + ref + ').';
  }
  function buyAnchor(e) {
    var t = e.target;
    var a = t && t.closest ? t.closest('a[data-pp-ref][href^="https://buy.stripe.com/"]') : null;
    return a;
  }
  window.addEventListener('click', function (e) {
    var a = buyAnchor(e);
    if (!a) return;
    if (!a.getAttribute('data-pp-base')) a.setAttribute('data-pp-base', a.getAttribute('href'));
    var ref = newRef(e);
    a.setAttribute('data-client-ref', ref);
    buyAt = Date.now();
    if (typeof window.gtag === 'function') { try { window.gtag('set', { client_reference_id: ref, pp_suspect: suspect || 'none' }); } catch (err) {} }
    // QA click: cancel navigation here too, so even a later stopPropagation cannot let it reach Stripe. GA's listener does not
    // read defaultPrevented, so buy_click and begin_checkout still fire.
    if (ref.indexOf('qa_') === 0) e.preventDefault();
  }, true);
  window.addEventListener('click', function (e) {
    var a = buyAnchor(e);
    if (!a) return;
    var base = a.getAttribute('data-pp-base') || a.getAttribute('href');
    var ref = a.getAttribute('data-client-ref');
    if (!ref) return;
    var q = ['client_reference_id=' + encodeURIComponent(ref)];
    try {
      var sp = new URLSearchParams(window.location.search);
      for (var i = 0; i < UTM_KEYS.length; i++) {
        var v = sp.get(UTM_KEYS[i]);
        if (v) q.push(UTM_KEYS[i] + '=' + encodeURIComponent(v.slice(0, 100)));
      }
    } catch (err) {}
    a.setAttribute('href', base + (base.indexOf('?') === -1 ? '?' : '&') + q.join('&'));
    if (ref.indexOf('qa_') === 0) {
      // QA click: GA already saw it; never navigate to Stripe.
      e.preventDefault();
      qaNotice(a, ref);
    }
    // Put the plain link back right after navigation starts, so copy-link and a bfcache return show the clean URL.
    window.setTimeout(function () { a.setAttribute('href', base); }, 1500);
  }, false);

  // 2. sign_up on the free sample page, and generate_lead on the sales and bundle pages:
  // both fire once when MailerLite reports a successful signup.
  if (page === 'sample' || page === 'sales' || page === 'bundle') {
    var signed = false;
    var fireSignUp = function () {
      if (signed) return; signed = true;
      if (page === 'sample') {
        send('sign_up', { method: 'mailerlite_embed', content_id: 'paycheck-planner-sample', transport_type: 'beacon' });
        var ok = document.getElementById('pp-sample-success'); if (ok) ok.classList.add('pp-show');
      } else {
        send('generate_lead', { form_id: 'planner_leads', method: 'mailerlite_embed', transport_type: 'beacon' });
      }
    };
    window.cdkPaycheckSampleSignup = fireSignUp;
    var signup = document.getElementById('pp-signup');
    var formId = document.body.getAttribute('data-pp-form-id') || (signup && signup.getAttribute('data-pp-form-id')) || '';
    var hookName = /^\d+$/.test(formId) ? ('ml_webform_success_' + formId) : '';
    var attachHook = function () {
      if (!hookName) return;
      var prev = window[hookName];
      if (prev && prev.__ppLead) return;
      var wrapped = function () {
        fireSignUp();
        if (typeof prev === 'function' && prev !== wrapped && !prev.__ppLead) {
          try { prev(); } catch (err) {}
        }
      };
      wrapped.__ppLead = true;
      window[hookName] = wrapped;
    };
    attachHook();
    var root = signup || document.body;
    if (root && window.MutationObserver) {
      new MutationObserver(function () {
        attachHook();
        var boxNow = (signup && signup.querySelector('.ml-embedded')) || document.querySelector('.ml-embedded');
        if (!boxNow) return;
        var done = boxNow.querySelector('.ml-form-successBody, .row-success');
        if (done && (done.offsetParent !== null || done.getClientRects().length)) fireSignUp();
      }).observe(root, { childList: true, subtree: true, attributes: true });
    }
  }

  // 4. checkout_return (checkout audit 1127). Payment Links have no cancel URL, so a visitor who leaves Stripe without paying
  // comes back with the browser Back button. If the page is restored from the back/forward cache after a Buy click in this
  // page view, send checkout_return with the same client_reference_id and the seconds spent away, so a Stripe session can be
  // matched to a person who came back. If the browser reloads the page instead (no cache), the ref is gone (this file stores
  // nothing), so the event goes out without a ref and return_type back_forward_reload; it can also mean a Back from another site.
  function sendReturn(type) {
    send('checkout_return', {
      return_type: type,
      client_reference_id: refId || '(none)',
      pp_suspect: suspect || 'none',
      seconds_away: buyAt ? Math.round((Date.now() - buyAt) / 1000) : -1,
      transport_type: 'beacon'
    });
  }
  window.addEventListener('pageshow', function (ev) {
    if (ev.persisted && buyAt) sendReturn('bfcache');
  });
  try {
    var nav = window.performance && performance.getEntriesByType ? performance.getEntriesByType('navigation')[0] : null;
    if (nav && nav.type === 'back_forward' && (page === 'sales' || page === 'bundle')) sendReturn('back_forward_reload');
  } catch (err) {}

})();
