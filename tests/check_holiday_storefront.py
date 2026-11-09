#!/usr/bin/env python3
"""Checks for the Gather & Play storefront.

Confirms the public pages use the real preview files, keep the live checkout
link, and do not publish the paid ZIP, a site download page, or the Ops archive.
"""

from __future__ import annotations

import hashlib
import html as html_lib
import json
import re
import struct
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOLIDAY = ROOT / "holiday"
STORE = HOLIDAY / "index.html"
MANIFEST = HOLIDAY / "product.json"

PREVIEW_HASHES = {
    "holiday/assets/previews/CyberDadKit-preview-page-01.png":
        "89fcf00322203cfe543ce7f32cc16adc1aab9d620acdb780eec72d12b9b50e09",
    "holiday/assets/previews/CyberDadKit-preview-page-09.png":
        "86a48f58cc563fa4076749c0770e09af6a31318ad096d92d971c41ab2c747a1c",
}
PAYMENT_URL = "https://buy.stripe.com/9B67sK4ea4U8dKZ07Jds405"
TRIVIA_PAYMENT_URL = "https://buy.stripe.com/bJecN4aCyfyM4apbQrds406"
BUNDLE_PAYMENT_URL = "https://buy.stripe.com/14A5kC7qmdqEfT78Efds407"
US_ELIGIBILITY = "Available only to customers located in the United States."
PIN_SHA = "a45cbb992293aef692d92a92222946e76f6c2b30c593c019048167bc2a21866e"
PIN_REL = "holiday/assets/pins/01-thanksgiving-host.png"
PIN_FILES = {
    "holiday/pins/02-christmas-gathering.png": "ace46fa9656ba34c532686983cf09ebac2c8f7f6ec8b4aa6edc13c54cf2914a7",
    "holiday/pins/03-office-holiday.png": "bea71bf1f06e4f7e5cb247c9b6979f1b0738ca61975a60a61efe720c95816181",
    "holiday/pins/04-low-ink-last-minute.png": "610f223e21f58593ef23e9eda98908210648f6d785e64564ee74605790a84285",
    "holiday/pins/pin-free-sample.png": "cb9f9d4385ce3b5ac29d8fb935cc216014212eb74083bf96c273a96c81041dc1",
    "holiday/pins/pin-gathering-games.png": "cb4a6a67b31d5e6bd4a59f2c06a867aac3e06c0947ed55e2b51ee421f8e93597",
    "holiday/pins/pin-low-ink.png": "6cbae8be1f50c88bb1e8c34f8aacb2db36981ad9d88fdd12ac883dd15bf681a8",
}
HOLIDAY_TITLE = "Gather & Play: Printable Thanksgiving and Christmas Games"
HOLIDAY_DESC = (
    "Printable Thanksgiving and Christmas family gathering games. "
    "Twelve games in four PDFs for $7.99 USD, one-time, for customers located in the United States."
)
SAMPLE_TITLE = "Free Thanksgiving Table Talk Trails Printable Sample"
SAMPLE_DESC = (
    "Print the free Table Talk Trails sample in US Letter or A4. No email. "
    "The 12-game bundle is $7.99 USD, one-time, for customers located in the United States."
)
PRODUCT_IMAGE = "https://getcyberdadkit.com/holiday/pins/pin-gathering-games.png"
SAMPLE_IMAGE = "https://getcyberdadkit.com/holiday/pins/pin-free-sample.png"
SERVED_ADSENSE_FILES = {
    "_layouts/default.html",
    "_layouts/post.html",
}
UNUSED_ADSENSE_FILES = {
    "_layouts/home.html",
}
ADSENSE_NEEDLES = ("adsbygoogle", "pagead2", "googlesyndication", "ca-pub-")
SAMPLE_PDFS = {
    "holiday/sample/Free-Sample-Table-Talk-Trails-US-Letter.pdf": "20e1cb2b96b03f147efa5a267a796dc2dbb1b5a1b8b64196747fe31c5d2f6c64",
    "holiday/sample/Free-Sample-Table-Talk-Trails-A4.pdf": "3f9bb5ac9f5c9d83b64df2bc06c82f5bcf80540daf538c2e593feabac7954c3a",
}
# Digests are the Trivia v1.0.1 handoff. Pin 03 is the replacement file.
TRIVIA_FILES = {
    "holiday/trivia/index.html":
        "5ac1d305001eb088802a1bea231285ed261b88b78215880bce5e6ebf314cf665",
    "holiday/trivia/sample/index.html":
        "60ff984fe51e7dfb611ab687f99c9a8f2f62d22f21df8dfcf77c5bb282514c0c",
    "holiday/trivia/refund/index.html":
        "63823a3ebdb67589736fa0756178064ae3fd729504cf74f5789bac4af4a93159",
    "holiday/trivia/sample/CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-A4.pdf":
        "3e5ac375bab5eb3c56748a12eee2d9a8449137329a6bfb52608a03b30288e0d3",
    "holiday/trivia/sample/CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-US-Letter.pdf":
        "bfb39dcb827ebd53bb5bf0d57f8818c40f9bd093da5b8b27a7f2434b0ccc1551",
    "holiday/assets/trivia/pins/01-christmas-trivia-family.png":
        "9a33e61a6d610d955cbd02c93a245c951ea24bde2416b379210fa0626a6d085c",
    "holiday/assets/trivia/pins/02-christmas-trivia-80-questions.png":
        "071bb3a4b58c7716853dfda632d23dff569bc679e79893ba6f553806d74bb524",
    "holiday/assets/trivia/pins/03-trivia-gather-play-bundle.png":
        "e73b055eb108170e363d2c5a62fa9ee89d2029056072a400e9a2119664818e4b",
    "holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-01.png":
        "6426e93479ed34804b67001f20f9bda35541ab56e1a11e7795233ee3878c67ab",
    "holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-05.png":
        "7b2ba870b4ce50401caa2ed513c115121a9fd3c8b6177929e133ffd2f94c37d2",
    "holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-12.png":
        "8acd6928392bad7155a24956eac8e7b4f84e428bd84d4b34174b37e903ac70f4",
}
TRIVIA_SAMPLE_PDFS = {
    rel: digest for rel, digest in TRIVIA_FILES.items() if rel.endswith(".pdf")
}
TRIVIA_PAGES = [
    HOLIDAY / "trivia" / "index.html",
    HOLIDAY / "trivia" / "sample" / "index.html",
    HOLIDAY / "trivia" / "refund" / "index.html",
]
POLICY_URLS = {
    "https://cyberdad2025.github.io/holiday/refund/",
    "https://getcyberdadkit.com/holiday/refund/",
}

GAMES = [
    "Table Talk Trails",
    "Harvest Category Sprint",
    "Thanksgiving Mix-Up",
    "Pass-the-Plate Sketch",
    "Gathering Forecast",
    "Thankful Alphabet Relay",
    "Winter Word Hunt",
    "Parcel Clues",
    "Snowfall Story Switch",
    "Ribbon Route",
    "Seasonal Priority Shuffle",
    "Holiday Table Logic",
]

ROUTES = {
    "/": ROOT / "index.html",
    "/contact/": ROOT / "contact.md",
    "/refund-policy/": ROOT / "refund-policy.md",
    "/terms-of-sale/": ROOT / "terms-of-sale.md",
    "/about/": ROOT / "about.md",
    "/cyberdadkit-privacy-policy.html": ROOT / "cyberdadkit-privacy-policy.html",
    "/cookie-policy.html": ROOT / "cookie-policy.html",
    "/sites/": ROOT / "sites" / "index.html",
    "/sites/refund/": ROOT / "sites" / "refund" / "index.html",
    "/shield-kit/": ROOT / "shield-kit" / "index.html",
    "/holiday/": STORE,
    "/holiday/refund/": HOLIDAY / "refund" / "index.html",
    "/holiday/sample/": HOLIDAY / "sample" / "index.html",
    "/holiday/sample/Free-Sample-Table-Talk-Trails-US-Letter.pdf": HOLIDAY / "sample" / "Free-Sample-Table-Talk-Trails-US-Letter.pdf",
    "/holiday/sample/Free-Sample-Table-Talk-Trails-A4.pdf": HOLIDAY / "sample" / "Free-Sample-Table-Talk-Trails-A4.pdf",
    "/holiday/product.json": MANIFEST,
    "/holiday/assets/holiday.css": HOLIDAY / "assets" / "holiday.css",
    "/holiday/trivia/": HOLIDAY / "trivia" / "index.html",
    "/holiday/trivia/sample/": HOLIDAY / "trivia" / "sample" / "index.html",
    "/holiday/trivia/refund/": HOLIDAY / "trivia" / "refund" / "index.html",
    "/holiday/trivia/sample/CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-US-Letter.pdf": HOLIDAY / "trivia" / "sample" / "CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-US-Letter.pdf",
    "/holiday/trivia/sample/CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-A4.pdf": HOLIDAY / "trivia" / "sample" / "CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-A4.pdf",
    "/holiday/assets/trivia/pins/01-christmas-trivia-family.png": HOLIDAY / "assets" / "trivia" / "pins" / "01-christmas-trivia-family.png",
    "/holiday/assets/trivia/pins/02-christmas-trivia-80-questions.png": HOLIDAY / "assets" / "trivia" / "pins" / "02-christmas-trivia-80-questions.png",
    "/holiday/assets/trivia/pins/03-trivia-gather-play-bundle.png": HOLIDAY / "assets" / "trivia" / "pins" / "03-trivia-gather-play-bundle.png",
    "/holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-01.png": HOLIDAY / "assets" / "trivia" / "previews" / "CyberDadKit-Christmas-Trivia-preview-page-01.png",
    "/holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-05.png": HOLIDAY / "assets" / "trivia" / "previews" / "CyberDadKit-Christmas-Trivia-preview-page-05.png",
    "/holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-12.png": HOLIDAY / "assets" / "trivia" / "previews" / "CyberDadKit-Christmas-Trivia-preview-page-12.png",
    "/holiday/host-planner/": HOLIDAY / "host-planner" / "index.html",
    "/holiday/host-planner/refund/": HOLIDAY / "host-planner" / "refund" / "index.html",
    "/holiday/kids-table/": HOLIDAY / "kids-table" / "index.html",
    "/holiday/kids-table/refund/": HOLIDAY / "kids-table" / "refund" / "index.html",
    "/holiday/assets/host-planner/previews/CyberDadKit-Host-Planner-preview-page-01.png": HOLIDAY / "assets" / "host-planner" / "previews" / "CyberDadKit-Host-Planner-preview-page-01.png",
    "/holiday/assets/host-planner/previews/CyberDadKit-Host-Planner-preview-page-03.png": HOLIDAY / "assets" / "host-planner" / "previews" / "CyberDadKit-Host-Planner-preview-page-03.png",
    "/holiday/assets/kids-table/previews/CyberDadKit-Kids-Table-preview-page-01.png": HOLIDAY / "assets" / "kids-table" / "previews" / "CyberDadKit-Kids-Table-preview-page-01.png",
    "/holiday/assets/kids-table/previews/CyberDadKit-Kids-Table-preview-page-06.png": HOLIDAY / "assets" / "kids-table" / "previews" / "CyberDadKit-Kids-Table-preview-page-06.png",
}

# Thanksgiving Host Dinner Planner and Kids' Table Activity Pack.
# Preview digests match previews/ in each product's final release folder.
# Buy buttons hold these placeholders until the Chief of Staff supplies the live
# Stripe links. Run with --require-live-links before merging: it fails while any
# placeholder remains.
STRIPE_PLACEHOLDERS = ("STRIPE_LINK_HOST", "STRIPE_LINK_KIDS", "STRIPE_LINK_KIDS_BUNDLE")
LIVE_LINK = re.compile(r"^https://buy\.stripe\.com/[A-Za-z0-9]+$")
THANKSGIVING_FILES = {
    "holiday/assets/host-planner/previews/CyberDadKit-Host-Planner-preview-page-01.png":
        "e1d47ae876940a44da567468919841403be9e856e5722239b4b41771c4b5c5b3",
    "holiday/assets/host-planner/previews/CyberDadKit-Host-Planner-preview-page-03.png":
        "3a304463ef3e43c65d54c5d513dc3f8d628ed8675ba441e5843247c6c49951e9",
    "holiday/assets/kids-table/previews/CyberDadKit-Kids-Table-preview-page-01.png":
        "55e22a71f712b07fb7a94d9be7d3959716d052aeca2d63305f96b7802caa218d",
    "holiday/assets/kids-table/previews/CyberDadKit-Kids-Table-preview-page-06.png":
        "6b6b50c8c3cd1d3f4616ab4e507089fdac89c587f7d6854e9cea28715298b417",
}
HOST_REFUND = (
    "Thanksgiving Host Dinner Planner is a digital product. You may request a full refund for any reason "
    "within 7 days of your purchase date. Email ruel@getcyberdadkit.com with the email address used for "
    "purchase and your order reference. Never send card details. Refunds are returned to the original "
    "payment method. No physical return is required. This policy applies only to Thanksgiving Host Dinner "
    "Planner and does not limit your statutory rights."
)
KIDS_REFUND = (
    "Kids' Table Activity Pack is a digital product. You may request a full refund for any reason "
    "within 7 days of your purchase date. Email ruel@getcyberdadkit.com with the email address used for "
    "purchase and your order reference. Never send card details. Refunds are returned to the original "
    "payment method. No physical return is required. This policy applies only to Kids' Table Activity "
    "Pack and does not limit your statutory rights."
)
KIDS_BUNDLE_REFUND = (
    "If you bought the $11.99 bundle of Kids' Table Activity Pack and Gather & Play, "
    "this 7-day policy covers the whole bundle purchase."
)
THANKSGIVING_PRODUCTS = {
    # page dir: (price, buy id, placeholder, refund wording id, refund wording)
    "host-planner": ("$4.99", "host-checkout", "STRIPE_LINK_HOST", "host-refund-wording", HOST_REFUND),
    "kids-table": ("$5.99", "kids-checkout", "STRIPE_LINK_KIDS", "kids-refund-wording", KIDS_REFUND),
}


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.anchors = []
        self.images = []
        self.buttons = []
        self.metas = []
        self.in_button = None
        self.stack = []
        self.download_attrs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append(tag)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            self.anchors.append(a)
        elif tag == "img":
            self.images.append(a)
        elif tag == "button":
            self.in_button = a
            self.buttons.append(a)
        elif tag == "meta":
            self.metas.append(a)
        if a.get("download") is not None:
            self.download_attrs.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        if tag == "button":
            self.in_button = None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


EXACT_REFUND = (
    "Gather & Play is a digital product. You may request a full refund for any reason "
    "within 7 days of your purchase date. Email ruel@getcyberdadkit.com with the email "
    "address used for purchase and your order reference. Never send card details. "
    "Refunds are returned to the original payment method. No physical return is required. "
    "This policy applies only to Gather & Play and does not limit your statutory rights."
)


class TextGrab(HTMLParser):
    def __init__(self, target_id: str):
        super().__init__(convert_charrefs=True)
        self.target_id = target_id
        self.depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.depth:
            self.depth += 1
        elif a.get("id") == self.target_id:
            self.depth = 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)


def title_text(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.S)
    return html_lib.unescape(match.group(1).strip()) if match else ""


def meta_content(html: str, attr: str, value: str) -> str:
    pattern = rf'<meta\s+{attr}="{re.escape(value)}"\s+content="([^"]*)"'
    match = re.search(pattern, html)
    return html_lib.unescape(match.group(1)) if match else ""


def json_ld_blocks(html: str) -> list:
    blocks = []
    for match in re.finditer(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S):
        blocks.append(json.loads(match.group(1)))
    return blocks


def has_key(obj, key: str) -> bool:
    if isinstance(obj, dict):
        return key in obj or any(has_key(value, key) for value in obj.values())
    if isinstance(obj, list):
        return any(has_key(value, key) for value in obj)
    return False


def repo_adsense_hits():
    # tests/ is excluded from the Jekyll build, so it is not a served file.
    skip_dirs = {".git", "_site", "vendor", ".jekyll-cache", "docs", ".bundle", "tests"}
    skip_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip"}
    hits = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or skip_dirs.intersection(path.parts) or path.suffix.lower() in skip_suffixes:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(lines, 1):
            lowered = line.lower()
            if any(needle in lowered for needle in ADSENSE_NEEDLES):
                hits.append((rel, lineno, line.strip()))
    return hits


def active_config_value(text: str, key: str):
    prefix = key + ":"
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(prefix):
            value = stripped.split(":", 1)[1].strip()
            if not value or value.startswith("#"):
                return ""
            return value.strip("'\"")
    return None


def element_text(html: str, element_id: str) -> str:
    grab = TextGrab(element_id)
    grab.feed(html)
    return " ".join("".join(grab.parts).split())


def body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.lower().find("<!doctype")
    return text[start:] if start >= 0 else text


def parse(path: Path) -> Doc:
    doc = Doc()
    doc.feed(body(path))
    return doc


def main() -> int:
    failed = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    store_html = body(STORE)
    store = parse(STORE)

    check(manifest["public_name"].startswith("Gather & Play"), "product name")
    check(manifest["counts"]["games"] == 12, "12 games")
    check(manifest["counts"]["pdf_formats"] == 4, "4 formats")
    check(manifest["counts"]["pages_per_pdf"] == 16, "16 pages each")
    check(manifest["counts"]["unique_pages"] == 16, "unique page count stays 16")
    check(manifest["counts"]["same_games_in_every_pdf"] is True, "same games in every PDF")
    check(manifest["checkout"]["enabled"] is True, "checkout enabled in manifest")
    check(manifest["checkout"]["payment_link"] == PAYMENT_URL, "manifest payment link is the live URL")
    check(manifest["checkout"]["livemode"] is True, "manifest records live mode")
    check(manifest["marketing_pin"]["sha256"] == PIN_SHA, "manifest pin hash")
    check(manifest["marketing_pin"]["canonical_url"] == "https://getcyberdadkit.com/holiday/assets/pins/01-thanksgiving-host.png", "canonical pin URL")
    check(manifest["marketing_pin"]["caption_link"] == "https://getcyberdadkit.com/holiday/sample/", "pin caption link is the sample page")
    check(manifest["delivery"]["site_page"] is False, "manifest does not publish a delivery page")
    check(manifest["final_customer_file"]["published_on_site"] is False, "customer file is not published on the site")
    check("public_url" not in manifest["final_customer_file"], "manifest has no public file URL")
    check(manifest["price"]["currency"] == "USD", "public price currency is USD")
    check(manifest["price"]["status"] == "final_public_price", "public price is final")
    check(len(manifest["previews"]) == 2, "cover and winter-game previews")
    check(manifest["price"]["type"] == "one_time" and manifest["price"]["recurring"] is False, "one-time price")
    check(manifest["price"]["amount"] == "7.99", "proposed 7.99")
    check(len(manifest["previews"]) == 2, "two final previews recorded")

    for rel, digest in PREVIEW_HASHES.items():
        path = ROOT / rel
        check(path.is_file() and sha256(path) == digest, f"preview hash {path.name}")

    for page_name, html, doc in (("storefront", store_html, store),):
        check("Review draft" not in html, f"{page_name} does not call the files a review draft")
        check(not re.search(r"proposed", html, re.I), f"{page_name} does not say the price is proposed")
        check("CyberDadKit" in html, f"{page_name} uses CyberDadKit")
        check(not re.search(r"\bCDK\b", html), f"{page_name} has no CDK abbreviation")
        check("64 unique" not in html.lower(), f"{page_name} makes no 64-unique-page claim")
        check("PO Box 940061, Maitland, FL 32794" in html, f"{page_name} uses the PO Box")
        check("ruel@getcyberdadkit.com" in html, f"{page_name} uses the existing contact")
        check(not re.search(r'href="[^"]+\.(?:pdf|zip)"', html, re.I), "storefront does not link the paid ZIP or a PDF")
        check("download=" not in html, f"{page_name} has no download attribute")
        check(html.count('href="' + PAYMENT_URL + '"') == 1, "storefront has one live payment link")
        check(not re.search(r'href=["\']#["\']', html), f"{page_name} has no empty hash href")
        for img in doc.images:
            src = img.get("src", "")
            check(src in {p["src"] for p in manifest["previews"]}, f"{page_name} image is a real preview: {src}")
        for anchor in doc.anchors:
            href = anchor.get("href", "")
            if href.startswith("mailto:"):
                check(href.startswith("mailto:ruel@getcyberdadkit.com"), f"mailto {href}")
                continue
            if href.startswith("#"):
                check(href[1:] in doc.ids, f"{page_name} anchor {href}")
                continue
            if href == PAYMENT_URL:
                check(page_name == "storefront", "live payment link stays on the product page")
                continue
            if href == BUNDLE_PAYMENT_URL:
                check(page_name == "storefront", "bundle payment link is the live bundle URL")
                continue
            path = href.split("#", 1)[0]
            check(path in ROUTES and ROUTES[path].is_file(), f"{page_name} link {href}")

    check(store.images[0]["src"].endswith("page-01.png"), "hero preview is the cover")
    check({img["src"] for img in store.images} == {p["src"] for p in manifest["previews"]}, "storefront shows the final previews")
    for game in GAMES:
        check(game in store_html, f"lists {game}")

    pay = [a for a in store.anchors if a.get("id") == "holiday-checkout"]
    check(len(pay) == 1 and pay[0].get("href") == PAYMENT_URL, "product checkout is the live payment anchor")
    check("disabled" not in pay[0], "product checkout anchor is not disabled")
    check("$7.99" in element_text(store_html, "holiday-checkout") and "USD" in element_text(store_html, "holiday-checkout"), "product button names $7.99 USD")
    check(US_ELIGIBILITY in store_html, "product page states US eligibility")
    check("Stripe checkout displays Ruel Miller." in store_html, "product page names the checkout display name")
    check(store_html.find("Stripe checkout displays Ruel Miller.") < store_html.find('id="holiday-checkout"'), "merchant notice is before the product pay link")
    check("CyberDad Kit LLC" in store_html and 'href="/holiday/refund/"' in store_html, "seller and refund stay on the product page")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    check("User-agent: *" in robots and "Allow: /" in robots, "robots.txt still allows the site")
    check("Sitemap: https://getcyberdadkit.com/sitemap.xml" in robots, "robots.txt sitemap line unchanged")
    check("Disallow:" not in robots, "robots.txt has no delivery disallow")

    banned = re.compile(r"best seller|bestseller|testimonial|limited time|customers love|selling fast", re.I)
    check(not banned.search(store_html), "no demand or testimonial claims")

    sites = (ROOT / "sites" / "index.html").read_text(encoding="utf-8")
    shield = (ROOT / "shield-kit" / "index.html").read_text(encoding="utf-8")
    check("checkout.mailerlite.com/checkout/4435" in shield, "Shield Kit checkout link preserved")
    check("holiday-checkout" not in sites, "Sites page has no holiday checkout")
    check("secure card link (Stripe)" in sites, "Sites Stripe wording preserved")
    order = (ROOT / "sites" / "assets" / "order-config.js").read_text(encoding="utf-8")
    check("203101607592724479" in order, "Sites order form action preserved")

    check(manifest["refund_wording"] == EXACT_REFUND, "manifest refund wording is exact")
    check(manifest["launch_pass"] is False, "no launch pass")
    check(manifest["policy_routes"]["deployed"] is False, "policy route not marked deployed")
    check(manifest["florida_document_number"] == "L25000463998", "Florida document number")
    check(manifest["mailing_address"] == "CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794", "footer address form")
    refund_path = HOLIDAY / "refund" / "index.html"
    refund_html = body(refund_path)
    refund = parse(refund_path)
    for label, html in (("storefront", store_html), ("refund", refund_html)):
        check(element_text(html, "gather-play-refund-wording") == EXACT_REFUND, f"{label} shows the exact refund wording")
        check("CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794" in html, f"{label} footer uses CyberDad Kit LLC")
        check("L25000463998" in html, f"{label} shows the Florida document number")
        check("does not promise automatic processing" in html or label == "refund", f"{label} avoids a processing-time promise")
    check("does not promise automatic processing" in refund_html, "refund page states there is no processing-time promise")
    check("personal, noncommercial gatherings" in refund_html, "printing license is personal and noncommercial")
    check("internal office use" in refund_html, "printing license includes internal office use")
    check("commercial event service" in refund_html, "printing license excludes a commercial event service")
    check('href="/holiday/refund/"' in store_html, "storefront links to the refund route")
    for anchor in refund.anchors:
        href = anchor.get("href", "")
        if href.startswith("mailto:"):
            check(href.startswith("mailto:ruel@getcyberdadkit.com"), f"refund mailto {href}")
        elif href.startswith("#"):
            check(href[1:] in refund.ids, f"refund anchor {href}")
        elif href in POLICY_URLS:
            check(True, f"refund policy URL {href}")
        else:
            path = href.split("#", 1)[0]
            check(path in ROUTES and ROUTES[path].is_file(), f"refund link {href}")
    shield_refund = (ROOT / "refund-policy.md").read_text(encoding="utf-8")
    shield_terms = (ROOT / "terms-of-sale.md").read_text(encoding="utf-8")
    sites_refund = (ROOT / "sites" / "refund" / "index.html").read_text(encoding="utf-8")
    check("Gather & Play" not in shield_refund, "Shield Kit refund policy unchanged in scope")
    check("30-day" in shield_refund or "30 days" in shield_refund, "Shield Kit refund period still present")
    check("Gather & Play" in shield_terms, "terms of sale include Gather & Play holiday downloads")
    check("Christmas Trivia Night" in shield_terms, "terms of sale name Christmas Trivia Night")
    check("/holiday/refund/" in shield_terms, "terms of sale use the holiday refund page")
    check("$47" in shield_terms, "Shield Kit price line remains in terms of sale")
    check("Gather & Play" not in sites_refund, "Sites refund page does not absorb Gather & Play")
    promise = re.compile(r"instant refund|refunds are automatic|within 24 hours|reply within", re.I)
    check(not promise.search(store_html + refund_html), "no automated or timed refund promise")

    sample_path = HOLIDAY / "sample" / "index.html"
    sample_html = body(sample_path)
    sample = parse(sample_path)
    check("noindex" not in sample_html.lower(), "sample page is indexable")
    check("<form" not in sample_html.lower(), "sample has no email form")
    check(element_text(sample_html, "gather-play-refund-wording") == EXACT_REFUND, "sample shows the exact refund wording")
    sample_pay = [a for a in sample.anchors if a.get("id") == "holiday-checkout"]
    check(len(sample_pay) == 1 and sample_pay[0].get("href") == PAYMENT_URL, "sample paid CTA is the live payment anchor")
    check("disabled" not in sample_pay[0], "sample paid CTA is not a disabled button")
    check("$7.99" in element_text(sample_html, "holiday-checkout") and "USD" in element_text(sample_html, "holiday-checkout"), "sample button names $7.99 USD")
    check(US_ELIGIBILITY in sample_html and US_ELIGIBILITY in refund_html, "sample and refund state US eligibility")
    check("not limited by country" in sample_html, "free sample is not country-limited")
    check("Stripe checkout displays Ruel Miller." in sample_html, "sample page names the checkout display name")
    check(sample_html.find("Stripe checkout displays Ruel Miller.") < sample_html.find('id="holiday-checkout"'), "merchant notice is before the sample pay link")
    check(sha256(ROOT / PIN_REL) == PIN_SHA, "pin bytes match the attached file")
    check("Table Talk Trails" in sample_html and "$7.99 USD" in sample_html, "sample names the free game and the bundle price")
    for anchor in sample.anchors:
        href = anchor.get("href", "")
        if href.startswith("mailto:"):
            check(href.startswith("mailto:ruel@getcyberdadkit.com"), f"sample mailto {href}")
        elif href.startswith("#"):
            check(href[1:] in sample.ids, f"sample anchor {href}")
        elif href == PAYMENT_URL:
            check(True, "sample paid link is the live payment URL")
        else:
            path = href.split("#", 1)[0]
            check(path in ROUTES and ROUTES[path].is_file(), f"sample link {href}")
    public_html = store_html + refund_html + sample_html
    internal = re.compile(r"\bdraft\b|launch pass|not deployed|\bproposed\b|\bOps\b", re.I)
    check(not internal.search(public_html), "public pages omit internal status wording")
    check("plink_" not in public_html and "acct_" not in public_html, "public pages omit internal Stripe ids")
    check("Checkout unavailable" not in public_html and "not open yet" not in public_html, "checkout is no longer described as closed")

    pdfs = sorted(p.relative_to(ROOT).as_posix() for p in HOLIDAY.rglob("*.pdf"))
    expected_pdfs = sorted([*SAMPLE_PDFS, *TRIVIA_SAMPLE_PDFS])
    check(pdfs == expected_pdfs, "loose PDFs are the Gather & Play samples and the trivia samples")
    for rel, digest in SAMPLE_PDFS.items():
        check(sha256(ROOT / rel) == digest, f"{rel} matches the final sample hash")
        info = subprocess.run(["pdfinfo", str(ROOT / rel)], capture_output=True, check=True, text=True).stdout
        text = subprocess.run(["pdftotext", str(ROOT / rel), "-"], capture_output=True, check=True, text=True).stdout
        pages = [ln for ln in info.splitlines() if ln.startswith("Pages:")]
        check(pages and pages[0].split()[-1] == "1", f"{rel} is one page")
        check("Table Talk Trails" in text, f"{rel} is Table Talk Trails")
        check("Winter Word Hunt" not in text and "Pass-the-Plate" not in text, f"{rel} is not the whole bundle")
        if "US-Letter" in rel:
            check("612 x 792 pts (letter)" in info, f"{rel} is US Letter")
        if rel.endswith("A4.pdf"):
            check("A4" in info, f"{rel} is A4")

    published_zips = [p for p in HOLIDAY.rglob("*") if p.is_file() and p.suffix.lower() == ".zip"]
    check(published_zips == [], "no ZIP under holiday/")
    check(not (HOLIDAY / "delivery").exists(), "delivery directory removed")
    stripe_confirmation = "After a successful payment, Stripe's confirmation screen shows the download link."
    resend = "with your checkout email address"
    for label, html in (("storefront", store_html), ("sample", sample_html), ("refund", refund_html)):
        check(stripe_confirmation in html, f"{label} says Stripe's confirmation screen shows the download link")
        check(resend in html, f"{label} keeps the checkout-email re-send instruction")
        check("file page" not in html.lower(), f"{label} does not describe a site file page")
    removed = ("/holiday/" + "delivery", "CyberDadKit-Gather-and-Play" + ".zip")
    hits = []
    skip_parts = {".git", "vendor", "_site", ".jekyll-cache"}
    skip_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".pdf", ".zip", ".gif"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip_parts.intersection(path.parts) or path.suffix.lower() in skip_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for needle in removed:
            if needle in text:
                hits.append(f"{path.relative_to(ROOT)} contains {needle}")
    check(hits == [], "no remaining delivery path or customer ZIP filename" + ("" if not hits else ": " + "; ".join(hits)))
    ops_names = list(ROOT.glob("CyberDadKit-Gather-and-Play-Ops-Review*")) + list(ROOT.glob("**/source/build.py"))
    check(ops_names == [], "Ops archive and source builder are not in the repo")

    delivery_path = removed[0]
    check(store_html.count(PAYMENT_URL) == 2, "Gather & Play payment URL still appears twice on /holiday/")
    check(sample_html.count(PAYMENT_URL) == 2, "Gather & Play payment URL is unchanged on the sample page")
    check(">Buy Gather &amp; Play for $7.99 USD</a>" in store_html, "Gather & Play buy button text is unchanged")
    check(store_html.find('id="holiday-checkout"') < store_html.find('id="bundle-checkout-holiday"'), "bundle callout is below the Gather & Play buy button")
    check(store_html.find('class="hday-facts"') < store_html.find('id="trivia-bundle"') < store_html.find('id="listing-title"'), "bundle callout sits after the facts list and before the product listing")
    check(store_html.count('href="' + BUNDLE_PAYMENT_URL + '"') == 1, "/holiday/ has one bundle href")
    check('href="/holiday/trivia/">Christmas Trivia</a>' in store_html, "holiday nav links to Christmas Trivia")
    check(not (HOLIDAY / "BUNDLE-CALLOUT-SNIPPET.html").exists(), "bundle snippet file is not a page")
    config = (ROOT / "_config.yml").read_text(encoding="utf-8")
    check("holiday/trivia" not in config and "assets/trivia" not in config, "Jekyll config does not exclude trivia")
    check("Disallow: /holiday/trivia" not in robots, "robots.txt does not block trivia")

    for rel, digest in TRIVIA_FILES.items():
        path = ROOT / rel
        check(path.is_file() and sha256(path) == digest, f"trivia hash {rel}")
        if "/previews/" in rel:
            width, height = struct.unpack(">II", path.read_bytes()[16:24])
            check((width, height) == (1391, 1800), f"{rel} is 1391x1800")

    trivia_html = body(TRIVIA_PAGES[0])
    trivia = parse(TRIVIA_PAGES[0])
    trivia_pay = [a for a in trivia.anchors if a.get("id") == "trivia-checkout"]
    check(len(trivia_pay) == 1 and trivia_pay[0].get("href") == TRIVIA_PAYMENT_URL, "trivia buy href is exact")
    check(f'data-payment-link="{TRIVIA_PAYMENT_URL}"' in trivia_html, "trivia checkout attribute matches the buy href")
    check(trivia_html.count(TRIVIA_PAYMENT_URL) == 2, "trivia page carries the buy URL on the attribute and the href")
    check(trivia_html.count('href="' + BUNDLE_PAYMENT_URL + '"') == 1, "trivia page has one bundle href")
    check(PAYMENT_URL not in trivia_html, "trivia page does not use the Gather & Play payment URL")
    for page in TRIVIA_PAGES:
        html = page.read_text(encoding="utf-8")
        label = page.relative_to(ROOT).as_posix()
        check(delivery_path not in html, f"{label} has no delivery path")
        check("G-5B1LNCPB56" in html, f"{label} includes the site GA4 id")
        check("{%" not in html and "layout:" not in html, f"{label} is static HTML, copied as-is by Jekyll")
        doc = parse(page)
        urls = re.findall(r'(?:href|src)="([^"]*)"', html)
        urls += re.findall(r'content="(https://[^"]+)"', html)
        for url in urls:
            if url.startswith("mailto:"):
                check(url.startswith("mailto:ruel@getcyberdadkit.com"), f"{label} mailto {url}")
                continue
            if url.startswith("#"):
                check(url[1:] in doc.ids, f"{label} anchor {url}")
                continue
            if url in {TRIVIA_PAYMENT_URL, BUNDLE_PAYMENT_URL, "https://www.googletagmanager.com/gtag/js?id=G-5B1LNCPB56"}:
                continue
            if url.startswith("https://getcyberdadkit.com"):
                path = url[len("https://getcyberdadkit.com"):] or "/"
            elif url.startswith("/"):
                path = url
            else:
                check(False, f"{label} unrecognized reference {url}")
                continue
            path = path.split("#", 1)[0]
            check(path in ROUTES and ROUTES[path].is_file(), f"{label} link {url}")
    check('href="/holiday/trivia/refund/"' in trivia_html, "trivia page links to the refund route")
    check('href="/holiday/trivia/refund/"' in TRIVIA_PAGES[1].read_text(encoding="utf-8"), "sample page links to the refund route")
    check("buy.stripe.com" not in TRIVIA_PAGES[1].read_text(encoding="utf-8"), "sample page does not sell")
    check("buy.stripe.com" not in TRIVIA_PAGES[2].read_text(encoding="utf-8"), "refund page does not sell")

    for rel in TRIVIA_SAMPLE_PDFS:
        info = subprocess.run(["pdfinfo", str(ROOT / rel)], capture_output=True, check=True, text=True).stdout
        text = subprocess.run(["pdftotext", str(ROOT / rel), "-"], capture_output=True, check=True, text=True).stdout
        pages = [ln for ln in info.splitlines() if ln.startswith("Pages:")]
        check(pages and pages[0].split()[-1] == "3", f"{rel} is the 3-page sample")
        check("getcyberdadkit.com/holiday/trivia/" in text, f"{rel} prints the trivia page URL")
        check("Round 1" in text, f"{rel} is Round 1")

    gp_files = []
    bundle_files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip_parts.intersection(path.parts) or path.suffix.lower() in skip_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if PAYMENT_URL in text:
            gp_files.append(rel)
        if BUNDLE_PAYMENT_URL in text:
            bundle_files.append(rel)
    check(sorted(gp_files) == [
        "holiday/index.html",
        "holiday/product.json",
        "holiday/sample/index.html",
        "tests/check_holiday_storefront.py",
    ], "Gather & Play payment URL is unchanged everywhere it appears" + ("" if not gp_files else ": " + ", ".join(sorted(gp_files))))
    check(sorted(bundle_files) == [
        "holiday/index.html",
        "holiday/trivia/index.html",
        "tests/check_holiday_storefront.py",
    ], "bundle payment URL is only on /holiday/ and the trivia page" + ("" if not bundle_files else ": " + ", ".join(sorted(bundle_files))))
    for rel, digest in PIN_FILES.items():
        path = ROOT / rel
        check(path.is_file() and sha256(path) == digest, f"pin hash {rel}")
    config_text = (ROOT / "_config.yml").read_text(encoding="utf-8")
    exclude_block = config_text.split("exclude:", 1)[-1].split("\n# Include", 1)[0]
    check("holiday/pins" not in exclude_block and not re.search(r"(?m)^  - holiday/?\s*$", exclude_block), "pin directory is not excluded from the Jekyll build")
    for rel in ("holiday/index.html", "holiday/sample/index.html", "holiday/refund/index.html"):
        front = (ROOT / rel).read_text(encoding="utf-8").split("---", 2)[1]
        check("sitemap: false" not in front, f"{rel} does not set sitemap: false")
        check("layout: null" in front, f"{rel} keeps layout null")

    check(store_html.count(PAYMENT_URL) == 2, "storefront payment URL still appears twice, unchanged")
    check(sample_html.count(PAYMENT_URL) == 2, "sample payment URL still appears twice, unchanged")
    check(title_text(store_html) == HOLIDAY_TITLE, "holiday title")
    check(meta_content(store_html, "name", "description") == HOLIDAY_DESC, "holiday description")
    check(meta_content(store_html, "property", "og:title") == HOLIDAY_TITLE, "holiday og:title matches title")
    check(meta_content(store_html, "property", "og:description") == HOLIDAY_DESC, "holiday og:description matches description")
    check(meta_content(store_html, "property", "og:image") == PRODUCT_IMAGE, "holiday og:image is the gathering-games pin")
    check('rel="canonical" href="https://getcyberdadkit.com/holiday/"' in store_html, "holiday canonical")
    check(title_text(sample_html) == SAMPLE_TITLE, "sample title")
    check(meta_content(sample_html, "name", "description") == SAMPLE_DESC, "sample description")
    check(meta_content(sample_html, "property", "og:title") == SAMPLE_TITLE, "sample og:title matches title")
    check(meta_content(sample_html, "property", "og:description") == SAMPLE_DESC, "sample og:description matches description")
    check(meta_content(sample_html, "property", "og:image") == SAMPLE_IMAGE, "sample og:image is the free-sample pin")
    check('rel="canonical" href="https://getcyberdadkit.com/holiday/sample/"' in sample_html, "sample canonical")
    for label, text in (("holiday title", HOLIDAY_TITLE), ("holiday description", HOLIDAY_DESC), ("sample title", SAMPLE_TITLE), ("sample description", SAMPLE_DESC)):
        check(50 <= len(text) <= 60 if "title" in label else 140 <= len(text) <= 160, f"{label} length {len(text)}")
        check(not re.search(r"\bCDK\b", text), f"{label} has no CDK")
    blocks = json_ld_blocks(store_html)
    check(len(blocks) == 1, "holiday page has one JSON-LD block")
    product = blocks[0] if blocks else {}
    offer = product.get("offers", {}) if isinstance(product, dict) else {}
    brand = product.get("brand", {}) if isinstance(product, dict) else {}
    brand_name = brand.get("name") if isinstance(brand, dict) else brand
    check(product.get("@context") == "https://schema.org" and product.get("@type") == "Product", "JSON-LD is a schema.org Product")
    check(product.get("name") == manifest["public_name"], "JSON-LD name matches product.json")
    check(product.get("description") == HOLIDAY_DESC, "JSON-LD description matches the meta description")
    check(product.get("image") == PRODUCT_IMAGE, "JSON-LD image is an absolute pin URL")
    check(brand_name == "CyberDadKit", "JSON-LD brand is CyberDadKit")
    check(product.get("sku") == "gather_and_play_v1", "JSON-LD sku")
    check(offer.get("@type") == "Offer", "JSON-LD offer type")
    check(offer.get("price") == manifest["price"]["amount"] == "7.99", "JSON-LD price matches product.json 7.99")
    check(offer.get("priceCurrency") == manifest["price"]["currency"] == "USD", "JSON-LD currency matches product.json USD")
    check(offer.get("availability") == "https://schema.org/InStock", "JSON-LD availability InStock")
    check(offer.get("url") == "https://getcyberdadkit.com/holiday/", "JSON-LD offer url")
    check(offer.get("areaServed") == "US", "JSON-LD areaServed US")
    check(not has_key(product, "aggregateRating") and not has_key(product, "review") and not has_key(product, "reviews"), "JSON-LD has no rating or review")
    check(json_ld_blocks(sample_html) == [] and json_ld_blocks(refund_html) == [], "Product JSON-LD is only on /holiday/")

    for key in ("pinterest_domain_verify", "google_site_verification"):
        check(active_config_value(config_text, key) in (None, ""), f"{key} is unset in _config.yml")
    verification = (ROOT / "_includes" / "site-verification.html").read_text(encoding="utf-8")
    layout = (ROOT / "_layouts" / "default.html").read_text(encoding="utf-8")
    check('{% if page.cd_business_home and site.pinterest_domain_verify %}' in verification, "Pinterest meta renders only when the homepage key is set")
    check('{% if page.cd_business_home and site.google_site_verification %}' in verification, "Google meta renders only when the homepage key is set")
    check('name="p:domain_verify"' in verification and 'name="google-site-verification"' in verification, "verification include contains both meta names")
    check(layout.count("site-verification.html") == 1 and "page.cd_business_home" in layout, "verification include is attached from the homepage head branch")
    home_source = (ROOT / "index.html").read_text(encoding="utf-8")
    check("p:domain_verify" not in home_source and "google-site-verification" not in home_source, "homepage content file has no verification meta")

    privacy_redirect = (ROOT / "privacy" / "index.html").read_text(encoding="utf-8")
    privacy_front = privacy_redirect.split("---", 2)[1]
    check('http-equiv="refresh" content="0; url=/cyberdadkit-privacy-policy.html"' in privacy_redirect, "privacy redirect target")
    check('rel="canonical" href="https://getcyberdadkit.com/cyberdadkit-privacy-policy.html"' in privacy_redirect, "privacy redirect canonical")
    check('name="robots" content="noindex"' in privacy_redirect, "privacy redirect is noindex")
    check('href="/cyberdadkit-privacy-policy.html"' in privacy_redirect, "privacy redirect has a visible link fallback")
    check("sitemap: false" in privacy_front and "layout: null" in privacy_front, "privacy redirect stays out of the sitemap")
    policy_html = (ROOT / "cyberdadkit-privacy-policy.html").read_text(encoding="utf-8")
    adsense_hits = repo_adsense_hits()
    print("note  AdSense grep (adsbygoogle, pagead2, googlesyndication, ca-pub-; docs excluded):")
    for rel, lineno, line in adsense_hits:
        role = "served" if rel in SERVED_ADSENSE_FILES else "not referenced by a page"
        print(f"note  {role}: {rel}:{lineno}: {line}")
    hit_files = {rel for rel, _, _ in adsense_hits}
    check(hit_files == SERVED_ADSENSE_FILES | UNUSED_ADSENSE_FILES, "AdSense grep matches only the known layout files")
    if hit_files & SERVED_ADSENSE_FILES:
        check("AdSense" in policy_html, "privacy policy keeps the AdSense claim while served pages load AdSense")
        check("Some pages on this site show ads served by Google AdSense" in policy_html, "AdSense claim sentence unchanged")
        check("Last updated: November 3, 2026" in policy_html, "privacy policy date unchanged while the claim stays")
    else:
        check("AdSense" not in policy_html, "privacy policy contains no AdSense")

    site_dir = ROOT / "_site"
    if (site_dir / "index.html").is_file() and (site_dir / "sitemap.xml").is_file():
        home_built = (site_dir / "index.html").read_text(encoding="utf-8")
        home_head = home_built.split("</head>", 1)[0]
        check('name="p:domain_verify"' not in home_head, "built homepage has no Pinterest verification meta while unset")
        check('name="google-site-verification"' not in home_head, "built homepage has no Google verification meta while unset")
        check('content=""' not in home_head, "built homepage head has no empty meta content")
        stray = []
        for built in site_dir.rglob("*.html"):
            text = built.read_text(encoding="utf-8", errors="ignore")
            if 'name="p:domain_verify"' in text or 'name="google-site-verification"' in text:
                stray.append(str(built.relative_to(site_dir)))
        check(stray == [], "built HTML has no verification metas while unset" + ("" if not stray else ": " + ", ".join(stray)))
        for rel, digest in PIN_FILES.items():
            built = site_dir / rel
            check(built.is_file() and sha256(built) == digest, f"built pin {rel}")
        sitemap = (site_dir / "sitemap.xml").read_text(encoding="utf-8")
        for loc in (
            "https://getcyberdadkit.com/holiday/",
            "https://getcyberdadkit.com/holiday/sample/",
            "https://getcyberdadkit.com/holiday/refund/",
        ):
            check(f"<loc>{loc}</loc>" in sitemap, f"sitemap includes {loc}")
        removed_delivery = "/holiday/" + "delivery"
        check(removed_delivery not in sitemap, "sitemap has no removed delivery URL")
        check("https://getcyberdadkit.com/privacy/" not in sitemap and "/privacy/index.html" not in sitemap, "sitemap omits /privacy/")
        built_privacy = (site_dir / "privacy" / "index.html").read_text(encoding="utf-8")
        check('content="0; url=/cyberdadkit-privacy-policy.html"' in built_privacy, "built /privacy/ keeps the redirect target")
        check('href="https://getcyberdadkit.com/cyberdadkit-privacy-policy.html"' in built_privacy, "built /privacy/ keeps the canonical")
        for rel in ("holiday/index.html", "holiday/sample/index.html"):
            built_html = (site_dir / rel).read_text(encoding="utf-8")
            check("<title>" in built_html and 'name="description"' in built_html, f"built {rel} has a title and description")
        print("note  built _site sitemap and homepage head checked")
    else:
        print("note  _site not present; skipped built sitemap and homepage head checks")

    # Thanksgiving Host Dinner Planner and Kids' Table Activity Pack
    require_live = "--require-live-links" in sys.argv[1:]
    for rel, digest in THANKSGIVING_FILES.items():
        path = ROOT / rel
        check(path.is_file() and sha256(path) == digest, f"thanksgiving preview hash {rel}")
        if path.is_file():
            width, height = struct.unpack(">II", path.read_bytes()[16:24])
            check((width, height) == (1391, 1800), f"{rel} is 1391x1800")
    copy_banned = re.compile(r"guarantee|shield|\bCDK\b|california|\b(?:my|our) (?:son|daughter|kids?|child|children|wife|family)\b", re.I)
    pending = []
    for slug, (price, buy_id, placeholder, refund_id, refund_text) in THANKSGIVING_PRODUCTS.items():
        product = HOLIDAY / slug / "index.html"
        refund = HOLIDAY / slug / "refund" / "index.html"
        check(product.is_file() and refund.is_file(), f"{slug} product and refund pages exist")
        if not (product.is_file() and refund.is_file()):
            continue
        html = product.read_text(encoding="utf-8")
        refund_html = refund.read_text(encoding="utf-8")
        doc = parse(product)
        pay = [a for a in doc.anchors if a.get("id") == buy_id]
        href = pay[0].get("href", "") if len(pay) == 1 else ""
        check(href == placeholder or bool(LIVE_LINK.match(href)), f"{slug} buy href is its placeholder or a live Stripe link")
        check(html.count(f'data-payment-link="{href}"') == 1 and html.count(f'"{href}"') == 2, f"{slug} checkout attribute matches the buy href")
        enabled = f'data-checkout-enabled="true" data-payment-link="{href}"' in html
        check(enabled == bool(LIVE_LINK.match(href)), f"{slug} checkout is enabled only with a live link")
        if href == placeholder:
            pending.append(placeholder)
            check("TODO: replace " + placeholder in html, f"{slug} placeholder is marked TODO")
        check(price in element_text(html, buy_id) and "USD" in element_text(html, buy_id), f"{slug} button names {price} USD")
        check(html.find("Stripe checkout displays Ruel Miller.") < html.find(f'id="{buy_id}"'), f"{slug} merchant notice is before the pay link")
        check(US_ELIGIBILITY in html and US_ELIGIBILITY in refund_html, f"{slug} states US eligibility")
        check("After a successful payment, Stripe's confirmation screen shows the download link." in html, f"{slug} says Stripe's confirmation screen shows the download link")
        check("with your checkout email address" in html, f"{slug} keeps the checkout-email re-send instruction")
        check(" ".join(element_text(html, refund_id).split()) == refund_text, f"{slug} product page refund wording is exact")
        refund_page_text = refund_text
        if slug == "kids-table":
            refund_page_text = refund_text.replace(
                "This policy applies only to Kids' Table Activity Pack and does not limit your statutory rights.",
                "This policy does not limit your statutory rights.",
            )
        check(" ".join(element_text(refund_html, refund_id).split()) == refund_page_text, f"{slug} refund page wording is exact")
        check(f'href="/holiday/{slug}/refund/"' in html, f"{slug} links its refund page")
        check("buy.stripe.com" not in refund_html and not any(p in refund_html for p in STRIPE_PLACEHOLDERS), f"{slug} refund page does not sell")
        for label, page_html in ((slug, html), (slug + " refund", refund_html)):
            visible = re.sub(r"<!--.*?-->", "", page_html, flags=re.S)
            check(not copy_banned.search(visible), f"{label} copy has no banned terms")
            check("PO Box 940061, Maitland, FL 32794" in page_html, f"{label} uses the PO Box")
            check("CyberDadKit" in page_html, f"{label} uses CyberDadKit")
            check("G-5B1LNCPB56" in page_html, f"{label} includes the site GA4 id")
            check("{%" not in page_html and "layout:" not in page_html and "sitemap: false" not in page_html, f"{label} is static HTML that jekyll-sitemap lists")
            check("drive.google.com" not in page_html and "docs.google.com" not in page_html, f"{label} has no Drive delivery URL")
            check(not re.search(r'href="[^"]+\.(?:pdf|zip)"', page_html, re.I) and "download=" not in page_html, f"{label} links no PDF or ZIP")
            check(not re.search(r'href=["\']#["\']', page_html), f"{label} has no empty hash href")
            check(not internal.search(visible), f"{label} omits internal status wording")
            page_doc = parse(product if label == slug else refund)
            urls = re.findall(r'(?:href|src)="([^"]*)"', page_html)
            urls += re.findall(r'content="(https://[^"]+)"', page_html)
            for url in urls:
                if url.startswith("mailto:"):
                    check(url.startswith("mailto:ruel@getcyberdadkit.com"), f"{label} mailto {url}")
                    continue
                if url.startswith("#"):
                    check(url[1:] in page_doc.ids, f"{label} anchor {url}")
                    continue
                if url in STRIPE_PLACEHOLDERS or LIVE_LINK.match(url) or url == "https://www.googletagmanager.com/gtag/js?id=G-5B1LNCPB56":
                    continue
                if url.startswith("https://getcyberdadkit.com"):
                    path = url[len("https://getcyberdadkit.com"):] or "/"
                elif url.startswith("/"):
                    path = url
                else:
                    check(False, f"{label} unrecognized reference {url}")
                    continue
                path = path.split("#", 1)[0]
                check(path in ROUTES and ROUTES[path].is_file(), f"{label} link {url}")
            for img in page_doc.images:
                check(img.get("src", "").lstrip("/") in THANKSGIVING_FILES, f"{label} image is a real preview: {img.get('src')}")

    kids_html = (HOLIDAY / "kids-table" / "index.html").read_text(encoding="utf-8")
    kids_refund_html = (HOLIDAY / "kids-table" / "refund" / "index.html").read_text(encoding="utf-8")
    kids_doc = parse(HOLIDAY / "kids-table" / "index.html")
    bundle_pay = [a for a in kids_doc.anchors if a.get("id") == "kids-bundle-checkout"]
    bundle_href = bundle_pay[0].get("href", "") if len(bundle_pay) == 1 else ""
    check(bundle_href == "STRIPE_LINK_KIDS_BUNDLE" or bool(LIVE_LINK.match(bundle_href)), "kids bundle buy href is its placeholder or a live Stripe link")
    check(bundle_href not in {PAYMENT_URL, TRIVIA_PAYMENT_URL, BUNDLE_PAYMENT_URL}, "kids bundle does not reuse another product's link")
    if bundle_href == "STRIPE_LINK_KIDS_BUNDLE":
        pending.append(bundle_href)
        check("STRIPE_LINK_KIDS_BUNDLE (1 place)" in kids_html, "kids bundle placeholder is marked TODO")
    check("$11.99" in element_text(kids_html, "kids-bundle-checkout"), "kids bundle button names $11.99")
    check(kids_html.find('id="kids-checkout"') < kids_html.find('id="bundle-title"') < kids_html.find('id="kids-bundle-checkout"'), "kids bundle callout sits below the pack's buy button")
    check(not re.search(r"bought separately|savings|\bsave \$|\bsave up|% off", kids_html, re.I), "kids bundle makes no savings or comparison claim")
    for label, page_html in (("kids-table", kids_html), ("kids-table refund", kids_refund_html)):
        check(" ".join(element_text(page_html, "kids-bundle-refund-wording").split()) == KIDS_BUNDLE_REFUND, f"{label} carries the bundle refund sentence")
    check(
        "does not promise automatic processing" not in kids_refund_html
        and "bought on its own" not in kids_refund_html
        and "applies only to" not in kids_refund_html,
        "kids refund page omits the extra policy sentences",
    )
    host_html = (HOLIDAY / "host-planner" / "index.html").read_text(encoding="utf-8")
    check("bundle" not in host_html.lower(), "host planner has no bundle (single product policy)")
    for p in STRIPE_PLACEHOLDERS:
        hits = []
        for path in HOLIDAY.rglob("*.html"):
            if p in path.read_text(encoding="utf-8"):
                hits.append(path.relative_to(ROOT).as_posix())
        allowed = ["holiday/host-planner/index.html"] if p == "STRIPE_LINK_HOST" else ["holiday/kids-table/index.html"]
        check(hits == [] or hits == allowed, f"{p} appears only on its product page" + ("" if hits in ([], allowed) else ": " + ", ".join(hits)))
    check(not (HOLIDAY / "host-planner" / "sample").exists() and not (HOLIDAY / "kids-table" / "sample").exists(), "no sample page without a small sample file")
    check('href="/holiday/host-planner/">Host Planner</a>' in store_html and 'href="/holiday/kids-table/">Kids\' Table</a>' in store_html, "holiday nav links to Host Planner and Kids' Table")
    check(store_html.find('id="trivia-bundle"') < store_html.find('id="thanksgiving-packs"') < store_html.find('id="listing-title"'), "Thanksgiving cards sit after the trivia callout and before the listing")
    check('href="/holiday/kids-table/#bundle"' in store_html, "/holiday/ card links the Kids' Table bundle")
    check(not any(p in store_html for p in STRIPE_PLACEHOLDERS), "/holiday/ carries no placeholder buy link")
    check("holiday/host-planner" not in config and "holiday/kids-table" not in config, "Jekyll config does not exclude the new pages")
    check("Disallow: /holiday/host-planner" not in robots and "Disallow: /holiday/kids-table" not in robots, "robots.txt does not block the new pages")
    drive_hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or skip_parts.intersection(path.parts) or path.suffix.lower() in skip_suffixes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if re.search(r"drive\.google\.com/(?:file|uc|drive)", text) and path.relative_to(ROOT).as_posix().startswith("holiday/"):
            drive_hits.append(path.relative_to(ROOT).as_posix())
    check(drive_hits == [], "no Drive delivery URL under holiday/" + ("" if not drive_hits else ": " + ", ".join(drive_hits)))
    if pending:
        print("PENDING Stripe link placeholders: " + ", ".join(pending))
    if require_live:
        check(pending == [], "--require-live-links: every Thanksgiving buy button has a live Stripe link")

    print()
    if failed:
        print(f"{len(failed)} check(s) failed")
        return 1
    print(f"all checks passed ({len(GAMES)} games, 3 preview hashes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
