#!/usr/bin/env python3
"""Checks for the 2027 Family Planner storefront (/planner/2027/), feat/planner-2027.

The Buy href reads _data/planner_2027.yml stripe_link. The data file and the public
pages carry no Drive delivery link (delivery is shown only on Stripe's confirmation
screen). The banner states the price once; social descriptions carry no price.

Run: python3 tests/check_planner_2027.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_data" / "planner_2027.yml"
PAGE = ROOT / "planner" / "2027" / "index.html"
REFUND = ROOT / "planner" / "2027" / "refund" / "index.html"
CARD_PAGE = ROOT / "holiday" / "index.html"
BANNER = ('<p><strong>Available only to customers located in the United States.</strong> '
          'The 2027 Family Planner is USD $9.99 one-time, US customers only. Digital download only. Nothing is shipped.</p>')
failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def meta(html: str, attr: str, name: str) -> str:
    m = re.search(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)">', html)
    return m.group(1) if m else ""


data = DATA.read_text(encoding="utf-8")
keys = re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:", data, re.M)
check(keys == ["stripe_link"], f"_data/planner_2027.yml has only the stripe_link key ({keys})")
check(not any("drive" in k.lower() for k in keys), "_data/planner_2027.yml has no drive key")
check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)", data, re.I), "_data/planner_2027.yml has no Google Drive URL")
check(re.search(r'^stripe_link: "https://buy\.stripe\.com/[A-Za-z0-9]+"$', data, re.M) is not None, "stripe_link is one buy.stripe.com URL")

html = PAGE.read_text(encoding="utf-8")
refund = REFUND.read_text(encoding="utf-8")
card = re.search(r'<article class="mp-card" id="planner-2027".*?</article>', CARD_PAGE.read_text(encoding="utf-8"), re.S)
card = card.group(0) if card else ""
for label, text in (("/planner/2027/", html), ("/planner/2027/refund/", refund), ("/holiday/ planner card", card)):
    check(bool(text), f"{label} exists")
    check(not re.search(r"(?:drive|docs)\.(?:google|usercontent)|drive_?link", text, re.I), f"{label} has no Drive delivery link")
    check("\u2014" not in text and "\u2013" not in text and "guarantee" not in text.lower(), f"{label} has no dashes or guarantee")
check(html.count(BANNER) == 1, "banner states the US-only price line exactly once")
check("{%- assign planner = site.data.planner_2027 -%}" in html and html.count('href="{{ planner.stripe_link }}"') == 1, "product page Buy href reads _data/planner_2027.yml")
check('href="{{ site.data.planner_2027.stripe_link }}"' in card, "/holiday/ card Buy href reads _data/planner_2027.yml")
for attr, name in (("property", "og:description"), ("name", "twitter:description")):
    check("9.99" not in meta(html, attr, name) and meta(html, attr, name) != "", f"{name} has no price")
check(meta(refund, "property", "og:title") == "Refund policy: 2027 Family Planner | CyberDad Kit", "refund og:title")
check(meta(refund, "property", "og:description") == "Refund policy for the 2027 Family Planner digital download from CyberDad Kit.", "refund og:description")
check(card.count(">See what's inside</a>") == 1 and 'href="/planner/2027/"' in card, "card link reads See what's inside")
for label, text in (("/planner/2027/", html), ("/planner/2027/refund/", refund)):
    check("CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794" in text, f"{label} uses the CyberDad Kit LLC address line")

if failed:
    print(f"FAILED {len(failed)} check(s)")
    sys.exit(1)
print("ALL PLANNER 2027 CHECKS PASSED")
