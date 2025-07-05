#!/bin/bash
# Portainer GUI Setup Script for Docker Engine
# Provides web-based Docker management interface

set -e

echo "🖥️  Setting up Portainer GUI for Docker..."

# Create Portainer data directory on external storage
echo "📁 Creating Portainer data directory..."
mkdir -p /media/cain/linux_storage/portainer

# Stop and remove existing Portainer (if any)
echo "🧹 Cleaning up existing Portainer..."
docker stop portainer 2>/dev/null || true
docker rm portainer 2>/dev/null || true

# Create Portainer volume
echo "💾 Creating Portainer volume..."
docker volume create portainer_data

# Deploy Portainer CE
echo "🚀 Deploying Portainer..."
docker run -d \
  -p 8000:8000 \
  -p 9443:9443 \
  --name portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

# Wait for Portainer to start
echo "⏳ Waiting for Portainer to start..."
sleep 10

# Check if Portainer is running
if docker ps | grep -q portainer; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Portainer GUI successfully installed!"
    echo ""
    echo "🌐 Access Portainer at:"
    echo "   https://localhost:9443"
    echo "   http://localhost:8000"
    echo ""
    echo "🔑 First-time setup:"
    echo "   1. Open https://localhost:9443 in your browser"
    echo "   2. Create admin account"
    echo "   3. Select 'Docker' environment"
    echo "   4. Start managing containers!"
    echo ""
    echo "📊 Portainer features:"
    echo "   • Container management"
    echo "   • Image management"
    echo "   • Volume & network management"
    echo "   • Stack deployment (Docker Compose)"
    echo "   • Real-time monitoring"
else
    echo "❌ Portainer failed to start. Check Docker logs:"
    echo "   docker logs portainer"
fi