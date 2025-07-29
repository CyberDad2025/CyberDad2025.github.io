#!/usr/bin/env python3
import os
from datetime import datetime
from openai import OpenAI

def generate_blog_post():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Enhanced prompt for better quality content
    prompt = """Write a comprehensive cybersecurity blog post for families. 

    Structure it like this:
    1. Start with a compelling hook about a current cybersecurity threat
    2. Provide 5-7 specific, actionable tips that families can implement
    3. Include real statistics and current trends (but don't make up specific numbers)
    4. Use scenarios like "Imagine if..." or "Consider this situation..." 
    5. End with a clear call-to-action
    
    Make it:
    - 1200-1500 words
    - Professional but conversational tone
    - Educational and practical
    - Focused on protecting families and children online
    - Include specific tools and resources (but don't make false claims)
    
    Write it as an expert cybersecurity advisor would, but keep it accessible for regular parents."""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,  # Increased for longer content
        temperature=0.7   # Slightly more creative while staying factual
    )
    
    blog_content = response.choices[0].message.content
    
    # Enhanced blog post format
    blog_post = f"""---
layout: post
title: "Daily Cybersecurity Update - {today}"
date: {today}
categories: cybersecurity
tags: family-security online-safety cybersecurity-tips
author: CyberDad
excerpt: "Essential cybersecurity guidance to keep your family safe online"
---

{blog_content}

---

## Stay Protected

Want more cybersecurity tips? Follow our daily updates and join thousands of families staying safe online.

**🔒 Remember: Your family's digital safety is worth the extra effort.**
## 🛡️ Recommended Security Tools

Protect your family with these trusted cybersecurity solutions:

- **[Norton 360 Deluxe](https://norton.com/affiliate-link)** - Complete family protection with VPN
- **[NordVPN](https://nordvpn.com/affiliate-link)** - Secure your internet connection worldwide  
- **[LastPass](https://lastpass.com/affiliate-link)** - Password manager trusted by millions
- **[Malwarebytes](https://malwarebytes.com/affiliate-link)** - Advanced malware protection

*As a cybersecurity affiliate, I earn from qualifying purchases at no cost to you.*
# Email signup section with MailerLite
email_signup = """

---

## 🔒 Get FREE Cybersecurity Alerts

**Join 12,000+ families getting instant notifications about threats affecting their devices!**

<div style="background: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
    <div class="ml-embedded" data-form="158915078478890584"></div>
    <p style="font-size: 12px; color: #666; margin-top: 10px;">✅ Real-time threat alerts • Unsubscribe anytime</p>
</div>

<!-- MailerLite Universal -->
<script>
    (function(w,d,e,u,f,l,n){w[f]=w[f]||function(){(w[f].q=w[f].q||[])
    .push(arguments);},l=d.createElement(e),l.async=1,l.src=u,
    n=d.getElementsByTagName(e)[0],n.parentNode.insertBefore(l,n);})
    (window,document,'script','https://assets.mailerlite.com/js/universal.js','ml');
    ml('account', '1632878');
</script>
<!-- End MailerLite Universal -->

"""
---
*This post was generated automatically to provide you with the latest cybersecurity insights and practical protection strategies.*
"""
    
    os.makedirs('_posts', exist_ok=True)
    filename = f"_posts/{today}-daily-cybersecurity-update.md"
    
    with open(filename, 'w') as f:
        f.write(blog_post)
    
    print(f"Enhanced blog post created: {filename}")

if __name__ == "__main__":
    generate_blog_post()
