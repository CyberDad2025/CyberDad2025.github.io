const { Octokit } = require("@octokit/rest");

exports.handler = async (event, context) => {
  context.callbackWaitsForEmptyEventLoop = false;
  
  const startTime = Date.now();
  
  try {
    const octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN,
      request: {
        timeout: 5000
      }
    });

    const now = new Date();
    const estTime = new Date(now.getTime() - (5 * 60 * 60 * 1000));
    const dateStr = estTime.toISOString().split('T')[0];
    const timeStr = estTime.toTimeString().split(' ')[0];
    const timestamp = dateStr + ' ' + timeStr;

    const fileName = dateStr + '-' + generateSlug() + '.md';
    const post = generateQuickPost(timestamp);

    try {
      await octokit.rest.repos.getContent({
        owner: 'CyberDad2025',
        repo: 'CyberDad2025.github.io',
        path: '_posts/' + fileName
      });
      
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
          executionTime: (Date.now() - startTime) + 'ms'
        })
      };
    } catch (error) {
      // File doesn't exist, continue
    }

    const createResult = await octokit.rest.repos.createOrUpdateFileContents({
      owner: 'CyberDad2025',
      repo: 'CyberDad2025.github.io',
      path: '_posts/' + fileName,
      message: 'Add new post: ' + fileName,
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
        executionTime: executionTime + 'ms',
        githubUrl: createResult.data.content.html_url
      })
    };

  } catch (error) {
    console.error('Error:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        success: false,
        error: error.message,
        executionTime: (Date.now() - startTime) + 'ms'
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

function generateQuickPost(timestamp) {
  const templates = [
    {
      title: "Essential Password Security Tips Every Family Should Know",
      content: "Your family's digital security starts with strong passwords. Here are the most important tips to keep your accounts safe:\n\n## 1. Use Strong, Unique Passwords\n- At least 12 characters long\n- Mix of uppercase, lowercase, numbers, and symbols\n- Never reuse passwords across accounts\n\n## 2. Enable Two-Factor Authentication\n- Add an extra layer of security\n- Use authenticator apps when possible\n- Never rely on SMS alone\n\n## 3. Consider a Password Manager\n- Generate and store complex passwords\n- Sync across all your devices\n- Popular options: 1Password, Bitwarden, LastPass\n\n## 4. Family Password Education\n- Teach kids about password safety\n- Set up parental controls\n- Lead by example with good habits\n\nRemember: Your password is your first line of defense. Take it seriously!\n\n*- CyberDad*"
    },
    {
      title: "WiFi Network Security: Protecting Your Home Internet",
      content: "Your home WiFi network is the gateway to your family's digital life. Here's how to secure it properly:\n\n## 1. Change Default Settings\n- Update router admin password immediately\n- Change default network name (SSID)\n- Disable WPS (WiFi Protected Setup)\n\n## 2. Use WPA3 Security\n- Enable WPA3 encryption (or WPA2 if unavailable)\n- Create a strong network password\n- Avoid WEP encryption at all costs\n\n## 3. Regular Updates\n- Check for router firmware updates monthly\n- Enable automatic updates if available\n- Replace old routers every 3-5 years\n\n## 4. Monitor Your Network\n- Review connected devices regularly\n- Set up guest networks for visitors\n- Watch for unusual activity\n\nA secure home network protects everything connected to it!\n\n*- CyberDad*"
    },
    {
      title: "Phishing Scams: How to Protect Your Family",
      content: "Phishing attacks are getting more sophisticated. Here's how to spot and avoid them:\n\n## 1. Common Warning Signs\n- Urgent emails demanding immediate action\n- Generic greetings like 'Dear Customer'\n- Spelling and grammar mistakes\n- Suspicious links and attachments\n\n## 2. Verification Steps\n- Contact companies directly through official channels\n- Check URLs carefully before clicking\n- Never provide passwords via email\n- When in doubt, don't click\n\n## 3. Family Education\n- Teach kids to ask before clicking links\n- Practice identifying suspicious emails together\n- Set up email filters and spam protection\n- Create a family 'verify first' policy\n\n## 4. If You're Targeted\n- Don't panic, but act quickly\n- Change passwords immediately\n- Monitor financial accounts\n- Report to authorities if necessary\n\nRemember: When in doubt, verify through official channels!\n\n*- CyberDad*"
    }
  ];

  const template = templates[Math.floor(Math.random() * templates.length)];
  
  return '---\nlayout: post\ntitle: "' + template.title + '"\ndate: ' + timestamp + ' -0500\ncategories: [cybersecurity, family-safety]\ntags: [security, tips, family, protection]\nauthor: CyberDad\ndescription: "Essential cybersecurity guidance for families"\n---\n\n# ' + template.title + '\n\n' + template.content;
}
