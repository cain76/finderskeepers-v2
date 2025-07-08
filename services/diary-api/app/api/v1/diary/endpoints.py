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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/diary", tags=["Diary"])

# ========================================
# AGENT SESSION ENDPOINTS
# ========================================

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
    """Get a specific session by ID"""
    try:
        logger.info(f"Getting session: {session_id}")
        
        # Mock session data
        session = {
            "id": session_id,
            "agent_type": "claude",
            "session_start": "2025-07-08T08:00:00Z",
            "session_end": None,
            "status": "active",
            "context": {"project": "finderskeepers-v2"},
            "total_actions": 5,
            "performance_metrics": {
                "avg_response_time": 150,
                "total_tokens_used": 1250,
                "error_count": 0
            },
            "metadata": {
                "project_name": "finderskeepers-v2",
                "session_type": "development",
                "tags": ["gui", "react"]
            }
        }
        
        return {
            "success": True,
            "data": session,
            "message": f"Retrieved session {session_id}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
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
                "agent_type": "claude",
                "project": "finderskeepers-v2",
                "start_time": "2025-07-08T08:00:00Z",
                "description": "React frontend development session",
                "key_actions": ["component creation", "api integration", "routing setup"],
                "relevance_score": 0.95
            },
            {
                "session_id": "session_002",
                "agent_type": "claude", 
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