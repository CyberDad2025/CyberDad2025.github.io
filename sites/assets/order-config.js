/* Rebuild order form config (P60, adopted in P59): the ONLY place to wire the /sites/#start order form to a backend.
   GitHub Pages is static, so answers go to a MailerLite embedded form (the owner's existing $0 tool).

   >>> PLACEHOLDER: ACTION_URL is empty on purpose. The MailerLite form does not exist yet. <<<
   While ACTION_URL is "", the form uses the email fallback: it copies the answers for the visitor and opens their
   own email app with a FIXED subject and NO body (answers are never put in a mailto: link or any URL).

   To wire it (after the privacy policy is updated to name MailerLite for website requests):
     1. Create the MailerLite embedded form + fields listed in platform/evidence/p59/ORDER-BACKEND.md.
     2. Paste its action URL below: https://assets.mailerlite.com/jsonp/<ACCOUNT_ID>/forms/<FORM_ID>/subscribe
     3. Make sure every FIELDS value matches the field "tag" MailerLite shows in the form's HTML code.
   Nothing else changes. Do not put API keys or tokens here: the action URL is public by design. */
window.SITE_ORDER_CONFIG = {
  ACTION_URL: "",              // PLACEHOLDER: MailerLite embedded-form action URL (leave "" to keep the email fallback)
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
