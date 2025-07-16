#!/usr/bin/env python3
"""
Check Docker docs ingestion progress and provide stats
"""

import subprocess
import time
import os

def check_process_running():
    """Check if Docker ingestion process is still running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'python3 ingest_docker_docs.py'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_database_count():
    """Get current count of Docker docs in database"""
    try:
        cmd = """docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM documents WHERE project = 'docker-docs';" """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return 0

def get_teams_count():
    """Get count of Teams/Enterprise documents"""
    try:
        cmd = """docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM documents WHERE project = 'docker-docs' AND (tags::text ILIKE '%teams%' OR tags::text ILIKE '%enterprise%');" """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return 0

def get_engine_count():
    """Get count of Engine/Linux documents"""
    try:
        cmd = """docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM documents WHERE project = 'docker-docs' AND (tags::text ILIKE '%engine%' OR tags::text ILIKE '%linux%');" """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return 0

def get_progress_from_log():
    """Get current progress from log file"""
    log_file = "/media/cain/linux_storage/projects/finderskeepers-v2/scripts/docker_ingestion.log"
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
        return 0, 1517
    except:
        return 0, 1517

def get_category_counts_from_log():
    """Count categories from log indicators"""
    log_file = "/media/cain/linux_storage/projects/finderskeepers-v2/scripts/docker_ingestion.log"
    teams_count = engine_count = gui_count = general_count = 0
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
            
        teams_count = content.count('✅ 🏢')     # Teams/Enterprise
        engine_count = content.count('✅ 🚀')    # Engine
        gui_count = content.count('✅ 🖥️')       # GUI
        general_count = content.count('✅ 📄')   # General
        
    except:
        pass
    
    return teams_count, engine_count, gui_count, general_count

def main():
    print("🔍 Docker Docs Ingestion Status Check")
    print("=" * 45)
    
    is_running = check_process_running()
    db_count = get_database_count()
    teams_db_count = get_teams_count()
    engine_db_count = get_engine_count()
    current, total = get_progress_from_log()
    teams_log, engine_log, gui_log, general_log = get_category_counts_from_log()
    
    if is_running:
        percent = (current / total * 100) if total > 0 else 0
        print(f"✅ Process running: {current}/{total} files ({percent:.1f}%)")
        print(f"💾 Documents in DB: {db_count}")
        print(f"📈 Success rate: {(db_count/current*100):.1f}%" if current > 0 else "📈 Success rate: 0%")
        
        print(f"\n🎯 PRIORITY CONTENT PROGRESS:")
        print(f"🏢 Teams/Enterprise: {teams_log} processed")
        print(f"🚀 Docker Engine: {engine_log} processed")
        print(f"🖥️ GUI/Management: {gui_log} processed")
        print(f"📄 General docs: {general_log} processed")
        
        remaining = total - current
        if current > 0:
            # Rough estimate based on current progress
            files_per_minute = 10  # Estimate based on rate limiting
            estimated_minutes = remaining / files_per_minute
            estimated_hours = estimated_minutes / 60
            print(f"⏰ Estimated remaining: {estimated_hours:.1f} hours")
        
        return False  # Not complete
    else:
        print("🏁 Process completed!")
        print(f"💾 Final document count: {db_count}")
        print(f"📁 Files processed: {current}/{total}")
        
        print(f"\n🎯 FINAL CONTENT BREAKDOWN:")
        print(f"🏢 Teams/Enterprise: {teams_db_count} docs in DB ({teams_log} processed)")
        print(f"🚀 Docker Engine/Linux: {engine_db_count} docs in DB ({engine_log} processed)")
        print(f"🖥️ GUI/Management: {gui_log} processed")
        print(f"📄 General documentation: {general_log} processed")
        
        # Sample some Teams/Engine content
        print(f"\n📝 TEAMS SUBSCRIPTION BENEFITS:")
        try:
            cmd = """docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -c "SELECT title FROM documents WHERE project = 'docker-docs' AND tags::text ILIKE '%teams%' LIMIT 5;" """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[2:-1]  # Skip header and footer
                for line in lines:
                    if line.strip() and not line.startswith('-'):
                        print(f"   • {line.strip()}")
        except:
            print("   • Unable to retrieve sample titles")
        
        return True  # Complete

if __name__ == "__main__":
    main()