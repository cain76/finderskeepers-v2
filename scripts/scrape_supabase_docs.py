#!/usr/bin/env python3
"""
Supabase Documentation Scraper
Scrapes all Supabase documentation pages and saves them as markdown files.
"""

import asyncio
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse, urljoin
import aiohttp
import aiofiles

# Base URLs and configuration
BASE_URL = "https://supabase.com/docs"
OUTPUT_DIR = "/media/cain/linux_storage/projects/finderskeepers-v2/docs/resources/supabase"
DELAY_BETWEEN_REQUESTS = 2  # seconds - be respectful to the server

# Initial URL list from crawl4ai mapping
INITIAL_URLS = [
    "https://supabase.com/docs",
    "https://supabase.com/docs/guides/storage",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/amazon-rds",
    "https://supabase.com/docs/guides/getting-started/quickstarts/nuxtjs",
    "https://supabase.com/docs/guides/getting-started/quickstarts/refine",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/render",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/heroku",
    "https://supabase.com/docs/guides/getting-started/quickstarts/sveltekit",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/auth0",
    "https://supabase.com/docs/guides/platform",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/vercel-postgres",
    "https://supabase.com/docs/reference/self-hosting-analytics/introduction",
    "https://supabase.com/docs/guides/getting-started/quickstarts/solidjs",
    "https://supabase.com/docs/guides/getting-started/quickstarts/flutter",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/firebase-auth",
    "https://supabase.com/docs/reference/python/introduction",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/mysql",
    "https://supabase.com/docs/reference/swift/introduction",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/neon",
    "https://supabase.com/docs/reference/self-hosting-auth/introduction",
    "https://supabase.com/docs/guides/database/overview",
    "https://supabase.com/docs/guides/self-hosting",
    "https://supabase.com/docs/reference/cli/introduction",
    "https://supabase.com/docs/guides/functions",
    "https://supabase.com/docs/reference/api/introduction",
    "https://supabase.com/docs/reference/dart/introduction",
    "https://supabase.com/docs/guides/getting-started/quickstarts/redwoodjs",
    "https://supabase.com/docs/guides/cron",
    "https://supabase.com/docs/guides/auth",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/mssql",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/postgres",
    "https://supabase.com/docs/guides/ai",
    "https://supabase.com/docs/reference/self-hosting-storage/introduction",
    "https://supabase.com/docs/guides/getting-started/ai-prompts",
    "https://supabase.com/docs/guides/integrations",
    "https://supabase.com/docs/guides/getting-started/quickstarts/nextjs",
    "https://supabase.com/docs/reference/self-hosting-realtime/introduction",
    "https://supabase.com/docs/guides/realtime",
    "https://supabase.com/docs/guides/resources",
    "https://supabase.com/docs/guides/getting-started/quickstarts/kotlin",
    "https://supabase.com/docs/guides/getting-started/quickstarts/vue",
    "https://supabase.com/docs/reference/kotlin/introduction",
    "https://supabase.com/docs/guides/getting-started",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/firestore-data",
    "https://supabase.com/docs/reference/javascript/introduction",
    "https://supabase.com/docs/guides/queues",
    "https://supabase.com/docs/guides/getting-started/quickstarts/reactjs",
    "https://supabase.com/docs/reference/csharp/introduction",
    "https://supabase.com/docs/guides/platform/migrating-to-supabase/firebase-storage"
]

def sanitize_filename(url):
    """Convert URL to a safe filename"""
    # Remove protocol and domain
    path = urlparse(url).path
    if path.startswith('/docs/'):
        path = path[6:]  # Remove '/docs/' prefix
    
    # Replace slashes with dashes and clean up
    filename = path.replace('/', '-').strip('-')
    if not filename:
        filename = 'index'
    
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return f"{filename}.md"

def get_directory_path(url):
    """Get the directory path for organizing files"""
    path = urlparse(url).path
    if path.startswith('/docs/'):
        path = path[6:]  # Remove '/docs/' prefix
    
    parts = path.strip('/').split('/')
    if len(parts) > 1:
        # Create subdirectory structure
        return '/'.join(parts[:-1])
    return ''

async def scrape_page_with_crawl4ai(session, url):
    """Scrape a single page using crawl4ai-like approach"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                
                # Basic HTML to markdown conversion
                # Remove script and style tags
                html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
                html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
                
                # Extract main content (try common selectors)
                import re
                
                # Look for main content areas
                main_content_patterns = [
                    r'<main[^>]*>(.*?)</main>',
                    r'<article[^>]*>(.*?)</article>',
                    r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                    r'<div[^>]*class="[^"]*documentation[^"]*"[^>]*>(.*?)</div>',
                ]
                
                content = html
                for pattern in main_content_patterns:
                    match = re.search(pattern, html, flags=re.DOTALL | re.IGNORECASE)
                    if match:
                        content = match.group(1)
                        break
                
                # Basic HTML to markdown conversion
                content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', content)
                content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', content)
                content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', content)
                content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1', content)
                content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1', content)
                content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1', content)
                
                content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content)
                content = re.sub(r'<br[^>]*/?>', r'\n', content)
                content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content)
                content = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```', content, flags=re.DOTALL)
                
                # Links
                content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', content)
                
                # Lists
                content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', content)
                content = re.sub(r'<ul[^>]*>', '', content)
                content = re.sub(r'</ul>', '', content)
                content = re.sub(r'<ol[^>]*>', '', content)
                content = re.sub(r'</ol>', '', content)
                
                # Remove remaining HTML tags
                content = re.sub(r'<[^>]+>', '', content)
                
                # Clean up whitespace
                content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
                content = content.strip()
                
                return content
                
            else:
                print(f"Failed to fetch {url}: {response.status}")
                return None
                
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

async def scrape_all_pages():
    """Scrape all pages with delays"""
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    connector = aiohttp.TCPConnector(limit=1)  # Limit to 1 connection for politeness
    async with aiohttp.ClientSession(connector=connector) as session:
        
        scraped_count = 0
        for url in INITIAL_URLS:
            print(f"Scraping {scraped_count + 1}/{len(INITIAL_URLS)}: {url}")
            
            # Get content
            content = await scrape_page_with_crawl4ai(session, url)
            
            if content:
                # Determine file path
                dir_path = get_directory_path(url)
                filename = sanitize_filename(url)
                
                if dir_path:
                    full_dir = os.path.join(OUTPUT_DIR, dir_path)
                    os.makedirs(full_dir, exist_ok=True)
                    file_path = os.path.join(full_dir, filename)
                else:
                    file_path = os.path.join(OUTPUT_DIR, filename)
                
                # Add metadata header
                metadata_header = f"""---
title: "{url.split('/')[-1] or 'Supabase Documentation'}"
source_url: "{url}"
scraped_date: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
---

"""
                
                # Save file
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(metadata_header + content)
                
                print(f"  ✓ Saved: {file_path}")
                scraped_count += 1
            else:
                print(f"  ✗ Failed to scrape: {url}")
            
            # Be respectful - wait between requests
            if scraped_count < len(INITIAL_URLS):
                print(f"  Waiting {DELAY_BETWEEN_REQUESTS} seconds...")
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
    
    print(f"\n✅ Scraping complete! {scraped_count}/{len(INITIAL_URLS)} pages scraped.")
    print(f"Files saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(scrape_all_pages())