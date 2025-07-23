#!/usr/bin/env python3
"""
Multi-AI Fallback Blog Generator
Tries multiple AI services to ensure content creation
"""

import os
import sys
import json
import random
import yaml
import requests
from datetime import datetime

class MultiAIBlogGenerator:
    def __init__(self):
        # API keys from environment
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY') 
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.cohere_key = os.getenv('COHERE_API_KEY')
        
        # Family cybersecurity topics
        self.topics = [
            "Password Manager Setup for Families",
            "Home Router Security in 5 Minutes", 
            "Smart TV Privacy Settings Guide",
            "iPhone Security for Parents",
            "Family WiFi Safety Checklist",
            "Two-Factor Authentication Made Simple",
            "Social Media Privacy for Teens",
            "Online Shopping Security Tips",
            "Identity Theft Prevention for Families",
            "Kids Internet Safety Guide",
            "Smart Home Device Security",
            "Phishing Email Recognition",
            "Family Data Backup Strategy",
            "Secure Video Calling for Families",
            "Gaming Console Safety Settings"
        ]
        
        self.content_prompt = """Write a comprehensive cybersecurity blog post for families about: {topic}

Requirements:
- 600-800 words
- Simple, non-technical language for parents
- Include step-by-step instructions
- Add practical examples families can relate to
- Focus on actionable advice
- Include a quick checklist at the end
- Keep it family-friendly and encouraging

Structure:
1. Introduction explaining why this matters for families
2. Main content with practical steps
3. Common mistakes to avoid
4. Quick action checklist
5. Encouraging conclusion

Write as "CyberDad" - a helpful cybersecurity expert for families."""

    def try_openai(self, topic):
        """Try OpenAI API first"""
        if not self.openai_key:
            return None
            
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are CyberDad, a family cybersecurity expert."},
                    {"role": "user", "content": self.content_prompt.format(topic=topic)}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            print("✅ OpenAI generation successful")
            return content
            
        except Exception as e:
            print(f"❌ OpenAI failed: {e}")
            return None

    def try_anthropic(self, topic):
        """Try Anthropic Claude API"""
        if not self.anthropic_key:
            return None
            
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1200,
                messages=[{
                    "role": "user", 
                    "content": self.content_prompt.format(topic=topic)
                }]
            )
            
            content = response.content[0].text
            print("✅ Anthropic generation successful")
            return content
            
        except Exception as e:
            print(f"❌ Anthropic failed: {e}")
            return None

    def try_gemini(self, topic):
        """Try Google Gemini API"""
        if not self.gemini_key:
            return None
            
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_key}"
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": self.content_prompt.format(topic=topic)
                    }]
                }]
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text']
                print("✅ Gemini generation successful")
                return content
            else:
                print(f"❌ Gemini API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Gemini failed: {e}")
            return None

    def try_cohere(self, topic):
        """Try Cohere API"""
        if not self.cohere_key:
            return None
            
        try:
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "command",
                "prompt": self.content_prompt.format(topic=topic),
                "max_tokens": 1200,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['generations'][0]['text']
                print("✅ Cohere generation successful")
                return content
            else:
                print(f"❌ Cohere API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Cohere failed: {e}")
            return None

    def create_fallback_content(self, topic):
        """Final fallback - always works"""
        print("🔄 Using final fallback content")
        
        return f"""# {topic}

Keeping your family safe online is crucial in today's digital world. This guide provides practical steps you can take today to improve your family's cybersecurity.

## Why This Matters for Your Family

Digital security affects every family member. From protecting your children's personal information to securing your financial accounts, {topic.lower()} plays a vital role in your family's online safety.

## Simple Steps to Get Started

### Step 1: Assess Your Current Situation
Take a few minutes to evaluate your current security practices. Look for areas where simple improvements can make a big difference.

### Step 2: Start with the Basics
Focus on fundamental security measures that provide the most protection with minimal effort. These form the foundation of good family cybersecurity.

### Step 3: Involve Everyone
Make security a family effort. When everyone understands and participates, your entire household becomes more secure.

### Step 4: Make It a Habit
Consistency is key to effective security. Regular practices protect your family better than one-time setup.

## Common Mistakes to Avoid

- Using the same password across multiple important accounts
- Ignoring software updates and security patches
- Sharing personal information with unknown contacts online
- Assuming that "it won't happen to us"

## Quick Action Checklist

Use this checklist to improve your family's security today:

- [ ] Update passwords on your most important accounts
- [ ] Enable automatic updates on family devices
- [ ] Review privacy settings on social media accounts
- [ ] Talk to family members about online safety
- [ ] Set up two-factor authentication on critical accounts
- [ ] Create a family plan for handling security incidents

## Making Security Simple for Your Family

The best security measures are ones your family will actually use consistently. Start with simple changes and gradually build better habits.

Remember: small, consistent security practices are much more effective than complex systems that get abandoned.

## Next Steps

Choose one item from the checklist above and implement it today. Once that becomes routine, add another security practice.

Your family's digital safety is worth the small effort these steps require.

---

**Stay safe and stay informed!**

*This guide is part of our family cybersecurity series. For more tips and resources, visit our security section.*
"""

    def generate_content_with_fallbacks(self, topic):
        """Try all AI services in order until one works"""
        print(f"🎯 Generating content for: {topic}")
        print("🔄 Trying AI services in order...")
        
        # Try each AI service
        ai_methods = [
            ("OpenAI", self.try_openai),
            ("Anthropic", self.try_anthropic), 
            ("Gemini", self.try_gemini),
            ("Cohere", self.try_cohere)
        ]
        
        for ai_name, ai_method in ai_methods:
            print(f"🤖 Trying {ai_name}...")
            content = ai_method(topic)
            if content:
                return content, ai_name
        
        # If all AI services fail, use fallback
        print("⚠️ All AI services failed, using fallback content")
        content = self.create_fallback_content(topic)
        return content, "Fallback"

    def create_blog_post(self, topic, content, ai_used):
        """Create Jekyll blog post"""
        try:
            # Create filename
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            title_slug = topic.lower().replace(' ', '-').replace(':', '').replace('/', '-')
            title_slug = ''.join(c for c in title_slug if c.isalnum() or c in '-')[:50]
            filename = f"{date_str}-{title_slug}.md"
            
            # Create frontmatter
            frontmatter = {
                'layout': 'post',
                'title': topic,
                'date': now.strftime('%Y-%m-%d %H:%M:%S +0000'),
                'categories': ['cybersecurity', 'family'],
                'tags': ['family-safety', 'cybersecurity', 'digital-parenting'],
                'excerpt': content[:150] + '...',
                'author': 'CyberDad',
                'ai_generated': ai_used,
                'reading_time': f"{max(1, len(content.split()) // 200)} min read"
            }
            
            # Create complete post
            post_content = f"""---
{yaml.dump(frontmatter, default_flow_style=False)}---

{content}

---

## 🛡️ More Family Security Resources

- [Family Password Security Guide](/password-security)
- [Smart Home Security Checklist](/smart-home-security) 
- [Kids Online Safety Guide](/kids-safety)

**Generated by**: {ai_used} AI • **Updated**: {now.strftime('%B %Y')}

*Stay safe, CyberDad Team* 🔒
"""
            
            # Write file
            os.makedirs('_posts', exist_ok=True)
            filepath = os.path.join('_posts', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(post_content)
            
            print(f"✅ Created: {filename}")
            print(f"🤖 Using: {ai_used}")
            return True
            
        except Exception as e:
            print(f"❌ Post creation failed: {e}")
            return False

    def run(self):
        """Main execution"""
        try:
            print("🚀 Multi-AI Blog Generator Starting...")
            print("=" * 50)
            
            # Select topic
            topic = random.choice(self.topics)
            print(f"📝 Topic: {topic}")
            
            # Generate content with fallbacks
            content, ai_used = self.generate_content_with_fallbacks(topic)
            
            # Create blog post
            success = self.create_blog_post(topic, content, ai_used)
            
            if success:
                print("\n🎉 SUCCESS!")
                print(f"✅ Blog post created using {ai_used}")
                return True
            else:
                print("\n❌ FAILED!")
                return False
                
        except Exception as e:
            print(f"💥 Critical error: {e}")
            return False

def main():
    generator = MultiAIBlogGenerator()
    success = generator.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
