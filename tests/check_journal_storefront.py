#!/usr/bin/env python3
"""Checks for the 2027 Bible Verse Journal storefront (/journal/2027/).

Confirms the size selector lists all three sizes with Ruel's final prices
(Letter $9.99, A4 $9.99, half-letter $7.99), each size has its own buy button
pointing at its own Stripe payment link, the free sample is the 12-page file
only (no full journal PDF is published), the refund page mirrors the 7-day
holiday wording, and the copy rules hold.

Run: python3 tests/check_journal_storefront.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
J = ROOT / "journal" / "2027"
PAGES = {
    "store": J / "index.html",
    "sample": J / "sample" / "index.html",
    "refund": J / "refund" / "index.html",
}
SAMPLE_PDF = J / "sample" / "CyberDadKit-2027-Bible-Verse-Journal-FREE-SAMPLE-US-Letter.pdf"
SIZES = {
    # button id: (price, live Stripe payment link URL)
    "buy-letter": ("$9.99", "https://buy.stripe.com/fZu00i9yu0DS22h1bNds408"),
    "buy-a4": ("$9.99", "https://buy.stripe.com/14AfZg9yudqEfT74nZds409"),
    "buy-half": ("$7.99", "https://buy.stripe.com/4gM6oGh0WfyM0Yd6w7ds40a"),
}
REFUND_CORE = ("You may request a full refund for any reason within 7 days of your purchase date. "
               "Email <a href=\"mailto:ruel@getcyberdadkit.com\">ruel@getcyberdadkit.com</a> with the email address "
               "used for purchase and your order reference. Never send card details. Refunds are returned to the "
               "original payment method. No physical return is required.")
US = "Available only to customers located in the United States."
ADDRESS = "PO Box 940061, Maitland, FL 32794"


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors: list[dict] = []
        self.ids: list[str] = []
        self.srcs: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get("id"):
            self.ids.append(d["id"])
        if tag == "a":
            self.anchors.append(d)
        if tag == "img" and d.get("src"):
            self.srcs.append(d["src"])


def main() -> int:
    failures = 0

    def check(ok: bool, msg: str) -> None:
        nonlocal failures
        print(("ok   " if ok else "FAIL ") + msg)
        failures += 0 if ok else 1

    html = {k: p.read_text(encoding="utf-8") for k, p in PAGES.items() if p.exists()}
    check(len(html) == 3, "store, sample and refund pages exist")
    parsed = {}
    for k, text in html.items():
        a = Anchors(); a.feed(text); parsed[k] = a
        check(f'<link rel="canonical" href="https://getcyberdadkit.com/journal/2027/{"" if k == "store" else k + "/"}">' in text,
              f"{k}: canonical URL on getcyberdadkit.com")
        check(ADDRESS in text, f"{k}: PO Box address in footer")
        check("World English Bible" in text or k == "refund", f"{k}: WEB translation credit")
        check(len(a.ids) == len(set(a.ids)), f"{k}: element ids are unique")
        for src in a.srcs:
            check((ROOT / src.lstrip("/")).is_file(), f"{k}: image {src} exists")
        for anc in a.anchors:
            href = anc.get("href", "")
            if href.startswith("/journal/") or href.startswith("/holiday/assets"):
                path = href.split("#")[0]
                target = ROOT / path.lstrip("/")
                ok = target.is_file() or (target / "index.html").is_file()
                check(ok, f"{k}: internal link {href} resolves")

    store = html.get("store", "")
    a = parsed.get("store")
    check('id="size-selector"' in store, "store has the size selector")
    for bid, (price, url) in SIZES.items():
        btn = [x for x in a.anchors if x.get("id") == bid]
        check(len(btn) == 1, f"{bid}: exactly one button")
        if btn:
            check(btn[0].get("href") == url, f"{bid}: links to its own live Stripe payment link")
        m = re.search(rf'id="{bid}"[^>]*>([^<]*)<', store)
        check(bool(m) and price in m.group(1) and "USD" in m.group(1), f"{bid}: button text names {price} USD")
    urls = [u for _, u in SIZES.values()]
    check(len(set(urls)) == 3, "three distinct payment links")
    check("STRIPE_LINK_" not in store, "no Stripe placeholders left")
    check(store.find("Stripe checkout displays Ruel Miller.") < store.find('id="buy-letter"'), "merchant notice is before the pay buttons")
    check(US in store, "store states US eligibility")
    check(REFUND_CORE in store and REFUND_CORE in html.get("refund", ""), "7-day refund wording on store and refund page")
    holiday_refund = (ROOT / "holiday" / "refund" / "index.html").read_text(encoding="utf-8")
    check(REFUND_CORE in holiday_refund, "refund wording mirrors the holiday refund page")
    for k in ("sample", "refund"):
        check("buy.stripe.com" not in html.get(k, ""), f"{k} page does not sell")

    # Only the 12-page sample PDF is published; no full journal PDF anywhere in the repo.
    pdfs = sorted(p.relative_to(ROOT).as_posix() for p in J.rglob("*.pdf"))
    check(pdfs == [SAMPLE_PDF.relative_to(ROOT).as_posix()], f"only the sample PDF is published under /journal/2027/ ({pdfs})")
    try:
        info = subprocess.run(["pdfinfo", str(SAMPLE_PDF)], capture_output=True, text=True, check=True).stdout
        pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        check(pages == 12, f"sample PDF has 12 pages (found {pages})")
    except (FileNotFoundError, subprocess.CalledProcessError, AttributeError):
        check(SAMPLE_PDF.stat().st_size < 500_000, "sample PDF is small (pdfinfo unavailable)")
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    full = [t for t in tracked if re.search(r"journal-2027-(letter|a4|half)\.pdf$", t)]
    check(not full, "no full journal PDF is tracked in the repo")

    # Sitemap is the Liquid template at sitemap.xml (not the jekyll-sitemap gem's
    # own file). Static .html/.pdf files, including /journal/2027/, are listed
    # from site.static_files. The gem stays installed and does not overwrite it.
    cfg = (ROOT / "_config.yml").read_text(encoding="utf-8")
    sitemap_src = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    check("{% for file in site.static_files %}" in sitemap_src and ".html" in sitemap_src and ".pdf" in sitemap_src,
          "Liquid sitemap lists static HTML and PDF, including /journal/2027/")
    check(not re.search(r'path:\s*"?journal', cfg), "_config.yml does not exclude /journal/ from the sitemap")
    check("Sitemap: https://getcyberdadkit.com/sitemap.xml" in (ROOT / "robots.txt").read_text(encoding="utf-8"), "robots.txt points to the sitemap")
    built_sitemap = next((p for p in (ROOT / "_site" / "sitemap.xml", Path("/tmp/cdk-copy-site/sitemap.xml")) if p.is_file()), None)
    if built_sitemap is not None:
        built_text = built_sitemap.read_text(encoding="utf-8")
        for loc in (
            "https://getcyberdadkit.com/journal/2027/",
            "https://getcyberdadkit.com/journal/2027/refund/",
            "https://getcyberdadkit.com/journal/2027/sample/",
        ):
            check(loc in built_text or loc.rstrip("/") in built_text, f"built sitemap lists {loc}")

    # Copy rules.
    public = "\n".join(html.values())
    check("drive.google.com" not in public, "no Drive delivery links on public pages")
    check("plink_" not in public and "acct_" not in public and "prod_" not in public, "no internal Stripe ids")
    for word, label in [(r"guarantee", "'guarantee'"), (r"\bCDK\b", "'CDK'"), (r"shield", "Shield Kit"),
                        (r"california", "California"), (r"\b(son|daughter|child|kids?)\b", "child details"),
                        (r"best ?seller|testimonial|limited time|selling fast", "demand claims")]:
        check(not re.search(word, public, re.I), f"copy has no {label}")

    print("\nall checks passed" if failures == 0 else f"\n{failures} check(s) failed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
