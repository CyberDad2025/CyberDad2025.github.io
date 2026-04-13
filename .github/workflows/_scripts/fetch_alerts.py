#!/usr/bin/env python3
"""
fetch_alerts.py
───────────────
Fetches real cybersecurity alerts from CISA and other free public feeds,
filters them for family relevance, then writes _data/alerts.json for
the Jekyll site to render automatically.

Run manually:  python _scripts/fetch_alerts.py
Run via CI:    GitHub Action calls this daily at 7 AM UTC
"""

import json
import re
import os
import feedparser
import requests
from datetime import datetime, timezone
from dateutil import parser as dateparser

# ── CONFIG ──────────────────────────────────────────────────────────────────

OUTPUT_FILE = "_data/alerts.json"
MAX_ALERTS  = 10
MAX_AGE_DAYS = 30

FEEDS = [
    {
        "name": "CISA Alerts",
        "url":  "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "source_label": "CISA (US Gov)",
    },
    {
        "name": "CISA Known Exploited Vulnerabilities",
        "url":  "https://www.cisa.gov/known-exploited-vulnerabilities.xml",
        "source_label": "CISA KEV",
    },
    {
        "name": "US-CERT Current Activity",
        "url":  "https://www.cisa.gov/uscert/ncas/current-activity.xml",
        "source_label": "US-CERT",
    },
]

FAMILY_KEYWORDS = [
    "android", "ios", "iphone", "ipad", "apple", "google", "chrome",
    "windows", "macos", "mac os", "router", "wi-fi", "wifi", "home network",
    "smart tv", "alexa", "ring", "nest", "smart home",
    "phishing", "scam", "credential", "password", "account takeover",
    "ransomware", "malware", "spyware", "identity theft",
    "school", "education", "student", "roblox", "minecraft", "fortnite",
    "discord", "snapchat", "instagram", "tiktok", "facebook", "youtube",
    "social media",
    "browser", "safari", "firefox", "edge", "extension", "app store",
    "critical", "actively exploited", "zero-day", "vulnerability",
    "patch", "update now", "remote code", "data breach",
]

SKIP_KEYWORDS = [
    "industrial control", "ics advisory", "scada", "plc",
    "operational technology", "nuclear", "water treatment",
    "aviation", "maritime", "railway",
]

def infer_severity(text: str) -> str:
    text = text.lower()
    if any(k in text for k in ["critical", "actively exploited", "zero-day", "ransomware",
                                 "remote code execution", "rce", "data breach", "phishing"]):
        return "high"
    if any(k in text for k in ["medium", "moderate", "scam", "credential", "password",
                                 "account takeover", "malware", "spyware"]):
        return "medium"
    return "info"

def make_family_friendly(title: str, summary: str) -> dict:
    clean_summary = re.sub(r'<[^>]+>', '', summary).strip()
    clean_summary = re.sub(r'\s+', ' ', clean_summary)
    if len(clean_summary) > 320:
        clean_summary = clean_summary[:317].rsplit(' ', 1)[0] + '…'

    combined = (title + ' ' + clean_summary).lower()
    action = None
    if any(k in combined for k in ["router", "wifi", "wi-fi", "home network"]):
        action = "Log into your router admin panel and check for firmware updates."
    elif any(k in combined for k in ["ios", "iphone", "ipad", "apple", "macos"]):
        action = "Go to Settings → General → Software Update on all Apple devices."
    elif any(k in combined for k in ["android", "google"]):
        action = "Go to Settings → System → Software Update on Android devices."
    elif any(k in combined for k in ["windows"]):
        action = "Run Windows Update on all family PCs and laptops."
    elif any(k in combined for k in ["chrome", "browser", "extension"]):
        action = "Update Chrome (or your browser) and review installed extensions."
    elif any(k in combined for k in ["phishing", "scam", "credential"]):
        action = "Do not click suspicious links. Go directly to sites by typing the URL."
    elif any(k in combined for k in ["password", "account takeover"]):
        action = "Enable two-factor authentication and update passwords for affected services."
    elif any(k in combined for k in ["ransomware", "malware"]):
        action = "Ensure your devices have up-to-date antivirus and avoid unknown downloads."
    else:
        action = "Keep all devices and apps updated to the latest version."

    return {"title": title, "summary": clean_summary, "action": action}

def is_family_relevant(title: str, summary: str) -> bool:
    combined = (title + ' ' + summary).lower()
    if any(k in combined for k in SKIP_KEYWORDS):
        return False
    return any(k in combined for k in FAMILY_KEYWORDS)

def fetch_all_alerts() -> list:
    alerts = []
    now = datetime.now(timezone.utc)

    for feed_cfg in FEEDS:
        print(f"Fetching: {feed_cfg['name']} …")
        try:
            feed = feedparser.parse(feed_cfg["url"])
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue

        for entry in feed.entries:
            title   = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            link    = entry.get("link", "")

            pub_date = None
            for date_field in ["published", "updated", "created"]:
                raw = entry.get(date_field)
                if raw:
                    try:
                        pub_date = dateparser.parse(raw)
                        if pub_date and pub_date.tzinfo is None:
                            pub_date = pub_date.replace(tzinfo=timezone.utc)
                        break
                    except Exception:
                        continue

            if pub_date is None:
                pub_date = now

            if (now - pub_date).days > MAX_AGE_DAYS:
                continue

            if not is_family_relevant(title, summary):
                continue

            friendly  = make_family_friendly(title, summary)
            severity  = infer_severity(title + ' ' + summary)

            alerts.append({
                "title":      friendly["title"],
                "summary":    friendly["summary"],
                "action":     friendly["action"],
                "severity":   severity,
                "date":       pub_date.strftime("%b %d, %Y"),
                "date_iso":   pub_date.strftime("%Y-%m-%d"),
                "source":     feed_cfg["source_label"],
                "link":       link,
            })

    seen_titles = set()
    unique = []
    for a in sorted(alerts, key=lambda x: x["date_iso"], reverse=True):
        slug = re.sub(r'[^a-z0-9]', '', a["title"].lower())[:60]
        if slug not in seen_titles:
            seen_titles.add(slug)
            unique.append(a)

    return unique[:MAX_ALERTS]

def main():
    print("── CyberDadKit Alert Fetcher ──")
    alerts = fetch_all_alerts()

    if not alerts:
        print("⚠️  No family-relevant alerts found. Keeping existing data.")
        return

    print(f"✓ Found {len(alerts)} family-relevant alerts")

    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_date_label": datetime.now(timezone.utc).strftime("%B %d, %Y"),
        "alert_count": len(alerts),
        "alerts": alerts,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
