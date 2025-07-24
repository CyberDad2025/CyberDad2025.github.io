#!/usr/bin/env python3
"""
Simple content generator that doesn't require external dependencies.
Creates cybersecurity/parenting blog posts using only built-in Python libraries.
"""

import os
import random
import datetime
from pathlib import Path

# Blog post templates and content
TOPICS = [
    "Cybersecurity for Parents",
    "Teaching Kids About Online Safety",
    "Family Digital Privacy",
    "Parental Controls Guide",
    "Safe Social Media for Teens",
    "Home Network Security",
    "Password Management for Families",
    "Protecting Kids from Cyberbullying",
    "Digital Footprint Awareness",
    "Smart Device Security at Home"
]

CONTENT_TEMPLATES = {
    "intro": [
        "As a parent in the digital age, keeping our families safe online has never been more important.",
        "In today's connected world, cybersecurity isn't just for IT professionals - it's a family responsibility.",
        "Every parent needs to understand the digital landscape their children are navigating.",
        "The intersection of parenting and cybersecurity creates unique challenges and opportunities."
    ],
    
    "tips": [
        "Set up strong, unique passwords for all family accounts",
        "Enable two-factor authentication wherever possible",
        "Regularly update all devices and software in your home",
        "Create a family technology agreement with clear rules",
        "Monitor your children's online activities appropriately",
        "Teach kids to recognize phishing attempts and suspicious links",
        "Use parental controls, but don't rely on them exclusively",
        "Have open conversations about online experiences",
        "Create tech-free zones and times in your home",
        "Lead by example with your own digital habits"
    ],
    
    "warnings": [
        "Never share personal information with strangers online",
        "Be cautious of free Wi-Fi networks in public places",
        "Don't click on suspicious links or download unknown files",
        "Watch out for cyberbullying and know how to report it",
        "Be aware of location sharing on social media apps",
        "Understand the privacy settings on all family devices",
        "Keep software and apps updated to patch security vulnerabilities"
    ],
    
    "conclusions": [
        "Remember, cybersecurity is an ongoing conversation, not a one-time setup.",
        "Stay informed about new threats and teach your family to adapt.",
        "The goal isn't to create fear, but to build digital resilience.",
        "Small steps today can prevent major problems tomorrow."
    ]
}

def generate_post_content(topic):
    """Generate a blog post about the given topic."""
    
    # Create the post content
    intro = random.choice(CONTENT_TEMPLATES["intro"])
    
    # Select 3-5 random tips
    selected_tips = random.sample(CONTENT_TEMPLATES["tips"], random.randint(3, 5))
    tips_section = "\n".join(f"- {tip}" for tip in selected_tips)
    
    # Select 2-3 warnings
    selected_warnings = random.sample(CONTENT_TEMPLATES["warnings"], random.randint(2, 3))
    warnings_section = "\n".join(f"⚠️ {warning}" for warning in selected_warnings)
    
    conclusion = random.choice(CONTENT_TEMPLATES["conclusions"])
    
    # Create the full post
    content = f"""---
layout: post
title: "{topic}: A Parent's Guide"
date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -0500
categories: cybersecurity parenting
tags: online-safety digital-parenting family-security
---

# {topic}: A Parent's Guide

{intro}

## Key Actions to Take

{tips_section}

## Important Warnings

{warnings_section}

## Final Thoughts

{conclusion}

---

*Stay safe, stay informed, and keep your family protected in the digital world.*

**CyberDad Central** - Where cybersecurity meets parenting wisdom.
"""
    
    return content

def create_post_file(content, topic):
    """Create a markdown file for the blog post."""
    
    # Create _posts directory if it doesn't exist
    posts_dir = Path("_posts")
    posts_dir.mkdir(exist_ok=True)
    
    # Generate filename
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    safe_title = topic.lower().replace(' ', '-').replace(':', '').replace(',', '')
    filename = f"{date_str}-{safe_title}.md"
    
    # Write the file
    filepath = posts_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created blog post: {filepath}")
    return filepath

def main():
    """Main function to generate a blog post."""
    
    print("🤖 CyberDad Content Generator Starting...")
    
    # Select a random topic
    topic = random.choice(TOPICS)
    print(f"📝 Generating post about: {topic}")
    
    # Generate content
    content = generate_post_content(topic)
    
    # Create the file
    filepath = create_post_file(content, topic)
    
    print(f"🎉 Blog post generated successfully!")
    print(f"📄 File: {filepath}")
    
    return True

if __name__ == "__main__":
    main()
