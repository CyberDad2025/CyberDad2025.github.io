#!/usr/bin/env python3
"""Checks for the holiday sample pages, guides, and cross-sell snippets.

Confirms the new Host Planner and Kids' Table samples, the five guide pages,
and the pairs-with blocks. Reads source files and, when the site has been
built, the Jekyll output. It does not request buy.stripe.com.

Run: python3 tests/check_holiday_samples_guides.py
"""

from __future__ import annotations

import hashlib
import html
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
MAIN = "origin/main"
GA4 = "G-5B1LNCPB56"
LLC = "CyberDad Kit LLC"
PO_BOX = "PO Box 940061, Maitland, FL 32794"
UTM_CROSSSELL = "utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content="
STRIPE_HOST = "buy" + ".stripe.com"
STRIPE_RE = re.compile(r"https://" + re.escape(STRIPE_HOST) + r"/[A-Za-z0-9]+")

NEW_PAGES = (
    "holiday/host-planner/sample/index.html",
    "holiday/kids-table/sample/index.html",
    "holiday/guides/printable-christmas-trivia/index.html",
    "holiday/guides/thanksgiving-games-printable/index.html",
    "holiday/guides/thanksgiving-hosting-checklist/index.html",
    "holiday/guides/kids-table-activities-thanksgiving/index.html",
    "holiday/guides/bible-verse-journal-2027/index.html",
)
EDITED_PAGES = (
    "holiday/index.html",
    "holiday/trivia/index.html",
    "holiday/host-planner/index.html",
    "holiday/kids-table/index.html",
    "journal/2027/index.html",
)
SAMPLE_PDFS = {
    "holiday/host-planner/sample/CyberDadKit-Host-Planner-FREE-SAMPLE-US-Letter.pdf":
        "406c248c7fba18e0acaa09f4bc8a434bd476d0c88d21b75f4a0858d850fed20f",
    "holiday/host-planner/sample/CyberDadKit-Host-Planner-FREE-SAMPLE-A4.pdf":
        "67fae34b631d3c67f938dbfdd43baed46d34e134c4b96797f9face1ec2fa3457",
    "holiday/kids-table/sample/CyberDadKit-Kids-Table-FREE-SAMPLE-US-Letter.pdf":
        "918a41eb1d6c6da3f69eda0af6c5cafe34641025c35b44e6a321a50ae8ce3036",
    "holiday/kids-table/sample/CyberDadKit-Kids-Table-FREE-SAMPLE-A4.pdf":
        "294e81a741035fa6ee6c87aa8f370637cb612f753a87171915b2c0aea70f1240",
}
SITEMAP_URLS = (
    "https://getcyberdadkit.com/holiday/host-planner/sample/",
    "https://getcyberdadkit.com/holiday/kids-table/sample/",
    "https://getcyberdadkit.com/holiday/guides/printable-christmas-trivia/",
    "https://getcyberdadkit.com/holiday/guides/thanksgiving-games-printable/",
    "https://getcyberdadkit.com/holiday/guides/thanksgiving-hosting-checklist/",
    "https://getcyberdadkit.com/holiday/guides/kids-table-activities-thanksgiving/",
    "https://getcyberdadkit.com/holiday/guides/bible-verse-journal-2027/",
)
# Exact pairs-with hrefs from the Growth cross-sell snippets.
PAIRS = {
    "holiday/index.html": (
        "/holiday/trivia/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=gather-to-trivia",
        "/holiday/kids-table/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=gather-to-kids",
    ),
    "holiday/trivia/index.html": (
        "/holiday/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=trivia-to-gather",
        "/journal/2027/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=trivia-to-journal",
    ),
    "holiday/host-planner/index.html": (
        "/holiday/kids-table/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=host-to-kids",
        "/holiday/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=host-to-gather",
    ),
    "holiday/kids-table/index.html": (
        "/holiday/host-planner/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=kids-to-host",
        "/holiday/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=kids-to-gather",
    ),
    "journal/2027/index.html": (
        "/holiday/trivia/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=journal-to-trivia",
        "/holiday/?utm_source=site&utm_medium=crosssell&utm_campaign=holiday_crosssell&utm_content=journal-to-gather",
    ),
}
PRODUCT_PATHS = {
    "/holiday/",
    "/holiday/trivia/",
    "/holiday/host-planner/",
    "/holiday/kids-table/",
    "/journal/2027/",
}
SKIP_EXTERNAL_HOSTS = {
    "www.googletagmanager.com",
    "www.google-analytics.com",
}


class PageDoc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.srcs: list[str] = []
        self.srcsets: list[str] = []
        self.h1 = 0
        self.in_footer = 0
        self.footer_parts: list[str] = []
        self.in_head = 0
        self.head_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "a" and data.get("href") is not None:
            classes = set((data.get("class") or "").split())
            self.hrefs.append((data["href"], classes))
        if data.get("src"):
            self.srcs.append(data["src"])
        if data.get("srcset"):
            self.srcsets.append(data["srcset"])
        if tag == "footer":
            self.in_footer += 1
        if tag == "head":
            self.in_head += 1

    def handle_endtag(self, tag):
        if tag == "footer" and self.in_footer:
            self.in_footer -= 1
        if tag == "head" and self.in_head:
            self.in_head -= 1

    def handle_data(self, data):
        if self.in_footer:
            self.footer_parts.append(data)
        if self.in_head:
            self.head_parts.append(data)


def stripe_hrefs(text: str) -> list[str]:
    return STRIPE_RE.findall(text)


def git_show(rel: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{MAIN}:{rel}"],
        cwd=ROOT,
        capture_output=True,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.decode("utf-8")


def title_and_description(text: str) -> tuple[str, str]:
    title = re.search(r"<title>(.*?)</title>", text, re.S)
    desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text)
    return (
        html.unescape(title.group(1)).strip() if title else "",
        html.unescape(desc.group(1)).strip() if desc else "",
    )


def canonical(text: str) -> str:
    match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', text)
    return match.group(1) if match else ""


def head_html(text: str) -> str:
    match = re.search(r"<head\b.*?</head>", text, re.S | re.I)
    return match.group(0) if match else ""


def pairs_hrefs(text: str) -> list[str]:
    match = re.search(r'<section\b[^>]*\bid="pairs".*?</section>', text, re.S)
    if not match:
        return []
    return [html.unescape(href) for href in re.findall(r'href="([^"]+)"', match.group(0))]


def pdf_pages(path: Path) -> int | None:
    proc = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    match = re.search(r"^Pages:\s+(\d+)\s*$", proc.stdout, re.M)
    return int(match.group(1)) if match else None


def site_dirs() -> list[Path]:
    found = []
    for path in (ROOT / "_site", Path("/tmp/cdk-copy-site")):
        if (path / "index.html").is_file():
            found.append(path)
    return found


def local_targets(url: str) -> list[str] | None:
    """Site-relative paths this URL must resolve to, or None when it is external."""
    if not url or url.startswith(("mailto:", "tel:", "javascript:")):
        return []
    if url.startswith("#"):
        return []
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc not in {"getcyberdadkit.com", "www.getcyberdadkit.com"}:
            return None
        path = parsed.path or "/"
    elif url.startswith("/"):
        path = url.split("#", 1)[0].split("?", 1)[0]
    else:
        return None
    path = unquote(path.split("#", 1)[0].split("?", 1)[0])
    return [path or "/"]


def built_has(site: Path, path: str) -> bool:
    rel = path.lstrip("/")
    if path == "/":
        return (site / "index.html").is_file()
    candidates = []
    if rel.endswith("/"):
        candidates.append(site / rel / "index.html")
        candidates.append(site / (rel.rstrip("/") + ".html"))
    else:
        candidates.append(site / rel)
        candidates.append(site / rel / "index.html")
    return any(item.is_file() for item in candidates)


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    for rel, digest in SAMPLE_PDFS.items():
        path = ROOT / rel
        got = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
        check(got == digest, f"{rel} sha256 matches the Growth packet")
        pages = pdf_pages(path) if path.is_file() else None
        check(pages == 3, f"{rel} has 3 pages" + ("" if pages == 3 else f" (found {pages})"))

    for rel in NEW_PAGES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        check(path.is_file(), f"{rel} exists")
        if not text:
            continue
        check(STRIPE_HOST not in text, f"{rel} has no {STRIPE_HOST}")
        head = head_html(text)
        check(GA4 in head, f"{rel} has {GA4} in head")
        doc = PageDoc()
        doc.feed(text)
        footer = " ".join(doc.footer_parts)
        check(LLC in footer and PO_BOX in footer, f"{rel} footer has the LLC and PO Box")
        lowered = text.lower()
        check("worldwide" not in lowered, f"{rel} has no worldwide")
        check(not re.search(r"\bCDK\b", text), f"{rel} has no bare CDK")
        check("Shield Kit" not in text and "/shield-kit/" not in text, f"{rel} has no Shield Kit")
        check("Family Planner" not in text and "family-planner" not in lowered, f"{rel} has no Family Planner link")
        check(doc.h1 == 1, f"{rel} has exactly one H1 ({doc.h1})")
        title, description = title_and_description(text)
        check(bool(canonical(text)), f"{rel} has a canonical")
        check(len(title) <= 60, f"{rel} title length {len(title)} <= 60")
        check(0 < len(description) <= 155, f"{rel} meta description length {len(description)} <= 155")
        for href, classes in doc.hrefs:
            if "hday-pay" not in classes and "hday-download" not in classes:
                continue
            bare = html.unescape(href).split("#", 1)[0]
            path_only = bare.split("?", 1)[0]
            if path_only.lower().endswith(".pdf"):
                check(path_only.startswith("/holiday/") and STRIPE_HOST not in bare, f"{rel} sample PDF link stays on the site: {path_only}")
                continue
            query = bare.split("?", 1)[1] if "?" in bare else ""
            check(
                path_only in PRODUCT_PATHS or path_only.rstrip("/").startswith(("/holiday/", "/journal/2027")),
                f"{rel} CTA stays on its own path: {bare}",
            )
            check(
                "utm_source=site" in query and "utm_medium=" in query and "utm_campaign=" in query and "utm_content=" in query,
                f"{rel} CTA carries the site UTM pattern: {bare}",
            )
            check(STRIPE_HOST not in bare, f"{rel} CTA does not use {STRIPE_HOST}")

    for rel in EDITED_PAGES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        current = stripe_hrefs(text)
        previous = stripe_hrefs(git_show(rel))
        check(current == previous, f"{rel} buy.stripe.com href set matches {MAIN}")
        found = pairs_hrefs(text)
        expected = list(PAIRS[rel])
        check(found == expected, f"{rel} pairs-with links use the cross-sell UTM pattern")
        check(all(href.startswith(("/",)) and UTM_CROSSSELL in href for href in found), f"{rel} pairs-with links stay on site paths")
        check(
            re.search(r'id="pairs".*?</section>\s*<section class="hday-section" id="support"', text, re.S) is not None,
            f"{rel} pairs section is immediately before support",
        )

    check(
        'href="/holiday/host-planner/sample/">Free sample</a>' in (ROOT / "holiday/host-planner/index.html").read_text(encoding="utf-8"),
        "host planner nav links the free sample",
    )
    check(
        'href="/holiday/kids-table/sample/">Free sample</a>' in (ROOT / "holiday/kids-table/index.html").read_text(encoding="utf-8"),
        "kids table nav links the free sample",
    )

    sites = site_dirs()
    check(bool(sites), "built _site exists (run jekyll build first)")
    for site in sites:
        sitemap_path = site / "sitemap.xml"
        check(sitemap_path.is_file(), f"{site.name} sitemap.xml exists")
        if not sitemap_path.is_file():
            continue
        locs = set()
        raw = sitemap_path.read_text(encoding="utf-8")
        for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", raw):
            locs.add(loc.rstrip("/"))
        for url in SITEMAP_URLS:
            check(url.rstrip("/") in locs, f"sitemap lists {url}")
        check("https://getcyberdadkit.com/holiday".rstrip("/") in locs or "https://getcyberdadkit.com/holiday" in locs, "sitemap still lists /holiday/")
        check("https://getcyberdadkit.com/holiday/trivia".rstrip("/") in locs, "sitemap still lists /holiday/trivia/")

        for rel in NEW_PAGES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            doc = PageDoc()
            doc.feed(text)
            urls = [href for href, _ in doc.hrefs] + doc.srcs
            for srcset in doc.srcsets:
                urls.extend(part.strip().split()[0] for part in srcset.split(",") if part.strip())
            for url in urls:
                targets = local_targets(html.unescape(url))
                if targets is None:
                    host = urlparse(url).netloc
                    check(host in SKIP_EXTERNAL_HOSTS, f"{rel} external link is not a product checkout: {url}")
                    continue
                if not targets and url.startswith("#"):
                    check(url[1:] in doc.ids, f"{rel} anchor {url} exists")
                    continue
                for target in targets:
                    check(built_has(site, target), f"{rel} link {url} resolves in {site.name}")

    print()
    if failed:
        print(f"{len(failed)} check(s) failed")
        return 1
    print(f"all checks passed ({len(NEW_PAGES)} pages, {len(SAMPLE_PDFS)} PDFs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
