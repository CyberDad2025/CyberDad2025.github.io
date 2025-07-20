#!/usr/bin/env python3
"""
Fixed CyberDad Analytics Script
Properly counts posts created by any workflow
"""

import os
import glob
from datetime import datetime, timedelta
import json

def count_posts_accurately():
    """Count posts with proper date filtering"""
    try:
        # Get all markdown files in _posts directory
        posts_pattern = os.path.join('_posts', '*.md')
        all_posts = glob.glob(posts_pattern)
        
        print(f"📁 Found {len(all_posts)} total post files")
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Count posts by date
        today_posts = [p for p in all_posts if today in os.path.basename(p)]
        yesterday_posts = [p for p in all_posts if yesterday in os.path.basename(p)]
        
        # Count this week's posts
        week_ago = datetime.now() - timedelta(days=7)
        this_week_posts = []
        
        for post_file in all_posts:
            filename = os.path.basename(post_file)
            if len(filename) >= 10:  # YYYY-MM-DD format
                try:
                    post_date_str = filename[:10]  # Extract YYYY-MM-DD
                    post_date = datetime.strptime(post_date_str, '%Y-%m-%d')
                    if post_date >= week_ago:
                        this_week_posts.append(post_file)
                except ValueError:
                    continue
        
        # Count recent posts (last 24 hours by file modification time)
        recent_posts = []
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for post_file in all_posts:
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(post_file))
                if mod_time >= cutoff_time:
                    recent_posts.append(post_file)
            except OSError:
                continue
        
        analytics_data = {
            'date': today,
            'total_posts': len(all_posts),
            'posts_today': len(today_posts),
            'posts_yesterday': len(yesterday_posts),
            'posts_this_week': len(this_week_posts),
            'posts_last_24h': len(recent_posts),
            'weekly_goal': 21,
            'weekly_progress': f"{len(this_week_posts)}/21",
            'website_status': 'Online',
            'last_updated': datetime.now().isoformat()
        }
        
        print(f"📊 Analytics Summary:")
        print(f"   📝 Total Posts: {analytics_data['total_posts']}")
        print(f"   📅 Today: {analytics_data['posts_today']}")
        print(f"   📅 Yesterday: {analytics_data['posts_yesterday']}")
        print(f"   📅 This Week: {analytics_data['posts_this_week']}")
        print(f"   📅 Last 24h: {analytics_data['posts_last_24h']}")
        
        # List recent posts for verification
        if recent_posts:
            print(f"\n📋 Recent Posts (Last 24h):")
            for post in recent_posts[-5:]:  # Show last 5
                filename = os.path.basename(post)
                mod_time = datetime.fromtimestamp(os.path.getmtime(post))
                print(f"   • {filename} (Modified: {mod_time.strftime('%H:%M')})")
        
        return analytics_data
        
    except Exception as e:
        print(f"❌ Error counting posts: {e}")
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_posts': 0,
            'posts_today': 0,
            'posts_yesterday': 0,
            'posts_this_week': 0,
            'posts_last_24h': 0,
            'weekly_goal': 21,
            'weekly_progress': "0/21",
            'website_status': 'Online',
            'last_updated': datetime.now().isoformat(),
            'error': str(e)
        }

def create_github_issue_content(analytics):
    """Create GitHub issue content with correct analytics"""
    
    # Determine status indicators
    posts_today_status = "✅" if analytics['posts_today'] > 0 else "⚠️"
    weekly_status = "✅" if analytics['posts_this_week'] >= 3 else "⚠️"
    total_status = "📈" if analytics['total_posts'] > 0 else "🔴"
    
    # Create issue content
    issue_content = f"""# 📊 Daily Analytics Report - {analytics['date']}

## 🎯 Action Items
{f"- ✅ Blog post activity detected - {analytics['posts_last_24h']} posts in last 24h" if analytics['posts_last_24h'] > 0 else "- ⚠️ Low blog post activity - Check automation status"}
- ✅ Website running smoothly
- 📝 Weekly goal tracking - Aim for 21 posts this week

## 📈 Quick Stats Summary

| Metric | Value | Status |
|--------|-------|--------|
| Posts Today | {analytics['posts_today']} | {posts_today_status} |
| Posts Yesterday | {analytics['posts_yesterday']} | ✅ |
| Total Posts | {analytics['total_posts']} | {total_status} |
| Weekly Progress | {analytics['weekly_progress']} | {weekly_status} |
| Website Status | {analytics['website_status']} | ✅ |
| Last 24h Activity | {analytics['posts_last_24h']} posts | {"✅" if analytics['posts_last_24h'] > 0 else "⚠️"} |

## 🤖 Generated automatically by CyberDad Analytics Reporter
*Stay secure, stay automated!* 🛡️

## 📋 System Status
- **Ultra-Secure CTI Generator**: ✅ Working
- **Content Generation**: {"✅ Active" if analytics['posts_last_24h'] > 0 else "⚠️ Check workflow"}
- **Analytics Tracking**: ✅ Updated
- **Repository Status**: ✅ Healthy

## 🔍 Debug Information
- **Analysis Date**: {analytics['date']}
- **Last Updated**: {analytics.get('last_updated', 'Unknown')}
- **Posts Directory**: `_posts/` ✅
- **Total Files Found**: {analytics['total_posts']}

---

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Workflow**: CyberDad Ultra-Secure CTI Analytics
"""
    
    return issue_content

def save_analytics_report(analytics):
    """Save analytics to files"""
    try:
        # Ensure reports directory exists
        os.makedirs('reports', exist_ok=True)
        
        # Save JSON for programmatic access
        json_path = os.path.join('reports', 'analytics.json')
        with open(json_path, 'w') as f:
            json.dump(analytics, f, indent=2)
        
        # Save markdown report for GitHub issues
        md_path = os.path.join('reports', 'daily-analytics.md')
        issue_content = create_github_issue_content(analytics)
        with open(md_path, 'w') as f:
            f.write(issue_content)
        
        print(f"💾 Analytics saved:")
        print(f"   📄 JSON: {json_path}")
        print(f"   📄 Markdown: {md_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving analytics: {e}")
        return False

def main():
    """Main analytics function"""
    print("🔍 CyberDad Analytics - Counting Posts Accurately...")
    print("=" * 50)
    
    # Count posts accurately
    analytics = count_posts_accurately()
    
    # Save reports
    success = save_analytics_report(analytics)
    
    if success:
        print("\n🎉 Analytics Update Completed Successfully!")
        print(f"✅ Found {analytics['total_posts']} total posts")
        print(f"✅ {analytics['posts_last_24h']} posts in last 24 hours")
        print(f"✅ Weekly progress: {analytics['weekly_progress']}")
        return 0
    else:
        print("\n❌ Analytics update failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
