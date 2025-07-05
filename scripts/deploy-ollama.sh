#!/bin/bash
# Deploy Ollama with GPU support

echo "🚀 Deploying Ollama with RTX 2080 Ti GPU support..."

# Set correct Docker socket
export DOCKER_HOST=unix:///var/run/docker.sock

# Deploy Ollama
sudo docker run -d \
    --gpus=all \
    -v ollama:/root/.ollama \
    -p 11434:11434 \
    --name ollama \
    --restart unless-stopped \
    ollama/ollama

echo "⏳ Waiting for Ollama to start..."
sleep 10

# Check if it's running
echo "📊 Checking Ollama status..."
sudo docker ps | grep ollama

# Test the API
echo "🧪 Testing Ollama API..."
curl -s http://localhost:11434/api/version

echo ""
echo "✅ Ollama deployed successfully!"
echo "🎯 Ready to download models and chat!"