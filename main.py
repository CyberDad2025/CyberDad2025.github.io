import datetime
import os
import json
import re
import feedparser
import openai

# ── CONFIG ──────────────────────────────────────────────
MAX_POSTS_PER_DAY = 1
POSTS_DIR = "_posts"
LOG_FILE = "logs/posted.json"
CISA_FEED = "https://www.cisa.gov/feeds/alerts.xml"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
# ────────────────────────────────────────────────────────

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_log(posted_slugs):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(list(posted_slugs), f, indent=2)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text[:60]

def already_exists(slug):
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
    for fname in os.listdir(POSTS_DIR):
        if slug in fname:
            return True
    return False

def fetch_cisa_alerts():
    """Pull latest alerts from CISA RSS feed."""
    try:
        feed = feedparser.parse(CISA_FEED)
        alerts = []
        for entry in feed.entries[:10]:
            alerts.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", entry.get("description", "")),
                "link": entry.get("link", ""),
            })
        return alerts
    except Exception as e:
        print(f"⚠️ CISA feed error: {e}")
        return []

def is_family_relevant(title, summary):
    """Check if alert is relevant to families/home users."""
    keywords = [
        "router", "wifi", "wi-fi", "home", "android", "ios", "iphone",
        "apple", "google", "microsoft", "windows", "chrome", "browser",
        "phishing", "scam", "password", "email", "social media", "facebook",
        "instagram", "tiktok", "snapchat", "roblox", "gaming", "kids",
        "children", "school", "family", "consumer", "mobile", "phone",
        "tablet", "smart", "alexa", "camera", "vpn", "ransomware"
    ]
    text = (title + " " + summary).lower()
    return any(kw in text for kw in keywords)

def translate_to_parent_post(alert_title, alert_summary, alert_link):
    """Use OpenAI to translate a CISA alert into a parent-friendly post."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""You are CyberDad — a friendly cybersecurity expert who writes for non-technical parents.

A new cybersecurity alert has been issued. Translate it into a practical, plain-English blog post for parents.

ALERT TITLE: {alert_title}
ALERT DETAILS: {alert_summary}
SOURCE: {alert_link}

Write a blog post with:
1. A parent-friendly title (not jargon, something a worried parent would click)
2. A 1-sentence "What happened" explanation in plain English
3. A "Does this affect my family?" section (2-3 sentences, be honest and practical)
4. A "What to do right now" section with 3-5 simple numbered action steps any parent can follow
5. A reassuring closing line

Format it in Markdown. Keep the total length under 400 words.
Do NOT use technical jargon. Write like you're texting a friend who's a parent, not a security briefing.
Do NOT include a YAML front matter block — just the body content starting with the title as a # heading."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def get_fallback_post(today):
    """Curated fallback posts if CISA has no family-relevant alerts today."""
    topics = [
        {
            "title": "Is Your Home Router a Security Risk? Check These 5 Things Today",
            "category": "Home Network",
            "body": """## Is Your Home Router a Security Risk? Check These 5 Things Today

Most families set up their router once and never touch it again. Here's the problem — routers are one of the most targeted devices in your home.

**Does this affect my family?**
If you haven't updated your router settings in the past year, there's a good chance it has known vulnerabilities. Attackers use these to spy on your traffic or redirect you to fake websites.

**What to do right now:**
1. Log into your router admin panel (usually 192.168.1.1 in your browser)
2. Check for a firmware update and install it
3. Change the default admin password if you haven't already
4. Make sure your WiFi password is at least 12 characters
5. Enable WPA3 encryption if your router supports it

Takes about 10 minutes and significantly reduces your risk. You've got this."""
        },
        {
            "title": "The One Thing Every Parent Should Do on Their Kid's Phone This Week",
            "category": "Device Security",
            "body": """## The One Thing Every Parent Should Do on Their Kid's Phone This Week

App permissions are quietly one of the biggest privacy risks on your kid's phone — and most parents never check them.

**Does this affect my family?**
Many apps your kids use — games, social media, even school apps — request access to location, microphone, camera, and contacts. Most of them don't need all of that.

**What to do right now:**
1. Open Settings on your kid's phone
2. Go to Privacy or App Permissions
3. Check which apps have access to Location, Camera, and Microphone
4. Revoke access for any app that doesn't obviously need it
5. Have a quick conversation with your kid about why you're doing this

Five minutes of checking can close a lot of unnecessary exposure."""
        },
        {
            "title": "Scam Texts Targeting Parents Are Getting Harder to Spot — Here's What to Look For",
            "category": "Scams",
            "body": """## Scam Texts Targeting Parents Are Getting Harder to Spot

Scammers are now using AI to write convincing texts pretending to be your child, their school, or a delivery service. They're getting good at it.

**Does this affect my family?**
These scams work because they create instant panic — "Mom I lost my phone, use this number" or "Your package requires urgent action." That panic makes people click before thinking.

**What to do right now:**
1. If you get an urgent text from your child from an unknown number, call their real number first
2. Never click links in unexpected texts — go directly to the website instead
3. Set up a family safe word your kids can use to verify it's really them in an emergency
4. Forward suspicious texts to 7726 (SPAM) to report them
5. Talk to your kids about these scams so they know what to watch for too

The best defense is a skeptical pause before you react."""
        },
        {
            "title": "Your Kid's Gaming Account Is a Target — Here's How to Lock It Down",
            "category": "Gaming Security",
            "body": """## Your Kid's Gaming Account Is a Target — Here's How to Lock It Down

Gaming accounts — Roblox, Fortnite, Minecraft, PlayStation, Xbox — are being targeted by hackers more than ever. Why? Because kids rarely have two-factor authentication turned on.

**Does this affect my family?**
A hacked gaming account can expose your payment info, your child's personal details, and even be used to scam their friends. It happens to thousands of families every week.

**What to do right now:**
1. Turn on two-factor authentication on every gaming account your child uses
2. Make sure the account email is one you control, not your kid's personal email
3. Remove saved credit cards from gaming platforms
4. Set spending limits or require parental approval for purchases
5. Talk to your kid about never sharing their password — even with friends

Fifteen minutes of setup prevents a major headache."""
        },
        {
            "title": "Free Password Manager Setup in 20 Minutes — Your Family Needs This",
            "category": "Passwords",
            "body": """## Free Password Manager Setup in 20 Minutes — Your Family Needs This

If your family is reusing the same password across multiple accounts, you're one data breach away from losing access to everything.

**Does this affect my family?**
Password reuse is the number one way family accounts get hacked. When one site gets breached, attackers try that same password everywhere else. It's automated and it works.

**What to do right now:**
1. Download Bitwarden — it's free and works on every device
2. Create one strong master password (make it a phrase you'll remember)
3. Import or manually add your most important accounts first — email, banking, school
4. Install the browser extension so it auto-fills passwords for you
5. Have your kids set it up on their devices too

One hour of setup and you never have to worry about weak passwords again."""
        },
    ]

    day = datetime.datetime.now().day
    topic = topics[day % len(topics)]
    return topic["title"], topic["category"], topic["body"]

def create_post(slug, title, category, body, today):
    os.makedirs(POSTS_DIR, exist_ok=True)
    filename = f"{POSTS_DIR}/{today}-{slug}.md"
    content = f"""---
title: "{title}"
date: {today}
categories: [Cybersecurity, "{category}"]
layout: post
description: "{title} — Plain-English cybersecurity advice for parents from CyberDadKit."
---

{body}

---
*Stay protected. Get free weekly family threat alerts at [CyberDadKit](https://cyberdadkit.com).*
"""
    with open(filename, "w") as f:
        f.write(content)
    return filename

# ── MAIN ────────────────────────────────────────────────
now = datetime.datetime.now()
today = now.strftime("%Y-%m-%d")

posted_slugs = load_log()
posts_created_today = sum(1 for s in posted_slugs if today in s)

if posts_created_today >= MAX_POSTS_PER_DAY:
    print(f"⏭️  Already posted today — skipping.")
    exit(0)

title = None
category = "Cybersecurity"
body = None

if OPENAI_API_KEY:
    print("🔍 Checking CISA feed for family-relevant alerts...")
    alerts = fetch_cisa_alerts()

    for alert in alerts:
        alert_slug = slugify(alert["title"])
        if alert_slug in posted_slugs or already_exists(alert_slug):
            print(f"⏭️  Already covered: {alert['title'][:50]}")
            continue

        if is_family_relevant(alert["title"], alert["summary"]):
            print(f"✅ Found relevant alert: {alert['title'][:60]}")
            try:
                body = translate_to_parent_post(
                    alert["title"],
                    alert["summary"],
                    alert["link"]
                )
                lines = body.split('\n')
                for line in lines:
                    if line.startswith('# '):
                        title = line.replace('# ', '').strip()
                        break
                if not title:
                    title = alert["title"]
                category = "Threat Alert"
                break
            except Exception as e:
                print(f"⚠️ OpenAI error: {e}")
                body = None

if not body:
    print("📝 No new CISA alert — using curated post.")
    title, category, body = get_fallback_post(today)

slug = slugify(title)

if slug in posted_slugs or already_exists(slug):
    print(f"⏭️  Already exists — skipping.")
    exit(0)

filename = create_post(slug, title, category, body, today)
posted_slugs.add(slug)
save_log(posted_slugs)

print(f"✅ Published: {filename}")
print(f"📰 Title: {title}")
