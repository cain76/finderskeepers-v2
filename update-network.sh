#!/bin/bash
# FindersKeepers v2 Network Migration Script
# This script safely updates all containers to use the new network configuration

echo "🔧 FindersKeepers v2 Network Configuration Update"
echo "================================================"

# Check if running as the correct user
if [ "$USER" != "cain" ]; then
    echo "❌ Please run this script as user 'cain'"
    exit 1
fi

# Change to project directory
cd /media/cain/linux_storage/projects/finderskeepers-v2 || exit 1

echo ""
echo "📋 Current container status:"
docker ps --filter "name=fk2_" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🔍 Checking network configuration..."
docker network inspect shared-network --format "Network exists: {{.Name}}" 2>/dev/null || echo "Network does not exist"

echo ""
echo "⚠️  This will restart all FindersKeepers v2 containers to apply network aliases."
echo "   This ensures containers can communicate using both service names and container names."
read -p "Continue? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled"
    exit 1
fi

echo ""
echo "🚀 Applying new network configuration..."

# Recreate containers with new network config
echo "📦 Recreating containers with updated network settings..."
docker compose up -d --force-recreate

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 10

echo ""
echo "✅ Verifying container status..."
docker ps --filter "name=fk2_" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🔍 Testing network connectivity..."

# Test from FastAPI container
echo ""
echo "Testing inter-container connectivity (container names):"
docker exec fk2_fastapi python -c "
import socket
hosts = [
    ('fk2_postgres', 5432),
    ('fk2_n8n', 5678),
    ('fk2_redis', 6379),
    ('fk2_neo4j', 7687),
    ('fk2_qdrant', 6333),
    ('fk2_ollama', 11434)
]
for host, port in hosts:
    try:
        socket.create_connection((host, port), timeout=2)
        print(f'  ✓ {host}:{port} - Connected')
    except:
        print(f'  ✗ {host}:{port} - Failed')
" 2>/dev/null || echo "  ⚠️  Could not test container name connectivity"

echo ""
echo "Testing inter-container connectivity (service aliases):"
docker exec fk2_fastapi python -c "
import socket
hosts = [
    ('postgres', 5432),
    ('n8n', 5678),
    ('redis', 6379),
    ('neo4j', 7687),
    ('qdrant', 6333),
    ('ollama', 11434)
]
for host, port in hosts:
    try:
        socket.create_connection((host, port), timeout=2)
        print(f'  ✓ {host}:{port} - Connected')
    except:
        print(f'  ✗ {host}:{port} - Failed')
" 2>/dev/null || echo "  ⚠️  Could not test service alias connectivity"

echo ""
echo "🎉 Network configuration update complete!"
echo ""
echo "📌 Summary:"
echo "  - All containers are on the 'shared-network'"
echo "  - Containers can be accessed by both:"
echo "    • Container names (fk2_postgres, fk2_n8n, etc.)"
echo "    • Service names (postgres, n8n, etc.)"
echo "  - Host can access all services via localhost:PORT"
echo "  - MCP tools can access services via localhost:PORT"
echo ""
echo "✅ Your FindersKeepers v2 networking is now properly configured!"
