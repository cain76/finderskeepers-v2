#!/usr/bin/env python3
"""
Comprehensive GitHub Documentation Scraper using crawl4ai

This script discovers and scrapes all GitHub documentation pages
and saves them as markdown files in the docs/resources/github directory.
"""

import os
import re
import time
import asyncio
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://docs.github.com/en"
OUTPUT_DIR = Path("/media/cain/linux_storage/projects/finderskeepers-v2/docs/resources/github")
MAX_PAGES = 2000  # Reasonable limit to prevent infinite scraping
DELAY_BETWEEN_REQUESTS = 1  # Respectful delay

class GitHubDocsScraper:
    def __init__(self):
        self.visited_urls = set()
        self.failed_urls = set()
        self.all_urls = set()
        
    def discover_urls_from_sitemap(self):
        """Attempt to discover URLs from GitHub docs sitemap if available"""
        sitemap_urls = [
            "https://docs.github.com/sitemap.xml",
            "https://docs.github.com/sitemaps/sitemap.xml"
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Found sitemap at {sitemap_url}")
                    # Parse sitemap XML to extract URLs
                    soup = BeautifulSoup(response.content, 'xml')
                    urls = [loc.text for loc in soup.find_all('loc') if '/en/' in loc.text]
                    self.all_urls.update(urls)
                    logger.info(f"Discovered {len(urls)} URLs from sitemap")
                    return True
            except Exception as e:
                logger.warning(f"Could not access sitemap {sitemap_url}: {e}")
        
        return False
    
    def discover_urls_recursively(self, start_url, max_depth=3, current_depth=0):
        """Recursively discover URLs by following links"""
        if current_depth >= max_depth or start_url in self.visited_urls:
            return
            
        if len(self.all_urls) >= MAX_PAGES:
            logger.info(f"Reached maximum page limit of {MAX_PAGES}")
            return
            
        try:
            logger.info(f"Discovering URLs from: {start_url} (depth: {current_depth})")
            response = requests.get(start_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(start_url, href)
                
                # Only include GitHub docs URLs in English
                if (full_url.startswith('https://docs.github.com/en/') and 
                    full_url not in self.visited_urls and
                    '#' not in full_url):  # Skip anchor links
                    self.all_urls.add(full_url)
            
            self.visited_urls.add(start_url)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
            # Recursively visit main category pages
            main_categories = [
                '/get-started', '/repositories', '/actions', '/codespaces', 
                '/copilot', '/issues', '/pull-requests', '/discussions',
                '/account-and-profile', '/authentication', '/organizations',
                '/code-security', '/packages', '/pages', '/communities',
                '/webhooks', '/apps', '/rest', '/graphql', '/github-cli',
                '/desktop', '/migrations', '/billing', '/education'
            ]
            
            for category in main_categories:
                category_url = f"{BASE_URL}{category}"
                if category_url not in self.visited_urls and current_depth < 2:
                    self.discover_urls_recursively(category_url, max_depth, current_depth + 1)
                    
        except Exception as e:
            logger.error(f"Error discovering URLs from {start_url}: {e}")
            self.failed_urls.add(start_url)
    
    def create_file_path(self, url):
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
    
    def scrape_and_save(self, urls):
        """Scrape URLs and save as markdown files"""
        logger.info(f"Starting to scrape {len(urls)} URLs...")
        
        success_count = 0
        failed_count = 0
        
        for i, url in enumerate(urls, 1):
            try:
                logger.info(f"[{i}/{len(urls)}] Scraping: {url}")
                
                # Use requests to get the content
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse with BeautifulSoup to extract main content
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try to find the main content area
                content_selectors = [
                    'main', '.article-body', '.markdown-body', 
                    '[role="main"]', '.content'
                ]
                
                content = None
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        content = content_elem.get_text(separator='\n', strip=True)
                        break
                
                if not content:
                    # Fallback to body content
                    content = soup.get_text(separator='\n', strip=True)
                
                # Create markdown content
                title = soup.find('title')
                title_text = title.get_text() if title else url.split('/')[-1]
                
                markdown_content = f"""# {title_text}

**Source:** {url}

---

{content}
"""
                
                # Save to file
                file_path = self.create_file_path(url)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                success_count += 1
                logger.info(f"✓ Saved: {file_path}")
                
                # Respectful delay
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"✗ Failed to scrape {url}: {e}")
                self.failed_urls.add(url)
        
        logger.info(f"Scraping completed: {success_count} successful, {failed_count} failed")
        
        if self.failed_urls:
            logger.info("Failed URLs:")
            for url in self.failed_urls:
                logger.info(f"  - {url}")
    
    def run(self):
        """Main execution method"""
        logger.info("Starting GitHub Documentation Scraper")
        
        # Create output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Start with initial known URLs
        initial_urls = [
            "https://docs.github.com/en/sponsors",
            "https://docs.github.com/en/migrations", 
            "https://docs.github.com/en/code-security/code-scanning",
            "https://docs.github.com/en/github-models",
            "https://docs.github.com/en/code-security",
            "https://docs.github.com/en/copilot/how-tos/chat/asking-github-copilot-questions-in-github",
            "https://docs.github.com/en/github-cli",
            "https://docs.github.com/en/rest",
            "https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax",
            "https://docs.github.com/en/account-and-profile",
            "https://docs.github.com/en/packages",
            "https://docs.github.com/en/repositories",
            "https://docs.github.com/en/copilot/how-tos/completions/getting-code-suggestions-in-your-ide-with-github-copilot",
            "https://docs.github.com/en/copilot/how-tos/build-copilot-extensions",
            "https://docs.github.com/en/get-started/using-github/github-mobile",
            "https://docs.github.com/en/graphql",
            "https://docs.github.com/en/nonprofit",
            "https://docs.github.com/en/apps",
            "https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent",
            "https://docs.github.com/en/get-started/git-basics/set-up-git",
            "https://docs.github.com/en/support",
            "https://docs.github.com/en/code-security/securing-your-organization",
            "https://docs.github.com/en/pull-requests",
            "https://docs.github.com/en/code-security/secret-scanning",
            "https://docs.github.com/en/copilot/concepts/prompt-engineering-for-copilot-chat",
            "https://docs.github.com/en/code-security/security-advisories",
            "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests",
            "https://docs.github.com/en/site-policy",
            "https://docs.github.com/en/search-github",
            "https://docs.github.com/en/issues",
            "https://docs.github.com/en/code-security/dependabot",
            "https://docs.github.com/en/code-security/supply-chain-security",
            "https://docs.github.com/en/desktop",
            "https://docs.github.com/en/codespaces",
            "https://docs.github.com/en/webhooks",
            "https://docs.github.com/en/communities",
            "https://docs.github.com/en/get-started",
            "https://docs.github.com/en/authentication",
            "https://docs.github.com/en/get-started/git-basics/managing-remote-repositories",
            "https://docs.github.com/en/copilot/tutorials/copilot-chat-cookbook",
            "https://docs.github.com/en/billing",
            "https://docs.github.com/en/education",
            "https://docs.github.com/en/pages",
            "https://docs.github.com/en/actions",
            "https://docs.github.com/en/organizations",
            "https://docs.github.com/en/copilot",
            "https://docs.github.com/en/issues/planning-and-tracking-with-projects",
            "https://docs.github.com/en/authentication/connecting-to-github-with-ssh",
            "https://docs.github.com/en",
            "https://docs.github.com/en/repositories/creating-and-managing-repositories",
            "https://docs.github.com/en/discussions"
        ]
        
        self.all_urls.update(initial_urls)
        
        # Try to discover more URLs from sitemap
        if not self.discover_urls_from_sitemap():
            logger.info("No sitemap found, using recursive discovery...")
            # Discover more URLs recursively
            self.discover_urls_recursively(BASE_URL)
        
        # Filter to only GitHub docs URLs
        github_docs_urls = [url for url in self.all_urls if url.startswith('https://docs.github.com/en/')]
        
        logger.info(f"Total URLs discovered: {len(github_docs_urls)}")
        
        # Scrape and save all URLs
        self.scrape_and_save(github_docs_urls)
        
        logger.info("GitHub Documentation Scraping Complete!")

if __name__ == "__main__":
    scraper = GitHubDocsScraper()
    scraper.run()