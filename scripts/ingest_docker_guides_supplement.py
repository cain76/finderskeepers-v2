#!/usr/bin/env python3
"""
Supplemental Docker Guides Ingestion Script for FindersKeepers v2
Specifically targets the /content/guides/ directory to ensure complete coverage
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
    print("🔄 Cloning Docker documentation repository for guides...")
    
    temp_dir = tempfile.mkdtemp(prefix="docker_guides_")
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

def find_guides_files(repo_dir: str) -> List[Path]:
    """Find all files in the guides directory"""
    docs_path = Path(repo_dir)
    
    # Focus specifically on the guides directory
    guides_dir = docs_path / "content" / "guides"
    
    if not guides_dir.exists():
        print(f"❌ Guides directory not found: {guides_dir}")
        return []
    
    # Look for all documentation file types in guides
    file_extensions = [".md", ".mdx", ".rst", ".txt"]
    
    guide_files = []
    
    for ext in file_extensions:
        pattern = f"**/*{ext}"
        for guide_file in guides_dir.rglob(pattern):
            # Skip certain files that aren't content
            if any(skip in str(guide_file) for skip in [
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
                
            guide_files.append(guide_file)
    
    print(f"📄 Found {len(guide_files)} files in guides directory")
    return guide_files

def classify_guide_content(file_path: Path) -> tuple:
    """Classify guide content by type"""
    path_str = str(file_path).lower()
    filename = file_path.name.lower()
    
    # Read content preview for classification
    content_preview = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content_preview = f.read(2000).lower()
    except:
        pass
    
    # Language-specific guides
    language_keywords = {
        'python': ['python', 'pip', 'django', 'flask', 'fastapi'],
        'javascript': ['javascript', 'nodejs', 'npm', 'reactjs', 'angular'],
        'java': ['java', 'maven', 'gradle', 'spring', 'jdk'],
        'golang': ['golang', 'go', 'gin', 'fiber'],
        'php': ['php', 'composer', 'laravel', 'symfony'],
        'ruby': ['ruby', 'rails', 'gem', 'bundler'],
        'rust': ['rust', 'cargo', 'tokio'],
        'cpp': ['cpp', 'cmake', 'gcc', 'clang'],
        'dotnet': ['dotnet', 'csharp', 'aspnet', 'nuget'],
        'r': ['r-lang', 'rstudio', 'cran'],
        'deno': ['deno', 'typescript'],
        'bun': ['bun', 'bunjs']
    }
    
    # AI/ML guides
    ai_keywords = ['ai', 'ml', 'tensorflow', 'pytorch', 'jupyter', 'model', 'genai', 'rag', 'ollama']
    
    # Infrastructure guides
    infra_keywords = ['kubernetes', 'k8s', 'docker-compose', 'swarm', 'traefik', 'kafka']
    
    # Admin/Enterprise guides
    admin_keywords = ['admin', 'enterprise', 'sso', 'security', 'management', 'zscaler']
    
    # Determine category
    category = "general"
    language = None
    
    for lang, keywords in language_keywords.items():
        if any(keyword in path_str or keyword in content_preview for keyword in keywords):
            category = "language"
            language = lang
            break
    
    if category == "general":
        if any(keyword in path_str or keyword in content_preview for keyword in ai_keywords):
            category = "ai-ml"
        elif any(keyword in path_str or keyword in content_preview for keyword in infra_keywords):
            category = "infrastructure"
        elif any(keyword in path_str or keyword in content_preview for keyword in admin_keywords):
            category = "admin"
    
    return category, language

def check_if_already_ingested(file_path: Path) -> bool:
    """Check if this file was already ingested"""
    try:
        # Check if a document with similar content already exists
        api_url = "http://localhost:8000/api/v1/ingestion/check"
        
        payload = {
            "project": "docker-docs",
            "filename": file_path.name,
            "file_path": str(file_path)
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("exists", False)
        
    except Exception as e:
        # If check fails, assume not ingested to be safe
        pass
    
    return False

def ingest_file_to_finderskeepers(file_path: Path, project: str = "docker-docs") -> bool:
    """Ingest a single guide file into FindersKeepers via API"""
    
    # Skip if already ingested
    if check_if_already_ingested(file_path):
        print(f"⏭️  Already ingested: {file_path.name}")
        return True
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Classify content
        category, language = classify_guide_content(file_path)
        
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'text/markdown')
            }
            
            # Build comprehensive tags
            tags = ['docker', 'documentation', 'guide', 'tutorial']
            
            if category == "language" and language:
                tags.extend([language, 'programming', 'containerization'])
            elif category == "ai-ml":
                tags.extend(['ai', 'machine-learning', 'artificial-intelligence'])
            elif category == "infrastructure":
                tags.extend(['infrastructure', 'deployment', 'orchestration'])
            elif category == "admin":
                tags.extend(['admin', 'enterprise', 'management'])
            
            # Add specific guide type tags
            if 'quickstart' in str(file_path).lower():
                tags.append('quickstart')
            if 'tutorial' in str(file_path).lower():
                tags.append('tutorial')
            if 'example' in str(file_path).lower():
                tags.append('example')
            
            data = {
                'project': project,
                'tags': tags,
                'metadata': json.dumps({
                    'source': 'docker-docs-guides',
                    'file_path': str(file_path),
                    'ingestion_method': 'git_clone_supplement',
                    'file_extension': file_path.suffix,
                    'category': category,
                    'language': language,
                    'guide_type': 'docker-guide',
                    'repository': 'https://github.com/docker/docs',
                    'section': 'guides'
                })
            }
            
            response = requests.post(
                api_url, 
                files=files, 
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                # Category indicators
                if category == "language":
                    indicator = f"🐍" if language == "python" else f"💻"
                elif category == "ai-ml":
                    indicator = "🤖"
                elif category == "infrastructure":
                    indicator = "🚀"
                elif category == "admin":
                    indicator = "🏢"
                else:
                    indicator = "📚"
                
                print(f"✅ {indicator} Ingested: {file_path.name}")
                return True
            else:
                print(f"❌ Failed to ingest {file_path.name}: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error ingesting {file_path.name}: {e}")
        return False

def main():
    """Main Docker guides supplemental ingestion process"""
    print("🚀 Starting Docker Guides Supplemental Ingestion")
    print("=" * 60)
    print("🎯 Target: /content/guides/ directory from Docker docs")
    print("📖 Focus: Complete coverage of Docker guides and tutorials")
    print("")
    
    # Step 1: Clone repository
    repo_dir = clone_docker_docs_repository()
    if not repo_dir:
        print("❌ Failed to clone Docker docs repository")
        return
    
    try:
        # Step 2: Find guides files
        guide_files = find_guides_files(repo_dir)
        
        if not guide_files:
            print("❌ No guides files found")
            return
        
        # Step 3: Ingest files with tracking
        successful = 0
        failed = 0
        skipped = 0
        language_count = 0
        ai_ml_count = 0
        infra_count = 0
        admin_count = 0
        
        print(f"📥 Processing {len(guide_files)} guide files...")
        print("🐍 = Language guides | 🤖 = AI/ML | 🚀 = Infrastructure | 🏢 = Admin | 📚 = General")
        print("")
        
        for i, guide_file in enumerate(guide_files):
            print(f"[{i+1}/{len(guide_files)}] Processing {guide_file.name}...")
            
            # Count categories for final stats
            category, language = classify_guide_content(guide_file)
            if category == "language":
                language_count += 1
            elif category == "ai-ml":
                ai_ml_count += 1
            elif category == "infrastructure":
                infra_count += 1
            elif category == "admin":
                admin_count += 1
            
            result = ingest_file_to_finderskeepers(guide_file)
            if result == True:
                successful += 1
            elif result == "skipped":
                skipped += 1
            else:
                failed += 1
            
            # Rate limiting - don't overwhelm the API
            if i % 5 == 0 and i > 0:
                print("⏳ Rate limiting pause...")
                time.sleep(3)
        
        print("\n" + "=" * 60)
        print(f"📊 DOCKER GUIDES SUPPLEMENTAL INGESTION COMPLETE")
        print(f"✅ Successfully ingested: {successful}")
        print(f"⏭️  Already existed: {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"🐍 Language-specific guides: {language_count}")
        print(f"🤖 AI/ML guides: {ai_ml_count}")
        print(f"🚀 Infrastructure guides: {infra_count}")
        print(f"🏢 Admin/Enterprise guides: {admin_count}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        
        # Summary
        print(f"\n💡 GUIDES COVERAGE SUMMARY:")
        print(f"   • Language tutorials: Python, Node.js, Java, Go, PHP, Ruby, etc.")
        print(f"   • AI/ML workflows: TensorFlow, Jupyter, sentiment analysis, etc.")
        print(f"   • Infrastructure: Kubernetes, Docker Compose, monitoring, etc.")
        print(f"   • Admin features: User management, SSO, enterprise setup")
        print(f"   • Complete Docker guides now available in knowledge base!")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()