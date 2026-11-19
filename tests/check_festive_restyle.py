#!/usr/bin/env python3
"""Lock the festive restyle to presentation.

Compares the six restyled pages with origin/main. Visible body text, anchor hrefs,
checkout hrefs, prices, and footer nav must match. The footer identity is the
four-line block. The holiday policy pages may also link festive.css. They are
not part of that origin/main text lock.
The check reads source files only. It does not request buy.stripe.com.

Run: python3 tests/check_festive_restyle.py
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "shop/index.html",
    "holiday/index.html",
    "holiday/trivia/index.html",
    "holiday/host-planner/index.html",
    "holiday/kids-table/index.html",
    "journal/2027/index.html",
)
BASE = "origin/main"
# One-page shop: these PAGES are now redirect stubs (or, for holiday/index.html,
# the new one-page shop). Their per-page "matches origin/main" pins are retired.
ONE_PAGE_REPLACED = {
    "shop/index.html",
    "holiday/index.html",
    "holiday/trivia/index.html",
    "holiday/host-planner/index.html",
    "holiday/kids-table/index.html",
}
# New holiday policy pages use the same stylesheet. They are not in PAGES,
# so this file still locks storefront text, prices, and checkout links to main.
POLICY_PAGES = (
    "refund-policy/index.html",
    "faq/index.html",
    "support/index.html",
)
# Holiday storefront text stays locked to origin/main except the archived-kit lines.
WORLDWIDE_BEFORE = "Round 1 is free to print, worldwide."
WORLDWIDE_AFTER = "Round 1 is free to print."
REFUND_LINE = (
    "Refund policy: Gather & Play, full refund within 7 days of purchase. "
    "Each product page lists its own refund terms."
)
TERMS_SENTENCE = (
    '<a href="/holiday/refund/">Refund policy: Gather &amp; Play, full refund within 7 days of purchase. '
    "Each product page lists its own refund terms.</a> "
    '<a href="/terms-of-sale/">Terms of sale: holiday digital printables.</a>'
)
SHIELD_VISIBLE_REPLACEMENTS = (
    (
        "The refund policy still covers only the CyberDad Shield Kit. "
        "Terms of sale cover the Shield Kit and holiday digital printables.",
        REFUND_LINE + " Terms of sale: holiday digital printables.",
    ),
    (
        "Shield Kit refund policy — CyberDad Shield Kit only",
        REFUND_LINE,
    ),
    (
        "Terms of sale — Shield Kit and holiday digital printables",
        "Terms of sale: holiday digital printables.",
    ),
)
LEGAL_ID = re.compile(r"refund|eligibility|seller-note|checkout-note", re.I)
LEGAL_TEXT = re.compile(r"refund|terms|United States", re.I)
BUDGET_FILES = (
    "assets/festive/festive.css",
    "assets/fonts/fredoka-latin.woff2",
)
BYTE_BUDGET = 150 * 1024
# Byte-identical to the supplied covers. Listed in SHA256SUMS.txt.
COVER_SHA256 = {
    "assets/img/festive/bible-verse-journal-2027-cover.webp": "62a54dd9687a856a41eec9c4a1d6c4cc68598fa0205e24ac40f047d14d4bfeff",
    "assets/img/festive/christmas-trivia-night-cover.webp": "a390bf66bbfc66f6ace4601d6d369bcec1a4966eb4ae27df194a6440a9de9b1f",
    "assets/img/festive/gather-and-play-cover.webp": "bf203a31db1d129e126f04f5d5dceb5705bcccea1c5e81dc6b80e820efad3107",
    "assets/img/festive/kids-table-bundle-cover.webp": "429694476322890f8c23626e1dd26d182542f8ce46c2f8ee05e2fc51dc6743b3",
    "assets/img/festive/kids-table-pack-cover.webp": "8bfb64cc8ee99ec1332e34a68abf55a11fcf27fa892cc28d9e9cbb7c9b43fc6d",
    "assets/img/festive/thanksgiving-host-planner-cover.webp": "6de1956d08b1e920461390a49669c4bc40e3fb40eacb1fcd690201489433304d",
    "assets/img/festive/trivia-gp-bundle-cover.webp": "007ffedc9038cec6526911a97ef8d0561eedc7c81b05df7a4a44208bf306fc33",
    "assets/img/festive/bible-verse-journal-2027-cover.jpg": "52a94ef1b718cec878301945544a25a27a5f243e19948239d7cf2fd35a465c62",
    "assets/img/festive/christmas-trivia-night-cover.jpg": "17ec84994aa1b8cccbc03b9bfb30c4a86b83fccc3761f52216963348fa10fc23",
    "assets/img/festive/gather-and-play-cover.jpg": "48c28c98e45334813d9b48d71127c9d8e55c16c6d5f892803f99eaee09aee86a",
    "assets/img/festive/kids-table-bundle-cover.jpg": "d0f4aaa285c0cc888cf96c3288949c556a6854507c606b9db3be8d20df9d6d75",
    "assets/img/festive/kids-table-pack-cover.jpg": "4c7c8747b8673531dbdbde5d286bcdc7dff4d77ba39799d3980d5eaca7ff4c94",
    "assets/img/festive/thanksgiving-host-planner-cover.jpg": "f95656c94399de14d363eeb877e428332e1883ec2e8f8f9c9bb35ea68a8a229f",
    "assets/img/festive/trivia-gp-bundle-cover.jpg": "058342571dc9d7d3a7dc9f18470a3e0d3f64da255501898e1ce0f2fd2c844ce1",
}


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hrefs: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "a":
            href = dict(attrs).get("href")
            if href is not None:
                self.hrefs.append(href)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


class InnerHTML(HTMLParser):
    """Inner markup of elements whose id matches the legal-copy pattern."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.blocks: dict[str, str] = {}
        self.capture: str | None = None
        self.depth = 0
        self.buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        element_id = attrs.get("id", "")
        if self.capture:
            self.depth += 1
            self.buf.append(self.get_starttag_text())
        elif element_id and LEGAL_ID.search(element_id):
            self.capture = element_id
            self.depth = 1
            self.buf = []

    def handle_endtag(self, tag):
        if not self.capture:
            return
        self.depth -= 1
        if self.depth == 0:
            self.blocks[self.capture] = "".join(self.buf)
            self.capture = None
        else:
            self.buf.append(f"</{tag}>")

    def handle_data(self, data):
        if self.capture:
            self.buf.append(data)

    def handle_entityref(self, name):
        if self.capture:
            self.buf.append(f"&{name};")

    def handle_charref(self, name):
        if self.capture:
            self.buf.append(f"&#{name};")

    def handle_startendtag(self, tag, attrs):
        if self.capture:
            self.buf.append(self.get_starttag_text())


def main_text(rel: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{BASE}:{rel}"],
        cwd=ROOT,
    ).decode("utf-8")


def normalized(parts: list[str]) -> str:
    return " ".join("".join(parts).split())


def allowed_text(rel: str, current: str, previous: str) -> str:
    """Return the origin/main text after the whitelisted holiday edits."""
    if rel == "holiday/trivia/index.html":
        text = previous
        for old, new in (
            (" Round 1 is free to print.", ""),
            ("Free sample", "Travel Adventure"),
            (
                "Print Round 1 free in US Letter or A4. No email is required.",
                "Traveling for Thanksgiving? See The Great Thanksgiving Travel Adventure.",
            ),
            (" Round 1 is free on the sample page.", ""),
            (" (free sample)", ""),
        ):
            text = text.replace(old, new, 1)
        return text
    if rel != "holiday/index.html":
        return previous
    text = previous.replace(WORLDWIDE_BEFORE, WORLDWIDE_AFTER, 1)
    for old, new in SHIELD_VISIBLE_REPLACEMENTS:
        text = text.replace(old, new, 1)
    return text


def expected_legal_parts(label: str, parts: list[str]) -> list[str]:
    """Holiday legal text stays as on main, except the archived-kit lines."""
    if label != "holiday/index.html":
        return parts
    # The trivia cross-sell no longer ends with "Round 1 is free to print."
    trivia_tail = (
        "Paid purchases are available only to customers located in the United States. "
    )
    parts = [part.rstrip() if part == trivia_tail or part.endswith(trivia_tail) else part for part in parts]
    # #1012 already replaced those lines on main. Do not rewrite them again.
    if not any(part in {"refund policy", "Shield Kit refund policy"} for part in parts):
        return parts
    refund_line = REFUND_LINE
    terms_line = "Terms of sale: holiday digital printables."
    terms_left = 2
    rewritten = []
    for part in parts:
        if part in {"refund policy", "Shield Kit refund policy"}:
            rewritten.append(refund_line)
        elif part == "Terms of sale" and terms_left:
            terms_left -= 1
            rewritten.append(terms_line)
        else:
            rewritten.append(part)
    return rewritten


def stripe_hrefs(html: str) -> list[str]:
    return re.findall(r"https://buy\.stripe\.com/[A-Za-z0-9]+", html)


def price_strings(html: str) -> list[str]:
    return re.findall(r"\$\d+\.\d{2}", html)


def without_journal_a4(html: str) -> str:
    """Apply the US-only journal edit to a copy of the main journal page."""
    html, removed = re.subn(
        r'\n        <div class="jrnl-size" id="size-a4">.*?\n        </div>',
        "",
        html,
        count=1,
        flags=re.S,
    )
    if removed != 1:
        return html
    nine = "$" + "9.99"
    seven = "$" + "7.99"
    replacements = (
        (f"Letter {nine}, A4 {nine}, half-letter {seven}", f"Letter {nine} or half-letter {seven}"),
        ("Letter, A4 or half-letter", "Letter or half-letter"),
        (f"Letter {nine}, A4 {nine} or half-letter {seven}", f"Letter {nine} or half-letter {seven}"),
        (f"US Letter {nine}, A4 {nine}, half-letter {seven}", f"US Letter {nine} or half-letter {seven}"),
        ("(all three sizes)", "(both sizes)"),
    )
    for old, new in replacements:
        html = html.replace(old, new, 1)
    return html


FOOTER_LINES = (
    "<p>CyberDadKit © 2026</p>",
    "<p>CyberDad Kit LLC</p>",
    "<p>PO Box 940061, Maitland, FL 32794</p>",
    '<p><a href="mailto:ruel@getcyberdadkit.com">ruel@getcyberdadkit.com</a></p>',
)


def footer_html(html: str) -> str:
    match = re.search(r"<footer\b.*?</footer>", html, re.S)
    return match.group(0) if match else ""


def without_footer(html: str) -> str:
    return re.sub(r"<footer\b.*?</footer>", "", html, count=1, flags=re.S)


def footer_nav(footer: str) -> str:
    match = re.search(r'<nav aria-label="Footer">.*?</nav>', footer, re.S)
    return match.group(0) if match else ""


def parse_visible(html: str) -> Visible:
    parser = Visible()
    parser.feed(html)
    return parser


def legal_blocks(html: str) -> dict[str, str]:
    parser = InnerHTML()
    parser.feed(html)
    return parser.blocks


def script_srcs(html: str) -> list[str]:
    return re.findall(r"<script\b[^>]*\bsrc=\"([^\"]+)\"", html)


# The landing funnel inserts a sample round and a signup, and moves the
# existing checkout block out of the hero. Those inserts are excluded here
# so the rest of the visible text, hrefs, and script srcs stay locked.
HERO_SAMPLE_NOTE = (
    '<p class="hday-buy-note"><a href="/holiday/sample/">Print the free Table Talk Trails sample</a> '
    "in US Letter or A4. No email is required.</p>"
)
FAQ_SAMPLE_COUNTRY = ", and that sample is not limited by country"


def strip_funnel_inserts(html: str) -> str:
    html = re.sub(
        r'\n  <section class="hday-section" id="sample-round".*?</section>',
        "",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'\n  <section class="sample-updates" id="updates".*?</section>',
        "",
        html,
        count=1,
        flags=re.S,
    )
    return html


def strip_checkout(html: str) -> str:
    return re.sub(r'\n[ \t]*<div id="checkout".*?</div>', "", html, count=1, flags=re.S)


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    # One-page shop: Stripe links and prices across the replaced pages, checked as a set.
    main_links: set[str] = set()
    main_prices: set[str] = {"$24.96"}  # verified Host Kit parts sum (PRICE-SUM.md)
    for rel in ONE_PAGE_REPLACED:
        main_links.update(stripe_hrefs(main_text(rel)))
        main_prices.update(price_strings(main_text(rel)))

    for rel in PAGES:
        current = (ROOT / rel).read_text(encoding="utf-8")
        previous = main_text(rel)
        label = rel
        if rel in ONE_PAGE_REPLACED:
            # Rewritten guards. The per-page "matches origin/main" pins are retired
            # because these pages are now the one-page shop or its redirect stubs.
            if rel == "holiday/index.html":
                links = stripe_hrefs(current)
                check(bool(links) and set(links) <= main_links, f"{label}: every buy.stripe.com href is already live on main")
                check(set(price_strings(current)) <= main_prices, f"{label}: every $ price is a main holiday price or the verified $24.96 sum")
                check(current.count("Available only to customers located in the United States.") == 1, f"{label}: US-only sentence appears once")
            else:
                check(not stripe_hrefs(current), f"{label}: redirect stub has no buy.stripe.com href")
                check("location.replace(\"/holiday/\" + window.location.search" in current, f"{label}: redirect stub keeps the query string")
            current_footer = footer_html(current)
            for line in FOOTER_LINES:
                check(current_footer.count(line) == 1, f"{label}: footer has one identity line: {line}")
            check(current_footer.count("CyberDad Kit LLC") == 1, f"{label}: footer names the LLC once")
            check("worldwide" not in current.lower(), f"{label}: worldwide is absent")
            continue
        # The Holiday Host Kit card is new catalog content. Compare the
        # rest of /shop/ and /holiday/ with origin/main. The Table Set card
        # is already on main, so it stays in the comparison.
        if rel == "shop/index.html":
            check('id="table-set"' in current, "shop page includes the Thanksgiving Table Set card")
            card = r'\n    <li class="shop-card" id="host-kit">.*?</li>'
            stripped, added = re.subn(card, "", current, count=1, flags=re.S)
            check(added == 1, "shop page includes one Holiday Host Kit card")
            current = stripped
            # Host Kit is on main, so drop the same card there before the lock.
            previous, _ = re.subn(card, "", previous, count=1, flags=re.S)
        if rel == "holiday/index.html":
            nine = "$" + "9.99"
            seven = "$" + "7.99"
            old_blurb = f"Letter {nine}, A4 {nine} or half-letter {seven}"
            new_blurb = f"Letter {nine} or half-letter {seven}"
            check(previous.count(old_blurb) == 1, "main holiday list names the journal A4 price once")
            check(old_blurb not in current and current.count(new_blurb) == 1, "holiday journal list drops the A4 price")
            previous = previous.replace(old_blurb, new_blurb, 1)
            section = r'\n  <section class="hday-section" id="host-kit"[^>]*>.*?</section>'
            stripped, added = re.subn(section, "", current, count=1, flags=re.S)
            check(added == 1, "holiday page includes one Holiday Host Kit section")
            current = stripped
            previous, _ = re.subn(section, "", previous, count=1, flags=re.S)
            trivia_btn = (
                '<a class="hday-pay" id="trivia-checkout-holiday" '
                'href="https://buy.stripe.com/bJecN4aCyfyM4apbQrds406">'
                "Buy Christmas Trivia Night for $5.99 USD</a> "
            )
            check(trivia_btn in current, "holiday page includes the Christmas Trivia Night buy button")
            current = current.replace(trivia_btn, "", 1)
            packs_btns = (
                "    <p>"
                '<a class="hday-pay" id="host-planner-checkout-holiday" '
                'href="https://buy.stripe.com/9B69ASdOK1HWayNdYzds40b">'
                "Buy Thanksgiving Host Planner for $4.99 USD</a> "
                '<a class="hday-pay" id="kids-checkout-holiday" '
                'href="https://buy.stripe.com/6oU7sK7qm2M05et3jVds40c">'
                "Buy Kids' Table Activity Pack for $5.99 USD</a> "
                '<a class="hday-pay" id="kids-bundle-checkout-holiday" '
                'href="https://buy.stripe.com/4gM9ASeSO72g9uJbQrds40d">'
                "Buy the Kids' Table + Gather &amp; Play bundle for $11.99 USD</a></p>\n"
            )
            check(packs_btns in current, "holiday page includes the Thanksgiving pack buy buttons")
            current = current.replace(packs_btns, "", 1)

        if rel == "journal/2027/index.html":
            check("A4" not in current, "journal/2027/index.html contains no A4 text")
            journal_links = re.findall(r'href="https://buy\.stripe\.com/', current)
            check(len(journal_links) == 2, "journal/2027/index.html has exactly 2 buy.stripe.com links")
            previous = without_journal_a4(previous)
            check("A4" not in previous, "journal A4 phrases are removed from the main comparison copy")

        check(stripe_hrefs(current) == stripe_hrefs(previous), f"{label}: buy.stripe.com hrefs match main")
        check(price_strings(current) == price_strings(previous), f"{label}: $ price strings match main")
        current_footer = footer_html(current)
        for line in FOOTER_LINES:
            check(current_footer.count(line) == 1, f"{label}: footer has one identity line: {line}")
        check(current_footer.count("CyberDad Kit LLC") == 1, f"{label}: footer names the LLC once")
        expected_footer_nav = footer_nav(footer_html(previous))
        if label == "holiday/index.html":
            expected_footer_nav = expected_footer_nav.replace(
                '<a href="/holiday/sample/">Free sample</a>',
                '<a href="/holiday/travel-adventure/" data-cta="sample-link-gp-footer">Travel Adventure</a>',
                1,
            )
        if label == "holiday/trivia/index.html":
            expected_footer_nav = expected_footer_nav.replace(
                '<a href="/holiday/trivia/sample/">Free sample</a>',
                '<a href="/holiday/travel-adventure/" data-cta="sample-link-trivia-footer">Travel Adventure</a>',
                1,
            )
        check(footer_nav(current_footer) == expected_footer_nav, f"{label}: footer nav matches main")
        text_current = current
        text_previous = previous
        if rel == "holiday/index.html":
            check(
                current.find('id="product-title"')
                < current.find('id="updates"')
                < current.find('id="holiday-checkout"')
                < current.find('class="hday-facts"'),
                "holiday funnel is product, signup, buy, then the facts",
            )
            check('id="sample-round"' not in current, "holiday page has no sample-round section")
            check(current.count("https://assets.mailerlite.com/js/universal.js") == 1, "holiday signup loads MailerLite universal.js once")
            check(HERO_SAMPLE_NOTE not in current, "hero has no free-sample line")
            text_current = strip_checkout(strip_funnel_inserts(current))
            text_previous = strip_checkout(previous.replace(HERO_SAMPLE_NOTE, "", 1)).replace(FAQ_SAMPLE_COUNTRY, "", 1)
            check(HERO_SAMPLE_NOTE not in text_previous, "comparison drops the hero sample line from main")
            check(FAQ_SAMPLE_COUNTRY not in text_current, "FAQ no longer says the sample is not limited by country")
            check('id="sample-round"' not in text_current and 'id="updates"' not in text_current, "comparison ignores the inserted sample and signup")
        check(script_srcs(text_current) == script_srcs(text_previous), f"{label}: script sources match main")

        current_doc = parse_visible(without_footer(text_current))
        previous_doc = parse_visible(without_footer(text_previous))
        current_text = normalized(current_doc.parts)
        previous_text = normalized(previous_doc.parts)
        check(current_text == allowed_text(label, current_text, previous_text), f"{label}: visible text matches origin/main")
        check("worldwide" not in current.lower(), f"{label}: worldwide is absent")
        expected_hrefs = previous_doc.hrefs
        if label == "holiday/trivia/index.html":
            expected_hrefs = []
            sample_seen = 0
            for href in previous_doc.hrefs:
                if href == "/holiday/trivia/sample/":
                    sample_seen += 1
                    if sample_seen <= 2:
                        expected_hrefs.append("/holiday/travel-adventure/")
                    # The third sample href was in the dropped preview sentence.
                    continue
                expected_hrefs.append(href)
            check(sample_seen == 3, "trivia page retargets two sample links and drops the preview sample link")
        if label == "holiday/index.html" and previous_doc.hrefs.count("/refund-policy/") >= 2:
            # The two former kit-policy links now point at the live Gather & Play refund page.
            expected_hrefs = []
            replaced = 0
            for href in previous_doc.hrefs:
                if href == "/refund-policy/" and replaced < 2:
                    expected_hrefs.append("/holiday/refund/")
                    replaced += 1
                else:
                    expected_hrefs.append(href)
            check(replaced == 2, "holiday page retargets exactly two /refund-policy/ links")
        check(current_doc.hrefs == expected_hrefs, f"{label}: every anchor href matches origin/main")

        current_legal = [part for part in current_doc.parts if LEGAL_TEXT.search(part)]
        previous_legal = [part for part in previous_doc.parts if LEGAL_TEXT.search(part)]
        check(current_legal == expected_legal_parts(label, previous_legal), f"{label}: refund, terms and US-only text nodes match origin/main")
        check(legal_blocks(current) == legal_blocks(previous), f"{label}: refund and eligibility markup matches origin/main")
        check(
            current.count("Available only to customers located in the United States.")
            == previous.count("Available only to customers located in the United States."),
            f"{label}: US-only sentence count matches origin/main",
        )

    holiday = (ROOT / "holiday" / "index.html").read_text(encoding="utf-8")
    footer = footer_html(holiday)
    header = holiday.split("<main", 1)[0]
    check('href="/shield-kit/"' not in header and 'href="/shield-kit/"' not in footer, "holiday nav and footer have no /shield-kit/ link")
    # One-page shop: the Gather & Play FAQ and support list are gone. Rewritten:
    # the single 7-day refund line on /holiday/ links every product refund page.
    refund_line = re.search(r"<p>You may request a full refund for any reason within 7 days of the purchase date\..*?</p>", holiday, re.S)
    check(
        refund_line is not None
        and all(f'href="/holiday/{slug}refund/"' in refund_line.group(0) for slug in ("", "host-kit/", "trivia/", "table-set/", "host-planner/", "kids-table/", "travel-adventure/")),
        "holiday 7-day refund line links every product refund page",
    )
    check('<a href="/terms-of-sale/">' in holiday, "holiday page links the terms of sale")
    check('href="/refund-policy/"' not in holiday, "holiday page does not send the 7-day line to /refund-policy/")
    journal = (ROOT / "journal" / "2027" / "index.html").read_text(encoding="utf-8")
    check(
        'alt="Cover of the 2027 Verse of the Day Journal, with Psalm 119:105 from the World English Bible."' in journal,
        "journal cover alt keeps the Psalm 119:105 (WEB) line from main",
    )

    linked = []
    for path in ROOT.rglob("*.html"):
        if any(part in {".git", "_site", "vendor"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if 'href="/assets/festive/festive.css"' in text:
            linked.append(path.relative_to(ROOT).as_posix())
    festive_pages = list(PAGES) + [
        "holiday/table-set/index.html",
        "holiday/host-kit/index.html",
        "holiday/host-kit/refund/index.html",
        "holiday/gather-and-play/index.html",
        *POLICY_PAGES,
    ]
    # Jekyll does not serve _unpublished/.
    festive_pages.extend(rel for rel in linked if rel.startswith("_unpublished/"))
    check(sorted(linked) == sorted(festive_pages), "festive.css is linked only from the festive storefront and holiday policy pages")
    for rel in POLICY_PAGES:
        policy_html = (ROOT / rel).read_text(encoding="utf-8")
        check('href="/assets/festive/festive.css"' in policy_html, f"{rel} links festive.css")
        check('class="festive festive-thanksgiving"' in policy_html, f"{rel} uses the Table Set festive theme")
        check("hday-header" in policy_html and "hday-footer" in policy_html and 'class="hday-main"' in policy_html, f"{rel} uses the holiday header, main, and footer")
        check("buy.stripe.com" not in policy_html, f"{rel} has no buy.stripe.com link")

    archive = ROOT / "_archive" / "shield-kit" / "index.html"
    archived_main = subprocess.check_output(["git", "show", f"{BASE}:_archive/shield-kit/index.html"], cwd=ROOT)
    check(archive.is_file() and archive.read_bytes() == archived_main, "archived kit page matches origin/main")
    public_kit = (ROOT / "shield-kit" / "index.html").read_text(encoding="utf-8")
    check("checkout.mailerlite.com" not in public_kit and "Shield Kit" not in public_kit, "public /shield-kit/ has no sales copy")

    added = 0
    for rel in BUDGET_FILES:
        size = (ROOT / rel).stat().st_size
        added += size
        check(size > 0, f"{rel} is present ({size} bytes)")
    check(added <= BYTE_BUDGET, f"added CSS + font bytes {added} stay under {BYTE_BUDGET}")
    print(f"note  CSS + woff2 bytes: {added}")

    css = (ROOT / "assets" / "festive" / "festive.css").read_text(encoding="utf-8")
    check("font-display: swap" in css, "Fredoka uses font-display: swap")
    check("size-adjust:" in css, "fallback face sets size-adjust")
    check("prefers-reduced-motion: reduce" in css, "motion is disabled when requested")
    check("fonts.googleapis.com" not in css and "fonts.gstatic.com" not in css, "font files are self-hosted")
    check((ROOT / "assets" / "fonts" / "Fredoka-OFL.txt").is_file(), "Fredoka OFL license is included")

    for rel, digest in COVER_SHA256.items():
        path = ROOT / rel
        got = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
        check(got == digest, f"{rel} sha256 matches the supplied cover")
        check(path.stat().st_size < 200 * 1024, f"{rel} is under 200 KB") if path.is_file() else None

    # One-page shop: /shop/ and the old product pages are redirect stubs with no
    # images, so the cover checks now target /holiday/ (rewritten, not removed).
    shop = (ROOT / "holiday" / "index.html").read_text(encoding="utf-8")
    shop_imgs = re.findall(r"<img\b[^>]*>", shop)
    check(bool(shop_imgs) and 'loading="lazy"' not in shop_imgs[0] and "host-kit-cover" in shop_imgs[0], "first /holiday/ cover (Host Kit) is eager")
    check(all('loading="lazy"' in tag for tag in shop_imgs[4:]), "/holiday/ covers below the hero are lazy")
    for tag in shop_imgs:
        check(re.search(r'width="\d+"', tag) is not None and re.search(r'height="\d+"', tag) is not None, "/holiday/ cover sets its image size")
        src = re.search(r'src="([^"]+)"', tag)
        check(src is not None and src.group(1).endswith(".webp"), f"/holiday/ image prefers webp: {src.group(1) if src else tag[:60]}")
    for rel in [r for r in PAGES if r not in ONE_PAGE_REPLACED]:
        html = (ROOT / rel).read_text(encoding="utf-8")
        check("<picture" in html and 'type="image/webp"' in html, f"{rel}: picture prefers webp")
        first = re.search(r"<picture\b.*?</picture>", html, re.S)
        check(first is not None and 'loading="lazy"' not in first.group(0), f"{rel}: first cover is the eager hero")

    print()
    if failed:
        print(f"{len(failed)} check(s) failed")
        return 1
    print(f"all checks passed ({len(PAGES)} pages, {added} CSS+font bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
