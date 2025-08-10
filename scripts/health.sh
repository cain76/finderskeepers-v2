#!/bin/bash
# FindersKeepers v2 - System Health Check Script
# Comprehensive health monitoring for all FK2 services

set -e

echo "==================================="
echo "FindersKeepers v2 Health Check"
echo "==================================="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local name=$1
    local check_cmd=$2
    printf "%-20s" "$name:"
    if eval "$check_cmd" &>/dev/null; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

# Overall health status
HEALTHY=true

echo "🐳 Docker Services"
echo "------------------"

# Check if services are running
SERVICES=("postgres" "qdrant" "neo4j" "redis" "ollama" "fastapi" "frontend")
for service in "${SERVICES[@]}"; do
    container_name="fk2_$service"
    printf "%-20s" "$service:"
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        status=$(docker inspect -f '{{.State.Status}}' "$container_name" 2>/dev/null || echo "unknown")
        if [ "$status" = "running" ]; then
            echo -e "${GREEN}✅ Running${NC}"
        else
            echo -e "${YELLOW}⚠️ Status: $status${NC}"
            HEALTHY=false
        fi
    else
        echo -e "${RED}❌ Not Found${NC}"
        HEALTHY=false
    fi
done

echo ""
echo "🔌 Service Endpoints"
echo "--------------------"

check_service "PostgreSQL" "docker compose exec -T postgres pg_isready -U finderskeepers"
check_service "Qdrant API" "curl -s -f http://localhost:6333/collections"
check_service "Neo4j Bolt" "curl -s -f http://localhost:7474"
check_service "Redis" "docker compose exec -T redis redis-cli ping"
check_service "FastAPI" "curl -s -f http://localhost:8000/health"
check_service "Ollama" "curl -s -f http://localhost:11434/api/version"

echo ""
echo "📊 Data Statistics"
echo "------------------"

# PostgreSQL stats
echo -n "Documents: "
DOC_COUNT=$(docker compose exec -T postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM documents;" 2>/dev/null | xargs || echo "0")
echo "$DOC_COUNT"

echo -n "Conversations: "
CONV_COUNT=$(docker compose exec -T postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM conversation_messages;" 2>/dev/null | xargs || echo "0")
echo "$CONV_COUNT"

echo -n "Sessions: "
SESS_COUNT=$(docker compose exec -T postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM agent_sessions;" 2>/dev/null | xargs || echo "0")
echo "$SESS_COUNT"

# Qdrant stats
echo -n "Vectors: "
VECTOR_COUNT=$(curl -s http://localhost:6333/collections/fk2_documents 2>/dev/null | jq -r '.result.points_count' || echo "0")
echo "$VECTOR_COUNT"

# Neo4j stats
echo -n "Graph Nodes: "
NODE_COUNT=$(curl -s -X POST http://localhost:7474/db/neo4j/tx/commit \
    -H "Content-Type: application/json" \
    -u "neo4j:fk2025neo4j" \
    -d '{"statements": [{"statement": "MATCH (n) RETURN COUNT(n) as count"}]}' 2>/dev/null | \
    jq -r '.results[0].data[0].row[0]' || echo "0")
echo "$NODE_COUNT"

echo ""
echo "🤖 AI Models"
echo "------------"

# Check Ollama models
MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | jq -r '.models[].name' || echo "")

echo -n "mxbai-embed-large: "
if echo "$MODELS" | grep -q "mxbai-embed-large"; then
    echo -e "${GREEN}✅ Available${NC}"
else
    echo -e "${RED}❌ Not Found${NC}"
    HEALTHY=false
fi

echo -n "llama3:8b: "
if echo "$MODELS" | grep -q "llama3:8b"; then
    echo -e "${GREEN}✅ Available${NC}"
else
    echo -e "${YELLOW}⚠️ Not Found (optional)${NC}"
fi

echo ""
echo "🔍 API Endpoints Test"
echo "---------------------"

# Test critical endpoints
echo -n "Vector Search: "
if curl -s -X POST http://localhost:8000/api/search/vector \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 1}' | grep -q "success" 2>/dev/null; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
    HEALTHY=false
fi

echo -n "Knowledge Search: "
if curl -s -X POST http://localhost:8000/api/knowledge/search \
    -H "Content-Type: application/json" \
    -d '{"query": "test", "limit": 1}' | grep -q "results" 2>/dev/null; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${YELLOW}⚠️ Not Responding${NC}"
fi

echo -n "MCP Session API: "
if curl -s http://localhost:8000/api/mcp/health | grep -q "healthy" 2>/dev/null; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${YELLOW}⚠️ Not Available${NC}"
fi

echo ""
echo "💾 Disk Usage"
echo "-------------"

# Check Docker volume sizes
echo "Docker Volumes:"
docker system df -v 2>/dev/null | grep -E "postgres_data|qdrant_data|neo4j_data|ollama_data" | awk '{printf "  %-20s %s\n", $1":", $3}'

echo ""
echo "==================================="
if [ "$HEALTHY" = true ]; then
    echo -e "${GREEN}✅ System Status: HEALTHY${NC}"
    echo "All critical services are operational"
else
    echo -e "${RED}❌ System Status: UNHEALTHY${NC}"
    echo "Some services need attention"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker compose logs [service_name]"
    echo "  2. Restart services: docker compose restart"
    echo "  3. Rebuild if needed: docker compose up -d --build"
fi
echo "==================================="

# Exit with appropriate code
if [ "$HEALTHY" = true ]; then
    exit 0
else
    exit 1
fi
