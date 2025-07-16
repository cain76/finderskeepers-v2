#!/usr/bin/env python3
"""
n8n Documentation Ingestion Script for FindersKeepers v2
Based on proven GitHub docs ingestion methodology
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

def clone_n8n_docs_repository():
    """Clone the n8n documentation repository"""
    print("🔄 Cloning n8n documentation repository...")
    
    temp_dir = tempfile.mkdtemp(prefix="n8n_docs_")
    repo_url = "https://github.com/n8n-io/n8n-docs.git"
    
    try:
        # Clone with depth=1 for faster download
        result = subprocess.run([
            "git", "clone", "--depth", "1", 
            "--filter=blob:none",  # Skip large files
            repo_url, temp_dir
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Git clone failed: {result.stderr}")
            return None
            
        print(f"✅ Cloned n8n docs to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        print("❌ Git clone timed out")
        return None
    except Exception as e:
        print(f"❌ Git clone error: {e}")
        return None

def find_documentation_files(repo_dir: str) -> List[Path]:
    """Find all n8n documentation files"""
    docs_path = Path(repo_dir)
    
    # n8n docs structure - look for common documentation directories
    target_dirs = [
        "docs",           # Main docs
        "content",        # Content directory
        "pages",          # Pages
        "src",            # Source content
        ".",              # Root level
    ]
    
    # Look for documentation file types
    file_extensions = [".md", ".mdx", ".rst", ".txt"]
    
    doc_files = []
    
    for target_dir in target_dirs:
        search_path = docs_path / target_dir
        if search_path.exists():
            for ext in file_extensions:
                pattern = f"*{ext}"
                for doc_file in search_path.rglob(pattern):
                    # Skip certain files that aren't content
                    if any(skip in str(doc_file) for skip in [
                        "README.md",
                        ".github",
                        "node_modules",
                        ".git",
                        "__pycache__",
                        ".next",
                        "package.json",
                        "yarn.lock",
                        ".gitignore"
                    ]):
                        continue
                        
                    doc_files.append(doc_file)
    
    # Remove duplicates
    doc_files = list(set(doc_files))
    
    print(f"📄 Found {len(doc_files)} n8n documentation files")
    return doc_files

def ingest_file_to_finderskeepers(file_path: Path, project: str = "n8n-docs") -> bool:
    """Ingest a single file into FindersKeepers via API"""
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/markdown')
            }
            
            # Check if this is self-hosting related content
            content_preview = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as preview_file:
                    content_preview = preview_file.read(1000).lower()
            except:
                pass
            
            is_self_hosting = any(term in content_preview for term in [
                'self-host', 'self host', 'docker', 'installation', 'setup',
                'deployment', 'configuration', 'environment', 'hosting'
            ])
            
            tags = ['n8n', 'documentation', 'workflow', 'automation']
            if is_self_hosting:
                tags.extend(['self-hosting', 'docker', 'deployment', 'critical'])
            
            data = {
                'project': project,
                'tags': tags,
                'metadata': json.dumps({
                    'source': 'n8n-docs-repo',
                    'file_path': str(file_path),
                    'ingestion_method': 'git_clone',
                    'file_extension': file_path.suffix,
                    'is_self_hosting_related': is_self_hosting,
                    'repository': 'https://github.com/n8n-io/n8n-docs'
                })
            }
            
            response = requests.post(
                api_url, 
                files=files, 
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                priority_marker = "🏠" if is_self_hosting else "📄"
                print(f"✅ {priority_marker} Ingested: {file_path.name}")
                return True
            else:
                print(f"❌ Failed to ingest {file_path.name}: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error ingesting {file_path.name}: {e}")
        return False

def main():
    """Main n8n documentation ingestion process"""
    print("🚀 Starting n8n Documentation Ingestion")
    print("=" * 50)
    print("🎯 Priority: Self-hosting and Docker documentation")
    print("🔗 Target: https://docs.n8n.io/")
    print("")
    
    # Step 1: Clone repository
    repo_dir = clone_n8n_docs_repository()
    if not repo_dir:
        print("❌ Failed to clone n8n docs repository")
        return
    
    try:
        # Step 2: Find documentation files
        doc_files = find_documentation_files(repo_dir)
        
        if not doc_files:
            print("❌ No documentation files found")
            return
        
        # Step 3: Sort files to prioritize self-hosting content
        def prioritize_self_hosting(file_path):
            """Sort function to prioritize self-hosting content"""
            path_str = str(file_path).lower()
            filename = file_path.name.lower()
            
            # High priority - self-hosting related
            if any(term in path_str for term in [
                'self-host', 'docker', 'installation', 'setup', 
                'deployment', 'hosting', 'environment'
            ]):
                return 0
            
            # Medium priority - core documentation
            elif any(term in path_str for term in [
                'getting-started', 'quickstart', 'tutorial', 'guide'
            ]):
                return 1
            
            # Normal priority
            else:
                return 2
        
        doc_files.sort(key=prioritize_self_hosting)
        
        # Step 4: Ingest files (with rate limiting)
        successful = 0
        failed = 0
        self_hosting_count = 0
        
        print(f"📥 Ingesting {len(doc_files)} files...")
        print("🏠 = Self-hosting related | 📄 = General documentation")
        print("")
        
        for i, doc_file in enumerate(doc_files):
            print(f"[{i+1}/{len(doc_files)}] Processing {doc_file.name}...")
            
            # Check if it's self-hosting related for counting
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content_preview = f.read(1000).lower()
                    if any(term in content_preview for term in [
                        'self-host', 'docker', 'installation', 'setup',
                        'deployment', 'hosting', 'environment'
                    ]):
                        self_hosting_count += 1
            except:
                pass
            
            if ingest_file_to_finderskeepers(doc_file):
                successful += 1
            else:
                failed += 1
            
            # Rate limiting - don't overwhelm the API
            if i % 10 == 0 and i > 0:
                print("⏳ Rate limiting pause...")
                time.sleep(2)
        
        print("\n" + "=" * 50)
        print(f"📊 N8N DOCS INGESTION COMPLETE")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"🏠 Self-hosting related: {self_hosting_count}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        print(f"🎯 Self-hosting coverage: {self_hosting_count}/{successful} docs")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()