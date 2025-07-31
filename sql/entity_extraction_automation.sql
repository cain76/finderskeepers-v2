-- FindersKeepers v2 Entity Extraction Automation
-- PostgreSQL triggers and functions for automatic entity extraction

-- Create system_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_system_logs_event_type ON system_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at DESC);

-- Function to notify n8n when a new document is added
CREATE OR REPLACE FUNCTION notify_new_document()
RETURNS TRIGGER AS $$
BEGIN
    -- Send notification with document details
    PERFORM pg_notify(
        'new_document_added',
        json_build_object(
            'id', NEW.id,
            'title', NEW.title,
            'project', NEW.project,
            'doc_type', NEW.doc_type,
            'content_length', LENGTH(NEW.content)
        )::text
    );
    
    -- Log the event
    INSERT INTO system_logs (event_type, event_data)
    VALUES (
        'document_created',
        jsonb_build_object(
            'document_id', NEW.id,
            'title', NEW.title,
            'project', NEW.project,
            'trigger', 'auto_entity_extraction'
        )
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_new_document ON documents;

-- Create trigger for new documents
CREATE TRIGGER trigger_new_document
    AFTER INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_document();

-- Function to queue documents for entity extraction
CREATE OR REPLACE FUNCTION queue_entity_extraction(
    p_document_id UUID,
    p_priority INTEGER DEFAULT 5
)
RETURNS UUID AS $$
DECLARE
    v_queue_id UUID;
BEGIN
    -- Create processing_queue table if it doesn't exist
    CREATE TABLE IF NOT EXISTS processing_queue (
        id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
        document_id UUID NOT NULL REFERENCES documents(id),
        queue_type VARCHAR(50) NOT NULL DEFAULT 'entity_extraction',
        priority INTEGER DEFAULT 5,
        status VARCHAR(50) DEFAULT 'pending',
        attempts INTEGER DEFAULT 0,
        max_attempts INTEGER DEFAULT 3,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        processed_at TIMESTAMP WITH TIME ZONE,
        error_message TEXT
    );
    
    -- Insert into queue
    INSERT INTO processing_queue (document_id, priority)
    VALUES (p_document_id, p_priority)
    RETURNING id INTO v_queue_id;
    
    -- Notify queue processor
    PERFORM pg_notify(
        'entity_extraction_queue',
        json_build_object(
            'queue_id', v_queue_id,
            'document_id', p_document_id,
            'priority', p_priority
        )::text
    );
    
    RETURN v_queue_id;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for processing queue
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_priority ON processing_queue(priority DESC, created_at ASC);

-- Function to get next item from queue
CREATE OR REPLACE FUNCTION get_next_queue_item()
RETURNS TABLE (
    queue_id UUID,
    document_id UUID,
    title VARCHAR(500),
    project VARCHAR(100),
    content TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH next_item AS (
        SELECT pq.id
        FROM processing_queue pq
        WHERE pq.status = 'pending'
        AND pq.attempts < pq.max_attempts
        ORDER BY pq.priority DESC, pq.created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    UPDATE processing_queue pq
    SET 
        status = 'processing',
        attempts = attempts + 1,
        updated_at = NOW()
    FROM next_item ni
    JOIN documents d ON pq.document_id = d.id
    WHERE pq.id = ni.id
    RETURNING 
        pq.id as queue_id,
        pq.document_id,
        d.title,
        d.project,
        d.content;
END;
$$ LANGUAGE plpgsql;

-- Function to mark queue item as completed
CREATE OR REPLACE FUNCTION complete_queue_item(
    p_queue_id UUID,
    p_success BOOLEAN,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE processing_queue
    SET 
        status = CASE WHEN p_success THEN 'completed' ELSE 'failed' END,
        processed_at = NOW(),
        updated_at = NOW(),
        error_message = p_error_message
    WHERE id = p_queue_id;
END;
$$ LANGUAGE plpgsql;

-- View to monitor entity extraction progress
CREATE OR REPLACE VIEW v_entity_extraction_status AS
SELECT 
    d.id as document_id,
    d.title,
    d.project,
    d.created_at as document_created,
    COUNT(DISTINCT er.entity_id) as entity_count,
    MAX(er.created_at) as last_extraction,
    CASE 
        WHEN COUNT(er.id) > 0 THEN 'extracted'
        WHEN pq.status IS NOT NULL THEN pq.status
        ELSE 'pending'
    END as extraction_status,
    pq.attempts,
    pq.error_message
FROM documents d
LEFT JOIN entity_references er ON er.reference_id = d.id AND er.reference_type = 'document'
LEFT JOIN processing_queue pq ON pq.document_id = d.id
GROUP BY d.id, d.title, d.project, d.created_at, pq.status, pq.attempts, pq.error_message;

-- Grant permissions if needed
GRANT SELECT ON v_entity_extraction_status TO finderskeepers;
GRANT EXECUTE ON FUNCTION queue_entity_extraction TO finderskeepers;
GRANT EXECUTE ON FUNCTION get_next_queue_item TO finderskeepers;
GRANT EXECUTE ON FUNCTION complete_queue_item TO finderskeepers;

-- Insert test notification
SELECT pg_notify('new_document_added', '{"test": true, "message": "Entity extraction automation ready"}');