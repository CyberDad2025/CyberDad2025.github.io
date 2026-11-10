#!/usr/bin/env python3
"""Optional email signup on /holiday/sample/ only.

The download links stay direct. The MailerLite embed is one container,
data-form eMwTaD, with a noscript fallback. Public copy does not claim
"No email" and does not use the CDK abbreviation. The footer is the
four-line identity, and the rest of the page matches the previous body.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "holiday" / "sample" / "index.html"
MAIN = "origin/main"
LETTER = "/holiday/sample/Free-Sample-Table-Talk-Trails-US-Letter.pdf"
A4 = "/holiday/sample/Free-Sample-Table-Talk-Trails-A4.pdf"
HOSTED = "https://preview.mailerlite.io/forms/1632878/203754930937268147/share"
UNTOUCHED = (
    "holiday/index.html",
    "holiday/refund/index.html",
    "holiday/trivia/index.html",
    "holiday/trivia/sample/index.html",
    "holiday/table-set/index.html",
    "shop/index.html",
    "shield-kit/index.html",
    "assets/festive/festive.css",
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


def outside_footer(html: str) -> str:
    return re.sub(r"<footer\b.*?</footer>", "", html, count=1, flags=re.S)


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

    html = SAMPLE.read_text(encoding="utf-8")
    previous = subprocess.check_output(
        ["git", "show", f"{MAIN}:holiday/sample/index.html"],
        cwd=ROOT,
        text=True,
    )
    head, body = html.split("<body", 1)
    letter_at = html.find(f'href="{LETTER}"')
    a4_at = html.find(f'href="{A4}"')
    note_at = html.find("Each file is a single page.")
    updates_at = html.find('id="updates"')
    how_at = html.find('id="how-title"')
    ml_at = html.find("https://assets.mailerlite.com/js/universal.js")
    ga_at = html.find("{% include ga4.html %}")
    embed = re.search(r'<div class="ml-embedded" data-form="eMwTaD"></div>', html)

    check(letter_at != -1 and a4_at != -1, "sample page still has both PDF links")
    check(html.count(f'href="{LETTER}"') == 1 and html.count(f'href="{A4}"') == 1, "each sample PDF href appears once")
    check(html.count('class="ml-embedded"') == 1 and embed is not None, "one form container with data-form eMwTaD")
    check(html.count("data-form=") == 1, "data-form is the slug, not a second numeric id")
    check('data-form="203754930937268147"' not in html, "data-form is not the numeric form id")
    check("ml('enablePopups',false)" in html, "MailerLite popups stay disabled")
    check(f"<noscript>Sign up on our updates page: <a href=\"{HOSTED}\" rel=\"noopener\">hosted signup form</a>.</noscript>" in html, "noscript fallback links to the hosted signup form")
    check('href="/privacy/">Privacy policy</a>' in html, "privacy policy link is visible near the form")
    check("no email" not in html.lower(), "no 'No email' contradiction")
    check("does not ask for an address" not in html.lower(), "old address sentence is gone")
    check("The download doesn't ask for an address." in html, "download copy stays accurate")
    check("Below, you can optionally sign up for updates." in html, "optional signup is offered below the download copy")
    check("Free worldwide" in html, "free sample stays worldwide")
    check('id="updates-title">Want the next free printable?</h2>' in html, "accessible heading is outside the embed")
    check("Optional. Your download above doesn't need this." in html, "short optional intro is visible")
    check(embed is not None and "Want the next free printable?" not in embed.group(0), "embed container does not repeat the heading")
    sample_footer = footer(html)
    for line in FOOTER_LINES:
        check(sample_footer.count(line) == 1, f"sample footer has one identity line: {line}")
    check(sample_footer.count("CyberDad Kit LLC") == 1, "sample footer names the LLC once")
    check(outside_footer(html) == outside_footer(previous), "sample page outside the footer matches main")
    check(not re.search(r"\bCDK\b", visible_text(html)), "no CDK in public copy")
    check("CyberDad Kit" in visible_text(html), "public copy can say CyberDad Kit")
    check(0 < letter_at < a4_at < note_at < ga_at < updates_at < ml_at < how_at, "signup sits after the download note and before how-title")
    check("<script" not in head.lower() and "mailerlite" not in head.lower(), "no third-party script before the download links")
    check("optin_view" in html and "IntersectionObserver" in html, "optin_view fires once via IntersectionObserver")
    check('form_id: "holiday_sample_optin"' in html and "page_path: window.location.pathname" in html, "optin_view sends form_id and page_path")
    check('typeof window.gtag !== "function"' in html, "gtag is guarded and not loaded a second time")
    check("optin_submit" not in html and "optin_success" not in html and "optin_error" not in html, "submit, success, and error events are omitted because MailerLite exposes no stable ml callback")
    check("autofocus" not in re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I).lower(), "no autofocus attribute")
    check('role="dialog"' not in html and "min-height: 28rem" in html and "44px" in html and ":focus-visible" in html, "reserved height, 44px targets, visible focus, no dialog")
    check(html.count("buy.stripe.com") == previous.count("buy.stripe.com") == 2, "Stripe payment link count is unchanged")

    for rel in UNTOUCHED:
        text = (ROOT / rel).read_text(encoding="utf-8")
        check("eMwTaD" not in text and 'id="updates-title"' not in text, f"{rel} has no sample signup")
        previous_rel = subprocess.check_output(
            ["git", "show", f"{MAIN}:{rel}"],
            cwd=ROOT,
            text=True,
        )
        check(outside_footer(text) == outside_footer(previous_rel), f"{rel} outside the footer is unchanged versus main")

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL SAMPLE OPT-IN CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
