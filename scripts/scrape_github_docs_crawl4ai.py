#!/usr/bin/env python3
"""
GitHub Documentation Scraper using direct URL list and manual batch processing
"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse

# Configuration  
OUTPUT_DIR = Path("/media/cain/linux_storage/projects/finderskeepers-v2/docs/resources/github")

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

def get_github_docs_urls():
    """Return comprehensive list of GitHub docs URLs to scrape"""
    base_urls = [
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
    
    # Add more specific URLs
    specific_urls = [
        "https://docs.github.com/en/get-started/git-basics/set-up-git",
        "https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax",
        "https://docs.github.com/en/get-started/using-github/github-mobile",
        "https://docs.github.com/en/get-started/git-basics/managing-remote-repositories",
        "https://docs.github.com/en/repositories/creating-and-managing-repositories",
        "https://docs.github.com/en/authentication/connecting-to-github-with-ssh",
        "https://docs.github.com/en/copilot/how-tos/completions/getting-code-suggestions-in-your-ide-with-github-copilot",
        "https://docs.github.com/en/copilot/how-tos/chat/asking-github-copilot-questions-in-github",
        "https://docs.github.com/en/copilot/how-tos/build-copilot-extensions",
        "https://docs.github.com/en/copilot/how-tos/agents/copilot-coding-agent",
        "https://docs.github.com/en/copilot/concepts/prompt-engineering-for-copilot-chat",
        "https://docs.github.com/en/copilot/tutorials/copilot-chat-cookbook",
        "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests",
        "https://docs.github.com/en/issues/planning-and-tracking-with-projects", 
        "https://docs.github.com/en/code-security/code-scanning",
        "https://docs.github.com/en/code-security/secret-scanning",
        "https://docs.github.com/en/code-security/security-advisories",
        "https://docs.github.com/en/code-security/dependabot",
        "https://docs.github.com/en/code-security/supply-chain-security",
        "https://docs.github.com/en/code-security/securing-your-organization",
    ]
    
    return base_urls + specific_urls

if __name__ == "__main__":
    urls = get_github_docs_urls()
    print(f"URLs to scrape: {len(urls)}")
    for url in urls:
        print(f"  - {url}")
        print(f"    -> {create_file_path(url)}")