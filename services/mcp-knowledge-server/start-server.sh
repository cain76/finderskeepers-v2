#!/bin/bash
# FindersKeepers v2 MCP Knowledge Server Startup Script

cd "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server"
source "/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/.venv/bin/activate"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 Starting FindersKeepers v2 MCP Knowledge Server..."
python src/knowledge_server.py
