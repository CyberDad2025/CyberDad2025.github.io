// netlify/functions/generate-blog.js
const { schedule } = require('@netlify/functions');

// Pinterest-optimized topics (short titles under 30 chars)
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
  "Cryptocurrency Security",
  "IoT Device Protection",
  "Mobile Security Apps",
  "Network Monitoring Tools",
  "Firewall Configuration",
  "Data Encryption Guide",
  "Phishing Prevention",
  "Ransomware Protection",
  "Social Media Privacy",
  "Wi-Fi Security Setup",
  "Backup Strategy Guide"
];

async function generateBlogPost(event, context) {
  try {
    console.log('🚀 Starting blog post generation...');
    
    // Verify authorization
    const authHeader = event.headers.authorization;
    if (!authHeader || authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return {
        statusCode: 401,
        body: JSON.stringify({ error: 'Unauthorized' })
      };
    }
    
    // Select random topic
    const topic = TOPICS[Math.floor(Math.random() * TOPICS.length)];
    console.log(`Selected topic: ${topic}`);
    
    // Generate content
    const content = await generateContent(topic);
    
    // Create blog post
    const filename = createFilename(topic);
    const blogPost = createBlogPost(topic, content);
    
    // Commit to GitHub
    await commitToGitHub(filename, blogPost);
    
    console.log('✅ Blog post generated successfully!');
    return {
      statusCode: 200,
      body: JSON.stringify({ 
        success: true, 
        topic: topic,
        filename: filename,
        timestamp: new Date().toISOString()
      })
    };
    
  } catch (error) {
    console.error('❌ Error generating blog post:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ 
        success: false, 
        error: error.message 
      })
    };
  }
}

async function generateContent(topic) {
  // Try OpenAI API first
  if (process.env.OPENAI_API_KEY) {
    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'gpt-3.5-turbo',
          messages: [{
            role: 'user',
            content: `Write a comprehensive cybersecurity blog post about "${topic}". 
            
            Structure:
            1. Engaging introduction
            2. Main content with practical tips
            3. Product recommendations
            4. Conclusion with call-to-action
            
            Make it SEO-friendly, informative, and family-oriented. Length: 800-1000 words.`
          }],
          max_tokens: 1500,
          temperature: 0.7
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.choices[0].message.content;
      }
    } catch (error) {
      console.error('OpenAI API error:', error);
    }
  }
  
  // Fallback content generation
  return generateFallbackContent(topic);
}

function generateFallbackContent(topic) {
  const now = new Date();
  const year = now.getFullYear();
  
  return `# ${topic}

In ${year}, cybersecurity threats continue to evolve at an unprecedented pace. Understanding ${topic.toLowerCase()} has become essential for protecting your digital life and maintaining online safety.

## Why ${topic} Matters Now

Digital security isn't just for large corporations anymore. Every individual, family, and small business needs to understand ${topic.toLowerCase()} to stay protected against modern cyber threats.

### Current Threat Landscape

- **Increased sophistication** of cyber attacks
- **Growing number** of connected devices
- **Rising costs** of security breaches
- **Expanding attack surfaces** in remote work environments

## Essential ${topic} Strategies

### 1. Risk Assessment
Start by evaluating your current security posture. Identify potential vulnerabilities and prioritize areas that need immediate attention.

### 2. Implementation Planning
Develop a comprehensive approach to ${topic.toLowerCase()} that fits your specific needs and budget constraints.

### 3. Active Monitoring
Continuously monitor your systems for suspicious activity and potential security incidents.

### 4. Regular Updates
Keep all software, systems, and security measures up to date with the latest patches and improvements.

### 5. Education and Training
Ensure all users understand basic security practices and can recognize potential threats.

## Best Practices for ${topic}

**Prevention is Key**
- Regular security audits and assessments
- Strong authentication mechanisms
- Encrypted communications and data storage
- Backup and recovery planning
- Incident response procedures

**Stay Informed**
- Follow cybersecurity news and trends
- Subscribe to security advisories
- Participate in security communities
- Attend training sessions and workshops

## Recommended Security Solutions

When selecting ${topic.toLowerCase()} tools and services, consider:

- **Reputation and track record** of the vendor
- **Compatibility** with your existing systems
- **Scalability** for future growth
- **Support and documentation** quality
- **Cost-effectiveness** and ROI

## Common Mistakes to Avoid

1. **Assuming you're not a target** - everyone is at risk
2. **Delaying security updates** - patches are critical
3. **Using weak passwords** - strength matters
4. **Ignoring employee training** - human error is common
5. **Neglecting mobile security** - phones are computers too

## Implementation Timeline

**Week 1-2: Assessment**
- Evaluate current security posture
- Identify gaps and vulnerabilities
- Prioritize improvement areas

**Week 3-4: Planning**
- Research solutions and vendors
- Develop implementation strategy
- Allocate budget and resources

**Month 2: Deployment**
- Install and configure security tools
- Train users on new procedures
- Test all systems and processes

**Ongoing: Maintenance**
- Monitor security metrics
- Update systems regularly
- Review and improve processes

## Measuring Success

Track these key metrics to ensure your ${topic.toLowerCase()} efforts are effective:

- **Incident response time**
- **System uptime and availability**
- **User compliance rates**
- **Security awareness levels**
- **Cost per incident**

## Looking Forward

As technology continues to evolve, so will the threats we face. Staying ahead requires:

- **Continuous learning** about new threats
- **Adaptive security strategies** that evolve with risks
- **Investment in emerging technologies** like AI-powered security
- **Collaboration** with security communities and experts

## Conclusion

${topic} isn't just a technical necessity—it's an investment in your digital future. By implementing these strategies and maintaining a proactive security posture, you can protect what matters most while enabling growth and innovation.

Remember: cybersecurity is not a one-time setup but an ongoing process that requires attention, investment, and adaptation. Start with the basics, build gradually, and never assume you're completely secure.

**Take action today** to improve your ${topic.toLowerCase()} posture. Your future self will thank you for the protection you put in place now.

---

*Stay secure, stay informed, and never stop learning about cybersecurity.*`;
}

function createFilename(topic) {
  const date = new Date().toISOString().split('T')[0];
  const slug = topic.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return `${date}-${slug}.md`;
}

function createBlogPost(topic, content) {
  const now = new Date();
  const tags = topic.toLowerCase().split(/[\s\-]+/).filter(tag => tag.length > 2);
  
  const frontmatter = `---
layout: post
title: "${topic}"
date: ${now.toISOString()}
categories: [cybersecurity, security, tech]
tags: [${tags.join(', ')}]
author: CyberDad2025
excerpt: "Essential ${topic.toLowerCase()} guide for ${now.getFullYear()}"
seo_title: "${topic} - Complete Guide ${now.getFullYear()}"
seo_description: "Learn about ${topic.toLowerCase()} with practical tips and recommendations for better cybersecurity."
---

${content}`;
  
  return frontmatter;
}

async function commitToGitHub(filename, content) {
  const token = process.env.GITHUB_TOKEN;
  const repo = 'CyberDad2025/CyberDad2025.github.io';
  
  const response = await fetch(`https://api.github.com/repos/${repo}/contents/_posts/${filename}`, {
    method: 'PUT',
    headers: {
      'Authorization': `token ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: `🤖 Auto-generated: ${filename}`,
      content: Buffer.from(content).toString('base64'),
      branch: 'main'
    })
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(`GitHub API error: ${response.status} - ${errorData.message}`);
  }
  
  return await response.json();
}

// Export both the scheduled function and a manual handler
exports.handler = generateBlogPost;

// Optional: Schedule function (if you want to use Netlify's built-in scheduling)
// exports.handler = schedule('0 10,18,2 * * *', generateBlogPost);
