#!/usr/bin/env python3
"""
Test script to verify activity logging integration
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from activity_logger import activity_logger

async def test_activity_logging():
    """Test the activity logging system"""
    
    print("🧪 Testing Activity Logger Integration...")
    print("-" * 50)
    
    try:
        # Initialize the logger
        await activity_logger.initialize()
        
        if activity_logger.initialized:
            print(f"✅ Activity logger initialized with session: {activity_logger.session_id}")
            
            # Test logging a tool call
            await activity_logger.log_tool_call(
                tool_name="test_search",
                arguments={"query": "test", "limit": 5},
                result={"total_results": 0, "results": []}
            )
            print("✅ Tool call logged successfully")
            
            # Test logging a resource access
            await activity_logger.log_resource_access("test://resource")
            print("✅ Resource access logged successfully")
            
            # Test logging an error
            test_error = Exception("Test error for logging")
            await activity_logger.log_error("test_operation", test_error)
            print("✅ Error logged successfully")
            
            print(f"\n🎉 All activity logging tests passed!")
            print(f"📋 Session ID: {activity_logger.session_id}")
            print(f"🔗 Check n8n UI at: http://localhost:5678")
            print(f"📊 Check PostgreSQL agent_sessions and agent_actions tables")
            
        else:
            print("⚠️  Activity logger failed to initialize - n8n workflows may not be active")
            
    except Exception as e:
        print(f"❌ Activity logging test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_activity_logging())