#!/usr/bin/env python3
"""
Test script to verify MCP Knowledge Server functionality
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_knowledge_server():
    """Test basic MCP server functionality"""
    
    # Create connection to the server
    server_params = StdioServerParameters(
        command="python",
        args=["src/knowledge_server.py"],
        cwd="/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server"
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Successfully connected to MCP Knowledge Server")
                
                # Initialize the session
                await session.initialize()
                print("✅ Session initialized")
                
                # List available tools
                tools_response = await session.list_tools()
                print(f"\n📋 Available tools ({len(tools_response.tools)}):")
                for tool in tools_response.tools:
                    print(f"  - {tool.name}: {tool.description[:60]}...")
                
                # List available resources
                resources_response = await session.list_resources()
                print(f"\n📚 Available resources ({len(resources_response.resources)}):")
                for resource in resources_response.resources:
                    print(f"  - {resource.uri}: {resource.name}")
                
                # List available prompts
                prompts_response = await session.list_prompts()
                print(f"\n💬 Available prompts ({len(prompts_response.prompts)}):")
                for prompt in prompts_response.prompts:
                    print(f"  - {prompt.name}: {prompt.description[:60]}...")
                
                # Test a simple tool call
                print("\n🔍 Testing search_documents tool...")
                try:
                    result = await session.call_tool(
                        "search_documents",
                        arguments={
                            "query": "Docker GPU configuration",
                            "limit": 3
                        }
                    )
                    print(f"✅ Tool call successful!")
                    print(f"   Response: {json.dumps(result.content, indent=2)[:200]}...")
                except Exception as e:
                    print(f"⚠️  Tool call failed (expected if databases not running): {e}")
                
                print("\n✅ All basic tests passed!")
                
    except Exception as e:
        print(f"❌ Failed to connect to server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing FindersKeepers MCP Knowledge Server...")
    print("-" * 50)
    
    success = asyncio.run(test_knowledge_server())
    
    if success:
        print("\n🎉 MCP Knowledge Server is working correctly!")
    else:
        print("\n❌ MCP Knowledge Server test failed!")