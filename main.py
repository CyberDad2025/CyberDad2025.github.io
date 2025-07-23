import datetime

# Create today's date
today = datetime.datetime.now().strftime("%Y-%m-%d")
hour = datetime.datetime.now().hour

# Match category by hour
if hour == 9:
    category = "Family Tips"
    body = "👨‍👩‍👧‍👦 **Family Tip**\n\nTeach your kids to always ask before clicking on links or downloading apps. Keep it fun and simple!"
elif hour == 13:
    category = "Cyber Threat Alert"
    body = "🚨 **Cyber Threat Alert**\n\nBeware of fake emails claiming to be from delivery services. Always check the sender’s address!"
elif hour == 20:
    category = "Security Tools"
    body = "🛡️ **Security Tool Tip**\n\nUse a password manager like Bitwarden or 1Password. It helps generate and store strong passwords."
else:
    category = "General"
    body = "💡 **Cyber Tip**\n\nStay aware and review your privacy settings on all your apps this week."

# Create filename and post content
filename = f"_posts/{today}-hour{hour:02d}-cyber-post.md"
content = f"""---
title: "{category} – {today}"
date: {today}
categories: [Cybersecurity, {category}]
---

{body}
"""

# Write the blog post
with open(filename, "w") as file:
    file.write(content)

print(f"✅ Blog post created for {hour}:00 – {filename}")
