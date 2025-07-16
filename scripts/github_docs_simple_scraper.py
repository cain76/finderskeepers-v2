#!/usr/bin/env python3
"""
Simple GitHub Documentation Scraper 
Uses urllib and basic HTML parsing to avoid external dependencies
"""

import os
import re
import time
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Configuration
OUTPUT_DIR = Path("/media/cain/linux_storage/projects/finderskeepers-v2/docs/resources/github")
DELAY_BETWEEN_REQUESTS = 3  # Respectful delay to avoid rate limiting

def create_file_path(url):
    """Create a file path from URL"""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    
    # Remove 'en/' prefix if present
    if path.startswith('en/'):
        path = path[3:]
    
    # Handle root URL
    if not path:
        path = 'index'
    
    # Replace slashes with underscores and ensure .md extension
    filename = path.replace('/', '_') + '.md'
    
    # Clean filename
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    
    return OUTPUT_DIR / filename

def simple_html_to_text(html_content):
    """Basic HTML to text conversion"""
    # Remove script and style elements
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html_content)
    
    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

def scrape_url(url):
    """Scrape a single URL and return the content"""
    try:
        # Add headers to look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        request = Request(url, headers=headers)
        
        print(f"Scraping: {url}")
        
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                print(f"  ✗ HTTP {response.status}")
                return None
                
            content = response.read()
            if response.headers.get('content-encoding') == 'gzip':
                import gzip
                content = gzip.decompress(content)
            
            html_content = content.decode('utf-8', errors='ignore')
            
            # Extract title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            title = title_match.group(1).strip() if title_match else url.split('/')[-1]
            title = re.sub(r'\s+', ' ', title)
            
            # Convert to text
            text_content = simple_html_to_text(html_content)
            
            return {
                'title': title,
                'content': text_content,
                'url': url
            }
            
    except HTTPError as e:
        if e.code == 429:
            print(f"  ✗ Rate limited (429) - will retry with longer delay")
            time.sleep(10)  # Wait longer for rate limit
            return 'retry'
        else:
            print(f"  ✗ HTTP Error {e.code}: {e.reason}")
            return None
    except URLError as e:
        print(f"  ✗ URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def save_content(url, content_data):
    """Save scraped content to markdown file"""
    if not content_data:
        return False
    
    file_path = create_file_path(url)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    markdown_content = f"""# {content_data['title']}

**Source:** {content_data['url']}  
**Scraped:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

{content_data['content']}
"""
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"  ✓ Saved: {file_path}")
        return True
    except Exception as e:
        print(f"  ✗ Save error: {e}")
        return False

def main():
    """Main execution function"""
    urls = [
        "https://docs.github.com/en",
        "https://docs.github.com/en/get-started",
        "https://docs.github.com/en/repositories", 
        "https://docs.github.com/en/actions",
        "https://docs.github.com/en/codespaces",
        "https://docs.github.com/en/copilot",
        "https://docs.github.com/en/issues",
        "https://docs.github.com/en/pull-requests",
        "https://docs.github.com/en/discussions",
        "https://docs.github.com/en/account-and-profile",
        "https://docs.github.com/en/authentication",
        "https://docs.github.com/en/organizations",
        "https://docs.github.com/en/code-security",
        "https://docs.github.com/en/packages",
        "https://docs.github.com/en/pages",
        "https://docs.github.com/en/communities",
        "https://docs.github.com/en/webhooks",
        "https://docs.github.com/en/apps",
        "https://docs.github.com/en/rest",
        "https://docs.github.com/en/graphql",
        "https://docs.github.com/en/github-cli",
        "https://docs.github.com/en/desktop",
        "https://docs.github.com/en/migrations",
        "https://docs.github.com/en/billing",
        "https://docs.github.com/en/education",
        "https://docs.github.com/en/site-policy",
        "https://docs.github.com/en/support",
        "https://docs.github.com/en/search-github",
        "https://docs.github.com/en/sponsors",
        "https://docs.github.com/en/github-models",
    ]
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    failed_count = 0
    
    print(f"Starting to scrape {len(urls)} GitHub documentation pages...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}]", end=' ')
        
        # Scrape with retry for rate limiting
        max_retries = 3
        for retry in range(max_retries):
            content = scrape_url(url)
            
            if content == 'retry':
                if retry < max_retries - 1:
                    print(f"  Retrying ({retry + 2}/{max_retries})...")
                    continue
                else:
                    print(f"  ✗ Failed after {max_retries} attempts")
                    failed_count += 1
                    break
            elif content:
                if save_content(url, content):
                    success_count += 1
                else:
                    failed_count += 1
                break
            else:
                failed_count += 1
                break
        
        # Respectful delay between requests
        if i < len(urls):  # Don't delay after the last request
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    print(f"\nScraping completed!")
    print(f"✓ Successfully scraped: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"Files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()