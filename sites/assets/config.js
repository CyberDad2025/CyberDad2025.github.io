/* Site config — the single place to change the brand and how requests are delivered.
   Section of the existing site: https://getcyberdadkit.com/sites/ (custom domain, apex).
   Submitting opens the visitor's own email app (mailto) with the answers pre-filled,
   addressed to CONTACT_EMAIL. Nothing is sent until the visitor presses Send. No paid service, no backend. */
window.SITE_CONFIG = {
  BRAND: "CyberDad Kit Sites",                    // visible brand (P59 final name; rename only with ventures/web-refresh/build/swap-brand.sh)
  LEGAL: "CyberDad Kit LLC",
  CONTACT_EMAIL: "ruel@getcyberdadkit.com",
  MAILTO_MAX: 1800                       // keep mailto links short enough for common mail apps
};
