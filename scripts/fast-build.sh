#!/bin/bash
# Fast Docker Build Script with BuildX Optimization
# Uses fast container builder with caching and multi-platform support

set -e

echo "🚀 Fast Build Script - FindersKeepers v2"
echo "========================================"

# Source environment variables
if [ -f ".env" ]; then
    source .env
else
    echo "⚠️ .env file not found - continuing without custom settings"
fi

# Set default builder if not specified
BUILDX_BUILDER=${BUILDX_BUILDER:-fast-builder}

echo "🔧 Using builder: $BUILDX_BUILDER"

# Check if builder exists and is running
if ! docker buildx inspect $BUILDX_BUILDER >/dev/null 2>&1; then
    echo "⚠️ Builder '$BUILDX_BUILDER' not found. Creating fast container builder..."
    docker buildx create --use --name $BUILDX_BUILDER --driver docker-container --bootstrap
    echo "✅ Fast builder '$BUILDX_BUILDER' created and ready!"
fi

# Set the builder as active
docker buildx use $BUILDX_BUILDER

# Function to build with cache optimization
build_service() {
    local service=$1
    local context=$2
    local tag=$3
    local platforms=${4:-"linux/amd64"}
    
    echo ""
    echo "🏗️  Building $service..."
    echo "   Context: $context"
    echo "   Tag: $tag"
    echo "   Platforms: $platforms"
    
    # Build with cache optimization and load to local registry
    if [[ "$platforms" == *","* ]]; then
        # Multi-platform build - push to registry
        echo "   Multi-platform build detected - will push to registry"
        docker buildx build \
            --builder $BUILDX_BUILDER \
            --platform $platforms \
            --tag $tag \
            --cache-from type=local,src=/tmp/buildx-cache-$service \
            --cache-to type=local,dest=/tmp/buildx-cache-$service,mode=max \
            --push \
            $context
    else
        # Single platform build - load locally
        docker buildx build \
            --builder $BUILDX_BUILDER \
            --platform $platforms \
            --tag $tag \
            --cache-from type=local,src=/tmp/buildx-cache-$service \
            --cache-to type=local,dest=/tmp/buildx-cache-$service,mode=max \
            --load \
            $context
    fi
    
    echo "✅ $service build complete!"
}

# Parse command line arguments
SERVICE=${1:-"all"}
PLATFORMS=${2:-"linux/amd64"}

case $SERVICE in
    "fastapi")
        echo "🎯 Building FastAPI service only..."
        build_service "fastapi" "./services/diary-api" "fk2_fastapi:latest" "$PLATFORMS"
        ;;
    "all")
        echo "🎯 Building all services..."
        echo "⚠️ For all services, using docker compose build with buildx..."
        
        # Use docker compose with buildx for coordinated builds
        export BUILDX_BUILDER=$BUILDX_BUILDER
        docker compose build
        ;;
    *)
        echo "❌ Unknown service: $SERVICE"
        echo "Usage: $0 [fastapi|all] [platforms]"
        echo "Examples:"
        echo "  $0 fastapi                    # Build FastAPI for linux/amd64"
        echo "  $0 fastapi linux/amd64,linux/arm64  # Build FastAPI multi-platform"
        echo "  $0 all                        # Build all services"
        exit 1
        ;;
esac

echo ""
echo "🎉 Build process completed!"
echo "📊 Builder status:"
docker buildx ls | grep $BUILDX_BUILDER
echo ""
echo "🐳 Ready for deployment with optimized builds!"