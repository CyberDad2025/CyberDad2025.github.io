---
layout: home
title: Cyber Dad Central
---

<style>
/* HIGH-REVENUE BLOG COLOR SCHEME */
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.main-container {
    background: white;
    margin: 0 auto;
    max-width: 1200px;
    box-shadow: 0 0 30px rgba(0,0,0,0.1);
    border-radius: 12px;
    overflow: hidden;
}

/* HERO SECTION */
.hero-section {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
    color: white;
    padding: 3rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="50" cy="10" r="0.5" fill="rgba(255,255,255,0.05)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    opacity: 0.3;
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.hero-subtitle {
    font-size: 1.2rem;
    opacity: 0.95;
    margin-bottom: 2rem;
    font-weight: 300;
}

.hero-stats {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
}

.stat-item {
    background: rgba(255,255,255,0.2);
    padding: 1rem 1.5rem;
    border-radius: 10px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.3);
}

.stat-number {
    display: block;
    font-size: 1.8rem;
    font-weight: 700;
}

/* CONTENT SECTION */
.content-section {
    padding: 2rem;
}

/* DIGITAL STORE SECTION */
.store-section {
    background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
    color: white;
    padding: 3rem 2rem;
    margin: 2rem 0;
    border-radius: 15px;
    box-shadow: 0 10px 25px rgba(78, 205, 196, 0.3);
}

.store-title {
    font-size: 2rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 1rem;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.store-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.store-item {
    background: rgba(255,255,255,0.15);
    padding: 1.5rem;
    border-radius: 12px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    text-align: center;
}

.store-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.2);
}

.store-item a {
    color: white;
    text-decoration: none;
    font-weight: 600;
    display: inline-block;
    background: rgba(255,255,255,0.2);
    padding: 0.75rem 1.5rem;
    border-radius: 25px;
    margin-top: 1rem;
    transition: all 0.3s ease;
}

.store-item a:hover {
    background: rgba(255,255,255,0.3);
    transform: scale(1.05);
}

.bestseller-badge {
    background: linear-gradient(45deg, #ff9a9e 0%, #fecfef 100%);
    color: #333;
    padding: 2rem;
    border-radius: 15px;
    margin: 2rem 0;
    text-align: center;
    box-shadow: 0 8px 20px rgba(255, 154, 158, 0.4);
}

/* BLOG POSTS SECTION */
.posts-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 3rem 2rem;
    margin: 2rem 0;
    border-radius: 15px;
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.posts-title {
    font-size: 2rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 2rem;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

.post-item {
    background: rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
    transition: all 0.3s ease;
}

.post-item:hover {
    background: rgba(255,255,255,0.15);
    transform: translateX(10px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.2);
}

.post-date {
    background: linear-gradient(45deg, #ff6b6b, #ee5a52);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 1rem;
    box-shadow: 0 4px 10px rgba(255, 107, 107, 0.3);
}

.post-category {
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    color: white;
    padding: 0.3rem 0.8rem;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: 500;
    margin-left: 0.5rem;
}

.post-title {
    font-size: 1.3rem;
    font-weight: 600;
    margin: 1rem 0 0.5rem 0;
}

.post-title a {
    color: white;
    text-decoration: none;
}

.post-title a:hover {
    color: #ffd93d;
    text-shadow: 0 0 10px rgba(255, 217, 61, 0.5);
}

.post-excerpt {
    opacity: 0.9;
    line-height: 1.6;
    margin: 1rem 0;
}

.read-more {
    color: #ffd93d;
    text-decoration: none;
    font-weight: 600;
    padding: 0.5rem 1rem;
    border: 2px solid #ffd93d;
    border-radius: 20px;
    display: inline-block;
    transition: all 0.3s ease;
}

.read-more:hover {
    background: #ffd93d;
    color: #333;
    transform: scale(1.05);
}

/* STATS SECTION */
.stats-section {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    color: #333;
    padding: 2rem;
    border-radius: 15px;
    margin: 2rem 0;
    text-align: center;
    box-shadow: 0 8px 20px rgba(252, 182, 159, 0.3);
}

.stats-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #d63031;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.stat-box {
    background: rgba(255,255,255,0.7);
    padding: 1rem;
    border-radius: 10px;
    backdrop-filter: blur(5px);
}

/* CONTACT SECTION */
.contact-section {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    color: #333;
    padding: 2rem;
    border-radius: 15px;
    margin: 2rem 0;
    text-align: center;
    box-shadow: 0 8px 20px rgba(168, 237, 234, 0.3);
}

.contact-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #00b894;
}

.emergency-btn {
    background: linear-gradient(45deg, #ff6b6b, #ee5a52);
    color: white;
    padding: 1rem 2rem;
    border: none;
    border-radius: 25px;
    font-weight: 600;
    text-decoration: none;
    display: inline-block;
    margin: 0.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
}

.emergency-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.6);
}

.help-btn {
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    color: white;
    padding: 1rem 2rem;
    border: none;
    border-radius: 25px;
    font-weight: 600;
    text-decoration: none;
    display: inline-block;
    margin: 0.5rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(78, 205, 196, 0.4);
}

.help-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(78, 205, 196, 0.6);
}

/* MOBILE RESPONSIVE */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2rem;
    }
    
    .hero-stats {
        flex-direction: column;
        gap: 1rem;
    }
    
    .store-grid {
        grid-template-columns: 1fr;
    }
    
    .content-section {
        padding: 1rem;
    }
}

/* FLOATING ELEMENTS */
.floating-icon {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: linear-gradient(45deg, #ff6b6b, #ee5a52);
    color: white;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.4);
    cursor: pointer;
    transition: all 0.3s ease;
    z-index: 1000;
}

.floating-icon:hover {
    transform: scale(1.1);
    box-shadow: 0 8px 25px rgba(255, 107, 107, 0.6);
}

/* ANIMATIONS */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.post-item, .store-item, .stat-box {
    animation: fadeInUp 0.6s ease forwards;
}

.post-item:nth-child(1) { animation-delay: 0.1s; }
.post-item:nth-child(2) { animation-delay: 0.2s; }
.post-item:nth-child(3) { animation-delay: 0.3s; }
</style>

<div class="main-container">

<div class="hero-section">
    <div class="hero-content">
        <h1 class="hero-title">🛡️ Cyber Dad Central</h1>
        <p class="hero-subtitle">Your Daily Dose of Family Cybersecurity</p>
        <div class="hero-stats">
            <div class="stat-item">
                <span class="stat-number">12K+</span>
                <span class="stat-label">Families Protected</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">500+</span>
                <span class="stat-label">Security Guides</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">24/7</span>
                <span class="stat-label">Threat Monitoring</span>
            </div>
        </div>
    </div>
</div>

<div class="content-section">

<div class="store-section">
    <h2 class="store-title">🛒 Digital Security Store</h2>
    <div class="store-grid">
        <div class="store-item">
            <h3>📋 Gumroad Store</h3>
            <p>Security guides & templates</p>
            <a href="https://cyberdad.gumroad.com" target="_blank">Shop Now →</a>
        </div>
        <div class="store-item">
            <h3>💾 Payhip Store</h3>
            <p>Digital downloads</p>
            <a href="https://payhip.com/CyberDadKit" target="_blank">Browse Store →</a>
        </div>
        <div class="store-item">
            <h3>🖨️ Etsy Printables</h3>
            <p>Print-at-home resources</p>
            <a href="https://www.etsy.com/shop/CyberDadPrints" target="_blank">Visit Etsy →</a>
        </div>
    </div>
    
    <div class="bestseller-badge">
        <h3>🏆 Best Seller: Family Security Bundle - $39.99</h3>
        <p><em>Complete protection guides for modern families</em></p>
        <a href="https://cyberdad.gumroad.com" style="background: #ff6b6b; color: white; padding: 0.75rem 2rem; border-radius: 25px; text-decoration: none; font-weight: 600; display: inline-block; margin-top: 1rem;">Get Bundle Now →</a>
    </div>
</div>

<div class="posts-section">
    <h2 class="posts-title">📅 Latest Security Posts (Newest First)</h2>
    
    {% assign sorted_posts = site.posts | sort: 'date' | reverse %}
    {% for post in sorted_posts limit: 10 %}
    <div class="post-item">
        <div class="post-date">{{ post.date | date: "%B %d, %Y at %l:%M %p" }}</div>
        <span class="post-category">{{ post.categories | first | upcase }}</span>
        
        <h3 class="post-title"><a href="{{ post.url }}">{{ post.title }}</a></h3>
        
        <p class="post-excerpt">{{ post.excerpt | strip_html | truncatewords: 30 }}</p>
        
        <a href="{{ post.url }}" class="read-more">Read Full Post →</a>
    </div>
    {% endfor %}
</div>

<div class="stats-section">
    <h3 class="stats-title">📊 Blog Performance</h3>
    <div class="stats-grid">
        <div class="stat-box">
            <strong>{{ site.posts.size }}</strong><br>Total Posts
        </div>
        <div class="stat-box">
            <strong>{{ site.time | date: "%B %d, %Y" }}</strong><br>Last Updated
        </div>
        <div class="stat-box">
            <strong>3 Daily</strong><br>Posts at 9am, 1pm, 8pm EST
        </div>
        <div class="stat-box">
            <strong>AI-Powered</strong><br>Real-time Intelligence
        </div>
    </div>
</div>

<div class="contact-section">
    <h3 class="contact-title">💡 Need Help?</h3>
    <a href="mailto:help@cyberdad2025.com" class="help-btn">📧 Email Support</a>
    <a href="tel:911" class="emergency-btn">🆘 Emergency: Call 911</a>
    <p style="margin-top: 1rem; opacity: 0.8;">For immediate cybersecurity threats</p>
</div>

</div>
</div>

<!-- Floating Help Button -->
<div class="floating-icon" onclick="window.location.href='mailto:help@cyberdad2025.com'">
    💬
</div>
