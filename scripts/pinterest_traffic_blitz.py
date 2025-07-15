#!/usr/bin/env python3
"""
Pinterest Traffic Blitz for GitHub Actions
Runs 5x daily automatically, each time with different content focus
"""

import openai
import requests
import os
import json
from datetime import datetime
import random

def generate_targeted_content():
    """Generate content based on time of day from environment"""
    
    openai.api_key = os.getenv('OPENAI_API_KEY')
    content_type = os.getenv('CONTENT_TYPE', 'general')
    
    content_templates = {
        'morning': {
            'prompt': 'Create a cybersecurity tip for busy parents getting kids ready for school. Focus on quick device safety checks and morning security routines.',
            'keywords': '#FamilyCybersecurity #MorningRoutine #KidsDeviceSafety #SchoolTech',
            'title_prefix': '🌅 Morning Security Tip',
            'cta': '👨‍👩‍👧‍👦 Start your day secure! Family Tech Rules Pack →'
        },
        'midday': {
            'prompt': 'Create a cybersecurity tip about password management that working parents can implement during a lunch break.',
            'keywords': '#PasswordSafety #FamilyPasswords #SecurePasswords #LunchBreakTips',
            'title_prefix': '🍽️ Lunch Break Security',
            'cta': '🔐 Secure passwords in 2 minutes! Password Safety Kit →'
        },
        'afternoon': {
            'prompt': 'Create a tip about protecting kids online after school - homework sites, social media, gaming safety.',
            'keywords': '#KidsOnlineSafety #AfterSchoolSafety #SocialMediaSafety #GamingSafety',
            'title_prefix': '🎒 After School Safety',
            'cta': '🛡️ Keep kids safe online! Screen-Free Activity Pack →'
        },
        'evening': {
            'prompt': 'Create a family cybersecurity activity for family time - checking settings, reviewing apps, security discussions.',
            'keywords': '#FamilyTime #CybersecurityCheck #HomeNetworkSecurity #FamilyTech',
            'title_prefix': '🏠 Family Security Time',
            'cta': '📋 Family security checklist! Cyber Threat Quick-Check →'
        },
        'night': {
            'prompt': 'Create a tip about securing home networks and devices before bedtime - router settings, device updates, overnight security.',
            'keywords': '#HomeNetworkSecurity #RouterSafety #DeviceUpdates #NightSecurity',
            'title_prefix': '🌙 Bedtime Security',
            'cta': '🛡️ Complete protection! Digital Shield Kit →'
        }
    }
    
    template = content_templates.get(content_type, content_templates['morning'])
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a cybersecurity expert helping families stay safe online. Write practical, actionable tips that busy parents can implement quickly."
            },
            {
                "role": "user",
                "content": f"{template['prompt']} Make it engaging for Pinterest, under 150 words, with specific actionable steps."
            }
        ],
        max_tokens=200,
        temperature=0.7
    )
    
    content = response.choices[0].message.content.strip()
    
    return {
        'content': content,
        'keywords': template['keywords'],
        'title_prefix': template['title_prefix'],
        'cta': template['cta'],
        'type': content_type
    }

def create_pinterest_description(content_data):
    """Create Pinterest-optimized description"""
    
    # Base hashtags that rotate
    base_hashtags = [
        "#CyberSecurity", "#FamilySafety", "#OnlineSafety", 
        "#TechTips", "#ParentingTips", "#DigitalParenting",
        "#CyberDad", "#FamilyTech", "#InternetSafety",
        "#KidsOnline", "#HomeSecurity", "#PrivacyTips"
    ]
    
    # Combine content-specific keywords with base hashtags
    all_hashtags = content_data['keywords'] + ' ' + ' '.join(random.sample(base_hashtags, 6))
    
    description = f"""{content_data['title_prefix']}

{content_data['content']}

✅ Quick to implement
✅ Protects your family
✅ Expert-approved

{all_hashtags}

{content_data['cta']}

🔗 Complete family security: https://payhip.com/CyberDadKit
📧 Join 1000+ cyber-smart parents: https://cyberdadkit.com"""

    return description

def post_to_pinterest(content_data, description):
    """Post to Pinterest with error handling"""
    
    pinterest_token = os.getenv('PINTEREST_ACCESS_TOKEN')
    board_id = os.getenv('PINTEREST_BOARD_ID')
    
    if not pinterest_token or not board_id:
        print("❌ Missing Pinterest credentials")
        return False
    
    # Pinterest API endpoint
    url = "https://api.pinterest.com/v5/pins"
    
    pin_data = {
        "board_id": board_id,
        "media_source": {
            "source_type": "image_url",
            "url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&h=1200&fit=crop"  # Cybersecurity image
        },
        "title": f"{content_data['title_prefix']}: {content_data['content'][:80]}...",
        "description": description,
        "link": "https://payhip.com/CyberDadKit"
    }
    
    headers = {
        "Authorization": f"Bearer {pinterest_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=pin_data, headers=headers)
        
        if response.status_code == 201:
            pin_info = response.json()
            print(f"✅ Pinterest pin created successfully!")
            print(f"🎯 Content type: {content_data['type']}")
            print(f"📌 Pin URL: https://pinterest.com/pin/{pin_info.get('id', '')}")
            return True
        else:
            print(f"❌ Pinterest API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting to Pinterest: {str(e)}")
        return False

def log_activity(content_data, success):
    """Log the automation activity"""
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "content_type": content_data.get('type', 'unknown'),
        "title": content_data.get('title_prefix', ''),
        "success": success,
        "content_preview": content_data.get('content', '')[:100] + "..."
    }
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Append to daily log file
    log_file = f"logs/pinterest_{datetime.now().strftime('%Y-%m-%d')}.json"
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"📊 Activity logged to {log_file}")
        
    except Exception as e:
        print(f"⚠️ Logging error: {str(e)}")

def main():
    """Main function for GitHub Actions"""
    
    print("🚀 Pinterest Traffic Blitz - GitHub Actions")
    print("=" * 50)
    
    try:
        # Generate targeted content
        print("📝 Generating targeted cybersecurity content...")
        content_data = generate_targeted_content()
        
        # Create Pinterest description
        print("📌 Creating Pinterest-optimized post...")
        description = create_pinterest_description(content_data)
        
        # Post to Pinterest
        print("🎯 Posting to Pinterest...")
        success = post_to_pinterest(content_data, description)
        
        # Log activity
        log_activity(content_data, success)
        
        if success:
            print("🎉 Pinterest traffic blitz completed successfully!")
            print(f"🔥 Posted {content_data['type']} content to maximize reach")
        else:
            print("⚠️ Pinterest posting failed - check credentials and board ID")
            
    except Exception as e:
        print(f"❌ Pinterest blitz error: {str(e)}")
        log_activity({'type': 'error', 'content': str(e)}, False)

if __name__ == "__main__":
    main()
