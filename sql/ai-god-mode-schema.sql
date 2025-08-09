-- AI GOD MODE Database Schema - Enhanced Session Memory System
-- Creates the ai_session_memory table for persistent AI memory across chat sessions
-- This enables true session continuity and eliminates context window limitations!
-- 
-- FIXED: All timestamps now use "timestamp with time zone" for consistency
-- Date: 2025-08-07 - bitcain timezone fix

-- Create enhanced AI session memory table
CREATE TABLE IF NOT EXISTS ai_session_memory (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    session_summary TEXT,
    accomplishments JSONB DEFAULT '[]'::jsonb,
    failures JSONB DEFAULT '[]'::jsonb,
    context_snapshot JSONB DEFAULT '{}'::jsonb,
    conversation_count INTEGER DEFAULT 0,
    tools_used JSONB DEFAULT '[]'::jsonb,
    files_touched JSONB DEFAULT '[]'::jsonb,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'ended', 'paused', 'error')),
    ai_insights TEXT,
    resume_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_user_id ON ai_session_memory(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_project ON ai_session_memory(project);
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_status ON ai_session_memory(status);
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_start_time ON ai_session_memory(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_end_time ON ai_session_memory(end_time DESC);

-- Create GIN index for JSONB fields for fast searching
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_accomplishments_gin ON ai_session_memory USING GIN(accomplishments);
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_context_gin ON ai_session_memory USING GIN(context_snapshot);
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_tools_gin ON ai_session_memory USING GIN(tools_used);

-- Create full-text search index for summaries
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_summary_fts ON ai_session_memory USING GIN(to_tsvector('english', coalesce(session_summary, '')));
CREATE INDEX IF NOT EXISTS idx_ai_session_memory_insights_fts ON ai_session_memory USING GIN(to_tsvector('english', coalesce(ai_insights, '')));

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ai_session_memory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and create new one
DROP TRIGGER IF EXISTS tr_ai_session_memory_updated_at ON ai_session_memory;
CREATE TRIGGER tr_ai_session_memory_updated_at
    BEFORE UPDATE ON ai_session_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_session_memory_updated_at();

-- Create view for easy session analytics
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

-- Create function to get session context for resume
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

-- Create function to search session history
CREATE OR REPLACE FUNCTION search_session_history(
    p_user_id TEXT,
    p_search_query TEXT,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    session_id TEXT,
    project TEXT,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
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

-- Insert sample data for testing (optional)
INSERT INTO ai_session_memory (
    session_id, user_id, project, session_summary, accomplishments, ai_insights, status, conversation_count
) VALUES (
    'fk2_sess_sample_ai_god_mode',
    'bitcain',
    'finderskeepers-v2',
    'Sample AI GOD MODE session for testing persistent memory capabilities',
    '[{"description": "Set up AI GOD MODE persistent memory system", "timestamp": "2025-08-07T16:00:00Z"}]'::jsonb,
    'AI GOD MODE system successfully implemented with persistent memory across chat sessions',
    'ended',
    25
) ON CONFLICT (session_id) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ai_session_memory TO finderskeepers;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO finderskeepers;

-- Verification queries
-- SELECT 'AI GOD MODE Schema Created Successfully!' as status;
-- SELECT COUNT(*) as total_ai_sessions FROM ai_session_memory;
-- SELECT * FROM ai_session_analytics;

COMMENT ON TABLE ai_session_memory IS 'AI GOD MODE: Persistent memory system for chat sessions across all MCP clients (timezone-aware timestamps)';
COMMENT ON COLUMN ai_session_memory.start_time IS 'Session start time (timezone-aware) - FIXED 2025-08-07';
COMMENT ON COLUMN ai_session_memory.end_time IS 'Session end time (timezone-aware) - FIXED 2025-08-07';
COMMENT ON COLUMN ai_session_memory.created_at IS 'Record creation time (timezone-aware) - FIXED 2025-08-07';
COMMENT ON COLUMN ai_session_memory.updated_at IS 'Record last update time (timezone-aware) - FIXED 2025-08-07';
COMMENT ON COLUMN ai_session_memory.session_summary IS 'Comprehensive AI-generated summary for perfect context restoration';
COMMENT ON COLUMN ai_session_memory.accomplishments IS 'JSON array of accomplishments achieved during the session';
COMMENT ON COLUMN ai_session_memory.failures IS 'JSON array of issues/failures encountered for learning';
COMMENT ON COLUMN ai_session_memory.context_snapshot IS 'JSON snapshot of session context and metadata';
COMMENT ON COLUMN ai_session_memory.resume_context IS 'Condensed context for quick session resumption';
COMMENT ON VIEW ai_session_analytics IS 'Analytics view for AI GOD MODE session performance tracking (timezone-aware)';
COMMENT ON FUNCTION get_resume_context IS 'Function to retrieve the best session context for resuming';
COMMENT ON FUNCTION search_session_history IS 'Full-text search function for finding relevant past sessions';
