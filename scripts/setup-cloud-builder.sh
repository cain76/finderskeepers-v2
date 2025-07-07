#!/bin/bash
# Setup Docker Build Cloud for bitcainnet
# Uses credentials from .env file

set -e

echo "🚀 Setting up Docker Build Cloud for bitcainnet..."

# Source environment variables
if [ -f ".env" ]; then
    source .env
else
    echo "❌ .env file not found!"
    exit 1
fi

# Check if credentials exist
if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_TOKEN" ]; then
    echo "❌ Docker credentials not found in .env file!"
    exit 1
fi

echo "📦 Installing latest Docker Buildx with cloud support..."
mkdir -p ~/.docker/cli-plugins/
ARCH=amd64
BUILDX_URL=$(curl -s https://raw.githubusercontent.com/docker/actions-toolkit/main/.github/buildx-lab-releases.json | jq -r ".latest.assets[] | select(endswith(\"linux-$ARCH\"))")
curl --silent -L --output ~/.docker/cli-plugins/docker-buildx $BUILDX_URL
chmod a+x ~/.docker/cli-plugins/docker-buildx

echo "🔑 Authenticating with Docker Hub..."
echo "$DOCKER_TOKEN" | docker login --username "$DOCKER_USERNAME" --password-stdin

echo "☁️ Creating cloud builder for $DOCKER_USERNAME..."
docker buildx create --use --driver cloud "$DOCKER_USERNAME/default" || {
    echo "⚠️ Cloud builder creation failed. Trying alternative builder name..."
    docker buildx create --use --driver cloud "$DOCKER_USERNAME/builder" || {
        echo "❌ Cloud builder setup failed. Using local container builder as fallback..."
        docker buildx create --use --name fast-builder --driver docker-container --bootstrap
        echo "✅ Fast local container builder 'fast-builder' created as fallback"
        exit 0
    }
}

echo "✅ Docker Build Cloud configured successfully!"
docker buildx ls
echo ""
echo "🎯 Ready for fast cloud builds! Use:"
echo "   docker buildx build --platform linux/amd64,linux/arm64 --tag <IMAGE> --push ."
echo "   docker compose build (will automatically use cloud builder)"