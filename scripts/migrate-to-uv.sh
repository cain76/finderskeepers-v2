#!/bin/bash
# FindersKeepers v2 - UV Migration Script
# Migrates FastAPI service from pip requirements.txt to UV pyproject.toml

set -e

echo "🚀 FindersKeepers v2 - UV Migration Script"
echo "=========================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check Docker Compose command (V1 vs V2)
if command_exists docker-compose; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites satisfied"

# Create backup before migration
echo "🔄 Creating backup before migration..."
./scripts/backup-before-migration.sh

echo ""
echo "⚠️  IMPORTANT: Backup created successfully!"
echo "   Continue with migration? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled by user"
    exit 0
fi

# Stop the current FastAPI container
echo "🛑 Stopping current FastAPI container..."
$DOCKER_COMPOSE stop fastapi

# Remove the old container to force rebuild
echo "🗑️  Removing old FastAPI container..."
$DOCKER_COMPOSE rm -f fastapi

# Generate UV lock file if it doesn't exist
echo "🔒 Generating UV lock file..."
cd services/diary-api
if [ ! -f uv.lock ]; then
    echo "📦 Creating uv.lock for reproducible builds..."
    if command_exists uv; then
        uv lock
    else
        echo "⚠️  UV not found locally. Lock file will be generated during Docker build."
    fi
fi
cd ../..

# Check for Docker Hub login
echo "🔐 Checking Docker Hub authentication..."
if [ -f .env ]; then
    source .env
    if [ -n "$DOCKER_USERNAME" ]; then
        echo "🔑 Using Docker Hub login: $DOCKER_USERNAME"
        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin 2>/dev/null || {
            echo "⚠️  Docker login failed, continuing without authentication"
        }
    elif docker info | grep -q "Registry:"; then
        echo "✅ Already logged into Docker Hub"
    else
        echo "⚠️  No Docker Hub credentials found, using public images only"
    fi
fi

# Build new UV-based FastAPI container with production optimizations
echo "🔨 Building production-optimized UV-based FastAPI container..."
DOCKER_BUILDKIT=1 $DOCKER_COMPOSE build fastapi

# Start the new container
echo "🚀 Starting new UV-based FastAPI container..."
$DOCKER_COMPOSE up -d fastapi

# Wait for container to be ready
echo "⏳ Waiting for FastAPI to start..."
sleep 10

# Test the API health
echo "🏥 Testing API health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI health check passed!"
else
    echo "⚠️  FastAPI health check failed. Checking logs..."
    docker-compose logs fastapi
fi

# Show container status
echo "📊 Container status:"
docker ps --filter "name=fk2_fastapi" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Show UV benefits
echo ""
echo "🎉 Production UV Migration Complete!"
echo "===================================="
echo "✅ Modern Python packaging with pyproject.toml"
echo "✅ 10-100x faster dependency resolution"
echo "✅ Multi-stage Docker build for smaller images"
echo "✅ Bytecode compilation for faster startup"
echo "✅ BuildKit caching for rapid rebuilds"
echo "✅ Non-root user for enhanced security"
echo "✅ Health checks and monitoring ready"
echo "✅ Reproducible builds with uv.lock"
echo ""
echo "📊 Next steps:"
echo "1. Test API endpoints: http://localhost:8000/docs"
echo "2. Check container logs: docker-compose logs fastapi"
echo "3. Add new dependencies: uv add <package>"
echo "4. Update dependencies: uv lock --upgrade"
echo ""
echo "💡 UV commands for development:"
echo "   uv add <package>          # Add dependency"
echo "   uv remove <package>       # Remove dependency"
echo "   uv sync                   # Sync environment"
echo "   uv run python script.py   # Run with project env"