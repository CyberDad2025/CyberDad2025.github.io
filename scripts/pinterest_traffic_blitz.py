#!/usr/bin/env python3
"""
Pinterest Traffic Blitz for GitHub Actions - ENHANCED VERSION
Runs 5x daily automatically with detailed error logging and debugging
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
        print(f"🔍 Testing image URL accessibility: {url}")
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ Image URL accessible: {response.status_code}")
            return True
        else:
            print(f"❌ Image URL not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing image URL: {str(e)}")
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
        if validate_image_url(image_url):
            print(f"✅ Selected working image: {image_url}")
            return image_url
        else:
            print(f"❌ Image failed, trying next option...")
    
    # If all fail, use a default
    print("⚠️ All image URLs failed, using fallback")
    return "https://images.unsplash.com/photo-1563986768609-322da13575f3"

def test_pinterest_connection(pinterest_token):
    """Test Pinterest API connection before posting"""
    
    if not pinterest_token:
        print("❌ No Pinterest access token provided")
        return False
    
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
            username = user_data.get('username', 'Unknown')
            print(f"✅ Pinterest API connected! User: {username}")
            return True
        else:
            print(f"❌ Pinterest API connection failed: {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Pinterest connection test error: {str(e)}")
        return False

def post_to_pinterest(content_data, description):
    """Post to Pinterest with enhanced error handling and debugging"""
    
    print("🎯 STARTING PINTEREST POSTING PROCESS...")
    print("=" * 50)
    
    # Check environment variables
    pinterest_token = os.getenv('PINTEREST_ACCESS_TOKEN')
    board_id = os.getenv('PINTEREST_BOARD_ID')
    
    print("🔧 Environment Check:")
    print(f"   Pinterest Token: {'✅ Present' if pinterest_token else '❌ Missing'}")
    print(f"   Board ID: {'✅ Present' if board_id else '❌ Missing'}")
    
    if not pinterest_token:
        error_msg = "Missing PINTEREST_ACCESS_TOKEN environment variable"
        print(f"❌ {error_msg}")
        return False, None, {"error": error_msg}
        
    if not board_id:
        error_msg = "Missing PINTEREST_BOARD_ID environment variable"
        print(f"❌ {error_msg}")
        return False, None, {"error": error_msg}
    
    # Test API connection first
    if not test_pinterest_connection(pinterest_token):
        error_msg = "Pinterest API connection failed"
        return False, None, {"error": error_msg}
    
    # Get and validate image URL
    print("\n🖼️ Image Processing:")
    image_url = get_cybersecurity_image()
    
    # Pinterest API endpoint
    url = "https://api.pinterest.com/v5/pins"
    
    # CORRECT Pinterest API v5 field names
    pin_data = {
        "board_id": board_id,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        },
        "note": description,  # CORRECT: Use "note" not "description"
        "link": "https://payhip.com/CyberDadKit"
    }
    
    headers = {
        "Authorization": f"Bearer {pinterest_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📤 Pinterest API Request:")
    print(f"   🎯 Board ID: {board_id}")
    print(f"   🖼️ Image URL: {image_url}")
    print(f"   📝 Description length: {len(description)} characters")
    print(f"   🔗 Destination URL: https://payhip.com/CyberDadKit")
    
    try:
        print("\n📡 Sending request to Pinterest API...")
        response = requests.post(url, json=pin_data, headers=headers, timeout=30)
        
        print(f"📊 Pinterest API Response: {response.status_code}")
        
        if response.status_code == 201:
            pin_info = response.json()
            pin_id = pin_info.get('id', '')
            pin_url = f"https://pinterest.com/pin/{pin_id}"
            
            print(f"🎉 SUCCESS! Pinterest pin created!")
            print(f"   📌 Pin URL: {pin_url}")
            print(f"   🎯 Content type: {content_data['type']}")
            print(f"   📊 Pin ID: {pin_id}")
            
            return True, pin_url, None
            
        else:
            print(f"❌ Pinterest API Error: {response.status_code}")
            print(f"📝 Response body: {response.text}")
            
            # Detailed error analysis
            error_details = {
                "status_code": response.status_code,
                "response_body": response.text,
                "headers": dict(response.headers)
            }
            
            # Common error interpretations
            if response.status_code == 400:
                print("🔍 Likely causes: Invalid request format, wrong field names, or bad data")
            elif response.status_code == 401:
                print("🔍 Likely cause: Invalid or expired access token")
            elif response.status_code == 403:
                print("🔍 Likely cause: Insufficient permissions or rate limiting")
            elif response.status_code == 404:
                print("🔍 Likely cause: Invalid board ID")
            
            try:
                error_data = response.json()
                error_details["parsed_error"] = error_data
                print(f"🔍 Parsed error: {error_data}")
            except:
                print("🔍 Could not parse error response as JSON")
            
            return False, None, error_details
            
    except requests.exceptions.Timeout:
        error_msg = "Pinterest API request timed out"
        print(f"❌ {error_msg}")
        return False, None, {"error": error_msg}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, {"error": error_msg}
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return False, None, {"error": error_msg
