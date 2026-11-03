/* Shared intake submission for the quick form, the full questionnaire and the chat assistant.
   No third-party services. Default mode is mailto: the visitor's own email app sends it; this page never transmits data. */
(function () {
  "use strict";
  function cfg() { return window.SITE_CONFIG || {}; }

  // P57 v3: the mailto link never carries answers (fixed subject, no body), so no answer text is ever put in an href or URL.
  // The visitor pastes the answers (copied for them when they press send) or attaches the downloaded file.
  function mailtoFor(source) {
    var c = cfg(), subj = source === "full-questionnaire" ? "Website intake" : "Website request";
    return { href: "mailto:" + c.CONTACT_EMAIL + "?subject=" + encodeURIComponent(subj), cut: false };
  }

  // Copies text to the visitor's clipboard during their own click; resolves true/false. Nothing is sent anywhere.
  function copyText(text) {
    function legacy() {
      try {
        var t = document.createElement("textarea"); t.value = text; t.setAttribute("readonly", ""); t.style.position = "fixed"; t.style.opacity = "0";
        document.body.appendChild(t); t.select(); var ok = document.execCommand("copy"); t.remove(); return ok;
      } catch (e) { return false; }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text).then(function () { return true; }, function () { return legacy(); });
    return Promise.resolve(legacy());
  }

  // Returns {ok, mode, body, href?, copied?, text?}. Copies the answers, then opens the visitor's own mail app with a blank
  // email (mailto, fixed subject); nothing is sent by this page.
  function submitIntake(payload, source, labels, emailLabels) {
    var body = { source: source, submitted_at: new Date().toISOString(), page: location.pathname, answers: payload };
    var c = cfg();
    if (!c.CONTACT_EMAIL) return Promise.resolve({ ok: false, mode: "none", body: body });
    var m = mailtoFor(source), text = answersText(body.answers, labels, true, emailLabels);
    return copyText(text).then(function (copied) {
      if (!window.SITE_NO_NAVIGATE) window.location.href = m.href;
      return { ok: true, mode: "mailto", body: body, href: m.href, cut: false, copied: copied, text: text };
    });
  }

  // Email version: blank answers are left out and long labels are cut to their short form
  // ("Your Google review link (optional): the link ..." -> "Your Google review link"), so more answers fit
  // under MAILTO_MAX. The downloaded file keeps every question, full labels and blanks.
  // A label/legend's data-email-label (emailLabels[name]) wins; anything still over 60 characters is cut at
  // the last space at or before 60 and ends with "…" (60 characters at most), never mid-word (a single
  // 60+ character word is the only case that has to be cut inside the word).
  function shortLabel(t) {
    var s = String(t).split(/\s\(|:\s/)[0].trim();
    if (s.length <= 60) return s;
    var cut = s.slice(0, 59), sp = s.charAt(59) === " " ? 59 : cut.lastIndexOf(" "); // 59 + "…" = 60 max
    return (sp > 0 ? cut.slice(0, sp) : cut).replace(/[\s,;:.\u2013\u2014-]+$/, "") + "\u2026";
  }
  function answersText(payload, labels, forEmail, emailLabels) {
    var lines = forEmail ? ["Hi, here is my website refresh request:", ""] : ["Website refresh request — your answers", "Saved " + new Date().toLocaleString(), ""];
    var skipped = 0;
    Object.keys(payload).forEach(function (k) {
      var v = payload[k]; if (Array.isArray(v)) v = v.join(", ");
      var blank = v === "" || v == null, label = (labels && labels[k]) || k;
      if (forEmail && blank) { skipped++; return; }
      lines.push((forEmail ? ((emailLabels && emailLabels[k]) || shortLabel(label)) : label) + ": " + (blank ? "(blank)" : v));
    });
    if (forEmail && skipped) lines.push("", "(" + skipped + " question" + (skipped === 1 ? "" : "s") + " left blank.)");
    if (!forEmail) lines.push("", "Paste these answers into your email to " + (cfg().CONTACT_EMAIL || "us") + ", or attach this file.");
    return lines.join("\n");
  }

  function download(filename, text) {
    var blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
  }

  function formToObject(form) {
    var out = {};
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || el.type === "submit" || el.type === "button") return;
      if (el.type === "checkbox") {
        if (form.querySelectorAll('[name="' + el.name + '"]').length > 1) { out[el.name] = out[el.name] || []; if (el.checked) out[el.name].push(el.value); }
        else out[el.name] = el.checked ? "yes" : "no";
      } else if (el.type === "radio") { if (el.checked) out[el.name] = el.value; else if (!(el.name in out)) out[el.name] = ""; }
      else out[el.name] = el.value.trim();
    });
    return out;
  }

  function wireForm(form, source) {
    var status = form.querySelector(".form-status");
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (!form.checkValidity()) {
        var bad = form.querySelector(":invalid"); if (bad) bad.focus();
        status.textContent = "Please fill in the highlighted required fields.";
        return;
      }
      var data = formToObject(form), labels = {}, emailLabels = {};
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name || labels[el.name]) return;
        var l = el.id && form.querySelector('label[for="' + el.id + '"]');
        var g = el.closest("fieldset.group"), lg = g && g.querySelector("legend");
        var t = (l && l.textContent) || (lg && lg.textContent) || (el.closest("label") && el.closest("label").textContent) || "";
        if (t) labels[el.name] = t.replace(/\s*\*\s*$/, "").trim();
        var src = [l, lg, el.closest("label")].filter(function (x) { return x && x.hasAttribute("data-email-label"); })[0];
        if (src) emailLabels[el.name] = src.getAttribute("data-email-label").trim();
      });
      // Email order: required answers first (name, address, form_to, approver...), then the rest in form order,
      // so the facts we can't build without stay in the email if it has to be shortened. The download keeps form order.
      var emailData = {}, req = {};
      Array.prototype.forEach.call(form.elements, function (el) { if (el.name && el.required) req[el.name] = 1; });
      Object.keys(data).forEach(function (k) { if (req[k]) emailData[k] = data[k]; });
      Object.keys(data).forEach(function (k) { if (!req[k]) emailData[k] = data[k]; });
      submitIntake(emailData, source, labels, emailLabels).then(function (res) {
        status.textContent = "";
        var p = document.createElement("p");
        var em = cfg().CONTACT_EMAIL;
        p.textContent = res.mode === "mailto"
            ? "Your email app should now open with a new email addressed to " + em + ". "
              + (res.copied ? "Your answers are copied: paste them into the email" : "Your answers aren't in it yet: use Copy my answers or Download my answers below, then paste them in or attach the file")
              + ", and press Send there — this page doesn't send anything by itself. Nothing opened? Email " + em + " and paste or attach your answers."
          : res.ok ? "Thanks — your request was received. We'll reply by email."
          : "Sorry, that didn't work. Please email " + (em || "us") + " or download your answers.";
        status.appendChild(p);
        if (res.mode === "mailto") {
          var a = document.createElement("a"); a.href = res.href; a.className = "btn btn-p dl"; a.textContent = "Open my email app again"; status.appendChild(a);
          var cb = document.createElement("button"); cb.type = "button"; cb.className = "btn btn-o dl"; cb.textContent = "Copy my answers";
          cb.addEventListener("click", function () { copyText(res.text).then(function (ok) { cb.textContent = ok ? "Answers copied" : "Couldn't copy, use Download my answers"; }); });
          status.appendChild(cb);
        }
        {
          var b = document.createElement("button"); b.type = "button"; b.className = "btn btn-o dl"; b.textContent = "Download my answers";
          b.addEventListener("click", function () { download("website-request.txt", answersText(data, labels)); });
          status.appendChild(b);
        }
      });
    });
  }

  window.SiteIntake = { submit: submitIntake, download: download, answersText: answersText };
  document.addEventListener("DOMContentLoaded", function () {
    var brand = cfg().BRAND;
    if (brand) document.querySelectorAll("[data-brand]").forEach(function (n) { n.textContent = brand; });
    var em = cfg().CONTACT_EMAIL;
    if (em) document.querySelectorAll("[data-email]").forEach(function (n) { n.textContent = em; if (n.tagName === "A") n.href = "mailto:" + em; });
    var q = document.getElementById("quick-intake"); if (q) wireForm(q, "landing-quick-form");
    var f = document.getElementById("full-intake"); if (f) wireForm(f, "full-questionnaire");
  });
})();
