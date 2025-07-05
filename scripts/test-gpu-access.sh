#!/bin/bash
# Test GPU access with Ubuntu 24.04

set -e

echo "🧪 Testing GPU access with Ubuntu 24.04..."

# First run the permission commands
echo "🔧 Setting up docker group permissions..."
sudo usermod -aG docker $USER

echo "⚡ Testing GPU access..."
docker run --rm --gpus all ubuntu:24.04 sh -c "apt update && apt install -y nvidia-utils-530 && nvidia-smi"

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ GPU access is working perfectly!"
    echo ""
    echo "🎯 Ready to deploy Ollama with GPU acceleration!"
    echo "🖥️  Portainer GUI: https://localhost:9443"
    echo "📦 Docker Hub: Ready with bitcainnet login"
else
    echo "❌ GPU access test failed"
fi