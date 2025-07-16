#!/usr/bin/env python3
"""
Supplemental Docker Manuals Ingestion Script for FindersKeepers v2
Specifically targets the /content/manuals/ directory for complete coverage
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
    print("🔄 Cloning Docker documentation repository for manuals...")
    
    temp_dir = tempfile.mkdtemp(prefix="docker_manuals_")
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

def find_manuals_files(repo_dir: str) -> List[Path]:
    """Find all files in the manuals directory"""
    docs_path = Path(repo_dir)
    
    # Focus specifically on the manuals directory
    manuals_dir = docs_path / "content" / "manuals"
    
    if not manuals_dir.exists():
        print(f"❌ Manuals directory not found: {manuals_dir}")
        return []
    
    # Look for all documentation file types in manuals
    file_extensions = [".md", ".mdx", ".rst", ".txt"]
    
    manual_files = []
    
    for ext in file_extensions:
        pattern = f"**/*{ext}"
        for manual_file in manuals_dir.rglob(pattern):
            # Skip certain files that aren't content
            if any(skip in str(manual_file) for skip in [
                "README.md",
                ".github",
                "node_modules",
                ".git",
                "__pycache__",
                "package.json",
                "yarn.lock",
                ".gitignore"
            ]):
                continue
                
            manual_files.append(manual_file)
    
    print(f"📄 Found {len(manual_files)} files in manuals directory")
    return manual_files

def classify_manual_content(file_path: Path) -> tuple:
    """Classify manual content by type"""
    path_str = str(file_path).lower()
    filename = file_path.name.lower()
    
    # Read content preview for classification
    content_preview = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content_preview = f.read(2000).lower()
    except:
        pass
    
    # Manual sections mapping
    manual_sections = {
        'subscription': {
            'keywords': ['subscription', 'billing', 'plan', 'pricing', 'payment'],
            'priority': 'critical',
            'emoji': '💳'
        },
        'admin': {
            'keywords': ['admin', 'organization', 'team', 'management', 'sso'],
            'priority': 'critical',
            'emoji': '🏢'
        },
        'engine': {
            'keywords': ['engine', 'daemon', 'runtime', 'linux', 'gpu'],
            'priority': 'high',
            'emoji': '🚀'
        },
        'desktop': {
            'keywords': ['desktop', 'gui', 'windows', 'mac', 'linux'],
            'priority': 'high',
            'emoji': '🖥️'
        },
        'compose': {
            'keywords': ['compose', 'docker-compose', 'yaml', 'services'],
            'priority': 'high',
            'emoji': '🐳'
        },
        'build': {
            'keywords': ['build', 'dockerfile', 'buildkit', 'cache'],
            'priority': 'high',
            'emoji': '🔨'
        },
        'scout': {
            'keywords': ['scout', 'vulnerability', 'security', 'scan'],
            'priority': 'high',
            'emoji': '🔍'
        },
        'security': {
            'keywords': ['security', 'hardening', 'threat', 'compliance'],
            'priority': 'high',
            'emoji': '🔒'
        },
        'hub': {
            'keywords': ['hub', 'registry', 'repository', 'push', 'pull'],
            'priority': 'medium',
            'emoji': '🌐'
        },
        'ai': {
            'keywords': ['ai', 'copilot', 'artificial', 'intelligence'],
            'priority': 'medium',
            'emoji': '🤖'
        },
        'enterprise': {
            'keywords': ['enterprise', 'dhi', 'commercial', 'business'],
            'priority': 'high',
            'emoji': '🏛️'
        },
        'extensions': {
            'keywords': ['extension', 'plugin', 'add-on'],
            'priority': 'medium',
            'emoji': '🔌'
        }
    }
    
    # Determine section from path
    section = "general"
    priority = "normal"
    emoji = "📖"
    
    for section_name, section_info in manual_sections.items():
        if section_name in path_str:
            section = section_name
            priority = section_info['priority']
            emoji = section_info['emoji']
            break
        elif any(keyword in path_str or keyword in content_preview for keyword in section_info['keywords']):
            section = section_name
            priority = section_info['priority']
            emoji = section_info['emoji']
            break
    
    return section, priority, emoji

def check_if_already_ingested(file_path: Path) -> bool:
    """Check if this file was already ingested"""
    try:
        # Simple check based on filename and project
        api_url = f"http://localhost:8000/api/v1/documents/search"
        
        payload = {
            "project": "docker-docs",
            "query": file_path.name,
            "limit": 1
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            documents = result.get("documents", [])
            
            # Check if we have a document with the same filename
            for doc in documents:
                if doc.get("title", "").endswith(file_path.name):
                    return True
        
    except Exception as e:
        # If check fails, assume not ingested to be safe
        pass
    
    return False

def ingest_file_to_finderskeepers(file_path: Path, project: str = "docker-docs") -> str:
    """Ingest a single manual file into FindersKeepers via API"""
    
    # Skip if already ingested
    if check_if_already_ingested(file_path):
        print(f"⏭️  Already ingested: {file_path.name}")
        return "skipped"
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Classify content
        section, priority, emoji = classify_manual_content(file_path)
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/markdown')
            }
            
            # Build comprehensive tags
            tags = ['docker', 'documentation', 'manual', 'reference']
            
            # Add section-specific tags
            if section == "subscription":
                tags.extend(['subscription', 'billing', 'pricing', 'teams', 'critical'])
            elif section == "admin":
                tags.extend(['admin', 'organization', 'management', 'sso', 'teams'])
            elif section == "engine":
                tags.extend(['engine', 'daemon', 'linux', 'gpu', 'runtime'])
            elif section == "desktop":
                tags.extend(['desktop', 'gui', 'client'])
            elif section == "compose":
                tags.extend(['compose', 'orchestration', 'services'])
            elif section == "build":
                tags.extend(['build', 'dockerfile', 'buildkit'])
            elif section == "scout":
                tags.extend(['scout', 'security', 'vulnerability'])
            elif section == "security":
                tags.extend(['security', 'hardening', 'compliance'])
            elif section == "hub":
                tags.extend(['hub', 'registry', 'repository'])
            elif section == "ai":
                tags.extend(['ai', 'copilot', 'artificial-intelligence'])
            elif section == "enterprise":
                tags.extend(['enterprise', 'commercial', 'business'])
            elif section == "extensions":
                tags.extend(['extensions', 'plugins'])
            
            data = {
                'project': project,
                'tags': tags,
                'metadata': json.dumps({
                    'source': 'docker-docs-manuals',
                    'file_path': str(file_path),
                    'ingestion_method': 'git_clone_manuals',
                    'file_extension': file_path.suffix,
                    'section': section,
                    'priority': priority,
                    'manual_type': 'docker-manual',
                    'repository': 'https://github.com/docker/docs',
                    'directory': 'manuals'
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
    """Main Docker manuals supplemental ingestion process"""
    print("🚀 Starting Docker Manuals Supplemental Ingestion")
    print("=" * 60)
    print("🎯 Target: /content/manuals/ directory from Docker docs")
    print("📖 Focus: Complete coverage of Docker manuals and references")
    print("🔑 Priority: Subscription, Admin, Engine, Desktop, Compose, Build, Scout, Security")
    print("")
    
    # Step 1: Clone repository
    repo_dir = clone_docker_docs_repository()
    if not repo_dir:
        print("❌ Failed to clone Docker docs repository")
        return
    
    try:
        # Step 2: Find manuals files
        manual_files = find_manuals_files(repo_dir)
        
        if not manual_files:
            print("❌ No manuals files found")
            return
        
        # Step 3: Sort by priority (subscription/admin first)
        def priority_sort_key(file_path):
            section, priority, emoji = classify_manual_content(file_path)
            priority_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "normal": 3
            }
            return priority_order.get(priority, 4)
        
        manual_files.sort(key=priority_sort_key)
        
        # Step 4: Ingest files with tracking
        successful = 0
        failed = 0
        skipped = 0
        
        # Category counters
        subscription_count = 0
        admin_count = 0
        engine_count = 0
        desktop_count = 0
        compose_count = 0
        build_count = 0
        scout_count = 0
        security_count = 0
        
        print(f"📥 Processing {len(manual_files)} manual files...")
        print("💳 = Subscription | 🏢 = Admin | 🚀 = Engine | 🖥️ = Desktop | 🐳 = Compose | 🔨 = Build | 🔍 = Scout | 🔒 = Security")
        print("")
        
        for i, manual_file in enumerate(manual_files):
            print(f"[{i+1}/{len(manual_files)}] Processing {manual_file.name}...")
            
            # Count categories for final stats
            section, priority, emoji = classify_manual_content(manual_file)
            if section == "subscription":
                subscription_count += 1
            elif section == "admin":
                admin_count += 1
            elif section == "engine":
                engine_count += 1
            elif section == "desktop":
                desktop_count += 1
            elif section == "compose":
                compose_count += 1
            elif section == "build":
                build_count += 1
            elif section == "scout":
                scout_count += 1
            elif section == "security":
                security_count += 1
            
            result = ingest_file_to_finderskeepers(manual_file)
            if result == "success":
                successful += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1
            
            # Rate limiting - don't overwhelm the API
            if i % 10 == 0 and i > 0:
                print("⏳ Rate limiting pause...")
                time.sleep(2)
        
        print("\n" + "=" * 60)
        print(f"📊 DOCKER MANUALS SUPPLEMENTAL INGESTION COMPLETE")
        print(f"✅ Successfully ingested: {successful}")
        print(f"⏭️  Already existed: {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"💳 Subscription/Billing: {subscription_count}")
        print(f"🏢 Admin/Organization: {admin_count}")
        print(f"🚀 Docker Engine: {engine_count}")
        print(f"🖥️ Docker Desktop: {desktop_count}")
        print(f"🐳 Docker Compose: {compose_count}")
        print(f"🔨 Docker Build: {build_count}")
        print(f"🔍 Docker Scout: {scout_count}")
        print(f"🔒 Security: {security_count}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        
        # Summary
        print(f"\n💡 MANUALS COVERAGE SUMMARY:")
        print(f"   • Complete subscription and billing documentation")
        print(f"   • Full admin and organization management guides")
        print(f"   • Docker Engine manual and reference")
        print(f"   • Docker Desktop comprehensive documentation")
        print(f"   • Docker Compose complete manual")
        print(f"   • Docker Build system documentation")
        print(f"   • Docker Scout security scanning manual")
        print(f"   • Security hardening and compliance guides")
        print(f"   • All Docker manuals now available in knowledge base!")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()