"""
Diary API endpoints for agent session tracking
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

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
    """Get agent sessions with filtering"""
    try:
        logger.info(f"Getting sessions: limit={limit}, agent_type={agent_type}, status={status}")
        
        # Mock response for now - would connect to actual database
        sessions = [
            {
                "id": "session_001",
                "agent_type": agent_type or "claude",
                "session_start": "2025-07-08T08:00:00Z",
                "session_end": None,
                "status": status or "active",
                "context": {"project": project or "finderskeepers-v2"},
                "total_actions": 5,
                "performance_metrics": {
                    "avg_response_time": 150,
                    "total_tokens_used": 1250,
                    "error_count": 0
                },
                "metadata": {
                    "project_name": project or "finderskeepers-v2",
                    "session_type": "development",
                    "tags": ["gui", "react"]
                }
            },
            {
                "id": "session_002",
                "agent_type": "claude",
                "session_start": "2025-07-08T07:30:00Z",
                "session_end": "2025-07-08T08:15:00Z",
                "status": "completed",
                "context": {"project": "finderskeepers-v2"},
                "total_actions": 12,
                "performance_metrics": {
                    "avg_response_time": 180,
                    "total_tokens_used": 2840,
                    "error_count": 1
                },
                "metadata": {
                    "project_name": "finderskeepers-v2",
                    "session_type": "backend-development",
                    "tags": ["fastapi", "endpoints"]
                }
            },
            {
                "id": "session_003",
                "agent_type": "gpt",
                "session_start": "2025-07-07T16:45:00Z",
                "session_end": "2025-07-07T17:20:00Z",
                "status": "completed",
                "context": {"project": "finderskeepers-v2"},
                "total_actions": 8,
                "performance_metrics": {
                    "avg_response_time": 120,
                    "total_tokens_used": 1650,
                    "error_count": 0
                },
                "metadata": {
                    "project_name": "finderskeepers-v2",
                    "session_type": "documentation",
                    "tags": ["docs", "setup"]
                }
            }
        ]
        
        # Filter by agent_type if specified
        if agent_type:
            sessions = [s for s in sessions if s["agent_type"] == agent_type]
        
        # Filter by status if specified
        if status:
            sessions = [s for s in sessions if s["status"] == status]
        
        return {
            "success": True,
            "data": sessions[:limit],
            "message": f"Retrieved {len(sessions[:limit])} sessions",
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
    """Get actions for a specific session"""
    try:
        logger.info(f"Getting actions for session: {session_id}")
        
        # Mock response for now - would connect to actual database
        actions = [
            {
                "id": f"action_{i}",
                "session_id": session_id,
                "action_type": "file_read" if i % 2 == 0 else "file_write",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": 100 + i * 10,
                "success": True,
                "description": f"Action {i} description",
                "details": {"file": f"test_{i}.py"},
                "files_affected": [f"test_{i}.py"],
                "error_message": None
            }
            for i in range(5)
        ]
        
        return {
            "success": True,
            "data": actions,
            "message": f"Retrieved {len(actions)} actions",
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