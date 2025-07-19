#!/usr/bin/env python3
"""
CyberDad Ultra-Secure CTI Backend System
Zero Trust Architecture with Multi-Layer Security Protection
Adaptive Threat Detection | Stealth Scraping | Self-Protection
"""

import requests
import openai
import os
import json
import feedparser
import hashlib
import hmac
import time
import random
import secrets
import base64
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import yaml
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import ssl
import socket
import subprocess
import psutil
import signal
import sys
from functools import wraps
from typing import Dict, List, Optional, Tuple
import ipaddress
from urllib.parse import urlparse, urljoin
import user_agent

# Security Configuration
SECURITY_CONFIG = {
    'max_file_size': 50 * 1024 * 1024,  # 50MB limit
    'max_memory_usage': 512 * 1024 * 1024,  # 512MB limit
    'max_execution_time': 1800,  # 30 minutes
    'allowed_domains': [
        'cisa.gov', 'krebsonsecurity.com', 'threatpost.com', 
        'securityweek.com', 'bleepingcomputer.com', 'nvd.nist.gov'
    ],
    'rate_limits': {
        'requests_per_minute': 6,  # Very conservative
        'requests_per_hour': 50,
        'delay_between_requests': (30, 90)  # Random delay range
    },
    'encryption_key_rotation': 3600,  # 1 hour
    'integrity_check_interval': 300,  # 5 minutes
    'self_defense_enabled': True,
    'stealth_mode': True
}

class SecurityManager:
    """Zero Trust Security Manager with Self-Protection"""
    
    def __init__(self):
        self.session_key = self._generate_session_key()
        self.encryption_key = self._derive_encryption_key()
        self.integrity_hashes = {}
        self.process_whitelist = set()
        self.network_monitor = NetworkSecurityMonitor()
        self.threat_detector = ThreatDetector()
        self.setup_logging()
        
    def _generate_session_key(self) -> bytes:
        """Generate cryptographically secure session key"""
        return secrets.token_bytes(32)
    
    def _derive_encryption_key(self) -> Fernet:
        """Derive encryption key using PBKDF2"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.session_key))
        return Fernet(key)
    
    def setup_logging(self):
        """Setup secure logging with encryption"""
        log_formatter = logging.Formatter(
            '%(asctime)s - [ENCRYPTED] - %(levelname)s - %(message)s'
        )
        
        # Create encrypted log handler
        handler = EncryptedFileHandler('logs/secure_operations.enc', self.encryption_key)
        handler.setFormatter(log_formatter)
        
        logger = logging.getLogger('cyberdad_security')
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        return logger
    
    def verify_integrity(self, filepath: str) -> bool:
        """Verify file integrity using SHA-256 hash"""
        try:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            if filepath in self.integrity_hashes:
                return self.integrity_hashes[filepath] == file_hash
            else:
                self.integrity_hashes[filepath] = file_hash
                return True
        except Exception:
            return False
    
    def check_memory_usage(self) -> bool:
        """Monitor memory usage for security"""
        process = psutil.Process()
        memory_usage = process.memory_info().rss
        return memory_usage < SECURITY_CONFIG['max_memory_usage']
    
    def validate_url(self, url: str) -> bool:
        """Validate URL against whitelist and security checks"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check domain whitelist
            if not any(allowed in domain for allowed in SECURITY_CONFIG['allowed_domains']):
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'javascript:', 'data:', 'file:', 'ftp:',
                '../', '..\\', '%2e%2e', 'localhost', '127.0.0.1'
            ]
            
            if any(pattern in url.lower() for pattern in suspicious_patterns):
                return False
            
            # Validate IP addresses
            try:
                ip = ipaddress.ip_address(domain)
                if ip.is_private or ip.is_loopback or ip.is_multicast:
                    return False
            except ValueError:
                pass  # Not an IP address, continue validation
            
            return True
        except Exception:
            return False

class EncryptedFileHandler(logging.FileHandler):
    """Custom logging handler with encryption"""
    
    def __init__(self, filename, encryption_key):
        super().__init__(filename)
        self.encryption_key = encryption_key
    
    def emit(self, record):
        try:
            msg = self.format(record)
            encrypted_msg = self.encryption_key.encrypt(msg.encode())
            
            with open(self.baseFilename, 'ab') as f:
                f.write(base64.b64encode(encrypted_msg) + b'\n')
        except Exception:
            self.handleError(record)

class NetworkSecurityMonitor:
    """Network traffic monitoring and anomaly detection"""
    
    def __init__(self):
        self.request_times = []
        self.failed_requests = 0
        self.suspicious_activity = False
    
    def log_request(self, url: str, response_time: float, status_code: int):
        """Log network request for monitoring"""
        self.request_times.append({
            'url': hashlib.sha256(url.encode()).hexdigest()[:16],  # Hash for privacy
            'time': datetime.now(),
            'response_time': response_time,
            'status': status_code
        })
        
        if status_code >= 400:
            self.failed_requests += 1
        
        # Clean old entries
        cutoff = datetime.now() - timedelta(hours=1)
        self.request_times = [r for r in self.request_times if r['time'] > cutoff]
    
    def detect_anomalies(self) -> bool:
        """Detect suspicious network patterns"""
        recent_requests = len(self.request_times)
        
        # Too many requests in short time
        if recent_requests > SECURITY_CONFIG['rate_limits']['requests_per_hour']:
            return True
        
        # High failure rate
        if self.failed_requests > 10:
            return True
        
        return False

class ThreatDetector:
    """Real-time threat detection and response"""
    
    def __init__(self):
        self.threat_indicators = {
            'malicious_patterns': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'onload\s*=',
                r'onerror\s*=',
                r'eval\s*\(',
                r'document\.cookie',
                r'window\.location'
            ],
            'suspicious_strings': [
                'rat', 'trojan', 'backdoor', 'keylogger', 'rootkit',
                'botnet', 'c2', 'command and control', 'payload',
                'shellcode', 'exploit kit', 'zero day'
            ]
        }
        self.quarantine_dir = 'quarantine'
        os.makedirs(self.quarantine_dir, exist_ok=True)
    
    def scan_content(self, content: str) -> Tuple[bool, List[str]]:
        """Scan content for threats"""
        threats_found = []
        
        # Check for malicious patterns
        for pattern in self.threat_indicators['malicious_patterns']:
            if re.search(pattern, content, re.IGNORECASE):
                threats_found.append(f"Malicious pattern: {pattern}")
        
        # Check for suspicious strings
        content_lower = content.lower()
        for suspicious in self.threat_indicators['suspicious_strings']:
            if suspicious in content_lower:
                threats_found.append(f"Suspicious content: {suspicious}")
        
        # Buffer overflow protection
        if len(content) > SECURITY_CONFIG['max_file_size']:
            threats_found.append("Content size exceeds security limits")
        
        return len(threats_found) == 0, threats_found
    
    def quarantine_content(self, content: str, reason: str) -> str:
        """Quarantine suspicious content"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"quarantined_{timestamp}.txt"
        filepath = os.path.join(self.quarantine_dir, filename)
        
        quarantine_data = {
            'timestamp': timestamp,
            'reason': reason,
            'content_hash': hashlib.sha256(content.encode()).hexdigest(),
            'content': base64.b64encode(content.encode()).decode()
        }
        
        with open(filepath, 'w') as f:
            json.dump(quarantine_data, f, indent=2)
        
        return filepath

class StealthScraper:
    """Stealth web scraping with advanced evasion techniques"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.session = requests.Session()
        self.user_agents = self._load_user_agents()
        self.proxies = self._setup_proxy_rotation()
        self.setup_session()
    
    def _load_user_agents(self) -> List[str]:
        """Load realistic user agent strings"""
        return [
            user_agent.generate_user_agent(),
            user_agent.generate_user_agent(device_type='desktop'),
            user_agent.generate_user_agent(os='win'),
            user_agent.generate_user_agent(os='mac'),
            user_agent.generate_user_agent(os='linux')
        ]
    
    def _setup_proxy_rotation(self) -> List[Dict]:
        """Setup proxy rotation (if available)"""
        # This would be configured with actual proxy services
        return []
    
    def setup_session(self):
        """Configure session with security headers"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # SSL/TLS configuration
        self.session.verify = True
        
        # Timeout configuration
        self.session.timeout = (10, 30)  # Connect, read timeout
    
    def randomize_request(self):
        """Randomize request characteristics"""
        # Random user agent
        self.session.headers['User-Agent'] = random.choice(self.user_agents)
        
        # Random delay
        delay = random.uniform(*SECURITY_CONFIG['rate_limits']['delay_between_requests'])
        time.sleep(delay)
    
    def safe_request(self, url: str) -> Optional[requests.Response]:
        """Make secure HTTP request with all protections"""
        try:
            # Validate URL
            if not self.security.validate_url(url):
                raise ValueError(f"URL failed security validation: {url}")
            
            # Randomize request characteristics
            self.randomize_request()
            
            # Make request with timing
            start_time = time.time()
            response = self.session.get(url, stream=True)
            response_time = time.time() - start_time
            
            # Log request for monitoring
            self.security.network_monitor.log_request(url, response_time, response.status_code)
            
            # Check response size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > SECURITY_CONFIG['max_file_size']:
                raise ValueError("Response too large")
            
            # Download with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > SECURITY_CONFIG['max_file_size']:
                    raise ValueError("Response exceeded size limit")
            
            response._content = content
            return response
            
        except Exception as e:
            logging.getLogger('cyberdad_security').error(f"Request failed: {str(e)}")
            return None

def security_decorator(func):
    """Decorator for adding security checks to functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Memory check
        if not args[0].security.check_memory_usage():
            raise MemoryError("Memory usage exceeded security limits")
        
        # Execution time check
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > SECURITY_CONFIG['max_execution_time']:
                raise TimeoutError("Execution time exceeded security limits")
            
            return result
        except Exception as e:
            logging.getLogger('cyberdad_security').error(f"Security violation in {func.__name__}: {str(e)}")
            raise
    
    return wrapper

class UltraSecureCyberDadGenerator:
    """Ultra-secure CTI content generator with zero trust architecture"""
    
    def __init__(self):
        # Initialize security layers
        self.security = SecurityManager()
        self.scraper = StealthScraper(self.security)
        self.threat_detector = ThreatDetector()
        
        # API configuration with encryption
        self.openai_key = self._decrypt_api_key('OPENAI_API_KEY')
        
        # Content tracking with integrity verification
        self.existing_posts = set()
        self.processed_items = set()
        self.content_hashes = {}
        
        # Initialize OpenAI with security
        if self.openai_key:
            openai.api_key = self.openai_key
        
        # CTI feeds with security validation
        self.cti_feeds = {
            'cisa_alerts': 'https://www.cisa.gov/cybersecurity-advisories/rss.xml',
            'nist_nvd': 'https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml',
            'krebs': 'https://krebsonsecurity.com/feed/',
            'threatpost': 'https://threatpost.com/feed/',
            'security_week': 'https://www.securityweek.com/feed/'
        }
        
        # Family keywords for threat relevance
        self.family_keywords = [
            'ring', 'doorbell', 'camera', 'alexa', 'google home', 'smart tv',
            'router', 'wifi', 'iphone', 'android', 'ipad', 'tablet',
            'smart watch', 'fitbit', 'home assistant', 'nest', 'roku',
            'apple tv', 'chromecast', 'xbox', 'playstation', 'nintendo',
            'smart thermostat', 'smart lock', 'baby monitor', 'security camera',
            'home automation', 'iot', 'smart home', 'family sharing',
            'parental controls', 'kids', 'children', 'family', 'home network'
        ]
        
        # Setup self-defense mechanisms
        self.setup_self_defense()
    
    def _decrypt_api_key(self, env_var: str) -> Optional[str]:
        """Securely retrieve and decrypt API key"""
        try:
            encrypted_key = os.getenv(env_var)
            if encrypted_key:
                # In production, implement proper key management
                return encrypted_key
            return None
        except Exception:
            return None
    
    def setup_self_defense(self):
        """Setup self-defense mechanisms"""
        if SECURITY_CONFIG['self_defense_enabled']:
            # Monitor for tampering
            threading.Thread(target=self._integrity_monitor, daemon=True).start()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._emergency_shutdown)
            signal.signal(signal.SIGINT, self._emergency_shutdown)
    
    def _integrity_monitor(self):
        """Continuous integrity monitoring"""
        while True:
            try:
                # Check script integrity
                if not self.security.verify_integrity(__file__):
                    self._emergency_shutdown(signal.SIGTERM, None)
                
                # Check for anomalies
                if self.security.network_monitor.detect_anomalies():
                    logging.getLogger('cyberdad_security').warning("Network anomaly detected")
                
                time.sleep(SECURITY_CONFIG['integrity_check_interval'])
            except Exception:
                break
    
    def _emergency_shutdown(self, signum, frame):
        """Emergency shutdown procedure"""
        logging.getLogger('cyberdad_security').critical("Emergency shutdown initiated")
        
        # Clear sensitive data
        if hasattr(self, 'openai_key'):
            self.openai_key = None
        
        # Secure cleanup
        self._secure_cleanup()
        sys.exit(1)
    
    def _secure_cleanup(self):
        """Secure cleanup of sensitive data"""
        try:
            # Overwrite sensitive variables
            if hasattr(self, 'security'):
                self.security.session_key = b'\x00' * 32
            
            # Clear process memory (simplified)
            import gc
            gc.collect()
            
        except Exception:
            pass
    
    @security_decorator
    def scrape_cti_feeds_secure(self) -> List[Dict]:
        """Securely scrape CTI feeds with all protections"""
        cti_items = []
        
        for source, url in self.cti_feeds.items():
            try:
                # Rate limiting check
                recent_requests = len(self.security.network_monitor.request_times)
                if recent_requests >= SECURITY_CONFIG['rate_limits']['requests_per_minute']:
                    time.sleep(60)  # Wait before continuing
                
                logging.getLogger('cyberdad_security').info(f"Secure scraping: {source}")
                
                # Secure request
                response = self.scraper.safe_request(url)
                if not response or response.status_code != 200:
                    continue
                
                # Content security scan
                is_safe, threats = self.threat_detector.scan_content(response.text)
                if not is_safe:
                    self.threat_detector.quarantine_content(
                        response.text, 
                        f"Threats detected in {source}: {threats}"
                    )
                    continue
                
                # Parse feed securely
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:5]:  # Limit entries
                    content = f"{entry.title} {getattr(entry, 'description', '')}"
                    
                    # Security scan on entry content
                    is_safe, _ = self.threat_detector.scan_content(content)
                    if not is_safe:
                        continue
                    
                    if self.is_family_relevant(content):
                        # Generate content hash for deduplication
                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        if content_hash not in self.content_hashes:
                            self.content_hashes[content_hash] = True
                            
                            item = {
                                'source': source,
                                'title': entry.title,
                                'description': getattr(entry, 'description', ''),
                                'link': getattr(entry, 'link', ''),
                                'published': getattr(entry, 'published', str(datetime.now())),
                                'relevance_score': self.calculate_relevance_score(content),
                                'content_hash': content_hash
                            }
                            cti_items.append(item)
                
                # Respectful delay between sources
                time.sleep(random.uniform(45, 75))
                
            except Exception as e:
                logging.getLogger('cyberdad_security').error(f"Error in secure scraping {source}: {str(e)}")
                continue
        
        # Sort by relevance and return top items
        cti_items.sort(key=lambda x: x['relevance_score'], reverse=True)
        return cti_items[:3]  # Conservative limit
    
    def is_family_relevant(self, content: str) -> bool:
        """Check family relevance with security filtering"""
        content_lower = content.lower()
        
        # Security check first
        is_safe, _ = self.threat_detector.scan_content(content)
        if not is_safe:
            return False
        
        return any(keyword in content_lower for keyword in self.family_keywords)
    
    def calculate_relevance_score(self, content: str) -> int:
        """Calculate relevance score with security considerations"""
        content_lower = content.lower()
        score = 0
        
        for keyword in self.family_keywords:
            if keyword in content_lower:
                score += content_lower.count(keyword) * 2
        
        # Boost score for critical security terms
        critical_terms = ['critical', 'vulnerability', 'patch', 'update', 'security']
        for term in critical_terms:
            if term in content_lower:
                score += 5
        
        return min(score, 100)  # Cap at 100
    
    @security_decorator
    def generate_secure_content(self, content_type: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Generate content with full security validation"""
        try:
            # Content templates (same as before but with additional security)
            templates = {
                'cti_alert': {
                    'prompt': """Convert this cybersecurity alert into a family-friendly blog post.

Technical Alert: {title}
Details: {content}

SECURITY REQUIREMENTS:
- Use only family-safe language
- No technical jargon that could enable attacks
- Focus on protection, not vulnerability details
- Include clear, safe action steps

Write a helpful post (300-500 words) that:
- Explains the issue in simple terms
- Provides 3-5 protection steps
- Includes "Why This Matters" section
- Ends with quick fix instructions
- Maintains calm, educational tone"""
                },
                'quick_tip': {
                    'prompt': """Create a quick cybersecurity tip for families about {topic}.

SECURITY REQUIREMENTS:
- Safe, actionable advice only
- No information that could be misused
- Family-appropriate language

Write a brief tip (150-250 words) with:
- One specific, safe action step
- Clear instructions
- Explanation of benefits"""
                },
                'family_guide': {
                    'prompt': """Create a comprehensive family security guide about {topic}.

SECURITY REQUIREMENTS:
- Comprehensive but safe information
- No details that enable attacks
- Focus on defense and protection

Write an in-depth guide (500-800 words) with:
- Simple explanations
- Complete setup instructions
- Troubleshooting tips
- Recommended tools"""
                }
            }
            
            # Generate content based on type
            if content_type == 'cti_alert' and data:
                device = self.extract_device_safely(data['title'])
                prompt = templates['cti_alert']['prompt'].format(
                    title=data['title'],
                    content=data['description']
                )
                title = f"{device} Users: Security Update Available"
            
            elif content_type == 'quick_tip':
                safe_topics = ['Router Settings', 'Smart TV Privacy', 'iPhone Security', 'Home Network']
                topic = random.choice(safe_topics)
                prompt = templates['quick_tip']['prompt'].format(topic=topic)
                title = f"Quick {topic} Security Check"
            
            elif content_type == 'family_guide':
                safe_guides = ['Password Security', 'Two-Factor Authentication', 'Home Network Setup']
                topic = random.choice(safe_guides)
                prompt = templates['family_guide']['prompt'].format(topic=topic)
                title = f"Complete Family Guide to {topic}"
            
            else:
                return self.generate_fallback_content(content_type)
            
            # Generate with OpenAI if available
            if self.openai_key:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a family cybersecurity expert. Provide helpful, safe advice without technical details that could enable attacks. Focus on protection and education."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.6
                )
                
                content = response.choices[0].message.content
                
                # Security scan generated content
                is_safe, threats = self.threat_detector.scan_content(content)
                if not is_safe:
                    logging.getLogger('cyberdad_security').warning(f"Generated content failed security scan: {threats}")
                    return self.generate_fallback_content(content_type)
                
                return {
                    'title': title,
                    'content': content,
                    'type': content_type,
                    'source_data': data,
                    'security_verified': True
                }
            else:
                return self.generate_fallback_content(content_type)
                
        except Exception as e:
            logging.getLogger('cyberdad_security').error(f"Content generation error: {str(e)}")
            return self.generate_fallback_content(content_type)
    
    def extract_device_safely(self, content: str) -> str:
        """Safely extract device name without exposing vulnerabilities"""
        content_safe = re.sub(r'[<>{}]', '', content.lower())
        
        for keyword in self.family_keywords:
            if keyword in content_safe:
                return keyword.title()
        
        return "Smart Device"
    
    def generate_fallback_content(self, content_type: str) -> Dict:
        """Generate safe fallback content"""
        fallback_titles = {
            'cti_alert': "Important Security Update for Your Devices",
            'quick_tip': "Quick Security Tip for Families",
            'family_guide': "Family Cybersecurity Guide"
        }
        
        fallback_content = """# Keeping Your Family Safe Online

Your family's digital security is important to us. Here are some simple steps to stay protected:

## Quick Security Steps
1. **Keep devices updated** - Enable automatic updates when possible
2. **Use strong passwords** - Consider a family password manager
3. **Enable two-factor authentication** - Add extra security to important accounts
4. **Review privacy settings** - Check settings on all family devices

## Why This Matters
Regular security practices help protect your family's personal information and digital life.

## Simple Action (Takes 2 Minutes)
Check one device today for available security updates. Your family's safety is worth these few minutes.

**Stay Safe, CyberDad** 🛡️
"""
        
        return {
            'title': fallback_titles.get(content_type, "Family Security Tips"),
            'content': fallback_content,
            'type': content_type,
            'source_data': None,
            'security_verified': True,
            'fallback': True
        }
    
    @security_decorator
    def create_secure_jekyll_post(self, post_data: Dict) -> bool:
        """Create Jekyll post with security validation"""
        try:
            # Final security scan
            is_safe, threats = self.threat_detector.scan_content(post_data['content'])
            if not is_safe:
                logging.getLogger('cyberdad_security').error(f"Post content failed final security scan: {threats}")
                return False
            
            # Generate secure filename
            date_str = datetime.now().strftime('%Y-%m-%d')
            title_clean = re.sub(r'[^\w\s-]', '', post_data['title']).strip()
            title_slug = re.sub(r'[-\s]+', '-', title_clean).lower()[:50]  # Limit length
            filename = f"{date_str}-{title_slug}.md"
            
            # Check for duplicates
            if title_slug in self.existing_posts:
                return False
            
            # Create secure front matter
            front_matter = {
                'layout': 'post',
                'title': post_data['title'],
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S +0000'),
                'categories': ['cybersecurity', 'family'],
                'tags': ['family-safety', 'cybersecurity', 'digital-parenting'],
                'excerpt': post_data['content'][:150] + '...',
                'reading_time': f"{max(1, len(post_data['content'].split()) // 200)} min read",
                'author': 'CyberDad',
                'image': '/assets/images/family-cybersecurity.jpg',
                'security_verified': post_data.get('security_verified', False)
            }
            
            # Create full content with security notice
            full_content = f"""---
{yaml.dump(front_matter, default_flow_style=False)}---

{post_data['content']}

---

## 🛡️ Family Cybersecurity Resources

- [Family Password Security Guide](/family-password-guide)
- [Smart Home Security Checklist](/smart-home-security)
- [Kids Online Safety Guide](/kids-online-safety)

**Content Security**: This post has been verified for family safety and security.

**Stay Safe, CyberDad** 👨‍💻🛡️
"""
            
            # Secure file creation
            os.makedirs('_posts', exist_ok=True)
            filepath = os.path.join('_posts', filename)
            
            # Write with atomic operation
            temp_filepath = filepath + '.tmp'
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            # Atomic move
            os.rename(temp_filepath, filepath)
            
            # Verify file integrity
            if self.security.verify_integrity(filepath):
                self.existing_posts.add(title_slug)
                logging.getLogger('cyberdad_security').info(f"Secure post created: {filename}")
                return True
            else:
                os.remove(filepath)
                return False
                
        except Exception as e:
            logging.getLogger('cyberdad_security').error(f"Secure post creation error: {str(e)}")
            return False
    
    def determine_content_type_secure(self) -> str:
        """Securely determine content type based on time and security state"""
        current_hour = datetime.now().hour
        
        # Check for security incidents
        if self.security.network_monitor.detect_anomalies():
            return 'family_guide'  # Safer content during anomalies
        
        if current_hour < 8:
            return 'quick_tip'
        elif 8 <= current_hour < 16:
            return 'cti_alert'
        else:
            return 'family_guide'
    
    @security_decorator
    def run_secure_generation(self) -> bool:
        """Main secure generation pipeline"""
        try:
            logging.getLogger('cyberdad_security').info("Starting secure content generation")
            
            # Pre-flight security checks
            if not self.security.check_memory_usage():
                raise MemoryError("Memory usage too high")
            
            # Load existing posts
            self.load_existing_posts_secure()
            
            # Determine content type
            content_type = self.determine_content_type_secure()
            
            # Scrape CTI feeds if needed
            cti_data = None
            if content_type == 'cti_alert':
                cti_items = self.scrape_cti_feeds_secure()
                if cti_items:
                    cti_data = cti_items[0]
            
            # Generate content
            post_data = self.generate_secure_content(content_type, cti_data)
            
            if post_data and post_data.get('security_verified', False):
                # Create post
                success = self.create_secure_jekyll_post(post_data)
                
                if success:
                    # Log success securely
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'content_type': content_type,
                        'title_hash': hashlib.sha256(post_data['title'].encode()).hexdigest()[:16],
                        'security_verified': True,
                        'success': True
                    }
                    
                    self.log_operation_secure(log_entry)
                    return True
            
            return False
            
        except Exception as e:
            logging.getLogger('cyberdad_security').error(f"Secure generation failed: {str(e)}")
            return False
    
    def load_existing_posts_secure(self):
        """Securely load existing posts"""
        posts_dir = '_posts'
        if os.path.exists(posts_dir):
            for filename in os.listdir(posts_dir):
                if filename.endswith('.md'):
                    # Verify file integrity before processing
                    filepath = os.path.join(posts_dir, filename)
                    if self.security.verify_integrity(filepath):
                        title = filename.replace('.md', '').split('-', 3)[-1] if '-' in filename else filename
                        self.existing_posts.add(title.lower())
    
    def log_operation_secure(self, log_data: Dict):
        """Securely log operations"""
        try:
            os.makedirs('logs', exist_ok=True)
            log_file = f"logs/secure_operations_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Encrypt sensitive log data
            encrypted_data = self.security.encryption_key.encrypt(
                json.dumps(log_data).encode()
            )
            
            with open(log_file, 'ab') as f:
                f.write(base64.b64encode(encrypted_data) + b'\n')
                
        except Exception as e:
            logging.getLogger('cyberdad_security').error(f"Secure logging failed: {str(e)}")

def main():
    """Main execution with security context"""
    try:
        # Initialize secure generator
        generator = UltraSecureCyberDadGenerator()
        
        # Run secure generation
        success = generator.run_secure_generation()
        
        if success:
            print("✅ Secure content generation completed successfully")
            return 0
        else:
            print("❌ Secure content generation failed")
            return 1
            
    except Exception as e:
        print(f"🚨 Critical error in secure generation: {str(e)}")
        return 1
    finally:
        # Secure cleanup
        try:
            if 'generator' in locals():
                generator._secure_cleanup()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
