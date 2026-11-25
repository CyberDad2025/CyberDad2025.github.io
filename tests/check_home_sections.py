#!/usr/bin/env python3
"""Checks for the homepage Year-round and Holiday kit sections (feat/home-evergreen-holiday-1124).

The Evergreen section must appear before the Holiday section. Card hrefs go to
existing product pages (or /holiday/ hashes for items that live on the holiday
shop). Prices must match the source product pages or _data files. New copy in
these sections has no em or en dashes and no banned words. No Stripe or Drive
links are added on the homepage.

Run: python3 tests/check_home_sections.py
"""
from __future__ import annotations

import html as html_lib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"
SITE = ROOT / "_site" / "index.html"
SAMPLE = ROOT / "screen-free" / "assets" / "CyberDadKit-Screen-Free-Kids-Activity-Bundle-FREE-SAMPLE-US-Letter.pdf"
SAMPLE_HREF = "/screen-free/assets/CyberDadKit-Screen-Free-Kids-Activity-Bundle-FREE-SAMPLE-US-Letter.pdf"

EVERGREEN = [
    {
        "name": "Screen-Free Kids Activity Bundle",
        "href": "/screen-free/",
        "prices": ["14.99"],
        "source": "_data/screen_free.yml (link target /screen-free/; price from /screen-free/ and the /holiday/ card, $14.99). yml holds stripe_link only and is not used as the card href.",
        "source_files": ["screen-free/index.html", "holiday/index.html"],
    },
    {
        "name": "2027 Family Planner",
        "href": "/planner/2027/",
        "prices": ["9.99"],
        "source": "/planner/2027/ and the /holiday/ card ($9.99). _data/planner_2027.yml holds stripe_link only.",
        "source_files": ["planner/2027/index.html", "holiday/index.html"],
    },
    {
        "name": "2027 Bible Verse Journal",
        "href": "/journal/2027/",
        "prices": ["7.99", "9.99"],
        "source": "/journal/2027/ (US Letter $9.99, half-letter $7.99, hero From $7.99).",
        "source_files": ["journal/2027/index.html"],
    },
]

HOLIDAY = [
    {
        "name": "Holiday Host Kit",
        "href": "/holiday/#host-kit",
        "prices": ["17.99"],
        "source": "/holiday/ Host Kit hero ($17.99). /holiday/host-kit/ is a redirect stub.",
        "source_files": ["holiday/index.html"],
    },
    {
        "name": "Gather & Play",
        "href": "/holiday/gather-and-play/",
        "prices": ["7.99"],
        "source": "/holiday/ card and /holiday/gather-and-play/ ($7.99).",
        "source_files": ["holiday/index.html", "holiday/gather-and-play/index.html"],
    },
    {
        "name": "Christmas Trivia Night",
        "href": "/holiday/#trivia",
        "prices": ["5.99"],
        "source": "/holiday/ card ($5.99). /holiday/trivia/ is a redirect stub.",
        "source_files": ["holiday/index.html"],
    },
    {
        "name": "Thanksgiving Table Set",
        "href": "/holiday/#table-set",
        "prices": ["4.99"],
        "source": "/holiday/ card ($4.99). /holiday/table-set/ is a redirect stub.",
        "source_files": ["holiday/index.html"],
    },
    {
        "name": "Thanksgiving Host Planner",
        "href": "/holiday/#host-planner",
        "prices": ["4.99"],
        "source": "/holiday/ card ($4.99). /holiday/host-planner/ is a redirect stub.",
        "source_files": ["holiday/index.html"],
    },
    {
        "name": "Kids' Table Activity Pack",
        "href": "/holiday/#kids-table",
        "prices": ["5.99"],
        "source": "/holiday/ card ($5.99). /holiday/kids-table/ is a redirect stub.",
        "source_files": ["holiday/index.html"],
    },
    {
        "name": "The Great Thanksgiving Travel Adventure",
        "href": "/holiday/travel-adventure/",
        "prices": ["4.99"],
        "source": "/holiday/ card and /holiday/travel-adventure/ ($4.99).",
        "source_files": ["holiday/index.html", "holiday/travel-adventure/index.html"],
    },
]

ALLOWED_TITLES = {c["name"] for c in EVERGREEN + HOLIDAY}
ALLOWED_TITLES.update({
    "Year-round family kits",
    "Holiday picks",
    "Try a free sample",
    "Printable kits",
    "Shop all holiday kits",
    "See what's inside",
    "See the full Screen-Free Kids Activity Bundle",
    "Download the free US Letter sample (PDF)",
})

BANNED = {
    "em or en dash": r"[\u2014\u2013]",
    "guarantee": r"\bguarantee",
    "bare CDK": r"\bCDK\b",
    "worldwide": r"\bworldwide\b",
    "employer": r"\bemployers?\b|\bmy job\b|\bwhere I work\b",
    "invented social proof": r"\bbest[- ]sellers?\b|\b\d[\d,]*\+?\s+reviews?\b|\bstars?\b",
}

failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def visible(text: str) -> str:
    text = re.sub(r"\A---.*?---", " ", text, flags=re.S)
    text = re.sub(r"<!--.*?-->|<script\b.*?</script>|<style\b.*?</style>|\{%.*?%\}|\{\{.*?\}\}", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html_lib.unescape(text))


def extract_section(html: str, start_pat: str, end_pat: str) -> str:
    start = re.search(start_pat, html)
    end = re.search(end_pat, html)
    if not start or not end or end.start() <= start.start():
        return ""
    return html[start.start():end.start()]


def cards_in(block: str) -> list[dict[str, str]]:
    found = []
    for m in re.finditer(r'<article class="home-kit-card">(.*?)</article>', block, re.S):
        chunk = m.group(1)
        href = re.search(r'<a class="home-kit-link" href="([^"]+)"', chunk)
        title = re.search(r"<h3>(.*?)</h3>", chunk, re.S)
        price_bits = " ".join(re.findall(r"\$[0-9]+\.[0-9]{2}", chunk))
        found.append({
            "href": html_lib.unescape(href.group(1)) if href else "",
            "name": html_lib.unescape(re.sub(r"<[^>]+>", "", title.group(1))).strip() if title else "",
            "prices": price_bits,
        })
    return found


def built_target(href: str) -> Path | None:
    if not href.startswith("/"):
        return None
    if href.startswith(("http://", "https://", "mailto:", "//")):
        return None
    path = href.split("?", 1)[0].split("#", 1)[0]
    rel = path.lstrip("/")
    site = ROOT / "_site"
    if not rel:
        candidate = site / "index.html"
        return candidate if candidate.is_file() else None
    direct = site / rel
    if direct.is_file():
        return direct
    if direct.is_dir() and (direct / "index.html").is_file():
        return direct / "index.html"
    if not rel.endswith("/") and (site / (rel + ".html")).is_file():
        return site / (rel + ".html")
    # source-tree fallback when _site has not been built yet
    src = ROOT / rel
    if src.is_file():
        return src
    if (src / "index.html").is_file():
        return src / "index.html"
    return None


def source_has_price(files: list[str], amount: str) -> bool:
    needle = "$" + amount
    for rel in files:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if needle in text:
            return True
    return False


def main() -> int:
    src = HOME.read_text(encoding="utf-8")
    front_now = src.split("---", 2)[1]
    # Front matter must stay the business-home values already on main.
    check("cd_business_home: true" in front_now, "homepage front matter still sets cd_business_home")
    check("title: Website rebuilds for small businesses" in front_now, "homepage title front matter is unchanged")
    check(not re.search(r'href=["\']/?assets/festive/festive\.css["\']', src), "homepage does not link the festive stylesheet")
    check(re.search(r'href="https://buy\.stripe\.com/', src) is None, "homepage source has no Stripe Payment Link hrefs")
    check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)", src, re.I), "homepage source has no Drive links")

    kits = re.search(r'<section class="home-kits" id="kits".*</section>\s*<div class="cd-wrap">', src, re.S)
    check(bool(kits), "home-kits section is present below the hero and above the existing wrap")
    kits_html = kits.group(0) if kits else ""

    ev_pos = kits_html.find('id="year-round"')
    hol_pos = kits_html.find('id="holiday-picks"')
    check(ev_pos != -1 and hol_pos != -1 and ev_pos < hol_pos, "Evergreen section appears before the Holiday section")
    check('id="evergreen-title">Year-round family kits</h2>' in kits_html, "Evergreen heading is Year-round family kits")
    check('id="holiday-title">Holiday picks</h2>' in kits_html, "Holiday heading is Holiday picks")
    check('>Shop all holiday kits</a>' in kits_html and 'href="/holiday/"' in kits_html, "Holiday section links to /holiday/")
    check(SAMPLE_HREF in kits_html and SAMPLE.is_file(), "free sample CTA points at the existing Screen-Free US Letter PDF")
    check("mailerlite" not in kits_html.lower(), "no new MailerLite form was added")

    ev_block = extract_section(kits_html, r'<section id="year-round"', r'<aside class="home-freebie"|<section class="home-holiday"')
    hol_block = extract_section(kits_html, r'<section class="home-holiday" id="holiday-picks"', r"</section>\s*</div>\s*</section>")
    ev_cards = cards_in(ev_block)
    hol_cards = cards_in(hol_block)
    check(len(ev_cards) == len(EVERGREEN), f"Evergreen has {len(EVERGREEN)} cards (found {len(ev_cards)})")
    check(len(hol_cards) == len(HOLIDAY), f"Holiday has {len(HOLIDAY)} cards (found {len(hol_cards)})")

    def check_group(label: str, expected: list[dict], actual: list[dict]) -> None:
        for i, exp in enumerate(expected):
            got = actual[i] if i < len(actual) else {"name": "", "href": "", "prices": ""}
            check(got["name"] == exp["name"], f"{label} card {i+1} name is {exp['name']}")
            check(got["href"] == exp["href"], f"{label} card {i+1} href is {exp['href']}")
            for amount in exp["prices"]:
                check("$" + amount in got["prices"], f"{label} card {i+1} shows ${amount}")
                check(source_has_price(exp["source_files"], amount), f"{label} card {i+1} price ${amount} matches source ({exp['source']})")
            target = built_target(exp["href"])
            check(target is not None, f"{label} card {i+1} href {exp['href']} resolves to an existing built or source page")

    check_group("Evergreen", EVERGREEN, ev_cards)
    check_group("Holiday", HOLIDAY, hol_cards)

    # New-copy lint: the kits block, with known product titles allowed.
    vis = visible(kits_html)
    check("\u2014" not in kits_html and "\u2013" not in kits_html and "&mdash;" not in kits_html and "&ndash;" not in kits_html, "new kits copy has no em or en dashes")
    for label, pat in BANNED.items():
        hit = re.search(pat, vis, re.I)
        check(hit is None, "new kits copy has no " + label + ("" if hit is None else f": {hit.group(0)}"))

    # Age / gender checks on editorial lines, not on existing product titles.
    editorial = vis
    for title in sorted(ALLOWED_TITLES, key=len, reverse=True):
        editorial = editorial.replace(title, " ")
    age = re.search(r"\bages?\b|\d+\s*\+|years?[ -]old|\btoddlers?\b|\bpreschool|\bteens?\b|\bgrade\s*\d|\bkindergarten", editorial, re.I)
    gender = re.search(r"\b(?:boys?|girls?|sons?|daughters?)\b", editorial, re.I)
    check(age is None, "new editorial copy has no ages" + ("" if age is None else f": {age.group(0)}"))
    check(gender is None, "new editorial copy has no gender words" + ("" if gender is None else f": {gender.group(0)}"))

    check("CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794" in src, "homepage footer still has the PO Box address line")
    check('<figcaption>Example with a fictional business, not a real company or client.</figcaption>' in src,
          "hero figcaption uses a comma, not an em or en dash")
    cap = re.search(r"<figcaption>(.*?)</figcaption>", src, re.S)
    check(bool(cap) and "—" not in cap.group(1) and "–" not in cap.group(1) and "&mdash;" not in cap.group(1) and "&ndash;" not in cap.group(1),
          "hero figcaption has no em or en dash")

    if SITE.is_file():
        built = SITE.read_text(encoding="utf-8")
        b_ev = built.find('id="year-round"')
        b_hol = built.find('id="holiday-picks"')
        check(b_ev != -1 and b_hol != -1 and b_ev < b_hol, "built homepage has Evergreen before Holiday")
        check(re.search(r'href="https://buy\.stripe\.com/', built) is None, "built homepage has no Stripe Payment Link hrefs")
        check('href="/screen-free/"' in built and "14.99" in built, "built homepage still prices Screen-Free at $14.99 and links to /screen-free/")
        for href in [c["href"] for c in EVERGREEN + HOLIDAY] + ["/holiday/", SAMPLE_HREF]:
            check(built_target(href) is not None, f"built target exists for {href}")
    else:
        print("note  _site/index.html not present; skipped built homepage checks")

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL HOME SECTION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
