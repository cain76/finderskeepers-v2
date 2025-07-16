#!/usr/bin/env python3
"""
Comprehensive Supabase Documentation Ingestion Script
Uses multiple methods to get ALL Supabase documentation including:
1. GitHub repository docs
2. Web scraping key sections
3. API documentation
"""

import os
import sys
import requests
import subprocess
import tempfile
import shutil
from pathlib import Path
import json
from typing import List, Dict, Any
import time
import hashlib
from urllib.parse import urljoin, urlparse
import concurrent.futures
from bs4 import BeautifulSoup

# Key Supabase documentation sections to scrape
SUPABASE_DOCS_SECTIONS = [
    # Start section
    "https://supabase.com/docs/guides/getting-started",
    "https://supabase.com/docs/guides/quickstart",
    
    # Products
    "https://supabase.com/docs/guides/database",
    "https://supabase.com/docs/guides/auth",
    "https://supabase.com/docs/guides/storage",
    "https://supabase.com/docs/guides/edge-functions",
    "https://supabase.com/docs/guides/realtime",
    "https://supabase.com/docs/guides/ai",
    
    # Build - Critical for development
    "https://supabase.com/docs/guides/cli",
    "https://supabase.com/docs/guides/local-development",
    "https://supabase.com/docs/guides/hosting",
    "https://supabase.com/docs/guides/self-hosting",
    "https://supabase.com/docs/guides/integrations",
    
    # Manage
    "https://supabase.com/docs/guides/platform",
    "https://supabase.com/docs/guides/dashboard",
    "https://supabase.com/docs/guides/database/overview",
    "https://supabase.com/docs/guides/auth/overview",
    
    # Reference - Critical for API usage
    "https://supabase.com/docs/reference/javascript",
    "https://supabase.com/docs/reference/python",
    "https://supabase.com/docs/reference/dart",
    "https://supabase.com/docs/reference/csharp",
    "https://supabase.com/docs/reference/swift",
    "https://supabase.com/docs/reference/kotlin",
    "https://supabase.com/docs/reference/cli",
    "https://supabase.com/docs/reference/api",
    "https://supabase.com/docs/reference/self-hosting-auth",
    "https://supabase.com/docs/reference/self-hosting-storage",
    "https://supabase.com/docs/reference/self-hosting-realtime",
    
    # Resources
    "https://supabase.com/docs/guides/resources",
    "https://supabase.com/docs/guides/examples",
    "https://supabase.com/docs/guides/troubleshooting",
    
    # Payment and billing specific
    "https://supabase.com/docs/guides/platform/pricing",
    "https://supabase.com/docs/guides/platform/billing",
    "https://supabase.com/docs/guides/platform/usage",
    "https://supabase.com/docs/guides/platform/org-based-billing",
    "https://supabase.com/docs/guides/platform/spend-cap",
    "https://supabase.com/docs/guides/platform/quotas",
    
    # Additional critical sections
    "https://supabase.com/docs/guides/database/postgres/configuration",
    "https://supabase.com/docs/guides/database/extensions",
    "https://supabase.com/docs/guides/database/functions",
    "https://supabase.com/docs/guides/database/webhooks",
    "https://supabase.com/docs/guides/auth/social-login",
    "https://supabase.com/docs/guides/auth/phone-login",
    "https://supabase.com/docs/guides/auth/server-side-auth",
    "https://supabase.com/docs/guides/auth/row-level-security",
    "https://supabase.com/docs/guides/storage/uploads",
    "https://supabase.com/docs/guides/storage/cdn",
    "https://supabase.com/docs/guides/edge-functions/quickstart",
    "https://supabase.com/docs/guides/realtime/quickstart",
    "https://supabase.com/docs/guides/ai/quickstart",
]

def clone_supabase_docs_repository():
    """Clone the Supabase documentation repository"""
    print("🔄 Cloning Supabase documentation repository...")
    
    temp_dir = tempfile.mkdtemp(prefix="supabase_docs_")
    repo_url = "https://github.com/supabase/supabase.git"
    
    try:
        # Clone with depth=1 and sparse checkout for docs only
        result = subprocess.run([
            "git", "clone", "--depth", "1", 
            "--filter=blob:none",
            "--no-checkout",
            repo_url, temp_dir
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Git clone failed: {result.stderr}")
            return None
        
        # Set up sparse checkout for docs only
        os.chdir(temp_dir)
        subprocess.run(["git", "sparse-checkout", "init", "--cone"], check=True)
        subprocess.run(["git", "sparse-checkout", "set", "apps/docs"], check=True)
        subprocess.run(["git", "checkout"], check=True)
        
        print(f"✅ Cloned Supabase docs to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        print("❌ Git clone timed out")
        return None
    except Exception as e:
        print(f"❌ Git clone error: {e}")
        return None

def scrape_supabase_page(url: str) -> Dict[str, Any]:
    """Scrape a single Supabase documentation page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print(f"🕷️ Scraping: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = ""
        title_selectors = ['h1', 'title', '[data-testid="page-title"]', '.page-title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        # Extract main content from Supabase docs structure
        content = ""
        content_selectors = [
            'main[role="main"]',
            '.prose',
            'article',
            '[data-testid="docs-content"]',
            '.documentation-content',
            '.markdown-body',
            '.content',
            'main'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Remove navigation and non-content elements
                for elem in content_div.select('nav, .sidebar, .navigation, .breadcrumb, .footer, .header'):
                    elem.decompose()
                
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
            "title": title or f"Supabase Documentation - {url.split('/')[-1]}",
            "content": content,
            "word_count": len(content.split()),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return {"success": False, "error": str(e), "url": url}

def find_supabase_docs_files(repo_dir: str) -> List[Path]:
    """Find all Supabase documentation files in the repository"""
    docs_path = Path(repo_dir) / "apps" / "docs"
    
    if not docs_path.exists():
        print(f"❌ Supabase docs directory not found: {docs_path}")
        return []
    
    # Look for documentation files
    file_extensions = [".md", ".mdx", ".rst", ".txt"]
    doc_files = []
    
    # Focus on key directories
    target_dirs = [
        "content",
        "pages", 
        "docs",
        "guides",
        "reference",
        "spec",
        ".",
    ]
    
    for target_dir in target_dirs:
        search_path = docs_path / target_dir
        if search_path.exists():
            for ext in file_extensions:
                pattern = f"**/*{ext}"
                for doc_file in search_path.rglob(pattern):
                    # Skip certain files
                    if any(skip in str(doc_file) for skip in [
                        "README.md",
                        ".github",
                        "node_modules",
                        ".git",
                        "__pycache__",
                        "package.json",
                        "yarn.lock",
                        ".gitignore",
                        ".next",
                        "test",
                        "spec"
                    ]):
                        continue
                    
                    doc_files.append(doc_file)
    
    # Remove duplicates
    doc_files = list(set(doc_files))
    
    print(f"📄 Found {len(doc_files)} Supabase documentation files in repository")
    return doc_files

def classify_supabase_content(content: str, source_url: str = "", file_path: str = "") -> tuple:
    """Classify Supabase content by category"""
    content_lower = content.lower()
    url_lower = source_url.lower()
    path_lower = file_path.lower()
    
    # Combined classification based on content, URL, and file path
    classification_keywords = {
        'payments': {
            'keywords': ['payment', 'billing', 'stripe', 'subscription', 'invoice', 'checkout', 'pricing', 'plan', 'cost', 'spend cap', 'usage', 'quota'],
            'priority': 'critical',
            'emoji': '💳'
        },
        'auth': {
            'keywords': ['auth', 'authentication', 'login', 'signup', 'oauth', 'jwt', 'session', 'user', 'password', 'social login', 'phone login', 'rls', 'row level security'],
            'priority': 'high',
            'emoji': '🔐'
        },
        'database': {
            'keywords': ['database', 'postgres', 'sql', 'query', 'table', 'schema', 'migration', 'function', 'trigger', 'extension', 'webhook'],
            'priority': 'high',
            'emoji': '🗄️'
        },
        'realtime': {
            'keywords': ['realtime', 'websocket', 'subscribe', 'broadcast', 'presence', 'channel', 'listen'],
            'priority': 'high',
            'emoji': '⚡'
        },
        'storage': {
            'keywords': ['storage', 'bucket', 'file', 'upload', 'download', 'cdn', 'image', 'asset'],
            'priority': 'high',
            'emoji': '📁'
        },
        'edge-functions': {
            'keywords': ['edge function', 'serverless', 'deno', 'function', 'api', 'webhook', 'cors'],
            'priority': 'high',
            'emoji': '⚙️'
        },
        'api': {
            'keywords': ['api', 'rest', 'graphql', 'endpoint', 'client', 'sdk', 'reference', 'javascript', 'python', 'dart', 'swift', 'kotlin'],
            'priority': 'high',
            'emoji': '🔗'
        },
        'cli': {
            'keywords': ['cli', 'command', 'terminal', 'supabase init', 'migration', 'local development', 'deploy'],
            'priority': 'medium',
            'emoji': '💻'
        },
        'platform': {
            'keywords': ['platform', 'dashboard', 'project', 'organization', 'team', 'settings', 'configuration'],
            'priority': 'medium',
            'emoji': '🏗️'
        },
        'integrations': {
            'keywords': ['integration', 'third party', 'webhook', 'external', 'vercel', 'netlify', 'github'],
            'priority': 'medium',
            'emoji': '🔌'
        },
        'ai': {
            'keywords': ['ai', 'artificial intelligence', 'machine learning', 'embedding', 'vector', 'openai'],
            'priority': 'high',
            'emoji': '🤖'
        }
    }
    
    # Determine category
    category = "general"
    priority = "normal"
    emoji = "📖"
    
    # Check URL first for stronger signals
    for cat_name, cat_info in classification_keywords.items():
        if any(keyword in url_lower for keyword in cat_info['keywords']):
            category = cat_name
            priority = cat_info['priority']
            emoji = cat_info['emoji']
            break
    
    # Then check content if no URL match
    if category == "general":
        for cat_name, cat_info in classification_keywords.items():
            if any(keyword in content_lower for keyword in cat_info['keywords']):
                category = cat_name
                priority = cat_info['priority']
                emoji = cat_info['emoji']
                break
    
    return category, priority, emoji

def ingest_content_to_finderskeepers(title: str, content: str, source_url: str = "", file_path: str = "", project: str = "supabase-docs") -> str:
    """Ingest content into FindersKeepers via API"""
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Classify content
        category, priority, emoji = classify_supabase_content(content, source_url, file_path)
        
        # Build comprehensive tags
        tags = ['supabase', 'documentation', 'database', 'backend']
        
        # Add category-specific tags
        if category == "payments":
            tags.extend(['payments', 'billing', 'stripe', 'subscription', 'critical'])
        elif category == "auth":
            tags.extend(['authentication', 'auth', 'jwt', 'oauth', 'security'])
        elif category == "database":
            tags.extend(['postgres', 'sql', 'database', 'schema'])
        elif category == "realtime":
            tags.extend(['realtime', 'websocket', 'subscription'])
        elif category == "storage":
            tags.extend(['storage', 'files', 'upload', 'cdn'])
        elif category == "edge-functions":
            tags.extend(['serverless', 'edge-functions', 'api'])
        elif category == "api":
            tags.extend(['api', 'rest', 'graphql', 'client', 'sdk'])
        elif category == "cli":
            tags.extend(['cli', 'command-line', 'local-development'])
        elif category == "platform":
            tags.extend(['platform', 'dashboard', 'project'])
        elif category == "integrations":
            tags.extend(['integration', 'third-party', 'webhook'])
        elif category == "ai":
            tags.extend(['ai', 'machine-learning', 'vector', 'embedding'])
        
        # Create a temporary file for the content
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_file.write(content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {
                    'file': (f"{title}.md", f, 'text/markdown')
                }
                
                data = {
                    'project': project,
                    'tags': tags,
                    'metadata': json.dumps({
                        'source_url': source_url,
                        'file_path': file_path,
                        'category': category,
                        'priority': priority,
                        'ingestion_method': 'comprehensive_supabase',
                        'doc_type': 'supabase-documentation'
                    })
                }
                
                response = requests.post(api_url, files=files, data=data, timeout=60)
        finally:
            # Clean up temporary file
            os.unlink(temp_file.name)
        
        if response.status_code == 200:
            print(f"✅ {emoji} Ingested: {title}")
            return "success"
        else:
            print(f"❌ Failed to ingest {title}: {response.status_code}")
            return "failed"
            
    except Exception as e:
        print(f"❌ Error ingesting {title}: {e}")
        return "failed"

def main():
    """Main comprehensive Supabase documentation ingestion process"""
    print("🚀 Starting Comprehensive Supabase Documentation Ingestion")
    print("=" * 70)
    print("🎯 Method 1: GitHub repository cloning")
    print("🕷️ Method 2: Web scraping key sections")
    print("💳 Priority: Payments, Auth, Database, Realtime, Storage, Edge Functions, AI")
    print("🔗 Target: Complete Supabase documentation coverage")
    print("")
    
    successful = 0
    failed = 0
    
    # Method 1: Clone repository and ingest files
    print("=" * 70)
    print("📂 METHOD 1: Repository-based ingestion")
    print("=" * 70)
    
    repo_dir = clone_supabase_docs_repository()
    if repo_dir:
        try:
            doc_files = find_supabase_docs_files(repo_dir)
            
            for i, doc_file in enumerate(doc_files):
                print(f"[{i+1}/{len(doc_files)}] Processing {doc_file.name}...")
                
                try:
                    with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if content.strip():
                        result = ingest_content_to_finderskeepers(
                            title=f"Supabase Docs - {doc_file.name}",
                            content=content,
                            file_path=str(doc_file)
                        )
                        
                        if result == "success":
                            successful += 1
                        else:
                            failed += 1
                    
                    # Rate limiting
                    if i % 10 == 0 and i > 0:
                        print("⏳ Rate limiting pause...")
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"❌ Error processing {doc_file.name}: {e}")
                    failed += 1
            
        finally:
            # Cleanup
            print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
            shutil.rmtree(repo_dir, ignore_errors=True)
    
    # Method 2: Web scraping key sections
    print("\n" + "=" * 70)
    print("🕷️ METHOD 2: Web scraping key sections")
    print("=" * 70)
    
    # Scrape key pages with threading for efficiency
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(scrape_supabase_page, url): url for url in SUPABASE_DOCS_SECTIONS}
        
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                scrape_result = future.result()
                
                if scrape_result["success"]:
                    result = ingest_content_to_finderskeepers(
                        title=scrape_result["title"],
                        content=scrape_result["content"],
                        source_url=scrape_result["url"]
                    )
                    
                    if result == "success":
                        successful += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                failed += 1
            
            # Rate limiting
            time.sleep(1)
    
    print("\n" + "=" * 70)
    print(f"📊 COMPREHENSIVE SUPABASE INGESTION COMPLETE")
    print(f"✅ Successfully ingested: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
    
    # Summary
    print(f"\n💡 COMPREHENSIVE SUPABASE COVERAGE:")
    print(f"   • Complete payments and billing integration docs")
    print(f"   • Authentication and authorization (all methods)")
    print(f"   • Database and PostgreSQL reference")
    print(f"   • Realtime subscriptions and websockets")
    print(f"   • File storage and CDN")
    print(f"   • Edge functions and serverless")
    print(f"   • AI and machine learning features")
    print(f"   • API reference for all languages")
    print(f"   • CLI tools and local development")
    print(f"   • Platform management and dashboard")
    print(f"   • Third-party integrations")
    print(f"   • Self-hosting and advanced configuration")
    print(f"   • Ready for heavy Supabase development! 🚀")

if __name__ == "__main__":
    main()