#!/usr/bin/env python3
"""
Smart GitHub Documentation Scraper
Uses proper headers, delays, and handles GitHub's anti-bot measures
"""

import requests
import time
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json
import sys
from typing import List, Set
from pathlib import Path

# Add the diary-api to Python path
sys.path.append('/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api')

class SmartGitHubScraper:
    def __init__(self):
        self.session = requests.Session()
        self.visited_urls: Set[str] = set()
        self.setup_session()
        
    def setup_session(self):
        """Setup session with proper headers to avoid bot detection"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
        self.session.headers.update(headers)
        
    def scrape_page(self, url: str) -> dict:
        """Scrape a single GitHub docs page"""
        if url in self.visited_urls:
            return {"success": False, "error": "Already visited"}
            
        try:
            print(f"🕷️ Scraping: {url}")
            
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            self.visited_urls.add(url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = ""
            title_tag = soup.find('h1')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content (GitHub docs structure)
            content = ""
            
            # Try multiple selectors for GitHub docs
            content_selectors = [
                '.markdown-body',
                '.js-wiki-content', 
                '[data-testid="wiki-content"]',
                'article',
                '.content'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text().strip()
                    break
            
            if not content:
                # Fallback to body text
                content = soup.get_text().strip()
            
            # Clean up content
            lines = content.split('\n')
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            content = '\n'.join(cleaned_lines)
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": content,
                "word_count": len(content.split()),
                "status_code": response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed for {url}: {e}")
            return {"success": False, "error": str(e), "url": url}
        except Exception as e:
            print(f"❌ Unexpected error for {url}: {e}")
            return {"success": False, "error": str(e), "url": url}
    
    def ingest_to_finderskeepers(self, scrape_result: dict, project: str = "github-docs") -> bool:
        """Send scraped content to FindersKeepers API"""
        if not scrape_result.get("success") or not scrape_result.get("content"):
            return False
            
        api_url = "http://localhost:8000/api/v1/ingestion/url"
        
        # Create a mock URL request since we already have the content
        payload = {
            "urls": [scrape_result["url"]],
            "project": project,
            "tags": ["github", "documentation", "scraped"],
            "metadata": {
                "scraping_method": "smart_scraper",
                "title": scrape_result.get("title", ""),
                "word_count": scrape_result.get("word_count", 0),
                "status_code": scrape_result.get("status_code", 200)
            }
        }
        
        try:
            response = requests.post(api_url, json=payload, timeout=60)
            if response.status_code == 200:
                print(f"✅ Ingested: {scrape_result['title']}")
                return True
            else:
                print(f"❌ Ingestion failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ingestion error: {e}")
            return False

def main():
    """Main scraping process"""
    
    # Key GitHub documentation URLs to scrape
    github_docs_urls = [
        "https://docs.github.com/en/get-started/quickstart/hello-world",
        "https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-your-membership-in-organizations/about-organization-membership",
        "https://docs.github.com/en/organizations/managing-membership-in-your-organization/adding-people-to-your-organization",
        "https://docs.github.com/en/organizations/managing-membership-in-your-organization/removing-a-member-from-your-organization",
        "https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories",
        "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests",
        "https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues",
        "https://docs.github.com/en/actions/learn-github-actions/understanding-github-actions",
        "https://docs.github.com/en/get-started/quickstart/github-flow",
        "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github",
    ]
    
    scraper = SmartGitHubScraper()
    
    print("🚀 Starting Smart GitHub Documentation Scraping")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, url in enumerate(github_docs_urls):
        print(f"\n[{i+1}/{len(github_docs_urls)}] Processing: {url}")
        
        # Scrape the page
        result = scraper.scrape_page(url)
        
        if result["success"]:
            # Try to ingest into FindersKeepers
            if scraper.ingest_to_finderskeepers(result):
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
            print(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
        
        # Longer delay between requests
        if i < len(github_docs_urls) - 1:
            delay = random.uniform(3, 7)
            print(f"⏳ Waiting {delay:.1f}s before next request...")
            time.sleep(delay)
    
    print("\n" + "=" * 60)
    print(f"📊 SCRAPING COMPLETE")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")

if __name__ == "__main__":
    main()