#!/bin/bash
# Fix Docker GPU Runtime Configuration

set -e

echo "🔧 Fixing Docker GPU runtime configuration..."

# Update Docker daemon configuration
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

echo "🔄 Restarting Docker service..."
sudo systemctl restart docker

echo "🧪 Testing GPU access..."
sleep 3
docker run --gpus all --rm ubuntu nvidia-smi

echo "✅ GPU runtime configuration fixed!"