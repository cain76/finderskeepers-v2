-- FindersKeepers v2 PostgreSQL+pgvector Initialization
-- Creates database schema for agent sessions, knowledge storage, and vector search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- AGENT SESSION TRACKING
-- ========================================

-- Agent sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    user_id VARCHAR(255) DEFAULT 'local_user',
    project VARCHAR(100),
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent actions table
CREATE TABLE IF NOT EXISTS agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    files_affected JSONB DEFAULT '[]',
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversation messages table for storing chat history
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL, -- 'user_message', 'ai_response', 'system_message', 'tool_result'
    content TEXT NOT NULL,
    context JSONB DEFAULT '{}', -- Additional context like emotional tone, urgency, topic changes
    reasoning TEXT, -- AI reasoning process and decision-making (for AI responses)
    tools_used JSONB DEFAULT '[]', -- List of tools used in this interaction
    files_referenced JSONB DEFAULT '[]', -- Files mentioned or referenced in the message
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sequence_number INTEGER, -- Order within the session
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- DOCUMENT STORAGE & VECTOR SEARCH
-- ========================================

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for duplicate detection
    project VARCHAR(100) NOT NULL,
    doc_type VARCHAR(100) DEFAULT 'general',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(content_hash, project) -- Prevent duplicates per project
);

-- Document chunks for vector search
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024), -- mxbai-embed-large dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- CONFIGURATION TRACKING
-- ========================================

-- Configuration changes table
CREATE TABLE IF NOT EXISTS config_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    change_id VARCHAR(255) UNIQUE NOT NULL,
    component VARCHAR(100) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    reason TEXT NOT NULL,
    impact TEXT,
    project VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- KNOWLEDGE GRAPH INTEGRATION
-- ========================================

-- Store references to Neo4j entities
CREATE TABLE IF NOT EXISTS knowledge_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(255) UNIQUE NOT NULL, -- Neo4j node ID
    entity_type VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Link entities to documents/sessions
CREATE TABLE IF NOT EXISTS entity_references (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id VARCHAR(255) REFERENCES knowledge_entities(entity_id),
    reference_type VARCHAR(50) NOT NULL, -- 'document', 'session', 'action'
    reference_id UUID NOT NULL,
    relevance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Agent sessions indexes
CREATE INDEX IF NOT EXISTS idx_agent_sessions_type ON agent_sessions(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_project ON agent_sessions(project);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_start_time ON agent_sessions(start_time);

-- Agent actions indexes
CREATE INDEX IF NOT EXISTS idx_agent_actions_session ON agent_actions(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_type ON agent_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_agent_actions_timestamp ON agent_actions(timestamp);

-- Conversation messages indexes
CREATE INDEX IF NOT EXISTS idx_conversation_messages_session ON conversation_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_type ON conversation_messages(message_type);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_sequence ON conversation_messages(session_id, sequence_number);

-- Documents indexes
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);

-- Vector search index (HNSW for fast approximate nearest neighbor)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- Configuration changes indexes
CREATE INDEX IF NOT EXISTS idx_config_changes_component ON config_changes(component);
CREATE INDEX IF NOT EXISTS idx_config_changes_timestamp ON config_changes(timestamp);

-- Knowledge entities indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_type ON knowledge_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_references_type ON entity_references(reference_type);

-- ========================================
-- FUNCTIONS & TRIGGERS
-- ========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_agent_sessions_updated_at 
    BEFORE UPDATE ON agent_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_entities_updated_at 
    BEFORE UPDATE ON knowledge_entities 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function for vector similarity search
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(1024),
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 10,
    filter_project text DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    project VARCHAR(100),
    doc_title VARCHAR(500)
) 
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dc.id,
        dc.document_id,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity,
        d.project,
        d.title
    FROM document_chunks dc
    JOIN documents d ON dc.document_id = d.id
    WHERE 
        1 - (dc.embedding <=> query_embedding) > similarity_threshold
        AND (filter_project IS NULL OR d.project = filter_project)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT max_results;
END;
$$;

-- ========================================
-- SAMPLE DATA (Optional)
-- ========================================

-- Insert sample session for testing
INSERT INTO agent_sessions (session_id, agent_type, project, context) 
VALUES (
    'sample_session_001',
    'claude',
    'finderskeepers-v2',
    '{"purpose": "Initial setup and testing", "version": "2.0.0"}'
) ON CONFLICT (session_id) DO NOTHING;

-- Insert sample document
INSERT INTO documents (title, content, project, doc_type, tags) 
VALUES (
    'FindersKeepers v2 Setup Guide',
    'This is a comprehensive guide for setting up FindersKeepers v2 with Docker containers...',
    'finderskeepers-v2',
    'documentation',
    ARRAY['setup', 'docker', 'guide']
) ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO finderskeepers;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO finderskeepers;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO finderskeepers;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ FindersKeepers v2 database initialized successfully!';
    RAISE NOTICE '📊 Tables created: agent_sessions, agent_actions, conversation_messages, documents, document_chunks';
    RAISE NOTICE '💬 Conversation history tracking enabled with conversation_messages table';
    RAISE NOTICE '🔍 Vector search enabled with pgvector extension';
    RAISE NOTICE '⚡ Indexes created for optimal performance';
END $$;