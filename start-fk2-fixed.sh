#!/bin/bash

# FindersKeepers v2 Complete Rebuild Script for bitcain
# This script performs a complete cleanup and rebuild of the FK2 ecosystem
# Fixes container communication issues after GitHub security updates

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║     FindersKeepers v2 - Complete System Rebuild Script       ║${NC}"
echo -e "${MAGENTA}║              Optimized for bitcain.net Infrastructure        ║${NC}"
echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check port availability
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}✗ Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✓ Port $port is available${NC}"
        return 0
    fi
}

# Verify Docker and Docker Compose v2 are installed
echo -e "${YELLOW}Verifying prerequisites...${NC}"
if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! docker compose version &>/dev/null; then
    echo -e "${RED}Error: Docker Compose v2 is not installed${NC}"
    echo "Please install Docker Compose v2: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker and Docker Compose v2 found${NC}"

# Check if .env file exists, create from example if not
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo -e "${YELLOW}Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your credentials before continuing${NC}"
        echo -e "${YELLOW}Required: DOCKER_USERNAME and DOCKER_TOKEN${NC}"
        exit 1
    else
        echo -e "${YELLOW}Creating default .env file...${NC}"
        cat > .env << 'EOF'
# Docker Hub Credentials (REQUIRED)
DOCKER_USERNAME=bitcainnet
DOCKER_TOKEN=your_docker_token_here

# Database Passwords (CHANGE THESE!)
POSTGRES_PASSWORD=fk2025secure
NEO4J_PASSWORD=fk2025neo4j
SESSION_SECRET=change_this_session_secret_in_production
N8N_JWT_SECRET=change_this_jwt_secret_in_production

# n8n Authentication (CHANGE THESE!)
N8N_BASIC_AUTH_USER=admin@bitcain.net
N8N_BASIC_AUTH_PASSWORD=changeme

# Timezone
TZ=America/Chicago
TIMEZONE=America/Chicago

# Optional AI API Keys (leave empty if using local LLM only)
OPENAI_API_KEY=
GOOGLE_API_KEY=
ANTHROPIC_API_KEY=

# Node Environment
NODE_ENV=development

# Frontend URLs (adjust if needed)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_NEO4J_URI=bolt://localhost:7687
VITE_NEO4J_USER=neo4j
VITE_NEO4J_PASSWORD=fk2025neo4j
VITE_QDRANT_URL=http://localhost:6333

# Admin Features
VITE_ADMIN_ENABLED=true
VITE_BULK_PROCESSING_ENABLED=true
VITE_QUEUE_MAINTENANCE_ENABLED=true
VITE_PROCESSING_STATS_ENABLED=true

# Background Processing
FK2_ENABLE_BACKGROUND_PROCESSING=true
FK2_PROCESSING_INTERVAL_MINUTES=5
FK2_PROCESSING_BATCH_SIZE=10
FK2_PROCESSING_MAX_RETRIES=3
FK2_PROCESSING_START_DELAY_SECONDS=30
EOF
        echo -e "${RED}Created .env file - Please edit it with your Docker credentials!${NC}"
        exit 1
    fi
fi

# Source environment variables
echo -e "${YELLOW}Loading environment variables...${NC}"
set -a  # Export all variables
source .env
set +a

# Validate required environment variables
if [ -z "$DOCKER_USERNAME" ] || [ "$DOCKER_TOKEN" = "your_docker_token_here" ] || [ -z "$DOCKER_TOKEN" ]; then
    echo -e "${RED}Error: DOCKER_USERNAME or DOCKER_TOKEN not properly set in .env${NC}"
    echo "Please edit .env file with your actual Docker Hub credentials"
    exit 1
fi

# Docker login
echo -e "${YELLOW}Logging into Docker Hub as ${DOCKER_USERNAME}...${NC}"
echo "$DOCKER_TOKEN" | docker login -u "$DOCKER_USERNAME" --password-stdin
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker login successful${NC}"
else
    echo -e "${RED}✗ Docker login failed${NC}"
    exit 1
fi

# Check for NVIDIA GPU and Docker support
echo -e "${YELLOW}Checking GPU support...${NC}"
GPU_AVAILABLE=false
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected:${NC}"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | while read line; do
        echo -e "  ${CYAN}$line${NC}"
    done
    
    # Check if nvidia-docker2 is installed
    if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ NVIDIA Docker runtime working${NC}"
        GPU_AVAILABLE=true
    else
        echo -e "${RED}Warning: nvidia-docker2 may not be properly installed${NC}"
        echo "GPU acceleration will be disabled. To enable:"
        echo "  sudo apt-get install nvidia-docker2"
        echo "  sudo systemctl restart docker"
    fi
else
    echo -e "${YELLOW}No NVIDIA GPU detected. Services will run on CPU.${NC}"
fi

# Check for port conflicts
echo -e "${YELLOW}Checking port availability...${NC}"
PORTS=(3000 5432 5678 6333 6334 6379 7474 7687 8000 8001 11434)
PORT_CONFLICT=false
for port in "${PORTS[@]}"; do
    if ! check_port $port; then
        PORT_CONFLICT=true
    fi
done

if [ "$PORT_CONFLICT" = true ]; then
    echo -e "${YELLOW}Some ports are in use. Attempting to stop existing FK2 services...${NC}"
    docker compose down 2>/dev/null || true
    sleep 3
    
    # Recheck ports
    echo -e "${YELLOW}Rechecking ports after cleanup...${NC}"
    PORT_CONFLICT=false
    for port in "${PORTS[@]}"; do
        if ! check_port $port; then
            PORT_CONFLICT=true
            echo -e "${RED}Port $port is still in use by another process${NC}"
        fi
    done
    
    if [ "$PORT_CONFLICT" = true ]; then
        echo -e "${RED}Cannot continue: Required ports are in use by other processes${NC}"
        echo -e "${YELLOW}Please stop conflicting services or change ports in docker-compose.yml${NC}"
        exit 1
    fi
fi

# COMPLETE CLEANUP PHASE
echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}           PERFORMING COMPLETE SYSTEM CLEANUP                  ${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"

# Stop all FK2 containers
echo -e "${YELLOW}Stopping all FindersKeepers v2 containers...${NC}"
docker compose down --remove-orphans 2>/dev/null || true

# Remove individual containers if they exist
FK2_CONTAINERS=(fk2_n8n fk2_fastapi fk2_postgres fk2_qdrant fk2_neo4j fk2_redis fk2_ollama fk2_frontend fk2_webscraper)
for container in "${FK2_CONTAINERS[@]}"; do
    if docker ps -a | grep -q $container; then
        echo -e "${YELLOW}Removing container: $container${NC}"
        docker rm -f $container 2>/dev/null || true
    fi
done

# Clean up the shared-network
echo -e "${YELLOW}Recreating Docker network...${NC}"
docker network rm shared-network 2>/dev/null || true
sleep 2
docker network create --driver bridge \
    --subnet=172.25.0.0/16 \
    --ip-range=172.25.0.0/24 \
    --gateway=172.25.0.1 \
    --attachable \
    --label project=finderskeepers-v2 \
    --label creator=bitcain \
    shared-network
echo -e "${GREEN}✓ Created fresh shared-network${NC}"

# Optional: Full volume cleanup (commented out to preserve data)
echo -e "${YELLOW}Do you want to delete all data volumes? (y/N)${NC}"
echo -e "${RED}WARNING: This will delete all stored data including documents, embeddings, and graphs!${NC}"
read -r -n 1 -s DELETE_VOLUMES
echo
if [[ $DELETE_VOLUMES =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deleting all data volumes...${NC}"
    docker volume rm finderskeepers-v2_postgres_data 2>/dev/null || true
    docker volume rm finderskeepers-v2_neo4j_data 2>/dev/null || true
    docker volume rm finderskeepers-v2_neo4j_logs 2>/dev/null || true
    docker volume rm finderskeepers-v2_qdrant_data 2>/dev/null || true
    docker volume rm finderskeepers-v2_redis_data 2>/dev/null || true
    docker volume rm finderskeepers-v2_n8n_data 2>/dev/null || true
    docker volume rm finderskeepers-v2_ollama_data 2>/dev/null || true
    docker volume rm finderskeepers-v2_frontend_node_modules 2>/dev/null || true
    echo -e "${GREEN}✓ All volumes deleted${NC}"
else
    echo -e "${CYAN}Preserving existing data volumes${NC}"
fi

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p config/redis
mkdir -p services/diary-api
mkdir -p services/crawl4ai-service
mkdir -p services/mcp-session-server/src
mkdir -p fk2_frontend
mkdir -p n8n/custom-nodes
mkdir -p scripts
mkdir -p sql

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
loglevel notice
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data
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
notify-keyspace-events ""
activerehashing yes
EOF
    echo -e "${GREEN}✓ Redis configuration created${NC}"
fi

# Create Ollama initialization script
if [ ! -f scripts/ollama-init.sh ]; then
    echo -e "${YELLOW}Creating Ollama initialization script...${NC}"
    cat > scripts/ollama-init.sh << 'EOF'
#!/bin/sh
# Ollama model initialization for FindersKeepers v2
echo "Starting Ollama service..."
ollama serve &
sleep 10
echo "Pulling required models..."
ollama pull mxbai-embed-large
ollama pull llama3:8b
echo "Models ready!"
wait
EOF
    chmod +x scripts/ollama-init.sh
    echo -e "${GREEN}✓ Ollama init script created${NC}"
fi

# BUILD AND START PHASE
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}           BUILDING AND STARTING SERVICES                      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"

# Pull latest base images
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker compose pull

# Build custom images
echo -e "${YELLOW}Building custom services...${NC}"
docker compose build --no-cache

# Start all services
echo -e "${YELLOW}Starting all services...${NC}"
if [ "$GPU_AVAILABLE" = true ]; then
    docker compose up -d
else
    echo -e "${YELLOW}Starting without GPU acceleration...${NC}"
    docker compose up -d
fi

# Wait for services to initialize
echo -e "${YELLOW}Waiting for services to initialize...${NC}"
WAIT_TIME=30
for i in $(seq $WAIT_TIME -1 1); do
    echo -ne "\r${CYAN}Waiting... $i seconds remaining ${NC}"
    sleep 1
done
echo -e "\r${GREEN}✓ Services initialization period complete${NC}"

# Health checks
echo -e "${YELLOW}Performing health checks...${NC}"

# Check PostgreSQL
if docker compose exec -T postgres pg_isready -U finderskeepers -d finderskeepers_v2 &>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is healthy${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not responding${NC}"
fi

# Check Redis
if docker compose exec -T redis redis-cli ping | grep -q PONG; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
fi

# Check FastAPI
if curl -s -f http://localhost:8000/health &>/dev/null; then
    echo -e "${GREEN}✓ FastAPI is healthy${NC}"
else
    echo -e "${YELLOW}⚠ FastAPI health endpoint not responding (may be normal)${NC}"
fi

# Check Qdrant
if curl -s -f http://localhost:6333/collections &>/dev/null; then
    echo -e "${GREEN}✓ Qdrant is healthy${NC}"
else
    echo -e "${RED}✗ Qdrant is not responding${NC}"
fi

# Check Neo4j
if curl -s -f http://localhost:7474 &>/dev/null; then
    echo -e "${GREEN}✓ Neo4j is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Neo4j HTTP interface not responding (Bolt may still work)${NC}"
fi

# Check Ollama
if curl -s -f http://localhost:11434 &>/dev/null; then
    echo -e "${GREEN}✓ Ollama is healthy${NC}"
    
    # Pull models if needed
    echo -e "${YELLOW}Ensuring Ollama models are available...${NC}"
    docker compose exec -T ollama ollama list | grep -q mxbai-embed-large || \
        docker compose exec -T ollama ollama pull mxbai-embed-large
    docker compose exec -T ollama ollama list | grep -q llama3:8b || \
        docker compose exec -T ollama ollama pull llama3:8b
    echo -e "${GREEN}✓ Ollama models ready${NC}"
else
    echo -e "${RED}✗ Ollama is not responding${NC}"
fi

# Show running containers
echo -e "${YELLOW}Current container status:${NC}"
docker compose ps

# SUCCESS MESSAGE
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        FindersKeepers v2 Successfully Rebuilt!               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo -e "  ${CYAN}FastAPI Docs:${NC}     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  ${CYAN}Admin Dashboard:${NC}  ${GREEN}http://localhost:3000/monitoring${NC}"
echo -e "  ${CYAN}Frontend UI:${NC}      ${GREEN}http://localhost:3000${NC}"
echo -e "  ${CYAN}Neo4j Browser:${NC}    ${GREEN}http://localhost:7474${NC}"
echo -e "                    Username: ${YELLOW}neo4j${NC} / Password: ${YELLOW}${NEO4J_PASSWORD}${NC}"
echo -e "  ${CYAN}Qdrant Console:${NC}   ${GREEN}http://localhost:6333/dashboard${NC}"
echo -e "  ${CYAN}n8n Workflows:${NC}    ${GREEN}http://localhost:5678${NC}"
echo -e "                    Username: ${YELLOW}${N8N_BASIC_AUTH_USER}${NC}"
echo ""
echo -e "${BLUE}🔧 MCP Server Health:${NC}"
echo -e "  ${CYAN}Check health:${NC}     ${YELLOW}curl http://localhost:8000/api/mcp/health${NC}"
echo -e "  ${CYAN}View sessions:${NC}    ${YELLOW}curl http://localhost:8000/api/mcp/sessions/recent${NC}"
echo ""
echo -e "${BLUE}📊 Monitoring Commands:${NC}"
echo -e "  ${CYAN}View all logs:${NC}       ${YELLOW}docker compose logs -f${NC}"
echo -e "  ${CYAN}FastAPI logs:${NC}        ${YELLOW}docker compose logs -f fastapi${NC}"
echo -e "  ${CYAN}Background process:${NC}  ${YELLOW}docker logs fk2_fastapi --tail 50 | grep Processing${NC}"
echo -e "  ${CYAN}Container stats:${NC}     ${YELLOW}docker stats${NC}"
echo -e "  ${CYAN}GPU usage:${NC}           ${YELLOW}nvidia-smi${NC}"
echo ""
echo -e "${BLUE}🛑 Maintenance:${NC}"
echo -e "  ${CYAN}Stop all:${NC}         ${YELLOW}docker compose down${NC}"
echo -e "  ${CYAN}Restart service:${NC}  ${YELLOW}docker compose restart [service_name]${NC}"
echo -e "  ${CYAN}Rebuild:${NC}          ${YELLOW}./start-fk2-fixed.sh${NC}"
echo ""

if [ "$GPU_AVAILABLE" = true ]; then
    echo -e "${GREEN}✅ GPU acceleration is ACTIVE (RTX 2080 Ti detected)${NC}"
else
    echo -e "${YELLOW}⚠️  Running in CPU mode (GPU not available)${NC}"
fi

echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Background document processing will start in 30 seconds...${NC}"
echo -e "${CYAN}Processing 10 documents every 5 minutes automatically.${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
