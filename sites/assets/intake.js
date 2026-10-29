/* Shared intake submission for the quick form, the full questionnaire and the chat assistant.
   No third-party services. Default mode is mailto: the visitor's own email app sends it; this page never transmits data. */
(function () {
  "use strict";
  function cfg() { return window.SITE_CONFIG || {}; }

  function mailtoFor(body, labels) {
    var c = cfg(), subj = "Website request: " + (body.answers.business_name || body.answers.legal_name || "my business");
    var text = answersText(body.answers, labels, true), max = c.MAILTO_MAX || 1800, cut = false;
    if (text.length > max) { text = text.slice(0, max) + "\n\n[Shortened to fit an email link. I'll attach the full answers file.]"; cut = true; }
    return { href: "mailto:" + c.CONTACT_EMAIL + "?subject=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(text), cut: cut };
  }

  // Returns {ok, mode, body, href?, cut?}. Opens the visitor's own mail app (mailto); nothing is sent by this page.
  function submitIntake(payload, source, labels) {
    var body = { source: source, submitted_at: new Date().toISOString(), page: location.pathname, answers: payload };
    var c = cfg();
    if (!c.CONTACT_EMAIL) return Promise.resolve({ ok: false, mode: "none", body: body });
    var m = mailtoFor(body, labels);
    if (!window.SITE_NO_NAVIGATE) window.location.href = m.href;
    return Promise.resolve({ ok: true, mode: "mailto", body: body, href: m.href, cut: m.cut });
  }

  function answersText(payload, labels, forEmail) {
    var lines = forEmail ? ["Hi, here is my website refresh request:", ""] : ["Website refresh request — your answers", "Saved " + new Date().toLocaleString(), ""];
    Object.keys(payload).forEach(function (k) {
      var v = payload[k]; if (Array.isArray(v)) v = v.join(", ");
      lines.push(((labels && labels[k]) || k) + ": " + (v === "" || v == null ? "(blank)" : v));
    });
    if (!forEmail) lines.push("", "Email this file to " + (cfg().CONTACT_EMAIL || "us") + " if your email app didn't open.");
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
      var data = formToObject(form), labels = {};
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name || labels[el.name]) return;
        var l = el.id && form.querySelector('label[for="' + el.id + '"]');
        var g = el.closest("fieldset.group"), lg = g && g.querySelector("legend");
        var t = (l && l.textContent) || (lg && lg.textContent) || (el.closest("label") && el.closest("label").textContent) || "";
        if (t) labels[el.name] = t.replace(/\s*\*\s*$/, "").trim();
      });
      submitIntake(data, source, labels).then(function (res) {
        status.textContent = "";
        var p = document.createElement("p");
        var em = cfg().CONTACT_EMAIL;
        p.textContent = res.mode === "mailto"
            ? "Your email app should now open with your answers filled in, addressed to " + em + ". Press Send there to send it — this page doesn't send anything by itself. Nothing opened? Email " + em + " or download your answers below."
              + (res.cut ? " (Your answers were long, so the email was shortened — please attach the downloaded file.)" : "")
          : res.ok ? "Thanks — your request was received. We'll reply by email."
          : "Sorry, that didn't work. Please email " + (em || "us") + " or download your answers.";
        status.appendChild(p);
        if (res.mode === "mailto") {
          var a = document.createElement("a"); a.href = res.href; a.className = "btn btn-p dl"; a.textContent = "Open my email app again"; status.appendChild(a);
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
