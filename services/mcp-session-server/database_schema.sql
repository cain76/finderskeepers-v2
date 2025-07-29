-- configuration data for bitcain.net platform
INSERT INTO agent_sessions (session_id, user_id, agent_type, project, status, platform, gpu_acceleration, metadata) 
VALUES (
    'init_session_bitcain_' || extract(epoch from now())::text,
    'bitcain',
    'claude-code',
    'finderskeepers-v2',
    'completed',
    'bitcain.net',
    true,
    '{"initialized_by": "database_schema", "version": "2.0.0", "features": ["vector_search", "redis_cache", "gpu_acceleration"]}'
) ON CONFLICT (session_id) DO NOTHING;

-- ========================================
-- PERFORMANCE OPTIMIZATION SETTINGS
-- ========================================

-- Optimize for bitcain.net workload patterns
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Optimize for JSONB operations
ALTER SYSTEM SET gin_pending_list_limit = '4MB';

-- ========================================
-- MONITORING AND ALERTING
-- ========================================

-- Create monitoring table for system health
CREATE TABLE IF NOT EXISTS system_health_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component VARCHAR(100) NOT NULL, -- 'database', 'redis', 'qdrant', 'mcp_server'
    status VARCHAR(50) NOT NULL CHECK (status IN ('healthy', 'warning', 'critical', 'down')),
    metric_name VARCHAR(100),
    metric_value DECIMAL(12,4),
    message TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_health_log_timestamp ON system_health_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_health_log_component ON system_health_log(component);
CREATE INDEX IF NOT EXISTS idx_health_log_status ON system_health_log(status);

-- Function to log system health metrics
CREATE OR REPLACE FUNCTION log_system_health(
    component_name VARCHAR,
    health_status VARCHAR,
    metric_name VARCHAR DEFAULT NULL,
    metric_value DECIMAL DEFAULT NULL,
    log_message TEXT DEFAULT NULL,
    additional_metadata JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO system_health_log (component, status, metric_name, metric_value, message, metadata)
    VALUES (component_name, health_status, metric_name, metric_value, log_message, additional_metadata)
    RETURNING id INTO log_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- BITCAIN.NET SPECIFIC FUNCTIONS
-- ========================================

-- Function to get user session analytics for bitcain user
CREATE OR REPLACE FUNCTION get_bitcain_session_analytics(days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    date_bucket DATE,
    session_count BIGINT,
    message_count BIGINT,
    avg_session_duration_minutes NUMERIC,
    gpu_enabled_sessions BIGINT,
    total_processing_time_ms BIGINT,
    unique_projects BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(s.start_time) as date_bucket,
        COUNT(DISTINCT s.session_id)::BIGINT as session_count,
        COUNT(m.id)::BIGINT as message_count,
        AVG(EXTRACT(EPOCH FROM (COALESCE(s.end_time, NOW()) - s.start_time)) / 60) as avg_session_duration_minutes,
        COUNT(DISTINCT s.session_id) FILTER (WHERE s.gpu_acceleration = true)::BIGINT as gpu_enabled_sessions,
        COALESCE(SUM(m.processing_time_ms), 0)::BIGINT as total_processing_time_ms,
        COUNT(DISTINCT s.project)::BIGINT as unique_projects
    FROM agent_sessions s
    LEFT JOIN conversation_messages m ON s.session_id = m.session_id
    WHERE s.user_id = 'bitcain' 
    AND s.start_time >= NOW() - INTERVAL '%s days' % days_back
    GROUP BY DATE(s.start_time)
    ORDER BY date_bucket DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get project performance metrics
CREATE OR REPLACE FUNCTION get_project_performance_metrics(project_name VARCHAR DEFAULT 'finderskeepers-v2')
RETURNS TABLE (
    metric_name TEXT,
    metric_value NUMERIC,
    metric_unit TEXT,
    description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'total_sessions'::TEXT,
        COUNT(*)::NUMERIC,
        'count'::TEXT,
        'Total number of sessions for this project'::TEXT
    FROM agent_sessions WHERE project = project_name
    UNION ALL
    SELECT 
        'avg_messages_per_session'::TEXT,
        AVG(message_count)::NUMERIC,
        'messages'::TEXT,
        'Average number of messages per session'::TEXT
    FROM agent_sessions WHERE project = project_name
    UNION ALL
    SELECT 
        'gpu_utilization_rate'::TEXT,
        (COUNT(*) FILTER (WHERE gpu_acceleration = true)::NUMERIC / NULLIF(COUNT(*)::NUMERIC, 0) * 100),
        'percent'::TEXT,
        'Percentage of sessions using GPU acceleration'::TEXT
    FROM agent_sessions WHERE project = project_name
    UNION ALL
    SELECT 
        'avg_session_duration_hours'::TEXT,
        AVG(EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) / 3600)::NUMERIC,
        'hours'::TEXT,
        'Average session duration in hours'::TEXT
    FROM agent_sessions WHERE project = project_name
    UNION ALL
    SELECT 
        'completion_rate'::TEXT,
        (COUNT(*) FILTER (WHERE status = 'completed')::NUMERIC / NULLIF(COUNT(*)::NUMERIC, 0) * 100),
        'percent'::TEXT,
        'Percentage of sessions completed successfully'::TEXT
    FROM agent_sessions WHERE project = project_name;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- DATABASE SCHEMA VERSION AND MIGRATION TRACKING
-- ========================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(100) DEFAULT 'system'
);

-- Record this schema version
INSERT INTO schema_migrations (version, description, applied_by) 
VALUES (
    'v2.0.0_enhanced', 
    'FindersKeepers-v2 Enhanced MCP Server Database Schema with full-text search, vector support, and bitcain.net optimizations',
    'bitcain'
) ON CONFLICT (version) DO NOTHING;

-- ========================================
-- FINAL OPTIMIZATIONS AND MAINTENANCE
-- ========================================

-- Update table statistics for optimal query planning
ANALYZE agent_sessions;
ANALYZE conversation_messages;

-- Set up automatic vacuum scheduling for optimal performance
ALTER TABLE agent_sessions SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE conversation_messages SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- Log successful schema deployment
SELECT log_system_health(
    'database'::VARCHAR,
    'healthy'::VARCHAR,
    'schema_deployment'::VARCHAR,
    2.0::DECIMAL,
    'FindersKeepers-v2 Enhanced Database Schema Successfully Deployed'::TEXT,
    '{"platform": "bitcain.net", "version": "v2.0.0_enhanced", "features": ["full_text_search", "vector_support", "gpu_optimization", "performance_monitoring"]}'::JSONB
);

-- Display deployment summary
SELECT 
    'FindersKeepers-v2 Enhanced Database Schema Deployed Successfully!' as status,
    NOW() as deployment_time,
    'bitcain.net' as platform,
    'v2.0.0_enhanced' as version;
