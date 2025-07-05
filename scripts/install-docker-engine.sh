#!/bin/bash
# Docker Engine Installation Script for FindersKeepers v2
# Configures Docker to use external storage and GPU support

set -e

echo "🚀 Installing Docker Engine with GPU support and external storage..."

# Set permissions for Docker storage directory
echo "📁 Setting up Docker storage directory..."
sudo chown root:root /media/cain/linux_storage/docker
sudo chmod 755 /media/cain/linux_storage/docker

# Remove old Docker packages (if any)
echo "🧹 Removing old Docker packages..."
sudo apt-get remove -y docker docker-engine docker.io containerd runc || true

# Update package index
echo "📦 Updating package index..."
sudo apt-get update

# Install prerequisites
echo "🔧 Installing prerequisites..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
echo "🔑 Adding Docker GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "📝 Adding Docker repository..."
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
echo "🔄 Updating package index with Docker repository..."
sudo apt-get update

# Install Docker Engine
echo "🐳 Installing Docker Engine..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Configure Docker daemon with external storage and NVIDIA support
echo "⚙️  Configuring Docker daemon..."
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "data-root": "/media/cain/linux_storage/docker",
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
EOF

# Configure NVIDIA Container Toolkit for Docker
echo "🎯 Configuring NVIDIA Container Toolkit..."
sudo nvidia-ctk runtime configure --runtime=docker

# Add user to docker group
echo "👤 Adding user to docker group..."
sudo usermod -aG docker $USER

# Restart Docker service
echo "🔄 Restarting Docker service..."
sudo systemctl restart docker
sudo systemctl enable docker

# Test Docker installation
echo "🧪 Testing Docker installation..."
sudo docker run hello-world

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Docker Engine installation complete!"
echo ""
echo "📊 Configuration:"
echo "   • Data storage: /media/cain/linux_storage/docker"
echo "   • NVIDIA GPU support: Configured"
echo "   • User added to docker group"
echo ""
echo "🔄 You may need to log out and back in for group changes to take effect"
echo "🧪 Test GPU access: docker run --gpus all ubuntu nvidia-smi"
echo ""
echo "Next steps:"
echo "1. Log out and back in (or run: newgrp docker)"
echo "2. Run ./scripts/setup-portainer.sh for GUI"
echo "3. Login to Docker Hub: docker login -u bitcainnet"