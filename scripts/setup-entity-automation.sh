#!/bin/bash
# Setup automatic entity extraction for FindersKeepers v2
# This script configures database triggers and n8n workflows

echo "🚀 Setting up FindersKeepers v2 Automatic Entity Extraction"
echo "========================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if services are running
echo "1️⃣ Checking services..."

if ! docker ps | grep -q fk2_postgres; then
    echo -e "${RED}❌ PostgreSQL container not running${NC}"
    echo "Please run: docker compose up -d"
    exit 1
fi

if ! docker ps | grep -q fk2_n8n; then
    echo -e "${YELLOW}⚠️  n8n container not running${NC}"
    echo "n8n workflows won't work until started"
fi

echo -e "${GREEN}✅ Services check complete${NC}"
echo ""

# Apply database changes
echo "2️⃣ Applying database automation..."

# Copy SQL file to container
docker cp /media/cain/linux_storage/projects/finderskeepers-v2/sql/entity_extraction_automation.sql fk2_postgres:/tmp/

# Execute SQL
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -f /tmp/entity_extraction_automation.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database triggers and functions created${NC}"
else
    echo -e "${RED}❌ Failed to create database automation${NC}"
    exit 1
fi

echo ""
echo "3️⃣ Testing entity extraction API..."

# Test if FastAPI endpoint exists
RESPONSE=$(curl -s -X GET "http://localhost:8000/api/entities/status/00000000-0000-0000-0000-000000000000" 2>/dev/null)

if echo "$RESPONSE" | jq -e '.document_id' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Entity extraction API is available${NC}"
else
    echo -e "${YELLOW}⚠️  Entity extraction API not responding${NC}"
    echo "You may need to restart FastAPI: docker compose restart fk2_fastapi"
fi

echo ""
echo "4️⃣ Creating test document to verify automation..."

# Create a test document
TEST_DOC=$(curl -s -X POST "http://localhost:8000/api/docs/ingest" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Entity Extraction Test Document",
        "content": "This document tests automatic entity extraction. It mentions Docker, PostgreSQL, n8n, and FindersKeepers v2. The system should automatically extract these technologies as entities.",
        "project": "finderskeepers-v2",
        "doc_type": "test",
        "tags": ["automation", "test"],
        "metadata": {"test": true}
    }' 2>/dev/null)

if echo "$TEST_DOC" | jq -e '.document_id' > /dev/null 2>&1; then
    DOC_ID=$(echo "$TEST_DOC" | jq -r '.document_id')
    echo -e "${GREEN}✅ Test document created: $DOC_ID${NC}"
    
    # Wait a moment for trigger to fire
    echo "   Waiting 5 seconds for automation to process..."
    sleep 5
    
    # Check if entities were extracted
    STATUS=$(curl -s -X GET "http://localhost:8000/api/entities/status/$DOC_ID" 2>/dev/null)
    ENTITY_COUNT=$(echo "$STATUS" | jq -r '.entity_count // 0')
    
    if [ "$ENTITY_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Automation working! Found $ENTITY_COUNT entities${NC}"
    else
        echo -e "${YELLOW}⚠️  No entities extracted yet${NC}"
        echo "   This might be normal if n8n workflow isn't active"
        echo "   You can manually extract: curl -X POST http://localhost:8000/api/entities/extract -d '{\"document_id\": \"$DOC_ID\"}'"
    fi
else
    echo -e "${YELLOW}⚠️  Could not create test document${NC}"
fi

echo ""
echo "📊 Setup Summary:"
echo "-----------------"
echo -e "${GREEN}✅ Database triggers created${NC}"
echo -e "${GREEN}✅ Processing queue table created${NC}"
echo -e "${GREEN}✅ System logs table created${NC}"
echo -e "${GREEN}✅ Monitoring view created${NC}"
echo ""

# Show current status
echo "📈 Current Entity Extraction Status:"
docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "
SELECT 
    extraction_status,
    COUNT(*) as documents,
    COALESCE(SUM(entity_count), 0) as total_entities
FROM v_entity_extraction_status
GROUP BY extraction_status
ORDER BY extraction_status;"

echo ""
echo "🎯 Next Steps:"
echo "1. Import n8n workflow: /n8n-workflows/auto-entity-extraction.json"
echo "2. Configure PostgreSQL credentials in n8n"
echo "3. Activate the workflow"
echo "4. All new documents will automatically have entities extracted!"
echo ""
echo "📚 Full documentation: /docs/ENTITY_EXTRACTION_AUTOMATION.md"
echo ""
echo "✨ Automatic entity extraction is ready to use!"