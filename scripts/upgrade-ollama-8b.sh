#!/bin/bash
# FindersKeepers v2 - Ollama 7B Model Upgrade Script
# Upgrades chat model from 3b to 7b while preserving data

echo "🚀 FindersKeepers v2 - Ollama Model Upgrade"
echo "=========================================="
echo "This will upgrade your chat model from 3b to 8b (llama3)"
echo ""

# Check if docker compose is running
if docker ps | grep -q fk2_ollama; then
    echo "✅ Ollama container is running"
    
    # Pull the new 7b model
    echo ""
    echo "📥 Downloading llama3:8b model (this may take 10-15 minutes)..."
    docker exec -it fk2_ollama ollama pull llama3:8b
    
    if [ $? -eq 0 ]; then
        echo "✅ Model downloaded successfully!"
        
        # Test the model
        echo ""
        echo "🧪 Testing new model..."
        docker exec -it fk2_ollama ollama run llama3:8b "Hello, testing model upgrade" --verbose
        
        echo ""
        echo "✅ Upgrade complete! Now restart services to use the new model:"
        echo "   cd /media/cain/linux_storage/projects/finderskeepers-v2"
        echo "   docker compose restart fastapi ollama"
    else
        echo "❌ Failed to download model. Please check your internet connection."
        exit 1
    fi
else
    echo "⚠️  Ollama container is not running."
    echo "Please start FindersKeepers v2 first:"
    echo "   cd /media/cain/linux_storage/projects/finderskeepers-v2"
    echo "   docker compose up -d"
    exit 1
fi

echo ""
echo "📝 Note: The docker-compose.yml has been updated to use llama3:8b"
echo "This change will persist across restarts and new installations."
