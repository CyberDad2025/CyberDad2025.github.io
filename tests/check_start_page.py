#!/usr/bin/env python3
"""Checks for the public /start/ hub.

Copy is the final START-COPY.md text, word for word. Mini Sheet is first
(a button to the existing sample page, not the signup include). Planner
is second, with the live demo, sample sheet views, 7-day refund sentence,
and an on-site Buy CTA. Buttons stay on-site, with no UTM params and no
Stripe hrefs. The $79 kit stays off this page. The page is indexable and
in the sitemap, and stays out of the main nav.

Run: python3 tests/check_start_page.py [--site BUILD_DIR]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "start" / "index.html"
SALES = ROOT / "paycheck-planner" / "index.html"
HEADER = ROOT / "_includes" / "home-header.html"
PRIVACY = ROOT / "cyberdadkit-privacy-policy.html"
BUYERS_TAG = "{% include what-buyers-say.html %}"
DEMO_SRC = 'data-src="/paycheck-planner/assets/page-paycheck-planner-demo.mp4"'
PRICE_LINE = "$14.99 through Dec 31, 2026, then $19.99"
REFUND_SENTENCE = "You may request a full refund for any reason within 7 days of your purchase date."
HEADLINE = "Paid every two weeks? See which bills each check covers."
SUPPORTING = "Most years, two months bring a third paycheck. Start here to see which bills each check covers, including those months."
MINI_HEADING = "Try it free for one month."
MINI_BODY_1 = "The Paycheck-to-Bills Mini Sheet maps up to 4 paychecks and 12 bills for one month, including bills due before your first check. See which paycheck pays which bill in about 3 minutes."
MINI_BODY_2 = "We will email the sheet and occasional money planning tips. Unsubscribe anytime. After you sign up, check your email and confirm your address to get the sheet."
MINI_BUTTON = "Get the free Mini Sheet"
MINI_UNDER = "Grab the free Mini Sheet, then plan your next paycheck before 2027 starts."
PLANNER_HEADING = "See which bills your next paycheck covers."
PLANNER_BODY = "Type your paychecks and bills once. See what each check has to pay, what is left after, and whether you can afford the next thing on your list, before you buy it."
DEMO_CAPTION = "Silent loop with sample numbers."
SAMPLE_FILE_BODY = "Sample numbers are already filled in, so you can see how it works before you type anything."
PLANNER_BUTTON = "Get the Paycheck Planner"
PLANNER_UNDER = "Prices in USD. Google Sheets and Excel. Instant download. One payment, no subscription. Digital download only. Nothing is shipped. Nothing links to your bank."
FOOTER_LINES = (
    "US and Canada customers only.",
    "A budgeting tool, not financial advice.",
    "Not tax or legal advice either.",
    "Sample numbers are made up.",
    "Digital download only. Nothing is shipped.",
)
SITE = Path(sys.argv[sys.argv.index("--site") + 1]) if "--site" in sys.argv else None

failed: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("ok   " if ok else "FAIL ") + message)
    if not ok:
        failed.append(message)


def visible_text(html: str) -> str:
    s = re.sub(r"\{%-?\s*comment.*?endcomment\s*-?%\}", " ", html, flags=re.S)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<script\b.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s)


def hrefs(html: str) -> list[str]:
    return re.findall(r"""<a\b[^>]*\bhref=["']([^"']+)["']""", html, flags=re.I)


def nav_hrefs(html: str) -> str:
    return " ".join(re.findall(r"<nav\b[^>]*>.*?</nav>", html, flags=re.S | re.I))


def main() -> int:
    check(START.is_file(), "start/index.html exists")
    check(PRIVACY.is_file(), "cyberdadkit-privacy-policy.html exists in the repo")
    text = START.read_text(encoding="utf-8") if START.is_file() else ""
    fm = re.search(r"(?s)^---\n(.*?)\n---", text)
    check(bool(fm) and re.search(r"(?m)^layout:\s*null\s*$", fm.group(1)), "start front matter has layout: null")
    check(bool(fm) and "noindex" not in fm.group(1), "start front matter has no noindex")
    check(bool(fm) and not re.search(r"(?m)^sitemap:\s*false\s*$", fm.group(1)), "start front matter does not set sitemap: false")
    check('<meta name="robots" content="noindex">' not in text, "start head has no noindex robots meta")

    check("{% include paycheck-planner-signup.html %}" not in text, "start does not embed the Mini Sheet signup include")
    check(HEADLINE in text, "start headline matches final copy")
    check(SUPPORTING in text, "start supporting line matches final copy")
    check(MINI_HEADING in text, "start Mini Sheet heading matches final copy")
    check(MINI_BODY_1 in text, "start Mini Sheet body matches the live sample sentence")
    check(MINI_BODY_2 in text, "start Mini Sheet email and confirm lines match final copy")
    check('href="/cyberdadkit-privacy-policy.html"' in text, "privacy policy link goes to /cyberdadkit-privacy-policy.html")
    check(f'id="start-get-mini-sheet" href="/paycheck-planner/sample/"' in text, "Mini Sheet button goes to /paycheck-planner/sample/")
    check(MINI_BUTTON in text, "Mini Sheet button label matches final copy")
    check(MINI_UNDER in text, "line under the Mini Sheet button matches final copy")

    check(PLANNER_HEADING in text, "planner heading matches final copy")
    check(PLANNER_BODY in text, "planner body matches final copy")
    check(DEMO_SRC in text, "start reuses the existing live planner demo video")
    check(DEMO_CAPTION in text, "demo caption matches final copy")
    check(SAMPLE_FILE_BODY in text, "sample file sentence matches final copy")
    check("paycheck-planner-dashboard-600.webp" in text, "start reuses the existing Dashboard sample view")
    check("paycheck-planner-still-1-paycheck-plan.webp" in text, "start reuses the existing Paycheck Plan sample view")
    check("paycheck-planner-still-2-bills.webp" in text, "start reuses the existing Bills sample view")
    check("still-3-sinking-funds" not in text and "still-4-savings-goals" not in text, "start does not use Plus Bundle sinking-fund or savings-goal stills")
    check(REFUND_SENTENCE in text, "start uses the 7-day refund sentence")
    check(PRICE_LINE in text, "price line is the short form of the live planner price")
    check('id="start-buy-planner" href="/paycheck-planner/"' in text, "start Buy CTA goes to /paycheck-planner/, not Stripe")
    check(PLANNER_BUTTON in text, "planner button label matches final copy")
    check(PLANNER_UNDER in text, "line under the planner button matches final copy")
    for line in FOOTER_LINES:
        check(line in text, f"footer has {line!r}")

    mini = text.find('id="start-mini-sheet"')
    planner = text.find('id="start-planner"')
    buyers = text.find(BUYERS_TAG)
    footer = text.find('id="start-footer-lines"')
    check(mini != -1 and planner != -1 and mini < planner, "Mini Sheet section comes first, then the Planner")
    demo_at = text.find(DEMO_SRC)
    sample_at = text.find(SAMPLE_FILE_BODY)
    refund_at = text.find(REFUND_SENTENCE)
    price_at = text.find(PRICE_LINE)
    buy_at = text.find('id="start-buy-planner"')
    check(
        planner < demo_at < sample_at < refund_at < price_at < buy_at,
        "planner section order is demo, sample views, refund, price, then on-site Buy",
    )
    check(BUYERS_TAG in text and buy_at < buyers < footer, "what-buyers-say sits after the planner Buy and before the required footer lines")

    for href in hrefs(text):
        check("utm_" not in href.lower(), f"start href has no UTM params ({href})")
        check("buy.stripe.com" not in href and "checkout.stripe.com" not in href, f"start href is not a Stripe checkout URL ({href})")
        check(href.startswith(("/", "#", "mailto:", "https://getcyberdadkit.com/", "{{ ")) or href.startswith("{%"), f"start href stays on-site ({href})")

    check("buy.stripe.com" not in text and "checkout.stripe.com" not in text, "start source has no Stripe checkout URL")
    check("$79" not in text and "money-reset-kit" not in text and "Money Reset Kit" not in text, "start does not mention the $79 kit")
    check("$39" not in text and "Plus Bundle" not in text, "start does not mention the $39 Plus Bundle")
    check("PLACEHOLDER" not in text, "start has no leftover PLACEHOLDER copy")
    check("DRAFT" not in text, "start has no DRAFT copy marker")
    check("\u2014" not in text and "\u2013" not in text, "start has no em or en dashes")
    check("guarantee" not in text.lower(), "start has no guarantee")
    check("a few minutes" not in text and "about 10 minutes" not in text, "start does not reuse the planner time-to-fill phrasing")
    check(text.count("about 3 minutes") == 1, "about 3 minutes appears only in the Mini Sheet body sentence")
    seen = visible_text(text)
    check(not re.search(r"\b(?:age|years old|child|children|kids?|son|daughter|family|parent|parents)\b", seen, re.I), "start visible text has no ages or family details")

    header = HEADER.read_text(encoding="utf-8") if HEADER.is_file() else ""
    check('href="/start/"' not in header and "href=\"https://getcyberdadkit.com/start/" not in header, "site home-header nav does not link to /start/")
    check('href="/start/"' not in nav_hrefs(text), "start page header nav does not link to /start/")
    sales = SALES.read_text(encoding="utf-8") if SALES.is_file() else ""
    check('href="/start/"' not in nav_hrefs(sales), "paycheck-planner header nav does not link to /start/")

    if SITE and SITE.is_dir():
        built = SITE / "start" / "index.html"
        check(built.is_file(), "built /start/ exists")
        if built.is_file():
            b = built.read_text(encoding="utf-8")
            check('<meta name="robots" content="noindex">' not in b, "built /start/ is indexable")
            check(HEADLINE in b and PRICE_LINE in b, "built /start/ has the final headline and price line")
            check('id="start-get-mini-sheet" href="/paycheck-planner/sample/"' in b, "built Mini Sheet button goes to /paycheck-planner/sample/")
            check('id="start-buy-planner" href="/paycheck-planner/"' in b, "built Buy CTA still goes to /paycheck-planner/")
            check('href="/cyberdadkit-privacy-policy.html"' in b, "built privacy policy link is /cyberdadkit-privacy-policy.html")
            stripe_hrefs = re.findall(r'<a [^>]*href="(https://(?:buy|checkout)\.stripe\.com/[^"]*)"', b)
            check(not stripe_hrefs, f"built /start/ has no Stripe checkout href ({stripe_hrefs})")
            utm_hrefs = [h for h in hrefs(b) if "utm_" in h.lower()]
            check(not utm_hrefs, f"built /start/ hrefs have no UTM params ({utm_hrefs})")
            check("$79" not in b and "Money Reset Kit" not in b, "built /start/ does not mention the $79 kit")
            check("$39" not in b and "Plus Bundle" not in b, "built /start/ does not mention the $39 Plus Bundle")
            check("What buyers say" not in b and 'id="what-buyers-say"' not in b, "built /start/ buyers-say block is omitted while data is empty")
            check("PLACEHOLDER" not in b, "built /start/ has no leftover PLACEHOLDER copy")
            check("{% include paycheck-planner-signup.html %}" not in b and 'data-form="IW0v9B"' not in b, "built /start/ does not embed the Mini Sheet signup form")
        sm = SITE / "sitemap.xml"
        if sm.is_file():
            sitemap = sm.read_text(encoding="utf-8")
            check("https://getcyberdadkit.com/start/" in sitemap or "https://getcyberdadkit.com/start/index.html" in sitemap, "built sitemap includes /start/")
            check("money-reset-kit" not in sitemap, "built sitemap omits hosted Money Reset Kit files")
        else:
            print("note  sitemap.xml not in --site dir")
        kit_dir = SITE / "assets" / "paycheck-planner" / "money-reset-kit"
        check(not any(kit_dir.glob("*.pdf")), "built kit folder has no PDFs")
        check(not any(kit_dir.glob("*.md")), "built kit folder has no markdown files")
        check(not any(kit_dir.glob("*.html")), "built kit folder has no HTML sibling pages")
    else:
        print("note  pass --site DIR after a jekyll build to assert the public /start/ page")

    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL START PAGE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
