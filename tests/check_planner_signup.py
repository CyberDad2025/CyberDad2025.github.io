"""Pins the optional Paycheck Planner email capture include."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "paycheck-planner"
DATA = ROOT / "_data" / "paycheck_planner.yml"
INCLUDE = ROOT / "_includes" / "paycheck-planner-signup.html"
EMBED = ROOT / "_includes" / "paycheck-planner-ml-embed.html"
PAGES = {
    "sales": DIR / "index.html",
    "bundle": DIR / "bundle" / "index.html",
    "sample": DIR / "sample" / "index.html",
    "refund": DIR / "refund" / "index.html",
}
INCLUDE_TAG = '{% include paycheck-planner-signup.html %}'
EMBED_TAG = '{% include paycheck-planner-ml-embed.html %}'
LOADER = "assets.mailerlite.com/js/universal.js"
OFFICIAL_LOADER = (
    "if(!window.ml){(function(w,d,e,u,f,l,n){w[f]=w[f]||function(){(w[f].q=w[f].q||[]).push(arguments);},"
    "l=d.createElement(e),l.async=1,l.src=u,n=d.getElementsByTagName(e)[0],n.parentNode.insertBefore(l,n);})"
    "(window,document,'script','https://assets.mailerlite.com/js/universal.js','ml');"
    "ml('enablePopups',false);ml('account','1632878');}"
)
DASH_RE = re.compile(r"[\u2014\u2013]|&mdash;|&ndash;", re.I)
PRICE_RE = re.compile(r"\$\d+(?:\.\d+)?")
FORM_ID = "205066869153990151"
UNUSED_FORM = "205147" + "354497549940"
# Marketing pass 1125: Buy markup now also carries data-pp-ref (click-time attribution); hrefs still read _data/paycheck_planner.yml.
BUY_PLANNER = '<a class="pp-btn" id="pp-buy-planner" href="{{ pp.stripe_url_planner }}" data-list-id="paycheck-planner" data-product="Paycheck Planner" data-price="14.99" data-pp-ref="planner">Get the Paycheck Planner, $14.99</a>'
BUY_BUNDLE_ON_SALES = '<a class="pp-btn" id="pp-buy-bundle" href="{{ pp.stripe_url_bundle }}" data-list-id="paycheck-planner" data-product="Paycheck Planner Plus Bundle" data-price="39.00" data-pp-ref="bundle">Get the Plus Bundle, $39</a>'
BUY_BUNDLE = '<a class="pp-btn" id="pp-buy-bundle" href="{{ pp.stripe_url_bundle }}" data-list-id="paycheck-planner-bundle" data-product="Paycheck Planner Plus Bundle" data-price="39.00" data-pp-ref="bundle">Get the Plus Bundle, $39</a>'

failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    if ok:
        print(f"  PASS  {msg}")
    else:
        failed.append(msg)
        print(f"  FAIL  {msg}")


def values_from_yml(text: str) -> dict[str, str]:
    return dict(re.findall(r'^([a-z_]+):\s*"([^"]*)"\s*$', text, re.M))


data_text = DATA.read_text(encoding="utf-8")
values = values_from_yml(data_text)
inc = INCLUDE.read_text(encoding="utf-8") if INCLUDE.is_file() else ""
embed = EMBED.read_text(encoding="utf-8") if EMBED.is_file() else ""
html = {name: path.read_text(encoding="utf-8") if path.is_file() else "" for name, path in PAGES.items()}

check(INCLUDE.is_file(), "_includes/paycheck-planner-signup.html exists")
check(EMBED.is_file(), "_includes/paycheck-planner-ml-embed.html exists")
check(values.get("mailerlite_form_slug") == "IW0v9B" and values.get("mailerlite_form_id") == FORM_ID, "yml still points at the existing mini-sheet form IW0v9B")
check("mailerlite_signup_form_id" not in values and "mailerlite_signup_action" not in values, "yml has no separate signup form keys")

check('{% include paycheck-planner-ml-embed.html lazy=true %}' in inc and inc.count('paycheck-planner-ml-embed.html') == 1 and EMBED_TAG not in inc, "signup include uses the shared official embed once, lazy-loaded")
check(EMBED_TAG in html["sample"] and html["sample"].count(EMBED_TAG) == 1, "[sample] uses the same shared official embed once")
check(OFFICIAL_LOADER in embed and 'class="ml-embedded"' in embed and 'data-form="{{ pp.mailerlite_form_slug }}"' in embed, "shared embed is the official IW0v9B MailerLite markup")
check("IntersectionObserver" in embed and "rootMargin:'200px 0px'" in embed and "window.cdkLoadMl" in embed, "shared embed can lazy-load universal.js when the box is near the viewport")
check(embed.count("if(!window.ml){(function(w,d,e,u,f,l,n)") == 1, "official loader function is defined once in the shared embed")
check(embed.count(LOADER) == 1 and embed.count('class="ml-embedded"') == 1, "shared embed loads universal.js once and has one ml-embedded box")
check('contains "_TODO"' in embed and "pp-sample-placeholder" in embed, "shared embed keeps the marked placeholder when the form slug is unset")
check("assets.mailerlite.com/jsonp" not in embed and "connect.mailerlite.com" not in embed, "shared embed does not post to the custom jsonp or connect endpoints")
check(LOADER not in inc and 'class="ml-embedded"' not in inc, "signup include does not copy the embed markup; it shares the include")
check(LOADER not in html["sample"] and 'class="ml-embedded"' not in html["sample"], "[sample] no longer inlines a second copy of the embed")

check("Get the free Mini Sheet and paycheck tips" in inc, "wrapper heading is Growth's Mini Sheet and tips line")
check("Get free paycheck budgeting tips" not in inc and "Not ready to buy?" not in inc, "wrapper no longer uses the placeholder or old heading")
check("Get the free Paycheck-to-Bills Mini Sheet" not in inc, "wrapper does not repeat the embed heading")
check("A free sample you can use on your next payday, plus occasional planning tips. For people in the US and Canada." in inc, "wrapper body is Growth's Mini Sheet and tips line")
check("You'll get a confirmation email first." not in inc, "old confirmation-email note is gone")
check('href="/privacy/"' in inc and "Privacy Policy" in inc, "wrapper still links /privacy/")
check("By signing up, you agree to get paycheck planning tips by email. Unsubscribe anytime." in inc, "wrapper has the consent line")
check('id="pp-signup-consent"' in inc and 'See the <a href="/privacy/">Privacy Policy</a>.' in inc, "consent line links Privacy Policy")
check("pp-signup-privacy" not in inc, "standalone privacy-only line is folded into the consent line")
check("We use your email only to send the sample and planner tips" not in inc, "wrapper does not repeat the embed privacy sentence")
check("Check your inbox to confirm" not in inc, "wrapper does not repeat the official embed success line")
check("we will" not in inc and "we will" not in embed, "signup include and shared embed have no 'we will'")
check("pp-signup-form" not in inc and "fields[email]" not in inc and "ml-submit" not in inc, "custom jsonp form and hidden fields are gone")
check("payday checklist" not in inc.lower() and "payday checklist" not in embed.lower(), "include does not invent a payday checklist asset")
check(not DASH_RE.search(inc) and not DASH_RE.search(embed), "include and shared embed have no em or en dashes")
check(not PRICE_RE.search(inc) and not PRICE_RE.search(embed), "include and shared embed have no price strings")
check("buy.stripe.com" not in inc and "checkout.stripe.com" not in inc and "buy.stripe.com" not in embed and "checkout.stripe.com" not in embed, "include has no Stripe checkout URL")
check("guarantee" not in inc.lower() and not re.search(r"\bCDK\b", inc) and "guarantee" not in embed.lower() and not re.search(r"\bCDK\b", embed), "include has no guarantee and no bare CDK")
check("gtag(" not in inc and "G-5B1LNCPB56" not in inc and "gtag(" not in embed and "G-5B1LNCPB56" not in embed, "include adds no GA tag")

for name in ("sales", "bundle"):
    check(INCLUDE_TAG in html[name] and html[name].count(INCLUDE_TAG) == 1, f"[{name}] includes paycheck-planner-signup.html once")
    check(EMBED_TAG not in html[name], f"[{name}] does not include the embed directly (it comes through the signup include)")
check(INCLUDE_TAG not in html["sample"] and "pp-signup" not in html["sample"], "[sample] has no signup include")
check(html["sample"].count(EMBED_TAG) == 1, "[sample] keeps exactly one email form, the shared IW0v9B embed")
check(INCLUDE_TAG not in html["refund"] and EMBED_TAG not in html["refund"] and "pp-signup" not in html["refund"] and "mailerlite.com" not in html["refund"], "[refund] has no signup include and no MailerLite")

# Placement: include sits immediately after the last Buy block (the Plus Bundle section on sales, the hero Buy block on bundle).
sales_last_buy = max(html["sales"].rfind(BUY_PLANNER), html["sales"].rfind(BUY_BUNDLE_ON_SALES))
sales_inc = html["sales"].find(INCLUDE_TAG)
sales_who = html["sales"].find('id="who"')
check(sales_last_buy != -1 and sales_who != -1 and sales_last_buy < sales_inc < sales_who, "[sales] signup include is immediately after the last Buy block and before Who it is for")
check(html["sales"].find('id="guides"') > sales_inc, "[sales] guides stay below the signup include (only one include)")
bundle_buy = html["bundle"].rfind(BUY_BUNDLE)
bundle_inc = html["bundle"].find(INCLUDE_TAG)
bundle_inc_title = html["bundle"].find('id="inc-title"')
check(bundle_buy != -1 and bundle_inc_title != -1 and bundle_buy < bundle_inc < bundle_inc_title, "[bundle] signup include is immediately after the Buy block and before the includes section")

check(BUY_PLANNER in html["sales"] and html["sales"].count('id="pp-buy-planner"') == 1, "[sales] planner Buy button is unchanged")
check(BUY_BUNDLE_ON_SALES in html["sales"] and html["sales"].count('id="pp-buy-bundle"') == 1, "[sales] bundle Buy button is unchanged")
check(BUY_BUNDLE in html["bundle"] and html["bundle"].count('id="pp-buy-bundle"') == 1, "[bundle] Buy button is unchanged")

site_texts = [data_text, inc, embed, html["sales"], html["bundle"], html["sample"], html["refund"]]
check(all(UNUSED_FORM not in t for t in site_texts), "planner pages, includes, and yml do not reference the unused new form")

if failed:
    print(f"FAILED {len(failed)} check(s)")
    sys.exit(1)
print("ALL PLANNER SIGNUP CHECKS PASSED")
