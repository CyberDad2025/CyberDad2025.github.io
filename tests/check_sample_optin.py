#!/usr/bin/env python3
"""Redirect stubs at /holiday/sample/ and /holiday/trivia/sample/.

Both pages send visitors to /holiday/travel-adventure/. Incoming utm_source
is carried (utm_medium kept, campaign set to ap006_travel, unique
utm_content). Visits with no utm_source get no UTM params. gclid, fbclid
and epik pass through. The no-JS fallback is a plain Travel Adventure URL.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "origin/main"
TA = "/holiday/travel-adventure/"
TA_ABS = "https://getcyberdadkit.com/holiday/travel-adventure/"

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
        check(f'rel="canonical" href="{TA_ABS}"' in html, f"{label} canonical points at the Travel Adventure page")
        check("{% include ga4.html %}" in html, f"{label} includes the site GA4 tag")
        check("window.location.replace(url)" in html, f"{label} uses location.replace")
        check('src = "pinterest"' not in html and "utm_source=pinterest" not in html and "utm_medium=paid" not in html, f"{label} has no pinterest/paid default")
        check('if (src)' in html and 'params.set("utm_source", src)' in html, f"{label} keeps incoming utm_source")
        check('params.set("utm_campaign", "ap006_travel")' in html, f"{label} sets utm_campaign=ap006_travel when source is present")
        check(f'params.set("utm_content", "{content}")' in html, f"{label} sets utm_content={content} when source is present")
        check('["gclid", "fbclid", "epik"]' in html, f"{label} passes through gclid, fbclid and epik")
        check(f'content="0; url={TA_ABS}"' in html, f"{label} meta refresh is the plain Travel Adventure URL")
        check(f'<a href="{TA}">Go to The Great Thanksgiving Travel Adventure</a>' in html, f"{label} has a visible no-JS fallback link with no UTM params")
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
