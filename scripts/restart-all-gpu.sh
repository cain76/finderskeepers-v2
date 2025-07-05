#!/bin/bash
# Restart All FindersKeepers v2 Services with GPU Support

set -e

echo "🔄 Restarting all FindersKeepers v2 services with GPU support..."

# Set Docker socket
export DOCKER_HOST=unix:///var/run/docker.sock

# Stop all existing services
echo "🛑 Stopping existing services..."
sudo docker-compose down

# Remove the standalone Ollama container (we'll use docker-compose version)
echo "🧹 Cleaning up standalone containers..."
sudo docker stop ollama 2>/dev/null || true
sudo docker rm ollama 2>/dev/null || true
sudo docker stop portainer 2>/dev/null || true
sudo docker rm portainer 2>/dev/null || true

# Start all services with GPU support
echo "🚀 Starting all services with GPU acceleration..."
sudo docker-compose up -d

# Wait for services to initialize
echo "⏳ Waiting for services to start..."
sleep 15

# Check service status
echo "📊 Service Status:"
sudo docker-compose ps

# Test key services
echo ""
echo "🧪 Testing services..."

# Test Ollama API
echo "🤖 Ollama API:"
curl -s http://localhost:11434/api/version || echo "Not ready yet"

# Test FastAPI
echo "⚡ FastAPI:"
curl -s http://localhost:8000/health || echo "Not ready yet"

# Restart Portainer with new setup
echo "🖥️  Restarting Portainer GUI..."
sudo docker run -d \
  -p 8000:8000 \
  -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All services restarted with GPU support!"
echo ""
echo "🎯 Access Points:"
echo "   • Ollama API: http://localhost:11434"
echo "   • FastAPI: http://localhost:8000"
echo "   • n8n: http://localhost:5678 (admin/finderskeepers2025)"
echo "   • Neo4j: http://localhost:7474 (neo4j/fk2025neo4j)"
echo "   • Portainer: https://localhost:9443"
echo ""
echo "🔥 Ollama, FastAPI, AND n8n now have RTX 2080 Ti GPU access!"
echo ""
echo "🤖 GPU-enabled services:"
echo "   • Ollama: Local LLM inference with GPU"
echo "   • FastAPI: ML operations and embeddings"  
echo "   • n8n: AI workflows and image processing"