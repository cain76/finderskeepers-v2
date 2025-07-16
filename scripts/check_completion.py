#!/usr/bin/env python3
"""
Check if GitHub docs ingestion is complete and provide final stats
"""

import subprocess
import time
import os

def check_process_running():
    """Check if ingestion process is still running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'python3 ingest_github_docs.py'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_database_count():
    """Get current count of GitHub docs in database"""
    try:
        cmd = """docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM documents WHERE project = 'github-docs';" """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return 0

def get_progress_from_log():
    """Get current progress from log file"""
    log_file = "/media/cain/linux_storage/projects/finderskeepers-v2/scripts/github_ingestion.log"
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        for line in reversed(lines):
            if "Processing" in line and ".md" in line:
                # Extract [current/total] pattern
                if '[' in line and ']' in line:
                    bracket_content = line.split('[')[1].split(']')[0]
                    if '/' in bracket_content:
                        current, total = bracket_content.split('/')
                        return int(current), int(total)
        return 0, 6424
    except:
        return 0, 6424

def main():
    print("🔍 GitHub Docs Ingestion Status Check")
    print("=" * 40)
    
    is_running = check_process_running()
    db_count = get_database_count()
    current, total = get_progress_from_log()
    
    if is_running:
        percent = (current / total * 100) if total > 0 else 0
        print(f"✅ Process running: {current}/{total} files ({percent:.1f}%)")
        print(f"💾 Documents in DB: {db_count}")
        print(f"📈 Success rate: {(db_count/current*100):.1f}%" if current > 0 else "📈 Success rate: 0%")
        
        remaining = total - current
        if current > 0:
            # Rough estimate based on current progress
            estimated_hours = remaining / (current / 2)  # Assume 2 hours so far
            print(f"⏰ Estimated remaining: {estimated_hours:.1f} hours")
        
        return False  # Not complete
    else:
        print("🏁 Process completed!")
        print(f"💾 Final document count: {db_count}")
        print(f"📁 Files processed: {current}/{total}")
        
        # Check for specific organization content
        try:
            cmd = """docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM documents WHERE project = 'github-docs' AND content ILIKE '%organization%';" """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            org_count = int(result.stdout.strip()) if result.returncode == 0 else 0
            print(f"🏢 Organization-related docs: {org_count}")
        except:
            print("🏢 Organization-related docs: Unable to check")
        
        return True  # Complete

if __name__ == "__main__":
    main()