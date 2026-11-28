#!/usr/bin/env python3
"""What buyers say include: renders nothing unless a data entry has permission: true.

Proves:
- the live _data/what_buyers_say.yml list is empty
- the include is used on /start/ and /paycheck-planner/
- rendering the include with empty data produces no heading and no box
- a fixture with permission: true renders the quote
- a fixture with permission: false renders nothing

Run: python3 tests/check_what_buyers_say.py
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ROOT / "_includes" / "what-buyers-say.html"
DATA = ROOT / "_data" / "what_buyers_say.yml"
FIXTURES = ROOT / "tests" / "fixtures" / "what_buyers_say"
SALES = ROOT / "paycheck-planner" / "index.html"
START = ROOT / "start" / "index.html"
INCLUDE_TAG = "{% include what-buyers-say.html %}"

failed: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("ok   " if ok else "FAIL ") + message)
    if not ok:
        failed.append(message)


def render(data_path: Path) -> str:
    helper = ROOT / "tests" / "render_what_buyers_say.rb"
    cmd = (
        "source /workspace/cdk/platform/tools/ruby-env.sh >/dev/null && "
        "ruby "
        + shlex.quote(str(helper))
        + " "
        + shlex.quote(str(data_path))
        + " "
        + shlex.quote(str(INCLUDE))
    )
    proc = subprocess.run(["bash", "-lc", cmd], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"liquid render failed: {proc.stderr or proc.stdout}")
    return proc.stdout


def main() -> int:
    check(INCLUDE.is_file(), "what-buyers-say include exists")
    check(DATA.is_file(), "what_buyers_say.yml exists")
    check("permission == true" in INCLUDE.read_text(encoding="utf-8"), "include gates on permission == true")
    check("What buyers say" in INCLUDE.read_text(encoding="utf-8"), "include heading is What buyers say")
    inc = INCLUDE.read_text(encoding="utf-8")
    check("parents" not in inc.lower() and "family" not in inc.lower() and "child" not in inc.lower(), "include has no family or child wording")
    check("guarantee" not in inc.lower() and "\u2014" not in inc and "\u2013" not in inc, "include has no guarantee and no em or en dashes")

    live_lines = [ln.strip() for ln in DATA.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")]
    check(live_lines == ["[]"], f"live data file is empty: {live_lines!r}")

    check(INCLUDE_TAG in SALES.read_text(encoding="utf-8"), "sales page includes what-buyers-say")
    check(INCLUDE_TAG in START.read_text(encoding="utf-8"), "start page includes what-buyers-say")

    empty_html = render(FIXTURES / "empty.yml")
    check(empty_html.strip() == "", f"empty data renders nothing (got {empty_html!r})")
    check("What buyers say" not in empty_html and "<section" not in empty_html, "empty data has no heading and no box")

    live_html = render(DATA)
    check(live_html.strip() == "", f"live empty data file renders nothing (got {live_html!r})")

    true_html = render(FIXTURES / "permission_true.yml")
    check("What buyers say" in true_html, "permission true renders the heading")
    check("The sample plan showed me which bills the next check covers." in true_html, "permission true renders the quote")
    check("A. B." in true_html, "permission true renders the name")
    check("permission is false" not in true_html, "permission true fixture has no false quote")

    false_html = render(FIXTURES / "permission_false.yml")
    check(false_html.strip() == "", f"permission false renders nothing (got {false_html!r})")
    check("This quote must not render because permission is false." not in false_html, "permission false quote is omitted")

    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL WHAT BUYERS SAY CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
