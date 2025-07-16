#!/usr/bin/env python3
"""
Docker Documentation Ingestion Script for FindersKeepers v2
Focuses on Teams subscription features and Docker Engine on Linux
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

def clone_docker_docs_repository():
    """Clone the Docker documentation repository"""
    print("🔄 Cloning Docker documentation repository...")
    
    temp_dir = tempfile.mkdtemp(prefix="docker_docs_")
    repo_url = "https://github.com/docker/docs.git"
    
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
            
        print(f"✅ Cloned Docker docs to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        print("❌ Git clone timed out")
        return None
    except Exception as e:
        print(f"❌ Git clone error: {e}")
        return None

def find_documentation_files(repo_dir: str) -> List[Path]:
    """Find all Docker documentation files"""
    docs_path = Path(repo_dir)
    
    # Docker docs structure - comprehensive search
    target_dirs = [
        "content",        # Main content directory
        "docs",           # Alternative docs location
        "engine",         # Docker Engine specific
        "desktop",        # Docker Desktop (for comparison)
        "subscription",   # Subscription-related docs
        "billing",        # Billing and subscription
        "admin",          # Admin features
        "enterprise",     # Enterprise features
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
    
    print(f"📄 Found {len(doc_files)} Docker documentation files")
    return doc_files

def classify_content_priority(file_path: Path) -> tuple:
    """Classify content by priority for Teams/Engine features"""
    path_str = str(file_path).lower()
    filename = file_path.name.lower()
    
    # Read content preview for deeper classification
    content_preview = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content_preview = f.read(2000).lower()
    except:
        pass
    
    # Critical: Teams subscription features
    teams_keywords = [
        'team', 'teams', 'subscription', 'billing', 'organization',
        'enterprise', 'admin', 'role', 'permission', 'sso', 'saml',
        'user management', 'access control'
    ]
    
    # High Priority: Docker Engine on Linux
    engine_keywords = [
        'engine', 'linux', 'ubuntu', 'gpu', 'nvidia', 'cuda',
        'runtime', 'daemon', 'containerd', 'runc', 'systemd'
    ]
    
    # Medium Priority: Portainer/GUI alternatives
    gui_keywords = [
        'portainer', 'gui', 'dashboard', 'web interface', 'visual',
        'management', 'monitoring'
    ]
    
    # Check content for priority keywords
    is_teams_related = any(keyword in content_preview or keyword in path_str for keyword in teams_keywords)
    is_engine_related = any(keyword in content_preview or keyword in path_str for keyword in engine_keywords)
    is_gui_related = any(keyword in content_preview or keyword in path_str for keyword in gui_keywords)
    
    # Priority scoring
    if is_teams_related:
        priority = "critical"
        category = "teams"
    elif is_engine_related:
        priority = "high"
        category = "engine"
    elif is_gui_related:
        priority = "medium"
        category = "gui"
    else:
        priority = "normal"
        category = "general"
    
    return priority, category, is_teams_related, is_engine_related, is_gui_related

def ingest_file_to_finderskeepers(file_path: Path, project: str = "docker-docs") -> bool:
    """Ingest a single file into FindersKeepers via API"""
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Classify content
        priority, category, is_teams, is_engine, is_gui = classify_content_priority(file_path)
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/markdown')
            }
            
            # Build comprehensive tags
            tags = ['docker', 'documentation', 'containerization']
            if is_teams:
                tags.extend(['teams', 'subscription', 'enterprise', 'critical'])
            if is_engine:
                tags.extend(['engine', 'linux', 'gpu', 'high-priority'])
            if is_gui:
                tags.extend(['gui', 'portainer', 'management'])
            
            data = {
                'project': project,
                'tags': tags,
                'metadata': json.dumps({
                    'source': 'docker-docs-repo',
                    'file_path': str(file_path),
                    'ingestion_method': 'git_clone',
                    'file_extension': file_path.suffix,
                    'priority': priority,
                    'category': category,
                    'is_teams_related': is_teams,
                    'is_engine_related': is_engine,
                    'is_gui_related': is_gui,
                    'repository': 'https://github.com/docker/docs'
                })
            }
            
            response = requests.post(
                api_url, 
                files=files, 
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                # Priority indicators
                if is_teams:
                    indicator = "🏢"  # Teams/Enterprise
                elif is_engine:
                    indicator = "🚀"  # Engine
                elif is_gui:
                    indicator = "🖥️"   # GUI
                else:
                    indicator = "📄"  # General
                
                print(f"✅ {indicator} Ingested: {file_path.name}")
                return True
            else:
                print(f"❌ Failed to ingest {file_path.name}: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error ingesting {file_path.name}: {e}")
        return False

def main():
    """Main Docker documentation ingestion process"""
    print("🚀 Starting Docker Documentation Ingestion")
    print("=" * 60)
    print("🎯 Priority Focus:")
    print("   🏢 Teams subscription features")
    print("   🚀 Docker Engine on Linux")
    print("   🖥️ Portainer/GUI management")
    print("   🔧 GPU acceleration (NVIDIA)")
    print("🔗 Target: https://docs.docker.com/")
    print("")
    
    # Step 1: Clone repository
    repo_dir = clone_docker_docs_repository()
    if not repo_dir:
        print("❌ Failed to clone Docker docs repository")
        return
    
    try:
        # Step 2: Find documentation files
        doc_files = find_documentation_files(repo_dir)
        
        if not doc_files:
            print("❌ No documentation files found")
            return
        
        # Step 3: Sort files by priority (Teams/Engine first)
        def priority_sort_key(file_path):
            """Sort function to prioritize Teams and Engine content"""
            priority, category, is_teams, is_engine, is_gui = classify_content_priority(file_path)
            
            # Sort order: critical (teams) -> high (engine) -> medium (gui) -> normal
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
        teams_count = 0
        engine_count = 0
        gui_count = 0
        
        print(f"📥 Ingesting {len(doc_files)} files...")
        print("🏢 = Teams/Enterprise | 🚀 = Engine | 🖥️ = GUI | 📄 = General")
        print("")
        
        for i, doc_file in enumerate(doc_files):
            print(f"[{i+1}/{len(doc_files)}] Processing {doc_file.name}...")
            
            # Count categories for final stats
            priority, category, is_teams, is_engine, is_gui = classify_content_priority(doc_file)
            if is_teams:
                teams_count += 1
            if is_engine:
                engine_count += 1
            if is_gui:
                gui_count += 1
            
            if ingest_file_to_finderskeepers(doc_file):
                successful += 1
            else:
                failed += 1
            
            # Rate limiting - don't overwhelm the API
            if i % 10 == 0 and i > 0:
                print("⏳ Rate limiting pause...")
                time.sleep(2)
        
        print("\n" + "=" * 60)
        print(f"📊 DOCKER DOCS INGESTION COMPLETE")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"🏢 Teams/Enterprise docs: {teams_count}")
        print(f"🚀 Docker Engine docs: {engine_count}")
        print(f"🖥️ GUI/Management docs: {gui_count}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        print(f"🎯 Priority coverage: {teams_count + engine_count}/{successful} docs")
        
        # Specific recommendations
        print(f"\n💡 RECOMMENDATIONS FOR YOUR SETUP:")
        print(f"   • Teams subscription features: {teams_count} docs ingested")
        print(f"   • Docker Engine on Linux: {engine_count} docs ingested")
        print(f"   • Alternative to Docker Desktop: {gui_count} GUI-related docs")
        print(f"   • Search for 'GPU', 'NVIDIA', 'Teams' in knowledge base")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()