#!/usr/bin/env python3
"""Browser checks for the planner marketing pass, against a BUILT site. Run: python3 tests/check_planner_marketing_browser.py SITE_DIR [SHOTS_DIR]
Clicks are observed by a test listener registered AFTER the page's own listeners (window bubble phase) that records the anchor's
computed href at activation time and calls preventDefault, so no navigation is attempted. Uses system Chrome via Playwright with --host-resolver-rules mapping GA, Tag Manager and Stripe hosts to 127.0.0.1. The site is served
by request interception on https://getcyberdadkit.com (nothing live is contacted). Any request to buy.stripe.com or checkout.stripe.com is
RECORDED AND ABORTED, never fulfilled and never sent (the host maps to 127.0.0.1 anyway). Checks per page at 375 and 1280 wide:
exactly one clear Buy button above the fold (rect inside the viewport) whose href equals the yml value; click attribution (client_reference_id,
utm pass-through, qa_ prefix, plain href at load, GA event fields); reduced layout shift risks are not measured here."""
import json, re, sys, pathlib
from playwright.sync_api import sync_playwright

SITE = pathlib.Path(sys.argv[1]); SHOTS = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
ROOT = pathlib.Path(__file__).resolve().parents[1]
yml = (ROOT / "_data/paycheck_planner.yml").read_text()
URL = {"planner": re.search(r'^stripe_url_planner:\s*"([^"]+)"', yml, re.M).group(1), "bundle": re.search(r'^stripe_url_bundle:\s*"([^"]+)"', yml, re.M).group(1)}
BASE = "https://getcyberdadkit.com"
TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".png": "image/png", ".webp": "image/webp", ".xml": "application/xml"}
fails, results, stripe_seen, other = [], {}, [], []
def check(c, m):
    print(("PASS " if c else "FAIL ") + m)
    if not c: fails.append(m)

def handler(route):
    u = route.request.url
    if u.startswith("https://buy.stripe.com/") or u.startswith("https://checkout.stripe.com/"):
        stripe_seen.append(u); return route.abort()
    if u.startswith(BASE):
        path = u[len(BASE):].split("?")[0].split("#")[0]
        f = SITE / path.lstrip("/")
        if path.endswith("/"): f = f / "index.html"
        if f.is_file(): return route.fulfill(status=200, content_type=TYPES.get(f.suffix, "application/octet-stream"), body=f.read_bytes())
        return route.fulfill(status=404, body="nf")
    other.append(u); return route.abort()

HOOK = '''() => { window.__clicks = []; window.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[href^="https://buy.stripe.com/"]'); if (a) { window.__clicks.push(a.href); e.preventDefault(); } }, false); }'''
PAGES = [("sales", "/paycheck-planner/", ["#pp-buy-planner"], "planner"), ("bundle", "/paycheck-planner/bundle/", ["#pp-buy-bundle"], "bundle"),
         ("sample", "/paycheck-planner/sample/", ["#pp-buy-planner"], "planner"), ("refund", "/paycheck-planner/refund/", [], None),
         ("delivered", "/paycheck-planner/delivered/", [], None)]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--host-resolver-rules=MAP www.googletagmanager.com 127.0.0.1, MAP www.google-analytics.com 127.0.0.1, MAP buy.stripe.com 127.0.0.1, MAP checkout.stripe.com 127.0.0.1"])
    for w, h in ((375, 812), (1280, 800)):
        ctx = b.new_context(viewport={"width": w, "height": h}); ctx.route("**/*", handler)
        for name, path, btns, key in PAGES:
            pg = ctx.new_page(); pg.goto(BASE + path, wait_until="load")
            allbuy = pg.query_selector_all('a[href^="https://buy.stripe.com/"]')
            above = [a for a in allbuy if a.is_visible() and (a.bounding_box() or {}).get("y", 9e9) + (a.bounding_box() or {}).get("height", 0) <= h]
            if key:
                hrefs = [a.get_attribute("href") for a in above]
                check(len(above) == 1 and hrefs == [URL[key]], f"[{name} {w}px] exactly one Buy above the fold, href equals yml ({len(above)} found)")
            else:
                check(len(allbuy) == 0, f"[{name} {w}px] no Buy button (not appropriate on this page)")
            if SHOTS: pg.screenshot(path=str(SHOTS / f"{name}-{w}.png"))
            pg.close()
        ctx.close()
    # click attribution (1280 only)
    for qa in (False, True):
        ctx = b.new_context(viewport={"width": 1280, "height": 800}); ctx.route("**/*", handler)
        for name, path, btns, key in PAGES[:3]:
            q = "?utm_source=pinterest&utm_medium=social&utm_campaign=pp-test&utm_content=pin1&utm_term=budget&other=x" + ("&cdk_qa=1" if qa else "")
            pg = ctx.new_page(); pg.goto(BASE + path + q, wait_until="load")
            sel = btns[0]; plain = pg.get_attribute(sel, "href")
            check(plain == URL[key], f"[{name} qa={qa}] href is the plain yml URL at load")
            pg.evaluate(HOOK)
            pg.click(sel); pg.wait_for_timeout(200)
            new = pg.evaluate("() => window.__clicks")
            check(len(new) == 1, f"[{name} qa={qa}] one click recorded; navigation prevented by the test hook (Stripe never contacted)")
            u = new[0] if new else ""
            m = re.match(re.escape(URL[key]) + r"\?client_reference_id=((?:qa|pp)_[0-9a-f]{24})&utm_source=pinterest&utm_medium=social&utm_campaign=pp-test&utm_content=pin1&utm_term=budget$", u)
            check(bool(m) and m.group(1).startswith("qa_" if qa else "pp_") and "other=" not in u, f"[{name} qa={qa}] URL has client_reference_id ({'qa_' if qa else 'pp_'} prefix) and the five utm_* only: {re.sub(r'[0-9a-f]{24}', 'X'*24, u).replace(URL[key], '<yml>')}")
            dl = pg.evaluate("() => (window.dataLayer||[]).map(a => Array.prototype.slice.call(a))")
            sets = [i for i, e in enumerate(dl) if e[0] == "set" and isinstance(e[1], dict) and "client_reference_id" in e[1]]
            evi = [i for i, e in enumerate(dl) if e[0] == "event" and e[1] in ("buy_click", "begin_checkout")]
            ref = dl[sets[0]][1]["client_reference_id"] if sets else None
            check(len(sets) == 1 and len(evi) == 2 and sets[0] < min(evi) and ref == (m.group(1) if m else None), f"[{name} qa={qa}] gtag set client_reference_id fires once, before both buy_click and begin_checkout, with the same id")
            bcl = [dl[i] for i in evi if dl[i][1] == "buy_click"]
            check(bool(bcl) and bcl[0][2].get("link_url") == URL[key], f"[{name} qa={qa}] buy_click link_url is still the plain URL")
            bc = [dl[i][2] for i in evi if dl[i][1] == "begin_checkout"]
            check(bool(bc) and bc[0].get("items", [{}])[0].get("item_id") == URL[key].rsplit("/", 1)[1], f"[{name} qa={qa}] begin_checkout item_id still the plain link id")
            pg.close()
        ctx.close()
    # second click on same page view reuses the id; internal links never rewritten
    ctx = b.new_context(viewport={"width": 1280, "height": 800}); ctx.route("**/*", handler)
    pg = ctx.new_page(); pg.goto(BASE + "/paycheck-planner/?utm_source=x", wait_until="load")
    internal = pg.evaluate("() => Array.from(document.querySelectorAll('a[href^=\"/\"]')).map(a => a.getAttribute('href'))")
    check(all("utm_" not in h and "client_reference_id" not in h for h in internal), "internal links carry no UTM or client_reference_id after load")
    pg.evaluate(HOOK); pg.click("#pp-buy-planner"); pg.wait_for_timeout(200); pg.click("#pp-buy-bundle"); pg.wait_for_timeout(200)
    ids = [re.search(r"client_reference_id=([^&]+)", u).group(1) for u in pg.evaluate("() => window.__clicks")]
    check(len(ids) == 2 and ids[0] == ids[1], "one opaque id per page view across both Buy buttons")
    b.close()
check(len(stripe_seen) == 0, "no request to buy.stripe.com or checkout.stripe.com was attempted at all")
check(not any("stripe" in u for u in other), "no other Stripe request")
print(f"Stripe request attempts: {len(stripe_seen)}; other aborted external requests: {len(other)}")
print("ALL BROWSER CHECKS PASSED" if not fails else f"FAILED {len(fails)}")
sys.exit(1 if fails else 0)
