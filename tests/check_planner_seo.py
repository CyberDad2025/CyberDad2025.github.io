#!/usr/bin/env python3
"""SEO checks for /paycheck-planner/ and /paycheck-planner/bundle/ (27 Nov 2026).

Asserts title and meta description lengths, no em or en dashes, no price in the
og or meta description, that Product JSON-LD parses with no aggregateRating or
review, and that the planner and bundle URLs are in the built sitemap.

Run: python3 tests/check_planner_seo.py [--site /path/to/_site]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "paycheck-planner"
SITE = Path(sys.argv[sys.argv.index("--site") + 1]) if "--site" in sys.argv else None
if SITE is None and (ROOT / "_site" / "sitemap.xml").is_file():
    SITE = ROOT / "_site"

DASH = re.compile(r"[\u2014\u2013]")
PRICE_IN_PREVIEW = re.compile(r"\$\s*\d|\b14\.99\b|\b19\.99\b|\b39(?:\.00)?\b")
SENTENCE = "If you want a simple way to plan each paycheck, try the [Paycheck Planner](/paycheck-planner/)."
# Blog-post links are out of this patch. Those posts have scrambled slugs and
# content; a later PR will fix them and add the planner sentence. This list
# is only to prove this patch does not leave the sentence in them.
UNTOUCHED_POSTS = [
    ROOT / "_posts" / "2026-10-20-safe-online-shopping.md",
    ROOT / "_posts" / "2026-09-27-prevent-online-scams.md",
    ROOT / "_posts" / "2026-01-01-simple-home-network-security-for-non-tech-parents.md",
    ROOT / "_posts" / "2026-10-20-safe-social-media.md",
    ROOT / "_posts" / "2026-10-20-simple-privacy-tips.md",
]
PAGES = {
    "sales": {
        "path": DIR / "index.html",
        "title": "Paycheck to Paycheck Planner for a 2027 Money Reset",
        "desc": "A paycheck to paycheck planner for paycheck budgeting and a 2027 money reset. Google Sheets and Excel. Digital download, US and Canada customers only.",
        "name": "Paycheck Planner",
        "url": "https://getcyberdadkit.com/paycheck-planner/",
        "canonical": "https://getcyberdadkit.com/paycheck-planner/",
        "built": "paycheck-planner/index.html",
        "loc": "https://getcyberdadkit.com/paycheck-planner/",
    },
    "bundle": {
        "path": DIR / "bundle" / "index.html",
        "title": "Paycheck Planner Plus Bundle for a 2027 Money Reset",
        "desc": "Paycheck budgeting, debt payoff, sinking funds and a 2027 money reset in one bundle. Google Sheets and Excel. Digital download, US and Canada customers only.",
        "name": "Paycheck Planner Plus Bundle",
        "url": "https://getcyberdadkit.com/paycheck-planner/bundle/",
        "canonical": "https://getcyberdadkit.com/paycheck-planner/bundle/",
        "built": "paycheck-planner/bundle/index.html",
        "loc": "https://getcyberdadkit.com/paycheck-planner/bundle/",
    },
}

failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def yml_values(text: str) -> dict[str, str]:
    return dict(re.findall(r'^([a-z_]+):\s*"([^"]*)"\s*$', text, re.M))


def offer_price(values: dict[str, str], which: str) -> str:
    if which == "bundle":
        return values["price_bundle"]
    return values["price_planner"]


def first_tag(html: str, pattern: str) -> str | None:
    m = re.search(pattern, html)
    return m.group(1) if m else None


def product_json(html: str) -> dict | None:
    for raw in re.findall(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html, re.S):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if data.get("@type") == "Product":
            return data
    return None


def render_liquid(html: str, values: dict[str, str]) -> str:
    out = html
    out = out.replace("{{ pp.price_planner }}", values["price_planner"])
    out = out.replace("{{ pp.price_bundle }}", values["price_bundle"])
    out = out.replace("{{ pp.price_currency }}", values["price_currency"])
    return out


yml_text = (ROOT / "_data" / "paycheck_planner.yml").read_text(encoding="utf-8")
values = yml_values(yml_text)
check(values.get("price_planner") == "14.99", "yml planner price is 14.99")
check(values.get("price_bundle") == "39.00" and values.get("price_currency") == "USD", "yml bundle price is 39.00 USD")
check("price_planner_regular" not in values and "price_planner_regular_from" not in values, "yml has no build-time 2027 price flip keys")
check(len(re.findall(r"https://buy\.stripe\.com/[A-Za-z0-9]+", yml_text)) == 2, "yml still has only the two existing Stripe Payment Links")

for name, spec in PAGES.items():
    html = spec["path"].read_text(encoding="utf-8")
    label = f"[{name}]"
    title = first_tag(html, r"<title>(.*?)</title>")
    desc = first_tag(html, r'<meta name="description" content="([^"]*)"')
    og_title = first_tag(html, r'<meta property="og:title" content="([^"]*)"')
    og_desc = first_tag(html, r'<meta property="og:description" content="([^"]*)"')
    og_image = first_tag(html, r'<meta property="og:image" content="([^"]*)"')
    og_url = first_tag(html, r'<meta property="og:url" content="([^"]*)"')
    og_type = first_tag(html, r'<meta property="og:type" content="([^"]*)"')
    tw_card = first_tag(html, r'<meta name="twitter:card" content="([^"]*)"')
    tw_title = first_tag(html, r'<meta name="twitter:title" content="([^"]*)"')
    tw_desc = first_tag(html, r'<meta name="twitter:description" content="([^"]*)"')
    canonical = first_tag(html, r'<link rel="canonical" href="([^"]*)"')
    check(title == spec["title"] and len(title or "") <= 60, f"{label} title is the agreed copy and is 60 characters or fewer ({len(title or '')})")
    check(desc == spec["desc"] and len(desc or "") <= 160, f"{label} meta description is the agreed copy and is 160 characters or fewer ({len(desc or '')})")
    check(og_title == spec["title"] and tw_title == spec["title"], f"{label} og:title and twitter:title match the page title")
    check(og_desc == spec["desc"] and tw_desc == spec["desc"], f"{label} og:description and twitter:description match the meta description")
    for field, value in (("title", title), ("description", desc), ("og:title", og_title), ("og:description", og_desc), ("twitter:title", tw_title), ("twitter:description", tw_desc)):
        check(value is not None and not DASH.search(value), f"{label} {field} has no em or en dash")
    for field, value in (("description", desc), ("og:title", og_title), ("og:description", og_desc), ("twitter:title", tw_title), ("twitter:description", tw_desc)):
        check(value is not None and not PRICE_IN_PREVIEW.search(value), f"{label} {field} has no price")
    check(canonical == spec["canonical"], f"{label} canonical is {spec['canonical']}")
    check(og_url == spec["url"] and og_type == "website", f"{label} og:url is the page and og:type is website")
    check(og_image == "https://getcyberdadkit.com/paycheck-planner/assets/paycheck-planner-og-1200x630.png", f"{label} og:image is the existing 1200x630 planner image")
    check(tw_card == "summary_large_image", f"{label} twitter:card is summary_large_image")
    check(re.search(r"(?s)^---.*?sitemap:\s*true.*?---", html) is not None, f"{label} front matter has sitemap: true")
    check('name="robots"' not in html and "noindex" not in html, f"{label} is not noindexed")

    rendered = render_liquid(html, values)
    product = product_json(rendered)
    check(product is not None, f"{label} Product JSON-LD parses")
    if product:
        brand = product.get("brand") or {}
        brand_name = brand.get("name") if isinstance(brand, dict) else brand
        offer = product.get("offers") or {}
        expected_price = offer_price(values, name)
        check(product.get("name") == spec["name"], f"{label} Product name is {spec['name']}")
        check(product.get("description") == spec["desc"], f"{label} Product description matches the meta description")
        check(product.get("image") == "https://getcyberdadkit.com/paycheck-planner/assets/paycheck-planner-og-1200x630.png", f"{label} Product image is the og image")
        check(brand_name == "CyberDad Kit", f"{label} brand is CyberDad Kit")
        check(offer.get("@type") == "Offer", f"{label} offers is an Offer")
        check(offer.get("price") == expected_price, f"{label} Offer price is {expected_price}")
        if name == "sales":
            check(offer.get("priceValidUntil") == "2026-12-31", f"{label} Offer priceValidUntil is 2026-12-31")
        else:
            check("priceValidUntil" not in offer, f"{label} Offer has no priceValidUntil")
        check(offer.get("priceCurrency") == "USD", f"{label} Offer priceCurrency is USD")
        check(offer.get("availability") in ("https://schema.org/InStock", "InStock"), f"{label} Offer availability is InStock")
        check(offer.get("url") == spec["url"], f"{label} Offer url is the page")
        regions = offer.get("eligibleRegion") or []
        if isinstance(regions, str):
            regions = [regions]
        check("US" in regions and "CA" in regions, f"{label} Offer eligibleRegion includes US and CA")
        blob = json.dumps(product)
        check("aggregateRating" not in product and "review" not in product and "aggregateRating" not in blob and '"review"' not in blob, f"{label} Product JSON-LD has no aggregateRating or review")
        check("buy.stripe.com" not in blob and "checkout.stripe.com" not in blob, f"{label} Product JSON-LD has no Stripe URL")

hero = (ROOT / "_includes" / "home-planner-hero.html").read_text(encoding="utf-8")
check('href="/paycheck-planner/"' in hero and "See what is inside" in hero, "homepage planner hero already has a visible link: See what is inside")

for path in UNTOUCHED_POSTS:
    text = path.read_text(encoding="utf-8")
    check(SENTENCE not in text, f"{path.relative_to(ROOT)} has no planner sentence (links deferred)")

if SITE and (SITE / "sitemap.xml").is_file():
    sm = (SITE / "sitemap.xml").read_text(encoding="utf-8")
    for name, spec in PAGES.items():
        check(f"<loc>{spec['loc']}</loc>" in sm, f"[built] sitemap lists {spec['loc']}")
        built = SITE / spec["built"]
        if built.is_file():
            bhtml = built.read_text(encoding="utf-8")
            check('name="robots"' not in bhtml and "noindex" not in bhtml, f"[built {name}] is not noindexed")
            product = product_json(bhtml)
            check(product is not None, f"[built {name}] Product JSON-LD parses")
            if product:
                offer = product.get("offers") or {}
                check(offer.get("price") == offer_price(values, name), f"[built {name}] Offer price matches yml")
                if name == "sales":
                    check(offer.get("priceValidUntil") == "2026-12-31", "[built sales] Offer priceValidUntil is 2026-12-31")
                check("aggregateRating" not in product and "review" not in product, f"[built {name}] Product JSON-LD has no aggregateRating or review")
        else:
            check(False, f"[built {name}] {spec['built']} is missing")
    check("/paycheck-planner/delivered" not in sm, "[built] delivered page is not in the sitemap")
else:
    print("NOTE: pass --site DIR after a jekyll build to assert the built sitemap and rendered JSON-LD.")

print("ALL PLANNER SEO CHECKS PASSED" if not failed else f"FAILED {len(failed)} check(s)")
sys.exit(1 if failed else 0)
