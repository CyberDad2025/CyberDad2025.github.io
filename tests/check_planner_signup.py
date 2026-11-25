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
FORM_ID = "205066869153990151"
ACTION_MARK = 'action="https://assets.mailerlite.com/jsonp/1632878/forms/{{ pp.mailerlite_form_id }}/subscribe"'
UNUSED_FORM = "205147" + "354497549940"
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
check(values.get("mailerlite_form_slug") == "IW0v9B" and values.get("mailerlite_form_id") == FORM_ID, "yml still points at the existing mini-sheet form IW0v9B")
check("mailerlite_signup_form_id" not in values and "mailerlite_signup_action" not in values, "yml has no separate signup form keys")
check(ACTION_MARK in inc, "include posts to IW0v9B's jsonp subscribe endpoint via mailerlite_form_id")
check(inc.count("mailerlite.com") == 1 and inc.count("forms/{{ pp.mailerlite_form_id }}/subscribe") == 1, "include has one MailerLite action, the IW0v9B endpoint")
check('name="fields[email]"' in inc and 'name="ml-submit" value="1"' in inc and 'name="anticsrf" value="true"' in inc, "include uses the same email field and hidden inputs as the live IW0v9B embed")
check(inc.count('type="email"') == 1 and "fields[name]" not in inc, "the form collects Email only")
check('for="pp-signup-email">Email</label>' in inc, "the only visible field label is Email")
check("Not ready to buy? Get the free Paycheck-to-Bills Mini Sheet by email." in inc, "headline promises the free Mini Sheet")
check(">Send me the free sheet</button>" in inc, "button matches the live IW0v9B button")
check("You'll get a confirmation email first." in inc, "confirmation-email note is present")
check("We use your email only to send the sample and planner tips. Unsubscribe anytime." in inc, "privacy line is unchanged")
check('href="/privacy/"' in inc and "Privacy policy" in inc, "privacy line links /privacy/")
check("Check your inbox to confirm, then we'll send the free Paycheck-to-Bills Mini Sheet." in inc, "success line uses we'll and names the Mini Sheet")
check("we will" not in inc, "include has no 'we will'")
check("payday checklist" not in inc.lower(), "include does not invent a payday checklist asset")
check(not DASH_RE.search(inc), "include has no em or en dashes")
check(not PRICE_RE.search(inc), "include has no price strings")
check("buy.stripe.com" not in inc and "checkout.stripe.com" not in inc, "include has no Stripe checkout URL")
check("guarantee" not in inc.lower() and not re.search(r"\bCDK\b", inc), "include has no guarantee and no bare CDK")
check("gtag(" not in inc and "G-5B1LNCPB56" not in inc, "include adds no GA tag")

for name in ("sales", "bundle"):
    check(INCLUDE_TAG in html[name] and html[name].count(INCLUDE_TAG) == 1, f"[{name}] includes paycheck-planner-signup.html once")
check(INCLUDE_TAG not in html["sample"] and "pp-signup" not in html["sample"], "[sample] has no signup include")
check(html["sample"].count('class="ml-embedded"') == 1 and html["sample"].count("assets.mailerlite.com/js/universal.js") == 1, "[sample] keeps exactly one email form, the IW0v9B embed")
check(INCLUDE_TAG not in html["refund"] and "pp-signup" not in html["refund"] and "mailerlite.com" not in html["refund"], "[refund] has no signup include and no MailerLite")

# Placement: include comes after the last Buy button in source order.
sales_last_buy = max(html["sales"].rfind(BUY_PLANNER), html["sales"].rfind(BUY_BUNDLE_ON_SALES))
sales_inc = html["sales"].find(INCLUDE_TAG)
check(sales_last_buy != -1 and sales_inc > sales_last_buy, "[sales] signup include is after the last Buy button")
bundle_buy = html["bundle"].rfind(BUY_BUNDLE)
bundle_inc = html["bundle"].find(INCLUDE_TAG)
check(bundle_buy != -1 and bundle_inc > bundle_buy, "[bundle] signup include is after the Buy button")

check(BUY_PLANNER in html["sales"] and html["sales"].count('id="pp-buy-planner"') == 1, "[sales] planner Buy button is unchanged")
check(BUY_BUNDLE_ON_SALES in html["sales"] and html["sales"].count('id="pp-buy-bundle"') == 1, "[sales] bundle Buy button is unchanged")
check(BUY_BUNDLE in html["bundle"] and html["bundle"].count('id="pp-buy-bundle"') == 1, "[bundle] Buy button is unchanged")

site_texts = [data_text, inc, html["sales"], html["bundle"], html["sample"], html["refund"]]
check(all(UNUSED_FORM not in t for t in site_texts), "planner pages, include, and yml do not reference the unused new form")

if failed:
    print(f"FAILED {len(failed)} check(s)")
    sys.exit(1)
print("ALL PLANNER SIGNUP CHECKS PASSED")
