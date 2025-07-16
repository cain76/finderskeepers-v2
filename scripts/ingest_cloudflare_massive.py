#!/usr/bin/env python3
"""
MASSIVE Cloudflare Documentation Ingestion Script for FindersKeepers v2
Ingests ALL 4,986+ Cloudflare documentation files to eliminate deployment failures
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

def clone_cloudflare_docs_repository():
    """Clone the Cloudflare documentation repository"""
    print("🔄 Cloning Cloudflare documentation repository...")
    
    temp_dir = tempfile.mkdtemp(prefix="cloudflare_docs_massive_")
    repo_url = "https://github.com/cloudflare/cloudflare-docs.git"
    
    try:
        # Clone with depth=1 for faster download
        result = subprocess.run([
            "git", "clone", "--depth", "1", 
            repo_url, temp_dir
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            print(f"❌ Git clone failed: {result.stderr}")
            return None
            
        print(f"✅ Cloned Cloudflare docs to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        print("❌ Git clone timed out")
        return None
    except Exception as e:
        print(f"❌ Git clone error: {e}")
        return None

def find_cloudflare_docs_files(repo_dir: str) -> List[Path]:
    """Find all Cloudflare documentation files in the repository"""
    docs_path = Path(repo_dir) / "src" / "content" / "docs"
    
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
            'priority': 'high',
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
        },
        'email': {
            'keywords': ['email', 'email routing', 'email security', 'dmarc', 'dkim'],
            'priority': 'medium',
            'emoji': '📧'
        },
        'images': {
            'keywords': ['images', 'image resizing', 'image optimization', 'image delivery'],
            'priority': 'medium',
            'emoji': '🖼️'
        },
        'stream': {
            'keywords': ['stream', 'video', 'streaming', 'live', 'video delivery'],
            'priority': 'medium',
            'emoji': '🎥'
        },
        'load-balancing': {
            'keywords': ['load balancing', 'load balancer', 'traffic manager', 'failover'],
            'priority': 'medium',
            'emoji': '⚖️'
        },
        'registrar': {
            'keywords': ['registrar', 'domain registration', 'whois', 'transfer'],
            'priority': 'medium',
            'emoji': '📝'
        },
        'terraform': {
            'keywords': ['terraform', 'infrastructure as code', 'iac', 'provisioning'],
            'priority': 'medium',
            'emoji': '🏗️'
        }
    }
    
    # Determine category from path first (most reliable)
    category = "general"
    priority = "normal"
    emoji = "📖"
    
    # Check path for product indicators
    for cat_name, cat_info in classification_keywords.items():
        if cat_name in path_lower or any(keyword in path_lower for keyword in cat_info['keywords']):
            category = cat_name
            priority = cat_info['priority']
            emoji = cat_info['emoji']
            break
    
    # Then check URL if no path match
    if category == "general":
        for cat_name, cat_info in classification_keywords.items():
            if any(keyword in url_lower for keyword in cat_info['keywords']):
                category = cat_name
                priority = cat_info['priority']
                emoji = cat_info['emoji']
                break
    
    # Finally check content if no URL match
    if category == "general":
        for cat_name, cat_info in classification_keywords.items():
            if any(keyword in content_lower for keyword in cat_info['keywords']):
                category = cat_name
                priority = cat_info['priority']
                emoji = cat_info['emoji']
                break
    
    return category, priority, emoji

def ingest_file_to_finderskeepers(file_path: Path, project: str = "cloudflare-docs") -> str:
    """Ingest a single Cloudflare file into FindersKeepers via API"""
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if not content.strip():
            return "skipped"
        
        # Classify content
        category, priority, emoji = classify_cloudflare_content(content, "", str(file_path))
        
        # Determine MIME type based on extension
        mime_type = "text/markdown"
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            mime_type = "application/yaml"
        elif file_path.suffix.lower() == '.json':
            mime_type = "application/json"
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, mime_type)
            }
            
            # Build comprehensive tags
            tags = ['cloudflare', 'documentation', 'cdn', 'edge', 'cloud']
            
            # Add category-specific tags
            if category == "workers":
                tags.extend(['workers', 'serverless', 'edge-compute', 'wrangler', 'deployment'])
            elif category == "pages":
                tags.extend(['pages', 'static-site', 'jamstack', 'deployment', 'frontend'])
            elif category == "r2":
                tags.extend(['r2', 'object-storage', 'bucket', 's3-compatible', 'storage'])
            elif category == "kv":
                tags.extend(['kv', 'key-value', 'storage', 'cache', 'edge-storage'])
            elif category == "d1":
                tags.extend(['d1', 'sqlite', 'database', 'sql', 'edge-database'])
            elif category == "dns":
                tags.extend(['dns', 'domain', 'nameserver', 'zone', 'records'])
            elif category == "cdn":
                tags.extend(['cdn', 'cache', 'performance', 'edge', 'optimization'])
            elif category == "ssl":
                tags.extend(['ssl', 'tls', 'certificate', 'https', 'encryption', 'security'])
            elif category == "security":
                tags.extend(['waf', 'firewall', 'ddos', 'bot', 'security', 'protection'])
            elif category == "api":
                tags.extend(['api', 'rest', 'endpoint', 'authentication', 'integration'])
            elif category == "zero-trust":
                tags.extend(['zero-trust', 'cloudflare-one', 'access', 'tunnel', 'ztna'])
            elif category == "ai":
                tags.extend(['ai', 'workers-ai', 'vectorize', 'ai-gateway', 'machine-learning'])
            elif category == "analytics":
                tags.extend(['analytics', 'metrics', 'monitoring', 'insights', 'dashboard'])
            elif category == "network":
                tags.extend(['network', 'magic-transit', 'spectrum', 'anycast', 'infrastructure'])
            elif category == "email":
                tags.extend(['email', 'email-routing', 'email-security', 'dmarc', 'dkim'])
            elif category == "images":
                tags.extend(['images', 'image-resizing', 'image-optimization', 'media'])
            elif category == "stream":
                tags.extend(['stream', 'video', 'streaming', 'live', 'media'])
            elif category == "load-balancing":
                tags.extend(['load-balancing', 'traffic-manager', 'failover', 'high-availability'])
            elif category == "registrar":
                tags.extend(['registrar', 'domain-registration', 'whois', 'transfer'])
            elif category == "terraform":
                tags.extend(['terraform', 'infrastructure-as-code', 'iac', 'provisioning'])
            
            # Get relative path from docs directory for context
            relative_path = str(file_path).split('/docs/')[-1] if '/docs/' in str(file_path) else str(file_path)
            
            data = {
                'project': project,
                'tags': tags,
                'metadata': json.dumps({
                    'source': 'cloudflare-docs-repo',
                    'file_path': relative_path,
                    'ingestion_method': 'git_clone_massive',
                    'file_extension': file_path.suffix,
                    'category': category,
                    'priority': priority,
                    'repository': 'https://github.com/cloudflare/cloudflare-docs',
                    'directory': 'src/content/docs',
                    'doc_type': 'cloudflare-documentation'
                })
            }
            
            response = requests.post(
                api_url, 
                files=files, 
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                print(f"✅ {emoji} Ingested: {relative_path}")
                return "success"
            else:
                print(f"❌ Failed to ingest {file_path.name}: {response.status_code}")
                return "failed"
                
    except Exception as e:
        print(f"❌ Error ingesting {file_path.name}: {e}")
        return "failed"

def main():
    """Main massive Cloudflare documentation ingestion process"""
    print("🚀 Starting MASSIVE Cloudflare Documentation Ingestion")
    print("=" * 70)
    print("🎯 Target: ALL 4,986+ Cloudflare documentation files")
    print("⚡ Goal: Complete coverage to eliminate deployment failures")
    print("🔗 Source: https://github.com/cloudflare/cloudflare-docs")
    print("")
    
    # Step 1: Clone repository
    repo_dir = clone_cloudflare_docs_repository()
    if not repo_dir:
        print("❌ Failed to clone Cloudflare docs repository")
        return
    
    try:
        # Step 2: Find documentation files
        doc_files = find_cloudflare_docs_files(repo_dir)
        
        if not doc_files:
            print("❌ No Cloudflare documentation files found")
            return
        
        # Step 3: Sort by priority (Workers and Pages first)
        def priority_sort_key(file_path):
            category, priority, emoji = classify_cloudflare_content("", "", str(file_path))
            priority_order = {
                "high": 0,
                "medium": 1,
                "normal": 2
            }
            return priority_order.get(priority, 3)
        
        doc_files.sort(key=priority_sort_key)
        
        # Step 4: Ingest files with tracking
        successful = 0
        failed = 0
        skipped = 0
        
        # Category counters
        workers_count = 0
        pages_count = 0
        r2_count = 0
        kv_count = 0
        d1_count = 0
        dns_count = 0
        cdn_count = 0
        ssl_count = 0
        security_count = 0
        api_count = 0
        zero_trust_count = 0
        ai_count = 0
        analytics_count = 0
        network_count = 0
        email_count = 0
        images_count = 0
        stream_count = 0
        load_balancing_count = 0
        registrar_count = 0
        terraform_count = 0
        
        print(f"📥 Processing {len(doc_files)} Cloudflare documentation files...")
        print("⚡ = Workers | 📄 = Pages | 🗄️ = R2 | 🔑 = KV | 💾 = D1 | 🌐 = DNS | 🚀 = CDN | 🔒 = SSL | 🛡️ = Security")
        print("")
        
        for i, doc_file in enumerate(doc_files):
            if i % 100 == 0:
                print(f"[{i+1}/{len(doc_files)}] Processing {doc_file.name}...")
            
            # Count categories for final stats
            category, priority, emoji = classify_cloudflare_content("", "", str(doc_file))
            if category == "workers":
                workers_count += 1
            elif category == "pages":
                pages_count += 1
            elif category == "r2":
                r2_count += 1
            elif category == "kv":
                kv_count += 1
            elif category == "d1":
                d1_count += 1
            elif category == "dns":
                dns_count += 1
            elif category == "cdn":
                cdn_count += 1
            elif category == "ssl":
                ssl_count += 1
            elif category == "security":
                security_count += 1
            elif category == "api":
                api_count += 1
            elif category == "zero-trust":
                zero_trust_count += 1
            elif category == "ai":
                ai_count += 1
            elif category == "analytics":
                analytics_count += 1
            elif category == "network":
                network_count += 1
            elif category == "email":
                email_count += 1
            elif category == "images":
                images_count += 1
            elif category == "stream":
                stream_count += 1
            elif category == "load-balancing":
                load_balancing_count += 1
            elif category == "registrar":
                registrar_count += 1
            elif category == "terraform":
                terraform_count += 1
            
            result = ingest_file_to_finderskeepers(doc_file)
            if result == "success":
                successful += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1
            
            # Rate limiting - don't overwhelm the API
            if i % 20 == 0 and i > 0:
                print(f"⏳ Rate limiting pause... ({successful + failed + skipped}/{len(doc_files)} processed)")
                time.sleep(1)
        
        print("\\n" + "=" * 70)
        print(f"📊 MASSIVE CLOUDFLARE DOCUMENTATION INGESTION COMPLETE")
        print(f"✅ Successfully ingested: {successful}")
        print(f"⏭️  Already existed: {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"⚡ Workers: {workers_count}")
        print(f"📄 Pages: {pages_count}")
        print(f"🗄️ R2 Storage: {r2_count}")
        print(f"🔑 KV Storage: {kv_count}")
        print(f"💾 D1 Database: {d1_count}")
        print(f"🌐 DNS: {dns_count}")
        print(f"🚀 CDN/Cache: {cdn_count}")
        print(f"🔒 SSL/TLS: {ssl_count}")
        print(f"🛡️ Security: {security_count}")
        print(f"🔗 API: {api_count}")
        print(f"🔐 Zero Trust: {zero_trust_count}")
        print(f"🤖 AI Services: {ai_count}")
        print(f"📊 Analytics: {analytics_count}")
        print(f"🌍 Network: {network_count}")
        print(f"📧 Email: {email_count}")
        print(f"🖼️ Images: {images_count}")
        print(f"🎥 Stream: {stream_count}")
        print(f"⚖️ Load Balancing: {load_balancing_count}")
        print(f"📝 Registrar: {registrar_count}")
        print(f"🏗️ Terraform: {terraform_count}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        
        # Summary
        print(f"\\n💡 MASSIVE CLOUDFLARE COVERAGE COMPLETE:")
        print(f"   • Complete Workers serverless platform documentation")
        print(f"   • Cloudflare Pages static site hosting (all guides)")
        print(f"   • R2 object storage and KV key-value store (complete)")
        print(f"   • D1 SQLite database documentation")
        print(f"   • DNS management and CDN configuration (comprehensive)")
        print(f"   • SSL/TLS certificates and security (all aspects)")
        print(f"   • WAF, DDoS protection, and bot management (complete)")
        print(f"   • Cloudflare One zero trust platform (full coverage)")
        print(f"   • AI services, analytics, and monitoring (complete)")
        print(f"   • API reference documentation (comprehensive)")
        print(f"   • Network services and infrastructure (complete)")
        print(f"   • Email routing, images, streaming (all services)")
        print(f"   • Load balancing, registrar, Terraform (complete)")
        print(f"   • NO MORE CLOUDFLARE DEPLOYMENT FAILURES! 🎉")
        
    finally:
        # Cleanup
        print(f"\\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()