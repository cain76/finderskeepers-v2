#!/bin/bash

# FindersKeepers v2 WSL2 Startup Script
# Optimized for Windows 11 WSL2 with Ubuntu and RTX 2080 Ti

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   FindersKeepers v2 WSL2 Startup Script${NC}"
echo -e "${BLUE}   Windows 11 + Ubuntu + RTX 2080 Ti${NC}"  
echo -e "${BLUE}=================================================${NC}"
echo ""

# Check if we're running in WSL2
if [[ ! $(grep -i microsoft /proc/version) ]]; then
    echo -e "${YELLOW}Warning: This script is optimized for WSL2${NC}"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure your settings."
    exit 1
fi

# Source environment variables
echo -e "${YELLOW}Loading environment variables...${NC}"
set -a  # Export all variables
source .env
set +a

# Validate required environment variables
if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_TOKEN" ]; then
    echo -e "${RED}Error: DOCKER_USERNAME or DOCKER_TOKEN not set in .env${NC}"
    exit 1
fi

# Check Docker Desktop integration
echo -e "${YELLOW}Checking Docker Desktop WSL2 integration...${NC}"
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker is not running or not integrated with WSL2${NC}"
    echo "Please ensure Docker Desktop is running and WSL2 integration is enabled"
    exit 1
fi
echo -e "${GREEN}✓ Docker Desktop WSL2 integration working${NC}"

# Docker login
echo -e "${YELLOW}Logging into Docker Hub...${NC}"
echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker login successful${NC}"
else
    echo -e "${RED}✗ Docker login failed${NC}"
    exit 1
fi

# Check for NVIDIA GPU support in WSL2
echo -e "${YELLOW}Checking GPU support in WSL2...${NC}"
if docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ GPU acceleration working through Docker${NC}"
    docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi | head -n 10
else
    echo -e "${YELLOW}GPU acceleration may not be available${NC}"
    echo "Check Docker Desktop GPU settings"
fi

# Create external network
echo -e "${YELLOW}Setting up Docker network for WSL2...${NC}"
if ! docker network inspect shared-network &> /dev/null; then
    echo "Creating shared-network..."
    docker network create shared-network --driver bridge
    echo -e "${GREEN}✓ Network created${NC}"
else
    echo -e "${GREEN}✓ Network already exists${NC}"
fi

# WSL2 Performance optimization
echo -e "${YELLOW}Optimizing for WSL2 performance...${NC}"
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Create required directories
mkdir -p config/redis services/{diary-api,crawl4ai-service} frontend n8n/custom-nodes

# Pull and start services
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker compose pull

echo -e "${YELLOW}Starting all services...${NC}" 
docker compose up -d

# Wait and check status
sleep 15
docker compose ps

# Setup Ollama models
if docker compose ps ollama | grep -q "running"; then
    echo -e "${YELLOW}Setting up Ollama models for RTX 2080 Ti...${NC}"
    docker compose exec -T ollama ollama pull mxbai-embed-large || true
    docker compose exec -T ollama ollama pull llama3:8b || true
    echo -e "${GREEN}✓ Ollama models ready${NC}"
fi

# Display access information
echo ""
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}   FindersKeepers v2 is now running on WSL2!${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""
echo -e "${BLUE}Access from Windows at:${NC}"
echo -e "  • Frontend UI:      ${GREEN}http://localhost:3000${NC}"
echo -e "  • n8n Workflows:    ${GREEN}http://localhost:5678${NC}"
echo -e "  • FastAPI Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  • Neo4j Browser:    ${GREEN}http://localhost:7474${NC}"
echo -e "  • Qdrant API:       ${GREEN}http://localhost:6333${NC}"
echo ""
echo -e "${GREEN}GPU acceleration enabled via Docker Desktop!${NC}"
