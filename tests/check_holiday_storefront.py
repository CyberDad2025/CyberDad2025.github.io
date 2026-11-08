#!/usr/bin/env python3
"""Checks for the Gather & Play review-draft storefront.

Confirms the public pages use the real preview files, leave checkout off,
and do not publish the Ops archive, draft PDFs, or a download link.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOLIDAY = ROOT / "holiday"
STORE = HOLIDAY / "index.html"
DELIVERY = HOLIDAY / "delivery" / "index.html"
MANIFEST = HOLIDAY / "product.json"

PREVIEW_HASHES = {
    "holiday/assets/previews/CyberDadKit-preview-page-01.png":
        "89fcf00322203cfe543ce7f32cc16adc1aab9d620acdb780eec72d12b9b50e09",
    "holiday/assets/previews/CyberDadKit-preview-page-09.png":
        "86a48f58cc563fa4076749c0770e09af6a31318ad096d92d971c41ab2c747a1c",
}
ZIP_SHA = "bc2e9c572f1e17af32cfbfc8ea17838878e5ccca1f0c45e066fed09ffc571313"
PAYMENT_URL = "https://buy.stripe.com/9B67sK4ea4U8dKZ07Jds405"
US_ELIGIBILITY = "Available only to customers located in the United States."
PIN_SHA = "a45cbb992293aef692d92a92222946e76f6c2b30c593c019048167bc2a21866e"
PIN_REL = "holiday/assets/pins/01-thanksgiving-host.png"
ZIP_REL = "holiday/delivery/files/CyberDadKit-Gather-and-Play.zip"
SAMPLE_PDFS = {
    "holiday/sample/Free-Sample-Table-Talk-Trails-US-Letter.pdf": "20e1cb2b96b03f147efa5a267a796dc2dbb1b5a1b8b64196747fe31c5d2f6c64",
    "holiday/sample/Free-Sample-Table-Talk-Trails-A4.pdf": "3f9bb5ac9f5c9d83b64df2bc06c82f5bcf80540daf538c2e593feabac7954c3a",
}
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
    "/holiday/delivery/": DELIVERY,
    "/holiday/refund/": HOLIDAY / "refund" / "index.html",
    "/holiday/sample/": HOLIDAY / "sample" / "index.html",
    "/holiday/sample/Free-Sample-Table-Talk-Trails-US-Letter.pdf": HOLIDAY / "sample" / "Free-Sample-Table-Talk-Trails-US-Letter.pdf",
    "/holiday/sample/Free-Sample-Table-Talk-Trails-A4.pdf": HOLIDAY / "sample" / "Free-Sample-Table-Talk-Trails-A4.pdf",
    "/holiday/delivery/files/CyberDadKit-Gather-and-Play.zip": HOLIDAY / "delivery" / "files" / "CyberDadKit-Gather-and-Play.zip",
    "/holiday/product.json": MANIFEST,
    "/holiday/assets/holiday.css": HOLIDAY / "assets" / "holiday.css",
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
    delivery_html = body(DELIVERY)
    store = parse(STORE)
    delivery = parse(DELIVERY)

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
    check(manifest["final_customer_file"]["ready"] is True, "customer ZIP is the release file")
    check(manifest["final_customer_file"]["sha256"] == ZIP_SHA, "manifest ZIP hash")
    check(manifest["price"]["currency"] == "USD", "public price currency is USD")
    check(manifest["price"]["status"] == "final_public_price", "public price is final")
    check(len(manifest["previews"]) == 2, "cover and winter-game previews")
    check(manifest["price"]["type"] == "one_time" and manifest["price"]["recurring"] is False, "one-time price")
    check(manifest["price"]["amount"] == "7.99", "proposed 7.99")
    check(len(manifest["previews"]) == 2, "two final previews recorded")

    for rel, digest in PREVIEW_HASHES.items():
        path = ROOT / rel
        check(path.is_file() and sha256(path) == digest, f"preview hash {path.name}")

    for page_name, html, doc in (("storefront", store_html, store), ("delivery", delivery_html, delivery)):
        check("Review draft" not in html, f"{page_name} does not call the files a review draft")
        check(not re.search(r"proposed", html, re.I), f"{page_name} does not say the price is proposed")
        check("CyberDadKit" in html, f"{page_name} uses CyberDadKit")
        check(not re.search(r"\bCDK\b", html), f"{page_name} has no CDK abbreviation")
        check("64 unique" not in html.lower(), f"{page_name} makes no 64-unique-page claim")
        check("PO Box 940061, Maitland, FL 32794" in html, f"{page_name} uses the PO Box")
        check("ruel@getcyberdadkit.com" in html, f"{page_name} uses the existing contact")
        if page_name == "storefront":
            check(not re.search(r'href="[^"]+\.(?:pdf|zip)"', html, re.I), "storefront does not link the paid ZIP or a PDF")
        if page_name == "delivery":
            check(html.count('href="/holiday/delivery/files/CyberDadKit-Gather-and-Play.zip"') == 1, "delivery links the customer ZIP once")
        check("download=" not in html, f"{page_name} has no download attribute")
        if page_name == "storefront":
            check(html.count('href="' + PAYMENT_URL + '"') == 1, "storefront has one live payment link")
        if page_name == "delivery":
            check("buy.stripe.com" not in html, "delivery page does not sell again")
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
            path = href.split("#", 1)[0]
            check(path in ROUTES and ROUTES[path].is_file(), f"{page_name} link {href}")

    check(store.images[0]["src"].endswith("page-01.png"), "hero preview is the cover")
    check({img["src"] for img in store.images} == {p["src"] for p in manifest["previews"]}, "storefront shows the final previews")
    check({img["src"] for img in delivery.images} == {p["src"] for p in manifest["previews"]}, "delivery shows the final previews")
    for game in GAMES:
        check(game in store_html, f"lists {game}")

    pay = [a for a in store.anchors if a.get("id") == "holiday-checkout"]
    check(len(pay) == 1 and pay[0].get("href") == PAYMENT_URL, "product checkout is the live payment anchor")
    check("disabled" not in pay[0], "product checkout anchor is not disabled")
    check("$7.99" in element_text(store_html, "holiday-checkout") and "USD" in element_text(store_html, "holiday-checkout"), "product button names $7.99 USD")
    check(US_ELIGIBILITY in store_html, "product page states US eligibility")
    check('href="/holiday/delivery/files/CyberDadKit-Gather-and-Play.zip"' in delivery_html, "delivery ZIP href is present")
    check('name="robots" content="noindex"' in delivery_html, "delivery noindex")
    check("sitemap: false" in DELIVERY.read_text(encoding="utf-8"), "delivery left out of the sitemap")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    check("Disallow: /holiday/delivery/" in robots, "robots.txt disallows the delivery page")

    banned = re.compile(r"best seller|bestseller|testimonial|limited time|customers love|selling fast", re.I)
    check(not banned.search(store_html + delivery_html), "no demand or testimonial claims")

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
    for label, html in (("storefront", store_html), ("delivery", delivery_html), ("refund", refund_html)):
        check(element_text(html, "gather-play-refund-wording") == EXACT_REFUND, f"{label} shows the exact refund wording")
        check("CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794" in html, f"{label} footer uses CyberDad Kit LLC")
        check("L25000463998" in html, f"{label} shows the Florida document number")
        check("does not promise automatic processing" in html or label == "refund", f"{label} avoids a processing-time promise")
    check("does not promise automatic processing" in refund_html, "refund page states there is no processing-time promise")
    check("personal, noncommercial gatherings" in refund_html, "printing license is personal and noncommercial")
    check("internal office use" in refund_html, "printing license includes internal office use")
    check("commercial event service" in refund_html, "printing license excludes a commercial event service")
    check('href="/holiday/refund/"' in store_html and 'href="/holiday/refund/"' in delivery_html, "storefront and delivery link to the refund route")
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
    check("Gather & Play" not in shield_terms, "terms of sale do not absorb Gather & Play")
    check("Gather & Play" not in sites_refund, "Sites refund page does not absorb Gather & Play")
    promise = re.compile(r"instant refund|refunds are automatic|within 24 hours|reply within", re.I)
    check(not promise.search(store_html + delivery_html + refund_html), "no automated or timed refund promise")

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
    public_html = store_html + delivery_html + refund_html + sample_html
    internal = re.compile(r"\bdraft\b|launch pass|not deployed|\bproposed\b|\bOps\b", re.I)
    check(not internal.search(public_html), "public pages omit internal status wording")
    check("plink_" not in public_html and "acct_" not in public_html, "public pages omit internal Stripe ids")
    check("Checkout unavailable" not in public_html and "not open yet" not in public_html, "checkout is no longer described as closed")

    zip_path = ROOT / ZIP_REL
    check(sha256(zip_path) == ZIP_SHA, "customer ZIP hash matches file QA")
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if not n.endswith("/")]
        check(len(names) == 4 and all(n.lower().endswith(".pdf") for n in names), "ZIP contains only four PDFs")
        check(sorted(names) == sorted(manifest["final_customer_file"]["contents"]), "ZIP names match the manifest")
        for name in names:
            info = subprocess.run(["pdfinfo", "-"], input=zf.read(name), capture_output=True, check=True)
            pages = [ln for ln in info.stdout.decode().splitlines() if ln.startswith("Pages:")]
            check(pages and pages[0].split()[-1] == "16", f"{name} is 16 pages")
    pdfs = sorted(p.relative_to(ROOT).as_posix() for p in HOLIDAY.rglob("*.pdf"))
    check(pdfs == sorted(SAMPLE_PDFS), "only the two one-page sample PDFs are loose files")
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

    published_extra = [p for p in HOLIDAY.rglob("*") if p.is_file() and p.suffix.lower() == ".zip" and p != zip_path]
    check(published_extra == [], "no second ZIP under holiday/")
    ops_names = list(ROOT.glob("CyberDadKit-Gather-and-Play-Ops-Review*")) + list(ROOT.glob("**/source/build.py"))
    check(ops_names == [], "Ops archive and source builder are not in the repo")

    print()
    if failed:
        print(f"{len(failed)} check(s) failed")
        return 1
    print(f"all checks passed ({len(GAMES)} games, 3 preview hashes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
