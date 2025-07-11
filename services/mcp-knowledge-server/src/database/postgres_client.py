"""
PostgreSQL Database Client for MCP Knowledge Server
Handles document metadata, session tracking, and knowledge base statistics
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

# Import asyncpg for PostgreSQL
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg not available")

logger = logging.getLogger(__name__)

class PostgresClient:
    """Async PostgreSQL client for knowledge base operations"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.dsn = os.getenv(
            "POSTGRES_URL",
            "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
        )
        
    async def connect(self):
        """Initialize connection pool to PostgreSQL"""
        if not ASYNCPG_AVAILABLE:
            logger.error("asyncpg not available")
            return
            
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=1,
                max_size=10,
                timeout=30
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"Connected to PostgreSQL: {version[:50]}...")
                
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.pool = None
            
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            
    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """
        Get comprehensive metadata for a document
        
        Args:
            document_id: Document ID to retrieve
            
        Returns:
            Document metadata dictionary
        """
        if not self.pool:
            return {}
            
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        id, filename, file_path, format, project,
                        tags, metadata, file_size, mime_type,
                        processing_method, word_count, language,
                        ingestion_id, created_at, updated_at
                    FROM documents 
                    WHERE id = $1
                """
                
                row = await conn.fetchrow(query, document_id)
                
                if row:
                    result = dict(row)
                    # Parse JSON fields
                    if result.get("tags"):
                        result["tags"] = json.loads(result["tags"]) if isinstance(result["tags"], str) else result["tags"]
                    if result.get("metadata"):
                        result["metadata"] = json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"]
                    
                    return result
                    
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get document metadata: {e}")
            return {}
    
    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get specific agent session details
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session details dictionary
        """
        if not self.pool:
            return {}
            
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        session_id, agent_type, user_id, project,
                        start_time, end_time, context, created_at
                    FROM agent_sessions 
                    WHERE session_id = $1
                """
                
                row = await conn.fetchrow(query, session_id)
                
                if row:
                    result = dict(row)
                    # Parse JSON context
                    if result.get("context"):
                        result["context"] = json.loads(result["context"]) if isinstance(result["context"], str) else result["context"]
                    
                    return result
                    
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return {}
    
    async def get_session_actions(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get actions for a specific session
        
        Args:
            session_id: Session ID to get actions for
            limit: Maximum number of actions to return
            
        Returns:
            List of action dictionaries
        """
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        action_id, session_id, timestamp, action_type,
                        description, details, files_affected, success
                    FROM agent_actions 
                    WHERE session_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """
                
                rows = await conn.fetch(query, session_id, limit)
                
                results = []
                for row in rows:
                    result = dict(row)
                    # Parse JSON fields
                    if result.get("details"):
                        result["details"] = json.loads(result["details"]) if isinstance(result["details"], str) else result["details"]
                    if result.get("files_affected"):
                        result["files_affected"] = json.loads(result["files_affected"]) if isinstance(result["files_affected"], str) else result["files_affected"]
                    
                    results.append(result)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to get session actions: {e}")
            return []
    
    async def get_recent_sessions(
        self,
        agent_type: Optional[str] = None,
        project: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get recent agent sessions with optional filters
        
        Args:
            agent_type: Filter by agent type
            project: Filter by project
            limit: Maximum number of sessions
            
        Returns:
            List of recent sessions
        """
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                # Build dynamic query
                conditions = []
                params = []
                param_idx = 1
                
                if agent_type:
                    conditions.append(f"agent_type = ${param_idx}")
                    params.append(agent_type)
                    param_idx += 1
                    
                if project:
                    conditions.append(f"project = ${param_idx}")
                    params.append(project)
                    param_idx += 1
                
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                
                query = f"""
                    SELECT 
                        session_id, agent_type, user_id, project,
                        start_time, end_time, context, created_at
                    FROM agent_sessions 
                    {where_clause}
                    ORDER BY start_time DESC
                    LIMIT ${param_idx}
                """
                
                params.append(limit)
                rows = await conn.fetch(query, *params)
                
                results = []
                for row in rows:
                    result = dict(row)
                    if result.get("context"):
                        result["context"] = json.loads(result["context"]) if isinstance(result["context"], str) else result["context"]
                    results.append(result)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    async def get_recent_actions(
        self,
        agent_type: Optional[str] = None,
        project: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent agent actions across all sessions
        
        Args:
            agent_type: Filter by agent type
            project: Filter by project
            limit: Maximum number of actions
            
        Returns:
            List of recent actions
        """
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                # Build query with session join for filtering
                conditions = []
                params = []
                param_idx = 1
                
                if agent_type:
                    conditions.append(f"s.agent_type = ${param_idx}")
                    params.append(agent_type)
                    param_idx += 1
                    
                if project:
                    conditions.append(f"s.project = ${param_idx}")
                    params.append(project)
                    param_idx += 1
                
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                
                query = f"""
                    SELECT 
                        a.action_id, a.session_id, a.timestamp, a.action_type,
                        a.description, a.details, a.files_affected, a.success,
                        s.agent_type, s.project
                    FROM agent_actions a
                    JOIN agent_sessions s ON a.session_id = s.session_id
                    {where_clause}
                    ORDER BY a.timestamp DESC
                    LIMIT ${param_idx}
                """
                
                params.append(limit)
                rows = await conn.fetch(query, *params)
                
                results = []
                for row in rows:
                    result = dict(row)
                    if result.get("details"):
                        result["details"] = json.loads(result["details"]) if isinstance(result["details"], str) else result["details"]
                    if result.get("files_affected"):
                        result["files_affected"] = json.loads(result["files_affected"]) if isinstance(result["files_affected"], str) else result["files_affected"]
                    results.append(result)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to get recent actions: {e}")
            return []
    
    async def get_files_affected_by_actions(self, action_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get file changes from a list of action IDs
        
        Args:
            action_ids: List of action IDs to analyze
            
        Returns:
            List of file changes with metadata
        """
        if not self.pool or not action_ids:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                # Get actions with file information
                query = """
                    SELECT 
                        action_id, session_id, action_type, description,
                        files_affected, timestamp, success
                    FROM agent_actions 
                    WHERE action_id = ANY($1) AND files_affected IS NOT NULL
                    ORDER BY timestamp DESC
                """
                
                rows = await conn.fetch(query, action_ids)
                
                file_changes = []
                for row in rows:
                    row_dict = dict(row)
                    files = json.loads(row_dict["files_affected"]) if isinstance(row_dict["files_affected"], str) else row_dict["files_affected"]
                    
                    if files:
                        for file_path in files:
                            file_changes.append({
                                "file_path": file_path,
                                "action_id": row_dict["action_id"],
                                "action_type": row_dict["action_type"],
                                "description": row_dict["description"],
                                "timestamp": row_dict["timestamp"],
                                "success": row_dict["success"]
                            })
                
                return file_changes
                
        except Exception as e:
            logger.error(f"Failed to get file changes: {e}")
            return []
    
    async def get_project_statistics(self, project: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a project
        
        Args:
            project: Project name to analyze
            
        Returns:
            Project statistics dictionary
        """
        if not self.pool:
            return {}
            
        try:
            async with self.pool.acquire() as conn:
                # Get document statistics
                doc_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(DISTINCT format) as unique_formats,
                        SUM(file_size) as total_size,
                        AVG(word_count) as avg_word_count
                    FROM documents 
                    WHERE project = $1
                """, project)
                
                # Get session statistics
                session_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_sessions,
                        COUNT(DISTINCT agent_type) as unique_agents,
                        COUNT(DISTINCT user_id) as unique_users,
                        MAX(start_time) as last_session
                    FROM agent_sessions 
                    WHERE project = $1
                """, project)
                
                # Get action statistics
                action_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_actions,
                        COUNT(*) FILTER (WHERE success = true) as successful_actions,
                        COUNT(DISTINCT action_type) as unique_action_types
                    FROM agent_actions a
                    JOIN agent_sessions s ON a.session_id = s.session_id
                    WHERE s.project = $1
                """, project)
                
                # Combine statistics
                stats = {
                    **dict(doc_stats),
                    **dict(session_stats),
                    **dict(action_stats)
                }
                
                # Calculate derived metrics
                if stats["total_actions"] > 0:
                    stats["success_rate"] = stats["successful_actions"] / stats["total_actions"]
                else:
                    stats["success_rate"] = 0.0
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get project statistics: {e}")
            return {}
    
    async def get_recent_documents(self, project: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently added documents for a project
        
        Args:
            project: Project name
            limit: Maximum number of documents
            
        Returns:
            List of recent documents
        """
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        id, filename, format, tags, word_count,
                        created_at, processing_method
                    FROM documents 
                    WHERE project = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """
                
                rows = await conn.fetch(query, project, limit)
                
                results = []
                for row in rows:
                    result = dict(row)
                    if result.get("tags"):
                        result["tags"] = json.loads(result["tags"]) if isinstance(result["tags"], str) else result["tags"]
                    results.append(result)
                    
                return results
                
        except Exception as e:
            logger.error(f"Failed to get recent documents: {e}")
            return []
    
    async def get_recent_project_activity(
        self, 
        project: str, 
        days: int = 7, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity for a project
        
        Args:
            project: Project name
            days: Number of days to look back
            limit: Maximum number of activities
            
        Returns:
            List of recent activities
        """
        if not self.pool:
            return []
            
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            async with self.pool.acquire() as conn:
                query = """
                    SELECT 
                        'action' as activity_type,
                        a.action_id as id,
                        a.action_type,
                        a.description,
                        a.timestamp,
                        a.success,
                        s.agent_type,
                        s.session_id
                    FROM agent_actions a
                    JOIN agent_sessions s ON a.session_id = s.session_id
                    WHERE s.project = $1 AND a.timestamp >= $2
                    
                    UNION ALL
                    
                    SELECT 
                        'document' as activity_type,
                        d.id,
                        d.format as action_type,
                        'Document ingested: ' || d.filename as description,
                        d.created_at as timestamp,
                        true as success,
                        'system' as agent_type,
                        null as session_id
                    FROM documents d
                    WHERE d.project = $1 AND d.created_at >= $2
                    
                    ORDER BY timestamp DESC
                    LIMIT $3
                """
                
                rows = await conn.fetch(query, project, since_date, limit)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get project activity: {e}")
            return []
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics
        
        Returns:
            Database statistics dictionary
        """
        if not self.pool:
            return {"healthy": False}
            
        try:
            async with self.pool.acquire() as conn:
                # Get table counts
                tables_stats = await conn.fetch("""
                    SELECT 
                        'documents' as table_name, COUNT(*) as count FROM documents
                    UNION ALL
                    SELECT 
                        'document_chunks' as table_name, COUNT(*) as count FROM document_chunks
                    UNION ALL
                    SELECT 
                        'agent_sessions' as table_name, COUNT(*) as count FROM agent_sessions
                    UNION ALL
                    SELECT 
                        'agent_actions' as table_name, COUNT(*) as count FROM agent_actions
                """)
                
                # Get project count
                project_count = await conn.fetchval("""
                    SELECT COUNT(DISTINCT project) FROM documents
                """)
                
                # Calculate average query time (simplified estimate)
                start_time = datetime.utcnow()
                await conn.fetchval("SELECT 1")
                query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Build stats dictionary
                stats = {"healthy": True, "active_projects": project_count, "avg_query_time": query_time}
                
                for row in tables_stats:
                    if row["table_name"] == "documents":
                        stats["total_documents"] = row["count"]
                    elif row["table_name"] == "document_chunks":
                        stats["total_chunks"] = row["count"]
                    elif row["table_name"] == "agent_sessions":
                        stats["total_sessions"] = row["count"]
                    elif row["table_name"] == "agent_actions":
                        stats["total_actions"] = row["count"]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get comprehensive stats: {e}")
            return {"healthy": False, "error": str(e)}
    
    async def get_detailed_schema(self) -> Dict[str, Any]:
        """
        Get detailed database schema information
        
        Returns:
            Schema information dictionary
        """
        if not self.pool:
            return {}
            
        try:
            async with self.pool.acquire() as conn:
                # Get table information
                tables = await conn.fetch("""
                    SELECT 
                        table_name,
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                """)
                
                # Group by table
                schema = {}
                for row in tables:
                    table = row["table_name"]
                    if table not in schema:
                        schema[table] = []
                    
                    schema[table].append({
                        "column": row["column_name"],
                        "type": row["data_type"],
                        "nullable": row["is_nullable"] == "YES",
                        "default": row["column_default"]
                    })
                
                return schema
                
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """
        Check if PostgreSQL is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.pool:
            return False
            
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
                
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False