/* Paycheck Planner pages: GA4 events (the site's existing GA4 tag only, via window.gtag from _includes/ga4.html).
   buy_click and begin_checkout on Buy buttons are sent by the site-wide listener in _includes/ga4.html for every
   a[href^="https://buy.stripe.com/"], so every Buy button here is a plain Stripe link. This file adds:
   view_item (sales and bundle pages) and sign_up (sample page). It does not rewrite links or copy utm_* parameters.
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
