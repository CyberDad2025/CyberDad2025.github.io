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
GUARANTEE_RE = re.compile(r"\bguarante(?:e|ed|es)\b", re.I)
SHIELD_RE = re.compile(r"\bshield\b", re.I)
DOC_NUMBER = "L25000463998"
UTM_KEYS = ("utm_source=site", "utm_medium=cta", "utm_campaign=holiday-funnel", "utm_content=")

# Trivia, Kids' Table, and Host Planner stay as they are: moving their buy
# blocks would rewrite pages whose visible text is locked, which is not a
# small edit. This list proves those files were left alone.
UNCHANGED = (
    "holiday/trivia/index.html",
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
    {
        "rel": "holiday/sample/index.html",
        "product": 'id="sample-title"',
        "sample": 'id="sample"',
        "buy": 'id="holiday-checkout"',
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

    print("Stripe hrefs (current == origin/main):")
    for page in PAGES:
        rel = page["rel"]
        html = (ROOT / rel).read_text(encoding="utf-8")
        previous = git_show(rel)
        label = "/" + rel[: -len("index.html")]
        product_at = html.find(page["product"])
        sample_at = html.find(page["sample"])
        signup_at = html.find('id="updates"')
        buy_at = html.find(page["buy"])
        page_hero = hero(html)
        stripe_now = STRIPE_RE.findall(html)
        stripe_old = STRIPE_RE.findall(previous)
        print(f"  {rel}: {stripe_now}")

        check(0 < product_at < sample_at < signup_at < buy_at, f"{label} order is product, sample, signup, buy")
        check(page["buy"] not in page_hero and "ml-embedded" not in page_hero, f"{label} hero is the product, without the form or the buy button")
        check(html.count('class="ml-embedded"') == 1, f"{label} has one ml-embedded container")
        check(html.count('data-form="eMwTaD"') == 1, f"{label} has one eMwTaD embed")
        check(html.count("data-form=") == 1, f"{label} has no second data-form")
        check(html.count("https://assets.mailerlite.com/js/universal.js") == 1, f"{label} loads universal.js once")
        check("ml('account','1632878')" in html, f"{label} uses MailerLite account 1632878")
        check(html.count(NOSCRIPT) == 1, f"{label} has one noscript hosted-form fallback")
        check("optin_view" in html and "IntersectionObserver" in html, f"{label} keeps the optin_view event")
        check(not GUARANTEE_RE.search(html), f"{label} has no guarantee wording")
        check(not SHIELD_RE.search(html), f"{label} has no Shield mention")
        check(US_ONLY in html, f"{label} keeps the US-only sentence")
        check(DOC_NUMBER not in html, f"{label} has no Florida document number")
        page_footer = footer(html)
        check(html.count("<footer") == 1 and page_footer.count("</footer>") == 1, f"{label} has one footer")
        for line in FOOTER_LINES:
            check(page_footer.count(line) == 1, f"{label} footer line once: {line}")
        check(stripe_now == stripe_old, f"{label} Stripe hrefs match main")
        for href in added_holiday_ctas(html, previous):
            decoded = href.replace("&amp;", "&")
            missing = [key for key in UTM_KEYS if key not in decoded]
            check(not missing, f"{label} added CTA {href} has UTM {UTM_KEYS}" + ("" if not missing else f" missing {missing}"))
        if rel != "holiday/sample/index.html":
            check('id="sample-round-cta"' in html, f"{label} sample CTA is marked")
            cta = re.search(r'id="sample-round-cta" href="([^"]+)"', html)
            target = cta.group(1).replace("&amp;", "&") if cta else ""
            check(target.startswith("/holiday/sample/?"), f"{label} sample CTA points at the sample page")
            check(all(key in target for key in UTM_KEYS), f"{label} sample CTA carries holiday-funnel UTM params")

    for rel in UNCHANGED:
        current = (ROOT / rel).read_text(encoding="utf-8")
        previous = git_show(rel)
        check(current == previous, f"{rel} left unchanged (funnel edit was not small enough)")

    worldwide_re = re.compile(r"\bworldwide\b", re.I)
    holiday_pages = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "holiday").rglob("*.html")
    )
    check(bool(holiday_pages), "holiday public pages were scanned for worldwide")
    for rel in holiday_pages:
        text = (ROOT / rel).read_text(encoding="utf-8")
        hits = worldwide_re.findall(text)
        check(not hits, f"{rel} does not say worldwide" + ("" if not hits else f" ({len(hits)})"))

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL HOLIDAY FUNNEL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
