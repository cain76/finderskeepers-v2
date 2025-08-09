-- AI GOD MODE Timezone Fix Migration (FINAL CORRECTED)
-- Fixes the datetime timezone inconsistency that prevents session creation
-- This migration converts all timestamp columns to use "timestamp with time zone"
-- 
-- Issue: Mixed use of "timestamp without time zone" and "timestamp with time zone"
-- Solution: Standardize all AI session tables to use timezone-aware timestamps
--
-- Author: bitcain
-- Date: 2025-08-07
-- Reference: FindersKeepers-v2 AI GOD MODE Session Management Fix

-- Migration Version: v1.0.2-timezone-fix-final
BEGIN;

-- Step 1: Drop dependent views and functions first
DROP VIEW IF EXISTS ai_session_analytics;
DROP FUNCTION IF EXISTS search_session_history(TEXT, TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_resume_context(TEXT, TEXT);

-- Step 2: Fix ai_session_memory table (core AI GOD MODE table)
ALTER TABLE ai_session_memory 
    ALTER COLUMN start_time TYPE timestamp with time zone USING start_time AT TIME ZONE 'UTC';

ALTER TABLE ai_session_memory 
    ALTER COLUMN end_time TYPE timestamp with time zone USING end_time AT TIME ZONE 'UTC';

ALTER TABLE ai_session_memory 
    ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC';

ALTER TABLE ai_session_memory 
    ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC';

-- Step 3: Update default values to use timezone-aware functions
ALTER TABLE ai_session_memory 
    ALTER COLUMN start_time SET DEFAULT NOW();

ALTER TABLE ai_session_memory 
    ALTER COLUMN updated_at SET DEFAULT NOW();

ALTER TABLE ai_session_memory 
    ALTER COLUMN created_at SET DEFAULT NOW();

-- Step 4: Update the trigger function to use timezone-aware timestamp
CREATE OR REPLACE FUNCTION update_ai_session_memory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();  -- NOW() returns timestamp with time zone
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 5: Recreate the view with timezone-aware timestamps
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

-- Step 6: Recreate stored functions with proper timezone-aware return types
CREATE OR REPLACE FUNCTION get_resume_context(p_user_id TEXT, p_project TEXT DEFAULT NULL)
RETURNS TABLE (
    session_id TEXT,
    session_summary TEXT,
    accomplishments JSONB,
    failures JSONB,
    conversation_count INTEGER,
    tools_used JSONB,
    files_touched JSONB,
    ai_insights TEXT,
    resume_context TEXT,
    session_duration INTERVAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sm.session_id,
        sm.session_summary,
        sm.accomplishments,
        sm.failures,
        sm.conversation_count,
        sm.tools_used,
        sm.files_touched,
        sm.ai_insights,
        sm.resume_context,
        (sm.end_time - sm.start_time) as session_duration
    FROM ai_session_memory sm
    WHERE sm.user_id = p_user_id
    AND (p_project IS NULL OR sm.project = p_project)
    AND sm.status = 'ended'
    AND sm.session_summary IS NOT NULL
    ORDER BY sm.end_time DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION search_session_history(
    p_user_id TEXT,
    p_search_query TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    session_id TEXT,
    project TEXT,
    start_time timestamp with time zone,
    end_time timestamp with time zone,
    session_summary TEXT,
    ai_insights TEXT,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sm.session_id,
        sm.project,
        sm.start_time,
        sm.end_time,
        sm.session_summary,
        sm.ai_insights,
        GREATEST(
            ts_rank(to_tsvector('english', coalesce(sm.session_summary, '')), plainto_tsquery('english', p_search_query)),
            ts_rank(to_tsvector('english', coalesce(sm.ai_insights, '')), plainto_tsquery('english', p_search_query))
        ) as relevance
    FROM ai_session_memory sm
    WHERE sm.user_id = p_user_id
    AND (
        to_tsvector('english', coalesce(sm.session_summary, '')) @@ plainto_tsquery('english', p_search_query)
        OR to_tsvector('english', coalesce(sm.ai_insights, '')) @@ plainto_tsquery('english', p_search_query)
        OR sm.project ILIKE '%' || p_search_query || '%'
    )
    ORDER BY relevance DESC, sm.end_time DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Step 7: Add comments for documentation
COMMENT ON TABLE ai_session_memory IS 'AI GOD MODE: Persistent memory system with timezone-aware timestamps (Fixed 2025-08-07)';
COMMENT ON COLUMN ai_session_memory.start_time IS 'Session start time (timezone-aware)';
COMMENT ON COLUMN ai_session_memory.end_time IS 'Session end time (timezone-aware)';
COMMENT ON COLUMN ai_session_memory.created_at IS 'Record creation time (timezone-aware)';
COMMENT ON COLUMN ai_session_memory.updated_at IS 'Record last update time (timezone-aware)';

-- Step 8: Verification
DO $$
DECLARE
    start_time_type TEXT;
    end_time_type TEXT;
    updated_at_type TEXT;
    created_at_type TEXT;
BEGIN
    -- Check all timestamp columns are now timezone-aware
    SELECT data_type INTO start_time_type 
    FROM information_schema.columns 
    WHERE table_name = 'ai_session_memory' AND column_name = 'start_time';
    
    SELECT data_type INTO end_time_type 
    FROM information_schema.columns 
    WHERE table_name = 'ai_session_memory' AND column_name = 'end_time';
    
    SELECT data_type INTO updated_at_type 
    FROM information_schema.columns 
    WHERE table_name = 'ai_session_memory' AND column_name = 'updated_at';
    
    SELECT data_type INTO created_at_type 
    FROM information_schema.columns 
    WHERE table_name = 'ai_session_memory' AND column_name = 'created_at';
    
    IF start_time_type = 'timestamp with time zone' AND 
       end_time_type = 'timestamp with time zone' AND 
       updated_at_type = 'timestamp with time zone' AND 
       created_at_type = 'timestamp with time zone' THEN
        RAISE NOTICE '✅ AI GOD MODE Timezone Fix Migration SUCCESSFUL - All timestamps now timezone-aware';
    ELSE
        RAISE EXCEPTION '❌ Migration failed - Some timestamps are still timezone-naive: start_time=%, end_time=%, updated_at=%, created_at=%', start_time_type, end_time_type, updated_at_type, created_at_type;
    END IF;
END $$;

COMMIT;

-- Final verification - run this after migration
SELECT 'AI GOD MODE Timezone Fix Applied Successfully!' as status;
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'ai_session_memory' AND column_name IN ('start_time', 'end_time', 'created_at', 'updated_at')
ORDER BY column_name;
