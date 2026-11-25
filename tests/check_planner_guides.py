#!/usr/bin/env python3
"""Checks for Paycheck Planner SEO guide pages under /guides/.
Run: python3 tests/check_planner_guides.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "guides"
PAGES = {
    "hub": DIR / "index.html",
    "budget-by-paycheck": DIR / "budget-by-paycheck" / "index.html",
    "bills-before-payday": DIR / "bills-before-payday" / "index.html",
    "three-paycheck-months-2027": DIR / "three-paycheck-months-2027" / "index.html",
    "january-budget-reset": DIR / "january-budget-reset" / "index.html",
}
CSS = ROOT / "paycheck-planner" / "assets" / "paycheck-planner.css"
FOOTER = ROOT / "_includes" / "paycheck-planner-footer.html"
ADDRESS = "CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794"
US_ONLY = "Available to customers located in the United States and Canada."
ADVICE = "A budgeting tool, not financial advice."
US_CUSTOMERS = "US and Canada customers only."
BANNED = {
    "em or en dash": r"[\u2014\u2013]",
    "guarantee": r"guarantee",
    "bare CDK": r"\bCDK\b",
    "age": r"\bages?\b|years?[ -]old|\btoddlers?\b|\bteens?\b|\bgrade\s*\d|\bkindergarten",
    "family or child details": r"\bfamil(?:y|ies)\b|\b(?:kids?|child(?:ren)?|mom|dad|mother|father|wife|husband|son|daughter|siblings?)\b",
    "employer": r"\bemployers?\b|\bmy job\b|\bwhere I work\b",
    "income claim": r"\b(?:earn (?:up to|\$|more)|make money|extra cash|get out of debt|save \$|save up to|get rich|passive income|side hustle)\b",
    "testimonial or review": r"\b(?:testimonials?|reviews?|rated|stars?|customers say|loved by)\b|\u2605",
    "fake urgency or counter": r"\b(?:limited time|hurry|last chance|today only|act now|only \d+ left|selling fast|countdown|ends (?:soon|tonight|today|sunday|monday)|sold \d+|\d+ (?:sold|bought|people))\b",
    "non-US offer": r"\bworldwide\b|\binternational shipping\b|\bships? to\b",
}
FORBIDDEN_PHRASES = ("exactly", "spending money", "debt-free", "receipt email", "/thanks/", "drive.google.com")
failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def visible_text(html: str) -> str:
    s = re.sub(r"\{%-?\s*comment.*?endcomment\s*-?%\}", " ", html, flags=re.S)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<script\b.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s)


html: dict[str, str] = {}
for name, path in PAGES.items():
    check(path.is_file(), f"{path.relative_to(ROOT)} exists")
    html[name] = path.read_text(encoding="utf-8") if path.is_file() else ""

footer = FOOTER.read_text(encoding="utf-8") if FOOTER.is_file() else ""
check(ADDRESS in footer, "planner footer still has the publisher line")
check(CSS.is_file(), "planner CSS exists")

for name, text in html.items():
    label = f"[{name}]"
    seen = visible_text(text)
    for what, rx in BANNED.items():
        hit = re.search(rx, text if what in ("em or en dash", "guarantee") else seen, re.I)
        check(hit is None, f"{label} no {what}" + (f" (found {hit.group(0)!r})" if hit else ""))
    for phrase in FORBIDDEN_PHRASES:
        if phrase == "exactly":
            hit = "exactly" in seen.lower()
        elif phrase == "/thanks/":
            hit = "/thanks/" in text.lower()
        else:
            hit = phrase.lower() in text.lower()
        check(not hit, f"{label} has no forbidden phrase {phrase!r}")
    check(US_ONLY in text, f"{label} has the US and Canada declaration")
    check(ADVICE in seen, f"{label} says a budgeting tool, not financial advice")
    check(US_CUSTOMERS in seen, f"{label} says US and Canada customers only")
    check("sitemap: true" in text, f"{label} is in the sitemap")
    check(text.count("<h1") == 1, f"{label} has one h1")
    check('lang="en"' in text and 'name="viewport"' in text, f"{label} has lang and viewport")
    check('rel="canonical"' in text, f"{label} has a canonical")
    check("application/ld+json" in text, f"{label} has JSON-LD")
    check("{% include paycheck-planner-footer.html %}" in text, f"{label} uses the planner footer")
    check(text.count("{% include ga4.html %}") == 1, f"{label} includes GA4 once")
    check("G-5B1LNCPB56" not in text and "gtag(" not in text, f"{label} adds no second GA config")
    check("buy.stripe.com" not in text and "checkout.stripe.com" not in text, f"{label} has no Stripe URL")
    check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)|\.xlsx\"|\.pdf\"|/downloads/", text, re.I), f"{label} has no Drive or download file link")
    check('href="/paycheck-planner/"' in text, f"{label} links to /paycheck-planner/")
    check('href="/paycheck-planner/assets/paycheck-planner.css"' in text, f"{label} uses the planner stylesheet")
    srcs = re.findall(r"<script[^>]+src=\"([^\"]+)\"", text)
    check(srcs == [], f"{label} loads no extra script src ({srcs})")
    prices = set(re.findall(r"\$\d[\d,]*(?:\.\d{2})?", seen))
    check("14.99" not in seen and "19.99" not in seen and "$39" not in seen, f"{label} does not show product prices")
    if name == "hub":
        check(prices == set(), f"{label} shows no dollar amounts: {sorted(prices)}")
    elif name == "three-paycheck-months-2027":
        check("sample" in seen.lower() and "January 1, 2027" in seen, f"{label} labels sample paydays")
    else:
        check(prices, f"{label} includes a worked example with dollar amounts")
        check("sample" in seen.lower(), f"{label} labels sample numbers")
    for href in re.findall(r'href="(/[^"#?{]*)', text):
        p = ROOT / href.lstrip("/")
        ok = (href == "/") or p.is_file() or (p / "index.html").is_file() or (p / "index.md").is_file() or p.with_suffix(".md").is_file() or p.with_suffix(".html").is_file()
        if href.endswith("/") and href != "/":
            ok = (p / "index.html").is_file() or (p / "index.md").is_file() or p.with_suffix(".md").is_file()
        check(ok, f"{label} internal link {href} resolves")

# Cross links and targets
check("/guides/budget-by-paycheck/" in html["hub"] and "/guides/bills-before-payday/" in html["hub"]
      and "/guides/three-paycheck-months-2027/" in html["hub"] and "/guides/january-budget-reset/" in html["hub"],
      "hub links all four guides")
sales = (ROOT / "paycheck-planner" / "index.html").read_text(encoding="utf-8")
check(all(s in sales for s in ("/guides/budget-by-paycheck/", "/guides/bills-before-payday/",
      "/guides/three-paycheck-months-2027/", "/guides/january-budget-reset/", "/guides/")),
      "sales page links the four guides and the hub")

if failed:
    print(f"FAILED {len(failed)} check(s)")
    sys.exit(1)
print("ALL PLANNER GUIDE CHECKS PASSED")
