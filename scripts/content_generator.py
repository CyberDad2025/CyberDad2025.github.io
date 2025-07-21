#!/usr/bin/env python3
import os
from datetime import datetime
from openai import OpenAI

def generate_blog_post():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    today = datetime.now().strftime('%Y-%m-%d')
    
    prompt = "Write a cybersecurity blog post about current threats and protection tips. Make it informative and practical for everyday users."
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    blog_content = response.choices[0].message.content
    
    blog_post = f"""---
layout: post
title: "Daily Cybersecurity Update - {today}"
date: {today}
categories: cybersecurity
---

{blog_content}
"""
    
    os.makedirs('_posts', exist_ok=True)
    filename = f"_posts/{today}-daily-cybersecurity-update.md"
    
    with open(filename, 'w') as f:
        f.write(blog_post)
    
    print(f"Blog post created: {filename}")

if __name__ == "__main__":
    generate_blog_post()
