exports.handler = async (event, context) => {
  const { Octokit } = require("@octokit/rest");
  
  try {
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });

    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    const fileName = dateStr + '-cybersecurity-tips.md';
    
    const postContent = `---
layout: post
title: "Daily Cybersecurity Tips for Families"
date: ${now.toISOString().split('T')[0]} 10:00:00 -0500
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
        filename: fileName
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
