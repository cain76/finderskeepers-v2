-- Create entity tables and fix the monitoring view
-- These tables are needed for entity extraction to work properly

-- Create entities table if it doesn't exist
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    entity_type VARCHAR(100),
    entity_name TEXT,
    entity_value TEXT,
    confidence FLOAT DEFAULT 0.9,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Create entity_relationships table
CREATE TABLE IF NOT EXISTS entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID NOT NULL,
    target_entity_id UUID NOT NULL,
    relationship_type VARCHAR(100),
    confidence FLOAT DEFAULT 0.9,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_source_entity FOREIGN KEY (source_entity_id) REFERENCES entities(id),
    CONSTRAINT fk_target_entity FOREIGN KEY (target_entity_id) REFERENCES entities(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_entities_document ON entities(document_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_source ON entity_relationships(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_target ON entity_relationships(target_entity_id);

-- Now recreate the monitoring view with correct tables
CREATE OR REPLACE VIEW v_entity_extraction_status AS
SELECT 
    d.id as document_id,
    d.title,
    d.doc_type,
    d.project,
    d.created_at as document_created,
    COALESCE(pq.queue_status, 'not_queued') as queue_status,
    pq.retry_count,
    pq.last_attempt,
    pq.error_message,
    COUNT(DISTINCT e.id) as entity_count,
    COUNT(DISTINCT er.id) as relationship_count,
    MAX(e.created_at) as last_entity_extracted,
    CASE 
        WHEN COUNT(e.id) > 0 THEN 'completed'
        WHEN pq.queue_status = 'processing' THEN 'in_progress'
        WHEN pq.queue_status = 'failed' THEN 'failed'
        ELSE 'pending'
    END as extraction_status
FROM documents d
LEFT JOIN processing_queue pq ON pq.document_id = d.id
LEFT JOIN entities e ON e.document_id = d.id
LEFT JOIN entity_relationships er ON er.source_entity_id = e.id OR er.target_entity_id = e.id
WHERE d.project = 'finderskeepers-v2'
GROUP BY d.id, d.title, d.doc_type, d.project, d.created_at, 
         pq.queue_status, pq.retry_count, pq.last_attempt, pq.error_message;

-- Grant permissions
GRANT SELECT ON v_entity_extraction_status TO finderskeepers;
GRANT ALL ON entities TO finderskeepers;
GRANT ALL ON entity_relationships TO finderskeepers;

-- Test the setup
SELECT 'Entity tables and view created successfully!' as status;