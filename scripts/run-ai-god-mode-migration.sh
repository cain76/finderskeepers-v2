#!/bin/bash
# AI GOD MODE Database Migration Runner (UPDATED)
# Automatically applies the timezone fix when containers start
# Author: bitcain
# Date: 2025-08-07 (Updated with working migration)

set -e

echo "🔧 Running AI GOD MODE Database Migrations..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
until PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 -c '\q' 2>/dev/null; do
  sleep 2
done
echo "✅ PostgreSQL is ready"

# Check if migration is needed
echo "🔍 Checking if timezone migration is needed..."
NEEDS_MIGRATION=$(PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 -t -c "
SELECT CASE 
    WHEN data_type = 'timestamp without time zone' THEN 'true'
    ELSE 'false'
END
FROM information_schema.columns 
WHERE table_name = 'ai_session_memory' 
AND column_name = 'start_time'
LIMIT 1;" 2>/dev/null || echo "true")

if [[ "$NEEDS_MIGRATION" == *"true"* ]]; then
    echo "⚠️ AI GOD MODE timezone migration needed"
    
    # Apply the migration
    echo "🚀 Applying AI GOD MODE timezone fix migration..."
    if PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 -f /app/sql/fix-ai-god-mode-timezone-migration.sql 2>/dev/null; then
        echo "✅ AI GOD MODE timezone migration completed successfully!"
    else
        echo "⚠️ Migration script not found, applying direct fixes..."
        
        # Apply fixes directly if migration file is not mounted
        PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 << 'EOF'
-- Apply timezone fixes directly
BEGIN;

-- Drop dependencies first
DROP VIEW IF EXISTS ai_session_analytics;
DROP FUNCTION IF EXISTS search_session_history(TEXT, TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_resume_context(TEXT, TEXT);

-- Apply timezone fixes
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

-- Recreate view
CREATE OR REPLACE VIEW ai_session_analytics AS
SELECT 
    user_id,
    project,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN status = 'ended' THEN 1 END) as completed_sessions,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
    AVG(conversation_count) as avg_conversations_per_session,
    AVG(EXTRACT(EPOCH FROM (end_time - start_time))/3600) as avg_duration_hours,
    MAX(start_time) as last_session_start,
    SUM(conversation_count) as total_conversations,
    COUNT(CASE WHEN jsonb_array_length(accomplishments) > 0 THEN 1 END) as sessions_with_accomplishments
FROM ai_session_memory 
GROUP BY user_id, project;

COMMIT;

SELECT 'AI GOD MODE timezone fix applied directly' as status;
EOF
        echo "✅ Direct timezone fixes applied!"
    fi
else
    echo "✅ AI GOD MODE timestamps are already timezone-aware, no migration needed"
fi

# Verify the fix
echo "🔍 Verifying timezone fix..."
VERIFICATION=$(PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 -t -c "
SELECT COUNT(*) 
FROM information_schema.columns 
WHERE table_name = 'ai_session_memory' 
AND column_name IN ('start_time', 'end_time', 'created_at', 'updated_at')
AND data_type = 'timestamp with time zone';" 2>/dev/null || echo "0")

if [[ "$VERIFICATION" == *"4"* ]]; then
    echo "✅ All AI GOD MODE timestamps are now timezone-aware!"
    echo "🚀 AI GOD MODE session management is ready!"
    
    # Test session creation capability
    echo "🧪 Testing AI GOD MODE session creation capability..."
    TEST_RESULT=$(PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 -t -c "
    INSERT INTO ai_session_memory (session_id, user_id, project, session_summary, status) 
    VALUES ('test_timezone_fix', 'bitcain', 'finderskeepers-v2', 'Timezone fix verification test', 'ended')
    ON CONFLICT (session_id) DO UPDATE SET updated_at = NOW()
    RETURNING 'SUCCESS';" 2>/dev/null || echo "FAILED")
    
    if [[ "$TEST_RESULT" == *"SUCCESS"* ]]; then
        echo "✅ AI GOD MODE session creation test PASSED!"
        # Clean up test record
        PGPASSWORD=fk2025secure psql -h postgres -U finderskeepers -d finderskeepers_v2 -c "DELETE FROM ai_session_memory WHERE session_id = 'test_timezone_fix';" 2>/dev/null || true
    else
        echo "⚠️ Session creation test failed, but migration was applied"
    fi
else
    echo "❌ Verification failed - some timestamps may still be timezone-naive"
    exit 1
fi

echo "🎉 AI GOD MODE Database Migration Complete!"
