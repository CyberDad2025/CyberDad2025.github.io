/* /sites/#start rebuild order form (P60 ed1077c4, adopted in P59 + page-count helper, budget, tier preselect). Accessible inline validation, then one of two paths:
   - SITE_ORDER_CONFIG.ACTION_URL set: POST the answers to that MailerLite embedded form, show the confirmation.
   - ACTION_URL empty (placeholder) or the post fails: email fallback. Copies the answers, opens the visitor's own
     email app with a fixed subject and NO body, and offers Copy / Download. Answers never go into a mailto: or URL.
   No other third-party calls. No payment links. */
(function () {
  "use strict";
  var FALLBACK_SUBJECT = "Website rebuild order request";
  function oc() { return window.SITE_ORDER_CONFIG || {}; }
  function contact() { return (window.SITE_CONFIG || {}).CONTACT_EMAIL || "ruel@getcyberdadkit.com"; }
  function $(sel, root) { return (root || document).querySelector(sel); }

  function normUrl(v) {
    v = String(v || "").trim(); if (!v) return "";
    if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(v)) v = "https://" + v;
    return v;
  }
  function validUrl(v) {
    try {
      var u = new URL(normUrl(v));
      return (u.protocol === "https:" || u.protocol === "http:") && /^[^.\s]+(\.[^.\s]+)+$/.test(u.hostname) && /[a-z]{2,}$/i.test(u.hostname) && !/\s/.test(v.trim());
    } catch (e) { return false; }
  }
  function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(v || "").trim()); }

  var RULES = {
    business_name: function (v) { return v ? "" : "Enter your business name."; },
    contact_name: function (v) { return v ? "" : "Enter your name."; },
    email: function (v) { return !v ? "Enter your email address." : validEmail(v) ? "" : "Enter an email address like name@yourbusiness.com."; },
    current_url: function (v) { return !v ? "Enter your current website address." : validUrl(v) ? "" : "Enter a web address like yourbusiness.com or https://yourbusiness.com."; },
    package: function (v) { return v ? "" : "Choose a package, or \"Not sure yet\"."; },
    what_you_want: function (v) { return v ? "" : "Tell us what you want changed or rebuilt."; },
    consent: function (v) { return v === "yes" ? "" : "Tick the box so we can email you about this order request."; }
  };

  function values(form) {
    var g = function (n) { var el = form.elements[n]; return el ? String(el.value || "").trim() : ""; };
    var pkg = form.querySelector('input[name="package"]:checked');
    return {
      business_name: g("business_name"), contact_name: g("contact_name"), email: g("email"),
      current_url: g("current_url") ? normUrl(g("current_url")) : "",
      package: pkg ? pkg.value : "", site_care: form.elements.site_care && form.elements.site_care.checked ? "yes" : "no",
      what_you_want: g("what_you_want"), goals: g("goals"), pages: g("pages"), deadline: g("deadline"),
      page_count: g("page_count"), budget: g("budget"),
      consent: form.elements.consent && form.elements.consent.checked ? "yes" : "no"
    };
  }
  var LABELS = { business_name: "Business name", contact_name: "Your name", email: "Email", current_url: "Current website",
    package: "Package", site_care: "Add Site Care", what_you_want: "What I want", goals: "Main goals", pages: "Pages I want", deadline: "Deadline", page_count: "Pages on current site", budget: "Budget range", consent: "OK to email me about this request" };
  function answersText(d) {
    var lines = ["Website rebuild order request", ""];
    Object.keys(LABELS).forEach(function (k) { if (d[k] !== "" && d[k] != null) lines.push(LABELS[k] + ": " + d[k]); });
    return lines.join("\n");
  }

  function setError(form, name, msg) {
    var err = document.getElementById("of-err-" + name); if (!err) return;
    err.textContent = msg; err.hidden = !msg;
    var els = form.querySelectorAll('[name="' + name + '"]');
    Array.prototype.forEach.call(els, function (el) { if (msg) el.setAttribute("aria-invalid", "true"); else el.removeAttribute("aria-invalid"); });
    var grp = err.closest(".field"); if (grp) grp.classList.toggle("has-err", !!msg);
  }
  function validate(form, only) {
    var d = values(form), bad = [];
    Object.keys(RULES).forEach(function (k) {
      if (only && only !== k) return;
      var raw = k === "current_url" ? (form.elements.current_url.value || "").trim() : d[k];
      var m = RULES[k](raw); setError(form, k, m); if (m) bad.push({ name: k, msg: m });
    });
    return bad;
  }

  function copyText(text) {
    function legacy() {
      try { var t = document.createElement("textarea"); t.value = text; t.setAttribute("readonly", ""); t.style.position = "fixed"; t.style.opacity = "0";
        document.body.appendChild(t); t.select(); var ok = document.execCommand("copy"); t.remove(); return ok; } catch (e) { return false; }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return legacy(); });
    return Promise.resolve(legacy());
  }
  function download(text) {
    var a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    a.download = "website-rebuild-order.txt"; document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }
  function mailtoHref() { return "mailto:" + contact() + "?subject=" + encodeURIComponent(FALLBACK_SUBJECT); } // fixed subject, never a body

  function postMailerLite(d) {
    var c = oc(), body = new URLSearchParams();
    Object.keys(c.FIELDS || {}).forEach(function (k) { if (d[k] !== undefined) body.append(c.FIELDS[k], d[k]); });
    Object.keys(c.EXTRA || {}).forEach(function (k) { body.append(k, c.EXTRA[k]); });
    var ctl = window.AbortController ? new AbortController() : null, timer = ctl && setTimeout(function () { ctl.abort(); }, c.TIMEOUT_MS || 15000);
    return fetch(c.ACTION_URL, { method: "POST", mode: c.MODE === "no-cors" ? "no-cors" : "cors", credentials: "omit", body: body, signal: ctl ? ctl.signal : undefined, referrerPolicy: "strict-origin" })
      .then(function (r) {
        if (r.type === "opaque") return true;
        if (!r.ok) return false;
        return r.json().then(function (j) { return !!(j && j.success); }, function () { return false; });
      }, function () { return false; })
      .then(function (ok) { if (timer) clearTimeout(timer); return ok; });
  }

  function show(form, panelId, d) {
    var done = document.getElementById(panelId); if (!done) return;
    form.hidden = true;
    ["order-done", "order-fallback"].forEach(function (id) { var p = document.getElementById(id); if (p) p.hidden = id !== panelId; });
    var biz = done.querySelector("[data-order-biz]"); if (biz) biz.textContent = d.business_name;
    done.focus();
  }

  function wireFallback(text) {
    var fb = document.getElementById("order-fallback"); if (!fb) return;
    var open = fb.querySelector("[data-order-mailto]"); if (open) open.href = mailtoHref();
    var cp = fb.querySelector("[data-order-copy]"), dl = fb.querySelector("[data-order-download]"), st = fb.querySelector("[data-order-copied]");
    if (cp) cp.onclick = function () { copyText(text).then(function (ok) { st.textContent = ok ? "Answers copied. Paste them into the email." : "Couldn't copy. Use Download my answers instead."; }); };
    if (dl) dl.onclick = function () { download(answersText(window.__lastOrder || {})); };
  }

  function init() {
    var form = document.getElementById("order-form"); if (!form) return;
    var status = $(".form-status", form), btn = $('button[type="submit"]', form);
    var live = !!(oc().ACTION_URL && /^https:\/\//.test(oc().ACTION_URL));
    form.setAttribute("data-mode", live ? "mailerlite" : "email-fallback");
    Array.prototype.forEach.call(form.querySelectorAll("[data-note-mode]"), function (n) { n.hidden = n.getAttribute("data-note-mode") !== (live ? "mailerlite" : "email-fallback"); });
    if (btn) { btn.textContent = live ? "Send my order request" : "Continue to email my order"; btn.disabled = false; } // rendered disabled for no-JS visitors
    // Inline validation: after a field is left (blur) and live while it's marked invalid.
    Object.keys(RULES).forEach(function (k) {
      Array.prototype.forEach.call(form.querySelectorAll('[name="' + k + '"]'), function (el) {
        el.addEventListener(el.type === "radio" || el.type === "checkbox" ? "change" : "blur", function () { if (el.value || el.type === "radio" || el.type === "checkbox" || el.getAttribute("aria-invalid")) validate(form, k); });
        el.addEventListener("input", function () { if (el.getAttribute("aria-invalid")) validate(form, k); });
      });
    });
    var url = form.elements.current_url;
    if (url) url.addEventListener("blur", function () { if (url.value.trim() && validUrl(url.value)) url.value = normUrl(url.value); });

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (form.getAttribute("aria-busy") === "true") return;
      var bad = validate(form);
      if (bad.length) {
        status.textContent = (bad.length === 1 ? "1 answer needs" : bad.length + " answers need") + " fixing: " + bad.map(function (b) { return LABELS[b.name]; }).join(", ") + ".";
        var first = form.querySelector('[name="' + bad[0].name + '"]'); if (first) first.focus();
        return;
      }
      status.textContent = "";
      var d = values(form); window.__lastOrder = d;
      var text = answersText(d);
      if (form.elements.website_hp && form.elements.website_hp.value) { show(form, "order-done", d); return; } // spam trap: pretend success, send nothing
      if (!live) {
        wireFallback(text);
        copyText(text).then(function (ok) {
          var st = document.querySelector("#order-fallback [data-order-copied]");
          if (st) st.textContent = ok ? "Your answers are copied. Paste them into the email." : "Your answers aren't copied yet: use Copy my answers or Download my answers.";
          show(form, "order-fallback", d);
          if (!window.SITE_NO_NAVIGATE) window.location.href = mailtoHref();
        });
        return;
      }
      form.setAttribute("aria-busy", "true"); btn.disabled = true; status.textContent = "Sending your order request…";
      postMailerLite(d).then(function (ok) {
        form.removeAttribute("aria-busy"); btn.disabled = false; status.textContent = "";
        if (ok) { show(form, "order-done", d); return; }
        wireFallback(text);
        var fb = document.getElementById("order-fallback"), why = fb && fb.querySelector("[data-order-failed]"); if (why) why.hidden = false;
        copyText(text).then(function (c) {
          var st = fb && fb.querySelector("[data-order-copied]"); if (st) st.textContent = c ? "Your answers are copied. Paste them into the email." : "Use Copy my answers or Download my answers.";
          show(form, "order-fallback", d);
        });
      });
    });
  }
  // P59: tier buttons (a[data-package] / a[data-care]) preselect the form; the link is only "#start", nothing typed goes in a URL.
  // Page-count helper suggests a package and selects it only if the visitor hasn't picked one.
  var SUGGEST = { "1 to 5": "Refresh ($499 one-time, up to 5 pages)", "6 to 10": "Refresh Plus ($799 one-time, up to 10 pages)", "More than 10, or more than one location": "Custom (from $1,499, quoted)" };
  function pick(form, value) {
    var r = form.querySelector('input[name="package"][value="' + value.replace(/"/g, "") + '"]'); if (r) { r.checked = true; r.dispatchEvent(new Event("change", { bubbles: true })); }
    return r;
  }
  function preselect() {
    var form = document.getElementById("order-form"); if (!form) return;
    var chosen = false;
    Array.prototype.forEach.call(form.querySelectorAll('input[name="package"]'), function (r) { r.addEventListener("click", function () { chosen = true; }); });
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[data-package], a[data-care]"); if (!a) return;
      if (a.hasAttribute("data-package") && pick(form, a.getAttribute("data-package"))) chosen = true;
      if (a.hasAttribute("data-care") && form.elements.site_care) form.elements.site_care.checked = true;
    });
    var pc = form.elements.page_count, hint = document.getElementById("of-pagecount-hint");
    if (pc) pc.addEventListener("change", function () {
      var m = SUGGEST[pc.value];
      if (hint) hint.textContent = m ? "Suggested: " + m.split(" (")[0] + "." + (chosen ? "" : " We've selected it below; you can change it.") : "";
      if (m && !chosen) pick(form, m);
    });
  }
  window.SiteOrder = { validUrl: validUrl, normUrl: normUrl, answersText: answersText, mailtoHref: mailtoHref };
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", init); document.addEventListener("DOMContentLoaded", preselect); } else { init(); preselect(); }
})();
