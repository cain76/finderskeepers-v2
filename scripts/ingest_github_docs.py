#!/usr/bin/env python3
"""
GitHub Documentation Ingestion Script for FindersKeepers v2
Properly ingests GitHub docs using API and git cloning
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

# Add the diary-api to Python path
sys.path.append('/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api')

def clone_github_docs_repo():
    """Clone the official GitHub docs repository"""
    print("🔄 Cloning GitHub docs repository...")
    
    temp_dir = tempfile.mkdtemp(prefix="github_docs_")
    repo_url = "https://github.com/github/docs.git"
    
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
            
        print(f"✅ Cloned GitHub docs to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        print("❌ Git clone timed out")
        return None
    except Exception as e:
        print(f"❌ Git clone error: {e}")
        return None

def find_markdown_files(repo_dir: str) -> List[Path]:
    """Find all markdown documentation files"""
    docs_path = Path(repo_dir)
    
    # Focus on key documentation directories
    key_dirs = [
        "content",  # Main docs content
        "data",     # Data files
    ]
    
    markdown_files = []
    
    for key_dir in key_dirs:
        search_path = docs_path / key_dir
        if search_path.exists():
            # Find .md files, excluding certain patterns
            for md_file in search_path.rglob("*.md"):
                # Skip certain files
                if any(skip in str(md_file) for skip in [
                    "README.md",
                    ".github",
                    "node_modules",
                    "translations"  # Focus on English docs
                ]):
                    continue
                    
                markdown_files.append(md_file)
    
    print(f"📄 Found {len(markdown_files)} markdown files")
    return markdown_files

def ingest_file_to_finderskeepers(file_path: Path, project: str = "github-docs") -> bool:
    """Ingest a single file into FindersKeepers via API"""
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/markdown')
            }
            
            data = {
                'project': project,
                'tags': ['github', 'documentation', 'official'],
                'metadata': json.dumps({
                    'source': 'github-docs-repo',
                    'file_path': str(file_path),
                    'ingestion_method': 'git_clone'
                })
            }
            
            response = requests.post(
                api_url, 
                files=files, 
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Ingested: {file_path.name}")
                return True
            else:
                print(f"❌ Failed to ingest {file_path.name}: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error ingesting {file_path.name}: {e}")
        return False

def main():
    """Main ingestion process"""
    print("🚀 Starting GitHub Documentation Ingestion")
    print("=" * 50)
    
    # Step 1: Clone repository
    repo_dir = clone_github_docs_repo()
    if not repo_dir:
        print("❌ Failed to clone repository")
        return
    
    try:
        # Step 2: Find markdown files
        markdown_files = find_markdown_files(repo_dir)
        
        if not markdown_files:
            print("❌ No markdown files found")
            return
        
        # Step 3: Ingest files (with rate limiting)
        successful = 0
        failed = 0
        
        print(f"\n📥 Ingesting {len(markdown_files)} files...")
        
        for i, md_file in enumerate(markdown_files):
            print(f"[{i+1}/{len(markdown_files)}] Processing {md_file.name}...")
            
            if ingest_file_to_finderskeepers(md_file):
                successful += 1
            else:
                failed += 1
            
            # Rate limiting - don't overwhelm the API
            if i % 10 == 0 and i > 0:
                print("⏳ Rate limiting pause...")
                time.sleep(2)
        
        print("\n" + "=" * 50)
        print(f"📊 INGESTION COMPLETE")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()