#!/usr/bin/env python3
"""Pins the home page Paycheck Planner block (_includes/home-planner-hero.html, included once near the top of index.html).
Source checks always run. With --site DIR (a built site) it also loads / in headless Chrome at 375 and 1280 (GA and Stripe hosts mapped to
127.0.0.1, any Stripe request aborted, never sent), checks one Buy sits above the fold with the yml href, and checks the click attribution.
Run: python3 tests/check_planner_home_hero.py [--site /path/to/_site] [--shots DIR]
"""
from __future__ import annotations
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fails = []
def check(c, m):
    print(("PASS " if c else "FAIL ") + m)
    if not c: fails.append(m)
def rd(p): return Path(p).read_text(encoding="utf-8")
home, inc = rd(ROOT / "index.html"), rd(ROOT / "_includes/home-planner-hero.html")
yml = rd(ROOT / "_data/paycheck_planner.yml")
URL = re.search(r'^stripe_url_planner:\s*"([^"]+)"', yml, re.M).group(1)
TAG = "{% include home-planner-hero.html %}"

# Share image (CoS ruling 2026-11-25): home og:image and twitter:image are the planner OG card. Title and description stay as on main, no prices in preview text.
_fm = home.split("---", 2)[1]
check("path: /paycheck-planner/assets/paycheck-planner-og-1200x630.png" in _fm and "width: 1200" in _fm and "height: 630" in _fm, "home front matter image is the planner OG card, 1200x630")
check((ROOT / "paycheck-planner/assets/paycheck-planner-og-1200x630.png").is_file(), "the planner OG image file exists")
_alt = re.search(r'^\s+alt:\s*"([^"]+)"', _fm, re.M)
check(bool(_alt) and "Paycheck Planner" in _alt.group(1) and not re.search(r"\$|\d+\.\d\d|price", _alt.group(1), re.I), "home og:image alt describes the planner and has no price")
check("title: Website rebuilds for small businesses\n" in _fm and "description: We rebuild outdated business websites into fast, mobile-friendly sites." in _fm, "home title and description are unchanged")
check(home.count(TAG) == 1, "home includes the planner block once")
check(home.index("{% include home-header.html %}") < home.index(TAG) < home.index('<section class="hero">'), "planner block sits after the header include and before the existing hero section")
check('href="{{ pp.stripe_url_planner }}"' in inc and "{%- assign pp = site.data.paycheck_planner -%}" in inc and "buy.stripe.com" not in inc and "checkout.stripe.com" not in inc, "Buy href reads _data/paycheck_planner.yml, no literal Stripe URL")
check('data-pp-ref="planner"' in inc and 'data-price="14.99"' in inc and 'data-list-id="home-planner"' in inc and 'data-product="Paycheck Planner"' in inc, "Buy carries data-pp-ref and the GA data attributes")
check(inc.count('<script src="/paycheck-planner/assets/paycheck-planner.js" defer></script>') == 1, "block loads the shared planner JS once (click attribution)")
check(">Get the Paycheck Planner, $14.99</a>" in inc, "Buy label is exact")
check("US and Canada customers only" in inc and "Prices in USD" in inc, "US and Canada wording and USD note present")
check('href="/paycheck-planner/"' in inc and not re.search(r'href="/[^"]*utm_', inc), "internal link to /paycheck-planner/ has no UTM")
check(not re.search(r"[\u2014\u2013]|&mdash;|&ndash;", inc), "no em or en dash")
vis = re.sub(r"(?s)<(style|script)\b.*?</\1>|\{%-? comment -?%\}.*?\{%-? endcomment -?%\}", "", inc)
check(not re.search(r"guarantee|\bCDK\b|countdown|limited time|hurry|\bfamil(?:y|ies)\b|\bkids?\b", vis, re.I), "no guarantee, bare CDK, urgency or family wording")
check(set(re.findall(r"\$\d+(?:\.\d+)?", inc)) == {"$14.99"}, "the only price is $14.99")
check("<h1" not in inc and "<h2" in inc, "block uses an h2 (the home page keeps its single h1)")
check(not re.search(r"<meta|og:|application/ld", inc), "block adds no meta, og or schema (no prices in meta)")
check(home.count("<h1") == 1, "home still has one h1")
check("pp-home-friday" not in home and "pp-home-cta" not in home and 'id="holiday-picks"' in home, "the old lower planner callout is removed (one planner promo on home) and the holiday section stays")
check("CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794" in rd(ROOT / "_includes/paycheck-planner-footer.html"), "publisher line unchanged in the planner footer")

# ---- Video Producer 4x5 hero video (silent) with a WebP poster
A = ROOT / "paycheck-planner/assets"
import hashlib, subprocess
mp4, poster = A / "hero-paycheck-planner-4x5.mp4", A / "hero-paycheck-planner-4x5-poster.webp"
check(mp4.is_file() and hashlib.sha256(mp4.read_bytes()).hexdigest() == "ccb77fd1a5895a3687fba993528b9180b1d232d7e3a3f6f6a4280c1c4a0638d8", "MP4 is the Video Producer re-render (sha256 ccb77fd1...)")
probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.split()
check(probe == ["video,1080,1350"], f"MP4 is 1080x1350 with no audio stream ({probe})")
check(poster.is_file() and poster.stat().st_size < 120 * 1024, f"poster WebP exists and is under 120 KB ({poster.stat().st_size if poster.is_file() else 0} bytes)")
m = re.search(r"<video [^>]*>", inc)
tag = m.group(0) if m else ""
check(all(a in tag for a in (" muted", " autoplay", " loop", " playsinline", 'preload="none"', 'data-src="/paycheck-planner/assets/hero-paycheck-planner-4x5.mp4"', 'width="1080"', 'height="1350"', 'poster="/paycheck-planner/assets/hero-paycheck-planner-4x5-poster.webp"', "data-pp-video")) and "controls" not in tag, "video has muted autoplay loop playsinline preload=metadata, width/height and the poster")
check(inc.count("<video") == 1 and inc.count('/paycheck-planner/assets/hero-paycheck-planner-4x5.mp4') == 1 and "<source" not in inc and "16x9" not in inc and "hero-paycheck-planner.mp4" not in inc, "one video source, the 4x5 MP4 (no 16:9 file)")
check('<img src="/paycheck-planner/assets/hero-paycheck-planner-4x5-poster.webp" width="720" height="900"' in inc, "video fallback is the poster image with width and height")
check("aspect-ratio: 4 / 5" in inc and "<figcaption>Sample numbers</figcaption>" in inc and inc.count("<figure") == 1, "media box reserves 4:5 space (no layout shift) and carries the Sample numbers caption")
js = rd(ROOT / "paycheck-planner/assets/paycheck-planner.js")
check("video[data-pp-video][data-src]" in js and "addEventListener('load'" in js and js.index("function attachVideos") < js.index("1a. Reduced motion"), "JS attaches the MP4 only after the load event and returns early under prefers-reduced-motion")
check("prefers-reduced-motion: reduce" in js and "video[data-pp-video]" in js and "v.pause()" in js and "removeAttribute('autoplay')" in js, "JS shows the poster only (pause, no autoplay or loop) under prefers-reduced-motion")
check(not any(f.suffix.lower() in (".xlsx", ".pdf", ".zip", ".csv") for f in A.rglob("*")) and sorted(f.name for f in A.glob("*.mp4")) == ["hero-paycheck-planner-4x5.mp4", "page-paycheck-planner-demo.mp4"], "planner asset MP4s are the home 4x5 hero and the page demo loop, no xlsx, pdf or zip")

if "--site" in sys.argv:
    site = Path(sys.argv[sys.argv.index("--site") + 1]); shots = Path(sys.argv[sys.argv.index("--shots") + 1]) if "--shots" in sys.argv else None
    built = rd(site / "index.html")
    check(f'id="pp-home-buy-planner" href="{URL}"' in built and "{{" not in built.split("</style>")[-1][:3000], "[built] home Buy href equals the yml value")
    check("/paycheck-planner/assets/paycheck-planner.js" in built, "[built] planner JS referenced")
    def _meta(k):
        m = re.search(r'<meta (?:property|name)="' + re.escape(k) + r'" content="([^"]*)"', built)
        return m.group(1) if m else ""
    OG = "https://getcyberdadkit.com/paycheck-planner/assets/paycheck-planner-og-1200x630.png"
    check(_meta("og:image") == OG and _meta("twitter:image") == OG, "[built] home og:image and twitter:image are the planner OG card")
    check(_meta("og:image:width") == "1200" and _meta("og:image:height") == "630" and _meta("twitter:card") == "summary_large_image", "[built] home og:image is 1200x630 and twitter:card stays summary_large_image")
    check("Paycheck Planner" in _meta("og:image:alt") and "Paycheck Planner" in _meta("twitter:image:alt"), "[built] home image alt text is planner-appropriate")
    check(_meta("og:title") == "Website rebuilds for small businesses" and not re.search(r"\$\d", _meta("og:title") + _meta("og:description") + _meta("twitter:title") + _meta("twitter:description")), "[built] home og:title unchanged and no price in preview text")
    from playwright.sync_api import sync_playwright
    BASE = "https://getcyberdadkit.com"
    TYPES = {".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".xml": "application/xml"}
    stripe, other = [], []
    def handler(route):
        u = route.request.url
        if "stripe.com" in u: stripe.append(u); return route.abort()
        if u.startswith(BASE):
            path = u[len(BASE):].split("?")[0].split("#")[0]; f = site / path.lstrip("/")
            if path.endswith("/"): f = f / "index.html"
            if f.is_file(): return route.fulfill(status=200, content_type=TYPES.get(f.suffix, "application/octet-stream"), body=f.read_bytes())
            return route.fulfill(status=404, body="nf")
        other.append(u); return route.abort()
    HOOK = '''() => { window.__clicks = []; window.addEventListener('click', function (e) { var a = e.target.closest && e.target.closest('a[href^="https://buy.stripe.com/"]'); if (a) { window.__clicks.push(a.href); e.preventDefault(); } }, false); }'''
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--host-resolver-rules=MAP www.googletagmanager.com 127.0.0.1, MAP www.google-analytics.com 127.0.0.1, MAP buy.stripe.com 127.0.0.1, MAP checkout.stripe.com 127.0.0.1"])
        for w, h in ((375, 812), (1280, 800)):
            ctx = b.new_context(viewport={"width": w, "height": h}); ctx.route("**/*", handler)
            pg = ctx.new_page(); pg.goto(BASE + "/", wait_until="load")
            buys = [a for a in pg.query_selector_all('a[href^="https://buy.stripe.com/"]')]
            bb = buys[0].bounding_box() if buys else None
            check(len(buys) == 1 and buys[0].get_attribute("href") == URL, f"[home {w}px] exactly one Buy on the page and its href equals yml")
            check(bool(bb) and bb["y"] + bb["height"] <= h, f"[home {w}px] the Buy is above the fold (bottom {bb and round(bb['y'] + bb['height'])} <= {h})")
            if shots: pg.screenshot(path=str(shots / f"home-{w}.png"))
            if w == 1280:
                pg.close(); pg = ctx.new_page(); pg.goto(BASE + "/?utm_source=pinterest&utm_medium=social&utm_campaign=bio&utm_content=a&utm_term=b&other=1", wait_until="load")
                pg.evaluate(HOOK); pg.click("#pp-home-buy-planner"); pg.wait_for_timeout(200)
                u = pg.evaluate("() => window.__clicks")
                check(len(u) == 1 and re.fullmatch(re.escape(URL) + r"\?client_reference_id=pp_home_[0-9a-f]{24}&utm_source=pinterest&utm_medium=social&utm_campaign=bio&utm_content=a&utm_term=b", u[0]) is not None, "[home] click adds client_reference_id (pp_home_) and the five utm_* only; plain href at load")
                dl = pg.evaluate("() => (window.dataLayer||[]).map(a => Array.prototype.slice.call(a))")
                sets = [i for i, e in enumerate(dl) if e[0] == "set" and isinstance(e[1], dict) and "client_reference_id" in e[1]]
                evs = [i for i, e in enumerate(dl) if e[0] == "event" and e[1] in ("buy_click", "begin_checkout")]
                check(len(sets) == 1 and len(evs) == 2 and sets[0] < min(evs), "[home] GA buy_click and begin_checkout fire after the client_reference_id set")
                bc = [dl[i][2] for i in evs if dl[i][1] == "begin_checkout"][0]
                check(bc["items"][0]["item_list_id"] == "home-planner" and bc["items"][0]["item_id"] == URL.rsplit("/", 1)[1], "[home] begin_checkout item_list_id home-planner, item_id from the plain link")
            ctx.close()
        ctx = b.new_context(viewport={"width": 375, "height": 812}); ctx.route("**/*", handler)
        pg = ctx.new_page(); pg.goto(BASE + "/", wait_until="load"); pg.wait_for_timeout(500)
        st = pg.evaluate("() => { var v = document.getElementById('pp-home-video'); return {a: v.autoplay, m: v.muted, l: v.loop, p: v.paused, w: v.getBoundingClientRect().width, h: v.getBoundingClientRect().height}; }")
        check(st["a"] and st["m"] and st["l"] and abs(st["h"] / st["w"] - 1.25) < 0.02, f"[home normal motion] video is muted, autoplay, loop and keeps 4:5 box ({st})")
        sr = pg.evaluate("() => { var v = document.getElementById('pp-home-video'); return {src: v.getAttribute('src'), ds: v.getAttribute('data-src'), pre: v.preload}; }")
        check(sr["src"] == "/paycheck-planner/assets/hero-paycheck-planner-4x5.mp4" and sr["ds"] is None and sr["pre"] == "none", f"[home normal motion] MP4 attached after load, preload none ({sr})")
        ctx.close()
        ctx = b.new_context(viewport={"width": 375, "height": 812}, reduced_motion="reduce"); ctx.route("**/*", handler)
        pg = ctx.new_page(); pg.goto(BASE + "/", wait_until="load"); pg.wait_for_timeout(500)
        st = pg.evaluate("() => { var v = document.getElementById('pp-home-video'); return {a: v.autoplay, l: v.loop, p: v.paused, t: v.currentTime, h: v.getBoundingClientRect().height}; }")
        check((not st["a"]) and (not st["l"]) and st["p"] and st["t"] == 0, f"[home reduced motion] poster only: autoplay off, loop off, paused at 0 ({st})")
        sr = pg.evaluate("() => document.getElementById('pp-home-video').getAttribute('src')")
        check(sr is None, "[home reduced motion] MP4 is never attached (poster only, no video bytes)")
        ctx.close()
        b.close()
    check(not stripe, "no request to any Stripe host was attempted")

print("ALL PLANNER HOME HERO CHECKS PASSED" if not fails else f"FAILED {len(fails)}")
sys.exit(1 if fails else 0)
