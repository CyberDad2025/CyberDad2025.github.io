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
FOOTER = ROOT / "_includes" / "site-footer.html"
ADDRESS = "CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794"
US_ONLY = "Available only to customers located in the United States."
REFUND_TEXT = ("Paycheck Planner and Paycheck Planner Plus Bundle are digital products. You may request a full refund for any reason "
               "within 7 days of your purchase date. Email ruel@getcyberdadkit.com with the email address used for purchase and your "
               "order reference. Never send card details. Refunds are returned to the original payment method. No physical return is required.")
EXPECTED_KEYS = ["stripe_url_planner", "stripe_url_bundle", "mailerlite_form_slug", "mailerlite_form_id"]
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
if LAUNCH:
    check(not placeholders, f"LAUNCH: no placeholder left ({sorted(placeholders)})")
    for k in ("stripe_url_planner", "stripe_url_bundle"):
        check(re.fullmatch(r"https://buy\.stripe\.com/[A-Za-z0-9]+", values.get(k, "")) is not None, f"LAUNCH: {k} is a real Payment Link")
    check(re.fullmatch(r"\d+", values.get("mailerlite_form_id", "")) is not None, "LAUNCH: mailerlite_form_id is numeric")
else:
    print(f"NOTE: {len(placeholders)} placeholder(s) flagged; run with --launch before merge (they must be 0 then).")

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
    check(US_ONLY in text, f"{label} has the US-only declaration")
    check("{% include site-footer.html %}" in text and ADDRESS in footer, f"{label} uses the site footer with the publisher line")
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
    check("mailerlite.com" not in text or name == "sample", f"{label} loads MailerLite only on the sample page")
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
check("Intro price. Regular $19.99. Google Sheets and Excel. Instant download. US only." in sales_vis, "[sales] states intro and regular price under the button")
check("Get the Paycheck Planner, $14.99" in html["sales"] and "Get the Plus Bundle, $39" in html["sales"], "[sales] both Buy labels carry their price")
check("not financial, tax or legal advice" in sales_vis.lower() and "planning tool" in sales_vis, "[sales] says planning tool, not financial advice")
check("Know exactly which bills your next paycheck covers." in html["sales"] and "whether you can afford the next thing on your list" in html["sales"], "[sales] leads with the relief line")
check("Published by CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794. Author: CyberDadKit." in sales_vis, "[sales] publisher and author line")
check("Google Sheets is a trademark of Google LLC. Excel is a trademark of Microsoft Corporation. Not affiliated with either." in sales_vis, "[sales] trademark disclaimer")
check(REFUND_TEXT in visible_text(html["refund"]), "[refund] has the exact 7-day refund wording")
check("7 days" in html["sales"] and "/paycheck-planner/refund/" in html["sales"], "[sales] links the refund policy")
check("{{ pp.stripe_url_planner }}" in html["sales"] and "{{ pp.stripe_url_bundle }}" in html["sales"], "[sales] Buy hrefs read _data")
check('href="/paycheck-planner/sample/"' in html["sales"], "[sales] links the free mini sheet page")
check("/paycheck-planner/assets/paycheck-planner-dashboard-600.webp" in html["sales"] and (DIR / "assets" / "paycheck-planner-dashboard-600.webp").is_file() and (DIR / "assets" / "paycheck-planner-dashboard-1000.webp").is_file(), "[sales] dashboard image exists and is used")

# ---------- Buy buttons ----------
for name, expect in (("sales", {"planner": 1, "bundle": 1}), ("bundle", {"planner": 0, "bundle": 1}), ("sample", {}), ("refund", {})):
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
for ev in ("view_item", "sign_up"):
    check(f"'{ev}'" in js, f"planner JS sends {ev}")
check("'purchase'" not in js and "session_id" not in js and "localStorage" not in js, "planner JS has no purchase event (hosted Stripe confirmation never returns to the site)")
check(not (ROOT / "thanks").exists() and not (DIR / "thank-you").exists(), "no thank-you or delivery pages exist")
check("utm_source" in js and "utm_campaign" in js and "sessionStorage" in js, "planner JS keeps utm_* on internal links")
check(not re.search(r"fetch\(|XMLHttpRequest|sendBeacon|document\.cookie|createElement\(.script", js), "planner JS makes no network calls of its own and sets no cookies")
check(not re.search(r"G-5B1LNCPB56|gtag\('config'|gtag\('js'", js), "planner JS adds no GA config (uses the existing tag)")
check('data-pp-page="sales"' in html["sales"] and 'data-pp-page="bundle"' in html["bundle"] and 'data-pp-page="sample"' in html["sample"], "page types wire view_item, sign_up")
check("data-pp-form-id" in html["sample"] and 'class="ml-embedded"' in html["sample"] and 'contains "_TODO"' in html["sample"] and "pp-sample-placeholder" in html["sample"],
      "[sample] renders the MailerLite embed, or a clearly marked placeholder while the form is unset")
check(values.get("mailerlite_form_slug") == "IW0v9B" and values.get("mailerlite_form_id") == "205066869153990151", "MailerLite form is Support's planner-sample form (slug IW0v9B, id 205066869153990151)")
check("double opt-in" in visible_text(html["sample"]) and "confirm your address" in visible_text(html["sample"]) and 'id="pp-sample-fallback"' in html["sample"], "[sample] tells visitors to confirm their email (double opt-in) and has a fallback line")
check(html["sample"].count("assets.mailerlite.com/js/universal.js") == 1 and "ml('account','1632878'" in html["sample"], "[sample] reuses the site's MailerLite account loader once")
# ---------- delivery wording and indexing ----------
for n in ("sales", "bundle"):
    t = visible_text(html[n])
    check("download links appear on the confirmation screen right after payment" in t.lower().replace("your download links", "download links") or "Your download links appear on the confirmation screen right after payment" in t, f"[{n}] says the download links appear on the confirmation screen right after payment")
    check("ruel@getcyberdadkit.com" in t, f"[{n}] gives the email for a re-send")
for n, h in html.items():
    check("receipt" not in visible_text(h).lower(), f"[{n}] never says a receipt carries the links")
check("with the email address you used at checkout" in visible_text(html["sales"]), "[sales] lost-download line matches the Screen-Free wording")
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
try:
    base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    changed = subprocess.run(["git", "diff", "--name-only", base], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    stray = [f for f in changed + untracked if not (f.startswith("paycheck-planner/") or f in ("_data/paycheck_planner.yml", "tests/check_paycheck_planner.py", "tests/check_copy_fixes.py") or f.startswith("tests/__pycache__/"))]
    check(not stray, f"change touches only planner files ({stray[:5]})")
except Exception as exc:  # shallow clone or no origin/main
    print(f"skip scope check ({exc.__class__.__name__})")

if failed:
    print(f"FAILED {len(failed)} check(s); {len(flags)} placeholder flag(s)")
    sys.exit(1)
print(f"ALL PAYCHECK PLANNER CHECKS PASSED ({len(flags)} placeholder flag(s); run with --launch before merge)")
