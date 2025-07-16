#!/usr/bin/env python3
"""
Supplemental Docker Reference Ingestion Script for FindersKeepers v2
Specifically targets the /content/reference/ directory for complete CLI, API, and reference coverage
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
    print("🔄 Cloning Docker documentation repository for reference docs...")
    
    temp_dir = tempfile.mkdtemp(prefix="docker_reference_")
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

def find_reference_files(repo_dir: str) -> List[Path]:
    """Find all files in the reference directory"""
    docs_path = Path(repo_dir)
    
    # Focus specifically on the reference directory
    reference_dir = docs_path / "content" / "reference"
    
    if not reference_dir.exists():
        print(f"❌ Reference directory not found: {reference_dir}")
        return []
    
    # Look for all documentation file types in reference
    file_extensions = [".md", ".mdx", ".rst", ".txt", ".yaml", ".yml"]
    
    reference_files = []
    
    for ext in file_extensions:
        pattern = f"**/*{ext}"
        for ref_file in reference_dir.rglob(pattern):
            # Skip certain files that aren't content
            if any(skip in str(ref_file) for skip in [
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
                
            reference_files.append(ref_file)
    
    print(f"📄 Found {len(reference_files)} files in reference directory")
    return reference_files

def classify_reference_content(file_path: Path) -> tuple:
    """Classify reference content by type"""
    path_str = str(file_path).lower()
    filename = file_path.name.lower()
    
    # Read content preview for classification
    content_preview = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content_preview = f.read(2000).lower()
    except:
        pass
    
    # Reference sections mapping
    reference_sections = {
        'cli': {
            'keywords': ['cli', 'command', 'docker run', 'docker build', 'docker pull', 'docker push'],
            'priority': 'critical',
            'emoji': '⚡'
        },
        'api': {
            'keywords': ['api', 'rest', 'http', 'endpoint', 'json'],
            'priority': 'high',
            'emoji': '🔗'
        },
        'compose-file': {
            'keywords': ['compose', 'docker-compose', 'yaml', 'services', 'version'],
            'priority': 'high',
            'emoji': '📝'
        },
        'dockerfile': {
            'keywords': ['dockerfile', 'from', 'run', 'copy', 'add', 'cmd'],
            'priority': 'high',
            'emoji': '📄'
        },
        'glossary': {
            'keywords': ['glossary', 'definition', 'term', 'meaning'],
            'priority': 'medium',
            'emoji': '📚'
        },
        'samples': {
            'keywords': ['sample', 'example', 'demo', 'template'],
            'priority': 'medium',
            'emoji': '📋'
        }
    }
    
    # Determine section from path
    section = "general"
    priority = "normal"
    emoji = "📖"
    
    for section_name, section_info in reference_sections.items():
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
    
    # Special handling for specific CLI commands
    if 'cli' in path_str:
        if any(cmd in filename for cmd in ['run', 'build', 'pull', 'push', 'exec', 'logs', 'ps', 'images']):
            priority = 'critical'
            emoji = '⚡'
        elif any(cmd in filename for cmd in ['compose', 'buildx', 'swarm', 'network', 'volume']):
            priority = 'high'
            emoji = '⚡'
    
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
    """Ingest a single reference file into FindersKeepers via API"""
    
    # Skip if already ingested
    if check_if_already_ingested(file_path):
        print(f"⏭️  Already ingested: {file_path.name}")
        return "skipped"
    
    # FindersKeepers ingestion API endpoint
    api_url = "http://localhost:8000/api/v1/ingestion/single"
    
    try:
        # Classify content
        section, priority, emoji = classify_reference_content(file_path)
        
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
            tags = ['docker', 'documentation', 'reference', 'command-line']
            
            # Add section-specific tags
            if section == "cli":
                tags.extend(['cli', 'command', 'terminal', 'bash', 'critical'])
            elif section == "api":
                tags.extend(['api', 'rest', 'http', 'endpoint', 'integration'])
            elif section == "compose-file":
                tags.extend(['compose', 'docker-compose', 'yaml', 'services', 'orchestration'])
            elif section == "dockerfile":
                tags.extend(['dockerfile', 'build', 'image', 'container'])
            elif section == "glossary":
                tags.extend(['glossary', 'terminology', 'definitions'])
            elif section == "samples":
                tags.extend(['samples', 'examples', 'templates', 'demos'])
            
            # Add specific command tags if it's a CLI reference
            if 'cli' in str(file_path).lower():
                command_name = file_path.name.replace('.md', '')
                tags.append(f'docker-{command_name}')
            
            data = {
                'project': project,
                'tags': tags,
                'metadata': json.dumps({
                    'source': 'docker-docs-reference',
                    'file_path': str(file_path),
                    'ingestion_method': 'git_clone_reference',
                    'file_extension': file_path.suffix,
                    'section': section,
                    'priority': priority,
                    'reference_type': 'docker-reference',
                    'repository': 'https://github.com/docker/docs',
                    'directory': 'reference',
                    'is_cli_reference': 'cli' in str(file_path).lower(),
                    'is_api_reference': 'api' in str(file_path).lower()
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
    """Main Docker reference supplemental ingestion process"""
    print("🚀 Starting Docker Reference Supplemental Ingestion")
    print("=" * 60)
    print("🎯 Target: /content/reference/ directory from Docker docs")
    print("⚡ Focus: CLI commands, API references, Compose files, samples")
    print("🔧 Goal: Stop Docker command hallucinations forever! 😄")
    print("")
    
    # Step 1: Clone repository
    repo_dir = clone_docker_docs_repository()
    if not repo_dir:
        print("❌ Failed to clone Docker docs repository")
        return
    
    try:
        # Step 2: Find reference files
        reference_files = find_reference_files(repo_dir)
        
        if not reference_files:
            print("❌ No reference files found")
            return
        
        # Step 3: Sort by priority (CLI commands first)
        def priority_sort_key(file_path):
            section, priority, emoji = classify_reference_content(file_path)
            priority_order = {
                "critical": 0,
                "high": 1,
                "medium": 2,
                "normal": 3
            }
            return priority_order.get(priority, 4)
        
        reference_files.sort(key=priority_sort_key)
        
        # Step 4: Ingest files with tracking
        successful = 0
        failed = 0
        skipped = 0
        
        # Category counters
        cli_count = 0
        api_count = 0
        compose_count = 0
        dockerfile_count = 0
        glossary_count = 0
        samples_count = 0
        
        print(f"📥 Processing {len(reference_files)} reference files...")
        print("⚡ = CLI | 🔗 = API | 📝 = Compose | 📄 = Dockerfile | 📚 = Glossary | 📋 = Samples")
        print("")
        
        for i, ref_file in enumerate(reference_files):
            print(f"[{i+1}/{len(reference_files)}] Processing {ref_file.name}...")
            
            # Count categories for final stats
            section, priority, emoji = classify_reference_content(ref_file)
            if section == "cli":
                cli_count += 1
            elif section == "api":
                api_count += 1
            elif section == "compose-file":
                compose_count += 1
            elif section == "dockerfile":
                dockerfile_count += 1
            elif section == "glossary":
                glossary_count += 1
            elif section == "samples":
                samples_count += 1
            
            result = ingest_file_to_finderskeepers(ref_file)
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
        print(f"📊 DOCKER REFERENCE SUPPLEMENTAL INGESTION COMPLETE")
        print(f"✅ Successfully ingested: {successful}")
        print(f"⏭️  Already existed: {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"⚡ CLI Commands: {cli_count}")
        print(f"🔗 API References: {api_count}")
        print(f"📝 Compose Files: {compose_count}")
        print(f"📄 Dockerfile Refs: {dockerfile_count}")
        print(f"📚 Glossary: {glossary_count}")
        print(f"📋 Samples: {samples_count}")
        print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")
        
        # Summary
        print(f"\n💡 REFERENCE COVERAGE SUMMARY:")
        print(f"   • Complete Docker CLI command reference")
        print(f"   • Full Docker API documentation")
        print(f"   • Docker Compose file reference")
        print(f"   • Dockerfile reference and best practices")
        print(f"   • Docker terminology glossary")
        print(f"   • Reference samples and examples")
        print(f"   • No more Docker command hallucinations! 🎉")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up temporary directory: {repo_dir}")
        shutil.rmtree(repo_dir, ignore_errors=True)

if __name__ == "__main__":
    main()