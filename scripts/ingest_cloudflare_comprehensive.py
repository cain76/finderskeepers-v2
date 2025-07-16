#!/usr/bin/env python3
"""
Comprehensive Cloudflare Documentation Ingestion Script for FindersKeepers v2
Uses multiple methods to get ALL Cloudflare documentation including:
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

# Key Cloudflare documentation sections to scrape
CLOUDFLARE_DOCS_SECTIONS = [
    # Developer Platform - Critical for development
    "https://developers.cloudflare.com/workers/",
    "https://developers.cloudflare.com/pages/",
    "https://developers.cloudflare.com/workers/wrangler/",
    "https://developers.cloudflare.com/workers/runtime-apis/",
    "https://developers.cloudflare.com/workers/tutorials/",
    "https://developers.cloudflare.com/workers/examples/",
    
    # Storage Services
    "https://developers.cloudflare.com/r2/",
    "https://developers.cloudflare.com/workers/runtime-apis/kv/",
    "https://developers.cloudflare.com/d1/",
    "https://developers.cloudflare.com/durable-objects/",
    "https://developers.cloudflare.com/queues/",
    "https://developers.cloudflare.com/images/",
    "https://developers.cloudflare.com/stream/",
    
    # Core Platform
    "https://developers.cloudflare.com/dns/",
    "https://developers.cloudflare.com/cache/",
    "https://developers.cloudflare.com/ssl/",
    "https://developers.cloudflare.com/load-balancing/",
    "https://developers.cloudflare.com/analytics/",
    
    # Security
    "https://developers.cloudflare.com/waf/",
    "https://developers.cloudflare.com/bots/",
    "https://developers.cloudflare.com/ddos-protection/",
    "https://developers.cloudflare.com/firewall/",
    "https://developers.cloudflare.com/ssl/edge-certificates/",
    
    # Cloudflare One (Zero Trust)
    "https://developers.cloudflare.com/cloudflare-one/",
    "https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/",
    "https://developers.cloudflare.com/cloudflare-one/identity/",
    "https://developers.cloudflare.com/cloudflare-one/policies/",
    
    # API Documentation
    "https://developers.cloudflare.com/api/",
    "https://developers.cloudflare.com/api/operations/",
    "https://developers.cloudflare.com/fundamentals/api/",
    
    # AI Services
    "https://developers.cloudflare.com/workers-ai/",
    "https://developers.cloudflare.com/vectorize/",
    "https://developers.cloudflare.com/ai-gateway/",
    
    # Performance & Optimization
    "https://developers.cloudflare.com/speed/",
    "https://developers.cloudflare.com/automatic-platform-optimization/",
    "https://developers.cloudflare.com/argo-smart-routing/",
    "https://developers.cloudflare.com/railgun/",
    
    # Network & Infrastructure
    "https://developers.cloudflare.com/network/",
    "https://developers.cloudflare.com/spectrum/",
    "https://developers.cloudflare.com/magic-transit/",
    "https://developers.cloudflare.com/magic-wan/",
    
    # Fundamentals
    "https://developers.cloudflare.com/fundamentals/",
    "https://developers.cloudflare.com/fundamentals/setup/",
    "https://developers.cloudflare.com/fundamentals/get-started/",
    "https://developers.cloudflare.com/fundamentals/concepts/",
    
    # Tutorials and Learning
    "https://developers.cloudflare.com/learning-paths/",
    "https://developers.cloudflare.com/tutorials/",
    "https://developers.cloudflare.com/reference/",
]

def clone_cloudflare_docs_repository():
    """Clone the Cloudflare documentation repository"""
    print("🔄 Cloning Cloudflare documentation repository...")
    
    temp_dir = tempfile.mkdtemp(prefix="cloudflare_docs_")
    repo_url = "https://github.com/cloudflare/cloudflare-docs.git"
    
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
        
        # Set up sparse checkout for content directories
        os.chdir(temp_dir)
        subprocess.run(["git", "sparse-checkout", "init", "--cone"], check=True)
        subprocess.run(["git", "sparse-checkout", "set", "content"], check=True)
        subprocess.run(["git", "checkout"], check=True)
        
        print(f"✅ Cloned Cloudflare docs to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        print("❌ Git clone timed out")
        return None
    except Exception as e:
        print(f"❌ Git clone error: {e}")
        return None

def scrape_cloudflare_page(url: str) -> Dict[str, Any]:
    """Scrape a single Cloudflare documentation page"""
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
        title_selectors = ['h1', 'title', '[data-testid="page-title"]', '.page-title', '.title']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        # Extract main content from Cloudflare docs structure
        content = ""
        content_selectors = [
            'main[role="main"]',
            '.prose',
            'article',
            '.content',
            '.markdown-body',
            '.documentation-content',
            '.docs-content',
            '.main-content',
            'main'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Remove navigation and non-content elements
                for elem in content_div.select('nav, .sidebar, .navigation, .breadcrumb, .footer, .header, .nav, .menu'):
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
            "title": title or f"Cloudflare Documentation - {url.split('/')[-1]}",
            "content": content,
            "word_count": len(content.split()),
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return {"success": False, "error": str(e), "url": url}

def find_cloudflare_docs_files(repo_dir: str) -> List[Path]:
    """Find all Cloudflare documentation files in the repository"""
    docs_path = Path(repo_dir) / "content"
    
    if not docs_path.exists():
        print(f"❌ Cloudflare docs directory not found: {docs_path}")
        return []
    
    # Look for documentation files
    file_extensions = [".md", ".mdx", ".rst", ".txt"]
    doc_files = []
    
    for ext in file_extensions:
        pattern = f"**/*{ext}"
        for doc_file in docs_path.rglob(pattern):
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
    
    print(f"📄 Found {len(doc_files)} Cloudflare documentation files in repository")
    return doc_files

def classify_cloudflare_content(content: str, source_url: str = "", file_path: str = "") -> tuple:
    """Classify Cloudflare content by category"""
    content_lower = content.lower()
    url_lower = source_url.lower()
    path_lower = file_path.lower()
    
    # Combined classification based on content, URL, and file path
    classification_keywords = {
        'workers': {
            'keywords': ['workers', 'serverless', 'edge compute', 'worker', 'wrangler', 'edge function'],
            'priority': 'critical',
            'emoji': '⚡'
        },
        'pages': {
            'keywords': ['pages', 'static site', 'jamstack', 'deployment', 'frontend'],
            'priority': 'high',
            'emoji': '📄'
        },
        'r2': {
            'keywords': ['r2', 'object storage', 'bucket', 's3 compatible', 'storage'],
            'priority': 'high',
            'emoji': '🗄️'
        },
        'kv': {
            'keywords': ['kv', 'key value', 'key-value', 'storage', 'cache'],
            'priority': 'high',
            'emoji': '🔑'
        },
        'd1': {
            'keywords': ['d1', 'sqlite', 'database', 'sql'],
            'priority': 'high',
            'emoji': '💾'
        },
        'dns': {
            'keywords': ['dns', 'domain', 'nameserver', 'record', 'zone'],
            'priority': 'high',
            'emoji': '🌐'
        },
        'cdn': {
            'keywords': ['cdn', 'cache', 'caching', 'edge', 'performance'],
            'priority': 'high',
            'emoji': '🚀'
        },
        'ssl': {
            'keywords': ['ssl', 'tls', 'certificate', 'https', 'encryption'],
            'priority': 'high',
            'emoji': '🔒'
        },
        'security': {
            'keywords': ['waf', 'firewall', 'ddos', 'bot', 'security', 'protection'],
            'priority': 'high',
            'emoji': '🛡️'
        },
        'api': {
            'keywords': ['api', 'rest', 'endpoint', 'authentication', 'token'],
            'priority': 'high',
            'emoji': '🔗'
        },
        'zero-trust': {
            'keywords': ['zero trust', 'cloudflare one', 'access', 'tunnel', 'ztna'],
            'priority': 'medium',
            'emoji': '🔐'
        },
        'ai': {
            'keywords': ['ai', 'workers ai', 'vectorize', 'ai gateway', 'machine learning'],
            'priority': 'medium',
            'emoji': '🤖'
        },
        'analytics': {
            'keywords': ['analytics', 'metrics', 'monitoring', 'insights', 'dashboard'],
            'priority': 'medium',
            'emoji': '📊'
        },
        'network': {
            'keywords': ['network', 'magic transit', 'magic wan', 'spectrum', 'anycast'],
            'priority': 'medium',
            'emoji': '🌍'
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

def ingest_content_to_finderskeepers(title: str, content: str, source_url: str = "", file_path: str = "", project: str = "cloudflare-docs") -> str:
    """Ingest content into FindersKeepers via API"""
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Classify content
        category, priority, emoji = classify_cloudflare_content(content, source_url, file_path)
        
        # Create a temporary file for the content
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_file.write(content)
        temp_file.close()
        
        try:
            with open(temp_file.name, 'rb') as f:
                files = {
                    'file': (f"{title}.md", f, 'text/markdown')
                }
                
                # Build comprehensive tags
                tags = ['cloudflare', 'documentation', 'cdn', 'edge', 'cloud']
                
                # Add category-specific tags
                if category == "workers":
                    tags.extend(['workers', 'serverless', 'edge-compute', 'wrangler', 'critical'])
                elif category == "pages":
                    tags.extend(['pages', 'static-site', 'jamstack', 'deployment'])
                elif category == "r2":
                    tags.extend(['r2', 'object-storage', 'bucket', 's3-compatible'])
                elif category == "kv":
                    tags.extend(['kv', 'key-value', 'storage', 'cache'])
                elif category == "d1":
                    tags.extend(['d1', 'sqlite', 'database', 'sql'])
                elif category == "dns":
                    tags.extend(['dns', 'domain', 'nameserver', 'zone'])
                elif category == "cdn":
                    tags.extend(['cdn', 'cache', 'performance', 'edge'])
                elif category == "ssl":
                    tags.extend(['ssl', 'tls', 'certificate', 'https', 'encryption'])
                elif category == "security":
                    tags.extend(['waf', 'firewall', 'ddos', 'bot', 'security'])
                elif category == "api":
                    tags.extend(['api', 'rest', 'endpoint', 'authentication'])
                elif category == "zero-trust":
                    tags.extend(['zero-trust', 'cloudflare-one', 'access', 'tunnel'])
                elif category == "ai":
                    tags.extend(['ai', 'workers-ai', 'vectorize', 'ai-gateway'])
                elif category == "analytics":
                    tags.extend(['analytics', 'metrics', 'monitoring', 'insights'])
                elif category == "network":
                    tags.extend(['network', 'magic-transit', 'spectrum', 'anycast'])
                
                data = {
                    'project': project,
                    'tags': tags,
                    'metadata': json.dumps({
                        'source_url': source_url,
                        'file_path': file_path,
                        'category': category,
                        'priority': priority,
                        'ingestion_method': 'comprehensive_cloudflare',
                        'doc_type': 'cloudflare-documentation'
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
    """Main comprehensive Cloudflare documentation ingestion process"""
    print("🚀 Starting Comprehensive Cloudflare Documentation Ingestion")
    print("=" * 70)
    print("🎯 Method 1: GitHub repository cloning")
    print("🕷️ Method 2: Web scraping key sections")
    print("⚡ Priority: Workers, Pages, R2, KV, DNS, CDN, Security, API")
    print("🔗 Target: Complete Cloudflare documentation coverage")
    print("")
    
    successful = 0
    failed = 0
    
    # Method 1: Clone repository and ingest files
    print("=" * 70)
    print("📂 METHOD 1: Repository-based ingestion")
    print("=" * 70)
    
    repo_dir = clone_cloudflare_docs_repository()
    if repo_dir:
        try:
            doc_files = find_cloudflare_docs_files(repo_dir)
            
            for i, doc_file in enumerate(doc_files):
                print(f"[{i+1}/{len(doc_files)}] Processing {doc_file.name}...")
                
                try:
                    with open(doc_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if content.strip():
                        result = ingest_content_to_finderskeepers(
                            title=f"Cloudflare Docs - {doc_file.name}",
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
        future_to_url = {executor.submit(scrape_cloudflare_page, url): url for url in CLOUDFLARE_DOCS_SECTIONS}
        
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
    print(f"📊 COMPREHENSIVE CLOUDFLARE INGESTION COMPLETE")
    print(f"✅ Successfully ingested: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
    
    # Summary
    print(f"\n💡 COMPREHENSIVE CLOUDFLARE COVERAGE:")
    print(f"   • Complete Workers serverless platform docs")
    print(f"   • Cloudflare Pages static site hosting")
    print(f"   • R2 object storage and KV key-value store")
    print(f"   • DNS management and CDN configuration")
    print(f"   • SSL/TLS certificates and security")
    print(f"   • WAF, DDoS protection, and bot management")
    print(f"   • Cloudflare One zero trust platform")
    print(f"   • AI services and analytics")
    print(f"   • Complete API reference documentation")
    print(f"   • Network services and infrastructure")
    print(f"   • Ready for comprehensive Cloudflare development! 🚀")

if __name__ == "__main__":
    main()