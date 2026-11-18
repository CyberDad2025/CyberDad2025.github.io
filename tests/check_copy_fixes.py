#!/usr/bin/env python3
"""Proofs for the public copy-fix pass.

Checks source text, compares checkout links and prices to main, and, when
Jekyll is available, builds the site and checks sitemap.xml plus pagination
link tags.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "origin/main"
SITE = Path(os.environ.get("COPY_FIX_SITE", "/tmp/cdk-copy-site"))
TEXT_SUFFIXES = {".html", ".md", ".liquid", ".xml", ".yml", ".js", ".txt", ".json"}
SKIP_DIRS = {".git", "_site", "vendor", ".jekyll-cache"}

OLD_ABSENT = [
    "protect our own kids",
    "tested by our own family for at least 3 months",
    "20-30% commission",
    "25% lifetime commission",
    "Up to 100% commission",
    "15-20% commission",
    "Every weekday, CyberDad Kit publishes one post",
    "I sell one product",
    "on our homepage and some articles",
    "on the homepage and on some articles",
    "Our family tries cybersecurity tools for months before reviewing",
    "A: No. We only recommend products we use.",
]
NEW_PRESENT = [
    (ROOT / "affiliate-disclosure.html", "A: No. We don't recommend products just to earn a commission."),
    (ROOT / "affiliate-disclosure.html", "&copy; 2026 CyberDadKit"),
    (ROOT / "affiliate-disclosure.html", "last updated on November 9, 2026"),
    (ROOT / "affiliate-disclosure.html", "Some links may be affiliate links; we may earn a commission at no extra cost to you."),
    (ROOT / "assets/js/ethical-compliance.js", "A: No. We don't recommend products just to earn a commission."),
    (ROOT / "assets/js/ethical-compliance.js", "&copy; 2026 CyberDadKit"),
    (ROOT / "assets/js/ethical-compliance.js", "last updated on November 9, 2026"),
    (ROOT / "assets/js/ethical-compliance.js", "Some links may be affiliate links; we may earn a commission at no extra cost to you."),
    (ROOT / "about.md", "[Holiday printables](/holiday/)"),
    (ROOT / "about.md", "[CyberDadKit Sites](/sites/)"),
    (ROOT / "terms-of-sale.md", "## Holiday digital printables"),
    (ROOT / "terms-of-sale.md", "Christmas Trivia Night"),
    (ROOT / "terms-of-sale.md", "Gather & Play ($7.99), Christmas Trivia Night ($5.99), the Thanksgiving Host Planner ($4.99), and the Kids' Table Activity Pack ($5.99) are instant digital downloads for personal/household use, available only to customers located in the United States."),
    (ROOT / "terms-of-sale.md", 'description: "CyberDadKit terms of sale for our digital products, including holiday digital printables (7-day refunds; US customers)."'),
    (ROOT / "terms-of-sale.md", "](/holiday/refund/)"),
    (ROOT / "terms-of-sale.md", "](/holiday/trivia/refund/)"),
    (ROOT / "terms-of-sale.md", "within 7 days of your purchase date"),
    (ROOT / "terms-of-sale.md", "This policy applies only to Gather & Play and does not limit your statutory rights."),
    (ROOT / "terms-of-sale.md", "This policy applies to Christmas Trivia Night, including a purchase of Christmas Trivia Night together with Gather & Play, and does not limit your statutory rights."),
    (ROOT / "terms-of-sale.md", "](/holiday/host-planner/refund/)"),
    (ROOT / "terms-of-sale.md", "](/holiday/kids-table/refund/)"),
    (ROOT / "holiday/index.html", 'href="/terms-of-sale/"'),
    (ROOT / "_includes/site-footer.html", "CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794"),
    (ROOT / "cyberdadkit-privacy-policy.html", "&copy; 2026 CyberDadKit"),
    (ROOT / "cyberdadkit-privacy-policy.html", "MailerLite signup form on some articles may store cookies"),
    (ROOT / "cookie-policy.html", "The email signup form on some articles is provided by MailerLite."),
    (ROOT / "cyber_parenting_global_blog.html", '<meta name="robots" content="noindex">'),
]
STRIPE_RE = re.compile(r"https://buy\.stripe\.com/[A-Za-z0-9]+")
PRICE_RE = re.compile(r"\$\d+(?:\.\d+)?")
FORM_RE = re.compile(
    r'data-form="[^"]+"|checkout\.mailerlite\.com/[^"\'\s<]+|forms/\d+'
)
WIFI_RE = re.compile(r"\bWiFi\b|Wi-fi|(?<![A-Za-z0-9_\-/.])wifi(?![A-Za-z0-9_\-/.])")
SHIELD_HREF_RE = re.compile(r"""href\s*=\s*["'][^"']*shield-kit""", re.I)
# Prices removed only because those sentences were deleted on purpose:
# the about-page "$47" product sentence, and the "$2 signup bonus" inside the
# partner commission-rate list. No price token may be added or rewritten.
ALLOWED_PRICE_REMOVALS = {
    "about.md": Counter({"$47": 1}),
    "affiliate-disclosure.html": Counter({"$2": 1}),
    # Follow-up SMALL 1117: drop the retired $11.99 Kids' Table + Gather & Play bundle price from the KT refund page.
    "holiday/kids-table/refund/index.html": Counter({"$11.99": 1}),
    "assets/js/ethical-compliance.js": Counter({"$2": 1}),
    # Follow-up SMALL 1117 drops the retired $11.99 and $12.99 bundle prices from the terms.
    "terms-of-sale.md": Counter({"$11.99": 2, "$12.99": 1}),
    "_posts/2026-04-28-your-kids-gaming-account-is-a-target-heres-how-to-lock-it-do.md": Counter({"$47": 1}),
    "_posts/2026-04-29-nsa-grassmarlin-a-hidden-risk-for-your-family.md": Counter({"$47": 1}),
    "_posts/2025 couple-loses-106k-email-scam.md": Counter({"$47": 1}),
    "cyber_2025-07-15_1752580178.html": Counter({"$47": 1}),
    "scripts/_posts/2025-07-28-daily-cybersecurity-update.md": Counter({"$47": 1}),
    # Journal 2027 is US-only: the A4 $9.99 mentions are deleted. Letter $9.99
    # and half-letter $7.99 stay. The holiday catalog drops that same A4 price.
    "journal/2027/index.html": Counter({"$9.99": 5}),
    "tests/check_journal_storefront.py": Counter({"$9.99": 2}),
}
# The only buy.stripe.com change vs main is deleting the journal A4 payment link.
JOURNAL_A4_LINK = "https://buy.stripe.com/14AfZg9yudqEfT74nZds409"
# shop/index.html prices belong to PR #1000. None means any price tokens are
# allowed, so this check passes whether that page lands on main first or here.
# Holiday printable prices are already on main, so terms-of-sale.md is not listed.
ALLOWED_PRICE_ADDITIONS = {
    "shop/index.html": None,
    "holiday/index.html": None,
    "holiday/sample/index.html": None,
    "holiday/host-kit/index.html": None,
    # One-page shop: the ta-crosslink $4.99, travel-adventure and table-set entries
    # are on main now (the product pages became redirect stubs), so they were dropped.
}
ONE_PAGE_STUBS = {
    "shop/index.html",
    "holiday/host-kit/index.html",
    "holiday/host-planner/index.html",
    "holiday/kids-table/index.html",
    "holiday/table-set/index.html",
    "holiday/travel-adventure/index.html",
    "holiday/trivia/index.html",
}
ONE_PAGE_FORM_REMOVALS = {"holiday/index.html"} | ONE_PAGE_STUBS


def main_holiday_stripe_links() -> set[str]:
    """Every buy.stripe.com URL on main's holiday product pages and /shop/."""
    links: set[str] = set()
    for name in ONE_PAGE_STUBS | {"holiday/index.html"}:
        links.update(STRIPE_RE.findall(git_show(name) or ""))
    return links


def main_holiday_prices() -> set[str]:
    """Price tokens on main's holiday product pages, plus the verified Host Kit parts sum."""
    prices = {"$24.96"}
    for name in ONE_PAGE_STUBS | {"holiday/index.html"}:
        prices.update(PRICE_RE.findall(git_show(name) or ""))
    return prices
LLC_LINE = "CyberDad Kit LLC, PO Box 940061"


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    for needle in OLD_ABSENT:
        hits = search(needle)
        check(not hits, f"old string gone: {needle}" + ("" if not hits else f" still in {hits[:5]}"))

    for path, needle in NEW_PRESENT:
        text = path.read_text(encoding="utf-8")
        check(needle in text, f"new string present in {path.relative_to(ROOT)}: {needle[:80]}")

    about = (ROOT / "about.md").read_text(encoding="utf-8")
    check("/shield-kit/" not in about and "Shield Kit" not in about, "about page does not list or link the Shield Kit")
    check("$47" not in about, "about page does not state the Shield Kit price")

    holiday_section = (ROOT / "terms-of-sale.md").read_text(encoding="utf-8").split("## Holiday digital printables", 1)[1].split("## Contact", 1)[0]
    for price in ("$4.99", "$5.99", "$7.99"):
        check(price in holiday_section, f"holiday terms cite the live price {price}")
    for price in ("$11.99", "$12.99"):
        check(price not in holiday_section, f"holiday terms no longer cite the retired bundle price {price}")
    check("$47" not in holiday_section, "holiday terms section does not repeat the Shield Kit price")
    check("bundle" not in holiday_section, "holiday terms section no longer names a bundle")
    check("together with Gather & Play" in holiday_section, "holiday terms still cover past combined purchases")
    check("/holiday/refund/" in holiday_section and "/holiday/trivia/refund/" in holiday_section, "terms mention both holiday refund URLs")
    check(holiday_section.count("You may request a full refund for any reason within 7 days of your purchase date.") == 5, "each printable repeats the 7-day refund substance")
    check("/holiday/table-set/refund/" in holiday_section, "terms link the Thanksgiving Table Set refund page")

    sitemap_src = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    check(sitemap_src.startswith("---\n") and "{% for post in site.posts %}" in sitemap_src and "{% for page in site.pages %}" in sitemap_src, "sitemap.xml is a Liquid template over site.posts and site.pages")
    check("https://getcyberdadkit.com/20" not in sitemap_src, "sitemap source is not a static post URL list")

    config = (ROOT / "_config.yml").read_text(encoding="utf-8")
    check("paginate: 25" in config and 'paginate_path: "/page:num/"' in config, "pagination is still enabled")
    check(re.search(r'path: "cyber_parenting_global_blog.html"\n\s+values:\n(?:.*\n)*?\s+sitemap: false', config), "global blog page is sitemap: false")
    robots = (ROOT / "cyber_parenting_global_blog.html").read_text(encoding="utf-8")
    check("nofollow" not in robots, "global blog noindex keeps follow")

    for href, target in {
        "/holiday/": ROOT / "holiday/index.html",
        "/sites/": ROOT / "sites/index.html",
        "/terms-of-sale/": ROOT / "terms-of-sale.md",
        "/holiday/refund/": ROOT / "holiday/refund/index.html",
    }.items():
        check(target.is_file(), f"added link {href} resolves to {target.relative_to(ROOT)}")

    shield_hits = shield_kit_hrefs()
    check(not shield_hits, "no /shield-kit/ links on /holiday/ HTML" + ("" if not shield_hits else f" {shield_hits}"))

    archive = ROOT / "_archive" / "shield-kit" / "index.html"
    public_kit = ROOT / "shield-kit" / "index.html"
    archived_main = git_show("_archive/shield-kit/index.html")
    check(archive.is_file() and archived_main is not None and archive.read_text(encoding="utf-8") == archived_main, "archived kit page matches origin/main")
    public_kit_text = public_kit.read_text(encoding="utf-8")
    check(
        'http-equiv="refresh"' in public_kit_text
        and 'url=/' in public_kit_text
        and 'rel="canonical" href="https://getcyberdadkit.com/"' in public_kit_text
        and 'name="robots" content="noindex"' in public_kit_text
        and "checkout.mailerlite.com" not in public_kit_text
        and "4435" not in public_kit_text
        and "Shield Kit" not in public_kit_text,
        "public /shield-kit/ is a noindex homepage redirect with no sales copy",
    )
    check("- _archive" in config, "_archive is excluded from the Jekyll build")
    trivia_changed = diff_names("holiday/trivia")
    allowed_trivia = {
        "holiday/trivia/index.html",
        "holiday/trivia/refund/index.html",
        "holiday/trivia/sample/index.html",
    }
    check(
        set(trivia_changed) <= allowed_trivia,
        "holiday/trivia changes are only footer identity pages" + ("" if not trivia_changed else f" {trivia_changed}"),
    )
    scripts_posts = diff_names("scripts/_posts")
    check(
        scripts_posts == [],
        "scripts/_posts unchanged vs origin/main"
        + ("" if not scripts_posts else f" {scripts_posts}"),
    )
    delivery_dir = ROOT / "holiday" / "delivery"
    holiday_zips = [p for p in (ROOT / "holiday").rglob("*") if p.is_file() and p.suffix.lower() == ".zip"]
    allowed_zip = ROOT / "holiday" / "host-kit" / "files" / "CyberDadKit-Holiday-Host-Kit.zip"
    check(not delivery_dir.exists(), "holiday delivery directory is absent")
    check(holiday_zips == [allowed_zip], "only the unlisted Host Kit ZIP is under holiday/" + ("" if holiday_zips == [allowed_zip] else f" {holiday_zips}"))
    if allowed_zip.is_file():
        digest = __import__("hashlib").sha256(allowed_zip.read_bytes()).hexdigest()
        check(digest == "0a43e1765c99b069c88cc7b60c889d49834aa5945ed7e5cb57eff222a556d6d1", "Host Kit ZIP sha256 is the 15-PDF release")

    llc_bad = changed_llc_lines()
    check(not llc_bad, "approved CyberDad Kit LLC, PO Box lines unchanged" + ("" if not llc_bad else f" {llc_bad[:5]}"))

    stripe_bad, price_bad, form_bad = checkout_drift()
    check(not stripe_bad, "no buy.stripe.com href changes vs main" + ("" if not stripe_bad else f" {stripe_bad[:5]}"))
    check(not price_bad, "no price-text changes vs main, except the required deletions" + ("" if not price_bad else f" {price_bad[:5]}"))
    check(not form_bad, "no MailerLite form id or checkout href changes vs main" + ("" if not form_bad else f" {form_bad[:5]}"))

    wifi_hits = wifi_in_visible_copy()
    check(not wifi_hits, "visible WiFi/wifi/Wi-fi normalized to Wi-Fi" + ("" if not wifi_hits else f" {wifi_hits[:8]}"))

    build_ok, build_log = jekyll_build()
    print(build_log)
    check(build_ok, "jekyll build succeeds")
    if build_ok:
        check_built_site(check)

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL COPY-FIX CHECKS PASSED")
    return 0


def search(needle: str) -> list[str]:
    hits = []
    self_name = Path(__file__).name
    for path in iter_text_files():
        if path.name == self_name:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        if needle in text:
            hits.append(str(path.relative_to(ROOT)))
    return hits


def iter_text_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() in TEXT_SUFFIXES:
                yield path


def shield_kit_hrefs() -> list[str]:
    hits = []
    holiday = ROOT / "holiday"
    for path in holiday.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".md", ".liquid"}:
            continue
        if "trivia" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if SHIELD_HREF_RE.search(text):
            hits.append(str(path.relative_to(ROOT)))
    return hits


def diff_names(pathspec: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", MAIN, "--", pathspec],
        cwd=ROOT,
        text=True,
    )
    return [line for line in out.splitlines() if line.strip()]


def footer_identity_replaced(old: str, new: str) -> bool:
    """The approved edit removes the one-line mailing footer and uses four lines."""
    old_hits = [line.strip() for line in old.splitlines() if LLC_LINE in line]
    new_hits = [line.strip() for line in new.splitlines() if LLC_LINE in line]
    identity = (
        "<p>CyberDadKit © 2026</p>",
        "<p>CyberDad Kit LLC</p>",
        "<p>PO Box 940061, Maitland, FL 32794</p>",
        '<p><a href="mailto:ruel@getcyberdadkit.com">ruel@getcyberdadkit.com</a></p>',
    )
    return (
        not new_hits
        and old_hits == ["<p>CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794</p>"]
        and all(line in new for line in identity)
    )


def changed_llc_lines() -> list[str]:
    """Lines that already used the approved LLC mailing form must be byte-identical."""
    names = subprocess.check_output(["git", "diff", "--name-only", MAIN], cwd=ROOT, text=True).splitlines()
    bad = []
    for name in names:
        if name.startswith("shield-kit/") or name.startswith("tests/"):
            continue
        old = git_show(name)
        if old is None or LLC_LINE not in old:
            continue
        new_path = ROOT / name
        new = new_path.read_text(encoding="utf-8") if new_path.is_file() else ""
        old_lines = [line for line in old.splitlines() if LLC_LINE in line]
        new_lines = [line for line in new.splitlines() if LLC_LINE in line]
        if old_lines != new_lines and not footer_identity_replaced(old, new):
            bad.append(name)
    return bad


def checkout_drift() -> tuple[list[str], list[str], list[str]]:
    names = set(subprocess.check_output(["git", "diff", "--name-only", MAIN], cwd=ROOT, text=True).splitlines())
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    names.update(untracked)
    stripe_bad, price_bad, form_bad = [], [], []
    for name in sorted(names):
        if name == "tests/check_copy_fixes.py":
            continue
        # The public page is a redirect. The archived sales page keeps its
        # original checkout href and is excluded from the build.
        if name == "shield-kit/index.html" or name.startswith("_archive/"):
            continue
        path = ROOT / name
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        new = path.read_text(encoding="utf-8", errors="ignore")
        old_raw = git_show(name)
        # New holiday product files. Existing checkout links and prices stay locked.
        if old_raw is None and (
            name.startswith("holiday/table-set/") or name.startswith("holiday/host-kit/")
        ):
            continue
        old = old_raw or ""
        if name.startswith("_site/") or name.startswith(".jekyll-cache/") or name.startswith("vendor/"):
            continue
        # Redirect stubs drop product copy, prices, and the sample signup form on purpose.
        # One-page shop: the old product pages and /shop/ are redirect stubs too. They
        # must carry no checkout URL and no form; their links and prices now live on
        # /holiday/ (checked below and in tests/check_holiday_one_page.py).
        if name in {"holiday/sample/index.html", "holiday/trivia/sample/index.html"} | ONE_PAGE_STUBS:
            if name in ONE_PAGE_STUBS and FORM_RE.findall(new):
                form_bad.append(name)
            if STRIPE_RE.findall(new):
                stripe_bad.append(name)
            continue
        old_links = Counter(STRIPE_RE.findall(old))
        new_links = Counter(STRIPE_RE.findall(new))
        if name == "journal/2027/index.html":
            removed = old_links - new_links
            added = new_links - old_links
            # A4 link may already be gone on main. Allow identical hrefs, or
            # the historical deletion of that one A4 payment link and nothing else.
            if added or (removed and removed != Counter({JOURNAL_A4_LINK: 1})):
                stripe_bad.append(name)
        elif name == "holiday/index.html":
            # One-page shop: every checkout URL on /holiday/ must already be live on main.
            if set(new_links) - main_holiday_stripe_links():
                stripe_bad.append(name)
        elif name.startswith("tests/") or name in {
            "holiday/host-kit/index.html",
            "holiday/index.html",
            "holiday/sample/index.html",
        }:
            pass
        elif old_links != new_links:
            stripe_bad.append(name)
        old_prices = Counter(PRICE_RE.findall(old))
        new_prices = Counter(PRICE_RE.findall(new))
        allowed_removed = ALLOWED_PRICE_REMOVALS.get(name, Counter())
        # Journal hero-cover swap (page-1 image only): prices already match main,
        # so do not require the historical A4 $9.99 deletions that already landed.
        if name == "journal/2027/index.html" and old_prices == new_prices:
            pass
        elif name == "holiday/index.html":
            # One-page shop: retired cards drop their prices. Every price left must be a
            # price main already shows on a holiday page, or the verified $24.96 sum.
            if set(new_prices) - main_holiday_prices():
                price_bad.append(name)
        elif name in ALLOWED_PRICE_ADDITIONS and ALLOWED_PRICE_ADDITIONS[name] is None:
            if old_prices - new_prices != allowed_removed:
                price_bad.append(name)
        else:
            allowed_added = ALLOWED_PRICE_ADDITIONS.get(name, Counter())
            # qa-flag-samples-1117: unchanged prices are fine once the required deletion is on main.
            if old_prices != new_prices and (old_prices - new_prices != allowed_removed or new_prices - old_prices != allowed_added):
                price_bad.append(name)
        if Counter(FORM_RE.findall(old)) != Counter(FORM_RE.findall(new)):
            added = Counter(FORM_RE.findall(new)) - Counter(FORM_RE.findall(old))
            removed = Counter(FORM_RE.findall(old)) - Counter(FORM_RE.findall(new))
            # The holiday sample page adds one embedded form. Tests may quote that slug and URL.
            allowed = {'data-form="eMwTaD"', "forms/1632878"}
            # One-page shop removes the inactive eMwTaD signup embed from /holiday/,
            # so removals are allowed there. Nothing may be added.
            if name in ONE_PAGE_FORM_REMOVALS:
                # hostkit-capture-1118: /holiday/ may add exactly the Host Kit capture form (embedded form 204511141540399100).
                if added and not (name == "holiday/index.html" and added == Counter({"forms/204511141540399100": 1})):
                    form_bad.append(name)
            elif removed or any(token not in allowed for token in added):
                form_bad.append(name)
    return stripe_bad, price_bad, form_bad


def git_show(name: str) -> str | None:
    proc = subprocess.run(
        ["git", "show", f"{MAIN}:{name}"],
        cwd=ROOT,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    try:
        return proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def wifi_in_visible_copy() -> list[str]:
    hits = []
    for path in iter_text_files():
        if path.suffix.lower() not in {".html", ".md", ".liquid"}:
            continue
        if "shield-kit" in path.parts or ("holiday" in path.parts and "trivia" in path.parts):
            continue
        if "scripts" in path.parts and "_posts" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if WIFI_RE.search(text):
            hits.append(str(path.relative_to(ROOT)))
    return hits


def jekyll_build() -> tuple[bool, str]:
    jekyll = os.path.expanduser("~/.local/share/gem/ruby/3.2.0/bin/jekyll")
    if not Path(jekyll).is_file():
        found = subprocess.run(["bash", "-lc", "command -v jekyll"], text=True, capture_output=True)
        jekyll = found.stdout.strip()
    if not jekyll:
        return False, "jekyll not installed"
    env = os.environ.copy()
    env["PATH"] = str(Path(jekyll).parent) + os.pathsep + env.get("PATH", "")
    if SITE.exists():
        subprocess.run(["rm", "-rf", str(SITE)], check=False)
    proc = subprocess.run(
        [jekyll, "build", "--destination", str(SITE), "--trace"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    tail = "\n".join((proc.stdout + "\n" + proc.stderr).splitlines()[-40:])
    return proc.returncode == 0, f"jekyll build exit {proc.returncode}\n{tail}"


def check_built_site(check) -> None:
    sitemap = SITE / "sitemap.xml"
    check(sitemap.is_file(), "built sitemap.xml exists")
    if not sitemap.is_file():
        return
    raw = sitemap.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        check(False, f"sitemap.xml is valid XML ({exc})")
        return
    check(True, "sitemap.xml is valid XML")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [node.text or "" for node in root.findall(".//sm:loc", ns)]
    if not locs:
        locs = [node.text or "" for node in root.iter() if node.tag.endswith("loc")]
    page_locs = [loc for loc in locs if re.search(r"/page([2-9]|[1-9][0-9])(/|$)", loc)]
    check(not page_locs, "sitemap has no /page2/ through /page99/" + ("" if not page_locs else f" {page_locs[:5]}"))

    expected = expected_holiday_urls()
    missing = [url for url in expected if not any(loc.rstrip("/") == url.rstrip("/") for loc in locs)]
    check(not missing, "sitemap still has every existing /holiday/ URL" + ("" if not missing else f" missing {missing}"))
    required_new = [
        # One-page shop: /holiday/host-planner/ and /holiday/kids-table/ are now noindex redirects to /holiday/#card,
        # so they leave the sitemap. Their refund pages stay listed.
        "https://getcyberdadkit.com/holiday/",
        "https://getcyberdadkit.com/holiday/host-planner/refund/",
        "https://getcyberdadkit.com/holiday/kids-table/refund/",
        "https://getcyberdadkit.com/journal/2027/",
        "https://getcyberdadkit.com/journal/2027/refund/",
        "https://getcyberdadkit.com/journal/2027/sample/",
        "https://getcyberdadkit.com/refund-policy/",
        "https://getcyberdadkit.com/faq/",
        "https://getcyberdadkit.com/support/",
    ]
    missing_new = [url for url in required_new if not any(loc.rstrip("/") == url.rstrip("/") for loc in locs)]
    check(not missing_new, "sitemap lists /holiday/, the host planner and kids table refund pages, and the journal pages" + ("" if not missing_new else f" missing {missing_new}"))
    check(not any(("/holiday/" + "delivery") in loc for loc in locs), "sitemap has no removed delivery URL")
    check(not any("/privacy/" in loc or loc.rstrip("/").endswith("/privacy") for loc in locs), "sitemap omits the privacy redirect")
    check(not any("/shield-kit" in loc for loc in locs), "sitemap omits /shield-kit/")
    check(any(loc.rstrip("/").endswith("getcyberdadkit.com") or loc.rstrip("/").endswith("getcyberdadkit.com/") for loc in locs) or any(loc.rstrip("/") == "https://getcyberdadkit.com" for loc in locs), "homepage remains in the sitemap")

    home = SITE / "index.html"
    page2 = SITE / "page2" / "index.html"
    check(page2.is_file(), "pagination still writes /page2/ (not disabled)")
    for label, path in (("homepage", home), ("page2", page2)):
        if not path.is_file():
            check(False, f"{label} built HTML exists")
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        check('rel="next"' not in html and 'rel="prev"' not in html, f"{label} has no rel=next/prev pagination tags")


def expected_holiday_urls() -> list[str]:
    """Holiday URLs the previous jekyll-sitemap output included.

    HTML pages under holiday/ with sitemap: false (the delivery page) stay out.
    PDF and extensionless-front-matter-free html/pdf static files stay in.
    """
    base = "https://getcyberdadkit.com"
    urls = []
    holiday = ROOT / "holiday"
    for path in holiday.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel == "holiday/product.json":
            continue
        text_head = ""
        if path.suffix.lower() in {".html", ".md"}:
            text_head = path.read_text(encoding="utf-8", errors="ignore")[:800]
        if text_head.startswith("---"):
            if re.search(r"(?m)^sitemap:\s*false\s*$", text_head):
                continue
            if path.name in {"index.html", "index.md"}:
                url_path = "/" + str(path.parent.relative_to(ROOT)).replace("\\", "/") + "/"
                if url_path == "/./":
                    url_path = "/"
                urls.append(base + url_path.replace("/holiday/holiday/", "/holiday/"))
            continue
        if path.suffix.lower() in {".pdf", ".html", ".htm", ".xhtml"}:
            urls.append(base + "/" + rel)
    cleaned = []
    for url in urls:
        url = url.replace("https://getcyberdadkit.com/.", "https://getcyberdadkit.com")
        if url.endswith("/index.html"):
            url = url[: -len("index.html")]
        cleaned.append(url)
    return sorted(set(cleaned))


if __name__ == "__main__":
    sys.exit(main())
