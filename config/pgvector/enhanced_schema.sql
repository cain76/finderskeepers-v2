-- FindersKeepers v2 Enhanced Database Schema
-- Enhanced conversation tracking, code snippets, todos, and file operations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================
-- CODE SNIPPETS TABLE
-- ================================================
CREATE TABLE IF NOT EXISTS code_snippets (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    language VARCHAR(100) NOT NULL DEFAULT 'unknown',
    code TEXT NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'block', -- 'block', 'inline', 'function', 'class'
    lines INTEGER DEFAULT 1,
    content_context TEXT, -- Context where this code was found
    message_type VARCHAR(50), -- 'user_input', 'assistant_response', etc.
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    project VARCHAR(255) DEFAULT 'finderskeepers-v2',
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- Vector embedding for code similarity search
    code_embedding vector(1024),
    
    CONSTRAINT fk_code_snippets_session 
        FOREIGN KEY (session_id) 
        REFERENCES agent_sessions(session_id) 
        ON DELETE CASCADE
);

-- Indexes for code snippets
CREATE INDEX IF NOT EXISTS idx_code_snippets_session ON code_snippets(session_id);
CREATE INDEX IF NOT EXISTS idx_code_snippets_language ON code_snippets(language);
CREATE INDEX IF NOT EXISTS idx_code_snippets_type ON code_snippets(type);
CREATE INDEX IF NOT EXISTS idx_code_snippets_extracted ON code_snippets(extracted_at);

-- ================================================
-- TODO ITEMS TABLE
-- ================================================
CREATE TABLE IF NOT EXISTS todo_items (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    task TEXT NOT NULL,
    type VARCHAR(50) NOT NULL DEFAULT 'todo', -- 'todo', 'note', 'fixme', 'action'
    priority VARCHAR(20) NOT NULL DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    status VARCHAR(20) NOT NULL DEFAULT 'open', -- 'open', 'in_progress', 'completed', 'cancelled'
    content_context TEXT, -- Context where this todo was found
    message_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    project VARCHAR(255) DEFAULT 'finderskeepers-v2',
    assigned_to VARCHAR(255),
    due_date TIMESTAMP WITH TIME ZONE,
    tags TEXT[], -- Array of tags
    
    CONSTRAINT fk_todo_items_session 
        FOREIGN KEY (session_id) 
        REFERENCES agent_sessions(session_id) 
        ON DELETE CASCADE
);

-- Indexes for todo items
CREATE INDEX IF NOT EXISTS idx_todo_items_session ON todo_items(session_id);
CREATE INDEX IF NOT EXISTS idx_todo_items_status ON todo_items(status);
CREATE INDEX IF NOT EXISTS idx_todo_items_priority ON todo_items(priority);
CREATE INDEX IF NOT EXISTS idx_todo_items_created ON todo_items(created_at);
CREATE INDEX IF NOT EXISTS idx_todo_items_due ON todo_items(due_date);

-- ================================================
-- FILE OPERATIONS TABLE
-- ================================================
CREATE TABLE IF NOT EXISTS file_operations (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    operation VARCHAR(50) NOT NULL DEFAULT 'reference', -- 'create', 'read', 'update', 'delete', 'reference'
    context TEXT, -- Context around the file operation
    content_context TEXT, -- Content where this file operation was mentioned
    message_type VARCHAR(50),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    project VARCHAR(255) DEFAULT 'finderskeepers-v2',
    file_type VARCHAR(100), -- Detected file extension/type
    file_size_bytes BIGINT,
    
    CONSTRAINT fk_file_operations_session 
        FOREIGN KEY (session_id) 
        REFERENCES agent_sessions(session_id) 
        ON DELETE CASCADE
);

-- Indexes for file operations
CREATE INDEX IF NOT EXISTS idx_file_operations_session ON file_operations(session_id);
CREATE INDEX IF NOT EXISTS idx_file_operations_path ON file_operations(file_path);
CREATE INDEX IF NOT EXISTS idx_file_operations_operation ON file_operations(operation);
CREATE INDEX IF NOT EXISTS idx_file_operations_detected ON file_operations(detected_at);

-- ================================================
-- CONVERSATION SUMMARIES TABLE
-- ================================================
CREATE TABLE IF NOT EXISTS conversation_summaries (
    session_id VARCHAR(255) PRIMARY KEY,
    message_count INTEGER NOT NULL DEFAULT 0,
    total_code_snippets INTEGER NOT NULL DEFAULT 0,
    total_todo_items INTEGER NOT NULL DEFAULT 0,
    total_file_operations INTEGER NOT NULL DEFAULT 0,
    client_info JSONB,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    conversation_text TEXT, -- Full conversation for context search
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    project VARCHAR(255) DEFAULT 'finderskeepers-v2',
    
    -- Vector embedding for conversation similarity
    conversation_embedding vector(1024),
    
    CONSTRAINT fk_conversation_summaries_session 
        FOREIGN KEY (session_id) 
        REFERENCES agent_sessions(session_id) 
        ON DELETE CASCADE
);

-- Indexes for conversation summaries
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_processed ON conversation_summaries(processed_at);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_start ON conversation_summaries(start_time);
CREATE INDEX IF NOT EXISTS idx_conversation_summaries_message_count ON conversation_summaries(message_count);

-- ================================================
-- ENHANCED CONVERSATION MESSAGES TABLE
-- ================================================
-- Add vector embedding column to existing conversation_messages if it doesn't exist
ALTER TABLE conversation_messages 
ADD COLUMN IF NOT EXISTS content_embedding vector(1024);

-- Add additional useful columns
ALTER TABLE conversation_messages 
ADD COLUMN IF NOT EXISTS tokens_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS processing_time_ms INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS extracted_entities JSONB,
ADD COLUMN IF NOT EXISTS sentiment_score FLOAT DEFAULT 0.0;

-- ================================================
-- VECTOR SIMILARITY SEARCH FUNCTIONS
-- ================================================

-- Function to find similar code snippets
CREATE OR REPLACE FUNCTION find_similar_code(
    query_embedding vector(1024),
    limit_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id VARCHAR(255),
    session_id VARCHAR(255),
    language VARCHAR(100),
    code TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cs.id,
        cs.session_id,
        cs.language,
        cs.code,
        1 - (cs.code_embedding <=> query_embedding) AS similarity_score
    FROM code_snippets cs
    WHERE cs.code_embedding IS NOT NULL
        AND 1 - (cs.code_embedding <=> query_embedding) >= similarity_threshold
    ORDER BY cs.code_embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to find similar conversations
CREATE OR REPLACE FUNCTION find_similar_conversations(
    query_embedding vector(1024),
    limit_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    session_id VARCHAR(255),
    conversation_text TEXT,
    message_count INTEGER,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cs.session_id,
        cs.conversation_text,
        cs.message_count,
        1 - (cs.conversation_embedding <=> query_embedding) AS similarity_score
    FROM conversation_summaries cs
    WHERE cs.conversation_embedding IS NOT NULL
        AND 1 - (cs.conversation_embedding <=> query_embedding) >= similarity_threshold
    ORDER BY cs.conversation_embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- ANALYTICS VIEWS
-- ================================================

-- Session productivity overview
CREATE OR REPLACE VIEW session_productivity AS
SELECT 
    s.session_id,
    s.agent_type,
    s.user_id,
    s.project,
    s.start_time,
    s.end_time,
    EXTRACT(EPOCH FROM (s.end_time - s.start_time))/60 as duration_minutes,
    COUNT(DISTINCT cs.id) as code_snippets_count,
    COUNT(DISTINCT t.id) as todo_items_count,
    COUNT(DISTINCT fo.id) as file_operations_count,
    COUNT(DISTINCT cm.id) as messages_count
FROM agent_sessions s
LEFT JOIN code_snippets cs ON s.session_id = cs.session_id
LEFT JOIN todo_items t ON s.session_id = t.session_id
LEFT JOIN file_operations fo ON s.session_id = fo.session_id
LEFT JOIN conversation_messages cm ON s.session_id = cm.session_id
GROUP BY s.session_id, s.agent_type, s.user_id, s.project, s.start_time, s.end_time;

-- Most used programming languages
CREATE OR REPLACE VIEW language_usage_stats AS
SELECT 
    language,
    COUNT(*) as snippet_count,
    SUM(lines) as total_lines,
    AVG(lines) as avg_lines_per_snippet,
    COUNT(DISTINCT session_id) as unique_sessions,
    MIN(extracted_at) as first_used,
    MAX(extracted_at) as last_used
FROM code_snippets
WHERE language != 'unknown'
GROUP BY language
ORDER BY snippet_count DESC;

-- Project activity overview
CREATE OR REPLACE VIEW project_activity AS
SELECT 
    project,
    COUNT(DISTINCT session_id) as total_sessions,
    COUNT(DISTINCT CASE WHEN status = 'active' THEN session_id END) as active_sessions,
    COUNT(DISTINCT user_id) as unique_users,
    MIN(start_time) as project_started,
    MAX(COALESCE(end_time, NOW())) as last_activity,
    SUM(CASE WHEN cs.session_id IS NOT NULL THEN 1 ELSE 0 END) as total_code_snippets,
    SUM(CASE WHEN t.session_id IS NOT NULL THEN 1 ELSE 0 END) as total_todos
FROM agent_sessions s
LEFT JOIN code_snippets cs ON s.session_id = cs.session_id
LEFT JOIN todo_items t ON s.session_id = t.session_id
GROUP BY project
ORDER BY total_sessions DESC;

-- ================================================
-- DATA CLEANUP & MAINTENANCE
-- ================================================

-- Function to cleanup old conversation data
CREATE OR REPLACE FUNCTION cleanup_old_conversations(
    retention_days INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old completed sessions and cascade to related data
    WITH deleted_sessions AS (
        DELETE FROM agent_sessions 
        WHERE status = 'ended' 
            AND end_time < NOW() - INTERVAL '1 day' * retention_days
        RETURNING session_id
    )
    SELECT COUNT(*) INTO deleted_count FROM deleted_sessions;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- PERFORMANCE OPTIMIZATIONS
-- ================================================

-- Vector similarity search indexes (HNSW for better performance)
CREATE INDEX IF NOT EXISTS idx_code_snippets_embedding_hnsw 
ON code_snippets USING hnsw (code_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_conversation_summaries_embedding_hnsw 
ON conversation_summaries USING hnsw (conversation_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_embedding_hnsw 
ON conversation_messages USING hnsw (content_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_code_snippets_session_language ON code_snippets(session_id, language);
CREATE INDEX IF NOT EXISTS idx_todo_items_session_status ON todo_items(session_id, status);
CREATE INDEX IF NOT EXISTS idx_file_operations_session_operation ON file_operations(session_id, operation);

-- ================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ================================================

-- Update conversation summary when messages are added
CREATE OR REPLACE FUNCTION update_conversation_summary()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO conversation_summaries (
        session_id, 
        message_count, 
        start_time, 
        end_time,
        processed_at
    ) 
    VALUES (
        NEW.session_id,
        1,
        NEW.created_at,
        NEW.created_at,
        NOW()
    )
    ON CONFLICT (session_id) 
    DO UPDATE SET 
        message_count = conversation_summaries.message_count + 1,
        end_time = NEW.created_at,
        processed_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_update_conversation_summary ON conversation_messages;
CREATE TRIGGER trigger_update_conversation_summary
    AFTER INSERT ON conversation_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_summary();

-- ================================================
-- SECURITY & PERMISSIONS
-- ================================================

-- Grant appropriate permissions to n8n user (if needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO n8n_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n8n_user;

-- ================================================
-- SAMPLE DATA VIEWS FOR TESTING
-- ================================================

-- Quick session overview
CREATE OR REPLACE VIEW session_overview AS
SELECT 
    s.session_id,
    s.agent_type,
    s.status,
    s.start_time,
    s.end_time,
    COUNT(DISTINCT cm.id) as messages,
    COUNT(DISTINCT cs.id) as code_snippets,
    COUNT(DISTINCT t.id) as todos,
    COUNT(DISTINCT fo.id) as file_ops
FROM agent_sessions s
LEFT JOIN conversation_messages cm ON s.session_id = cm.session_id
LEFT JOIN code_snippets cs ON s.session_id = cs.session_id
LEFT JOIN todo_items t ON s.session_id = t.session_id
LEFT JOIN file_operations fo ON s.session_id = fo.session_id
GROUP BY s.session_id, s.agent_type, s.status, s.start_time, s.end_time
ORDER BY s.start_time DESC;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION find_similar_code(vector(1024), INTEGER, FLOAT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION find_similar_conversations(vector(1024), INTEGER, FLOAT) TO PUBLIC;
GRANT EXECUTE ON FUNCTION cleanup_old_conversations(INTEGER) TO PUBLIC;

COMMIT;

-- ================================================
-- SCHEMA VERIFICATION
-- ================================================
SELECT 'Enhanced FindersKeepers v2 schema installed successfully!' as status;
