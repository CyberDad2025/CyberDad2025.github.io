#!/usr/bin/env python3
"""Checks for the Screen-Free Kids Activity Bundle pages (/screen-free/ and /screen-free/refund/).

The Buy href on /screen-free/ and on the /holiday/ card reads _data/screen_free.yml stripe_link, the one
place to swap the Payment Link. Copy is from Product's LISTING.md 0d120a4a and REFUND.md ae2b23a9.
The free sample is delivered as a direct PDF link on the page (no signup form).

Run: python3 tests/check_screen_free.py
"""
from __future__ import annotations

import hashlib
import html as html_lib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data" / "screen_free.yml"
PAGE = ROOT / "screen-free" / "index.html"
REFUND = ROOT / "screen-free" / "refund" / "index.html"
CARD_PAGE = ROOT / "holiday" / "index.html"
FOOTER = ROOT / "_includes" / "site-footer.html"
CSS = ROOT / "screen-free" / "assets" / "screen-free.css"
SAMPLE = ROOT / "screen-free" / "assets" / "CyberDadKit-Screen-Free-Kids-Activity-Bundle-FREE-SAMPLE-US-Letter.pdf"
SAMPLE_SHA = "8af161962f355d67cbd7e6caf9a2548a336b2b9cda1946da6a96962fefede03b"
STRIPE_LINK = "https://buy.stripe.com/6oU6oG11Y3Q48qF9Ijds40i"
PAID_ZIP_SHAS = {"626ee0f68aec102150d97e8667e5ac8d1ffbd7207f9635bf9e733f9abd8741a4", "5f1525ad18eed7b9450c913184f35a54c1319c2d181e36491d6b9126fb65c734"}
ADDRESS = "CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794"
BUY_LABEL = "Buy Screen-Free Kids Activity Bundle for $14.99 USD"
BANNER = ('<p><strong>Available only to customers located in the United States.</strong> '
          'Digital download only; nothing is shipped.</p>')
PRICE_LINE = ('<p class="hday-price"><span class="hday-price-meta">USD</span> <span class="hday-price-amount">$14.99</span> '
              '<span class="hday-price-meta">one-time, US customers only</span></p>')
REFUND_TEXT = ("Screen-Free Kids Activity Bundle is a digital product. You may request a full refund for any reason within 7 days "
               "of your purchase date. Email ruel@getcyberdadkit.com with the email address used for purchase and your order "
               "reference. Never send card details. Refunds are returned to the original payment method. No physical return is required.")
BANNED = {
    "em or en dash": r"[\u2014\u2013]",
    "guarantee": r"\bguarantee",
    "bare CDK": r"\bCDK\b",
    "age": r"\bages?\b|\d+\s*\+|years?[ -]old|\btoddlers?\b|\bpreschool|\bteens?\b|\bgrade\s*\d|\bkindergarten",
    "gender": r"\b(?:boys?|girls?|sons?|daughters?|he|she|him|his|hers?)\b",
    "number of kids": r"\b(?:one|two|three|four|five|\d+)\s+(?:kids?|child(?:ren)?)\b|\bonly child\b",
    "family details": r"\bfamil(?:y|ies)\b|\b(?:mom|dad|mother|father|wife|husband|siblings?|grandparents?)\b",
    "employer": r"\bemployers?\b|\bmy job\b|\bwhere I work\b",
    "seasonal": r"\b(?:holidays?|thanksgiving|christmas|winter|summer|spring break|fall|autumn|halloween|easter|seasonal|snow|santa|turkey|harvest)\b",
    "non-US offer": r"\bworldwide\b|\binternational shipping\b|\bships? to\b",
    "A4": r"\bA4\b",
    "trademark": r"\bspot[- ]it\b|\bi spy\b",
    "unfilled placeholder": r"\[[A-Z ]+:|\bpending\b",
}
failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def visible(text: str) -> str:
    text = re.sub(r"\A---.*?---", " ", text, flags=re.S)
    text = re.sub(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|\{%.*?%\}|\{\{.*?\}\}", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html_lib.unescape(text))


data = DATA.read_text(encoding="utf-8")
keys = re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:", data, re.M)
check(keys == ["stripe_link"], f"_data/screen_free.yml has only stripe_link ({keys})")
check(re.search(r'^stripe_link: "' + re.escape(STRIPE_LINK) + '"$', data, re.M) is not None, "stripe_link is the approved Payment Link")
check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)|checkout\.stripe\.com|\.zip\b", data, re.I),
      "data file has no Drive, checkout session, or ZIP URL")

html = PAGE.read_text(encoding="utf-8")
refund = REFUND.read_text(encoding="utf-8")
card_match = re.search(r'<article class="mp-card" id="screen-free".*?</article>', CARD_PAGE.read_text(encoding="utf-8"), re.S)
card = card_match.group(0) if card_match else ""
check(bool(card), "/holiday/ Screen-Free card exists")
check("sitemap: true" in html and "sitemap: true" in refund and "noindex" not in html + refund, "both pages are indexable sitemap pages")
check(html.count(BANNER) == 1 and refund.count(BANNER) == 1, "banner states US-only and digital-only once per page")
check(html.count(PRICE_LINE) == 1, "hero shows the LISTING price line USD $14.99 one-time, US customers only")
check(set(re.findall(r"\$\d+(?:\.\d{2})?", html + refund + card)) == {"$14.99"}, "$14.99 is the only price")
check(html.count(BUY_LABEL) == 1 and card.count(BUY_LABEL) == 1, "Buy labels keep the GA4 product and price format")
check(html.count('href="{{ site.data.screen_free.stripe_link }}"') == 1, "product Buy href reads _data/screen_free.yml")
check('data-list-id="screen-free"' in html and 'data-product="Screen-Free Kids Activity Bundle"' in html and 'data-price="14.99"' in html,
      "product Buy button carries GA4 list, product and price data")
check('href="{{ site.data.screen_free.stripe_link }}"' in card and 'data-list-id="holiday-screen-free"' in card,
      "/holiday/ card uses the same one-line data value")
check("buy.stripe.com" not in html + refund + card and "checkout.stripe.com" not in html + refund + card, "pages hold no hard-coded Stripe URL")
for label, text in (("/screen-free/", html), ("/screen-free/refund/", refund)):
    check(text.count("{% include ga4.html %}") == 1, f"{label} includes GA4 once")
    check(text.count("{% include site-footer.html %}") == 1, f"{label} uses the shared site footer")
    check('<body class="festive festive-screen-free">' in text, f"{label} uses the evergreen festive style")
    check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)|\.zip\b", text, re.I), f"{label} has no paid Drive or ZIP link")
    vis = visible(text)
    for name, pattern in BANNED.items():
        check(not re.search(pattern, vis, re.I), f"{label} visible copy has no {name}")
    check("United States" in vis, f"{label} states the US-only offer")
check(re.search(BANNED["em or en dash"] + "|" + BANNED["guarantee"] + "|" + BANNED["bare CDK"], visible(card), re.I) is None,
      "/holiday/ card has no dash, guarantee or bare CDK")
for line in ("Give your kids something fun to do without handing them your phone.",
             "Print a few pages before your next restaurant wait, rainy afternoon or long drive, and keep them in your bag with a pencil.",
             "The Screen-Free Kids Activity Bundle gives you 34 pages to print at home for exactly those moments",
             "Try a free sample activity first.",
             "You may print copies for your own personal, noncommercial use at home and on the go."):
    check(line in visible(html), f"product page carries LISTING line: {line[:48]}")
check(REFUND_TEXT in visible(refund) and "Screen-Free Kids Activity Bundle refund policy" in refund, "refund page carries REFUND.md heading and text")
check(ADDRESS in FOOTER.read_text(encoding="utf-8"), "shared footer has the exact address line")
built = [ROOT / "_site" / "screen-free" / "index.html", ROOT / "_site" / "screen-free" / "refund" / "index.html"]
if all(p.is_file() for p in built):
    rendered = [p.read_text(encoding="utf-8") for p in built]
    check(rendered[0].count(ADDRESS) == 1 and rendered[1].count(ADDRESS) == 2, "built pages show the exact address line (footer; refund page also in the REFUND.md text)")
    check(all("{{" not in r and "{%" not in r for r in rendered), "built pages have no unrendered Liquid")
    check(rendered[0].count(f'href="{STRIPE_LINK}"') == 1, "built product page has the approved Buy link once")
    built_card = ROOT / "_site" / "holiday" / "index.html"
    if built_card.is_file():
        check(f'data-list-id="holiday-screen-free" data-product="Screen-Free Kids Activity Bundle" data-price="14.99" href="{STRIPE_LINK}"' in built_card.read_text(encoding="utf-8"), "built /holiday/ card has the approved Buy link")
    check(all(REFUND_TEXT in visible(r) for r in rendered), "built pages carry the REFUND.md policy text verbatim")
else:
    print("note _site not present; skipped rendered checks")

check(SAMPLE.is_file() and hashlib.sha256(SAMPLE.read_bytes()).hexdigest() == SAMPLE_SHA, "free sample PDF is sha256 8af16196...")
check(html.count('href="/screen-free/assets/CyberDadKit-Screen-Free-Kids-Activity-Bundle-FREE-SAMPLE-US-Letter.pdf"') == 1,
      "product page links the free sample once")
assets = [p for p in (ROOT / "screen-free").rglob("*") if p.is_file()]
check(not any(p.suffix.lower() == ".zip" or hashlib.sha256(p.read_bytes()).hexdigest() in PAID_ZIP_SHAS for p in assets),
      "no paid ZIP is committed under screen-free/")
check([p.name for p in assets if p.suffix.lower() == ".pdf"] == [SAMPLE.name], "the free sample is the only PDF under screen-free/")
css = CSS.read_text(encoding="utf-8")
check(all(f"--festive-icon-{x}: var(--festive-star" in css for x in "abc"), "evergreen ribbon uses star icons, not seasonal icons")

if failed:
    print(f"FAILED {len(failed)} check(s)")
    sys.exit(1)
print("ALL SCREEN-FREE CHECKS PASSED")
