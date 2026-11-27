#!/usr/bin/env python3
"""blog-generator-off-1127 checks (follow-up to blog-slug-1127).

1. netlify/functions/generate-blog.js is kept but disabled: the one exported handler returns 410
   "disabled" and touches no GitHub API, token or post generation. When node is on PATH the module
   is loaded and the handler is called offline (it makes no request).
2. /feed.xml is a site template (jekyll-feed then skips its own) that leaves out redirect stubs.
   With --site, the built feed has 0 stub entries, the newest-10 real posts in date order, and
   no empty entries.
3. _layouts/redirect.html escapes the target: only a site path ("/...") is accepted, it is
   uri_escape'd, HTML-escaped in the refresh, canonical and href, and written with jsonify in
   the script. With --site, every built stub prints one target, the same in all four places, with
   no raw quote or angle bracket. With --escape-fixture SITE, the 12 hostile fixture stubs built
   from tests/fixtures (see TEST-EVIDENCE) render escaped or fall back to "/".
Run: python3 tests/check_blog_generator_off.py [--site /path/to/_site] [--escape-fixture /path/to/fixture_site]
Stdlib only. Never requests anything live.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "netlify" / "functions" / "generate-blog.js"
FEED = ROOT / "feed.xml"
fails: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def exported_handler(src: str) -> str:
    """Text of the exported handler, from 'exports.handler' to the end of its statement."""
    i = src.find("exports.handler")
    depth, j, started = 0, i, False
    while j < len(src):
        c = src[j]
        if c in "({":
            depth += 1
            started = True
        elif c in ")}":
            depth -= 1
        elif c == ";" and started and depth == 0:
            return src[i:j + 1]
        j += 1
    return src[i:]


def check_generator() -> None:
    check(GEN.is_file(), "generate-blog.js is kept")
    src = GEN.read_text(encoding="utf-8")
    check(src.count("exports.handler") == 1 and "module.exports" not in src, "exactly one exported handler")
    h = exported_handler(src)
    check("statusCode: 410" in h and "disabled" in h, "exported handler returns 410 disabled")
    for bad in ("octokit", "Octokit", "GITHUB_TOKEN", "createOrUpdateFileContents", "generateSlug", "generateUltraReadablePost", "require("):
        check(bad not in h, f"exported handler does not use {bad}")
    check("blog-slug-1127" in src[: src.find("exports.handler")], "disable comment points to blog-slug-1127")
    check("/workspace" not in src, "no workspace path in the function source")
    check(not re.search(r"exports\.(config|schedule)|schedule\(", src), "no schedule config in the function")
    node = shutil.which("node")
    if node:
        js = ("require(process.argv[1]).handler({httpMethod:'POST'},{})"
              ".then(r=>console.log(JSON.stringify(r))).catch(e=>{console.error(e);process.exit(2)})")
        out = subprocess.run([node, "-e", js, str(GEN)], capture_output=True, text=True, timeout=30,
                             env={"PATH": "/usr/bin:/bin", "GITHUB_TOKEN": ""})
        try:
            r = json.loads(out.stdout.strip().splitlines()[-1])
            body = json.loads(r.get("body", "{}"))
            check(r.get("statusCode") == 410 and body.get("disabled") is True, "node: handler returns 410 {disabled: true}")
        except Exception as e:  # noqa: BLE001
            check(False, f"node: handler call failed {e} {out.stderr[:200]}")
    else:
        print("note node not on PATH; skipped the live-module call")
    netlify_toml = ROOT / "netlify.toml"
    if netlify_toml.is_file():
        check("generate-blog" not in netlify_toml.read_text(encoding="utf-8"), "netlify.toml does not schedule generate-blog")


def is_stub_page(html: str) -> bool:
    return 'http-equiv="refresh"' in html and 'name="robots" content="noindex"' in html


def check_feed(site: Path | None) -> None:
    check(FEED.is_file(), "/feed.xml template exists in the site source")
    src = FEED.read_text(encoding="utf-8")
    check(src.startswith("---\n") and "layout: null" in src, "feed.xml has front matter with layout: null")
    check('post.redirect_to == nil' in src and "post.layout != 'redirect'" in src, "feed.xml skips redirect stubs")
    if not site:
        print("note --site not given; skipped built feed checks")
        return
    built = site / "feed.xml"
    check(built.is_file(), "built /feed.xml exists")
    if not built.is_file():
        return
    raw = built.read_text(encoding="utf-8")
    check(raw.lstrip().startswith("<?xml"), "built feed starts with the XML declaration")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw.lstrip())
    entries = root.findall("a:entry", ns)
    base = "https://getcyberdadkit.com"
    links = [e.find("a:link", ns).get("href") for e in entries]
    paths = [l[len(base):] if l.startswith(base) else l for l in links]
    check(all(l.startswith(base + "/") for l in links), "feed links are https absolute URLs")
    pages = [site / p.lstrip("/") for p in paths]
    check(all(p.is_file() for p in pages), "every feed entry is a built page")
    stub_hits = [p for p in paths if (site / p.lstrip("/")).is_file() and is_stub_page((site / p.lstrip("/")).read_text(encoding="utf-8"))]
    check(not stub_hits, f"built feed has 0 redirect stubs (entries {len(entries)}, stubs {len(stub_hits)})")
    check(len(entries) == 10, "feed has 10 entries")
    try:  # exact newest-10 list, when the blog-slug-1127 test module is present (#1089)
        sys.path.insert(0, str(ROOT / "tests"))
        import check_blog_slugs as cbs
        real = {p["url"] for p in cbs.load_posts() if not p["stub"]}
        check(all(p in real for p in paths), "every feed entry is a real (non-stub) post")
        newest_day = max(u[:12] for u in real)
        check(paths and paths[0][:12] == newest_day, f"first feed entry is from the newest post day {newest_day}")
    except ImportError:
        print("note tests/check_blog_slugs.py not present; skipped the cross-check with the post list")
    pub = [e.find("a:published", ns).text for e in entries]
    check(pub == sorted(pub, reverse=True), "feed entries are newest first")
    check(all((e.find("a:content", ns) is not None and (e.find("a:content", ns).text or "").strip()) for e in entries), "no empty feed entries")
    self_link = [l.get("href") for l in root.findall("a:link", ns) if l.get("rel") == "self"]
    check(self_link == [base + "/feed.xml"], "feed self link is https://getcyberdadkit.com/feed.xml")


REDIRECT = ROOT / "_layouts" / "redirect.html"
TARGET_RE = {
    "canonical": re.compile(r'<link rel="canonical" href="https://getcyberdadkit\.com([^"]*)">'),
    "refresh": re.compile(r'<meta http-equiv="refresh" content="0; url=([^"]*)">'),
    "script": re.compile(r'<script>location\.replace\(("(?:[^"\\]|\\.)*")\);</script>'),
    "href": re.compile(r'<p>This guide has moved: <a href="([^"]*)">'),
}


def stub_targets(html: str) -> dict:
    out = {}
    for k, rx in TARGET_RE.items():
        m = rx.findall(html)
        out[k] = m
    if len(out["script"]) == 1:
        out["script"] = [json.loads(out["script"][0])]
    return out


def unescape_attr(v: str) -> str:
    import html as _h
    return _h.unescape(v)


def check_redirect_source() -> None:
    src = REDIRECT.read_text(encoding="utf-8")
    check("uri_escape" in src, "redirect.html: target goes through uri_escape")
    check("{{ cdk_to | jsonify }}" in src, "redirect.html: script target written with jsonify")
    check('content="0; url={{ cdk_to | escape }}"' in src and 'href="{{ cdk_to | escape }}"' in src, "redirect.html: refresh and href HTML-escaped")
    check('href="{{ cdk_canonical | escape }}"' in src, "redirect.html: canonical HTML-escaped")
    check('cdk_c1 != "/"' in src and 'cdk_c2 == "/"' in src, "redirect.html: only a site path is accepted")
    check("| url_decode | url_decode" in src and "cdk_chk | slice: 0, 1" in src, "redirect.html: site-path check runs on the URL-decoded target")
    raw = [l for l in src.splitlines() if "page.redirect_to" in l and "{{" in l]
    check(not raw, "redirect.html: page.redirect_to is never printed raw")


def check_built_stub(html: str, label: str) -> str | None:
    t = stub_targets(html)
    vals = []
    for k in ("canonical", "refresh", "href"):
        if len(t[k]) != 1:
            check(False, f"{label}: one {k} target")
            return None
        vals.append(unescape_attr(t[k][0]))
    if len(t["script"]) != 1:
        check(False, f"{label}: one script target")
        return None
    vals.append(t["script"][0])
    ok = len(set(vals)) == 1 and vals[0].startswith("/") and not vals[0].startswith("//")
    ok = ok and not re.search(r'[\s"<>\\]', vals[0])
    if not ok:
        check(False, f"{label}: target same in all four places, site path, no raw quote/angle/space ({vals})")
        return None
    return vals[0]


def check_redirect_site(site: Path) -> None:
    n = bad = 0
    for p in site.rglob("*.html"):
        rel = p.relative_to(site).as_posix()
        if not re.match(r"20\d\d/", rel):
            continue
        h = p.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' not in h:
            continue
        n += 1
        if check_built_stub(h, rel) is None:
            bad += 1
    check(n > 0 and bad == 0, f"built stubs: {n} checked, all print one escaped site-path target ({bad} bad)")


FIXTURE_EXPECT = {
    "fx-normal": "/2025/07/25/parental-controls-guide.html",
    "fx-quote": "/x%22%3E%3Cscript%3Ealert(1)%3C/script%3E.html",
    "fx-space": "/a%20b/'q'&c.html",
    "fx-js": "/",
    "fx-proto": "/",
    "fx-https": "/",
    "fx-backslash": "/",
    "fx-scriptclose": "/p%3C/script%3E%3Cscript%3Ealert(2)%3C/script%3E",
    # encoded forms of "//host" and "/\\host": the site-path check runs on the decoded value
    "fx-enc-slash": "/",
    "fx-enc-backslash": "/",
    "fx-dbl-enc": "/",
    "fx-tab": "/",
}


def check_escape_fixture(site: Path) -> None:
    for k, want in FIXTURE_EXPECT.items():
        f = site / "2026" / "11" / "27" / f"{k}.html"
        if not f.is_file():
            check(False, f"fixture {k} built")
            continue
        h = f.read_text(encoding="utf-8")
        got = check_built_stub(h, f"fixture {k}")
        check(got == want, f"fixture {k}: target {got!r} == {want!r}")
        check(h.count("<script") == 1 and h.count("</script") == 1 and "<script>alert" not in h, f"fixture {k}: one script tag, no injected markup")


def main() -> int:
    args = sys.argv[1:]
    site = Path(args[args.index("--site") + 1]) if "--site" in args else None
    check_generator()
    check_feed(site)
    check_redirect_source()
    if site:
        check_redirect_site(site)
    if "--escape-fixture" in args:
        check_escape_fixture(Path(args[args.index("--escape-fixture") + 1]))
    print("PASS" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
