#!/usr/bin/env python3
"""
Activity Logger for MCP Knowledge Server
Automatically logs all agent activities to n8n workflows
"""

import asyncio
import httpx
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ActivityLogger:
    """Logs MCP server activities to n8n workflows"""
    
    def __init__(self):
        self.n8n_base_url = "http://localhost:5678"
        self.session_id = None
        self.agent_type = "mcp_knowledge_server"
        self.initialized = False
        
    async def initialize(self):
        """Create a new session for this MCP server instance"""
        try:
            # Create session with n8n webhook
            session_data = {
                "agent_type": self.agent_type,
                "project": "finderskeepers_v2",
                "context": {
                    "server": "mcp_knowledge_server",
                    "version": "1.0.0",
                    "started_at": datetime.utcnow().isoformat(),
                    "capabilities": [
                        "search_documents",
                        "query_knowledge_graph", 
                        "get_session_context",
                        "analyze_document_similarity",
                        "get_project_overview"
                    ]
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.n8n_base_url}/webhook/agent-logger",
                    json=session_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # n8n returns array with session info
                    if isinstance(result, list) and len(result) > 0:
                        session_info = result[0]
                        if isinstance(session_info, dict) and "session_id" in session_info:
                            self.session_id = session_info["session_id"]
                    elif isinstance(result, dict) and "session_id" in result:
                        self.session_id = result["session_id"]
                    
                    if not self.session_id:
                        # Generate our own if not provided
                        self.session_id = f"mcp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                    
                    self.initialized = True
                    logger.info(f"✅ Activity logger initialized with session: {self.session_id}")
                else:
                    logger.warning(f"Failed to initialize activity logger: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Activity logger initialization failed: {e}")
            # Continue without logging rather than fail the server
            self.initialized = False
    
    async def log_action(
        self,
        action_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        files_affected: Optional[list] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log an action to the n8n workflow"""
        
        if not self.initialized or not self.session_id:
            return  # Skip logging if not initialized
            
        try:
            # Generate action_id for this action
            action_id = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            action_data = {
                "action_id": action_id,
                "session_id": self.session_id,
                "action_type": action_type,
                "description": description,
                "details": details or {},
                "files_affected": files_affected or [],
                "success": success,
                "error_message": error_message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.n8n_base_url}/webhook/agent-actions",
                    json=action_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ Logged action: {action_type}")
                else:
                    logger.debug(f"Failed to log action: {response.status_code}")
                    
        except Exception as e:
            logger.debug(f"Action logging failed: {e}")
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