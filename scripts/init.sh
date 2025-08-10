#!/bin/bash
# FindersKeepers v2 - Full System Initialization Script
# This script sets up the complete FK2 system from scratch

set -e  # Exit on error

echo "==================================="
echo "FindersKeepers v2 Initialization"
echo "==================================="

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📍 Working directory: $PROJECT_ROOT"

# Check Docker and Docker Compose
echo "🔍 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose v2 is not installed. Please install Docker Compose v2."
    exit 1
fi

echo "✅ Docker and Docker Compose v2 found"

# Create shared network if it doesn't exist
echo "🔗 Creating shared network..."
docker network create shared-network 2>/dev/null || echo "  Network already exists"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down

# Build and start all services
echo "🚀 Starting all services..."
docker compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# PostgreSQL
echo -n "  PostgreSQL: "
if docker compose exec -T postgres pg_isready -U finderskeepers &>/dev/null; then
    echo "✅"
else
    echo "⚠️ Not ready yet"
fi

# Qdrant
echo -n "  Qdrant: "
if curl -s http://localhost:6333/collections &>/dev/null; then
    echo "✅"
    # Initialize Qdrant collection if needed
    echo "  📦 Checking Qdrant collections..."
    COLLECTIONS=$(curl -s http://localhost:6333/collections | jq -r '.result.collections[].name' 2>/dev/null || echo "")
    if [[ ! "$COLLECTIONS" =~ "fk2_documents" ]]; then
        echo "  📦 Creating fk2_documents collection..."
        curl -X PUT "http://localhost:6333/collections/fk2_documents" \
            -H "Content-Type: application/json" \
            -d '{
                "vectors": {
                    "size": 1024,
                    "distance": "Cosine"
                }
            }' &>/dev/null
        echo "  ✅ Collection created"
    else
        echo "  ✅ Collection exists"
    fi
else
    echo "⚠️ Not ready yet"
fi

# Neo4j
echo -n "  Neo4j: "
if curl -s http://localhost:7474 &>/dev/null; then
    echo "✅"
else
    echo "⚠️ Not ready yet"
fi

# FastAPI
echo -n "  FastAPI: "
if curl -s http://localhost:8000/health &>/dev/null; then
    echo "✅"
else
    echo "⚠️ Not ready yet"
fi

# Redis
echo -n "  Redis: "
if docker compose exec -T redis redis-cli ping &>/dev/null; then
    echo "✅"
else
    echo "⚠️ Not ready yet"
fi

# Ollama
echo -n "  Ollama: "
if curl -s http://localhost:11434/api/version &>/dev/null; then
    echo "✅"
    # Pull required models if not present
    echo "  🤖 Checking AI models..."
    MODELS=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "")
    
    if [[ ! "$MODELS" =~ "mxbai-embed-large" ]]; then
        echo "  📥 Pulling mxbai-embed-large (this may take a few minutes)..."
        docker compose exec -T ollama ollama pull mxbai-embed-large
    else
        echo "  ✅ mxbai-embed-large ready"
    fi
    
    if [[ ! "$MODELS" =~ "llama3:8b" ]]; then
        echo "  📥 Pulling llama3:8b (this may take 10-15 minutes)..."
        docker compose exec -T ollama ollama pull llama3:8b
    else
        echo "  ✅ llama3:8b ready"
    fi
else
    echo "⚠️ Not ready yet"
fi

# Initialize database indexes
echo "🗄️ Creating database indexes..."
docker compose exec -T postgres psql -U finderskeepers -d finderskeepers_v2 <<EOF 2>/dev/null || true
-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project);
CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session ON conversation_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_session ON agent_actions(session_id);
EOF
echo "  ✅ PostgreSQL indexes created"

# Initialize Neo4j indexes
echo "  🔗 Creating Neo4j indexes..."
curl -X POST http://localhost:7474/db/neo4j/tx/commit \
    -H "Content-Type: application/json" \
    -u "neo4j:fk2025neo4j" \
    -d '{
        "statements": [
            {"statement": "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)"},
            {"statement": "CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.id)"},
            {"statement": "CALL db.index.fulltext.createNodeIndex(\"entity_search\", [\"Entity\", \"Document\"], [\"name\", \"title\", \"content\"]) YIELD indexName RETURN indexName"}
        ]
    }' &>/dev/null 2>&1 || echo "  ℹ️ Neo4j indexes may already exist"

echo ""
echo "==================================="
echo "✨ Initialization Complete!"
echo "==================================="
echo ""
echo "🌐 Access Points:"
echo "  - FastAPI Docs: http://localhost:8000/docs"
echo "  - Neo4j Browser: http://localhost:7474"
echo "  - Qdrant Dashboard: http://localhost:6333/dashboard"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "🔍 Health Check:"
echo "  Run: ./scripts/health.sh"
echo ""
echo "📊 View Logs:"
echo "  docker compose logs -f [service_name]"
echo ""
echo "🧠 MCP Server:"
echo "  Configure in Claude Desktop with:"
echo "  Command: $PROJECT_ROOT/services/mcp-session-server/.venv/bin/python"
echo "  Args: $PROJECT_ROOT/services/mcp-session-server/src/fk2_mcp_server.py"
echo ""
echo "🚀 FindersKeepers v2 is ready for AI GOD MODE!"
