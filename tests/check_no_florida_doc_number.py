#!/usr/bin/env python3
"""The retired filing identifier is absent, and storefront footers use four lines.

Scans every tracked text file except this one. The identifier is matched as
L2500046 plus four digits so this file does not contain the literal. Each
listed page must show the four footer lines once, with the legal name once.

Run: python3 tests/check_no_florida_doc_number.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = "tests/check_no_florida_doc_number.py"
NUMBER = re.compile(r"L2500046\d{4}")
OLD_PHRASE = "Florida document " + "number"
TEXT_SUFFIXES = {
    ".html", ".htm", ".md", ".markdown", ".liquid", ".xml", ".yml", ".yaml",
    ".js", ".mjs", ".css", ".txt", ".json", ".py", ".svg", ".csv", ".toml",
}
FOOTER_LINES = (
    "<p>CyberDadKit © 2026</p>",
    "<p>CyberDad Kit LLC</p>",
    "<p>PO Box 940061, Maitland, FL 32794</p>",
    '<p><a href="mailto:ruel@getcyberdadkit.com">ruel@getcyberdadkit.com</a></p>',
)
PAGES = (
    "shop/index.html",
    "holiday/index.html",
    "holiday/sample/index.html",
    "holiday/refund/index.html",
    "holiday/trivia/index.html",
    "holiday/trivia/sample/index.html",
    "holiday/trivia/refund/index.html",
    "holiday/host-planner/index.html",
    "holiday/host-planner/refund/index.html",
    "holiday/kids-table/index.html",
    "holiday/kids-table/refund/index.html",
    "holiday/table-set/index.html",
    "holiday/table-set/refund/index.html",
    "holiday/host-kit/index.html",
    "holiday/host-kit/refund/index.html",
    "journal/2027/index.html",
    "journal/2027/sample/index.html",
    "journal/2027/refund/index.html",
    "faq/index.html",
    "support/index.html",
    "refund-policy/index.html",
)


def footer(html: str) -> str:
    match = re.search(r"<footer\b.*?</footer>", html, re.S)
    return match.group(0) if match else ""


def tracked_text_files() -> list[str]:
    names = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    found = []
    for rel in names:
        if rel == SELF:
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.suffix != "":
            continue
        found.append(rel)
    return found


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + message)
        if not ok:
            failed.append(message)

    for rel in tracked_text_files():
        path = ROOT / rel
        data = path.read_bytes()
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="ignore")
        number_hit = NUMBER.search(text)
        check(number_hit is None, f"{rel} has no retired filing identifier" + ("" if number_hit is None else f" at {number_hit.group(0)}"))
        check(OLD_PHRASE.lower() not in text.lower(), f"{rel} has no retired filing phrase")

    for rel in PAGES:
        path = ROOT / rel
        check(path.is_file(), f"{rel} exists")
        if not path.is_file():
            continue
        block = footer(path.read_text(encoding="utf-8"))
        check(bool(block), f"{rel} has a footer")
        for line in FOOTER_LINES:
            check(block.count(line) == 1, f"{rel} footer has one identity line: {line}")
        check(block.count("CyberDad Kit LLC") == 1, f"{rel} footer names the LLC once")
        check("CyberDad Kit LLC," not in block, f"{rel} footer has no combined LLC address line")

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL FILING-IDENTIFIER CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
