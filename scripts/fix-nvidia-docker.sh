#!/bin/bash
# Complete NVIDIA Docker Configuration Fix

set -e

echo "🔧 Fixing NVIDIA Docker integration..."

# Install/update NVIDIA Container Toolkit
echo "📦 Updating NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure the runtime properly
echo "⚙️  Configuring NVIDIA runtime..."
sudo nvidia-ctk runtime configure --runtime=docker --set-as-default

# Update Docker daemon config
echo "📝 Updating Docker daemon configuration..."
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
  },
  "default-runtime": "nvidia"
}
EOF

# Restart Docker
echo "🔄 Restarting Docker..."
sudo systemctl restart docker

# Wait for Docker to fully start
echo "⏳ Waiting for Docker to start..."
sleep 5

# Test GPU access
echo "🧪 Testing GPU access..."
docker run --rm --gpus all ubuntu:20.04 nvidia-smi

echo "✅ NVIDIA Docker integration fixed!"