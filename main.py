import datetime
import os
import json

# ── CONFIG ──────────────────────────────────────────────
MAX_POSTS_PER_DAY = 1          # Change to 2 or 3 if you want more
POSTS_DIR = "_posts"
LOG_FILE = "logs/posted.json"  # Tracks every slug ever posted
# ────────────────────────────────────────────────────────

def load_log():
    """Load the set of slugs we've already posted."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_log(posted_slugs):
    """Save updated slug log."""
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(list(posted_slugs), f, indent=2)

def already_exists(slug):
    """Check if a file with this slug already exists in _posts."""
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
    for fname in os.listdir(POSTS_DIR):
        if slug in fname:
            return True
    return False

def get_post_for_hour(hour, today):
    """Return (slug, category, title, body) based on hour."""
    posts = {
        9: {
            "slug": f"{today}-family-tip-morning",
            "category": "Family Tips",
            "title": "Family Tip of the Day",
            "body": (
                "👨‍👩‍👧‍👦 **Family Tip**\n\n"
                "Teach your kids to always ask before clicking on links or downloading apps. "
                "Make it a household rule — no new apps without a parent check first. "
                "Keep the conversation open so they feel safe telling you when something feels off."
            )
        },
        13: {
            "slug": f"{today}-cyber-threat-alert",
            "category": "Cyber Threat Alert",
            "title": "Cyber Threat Alert — What Families Should Know",
            "body": (
                "🚨 **Cyber Threat Alert**\n\n"
                "Fake emails impersonating delivery services, banks, and schools are circulating this week. "
                "Before clicking any link in an email, hover over it to see the real destination. "
                "When in doubt, go directly to the website instead of clicking the link."
            )
        },
        20: {
            "slug": f"{today}-security-tool-tip",
            "category": "Security Tools",
            "title": "Security Tool Tip for Families",
            "body": (
                "🛡️ **Security Tool Tip**\n\n"
                "A password manager is the single best thing your family can set up today. "
                "Bitwarden is completely free and works on every device. "
                "It generates strong unique passwords and remembers them for you — "
                "no more reusing the same password everywhere."
            )
        },
    }

    # Default post for any other hour (won't run unless you add more schedule times)
    default = {
        "slug": f"{today}-cyber-tip-{hour:02d}",
        "category": "General",
        "title": f"Cyber Safety Tip — {today}",
        "body": (
            "💡 **Cyber Tip**\n\n"
            "Take 5 minutes this week to review the privacy settings on your family's most-used apps. "
            "Check who can see your kids' profiles, posts, and location data."
        )
    }

    return posts.get(hour, default)

def create_post(slug, category, title, body, today):
    """Write the markdown file to _posts."""
    os.makedirs(POSTS_DIR, exist_ok=True)
    filename = f"{POSTS_DIR}/{slug}.md"
    content = f"""---
title: "{title}"
date: {today}
categories: [Cybersecurity, "{category}"]
layout: post
---

{body}
"""
    with open(filename, "w") as f:
        f.write(content)
    return filename

# ── MAIN ────────────────────────────────────────────────
now = datetime.datetime.now()
today = now.strftime("%Y-%m-%d")
hour = now.hour

posted_slugs = load_log()
posts_created_today = sum(1 for s in posted_slugs if s.startswith(today))

# Hard stop if we've already hit today's limit
if posts_created_today >= MAX_POSTS_PER_DAY:
    print(f"⏭️  Already created {posts_created_today} post(s) today — limit reached. Skipping.")
    exit(0)

post = get_post_for_hour(hour, today)
slug = post["slug"]

# Skip if this exact slug already exists
if slug in posted_slugs:
    print(f"⏭️  Already posted slug '{slug}' — skipping duplicate.")
    exit(0)

if already_exists(slug):
    print(f"⏭️  File with slug '{slug}' already exists in _posts — skipping.")
    posted_slugs.add(slug)
    save_log(posted_slugs)
    exit(0)

# All clear — create the post
filename = create_post(
    slug=slug,
    category=post["category"],
    title=post["title"],
    body=post["body"],
    today=today
)

posted_slugs.add(slug)
save_log(posted_slugs)

print(f"✅ Post created: {filename}")
