#!/bin/bash

# FindersKeepers v2 - Container Restart Script for bitcain
# This script restarts all containers with the updated MCP server fixes

echo "🚀 FindersKeepers v2 - Restarting Containers with Conversation Logging Fixes"
echo "=================================================================="

# Navigate to project directory
cd /media/cain/linux_storage/projects/finderskeepers-v2

echo "📍 Current directory: $(pwd)"

# Stop all containers
echo "🛑 Stopping all FindersKeepers v2 containers..."
docker compose down

# Wait for clean shutdown
echo "⏳ Waiting for clean shutdown..."
sleep 5

# Start all containers in detached mode
echo "🚀 Starting all containers with updated configuration..."
docker compose up -d

# Wait for services to initialize
echo "⏳ Waiting for services to initialize..."
sleep 10

# Show container status
echo "📊 Container Status:"
docker ps --filter "name=fk2_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔧 Service Health Check URLs:"
echo "- n8n Workflows: http://localhost:5678"
echo "- FastAPI Backend: http://localhost:8000/docs"
echo "- PostgreSQL: localhost:5432"
echo "- Neo4j: http://localhost:7474"
echo "- Qdrant: http://localhost:6333"
echo "- Frontend: http://localhost:3000"

echo ""
echo "⚡ CRITICAL: Test the conversation logging pipeline with:"
echo "1. Start MCP server: Run fk2-mcp server"
echo "2. start_session()"
echo "3. test_webhooks() - Validate full pipeline"
echo "4. capture_this_conversation('Hello Claude!') - Test manual capture"

echo ""
echo "🎯 FINDERSKEEPERS V2 CONVERSATION LOGGING: ACTIVATED! 🧠⚡"
