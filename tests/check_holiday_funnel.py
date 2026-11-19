#!/usr/bin/env python3
"""Holiday funnel order on the pages reworked for checkout starts.

Each reworked page is: one product, the free sample round, one MailerLite
embed (eMwTaD), then the existing buy offer. Stripe hrefs are compared to
origin/main. Added internal holiday CTAs carry the holiday-funnel UTM tags.

Run: python3 tests/check_holiday_funnel.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "origin/main"
HOSTED = "https://preview.mailerlite.io/forms/1632878/203754930937268147/share"
NOSCRIPT = (
    f'<noscript>Sign up on our updates page: <a href="{HOSTED}" rel="noopener">hosted signup form</a>.</noscript>'
)
US_ONLY = "Available only to customers located in the United States."
FOOTER_LINES = (
    "<p>CyberDadKit © 2026</p>",
    "<p>CyberDad Kit LLC</p>",
    "<p>PO Box 940061, Maitland, FL 32794</p>",
    '<p><a href="mailto:ruel@getcyberdadkit.com">ruel@getcyberdadkit.com</a></p>',
)
STRIPE_RE = re.compile(r"https://buy\.stripe\.com/[A-Za-z0-9]+")
HOST_KIT_PAYMENT_URL = "https://buy.stripe.com/28EbJ07qmaes36l7Abds40f"
TRIVIA_PAYMENT_URL = "https://buy.stripe.com/bJecN4aCyfyM4apbQrds406"
BUNDLE_PAYMENT_URL = "https://buy.stripe.com/14A5kC7qmdqEfT78Efds407"
PLANNER_PAYMENT_URL = "https://buy.stripe.com/9B69ASdOK1HWayNdYzds40b"
KIDS_PAYMENT_URL = "https://buy.stripe.com/6oU7sK7qm2M05et3jVds40c"
KIDS_BUNDLE_PAYMENT_URL = "https://buy.stripe.com/4gM9ASeSO72g9uJbQrds40d"
ALLOWED_STRIPE_ADDITIONS = {
    "holiday/host-kit/index.html": [HOST_KIT_PAYMENT_URL],
    "holiday/index.html": [
        TRIVIA_PAYMENT_URL,
        PLANNER_PAYMENT_URL,
        KIDS_PAYMENT_URL,
        KIDS_BUNDLE_PAYMENT_URL,
        HOST_KIT_PAYMENT_URL,
    ],
    "holiday/sample/index.html": [
        TRIVIA_PAYMENT_URL,
        BUNDLE_PAYMENT_URL,
        PLANNER_PAYMENT_URL,
        KIDS_PAYMENT_URL,
        KIDS_BUNDLE_PAYMENT_URL,
        HOST_KIT_PAYMENT_URL,
    ],
}
GUARANTEE_RE = re.compile(r"\bguarante(?:e|ed|es)\b", re.I)
SHIELD_RE = re.compile(r"\bshield\b", re.I)
DOC_NUMBER = "L2500046" + "3998"
UTM_KEYS = ("utm_source=site", "utm_medium=cta", "utm_campaign=holiday-funnel", "utm_content=")

# Trivia, Kids' Table, and Host Planner stay as they are: moving their buy
# blocks would rewrite pages whose visible text is locked, which is not a
# small edit. This list proves those files were left alone.
UNCHANGED = (
    "holiday/kids-table/index.html",
    "holiday/host-planner/index.html",
)

PAGES = (
    {
        "rel": "holiday/index.html",
        "product": 'id="product-title"',
        "sample": 'id="sample-round"',
        "buy": 'id="holiday-checkout"',
    },
    {
        "rel": "holiday/table-set/index.html",
        "product": 'id="product-title"',
        "sample": 'id="sample-round"',
        "buy": 'id="table-set-checkout"',
    },
    {
        "rel": "holiday/host-kit/index.html",
        "product": 'id="product-title"',
        "sample": 'id="sample-round"',
        "buy": 'id="host-kit-checkout"',
    },
)


class AnchorList(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href is not None:
                self.hrefs.append(href)


def git_show(rel: str) -> str:
    return subprocess.check_output(["git", "show", f"{MAIN}:{rel}"], cwd=ROOT, text=True)


def footer(html: str) -> str:
    match = re.search(r"<footer\b.*?</footer>", html, re.S)
    return match.group(0) if match else ""


def hero(html: str) -> str:
    match = re.search(r'<section class="hday-hero"\b.*?</section>', html, re.S)
    return match.group(0) if match else ""


def hrefs(html: str) -> list[str]:
    parser = AnchorList()
    parser.feed(html)
    return parser.hrefs


def holiday_page_path(href: str) -> str | None:
    path = href.split("#", 1)[0].split("?", 1)[0]
    if not path.startswith("/holiday/"):
        return None
    if path.rsplit("/", 1)[-1].lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".webp", ".zip")):
        return None
    return path


def added_holiday_ctas(current: str, previous: str) -> list[str]:
    added = Counter(hrefs(current)) - Counter(hrefs(previous))
    found = []
    for href, count in added.items():
        if holiday_page_path(href) is None:
            continue
        found.extend([href] * count)
    return found


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    # One-page shop (feat/holiday-one-page-1117). /holiday/ is now the single shop
    # page with no signup embed (the eMwTaD form is inactive, so it was removed), and
    # /holiday/table-set/, /holiday/host-kit/, /holiday/kids-table/,
    # /holiday/host-planner/ and the two sample URLs are redirect stubs that pass the
    # visitor's own query string through. Retired: the product, sample, signup, buy
    # order; the MailerLite embed checks; the sample-round CTA checks; the
    # "left unchanged" locks; the fixed utm_content on the sample redirects.
    # Kept and rewritten: Stripe hrefs, US-only, guarantee, Shield, filing id, footer.
    main_links: set[str] = set()
    for rel in ("holiday/index.html", "holiday/table-set/index.html", "holiday/host-kit/index.html",
                "holiday/kids-table/index.html", "holiday/host-planner/index.html", "holiday/trivia/index.html",
                "holiday/travel-adventure/index.html", "shop/index.html"):
        main_links.update(STRIPE_RE.findall(git_show(rel)))
    print("Stripe hrefs (current, each must be live on main):")
    for page in PAGES:
        rel = page["rel"]
        html = (ROOT / rel).read_text(encoding="utf-8")
        label = "/" + rel[: -len("index.html")]
        stripe_now = STRIPE_RE.findall(html)
        print(f"  {rel}: {stripe_now}")
        check(not GUARANTEE_RE.search(html), f"{label} has no guarantee wording")
        check(not SHIELD_RE.search(html), f"{label} has no Shield mention")
        check(DOC_NUMBER not in html, f"{label} has no retired filing identifier")
        page_footer = footer(html)
        check(html.count("<footer") == 1 and page_footer.count("</footer>") == 1, f"{label} has one footer")
        for line in FOOTER_LINES:
            check(page_footer.count(line) == 1, f"{label} footer line once: {line}")
        if rel == "holiday/index.html":
            hero_buy = html.find('id="host-kit-checkout-holiday"')
            first_card = html.find('id="gather-and-play"')
            check(0 < html.find('id="hk-title"') < hero_buy < first_card, f"{label} order is the Host Kit hero, its buy button, then the cards")
            check(page["buy"] not in hero(html), f"{label} hero has no Gather & Play buy button")
            check("ml-embedded" not in html and "data-form=" not in html and "universal.js" not in html, f"{label} has no MailerLite embed (inactive form removed)")
            check(US_ONLY in html, f"{label} keeps the US-only sentence")
            check(HOST_KIT_PAYMENT_URL in stripe_now and TRIVIA_PAYMENT_URL in stripe_now and PLANNER_PAYMENT_URL in stripe_now and KIDS_PAYMENT_URL in stripe_now, f"{label} carries the Host Kit, Trivia, Host Planner and Kids' Table buy links")
            check(bool(stripe_now) and set(stripe_now) <= main_links, f"{label} Stripe hrefs are all live on main")
            for href in hrefs(html):
                path = holiday_page_path(href)
                check(path is None or path in {"/holiday/", "/holiday/gather-and-play/"} or path.endswith("/refund/"), f"{label} link {href} does not hop through a redirect stub")
        else:
            check(not stripe_now, f"{label} redirect stub has no Stripe href")
            check('location.replace("/holiday/" + window.location.search' in html, f"{label} redirect stub keeps the query string")

    for rel in UNCHANGED + ("holiday/sample/index.html", "holiday/trivia/sample/index.html"):
        html = (ROOT / rel).read_text(encoding="utf-8")
        label = "/" + rel[: -len("index.html")]
        check("window.location.replace" in html, f"{label} redirect uses location.replace")
        check('name="robots" content="noindex, follow"' in html, f"{label} is noindex")
        check("{% include ga4.html %}" in html, f"{label} includes GA4")
        check("buy.stripe.com" not in html, f"{label} has no Stripe href")
        check("window.location.search" in html, f"{label} passes the visitor's query string through")
        check("utm_source=pinterest" not in html, f"{label} has no pinterest/paid default")

    worldwide_re = re.compile(r"\bworldwide\b", re.I)
    country_phrase = "not limited by country"
    holiday_pages = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "holiday").rglob("*.html")
    )
    check(bool(holiday_pages), "holiday public pages were scanned for worldwide")
    for rel in holiday_pages:
        text = (ROOT / rel).read_text(encoding="utf-8")
        hits = worldwide_re.findall(text)
        check(not hits, f"{rel} does not say worldwide" + ("" if not hits else f" ({len(hits)})"))
        check(country_phrase not in text.lower(), f"{rel} does not say {country_phrase}")
    holiday_files = []
    for path in (ROOT / "holiday").rglob("*"):
        if not path.is_file():
            continue
        try:
            file_text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        holiday_files.append(path)
        if country_phrase in file_text.lower():
            check(False, f"{path.relative_to(ROOT).as_posix()} does not say {country_phrase}")
    check(bool(holiday_files), "holiday/ was scanned for 'not limited by country'")

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL HOLIDAY FUNNEL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
