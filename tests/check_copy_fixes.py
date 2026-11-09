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
]
NEW_PRESENT = [
    (ROOT / "affiliate-disclosure.html", "A: No. We only recommend products we use."),
    (ROOT / "affiliate-disclosure.html", "Some links may be affiliate links; we may earn a commission at no extra cost to you."),
    (ROOT / "assets/js/ethical-compliance.js", "A: No. We only recommend products we use."),
    (ROOT / "assets/js/ethical-compliance.js", "Some links may be affiliate links; we may earn a commission at no extra cost to you."),
    (ROOT / "about.md", "[Holiday printables](/holiday/)"),
    (ROOT / "about.md", "[CyberDad Kit Sites](/sites/)"),
    (ROOT / "terms-of-sale.md", "## Holiday digital printables"),
    (ROOT / "terms-of-sale.md", "Christmas Trivia Night"),
    (ROOT / "terms-of-sale.md", "instant digital downloads for personal/household use"),
    (ROOT / "terms-of-sale.md", "](/holiday/refund/)"),
    (ROOT / "terms-of-sale.md", "](/holiday/trivia/refund/)"),
    (ROOT / "terms-of-sale.md", "within 7 days of your purchase date"),
    (ROOT / "terms-of-sale.md", "This policy applies only to Gather & Play and does not limit your statutory rights."),
    (ROOT / "terms-of-sale.md", "This policy applies only to Christmas Trivia Night and the Christmas Trivia Night + Gather & Play bundle and does not limit your statutory rights."),
    (ROOT / "terms-of-sale.md", "](/holiday/host-planner/refund/)"),
    (ROOT / "terms-of-sale.md", "](/holiday/kids-table/refund/)"),
    (ROOT / "holiday/index.html", 'href="/terms-of-sale/"'),
    (ROOT / "_includes/site-footer.html", "CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794"),
    (ROOT / "cyberdadkit-privacy-policy.html", "&copy; 2026 Cyber Dad Kit"),
    (ROOT / "cyberdadkit-privacy-policy.html", "MailerLite signup form on some articles and on the Shield Kit page"),
    (ROOT / "cookie-policy.html", "email signup form on some articles and on the Shield Kit page"),
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
    "assets/js/ethical-compliance.js": Counter({"$2": 1}),
}
# Prices cited in the holiday terms are copied from the live product pages.
ALLOWED_PRICE_ADDITIONS = {
    "terms-of-sale.md": Counter({"$4.99": 1, "$5.99": 1, "$11.99": 2, "$12.99": 1}),
}
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
    for price in ("$4.99", "$5.99", "$11.99", "$12.99"):
        check(price in holiday_section, f"holiday terms cite the live price {price}")
    check("$47" not in holiday_section, "holiday terms section does not repeat the Shield Kit price")
    check("the bundle" in holiday_section, "holiday terms section names the bundle")
    check("/holiday/refund/" in holiday_section and "/holiday/trivia/refund/" in holiday_section, "terms mention both holiday refund URLs")
    check(holiday_section.count("You may request a full refund for any reason within 7 days of your purchase date.") == 4, "each printable repeats the 7-day refund substance")

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

    check(not diff_names("shield-kit"), "shield-kit/ untouched")
    check(not diff_names("holiday/trivia"), "holiday/trivia/ untouched")
    check(not diff_names("scripts/_posts"), "scripts/_posts unchanged vs origin/main")
    delivery_dir = ROOT / "holiday" / "delivery"
    holiday_zips = [p for p in (ROOT / "holiday").rglob("*") if p.is_file() and p.suffix.lower() == ".zip"]
    check(not delivery_dir.exists(), "holiday delivery directory is absent")
    check(not holiday_zips, "no zip files under holiday/" + ("" if not holiday_zips else f" {holiday_zips}"))

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


def changed_llc_lines() -> list[str]:
    """Lines that already used the approved LLC mailing form must be byte-identical."""
    names = subprocess.check_output(["git", "diff", "--name-only", MAIN], cwd=ROOT, text=True).splitlines()
    bad = []
    for name in names:
        if name.startswith("shield-kit/"):
            continue
        old = git_show(name)
        if old is None or LLC_LINE not in old:
            continue
        new_path = ROOT / name
        new = new_path.read_text(encoding="utf-8") if new_path.is_file() else ""
        old_lines = [line for line in old.splitlines() if LLC_LINE in line]
        new_lines = [line for line in new.splitlines() if LLC_LINE in line]
        if old_lines != new_lines:
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
        path = ROOT / name
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        new = path.read_text(encoding="utf-8", errors="ignore")
        old = git_show(name) or ""
        if Counter(STRIPE_RE.findall(old)) != Counter(STRIPE_RE.findall(new)):
            stripe_bad.append(name)
        old_prices = Counter(PRICE_RE.findall(old))
        new_prices = Counter(PRICE_RE.findall(new))
        allowed_removed = ALLOWED_PRICE_REMOVALS.get(name, Counter())
        allowed_added = ALLOWED_PRICE_ADDITIONS.get(name, Counter())
        if old_prices - new_prices != allowed_removed or new_prices - old_prices != allowed_added:
            price_bad.append(name)
        if Counter(FORM_RE.findall(old)) != Counter(FORM_RE.findall(new)):
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
        "https://getcyberdadkit.com/holiday/host-planner/",
        "https://getcyberdadkit.com/holiday/host-planner/refund/",
        "https://getcyberdadkit.com/holiday/kids-table/",
        "https://getcyberdadkit.com/holiday/kids-table/refund/",
        "https://getcyberdadkit.com/journal/2027/",
        "https://getcyberdadkit.com/journal/2027/refund/",
        "https://getcyberdadkit.com/journal/2027/sample/",
    ]
    missing_new = [url for url in required_new if not any(loc.rstrip("/") == url.rstrip("/") for loc in locs)]
    check(not missing_new, "sitemap lists host planner, kids table, journal, and their refund pages" + ("" if not missing_new else f" missing {missing_new}"))
    check(not any(("/holiday/" + "delivery") in loc for loc in locs), "sitemap has no removed delivery URL")
    check(not any("/privacy/" in loc or loc.rstrip("/").endswith("/privacy") for loc in locs), "sitemap omits the privacy redirect")
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
