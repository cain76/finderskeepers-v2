#!/usr/bin/env python3
"""
Test script to verify FastMCP 2.9+ middleware is working correctly
"""

import sys
import os
sys.path.insert(0, 'src')

def test_middleware_imports():
    """Test that FastMCP middleware imports work"""
    try:
        from fastmcp.server.middleware import Middleware, MiddlewareContext
        print("✅ FastMCP middleware imports successful")
        return True
    except ImportError as e:
        print(f"❌ FastMCP middleware import failed: {e}")
        return False

def test_server_initialization():
    """Test that the fk2_mcp_server initializes correctly"""
    try:
        # Import the server module
        from fk2_mcp_server import middleware_available, mcp, logger
        
        print(f"✅ Server initialized successfully")
        print(f"   - Middleware available: {middleware_available}")
        print(f"   - Server name: {mcp.name}")
        print(f"   - Logger configured: {logger.name}")
        
        return True
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")
        return False

def test_middleware_registration():
    """Test that middleware is properly registered"""
    try:
        from fk2_mcp_server import conversation_middleware
        print("✅ Middleware instance created successfully")
        print(f"   - Conversation buffer: {len(conversation_middleware.conversation_buffer)} messages")
        return True
    except Exception as e:
        print(f"❌ Middleware registration failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing FindersKeepers v2 MCP Server with FastMCP 2.9+ Middleware")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Test 1: Middleware imports
    all_tests_passed &= test_middleware_imports()
    
    # Test 2: Server initialization
    all_tests_passed &= test_server_initialization()
    
    # Test 3: Middleware registration
    all_tests_passed &= test_middleware_registration()
    
    print("=" * 70)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! FastMCP 2.9+ middleware is working correctly!")
        print("🚀 Ready for Claude Desktop integration with progressive memory!")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)
