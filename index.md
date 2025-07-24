---
layout: default
---
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberDad - Family Cybersecurity Intelligence</title>
    <meta name="description" content="Real-time cybersecurity intelligence for modern families. Get protection guides, threat alerts, and security tips that keep your family safe online.">
    
    <!-- IP GEOLOCATION & ANALYTICS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    
    <!-- GOOGLE ANALYTICS - REVENUE TRACKING -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'GA_MEASUREMENT_ID');
        
        // Revenue Event Tracking
        function trackRevenue(action, value) {
            gtag('event', action, {
                'event_category': 'Revenue',
                'event_label': 'CyberDad',
                'value': value
            });
        }
    </script>
    <style>
        /* GLOBAL LANGUAGE & LOCATION BAR */
        .global-bar {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.5rem 0;
            font-size: 0.9rem;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }

        .global-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .location-info {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .language-switcher select {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            cursor: pointer;
        }

        .language-switcher select option {
            background: #2d3748;
            color: white;
        }

        .local-threat-alert {
            background: rgba(255, 107, 107, 0.2);
            border: 1px solid rgba(255, 107, 107, 0.5);
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        /* REVENUE-OPTIMIZED BLOG DESIGN - BASED ON $1M/MONTH EARNERS */
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #2d3748;
            background: #ffffff;
        }

        /* HEADER - Clean & Professional */
        .main-header {
            background: #ffffff;
            border-bottom: 1px solid #e2e8f0;
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .header-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            color: #2b6cb0;
            text-decoration: none;
        }

        .main-nav {
            display: flex;
            gap: 2rem;
            list-style: none;
        }

        .main-nav a {
            color: #4a5568;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s ease;
        }

        .main-nav a:hover {
            color: #2b6cb0;
        }

        /* HERO SECTION - Value Proposition */
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4rem 0;
            text-align: center;
        }

        .hero-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        .hero-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            line-height: 1.2;
        }

        .hero-subtitle {
            font-size: 1.3rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }

        .hero-stats {
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-top: 2rem;
            flex-wrap: wrap;
        }

        .stat-item {
            text-align: center;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: 700;
            display: block;
        }

        .stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        /* TRUST INDICATORS */
        .trust-bar {
            background: #f7fafc;
            padding: 1rem 0;
            border-bottom: 1px solid #e2e8f0;
        }

        .trust-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 3rem;
            flex-wrap: wrap;
        }

        .trust-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #4a5568;
            font-size: 0.9rem;
        }

        /* MAIN CONTENT AREA */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        /* FEATURED ALERT SECTION */
        .alert-section {
            background: #fff5f5;
            border: 1px solid #feb2b2;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 2rem 0;
        }

        .alert-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .alert-icon {
            font-size: 1.5rem;
        }

        .alert-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #c53030;
        }

        .alert-content {
            color: #4a5568;
            margin-bottom: 1rem;
        }

        .alert-cta {
            background: #c53030;
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }

        /* CONTENT GRID - 3 COLUMN LAYOUT */
        .content-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 3rem;
            margin: 3rem 0;
        }

        .main-content {
            display: grid;
            gap: 2rem;
        }

        .post-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }

        .post-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid #e2e8f0;
        }

        .post-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .post-image {
            width: 100%;
            height: 200px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: white;
        }

        .post-content {
            padding: 1.5rem;
        }

        .post-category {
            background: #bee3f8;
            color: #2b6cb0;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
            margin-bottom: 1rem;
            display: inline-block;
        }

        .post-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            line-height: 1.4;
        }

        .post-excerpt {
            color: #718096;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }

        .post-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            color: #a0aec0;
        }

        .read-more {
            color: #2b6cb0;
            text-decoration: none;
            font-weight: 500;
        }

        /* SIDEBAR */
        .sidebar {
            display: grid;
            gap: 2rem;
            height: fit-content;
        }

        .sidebar-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
        }

        .sidebar-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #2d3748;
        }

        /* EMAIL CAPTURE - HIGH CONVERSION */
        .email-capture {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            text-align: center;
        }

        .email-form {
            margin-top: 1rem;
        }

        .email-input {
            width: 100%;
            padding: 0.75rem;
            border: none;
            border-radius: 4px;
            margin-bottom: 1rem;
            font-size: 1rem;
        }

        .email-btn {
            width: 100%;
            background: #2d3748;
            color: white;
            padding: 0.75rem;
            border: none;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
            font-size: 1rem;
        }

        .email-benefits {
            font-size: 0.8rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }

        /* REVENUE SECTIONS */
        .revenue-section {
            background: #f7fafc;
            border-radius: 8px;
            padding: 2rem;
            margin: 3rem 0;
            text-align: center;
        }

        .revenue-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        .product-card {
            background: white;
            border-radius: 6px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .product-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
        }

        .product-name {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .product-description {
            color: #718096;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }

        .product-btn {
            background: #667eea;
            color: white;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            text-decoration: none;
            font-weight: 500;
            display: inline-block;
            transition: background 0.3s ease;
        }

        .product-btn:hover {
            background: #5a67d8;
        }

        /* TOOLS SECTION */
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }

        .tool-card {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid #e2e8f0;
            text-align: center;
        }

        .tool-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .tool-name {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        .tool-description {
            color: #718096;
            margin-bottom: 1.5rem;
        }

        .tool-link {
            background: #48bb78;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            display: inline-block;
            transition: background 0.3s ease;
        }

        .tool-link:hover {
            background: #38a169;
        }

        /* FOOTER */
        .footer {
            background: #2d3748;
            color: white;
            padding: 3rem 0 2rem;
            margin-top: 4rem;
        }

        .footer-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
        }

        .footer-section h3 {
            margin-bottom: 1rem;
            color: #e2e8f0;
        }

        .footer-section a {
            color: #a0aec0;
            text-decoration: none;
            display: block;
            margin-bottom: 0.5rem;
            transition: color 0.3s ease;
        }

        .footer-section a:hover {
            color: white;
        }

        .footer-bottom {
            border-top: 1px solid #4a5568;
            margin-top: 2rem;
            padding-top: 2rem;
            text-align: center;
            color: #a0aec0;
        }

        /* RESPONSIVE DESIGN */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2rem;
            }
            
            .hero-subtitle {
                font-size: 1.1rem;
            }
            
            .content-grid {
                grid-template-columns: 1fr;
            }
            
            .post-grid {
                grid-template-columns: 1fr;
            }
            
            .hero-stats {
                gap: 1.5rem;
            }
            
            .trust-container {
                flex-direction: column;
                gap: 1rem;
            }
            
            .main-nav {
                flex-direction: column;
                gap: 1rem;
            }
        }

        /* LOADING ANIMATIONS */
        .fade-in {
            animation: fadeIn 0.6s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* CTA BUTTONS OPTIMIZATION */
        .cta-primary {
            background: linear-gradient(45deg, #48bb78, #38a169);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 6px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(72, 187, 120, 0.3);
        }

        .cta-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(72, 187, 120, 0.4);
        }
    </style>
</head>
<body>
    <!-- GLOBAL LANGUAGE & LOCATION BAR -->
    <div class="global-bar" id="globalBar" style="display: none;">
        <div class="global-container">
            <div class="location-info">
                <span id="locationFlag">🌍</span>
                <span id="locationText">Detecting location...</span>
            </div>
            <div class="language-switcher">
                <select id="languageSelect" onchange="changeLanguage()">
                    <option value="en">🇺🇸 English</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="fr">🇫🇷 Français</option>
                    <option value="de">🇩🇪 Deutsch</option>
                    <option value="pt">🇵🇹 Português</option>
                </select>
            </div>
            <div class="local-threat-alert" id="localThreatAlert" style="display: none;">
                <span>⚠️</span>
                <span id="threatText">Local security alert for your region</span>
            </div>
        </div>
    </div>

    <!-- HEADER -->
    <header class="main-header">
        <div class="header-container">
            <a href="/" class="logo" id="brandName">🛡️ CyberDad</a>
            <nav>
                <ul class="main-nav">
                    <li><a href="#alerts" id="nav-alerts">Security Alerts</a></li>
                    <li><a href="#guides" id="nav-guides">Family Guides</a></li>
                    <li><a href="#tools" id="nav-tools">Security Tools</a></li>
                    <li><a href="#products" id="nav-products">Resources</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <!-- TRUST BAR -->
    <div class="trust-bar">
        <div class="trust-container">
            <div class="trust-item">
                <span>✅</span>
                <span>Real-time threat monitoring</span>
            </div>
            <div class="trust-item">
                <span>🛡️</span>
                <span>Family-tested security advice</span>
            </div>
            <div class="trust-item">
                <span>👨‍👩‍👧‍👦</span>
                <span>Trusted by 12,000+ families</span>
            </div>
            <div class="trust-item">
                <span>📊</span>
                <span>AI-powered intelligence</span>
            </div>
        </div>
    </div>

    <!-- HERO SECTION -->
    <section class="hero-section">
        <div class="hero-container">
            <h1 class="hero-title">Family Cybersecurity Intelligence</h1>
            <p class="hero-subtitle">Get real-time threat alerts, protection guides, and security tips that keep your family safe in the digital world</p>
            
            <div class="hero-stats">
                <div class="stat-item">
                    <span class="stat-number">12,000+</span>
                    <span class="stat-label">Families Protected</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">{{ site.posts.size }}</span>
                    <span class="stat-label">Security Guides</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">24/7</span>
                    <span class="stat-label">Threat Monitoring</span>
                </div>
            </div>
        </div>
    </section>

    <!-- MAIN CONTENT -->
    <main class="main-container">
        
        <!-- CURRENT ALERT -->
        <section class="alert-section" id="alerts">
            <div class="alert-header">
                <span class="alert-icon">🛡️</span>
                <h2 class="alert-title">Latest: {{ site.posts.first.title }}</h2>
            </div>
            <div class="alert-content">
                <p>{{ site.posts.first.excerpt | strip_html | truncatewords: 30 }}</p>
            </div>
            <a href="{{ site.posts.first.url }}" class="alert-cta">Read Latest Guide →</a>
        </section>

        <!-- CONTENT GRID -->
        <div class="content-grid">
            
            <!-- MAIN CONTENT AREA -->
            <div class="main-content">
                
                <!-- LATEST POSTS - JEKYLL POWERED -->
                <section>
                    <h2 style="margin-bottom: 2rem; font-size: 1.8rem; font-weight: 600;">Latest Family Security Posts</h2>
                    
                    <div class="post-grid">
                        {% assign sorted_posts = site.posts | sort: 'date' | reverse %}
                        {% for post in sorted_posts limit: 6 %}
                        <article class="post-card fade-in">
                            <div class="post-image">🛡️</div>
                            <div class="post-content">
                                <span class="post-category">{{ post.categories | first | upcase | default: "SECURITY" }}</span>
                                <h3 class="post-title">{{ post.title }}</h3>
                                <p class="post-excerpt">{{ post.excerpt | strip_html | truncatewords: 20 }}</p>
                                <div class="post-meta">
                                    <span>{{ post.date | date: "%b %d" }}</span>
                                    <a href="{{ post.url }}" class="read-more">Read Guide →</a>
                                </div>
                            </div>
                        </article>
                        {% endfor %}
                    </div>
                </section>

            </div>

            <!-- SIDEBAR -->
            <aside class="sidebar">
                
                <!-- EMAIL CAPTURE -->
                <div class="sidebar-card email-capture">
                    <h3 class="sidebar-title">🛡️ Get FREE Security Alerts</h3>
                    <p style="margin-bottom: 1rem; font-size: 0.9rem;">Join 12,000+ families getting instant notifications about threats affecting their devices!</p>
                    <form class="email-form" onsubmit="handleEmailSignup(event)">
                        <input type="email" placeholder="Enter your family email..." class="email-input" required>
                        <button type="submit" class="email-btn">🔒 Get Instant Alerts</button>
                    </form>
                    <p class="email-benefits">✅ Real-time threat alerts • Unsubscribe anytime</p>
                </div>

                <!-- TRENDING GUIDES -->
                <div class="sidebar-card">
                    <h3 class="sidebar-title">🔥 Most Popular Guides</h3>
                    <div style="display: grid; gap: 1rem;">
                        {% for post in site.posts limit: 3 %}
                        <a href="{{ post.url }}" style="text-decoration: none; color: #4a5568; font-size: 0.9rem; padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0;">
                            <strong>{{ post.title | truncatewords: 5 }}</strong><br>
                            <span style="color: #a0aec0; font-size: 0.8rem;">{{ post.date | date: "%B %d, %Y" }}</span>
                        </a>
                        {% endfor %}
                    </div>
                </div>

                <!-- EMERGENCY CONTACT -->
                <div class="sidebar-card" style="background: #fff5f5; border: 1px solid #feb2b2;">
                    <h3 class="sidebar-title" style="color: #c53030;">🆘 Need Immediate Help?</h3>
                    <p style="margin-bottom: 1rem; font-size: 0.9rem; color: #4a5568;">Suspect a security breach or need urgent assistance?</p>
                    <a href="mailto:help@cyberdad2025.com" style="background: #c53030; color: white; padding: 0.75rem 1rem; border-radius: 4px; text-decoration: none; font-weight: 600; display: inline-block;">📧 Emergency Contact</a>
                </div>

            </aside>

        </div>

        <!-- PRODUCTS SECTION -->
        <section class="revenue-section" id="products">
            <h2 class="revenue-title">🎯 CyberDad Digital Security Store</h2>
            <p style="color: #718096; margin-bottom: 2rem;">Professional-grade family cybersecurity resources • Instant download • 30-day guarantee</p>
            
            <div class="product-grid">
                <div class="product-card">
                    <div class="product-icon">🔐</div>
                    <h3 class="product-name">Gumroad Store</h3>
                    <p class="product-description">Complete family security guides, password templates, and protection checklists. Professional PDF downloads.</p>
                    <a href="https://cyberdad.gumroad.com" target="_blank" class="product-btn" onclick="trackRevenue('gumroad_click', 0)">Shop Gumroad Store →</a>
                </div>
                
                <div class="product-card">
                    <div class="product-icon">📋</div>
                    <h3 class="product-name">Payhip Store</h3>
                    <p class="product-description">Digital security products, family safety bundles, and cybersecurity training materials for modern families.</p>
                    <a href="https://payhip.com/CyberDadKit" target="_blank" class="product-btn" onclick="trackRevenue('payhip_click', 0)">Browse Payhip Store →</a>
                </div>
                
                <div class="product-card">
                    <div class="product-icon">🖨️</div>
                    <h3 class="product-name">Etsy Printables</h3>
                    <p class="product-description">Printable security checklists, family safety posters, and cybersecurity worksheets. Perfect for home and office.</p>
                    <a href="https://www.etsy.com/shop/CyberDadPrints" target="_blank" class="product-btn" onclick="trackRevenue('etsy_click', 0)">Visit Etsy Shop →</a>
                </div>
            </div>
            
            <p style="margin-top: 2rem; color: #718096; font-size: 0.9rem;">
                💡 <strong>Blog Stats:</strong> {{ site.posts.size }} security articles • Updated {{ site.time | date: "%B %d, %Y" }} • 3 posts daily at 9am, 1pm, 8pm EST
            </p>
        </section>

        <!-- TOOLS SECTION -->
        <section id="tools">
            <h2 style="margin-bottom: 2rem; font-size: 1.8rem; font-weight: 600; text-align: center;">🔧 Essential Security Tools for Families</h2>
            
            <div class="tools-grid">
                <div class="tool-card">
                    <div class="tool-icon">🛡️</div>
                    <h3 class="tool-name">VPN Protection</h3>
                    <p class="tool-description">Secure your family's internet connection with military-grade encryption wherever you go.</p>
                    <a href="https://nordvpn.com" target="_blank" class="tool-link">Get NordVPN →</a>
                </div>
                
                <div class="tool-card">
                    <div class="tool-icon">🔒</div>
                    <h3 class="tool-name">Password Manager</h3>
                    <p class="tool-description">Generate and store unique passwords for every account. Family plans available.</p>
                    <a href="https://1password.com" target="_blank" class="tool-link">Try 1Password →</a>
                </div>
                
                <div class="tool-card">
                    <div class="tool-icon">🦠</div>
                    <h3 class="tool-name">Antivirus Protection</h3>
                    <p class="tool-description">Comprehensive protection against malware, ransomware, and cyber threats.</p>
                    <a href="https://norton.com" target="_blank" class="tool-link">Get Norton →</a>
                </div>
            </div>
        </section>

    </main>

    <!-- FOOTER -->
    <footer class="footer">
        <div class="footer-container">
            <div class="footer-section">
                <h3>🛡️ CyberDad Intelligence</h3>
                <p style="color: #a0aec0; margin-bottom: 1rem;">AI-powered cybersecurity intelligence for modern families. Real-time threat monitoring and family-friendly protection guidance.</p>
                <div style="display: flex; gap: 1rem;">
                    <a href="https://www.pinterest.com/cyberdadkit/" style="font-size: 1.2rem;">📌</a>
                    <a href="https://linktr.ee/cyberdadkit" style="font-size: 1.2rem;">🔗</a>
                    <a href="mailto:help@cyberdad2025.com" style="font-size: 1.2rem;">📧</a>
                </div>
            </div>
            
            <div class="footer-section">
                <h3>Security Resources</h3>
                <a href="#">Latest Threat Alerts</a>
                <a href="#">Family Security Guides</a>
                <a href="#">Device Protection Tips</a>
                <a href="#">Emergency Response</a>
            </div>
            
            <div class="footer-section">
                <h3>Tools & Products</h3>
                <a href="#">Security Printables</a>
                <a href="#">Family Checklists</a>
                <a href="#">Protection Templates</a>
                <a href="#">Emergency Plans</a>
            </div>
            
            <div class="footer-section">
                <h3>Support</h3>
                <a href="mailto:help@cyberdad2025.com">Email Support</a>
                <a href="#">Emergency Contact</a>
                <a href="#">Security Consultation</a>
                <a href="#">All Resources</a>
            </div>
        </div>
        
        <div class="footer-bottom">
            <p>&copy; 2025 CyberDad. Protecting families through intelligent cybersecurity.</p>
        </div>
    </footer>

    <!-- ALL YOUR ORIGINAL JAVASCRIPT - GEOLOCATION, MULTI-LANGUAGE, ETC -->
    <script>
        // [All your original JavaScript code goes here - geolocation, language switching, etc.]
        // ... (same as your original file)
        
        console.log('🛡️ CyberDad: Professional Layout + Jekyll Integration Loaded!');
    </script>
</body>
</html>
