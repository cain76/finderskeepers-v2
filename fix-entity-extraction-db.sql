-- Fix FK2 Entity Extraction Database Schema
-- Create missing tables and views

-- Create processing_queue table
CREATE TABLE IF NOT EXISTS processing_queue (
    id SERIAL PRIMARY KEY,
    document_id UUID NOT NULL,
    queue_status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_processing_queue_status ON processing_queue(queue_status);
CREATE INDEX IF NOT EXISTS idx_processing_queue_document ON processing_queue(document_id);

-- Create function to track processing status
CREATE OR REPLACE FUNCTION update_processing_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the queue status based on entity extraction
    IF TG_OP = 'INSERT' THEN
        UPDATE processing_queue 
        SET queue_status = 'processing', 
            last_attempt = NOW()
        WHERE document_id = NEW.document_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the monitoring view for entity extraction status
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
GRANT ALL ON processing_queue TO finderskeepers;
GRANT USAGE ON SEQUENCE processing_queue_id_seq TO finderskeepers;

-- Create function to add documents to processing queue
CREATE OR REPLACE FUNCTION queue_document_for_processing(doc_id UUID)
RETURNS void AS $$
BEGIN
    INSERT INTO processing_queue (document_id, queue_status, priority)
    VALUES (doc_id, 'pending', 5)
    ON CONFLICT (document_id) DO UPDATE
    SET queue_status = 'pending',
        retry_count = processing_queue.retry_count + 1,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Test the setup
SELECT 'Database schema fixed!' as status;