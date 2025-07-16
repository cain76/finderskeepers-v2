#!/usr/bin/env python3
"""
Final GitHub Documentation Ingester - Works!
"""

import requests
import json
import time

def ingest_github_url(url, project="github-docs"):
    """Ingest a GitHub docs URL using the working API format"""
    
    api_url = "http://localhost:8000/api/v1/ingestion/url"
    
    payload = {
        "url": url,
        "project": project,
        "tags": ["github", "documentation", "official"],
        "metadata": {
            "source": "github-docs-ingester",
            "ingestion_method": "direct_api"
        }
    }
    
    try:
        print(f"🔄 Queuing: {url}")
        response = requests.post(api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ingestion_id = result.get('ingestion_id')
            print(f"✅ Queued successfully: {ingestion_id}")
            return ingestion_id
        else:
            print(f"❌ Failed to queue: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def check_ingestion_status(ingestion_id):
    """Check if the document was successfully ingested"""
    import subprocess
    
    cmd = f"""docker compose exec postgres psql -U finderskeepers -d finderskeepers_v2 -c "SELECT title, metadata->>'source_url' as source_url FROM documents WHERE title LIKE '%{ingestion_id}%' LIMIT 1;" """
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return "http" in result.stdout

def main():
    """Ingest key GitHub documentation URLs"""
    
    # Specific GitHub docs that you need
    github_urls = [
        "https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-your-membership-in-organizations/about-organization-membership",
        "https://docs.github.com/en/get-started/quickstart/hello-world",
        "https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories",
        "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests",
        "https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues"
    ]
    
    print("🚀 Starting GitHub Documentation Ingestion")
    print("=" * 60)
    print(f"📄 Queuing {len(github_urls)} URLs for processing...")
    
    queued_ids = []
    
    # Queue all URLs
    for i, url in enumerate(github_urls):
        print(f"\n[{i+1}/{len(github_urls)}] Processing...")
        ingestion_id = ingest_github_url(url)
        
        if ingestion_id:
            queued_ids.append((ingestion_id, url))
        
        # Small delay to avoid overwhelming the API
        time.sleep(2)
    
    print(f"\n✅ Successfully queued {len(queued_ids)} URLs")
    print("⏳ Waiting 30 seconds for processing...")
    time.sleep(30)
    
    # Check results
    print("\n📊 Checking ingestion results...")
    successful = 0
    
    for ingestion_id, url in queued_ids:
        if check_ingestion_status(ingestion_id):
            print(f"✅ Successfully ingested: {url}")
            successful += 1
        else:
            print(f"⏳ Still processing or failed: {url}")
    
    print("\n" + "=" * 60)
    print(f"📈 INGESTION SUMMARY")
    print(f"📥 Queued: {len(queued_ids)}")
    print(f"✅ Completed: {successful}")
    print(f"⏳ Processing/Failed: {len(queued_ids) - successful}")
    
    if successful > 0:
        print("\n🎉 GitHub documentation is now available in your FindersKeepers knowledge base!")
        print("💡 You can search for GitHub organization, repository, and workflow information.")

if __name__ == "__main__":
    main()