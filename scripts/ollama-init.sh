#!/bin/sh
# Ollama Model Initialization Script for FindersKeepers v2
# Automatically downloads required models on first container start

echo "🚀 Initializing Ollama models for FindersKeepers v2..."

# Start Ollama service in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama service to start..."
sleep 10

# Pull required models
echo "📥 Pulling llama3:8b model (upgraded for better performance)..."
ollama pull llama3:8b

echo "📥 Pulling mxbai-embed-large model (1024 dimensions for vector search)..."
ollama pull mxbai-embed-large

# Optional: Pre-load models into memory for faster first response
echo "🔄 Pre-loading models into memory..."
ollama run llama3:8b "Hello, this is a test to load the model." &
sleep 5
ollama run mxbai-embed-large "Test embedding generation" &
sleep 5

echo "✅ Ollama models initialized successfully!"
echo "📊 Available models:"
ollama list

# Keep Ollama running
wait $OLLAMA_PID