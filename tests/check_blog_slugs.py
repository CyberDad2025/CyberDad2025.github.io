#!/usr/bin/env python3
"""Blog slug checks (blog-slug-1127).

Every dated post URL must serve the article its slug names:
  1. A real post's front-matter title (and its first H1, when it is one of the three
     netlify/functions/generate-blog.js template titles) must be about the slug's topic.
  2. A redirect stub (layout: redirect) must point at a real post whose title is about the
     stub's slug topic, and must carry noindex: true and sitemap: false.
  3. No two real posts may share an identical body, apart from the legacy duplicate groups
     frozen in tests/blog_slug_known_dups.json (generic posts from the older generators; they
     may shrink, never grow, and no new group may appear).
Optional: --site PATH checks the built site (each stub page refreshes to its target, and the
target page exists and is not itself a stub).

Run: python3 tests/check_blog_slugs.py [--site /path/to/_site]
Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
POST_DIRS = [ROOT / "_posts", ROOT / "scripts" / "_posts"]
KNOWN_DUPS = Path(__file__).resolve().parent / "blog_slug_known_dups.json"
TZ = ZoneInfo("America/New_York")  # _config.yml timezone

# Slug topic map for the 15 slugs netlify/functions/generate-blog.js picked at random
# (independently of which of its three article templates it wrote).
EASY = {
    "simple-password-safety": ["password"],
    "easy-wifi-protection": ["wi-fi", "wifi"],
    "avoid-bad-emails": ["email"],
    "prevent-online-scams": ["scam"],
    "safe-online-shopping": ["shopping"],
    "simple-two-factor-auth": ["two-factor"],
    "safe-internet-browsing": ["browsing"],
    "protect-your-phone": ["phone"],
    "easy-backup-guide": ["backup"],
    "simple-privacy-tips": ["privacy"],
    "safe-social-media": ["social media"],
    "easy-antivirus-guide": ["antivirus"],
    "family-computer-safety": ["laptop", "computer"],
    "kids-online-safety": ["child", "kids", "parental"],
    "grandparent-tech-security": ["grandparent", "family cybersecurity"],
}
# Other slugs whose topic is spelled differently in the matching title.
EXTRA = {
    "home-router-hardening": ["router"],
    "social-media-privacy": ["social media"],
    "two-factor-authentication": ["two-factor"],
    # dated digest slot from scripts/: any digest title is fine
    "daily-cybersecurity-update": [""],
}
NEEDS_ARTICLE = {"grandparent-tech-security"}  # no on-topic article in the repo yet
TEMPLATE_TOPIC = {
    "\U0001F512 Keep Your Passwords Safe": "simple-password-safety",
    "\U0001F4F6 Make Your Home Wi": "easy-wifi-protection",
    "\U0001F3A3 Avoid Email Tricks": "avoid-bad-emails",
}
STOP = set(
    "a an the and or for of to in on your you how why what from with is are be it its this that my our best "
    "simple easy safe safety family families guide tips step steps setup kids parents parent parental modern "
    "practices security secure protect protection protecting non tech complete update daily alert attacks threats "
    "need needs every essential home keep work practical expert 2025 2026 minutes less md html child new important quick".split()
)
NAME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.(md|markdown|html)$")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", s.lower().replace("wi-fi", "wifi").replace("two-factor", "twofactor"))


def title_topic_ok(slug: str, title: str) -> bool:
    t = title.lower()
    for pfx, topic in TEMPLATE_TOPIC.items():
        if title.startswith(pfx):
            return slug == topic
    keys = EASY.get(slug) or EXTRA.get(slug)
    if keys is not None:
        return any(k in t for k in keys)
    toks = [w for w in norm(slug.replace("-", " ")).split() if w not in STOP and len(w) > 2]
    if not toks:
        return True
    tt = norm(title)
    # slugs were cut at 50 characters, so the last token can be the start of a title word
    return any(re.search(r"\b" + re.escape(w), tt) for w in toks)


def front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip('"').strip("'")
    return fm, text[m.end():]


def post_url(fm: dict, name_date: tuple[str, str, str], slug: str) -> str:
    y, mo, d = name_date
    raw = fm.get("date", "")
    m = re.match(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}(?::\d{2})?)\s*([+-]\d{4}|Z)?", raw)
    if m:
        off = m.group(3) or ""
        fmt = "%Y-%m-%d %H:%M:%S" if m.group(2).count(":") == 2 else "%Y-%m-%d %H:%M"
        dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", fmt)
        if off and off != "Z":
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {off}", fmt + " %z").astimezone(TZ)
        elif off == "Z":
            dt = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
        y, mo, d = f"{dt.year:04d}", f"{dt.month:02d}", f"{dt.day:02d}"
    elif re.match(r"\d{4}-\d{2}-\d{2}$", raw):
        y, mo, d = raw.split("-")
    s = re.sub(r"[^A-Za-z0-9._~!$&'()+,;=@]+", "-", slug).strip("-")  # Jekyll slugify, pretty mode
    s = re.sub(r"-+", "-", s)
    return f"/{y}/{mo}/{d}/{s}.html"


def load_posts() -> list[dict]:
    posts = []
    for d in POST_DIRS:
        for p in sorted(d.rglob("*")):
            m = NAME.match(p.name)
            if not p.is_file() or not m:
                continue
            fm, body = front_matter(p.read_text(encoding="utf-8"))
            if fm.get("published", "").lower() == "false":
                continue
            h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S) or re.search(r"^#\s+(.+)$", body, re.M)
            posts.append({
                "file": p.relative_to(ROOT).as_posix(),
                "slug": m.group(4),
                "fm": fm,
                "body": body,
                "h1": h1.group(1).strip() if h1 else "",
                "url": post_url(fm, m.group(1, 2, 3), m.group(4)),
                "stub": fm.get("layout") == "redirect",
            })
    return posts


def main() -> int:
    args = sys.argv[1:]
    site = Path(args[args.index("--site") + 1]) if "--site" in args else None
    fails: list[str] = []
    posts = load_posts()
    by_url: dict[str, dict] = {}
    for p in posts:
        # _posts wins a URL clash with scripts/_posts (it is read first)
        by_url.setdefault(p["url"], p)
    real = [p for p in posts if not p["stub"]]
    stubs = [p for p in posts if p["stub"]]

    for p in real:
        title = p["fm"].get("title", "")
        if not title_topic_ok(p["slug"], title):
            fails.append(f"{p['file']}: title {title!r} is not about slug {p['slug']!r}")
        if p["h1"] and any(p["h1"].startswith(x) for x in TEMPLATE_TOPIC) and not title_topic_ok(p["slug"], p["h1"]):
            fails.append(f"{p['file']}: H1 {p['h1']!r} is not about slug {p['slug']!r}")

    for p in stubs:
        fm = p["fm"]
        tgt = by_url.get(fm.get("redirect_to", ""))
        if fm.get("noindex") != "true" or fm.get("sitemap") != "false":
            fails.append(f"{p['file']}: stub must set noindex: true and sitemap: false")
        if p["body"].strip():
            fails.append(f"{p['file']}: stub has body content")
        if not tgt:
            fails.append(f"{p['file']}: redirect_to {fm.get('redirect_to')!r} is not a post URL")
            continue
        if tgt["stub"]:
            fails.append(f"{p['file']}: redirect_to points at another stub {tgt['file']}")
        if p["slug"] not in NEEDS_ARTICLE and not title_topic_ok(p["slug"], tgt["fm"].get("title", "")):
            fails.append(f"{p['file']}: target {tgt['file']} title {tgt['fm'].get('title')!r} is not about {p['slug']!r}")
        if fm.get("redirect_title", "") != tgt["fm"].get("title", ""):
            fails.append(f"{p['file']}: redirect_title does not match the target title")

    # identical bodies among real posts
    groups: dict[str, list[str]] = {}
    for p in real:
        groups.setdefault(hashlib.sha256(p["body"].encode()).hexdigest(), []).append(p["file"])
    known = [set(g) for g in json.loads(KNOWN_DUPS.read_text(encoding="utf-8"))["groups"]]
    for files in groups.values():
        if len(files) > 1 and not any(set(files) <= k for k in known):
            fails.append(f"identical body shared by: {', '.join(files)}")
    # every stub file in the easy set: the generator family is fully resolved
    for p in real:
        if p["slug"] in EASY and p["file"].startswith("_posts/"):
            same = [q for q in real if q["slug"] == p["slug"] and q["file"] != p["file"] and q["file"].startswith("_posts/")]
            if same:
                fails.append(f"{p['file']}: more than one live post for generator slug {p['slug']!r}")

    if site:
        for p in stubs:
            out = site / p["url"].lstrip("/")
            if not out.is_file():
                fails.append(f"built: {p['url']} missing")
                continue
            html = out.read_text(encoding="utf-8")
            to = p["fm"]["redirect_to"]
            if f'http-equiv="refresh" content="0; url={to}"' not in html or 'name="robots" content="noindex"' not in html:
                fails.append(f"built: {p['url']} lacks refresh to {to} or noindex")
            if f'rel="canonical" href="https://getcyberdadkit.com{to}"' not in html:
                fails.append(f"built: {p['url']} lacks https canonical to {to}")
            tout = site / to.lstrip("/")
            if not tout.is_file() or 'http-equiv="refresh"' in tout.read_text(encoding="utf-8"):
                fails.append(f"built: target {to} missing or is a stub")

    print(f"posts {len(posts)} | real {len(real)} | redirect stubs {len(stubs)} | duplicate groups allowed {len(known)}")
    for f in fails:
        print("FAIL", f)
    print("PASS" if not fails else f"{len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
