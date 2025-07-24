---
layout: home
title: Cyber Dad Central
---

🛡️ **Welcome to Cyber Dad Central — Your Daily Dose of Family Cybersecurity.**

This blog delivers 3 ultra-readable tips a day:

• 🚨 Real-world cyber threat alerts (CTI)
• 👨‍💻 Tech tips for non-tech families (TIP)  
• ⏰ Timeless family-safe digital habits (Evergreen)

Powered by AI. Designed for humans. Loved by families.

---

## 🛒 **Digital Security Store**
---

## 📅 **Latest Security Posts** (Newest First)

{% assign sorted_posts = site.posts | sort: 'date' | reverse %}
{% for post in sorted_posts limit: 10 %}
**{{ post.date | date: "%B %d, %Y at %l:%M %p" }}** • {{ post.categories | first | upcase }}

### [{{ post.title }}]({{ post.url }})

{{ post.excerpt | strip_html | truncatewords: 30 }}

[Read Full Post →]({{ post.url }})

---
{% endfor %}

**📊 Blog Stats:** {{ site.posts.size }} total posts • Last updated: {{ site.time | date: "%B %d, %Y" }}

**🔔 Updates:** 3 posts daily at 9am, 1pm, 8pm EST

---

💡 **Need help?** Email: help@cyberdad2025.com | **Emergency:** Call 911 for immediate threats
**[📋 Gumroad Store](https://cyberdad.gumroad.com)** - Security guides & templates  
**[💾 Payhip Store](https://payhip.com/CyberDadKit)** - Digital downloads  
**[🖨️ Etsy Printables](https://www.etsy.com/shop/CyberDadPrints)** - Print-at-home resources  

**🏆 Best Seller: Family Security Bundle - $39.99**  
*Complete protection guides for modern families*

---

## 📅 **Latest Security Posts** (Newest First)

<div class="post-list">
{% assign sorted_posts = site.posts | sort: 'date' | reverse %}
{% for post in sorted_posts limit: 20 %}
  <div class="post-item">
    <div class="post-date">
      <strong>{{ post.date | date: "%b %d, %Y" }}</strong>
      <span class="time-ago">{{ post.date | date: "%l:%M %p" }}</span>
    </div>
    <div class="post-content">
      <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
      <p class="post-excerpt">{{ post.excerpt | strip_html | truncatewords: 25 }}</p>
      <div class="post-meta">
        <span class="category">{{ post.categories | first | capitalize }}</span>
        <span class="read-time">• 3 min read</span>
      </div>
    </div>
  </div>
{% endfor %}
</div>

<style>
.post-list {
  max-width: 800px;
  margin: 2rem 0;
}

.post-item {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s ease;
}

.post-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.post-date {
  min-width: 120px;
  text-align: center;
  padding: 0.5rem;
  background: #f7fafc;
  border-radius: 6px;
  border-left: 4px solid #3182ce;
}

.post-date strong {
  display: block;
  color: #2d3748;
  font-size: 0.9rem;
}

.time-ago {
  display: block;
  color: #718096;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.post-content {
  flex: 1;
}

.post-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  line-height: 1.4;
}

.post-content h3 a {
  color: #2d3748;
  text-decoration: none;
}

.post-content h3 a:hover {
  color: #3182ce;
}

.post-excerpt {
  color: #4a5568;
  margin: 0.5rem 0;
  line-height: 1.5;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #718096;
}

.category {
  background: #bee3f8;
  color: #2c5282;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-weight: 500;
}

/* Mobile responsive */
@media (max-width: 640px) {
  .post-item {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .post-date {
    min-width: auto;
    text-align: left;
  }
}

/* NEW/TODAY indicators */
.post-item:first-child .post-date {
  border-left-color: #38a169;
  background: #f0fff4;
}

.post-item:first-child .post-date::after {
  content: "🆕 NEW";
  display: block;
  font-size: 0.7rem;
  color: #38a169;
  font-weight: bold;
  margin-top: 0.25rem;
}

/* If posted today */
.post-item[data-today="true"] .post-date {
  border-left-color: #e53e3e;
  background: #fff5f5;
}

.post-item[data-today="true"] .post-date::after {
  content: "🔥 TODAY";
  display: block;
  font-size: 0.7rem;
  color: #e53e3e;
  font-weight: bold;
  margin-top: 0.25rem;
}
</style>

---

### 📊 **Blog Stats**
- **Total Posts:** {{ site.posts.size }}
- **Last Updated:** {{ site.time | date: "%B %d, %Y at %l:%M %p" }}
- **Update Frequency:** 3 posts daily (9am, 1pm, 8pm EST)

---

💡 **Subscribe for instant security alerts:** [Email Updates] | **Emergency Help:** [Contact Support]
