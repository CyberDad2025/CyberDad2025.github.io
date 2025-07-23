import requests
import feedparser
import openai
from datetime import datetime, timedelta
import schedule
import time
import json
import os
from dataclasses import dataclass
from typing import List, Dict
import yaml

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
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def fetch_cti_feeds(self) -> List[Dict]:
        """Fetch latest cybersecurity threat intelligence"""
        all_threats = []
        
        for feed_url in self.cti_sources:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:  # Latest 3 from each source
                    all_threats.append({
                        'title': entry.title,
                        'summary': entry.summary,
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'source': feed.feed.title
                    })
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
        
        return all_threats[:10]  # Top 10 most recent
    
    def convert_to_family_friendly(self, threat_data: Dict) -> CyberThreatIntel:
        """Convert technical CTI to family-friendly content using AI"""
        
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
        
        Keep it conversational and actionable for busy parents.
        """
        
        # Using OpenAI API (replace with your preferred AI service)
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            return self.parse_ai_response(content, threat_data['link'])
            
        except Exception as e:
            print(f"AI conversion error: {e}")
            return self.create_fallback_content(threat_data)
    
    def parse_ai_response(self, ai_content: str, source_link: str) -> CyberThreatIntel:
        """Parse AI response into structured content"""
        lines = ai_content.split('\n')
        
        # Simple parsing logic - you might want to make this more robust
        title = "Family Cybersecurity Alert"
        description = ai_content[:200] + "..."
        severity = "Medium"
        family_impact = "Potential risk to family devices and data"
        prevention_tips = ["Keep software updated", "Use strong passwords", "Be cautious with links"]
        product_tie_in = "Digital Shield Kit"
        
        return CyberThreatIntel(
            title=title,
            description=description,
            severity=severity,
            family_impact=family_impact,
            prevention_tips=prevention_tips,
            product_tie_in=product_tie_in
        )
    
    def create_blog_post(self, threat_intel: CyberThreatIntel) -> str:
        """Generate complete blog post HTML"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        blog_post = f"""
        ---
        layout: post
        title: "{threat_intel.title}"
        date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        categories: [cybersecurity, family-safety]
        tags: [parenting, tech-safety, cyber-threats]
        ---
        
        # {threat_intel.title}
        
        **Alert Level: {threat_intel.severity}** | **Date: {current_date}**
        
        ## What Parents Need to Know
        
        {threat_intel.description}
        
        ## How This Affects Your Family
        
        {threat_intel.family_impact}
        
        ## Protect Your Family Today
        
        """
        
        for i, tip in enumerate(threat_intel.prevention_tips, 1):
            blog_post += f"{i}. {tip}\n"
        
        blog_post += f"""
        
        ## 🛡️ Get Extra Protection
        
        This threat highlights why every family needs the **{threat_intel.product_tie_in}**. 
        
        [🔒 Protect Your Family Now - Get {threat_intel.product_tie_in}]({self.config['products'][threat_intel.product_tie_in]['link']})
        
        *Special offer: Use code CYBERDAD20 for 20% off this week only!*
        
        ## Free Family Security Checklist
        
        Want our complete Family Wi-Fi Security Checklist? It's free!
        
        [📋 Download Free Checklist]({self.config['lead_magnets']['wifi_checklist']})
        
        ---
        
        **Stay Safe, Cyber Dads & Moms!** 👨‍👩‍👧‍👦
        
        *Follow us for daily family cybersecurity tips:*
        - [Instagram]({self.config['social']['instagram']})
        - [Threads]({self.config['social']['threads']})
        - [Pinterest]({self.config['social']['pinterest']})
        
        """
        
        return blog_post

class GitHubBlogPublisher:
    def __init__(self, repo_path, github_token=None):
        self.repo_path = repo_path
        self.github_token = github_token
        
    def publish_post(self, content: str, filename: str):
        """Publish post to GitHub Pages"""
        posts_dir = os.path.join(self.repo_path, '_posts')
        filepath = os.path.join(posts_dir, filename)
        
        # Write the post
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Git operations
        os.system(f'cd {self.repo_path} && git add .')
        os.system(f'cd {self.repo_path} && git commit -m "Auto-post: {filename}"')
        os.system(f'cd {self.repo_path} && git push origin main')
        
        print(f"Published: {filename}")

class PinterestAutomation:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://api.pinterest.com/v5"
        
    def create_pin(self, title: str, description: str, link: str, image_url: str):
        """Create Pinterest pin from blog post"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        pin_data = {
            'title': title,
            'description': description,
            'link': link,
            'media_source': {
                'source_type': 'image_url',
                'url': image_url
            }
        }
        
        response = requests.post(
            f"{self.base_url}/pins",
            headers=headers,
            json=pin_data
        )
        
        return response.status_code == 201

class CyberDadAutomation:
    def __init__(self):
        self.content_engine = CyberDadContentEngine()
        self.blog_publisher = GitHubBlogPublisher('/path/to/cyberdad2025.github.io')
        self.pinterest = PinterestAutomation(os.getenv('PINTEREST_ACCESS_TOKEN'))
        
    def daily_content_cycle(self):
        """Main automation cycle - runs 3x daily"""
        print(f"🚀 Starting Cyber Dad content cycle at {datetime.now()}")
        
        # 1. Fetch latest threats
        threats = self.content_engine.fetch_cti_feeds()
        
        if not threats:
            print("No new threats found")
            return
        
        # 2. Convert to family-friendly content
        selected_threat = threats[0]  # Most recent
        family_content = self.content_engine.convert_to_family_friendly(selected_threat)
        
        # 3. Create blog post
        blog_post = self.content_engine.create_blog_post(family_content)
        
        # 4. Publish to GitHub Pages
        filename = f"{datetime.now().strftime('%Y-%m-%d')}-{family_content.title.lower().replace(' ', '-')}.md"
        self.blog_publisher.publish_post(blog_post, filename)
        
        # 5. Create Pinterest pin
        blog_url = f"https://cyberdad2025.github.io/{filename.replace('.md', '.html')}"
        pin_description = f"{family_content.description[:100]}... 🛡️ Protect your family with our Cyber Dad Kit! #CyberSecurity #FamilySafety #ParentingTips"
        
        self.pinterest.create_pin(
            title=family_content.title,
            description=pin_description,
            link=blog_url,
            image_url="https://your-cdn.com/cyberdad-alert-template.png"
        )
        
        print(f"✅ Published: {family_content.title}")

# Configuration file (cyberdad_config.yaml)
config_template = """
products:
  Digital Shield Kit:
    link: "https://etsy.com/shop/cyberdadprints/digital-shield-kit"
    price: 47
  Password Safety Kit:
    link: "https://etsy.com/shop/cyberdadprints/password-kit"
    price: 7.99
  Screen-Free Activity Pack:
    link: "https://etsy.com/shop/cyberdadprints/screen-free-pack"
    price: 14
  Family Tech Rules Pack:
    link: "https://etsy.com/shop/cyberdadprints/tech-rules"
    price: 9.99

lead_magnets:
  wifi_checklist: "https://cyberdad2025.github.io/free-wifi-checklist"
  starter_pack: "https://gumroad.com/l/cyberdad-starter"

social:
  instagram: "https://instagram.com/cyberdad2025"
  threads: "https://threads.net/@cyberdad2025"
  pinterest: "https://pinterest.com/cyberdad2025"

email:
  mailerlite_api_key: "your_api_key"
  list_id: "your_list_id"

posting_schedule:
  times: ["09:00", "13:00", "20:00"]
  timezone: "EST"
"""

# Main execution
def main():
    automation = CyberDadAutomation()
    
    # Schedule posts
    schedule.every().day.at("09:00").do(automation.daily_content_cycle)
    schedule.every().day.at("13:00").do(automation.daily_content_cycle)
    schedule.every().day.at("20:00").do(automation.daily_content_cycle)
    
    print("🚀 Cyber Dad Automation Engine Started!")
    print("📅 Scheduled posts: 9 AM, 1 PM, 8 PM EST")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
