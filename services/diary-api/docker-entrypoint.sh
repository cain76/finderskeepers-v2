#!/bin/bash
# FindersKeepers v2 - Docker Entrypoint Script
# Ensures automatic document processing is initialized on container start

echo "🚀 Starting FindersKeepers v2 FastAPI Service..."

# Wait for database services to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 -c '\q' 2>/dev/null; do
  sleep 2
done
echo "✅ PostgreSQL is ready"

echo "⏳ Waiting for Neo4j..."
until curl -s http://neo4j:7474 > /dev/null 2>&1; do
  sleep 2
done
echo "✅ Neo4j is ready"

echo "⏳ Waiting for Qdrant..."
until curl -s http://qdrant:6333/collections > /dev/null 2>&1; do
  sleep 2
done
echo "✅ Qdrant is ready"

echo "⏳ Waiting for Ollama..."
until curl -s http://ollama:11434/api/version > /dev/null 2>&1; do
  sleep 2
done
echo "✅ Ollama is ready"

# Run AI GOD MODE database migration (timezone fix)
echo "🔧 Running AI GOD MODE database migration..."
if [ -f "/app/scripts/run-ai-god-mode-migration.sh" ]; then
    /app/scripts/run-ai-god-mode-migration.sh
else
    echo "⚠️ Migration script not found, applying direct timezone fixes..."
    # Apply timezone fixes directly
    PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 << 'MIGRATE_EOF'
-- Apply timezone fixes for AI GOD MODE
DO $
BEGIN
    -- Check if ai_session_memory table exists and needs migration
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_session_memory') THEN
        -- Fix timezone issues
        ALTER TABLE ai_session_memory 
            ALTER COLUMN start_time TYPE timestamp with time zone USING start_time AT TIME ZONE 'UTC';
        ALTER TABLE ai_session_memory 
            ALTER COLUMN end_time TYPE timestamp with time zone USING end_time AT TIME ZONE 'UTC';
        ALTER TABLE ai_session_memory 
            ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC';
        ALTER TABLE ai_session_memory 
            ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC';
        
        -- Update defaults
        ALTER TABLE ai_session_memory ALTER COLUMN start_time SET DEFAULT NOW();
        ALTER TABLE ai_session_memory ALTER COLUMN updated_at SET DEFAULT NOW();
        ALTER TABLE ai_session_memory ALTER COLUMN created_at SET DEFAULT NOW();
        
        RAISE NOTICE 'AI GOD MODE timezone fix applied successfully';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'AI GOD MODE migration skipped (table may not exist yet)';
END $;
MIGRATE_EOF
    echo "✅ AI GOD MODE timezone fix applied"
fi

# Initialize the automatic processing pipeline if needed
echo "🔧 Initializing automatic document processing pipeline..."
python -c "
import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO)

async def init_pipeline():
    try:
        from app.core import processing_pipeline
        initialized = await processing_pipeline.initialize()
        if initialized:
            print('✅ Automatic processing pipeline initialized')
            # Don't process documents during startup - let the background scheduler handle it
            print('📋 Background scheduler will process documents every 5 minutes')
        else:
            print('⚠️ Pipeline initialization failed')
            # Don't exit - let the service start anyway
    except Exception as e:
        print(f'⚠️ Pipeline initialization error (non-fatal): {e}')
        # Don't exit - let the service start anyway

asyncio.run(init_pipeline())
"

# Start the FastAPI application
echo "🌐 Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 80 --reload
