#!/usr/bin/env python3
"""Checks for the Paycheck Planner pages: /paycheck-planner/ (sales), /sample/ (free mini sheet), /bundle/ (upgrade), /refund/.
There are no thank-you pages and no purchase event: the Stripe Payment Links use hosted confirmation (like Gather & Play), which
never returns to this site. Download links appear only in Stripe's confirmation message, never in the repo or on a page.

Placeholders: every value in _data/paycheck_planner.yml that ends in _TODO is a placeholder (today only the two Stripe
Payment Links). That file is the ONLY place a placeholder may live. No paid download link or file exists anywhere in the
repo or on any page.
By default this test PRINTS each one as a FLAG and still passes, so CI stays green while the pages are in review.
Run with --launch before merging: any leftover placeholder then FAILS, and the real values are format-checked.

Run: python3 tests/check_paycheck_planner.py [--launch]
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = "--launch" in sys.argv
DATA = ROOT / "_data" / "paycheck_planner.yml"
DIR = ROOT / "paycheck-planner"
PAGES = {
    "sales": DIR / "index.html",
    "sample": DIR / "sample" / "index.html",
    "bundle": DIR / "bundle" / "index.html",
    "refund": DIR / "refund" / "index.html",
}
CSS = DIR / "assets" / "paycheck-planner.css"
JS = DIR / "assets" / "paycheck-planner.js"
GA4 = ROOT / "_includes" / "ga4.html"
FOOTER = ROOT / "_includes" / "paycheck-planner-footer.html"
SITE_FOOTER = ROOT / "_includes" / "site-footer.html"
ADDRESS = "CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794"
US_ONLY = "Available to customers located in the United States and Canada."
REFUND_PLANNER = ('Paycheck Planner is a digital product. You may request a full refund for any reason within 7 days of your purchase date. Email ruel@getcyberdadkit.com with the email address used for purchase and your order reference. Never send card details. Refunds are returned to the original payment method. No physical return is required. This policy applies only to Paycheck Planner and does not limit your statutory rights.')
REFUND_BUNDLE = ('Paycheck Planner Plus Bundle is a digital product. You may request a full refund for any reason within 7 days of your purchase date. Email ruel@getcyberdadkit.com with the email address used for purchase and your order reference. Never send card details. Refunds are returned to the original payment method. No physical return is required. This policy applies only to Paycheck Planner Plus Bundle and does not limit your statutory rights.')
REFUND_TEXT = REFUND_PLANNER + " " + REFUND_BUNDLE
HEADLINE = "Know which bills your next paycheck covers."
LAUNCH_PRICE = "$14.99 launch price through December 31, 2026, then $19.99"
EXCEL_FAQ = "No. Use the Google Sheets copy link (free Google account). The .xlsx should open in Excel 2016 or later. Both are included."
HOW_GET = ("Right after you pay, Stripe's hosted confirmation screen shows real links to your Google Sheets copy and the Excel (.xlsx) file. "
           "Plus Bundle purchases also include The January Money Reset PDF. Save those files now. If you need the links again, email ruel@getcyberdadkit.com with the email address you used at checkout.")
STRIPE_PLANNER = "https://buy.stripe.com/bJe28qaCyfyMeP33jVds40j"
STRIPE_BUNDLE = "https://buy.stripe.com/aFacN42620DS5et8Efds40k"
FORBIDDEN_PHRASES = ("exactly", "spending money", "debt-free", "receipt email", "/thanks/", "drive.google.com")

EXPECTED_KEYS = [
    "stripe_url_planner",
    "stripe_url_bundle",
    "mailerlite_form_slug",
    "mailerlite_form_id",
    "price_planner",
    "price_bundle",
    "price_currency",
]
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
    "shield kit": r"shield kit",
    "other tracker": r"\b(?:fbq|facebook pixel|hotjar|clarity\.ms|tiktok pixel|ttq|pinterest tag|linkedin insight|segment\.com|mixpanel|plausible)\b",
}
# Text and background pairs used by paycheck-planner.css (WCAG AA needs 4.5 for normal text).
CONTRAST_PAIRS = [
    ("#1d2939", "#fffdf8"), ("#475467", "#fffdf8"), ("#475467", "#f8f2e4"), ("#14304f", "#fffdf8"), ("#14304f", "#f8f2e4"),
    ("#1f4469", "#fffdf8"), ("#1f4469", "#f8f2e4"), ("#1f4469", "#e7f6ee"), ("#ffffff", "#14304f"), ("#14304f", "#f2c14e"),
    ("#14304f", "#e8ae25"), ("#0b7a4b", "#fffdf8"), ("#0b7a4b", "#e7f6ee"), ("#1d2939", "#e7f6ee"), ("#475467", "#e7f6ee"),
    ("#7a271a", "#fee4e2"),
]
failed: list[str] = []
flags: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def lum(h: str) -> float:
    h = h.lstrip("#")
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def visible_text(html: str) -> str:
    s = re.sub(r"\{%-?\s*comment.*?endcomment\s*-?%\}", " ", html, flags=re.S)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<script\b.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s)


# ---------- data file and placeholders ----------
data_text = DATA.read_text(encoding="utf-8")
values = dict(re.findall(r'^([a-z_]+):\s*"([^"]*)"\s*$', data_text, re.M))
check(list(values) == EXPECTED_KEYS, f"_data/paycheck_planner.yml has exactly the expected keys ({list(values)})")
placeholders = {k: v for k, v in values.items() if v.endswith("_TODO")}
for k, v in placeholders.items():
    flags.append(f"{k} = {v}")
    print(f"FLAG placeholder: {k} = {v}")
check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)|drive_?link|\.xlsx|\.pdf|/downloads/", data_text, re.I), "data file has no Google Drive URL and no download link")
check(not any(f.is_file() and f.suffix.lower() in (".xlsx", ".pdf", ".zip") for d in (DIR,) for f in d.rglob("*")), "no paid .xlsx, .pdf or .zip file is committed under paycheck-planner/")
for k in ("stripe_url_planner", "stripe_url_bundle"):
    v = values.get(k, "")
    check(v == f"#{k.upper()}_TODO" or re.fullmatch(r"https://buy\.stripe\.com/[A-Za-z0-9]+", v) is not None,
          f"{k} is the placeholder or one https://buy.stripe.com/ Payment Link")
check(values.get("stripe_url_planner") != values.get("stripe_url_bundle"), "planner and bundle Stripe values differ")
check(values.get("stripe_url_planner") == STRIPE_PLANNER, "stripe_url_planner matches the CoS Payment Link")
check(values.get("stripe_url_bundle") == STRIPE_BUNDLE, "stripe_url_bundle matches the CoS Payment Link")
check(values.get("price_planner") == "14.99", "planner offer price is 14.99")
check(values.get("price_bundle") == "39.00" and values.get("price_currency") == "USD", "bundle offer price is 39.00 USD")
check("receipt email" not in data_text.lower() and "receipt" not in data_text.lower(), "yml comments do not say buyers get links in a receipt email")
if LAUNCH:
    check(not placeholders, f"LAUNCH: no placeholder left ({sorted(placeholders)})")
    check(values.get("stripe_url_planner") == STRIPE_PLANNER and values.get("stripe_url_bundle") == STRIPE_BUNDLE, "LAUNCH: Payment Links are the exact CoS URLs")
    check(re.fullmatch(r"\d+", values.get("mailerlite_form_id", "")) is not None, "LAUNCH: mailerlite_form_id is numeric")
    check(values.get("mailerlite_form_slug") == "IW0v9B" and values.get("mailerlite_form_id") == "205066869153990151", "LAUNCH: MailerLite form is still IW0v9B")
elif placeholders:
    print(f"NOTE: {len(placeholders)} placeholder(s) flagged; run with --launch before merge (they must be 0 then).")
else:
    print("NOTE: no placeholders remain; --launch is the merge gate and should also pass.")

# ---------- pages ----------
html: dict[str, str] = {}
for name, path in PAGES.items():
    check(path.is_file(), f"{path.relative_to(ROOT)} exists")
    html[name] = path.read_text(encoding="utf-8") if path.is_file() else ""
css = CSS.read_text(encoding="utf-8") if CSS.is_file() else ""
js = JS.read_text(encoding="utf-8") if JS.is_file() else ""
check(bool(css) and bool(js), "planner CSS and JS exist")
footer = FOOTER.read_text(encoding="utf-8")
check(ADDRESS in footer, "site footer include carries the exact publisher line")

for name, text in html.items():
    label = f"[{name}]"
    seen = visible_text(text)
    for what, rx in BANNED.items():
        hit = re.search(rx, text if what in ("em or en dash", "guarantee", "other tracker") else seen, re.I)
        check(hit is None, f"{label} no {what}" + (f" (found {hit.group(0)!r})" if hit else ""))
    check("DRAFT" not in text, f"{label} has no DRAFT copy marker")
    for phrase in FORBIDDEN_PHRASES:
        hit = phrase.lower() in (text.lower() if phrase != "exactly" else seen.lower())
        # 'exactly' is checked in visible text so test comments and markup ids cannot trip it.
        if phrase == "exactly":
            hit = "exactly" in seen.lower()
        elif phrase == "/thanks/":
            hit = "/thanks/" in text.lower()
        else:
            hit = phrase.lower() in text.lower()
        check(not hit, f"{label} has no forbidden phrase {phrase!r}")
    check(US_ONLY in text, f"{label} has the US and Canada declaration")
    check("/refund-policy/" not in text, f"{label} does not link the sitewide /refund-policy/")
    check("{% include paycheck-planner-footer.html %}" in text and ADDRESS in footer, f"{label} uses the planner footer with the publisher line")
    check("{% include site-footer.html %}" not in text, f"{label} does not use the sitewide footer include")
    check("CyberDadKit" in text.split("<main")[0], f"{label} shows the CyberDadKit name in the header")
    check(text.count("{% include ga4.html %}") == 1, f"{label} includes the existing GA4 tag once")
    check("G-5B1LNCPB56" not in text and "gtag(" not in text, f"{label} adds no second GA config or inline gtag")
    check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)|\.xlsx\"|\.pdf\"|/downloads/", text, re.I), f"{label} has no Google Drive link and no download file link")
    check("buy.stripe.com" not in text and "checkout.stripe.com" not in text, f"{label} hardcodes no Stripe URL (reads _data)")
    check(f'<body class="pp" data-pp-page="' in text, f"{label} body carries the pp class and data-pp-page")
    check('href="/paycheck-planner/assets/paycheck-planner.css"' in text and "holiday.css" not in text and "festive" not in text,
          f"{label} uses only the planner stylesheet (no holiday or festive CSS)")
    srcs = re.findall(r"<script[^>]+src=\"([^\"]+)\"", text)
    allowed = {"/paycheck-planner/assets/paycheck-planner.js"}
    check(set(srcs) <= allowed, f"{label} loads no extra script src ({srcs})")
    if name in ("sales", "bundle"):
        check('{% include paycheck-planner-signup.html %}' in text and "mailerlite.com" not in text, f"{label} adds the optional signup include; the page source itself has no MailerLite URL")
    elif name == "sample":
        check('{% include paycheck-planner-signup.html %}' not in text and '{% include paycheck-planner-ml-embed.html %}' in text and text.count('{% include paycheck-planner-ml-embed.html %}') == 1, "[sample] keeps exactly one MailerLite embed include and has no signup include")
    else:
        check("mailerlite.com" not in text and '{% include paycheck-planner-signup.html %}' not in text, f"{label} loads no MailerLite and has no signup include")
    check(text.count("<h1") == 1, f"{label} has one h1")
    check('lang="en"' in text and 'name="viewport"' in text, f"{label} has lang and viewport")
    # internal links resolve
    for href in re.findall(r'href="(/[^"#?{]*)', text):
        p = ROOT / href.lstrip("/")
        ok = (href == "/") or p.is_file() or (p / "index.html").is_file() or (p / "index.md").is_file() or p.with_suffix(".md").is_file() or p.with_suffix(".html").is_file()
        if href.endswith("/") and href != "/":
            ok = (p / "index.html").is_file() or (p / "index.md").is_file() or p.with_suffix(".md").is_file()
        check(ok, f"{label} internal link {href} resolves")

# ---------- prices ----------
def prices(t: str) -> set[str]:
    return set(re.findall(r"\$\d[\d,]*(?:\.\d{2})?", visible_text(t)))

sales_vis = visible_text(html["sales"])
check(prices(html["sales"]) == {"$14.99", "$19.99", "$39"}, f"[sales] prices are exactly $14.99, $19.99 and $39: {sorted(prices(html['sales']))}")
check(prices(html["bundle"]) == {"$39"}, f"[bundle] only price is $39: {sorted(prices(html['bundle']))}")
check(prices(html["sample"]) == {"$14.99", "$19.99"}, f"[sample] prices are the $14.99 intro and $19.99 regular: {sorted(prices(html['sample']))}")
check(prices(html["refund"]) == set(), "[refund] shows no prices")
check(LAUNCH_PRICE + ". Prices in USD. Google Sheets and Excel. Instant download. US and Canada customers only. Nothing is shipped." in sales_vis, "[sales] hero states $14.99 launch price through December 31, 2026, then $19.99")
check(LAUNCH_PRICE in visible_text(html["sales"]) and html["sales"].count(LAUNCH_PRICE) >= 2, "[sales] launch-price line is in the hero and in What's inside")
check("Get the Paycheck Planner, $14.99" in html["sales"] and "Get the Plus Bundle, $39" in html["sales"], "[sales] both Buy labels carry their price")
check("not financial, tax or legal advice" in sales_vis.lower() and "planning tool" in sales_vis, "[sales] says planning tool, not financial advice")
check(HEADLINE in html["sales"] and html["sales"].count("Know exactly") == 0 and "whether you can afford the next thing on your list" in html["sales"], "[sales] headline is the relief line with no 'exactly'")
check("Living money" in sales_vis and "spending money" not in sales_vis.lower(), "[sales] uses Living money, not spending money")
check("NOT IN THIS PLAN" in sales_vis, "[sales] Can I Afford It answers include NOT IN THIS PLAN")
check("months to pay off" in sales_vis and "debt-free" not in sales_vis.lower(), "[sales] debt line is months to pay off, never debt-free")
check(EXCEL_FAQ in sales_vis, "[sales] Excel FAQ matches PRODUCT-PAGE wording")
check(HOW_GET in sales_vis, "[sales] How do I get it FAQ matches PRODUCT-PAGE wording")
check(REFUND_PLANNER in sales_vis and REFUND_BUNDLE in sales_vis, "[sales] Refunds FAQ matches the refund-page wording")
check("Published by CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794. Author: CyberDadKit." in sales_vis, "[sales] publisher and author line")
check("Google Sheets is a trademark of Google LLC. Excel is a trademark of Microsoft Corporation. Not affiliated with either." in sales_vis, "[sales] trademark disclaimer")
check(REFUND_PLANNER in visible_text(html["refund"]) and REFUND_BUNDLE in visible_text(html["refund"]), "[refund] has the exact PRODUCT-PAGE refund wording for both products")
check("7 days" in html["sales"] and "/paycheck-planner/refund/" in html["sales"], "[sales] links the refund policy")
check("US and Canada customers only." in visible_text(html["sample"]) and "Unsubscribe anytime. US and Canada customers only." in visible_text(html["sample"]), "[sample] mini-sheet fine print is US and Canada customers only.")
check("months to pay off" in visible_text(html["bundle"]) and "debt-free" not in visible_text(html["bundle"]).lower(), "[bundle] debt line is months to pay off")
check(HOW_GET in visible_text(html["bundle"]), "[bundle] uses the How do I get it delivery wording")
check("For personal use only. Please do not resell, rehost or share the file." in sales_vis, "[sales] use-terms line is the Proofreader wording")
check('<p id="sales-refund-planner">' in html["sales"] and '<p id="sales-refund-bundle">' in html["sales"], "[sales] planner and bundle refund paragraphs are separate p tags")
check('id="us-eligibility"' not in html["sales"] and US_ONLY in html["sales"], "[sales] drops the repeated eligibility hero line; banner, FAQ and footnote keep it")
check("The launch price is $14.99 through December 31, 2026, then $19.99. One-time payment. Prices in USD. US and Canada customers only." in visible_text(html["sample"]), "[sample] launch-price line is the Proofreader wording")
check("Add debt payoff, savings goals, sinking funds and a 2027 year view." in visible_text(html["bundle"]), "[bundle] lede adds debt, savings, sinking funds and a 2027 year view")
check("Includes everything in the Paycheck Planner" in visible_text(html["bundle"]), "[bundle] includes-everything heading is the Proofreader wording")
check("Plus everything in the Paycheck Planner" not in html["bundle"], "[bundle] no longer says Plus everything")
site_refund = (ROOT / "refund-policy" / "index.html").read_text(encoding="utf-8")
check("Paycheck Planner and Plus Bundle:" in site_refund and 'href="/paycheck-planner/refund/"' in site_refund and ">See the Paycheck Planner refund policy</a>" in site_refund and ">/paycheck-planner/refund/</a>" not in site_refund,
      "site refund-policy page links to /paycheck-planner/refund/ as See the Paycheck Planner refund policy")
check('<p class="pp-price"><span>USD</span> <strong>$39</strong> <span>one-time. US and Canada customers only.</span></p>' in html["bundle"],
      "[bundle] price note is one-time. US and Canada customers only.")
check('<span>USD</span>' in html["bundle"] and "USD" in visible_text(html["bundle"]), "[bundle] visible text includes the USD label")
footer = FOOTER.read_text(encoding="utf-8")
check("paycheck-planner/refund/" in footer and ">Refund</a>" in footer and "/refund-policy/" not in footer,
      "planner footer Refund link points at /paycheck-planner/refund/")
check("'/refund-policy/' | relative_url" in SITE_FOOTER.read_text(encoding="utf-8") and ">Refund</a>" in SITE_FOOTER.read_text(encoding="utf-8"),
      "sitewide footer include is unchanged and still points Refund at /refund-policy/")
check("{{ pp.stripe_url_planner }}" in html["sales"] and "{{ pp.stripe_url_bundle }}" in html["sales"], "[sales] Buy hrefs read _data")
check('href="/paycheck-planner/sample/"' in html["sales"], "[sales] links the free mini sheet page")
check("/paycheck-planner/assets/paycheck-planner-dashboard-600.webp" in html["sales"] and (DIR / "assets" / "paycheck-planner-dashboard-600.webp").is_file() and (DIR / "assets" / "paycheck-planner-dashboard-1000.webp").is_file(), "[sales] dashboard image exists and is used")

# ---------- page demo loop ----------
import hashlib
DEMO_ARIA = (
    "Silent loop of the Paycheck Planner with sample numbers. "
    "Settings shows usual take-home pay entered. "
    "The Paycheck Plan then shows what is left. "
    "A phone bill is added, and what is left on the second paycheck updates from $1,406.60 to $1,321.60. "
    "The second paycheck includes a $200 one-time column."
)
demo_mp4 = DIR / "assets" / "page-paycheck-planner-demo.mp4"
demo_webp = DIR / "assets" / "page-paycheck-planner-demo-poster.webp"
demo_png = DIR / "assets" / "page-paycheck-planner-demo-poster.png"
check(demo_mp4.is_file() and hashlib.sha256(demo_mp4.read_bytes()).hexdigest() == "61dff740424feec1f841cb99309c7a7386ddb79163b7fc7045a6ffe7207bf644",
      "[sales] demo MP4 matches the Video Producer sha256")
check(demo_webp.is_file() and hashlib.sha256(demo_webp.read_bytes()).hexdigest() == "27c2702a227028f2c44bdac36906670d6f0d842391d21b2780ff0dbb90ae201d",
      "[sales] demo poster webp matches the Video Producer sha256")
check(demo_png.is_file() and hashlib.sha256(demo_png.read_bytes()).hexdigest() == "a2fb0f138dfa2d98b26060fb16a8eef86c24ece8f9474a428fa21bd28b90c42f",
      "[sales] demo poster PNG matches the Video Producer sha256")
check(html["sales"].count("<video") == 1, "[sales] one video element")
check(all("<video" not in html[n] for n in ("sample", "bundle", "refund")), "sample, bundle and refund pages have no video")
vm = re.search(r"(?s)<video\b([^>]*)>(.*?)</video>", html["sales"])
va, vi = (vm.group(1), vm.group(2)) if vm else ("", "")
check(bool(vm) and 'id="pp-page-demo-video"' in va and "data-pp-video" in va, "[sales] demo video id and data-pp-video hook")
check("autoplay" in va.split() and "muted" in va.split() and "loop" in va.split() and "playsinline" in va.split() and 'preload="none"' in va,
      "[sales] video attrs: autoplay muted loop playsinline preload=none")
check('poster="/paycheck-planner/assets/page-paycheck-planner-demo-poster.webp"' in va, "[sales] poster is the webp")
check('data-src="/paycheck-planner/assets/page-paycheck-planner-demo.mp4"' in va and re.search(r"\ssrc=", va) is None, "[sales] MP4 is lazy (data-src, no src)")
check('width="1920"' in va and 'height="1080"' in va, "[sales] video width and height are 1920x1080")
check(f'aria-label="{DEMO_ARIA}"' in va, "[sales] aria-label describes the exact sheet and sample leftover change")
check(f'alt="{DEMO_ARIA}"' in vi and "page-paycheck-planner-demo-poster.webp" in vi, "[sales] poster img fallback alt matches the aria-label")
check(html["sales"].index('id="pp-buy-planner"') < html["sales"].index("paycheck-planner-dashboard-600.webp") < html["sales"].index('id="pp-page-demo-video"') < html["sales"].index('id="previews"'),
      "[sales] demo video sits below the hero image and above the preview stills")
check("IntersectionObserver" in js and "prefers-reduced-motion: reduce" in js, "planner JS lazy-loads video and honors reduced motion")
check("prefers-reduced-motion: reduce" in css and "aspect-ratio: 16 / 9" in css, "planner CSS reserves 16:9 and has a reduced-motion rule")
check("No. It is a planning tool for your own numbers. It is not financial, tax or legal advice." in visible_text(html["sales"]),
      "[sales] NFA FAQ line is unchanged")
check("Paycheck Planner is a budgeting tool, not financial advice." in visible_text(html["sales"]),
      "[sales] NFA footnote is unchanged")

# ---------- Buy buttons ----------
for name, expect in (("sales", {"planner": 4, "bundle": 1}), ("bundle", {"planner": 0, "bundle": 1}), ("sample", {"planner": 1}), ("refund", {})):
    buttons = re.findall(r"<a [^>]*data-price=[^>]*>", html[name])
    planner = [b for b in buttons if "pp.stripe_url_planner" in b]
    bundle = [b for b in buttons if "pp.stripe_url_bundle" in b]
    check(len(planner) == expect.get("planner", 0) and len(bundle) == expect.get("bundle", 0) and len(buttons) == len(planner) + len(bundle),
          f"[{name}] Buy buttons: {len(planner)} planner, {len(bundle)} bundle")
    for b in buttons:
        check(all(a in b for a in ("data-list-id=", "data-product=", "data-price=")), f"[{name}] Buy button has data-list-id, data-product, data-price")
        check(("14.99" in b) if "stripe_url_planner" in b else ("39.00" in b), f"[{name}] Buy button data-price matches its product")

# ---------- GA4 ----------
ga = GA4.read_text(encoding="utf-8")
check("a[href^=\"https://buy.stripe.com/\"]" in ga and "'buy_click'" in ga and "'begin_checkout'" in ga, "ga4.html still sends buy_click and begin_checkout on buy.stripe.com links")
check(ga.count("G-5B1LNCPB56") >= 3, "ga4.html keeps the one G-5B1LNCPB56 tag")
check("navigator.sendBeacon" in ga and "https://www.google-analytics.com/g/collect" in ga, "ga4.html sendBeacon fallback to the GA4 collect endpoint is present")
check("preventDefault" not in ga and "setTimeout" not in ga, "planner GA listener still does not delay or cancel the Stripe click")
for ev in ("view_item", "sign_up", "generate_lead"):
    check(f"'{ev}'" in js, f"planner JS sends {ev}")
# Marketing pass 1125: the click-time attribution reads ONLY the existing cdk_qa flag from localStorage to prefix qa_ (no writes).
check("'purchase'" not in js and "session_id" not in js and "localStorage.setItem" not in js and "localStorage.removeItem" not in js, "planner JS has no purchase event (hosted Stripe confirmation never returns to the site)")
check(not (ROOT / "thanks").exists() and not (DIR / "thank-you").exists(), "no thank-you or delivery pages exist")
check("sessionStorage" not in js and "document.cookie" not in js and 'a[data-pp-ref][href^="https://buy.stripe.com/"]' in js,
      "planner JS touches only Stripe Buy links (a[data-pp-ref]) at click time, no cookies or sessionStorage; internal links are never rewritten (tests/check_planner_marketing.py pins the behavior)")
check(not re.search(r"fetch\(|XMLHttpRequest|sendBeacon|document\.cookie|createElement\(.script", js), "planner JS makes no network calls of its own and sets no cookies")
check(not re.search(r"G-5B1LNCPB56|gtag\('config'|gtag\('js'", js), "planner JS adds no GA config (uses the existing tag)")
check('data-pp-page="sales"' in html["sales"] and 'data-pp-page="bundle"' in html["bundle"] and 'data-pp-page="sample"' in html["sample"], "page types wire view_item, sign_up")
check("form_id: 'planner_leads'" in js and "generate_lead" in js, "sales and bundle signup fires generate_lead with form_id planner_leads")
embed_inc = (ROOT / "_includes" / "paycheck-planner-ml-embed.html").read_text(encoding="utf-8") if (ROOT / "_includes" / "paycheck-planner-ml-embed.html").is_file() else ""
check("data-pp-form-id" in html["sample"] and '{% include paycheck-planner-ml-embed.html %}' in html["sample"],
      "[sample] has the form-id hook and the shared official MailerLite embed include")
check('class="ml-embedded"' in embed_inc and 'contains "_TODO"' in embed_inc and "pp-sample-placeholder" in embed_inc,
      "shared embed include renders the MailerLite embed, or a clearly marked placeholder while the form is unset")
check(values.get("mailerlite_form_slug") == "IW0v9B" and values.get("mailerlite_form_id") == "205066869153990151", "MailerLite form is Support's planner-sample form (slug IW0v9B, id 205066869153990151)")
check("(double opt-in)" not in html["sample"] and "confirm your address to get the sheet." in visible_text(html["sample"]) and 'id="pp-sample-fallback"' in html["sample"],
      "[sample] tells visitors to confirm their address to get the sheet, without saying double opt-in")
check(embed_inc.count("assets.mailerlite.com/js/universal.js") == 1 and "ml('account','1632878'" in embed_inc, "shared embed include reuses the site's MailerLite account loader once")
# ---------- delivery wording, homepage link, and indexing ----------
for n in ("sales", "bundle"):
    t = visible_text(html[n])
    check("hosted confirmation screen" in t and "ruel@getcyberdadkit.com" in t, f"[{n}] describes hosted confirmation and the re-send email")
for n, h in html.items():
    _t = visible_text(h).replace("Lost your files? Email ruel@getcyberdadkit.com with your receipt and we'll resend them.", "")
    check("receipt" not in _t.lower() and "receipt email" not in h.lower().replace("with your receipt and we'll resend them", ""), f"[{n}] never says a receipt or receipt email carries the links (the one Lost your files line is allowed)")
HOME = ROOT / "index.html"
home = HOME.read_text(encoding="utf-8") if HOME.is_file() else ""
# Marketing pass 1125 (CoS ruling): the old lower Friday callout (#pp-home-friday) is gone. The one planner promo on the home page is the
# self-contained include _includes/home-planner-hero.html near the top (pinned in detail by tests/check_planner_home_hero.py).
hero_inc_path = ROOT / "_includes" / "home-planner-hero.html"
hero_inc = hero_inc_path.read_text(encoding="utf-8") if hero_inc_path.is_file() else ""
check("pp-home-friday" not in home and "Paycheck Planner Friday callout" not in home and "pp-home-cta" not in home, "homepage no longer has the old lower planner callout (id=pp-home-friday)")
check(home.count("{% include home-planner-hero.html %}") == 1 and home.split("---", 2)[2].count("/paycheck-planner/") == 0, "homepage has exactly one planner promo, the include (no other /paycheck-planner/ link in index.html)")
check(HEADLINE in hero_inc and "Google Sheets and Excel" in hero_inc and "US and Canada customers only" in hero_inc and "US customers only." not in hero_inc, "homepage planner block uses the relief headline and is US and Canada customers only")
check("Find it Friday" not in home, "homepage no longer says Find it Friday")
check("holiday.css" not in hero_inc and "festive" not in hero_inc, "homepage planner block does not use holiday or festive styles")
check("#14304f" in hero_inc and "#0b7a4b" in hero_inc and "#fffdf8" in hero_inc and "#f2c14e" in hero_inc, "homepage planner block uses navy, green, warm white and gold")
check("\u2014" not in hero_inc and "\u2013" not in hero_inc and "guarantee" not in hero_inc.lower() and "receipt" not in hero_inc.lower(), "homepage planner block has no dashes, guarantee or receipt wording")
check('id="holiday-picks"' in home and 'id="year-round"' in home, "home keeps the year-round and Holiday picks sections")
check(contrast("#0b7a4b", "#fffdf8") >= 4.5 and contrast("#14304f", "#f2c14e") >= 4.5 and contrast("#1d2939", "#fffdf8") >= 4.5, "homepage planner block text and button colors meet WCAG AA")
for name in ("sales", "sample", "bundle", "refund"):
    check("noindex" not in html[name] and "sitemap: true" in html[name], f"[{name}] is indexable and in the sitemap")
check('rel="canonical"' in html["sales"] and 'href="https://getcyberdadkit.com/paycheck-planner/"' in html["sales"], "[sales] canonical is the live URL")

# ---------- design: calm palette, scoped to planner pages ----------
selectors = [s.strip() for blk in re.findall(r"([^{}]+)\{", re.sub(r"/\*.*?\*/", "", css, flags=re.S)) for s in blk.split(",") if s.strip() and not s.strip().startswith("@media")]
unscoped = [s for s in selectors if not re.match(r"^(?:body\.pp|\.pp)", s)]
check(not unscoped, f"every CSS selector is scoped to body.pp or .pp ({unscoped[:3]})")
check(not re.search(r"@import|url\(", css), "planner CSS imports nothing and loads no images or fonts")
for fg, bg in CONTRAST_PAIRS:
    check(contrast(fg, bg) >= 4.5, f"contrast {fg} on {bg} is {contrast(fg, bg):.2f} (AA needs 4.5)")
check(contrast("#14304f", "#f2c14e") >= 4.5 and "--pp-gold: #f2c14e" in css and "--pp-navy: #14304f" in css, "gold Buy button uses navy text on soft gold")

# ---------- scope: only planner files changed ----------
# Enforce the allowlist only when a Paycheck Planner file is in the diff, so
# later PRs that do not touch paycheck-planner/ still pass this test.
try:
    base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    changed = subprocess.run(["git", "diff", "--name-only", base], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    pay_names = {
        "index.html",
        "refund-policy/index.html",
        "_data/paycheck_planner.yml",
        "_includes/paycheck-planner-footer.html",
        "_includes/paycheck-planner-signup.html",
        "_includes/paycheck-planner-ml-embed.html",
        "tests/check_paycheck_planner.py",
        "tests/check_planner_guides.py",
        "tests/check_planner_signup.py",
        "tests/check_planner_marketing.py",
        "tests/check_planner_marketing_browser.py",
        "_includes/ga4.html",
        "tests/check_copy_fixes.py",
        "tests/check_home_sections.py",
        "_includes/home-planner-hero.html",
        "tests/check_planner_home_hero.py",
        "tests/check_holiday_storefront.py",
        "tests/check_planner_seo.py",
        "tests/check_no_dashes.py",
        "tests/check_hero_outcome.py",
        # M-S65 sign-off pack publishes refund/FAQ pages in the same commit as the planner refund sentence.
        "faq/index.html",
        "support/index.html",
        "contact.md",
        "sites/refund/index.html",
        "sites/index.html",
        "screen-free/refund/index.html",
    }
    # Product files only. A later PR that edits this test, or the shared
    # homepage, must not retrigger the paycheck-only allowlist.
    pay_touched = any(
        f.startswith("paycheck-planner/")
        or f.startswith("_includes/paycheck-planner-")
        or f == "_data/paycheck_planner.yml"
        for f in changed + untracked
    )
    if pay_touched:
        # Checkout audit 1127: planner/index.html is the /planner/ short path that redirects to /paycheck-planner/.
        # PR #1070 also edits tests/check_home_sections.py (holiday cards). Allow it so a combined merge does not fail this scope check.
        stray = [f for f in changed + untracked if not (f.startswith("paycheck-planner/") or f.startswith("guides/") or f in pay_names or f == "planner/index.html" or f.startswith("tests/__pycache__/"))]
        check(not stray, f"change touches only planner files ({stray[:5]})")
    else:
        print("skip scope check (no paycheck-planner files in the diff)")
except Exception as exc:  # shallow clone or no origin/main
    print(f"skip scope check ({exc.__class__.__name__})")

if failed:
    print(f"FAILED {len(failed)} check(s); {len(flags)} placeholder flag(s)")
    sys.exit(1)
print(f"ALL PAYCHECK PLANNER CHECKS PASSED ({len(flags)} placeholder flag(s)" + ("; --launch gate passed)" if not flags else "; run with --launch before merge)"))
