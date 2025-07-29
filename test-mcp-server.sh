#!/bin/bash
# Test script for FK2 MCP Server

echo "Testing FK2 MCP Server..."
echo "========================="

# Set environment variables
export POSTGRES_URL="postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
export N8N_WEBHOOK_URL="http://localhost:5678"
export LOG_LEVEL="INFO"
export FINDERSKEEPERS_PROJECT="finderskeepers-v2"
export FINDERSKEEPERS_USER="bitcain"
export FASTAPI_URL="http://localhost:8000"
export QDRANT_URL="http://localhost:6333"
export NEO4J_URL="bolt://localhost:7687"
export PYTHONPATH="/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server"

# Run the server with a timeout
echo "Starting server..."
timeout 5 /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/venv/bin/python /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-session-server/src/fk2_mcp_server.py

echo ""
echo "Test completed. Exit code: $?"
