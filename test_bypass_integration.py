#!/usr/bin/env python3
"""
Test script for verifying the n8n bypass implementation
Run this after restarting Docker containers to verify everything works
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_mcp_health():
    """Test MCP health endpoint"""
    print("\n1. Testing MCP Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/mcp/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ MCP Health Check PASSED")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Database: {data.get('database')}")
            print(f"   - 24h Stats: {data.get('stats_24h')}")
        else:
            print(f"❌ MCP Health Check FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ MCP Health Check ERROR: {e}")

def test_session_lifecycle():
    """Test session start, action logging, and end"""
    print("\n2. Testing Session Lifecycle...")
    
    # Start session
    session_id = f"test_bypass_{int(datetime.now().timestamp())}"
    session_data = {
        "session_id": session_id,
        "agent_type": "test_script",
        "user_id": "bitcain",
        "project": "finderskeepers-v2",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/mcp/session/start", json=session_data)
        if response.status_code == 200:
            print(f"✅ Session Start PASSED: {session_id}")
        else:
            print(f"❌ Session Start FAILED: HTTP {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Session Start ERROR: {e}")
        return
    
    # Log action
    action_data = {
        "session_id": session_id,
        "action_type": "test_action",
        "description": "Testing direct FastAPI integration",
        "details": {"test": True, "bypass": "n8n"},
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/mcp/action", json=action_data)
        if response.status_code == 200:
            print(f"✅ Action Logging PASSED")
        else:
            print(f"❌ Action Logging FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Action Logging ERROR: {e}")
    
    # Log conversation message
    conversation_data = {
        "session_id": session_id,
        "action_type": "conversation_message",
        "description": "Test conversation",
        "details": {
            "message_type": "test_message",
            "content": "This is a test conversation message via direct FastAPI integration"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/mcp/action", json=conversation_data)
        if response.status_code == 200:
            print(f"✅ Conversation Logging PASSED")
        else:
            print(f"❌ Conversation Logging FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Conversation Logging ERROR: {e}")
    
    # End session
    end_data = {
        "session_id": session_id,
        "reason": "test_complete",
        "summary": "Test session completed successfully",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/mcp/session/end", json=end_data)
        if response.status_code == 200:
            print(f"✅ Session End PASSED")
        else:
            print(f"❌ Session End FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Session End ERROR: {e}")

def test_recent_sessions():
    """Test fetching recent sessions"""
    print("\n3. Testing Recent Sessions Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/mcp/sessions/recent?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recent Sessions PASSED")
            print(f"   - Found {data.get('count', 0)} sessions")
        else:
            print(f"❌ Recent Sessions FAILED: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Recent Sessions ERROR: {e}")

def test_fastapi_docs():
    """Check if FastAPI docs show MCP endpoints"""
    print("\n4. Checking FastAPI Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            mcp_endpoints = [path for path in openapi.get("paths", {}) if "/api/mcp" in path]
            if mcp_endpoints:
                print(f"✅ MCP Endpoints Found in API Docs:")
                for endpoint in mcp_endpoints:
                    print(f"   - {endpoint}")
            else:
                print(f"❌ No MCP endpoints found in API docs")
        else:
            print(f"❌ Cannot fetch API documentation")
    except Exception as e:
        print(f"❌ API Docs ERROR: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("FindersKeepers v2 - n8n Bypass Verification")
    print("=" * 60)
    
    test_mcp_health()
    test_session_lifecycle()
    test_recent_sessions()
    test_fastapi_docs()
    
    print("\n" + "=" * 60)
    print("✅ Verification Complete!")
    print("Check http://localhost:8000/docs for interactive API testing")
    print("=" * 60)
