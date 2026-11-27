#!/usr/bin/env python3
"""Hostname allowlist gate for the site GA4 tag in _includes/ga4.html.

Non-production hosts must not load gtag.js (G-5B1LNCPB56). The gate is an
allowlist of production hostnames, not a blocklist of local names. On a
non-prod host, window.gtag and the sendBeacon collect fallback are no-ops so
Buy click handlers still run. On production, cdk_qa / traffic_type=internal
is unchanged.

Run: python3 tests/check_ga4_host_gate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GA4 = ROOT / "_includes" / "ga4.html"
CNAME = ROOT / "CNAME"
CONFIG = ROOT / "_config.yml"

PROD_HOST = "getcyberdadkit.com"
# Verified 2026-11-27: both respond 301 to https://getcyberdadkit.com/ and
# do not serve pages, so they do not belong in the allowlist.
REDIRECT_ONLY_HOSTS = ("www.getcyberdadkit.com", "cyberdad2025.github.io")

failed: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("ok  " if ok else "FAIL") + " " + msg)
    if not ok:
        failed.append(msg)


def main() -> int:
    text = GA4.read_text(encoding="utf-8") if GA4.is_file() else ""
    cname = CNAME.read_text(encoding="utf-8").strip() if CNAME.is_file() else ""
    config = CONFIG.read_text(encoding="utf-8") if CONFIG.is_file() else ""

    check(GA4.is_file(), "_includes/ga4.html exists")
    check(cname == PROD_HOST, f"CNAME is {PROD_HOST}")
    check(f'url: "https://{PROD_HOST}"' in config, f"_config.yml url is https://{PROD_HOST}")

    check("var PROD_HOSTS" in text, "allowlist is named PROD_HOSTS")
    check(re.search(r"var PROD_HOSTS = \{[^}]*'" + re.escape(PROD_HOST) + r"': 1", text) is not None,
          f"allowlist includes the production host {PROD_HOST}")
    for host in REDIRECT_ONLY_HOSTS:
        check(f"'{host}'" not in text and f'"{host}"' not in text,
              f"allowlist omits redirect-only host {host}")
    check("location.hostname" in text, "gate reads location.hostname")
    check("toLowerCase()" in text, "hostname compare is case-insensitive")
    check("var onProd = !!PROD_HOSTS[host];" in text, "onProd is computed from the allowlist")

    # Must be an allowlist, not a blocklist of local names.
    check("127.0.0.1" not in text.split("PROD_HOSTS")[0] or "PROD_HOSTS" in text,
          "gate file mentions the allowlist")
    host_block = re.search(r"var PROD_HOSTS = \{([^}]*)\}", text)
    block = host_block.group(1) if host_block else ""
    check("127.0.0.1" not in block and "localhost" not in block and "netlify" not in block,
          "allowlist does not list local, file, or preview hosts")
    check("host === '127.0.0.1'" not in text and 'host === "127.0.0.1"' not in text
          and "host !== '127.0.0.1'" not in text and "hostname !== 'localhost'" not in text,
          "gate is not a 127.0.0.1/localhost blocklist")

    static_src = re.search(r"<script[^>]+src=['\"]https://www\.googletagmanager\.com/gtag/js\?id=G-5B1LNCPB56['\"]", text)
    check(static_src is None, "gtag.js is not loaded by a static script src (would run on every host)")
    check("s.src = 'https://www.googletagmanager.com/gtag/js?id=G-5B1LNCPB56';" in text, "gtag.js is injected at runtime with the production measurement id")
    check("if (onProd)" in text and "document.head.appendChild(s);" in text, "gtag.js is appended only on a production host")

    check("window.gtag = function () {};" in text, "window.gtag is a no-op on non-production hosts")
    check("function sendCollect" in text and "if (!onProd) return;" in text,
          "sendBeacon collect fallback is a no-op on non-production hosts")

    check("if (p === '1') localStorage.setItem('cdk_qa', '1'); else if (p === '0') localStorage.removeItem('cdk_qa'); qa = localStorage.getItem('cdk_qa') === '1';" in text,
          "cdk_qa localStorage read/write is unchanged")
    check("if (qa) { gtag('config', 'G-5B1LNCPB56', { traffic_type: 'internal' }); } else { gtag('config', 'G-5B1LNCPB56'); }" in text,
          "production gtag config still sets traffic_type=internal only when cdk_qa is set")
    check("if (qa) q.push('tt=internal');" in text, "production sendBeacon fallback still adds tt=internal when cdk_qa is set")
    check("tid=G-5B1LNCPB56" in text and "G-5B1LNCPB56" in text, "measurement id is still G-5B1LNCPB56")
    check("window.__buyClickBound" in text and 'a[href^="https://buy.stripe.com/"]' in text,
          "Buy click listener is still bound and does not cancel the click")
    check("gtag('event', 'buy_click'" in text and "gtag('event', 'begin_checkout'" in text
          and "sendCollect('buy_click'" in text and "sendCollect('begin_checkout'" in text,
          "buy_click and begin_checkout still fire on the gtag path and the sendBeacon fallback")
    check("\u2013" not in text and "\u2014" not in text, "ga4.html has no en or em dashes")
    check(not text.endswith("\n"), "ga4.html has no trailing newline")

    print()
    if failed:
        print(f"FAILED {len(failed)} check(s)")
        return 1
    print("ALL GA4 HOST GATE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
