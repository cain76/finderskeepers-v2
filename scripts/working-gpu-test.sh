#!/bin/bash
# Working GPU test with correct NVIDIA image

echo "🧪 Testing GPU access with correct NVIDIA CUDA image..."

# Set correct Docker socket
export DOCKER_HOST=unix:///var/run/docker.sock

# Test with a known working NVIDIA CUDA image
echo "📥 Testing with nvidia/cuda:12.0-base-ubuntu20.04..."
sudo docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi

if [ $? -ne 0 ]; then
    echo "🔄 Trying nvidia/cuda:11.8-base-ubuntu20.04..."
    sudo docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
fi

if [ $? -ne 0 ]; then
    echo "🔄 Trying simple ubuntu with nvidia-smi install..."
    sudo docker run --rm --gpus all ubuntu:20.04 sh -c "apt update -qq && apt install -y nvidia-utils-470 && nvidia-smi"
fi

echo ""
echo "🎯 If any of the above worked, GPU access is confirmed!"
echo "Ready to deploy Ollama!"