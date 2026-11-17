#!/usr/bin/env python3
"""/shop/ after the one-page holiday shop (feat/holiday-one-page-1117).

The old /shop/ catalog page was retired: /shop/ is now a noindex redirect
stub to /holiday/ that keeps the query string and hash. The catalog checks
that used to live here pinned the old page content; the shop layout is now
covered by tests/check_holiday_one_page.py. Restore the previous version of
this file with the rollback (revert the merge commit).

Run: python3 tests/check_shop_page.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    failed: list[str] = []

    def check(ok: bool, msg: str) -> None:
        print(("ok  " if ok else "FAIL") + " " + msg)
        if not ok:
            failed.append(msg)

    html = (ROOT / "shop" / "index.html").read_text(encoding="utf-8")
    check(html.startswith("---\nlayout: null\nsitemap: false\n---\n"), "front matter is layout null, sitemap: false")
    check('content="noindex, follow"' in html, "/shop/ is noindex, follow")
    check('rel="canonical" href="https://getcyberdadkit.com/holiday/"' in html, "canonical is /holiday/")
    check('window.location.replace("/holiday/" + window.location.search + h)' in html, "JS redirect keeps the query string")
    check('var h = window.location.hash || "";' in html, "JS redirect keeps the incoming hash")
    check('content="0; url=/holiday/"' in html, "meta refresh fallback goes to /holiday/")
    check("buy.stripe.com" not in html, "no Buy links on the stub")
    check("PO Box 940061, Maitland, FL 32794" in html, "footer has the PO Box")
    check("\u2014" not in html and "\u2013" not in html and not re.search(r"\bCDK\b|guarantee|worldwide", html), "no banned strings")
    built = ROOT / "_site" / "sitemap.xml"
    if built.is_file():
        check("https://getcyberdadkit.com/shop/" not in built.read_text(encoding="utf-8"), "built sitemap no longer lists /shop/")
    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL SHOP REDIRECT CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
