#!/bin/bash
# Switch from Docker Desktop to Docker Engine completely

set -e

echo "🔄 Switching from Docker Desktop to Docker Engine..."

# Stop Docker Desktop
echo "🛑 Stopping Docker Desktop..."
pkill -f "docker-desktop" || true
pkill -f "qemu-system-x86_64" || true

# Make sure Docker Engine daemon is running
echo "🚀 Starting Docker Engine daemon..."
sudo systemctl start docker
sudo systemctl enable docker

# Set Docker CLI to use Docker Engine socket
echo "🔧 Configuring Docker CLI..."
export DOCKER_HOST=unix:///var/run/docker.sock
echo 'export DOCKER_HOST=unix:///var/run/docker.sock' >> ~/.bashrc

# Wait for Docker Engine to be ready
echo "⏳ Waiting for Docker Engine..."
sleep 5

# Test Docker Engine connection
echo "🧪 Testing Docker Engine..."
docker version

# Test GPU access
echo "🎯 Testing GPU access..."
docker run --rm --gpus all ubuntu:20.04 nvidia-smi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Successfully switched to Docker Engine!"
echo ""
echo "📊 Benefits:"
echo "   • Native GPU access working"
echo "   • Better performance (no VM overhead)"
echo "   • External storage configured"
echo "   • All data on /media/cain/linux_storage/docker"
echo ""
echo "🖥️  Access Portainer GUI: https://localhost:9443"
echo "📦 Docker Hub login: Already configured"
echo ""
echo "🔄 You may need to restart your terminal or run:"
echo "   source ~/.bashrc"