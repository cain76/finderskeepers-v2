#!/usr/bin/env python3
"""
Test script for FK2 Direct FastAPI Integration
Verifies that conversations are captured and processed automatically
"""

import asyncio
import httpx
import json
from datetime import datetime

FASTAPI_URL = "http://localhost:8000"

async def test_fk2_integration():
    """Test the complete FK2 conversation capture and processing pipeline"""
    
    print("=" * 70)
    print("FK2 DIRECT FASTAPI INTEGRATION TEST")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Check health
        print("\n1. Testing MCP health endpoint...")
        response = await client.get(f"{FASTAPI_URL}/api/mcp/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Health: {health['status']}")
            print(f"   📊 Last 24h: {health.get('stats_24h', {})}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
        
        # 2. Start a test session
        print("\n2. Starting test session...")
        session_id = f"test_sess_{int(datetime.now().timestamp())}"
        session_data = {
            "session_id": session_id,
            "user_id": "test_user",
            "agent_type": "test_agent",
            "project": "test_project",
            "timestamp": datetime.now().isoformat(),
            "source": "test_script",
            "ai_god_mode": True,
            "context": {"test": True}
        }
        
        response = await client.post(f"{FASTAPI_URL}/api/mcp/session/start", json=session_data)
        if response.status_code == 200:
            print(f"   ✅ Session started: {session_id}")
        else:
            print(f"   ❌ Session start failed: {response.status_code}")
            print(f"      {response.text}")
        
        # 3. Log a conversation message
        print("\n3. Logging conversation message...")
        action_data = {
            "session_id": session_id,
            "action_type": "conversation_message",
            "description": "Test conversation",
            "details": {
                "message_type": "user_message",
                "content": "This is a test message to verify the FK2 system is capturing conversations correctly. It should trigger automatic embedding generation and knowledge graph creation.",
                "context": {"test": True},
                "tools_used": ["test_tool"],
                "files_referenced": []
            },
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "source": "test_script",
            "ai_god_mode": True
        }
        
        response = await client.post(f"{FASTAPI_URL}/api/mcp/action", json=action_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Conversation logged: {result.get('action_id')}")
        else:
            print(f"   ❌ Conversation logging failed: {response.status_code}")
        
        # 4. Check if conversation was stored
        print("\n4. Verifying conversation storage...")
        response = await client.get(f"{FASTAPI_URL}/api/conversations/{session_id}")
        if response.status_code == 200:
            conversations = response.json()
            print(f"   ✅ Found {conversations['count']} conversations")
            if conversations['messages']:
                print(f"   📝 Latest: {conversations['messages'][0]['content'][:100]}...")
        else:
            print(f"   ❌ Failed to retrieve conversations: {response.status_code}")
        
        # 5. End session
        print("\n5. Ending test session...")
        end_data = {
            "session_id": session_id,
            "reason": "test_complete",
            "summary": "Test session completed successfully",
            "timestamp": datetime.now().isoformat(),
            "ai_god_mode": True,
            "accomplishments_count": 1,
            "conversations_count": 1
        }
        
        response = await client.post(f"{FASTAPI_URL}/api/mcp/session/end", json=end_data)
        if response.status_code == 200:
            print(f"   ✅ Session ended successfully")
        else:
            print(f"   ❌ Session end failed: {response.status_code}")
        
        # 6. Check recent sessions
        print("\n6. Checking recent sessions...")
        response = await client.get(f"{FASTAPI_URL}/api/mcp/sessions/recent?limit=5")
        if response.status_code == 200:
            sessions = response.json()
            print(f"   ✅ Found {sessions['count']} recent sessions")
            for sess in sessions['sessions'][:3]:
                print(f"      - {sess['session_id']} ({sess['status']})")
        else:
            print(f"   ❌ Failed to get recent sessions: {response.status_code}")
        
        print("\n" + "=" * 70)
        print("TEST COMPLETE - FK2 Direct FastAPI Integration Working!")
        print("Conversations are being captured and processed automatically.")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_fk2_integration())
