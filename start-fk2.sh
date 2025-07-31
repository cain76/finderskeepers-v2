#!/bin/bash

# FindersKeepers v2 Startup Script
# This script handles Docker login, network setup, and service startup with GPU support

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

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   FindersKeepers v2 Startup Script${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""

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

# Docker login
echo -e "${YELLOW}Logging into Docker Hub...${NC}"
echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker login successful${NC}"
else
    echo -e "${RED}✗ Docker login failed${NC}"
    exit 1
fi

# Check for NVIDIA Docker support
echo -e "${YELLOW}Checking GPU support...${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    
    # Check if nvidia-docker2 is installed
    if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo -e "${RED}Warning: nvidia-docker2 may not be properly installed${NC}"
        echo "Please install nvidia-docker2 for GPU support"
        echo "Visit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    else
        echo -e "${GREEN}✓ NVIDIA Docker runtime working${NC}"
    fi
else
    echo -e "${YELLOW}No NVIDIA GPU detected. Services will run without GPU acceleration.${NC}"
fi

# Create external network if it doesn't exist
echo -e "${YELLOW}Setting up Docker network...${NC}"
if ! docker network inspect shared-network &> /dev/null; then
    echo "Creating shared-network..."
    docker network create shared-network
    echo -e "${GREEN}✓ Network created${NC}"
else
    echo -e "${GREEN}✓ Network already exists${NC}"
fi

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p config/redis
mkdir -p services/diary-api
mkdir -p services/crawl4ai-service
mkdir -p frontend
mkdir -p n8n/custom-nodes

# Create Redis config if it doesn't exist
if [ ! -f config/redis/redis.conf ]; then
    echo -e "${YELLOW}Creating Redis configuration...${NC}"
    cat > config/redis/redis.conf << 'EOF'
# Redis configuration for FindersKeepers v2
bind 0.0.0.0
protected-mode no
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16
always-show-logo yes
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
replica-priority 100
lazyfree-lazy-eviction no
lazyfree-lazy-expire no
lazyfree-lazy-server-del no
replica-lazy-flush no
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
latency-monitor-threshold 0
notify-keyspace-events ""
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
EOF
    echo -e "${GREEN}✓ Redis configuration created${NC}"
fi

# Pull latest images
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker compose pull

# Start services
echo -e "${YELLOW}Starting all services...${NC}"
docker compose up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check service health
echo -e "${YELLOW}Checking service status...${NC}"
docker compose ps

# Pull Ollama models if Ollama is running
if docker compose ps ollama | grep -q "running"; then
    echo -e "${YELLOW}Setting up Ollama models...${NC}"
    
    # Pull embedding model
    echo "Pulling embedding model (mxbai-embed-large)..."
    docker compose exec -T ollama ollama pull mxbai-embed-large || true
    
    # Pull chat model optimized for RTX 2080 Ti (11GB VRAM)
    echo "Pulling chat model (llama3:8b)..."
    docker compose exec -T ollama ollama pull llama3:8b || true
    
    echo -e "${GREEN}✓ Ollama models ready${NC}"
fi

# Display access information
echo ""
echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}   FindersKeepers v2 is now running!${NC}"
echo -e "${GREEN}===========================================${NC}"
echo ""
echo -e "${BLUE}Access your services at:${NC}"
echo -e "  • n8n Workflows:    ${GREEN}http://localhost:5678${NC}"
echo -e "    Username: ${YELLOW}${N8N_BASIC_AUTH_USER}${NC}"
echo -e "    Password: ${YELLOW}${N8N_BASIC_AUTH_PASSWORD}${NC}"
echo ""
echo -e "  • FastAPI Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  • Frontend UI:      ${GREEN}http://localhost:3000${NC}"
echo -e "  • Neo4j Browser:    ${GREEN}http://localhost:7474${NC}"
echo -e "    Username: ${YELLOW}neo4j${NC}"
echo -e "    Password: ${YELLOW}${NEO4J_PASSWORD}${NC}"
echo ""
echo -e "  • Qdrant API:       ${GREEN}http://localhost:6333${NC}"
echo -e "  • Ollama API:       ${GREEN}http://localhost:11434${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  • View logs:        ${YELLOW}docker compose logs -f [service_name]${NC}"
echo -e "  • Stop all:         ${YELLOW}docker compose down${NC}"
echo -e "  • Restart service:  ${YELLOW}docker compose restart [service_name]${NC}"
echo -e "  • GPU usage:        ${YELLOW}nvidia-smi${NC}"
echo ""
echo -e "${GREEN}GPU acceleration is enabled for compatible services.${NC}"
echo ""
