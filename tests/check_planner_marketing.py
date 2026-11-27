#!/usr/bin/env python3
"""Marketing pass 1125 checks for the Paycheck Planner pages (source checks; add --site DIR to also check a built site).
Pins: Buy above the fold markup order, Buy hrefs equal _data/paycheck_planner.yml, intro price note, trust row, Sample numbers badge,
free sample link below Buy, og/product meta (no prices in og/twitter text), client-side attribution wiring, the noindex /delivered/
page (no paid links, unlinked), the Lost your files line, no dashes. Never requests any Stripe host.
Run: python3 tests/check_planner_marketing.py [--site /path/to/_site]
"""
from __future__ import annotations
import re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "paycheck-planner"
SITE = Path(sys.argv[sys.argv.index("--site") + 1]) if "--site" in sys.argv else None
fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: fails.append(msg)
def rd(p): return Path(p).read_text(encoding="utf-8")
def vis(h):
    h = re.sub(r"(?s)<(script|style)\b.*?</\1>", "", h)
    h = re.sub(r"<[^>]+>", "", h)
    return re.sub(r"\s+", " ", h.replace("&middot;", "\u00b7")).strip()
def pos(h, needle):
    i = h.find(needle); return i if i >= 0 else 10**9

sales, bundle, sample, delivered, refund = (rd(DIR / n) for n in ("index.html", "bundle/index.html", "sample/index.html", "delivered/index.html", "refund/index.html"))
yml = rd(ROOT / "_data" / "paycheck_planner.yml")
planner_url = re.search(r'^stripe_url_planner:\s*"([^"]+)"', yml, re.M).group(1)
bundle_url = re.search(r'^stripe_url_bundle:\s*"([^"]+)"', yml, re.M).group(1)
js, css, ga = rd(DIR / "assets/paycheck-planner.js"), rd(DIR / "assets/paycheck-planner.css"), rd(ROOT / "_includes/ga4.html")

PRICE_NOTE = "$14.99 launch price through December 31, 2026, then $19.99."
TRUST = ["Built by a Marine Corps veteran with Security+ certification", "Refund policy", "Secure checkout by Stripe"]
LOST = "Lost your files? Email ruel@getcyberdadkit.com with your receipt and we'll resend them."
DASH = re.compile(r"[\u2014\u2013]")

# ---- Buy above the fold: markup order (hero is the first section in main; Buy comes before image, sample link, trust row)
for name, h, btn in (("sales", sales, "pp-buy-planner"), ("bundle", bundle, "pp-buy-bundle"), ("sample", sample, "pp-buy-planner")):
    main = h[h.index('<main id="main"'):]
    check(main.index('class="pp-hero"') < main.index('id="%s"' % btn) < main.index("</section>"), f"[{name}] the Buy button ({btn}) is inside the first hero section")
    hero = main[:main.index("</section>")]
    b = hero.index('id="%s"' % btn)
    check(b < hero.find("<img") or "<img" not in hero, f"[{name}] Buy comes before any hero image")
    check("sample/" not in hero[:b] and "Free sample" not in hero[:b], f"[{name}] no free sample link in the hero at or above the Buy button")
    check("pp-trust" not in hero[:b], f"[{name}] trust row sits after the Buy button")
check(pos(sales, 'id="checkout"') < pos(sales, 'class="pp-price-note"') < pos(sales, 'id="pp-trust"') < pos(sales, 'id="pp-sample-line"'),
      "[sales] order: Buy, launch price note, trust row, then the free sample link")
check(pos(bundle, 'id="checkout"') < pos(bundle, 'id="pp-trust"') < pos(bundle, 'id="pp-sample-line"'), "[bundle] order: Buy, trust row, then the free sample link")
for n, h in (("sales", sales), ("bundle", bundle)):
    check('href="/paycheck-planner/sample/"' in h[h.index('id="pp-sample-line"'):], f"[{n}] a free sample link sits in the page below the Buy area (the header nav item is untouched here; the SEO PR owns nav)")
check("buy.stripe.com" not in refund and "pp-btn" not in refund, "[refund] the page has no Buy button")

# ---- hrefs equal yml
for n, h in (("sales", sales), ("bundle", bundle), ("sample", sample)):
    for m in re.finditer(r"<a [^>]*href=\"([^\"]+)\"[^>]*data-pp-ref=\"(planner|bundle)\"", h):
        want = {"planner": "{{ pp.stripe_url_planner }}", "bundle": "{{ pp.stripe_url_bundle }}"}[m.group(2)]
        check(m.group(1) == want, f"[{n}] data-pp-ref={m.group(2)} Buy href reads the yml value")
    check("buy.stripe.com" not in h and "checkout.stripe.com" not in h, f"[{n}] hardcodes no Stripe URL")
check(bool(re.search(r"data-pp-ref=\"planner\"", sales)) and bool(re.search(r"data-pp-ref=\"bundle\"", bundle)) and bool(re.search(r"data-pp-ref=\"planner\"", sample)), "planner Buy buttons on sales and sample, bundle Buy on bundle, all carry data-pp-ref")

# ---- price note, trust row, badge
check(vis(sales).count(PRICE_NOTE) == 1 and "pp-intro-note" not in sales and "Intro price" not in vis(sales), "[sales] one launch price note, no separate intro line")
check("Intro price" not in vis(bundle) and "Intro price" not in vis(sample), "no Intro price line on bundle or sample")
for n, h in (("sales", sales), ("bundle", bundle)):
    m = re.search(r'(?s)<ul class="pp-trust" id="pp-trust"[^>]*>(.*?)</ul>', h)
    items = [vis(x) for x in re.findall(r"(?s)<li>(.*?)</li>", m.group(1))] if m else []
    check(items == TRUST, f"[{n}] trust row is exactly {TRUST}")
    check('<a href="/paycheck-planner/refund/">Refund policy</a>' in (m.group(1) if m else ""), f"[{n}] trust row Refund policy links to /paycheck-planner/refund/")
    low = (m.group(1) if m else "").lower()
    check(not re.search(r"soc analyst|analyst|guarantee|family|wife|kids?|child|employer|\bcdk\b", low), f"[{n}] trust row has no family, employer, SOC Analyst or guarantee wording")
check('<span class="pp-badge">Sample numbers</span>' in sales and "Sample numbers" in sales[sales.index("pp-shot-frame"):sales.index("</figure>")], "[sales] hero preview carries the Sample numbers badge")
check(re.search(r'<img [^>]*alt="The Paycheck Planner Dashboard[^"]{40,}"', sales) is not None, "[sales] hero preview has descriptive alt text")

# ---- page demo loop (below the hero image; sample amounts live only in aria-label and alt)
DEMO_ARIA = (
    "Silent loop of the Paycheck Planner with sample numbers. "
    "Settings shows usual take-home pay entered. "
    "The Paycheck Plan then shows what is left. "
    "A phone bill is added, and what is left on the second paycheck updates from $1,406.60 to $1,321.60. "
    "The second paycheck includes a $200 one-time column."
)
NFA_FAQ = "No. It is a planning tool for your own numbers. It is not financial, tax or legal advice."
NFA_FOOT = "Paycheck Planner is a budgeting tool, not financial advice."
check(sales.count("<video") == 1 and bundle.count("<video") == 0 and sample.count("<video") == 0 and refund.count("<video") == 0,
      "[sales] one demo video on the sales page only")
vm = re.search(r"(?s)<video\b([^>]*)>(.*?)</video>", sales)
vattrs, vinner = (vm.group(1), vm.group(2)) if vm else ("", "")
check(bool(vm) and 'id="pp-page-demo-video"' in vattrs and 'data-pp-video' in vattrs, "[sales] demo video has id and data-pp-video")
check(all(a in vattrs.split() or a in vattrs for a in ("autoplay", "muted", "loop", "playsinline")) and 'preload="none"' in vattrs,
      "[sales] video has autoplay muted loop playsinline preload=none")
check('poster="/paycheck-planner/assets/page-paycheck-planner-demo-poster.webp"' in vattrs, "[sales] video poster is the webp still")
check('data-src="/paycheck-planner/assets/page-paycheck-planner-demo.mp4"' in vattrs and re.search(r"\ssrc=", vattrs) is None,
      "[sales] MP4 is in data-src only (no src), so the poster can paint first")
check('width="1920"' in vattrs and 'height="1080"' in vattrs, "[sales] video has explicit 1920x1080 to avoid layout shift")
check(f'aria-label="{DEMO_ARIA}"' in vattrs, "[sales] video aria-label describes the sheet, sample numbers and leftover update")
check(f'<img src="/paycheck-planner/assets/page-paycheck-planner-demo-poster.png" width="1920" height="1080" alt="{DEMO_ARIA}">' in vinner,
      "[sales] PNG poster fallback uses the same descriptive alt")
demo = sales[sales.index('id="pp-page-demo"'):sales.index('id="previews"')]
hero_img_at = sales.index('paycheck-planner-dashboard-600.webp')
video_at = sales.index('id="pp-page-demo-video"')
previews_at = sales.index('id="previews"')
buy_at = sales.index('id="pp-buy-planner"')
check(buy_at < hero_img_at < video_at < previews_at, "[sales] order: Buy, hero image, then the demo video, then the preview stills")
check('id="pp-page-demo"' in sales[sales.index('class="pp-hero"'):] and sales.index('class="pp-hero"') < sales.index('id="pp-page-demo"') < previews_at,
      "[sales] demo section sits below the hero section and above the previews")
check(NFA_FAQ in vis(sales) and NFA_FOOT in vis(sales) and "Not financial, tax or legal advice." in vis(sales),
      "[sales] NFA lines are unchanged")
check("$1,406.60" not in vis(sales) and "$1,321.60" not in vis(sales) and "$200" not in vis(sales),
      "[sales] sample leftover amounts are not in visible copy (aria-label and alt only)")
check("IntersectionObserver" in js and "prefers-reduced-motion: reduce" in js and "rootMargin" in js,
      "JS attaches the MP4 via IntersectionObserver and skips it when motion is reduced")
check("prefers-reduced-motion: reduce" in css and "aspect-ratio: 16 / 9" in css and "pointer-events: none" in css,
      "CSS reserves a 16:9 box and disables video pointer events when motion is reduced")

# ---- sheet stills (Video Producer webps) in the sales preview area
import hashlib
DEMO_MP4 = DIR / "assets" / "page-paycheck-planner-demo.mp4"
DEMO_POSTER = DIR / "assets" / "page-paycheck-planner-demo-poster.webp"
DEMO_PNG = DIR / "assets" / "page-paycheck-planner-demo-poster.png"
check(DEMO_MP4.is_file() and hashlib.sha256(DEMO_MP4.read_bytes()).hexdigest() == "61dff740424feec1f841cb99309c7a7386ddb79163b7fc7045a6ffe7207bf644",
      "demo MP4 is the Video Producer file (sha256 61dff740...)")
check(DEMO_POSTER.is_file() and hashlib.sha256(DEMO_POSTER.read_bytes()).hexdigest() == "27c2702a227028f2c44bdac36906670d6f0d842391d21b2780ff0dbb90ae201d",
      "demo poster webp is the Video Producer file (sha256 27c2702a...)")
check(DEMO_PNG.is_file() and hashlib.sha256(DEMO_PNG.read_bytes()).hexdigest() == "a2fb0f138dfa2d98b26060fb16a8eef86c24ece8f9474a428fa21bd28b90c42f",
      "demo poster PNG fallback is the Video Producer file (sha256 a2fb0f13...)")
STILLS = [("still-1-paycheck-plan", "ec7f7d46", 1600, 744, "Paycheck Plan"), ("still-2-bills", "02e55734", 1600, 656, "Bills"),
          ("still-3-sinking-funds", "7d784daf", 1600, 659, "Sinking Funds"), ("still-4-savings-goals", "ed1e6a09", 1600, 854, "Savings Goals")]
prev = sales[sales.index('id="previews"'):sales.index('id="problem"')]
check(prev.count("<img") == 4 and sales.index('id="previews"') > sales.index('id="pp-buy-planner"'), "[sales] four preview stills, after the hero Buy")
for n, sha, w, h, sheet in STILLS:
    f = DIR / "assets" / f"paycheck-planner-{n}.webp"
    tagm = re.search(r'<img src="/paycheck-planner/assets/paycheck-planner-%s\.webp"[^>]*>' % n, prev)
    t = tagm.group(0) if tagm else ""
    check(f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest().startswith(sha), f"still {n} is the Video Producer file (sha256 {sha}...)")
    check(f'width="{w}" height="{h}"' in t and 'loading="lazy"' in t and re.search(r'alt="[^"]*%s sheet[^"]*sample numbers' % sheet, t) is not None, f"[sales] {n}: width/height, lazy, alt names the {sheet} sheet and says sample numbers")

# ---- Lost your files line and delivered page
for n, h in (("sales", sales), ("bundle", bundle), ("delivered", delivered)):
    check(LOST in vis(h) and vis(h).count(LOST) == 1, f"[{n}] has the exact Lost your files line once")
check(LOST not in vis(sample) and LOST not in vis(refund), "Lost your files line is not on the sample or refund page")
check('name="robots" content="noindex, nofollow"' in delivered and re.search(r"(?s)^---.*?sitemap:\s*false.*?---", delivered) is not None, "[delivered] noindex and kept out of the sitemap")
check(not re.search(r"drive\.google|docs\.google|buy\.stripe|checkout\.stripe|usercontent", delivered, re.I), "[delivered] has no Drive, Docs or Stripe links")
others = subprocess.run(["git", "grep", "-l", "paycheck-planner/delivered", "--", ".", ":!tests/", ":!paycheck-planner/delivered/"], cwd=ROOT, capture_output=True, text=True).stdout.split()
check(not others and "/delivered/" not in "".join(rd(DIR / p) for p in ("index.html", "bundle/index.html", "sample/index.html", "refund/index.html")) and "delivered" not in rd(ROOT / "_includes/paycheck-planner-footer.html"),
      f"[delivered] is unlinked from the site, nav and footer ({others})")
check("<h1" in delivered and "Download now" in delivered and "Google Drive" in delivered and "Stripe receipt" in delivered, "[delivered] has the save-your-files tips")

BASE = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or "origin/main"
# ---- head: SEO may update title, description, og, twitter and Product JSON-LD on the sales and bundle pages.
# The sample page head, and the shared nav on all three pages, stay unchanged here.
for n, pth in (("sample", "sample/index.html"),):
    d = subprocess.run(["git", "diff", BASE, "--", f"paycheck-planner/{pth}"], cwd=ROOT, capture_output=True, text=True).stdout
    touched = [l for l in d.splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---") and re.search(r"<(title|meta|link|script type=\"application/ld\+json)|pp-nav|<li><a href=\"/(?:paycheck-planner/[^\"]*|contact/)\">(?:Paycheck Planner|Free sample|Plus Bundle|FAQ|Refund|Contact)</a></li>", l)]
    check(not touched, f"[{n}] no head, meta, schema or nav lines changed vs the merge base with origin/main ({touched[:2]})")
for n, pth in (("sales", "index.html"), ("bundle", "bundle/index.html")):
    d = subprocess.run(["git", "diff", BASE, "--", f"paycheck-planner/{pth}"], cwd=ROOT, capture_output=True, text=True).stdout
    nav_touched = [l for l in d.splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---") and re.search(r"pp-nav|<li><a href=\"/(?:paycheck-planner/[^\"]*|contact/)\">(?:Paycheck Planner|Free sample|Plus Bundle|FAQ|Refund|Contact)</a></li>", l)]
    check(not nav_touched, f"[{n}] nav lines unchanged vs the merge base with origin/main ({nav_touched[:2]})")

# ---- attribution wiring (source level; tests/check_planner_marketing_browser.py proves the behavior)
check("client_reference_id" in js and "UTM_KEYS" in js and all(k in js for k in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")), "JS appends client_reference_id and the five utm_* keys")
check("window.addEventListener('click'" in js and js.count("window.addEventListener('click'") == 2 and "}, true);" in js, "JS uses a window capture listener (before GA) and a window bubble listener (after GA)")
check("'qa_'" in js and "cdk_qa" in js and "document.cookie" not in js and "sessionStorage" not in js and "localStorage.setItem" not in js, "JS prefixes qa_ from the existing cdk_qa flag and stores nothing")
check("gtag('set', { client_reference_id: ref })" in js and "client_reference_id" not in ga and "a.href.split('/').pop()" in ga, "client_reference_id reaches GA via gtag set from the planner JS; ga4.html still does not name it (holiday tests pin the gtag event lines)")

# ---- Stripe and MailerLite keys in paycheck_planner.yml stay the same. SEO may add offer-price keys for JSON-LD.
# ga4.html may add the production hostname allowlist; event and cdk_qa behavior stay pinned.
check('stripe_url_planner: "https://buy.stripe.com/bJe28qaCyfyMeP33jVds40j"' in yml, "stripe_url_planner is unchanged")
check('stripe_url_bundle: "https://buy.stripe.com/aFacN42620DS5et8Efds40k"' in yml, "stripe_url_bundle is unchanged")
check('mailerlite_form_slug: "IW0v9B"' in yml and 'mailerlite_form_id: "205066869153990151"' in yml, "MailerLite form ids are unchanged")
check(len(re.findall(r"https://buy\.stripe\.com/[A-Za-z0-9]+", yml)) == 2, "yml still has exactly two Stripe Payment Links")
check("var PROD_HOSTS = { 'getcyberdadkit.com': 1 };" in ga and "location.hostname" in ga, "ga4.html gates gtag.js behind a production hostname allowlist")
check("if (!onProd) return;" in ga and "window.gtag = function () {};" in ga, "ga4.html makes gtag and the sendBeacon fallback no-ops off production")
check("if (qa) { gtag('config', 'G-5B1LNCPB56', { traffic_type: 'internal' }); } else { gtag('config', 'G-5B1LNCPB56'); }" in ga, "ga4.html production config still honors cdk_qa / traffic_type=internal")
check("sendCollect('buy_click'" in ga and "sendCollect('begin_checkout'" in ga and "if (qa) q.push('tt=internal');" in ga, "ga4.html still sends buy_click and begin_checkout on the fallback path, with tt=internal when cdk_qa is set")

# ---- no dashes in anything added or touched
for n, h in (("sales", sales), ("bundle", bundle), ("sample", sample), ("delivered", delivered)):
    check(not DASH.search(h), f"[{n}] no em or en dash")
check(not DASH.search(js) and not DASH.search(css) and not DASH.search(ga), "no em or en dash in planner JS, CSS or ga4.html")
check("CyberDad Kit LLC, PO Box 940061, Maitland, FL 32794" in rd(ROOT / "_includes/paycheck-planner-footer.html"), "publisher address line unchanged")

# ---- built site (optional): rendered hrefs equal yml, no UTM on internal links, delivered not in sitemap
if SITE:
    def built(p): return rd(SITE / p / "index.html")
    bs, bb, bm = built("paycheck-planner"), built("paycheck-planner/bundle"), built("paycheck-planner/sample")
    check(f'id="pp-buy-planner" href="{planner_url}"' in bs and f'id="pp-buy-bundle" href="{bundle_url}"' in bs, "[built sales] Buy hrefs equal the yml values")
    check(f'id="pp-buy-bundle" href="{bundle_url}"' in bb and f'id="pp-buy-planner" href="{planner_url}"' in bm, "[built bundle, sample] Buy hrefs equal the yml values")
    check(not re.search(r'href="/[^"]*[?&]utm_', bs + bb + bm + built("paycheck-planner/delivered")), "[built] internal links carry no UTM")
    check(not re.search(r"drive\.google|docs\.google", built("paycheck-planner/delivered")), "[built delivered] no Drive or Docs link")
    sm = rd(SITE / "sitemap.xml")
    check("/paycheck-planner/delivered" not in sm and "/paycheck-planner/bundle/" in sm, "[built] delivered page is not in the sitemap, bundle page is")
    check("{{" not in bs + bb + bm and "{%" not in bs + bb + bm, "[built] no unrendered Liquid")

print("ALL PLANNER MARKETING CHECKS PASSED" if not fails else f"FAILED {len(fails)} check(s)")
sys.exit(1 if fails else 0)
