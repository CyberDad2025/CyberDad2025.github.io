#!/usr/bin/env python3
"""
Simple Blog Generator - NO F-STRING ISSUES
Just works without complex syntax
"""

import os
from datetime import datetime
from openai import OpenAI

def generate_blog_post():
    # Get current date
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Simple prompt - no complex formatting
    prompt = """Write a comprehensive cybersecurity blog post for families. 
    Include 5-7 practical tips that parents can use to protect their children online.
    Make it 1200+ words, professional but easy to understand.
    Focus on current threats and real protection steps families can take today."""
    
    # Generate content
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    
    # Get the content
    blog_content = response.choices[0].message.content
    
    # Create title
    title = "Daily Cybersecurity Update - " + today
    
    # Affiliate section
    affiliate_links = """

## 🛡️ Recommended Security Tools

Protect your family with these trusted cybersecurity solutions:

- **[Norton 360 Deluxe](https://norton.com/affiliate-link)** - Complete family protection with VPN
- **[NordVPN](https://nordvpn.com/affiliate-link)** - Secure your internet connection worldwide  
- **[LastPass](https://lastpass.com/affiliate-link)** - Password manager trusted by millions
- **[Malwarebytes](https://malwarebytes.com/affiliate-link)** - Advanced malware protection

*As a cybersecurity affiliate, I earn from qualifying purchases at no cost to you.*"""

    # Email signup section
    email_section = """

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
<!-- End MailerLite Universal -->"""

    # Build the complete blog post using simple string concatenation
    blog_post = "---\n"
    blog_post += "layout: post\n"
    blog_post += "title: \"" + title + "\"\n"
    blog_post += "date: " + today + "\n"
    blog_post += "categories: cybersecurity\n"
    blog_post += "tags: family-security online-safety cybersecurity-tips\n"
    blog_post += "author: CyberDad\n"
    blog_post += "excerpt: \"Essential cybersecurity guidance to keep your family safe online\"\n"
    blog_post += "---\n\n"
    blog_post += blog_content + "\n"
    blog_post += affiliate_links + "\n"
    blog_post += email_section + "\n"
    
    # Create filename
    filename = "_posts/" + today + "-daily-cybersecurity-update.md"
    
    # Create directory if needed
    os.makedirs('_posts', exist_ok=True)
    
    # Write the file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(blog_post)
    
    print("Blog post created successfully: " + filename)
    return True

if __name__ == "__main__":
    generate_blog_post()
