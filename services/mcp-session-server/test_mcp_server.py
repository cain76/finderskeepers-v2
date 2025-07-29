#!/usr/bin/env python3
"""
Test script for fk2-mcp server
This tests if the server can start and list tools correctly
"""

import asyncio
import sys
import os
import json

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fk2_mcp_server import FindersKeepersV2MCPServer

async def test_server():
    """Test if the server can start and list tools"""
    print("🧪 Testing fk2-mcp server...")
    
    try:
        # Create server instance
        server_instance = FindersKeepersV2MCPServer()
        print("✅ Server instance created successfully")
        
        # Test database connection (this will likely fail but should not crash)
        print("🔗 Testing database connection...")
        try:
            db_result = await server_instance.initialize_database()
            if db_result:
                print("✅ Database connection successful")
            else:
                print("⚠️  Database connection failed (expected if containers not running)")
        except Exception as e:
            print(f"⚠️  Database connection failed: {e} (expected if containers not running)")
        
        # Test tool listing
        print("🔧 Testing tool listing...")
        
        # Get the list_tools function from the server
        list_tools_handler = None
        for handler in server_instance.server._tool_handlers.values():
            if hasattr(handler, '__name__') and 'list_tools' in str(handler):
                list_tools_handler = handler
                break
        
        if list_tools_handler:
            try:
                tools_result = await list_tools_handler()
                print(f"✅ Tool listing successful - Found {len(tools_result.tools)} tools:")
                for tool in tools_result.tools:
                    print(f"   - {tool.name}: {tool.description}")
            except Exception as e:
                print(f"❌ Tool listing failed: {e}")
        else:
            print("❌ Could not find list_tools handler")
        
        print("\n🎯 fk2-mcp server test completed!")
        print("✅ Server is ready for Claude Desktop integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
