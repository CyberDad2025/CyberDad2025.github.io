/* Site config — the single place to change the brand and how requests are delivered.
   Section of the existing site: https://cyberdad2025.github.io/sites/ (no new domain).
   Submitting opens the visitor's own email app (mailto) with the answers pre-filled,
   addressed to CONTACT_EMAIL. Nothing is sent until the visitor presses Send. No paid service, no backend. */
window.SITE_CONFIG = {
  BRAND: "CyberDad Kit Sites",           // working brand name
  LEGAL: "CyberDad Kit LLC",
  CONTACT_EMAIL: "ruel@getcyberdadkit.com",
  MAILTO_MAX: 1800                       // keep mailto links short enough for common mail apps
};
