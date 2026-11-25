"""Pins the optional Paycheck Planner email capture include."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "paycheck-planner"
DATA = ROOT / "_data" / "paycheck_planner.yml"
INCLUDE = ROOT / "_includes" / "paycheck-planner-signup.html"
PAGES = {
    "sales": DIR / "index.html",
    "bundle": DIR / "bundle" / "index.html",
    "sample": DIR / "sample" / "index.html",
    "refund": DIR / "refund" / "index.html",
}
INCLUDE_TAG = '{% include paycheck-planner-signup.html %}'
DASH_RE = re.compile(r"[\u2014\u2013]|&mdash;|&ndash;", re.I)
PRICE_RE = re.compile(r"\$\d+(?:\.\d+)?")
FORM_ID = "205147354497549940"
ACTION = "https://assets.mailerlite.com/jsonp/1632878/forms/205147354497549940/subscribe"
BUY_PLANNER = '<a class="pp-btn" id="pp-buy-planner" href="{{ pp.stripe_url_planner }}" data-list-id="paycheck-planner" data-product="Paycheck Planner" data-price="14.99">Get the Paycheck Planner, $14.99</a>'
BUY_BUNDLE_ON_SALES = '<a class="pp-btn" id="pp-buy-bundle" href="{{ pp.stripe_url_bundle }}" data-list-id="paycheck-planner" data-product="Paycheck Planner Plus Bundle" data-price="39.00">Get the Plus Bundle, $39</a>'
BUY_BUNDLE = '<a class="pp-btn" id="pp-buy-bundle" href="{{ pp.stripe_url_bundle }}" data-list-id="paycheck-planner-bundle" data-product="Paycheck Planner Plus Bundle" data-price="39.00">Get the Plus Bundle, $39</a>'

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
html = {name: path.read_text(encoding="utf-8") if path.is_file() else "" for name, path in PAGES.items()}

check(INCLUDE.is_file(), "_includes/paycheck-planner-signup.html exists")
check(values.get("mailerlite_signup_action") == ACTION, "yml signup action is the new MailerLite form only")
check(values.get("mailerlite_signup_form_id") == FORM_ID and values.get("mailerlite_signup_form_slug") == "vRIwVD", "yml signup form id and slug match the new form")
check(values.get("mailerlite_form_slug") == "IW0v9B" and values.get("mailerlite_form_id") == "205066869153990151", "existing mini-sheet MailerLite form ids are unchanged")
check("mailerlite.com" not in inc and 'action="{{ pp.mailerlite_signup_action }}"' in inc, "include action comes from yml (no hardcoded MailerLite URL)")
check('action="{{ pp.mailerlite_signup_action }}"' in inc, "form action is the yml signup URL, not a hardcoded second form")
check(inc.count(FORM_ID) == 0, "include does not hardcode the numeric form id (reads _data)")
check('href="/privacy/"' in inc and "Privacy policy" in inc, "privacy line links /privacy/")
check("Not ready to buy? Get the free sample page by email." in inc, "headline is the agreed wording")
check('for="pp-signup-email">Email</label>' in inc, "the only visible field label is Email")
check('type="email"' in inc and inc.count('type="text"') == 0 and "fields[name]" not in inc, "the form collects Email only")
check(">Send me the sample</button>" in inc, "button says Send me the sample")
check("You'll get a confirmation email first." in inc, "confirmation-email note is present")
check("We use your email only to send the sample and planner tips. Unsubscribe anytime." in inc, "privacy line is the agreed wording")
check("Check your inbox to confirm, then we will send the sample." in inc, "success message is the agreed wording")
check('href="/paycheck-planner/sample/"' in inc and "Open the free sample page" in inc, "success message links the existing sample page")
check("payday checklist" not in inc.lower(), "include does not invent a payday checklist asset")
check(not DASH_RE.search(inc), "include has no em or en dashes")
check(not PRICE_RE.search(inc), "include has no price strings")
check("buy.stripe.com" not in inc and "checkout.stripe.com" not in inc, "include has no Stripe checkout URL")
check("guarantee" not in inc.lower() and not re.search(r"\bCDK\b", inc), "include has no guarantee and no bare CDK")
check("gtag(" not in inc and "G-5B1LNCPB56" not in inc, "include adds no GA tag")

for name in ("sales", "bundle", "sample"):
    check(INCLUDE_TAG in html[name], f"[{name}] includes paycheck-planner-signup.html")
    check(html[name].count(INCLUDE_TAG) == 1, f"[{name}] includes the signup block once")
check(INCLUDE_TAG not in html["refund"] and "pp-signup" not in html["refund"] and "mailerlite.com" not in html["refund"], "[refund] has no signup include and no MailerLite")

# Placement: include comes after the main buy section, never above a Buy button.
sales_buy = html["sales"].find(BUY_PLANNER)
sales_inc = html["sales"].find(INCLUDE_TAG)
check(sales_buy != -1 and sales_inc > sales_buy, "[sales] signup include is below the main Buy button")
bundle_buy = html["bundle"].find(BUY_BUNDLE)
bundle_inc = html["bundle"].find(INCLUDE_TAG)
check(bundle_buy != -1 and bundle_inc > bundle_buy, "[bundle] signup include is below the Buy button")
sample_cta = html["sample"].find('See the Paycheck Planner')
sample_inc = html["sample"].find(INCLUDE_TAG)
check(sample_cta != -1 and sample_inc > sample_cta, "[sample] signup include is below the full-year call to action")

# Buy buttons unchanged
check(BUY_PLANNER in html["sales"] and html["sales"].count('id="pp-buy-planner"') == 1, "[sales] planner Buy button is unchanged")
check(BUY_BUNDLE_ON_SALES in html["sales"] and html["sales"].count('id="pp-buy-bundle"') == 1, "[sales] bundle Buy button is unchanged")
check(BUY_BUNDLE in html["bundle"] and html["bundle"].count('id="pp-buy-bundle"') == 1, "[bundle] Buy button is unchanged")
check("buy.stripe.com" not in html["sales"] and "buy.stripe.com" not in html["bundle"], "page source still has no hardcoded Stripe URL")

# The signup block itself (the include file) is the form action source
for name in ("sales", "bundle", "sample"):
    # After Liquid would render; in source, action is the Liquid tag
    check('action="{{ pp.mailerlite_signup_action }}"' in inc, "source form action is the yml key")

if failed:
    print(f"FAILED {len(failed)} check(s)")
    sys.exit(1)
print("ALL PLANNER SIGNUP CHECKS PASSED")
