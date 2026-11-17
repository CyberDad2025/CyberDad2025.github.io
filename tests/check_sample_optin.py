#!/usr/bin/env python3
"""Redirect stubs at /holiday/sample/ and /holiday/trivia/sample/.

One-page holiday shop (feat/holiday-one-page-1117): both pages now send
visitors to the Travel Adventure card at /holiday/#travel-adventure. The full
incoming query string (utm_*, gclid, fbclid, epik and anything else) passes
through unchanged, with the hash last. The no-JS fallback is a plain meta
refresh and link to /holiday/#travel-adventure. (Before this change the stubs
went to /holiday/travel-adventure/ and rewrote utm_campaign/utm_content.)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "origin/main"
TA = "/holiday/#travel-adventure"
SHOP_ABS = "https://getcyberdadkit.com/holiday/"

STUBS = (
    ("holiday/sample/index.html", "sample-redirect-table-talk-trails"),
    ("holiday/trivia/sample/index.html", "sample-redirect-trivia"),
)

FOOTER_LINES = (
    "<p>CyberDadKit © 2026</p>",
    "<p>CyberDad Kit LLC</p>",
    "<p>PO Box 940061, Maitland, FL 32794</p>",
    '<p><a href="mailto:ruel@getcyberdadkit.com">ruel@getcyberdadkit.com</a></p>',
)


def footer(html: str) -> str:
    match = re.search(r"<footer\b.*?</footer>", html, re.S)
    return match.group(0) if match else ""


def visible_text(html: str) -> str:
    stripped = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    stripped = re.sub(r"<style\b.*?</style>", " ", stripped, flags=re.S | re.I)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    return stripped


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    for rel, content in STUBS:
        html = (ROOT / rel).read_text(encoding="utf-8")
        label = "/" + rel[: -len("index.html")]
        check("layout: null" in html and "sitemap: false" in html, f"{label} is layout null and sitemap: false")
        check('name="robots" content="noindex, follow"' in html, f"{label} is noindex, follow")
        check(f'rel="canonical" href="{SHOP_ABS}"' in html, f"{label} canonical points at the holiday shop")
        check("{% include ga4.html %}" in html, f"{label} includes the site GA4 tag")
        check('window.location.replace("/holiday/" + window.location.search + h)' in html, f"{label} uses location.replace and keeps the whole query string")
        check('var h = "#travel-adventure";' in html, f"{label} lands on the #travel-adventure card")
        check('src = "pinterest"' not in html and "utm_source=pinterest" not in html and "utm_medium=paid" not in html, f"{label} has no pinterest/paid default")
        check("params.set(" not in html, f"{label} does not rewrite any query parameter")
        check(f'content="0; url={TA}"' in html, f"{label} meta refresh is the plain Travel Adventure card URL")
        check(f'<a href="{TA}">See The Great Thanksgiving Travel Adventure in the holiday shop</a>' in html, f"{label} has a visible no-JS fallback link with no UTM params")
        check("buy.stripe.com" not in html, f"{label} has no Stripe href")
        check("utm_source=site" not in html, f"{label} in-page links have no internal UTMs")
        sample_footer = footer(html)
        for line in FOOTER_LINES:
            check(sample_footer.count(line) == 1, f"{label} footer has one identity line: {line}")
        check(not re.search(r"\bCDK\b", visible_text(html)), f"{label} has no CDK in public copy")
        check("CyberDadKit" in visible_text(html), f"{label} uses CyberDadKit")
        check("\u2013" not in html and "\u2014" not in html, f"{label} has no en or em dashes")
        check(not re.search(r"\b(guarantee|worldwide|hurry|limited|last chance|now only)\b", html, re.I), f"{label} has no banned wording")

    journal = "journal/2027/sample/index.html"
    current = (ROOT / journal).read_text(encoding="utf-8")
    previous = subprocess.check_output(["git", "show", f"{MAIN}:{journal}"], cwd=ROOT, text=True)
    check(current == previous, "journal/2027/sample/ is unchanged versus main")

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL SAMPLE REDIRECT CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
