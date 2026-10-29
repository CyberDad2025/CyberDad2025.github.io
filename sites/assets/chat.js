/* Request assistant: a scripted, step-by-step chat that collects a website-refresh request.
   No AI, no third-party service, no live person. Submits through SiteIntake: opens the visitor's own email app with the answers (mailto), nothing is sent by the page. */
(function () {
  "use strict";
  var STEPS = [
    { key: "business_name", label: "Business name", type: "text", required: true, auto: "organization",
      q: "Hi! I'm an automated assistant that collects your website request for our team (I'm not a live person). It's 8 short questions.\n\nFirst, what's the name of your business?" },
    { key: "current_url", label: "Current website", type: "url", required: false, placeholder: "https://example.com",
      q: "What's your current website address? If you don't have one, type \"none\".", validate: function (v) {
        if (!v || /^none$/i.test(v)) return ""; return /^(https?:\/\/)?[^\s.]+\.[^\s]{2,}$/i.test(v) ? "" : "That doesn't look like a web address. Try something like example.com, or type \"none\"."; } },
    { key: "dislikes", label: "What you dislike about the current site", type: "textarea", required: true,
      chips: ["Looks outdated", "Hard to use on phones", "Security warning", "Slow", "Hard to update", "Wrong or old info"], multi: true,
      q: "What don't you like about the current site? Tap any that apply and/or type in your own words." },
    { key: "must_haves", label: "Must-have pages and features", type: "textarea", required: true,
      chips: ["Home", "About", "Services", "Gallery/photos", "Menu or price list", "Contact form", "Map & hours", "Reviews", "Link to booking/store"], multi: true,
      q: "Which pages and features must the new site have? Tap all that apply and add anything else." },
    { key: "style_examples", label: "Style examples", type: "textarea", required: false,
      q: "Any websites whose look you like? Paste links or describe the style (for example \"clean and bright\"). Type \"skip\" if none." },
    { key: "budget", label: "Budget range", type: "choice", required: true,
      chips: ["Under $500", "$500–$800", "$800–$1,500", "Over $1,500", "Not sure yet"],
      q: "What budget range are you thinking about for the rebuild? (This just helps us scope it.)" },
    { key: "timeline", label: "Timeline", type: "choice", required: true,
      chips: ["As soon as possible", "Within a month", "1–3 months", "Just exploring"],
      q: "When would you like the new site live?" },
    { key: "email", label: "Contact email", type: "email", required: true, auto: "email",
      q: "Last one: what email should we reply to? We only use it for this request.", validate: function (v) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v) ? "" : "Please enter a valid email address, like name@business.com."; } }
  ];

  var panel, log, formEl, answers = {}, idx = 0, editing = false, lastFocus = null, built = false, sent = false;

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) { if (k === "class") n.className = attrs[k]; else n.setAttribute(k, attrs[k]); });
    if (text != null) n.textContent = text; return n;
  }
  function say(text, who) { var m = el("div", { class: "msg " + (who || "bot") }, text); log.appendChild(m); log.scrollTop = log.scrollHeight; return m; }

  function build() {
    panel = document.getElementById("chat-panel");
    var head = el("div", { class: "chat-head" });
    var t = el("div"); t.appendChild(el("h2", { id: "chat-title" }, "Request assistant"));
    t.appendChild(el("p", null, "Automated — collects your request for our team. Not a live chat."));
    var x = el("button", { class: "chat-x", type: "button", "aria-label": "Close request assistant" }, "✕");
    x.addEventListener("click", close);
    head.appendChild(t); head.appendChild(x);
    log = el("div", { class: "chat-log", role: "log", "aria-live": "polite", "aria-label": "Conversation" });
    formEl = el("form", { class: "chat-form", novalidate: "" });
    panel.appendChild(head); panel.appendChild(log); panel.appendChild(formEl);
    panel.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
    built = true;
  }

  function renderInput(step) {
    formEl.innerHTML = "";
    var selected = [];
    var err = el("p", { class: "chat-err", id: "chat-err", "aria-live": "assertive" });
    if (step.chips) {
      var chips = el("div", { class: "chat-chips", role: "group", "aria-label": step.label + " options" });
      step.chips.forEach(function (c) {
        var b = el("button", { type: "button", class: "chip", "aria-pressed": "false" }, c);
        b.addEventListener("click", function () {
          if (step.type === "choice") { finish(c); return; }
          var on = b.getAttribute("aria-pressed") !== "true"; b.setAttribute("aria-pressed", on ? "true" : "false");
          if (on) selected.push(c); else selected = selected.filter(function (s) { return s !== c; });
        });
        chips.appendChild(b);
      });
      formEl.appendChild(chips);
    }
    var input = null;
    if (step.type !== "choice") {
      var row = el("div", { class: "chat-row" });
      var id = "chat-in-" + step.key;
      var lab = el("label", { for: id, class: "sr-only" }, step.label);
      input = step.type === "textarea" ? el("textarea", { id: id, rows: "2" }) : el("input", { id: id, type: step.type === "url" ? "text" : step.type });
      if (step.type === "url") input.setAttribute("inputmode", "url");
      if (step.placeholder) input.setAttribute("placeholder", step.placeholder);
      if (step.auto) input.setAttribute("autocomplete", step.auto);
      input.setAttribute("aria-describedby", "chat-err");
      if (answers[step.key] && step.type !== "textarea") input.value = answers[step.key];
      row.appendChild(lab); row.appendChild(input);
      formEl.appendChild(row);
    }
    formEl.appendChild(err);
    var acts = el("div", { class: "chat-actions" });
    if (step.type !== "choice") acts.appendChild(el("button", { type: "submit", class: "btn btn-p" }, "Next"));
    if (idx > 0 && !editing) {
      var back = el("button", { type: "button", class: "btn btn-o" }, "Back");
      back.addEventListener("click", function () { idx--; ask(); }); acts.appendChild(back);
    }
    formEl.appendChild(acts);
    formEl.onsubmit = function (e) {
      e.preventDefault();
      var typed = input ? input.value.trim() : "";
      var val = step.multi ? selected.concat(typed ? [typed] : []).join("; ") : typed;
      if (/^skip$/i.test(val) && !step.required) val = "";
      if (step.required && !val) { err.textContent = "Please answer this one (tap an option or type)."; (input || formEl).focus(); return; }
      var msg = step.validate ? step.validate(val) : "";
      if (msg) { err.textContent = msg; input.setAttribute("aria-invalid", "true"); input.focus(); return; }
      finish(val);
    };
    function finish(v) { answers[step.key] = v; say(v || "(skipped)", "me"); if (editing) { editing = false; summary(); } else { idx++; next(); } }
    (input || formEl.querySelector("button")).focus();
  }

  function ask() { var s = STEPS[idx]; say(s.q); renderInput(s); }
  function next() { if (idx < STEPS.length) ask(); else summary(); }

  function labels() { var o = {}; STEPS.forEach(function (s) { o[s.key] = s.label; }); return o; }

  function summary() {
    say("Here's what I've got. Please check it before sending.");
    var box = el("div", { class: "summary" }); var dl = el("dl");
    STEPS.forEach(function (s, i) {
      dl.appendChild(el("dt", null, s.label));
      var dd = el("dd", null, answers[s.key] || "(blank)");
      var ch = el("button", { type: "button", class: "linkbtn", "aria-label": "Change " + s.label }, " Change");
      ch.addEventListener("click", function () { editing = true; idx = i; ask(); });
      dd.appendChild(document.createTextNode(" ")); dd.appendChild(ch); dl.appendChild(dd);
    });
    box.appendChild(dl); log.appendChild(box); log.scrollTop = log.scrollHeight;
    formEl.innerHTML = "";
    var acts = el("div", { class: "chat-actions" });
    var ok = el("button", { type: "button", class: "btn btn-p" }, "Confirm and open email");
    var dlb = el("button", { type: "button", class: "btn btn-o" }, "Download my answers");
    ok.addEventListener("click", function () {
      if (sent) return; ok.disabled = true;
      window.SiteIntake.submit(answers, "chat-assistant", labels()).then(function (res) {
        var em = (window.SITE_CONFIG || {}).CONTACT_EMAIL;
        if (res.mode === "mailto") { ok.disabled = false; say("Your email app should open with your answers filled in, addressed to " + em + ". Press Send there to send your request — I can't send it for you." + (res.cut ? " Your answers were long, so the email is shortened; please attach the file from \"Download my answers\"." : "") + " If nothing opened, email " + em + " and attach your downloaded answers."); }
        else if (res.ok) { sent = true; say("Thanks — your request was received. Our team will reply by email."); }
        else { ok.disabled = false; say("Sorry, that didn't work. Please email " + (em || "us") + " or download your answers."); }
      });
    });
    dlb.addEventListener("click", function () { window.SiteIntake.download("website-request.txt", window.SiteIntake.answersText(answers, labels())); });
    var restart = el("button", { type: "button", class: "btn btn-o" }, "Start over");
    restart.addEventListener("click", function () { answers = {}; idx = 0; sent = false; log.innerHTML = ""; ask(); });
    acts.appendChild(ok); acts.appendChild(dlb); acts.appendChild(restart);
    formEl.appendChild(acts); ok.focus();
  }

  function open(e) {
    lastFocus = (e && e.currentTarget) || document.activeElement;
    if (!built) { build(); }
    panel.hidden = false;
    document.querySelectorAll(".chat-launch").forEach(function (b) { b.setAttribute("aria-expanded", "true"); });
    if (!log.childNodes.length) ask(); else { var f = formEl.querySelector("input,textarea,button"); if (f) f.focus(); }
  }
  function close() {
    panel.hidden = true;
    document.querySelectorAll(".chat-launch").forEach(function (b) { b.setAttribute("aria-expanded", "false"); });
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-open-chat]").forEach(function (b) { b.addEventListener("click", open); });
    if (location.hash === "#assistant") open();
  });
  window.SiteChat = { open: open, close: close, _answers: function () { return answers; } };
})();
