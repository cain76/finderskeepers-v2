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
        """Initialize the activity logger without creating a session"""
        try:
            # No automatic session creation - sessions are only created explicitly via MCP tools
            logger.info("🔒 Activity logger initialized without auto-session creation")
            self.initialized = True
            return
                    
        except Exception as e:
            logger.error(f"❌ Activity logger initialization failed: {e}")
            # Continue without logging rather than fail the server
            self.initialized = False
    
    def set_session_id(self, session_id: str):
        """Set the session ID for logging (called when session is created via MCP tools)"""
        self.session_id = session_id
        self.session_start_time = datetime.utcnow()
        logger.info(f"📝 Activity logger now tracking session: {session_id}")
        
        # Start cleanup timer
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        self._cleanup_task = asyncio.create_task(self._session_timeout_cleanup())
    
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
        
        if not self.initialized:
            return  # Skip logging if not initialized
        
        # Skip logging if no session is active (sessions are created explicitly via MCP tools)
        if not self.session_id:
            return
            
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
                database_success = False
                if not webhook_success:
                    database_success = await self._direct_database_session_end(reason)
                
                # Cancel cleanup task
                if self._cleanup_task and not self._cleanup_task.done():
                    self._cleanup_task.cancel()
                
                # Mark as no longer initialized to prevent further logging
                self.initialized = False
                self.session_id = None
                
                return {
                    "success": True,
                    "webhook_success": webhook_success,
                    "database_success": database_success or webhook_success,
                    "reason": reason,
                    "message": "Session ended gracefully"
                }
                
            except Exception as e:
                logger.error(f"Error during activity logger shutdown: {e}")
                # Don't let shutdown errors prevent the main shutdown
                self.initialized = False
                self.session_id = None
                
                return {
                    "success": False,
                    "error": str(e),
                    "reason": reason,
                    "message": "Session shutdown encountered errors"
                }
        else:
            return {
                "success": True,
                "message": "No active session to shutdown",
                "reason": reason
            }

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

    async def _direct_database_session_end(self, reason: str) -> bool:
        """Directly end session in database as fallback"""
        try:
            logger.info(f"Using direct database call to end session {self.session_id}")
            
            # Import and use the existing postgres client from knowledge_server
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Import the postgres client - using the same class as knowledge_server
            from database.postgres_client import PostgresClient
            
            # Use direct database call instead of HTTP request
            postgres = PostgresClient()
            result = await postgres.end_session(self.session_id, reason)
            
            if result.get("success", False):
                logger.info(f"✅ Session {self.session_id} ended via direct database call")
                return True
            else:
                logger.error(f"Direct database call failed: {result.get('error', 'Unknown error')}")
                return False
                    
        except Exception as e:
            logger.error(f"Direct database call error: {e}")
            # Log this as a critical issue for manual intervention
            logger.critical(f"MANUAL_INTERVENTION_NEEDED: Session {self.session_id} not properly ended")
            return False

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