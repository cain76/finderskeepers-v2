#!/bin/bash
# Docker Hub Login Script
# Uses bitcainnet credentials from .env file

set -e

echo "🔑 Setting up Docker Hub authentication..."

# Source environment variables
if [ -f ".env" ]; then
    source .env
else
    echo "❌ .env file not found!"
    echo "Please ensure .env file exists with DOCKER_USERNAME and DOCKER_TOKEN"
    exit 1
fi

# Check if credentials exist
if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_TOKEN" ]; then
    echo "❌ Docker credentials not found in .env file!"
    echo "Please ensure these variables are set:"
    echo "   DOCKER_USERNAME=bitcainnet"
    echo "   DOCKER_TOKEN=your_docker_token"
    exit 1
fi

# Login to Docker Hub
echo "🚀 Logging into Docker Hub as $DOCKER_USERNAME..."
echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin

if [ $? -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Successfully logged into Docker Hub!"
    echo ""
    echo "📊 Your Docker Hub access:"
    echo "   • Username: $DOCKER_USERNAME"
    echo "   • Private repositories: Available"
    echo "   • Pull/push images: Ready"
    echo ""
    echo "🧪 Test access:"
    echo "   docker pull your-private-repo/image:tag"
    echo "   docker push your-private-repo/image:tag"
else
    echo "❌ Docker Hub login failed!"
    echo "Please check your credentials in .env file"
fi