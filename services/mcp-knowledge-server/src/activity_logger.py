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
        self.agent_type = "claude-code"
        self.initialized = False
        self.session_start_time = None
        self.max_session_hours = int(os.getenv("MCP_SESSION_TIMEOUT_HOURS", "6"))  # Auto-end after 6h
        self._cleanup_task = None
        
    async def initialize(self):
        """Create a new session for this MCP server instance using n8n webhook"""
        try:
            # Only create session if explicitly requested
            if os.getenv("MCP_AUTO_SESSION", "false").lower() != "true":
                logger.info("🔒 Auto-session creation disabled (set MCP_AUTO_SESSION=true to enable)")
                self.initialized = False
                return
            
            # Check if services are available before creating session
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.fastapi_base_url}/health")
                    if response.status_code != 200:
                        logger.warning("⚠️ FastAPI not available, skipping session creation")
                        self.initialized = False
                        return
            except Exception as e:
                logger.info(f"⚠️ FastAPI not available ({e}), skipping session creation")
                self.initialized = False
                return
            
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
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.n8n_webhook_url}/webhook/agent-logger",
                    json=session_data,
                    timeout=5.0
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
                    self.session_start_time = datetime.utcnow()
                    logger.info(f"✅ MCP session created via n8n webhook: {self.session_id}")
                    
                    # Start cleanup timer
                    self._cleanup_task = asyncio.create_task(self._session_timeout_cleanup())
                    
                else:
                    logger.warning(f"⚠️ Failed to create session via n8n webhook: {response.status_code}")
                    self.initialized = False
                    
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"⚠️ n8n webhook timeout/connection error during initialization: {e}")
            # Continue without logging rather than fail the server
            self.initialized = False
        except Exception as e:
            logger.error(f"❌ MCP session initialization failed: {e}")
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
                    timeout=3.0  # Reduced timeout to prevent lockups
                )
                
                if response.status_code == 200:
                    logger.debug(f"✅ Logged action via n8n: {action_type}")
                else:
                    logger.debug(f"Failed to log action via n8n: {response.status_code}")
                    
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.debug(f"n8n webhook timeout/connection error: {e}")
            # Don't let network failures affect the main operation
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
    
    async def shutdown(self, reason: str = "graceful_shutdown"):
        """Log server shutdown and mark session as ended with fallback"""
        
        if self.initialized and self.session_id:
            try:
                # Log shutdown action first
                await self.log_action(
                    action_type="server_shutdown",
                    description="MCP Knowledge Server shutting down",
                    details={
                        "shutdown_time": datetime.utcnow().isoformat(),
                        "shutdown_reason": reason,
                        "graceful_shutdown": reason in ["graceful_shutdown", "user_exit", "sigterm"]
                    }
                )
                
                
                # Try to mark session as ended via n8n webhook first
                webhook_success = await self._try_webhook_session_end(reason)
                
                # If webhook fails, use direct database fallback
                if not webhook_success:
                    await self._direct_database_session_end(reason)
                
                # Cancel cleanup task
                if self._cleanup_task and not self._cleanup_task.done():
                    self._cleanup_task.cancel()
                
                # Mark as no longer initialized to prevent further logging
                self.initialized = False
                self.session_id = None
                
            except Exception as e:
                logger.error(f"Error during activity logger shutdown: {e}")
                # Don't let shutdown errors prevent the main shutdown
                self.initialized = False
                self.session_id = None

    async def _try_webhook_session_end(self, reason: str) -> bool:
        """Try to end session via n8n webhook"""
        try:
            session_end_data = {
                "session_id": self.session_id,
                "status": "ended",
                "end_time": datetime.utcnow().isoformat(),
                "reason": reason
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.n8n_webhook_url}/webhook/session-end",
                    json=session_end_data,
                    timeout=3.0  # Shorter timeout for faster fallback
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Session {self.session_id} ended via webhook")
                    return True
                else:
                    logger.warning(f"Webhook session end failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"Webhook session end error: {e}")
            return False

    async def _direct_database_session_end(self, reason: str):
        """Directly end session in database as fallback"""
        try:
            logger.info(f"Using database fallback to end session {self.session_id}")
            
            # Direct FastAPI call as fallback
            fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8000")
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{fastapi_url}/api/diary/sessions/{self.session_id}/end",
                    json={"reason": reason, "fallback": True},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Session {self.session_id} ended via database fallback")
                else:
                    logger.error(f"Database fallback failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Database fallback error: {e}")
            # Log this as a critical issue for manual intervention
            logger.critical(f"MANUAL_INTERVENTION_NEEDED: Session {self.session_id} not properly ended")

    async def _session_timeout_cleanup(self):
        """Auto-cleanup session after timeout to prevent zombies"""
        try:
            timeout_seconds = self.max_session_hours * 3600
            await asyncio.sleep(timeout_seconds)
            
            if self.initialized and self.session_id:
                logger.warning(f"⏰ Session {self.session_id} auto-ending after {self.max_session_hours}h timeout")
                await self.shutdown("session_timeout")
                
        except asyncio.CancelledError:
            # Normal cancellation during shutdown
            pass
        except Exception as e:
            logger.error(f"Error in session timeout cleanup: {e}")

# Global activity logger instance
activity_logger = ActivityLogger()