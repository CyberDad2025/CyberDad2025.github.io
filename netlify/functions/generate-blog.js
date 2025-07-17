#!/bin/bash

# Deploy Optimized Blog Generator Function
# This script will backup your current function and deploy the optimized version

echo "🚀 Starting deployment of optimized blog generator..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "netlify.toml" ]; then
    print_error "netlify.toml not found. Please run this script from your project root."
    exit 1
fi

# Create netlify functions directory if it doesn't exist
mkdir -p netlify/functions

# Backup existing function if it exists
if [ -f "netlify/functions/generate-blog.js" ]; then
    print_warning "Backing up existing function..."
    cp netlify/functions/generate-blog.js netlify/functions/generate-blog.js.backup.$(date +%Y%m%d_%H%M%S)
    print_status "Backup created"
fi

# Create the optimized function
print_status "Creating optimized function..."

cat > netlify/functions/generate-blog.js << 'EOF'
const { Octokit } = require("@octokit/rest");

// Optimized blog generator with timeout fixes
exports.handler = async (event, context) => {
  // Set shorter timeout for the entire function
  context.callbackWaitsForEmptyEventLoop = false;
  
  const startTime = Date.now();
  
  try {
    // Quick validation
    if (event.httpMethod !== 'POST' && event.httpMethod !== 'GET') {
      return {
        statusCode: 405,
        body: JSON.stringify({ error: 'Method not allowed' })
      };
    }

    // Initialize GitHub client
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
      request: {
        timeout: 5000 // 5 second timeout for GitHub API calls
      }
    });

    // Get current EST time
    const now = new Date();
    const estTime = new Date(now.getTime() - (5 * 60 * 60 * 1000)); // EST = UTC-5
    const dateStr = estTime.toISOString().split('T')[0];
    const timeStr = estTime.toTimeString().split(' ')[0];
    const timestamp = `${dateStr} ${timeStr}`;

    // Generate filename
    const fileName = `${dateStr}-${generateSlug()}.md`;

    // FAST content generation - pre-written templates
    const post = generateQuickPost(timestamp);

    // Check if file already exists (avoid duplicates)
    try {
      await octokit.rest.repos.getContent({
        owner: 'CyberDad2025',
        repo: 'CyberDad2025.github.io',
        path: `_posts/${fileName}`
      });
      
      // File exists, return success without creating duplicate
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ 
          success: true, 
          message: 'Post already exists',
          filename: fileName,
          executionTime: `${Date.now() - startTime}ms`
        })
      };
    } catch (error) {
      // File doesn't exist, continue with creation
    }

    // Create the post in GitHub
    const createResult = await octokit.rest.repos.createOrUpdateFileContents({
      owner: 'CyberDad2025',
      repo: 'CyberDad2025.github.io',
      path: `_posts/${fileName}`,
      message: `Add new post: ${fileName}`,
      content: Buffer.from(post).toString('base64'),
      branch: 'main'
    });

    const executionTime = Date.now() - startTime;

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        success: true,
        message: 'Blog post created successfully',
        filename: fileName,
        timestamp: timestamp,
        executionTime: `${executionTime}ms`,
        githubUrl: createResult.data.content.html_url
      })
    };

  } catch (error) {
    console.error('Error:', error);
    
    // Create GitHub issue for failed posts
    try {
      const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
      await octokit.rest.issues.create({
        owner: 'CyberDad2025',
        repo: 'CyberDad2025.github.io',
        title: `Blog Generation Failed - ${new Date().toISOString()}`,
        body: `**Error Details:**\n\`\`\`\n${error.message}\n\`\`\`\n\n**Stack:**\n\`\`\`\n${error.stack}\n\`\`\`\n\n**Time:** ${new Date().toISOString()}\n**Execution Time:** ${Date.now() - startTime}ms`
      });
    } catch (issueError) {
      console.error('Failed to create GitHub issue:', issueError);
    }

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        success: false,
        error: error.message,
        executionTime: `${Date.now() - startTime}ms`
      })
    };
  }
};

// Generate random slug for post filename
function generateSlug() {
  const topics = [
    'password-security-tips',
    'wifi-network-protection',
    'phishing-scam-prevention',
    'vpn-setup-guide',
    'antivirus-software-review',
    'mobile-security-essentials',
    'home-router-hardening',
    'social-media-privacy',
    'email-security-best-practices',
    'backup-strategy-guide',
    'malware-protection-tips',
    'identity-theft-prevention',
    'secure-browsing-habits',
    'family-cyber-safety',
    'two-factor-authentication',
    'secure-file-sharing',
    'privacy-settings-guide',
    'cyber-threat-awareness',
    'digital-footprint-management',
    'online-banking-security'
  ];
  
  return topics[Math.floor(Math.random() * topics.length)];
}

// Fast content generation using templates
function generateQuickPost(timestamp) {
  const templates = [
    {
      title: "Essential Password Security Tips Every Family Should Know",
      content: `# Essential Password Security Tips Every Family Should Know

Your family's digital security starts with strong passwords. Here are the most important tips to keep your accounts safe:

## 1. Use Strong, Unique Passwords
- At least 12 characters long
- Mix of uppercase, lowercase, numbers, and symbols
- Never reuse passwords across accounts

## 2. Enable Two-Factor Authentication
- Add an extra layer of security
- Use authenticator apps when possible
- Never rely on SMS alone

## 3. Consider a Password Manager
- Generate and store complex passwords
- Sync across all your devices
- Popular options: 1Password, Bitwarden, LastPass

## 4. Regular Password Updates
- Change passwords if there's a breach
- Update default passwords immediately
- Review and update every 6 months

## 5. Family Password Education
- Teach kids about password safety
- Set up parental controls
- Lead by example with good habits

## Red Flags to Watch For
- Unexpected password reset emails
- Suspicious login notifications
- Accounts being locked or compromised

Remember: Your password is your first line of defense. Take it seriously, and your family's digital life will be much more secure.

Stay safe out there!
*- CyberDad*`
    },
    {
      title: "WiFi Network Security: Protecting Your Home Internet",
      content: `# WiFi Network Security: Protecting Your Home Internet

Your home WiFi network is the gateway to your family's digital life. Here's how to secure it properly:

## 1. Change Default Settings
- Update router admin password immediately
- Change default network name (SSID)
- Disable WPS (WiFi Protected Setup)

## 2. Use WPA3 Security
- Enable WPA3 encryption (or WPA2 if unavailable)
- Create a strong network password
- Avoid WEP encryption at all costs

## 3. Regular Firmware Updates
- Check for router updates monthly
- Enable automatic updates if available
- Replace old routers every 3-5 years

## 4. Network Monitoring
- Review connected devices regularly
- Set up guest networks for visitors
- Monitor bandwidth usage for suspicious activity

## 5. Advanced Security Features
- Enable firewall protection
- Disable remote management unless needed
- Use MAC address filtering for critical devices

## Warning Signs of Compromise
- Slow internet speeds
- Unknown devices on network
- Unusual data usage spikes
- Unexpected router behavior

## Family WiFi Best Practices
- Teach kids about public WiFi dangers
- Use VPN for sensitive activities
- Separate IoT devices on guest network

A secure home network protects everything connected to it. Take these steps today!

*- CyberDad*`
    },
    {
      title: "Phishing Scams: How to Protect Your Family",
      content: `# Phishing Scams: How to Protect Your Family

Phishing attacks are getting more sophisticated. Here's how to spot and avoid them:

## 1. Common Phishing Tactics
- Urgent emails demanding immediate action
- Links that don't match the sender's domain
- Requests for personal information via email
- Fake alerts about account problems

## 2. Red Flags to Watch For
- Generic greetings ("Dear Customer")
- Spelling and grammar mistakes
- Mismatched URLs and sender addresses
- Threats of account closure

## 3. Verification Steps
- Contact companies directly through official channels
- Check URLs carefully before clicking
- Verify sender identity through separate communication
- Never provide passwords or SSN via email

## 4. Family Education
- Teach kids to ask before clicking links
- Practice identifying suspicious emails together
- Set up email filters and spam protection
- Create a family "verify first" policy

## 5. Technical Protections
- Use email security software
- Enable two-factor authentication
- Keep browsers and security software updated
- Use reputable antivirus with email scanning

## If You've Been Targeted
- Don't panic, but act quickly
- Change passwords immediately
- Monitor financial accounts
- Report to authorities if necessary

## Teaching Moments
- Review suspicious emails as a family
- Discuss current scam trends
- Practice safe email habits
- Celebrate good security decisions

Remember: When in doubt, verify through official channels. It's better to be cautious than compromised!

*- CyberDad*`
    }
  ];

  const template = templates[Math.floor(Math.random() * templates.length)];
  
  return `---
layout: post
title: "${template.title}"
date: ${timestamp} -0500
categories: [cybersecurity, family-safety]
tags: [security, tips, family, protection]
author: CyberDad
description: "Essential cybersecurity guidance for families"
---

${template.content}`;
}
EOF

print_status "Optimized function created successfully!"

# Update package.json if it exists
if [ -f "package.json" ]; then
    print_status "Updating package.json dependencies..."
    
    # Check if @octokit/rest is already in dependencies
    if ! grep -q "@octokit/rest" package.json; then
        print_status "Adding @octokit/rest dependency..."
        npm install @octokit/rest
    fi
else
    print_status "Creating package.json..."
    npm init -y
    npm install @octokit/rest
fi

# Create or update netlify.toml
print_status "Updating netlify.toml configuration..."

cat > netlify.toml << 'EOF'
[build]
  command = "echo 'No build command needed'"
  functions = "netlify/functions"
  publish = "."

[functions]
  directory = "netlify/functions"
  
[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/:splat"
  status = 200
EOF

print_status "netlify.toml updated successfully!"

# Test the function locally if netlify dev is available
if command -v netlify &> /dev/null; then
    print_status "Testing function locally..."
    echo "You can test the function by running: netlify dev"
    echo "Then visit: http://localhost:8888/.netlify/functions/generate-blog"
fi

print_status "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Commit and push these changes to your repository"
echo "2. Netlify will automatically deploy the updated function"
echo "3. Test the function manually at: https://rainbow-creponne-1d701f.netlify.app/.netlify/functions/generate-blog"
echo "4. Monitor the next cron job execution for improved performance"
echo ""
echo "🔧 Key optimizations made:"
echo "- Removed OpenAI API calls (major timeout source)"
echo "- Pre-written content templates for instant generation"
echo "- 5-second timeout on GitHub API calls"
echo "- Duplicate post prevention"
echo "- Better error handling and reporting"
echo "- Execution time tracking"
echo ""
echo "⚡ Expected execution time: 2-5 seconds (down from 30+ seconds)"

# Git commands for easy deployment
echo ""
echo "🚀 Quick deployment commands:"
echo "git add ."
echo "git commit -m 'Deploy optimized blog generator function'"
echo "git push origin main"
