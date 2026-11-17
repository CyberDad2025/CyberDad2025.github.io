#!/usr/bin/env python3
"""One-page holiday shop at /holiday/ (feat/holiday-one-page-1117).

Hero is the Holiday Host Kit with three real preview pages and one primary
Buy button, then Gather & Play as the smaller option, then five single
printables. Every Buy href is the existing Stripe Payment Link for that
product. Old product URLs redirect to card anchors and keep the query string.

Run: python3 tests/check_holiday_one_page.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "holiday" / "index.html"

# card anchor -> (button id, Stripe link, price string on the card)
CARDS = {
    "host-kit": ("host-kit-checkout-holiday", "https://buy.stripe.com/28EbJ07qmaes36l7Abds40f", "$17.99"),
    "gather-and-play": ("holiday-checkout", "https://buy.stripe.com/9B67sK4ea4U8dKZ07Jds405", "$7.99"),
    "trivia": ("trivia-checkout-holiday", "https://buy.stripe.com/bJecN4aCyfyM4apbQrds406", "$5.99"),
    "table-set": ("table-set-checkout-holiday", "https://buy.stripe.com/dRm28q9yu2M08qFaMnds40e", "$4.99"),
    "host-planner": ("host-planner-checkout-holiday", "https://buy.stripe.com/9B69ASdOK1HWayNdYzds40b", "$4.99"),
    "kids-table": ("kids-checkout-holiday", "https://buy.stripe.com/6oU7sK7qm2M05et3jVds40c", "$5.99"),
    "travel-adventure": ("travel-adventure-checkout-holiday", "https://buy.stripe.com/00waEW4ea3Q4eP3f2Dds40g", "$4.99"),
}
REMOVED_LINKS = (
    "https://buy.stripe.com/14A5kC7qmdqEfT78Efds407",  # Trivia + Gather & Play bundle
    "https://buy.stripe.com/4gM9ASeSO72g9uJbQrds40d",  # Kids' Table + Gather & Play bundle
    "https://buy.stripe.com/fZu00i9yu0DS22h1bNds408",  # journal US Letter
    "https://buy.stripe.com/4gM6oGh0WfyM0Yd6w7ds40a",  # journal half-letter
)
PREVIEWS = (
    "/holiday/assets/previews/CyberDadKit-preview-page-09.png",
    "/holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-05.png",
    "/holiday/assets/host-planner/previews/CyberDadKit-Host-Planner-preview-page-03.png",
)
# old URL (repo file) -> expected JS hash expression, meta refresh target
REDIRECTS = {
    "holiday/travel-adventure/index.html": ('var h = "#travel-adventure";', "/holiday/#travel-adventure"),
    "holiday/host-kit/index.html": ('var h = "#host-kit";', "/holiday/#host-kit"),
    "holiday/host-planner/index.html": ('var h = "#host-planner";', "/holiday/#host-planner"),
    "holiday/kids-table/index.html": ('var h = "#kids-table";', "/holiday/#kids-table"),
    "holiday/table-set/index.html": ('var h = "#table-set";', "/holiday/#table-set"),
    "holiday/trivia/index.html": ('var h = "#trivia";', "/holiday/#trivia"),
    "holiday/sample/index.html": ('var h = "#travel-adventure";', "/holiday/#travel-adventure"),
    "holiday/trivia/sample/index.html": ('var h = "#travel-adventure";', "/holiday/#travel-adventure"),
    "shop/index.html": ('var h = window.location.hash || "";', "/holiday/"),
}
KEEP_UNCHANGED = (
    "journal/2027/index.html",
    "holiday/refund/index.html",
    "holiday/host-kit/refund/index.html",
    "holiday/host-planner/refund/index.html",
    "holiday/kids-table/refund/index.html",
    "holiday/table-set/refund/index.html",
    "holiday/travel-adventure/refund/index.html",
    "holiday/trivia/refund/index.html",
)
BANNED = [r"\u2014", r"\u2013", r"\bguarantee", r"\bworldwide\b", r"\bCDK\b", r"\bA4\b", r"\bfamily\b",
          r"\bchildren\b", r"\bages?\b", r"\bhurry\b", r"\blimited\b", r"\blast chance\b", r"\btonight\b", r"preview\.mailerlite\.io"]


def visible(html: str) -> str:
    s = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", html, flags=re.S | re.I)
    s = re.sub(r"^---\n.*?\n---\n", "", s, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, msg: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + msg)
        if not ok:
            failed.append(msg)

    html = PAGE.read_text(encoding="utf-8")
    hrefs = re.findall(r'href="(https://buy\.stripe\.com/[^"]+)"', html)
    check(len(hrefs) == len(CARDS), f"/holiday/ has exactly {len(CARDS)} Buy links ({len(hrefs)})")
    for anchor, (bid, link, price) in CARDS.items():
        check(f'id="{anchor}"' in html, f"card #{anchor} exists")
        m = re.search(rf'<a [^>]*id="{bid}"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', html)
        check(bool(m) and m.group(1) == link, f"#{anchor} Buy button {bid} links to {link}")
        check(bool(m) and m.group(2).endswith(f"for {price} USD"), f"#{anchor} Buy label ends with 'for {price} USD' (begin_checkout value)")
        check(html.count(link) == 1, f"#{anchor} Stripe link appears once")
    for link in REMOVED_LINKS:
        check(link not in html, f"removed card link {link} is not on /holiday/")
    check(html.index('id="host-kit"') < html.index('id="gather-and-play"') < html.index('id="more"'), "order: Host Kit hero, Gather & Play, then the single printables")
    check(html.count('class="hk-buy"') == 1, "one primary Buy CTA (Host Kit)")
    check('class="gp-buy"' in html, "Gather & Play uses the secondary button style")
    check("Digital PDFs, U.S. customers, 7-day refund policy" in html, "hero fine line is present")
    check("$24.96 separately" in html, "hero shows the verified $24.96 separate-price line (7.99 + 5.99 + 4.99 + 5.99)")
    for p in PREVIEWS:
        check(html.count(f'src="{p}"') == 1 and (ROOT / p.lstrip("/")).is_file(), f"hero preview {p} exists in the repo")
    body = visible(html.split("<body", 1)[1])
    check(body.count("7 days") == 1, "refund window sentence appears once in visible text")
    check(body.count("located in the United States") == 1, "US eligibility sentence appears once in visible text")
    check("mailerlite" not in html.lower(), "no MailerLite signup on /holiday/ (form is inactive, share URL is preview-only)")
    check("2027 Bible Verse Journal" not in html, "journal card removed from /holiday/")
    check("{% include ga4.html %}" in html, "site GA4 include (buy_click + begin_checkout listener) is present")
    text = visible(html)
    for pat in BANNED:
        check(not re.search(pat, html if "mailerlite" in pat else text, re.I), f"no banned string /{pat}/ in /holiday/")
    footer = re.search(r"<footer\b.*?</footer>", html, re.S).group(0)
    check("PO Box 940061, Maitland, FL 32794" in footer and len(re.findall(r"\bFL\b", footer)) == 1, "footer has the PO Box address only")
    for rel, (js, dest) in REDIRECTS.items():
        stub = (ROOT / rel).read_text(encoding="utf-8")
        label = "/" + rel[: -len("index.html")]
        check("sitemap: false" in stub and 'content="noindex, follow"' in stub, f"{label} is noindex and out of the sitemap")
        check(js in stub, f"{label} lands on {dest}")
        check('window.location.replace("/holiday/" + window.location.search + h)' in stub, f"{label} keeps the full query string, hash last")
        check(f'content="0; url={dest}"' in stub, f"{label} meta refresh fallback goes to {dest}")
        check('rel="canonical" href="https://getcyberdadkit.com/holiday/"' in stub, f"{label} canonical is /holiday/")
        check("buy.stripe.com" not in stub, f"{label} has no Buy link")
    check('"trivia-bundle": "trivia"' in html and '"kids-table-bundle": "kids-table"' in html, "old bundle anchors land on the single-product cards")
    for name in ("kids-table", "trivia"):
        stub = (ROOT / "holiday" / name / "index.html").read_text(encoding="utf-8")
        check("#bundle" not in stub, f"/holiday/{name}/#bundle lands on #{name}")
    import subprocess
    for rel in KEEP_UNCHANGED:
        diff = subprocess.run(["git", "diff", "--quiet", "origin/main", "--", rel], cwd=ROOT).returncode
        check(diff == 0, f"{rel} is unchanged versus origin/main")
    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL ONE-PAGE HOLIDAY SHOP CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
