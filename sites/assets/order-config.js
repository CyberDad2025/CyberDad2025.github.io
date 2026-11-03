/* Rebuild order form config (P60, adopted in P59): the ONLY place to wire the /sites/#start order form to a backend.
   GitHub Pages is static, so answers go to a MailerLite embedded form (the owner's existing $0 tool).

   WIRED (P59 v2, Nov 3, 2026): ACTION_URL is the action of MailerLite embedded form "CyberDad Kit Sites order requests"
   (form 203101607592724479, group "Sites order requests", double opt-in off). FIELDS and EXTRA match the inputs in that
   form's HTML embed code. If a post fails, times out or MailerLite doesn't answer {"success":true}, the page shows the
   email fallback (copies the answers, offers a download and an email-app button with a FIXED subject and NO body;
   answers are never put in a mailto: link or any URL). Set ACTION_URL back to "" to use only the email fallback. Do not put API keys or tokens here: the action URL is public by design. */
window.SITE_ORDER_CONFIG = {
  ACTION_URL: "https://assets.mailerlite.com/jsonp/1632878/forms/203101607592724479/subscribe", // MailerLite embedded-form action (method post)
  MODE: "cors",                // "cors": read MailerLite's {"success":true}; any network/CORS error shows the email fallback
  TIMEOUT_MS: 15000,
  FIELDS: {                    // our input name -> MailerLite field name
    email:          "fields[email]",          // default field
    contact_name:   "fields[name]",           // default field
    business_name:  "fields[company]",        // default field
    current_url:    "fields[current_website]",// custom text field
    package:        "fields[sites_package]",  // custom text field
    site_care:      "fields[site_care]",      // custom text field ("yes"/"no")
    what_you_want:  "fields[what_you_want]",  // custom text field
    goals:          "fields[sites_goals]",    // custom text field (optional)
    pages:          "fields[pages_needed]",   // custom text field (optional)
    deadline:       "fields[deadline]",       // custom text field (optional)
    page_count:     "fields[sites_page_count]", // custom text field (optional, P59)
    budget:         "fields[sites_budget]",   // custom text field (optional, P59)
    consent:        "fields[order_consent]"   // custom text field ("yes")
  },
  EXTRA: { "ml-submit": "1", "anticsrf": "true" } // sent as-is with every MailerLite post (from MailerLite's embed code)
};
