#!/usr/bin/env python3
"""One-page holiday shop at /holiday/ (feat/holiday-one-page-1117).

Hero is the Holiday Host Kit with three real preview pages and one primary
Buy button, then Gather & Play as the smaller option, then five single
printables. Every Buy href is the existing Stripe Payment Link for that
product. Old product URLs redirect to card anchors and keep the query string.

Run: python3 tests/check_holiday_one_page.py
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
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
# Hero previews: downscaled WebP copies of these existing post-#1045 preview pages.
PREVIEWS = {
    "/holiday/assets/shop/gather-and-play-page-09-360.webp": "holiday/assets/previews/CyberDadKit-preview-page-09.png",
    "/holiday/assets/shop/christmas-trivia-page-05-360.webp": "holiday/assets/trivia/previews/CyberDadKit-Christmas-Trivia-preview-page-05.png",
    "/holiday/assets/shop/host-planner-page-03-360.webp": "holiday/assets/host-planner/previews/CyberDadKit-Host-Planner-preview-page-03.png",
}
# fix/trivia-sample-og-badge-1118: the #trivia card links the two free sample PDFs
# (the /holiday/trivia/sample/ redirect lands on this card). US Letter only; the A4 file stays on disk, unlinked.
TRIVIA_SAMPLES = {
    "/holiday/trivia/sample/CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-US-Letter.pdf": ("sample-link-trivia-card-letter", "US Letter PDF"),
}
TRIVIA_SAMPLE_A4 = "/holiday/trivia/sample/CyberDadKit-Christmas-Trivia-Night-FREE-SAMPLE-A4.pdf"
SAMPLE_LINE_RE = re.compile(r'<p class="mp-sample">.*?</p>', re.S)
# Every downscaled image: source file and its sha256 at the time of the copy, and the output size.
IMAGES = json.loads((ROOT / "tests" / "holiday_one_page_images.json").read_text(encoding="utf-8"))
REFUND_LINKS = ("/holiday/host-kit/refund/", "/holiday/refund/", "/holiday/trivia/refund/", "/holiday/table-set/refund/",
                "/holiday/host-planner/refund/", "/holiday/kids-table/refund/", "/holiday/travel-adventure/refund/")
# old URL (repo file) -> expected JS hash expression, meta refresh target
REDIRECTS = {
    "holiday/host-kit/index.html": ('var h = "#host-kit";', "/holiday/#host-kit"),
    "holiday/host-planner/index.html": ('var h = "#host-planner";', "/holiday/#host-planner"),
    "holiday/kids-table/index.html": ('var h = "#kids-table";', "/holiday/#kids-table"),
    "holiday/table-set/index.html": ('var h = "#table-set";', "/holiday/#table-set"),
    "holiday/trivia/index.html": ('var h = "#trivia";', "/holiday/#trivia"),
    "holiday/sample/index.html": ('var h = "#gather-and-play";', "/holiday/#gather-and-play"),
    "holiday/trivia/sample/index.html": ('var h = "#trivia";', "/holiday/#trivia"),
    "shop/index.html": ('var h = window.location.hash || "";', "/holiday/"),
}
# The journal storefront may swap the hero picture to the real page-1 cover.
# Caption, alt, prices, Stripe hrefs, and all other markup stay locked to main.
JOURNAL_PAGE = "journal/2027/index.html"

# qa-flag-samples-1117: the ?cdk_qa=1 internal-traffic flag replaced the one GA4
# config line with a small block. Fold it back so lock-to-main comparisons only
# see the edits they were written to allow.
QA_FLAG_BLOCK = (
    "      (function () {\n"
    "        var qa = false;\n"
    "        try { var p = new URLSearchParams(location.search).get('cdk_qa'); if (p === '1') localStorage.setItem('cdk_qa', '1'); else if (p === '0') localStorage.removeItem('cdk_qa'); qa = localStorage.getItem('cdk_qa') === '1'; } catch (err) {}\n"
    "        if (qa) { gtag('config', 'G-5B1LNCPB56', { traffic_type: 'internal' }); } else { gtag('config', 'G-5B1LNCPB56'); }\n"
    "      })();\n"
)


def without_qa_flag(html: str) -> str:
    return html.replace(QA_FLAG_BLOCK, "      gtag('config', 'G-5B1LNCPB56');\n")
JOURNAL_HERO_PICTURE_RE = re.compile(r'<picture class="festive-cover">.*?</picture>', re.S)

def journal_without_hero_picture(html: str) -> str:
    return JOURNAL_HERO_PICTURE_RE.sub('<picture class="festive-cover">HERO</picture>', html)

# Refund pages: only product-link hrefs may change (to /holiday/#card); the text stays the same,
# except holiday/kids-table/refund/index.html, which drops the old $11.99 bundle offer wording.
REFUND_PAGES = (
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
    for p, src in PREVIEWS.items():
        check(html.count(f'src="{p}"') == 1 and (ROOT / p.lstrip("/")).is_file() and (ROOT / src).is_file(), f"hero preview {p} (from {src}) is on the page and exists")
    used = set(re.findall(r'/holiday/assets/shop/[a-z0-9-]+\.webp', html))
    check(used == {"/" + k for k in IMAGES}, f"/holiday/ uses exactly the {len(IMAGES)} listed downscaled images")
    for rel, meta in IMAGES.items():
        path = ROOT / rel
        src = ROOT / meta["source"]
        ok = path.is_file() and src.is_file() and hashlib.sha256(src.read_bytes()).hexdigest() == meta["source_sha256"]
        if ok:
            data = path.read_bytes()
            ok = data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) < 80000
        check(ok, f"{rel} exists, is WebP under 80 KB, and its source {meta['source']} is unchanged")
    imgs = re.findall(r"<img [^>]*>", html)
    check(len(imgs) >= 4 and all('loading="lazy"' not in i for i in imgs[:4]), "hero cover and 3 previews load eagerly")
    check(all('loading="lazy"' in i for i in imgs[4:]), "every image below the hero is lazy-loaded")
    check(all("width=" in i and "height=" in i for i in imgs), "every image has width and height")
    for link in REFUND_LINKS:
        check(f'href="{link}"' in html, f"/holiday/ links the refund page {link}")
    for phrase in ("Available only to customers located in the United States.", "Stripe checkout displays CyberDad Kit.",
                   "After a successful payment, Stripe's confirmation screen shows the download link.",
                   "with your checkout email address", "does not promise automatic processing", "CyberDad Kit LLC"):
        check(phrase in html, f"/holiday/ keeps the checkout/refund wording: {phrase}")
    for anchor, (bid, link, price) in CARDS.items():
        check(f'id="{bid}" data-list-id="holiday-{anchor}"' in html, f"#{anchor} Buy button sends item_list_id holiday-{anchor}")
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    ldj = json.loads(ld.group(1)) if ld else {}
    check(ldj.get("offers", {}).get("price") == "17.99" and ldj.get("name") == "Holiday Host Kit", "JSON-LD is the Host Kit at 17.99 USD")
    ga = (ROOT / "_includes" / "ga4.html").read_text(encoding="utf-8")
    check("a.getAttribute('data-list-id') || location.pathname" in ga, "ga4.html uses data-list-id for item_list_id, else the page path")
    body = visible(html.split("<body", 1)[1])
    check(body.count("7 days") == 1, "refund window sentence appears once in visible text")
    check(body.count("located in the United States") == 1, "US eligibility sentence appears once in visible text")
    check("mailerlite" not in html.lower(), "no MailerLite signup on /holiday/ (form is inactive, share URL is preview-only)")
    check("2027 Bible Verse Journal" not in html, "journal card removed from /holiday/")
    check("{% include ga4.html %}" in html, "site GA4 include (buy_click + begin_checkout listener) is present")
    text = visible(html)
    # feat/planner-2027: the product name "2027 Family Planner" is the only allowed use of "family" on /holiday/.
    text_np = text.replace("2027 Family Planner", "")
    for pat in BANNED:
        check(not re.search(pat, html if "mailerlite" in pat else text_np, re.I), f"no banned string /{pat}/ in /holiday/")
    card = re.search(r'<article class="mp-card" id="trivia".*?</article>', html, re.S)
    card = card.group(0) if card else ""
    samples = SAMPLE_LINE_RE.findall(html)
    check(len(samples) == 1 and samples[0] in card, "exactly one sample line on /holiday/, inside the #trivia card")
    check(card.find('id="trivia-checkout-holiday"') < card.find('class="mp-sample"'), "trivia sample line sits under the Buy button")
    for href, (cta, label) in TRIVIA_SAMPLES.items():
        check(f'<a href="{href}" data-cta="{cta}">{label}</a>' in card, f"#trivia links {label} with data-cta {cta}")
        check(html.count(href) == 1 and (ROOT / href.lstrip("/")).is_file(), f"{href} appears once and the file exists")
    check(bool(samples) and "buy.stripe.com" not in samples[0], "sample line has no Stripe link (no buy_click / begin_checkout)")
    check(bool(samples) and visible(samples[0]).strip() == "Free sample, Round 1: US Letter PDF", "sample line reads exactly 'Free sample, Round 1: US Letter PDF'")
    check(TRIVIA_SAMPLE_A4 not in html and (ROOT / TRIVIA_SAMPLE_A4.lstrip("/")).is_file(), "A4 sample PDF stays on disk and is not linked from /holiday/")
    check(".mp-thumb { position: relative; align-self: start;" in html, ".mp-thumb is align-self: start (badge stays on the cover)")
    tstub = (ROOT / "holiday" / "trivia" / "sample" / "index.html").read_text(encoding="utf-8")
    for tag in ('property="og:title"', 'property="og:description"', 'property="og:image" content="https://getcyberdadkit.com/assets/share/holiday-christmas-trivia.png"',
                'name="twitter:card" content="summary_large_image"', 'name="twitter:image"', 'property="og:url" content="https://getcyberdadkit.com/holiday/trivia/sample/"'):
        check(tag in tstub, f"/holiday/trivia/sample/ has {tag.split(' content')[0]}")
    for pat in (r"\u2014", r"\u2013", r"\bguarantee", r"\bCDK\b"):
        check(not re.search(pat, tstub, re.I), f"/holiday/trivia/sample/ has no /{pat}/")
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
    journal_old = subprocess.run(["git", "show", f"origin/main:{JOURNAL_PAGE}"], cwd=ROOT, capture_output=True, text=True).stdout
    journal_new = without_qa_flag((ROOT / JOURNAL_PAGE).read_text(encoding="utf-8"))
    check(journal_without_hero_picture(without_qa_flag(journal_old)) == journal_without_hero_picture(journal_new),
          "journal/2027/index.html only changes the hero picture")
    check("/journal/2027/assets/CyberDadKit-2027-Journal-preview-page-01.webp" in journal_new,
          "journal hero prefers the real page-1 cover webp")
    check('src="/journal/2027/assets/CyberDadKit-2027-Journal-preview-page-01.png"' in journal_new,
          "journal hero PNG is the real page-1 cover")
    check('alt="Cover of the 2027 Verse of the Day Journal, with Psalm 119:105 from the World English Bible."' in journal_new,
          "journal hero alt stays accurate")
    check("<strong>Cover · page 1 of 373</strong>" in journal_new,
          "journal caption still names page 1 of 373")
    check("bible-verse-journal-2027-cover" not in journal_new,
          "journal hero is not the festive marketing graphic")
    for rel in REFUND_PAGES:
        old = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=ROOT, capture_output=True, text=True).stdout
        new = without_qa_flag((ROOT / rel).read_text(encoding="utf-8"))
        norm = lambda t: re.sub(r'href="/(holiday/(travel-adventure|host-kit|host-planner|kids-table|table-set|trivia)/|holiday/#[a-z-]+|shop/|holiday/)"', 'href="X"', t)
        if rel == "holiday/kids-table/refund/index.html":
            check("If you bought the Kids' Table Activity Pack together with Gather &amp; Play, this 7-day policy covers that whole purchase." in new, f"{rel}: bundle sentence no longer cites the $11.99 offer")
            check("$11.99" not in new, f"{rel}: $11.99 is gone")
            check('id="kids-refund-wording"' in new and "within 7 days of your purchase date" in new, f"{rel}: KT purchase refund wording remains")
        else:
            check(norm(without_qa_flag(old)) == norm(new), f"{rel}: only product-link hrefs changed; refund text is unchanged")
        if rel == "holiday/travel-adventure/refund/index.html":
            check('href="/holiday/travel-adventure/"' in new and 'href="/holiday/#travel-adventure"' not in new, f"{rel}: product links go to the indexable Travel Adventure page")
        else:
            check(not re.search(r'href="/holiday/(travel-adventure|host-kit|host-planner|kids-table|table-set|trivia)/"', new), f"{rel}: product links go straight to /holiday/#card")
    for rel in ("_includes/home-header.html", "_includes/ta-crosslink.html"):
        inc = (ROOT / rel).read_text(encoding="utf-8")
        check(not re.search(r'href="/(shop/|holiday/(travel-adventure|host-kit|host-planner|kids-table|table-set|trivia)/)"', inc), f"{rel} links straight to /holiday/ cards (no redirect hop)")
    gp = (ROOT / "holiday/gather-and-play/index.html").read_text(encoding="utf-8")
    check("sitemap: true" in gp and "sitemap: false" not in gp and "noindex" not in gp, "Gather & Play page is not a noindex stub")
    check('rel="canonical" href="https://getcyberdadkit.com/holiday/gather-and-play/"' in gp, "Gather & Play canonical is the product URL")
    check("{% include ga4.html %}" in gp, "Gather & Play page includes ga4.html")
    check('href="https://buy.stripe.com/9B67sK4ea4U8dKZ07Jds405"' in gp, "Gather & Play page reuses the live Gather & Play Stripe link")
    check('href="/holiday/gather-and-play/"' in html, "/holiday/ card links /holiday/gather-and-play/")
    check("<title>Printable Office Party Games | Gather &amp; Play</title>" in gp and 'content="Hosting an office holiday party? Gather &amp; Play offers printable group activities. Instant digital download for US customers. Print before guests arrive."' in gp and "<h1 id=\"product-title\">Turn an awkward office Christmas party into an afternoon of laughter and friendly competition.</h1>" in gp, "Gather & Play title, meta and H1 match the Growth handoff")
    check("<h3>Color and low-ink</h3>" in gp and "US Letter color and US Letter low-ink PDFs. Each holds the same 12 games." in gp, "Gather & Play facts card names the two US Letter PDFs")
    check("Hosting a work party? You may print copies for internal office use." in gp, "Gather & Play states internal office printing")
    check("The seller is CyberDad Kit LLC (CyberDadKit)." in gp and "does not promise automatic processing" not in gp, "Gather & Play seller and processing lines match the Watchdog polish")
    check(not re.search(r"\bA4\b", gp), "Gather & Play page has no A4")
    ta = (ROOT / "holiday/travel-adventure/index.html").read_text(encoding="utf-8")
    check("sitemap: true" in ta and "sitemap: false" not in ta and "noindex" not in ta, "Travel Adventure page is not a noindex stub")
    check('rel="canonical" href="https://getcyberdadkit.com/holiday/travel-adventure/"' in ta, "Travel Adventure canonical is the product URL")
    check("window.location.replace" not in ta and "http-equiv=\"refresh\"" not in ta, "Travel Adventure page does not redirect")
    check("{% include ga4.html %}" in ta, "Travel Adventure page includes ga4.html")
    check('href="https://buy.stripe.com/00waEW4ea3Q4eP3f2Dds40g"' in ta, "Travel Adventure page reuses the live Travel Adventure Stripe link")
    check('href="/holiday/travel-adventure/"' in html, "/holiday/ card links /holiday/travel-adventure/")
    check("<title>Thanksgiving Road Trip Printables | Travel Adventure</title>" in ta and 'content="Heading out for Thanksgiving? Travel Adventure is a printable road-trip activity pack. Instant digital download for US customers. Print it before you leave."' in ta and "<h1 id=\"product-title\">Printable Activities for Your Thanksgiving Road Trip</h1>" in ta, "Travel Adventure title, meta and H1 use the Growth handoff with activity pack wording")
    check("The seller is CyberDad Kit LLC (CyberDadKit)." in ta and "does not promise automatic processing" not in ta, "Travel Adventure seller and processing lines match the Proofreader polish")
    check("The cover is above. These are pages 2 and 4, the word search and the Fall Trail Maze. They are pictures of the pages, not the file download. The answer key is on page 6 and is not shown here." in ta, "Travel Adventure previews paragraph names pages 2 and 4")
    check('src="/holiday/assets/previews/CyberDadKit-travel-adventure-page-02.png"' in ta and 'src="/holiday/assets/previews/CyberDadKit-travel-adventure-page-04.png"' in ta, "Travel Adventure page shows the word search and maze previews")
    check("CyberDadKit-travel-adventure-page-03.png" not in ta and "airport" not in ta.lower(), "Travel Adventure page no longer shows the page 3 bingo preview or airport wording")



    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL ONE-PAGE HOLIDAY SHOP CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
