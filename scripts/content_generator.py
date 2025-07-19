#!/usr/bin/env python3
"""
CyberDad CTI Backend System - Blog Post Generator
Scrapes CTI feeds, generates family-friendly blog posts, creates Jekyll markdown files
Runs 3x daily: CTI alerts, tips, guides
"""

import requests
import openai
import os
import json
import feedparser
import hashlib
import time
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import yaml

class CyberDadContentGenerator:
    def __init__(self):
        # API Keys
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.pinterest_token = os.getenv('PINTEREST_ACCESS_TOKEN')  # For future use
        self.board_id = os.getenv('PINTEREST_BOARD_ID')  # For future use
        
        # Content tracking
        self.existing_posts = set()
        self.content_calendar = {}
        
        # CTI Intelligence Sources
        self.cti_sources = [
            {
                'name': 'CISA Alerts',
                'url': 'https://www.cisa.gov/news-events/cybersecurity-advisories.rss',
                'type': 'government',
                'priority': 'high'
            },
            {
                'name': 'Krebs Security',
                'url': 'https://krebsonsecurity.com/feed/',
                'type': 'security_news',
                'priority': 'medium'
            },
            {
                'name': 'Threatpost',
                'url': 'https://threatpost.com/feed/',
                'type': 'security_news',
                'priority': 'medium'
            },
            {
                'name': 'Security Week',
                'url': 'https://feeds.feedburner.com/securityweek',
                'type': 'security_news',
                'priority': 'medium'
            },
            {
                'name': 'Bleeping Computer',
                'url': 'https://www.bleepingcomputer.com/feed/',
                'type': 'security_news',
                'priority': 'high'
            }
        ]
        
        # Family IoT/Home Device Keywords
        self.family_keywords = [
            'smart home', 'iot', 'router', 'wifi', 'alexa', 'google home', 'siri',
            'ring doorbell', 'nest', 'smart tv', 'smart thermostat', 'smart bulb',
            'baby monitor', 'security camera', 'smart lock', 'mesh network',
            'home automation', 'smart speaker', 'chromecast', 'roku', 'apple tv',
            'smart watch', 'fitness tracker', 'tablet', 'smartphone', 'android',
            'iphone', 'ipad', 'smart fridge', 'smart garage', 'family', 'parents',
            'children', 'kids', 'teens', 'home', 'household', 'personal', 'consumer'
        ]
        
        # Content types and their distribution
        self.content_types = {
            'cti_alert': {
                'percentage': 40,
                'templates': ['security_alert', 'vulnerability_guide', 'urgent_update'],
                'tone': 'informative but not alarming'
            },
            'quick_tip': {
                'percentage': 35,
                'templates': ['device_tip', 'privacy_check', 'security_hack'],
                'tone': 'helpful and practical'
            },
            'family_guide': {
                'percentage': 25,
                'templates': ['comprehensive_guide', 'setup_tutorial', 'family_strategy'],
                'tone': 'educational and thorough'
            }
        }

    def load_existing_posts(self):
        """Load existing blog posts to prevent duplicates"""
        try:
            print("📚 Loading existing blog posts for duplicate detection...")
            
            # Check _posts directory for existing Jekyll posts
            posts_dir = "_posts"
            if os.path.exists(posts_dir):
                for filename in os.listdir(posts_dir):
                    if filename.endswith('.md'):
                        with open(os.path.join(posts_dir, filename), 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Extract title from front matter
                            if '---' in content:
                                try:
                                    front_matter = content.split('---')[1]
                                    title_match = re.search(r'title:\s*["\']?(.*?)["\']?\n', front_matter)
                                    if title_match:
                                        title = title_match.group(1).strip()
                                        content_hash = hashlib.md5(title.lower().encode()).hexdigest()[:8]
                                        self.existing_posts.add(content_hash)
                                except:
                                    pass
            
            print(f"✅ Loaded {len(self.existing_posts)} existing posts for duplicate detection")
            
        except Exception as e:
            print(f"⚠️ Could not load existing posts: {e}")

    def scrape_cti_intelligence(self):
        """Scrape latest CTI from multiple sources"""
        print("🕵️ Scraping cybersecurity threat intelligence...")
        
        all_threats = []
        
        for source in self.cti_sources:
            try:
                print(f"📡 Checking {source['name']}...")
                threats = self.scrape_rss_source(source)
                all_threats.extend(threats)
                time.sleep(2)  # Be respectful to sources
                
            except Exception as e:
                print(f"⚠️ Error with {source['name']}: {e}")
                continue
        
        # Filter for family/home relevant threats
        relevant_threats = self.filter_family_relevant(all_threats)
        print(f"🎯 Found {len(relevant_threats)} family-relevant threats")
        
        return relevant_threats

    def scrape_rss_source(self, source):
        """Scrape threats from RSS feed"""
        threats = []
        
        try:
            feed = feedparser.parse(source['url'])
            
            for entry in feed.entries[:10]:  # Latest 10 from each source
                threat = {
                    'title': entry.title,
                    'summary': entry.get('summary', entry.get('description', entry.title))[:500],
                    'url': entry.link,
                    'published': entry.get('published', datetime.now().isoformat()),
                    'source': source['name'],
                    'type': source['type'],
                    'priority': source['priority']
                }
                threats.append(threat)
                
        except Exception as e:
            print(f"❌ RSS scrape failed for {source['name']}: {e}")
            
        return threats

    def filter_family_relevant(self, threats):
        """Filter threats relevant to families and home users"""
        relevant = []
        
        for threat in threats:
            text = (threat['title'] + ' ' + threat['summary']).lower()
            
            # Check if contains family/home keywords
            relevance_score = sum(1 for keyword in self.family_keywords if keyword in text)
            
            if relevance_score > 0:
                # Check if not already covered
                title_hash = hashlib.md5(threat['title'].lower().encode()).hexdigest()[:8]
                
                if title_hash not in self.existing_posts:
                    threat['relevance_score'] = relevance_score
                    threat['content_hash'] = title_hash
                    relevant.append(threat)
                else:
                    print(f"🔄 Skipping duplicate: {threat['title'][:50]}...")
        
        # Sort by relevance score (most relevant first)
        relevant.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant

    def determine_content_type(self):
        """Determine what type of content to generate based on distribution"""
        # Simple rotation logic - can be enhanced with more sophisticated scheduling
        current_hour = datetime.now().hour
        
        if current_hour < 8:  # Early morning - tips
            return 'quick_tip'
        elif current_hour < 16:  # Daytime - CTI alerts
            return 'cti_alert'
        else:  # Evening - guides
            return 'family_guide'

    def generate_family_content(self, threat_data=None, content_type=None):
        """Generate family-friendly content using AI"""
        
        if not self.openai_key:
            return self.create_fallback_content(threat_data, content_type)
        
        content_type = content_type or self.determine_content_type()
        
        print(f"🤖 Generating {content_type} content...")
        
        try:
            openai.api_key = self.openai_key
            
            if content_type == 'cti_alert' and threat_data:
                prompt = self.create_cti_prompt(threat_data)
            elif content_type == 'quick_tip':
                prompt = self.create_tip_prompt()
            else:  # family_guide
                prompt = self.create_guide_prompt()
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are CyberDad, a cybersecurity expert who helps families stay safe online. Write practical, actionable content that busy parents can understand and implement. Always use a helpful, reassuring tone - never scary or alarmist. Focus on simple solutions that work for real families."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            ai_content = response.choices[0].message.content.strip()
            
            return self.parse_ai_content(ai_content, content_type, threat_data)
            
        except Exception as e:
            print(f"⚠️ AI generation failed: {e}")
            return self.create_fallback_content(threat_data, content_type)

    def create_cti_prompt(self, threat_data):
        """Create prompt for CTI-based content"""
        return f"""
        Convert this cybersecurity threat into a helpful family blog post:
        
        THREAT: {threat_data['title']}
        DETAILS: {threat_data['summary'][:300]}
        SOURCE: {threat_data['source']}
        
        REQUIREMENTS:
        - Write for busy parents (ages 25-55)
        - Explain what this means for families in simple terms
        - Focus on devices/services families actually use
        - Provide 3-5 specific protection steps
        - Keep tone helpful and reassuring, not scary
        - Include why this matters for family safety
        - Perfect for ages 4-99 to understand
        - 400-600 words
        
        FORMAT:
        Title: [Catchy, family-friendly title]
        
        Introduction: [What this means for families]
        
        Why This Matters: [Family impact explanation]
        
        Simple Protection Steps:
        1. [Specific action]
        2. [Specific action]
        3. [Specific action]
        
        Family Tip: [Additional helpful advice]
        
        Bottom Line: [Reassuring summary]
        """

    def create_tip_prompt(self):
        """Create prompt for quick tip content"""
        tip_topics = [
            "router security settings families should check",
            "smart TV privacy settings parents miss", 
            "smartphone security for kids and teens",
            "home WiFi protection for families",
            "password security for busy parents",
            "smart speaker privacy for family homes",
            "gaming console safety for kids",
            "social media privacy for families",
            "backup strategies for family photos",
            "parental controls that actually work"
        ]
        
        topic = random.choice(tip_topics)
        
        return f"""
        Write a helpful cybersecurity tip about {topic}.
        
        REQUIREMENTS:
        - Quick, actionable advice (3-4 minutes to read)
        - Specific steps families can take today
        - Focus on one main tip with clear instructions
        - Include why this matters for family safety
        - Keep tone friendly and encouraging
        - Perfect for ages 4-99 to understand
        - 300-400 words
        
        FORMAT:
        Title: [Clear, benefit-focused title]
        
        The Problem: [What families face]
        
        Simple Solution: [Step-by-step instructions]
        
        Why This Works: [Explanation of benefits]
        
        Pro Tip: [Bonus advice]
        """

    def create_guide_prompt(self):
        """Create prompt for comprehensive guide content"""
        guide_topics = [
            "complete family password strategy",
            "smart home security setup for families",
            "digital parenting and device safety",
            "family internet safety rules and guidelines",
            "protecting kids online: age-appropriate strategies",
            "home network security for non-technical parents",
            "family cloud storage and backup strategy",
            "teaching kids about cybersecurity and privacy",
            "family emergency cybersecurity plan",
            "choosing family-friendly security tools"
        ]
        
        topic = random.choice(guide_topics)
        
        return f"""
        Write a comprehensive family guide about {topic}.
        
        REQUIREMENTS:
        - Thorough but accessible explanation
        - Step-by-step implementation guide
        - Include specific product recommendations
        - Address different family situations
        - Provide troubleshooting tips
        - Keep tone educational but encouraging
        - Perfect for ages 4-99 to understand
        - 600-800 words
        
        FORMAT:
        Title: [Comprehensive, value-focused title]
        
        Introduction: [Why families need this]
        
        Step-by-Step Guide:
        1. [Detailed step]
        2. [Detailed step]
        3. [Detailed step]
        
        Family Considerations: [Age-specific advice]
        
        Recommended Tools: [Specific products/services]
        
        Troubleshooting: [Common issues and solutions]
        
        Next Steps: [What to do after implementation]
        """

    def parse_ai_content(self, ai_content, content_type, threat_data=None):
        """Parse AI-generated content into structured format"""
        lines = ai_content.split('\n')
        
        # Extract title
        title_line = next((line for line in lines if line.startswith('Title:')), lines[0])
        title = re.sub(r'^Title:\s*', '', title_line).strip()
        
        # Clean and structure content
        content_body = '\n'.join(lines[1:]).strip()
        
        # Remove title from content body if it's repeated
        if title in content_body:
            content_body = content_body.replace(title, '').strip()
        
        return {
            'title': title,
            'content': content_body,
            'content_type': content_type,
            'category': self.determine_category(content_body, threat_data),
            'tags': self.generate_tags(content_body, content_type),
            'source_threat': threat_data,
            'reading_time': self.estimate_reading_time(content_body),
            'difficulty': self.determine_difficulty(content_type)
        }

    def create_fallback_content(self, threat_data=None, content_type='quick_tip'):
        """Create basic content when AI fails"""
        fallback_content = {
            'cti_alert': {
                'title': f"Security Update: {threat_data['title'][:50] if threat_data else 'Keep Your Devices Updated'}",
                'content': f"A new security issue has been discovered that may affect family devices. {threat_data['summary'][:200] if threat_data else 'Regular updates help protect your family from cyber threats.'} Here's what families should do: 1) Update all devices, 2) Check security settings, 3) Monitor for unusual activity.",
                'category': 'security-alerts'
            },
            'quick_tip': {
                'title': "Quick Security Tip: Check Your Router Settings",
                'content': "Your home router is the gateway to your family's internet connection. Most routers come with default passwords that are easy for hackers to guess. Take 2 minutes to log into your router and change the admin password to something strong and unique. This simple step protects your entire family's internet activity.",
                'category': 'home-network'
            },
            'family_guide': {
                'title': "Family Password Safety: A Complete Guide",
                'content': "Strong passwords are your family's first line of defense against cyber attacks. Every family member should use unique passwords for each account. Consider using a family password manager to generate and store secure passwords. Teach kids about password safety early. Enable two-factor authentication on important accounts. Review and update passwords regularly.",
                'category': 'password-security'
            }
        }
        
        template = fallback_content.get(content_type, fallback_content['quick_tip'])
        
        return {
            'title': template['title'],
            'content': template['content'],
            'content_type': content_type,
            'category': template['category'],
            'tags': ['cybersecurity', 'family-safety', 'easy-guide'],
            'source_threat': threat_data,
            'reading_time': '3 minutes',
            'difficulty': 'Beginner'
        }

    def determine_category(self, content, threat_data=None):
        """Determine post category based on content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['router', 'wifi', 'network', 'internet']):
            return 'home-network'
        elif any(word in content_lower for word in ['smart home', 'iot', 'alexa', 'nest', 'smart tv']):
            return 'smart-home'
        elif any(word in content_lower for word in ['mobile', 'phone', 'iphone', 'android', 'tablet']):
            return 'mobile-security'
        elif any(word in content_lower for word in ['password', 'login', 'account', 'authentication']):
            return 'password-security'
        elif any(word in content_lower for word in ['kids', 'children', 'teens', 'parental']):
            return 'family-safety'
        elif any(word in content_lower for word in ['privacy', 'data', 'tracking']):
            return 'privacy-tips'
        else:
            return 'cybersecurity'

    def generate_tags(self, content, content_type):
        """Generate relevant tags for the post"""
        base_tags = ['cybersecurity', 'family-safety']
        
        content_lower = content.lower()
        
        # Add content-specific tags
        if 'router' in content_lower: base_tags.append('home-network')
        if 'password' in content_lower: base_tags.append('password-security')
        if 'smart' in content_lower: base_tags.append('smart-home')
        if 'kids' in content_lower or 'children' in content_lower: base_tags.append('parental-guidance')
        if 'privacy' in content_lower: base_tags.append('privacy-tips')
        if 'mobile' in content_lower or 'phone' in content_lower: base_tags.append('mobile-security')
        
        # Add content type tag
        if content_type == 'cti_alert': base_tags.append('security-alert')
        elif content_type == 'quick_tip': base_tags.append('quick-tip')
        elif content_type == 'family_guide': base_tags.append('comprehensive-guide')
        
        base_tags.append('easy-guide')  # Always add this
        
        return list(set(base_tags))  # Remove duplicates

    def estimate_reading_time(self, content):
        """Estimate reading time based on word count"""
        words = len(content.split())
        minutes = max(1, round(words / 200))  # Assume 200 words per minute
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

    def determine_difficulty(self, content_type):
        """Determine difficulty level"""
        difficulty_map = {
            'quick_tip': 'Beginner',
            'cti_alert': 'Beginner', 
            'family_guide': 'Intermediate'
        }
        return difficulty_map.get(content_type, 'Beginner')

    def create_jekyll_post(self, content_data):
        """Create Jekyll markdown post file"""
        
        # Generate filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        title_slug = re.sub(r'[^\w\s-]', '', content_data['title'].lower())
        title_slug = re.sub(r'\s+', '-', title_slug)[:50]
        filename = f"{date_str}-{title_slug}.md"
        
        # Create front matter
        front_matter = {
            'layout': 'post',
            'title': content_data['title'],
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S %z') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'categories': [content_data['category'], 'family-safety'],
            'tags': content_data['tags'],
            'excerpt': self.create_excerpt(content_data['content']),
            'reading_time': content_data['reading_time'],
            'difficulty': content_data['difficulty'],
            'perfect_for_ages': '4-99'
        }
        
        # Add source attribution if CTI-based
        if content_data['source_threat']:
            front_matter['source'] = content_data['source_threat']['source']
            front_matter['cti_based'] = True
        
        # Create full post content
        post_content = f"""---
{yaml.dump(front_matter, default_flow_style=False)}---

{content_data['content']}

---

## 🛡️ Keep Your Family Safe

Want more family cybersecurity tips? [Get our free family security checklist](https://cyberdad2025.github.io) and join 1,200+ families staying safe online.

### 🔧 Recommended Security Tools:
- **VPN Protection**: [NordVPN for Families](https://affiliate-link) 
- **Password Manager**: [1Password Family Plan](https://affiliate-link)
- **Antivirus**: [Norton Family Security](https://affiliate-link)

### 📚 Related Resources:
- [Complete Family Security Guide](https://payhip.com/CyberDadKit)
- [Printable Security Checklists](https://www.etsy.com/shop/CyberDadPrints)
- [Digital Safety Worksheets](https://cyberdad.gumroad.com/l/ojawof)

*Remember: Perfect for ages 4-99! Share this with other families who need to stay cyber-safe.*
"""
        
        return filename, post_content

    def create_excerpt(self, content):
        """Create excerpt from content"""
        sentences = content.split('.')[:2]  # First 2 sentences
        excerpt = '. '.join(sentences)
        if len(excerpt) > 160:
            excerpt = excerpt[:157] + "..."
        return excerpt

    def save_post(self, filename, content):
        """Save Jekyll post to _posts directory"""
        try:
            # Create _posts directory if it doesn't exist
            os.makedirs('_posts', exist_ok=True)
            
            filepath = os.path.join('_posts', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Blog post saved: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save post: {e}")
            return False

    def log_generation_activity(self, success, content_title="", content_type="", source="", error=None):
        """Log content generation activity"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "content_title": content_title,
            "content_type": content_type,
            "source": source,
            "error": str(error) if error else None
        }
        
        try:
            os.makedirs('logs', exist_ok=True)
            log_file = f"logs/content_generation_{datetime.now().strftime('%Y%m%d')}.json"
            
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            
            logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Logging failed: {e}")

    def run_content_generation(self):
        """Main content generation function"""
        print("🚀 CYBERDAD CONTENT GENERATION SYSTEM")
        print("=" * 60)
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Step 1: Load existing posts
            self.load_existing_posts()
            
            # Step 2: Determine content type for this run
            content_type = self.determine_content_type()
            print(f"📝 Generating {content_type} content...")
            
            # Step 3: Get CTI data if needed
            threat_data = None
            if content_type == 'cti_alert':
                threats = self.scrape_cti_intelligence()
                if threats:
                    threat_data = threats[0]  # Use most relevant threat
                    print(f"🎯 Using threat: {threat_data['title'][:50]}...")
                else:
                    print("⚠️ No relevant threats found, switching to tip content")
                    content_type = 'quick_tip'
            
            # Step 4: Generate family-friendly content
            content_data = self.generate_family_content(threat_data, content_type)
            
            # Step 5: Create Jekyll post
            filename, post_content = self.create_jekyll_post(content_data)
            
            # Step 6: Save post
            success = self.save_post(filename, post_content)
            
            # Step 7: Update existing posts tracking
            if success:
                self.existing_posts.add(content_data.get('content_hash', hashlib.md5(content_data['title'].encode()).hexdigest()[:8]))
            
            # Step 8: Log activity
            self.log_generation_activity(
                success=success,
                content_title=content_data['title'],
                content_type=content_type,
                source=threat_data['source'] if threat_data else 'Generated'
            )
            
            print("=" * 60)
            if success:
                print("✅ CONTENT GENERATION SUCCESS!")
                print(f"📄 Created: {content_data['title']}")
                print(f"📂 File: {filename}")
                print(f"🏷️ Type: {content_type}")
                print(f"📚 Category: {content_data['category']}")
                print(f"⏱️ Reading time: {content_data['reading_time']}")
                if threat_data:
                    print(f"🕵️ Source: {threat_data['source']}")
            else:
                print("❌ CONTENT GENERATION FAILED!")
            
            print(f"🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return success
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR: {e}")
            self.log_generation_activity(False, error=str(e))
            return False

def main():
    """Entry point for GitHub Actions"""
    generator = CyberDadContentGenerator()
    
    # Add random delay to avoid rate limiting
    delay = random.randint(5, 30)
    print(f"⏱️ Starting delay: {delay} seconds")
    time.sleep(delay)
    
    # Run content generation
    success = generator.run_content_generation()
    
    if success:
        print("🎉 CyberDad content generation completed successfully!")
        exit(0)
    else:
        print("💥 Content generation failed!")
        exit(1)

if __name__ == "__main__":
    main()
