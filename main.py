import datetime

# Create a basic blog post with today's date
today = datetime.datetime.now().strftime("%Y-%m-%d")
filename = f"_posts/{today}-daily-cyber-tip.md"

content = f"""---
title: "Cyber Tip for {today}"
date: {today}
categories: [Cybersecurity, Family Safety]
---

🔐 **Daily Cyber Tip**

Always use **unique passwords** for each online account and enable **two-factor authentication (2FA)** wherever possible.

Stay safe online! 🛡️
"""

# Write the blog post
with open(filename, "w") as file:
    file.write(content)

print(f"✅ Blog post created: {filename}")
