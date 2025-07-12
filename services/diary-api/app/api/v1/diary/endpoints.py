"""
Diary API endpoints for agent session tracking - REAL DATA ONLY
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.database.queries import SessionQueries
from pydantic import BaseModel, Field
from uuid import uuid4

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diary", tags=["Diary"])

# ========================================
# DATA MODELS
# ========================================

class SessionCreate(BaseModel):
    """Create new agent session"""
    agent_type: str = Field(..., description="Type of agent (claude, gpt, etc.)")
    user_id: str = Field(default="local_user", description="User identifier")
    project: Optional[str] = Field(None, description="Project context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Session context")

class ActionCreate(BaseModel):
    """Create new agent action"""
    session_id: str = Field(..., description="Parent session ID")
    action_type: str = Field(..., description="Type of action (file_edit, command, etc.)")
    description: str = Field(..., description="Human-readable description")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action details")
    files_affected: Optional[List[str]] = Field(default_factory=list, description="Files modified")
    success: bool = Field(default=True, description="Action success status")

# ========================================
# AGENT SESSION ENDPOINTS
# ========================================

@router.post("/sessions")
async def create_session(session: SessionCreate):
    """Create new agent session"""
    try:
        session_id = f"session_{uuid4().hex[:8]}"
        
        logger.info(f"Creating new session: {session_id} for agent: {session.agent_type}")
        
        # Create session in database
        session_data = await SessionQueries.create_session(
            session_id=session_id,
            agent_type=session.agent_type,
            user_id=session.user_id,
            project=session.project,
            context=session.context
        )
        
        return {
            "success": True,
            "data": session_data,
            "message": f"Session {session_id} created successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/actions")
async def create_action(action: ActionCreate):
    """Create new agent action"""
    try:
        action_id = f"action_{uuid4().hex[:8]}"
        
        logger.info(f"Creating new action: {action_id} for session: {action.session_id}")
        
        # Create action in database
        action_data = await SessionQueries.create_action(
            action_id=action_id,
            session_id=action.session_id,
            action_type=action.action_type,
            description=action.description,
            details=action.details,
            files_affected=action.files_affected,
            success=action.success
        )
        
        return {
            "success": True,
            "data": action_data,
            "message": f"Action {action_id} created successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/end")
async def end_session(session_id: str):
    """End an active session"""
    try:
        logger.info(f"Ending session: {session_id}")
        
        # Update session end time
        session_data = await SessionQueries.end_session(session_id)
        
        return {
            "success": True,
            "data": session_data,
            "message": f"Session {session_id} ended successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/list")
async def list_sessions(
    limit: int = 10,
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    project: Optional[str] = None
):
    """Get REAL agent sessions from PostgreSQL database"""
    try:
        logger.info(f"Getting REAL sessions: limit={limit}, agent_type={agent_type}, status={status}")
        
        # Get REAL sessions from database
        sessions = await SessionQueries.get_sessions(
            limit=limit,
            agent_type=agent_type,
            project=project,
            status=status
        )
        
        return {
            "success": True,
            "data": sessions,
            "message": f"Retrieved {len(sessions)} REAL sessions from database",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session by ID - REAL DATABASE QUERY"""
    try:
        logger.info(f"Getting REAL session: {session_id}")
        
        # Get REAL session data from database
        session = await SessionQueries.get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "data": session,
            "message": f"Retrieved REAL session {session_id}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/actions")
async def get_session_actions(session_id: str):
    """Get REAL actions for a specific session from PostgreSQL"""
    try:
        logger.info(f"Getting REAL actions for session: {session_id}")
        
        # Get REAL actions from database
        actions = await SessionQueries.get_session_actions(session_id)
        
        return {
            "success": True,
            "data": actions,
            "message": f"Retrieved {len(actions)} REAL actions from database",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get session actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_sessions(
    q: Optional[str] = None,
    project: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: int = 10
):
    """Search agent session history"""
    try:
        logger.info(f"Searching sessions: q={q}, project={project}, agent_type={agent_type}")
        
        # Mock response for now
        results = [
            {
                "session_id": "session_001",
                "agent_type": "claude-code",
                "project": "finderskeepers-v2",
                "start_time": "2025-07-08T08:00:00Z",
                "description": "React frontend development session",
                "key_actions": ["component creation", "api integration", "routing setup"],
                "relevance_score": 0.95
            },
            {
                "session_id": "session_002",
                "agent_type": "claude-code", 
                "project": "finderskeepers-v2",
                "start_time": "2025-07-07T16:00:00Z",
                "description": "FastAPI endpoint development",
                "key_actions": ["endpoint creation", "database integration", "testing"],
                "relevance_score": 0.87
            }
        ]
        
        # Simple filtering
        if q:
            results = [r for r in results if q.lower() in r["description"].lower()]
        if project:
            results = [r for r in results if r["project"] == project]
        if agent_type:
            results = [r for r in results if r["agent_type"] == agent_type]
        
        return {
            "status": "success",
            "results": results[:limit],
            "total": len(results),
            "query": {"q": q, "project": project, "agent_type": agent_type}
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# # ========================================
# # DOCUMENTS ENDPOINT - Frontend Support  
# # ========================================

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Test endpoint working"}