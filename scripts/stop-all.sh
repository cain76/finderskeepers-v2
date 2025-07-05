#!/bin/bash
# FindersKeepers v2 - Stop All Services
set -e

echo "🛑 Stopping FindersKeepers v2..."

# Stop all services
echo "📦 Stopping Docker containers..."
docker-compose down

# Check if user wants to remove volumes
read -p "🗑️  Remove all data volumes? This will DELETE all your data! (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️  Removing all data volumes..."
    docker-compose down -v
    sudo rm -rf data/
    echo "💀 All data has been deleted!"
else
    echo "💾 Data volumes preserved"
fi

# Clean up orphaned containers
echo "🧹 Cleaning up orphaned containers..."
docker-compose down --remove-orphans

# Show remaining containers
echo ""
echo "📊 Remaining FindersKeepers containers:"
docker ps -a | grep -E "(fk2_|finderskeepers)" || echo "None found"

echo ""
echo "✅ FindersKeepers v2 stopped!"
echo ""
echo "To restart: ./scripts/start-all.sh"