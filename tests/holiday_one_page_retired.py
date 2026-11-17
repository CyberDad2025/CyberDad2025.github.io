"""Assertions retired by the one-page holiday shop (feat/holiday-one-page-1117).

/holiday/ is now one page: the Holiday Host Kit hero, Gather & Play as a
secondary card, then five single-product cards. /shop/ and the old product
pages are noindex redirect stubs to /holiday/#card that keep the query string.

Each entry is (suite, exact-message regex, reason). A check whose message
matches is printed as "skip" and not counted. Only checks that pin content or
pages that no longer exist are listed. Guards for refund pages, download ZIPs,
sample PDFs, images that still exist, Stripe links and prices stay in the
suites, or were rewritten to target /holiday/ (see TEST-COMPARISON.md), and the
same facts are asserted again in tests/check_holiday_one_page.py.
"""
from __future__ import annotations

import re

STUB = "page is now a redirect stub to /holiday/#card"
OLD_GP = "old Gather & Play /holiday/ layout replaced by the one-page shop"
SIGNUP = "inactive MailerLite signup embed removed by decision"
MOVED = "moved: asserted on /holiday/ in tests/check_holiday_one_page.py"

RETIRED: dict[str, list[tuple[str, str]]] = {
    "check_holiday_storefront": [
        ('hero image is the Gather and Play cover', OLD_GP),
        ('lists (Table Talk Trails|Harvest Category Sprint|Thanksgiving Mix-Up|Pass-the-Plate Sketch|Gathering Forecast|Thankful Alphabet Relay|Parcel Clues|Snowfall Story Switch|Ribbon Route|Seasonal Priority Shuffle|Holiday Table Logic)', OLD_GP),  # the 12-game list on the old Gather & Play page
        ('storefront shows the exact refund wording', OLD_GP),
        ('bundle callout is below the Gather \\& Play buy button', OLD_GP),
        ('bundle callout sits after the facts list and before the product listing', OLD_GP),
        ('/holiday/ nav links the Travel Adventure page', OLD_GP),
        ('/holiday/ Travel Adventure text line sits before the signup block', OLD_GP),
        ('/holiday/ uses the exact Travel Adventure price phrase', OLD_GP),
        ('/holiday/ has plain text links to the Travel Adventure page', OLD_GP),
        ('holiday nav links to Christmas Trivia', OLD_GP),
        ('holiday title', OLD_GP),
        ('holiday description', OLD_GP),
        ('holiday og:title', OLD_GP),
        ('holiday og:description matches description', OLD_GP),
        ('holiday og:image is the landscape share card', OLD_GP),
        ('JSON\\-LD name matches product\\.json', OLD_GP),
        ('JSON\\-LD description matches the meta description', OLD_GP),
        ('JSON\\-LD image is the landscape share card', OLD_GP),
        ('JSON\\-LD sku', OLD_GP),
        ("holiday nav links to Host Planner and Kids' Table", OLD_GP),
        ('Thanksgiving cards sit after the trivia callout and before the listing', OLD_GP),
        ('Gather \\& Play payment URL still appears twice on /holiday/', MOVED),
        ('/holiday/ has one bundle href', MOVED),
        ('/holiday/ buy\\.stripe\\.com href counts are unchanged', MOVED),
        ('storefront payment URL still appears twice, unchanged', MOVED),
        ('JSON\\-LD price matches product\\.json 7\\.99', MOVED),
        ("/holiday/ card links the Kids' Table bundle", MOVED),
        ('trivia buy href is exact', MOVED),
        ('trivia checkout attribute matches the buy href', MOVED),
        ('trivia page carries the buy URL on the attribute and the href', MOVED),
        ('trivia page has one bundle href', MOVED),
        ('trivia page links to the refund route', MOVED),
        ('(host-planner|kids-table) buy href is its placeholder or a live Stripe link', MOVED),
        ('(host-planner|kids-table) checkout attribute matches the buy href', MOVED),
        ('host-planner button names \\$4\\.99 USD', MOVED),
        ('kids-table button names \\$5\\.99 USD', MOVED),
        ('(host-planner|kids-table) states US eligibility', MOVED),
        ("(host-planner|kids-table) says Stripe's confirmation screen shows the download link", MOVED),
        ('(host-planner|kids-table) keeps the checkout-email re-send instruction', MOVED),
        ('(host-planner|kids-table) links its refund page', MOVED),
        ('(host-planner|kids-table) includes the site GA4 id', MOVED),
        ('kids bundle buy href is its placeholder or a live Stripe link', MOVED),
        ('kids bundle button names \\$11\\.99', MOVED),
        ('Travel Adventure buy href is the same URL as /holiday/', MOVED),
        ('Travel Adventure page has one Travel Adventure Stripe href', MOVED),
        ('Travel Adventure page adds only that Stripe href \\(buy_click selector excluded\\)', MOVED),
        ('Travel Adventure page states US eligibility', MOVED),
        ('Travel Adventure page includes the site GA4 id', MOVED),
        ('Travel Adventure source has exactly one buy\\.stripe\\.com href', MOVED),
        ('built Travel Adventure page has exactly one buy\\.stripe\\.com href', MOVED),
        ('Travel Adventure page links its refund page from the header, seller note, refund sentence, and footer', MOVED),
        ('sample redirect canonical is the Travel Adventure page', STUB),
        ('sample meta refresh is the plain Travel Adventure URL', STUB),
        ('sample redirect has a visible no\\-JS fallback', STUB),
        ('holiday/trivia/index\\.html is static HTML, copied as\\-is by Jekyll', STUB),
        ('trivia sample redirect points at the Travel Adventure page', STUB),
        ('sample canonical points at the Travel Adventure page', STUB),
        ('sample has a visible no\\-JS fallback link', STUB),
        ('sitemap includes https://getcyberdadkit\\.com/holiday/travel\\-adventure/', STUB),
        ('built holiday/sample/index\\.html is the Travel Adventure redirect', STUB),
        ('(host-planner|kids-table) merchant notice is before the pay link', STUB),
        ('(host-planner|kids-table) product page refund wording is exact', STUB),
        ('(host-planner|kids-table) is static HTML that jekyll-sitemap lists', STUB),
        ("kids bundle callout sits below the pack's buy button", STUB),
        ('kids\\-table carries the bundle refund sentence', STUB),
        ('Travel Adventure canonical is exact', STUB),
        ('Travel Adventure buy button sits in the hero, beside the price', STUB),
        ('Travel Adventure page keeps one \\#checkout anchor for the nav Buy link', STUB),
        ('Travel Adventure hero puts the buy button before the cover on phones', STUB),
        ('only the Travel Adventure page uses hday\\-hero\\-buy\\-first', STUB),
        ('Travel Adventure page shows inside page 0[34]', STUB),
        ('Travel Adventure mid\\-page CTA points at the existing buy button', STUB),
        ('Travel Adventure page is static HTML that jekyll\\-sitemap lists', STUB),
        ('Travel Adventure page uses the table\\-set refund sentence', STUB),
    ],
}


def retired_reason(suite: str, message: str) -> str | None:
    for pattern, reason in RETIRED.get(suite, []):
        if re.fullmatch(pattern, message):
            return reason
    return None
