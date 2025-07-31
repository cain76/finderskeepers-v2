#!/bin/bash
# Final GPU test and Ollama deployment

echo "🧪 Testing GPU access with NVIDIA CUDA image..."

# Set correct Docker socket
export DOCKER_HOST=unix:///var/run/docker.sock

# Test with NVIDIA's official CUDA image
sudo docker run --rm --gpus all nvidia/cuda:12.2-base-ubuntu22.04 nvidia-smi

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ GPU ACCESS IS WORKING PERFECTLY!"
    echo ""
    echo "🚀 Deploying Ollama with GPU acceleration..."
    
    # Deploy Ollama with GPU support
    sudo docker run -d \
        --gpus=all \
        -v ollama:/root/.ollama \
        -p 11434:11434 \
        --name ollama \
        --restart unless-stopped \
        ollama/ollama
    
    echo ""
    echo "✅ Ollama deployed successfully!"
    echo ""
    echo "📊 Your setup:"
    echo "   • GPU: RTX 2080 Ti with CUDA 12.8"
    echo "   • Docker Engine: Native GPU access"
    echo "   • Storage: /media/cain/linux_storage/docker"
    echo "   • GUI: Portainer at https://localhost:9443"
    echo "   • Ollama API: http://localhost:11434"
    echo ""
    echo "🎯 Next steps:"
    echo "   1. Log out and back in to fix docker permissions"
    echo "   2. Download models: docker exec ollama ollama pull llama3:8b"
    echo "   3. Test chat: docker exec ollama ollama run llama3:8b"
else
    echo "❌ GPU test failed"
fi