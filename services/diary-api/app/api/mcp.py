"""
MCP (Model Context Protocol) API Router for FindersKeepers v2
Direct integration bypassing n8n for session, action, and conversation logging
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncpg
import json
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(tags=["MCP"])

# ========================================
# PYDANTIC MODELS
# ========================================

class SessionStart(BaseModel):
    """Session start request from MCP server"""
    session_id: str
    agent_type: str = "claude-desktop"
    user_id: str = "bitcain"
    project: str = "finderskeepers-v2"
    timestamp: str
    source: Optional[str] = "fk2_mcp_server"

class Action(BaseModel):
    """Action logging request from MCP server"""
    session_id: str
    action_type: str
    description: str
    details: Dict[str, Any]
    files_affected: Optional[List[str]] = []
    success: bool = True
    timestamp: str
    source: Optional[str] = "fk2_mcp_server"

class SessionEnd(BaseModel):
    """Session end request from MCP server"""
    session_id: str
    reason: str = "session_complete"
    summary: str
    timestamp: str
    user_id: Optional[str] = "bitcain"
    agent_type: Optional[str] = "claude-desktop"
    project: Optional[str] = "finderskeepers-v2"

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
# SESSION ENDPOINTS
# ========================================

@router.post("/session/start")
async def mcp_session_start(data: SessionStart, conn=Depends(get_conn)):
    """Start a new MCP session - direct PostgreSQL insert"""
    try:
        logger.info(f"📝 MCP session start: {data.session_id} for {data.user_id}")
        
        # Insert or update agent_sessions
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
            json.dumps({"source": data.source, "timestamp": data.timestamp})
        )
        
        logger.info(f"✅ Session {data.session_id} started successfully")
        return {"status": "ok", "session_id": data.session_id}
        
    except Exception as e:
        logger.error(f"❌ Session start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/end")
async def mcp_session_end(data: SessionEnd, conn=Depends(get_conn)):
    """End an MCP session - update PostgreSQL"""
    try:
        logger.info(f"📝 MCP session end: {data.session_id}, reason: {data.reason}")
        
        # Update session status and summary
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
            data.summary,
            data.session_id
        )
        
        # Check if session was found and updated
        if result.split()[-1] == '0':
            logger.warning(f"Session {data.session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"✅ Session {data.session_id} ended successfully")
        return {"status": "ok", "session_id": data.session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Session end failed: {e}")
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
            message_id = f"msg_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
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
            
            # TODO: Trigger embedding generation and knowledge graph update
            # This would be done asynchronously via background tasks
            # For now, we'll add a TODO marker
            
            # from app.services.embedding import generate_and_store_embedding
            # from app.services.entities import extract_and_store_entities
            # await generate_and_store_embedding(message_id, details.get("content"))
            # await extract_and_store_entities(message_id)
        
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
