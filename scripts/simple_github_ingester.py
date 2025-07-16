#!/usr/bin/env python3
"""
Simple GitHub Docs Ingester - Works in Docker container
"""

import requests
import json
import time

def ingest_github_url(url, project="github-docs"):
    """Ingest a GitHub docs URL directly via the existing URL ingestion API"""
    
    api_url = "http://fastapi:80/api/v1/ingestion/url"
    
    payload = {
        "urls": [url],
        "project": project,
        "tags": ["github", "documentation", "official"],
        "metadata": {
            "source": "github-docs-direct",
            "ingestion_method": "api_call"
        }
    }
    
    try:
        print(f"🔄 Ingesting: {url}")
        response = requests.post(api_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('message', 'Ingested successfully')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ingest key GitHub documentation URLs"""
    
    github_urls = [
        "https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-your-membership-in-organizations/about-organization-membership",
        "https://docs.github.com/en/get-started/quickstart/hello-world",
        "https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories",
        "https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests",
        "https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues"
    ]
    
    print("🚀 Starting GitHub Documentation Ingestion")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    for i, url in enumerate(github_urls):
        print(f"\n[{i+1}/{len(github_urls)}] Processing...")
        
        if ingest_github_url(url):
            successful += 1
        else:
            failed += 1
        
        # Delay between requests
        if i < len(github_urls) - 1:
            print("⏳ Waiting 5 seconds...")
            time.sleep(5)
    
    print("\n" + "=" * 50)
    print(f"📊 COMPLETE")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {successful/(successful+failed)*100:.1f}%")

if __name__ == "__main__":
    main()