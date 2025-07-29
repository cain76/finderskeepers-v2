#!/bin/bash
# bitcain network setup script for FindersKeepers v2

echo "🔧 Setting up shared-network for FindersKeepers v2..."

# Check if shared-network exists
if ! docker network ls | grep -q "shared-network"; then
    echo "Creating shared-network..."
    docker network create shared-network \
        --driver bridge \
        --subnet=172.19.0.0/16 \
        --gateway=172.19.0.1 \
        --opt com.docker.network.bridge.name=br-shared
    echo "✅ shared-network created successfully"
else
    echo "✅ shared-network already exists"
fi

echo "🚀 Network ready! You can now run: docker compose up -d"
