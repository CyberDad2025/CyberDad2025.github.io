#!/usr/bin/env python3
"""Lock the festive restyle to presentation.

Compares the six restyled pages with origin/main. Visible text, anchor hrefs,
checkout hrefs, prices, and footer markup must match. The holiday policy pages
may also link festive.css. They are not part of that origin/main text lock.
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
# New holiday policy pages use the same stylesheet. They are not in PAGES,
# so this file still locks storefront text, prices, and checkout links to main.
POLICY_PAGES = (
    "refund-policy/index.html",
    "faq/index.html",
    "support/index.html",
)
TERMS_SENTENCE = (
    'The <a href="/refund-policy/">refund policy</a> still covers only the CyberDad Shield Kit. '
    '<a href="/terms-of-sale/">Terms of sale</a> cover the Shield Kit and holiday digital printables.'
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


def stripe_hrefs(html: str) -> list[str]:
    return re.findall(r"https://buy\.stripe\.com/[A-Za-z0-9]+", html)


def price_strings(html: str) -> list[str]:
    return re.findall(r"\$\d+\.\d{2}", html)


def footer_html(html: str) -> str:
    match = re.search(r"<footer\b.*?</footer>", html, re.S)
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


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    for rel in PAGES:
        current = (ROOT / rel).read_text(encoding="utf-8")
        previous = main_text(rel)
        label = rel
        if rel == "shop/index.html":
            check('id="table-set"' in current, "shop page includes the Thanksgiving Table Set card")

        check(stripe_hrefs(current) == stripe_hrefs(previous), f"{label}: buy.stripe.com hrefs match main")
        check(price_strings(current) == price_strings(previous), f"{label}: $ price strings match main")
        check(footer_html(current) == footer_html(previous), f"{label}: footer markup matches main")
        check(script_srcs(current) == script_srcs(previous), f"{label}: script sources match main")

        current_doc = parse_visible(current)
        previous_doc = parse_visible(previous)
        current_text = normalized(current_doc.parts)
        previous_text = normalized(previous_doc.parts)
        check(current_text == previous_text, f"{label}: visible text matches origin/main")
        check("worldwide" not in current.lower(), f"{label}: worldwide is absent")
        check(current_doc.hrefs == previous_doc.hrefs, f"{label}: every anchor href matches origin/main")

        current_legal = [part for part in current_doc.parts if LEGAL_TEXT.search(part)]
        previous_legal = [part for part in previous_doc.parts if LEGAL_TEXT.search(part)]
        check(current_legal == previous_legal, f"{label}: refund, terms and US-only text nodes match origin/main")
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
    check(TERMS_SENTENCE in holiday, "holiday FAQ has main's #995 terms sentence")
    check("<span>— Shield Kit and holiday digital printables</span>" in holiday, "holiday terms link note matches #995")
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
    festive_pages = list(PAGES) + ["holiday/table-set/index.html", *POLICY_PAGES]
    check(sorted(linked) == sorted(festive_pages), "festive.css is linked only from the festive storefront and holiday policy pages")
    for rel in POLICY_PAGES:
        policy_html = (ROOT / rel).read_text(encoding="utf-8")
        check('href="/assets/festive/festive.css"' in policy_html, f"{rel} links festive.css")
        check('class="festive festive-thanksgiving"' in policy_html, f"{rel} uses the Table Set festive theme")
        check("hday-header" in policy_html and "hday-footer" in policy_html and 'class="hday-main"' in policy_html, f"{rel} uses the holiday header, main, and footer")
        check("buy.stripe.com" not in policy_html, f"{rel} has no buy.stripe.com link")

    archive = ROOT / "_archive" / "shield-kit" / "index.html"
    archived_main = subprocess.check_output(["git", "show", f"{BASE}:shield-kit/index.html"], cwd=ROOT)
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

    shop = (ROOT / "shop" / "index.html").read_text(encoding="utf-8")
    shop_imgs = re.findall(r"<img\b[^>]*>", shop)
    check(shop_imgs and "loading=\"lazy\"" not in shop_imgs[0], "first shop cover is eager")
    check(all("loading=\"lazy\"" in tag for tag in shop_imgs[1:]), "later shop covers are lazy")
    for tag in shop_imgs:
        if "table-set" in tag:
            check('width="1200"' in tag and 'height="1600"' in tag, "table set shop cover uses its image size")
        else:
            check('width="720"' in tag and 'height="1022"' in tag, "shop covers set 720 by 1022")
    for rel in PAGES:
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
