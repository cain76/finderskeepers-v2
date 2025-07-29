#!/usr/bin/env python3
"""
Minimal fk2-mcp server test to debug the 'tuple' object error
"""

import asyncio
import sys
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging to stderr only (MCP requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class MinimalMCPServer:
    def __init__(self):
        self.server = Server("fk2-mcp-test")
        self._register_tools()
        
    def _register_tools(self):
        """Register minimal tools to test"""
        
        @self.server.list_tools()
        async def list_tools():
            return ListToolsResult(
                tools=[
                    Tool(
                        name="test_tool",
                        description="Simple test tool",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Test message"
                                }
                            }
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            if request.name == "test_tool":
                message = request.arguments.get("message", "Hello") if request.arguments else "Hello"
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Test response: {message}")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {request.name}")]
                )

async def main():
    """Main function to run the minimal MCP server"""
    server = MinimalMCPServer()
    
    logger.info("🧪 Starting minimal fk2-mcp test server...")
    
    try:
        # Use the correct MCP stdio_server pattern
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream, 
                write_stream, 
                InitializationOptions(
                    server_name="fk2-mcp-test",
                    server_version="1.0.0",
                    capabilities={
                        "tools": {},
                    }
                )
            )
    except Exception as e:
        logger.error(f"❌ Test server error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal test server error: {e}")
        sys.exit(1)
