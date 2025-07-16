#!/bin/bash

# Restart FK Knowledge MCP Server Script
# Cleans up existing processes and starts fresh

echo "🔄 Restarting FK Knowledge MCP Server..."

# Kill any existing MCP Knowledge Server processes
echo "🛑 Stopping existing MCP server processes..."
pkill -f "knowledge_server.py" || echo "No existing processes found"

# Wait a moment for cleanup
sleep 2

# Navigate to MCP server directory
cd /media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables for Docker container communication
export FASTAPI_URL="http://fk2_fastapi:8000"
export N8N_WEBHOOK_URL="http://fk2_n8n:5678"
export POSTGRES_URL="postgresql://finderskeepers:fk2025secure@fk2_postgres:5432/finderskeepers_v2"
export NEO4J_URI="bolt://fk2_neo4j:7687"
export QDRANT_URL="http://fk2_qdrant:6333"
export REDIS_URL="redis://fk2_redis:6379"

echo "🚀 Starting FK Knowledge MCP Server..."
echo "📡 FastAPI URL: $FASTAPI_URL"
echo "🔗 N8N Webhook URL: $N8N_WEBHOOK_URL"
echo "🗄️ PostgreSQL URL: $POSTGRES_URL"

# Start the MCP server
python src/knowledge_server.py