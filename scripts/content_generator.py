#!/usr/bin/env python3
"""
Real CTI Blog Generator
Pulls actual cyber threat intelligence and converts to family-friendly advice
"""

import os
import requests
import json
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from openai import OpenAI

def get_cisa_alerts():
    """Get latest CISA cybersecurity alerts"""
    try:
        # CISA RSS feed for current alerts
        url = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            alerts = []
            
            # Parse RSS feed
            for item in root.findall('.//item')[:5]:  # Get latest 5 alerts
                title = item.find('title').text if item.find('title') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                
                alerts.append({
                    'title': title,
                    'description': description,
                    'link': link,
                    'date': pub_date
                })
            
            return alerts
    except Exception as e:
        print(f"Error fetching CISA alerts: {e}")
        return []

def get_sans_isc_threats():
    """Get current threats from SANS Internet Storm Center"""
    try:
        # SANS ISC diary RSS feed
        url = "https://isc.sans.edu/rssfeed.xml"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            threats = []
            
            for item in root.findall('.//item')[:3]:  # Get latest 3 diary entries
                title = item.find('title').text if item.find('title') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                
                threats.append({
                    'title': title,
                    'description': description,
                    'link': link
                })
            
            return threats
    except Exception as e:
        print(f"Error fetching SANS threats: {e}")
        return []

def get_nvd_vulnerabilities():
    """Get recent high-severity vulnerabilities from NVD"""
    try:
        # NVD API for recent high-severity CVEs
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last 7 days
        
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {
            'pubStartDate': start_date.strftime('%Y-%m-%dT%H:%M:%S.000'),
            'pubEndDate': end_date.strftime('%Y-%m-%dT%H:%M:%S.000'),
            'cvssV3Severity': 'HIGH,CRITICAL',
            'resultsPerPage': 5
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            vulns = []
            
            for vuln in data.get('vulnerabilities', []):
                cve_data = vuln.get('cve', {})
                cve_id = cve_data.get('id', '')
                description = cve_data.get('descriptions', [{}])[0].get('value', '')
                
                vulns.append({
                    'id': cve_id,
                    'description': description
                })
            
            return vulns
    except Exception as e:
        print(f"Error fetching NVD data: {e}")
        return []

def get_threat_intelligence():
    """Gather CTI from multiple sources"""
    print("🔍 Gathering real-time cyber threat intelligence...")
    
    cti_data = {
        'cisa_alerts': get_cisa_alerts(),
        'sans_threats': get_sans_isc_threats(),
        'nvd_vulns': get_nvd_vulnerabilities(),
        'collection_time': datetime.now().isoformat()
    }
    
    return cti_data

def convert_cti_to_family_advice(cti_data):
    """Use OpenAI to convert technical CTI into family-friendly advice"""
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Prepare CTI summary for AI processing
        cti_summary = "CURRENT CYBER THREAT INTELLIGENCE:\n\n"
        
        # Add CISA alerts
        if cti_data['cisa_alerts']:
            cti_summary += "CISA ALERTS:\n"
            for alert in cti_data['cisa_alerts']:
                cti_summary += f"- {alert['title']}: {alert['description'][:200]}...\n"
        
        # Add SANS threats
        if cti_data['sans_threats']:
            cti_summary += "\nSANS THREAT REPORTS:\n"
            for threat in cti_data['sans_threats']:
                cti_summary += f"- {threat['title']}: {threat['description'][:200]}...\n"
        
        # Add vulnerabilities
        if cti_data['nvd_vulns']:
            cti_summary += "\nHIGH-SEVERITY VULNERABILITIES:\n"
            for vuln in cti_data['nvd_vulns']:
                cti_summary += f"- {vuln['id']}: {vuln['description'][:200]}...\n"
        
        # Create prompt for family-friendly translation
        prompt = f"""You are a cybersecurity expert writing for parents who want to protect their families online.

CURRENT THREAT INTELLIGENCE:
{cti_summary}

Your task: Convert this technical cyber threat intelligence into a practical, easy-to-understand blog post for parents.

Requirements:
1. Write in simple language that non-technical parents can understand
2. Focus on actionable steps families can take TODAY
3. Include specific protection measures for each threat mentioned
4. Make it practical and reassuring, not scary
5. Include 5-7 numbered steps parents can follow
6. Length: 1200-1500 words
7. Include a compelling title that mentions current threats

Structure:
- Engaging introduction about current threats
- 5-7 numbered actionable steps
- Specific advice for protecting children
- Emergency response guidance
- Reassuring conclusion

Write this as a complete cybersecurity blog post for families."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error processing CTI with OpenAI: {e}")
        return None

def create_cti_blog_post():
    """Main function to create CTI-based blog post"""
    try:
        # Get real CTI data
        cti_data = get_threat_intelligence()
        
        # Check if we got any data
        total_threats = len(cti_data['cisa_alerts']) + len(cti_data['sans_threats']) + len(cti_data['nvd_vulns'])
        
        if total_threats == 0:
            print("❌ No CTI data available - using fallback content")
            return False
        
        print(f"✅ Collected {total_threats} current threats")
        
        # Convert CTI to family-friendly content
        blog_content = convert_cti_to_family_advice(cti_data)
        
        if not blog_content:
            print("❌ Failed to process CTI data")
            return False
        
        # Get current date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create blog post title from content
        title_line = blog_content.split('\n')[0].replace('#', '').strip()
        if not title_line:
            title_line = f"Current Cyber Threats and Family Protection - {today}"
        
        # Affiliate section
        affiliate_section = """

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

        # CTI sources section
        sources_section = """

---
## 📊 Threat Intelligence Sources

This analysis is based on current threat intelligence from:
- US CISA (Cybersecurity & Infrastructure Security Agency)
- SANS Internet Storm Center
- National Vulnerability Database (NVD)
- Real-time security monitoring

*Updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M UTC') + "*"

        # Build complete blog post
        complete_post = "---\n"
        complete_post += "layout: post\n"
        complete_post += "title: \"" + title_line + "\"\n"
        complete_post += "date: " + today + "\n"
        complete_post += "categories: cybersecurity\n"
        complete_post += "tags: [family-security, current-threats, cti, cybersecurity-tips]\n"
        complete_post += "author: CyberDad\n"
        complete_post += "excerpt: \"Current cyber threat analysis with practical protection steps for families\"\n"
        complete_post += "---\n\n"
        complete_post += blog_content + "\n"
        complete_post += affiliate_section + "\n"
        complete_post += email_section + "\n"
        complete_post += sources_section + "\n"
        
        # Create filename
        clean_title = title_line.lower().replace(' ', '-').replace(':', '').replace('(', '').replace(')', '').replace(',', '')
        filename = today + "-" + clean_title[:50] + ".md"
        
        # Create directory and save file
        os.makedirs('_posts', exist_ok=True)
        filepath = "_posts/" + filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(complete_post)
        
        print(f"✅ Real CTI blog post created: {filename}")
        print(f"📊 Based on {total_threats} current threats")
        return True
        
    except Exception as e:
        print(f"❌ Error creating CTI blog post: {e}")
        return False

if __name__ == "__main__":
    create_cti_blog_post()
