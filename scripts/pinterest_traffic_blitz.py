#!/usr/bin/env python3
"""
Pinterest Traffic Blitz for GitHub Actions - FIXED VERSION
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
✅ Perfect for ages 4-99

{all_hashtags}

{content_data['cta']}

🔗 Complete family security: https://payhip.com/CyberDadKit
📧 Join 1000+ cyber-smart parents: https://cyberdadkit.com"""

    # Pinterest has a 500 character limit for descriptions
    if len(description) > 500:
        # Truncate and add ellipsis
        description = description[:497] + "..."
    
    return description

def validate_image_url(url):
    """Validate that Pinterest can access the image URL"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_cybersecurity_image():
    """Get a reliable cybersecurity image URL"""
    
    # Multiple backup image options
    image_options = [
        "https://images.unsplash.com/photo-1563986768609-322da13575f3",  # Clean URL
        "https://images.unsplash.com/photo-1550751827-4bd374c3f58b",   # Backup option
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5",  # Another backup
    ]
    
    # Test each image URL
    for image_url in image_options:
        print(f"🔍 Testing image URL: {image_url}")
        if validate_image_url(image_url):
            print(f"✅ Image URL validated: {image_url}")
            return image_url
        else:
            print(f"❌ Image URL failed: {image_url}")
    
    # If all fail, use a default
    print("⚠️ All image URLs failed, using fallback")
    return "https://images.unsplash.com/photo-1563986768609-322da13575f3"

def test_pinterest_connection(pinterest_token):
    """Test Pinterest API connection before posting"""
    
    print("🔗 Testing Pinterest API connection...")
    
    headers = {
        "Authorization": f"Bearer {pinterest_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test with user account endpoint
        response = requests.get("https://api.pinterest.com/v5/user_account", headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Pinterest API connected! User: {user_data.get('username', 'Unknown')}")
            return True
        else:
            print(f"❌ Pinterest API connection failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Pinterest connection test error: {str(e)}")
        return False

def post_to_pinterest(content_data, description):
    """Post to Pinterest with enhanced error handling and debugging"""
    
    pinterest_token = os.getenv('PINTEREST_ACCESS_TOKEN')
    board_id = os.getenv('PINTEREST_BOARD_ID')
    
    if not pinterest_token or not board_id:
        print("❌ Missing Pinterest credentials")
        print(f"Token present: {'Yes' if pinterest_token else 'No'}")
        print(f"Board ID present: {'Yes' if board_id else 'No'}")
        return False
    
    # Test API connection first
    if not test_pinterest_connection(pinterest_token):
        return False
    
    # Get and validate image URL
    image_url = get_cybersecurity_image()
    
    # Pinterest API endpoint
    url = "https://api.pinterest.com/v5/pins"
    
    # FIXED: Use correct Pinterest API v5 field names
    pin_data = {
        "board_id": board_id,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        },
        "note": description,  # FIXED: Changed from "description" to "note"
        "link": "https://payhip.com/CyberDadKit"
    }
    
    headers = {
        "Authorization": f"Bearer {pinterest_token}",
        "Content-Type": "application/json"
    }
    
    print("📤 Sending Pinterest API request...")
    print(f"🎯 Board ID: {board_id}")
    print(f"🖼️ Image URL: {image_url}")
    print(f"📝 Description length: {len(description)} characters")
    
    try:
        response = requests.post(url, json=pin_data, headers=headers, timeout=30)
        
        print(f"📡 Pinterest API Response Status: {response.status_code}")
        
        if response.status_code == 201:
            pin_info = response.json()
            pin_id = pin_info.get('id', '')
            print(f"✅ Pinterest pin created successfully!")
            print(f"🎯 Content type: {content_data['type']}")
            print(f"📌 Pin URL: https://pinterest.com/pin/{pin_id}")
            return True
        else:
            print(f"❌ Pinterest API error: {response.status_code}")
            print(f"📄 Response headers: {dict(response.headers)}")
            print(f"📝 Response body: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"🔍 Error details: {error_data}")
            except:
                print("🔍 Could not parse error response as JSON")
            
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Pinterest API request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Pinterest API request error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error posting to Pinterest: {str(e)}")
        return False

def log_activity(content_data, success):
    """Log the automation activity with enhanced details"""
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "content_type": content_data.get('type', 'unknown'),
        "title": content_data.get('title_prefix', ''),
        "success": success,
        "content_preview": content_data.get('content', '')[:100] + "...",
        "environment": {
            "has_openai_key": bool(os.getenv('OPENAI_API_KEY')),
            "has_pinterest_token": bool(os.getenv('PINTEREST_ACCESS_TOKEN')),
            "has_board_id": bool(os.getenv('PINTEREST_BOARD_ID')),
            "content_type_env": os.getenv('CONTENT_TYPE', 'not_set')
        }
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
    """Main function for GitHub Actions with enhanced debugging"""
    
    print("🚀 Pinterest Traffic Blitz - GitHub Actions (FIXED VERSION)")
    print("=" * 60)
    
    # Environment check
    print("🔧 Environment Check:")
    print(f"   OpenAI API Key: {'✅ Present' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"   Pinterest Token: {'✅ Present' if os.getenv('PINTEREST_ACCESS_TOKEN') else '❌ Missing'}")
    print(f"   Pinterest Board ID: {'✅ Present' if os.getenv('PINTEREST_BOARD_ID') else '❌ Missing'}")
    print(f"   Content Type: {os.getenv('CONTENT_TYPE', 'Not set (will default to morning)')}")
    print()
    
    try:
        # Generate targeted content
        print("📝 Generating targeted cybersecurity content...")
        content_data = generate_targeted_content()
        print(f"✅ Generated {content_data['type']} content")
        print(f"📄 Content preview: {content_data['content'][:100]}...")
        print()
        
        # Create Pinterest description
        print("📌 Creating Pinterest-optimized post...")
        description = create_pinterest_description(content_data)
        print(f"✅ Description created ({len(description)} characters)")
        print()
        
        # Post to Pinterest
        print("🎯 Posting to Pinterest...")
        success = post_to_pinterest(content_data, description)
        print()
        
        # Log activity
        log_activity(content_data, success)
        
        if success:
            print("🎉 Pinterest traffic blitz completed successfully!")
            print(f"🔥 Posted {content_data['type']} content to maximize reach")
        else:
            print("⚠️ Pinterest posting failed - check logs above for details")
            
    except Exception as e:
        print(f"❌ Pinterest blitz error: {str(e)}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        log_activity({'type': 'error', 'content': str(e)}, False)

if __name__ == "__main__":
    main()
