#!/bin/bash
# FindersKeepers v2 - Start All Services
set -e

echo "🔍 Starting FindersKeepers v2..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy .env.example to .env and configure your API keys."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Docker Hub login with bitcainnet credentials
echo "🔑 Logging into Docker Hub as bitcainnet..."
if [ -n "$DOCKER_TOKEN" ] && [ -n "$DOCKER_USERNAME" ]; then
    echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin
    if [ $? -eq 0 ]; then
        echo "✅ Docker Hub login successful"
    else
        echo "❌ Docker Hub login failed - continuing anyway"
    fi
else
    echo "⚠️  Docker credentials not found in .env - some images may not be accessible"
fi

# Create data directories if they don't exist
echo "📁 Creating data directories..."
mkdir -p data/{postgres-data,neo4j-data,qdrant-data,redis-data,n8n-data,documents}
mkdir -p logs

# Set proper permissions
chmod -R 755 data/
chmod -R 755 logs/

# Ensure shared network exists
echo "🌐 Ensuring shared Docker network exists..."
if [ ! -f ./ensure-network.sh ] || [ ! -x ./ensure-network.sh ]; then
    echo "❌ ensure-network.sh not found or not executable! Please add the file and ensure it has execute permissions."
    exit 1
fi
./ensure-network.sh

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker compose pull

# Start services
echo "🚀 Starting all services..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose ps

# Test key endpoints
echo ""
echo "🧪 Testing key endpoints..."

# Test FastAPI
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ FastAPI: http://localhost:8000"
else
    echo "❌ FastAPI not responding"
fi

# Test n8n
if curl -s http://localhost:5678 > /dev/null; then
    echo "✅ n8n: http://localhost:5678"
else
    echo "❌ n8n not responding"
fi

# Test Neo4j
if curl -s http://localhost:7474 > /dev/null; then
    echo "✅ Neo4j: http://localhost:7474"
else
    echo "❌ Neo4j not responding"
fi

# Test Qdrant
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant: http://localhost:6333"
else
    echo "❌ Qdrant not responding"
fi

# Test Ollama
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama: http://localhost:11434"
else
    echo "❌ Ollama not responding"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 FindersKeepers v2 is running!"
echo ""
echo "Access Points:"
echo "• n8n Workflows: http://localhost:5678 (admin/finderskeepers2025)"
echo "• FastAPI Docs: http://localhost:8000/docs"
echo "• Neo4j Browser: http://localhost:7474 (neo4j/fk2025neo4j)"
echo "• Qdrant Dashboard: http://localhost:6333/dashboard"
echo "• Ollama API: http://localhost:11434"
echo ""
echo "Next steps:"
echo "1. Configure your workflows in n8n"
echo "2. Import existing FindersKeepers data (optional)"
echo "3. Start using the knowledge hub!"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"