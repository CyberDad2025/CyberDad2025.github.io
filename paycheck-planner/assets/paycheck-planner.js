/* Paycheck Planner pages: GA4 events (the site's existing GA4 tag only, via window.gtag from _includes/ga4.html).
   buy_click and begin_checkout on Buy buttons are sent by the site-wide listener in _includes/ga4.html for every
   a[href^="https://buy.stripe.com/"], so every Buy button here is a plain Stripe link. This file adds:
   view_item (sales and bundle pages) and sign_up (sample page). It does not rewrite links on load. On click only, section 1b appends client_reference_id and the page's utm_* to the Stripe link.
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

  // 1b. Buy attribution (progressive enhancement). The href in the HTML stays the plain Payment Link. On click only:
  // (a) a window CAPTURE listener runs before the site-wide GA listener in _includes/ga4.html and stores an opaque random id in
  //     data-client-ref and calls gtag('set', { client_reference_id }) so the site-wide buy_click and begin_checkout events that follow in
//     _includes/ga4.html (left unchanged) carry it; those events still read the plain href;
  // (b) a window BUBBLE listener runs after GA and only then appends client_reference_id and any utm_* from the page URL to the
  //     link, so the browser navigates to the enhanced URL. No PII, no cookies, no storage. The id starts with qa_ when the
  //     existing cdk_qa localStorage flag is on, so QA clicks stay separable from buyers.
  var UTM_KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'];
  var refId = '';
  function newRef() {
    if (refId) return refId;
    var hex = '';
    try {
      var buf = new Uint8Array(12); window.crypto.getRandomValues(buf);
      for (var i = 0; i < buf.length; i++) hex += ('0' + buf[i].toString(16)).slice(-2);
    } catch (err) {
      while (hex.length < 24) hex += Math.floor(Math.random() * 16).toString(16);
    }
    var qa = false;
    try { qa = window.localStorage.getItem('cdk_qa') === '1'; } catch (err) {}
    refId = (qa ? 'qa_' : 'pp_') + hex;
    return refId;
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
    var ref = newRef();
    a.setAttribute('data-client-ref', ref);
    if (typeof window.gtag === 'function') { try { window.gtag('set', { client_reference_id: ref }); } catch (err) {} }
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
    // Put the plain link back right after navigation starts, so copy-link and a bfcache return show the clean URL.
    window.setTimeout(function () { a.setAttribute('href', base); }, 1500);
  }, false);

  // 2. sign_up on the free sample page: fires once when MailerLite reports a successful signup.
  if (page === 'sample') {
    var signed = false;
    var fireSignUp = function () {
      if (signed) return; signed = true;
      send('sign_up', { method: 'mailerlite_embed', content_id: 'paycheck-planner-sample', transport_type: 'beacon' });
      var ok = document.getElementById('pp-sample-success'); if (ok) ok.classList.add('pp-show');
    };
    window.cdkPaycheckSampleSignup = fireSignUp;
    var formId = document.body.getAttribute('data-pp-form-id') || '';
    if (/^\d+$/.test(formId)) window['ml_webform_success_' + formId] = fireSignUp;
    var box = document.querySelector('.ml-embedded');
    if (box && window.MutationObserver) {
      new MutationObserver(function () {
        var done = box.querySelector('.ml-form-successBody, .row-success');
        if (done && done.offsetParent !== null) fireSignUp();
      }).observe(box, { childList: true, subtree: true, attributes: true });
    }
  }

})();
