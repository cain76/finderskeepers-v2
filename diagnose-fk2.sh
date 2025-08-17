#!/bin/bash

# FindersKeepers v2 Container Communication Diagnostic Script
# For bitcain.net infrastructure debugging

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     FindersKeepers v2 - Container Communication Diagnostics    ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if containers are running
echo -e "${YELLOW}Checking container status...${NC}"
docker compose ps

echo ""
echo -e "${YELLOW}Testing inter-container communication...${NC}"
echo ""

# Test PostgreSQL connectivity from FastAPI container
echo -e "${CYAN}1. Testing PostgreSQL connection from FastAPI:${NC}"
if docker compose exec -T fastapi sh -c "apt-get update -qq && apt-get install -qq -y postgresql-client > /dev/null 2>&1 && pg_isready -h fk2_postgres -p 5432 -U finderskeepers" 2>/dev/null; then
    echo -e "${GREEN}   ✓ FastAPI can reach PostgreSQL via container name (fk2_postgres)${NC}"
else
    echo -e "${RED}   ✗ FastAPI cannot reach PostgreSQL via container name${NC}"
    # Try with service name
    if docker compose exec -T fastapi sh -c "pg_isready -h postgres -p 5432 -U finderskeepers" 2>/dev/null; then
        echo -e "${GREEN}   ✓ FastAPI can reach PostgreSQL via service name (postgres)${NC}"
    else
        echo -e "${RED}   ✗ FastAPI cannot reach PostgreSQL${NC}"
    fi
fi

# Test Redis connectivity from FastAPI
echo -e "${CYAN}2. Testing Redis connection from FastAPI:${NC}"
if docker compose exec -T fastapi sh -c "apt-get install -qq -y redis-tools > /dev/null 2>&1 && redis-cli -h fk2_redis ping" 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}   ✓ FastAPI can reach Redis via container name (fk2_redis)${NC}"
else
    echo -e "${RED}   ✗ FastAPI cannot reach Redis via container name${NC}"
    if docker compose exec -T fastapi sh -c "redis-cli -h redis ping" 2>/dev/null | grep -q PONG; then
        echo -e "${GREEN}   ✓ FastAPI can reach Redis via service name (redis)${NC}"
    else
        echo -e "${RED}   ✗ FastAPI cannot reach Redis${NC}"
    fi
fi

# Test Qdrant connectivity from FastAPI
echo -e "${CYAN}3. Testing Qdrant connection from FastAPI:${NC}"
if docker compose exec -T fastapi sh -c "curl -s -f http://fk2_qdrant:6333/collections" &>/dev/null; then
    echo -e "${GREEN}   ✓ FastAPI can reach Qdrant via container name (fk2_qdrant)${NC}"
else
    echo -e "${RED}   ✗ FastAPI cannot reach Qdrant via container name${NC}"
    if docker compose exec -T fastapi sh -c "curl -s -f http://qdrant:6333/collections" &>/dev/null; then
        echo -e "${GREEN}   ✓ FastAPI can reach Qdrant via service name (qdrant)${NC}"
    else
        echo -e "${RED}   ✗ FastAPI cannot reach Qdrant${NC}"
    fi
fi

# Test Neo4j connectivity from FastAPI
echo -e "${CYAN}4. Testing Neo4j connection from FastAPI:${NC}"
if docker compose exec -T fastapi sh -c "apt-get install -qq -y netcat > /dev/null 2>&1 && nc -zv fk2_neo4j 7687" &>/dev/null; then
    echo -e "${GREEN}   ✓ FastAPI can reach Neo4j Bolt port via container name (fk2_neo4j)${NC}"
else
    echo -e "${RED}   ✗ FastAPI cannot reach Neo4j via container name${NC}"
    if docker compose exec -T fastapi sh -c "nc -zv neo4j 7687" &>/dev/null; then
        echo -e "${GREEN}   ✓ FastAPI can reach Neo4j Bolt port via service name (neo4j)${NC}"
    else
        echo -e "${RED}   ✗ FastAPI cannot reach Neo4j${NC}"
    fi
fi

# Test Ollama connectivity from FastAPI
echo -e "${CYAN}5. Testing Ollama connection from FastAPI:${NC}"
if docker compose exec -T fastapi sh -c "curl -s -f http://fk2_ollama:11434" &>/dev/null; then
    echo -e "${GREEN}   ✓ FastAPI can reach Ollama via container name (fk2_ollama)${NC}"
else
    echo -e "${RED}   ✗ FastAPI cannot reach Ollama via container name${NC}"
    if docker compose exec -T fastapi sh -c "curl -s -f http://ollama:11434" &>/dev/null; then
        echo -e "${GREEN}   ✓ FastAPI can reach Ollama via service name (ollama)${NC}"
    else
        echo -e "${RED}   ✗ FastAPI cannot reach Ollama${NC}"
    fi
fi

echo ""
echo -e "${YELLOW}Checking network configuration...${NC}"

# Check if shared-network exists
if docker network inspect shared-network &>/dev/null; then
    echo -e "${GREEN}✓ shared-network exists${NC}"
    
    # List containers on the network
    echo -e "${CYAN}Containers on shared-network:${NC}"
    docker network inspect shared-network --format '{{range .Containers}}  - {{.Name}} ({{.IPv4Address}}){{println}}{{end}}'
else
    echo -e "${RED}✗ shared-network does not exist!${NC}"
fi

echo ""
echo -e "${YELLOW}Testing external connectivity...${NC}"

# Test FastAPI health endpoint
echo -e "${CYAN}6. Testing FastAPI health endpoint:${NC}"
if curl -s -f http://localhost:8000/health &>/dev/null; then
    echo -e "${GREEN}   ✓ FastAPI health endpoint accessible from host${NC}"
else
    echo -e "${YELLOW}   ⚠ FastAPI health endpoint not responding (may be normal)${NC}"
fi

# Test MCP endpoints
echo -e "${CYAN}7. Testing MCP endpoints:${NC}"
if curl -s -f http://localhost:8000/api/mcp/health &>/dev/null; then
    echo -e "${GREEN}   ✓ MCP health endpoint accessible${NC}"
else
    echo -e "${RED}   ✗ MCP health endpoint not accessible${NC}"
fi

echo ""
echo -e "${YELLOW}Environment variable check in FastAPI:${NC}"
docker compose exec -T fastapi sh -c 'echo "POSTGRES_URL: $POSTGRES_URL" | head -c 50; echo "..."'
docker compose exec -T fastapi sh -c 'echo "QDRANT_URL: $QDRANT_URL"'
docker compose exec -T fastapi sh -c 'echo "NEO4J_URI: $NEO4J_URI"'
docker compose exec -T fastapi sh -c 'echo "REDIS_URL: $REDIS_URL" | head -c 50; echo "..."'
docker compose exec -T fastapi sh -c 'echo "OLLAMA_URL: $OLLAMA_URL"'

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                      Diagnostic Summary                        ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

echo ""
echo -e "${YELLOW}Recommended fixes if issues found:${NC}"
echo -e "1. ${CYAN}Run the fixed startup script:${NC}"
echo -e "   ${GREEN}./start-fk2-fixed.sh${NC}"
echo ""
echo -e "2. ${CYAN}If containers can't communicate, check DNS:${NC}"
echo -e "   ${GREEN}docker compose exec fastapi cat /etc/hosts${NC}"
echo ""
echo -e "3. ${CYAN}For persistent issues, rebuild with clean slate:${NC}"
echo -e "   ${GREEN}docker compose down -v${NC}"
echo -e "   ${GREEN}docker network rm shared-network${NC}"
echo -e "   ${GREEN}./start-fk2-fixed.sh${NC}"
echo ""
echo -e "4. ${CYAN}Check container logs for errors:${NC}"
echo -e "   ${GREEN}docker compose logs fastapi | tail -50${NC}"
echo ""
