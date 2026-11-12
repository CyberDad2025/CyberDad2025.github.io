#!/usr/bin/env python3
"""Checks for the /shop/ catalog.

Confirms one card per live product, in order, with the price and preview image
taken from that product's page, a button to the product page (never a Stripe
URL), the shared nav and /holiday/ "Shop all" links, and that jekyll-sitemap
will list /shop/.

Run: python3 tests/check_shop_page.py
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOP = ROOT / "shop" / "index.html"
NAV = ROOT / "_includes" / "home-header.html"
HOLIDAY = ROOT / "holiday" / "index.html"
SITEMAP_LOC = "https://getcyberdadkit.com/shop/"

# Order, names, hrefs and prices are the live catalog. Each price string is also
# required on the product page, which is where the number was read from.
# Christmas Trivia Night's single price is $5.99 on holiday/trivia/index.html.
CARDS = [
    {
        "id": "gather-and-play",
        "name": "Gather & Play",
        "href": "/holiday/",
        "price": "$7.99",
        "page": "holiday/index.html",
        "image": "/assets/img/festive/gather-and-play-cover.jpg",
    },
    {
        "id": "christmas-trivia",
        "name": "Christmas Trivia Night",
        "href": "/holiday/trivia/",
        "price": "$5.99",
        "page": "holiday/trivia/index.html",
        "image": "/assets/img/festive/christmas-trivia-night-cover.jpg",
    },
    {
        "id": "trivia-bundle",
        "name": "Christmas Trivia Night + Gather & Play bundle",
        "href": "/holiday/trivia/#bundle",
        "price": "$12.99",
        "page": "holiday/trivia/index.html",
        "image": "/assets/img/festive/trivia-gp-bundle-cover.jpg",
    },
    {
        "id": "host-planner",
        "name": "Thanksgiving Host Planner",
        "href": "/holiday/host-planner/",
        "price": "$4.99",
        "page": "holiday/host-planner/index.html",
        "image": "/assets/img/festive/thanksgiving-host-planner-cover.jpg",
    },
    {
        "id": "table-set",
        "name": "Thanksgiving Table Set",
        "href": "/holiday/table-set/",
        "price": "$4.99",
        "page": "holiday/table-set/index.html",
        "image": "/holiday/table-set/img/CyberDadKit-Thanksgiving-Table-Set-cover.png",
    },
    {
        "id": "kids-table",
        "name": "Kids' Table Activity Pack",
        "href": "/holiday/kids-table/",
        "price": "$5.99",
        "page": "holiday/kids-table/index.html",
        "image": "/assets/img/festive/kids-table-pack-cover.jpg",
    },
    {
        "id": "kids-bundle",
        "name": "Kids' Table + Gather & Play bundle",
        "href": "/holiday/kids-table/#bundle",
        "price": "$11.99",
        "page": "holiday/kids-table/index.html",
        "image": "/assets/img/festive/kids-table-bundle-cover.jpg",
    },
    {
        "id": "bible-journal-2027",
        "name": "2027 Bible Verse Journal",
        "href": "/journal/2027/",
        "price": "From $7.99",
        "page": "journal/2027/index.html",
        "image": "/assets/img/festive/bible-verse-journal-2027-cover.jpg",
    },
    {
        "id": "host-kit",
        "name": "Holiday Host Kit",
        "href": "/holiday/host-kit/",
        "price": None,
        "status": "Back soon",
        "page": "holiday/host-kit/index.html",
        "image": "/holiday/host-kit/img/CyberDadKit-Holiday-Host-Kit-cover.png",
    },
]

# jekyll-sitemap 1.4.0 template (GitHub Pages / github-pages 232) lists
# site.html_pages where `doc.sitemap != false` and the url is not /404.html.
# A file with front matter is an HTML page. sitemap: true is the explicit opt-in
# this repo already uses for indexed posts. Static .html files without front
# matter are attached separately and are not how /shop/ is published.
BANNED = [
    (r"guarantee", "the word guarantee"),
    (r"\bCDK\b", "CDK"),
    (r"shield\s*kit", "Shield Kit"),
    (r"\bshield\b", "Shield"),
    (r"\b(?:my|our)\s+(?:son|daughter|kids?|child|children|wife|husband|family)\b", "family details"),
    (r"\b\d+\s*[- ]year[- ]olds?\b", "a child age"),
    (r"\b(?:boy|girl)s?\b", "a child gender"),
    (r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+(?:kids|children|boys|girls)\b", "a child count"),
]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class ShopParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.anchors = []
        self.ids = []
        self.depth = 0
        self.card_depth = None
        self.current = None

    def handle_starttag(self, tag, attrs):
        self.depth += 1
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "a":
            self.anchors.append(a)
        classes = a.get("class", "").split()
        if tag == "li" and "shop-card" in classes:
            self.current = {"id": a.get("id", ""), "parts": [], "imgs": [], "anchors": []}
            self.cards.append(self.current)
            self.card_depth = self.depth
        if self.current is not None:
            if tag == "img":
                self.current["imgs"].append(a)
            if tag == "a":
                self.current["anchors"].append(a)
        if tag in VOID:
            self.depth -= 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.current is not None and tag == "li" and self.depth == self.card_depth:
            self.current = None
            self.card_depth = None
        self.depth -= 1

    def handle_data(self, data):
        if self.current is not None:
            self.current["parts"].append(data)


def card_text(card: dict) -> str:
    return " ".join("".join(card["parts"]).split())


def meta_content(html: str, attr: str, value: str) -> str:
    pattern = rf'<meta\s+{attr}="{re.escape(value)}"\s+content="([^"]*)"'
    match = re.search(pattern, html)
    return match.group(1) if match else ""


def title_text(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.S)
    return match.group(1).strip() if match else ""


def yaml_list(text: str, key: str) -> list[str]:
    items = []
    in_list = False
    for line in text.splitlines():
        if not in_list:
            if re.match(rf"^{key}:\s*$", line):
                in_list = True
            continue
        if re.match(r"^[A-Za-z_]", line):
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"-\s+(.+)$", stripped)
        if match:
            items.append(match.group(1).strip().strip("'\""))
    return items


def page_file(path: str) -> Path | None:
    if path in ("", "/"):
        return ROOT / "index.html"
    rel = path.strip("/")
    for candidate in (ROOT / rel, ROOT / rel / "index.html", ROOT / f"{rel}.html", ROOT / f"{rel}.md"):
        if candidate.is_file():
            return candidate
    return None


def resolves(href: str) -> bool:
    if href.startswith("mailto:"):
        return href.startswith("mailto:ruel@getcyberdadkit.com")
    path = href.split("#", 1)[0]
    if path in ("", "/"):
        return (ROOT / "index.html").is_file()
    rel = path.strip("/")
    if (ROOT / rel).is_file():
        return True
    if (ROOT / rel / "index.html").is_file():
        return True
    if (ROOT / f"{rel}.md").is_file() or (ROOT / f"{rel}.html").is_file():
        return True
    return False


def main() -> int:
    failed = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    check(SHOP.is_file(), "shop/index.html exists")
    html = SHOP.read_text(encoding="utf-8") if SHOP.is_file() else ""
    front = ""
    if html.startswith("---"):
        front = html.split("---", 2)[1]
    parser = ShopParser()
    parser.feed(html)
    visible = re.sub(r"<!--.*?-->", " ", html, flags=re.S)

    check(len(parser.cards) == len(CARDS), f"{len(CARDS)} product cards")
    check([c["id"] for c in parser.cards] == [c["id"] for c in CARDS], "cards are in catalog order")
    check(len(parser.ids) == len(set(parser.ids)), "element ids are unique")

    for expected, card in zip(CARDS, parser.cards):
        label = expected["id"]
        text = card_text(card)
        product = (ROOT / expected["page"]).read_text(encoding="utf-8")
        image = expected["image"]
        check(card["id"] == expected["id"], f"{label}: id")
        check(expected["name"] in text, f"{label}: name {expected['name']}")
        if expected.get("status"):
            check(expected["status"] in text, f"{label}: {expected['status']}")
            check("$17.99" not in text, f"{label}: card does not show the price as a CTA")
            check("$17.99" in product, f"{label}: product page still states $17.99")
        else:
            check(expected["price"] in text, f"{label}: price {expected['price']}")
            check(expected["price"] in product, f"{label}: product page states {expected['price']}")
        check(len(card["anchors"]) == 1 and card["anchors"][0].get("href") == expected["href"], f"{label}: button href {expected['href']}")
        check(len(card["imgs"]) == 1 and card["imgs"][0].get("src") == image, f"{label}: preview image")
        alt = card["imgs"][0].get("alt", "").strip() if card["imgs"] else ""
        check(bool(alt), f"{label}: image alt text")
        check(image in product, f"{label}: image is already used on the product page")
        check(alt in product, f"{label}: alt text is the one on the product page")
        path = ROOT / image.lstrip("/")
        check(path.is_file(), f"{label}: image file exists")

    for anchor in parser.anchors:
        href = anchor.get("href", "")
        check("stripe.com" not in href.lower(), f"link is not a Stripe URL: {href}")
        path, sep, frag = href.partition("#")
        if href.startswith("#"):
            check(frag in parser.ids, f"anchor {href}")
            continue
        check(resolves(href), f"link resolves: {href}")
        if sep and frag:
            target = page_file(path)
            found = target is not None and f'id="{frag}"' in target.read_text(encoding="utf-8")
            check(found, f"anchor {href}")

    lowered = html.lower()
    check("stripe.com" not in lowered, "shop page has no stripe.com URL")
    check("buy.stripe.com" not in lowered, "shop page has no buy.stripe.com link")
    for pattern, label in BANNED:
        check(not re.search(pattern, visible, re.I), f"shop copy has no {label}")

    check('name="viewport" content="width=device-width, initial-scale=1"' in html, "viewport is set for small screens")
    title = title_text(html)
    description = meta_content(html, "name", "description")
    check(title == "CyberDadKit Shop: Printable Games and Journals", f"title is CyberDadKit Shop ({title!r})")
    check(description.count("a Kids' Table Activity Pack") == 1, "meta description says a Kids' Table Activity Pack")
    check(html.count("a Kids' Table Activity Pack") == 3, "description, social description, and lede use a Kids' Table Activity Pack")
    check("CyberDad Kit LLC" in html, "legal name stays CyberDad Kit LLC")
    check(20 <= len(title) <= 70, f"title length {len(title)}")
    check(bool(description), "meta description is present")
    check(80 <= len(description) <= 200, f"meta description length {len(description)}")
    check(meta_content(html, "property", "og:title") == title, "og:title matches title")
    check(meta_content(html, "property", "og:description") == description, "og:description matches description")
    check('rel="canonical" href="https://getcyberdadkit.com/shop/"' in html, "canonical /shop/")
    check("Available only to customers located in the United States." in html, "US-only eligibility wording")
    for pattern, label in BANNED:
        check(not re.search(pattern, title + "\n" + description, re.I), f"title and description have no {label}")

    nav = NAV.read_text(encoding="utf-8")
    holiday = HOLIDAY.read_text(encoding="utf-8")
    check('<a href="/shop/">Shop all</a>' in nav, "shared nav include links to Shop all")
    check('<a href="/shop/">Shop all</a>' in holiday, "/holiday/ links to Shop all")

    check("layout: null" in front, "shop page keeps layout null, like the other storefronts")
    check(re.search(r"(?m)^sitemap:\s*true\s*$", front) is not None, "front matter sets sitemap: true")
    check("sitemap: false" not in front, "shop page does not opt out of the sitemap")
    check("permalink:" not in front, "shop page keeps the /shop/ URL from shop/index.html")
    config = (ROOT / "_config.yml").read_text(encoding="utf-8")
    check("jekyll-sitemap" in yaml_list(config, "plugins"), "jekyll-sitemap plugin is enabled")
    excluded = yaml_list(config, "exclude")
    check(not any(item == "shop" or item.startswith("shop/") for item in excluded), "Jekyll exclude list does not drop /shop/")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    check("Sitemap: https://getcyberdadkit.com/sitemap.xml" in robots, "robots.txt publishes sitemap.xml")
    check("Disallow: /shop" not in robots, "robots.txt does not block /shop/")
    built = ROOT / "_site" / "sitemap.xml"
    if built.is_file():
        sitemap = built.read_text(encoding="utf-8")
        check(f"<loc>{SITEMAP_LOC}</loc>" in sitemap, "built sitemap lists /shop/")
    else:
        print("note  _site/sitemap.xml not present; inclusion follows sitemap: true on an html page")

    print()
    if failed:
        print(f"{len(failed)} check(s) failed")
        return 1
    print(f"all checks passed ({len(CARDS)} cards)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
