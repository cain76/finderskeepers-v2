"""
MCP (Model Context Protocol) API Router for FindersKeepers v2 - AI GOD MODE
Direct integration bypassing n8n for session, action, and conversation logging
Enhanced with persistent memory capabilities and intelligent session management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncpg
import json
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(tags=["MCP - AI GOD MODE"])

# ========================================
# AI GOD MODE PYDANTIC MODELS
# ========================================

class SessionStart(BaseModel):
    """AI GOD MODE Session start request from MCP server"""
    session_id: str
    agent_type: str = "claude-desktop-ai-god-mode"
    user_id: str = "bitcain"
    project: str = "finderskeepers-v2"
    timestamp: str
    source: Optional[str] = "fk2_mcp_ai_god_mode"
    ai_god_mode: bool = Field(default=False, description="AI GOD MODE capabilities enabled")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session context")

class Action(BaseModel):
    """Enhanced Action logging with AI GOD MODE tracking"""
    session_id: str
    action_type: str
    description: str
    details: Dict[str, Any]
    files_affected: Optional[List[str]] = []
    success: bool = True
    timestamp: str
    source: Optional[str] = "fk2_mcp_ai_god_mode"
    ai_god_mode: bool = Field(default=False, description="AI GOD MODE enhanced logging")

class SessionEnd(BaseModel):
    """AI GOD MODE Session end request with comprehensive summary"""
    session_id: str
    reason: str = "session_complete"
    summary: str
    timestamp: str
    user_id: Optional[str] = "bitcain"
    agent_type: Optional[str] = "claude-desktop-ai-god-mode"
    project: Optional[str] = "finderskeepers-v2"
    ai_god_mode: bool = Field(default=False, description="AI GOD MODE session")
    accomplishments_count: Optional[int] = Field(default=0, description="Number of accomplishments")
    conversations_count: Optional[int] = Field(default=0, description="Number of conversations")

# ========================================
# DATABASE CONNECTION
# ========================================

async def get_conn():
    """Get a database connection - reuse from db_manager if available"""
    from app.database.connection import db_manager
    
    if db_manager.postgres_pool:
        async with db_manager.postgres_pool.acquire() as conn:
            yield conn
    else:
        # Fallback to direct connection
        conn = await asyncpg.connect(
            dsn="postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
        )
        try:
            yield conn
        finally:
            await conn.close()

# ========================================
# AI GOD MODE SESSION ENDPOINTS
# ========================================

@router.post("/session/start")
async def mcp_session_start(data: SessionStart, conn=Depends(get_conn)):
    """Start a new AI GOD MODE MCP session with enhanced tracking"""
    try:
        logger.info(f"🧠 AI GOD MODE session start: {data.session_id} for {data.user_id}")
        
        # Insert into standard agent_sessions for compatibility
        await conn.execute(
            """
            INSERT INTO agent_sessions (
                session_id, agent_type, user_id, project, status, 
                start_time, created_at, updated_at, context
            )
            VALUES ($1, $2, $3, $4, 'active', NOW(), NOW(), NOW(), $5::jsonb)
            ON CONFLICT (session_id)
            DO UPDATE SET 
                status = 'active',
                start_time = NOW(),
                updated_at = NOW()
            """,
            data.session_id, 
            data.agent_type, 
            data.user_id, 
            data.project,
            json.dumps({
                "source": data.source, 
                "timestamp": data.timestamp,
                "ai_god_mode": data.ai_god_mode,
                **data.context
            })
        )
        
        # If AI GOD MODE enabled, also create enhanced session record
        if data.ai_god_mode:
            try:
                await conn.execute(
                    """
                    INSERT INTO ai_session_memory (
                        session_id, user_id, project, start_time, status,
                        context_snapshot, ai_insights
                    )
                    VALUES ($1, $2, $3, NOW(), 'active', $4::jsonb, $5)
                    ON CONFLICT (session_id)
                    DO UPDATE SET 
                        status = 'active',
                        start_time = NOW(),
                        updated_at = NOW()
                    """,
                    data.session_id,
                    data.user_id,
                    data.project,
                    json.dumps({
                        "agent_type": data.agent_type,
                        "source": data.source,
                        "ai_god_mode": True,
                        "capabilities": ["persistent_memory", "conversation_capture", "smart_resumption"],
                        **data.context
                    }),
                    f"AI GOD MODE session started with persistent memory capabilities"
                )
                logger.info(f"🧠 AI GOD MODE enhanced session record created: {data.session_id}")
            except Exception as e:
                # If ai_session_memory table doesn't exist, log warning but continue
                logger.warning(f"⚠️ AI GOD MODE table not available: {e}")
        
        logger.info(f"✅ Session {data.session_id} started successfully")
        return {
            "status": "ok", 
            "session_id": data.session_id,
            "ai_god_mode": data.ai_god_mode,
            "persistent_memory": data.ai_god_mode
        }
        
    except Exception as e:
        logger.error(f"❌ AI GOD MODE session start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/end")
async def mcp_session_end(data: SessionEnd, conn=Depends(get_conn)):
    """End an AI GOD MODE MCP session with comprehensive summary storage"""
    try:
        logger.info(f"🧠 AI GOD MODE session end: {data.session_id}, reason: {data.reason}")
        
        # Update standard session table for compatibility
        result = await conn.execute(
            """
            UPDATE agent_sessions
            SET status = 'ended',
                end_time = NOW(),
                termination_reason = $1,
                session_summary = $2,
                updated_at = NOW()
            WHERE session_id = $3
            """,
            data.reason,
            data.summary[:1000],  # Truncate for standard table
            data.session_id
        )
        
        # If AI GOD MODE enabled, update enhanced session record
        if data.ai_god_mode:
            try:
                await conn.execute(
                    """
                    UPDATE ai_session_memory
                    SET status = 'ended',
                        end_time = NOW(),
                        session_summary = $1,
                        ai_insights = $2,
                        resume_context = $3,
                        conversation_count = $4,
                        updated_at = NOW()
                    WHERE session_id = $5
                    """,
                    data.summary,  # Full summary for AI GOD MODE
                    f"AI GOD MODE session completed with {data.accomplishments_count} accomplishments and {data.conversations_count} conversations",
                    data.summary[:1000],  # Condensed version for quick resumption
                    data.conversations_count or 0,
                    data.session_id
                )
                logger.info(f"🧠 AI GOD MODE enhanced session summary stored: {data.session_id}")
            except Exception as e:
                logger.warning(f"⚠️ AI GOD MODE table update failed: {e}")
        
        # Check if session was found and updated
        if result.split()[-1] == '0':
            logger.warning(f"Session {data.session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"✅ Session {data.session_id} ended successfully")
        return {
            "status": "ok", 
            "session_id": data.session_id,
            "ai_god_mode": data.ai_god_mode,
            "persistent_memory": data.ai_god_mode,
            "summary_stored": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI GOD MODE session end failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# ACTION AND CONVERSATION ENDPOINTS
# ========================================

@router.post("/action")
async def mcp_action(data: Action, conn=Depends(get_conn)):
    """Log an action - includes conversation messages"""
    try:
        logger.info(f"📝 MCP action: {data.action_type} for session {data.session_id}")
        
        # Generate action ID
        action_id = f"action_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # Insert into agent_actions
        await conn.execute(
            """
            INSERT INTO agent_actions (
                action_id, session_id, action_type, description, 
                details, files_affected, success, created_at
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, NOW())
            ON CONFLICT DO NOTHING
            """,
            action_id,
            data.session_id,
            data.action_type,
            data.description,
            json.dumps(data.details),
            json.dumps(data.files_affected) if data.files_affected else json.dumps([]),
            data.success
        )
        
        # If this is a conversation message, also store in conversation_messages
        if data.action_type == "conversation_message" and "message_type" in data.details and "content" in data.details:
            details = data.details
            # Generate a proper UUID for the message
            message_id = str(uuid.uuid4())
            
            await conn.execute(
                """
                INSERT INTO conversation_messages (
                    message_id, session_id, message_type, content, 
                    context, reasoning, tools_used, files_referenced, created_at
                )
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7::jsonb, $8::jsonb, NOW())
                ON CONFLICT DO NOTHING
                """,
                message_id,
                data.session_id,
                details.get("message_type"),
                details.get("content"),
                json.dumps(details.get("context", {})),
                details.get("reasoning"),
                json.dumps(details.get("tools_used", [])),
                json.dumps(details.get("files_referenced", []))
            )
            
            logger.info(f"💬 Conversation message stored: {message_id}")
            
            # Trigger automatic processing for embeddings and knowledge graph
            try:
                from app.core.automatic_processing import AutomaticProcessingPipeline
                pipeline = AutomaticProcessingPipeline()
                
                # Create a document-like structure for conversation processing
                conversation_doc = {
                    'id': message_id,
                    'title': f"Conversation: {details.get('message_type', 'unknown')}",
                    'content': details.get("content", ""),
                    'project': 'finderskeepers-v2',
                    'doc_type': 'conversation',
                    'tags': ['conversation', data.session_id, details.get('message_type', 'unknown')],
                    'metadata': {
                        'session_id': data.session_id,
                        'message_type': details.get('message_type'),
                        'context': details.get('context', {}),
                        'tools_used': details.get('tools_used', []),
                        'files_referenced': details.get('files_referenced', [])
                    }
                }
                
                # Process asynchronously for embeddings and entity extraction
                asyncio.create_task(pipeline.process_document(conversation_doc))
                logger.info(f"🧠 Triggered automatic processing for conversation {message_id}")
                
            except Exception as proc_error:
                logger.warning(f"Could not trigger automatic processing: {proc_error}")
            
        logger.info(f"✅ Action {action_id} logged successfully")
        return {"status": "ok", "action_id": action_id}
        
    except Exception as e:
        logger.error(f"❌ Action logging failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# HEALTH AND STATUS ENDPOINTS
# ========================================

@router.get("/health")
async def mcp_health(conn=Depends(get_conn)):
    """Check MCP integration health"""
    try:
        # Test database connection
        result = await conn.fetchval("SELECT 1")
        
        # Count recent sessions and actions
        session_count = await conn.fetchval(
            "SELECT COUNT(*) FROM agent_sessions WHERE created_at > NOW() - INTERVAL '24 hours'"
        )
        action_count = await conn.fetchval(
            "SELECT COUNT(*) FROM agent_actions WHERE created_at > NOW() - INTERVAL '24 hours'"
        )
        message_count = await conn.fetchval(
            "SELECT COUNT(*) FROM conversation_messages WHERE created_at > NOW() - INTERVAL '24 hours'"
        )
        
        return {
            "status": "healthy",
            "database": "connected" if result == 1 else "error",
            "stats_24h": {
                "sessions": session_count or 0,
                "actions": action_count or 0,
                "messages": message_count or 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ MCP health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/sessions/recent")
async def get_recent_sessions(limit: int = 10, conn=Depends(get_conn)):
    """Get recent MCP sessions"""
    try:
        sessions = await conn.fetch(
            """
            SELECT session_id, agent_type, user_id, project, status, 
                   start_time, end_time, termination_reason
            FROM agent_sessions
            ORDER BY start_time DESC
            LIMIT $1
            """,
            limit
        )
        
        return {
            "sessions": [dict(s) for s in sessions],
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get recent sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# CONVERSATION RETRIEVAL
# ========================================

@router.get("/conversations/{session_id}")
async def get_session_conversations(session_id: str, conn=Depends(get_conn)):
    """Get all conversation messages for a session"""
    try:
        messages = await conn.fetch(
            """
            SELECT message_id, message_type, content, context, 
                   reasoning, tools_used, files_referenced, created_at
            FROM conversation_messages
            WHERE session_id = $1
            ORDER BY created_at ASC
            """,
            session_id
        )
        
        return {
            "session_id": session_id,
            "messages": [dict(m) for m in messages],
            "count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# AI GOD MODE SPECIFIC ENDPOINTS
# ========================================

@router.get("/ai-god-mode/resume-context/{user_id}")
async def get_resume_context(user_id: str, project: str = None, conn=Depends(get_conn)):
    """Get AI GOD MODE resume context for perfect session restoration"""
    try:
        # Query the most recent ended AI GOD MODE session
        if project:
            session = await conn.fetchrow(
                """
                SELECT 
                    session_id, session_summary, accomplishments, failures,
                    conversation_count, tools_used, files_touched, ai_insights,
                    resume_context, (end_time - start_time) as session_duration
                FROM ai_session_memory
                WHERE user_id = $1 AND project = $2 AND status = 'ended'
                AND session_summary IS NOT NULL
                ORDER BY end_time DESC
                LIMIT 1
                """,
                user_id, project
            )
        else:
            session = await conn.fetchrow(
                """
                SELECT 
                    session_id, session_summary, accomplishments, failures,
                    conversation_count, tools_used, files_touched, ai_insights,
                    resume_context, (end_time - start_time) as session_duration
                FROM ai_session_memory
                WHERE user_id = $1 AND status = 'ended'
                AND session_summary IS NOT NULL
                ORDER BY end_time DESC
                LIMIT 1
                """,
                user_id
            )
        
        if not session:
            return {
                "status": "no_context",
                "message": "No previous AI GOD MODE sessions found",
                "user_id": user_id
            }
        
        return {
            "status": "context_available",
            "user_id": user_id,
            "context": dict(session),
            "ai_god_mode": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get AI GOD MODE resume context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-god-mode/sessions/{user_id}")
async def get_ai_god_mode_sessions(user_id: str, limit: int = 10, conn=Depends(get_conn)):
    """Get AI GOD MODE session history with analytics"""
    try:
        # Get recent AI GOD MODE sessions
        sessions = await conn.fetch(
            """
            SELECT 
                session_id, project, start_time, end_time, status,
                conversation_count, ai_insights, 
                jsonb_array_length(accomplishments) as accomplishments_count,
                jsonb_array_length(failures) as failures_count,
                (end_time - start_time) as duration
            FROM ai_session_memory
            WHERE user_id = $1
            ORDER BY start_time DESC
            LIMIT $2
            """,
            user_id, limit
        )
        
        # Get analytics
        analytics = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_sessions,
                COUNT(CASE WHEN status = 'ended' THEN 1 END) as completed_sessions,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_sessions,
                AVG(conversation_count) as avg_conversations_per_session,
                SUM(conversation_count) as total_conversations,
                AVG(EXTRACT(EPOCH FROM (end_time - start_time))/3600) as avg_duration_hours
            FROM ai_session_memory
            WHERE user_id = $1
            """,
            user_id
        )
        
        return {
            "user_id": user_id,
            "sessions": [dict(s) for s in sessions],
            "analytics": dict(analytics) if analytics else {},
            "ai_god_mode": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get AI GOD MODE sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-god-mode/search")
async def search_ai_god_mode_history(
    query: str, 
    user_id: str = "bitcain", 
    limit: int = 10, 
    conn=Depends(get_conn)
):
    """Search AI GOD MODE session history with intelligent ranking"""
    try:
        # Full-text search across AI GOD MODE sessions
        results = await conn.fetch(
            """
            SELECT 
                session_id, project, start_time, end_time,
                session_summary, ai_insights,
                GREATEST(
                    ts_rank(to_tsvector('english', coalesce(session_summary, '')), plainto_tsquery('english', $1)),
                    ts_rank(to_tsvector('english', coalesce(ai_insights, '')), plainto_tsquery('english', $1))
                ) as relevance
            FROM ai_session_memory
            WHERE user_id = $2
            AND (
                to_tsvector('english', coalesce(session_summary, '')) @@ plainto_tsquery('english', $1)
                OR to_tsvector('english', coalesce(ai_insights, '')) @@ plainto_tsquery('english', $1)
                OR project ILIKE '%' || $1 || '%'
            )
            ORDER BY relevance DESC, end_time DESC
            LIMIT $3
            """,
            query, user_id, limit
        )
        
        return {
            "query": query,
            "user_id": user_id,
            "results": [dict(r) for r in results],
            "count": len(results),
            "ai_god_mode": True
        }
        
    except Exception as e:
        logger.error(f"❌ AI GOD MODE search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
