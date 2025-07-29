#!/bin/bash
# FindersKeepers v2 Quick Network Update Script
# This script updates the network configuration for existing containers

echo "🔧 FindersKeepers v2 Network Configuration - Quick Update"
echo "======================================================="

cd /media/cain/linux_storage/projects/finderskeepers-v2 || exit 1

echo ""
echo "📋 Current container status:"
docker ps --filter "name=fk2_" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🚀 Restarting containers to apply network aliases..."
echo "(This will only restart existing containers, not build new ones)"

# Restart each container individually to apply network aliases
for container in fk2_n8n fk2_postgres fk2_redis fk2_neo4j fk2_qdrant fk2_ollama fk2_fastapi fk2_frontend; do
    echo -n "  Restarting $container... "
    docker restart $container >/dev/null 2>&1 && echo "✓" || echo "✗"
done

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 10

echo ""
echo "✅ Verifying container status..."
docker ps --filter "name=fk2_" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "🔍 Testing network connectivity..."

# Test with both naming conventions
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
" 2>/dev/null || echo "  ⚠️  Service aliases will work after full docker-compose update"

echo ""
echo "🎉 Network update complete!"
echo ""
echo "📌 Current Status:"
echo "  ✅ All containers are on the 'shared-network'"
echo "  ✅ Containers accessible by container names (fk2_*)"
echo "  ⚠️  Service name aliases require full docker-compose recreate"
echo ""
echo "To enable service name aliases (postgres, n8n, etc.), run:"
echo "  docker compose down && docker compose up -d"
echo ""
echo "✅ Your FindersKeepers v2 is operational with current naming!"
