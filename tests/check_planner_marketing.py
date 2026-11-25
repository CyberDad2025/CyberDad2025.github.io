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

INTRO = "Intro price $14.99 ends Dec 31."
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
    check("pp-trust" not in hero[:b] and "pp-intro-note" not in hero[:b], f"[{name}] trust row and intro note sit after the Buy button")
check(pos(sales, 'id="checkout"') < pos(sales, 'id="pp-intro-note"') < pos(sales, 'id="pp-trust"') < pos(sales, 'id="pp-sample-line"'),
      "[sales] order: Buy, intro price note, trust row, then the free sample link")
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
check(f'<p class="pp-intro-note" id="pp-intro-note">{INTRO}</p>' in sales and vis(sales).count(INTRO) == 1, "[sales] intro price note is exact and appears once")
check(INTRO not in vis(bundle) and INTRO not in vis(sample), "intro price note is only on the sales page")
for n, h in (("sales", sales), ("bundle", bundle)):
    m = re.search(r'(?s)<ul class="pp-trust" id="pp-trust"[^>]*>(.*?)</ul>', h)
    items = [vis(x) for x in re.findall(r"(?s)<li>(.*?)</li>", m.group(1))] if m else []
    check(items == TRUST, f"[{n}] trust row is exactly {TRUST}")
    check('<a href="/paycheck-planner/refund/">Refund policy</a>' in (m.group(1) if m else ""), f"[{n}] trust row Refund policy links to /paycheck-planner/refund/")
    low = (m.group(1) if m else "").lower()
    check(not re.search(r"soc analyst|analyst|guarantee|family|wife|kids?|child|employer|\bcdk\b", low), f"[{n}] trust row has no family, employer, SOC Analyst or guarantee wording")
check('<span class="pp-badge">Sample numbers</span>' in sales and "Sample numbers" in sales[sales.index("pp-shot-frame"):sales.index("</figure>")], "[sales] hero preview carries the Sample numbers badge")
check(re.search(r'<img [^>]*alt="The Paycheck Planner Dashboard[^"]{40,}"', sales) is not None, "[sales] hero preview has descriptive alt text")
check(sales.count("<video") == 0, "[sales] no video tag in this patch (video slot deferred)")

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

# ---- head: this patch makes no <head> edits on the planner pages (title, description, og, schema and nav belong to the SEO PR)
for n, p in (("sales", "index.html"), ("bundle", "bundle/index.html"), ("sample", "sample/index.html")):
    d = subprocess.run(["git", "diff", "origin/main", "--", f"paycheck-planner/{p}"], cwd=ROOT, capture_output=True, text=True).stdout
    touched = [l for l in d.splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---") and re.search(r"<(title|meta|link|script type=\"application/ld\+json)|pp-nav|<li><a href=\"/(?:paycheck-planner/[^\"]*|contact/)\">(?:Paycheck Planner|Free sample|Plus Bundle|FAQ|Refund|Contact)</a></li>", l)]
    check(not touched, f"[{n}] no head, meta, schema or nav lines changed vs origin/main ({touched[:2]})")

# ---- attribution wiring (source level; tests/check_planner_marketing_browser.py proves the behavior)
check("client_reference_id" in js and "UTM_KEYS" in js and all(k in js for k in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")), "JS appends client_reference_id and the five utm_* keys")
check("window.addEventListener('click'" in js and js.count("window.addEventListener('click'") == 2 and "}, true);" in js, "JS uses a window capture listener (before GA) and a window bubble listener (after GA)")
check("'qa_'" in js and "cdk_qa" in js and "document.cookie" not in js and "sessionStorage" not in js and "localStorage.setItem" not in js, "JS prefixes qa_ from the existing cdk_qa flag and stores nothing")
check("gtag('set', { client_reference_id: ref })" in js and "client_reference_id" not in ga and "a.href.split('/').pop()" in ga, "client_reference_id reaches GA via gtag set from the planner JS; ga4.html is unchanged (holiday tests pin its exact lines)")

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
