// netlify/functions/generate-blog.js
// BULLETPROOF Blog Generator - Fixed All Issues

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_OWNER = 'CyberDad2025';
const GITHUB_REPO = 'CyberDad2025.github.io';
const CRON_SECRET = process.env.CRON_SECRET;

// Cybersecurity topics pool
const CYBERSECURITY_TOPICS = [
  'password security', 'home network security', 'VPN setup', 'phishing prevention',
  'social media privacy', 'smart home security', 'mobile device security', 'backup strategies',
  'identity theft protection', 'secure browsing', 'email security', 'WiFi security',
  'router configuration', 'antivirus software', 'firewall setup', 'secure passwords',
  'two-factor authentication', 'data encryption', 'secure file sharing', 'privacy settings',
  'parental controls', 'online banking security', 'remote work security', 'IoT security',
  'cloud storage security', 'browser security', 'social engineering awareness', 
  'ransomware protection', 'secure communication', 'digital footprint management'
];

exports.handler = async (event, context) => {
  console.log('🚀 Starting bulletproof blog generator...');

  try {
    // 1. VERIFY AUTHORIZATION
    const auth = event.headers.authorization;
    if (!auth || !auth.includes(CRON_SECRET)) {
      console.log('❌ Unauthorized request');
      return {
        statusCode: 401,
        body: JSON.stringify({ error: 'Unauthorized' })
      };
    }

    // 2. CHECK ENVIRONMENT VARIABLES
    if (!OPENAI_API_KEY) {
      throw new Error('Missing OPENAI_API_KEY environment variable');
    }
    if (!GITHUB_TOKEN) {
      throw new Error('Missing GITHUB_TOKEN environment variable');
    }

    console.log('✅ Authorization and environment check passed');

    // 3. GENERATE PROPER TIMESTAMP (EST/EDT timezone aware)
    const now = new Date();
    const estOffset = -5; // EST is UTC-5, EDT is UTC-4
    const isDST = isDaylightSavingTime(now);
    const timezoneOffset = isDST ? -4 : -5; // EDT vs EST
    
    const estTime = new Date(now.getTime() + (timezoneOffset * 60 * 60 * 1000));
    const dateStr = estTime.toISOString().split('T')[0]; // YYYY-MM-DD
    const timeStr = estTime.toISOString().split('T')[1].split('.')[0]; // HH:MM:SS
    
    console.log(`📅 Generated EST time: ${dateStr} ${timeStr}`);

    // 4. GENERATE TOPIC AND TITLE
    const topic = CYBERSECURITY_TOPICS[Math.floor(Math.random() * CYBERSECURITY_TOPICS.length)];
    const currentYear = new Date().getFullYear();
    
    console.log(`🎯 Selected topic: ${topic}`);

    // 5. GENERATE BLOG CONTENT WITH OPENAI
    console.log('🤖 Generating blog content with OpenAI...');
    
    const prompt = `Write a comprehensive cybersecurity blog post about "${topic}" for families in ${currentYear}. 
    
    Requirements:
    - Write for parents and families
    - Include practical, actionable tips
    - Make it engaging and easy to understand
    - Include specific product recommendations
    - Add real-world examples
    - Target 800-1200 words
    - Include a compelling introduction
    - Use subheadings with ##
    - End with a practical summary
    
    Focus on helping families protect themselves online in ${currentYear}.`;

    const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4',
        messages: [
          {
            role: 'system',
            content: 'You are a cybersecurity expert who writes engaging, practical blog posts for families. Write in a friendly, authoritative tone.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 2000,
        temperature: 0.7,
      }),
    });

    if (!openaiResponse.ok) {
      const errorData = await openaiResponse.text();
      console.log('❌ OpenAI API error:', errorData);
      throw new Error(`OpenAI API error: ${openaiResponse.status} - ${errorData}`);
    }

    const openaiData = await openaiResponse.json();
    const blogContent = openaiData.choices[0].message.content;
    
    console.log('✅ Blog content generated successfully');

    // 6. EXTRACT TITLE FROM CONTENT
    const titleMatch = blogContent.match(/^#\s*(.+)$/m) || blogContent.match(/^(.+)$/m);
    let title = titleMatch ? titleMatch[1].trim() : `${topic.charAt(0).toUpperCase() + topic.slice(1)} Guide for ${currentYear}`;
    
    // Clean title for filename
    title = title.replace(/[#*]/g, '').trim();
    const cleanTitle = title.toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');

    console.log(`📝 Generated title: ${title}`);

    // 7. CREATE FILENAME
    const filename = `${dateStr}-${cleanTitle}.md`;
    console.log(`📄 Filename: ${filename}`);

    // 8. CREATE JEKYLL FRONT MATTER
    const categories = ['cybersecurity', 'security', 'family-safety'];
    const tags = extractTags(topic, blogContent);
    
    const frontMatter = `---
layout: post
title: "${title}"
date: ${dateStr} ${timeStr} -0500
categories: [${categories.join(', ')}]
tags: [${tags.join(', ')}]
author: CyberDad2025
excerpt: "${generateExcerpt(blogContent)}"
seo_title: "${title} - Complete ${currentYear} Guide"
seo_description: "Learn ${topic} with practical tips for families. Protect your home network and keep your family safe online in ${currentYear}."
featured: true
image: /assets/images/cybersecurity-${cleanTitle}.jpg
---

`;

    const fullContent = frontMatter + blogContent;

    // 9. CHECK IF POST ALREADY EXISTS
    console.log('🔍 Checking if post already exists...');
    
    try {
      const existingResponse = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/_posts/${filename}`, {
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      });
      
      if (existingResponse.ok) {
        console.log('⚠️ Post already exists, appending timestamp...');
        const timestamp = Date.now();
        const newFilename = `${dateStr}-${cleanTitle}-${timestamp}.md`;
        return await createGitHubPost(newFilename, fullContent, title);
      }
    } catch (error) {
      console.log('✅ Post does not exist, proceeding with creation');
    }

    // 10. CREATE THE BLOG POST
    return await createGitHubPost(filename, fullContent, title);

  } catch (error) {
    console.error('💥 Fatal error in blog generator:', error);
    
    // 11. FALLBACK ERROR HANDLING
    try {
      await createErrorIssue(error);
    } catch (issueError) {
      console.error('Failed to create error issue:', issueError);
    }
    
    return {
      statusCode: 500,
      body: JSON.stringify({ 
        error: error.message,
        details: 'Check function logs for more information',
        timestamp: new Date().toISOString()
      })
    };
  }
};

// HELPER FUNCTIONS

async function createGitHubPost(filename, content, title) {
  console.log(`📤 Creating GitHub post: ${filename}`);
  
  try {
    const response = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/_posts/${filename}`, {
      method: 'PUT',
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Auto-generated blog post: ${filename}`,
        content: Buffer.from(content).toString('base64'),
        author: {
          name: 'CyberDad2025 Bot',
          email: 'cyberdadkit@gmail.com'
        }
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`GitHub API error: ${response.status} - ${errorData}`);
    }

    const result = await response.json();
    console.log('✅ Blog post created successfully on GitHub');

    return {
      statusCode: 200,
      body: JSON.stringify({
        success: true,
        message: 'Blog post created successfully',
        filename: filename,
        title: title,
        url: result.content.html_url,
        timestamp: new Date().toISOString()
      })
    };

  } catch (error) {
    console.error('❌ Error creating GitHub post:', error);
    throw error;
  }
}

function isDaylightSavingTime(date) {
  const year = date.getFullYear();
  // DST in US: 2nd Sunday in March to 1st Sunday in November
  const dstStart = new Date(year, 2, 1); // March 1st
  const dstEnd = new Date(year, 10, 1); // November 1st
  
  // Find 2nd Sunday in March
  dstStart.setDate(1 + (7 - dstStart.getDay()) % 7 + 7);
  
  // Find 1st Sunday in November  
  dstEnd.setDate(1 + (7 - dstEnd.getDay()) % 7);
  
  return date >= dstStart && date < dstEnd;
}

function extractTags(topic, content) {
  const baseTags = topic.split(' ').slice(0, 3);
  const contentTags = [];
  
  // Extract additional tags from content
  if (content.toLowerCase().includes('vpn')) contentTags.push('vpn');
  if (content.toLowerCase().includes('password')) contentTags.push('passwords');
  if (content.toLowerCase().includes('router')) contentTags.push('router');
  if (content.toLowerCase().includes('wifi')) contentTags.push('wifi');
  if (content.toLowerCase().includes('family')) contentTags.push('family');
  if (content.toLowerCase().includes('home')) contentTags.push('home');
  
  return [...baseTags, ...contentTags].slice(0, 8);
}

function generateExcerpt(content) {
  // Extract first paragraph or first 160 characters
  const firstParagraph = content.split('\n\n')[0];
  const excerpt = firstParagraph.replace(/[#*]/g, '').trim();
  
  if (excerpt.length > 160) {
    return excerpt.substring(0, 157) + '...';
  }
  
  return excerpt;
}

async function createErrorIssue(error) {
  console.log('📝 Creating error report issue...');
  
  try {
    const errorIssue = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/issues`, {
      method: 'POST',
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: `🚨 Blog Generator Error - ${new Date().toISOString().split('T')[0]}`,
        body: `# Blog Generator Error Report

**Time:** ${new Date().toLocaleString()}
**Error:** ${error.message}

**Stack Trace:**
\`\`\`
${error.stack}
\`\`\`

**Environment:**
- Function: generate-blog
- Trigger: Cron job

**Next Steps:**
1. Check environment variables
2. Verify API keys
3. Test function manually
`,
        labels: ['bug', 'automation', 'high-priority']
      })
    });

    if (errorIssue.ok) {
      console.log('✅ Error issue created successfully');
    }
  } catch (issueError) {
    console.error('Failed to create error issue:', issueError);
  }
}
