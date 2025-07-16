#!/usr/bin/env python3
"""
Supabase Documentation Ingestion Script for FindersKeepers v2
Comprehensive ingestion of Supabase documentation with focus on payments integration
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

def find_supabase_docs_files(repo_dir: str) -> List[Path]:
    """Find all Supabase documentation files"""
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
                        ".next"
                    ]):
                        continue
                    
                    doc_files.append(doc_file)
    
    # Remove duplicates
    doc_files = list(set(doc_files))
    
    print(f"📄 Found {len(doc_files)} Supabase documentation files")
    return doc_files

def classify_supabase_content(file_path: Path) -> tuple:
    """Classify Supabase content by category"""
    path_str = str(file_path).lower()
    filename = file_path.name.lower()
    
    # Read content preview for deeper classification
    content_preview = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content_preview = f.read(2000).lower()
    except:
        pass
    
    # Supabase documentation categories
    categories = {
        'payments': {
            'keywords': ['payment', 'billing', 'stripe', 'subscription', 'invoice', 'checkout', 'pricing'],
            'priority': 'critical',
            'emoji': '💳'
        },
        'auth': {
            'keywords': ['auth', 'authentication', 'login', 'signup', 'oauth', 'jwt', 'session'],
            'priority': 'high',
            'emoji': '🔐'
        },
        'database': {
            'keywords': ['database', 'postgres', 'sql', 'query', 'table', 'rls', 'row level security'],
            'priority': 'high',
            'emoji': '🗄️'
        },
        'realtime': {
            'keywords': ['realtime', 'websocket', 'subscribe', 'broadcast', 'presence'],
            'priority': 'high',
            'emoji': '⚡'
        },
        'storage': {
            'keywords': ['storage', 'bucket', 'file', 'upload', 'download', 'cdn'],
            'priority': 'high',
            'emoji': '📁'
        },
        'edge-functions': {
            'keywords': ['edge function', 'serverless', 'deno', 'webhook', 'api'],
            'priority': 'high',
            'emoji': '⚙️'
        },
        'api': {
            'keywords': ['api', 'rest', 'graphql', 'endpoint', 'client', 'sdk'],
            'priority': 'high',
            'emoji': '🔗'
        },
        'cli': {
            'keywords': ['cli', 'command', 'terminal', 'supabase init', 'migration'],
            'priority': 'medium',
            'emoji': '⚡'
        },
        'integrations': {
            'keywords': ['integration', 'third party', 'webhook', 'external'],
            'priority': 'medium',
            'emoji': '🔌'
        },
        'deployment': {
            'keywords': ['deploy', 'hosting', 'production', 'self-hosted'],
            'priority': 'medium',
            'emoji': '🚀'
        }
    }
    
    # Determine category
    category = "general"
    priority = "normal"
    emoji = "📖"
    
    for cat_name, cat_info in categories.items():
        if any(keyword in path_str or keyword in content_preview for keyword in cat_info['keywords']):
            category = cat_name
            priority = cat_info['priority']
            emoji = cat_info['emoji']
            break
    
    return category, priority, emoji

def check_if_already_ingested(file_path: Path) -> bool:
    """Check if this file was already ingested"""
    try:
        # Create a hash of the file content to check for duplicates
        with open(file_path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Check if we have this content hash
        api_url = f"http://localhost:8000/api/v1/documents/search"
        
        payload = {
            "project": "supabase-docs",
            "query": content_hash,
            "limit": 1
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            documents = result.get("documents", [])
            
            # Check if we have a document with the same content hash
            for doc in documents:
                if content_hash in doc.get("content", ""):
                    return True
        
    except Exception as e:
        # If check fails, assume not ingested to be safe
        pass
    
    return False

def ingest_file_to_finderskeepers(file_path: Path, project: str = "supabase-docs") -> str:
    """Ingest a single Supabase file into FindersKeepers via API"""
    
    # Skip if already ingested
    if check_if_already_ingested(file_path):
        print(f"⏭️  Already ingested: {file_path.name}")
        return "skipped"
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Classify content
        category, priority, emoji = classify_supabase_content(file_path)
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/markdown')
            }
            
            # Build comprehensive tags
            tags = ['supabase', 'documentation', 'database', 'backend']
            
            # Add category-specific tags
            if category == "payments":
                tags.extend(['payments', 'billing', 'stripe', 'subscription', 'critical'])
            elif category == "auth":
                tags.extend(['authentication', 'auth', 'jwt', 'oauth', 'security'])
            elif category == "database":
                tags.extend(['postgres', 'sql', 'rls', 'database'])
            elif category == "realtime":
                tags.extend(['realtime', 'websocket', 'subscription'])
            elif category == "storage":
                tags.extend(['storage', 'files', 'upload', 'cdn'])
            elif category == "edge-functions":
                tags.extend(['serverless', 'edge-functions', 'api'])
            elif category == "api":
                tags.extend(['api', 'rest', 'graphql', 'client'])
            elif category == "cli":
                tags.extend(['cli', 'command-line', 'migration'])
            elif category == "integrations":
                tags.extend(['integration', 'third-party', 'webhook'])
            elif category == "deployment":
                tags.extend(['deployment', 'hosting', 'production'])
            
            data = {
                'project': project,
                'tags': tags,
                'metadata': json.dumps({
                    'source': 'supabase-docs-repo',
                    'file_path': str(file_path),
                    'ingestion_method': 'git_clone_supabase',
                    'file_extension': file_path.suffix,
                    'category': category,
                    'priority': priority,
                    'repository': 'https://github.com/supabase/supabase',
                    'doc_type': 'supabase-documentation'
                })
            }
            
            response = requests.post(
                api_url, 
                files=files, 
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                print(f"✅ {emoji} Ingested: {file_path.name}")
                return "success"
            else:
                print(f"❌ Failed to ingest {file_path.name}: {response.status_code}")
                return "failed"
                
    except Exception as e:
        print(f"❌ Error ingesting {file_path.name}: {e}")
        return "failed"

def main():
    """Main Supabase documentation ingestion process"""
    print("🚀 Starting Supabase Documentation Ingestion")
    print("=" * 60)
    print("🎯 Target: Complete Supabase documentation")
    print("💳 Priority: Payments, Auth, Database, Realtime, Storage")
    print("🔗 Source: https://supabase.com/docs")
    print("")
    
    # Step 1: Clone repository
    repo_dir = clone_supabase_docs_repository()
    if not repo_dir:
        print("❌ Failed to clone Supabase docs repository")
        return
    
    try:
        # Step 2: Find documentation files
        doc_files = find_supabase_docs_files(repo_dir)
        
        if not doc_files:
            print("❌ No Supabase documentation files found")
            return
        
        # Step 3: Sort by priority (payments first)
        def priority_sort_key(file_path):
            category, priority, emoji = classify_supabase_content(file_path)
            priority_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "normal": 3
            }
            return priority_order.get(priority, 4)
        
        doc_files.sort(key=priority_sort_key)
        
        # Step 4: Ingest files with tracking
        successful = 0
        failed = 0
        skipped = 0
        
        # Category counters
        payments_count = 0
        auth_count = 0
        database_count = 0
        realtime_count = 0
        storage_count = 0
        edge_functions_count = 0
        api_count = 0
        cli_count = 0
        integrations_count = 0
        deployment_count = 0
        
        print(f"📥 Processing {len(doc_files)} Supabase documentation files...")
        print("💳 = Payments | 🔐 = Auth | 🗄️ = Database | ⚡ = Realtime | 📁 = Storage | ⚙️ = Edge Functions")
        print("")
        
        for i, doc_file in enumerate(doc_files):
            print(f"[{i+1}/{len(doc_files)}] Processing {doc_file.name}...")
            
            # Count categories for final stats
            category, priority, emoji = classify_supabase_content(doc_file)
            if category == "payments":
                payments_count += 1
            elif category == "auth":
                auth_count += 1
            elif category == "database":
                database_count += 1
            elif category == "realtime":
                realtime_count += 1
            elif category == "storage":
                storage_count += 1
            elif category == "edge-functions":
                edge_functions_count += 1
            elif category == "api":
                api_count += 1
            elif category == "cli":
                cli_count += 1
            elif category == "integrations":
                integrations_count += 1
            elif category == "deployment":
                deployment_count += 1
            
            result = ingest_file_to_finderskeepers(doc_file)
            if result == "success":
                successful += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1
            
            # Rate limiting
            if i % 10 == 0 and i > 0:
                print("⏳ Rate limiting pause...")
                time.sleep(3)
        
        print("\n" + "=" * 60)
        print(f"📊 SUPABASE DOCUMENTATION INGESTION COMPLETE")
        print(f"✅ Successfully ingested: {successful}")
        print(f"⏭️  Already existed: {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"💳 Payments/Billing: {payments_count}")
        print(f"🔐 Authentication: {auth_count}")
        print(f"🗄️ Database: {database_count}")
        print(f"⚡ Realtime: {realtime_count}")
        print(f"📁 Storage: {storage_count}")
        print(f"⚙️ Edge Functions: {edge_functions_count}")
        print(f"🔗 API: {api_count}")
        print(f"⚡ CLI: {cli_count}")
        print(f"🔌 Integrations: {integrations_count}")
        print(f"🚀 Deployment: {deployment_count}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        
        # Summary
        print(f"\n💡 SUPABASE COVERAGE SUMMARY:")
        print(f"   • Complete payments and billing integration docs")
        print(f"   • Authentication and authorization guides")
        print(f"   • Database and SQL reference")
        print(f"   • Realtime subscriptions and websockets")
        print(f"   • File storage and CDN")
        print(f"   • Edge functions and serverless")
        print(f"   • API reference and SDKs")
        print(f"   • CLI tools and migrations")
        print(f"   • Third-party integrations")
        print(f"   • Deployment and hosting")
        print(f"   • Ready for heavy Supabase usage! 🚀")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()