import os
import requests
import feedparser
import openai
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict
import yaml

# Set your OpenAI API Key
openai.api_key = os.getenv('OPENAI_API_KEY')


@dataclass
class CyberThreatIntel:
    title: str
    description: str
    severity: str
    family_impact: str
    prevention_tips: List[str]
    product_tie_in: str


class CyberDadContentEngine:
    def __init__(self, config_path='cyberdad_config.yaml'):
        self.config = self.load_config(config_path)
        self.cti_sources = [
            'https://feeds.feedburner.com/TheHackersNews',
            'https://krebsonsecurity.com/feed/',
            'https://www.bleepingcomputer.com/feed/',
            'https://threatpost.com/feed/',
            'https://www.darkreading.com/rss.xml'
        ]

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[❌] Error loading config: {e}")
            return {}

    def fetch_cti_feeds(self) -> List[Dict]:
        all_threats = []
        for feed_url in self.cti_sources:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:
                    all_threats.append({
                        'title': entry.title,
                        'summary': entry.summary,
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'source': feed.feed.title
                    })
            except Exception as e:
                print(f"[❌] Error fetching {feed_url}: {e}")
        return all_threats[:5]

    def convert_to_family_friendly(self, threat_data: Dict) -> CyberThreatIntel:
        prompt = f"""
        Convert this cybersecurity threat into family-friendly content for parents:

        Title: {threat_data['title']}
        Summary: {threat_data['summary']}

        Create:
        1. Family-friendly title (avoid technical jargon)
        2. Simple explanation parents can understand
        3. Severity level (Low/Medium/High)
        4. How this affects families specifically
        5. 3 practical prevention tips for families
        6. Which Cyber Dad product would help (choose from: Digital Shield Kit, Password Safety Kit, Screen-Free Activity Pack, Family Tech Rules Pack)
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            content = response.choices[0].message.content
            return self.parse_ai_response(content)
        except Exception as e:
            print(f"[❌] OpenAI conversion error: {e}")
            return self.create_fallback_content(threat_data)

    def parse_ai_response(self, ai_content: str) -> CyberThreatIntel:
        # Naive parser – improve based on your format if needed
        return CyberThreatIntel(
            title="Family Cybersecurity Alert",
            description=ai_content.strip()[:300] + "...",
            severity="Medium",
            family_impact="May affect family devices and online activity",
            prevention_tips=["Update your devices", "Avoid strange links", "Talk to kids about online safety"],
            product_tie_in="Digital Shield Kit"
        )

    def create_blog_post(self, intel: CyberThreatIntel) -> str:
        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d %H:%M:%S')
        current_date = today.strftime('%B %d, %Y')
        product_url = self.config.get('products', {}).get(intel.product_tie_in, {}).get('link', '#')
        checklist_url = self.config.get('lead_magnets', {}).get('wifi_checklist', '#')

        content = f"""---
layout: post
title: "{intel.title}"
date: {date_str}
categories: [cybersecurity, family-safety]
tags: [parenting, tech-safety, cyber-threats]
---

# {intel.title}

**Alert Level: {intel.severity}** | **Date: {current_date}**

## What Parents Need to Know

{intel.description}

## How This Affects Your Family

{intel.family_impact}

## How to Protect Your Family

"""
        for i, tip in enumerate(intel.prevention_tips, 1):
            content += f"{i}. {tip}\n"

        content += f"""

## 🛡️ Get Extra Protection

This threat highlights why every family needs the **{intel.product_tie_in}**.

[🔒 Protect Your Family Now - Get {intel.product_tie_in}]({product_url})

*Use code CYBERDAD20 for 20% off this week only!*

---

[📋 Download Free Wi-Fi Checklist]({checklist_url})

Stay safe,
**Cyber Dad Team**
"""
        return content


class GitHubBlogPublisher:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def publish_post(self, content: str, filename: str):
        posts_dir = os.path.join(self.repo_path, '_posts')
        os.makedirs(posts_dir, exist_ok=True)
        filepath = os.path.join(posts_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[✅] Blog post written: {filepath}")
        except Exception as e:
            print(f"[❌] Write error: {e}")
            return

        # Git push
        try:
            os.system(f'cd {self.repo_path} && git add .')
            os.system(f'cd {self.repo_path} && git commit -m "Auto-post: {filename}"')
            os.system(f'cd {self.repo_path} && git push origin main')
            print(f"[✅] Blog post pushed: {filename}")
        except Exception as e:
            print(f"[❌] Git push failed: {e}")


def main():
    print("🚀 Starting Cyber Dad Blog Publisher")
    repo_path = "/your/full/path/to/cyberdad2025.github.io"  # <- CHANGE THIS
    config_path = "cyberdad_config.yaml"

    engine = CyberDadContentEngine(config_path=config_path)
    publisher = GitHubBlogPublisher(repo_path)

    threats = engine.fetch_cti_feeds()
    if not threats:
        print("[⚠️] No threats found.")
        return

    intel = engine.convert_to_family_friendly(threats[0])
    blog_post = engine.create_blog_post(intel)
    filename = f"{datetime.now().strftime('%Y-%m-%d')}-{intel.title.lower().replace(' ', '-')}.md"
    publisher.publish_post(blog_post, filename)


if __name__ == "__main__":
    main()
