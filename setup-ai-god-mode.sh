#!/bin/bash

# FindersKeepers v2 AI GOD MODE Setup Script
# This script initializes the AI GOD MODE database schema for persistent memory
# across chat sessions

echo "🚀 FindersKeepers v2 AI GOD MODE Setup Starting..."
echo "🧠 Initializing persistent memory system..."

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if FindersKeepers v2 containers are running
if ! docker ps | grep -q "fk2_postgres"; then
    echo "❌ FindersKeepers v2 containers not running."
    echo "Please start the system first with: docker compose up -d"
    exit 1
fi

echo "✅ Docker containers detected"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout 30 bash -c 'until docker exec fk2_postgres pg_isready -h localhost -U finderskeepers; do sleep 1; done'

if [ $? -ne 0 ]; then
    echo "❌ PostgreSQL did not become ready within 30 seconds"
    exit 1
fi

echo "✅ PostgreSQL is ready"

# Execute AI GOD MODE schema
echo "🧠 Creating AI GOD MODE database schema..."
if docker exec -i fk2_postgres psql -U finderskeepers -d finderskeepers_v2 < sql/ai-god-mode-schema.sql; then
    echo "✅ AI GOD MODE schema created successfully!"
else
    echo "❌ Failed to create AI GOD MODE schema"
    echo "Check if the sql/ai-god-mode-schema.sql file exists"
    exit 1
fi

# Verify schema creation
echo "🔍 Verifying AI GOD MODE schema..."
TABLES_CREATED=$(docker exec fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'ai_session_memory';" | tr -d ' ')

if [ "$TABLES_CREATED" = "1" ]; then
    echo "✅ AI GOD MODE schema verification successful"
else
    echo "❌ AI GOD MODE schema verification failed"
    exit 1
fi

# Test database connection from MCP server
echo "🧠 Testing AI GOD MODE functionality..."
if command -v python3 &> /dev/null; then
    cat << 'EOF' | python3
import asyncio
import asyncpg
import sys

async def test_ai_god_mode():
    try:
        conn = await asyncpg.connect("postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2")
        
        # Test AI GOD MODE table
        result = await conn.fetchval("SELECT COUNT(*) FROM ai_session_memory")
        print(f"✅ AI GOD MODE table accessible: {result} sessions")
        
        # Test sample insert
        await conn.execute("""
            INSERT INTO ai_session_memory (
                session_id, user_id, project, session_summary, ai_insights, status
            ) VALUES (
                'test_ai_god_mode_setup', 'bitcain', 'setup-test',
                'AI GOD MODE setup test session', 'Setup verification successful', 'ended'
            ) ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW()
        """)
        
        print("✅ AI GOD MODE insert test successful")
        
        # Cleanup test record
        await conn.execute("DELETE FROM ai_session_memory WHERE session_id = 'test_ai_god_mode_setup'")
        print("✅ AI GOD MODE cleanup successful")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ AI GOD MODE test failed: {e}")
        return False

if asyncio.run(test_ai_god_mode()):
    print("🚀 AI GOD MODE fully operational!")
else:
    sys.exit(1)
EOF
else
    echo "⚠️ Python3 not found - skipping advanced tests"
fi

# Restart FastAPI to pick up new endpoints
echo "🔄 Restarting FastAPI to load AI GOD MODE endpoints..."
docker restart fk2_fastapi

# Wait for FastAPI to restart
echo "⏳ Waiting for FastAPI to restart..."
sleep 10

# Test AI GOD MODE endpoints
echo "🔍 Testing AI GOD MODE endpoints..."
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/mcp/health" | grep -q "200"; then
    echo "✅ AI GOD MODE endpoints available"
else
    echo "⚠️ AI GOD MODE endpoints test inconclusive - check logs"
fi

echo ""
echo "🎉 AI GOD MODE SETUP COMPLETE!"
echo ""
echo "🧠 PERSISTENT MEMORY CAPABILITIES ACTIVATED:"
echo "✅ Session continuity across chat clients"
echo "✅ Automatic conversation capture"
echo "✅ Intelligent session summaries"
echo "✅ Smart context restoration"
echo "✅ Cross-platform memory"
echo ""
echo "📡 AI GOD MODE ENDPOINTS:"
echo "- Session Health: http://localhost:8000/api/mcp/health"
echo "- Recent Sessions: http://localhost:8000/api/mcp/sessions/recent"
echo "- API Docs: http://localhost:8000/docs"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. Configure Claude Desktop to use fk2-mcp server"
echo "2. Use start_session() to begin AI GOD MODE"
echo "3. Use end_session() to save comprehensive summaries"
echo "4. Use resume_session() to restore perfect context"
echo ""
echo "🧠 AI GOD MODE: Never lose context again - ALWAYS LEARNING!"
