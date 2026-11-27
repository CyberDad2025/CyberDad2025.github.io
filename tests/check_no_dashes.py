#!/usr/bin/env python3
"""Fail if public page sources contain an em dash (U+2014) or en dash (U+2013).

Scans tracked *.html and *.md files that render as pages, plus _includes and
_layouts (they are pulled into those pages). The file is read as UTF-8 source,
the same way other copy tests search page text, including titles.

Skipped directories: _site, node_modules, vendor, .git, .jekyll-cache,
_posts, scripts/_posts, _archive, _unpublished, tests, scripts, .github,
logs, assets (binaries live there; page HTML/MD under product trees is still
scanned). README.md is skipped because it is not a site page.

_posts are excluded because other dash rules in this repo do not cover blog
posts.

On origin/main at 8abcefce some public pages already contain these characters.
Those paths are listed in EXEMPT and are not failed here (and were not edited
in the checkout-line /sites/ cleanup). Everything else in scope must be clean,
including sites/index.html and all of paycheck-planner/.

This test is run the same way as the other checks: python3 tests/check_no_dashes.py
There is no GitHub Actions workflow that runs the tests/check_*.py suite.

Run: python3 tests/check_no_dashes.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHES = ("\u2014", "\u2013")
PAGE_SUFFIXES = {".html", ".htm", ".md", ".markdown", ".liquid"}
SKIP_DIR_PREFIXES = (
    "_site/",
    "node_modules/",
    "vendor/",
    "_posts/",
    "scripts/_posts/",
    "scripts/",
    "_archive/",
    "_unpublished/",
    "tests/",
    ".github/",
    "logs/",
)
SKIP_DIR_PARTS = {
    ".git",
    "_site",
    "node_modules",
    "vendor",
    ".jekyll-cache",
    "assets",
}
SKIP_EXACT = {
    "README.md",
}
# Pre-existing hits on 8abcefce, left untouched. sites/index.html is not exempt.
EXEMPT = {
    "about.md",
    "cyber_parenting_global_blog.html",
    "cyber_2025-07-15_1752577965.html",
    "sites/intake/index.html",
    "sites/examples/sampletown-auto/index.html",
    "sites/examples/sampletown-auto/privacy.html",
    "sites/examples/sampletown-motel/index.html",
    "sites/examples/sampletown-motel/privacy.html",
}


def tracked_page_files() -> list[str]:
    names = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    found = []
    for rel in names:
        if rel in SKIP_EXACT:
            continue
        if any(rel == p[:-1] or rel.startswith(p) for p in SKIP_DIR_PREFIXES):
            continue
        parts = set(Path(rel).parts)
        if parts & SKIP_DIR_PARTS:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        if path.suffix.lower() not in PAGE_SUFFIXES:
            continue
        found.append(rel)
    return found


def dash_hits(text: str) -> list[tuple[int, str, str]]:
    hits = []
    for i, ch in enumerate(text):
        if ch not in DASHES:
            continue
        line_no = text.count("\n", 0, i) + 1
        start = text.rfind("\n", 0, i) + 1
        end = text.find("\n", i)
        if end < 0:
            end = len(text)
        kind = "em" if ch == "\u2014" else "en"
        hits.append((line_no, kind, text[start:end].strip()))
    return hits


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok   " if ok else "FAIL ") + message)
        if not ok:
            failed.append(message)

    files = tracked_page_files()
    check(bool(files), f"found public page sources to scan ({len(files)} files)")
    check("sites/index.html" in files, "sites/index.html is in scope")
    planner = [f for f in files if f.startswith("paycheck-planner/")]
    check(bool(planner), f"paycheck-planner/ pages are in scope ({len(planner)} files)")
    for rel in ("sites/index.html", "paycheck-planner/index.html"):
        check(rel not in EXEMPT, f"{rel} is not exempt")

    scanned = 0
    for rel in files:
        path = ROOT / rel
        data = path.read_bytes()
        if b"\0" in data[:8192]:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            check(False, f"{rel} is not valid UTF-8")
            continue
        scanned += 1
        hits = dash_hits(text)
        if rel in EXEMPT:
            continue
        if hits:
            shown = "; ".join(f"line {n} ({kind})" for n, kind, _ in hits[:5])
            check(False, f"{rel} has no em or en dash ({len(hits)} hit(s): {shown})")
        else:
            check(True, f"{rel} has no em or en dash")

    check(scanned > 0, f"scanned {scanned} page sources")

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL DASH CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
