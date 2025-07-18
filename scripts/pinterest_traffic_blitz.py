#!/usr/bin/env python3
"""
Pinterest Log Analyzer
Analyzes your Pinterest automation logs to show exactly what was posted and what failed
"""

import json
import os
from datetime import datetime, timedelta
import glob

class PinterestLogAnalyzer:
    def __init__(self, logs_directory="logs"):
        self.logs_dir = logs_directory
        
    def get_all_log_files(self):
        """Get all Pinterest log files"""
        pattern = os.path.join(self.logs_dir, "pinterest_*.json")
        return sorted(glob.glob(pattern))
    
    def load_log_file(self, filepath):
        """Load and parse a log file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return []
    
    def analyze_all_logs(self):
        """Analyze all Pinterest logs"""
        
        print("📊 PINTEREST AUTOMATION LOG ANALYSIS")
        print("=" * 60)
        
        log_files = self.get_all_log_files()
        
        if not log_files:
            print("❌ No Pinterest log files found!")
            print(f"Looking in: {os.path.abspath(self.logs_dir)}")
            return
        
        all_entries = []
        total_attempts = 0
        successful_posts = 0
        failed_posts = 0
        
        # Load all log entries
        for log_file in log_files:
            entries = self.load_log_file(log_file)
            all_entries.extend(entries)
            print(f"📁 Loaded {len(entries)} entries from {os.path.basename(log_file)}")
        
        if not all_entries:
            print("❌ No log entries found!")
            return
        
        # Sort by timestamp
        all_entries.sort(key=lambda x: x.get('timestamp', ''))
        
        print(f"\n📈 SUMMARY STATISTICS")
        print(f"   Total automation runs: {len(all_entries)}")
        
        successful_posts = len([e for e in all_entries if e.get('success', False)])
        failed_posts = len([e for e in all_entries if not e.get('success', False)])
        
        print(f"   ✅ Successful posts: {successful_posts}")
        print(f"   ❌ Failed attempts: {failed_posts}")
        print(f"   📊 Success rate: {(successful_posts/len(all_entries)*100):.1f}%")
        
        # Content type breakdown
        content_types = {}
        for entry in all_entries:
            content_type = entry.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        print(f"\n🕐 CONTENT TYPE BREAKDOWN")
        for content_type, count in sorted(content_types.items()):
            print(f"   {content_type}: {count} posts")
        
        return all_entries
    
    def show_failed_posts(self, all_entries):
        """Show detailed info about failed posts"""
        
        failed_entries = [e for e in all_entries if not e.get('success', False)]
        
        if not failed_entries:
            print("\n🎉 NO FAILED POSTS FOUND!")
            return
        
        print(f"\n❌ FAILED POSTS ANALYSIS ({len(failed_entries)} failures)")
        print("=" * 60)
        
        for i, entry in enumerate(failed_entries[-10:], 1):  # Show last 10 failures
            print(f"\n💥 FAILURE #{i}")
            print(f"   📅 Time: {entry.get('timestamp', 'Unknown')}")
            print(f"   🏷️ Type: {entry.get('content_type', 'Unknown')}")
            print(f"   📝 Title: {entry.get('title', 'No title')}")
            
            # Show what content was supposed to be posted
            generated_content = entry.get('generated_content', {})
            if generated_content.get('full_content'):
                print(f"   📄 Content: {generated_content['full_content'][:200]}...")
            
            # Show Pinterest post details
            pinterest_post = entry.get('pinterest_post', {})
            if pinterest_post.get('full_description'):
                print(f"   📌 Pinterest Description ({pinterest_post.get('description_length', 0)} chars):")
                print(f"      {pinterest_post['full_description'][:300]}...")
            
            # Show error details
            error_info = entry.get('error_info')
            if error_info:
                print(f"   🚨 Error: {error_info}")
            
            print("   " + "-" * 50)
    
    def show_successful_posts(self, all_entries):
        """Show successful posts"""
        
        successful_entries = [e for e in all_entries if e.get('success', False)]
        
        if not successful_entries:
            print("\n😢 NO SUCCESSFUL POSTS FOUND!")
            return
        
        print(f"\n✅ SUCCESSFUL POSTS ({len(successful_entries)} posts)")
        print("=" * 60)
        
        for i, entry in enumerate(successful_entries[-5:], 1):  # Show last 5 successes
            print(f"\n🎉 SUCCESS #{i}")
            print(f"   📅 Time: {entry.get('timestamp', 'Unknown')}")
            print(f"   🏷️ Type: {entry.get('content_type', 'Unknown')}")
            print(f"   📝 Title: {entry.get('title', 'No title')}")
            
            # Show what was actually posted
            generated_content = entry.get('generated_content', {})
            if generated_content.get('full_content'):
                print(f"   📄 Content: {generated_content['full_content'][:200]}...")
            
            # Show Pinterest URL if available
            pinterest_post = entry.get('pinterest_post', {})
            if pinterest_post.get('pin_url'):
                print(f"   🔗 Pinterest URL: {pinterest_post['pin_url']}")
            
            if pinterest_post.get('full_description'):
                print(f"   📌 Posted Description ({pinterest_post.get('description_length', 0)} chars):")
                print(f"      {pinterest_post['full_description'][:200]}...")
            
            print("   " + "-" * 50)
    
    def show_recent_activity(self, all_entries, days=7):
        """Show activity from last N days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_entries = []
        for entry in all_entries:
            try:
                entry_date = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))
                if entry_date.replace(tzinfo=None) >= cutoff_date:
                    recent_entries.append(entry)
            except:
                pass  # Skip entries with bad timestamps
        
        if not recent_entries:
            print(f"\n📅 NO ACTIVITY IN LAST {days} DAYS")
            return
        
        print(f"\n📅 RECENT ACTIVITY (Last {days} days - {len(recent_entries)} runs)")
        print("=" * 60)
        
        for entry in recent_entries[-10:]:  # Show last 10
            timestamp = entry.get('timestamp', 'Unknown')[:19]  # Remove microseconds
            content_type = entry.get('content_type', 'unknown')
            success = "✅" if entry.get('success', False) else "❌"
            title = entry.get('title', 'No title')
            
            print(f"   {success} {timestamp} | {content_type:8} | {title}")
            
            # Show Pinterest URL for successful posts
            if entry.get('success') and entry.get('pinterest_post', {}).get('pin_url'):
                print(f"      🔗 {entry['pinterest_post']['pin_url']}")
    
    def export_failed_content(self, all_entries):
        """Export failed content to retry manually"""
        
        failed_entries = [e for e in all_entries if not e.get('success', False)]
        
        if not failed_entries:
            print("\n🎉 No failed content to export!")
            return
        
        export_data = []
        
        for entry in failed_entries:
            generated_content = entry.get('generated_content', {})
            pinterest_post = entry.get('pinterest_post', {})
            
            export_item = {
                "timestamp": entry.get('timestamp'),
                "content_type": entry.get('content_type'),
                "title": entry.get('title'),
                "full_content": generated_content.get('full_content', ''),
                "keywords": generated_content.get('keywords', ''),
                "cta": generated_content.get('cta', ''),
                "pinterest_description": pinterest_post.get('full_description', ''),
                "error": entry.get('error_info', {})
            }
            export_data.append(export_item)
        
        # Save to file
        export_filename = f"failed_pinterest_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(export_filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"\n💾 EXPORTED FAILED CONTENT")
            print(f"   📁 File: {export_filename}")
            print(f"   📊 Items: {len(export_data)} failed posts")
            print(f"   💡 You can now manually post this content to Pinterest!")
            
        except Exception as e:
            print(f"❌ Error exporting: {e}")

def main():
    """Main analysis function"""
    
    analyzer = PinterestLogAnalyzer()
    
    # Load and analyze all logs
    all_entries = analyzer.analyze_all_logs()
    
    if not all_entries:
        return
    
    # Show different analysis views
    analyzer.show_recent_activity(all_entries)
    analyzer.show_successful_posts(all_entries)
    analyzer.show_failed_posts(all_entries)
    
    # Export failed content for manual posting
    analyzer.export_failed_content(all_entries)
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Check failed posts above for error patterns")
    print(f"   2. Use exported failed content file for manual posting")
    print(f"   3. Fix any credential/configuration issues identified")
    print(f"   4. Re-run the Pinterest automation script")

if __name__ == "__main__":
    main()
