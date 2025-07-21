#!/usr/bin/env python3
"""
Universal Conversation Logging Middleware for MCP Knowledge Server
Automatically captures ALL conversations from ANY MCP client (Claude, Copilot, Google, etc.)

This middleware intercepts all MCP messages and automatically logs conversations
to our n8n Agent workflows, enabling universal agent memory across all platforms.
"""

import asyncio
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ConversationLoggingMiddleware:
    """
    Universal MCP Middleware that automatically captures conversations from ANY MCP client
    
    This middleware:
    - Intercepts ALL MCP requests and responses
    - Infers conversation content from tool calls and responses
    - Automatically logs to n8n Agent Action Tracker 
    - Works with Claude Code, GitHub Copilot, Google agents, etc.
    - Creates universal agent memory across all platforms
    """
    
    def __init__(self, activity_logger):
        self.activity_logger = activity_logger
        self.session_conversations = {}  # Track conversation flow per session
        self.message_sequence = {}       # Track message ordering
        
    async def on_message(self, message: Dict[str, Any], session_id: Optional[str] = None):
        """
        Universal message interceptor - captures ALL MCP communication
        
        Args:
            message: MCP message (request or response)
            session_id: Session identifier (if available)
        """
        try:
            if not self.activity_logger.initialized or not session_id:
                return
                
            # Initialize session tracking
            if session_id not in self.session_conversations:
                self.session_conversations[session_id] = []
                self.message_sequence[session_id] = 0
                
            message_type = message.get('method', message.get('type', 'unknown'))
            
            # Handle different message types
            if message.get('method'):  # This is a request
                await self._handle_request(message, session_id)
            elif message.get('result') is not None:  # This is a response
                await self._handle_response(message, session_id)
                
        except Exception as e:
            logger.error(f"Error in conversation logging middleware: {e}")
    
    async def _handle_request(self, request: Dict[str, Any], session_id: str):
        """Handle MCP request messages - infer user intent"""
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            
            # Infer user message from tool calls
            user_content = await self._infer_user_intent(method, params)
            
            if user_content:
                await self._log_conversation_message(
                    session_id=session_id,
                    message_type="user_message", 
                    content=user_content,
                    context={
                        "mcp_method": method,
                        "inferred_from": "tool_call",
                        "source_client": "universal_mcp"
                    },
                    reasoning=f"User action inferred from MCP tool call: {method}",
                    tools_used=[method],
                    files_referenced=self._extract_file_references(params)
                )
                
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
    
    async def _handle_response(self, response: Dict[str, Any], session_id: str):
        """Handle MCP response messages - capture AI responses"""
        try:
            result = response.get('result', {})
            
            # Extract meaningful response content
            ai_content = await self._extract_ai_response(result)
            
            if ai_content:
                await self._log_conversation_message(
                    session_id=session_id,
                    message_type="ai_response",
                    content=ai_content,
                    context={
                        "response_type": "mcp_tool_result",
                        "source_system": "mcp_knowledge_server"  
                    },
                    reasoning="AI response from MCP tool execution",
                    tools_used=["mcp_knowledge_server"],
                    files_referenced=self._extract_file_references(result)
                )
                
        except Exception as e:
            logger.error(f"Error handling MCP response: {e}")
    
    async def _infer_user_intent(self, method: str, params: Dict[str, Any]) -> str:
        """
        Infer user intent from MCP tool calls
        
        This converts technical tool calls into natural language representing
        what the user was trying to accomplish
        """
        intent_patterns = {
            'search_documents': lambda p: f"User wants to search for: {p.get('query', 'unknown query')}",
            'query_knowledge_graph': lambda p: f"User wants to find relationships about: {p.get('question', 'unknown topic')}",
            'get_full_conversation_context': lambda p: f"User wants to see conversation history for session: {p.get('session_id', 'current session')}",
            'resume_session': lambda p: f"User wants to resume work on project: {p.get('project', 'current project')}",
            'initialize_claude_session': lambda p: f"User started a new session for: {p.get('project', 'unknown project')}",
            'endsession': lambda p: f"User wants to end session because: {p.get('reason', 'work complete')}",
            'analyze_document_similarity': lambda p: f"User wants to find documents similar to: {p.get('document_id', 'unknown document')}",
            'log_conversation_message': lambda p: f"System logging: {p.get('content', '')[:100]}...",
            'log_claude_action': lambda p: f"User performed action: {p.get('description', 'unknown action')}"
        }
        
        # Remove mcp__fk-knowledge__ prefix if present
        clean_method = method.replace('mcp__fk-knowledge__', '')
        
        if clean_method in intent_patterns:
            return intent_patterns[clean_method](params)
        else:
            return f"User used tool: {method} with parameters: {json.dumps(params, default=str)[:200]}"
    
    async def _extract_ai_response(self, result: Dict[str, Any]) -> str:
        """Extract meaningful AI response content from MCP results"""
        try:
            # Handle different result formats
            if isinstance(result, str):
                return result[:1000]  # Truncate long responses
            elif isinstance(result, dict):
                # Look for common response fields
                response_fields = ['message', 'content', 'summary', 'result', 'answer']
                for field in response_fields:
                    if field in result:
                        return str(result[field])[:1000]
                        
                # If no specific field, return formatted dict
                return json.dumps(result, default=str)[:1000]
            elif isinstance(result, list):
                return f"Returned {len(result)} results: {str(result[:3])[:500]}..."
            else:
                return str(result)[:1000]
                
        except Exception as e:
            logger.error(f"Error extracting AI response: {e}")
            return f"AI response (parsing error): {str(result)[:200]}"
    
    def _extract_file_references(self, data: Any) -> list:
        """Extract file references from MCP parameters or results"""
        try:
            files = []
            if isinstance(data, dict):
                # Look for common file reference fields
                file_fields = ['file_path', 'files', 'documents', 'files_referenced', 'files_affected']
                for field in file_fields:
                    if field in data:
                        value = data[field]
                        if isinstance(value, str):
                            files.append(value)
                        elif isinstance(value, list):
                            files.extend([str(f) for f in value])
                            
            return files[:10]  # Limit to 10 files max
            
        except Exception:
            return []
    
    async def _log_conversation_message(self, session_id: str, message_type: str, 
                                      content: str, context: Dict[str, Any],
                                      reasoning: str, tools_used: list, 
                                      files_referenced: list):
        """Log conversation message directly to n8n Agent Session Logger (bypassing broken Action Tracker)"""
        try:
            # Increment message sequence for this session
            self.message_sequence[session_id] = self.message_sequence.get(session_id, 0) + 1
            
            # Create conversation message payload for Agent Session Logger
            conversation_data = {
                "session_id": session_id,
                "action_type": "conversation_message", 
                "message_type": message_type,
                "content": content,
                "context": context,
                "reasoning": reasoning,
                "tools_used": tools_used,
                "files_referenced": files_referenced,
                "sequence_number": self.message_sequence[session_id],
                "capture_method": "universal_mcp_middleware",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Direct call to Agent Session Logger webhook (bypasses broken Action Tracker)
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.activity_logger.n8n_webhook_url}/webhook/agent-logger",
                    json=conversation_data,
                    timeout=3.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Conversation logged directly to Agent Session Logger: {message_type}")
                else:
                    logger.warning(f"⚠️ Agent Session Logger failed: {response.status_code} - {response.text}")
            
            # FALLBACK: Also try the broken activity_logger for compatibility
            try:
                await self.activity_logger.log_action(
                    action_type=f"conversation:{message_type}",
                    description=f"Universal MCP conversation capture: {message_type}",
                    files_affected=files_referenced,
                    details={
                        "message_type": message_type,
                        "content": content[:500],  # Truncated for details
                        "context": context,
                        "reasoning": reasoning,
                        "tools_used": tools_used,
                        "sequence_number": self.message_sequence[session_id],
                        "capture_method": "mcp_middleware"
                    },
                    success=True
                )
            except Exception as fallback_error:
                logger.debug(f"Activity logger fallback failed (expected): {fallback_error}")
            
            # Store in session conversation buffer
            self.session_conversations[session_id].append({
                "sequence": self.message_sequence[session_id],
                "type": message_type,
                "content": content,
                "timestamp": datetime.utcnow(),
                "context": context
            })
            
            # Keep only last 50 messages per session to prevent memory bloat
            if len(self.session_conversations[session_id]) > 50:
                self.session_conversations[session_id] = self.session_conversations[session_id][-50:]
                
            logger.info(f"🎯 Universal conversation captured: {message_type} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error logging conversation message: {e}")
    
    def get_session_conversation_buffer(self, session_id: str) -> list:
        """Get recent conversation buffer for a session"""
        return self.session_conversations.get(session_id, [])
    
    def clear_session_conversation_buffer(self, session_id: str):
        """Clear conversation buffer for a session (e.g., when session ends)"""
        if session_id in self.session_conversations:
            del self.session_conversations[session_id]
        if session_id in self.message_sequence:
            del self.message_sequence[session_id]
            
        logger.info(f"🧹 Cleared conversation buffer for session {session_id}")


# Global middleware instance
conversation_middleware = None

def initialize_conversation_middleware(activity_logger):
    """Initialize the global conversation logging middleware"""
    global conversation_middleware
    conversation_middleware = ConversationLoggingMiddleware(activity_logger)
    logger.info("🌐 Universal conversation logging middleware initialized")
    return conversation_middleware

def get_conversation_middleware():
    """Get the global conversation middleware instance"""
    return conversation_middleware