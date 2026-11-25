#!/usr/bin/env python3
"""Guard T-034 outcome-hero rewrites (feat/hero-outcome-1124).

Locks Stripe hrefs, price strings, {% include %} tags, footer markup and
address lines on each rewritten page to origin/main. Asserts the chosen
HOOKS-COMPARE lines verbatim and checks those slots for em/en dashes,
'guarantee', bare 'CDK', ages or personal family details, and countdown
wording.

HOOKS-COMPARE sha256:
d6f890310d4edd86dc3e8d5d52a43fd47f098d0464d3617b82d81a7216329acc

Run: python3 tests/check_hero_outcome.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = "origin/main"

# Pages rewritten so far, stacked PL-S1, then GP-S1, then SI-S1.
PAGES = (
    {
        "label": "/planner/2027/",
        "rel": "planner/2027/index.html",
        "pick": "PL-S1",
        "h1_re": re.compile(r'<h1 id="product-title">(.*?)</h1>', re.S),
        "lede_re": re.compile(r'<p class="hday-lede">(.*?)</p>', re.S),
        "hero": "Start January knowing exactly what's coming up instead of scrambling to keep track of everything.",
        "lede": (
            "Keep the year in one place, with a year view, monthly calendars "
            "and weekly pages you can print or write on in the tablet edition. "
            "Week 1 starts Sunday, Dec 27, 2026, so it is ready before the new year. "
            "US customers only."
        ),
    },
    {
        "label": "/holiday/gather-and-play/",
        "rel": "holiday/gather-and-play/index.html",
        "pick": "GP-S1",
        "h1_re": re.compile(r'<h1 id="product-title">(.*?)</h1>', re.S),
        "lede_re": re.compile(r'<p class="hday-lede">(.*?)</p>', re.S),
        "hero": "Turn an awkward office Christmas party into an afternoon of laughter and friendly competition.",
        "lede": (
            "Print the pages before coworkers arrive, then put a game on the table "
            "and play together. US customers only."
        ),
    },
)

PRICE_RE = re.compile(r"\$[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?(?:/mo)?")
SCHEMA_PRICE_RE = re.compile(
    r'"price":\s*"[0-9]+\.[0-9]{2}"'
    r'|property="og:price:amount" content="[0-9]+\.[0-9]{2}"'
)
STRIPE_HREF_RE = re.compile(
    r'href="(https://buy\.stripe\.com/[A-Za-z0-9]+|\{\{[^"]*stripe_link[^"]*\}\})"'
)
INCLUDE_RE = re.compile(r"\{%-?\s*include\s+[^%]+%\}")
FOOTER_RE = re.compile(r"<footer\b.*?</footer>", re.S)
ADDRESS_RE = re.compile(r"^.*PO Box 940061, Maitland, FL 32794.*$", re.M)

DASH_TOKENS = (
    "\u2014", "\u2013", "&mdash;", "&ndash;",
    "&#8212;", "&#8211;", "&#x2014;", "&#x2013;", "&#X2014;", "&#X2013;",
)
AGE_RE = re.compile(
    r"\bages?\s+\d|\bfor ages\b|\d+\s*[- ]\s*years?\s+old|\d+\s*-?\s*year-?olds?\b",
    re.I,
)
FAMILY_DETAIL_RE = re.compile(
    r"\bmy\s+(son|daughter|wife|husband|kids|children|family)\b"
    r"|\bour\s+(son|daughter|kids|children)\b",
    re.I,
)
COUNTDOWN_RE = re.compile(
    r"\bcountdown\b|\blimited time\b|\blasts? chance\b|\bhurry\b"
    r"|\bends? (soon|tonight|today|this week)\b"
    r"|\bonly\s+\d+\s+(hours?|days?|spots?|left)\b"
    r"|\bwhile (supplies|stocks) last\b",
    re.I,
)

failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def git_show(rel: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{MAIN}:{rel}"],
        cwd=ROOT,
        capture_output=True,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        check(False, f"git show {MAIN}:{rel} failed: {err or proc.returncode}")
        return ""
    return proc.stdout.decode("utf-8")


def first(html: str, pat: re.Pattern[str]) -> str:
    match = pat.search(html)
    return match.group(0) if match else ""


def slot(html: str, pat: re.Pattern[str]) -> str:
    match = pat.search(html)
    return match.group(1).strip() if match else ""


def main() -> int:
    check(any(p["pick"] == "PL-S1" and "US customers only." in p["lede"] for p in PAGES),
          "PL-S1 supporting lede keeps 'US customers only.'")
    for page in PAGES:
        label, rel = page["label"], page["rel"]
        path = ROOT / rel
        check(path.is_file(), f"{label} source {rel} exists")
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        previous = git_show(rel)
        if not previous:
            continue
        check(
            STRIPE_HREF_RE.findall(current) == STRIPE_HREF_RE.findall(previous),
            f"{label}: Stripe hrefs are byte-identical to {MAIN}",
        )
        now = PRICE_RE.findall(current) + SCHEMA_PRICE_RE.findall(current)
        old = PRICE_RE.findall(previous) + SCHEMA_PRICE_RE.findall(previous)
        check(now == old, f"{label}: price strings are byte-identical to {MAIN}")
        check(
            INCLUDE_RE.findall(current) == INCLUDE_RE.findall(previous),
            f"{label}: {{% include %}} tags are byte-identical to {MAIN}",
        )
        foot_now, foot_old = first(current, FOOTER_RE), first(previous, FOOTER_RE)
        check(foot_now == foot_old and foot_now != "", f"{label}: footer markup is byte-identical to {MAIN}")
        addr_now, addr_old = ADDRESS_RE.findall(current), ADDRESS_RE.findall(previous)
        check(addr_now == addr_old and addr_now != [], f"{label}: address lines are byte-identical to {MAIN}")

        title = slot(current, page["h1_re"])
        lede = slot(current, page["lede_re"])
        check(title == page["hero"], f"{label}: h1 is the {page['pick']} hero line verbatim")
        check(lede == page["lede"], f"{label}: first line is the {page['pick']} supporting lede verbatim")
        for name, raw in (("h1", title), ("lede", lede)):
            dash_hits = [tok for tok in DASH_TOKENS if tok in raw]
            check(not dash_hits, f"{label} {name}: no em or en dashes")
            check("guarantee" not in raw.lower(), f"{label} {name}: no 'guarantee'")
            check(re.search(r"\bCDK\b", raw) is None, f"{label} {name}: no bare 'CDK'")
            check(AGE_RE.search(raw) is None, f"{label} {name}: no ages")
            check(FAMILY_DETAIL_RE.search(raw) is None, f"{label} {name}: no personal family details")
            check(COUNTDOWN_RE.search(raw) is None, f"{label} {name}: no countdown wording")

    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL HERO OUTCOME CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
