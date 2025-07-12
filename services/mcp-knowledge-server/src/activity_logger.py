#!/usr/bin/env python3
"""
Activity Logger for MCP Knowledge Server
Automatically logs all agent activities to n8n workflows
"""

import asyncio
import httpx
import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ActivityLogger:
    """Logs MCP server activities to n8n workflows"""
    
    def __init__(self):
        self.fastapi_base_url = os.getenv("FASTAPI_URL", "http://localhost:8000")
        self.n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678")
        self.session_id = None
        self.agent_type = "fk2_mcp_knowledge_server"
        self.initialized = False
        
    async def initialize(self):
        """Create a new session for this MCP server instance using n8n webhook"""
        try:
            # Create session using n8n Agent Session Logger webhook
            session_data = {
                "agent_type": self.agent_type,
                "user_id": "local_user",
                "project": "finderskeepers-v2",
                "context": {
                    "server": "mcp_knowledge_server",
                    "version": "2.0.0",
                    "started_at": datetime.utcnow().isoformat(),
                    "connection_type": "automatic_startup",
                    "capabilities": [
                        "search_documents",
                        "query_knowledge_graph", 
                        "get_session_context",
                        "analyze_document_similarity",
                        "get_project_overview"
                    ],
                    "auto_logging": True,
                    "purpose": "MCP server session for AI agent knowledge access"
                }
            }
            
            # Call n8n Agent Session Logger webhook using fk2 naming convention
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.n8n_webhook_url}/webhook/agent-logger",
                    json=session_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # n8n webhook returns array with session data
                    if isinstance(result, list) and len(result) > 0:
                        session_response = result[0]
                        if "session_id" in session_response:
                            self.session_id = session_response["session_id"]
                    
                    if not self.session_id:
                        # Generate fallback session_id
                        self.session_id = f"mcp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    
                    self.initialized = True
                    logger.info(f"✅ MCP session created via n8n webhook: {self.session_id}")
                    
                    # Get current project context immediately after session creation
                    await self.retrieve_current_context()
                    
                else:
                    logger.warning(f"Failed to create session via n8n webhook: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"MCP session initialization failed: {e}")
            # Continue without logging rather than fail the server
            self.initialized = False
    
    async def retrieve_current_context(self):
        """Retrieve current project context and recent activity to understand where we are"""
        try:
            if not self.session_id:
                return
                
            # Get recent sessions and actions for finderskeepers-v2 project
            async with httpx.AsyncClient() as client:
                # Get recent session data
                sessions_response = await client.get(
                    f"{self.fastapi_base_url}/api/diary/sessions",
                    params={"project": "finderskeepers-v2", "limit": 5},
                    timeout=10.0
                )
                
                if sessions_response.status_code == 200:
                    sessions_data = sessions_response.json()
                    recent_sessions = sessions_data.get("data", {}).get("sessions", [])
                    
                    if recent_sessions:
                        latest_session = recent_sessions[0]
                        logger.info(f"📋 Latest session: {latest_session.get('session_id')} by {latest_session.get('agent_type')}")
                        
                        # Get actions from the most recent session
                        actions_response = await client.get(
                            f"{self.fastapi_base_url}/api/diary/sessions/{latest_session['session_id']}/actions",
                            timeout=10.0
                        )
                        
                        if actions_response.status_code == 200:
                            actions_data = actions_response.json()
                            recent_actions = actions_data.get("data", {}).get("actions", [])
                            
                            # Log context retrieval with summary of recent activity
                            await self.log_action(
                                action_type="context_retrieval",
                                description="Retrieved current project context on MCP server startup",
                                details={
                                    "recent_sessions_found": len(recent_sessions),
                                    "latest_session_id": latest_session.get('session_id'),
                                    "latest_agent_type": latest_session.get('agent_type'),
                                    "recent_actions_count": len(recent_actions),
                                    "last_action_time": recent_actions[0].get('timestamp') if recent_actions else None,
                                    "last_action_type": recent_actions[0].get('action_type') if recent_actions else None,
                                    "files_recently_modified": [action.get('files_affected', []) for action in recent_actions[:3] if action.get('files_affected')],
                                    "project_status": "active" if recent_sessions else "new"
                                },
                                success=True
                            )
                            
                            logger.info(f"🔍 Found {len(recent_actions)} recent actions. Last: {recent_actions[0].get('action_type') if recent_actions else 'None'}")
                            
        except Exception as e:
            logger.debug(f"Context retrieval failed (non-critical): {e}")
    
    async def log_action(
        self,
        action_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        files_affected: Optional[list] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log an action to the n8n Agent Action Tracker webhook"""
        
        if not self.initialized or not self.session_id:
            return  # Skip logging if not initialized
            
        try:
            action_data = {
                "session_id": self.session_id,
                "action_type": action_type,
                "description": description,
                "details": details or {},
                "files_affected": files_affected or [],
                "success": success
            }
            
            if error_message:
                action_data["details"]["error_message"] = error_message
            
            # Call n8n Agent Action Tracker webhook using fk2 naming convention
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.n8n_webhook_url}/webhook/agent-actions",
                    json=action_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ Logged action via n8n: {action_type}")
                else:
                    logger.debug(f"Failed to log action via n8n: {response.status_code}")
                    
        except Exception as e:
            logger.debug(f"Action logging via n8n failed: {e}")
            # Don't let logging failures affect the main operation
    
    async def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: Any):
        """Log a tool call with its arguments and results"""
        
        details = {
            "tool": tool_name,
            "arguments": arguments,
            "result_preview": str(result)[:500] if result else None,
            "result_type": type(result).__name__
        }
        
        await self.log_action(
            action_type=f"tool_call:{tool_name}",
            description=f"Called tool: {tool_name}",
            details=details,
            success=result is not None
        )
    
    async def log_resource_access(self, resource_uri: str):
        """Log when a resource is accessed"""
        
        await self.log_action(
            action_type="resource_access",
            description=f"Accessed resource: {resource_uri}",
            details={"resource_uri": resource_uri}
        )
    
    async def log_error(self, operation: str, error: Exception):
        """Log an error that occurred during an operation"""
        
        await self.log_action(
            action_type=f"error:{operation}",
            description=f"Error in {operation}",
            details={
                "error_type": type(error).__name__,
                "error_message": str(error)
            },
            success=False,
            error_message=str(error)
        )
    
    async def shutdown(self):
        """Log server shutdown"""
        
        if self.initialized and self.session_id:
            await self.log_action(
                action_type="server_shutdown",
                description="MCP Knowledge Server shutting down",
                details={
                    "shutdown_time": datetime.utcnow().isoformat(),
                    "session_duration": "calculated_by_n8n"
                }
            )

# Global activity logger instance
activity_logger = ActivityLogger()