#!/usr/bin/env python3
"""
Super Simple Blog Generator
Just generates a cybersecurity blog post and saves it
"""

import os
import requests
from datetime import datetime
from openai import OpenAI

def generate_blog_post():
    """Generate a simple cybersecurity blog post"""
    
    # Initialize OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Simple prompt for cybersecurity content
    prompt = """Write a cybersecurity blog post about current threats and protection tips. 
    Make it informative and practical for everyday users. 
    Include specific actionable advice.
    Keep it around 800 words."""
    
    try:
        # Generate content with OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        blog_content = response.choices[0].message.content
        
        # Create blog post with Jekyll front matter
        blog_post = f"""---
layout: post
title: "Daily Cybersecurity Update - {today}"
date: {today}
categories: cybersecurity
tags: security tips threats
---

{blog_content}

---
*This post was generated automatically to keep you informed about cybersecurity best practices.*
"""
        
        # Save to _posts directory
        filename = f"_posts/{today}-daily-cybersecurity-update.md"
        
        # Create _posts directory if it doesn't exist
        os.makedirs('_posts', exist_ok=True)
        
        # Write the blog post
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(blog_post)
        
        print(f"✅ Blog post created: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating blog post: {e}")
        return False

if __name__ == "__main__":
    success = generate_blog_post()
    if success:
        print("🎉 Blog generation completed successfully!")
    else:
        print("💥 Blog generation failed!")
        exit(1)
