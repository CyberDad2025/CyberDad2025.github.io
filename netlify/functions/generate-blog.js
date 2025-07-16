// netlify/functions/generate-blog.js
// Simple blog generator with no external dependencies

const TOPICS = [
  "VPN Security Tips 2025",
  "Password Manager Guide",
  "Home Router Setup",
  "Antivirus Review",
  "Cloud Backup Security",
  "Parental Control Software",
  "Identity Theft Protection",
  "Enterprise Security Tools",
  "Email Security Privacy",
  "Cryptocurrency Security"
];

exports.handler = async (event, context) => {
  // Set CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // Handle OPTIONS request for CORS
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    console.log('🚀 Blog generation started');
    
    // Check authorization
    const authHeader = event.headers.authorization || event.headers.Authorization;
    if (!authHeader || authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return {
        statusCode: 401,
        headers,
        body: JSON.stringify({ error: 'Unauthorized - Invalid or missing authorization' })
      };
    }

    // Select random topic
    const topic = TOPICS[Math.floor(Math.random() * TOPICS.length)];
    console.log(`Selected topic: ${topic}`);
    
    // Generate simple content
    const content = generateContent(topic);
    
    // Create filename
    const now = new Date();
    const date = now.toISOString().split('T')[0];
    const slug = topic.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const filename = `${date}-${slug}.md`;
    
    // Create blog post with frontmatter
    const blogPost = createBlogPost(topic, content, now);
    
    // Commit to GitHub
    await commitToGitHub(filename, blogPost);
    
    console.log('✅ Blog post created successfully');
    
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ 
        success: true, 
        topic: topic,
        filename: filename,
        timestamp: now.toISOString(),
        message: 'Blog post generated and committed to GitHub'
      })
    };
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        success: false, 
        error: error.message,
        details: 'Check function logs for more information'
      })
    };
  }
};

function generateContent(topic) {
  const currentYear = new Date().getFullYear();
  
  return `# ${topic}

In ${currentYear}, cybersecurity has become more critical than ever. Understanding ${topic.toLowerCase()} is essential for protecting your digital life and maintaining online security.

## Why ${topic} Matters

Digital threats are constantly evolving, making it crucial to stay informed about ${topic.toLowerCase()}. Whether you're an individual, family, or business, implementing proper security measures can save you from costly breaches and privacy violations.

## Key Benefits

- **Enhanced Protection**: Safeguard your personal and professional data
- **Peace of Mind**: Sleep better knowing your systems are secure  
- **Cost Savings**: Prevent expensive security incidents before they happen
- **Compliance**: Meet industry standards and regulatory requirements
- **Reputation Protection**: Maintain trust with customers and partners

## Getting Started with ${topic}

### Step 1: Assessment
Begin by evaluating your current security posture. Identify potential vulnerabilities and areas that need immediate attention.

### Step 2: Planning  
Develop a comprehensive security strategy that aligns with your specific needs and budget constraints.

### Step 3: Implementation
Deploy the necessary tools and processes to strengthen your security infrastructure.

### Step 4: Monitoring
Continuously monitor your systems for threats and unusual activity.

### Step 5: Maintenance
Keep all security measures updated and review your strategy regularly.

## Best Practices

**Prevention First**
- Use strong, unique passwords for all accounts
- Enable two-factor authentication whenever possible
- Keep software and systems updated with latest patches
- Regular security training for all users
- Implement backup and recovery procedures

**Stay Informed**
- Follow cybersecurity news and threat intelligence
- Subscribe to security advisories from vendors
- Participate in security communities and forums
- Attend training sessions and webinars

## Common Mistakes to Avoid

1. **Assuming you're not a target** - Everyone is at risk
2. **Delaying security updates** - Patches are critical
3. **Using weak passwords** - Complexity matters
4. **Ignoring user training** - Human error is common
5. **Neglecting mobile devices** - Phones need security too

## Implementation Timeline

**Week 1-2: Discovery**
- Audit current security measures
- Identify gaps and vulnerabilities  
- Prioritize critical areas

**Week 3-4: Strategy**
- Research available solutions
- Develop implementation plan
- Allocate necessary resources

**Month 2: Deployment**
- Install and configure security tools
- Train users on new procedures
- Test all systems thoroughly

**Ongoing: Operations**
- Monitor security metrics
- Update systems regularly
- Review and improve processes

## Measuring Success

Track these important metrics to ensure your ${topic.toLowerCase()} efforts are effective:

- **Response Time**: How quickly threats are detected and addressed
- **System Uptime**: Availability and reliability of your systems
- **User Compliance**: Adherence to security policies and procedures
- **Incident Frequency**: Number and severity of security events
- **Cost Efficiency**: Return on investment for security measures

## Looking Ahead

The cybersecurity landscape continues to evolve rapidly. Staying ahead requires:

- **Continuous Learning**: Keep up with new threats and technologies
- **Adaptive Strategies**: Flexible approaches that evolve with risks
- **Technology Investment**: Leverage AI and automation for better security
- **Community Engagement**: Collaborate with other security professionals

## Conclusion

${topic} represents a critical investment in your digital future. By implementing comprehensive security measures and maintaining a proactive approach, you can protect what matters most while enabling growth and innovation.

Remember that cybersecurity is not a destination but a journey. It requires ongoing attention, investment, and adaptation to new threats and technologies. Start with the fundamentals, build systematically, and never assume you're completely secure.

**Take action today** to strengthen your ${topic.toLowerCase()} posture. Your future self will appreciate the protection you implement now.

---

*Stay vigilant, stay informed, and prioritize cybersecurity in everything you do.*`;
}

function createBlogPost(topic, content, date) {
  const tags = topic.toLowerCase().split(/[\s\-]+/).filter(tag => tag.length > 2);
  
  return `---
layout: post
title: "${topic}"
date: ${date.toISOString()}
categories: [cybersecurity, security, tech]
tags: [${tags.join(', ')}]
author: CyberDad2025
excerpt: "Complete guide to ${topic.toLowerCase()} for ${date.getFullYear()}"
seo_title: "${topic} - Essential Guide ${date.getFullYear()}"
seo_description: "Learn about ${topic.toLowerCase()} with practical tips and expert recommendations for better cybersecurity."
featured: false
---

${content}`;
}

async function commitToGitHub(filename, content) {
  const token = process.env.GITHUB_TOKEN;
  const repo = 'CyberDad2025/CyberDad2025.github.io';
  
  if (!token) {
    throw new Error('GitHub token not found in environment variables');
  }
  
  const url = `https://api.github.com/repos/${repo}/contents/_posts/${filename}`;
  
  const body = JSON.stringify({
    message: `🤖 Auto-generated blog post: ${filename}`,
    content: Buffer.from(content).toString('base64'),
    branch: 'main'
  });
  
  const response = await fetch(url, {
    method: 'PUT',
    headers: {
      'Authorization': `token ${token}`,
      'Content-Type': 'application/json',
      'User-Agent': 'CyberDad-Blog-Bot'
    },
    body: body
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GitHub API error ${response.status}: ${errorText}`);
  }
  
  const result = await response.json();
  console.log('✅ Successfully committed to GitHub:', result.commit.sha);
  
  return result;
}
