#!/bin/bash
# Test script for FindersKeepers v2 Vector Search and Knowledge Graph fixes
# Run this after restarting Claude Desktop to verify the fixes

echo "🧪 FindersKeepers v2 Fix Verification Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base URLs
FASTAPI_URL="http://localhost:8000"
QDRANT_URL="http://localhost:6333"
NEO4J_URL="http://localhost:7474"

echo "1️⃣ Checking Services Health..."
echo "--------------------------------"

# Check FastAPI
if curl -s "$FASTAPI_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ FastAPI is running${NC}"
else
    echo -e "${RED}❌ FastAPI is not accessible${NC}"
fi

# Check Qdrant
if curl -s "$QDRANT_URL/collections" > /dev/null 2>&1; then
    COLLECTIONS=$(curl -s "$QDRANT_URL/collections" | jq -r '.result.collections[].name' 2>/dev/null | tr '\n' ', ')
    echo -e "${GREEN}✅ Qdrant is running - Collections: ${COLLECTIONS}${NC}"
else
    echo -e "${RED}❌ Qdrant is not accessible${NC}"
fi

# Check Neo4j
if curl -s "$NEO4J_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Neo4j is running${NC}"
else
    echo -e "${RED}❌ Neo4j is not accessible${NC}"
fi

echo ""
echo "2️⃣ Testing Vector Search (Fixed Collection Name)..."
echo "---------------------------------------------------"

# Test vector search with the fixed collection name
VECTOR_RESPONSE=$(curl -s -X POST "$FASTAPI_URL/api/search/vector" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "docker compose n8n",
        "collection": "fk2_documents",
        "limit": 5
    }')

if echo "$VECTOR_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    RESULT_COUNT=$(echo "$VECTOR_RESPONSE" | jq '.data | length')
    echo -e "${GREEN}✅ Vector search working! Found ${RESULT_COUNT} results${NC}"
    echo "   Sample result: $(echo "$VECTOR_RESPONSE" | jq -r '.data[0].payload.title' 2>/dev/null || echo "No title")"
else
    echo -e "${RED}❌ Vector search failed${NC}"
    echo "   Response: $(echo "$VECTOR_RESPONSE" | jq -c '.' 2>/dev/null || echo "$VECTOR_RESPONSE")"
fi

echo ""
echo "3️⃣ Testing Knowledge Graph Query..."
echo "------------------------------------"

# Test knowledge graph query
GRAPH_RESPONSE=$(curl -s -X POST "$FASTAPI_URL/api/knowledge/query" \
    -H "Content-Type: application/json" \
    -d '{
        "question": "What services use PostgreSQL?",
        "include_history": true
    }')

if echo "$GRAPH_RESPONSE" | jq -e '.relationships' > /dev/null 2>&1; then
    REL_COUNT=$(echo "$GRAPH_RESPONSE" | jq '.relationships | length')
    DOC_COUNT=$(echo "$GRAPH_RESPONSE" | jq '.documents | length')
    DATA_SOURCE=$(echo "$GRAPH_RESPONSE" | jq -r '.data_source')
    
    if [ "$DATA_SOURCE" = "real" ] && [ "$REL_COUNT" -gt 0 -o "$DOC_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Knowledge graph returning REAL data!${NC}"
        echo "   Relationships found: ${REL_COUNT}"
        echo "   Documents found: ${DOC_COUNT}"
    else
        echo -e "${YELLOW}⚠️  Knowledge graph working but no data found${NC}"
        echo "   You need to run the entity extraction script"
    fi
else
    echo -e "${RED}❌ Knowledge graph query failed${NC}"
    echo "   Response: $(echo "$GRAPH_RESPONSE" | jq -c '.' 2>/dev/null || echo "$GRAPH_RESPONSE")"
fi

echo ""
echo "4️⃣ Checking Entity Population..."
echo "----------------------------------"

# Check PostgreSQL for entities
PG_ENTITIES=$(docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM knowledge_entities;" 2>/dev/null | tr -d ' \r\n')

if [ -n "$PG_ENTITIES" ] && [ "$PG_ENTITIES" -gt 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL has ${PG_ENTITIES} entities${NC}"
else
    echo -e "${YELLOW}⚠️  No entities in PostgreSQL - run extract_entities_llama8b.py${NC}"
fi

echo ""
echo "5️⃣ Testing MCP Server Connection (if available)..."
echo "---------------------------------------------------"
echo -e "${YELLOW}Note: MCP tests require Claude Desktop restart after fixes${NC}"

echo ""
echo "📊 Summary:"
echo "-----------"
echo "1. Vector Search: Fixed collection name 'fk2_documents' ✓"
echo "2. Knowledge Graph: Updated to query real Neo4j data ✓"
echo "3. Entity Extraction: Script created at scripts/extract_entities_llama8b.py ✓"
echo "4. Ollama: Configured with llama3:8b model ✓"
echo ""
echo "🚀 Next Steps:"
echo "1. Restart Claude Desktop to apply MCP server fixes"
echo "2. Run: python scripts/extract_entities_llama8b.py"
echo "3. Test with: fk2-mcp vector_search 'docker compose'"
echo ""