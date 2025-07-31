#!/bin/bash
# FindersKeepers v2 - Ollama Model Setup Script
# Downloads and configures local LLM models for zero-cost AI inference

set -e

echo "🤖 Setting up Ollama models for FindersKeepers v2..."
echo "🎯 Target GPU: RTX 2080 Ti (11GB VRAM)"
echo ""

# Wait for Ollama service to be ready
echo "⏳ Waiting for Ollama service to be ready..."
timeout=120
while ! curl -s http://localhost:11434/api/version > /dev/null; do
    sleep 2
    timeout=$((timeout - 2))
    if [ $timeout -le 0 ]; then
        echo "❌ Timeout waiting for Ollama service"
        exit 1
    fi
done

echo "✅ Ollama service is ready"
echo ""

# Function to download model with progress
download_model() {
    local model=$1
    local description=$2
    
    echo "📥 Downloading $model ($description)..."
    docker exec -it fk2_ollama ollama pull $model
    
    if [ $? -eq 0 ]; then
        echo "✅ $model downloaded successfully"
    else
        echo "❌ Failed to download $model"
        return 1
    fi
    echo ""
}

# Download embedding model (essential for vector search)
download_model "mxbai-embed-large" "Embedding model - 334M params, optimized for RTX 2080 Ti"

# Download small chat model (fits comfortably in 11GB VRAM)
download_model "llama3:8b" "Chat model - 8B params, better performance"

echo "🧪 Testing model functionality..."

# Test embedding model
echo "Testing embedding generation..."
response=$(docker exec fk2_ollama curl -s http://localhost:11434/api/embed -d '{
  "model": "mxbai-embed-large",
  "input": "FindersKeepers v2 knowledge management system"
}')

if echo "$response" | grep -q "embeddings"; then
    echo "✅ Embedding model working correctly"
else
    echo "⚠️  Embedding model test failed"
fi

# Test chat model
echo "Testing chat generation..."
response=$(docker exec fk2_ollama curl -s http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Hello, this is a test.",
  "stream": false
}')

if echo "$response" | grep -q "response"; then
    echo "✅ Chat model working correctly"
else
    echo "⚠️  Chat model test failed"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Ollama models setup complete!"
echo ""
echo "Available models:"
docker exec fk2_ollama ollama list

echo ""
echo "💡 Model recommendations for RTX 2080 Ti (11GB VRAM):"
echo "• Embedding: mxbai-embed-large (334M) - Always loaded"
echo "• Chat: llama3:8b (8B) - Primary chat model"
echo "• Code: codestral:7b (7B) - Code generation/analysis"
echo "• Testing: qwen2.5:0.5b (0.5B) - Lightweight testing"
echo ""
echo "🚀 Ready for zero-cost AI inference!"
echo "🔧 FastAPI will automatically use these models when USE_LOCAL_LLM=true"