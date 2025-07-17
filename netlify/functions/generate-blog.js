exports.handler = async (event, context) => {
  const { Octokit } = require("@octokit/rest");
  
  try {
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });

    // Get current time in EST/EDT
    const now = new Date();
    const estOffset = -5; // EST is UTC-5
    const estTime = new Date(now.getTime() + (estOffset * 60 * 60 * 1000));
    
    // Format: YYYY-MM-DD HH:MM:SS -0500
    const year = estTime.getFullYear();
    const month = String(estTime.getMonth() + 1).padStart(2, '0');
    const day = String(estTime.getDate()).padStart(2, '0');
    const hours = String(estTime.getHours()).padStart(2, '0');
    const minutes = String(estTime.getMinutes()).padStart(2, '0');
    const seconds = String(estTime.getSeconds()).padStart(2, '0');
    
    const dateStr = `${year}-${month}-${day}`;
    const timeStr = `${hours}:${minutes}:${seconds}`;
    const fullTimestamp = `${dateStr} ${timeStr} -0500`;
    
    const fileName = `${dateStr}-${generateSlug()}.md`;
    
    const postContent = `---
layout: post
title: "Daily Cybersecurity Tips for Families"
date: ${fullTimestamp}
categories: [cybersecurity]
tags: [security, tips, family]
---

# Daily Cybersecurity Tips for Families

Here are important security tips to keep your family safe online:

## Password Security
- Use unique passwords for each account
- Enable two-factor authentication
- Consider using a password manager

## Safe Browsing
- Verify URLs before clicking
- Keep software updated
- Use reputable antivirus software

## Family Education
- Teach children about online safety
- Review privacy settings regularly
- Stay informed about current threats

Stay safe online!
*- CyberDad*`;

    // Check if file already exists
    try {
      await octokit.rest.repos.getContent({
        owner: 'CyberDad2025',
        repo: 'CyberDad2025.github.io',
        path: `_posts/${fileName}`
      });
      
      return {
        statusCode: 200,
        body: JSON.stringify({ 
          success: true, 
          message: 'Post already exists',
          filename: fileName,
          timestamp: fullTimestamp
        })
      };
    } catch (error) {
      // File doesn't exist, create it
    }

    await octokit.rest.repos.createOrUpdateFileContents({
      owner: 'CyberDad2025',
      repo: 'CyberDad2025.github.io',
      path: `_posts/${fileName}`,
      message: `Add post ${fileName}`,
      content: Buffer.from(postContent).toString('base64'),
      branch: 'main'
    });

    return {
      statusCode: 200,
      body: JSON.stringify({
        success: true,
        message: 'Post created successfully',
        filename: fileName,
        timestamp: fullTimestamp
      })
    };

  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({
        success: false,
        error: error.message
      })
    };
  }
};

function generateSlug() {
  const topics = [
    'password-security-tips',
    'wifi-network-protection',
    'phishing-scam-prevention',
    'vpn-setup-guide',
    'mobile-security-essentials',
    'home-router-hardening',
    'social-media-privacy',
    'email-security-best-practices',
    'backup-strategy-guide',
    'identity-theft-prevention',
    'secure-browsing-habits',
    'family-cyber-safety',
    'two-factor-authentication'
  ];
  
  return topics[Math.floor(Math.random() * topics.length)];
}
