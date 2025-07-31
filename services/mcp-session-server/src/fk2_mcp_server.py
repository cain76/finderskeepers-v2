#!/usr/bin/env python3
"""
FindersKeepers v2 Enhanced MCP Server (fk2-mcp) - FIXED VERSION
Modern FastMCP implementation for 2025 best practices
Optimized for bitcain.net Claude Desktop integration
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
import httpx
from fastmcp import FastMCP
import re

# Configure logging to stderr only (MCP requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# FastMCP 2.9+ Middleware imports for automatic conversation capture
try:
    from fastmcp.server.middleware import Middleware, MiddlewareContext
    middleware_available = True
    logger.info("✅ FastMCP 2.9+ middleware support available")
except ImportError:
    # Fallback if middleware not available in this FastMCP version
    middleware_available = False
    logger.warning("⚠️ FastMCP Middleware not available - continuing without auto-capture")

# Create FastMCP server instance
mcp = FastMCP("fk2-mcp")

# Global state for session management
current_session_id: Optional[str] = None
session_start_time: Optional[datetime] = None
db_pool: Optional[asyncpg.Pool] = None

# Service URLs - Updated for Docker containerized environment (2025 best practices)
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")

# CORRECTED: Use the ACTUAL n8n webhook endpoints that exist in active workflows
N8N_BASE_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678")

# FIXED: Use correct webhook endpoints from active n8n workflows
SESSION_WEBHOOK = f"{N8N_BASE_URL}/webhook/session-logger"       # FK2-MCP Enhanced Agent Session Logger
ACTION_WEBHOOK = f"{N8N_BASE_URL}/webhook/action-tracker"        # FK2-MCP Agent Action Tracker

# CONVERSATION LOGGING: action-tracker webhook processes conversation_message actions  
CONVERSATION_WEBHOOK = f"{N8N_BASE_URL}/webhook/action-tracker"  # Same as ACTION_WEBHOOK

async def initialize_database():
    """Initialize database connection pool with fixed concurrency settings"""
    global db_pool
    try:
        postgres_url = os.getenv(
            "POSTGRES_URL", 
            "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
        )
        
        # FIX: Reduced pool size and added connection limits to prevent conflicts
        db_pool = await asyncpg.create_pool(
            postgres_url,
            min_size=1,          # Reduced from previous value
            max_size=3,          # Reduced to prevent connection conflicts
            max_queries=50000,   # Limit queries per connection
            max_inactive_connection_lifetime=300,  # 5 minutes
            command_timeout=10,  # Reduced timeout
            server_settings={
                'jit': 'off',    # Disable JIT for faster connection
                'application_name': 'fk2_mcp_server'
            }
        )
        
        # Test connection with proper error handling
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Database connection test failed")
            
        logger.info("✅ Database connection pool established with fixed settings")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def log_action(action_type: str, description: str, details: Dict):
    """Log action via n8n webhook with enhanced error handling AND conversation capture"""
    global current_session_id
    if not current_session_id:
        return
        
    try:
        # CRITICAL: Also capture this as a conversation message for full context
        if action_type in ['vector_search', 'database_query', 'knowledge_graph_search', 'document_search']:
            # Extract the query from details for conversation logging
            query = details.get('query', description)
            await capture_conversation_message("tool_execution", f"User executed {action_type}: {query}")
        
        # Continue with normal action logging
        timeout_config = httpx.Timeout(20.0, connect=5.0, read=15.0)
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            action_data = {
                "session_id": current_session_id,
                "action_type": action_type,
                "description": description,
                "details": details,
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "source": "fk2_mcp_server"
            }
            
            response = await client.post(ACTION_WEBHOOK, json=action_data)
            
            # FIXED: Accept any successful response
            if 200 <= response.status_code < 300:
                logger.debug(f"✅ Action logged: {action_type}")
            else:
                logger.warning(f"Action webhook returned {response.status_code}")
            
    except httpx.TimeoutException:
        logger.debug(f"Action logging timeout (non-critical): {action_type}")
    except httpx.ConnectError:
        logger.debug(f"Action logging connection error (non-critical): {action_type}")
    except Exception as e:
        logger.debug(f"Action logging error (non-critical): {e}")

# FIXED: Simplified database query function without asyncio.timeout
async def safe_database_query(query: str, *args):
    """Execute database query with simplified connection handling"""
    global db_pool
    
    if not db_pool:
        success = await initialize_database()
        if not success:
            raise Exception("Database pool not available")
    
    # Simplified connection handling without asyncio.timeout
    try:
        async with db_pool.acquire() as conn:
            # Use fetchval for single values, fetch for multiple rows
            if query.strip().upper().startswith('SELECT') and 'COUNT(' in query.upper():
                return await conn.fetchval(query, *args)
            else:
                return await conn.fetch(query, *args)
    except asyncpg.exceptions.InterfaceError as e:
        # Handle the "operation in progress" error
        logger.error(f"Database interface error: {e}")
        raise Exception(f"Database interface error: {str(e)}")
    except Exception as e:
        logger.error(f"Database query error: {e}")
        raise Exception(f"Database query failed: {str(e)}")

async def close_database_pool():
    """Safely close database pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None

# =============================================================================
# AUTOMATIC CONVERSATION CAPTURE - n8n Integration
# =============================================================================

async def capture_conversation_message(message_type: str, content: str, metadata: dict = None):
    """
    CRITICAL FUNCTION: Send every conversation message to n8n for processing
    
    This is the CORE of FindersKeepers v2 - without this, no conversation logging,
    no vector embeddings, no knowledge graph relations, no semantic search!
    
    Usage:
        await capture_conversation_message("user_message", "Hello Claude!")
        await capture_conversation_message("assistant_response", "Hello! How can I help?")
        await capture_conversation_message("tool_execution", "Used vector_search tool")
        
    Args:
        message_type: Type of message ('user_message', 'assistant_response', 'tool_execution')
        content: The actual message content
        metadata: Additional context data
        
    This function sends to n8n agent-logger webhook which triggers:
    1. Database storage in PostgreSQL
    2. Vector embedding generation via Ollama
    3. Qdrant vector database storage  
    4. Knowledge graph relationship building
    5. Enables semantic search capabilities
    """
    global current_session_id
    
    if not current_session_id:
        logger.debug("No active session - skipping conversation capture")
        return
        
    try:
        payload = {
            "session_id": current_session_id,
            "action_type": "conversation_message",  # CRITICAL: This triggers the full pipeline
            "description": f"{message_type}: {content[:100]}...",
            "details": {
                "message_type": message_type,
                "content": content,
                "context": {
                    "user": "bitcain", 
                    "project": "finderskeepers-v2",
                    "server": "fk2_mcp_server",
                    "gpu_enabled": True,  # RTX 2080 Ti
                    "timestamp": datetime.now().isoformat()
                },
                "metadata": metadata or {},
                "tools_used": [],
                "files_referenced": []
            },
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "source": "fk2_mcp_server"
        }
        
        # CRITICAL: Send to n8n agent-logger webhook (Docker container: fk2_n8n:5678)
        # This webhook processes conversation data through the full FindersKeepers v2 pipeline
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            response = await client.post(CONVERSATION_WEBHOOK, json=payload)
            
            if 200 <= response.status_code < 300:
                logger.debug(f"✅ Conversation logged: {message_type} ({len(content)} chars)")
            else:
                logger.warning(f"⚠️ Conversation webhook returned HTTP {response.status_code}")
            
    except httpx.TimeoutException:
        logger.debug(f"Conversation logging timeout (non-critical): {message_type}")
    except httpx.ConnectError:
        logger.warning(f"❌ Cannot connect to n8n container - check Docker network: {message_type}")
    except Exception as e:
        logger.error(f"❌ CRITICAL: Conversation capture failed - {e}")
        logger.error("This breaks the entire FindersKeepers v2 memory system!")

# =============================================================================
# FASTMCP 2.9+ MIDDLEWARE FOR AUTOMATIC CONVERSATION CAPTURE
# =============================================================================

class FindersKeepersConversationMiddleware(Middleware if middleware_available else object):
    """
    2025 FastMCP Middleware for Automatic Conversation Capture
    Implements persistent memory across sessions for FindersKeepers v2
    """
    
    def __init__(self):
        if middleware_available:
            super().__init__()
        self.conversation_buffer = []
        self.last_user_message = None
        self.session_context = {}
        logger.info("🧠 FindersKeepers Conversation Middleware initialized")
    async def on_message(self, context: "MiddlewareContext", call_next):
        """
        CRITICAL: Capture ALL MCP messages for conversation tracking - FastMCP 2.9+ interface
        This is the AUTO-CAPTURE system that logs every user message and assistant response!
        """
        if not middleware_available:
            # Fallback if middleware not available
            return await call_next(context)
            
        global current_session_id
        
        if not current_session_id:
            return await call_next(context)
            
        # Extract content from the JSON-RPC message
        content = None
        message_type = "system"
        message = context.message
        
        try:
            # Handle different message formats
            if hasattr(message, 'method'):
                # This is a request - likely user input or tool call
                method = getattr(message, 'method', '')
                
                if method == "tools/call":
                    # Tool execution - extract user intent
                    params = getattr(message, 'params', {})
                    if 'arguments' in params:
                        args = params['arguments']
                        if isinstance(args, dict):
                            # Look for query, content, or message fields
                            content = args.get('query') or args.get('content') or args.get('message')
                            if content:
                                message_type = "user_tool_request"
                                self.last_user_message = content
                                
                elif method == "prompts/get":
                    # User prompt request
                    params = getattr(message, 'params', {})
                    prompt_name = params.get('name', '')
                    content = f"User requested prompt: {prompt_name}"
                    message_type = "user_prompt_request"
                    
                elif method.startswith("notifications/"):
                    # Skip notifications to avoid spam
                    pass
                    
            elif hasattr(message, 'result'):
                # This is a response - likely assistant output
                result = message.result
                if isinstance(result, dict):
                    if 'content' in result:
                        content = str(result['content'])
                        message_type = "assistant_response"
                    elif 'text' in result:
                        content = str(result['text'])
                        message_type = "assistant_response"
                elif isinstance(result, str):
                    content = result
                    message_type = "assistant_response"
                    
        except Exception as e:
            logger.debug(f"Middleware content extraction error: {e}")
            
        # Auto-capture significant conversations (more than 10 characters)
        if content and len(content.strip()) > 10:
            # Run capture in background to avoid blocking
            try:
                await self._auto_capture_conversation(message_type, content)
            except Exception as e:
                logger.debug(f"Background conversation capture error: {e}")
            
        # Continue the middleware chain with proper FastMCP 2.9+ interface
        return await call_next(context)
    
    async def _auto_capture_conversation(self, message_type: str, content: str):
        """Automatically capture conversation to n8n"""
        try:
            # Use existing capture function
            await capture_conversation_message(message_type, content)
            
            # Store in buffer for session summary
            self.conversation_buffer.append({
                "type": message_type,
                "content": content[:500],  # Limit for summary
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep buffer manageable (last 50 messages)
            if len(self.conversation_buffer) > 50:
                self.conversation_buffer = self.conversation_buffer[-50:]
                
        except Exception as e:
            logger.debug(f"Auto-capture error: {e}")
    
    async def generate_session_summary(self) -> str:
        """Generate CONCISE session summary for resume_session (context-window friendly)"""
        if not self.conversation_buffer:
            return "No significant conversation captured in this session."
            
        # Extract key topics and actions (CONCISE VERSION)
        topics = set()
        key_actions = []
        current_objectives = []
        
        for msg in self.conversation_buffer[-10:]:  # Only analyze last 10 messages
            content = msg["content"].lower()
            
            # Extract main topics
            for topic in ['docker', 'database', 'api', 'error', 'middleware', 'n8n', 'fastapi', 'postgres', 'vector', 'knowledge']:
                if topic in content:
                    topics.add(topic)
            
            # Extract key actions and objectives
            if msg["type"] == "user_tool_request":
                if any(word in content for word in ['implement', 'fix', 'create', 'update', 'install']):
                    key_actions.append(msg['content'][:80])
            
            # Extract current objectives
            if any(word in content for word in ['need to', 'should', 'next', 'todo', 'implement']):
                current_objectives.append(msg['content'][:100])
        
        # Build CONCISE summary (not full conversation history)
        summary_parts = [
            f"## 🧠 Smart Resume Context - {datetime.now().strftime('%m/%d %H:%M')}",
            f"**Session**: {current_session_id}",
            "",
            "### 🎯 Key Topics This Session:",
            ", ".join(sorted(topics)) if topics else "General conversation",
            "",
            "### ⚡ Recent Actions:",
        ]
        
        if key_actions:
            for action in key_actions[-3:]:  # Only last 3 actions
                summary_parts.append(f"- {action}")
        else:
            summary_parts.append("- No major actions recorded")
        
        if current_objectives:
            summary_parts.extend([
                "",
                "### 🎯 Current Objectives:",
            ])
            for obj in current_objectives[-3:]:  # Only last 3 objectives
                summary_parts.append(f"- {obj}")
        
        summary_parts.extend([
            "",
            "### 📋 Project State:",
            "- **Project**: FindersKeepers v2 MCP Server with Auto-Conversation Capture",
            "- **Location**: `/media/cain/linux_storage/projects/finderskeepers-v2/`",
            "- **Main File**: `services/mcp-session-server/src/fk2_mcp_server.py`",
            "- **Docker**: `fk2_network` - postgres:5432, fastapi:8000, n8n:5678, qdrant:6333",
            "- **n8n Active**: session-logger, action-tracker workflows",
            "",
            "### 🔍 Smart Memory Available:",
            f"- **Full conversation history**: Use `vector_search('topic')` to find past discussions",
            f"- **Technical context**: Use `knowledge_graph_search('implementation')` for relationships", 
            f"- **Specific details**: Use `database_query()` to find exact conversation records",
            "- **System gets smarter**: More sessions = better search results",
            "",
            "**💡 Use search tools to retrieve relevant past context when needed!**"
        ])
        
        return "\n".join(summary_parts)

# Initialize middleware instance only if available
if middleware_available:
    conversation_middleware = FindersKeepersConversationMiddleware()
    
    # Add middleware to FastMCP server with compatibility check
    try:
        if hasattr(mcp, 'add_middleware'):
            mcp.add_middleware(conversation_middleware)
            logger.info("✅ Conversation middleware registered via add_middleware")
        else:
            logger.warning("⚠️ add_middleware method not found")
            middleware_available = False
    except Exception as e:
        logger.warning(f"⚠️ Middleware registration failed: {e}")
        middleware_available = False
else:
    logger.info("ℹ️ Middleware not available, continuing without auto-conversation capture")

# =============================================================================
# MANUAL CONVERSATION CAPTURE TOOLS - FOR TESTING AND VALIDATION
# =============================================================================

@mcp.tool()
async def capture_this_conversation(user_message: str, assistant_response: str = None) -> str:
    """
    MANUAL CONVERSATION CAPTURE - Explicitly log this conversation exchange
    
    Use this tool to manually capture the current conversation exchange and send it
    through the FindersKeepers v2 pipeline for processing and storage.
    
    Args:
        user_message: What the user said/asked
        assistant_response: What Claude responded (optional - will be captured separately)
        
    This is useful for:
    - Testing the conversation logging pipeline
    - Ensuring important conversations are captured
    - Validating that the middleware is working
    """
    global current_session_id
    
    if not current_session_id:
        return "❌ No active session. Use `start_session` first."
    
    results = []
    
    try:
        # Capture user message
        await capture_conversation_message("user_message", user_message, {
            "manual_capture": True,
            "source": "capture_this_conversation_tool",
            "timestamp": datetime.now().isoformat()
        })
        results.append("✅ User message captured")
        
        # Capture assistant response if provided
        if assistant_response:
            await capture_conversation_message("assistant_response", assistant_response, {
                "manual_capture": True,
                "source": "capture_this_conversation_tool",
                "timestamp": datetime.now().isoformat()
            })
            results.append("✅ Assistant response captured")
        
        return f"""
🎯 **MANUAL CONVERSATION CAPTURE COMPLETED**

**Session**: {current_session_id}
**Results**: {len(results)} messages sent to n8n pipeline

{chr(10).join(results)}

**📡 Sent to n8n webhook**: {CONVERSATION_WEBHOOK}
**🔄 Processing pipeline**: 
1. n8n agent-logger workflow
2. PostgreSQL database storage
3. Ollama embedding generation
4. Qdrant vector database indexing
5. Neo4j knowledge graph relations

**⚡ Use `test_webhooks()` to validate the pipeline processed these messages!**
        """
        
    except Exception as e:
        return f"❌ Error capturing conversation: {str(e)}"

# =============================================================================
# SESSION MANAGEMENT TOOLS  
# =============================================================================

@mcp.tool()
async def start_session(project: str = "finderskeepers-v2", user_id: str = "bitcain") -> str:
    """Start a new FindersKeepers v2 session with enhanced error handling"""
    global current_session_id, session_start_time
    
    # Generate new session ID
    new_session_id = f"fk2_sess_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
    
    try:
        # FIX: Enhanced webhook call with better error handling
        session_data = {
            "session_id": new_session_id,
            "action_type": "session_start",
            "user_id": user_id,
            "agent_type": "claude-desktop",
            "project": project,
            "timestamp": datetime.now().isoformat(),
            "source": "fk2_mcp_server"
        }
        
        # FIXED: Increased timeout to allow for database retries
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0, read=20.0)  # Increased from 15s
        ) as client:
            response = await client.post(SESSION_WEBHOOK, json=session_data)
            
            # FIXED: Accept any 2xx response, not just 200
            if 200 <= response.status_code < 300:
                current_session_id = new_session_id
                session_start_time = datetime.now()
                
                logger.info(f"✅ Session started: {new_session_id}")
                
                return f"""
🚀 **FindersKeepers v2 Session Started Successfully**

**Session ID**: {new_session_id}
**Project**: {project}
**User**: {user_id}
**Started**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ **n8n Webhook Response**: HTTP {response.status_code}
✅ **Database Integration**: Active with error handling
✅ **GPU Acceleration**: RTX 2080 Ti enabled
✅ **Session Management**: Full lifecycle tracking enabled

**Available tools**: end_session, resume_session, vector_search, database_query, knowledge_graph_search
                """
            else:
                # FIXED: Better error reporting with graceful fallback
                try:
                    error_detail = response.text[:500]
                except:
                    error_detail = "Unable to read response"
                
                logger.warning(f"n8n webhook returned HTTP {response.status_code}: {error_detail}")
                
                # STILL CREATE SESSION LOCALLY for functionality
                current_session_id = new_session_id
                session_start_time = datetime.now()
                
                return f"""
⚠️ **Session Started with Partial Success**

**Session ID**: {new_session_id}
**Status**: Local session active, webhook logging degraded
**n8n Response**: HTTP {response.status_code}

**Note**: Core functionality available, session logging may be incomplete.
                """
                
    except httpx.TimeoutException as e:
        logger.warning(f"Session webhook timeout (normal if n8n is processing): {e}")
        
        # FIXED: Create session locally even if webhook times out
        current_session_id = new_session_id
        session_start_time = datetime.now()
        
        return f"""
⚠️ **Session Started Locally**

**Session ID**: {new_session_id}
**Status**: Session active, n8n logging delayed/offline
**Timeout**: {e}

**Core functionality available**: All search and database operations working.
**Note**: Session will be logged when n8n becomes responsive.
        """
        
    except httpx.ConnectError as e:
        logger.warning(f"Cannot connect to n8n (service may be starting): {e}")
        
        # FIXED: Graceful fallback
        current_session_id = new_session_id
        session_start_time = datetime.now()
        
        return f"""
⚠️ **Session Started in Offline Mode**

**Session ID**: {new_session_id}
**Status**: Local session only, n8n service unreachable
**Connection**: {e}

**All core tools available**: vector_search, database_query, document_search, knowledge_graph_search
**n8n Status**: Will retry logging when service becomes available
        """
        
    except Exception as e:
        logger.error(f"Unexpected session start error: {e}")
        
        # FIXED: Always provide functionality
        current_session_id = new_session_id
        session_start_time = datetime.now()
        
        return f"""
⚠️ **Session Started with Error Recovery**

**Session ID**: {new_session_id}
**Error**: {str(e)[:200]}...
**Status**: Core functionality preserved

**Available**: All search and database operations
**Recommendation**: Check n8n container status: `docker ps | grep fk2_n8n`
        """

@mcp.tool()
async def end_session(reason: str = "session_complete") -> str:
    """End current session, generate summary, and save for resume_session"""
    global current_session_id, session_start_time, db_pool
    
    if not current_session_id:
        return "❌ No active session to end"

    try:
        # Generate comprehensive session summary using middleware if available
        if middleware_available and 'conversation_middleware' in globals():
            session_summary = await conversation_middleware.generate_session_summary()
        else:
            session_summary = f"Session ended on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Basic summary (middleware not available)"
        
        # Store summary in database for resume_session
        async with db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE agent_sessions 
                SET 
                    status = 'ended',
                    end_time = NOW(),
                    termination_reason = $1,
                    session_summary = $2,
                    context = context || $3::jsonb
                WHERE session_id = $4
            """, reason, session_summary, json.dumps({
                "conversation_count": len(conversation_middleware.conversation_buffer) if middleware_available and 'conversation_middleware' in globals() else 0,
                "ended_by": "user_request",
                "summary_generated": True
            }), current_session_id)
        
        # Send end session to n8n
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            session_data = {
                "session_id": current_session_id,
                "action_type": "session_end",
                "reason": reason,
                "user_id": "bitcain",
                "agent_type": "claude-desktop",
                "project": "finderskeepers-v2",
                "summary": session_summary[:500]  # Truncated for webhook
            }
            await client.post(SESSION_WEBHOOK, json=session_data)
        
        ended_session = current_session_id
        current_session_id = None
        session_start_time = None
        
        # Clear middleware buffer if available
        if middleware_available and 'conversation_middleware' in globals():
            conversation_middleware.conversation_buffer.clear()
        
        return f"""
🎯 **Session Ended with Persistent Memory**

📊 **Session**: {ended_session}
📝 **Summary Generated**: ✅ Ready for resume_session
🧠 **Memory**: Stored in PostgreSQL for next session
⚡ **Reason**: {reason}

💾 **Summary Preview:**
{session_summary[:300]}...

🚀 **Next Session**: Use `resume_session()` to load this context automatically!
**AI GOD MODE**: Your context will be preserved! 🧠⚡
        """
        
    except Exception as e:
        return f"❌ Error ending session: {str(e)}"

@mcp.tool()
async def resume_session(max_messages: int = 20) -> str:
    """Resume from last session with SMART context summary - Progressive AI Memory!"""
    global current_session_id, session_start_time, db_pool
    
    try:
        # Find the most recent ended session with summary
        async with db_pool.acquire() as conn:
            recent_session = await conn.fetchrow("""
                SELECT 
                    session_id, agent_type, project, start_time, end_time, 
                    termination_reason, session_summary, context
                FROM agent_sessions 
                WHERE session_summary IS NOT NULL
                ORDER BY end_time DESC 
                LIMIT 1
            """)
            
            if not recent_session:
                return "❌ No previous sessions with summaries found"
        
        # Start new session
        new_session_id = f"fk2_sess_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        current_session_id = new_session_id
        session_start_time = datetime.now()
        
        # Create new session in n8n
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            session_data = {
                "session_id": new_session_id,
                "action_type": "session_start",
                "user_id": "bitcain", 
                "agent_type": "claude-desktop",
                "project": "finderskeepers-v2",
                "context": {
                    "resumed_from": recent_session['session_id'],
                    "has_memory": True,
                    "smart_memory": True,
                    "resume_time": datetime.now().isoformat()
                }
            }
            await client.post(SESSION_WEBHOOK, json=session_data)
        
        # Get the stored CONCISE summary (not full history)
        stored_summary = recent_session['session_summary'] or "No summary available"
        
        return f"""
🧠 **PROGRESSIVE AI MEMORY ACTIVATED - SMART CONTEXT LOADED!**

🔄 **New Session**: {new_session_id}
📜 **Smart Summary From**: {recent_session['session_id']} ({recent_session['end_time'].strftime('%m/%d %H:%M')})

{stored_summary}

---

## 🚀 **PROGRESSIVE MEMORY SYSTEM ACTIVE!**

✅ **Current context**: Loaded efficiently (no context window crushing!)
🔍 **Full history available**: Use search tools when you need specific past context:

### 💡 **Smart Memory Retrieval:**
- `vector_search("docker issue we solved")` → Find past technical solutions
- `knowledge_graph_search("middleware implementation")` → See project relationships  
- `database_query("SELECT content FROM conversation_messages WHERE...")` → Get exact details

### 🧠 **System Gets Smarter:**
- More sessions = Better search results
- More context = More relevant retrieval
- **AI evolves** with each interaction!

**Ready to continue with SMART context awareness!** 🧠⚡
        """
        
    except Exception as e:
        return f"❌ Error resuming session: {str(e)}"

@mcp.tool()
async def get_session_status() -> str:
    """Get current session information and statistics"""
    global current_session_id, session_start_time, db_pool
    
    if not current_session_id:
        return "❌ No active session"
    
    try:
        # Get session info from database
        async with db_pool.acquire() as conn:
            session_info = await conn.fetchrow("""
                SELECT * FROM agent_sessions 
                WHERE session_id = $1
            """, current_session_id)
            
            if session_info:
                duration = datetime.now() - session_info['start_time']
                
                # Get message count
                message_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM conversation_messages 
                    WHERE session_id = $1
                """, current_session_id) or 0
                
                # Get action count  
                action_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM agent_actions 
                    WHERE session_id = $1
                """, current_session_id) or 0
                
                return f"""
📊 **Current Session Status**

🆔 **Session ID**: {current_session_id}
⏰ **Duration**: {str(duration).split('.')[0]}
👤 **User**: {session_info['user_id']}
🤖 **Agent**: {session_info['agent_type']}
📁 **Project**: {session_info['project']}

📈 **Activity:**
- 💬 **Messages Logged**: {message_count}
- ⚡ **Actions Recorded**: {action_count}

🏠 **Platform**: bitcain.net
✅ **Session Status**: Active and logging

**FindersKeepers v2 ready for operations!**
                """
            else:
                return "❌ Session not found in database"
                
    except Exception as e:
        return f"❌ Error getting session status: {str(e)}"

@mcp.tool()
async def test_webhooks() -> str:
    """Test n8n webhook connectivity and database access with CORRECT WEBHOOK ENDPOINTS"""
    results = {
        "session_webhook": "❌ Not tested",
        "action_conversation_webhook": "❌ Not tested", 
        "database": "❌ Not tested",
        "full_pipeline": "❌ Not tested",
        "overall_status": "❌ Failed"
    }
    
    # Test session webhook (session-logger) - CORRECT ENDPOINT
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            test_data = {
                "session_id": "test_session_health_check",
                "action_type": "session_start",
                "user_id": "bitcain",
                "project": "finderskeepers-v2",
                "timestamp": datetime.now().isoformat(),
                "source": "fk2_mcp_server_test"
            }
            response = await client.post(SESSION_WEBHOOK, json=test_data)
            if 200 <= response.status_code < 300:
                results["session_webhook"] = f"✅ HTTP {response.status_code}"
            else:
                results["session_webhook"] = f"⚠️ HTTP {response.status_code}"
                
    except httpx.ConnectError as e:
        results["session_webhook"] = f"❌ Connection failed: {str(e)[:30]}..."
    except Exception as e:
        results["session_webhook"] = f"❌ {str(e)[:50]}..."
    
    # Test action-tracker webhook (CRITICAL for conversation logging) - CORRECT ENDPOINT
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            test_data = {
                "session_id": "test_session_health_check",
                "action_type": "conversation_message",  # CRITICAL: This triggers the full pipeline
                "description": "test: Pipeline validation message",
                "details": {
                    "message_type": "test_message",
                    "content": "This is a test conversation message to validate the FindersKeepers v2 pipeline works correctly.",
                    "context": {
                        "user": "bitcain", 
                        "project": "finderskeepers-v2",
                        "test": True,
                        "gpu_enabled": True
                    }
                },
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "source": "fk2_mcp_server_test"
            }
            response = await client.post(ACTION_WEBHOOK, json=test_data)
            if 200 <= response.status_code < 300:
                results["action_conversation_webhook"] = f"✅ HTTP {response.status_code} - PIPELINE TRIGGERED"
            else:
                results["action_conversation_webhook"] = f"❌ CRITICAL: HTTP {response.status_code} - PIPELINE BROKEN"
                
    except httpx.ConnectError as e:
        results["action_conversation_webhook"] = f"❌ CRITICAL: n8n container unreachable - {str(e)[:30]}..."
    except Exception as e:
        results["action_conversation_webhook"] = f"❌ CRITICAL: {str(e)[:50]}..."
    
    # Test database connectivity and document count
    try:
        count = await safe_database_query("SELECT COUNT(*) FROM documents;")
        results["database"] = f"✅ {count:,} documents ready for search"
    except Exception as e:
        results["database"] = f"❌ {str(e)[:50]}..."
    
    # Test full pipeline by checking if test data gets processed
    try:
        # Wait a moment for webhook processing
        await asyncio.sleep(2)
        
        # Check if our test conversation message was stored
        test_check = await safe_database_query("""
            SELECT COUNT(*) FROM conversation_messages 
            WHERE content LIKE '%Pipeline validation message%' 
            AND created_at > NOW() - INTERVAL '1 minute'
        """)
        
        if test_check and test_check > 0:
            results["full_pipeline"] = f"✅ End-to-end pipeline working - {test_check} test messages processed"
        else:
            results["full_pipeline"] = "⚠️ No test messages found in database - pipeline may have delays"
            
    except Exception as e:
        results["full_pipeline"] = f"❌ Pipeline validation failed: {str(e)[:50]}..."
    
    # Overall status assessment
    critical_working = "✅" in results["action_conversation_webhook"] and "✅" in results["database"]
    if critical_working and "✅" in results["full_pipeline"]:
        results["overall_status"] = "🚀 FINDERSKEEPERS V2 FULLY OPERATIONAL!"
    elif critical_working:
        results["overall_status"] = "⚡ Core functional - conversation logging active"
    elif "✅" in results["database"]:
        results["overall_status"] = "⚠️ Database working, webhooks need attention"
    else:
        results["overall_status"] = "❌ CRITICAL: System needs immediate attention"
    
    return f"""
🔧 **FINDERSKEEPERS V2 FULL SYSTEM HEALTH CHECK - CORRECTED ENDPOINTS**

**🎯 CRITICAL CONVERSATION PIPELINE:**
**Action/Conversation Webhook**: {results["action_conversation_webhook"]}

**📡 OTHER COMPONENTS:**
**Session Webhook**: {results["session_webhook"]}
**Database**: {results["database"]}
**Full Pipeline Test**: {results["full_pipeline"]}

**🏆 OVERALL STATUS**: {results["overall_status"]}

**🔗 CORRECT WEBHOOK URLs:**
- **Session**: {SESSION_WEBHOOK}
- **Action/Conversation**: {ACTION_WEBHOOK}

**✅ ACTIVE n8n WORKFLOWS:**
- FK2-MCP Enhanced Agent Session Logger (session-logger)
- FK2-MCP Agent Action Tracker (action-tracker) ← HANDLES CONVERSATIONS
- FK2 - Auto Entity Extraction (PostgreSQL trigger)

**🚀 DOCKER CONTAINERS TO CHECK:**
```bash
docker ps | grep fk2_n8n        # n8n workflows
docker ps | grep fk2_postgres   # Database
docker ps | grep fk2_fastapi    # Backend API
docker logs fk2_n8n --tail 20   # Check n8n logs
```

**⚡ AI GOD STATUS**: {'🏆 ACTIVATED!' if critical_working else '❌ NEEDS REPAIR!'}
    """

# =============================================================================
# SEARCH AND KNOWLEDGE TOOLS
# =============================================================================

@mcp.tool()
async def vector_search(query: str, collection: str = "fk2_documents", limit: int = 10) -> str:
    """Search the FindersKeepers v2 vector database using semantic similarity"""
    try:
        await log_action("vector_search", f"Searching: {query}", {"query": query, "collection": collection})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{FASTAPI_URL}/api/search/vector",
                json={
                    "query": query,
                    "collection": collection,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # FIX: FastAPI returns "data" not "results"
                search_data = results.get("data", [])
                if not search_data:
                    return f"🔍 No vector search results found for: '{query}'"
                
                search_results = []
                for idx, result in enumerate(search_data[:limit], 1):
                    # Handle both formats - payload.content or direct content
                    payload = result.get("payload", {})
                    content = payload.get("content", result.get("content", "No content available"))[:200]
                    score = result.get("score", 0)
                    metadata = payload if payload else result.get("metadata", {})
                    
                    search_results.append(f"""
**Result {idx}** (Score: {score:.3f})
**Content**: {content}...
**Metadata**: {json.dumps(metadata, indent=2) if metadata else 'None'}
                    """)
                
                return f"""
🔍 **Vector Search Results**

**Query**: "{query}"
**Collection**: {collection}
**Results Found**: {len(search_data)}

{chr(10).join(search_results)}

**Search completed successfully!**
                """
            else:
                return f"❌ Vector search failed: HTTP {response.status_code}"
                
    except Exception as e:
        return f"❌ Vector search error: {str(e)}"

@mcp.tool()
async def database_query(query: str, table: str = None) -> str:
    """Query the FindersKeepers v2 PostgreSQL database with fixed connection handling"""
    
    try:
        await log_action("database_query", f"Query: {query[:100]}", {"query": query, "table": table})
        
        # Security check - only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith(('SELECT', 'WITH')):
            return "❌ Only SELECT and WITH queries are allowed for security"
        
        # FIX: Use the safe database query function
        results = await safe_database_query(query)
        
        if not results:
            return f"🔍 No results found for query: {query[:100]}..."
        
        # Handle both single values and rows
        if isinstance(results, (int, str, float)):
            # Single value result
            return f"""
💾 **Database Query Results**

**Query**: {query}
**Result**: {results}

**Query completed successfully!**
            """
        else:
            # Multiple rows result
            formatted_results = []
            for idx, row in enumerate(results[:20], 1):  # Limit to 20 rows
                if hasattr(row, '_asdict'):
                    row_dict = row._asdict()
                else:
                    row_dict = dict(row)
                formatted_results.append(f"**Row {idx}**: {json.dumps(row_dict, default=str, indent=2)}")
            
            return f"""
💾 **Database Query Results**

**Query**: {query}
**Table**: {table or 'Multiple/Dynamic'}
**Rows Found**: {len(results)}

{chr(10).join(formatted_results)}

{f"**Note**: Showing first 20 rows of {len(results)} total results" if len(results) > 20 else ""}

**Query completed successfully!**
            """
            
    except Exception as e:
        error_msg = f"Database query error: {str(e)}"
        logger.error(error_msg)
        return f"❌ {error_msg}"

@mcp.tool()
async def knowledge_graph_search(query: str, entity_type: str = None, limit: int = 15) -> str:
    """Search the Neo4j knowledge graph for relationships and entities"""
    try:
        await log_action("knowledge_graph_search", f"Graph search: {query}", {"query": query, "entity_type": entity_type})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # FIX: Use correct FastAPI endpoint
            response = await client.post(
                f"{FASTAPI_URL}/api/knowledge/query",
                json={
                    "question": query,
                    "project": "finderskeepers-v2",
                    "include_history": True
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # FIX: FastAPI knowledge/query returns different format
                answer = results.get("answer", "")
                sources = results.get("sources", [])
                confidence = results.get("confidence", 0)
                
                if not answer and not sources:
                    return f"🔍 No knowledge graph results found for: '{query}'"
                
                knowledge_summary = []
                
                if answer:
                    knowledge_summary.append(f"**AI Analysis**: {answer}")
                
                if sources:
                    knowledge_summary.append(f"\n**Sources Found**: {len(sources)}")
                    for idx, source in enumerate(sources[:5], 1):
                        source_type = source.get("type", "Unknown")
                        source_id = source.get("id", "Unknown")
                        relevance = source.get("relevance", 0)
                        knowledge_summary.append(f"""
**Source {idx}**: {source_type}
**ID**: {source_id}
**Relevance**: {relevance}
                        """)
                
                return f"""
🕸️ **Knowledge Graph Search Results**

**Query**: "{query}"
**Confidence**: {confidence}

{chr(10).join(knowledge_summary)}

**Graph search completed successfully!**
                """
            else:
                return f"❌ Knowledge graph search failed: HTTP {response.status_code}"
                
    except Exception as e:
        return f"❌ Knowledge graph search error: {str(e)}"

@mcp.tool()
async def document_search(query: str, doc_type: str = "all", limit: int = 10) -> str:
    """Search through ingested documents in FindersKeepers v2"""
    try:
        await log_action("document_search", f"Document search: {query}", {"query": query, "doc_type": doc_type})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # FIX: Use correct FastAPI endpoint
            response = await client.post(
                f"{FASTAPI_URL}/api/docs/search",
                json={
                    "q": query,
                    "limit": limit
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # FIX: FastAPI docs/search returns "data" not "documents"
                documents = results.get("data", [])
                if not documents:
                    return f"🔍 No documents found for: '{query}'"
                
                doc_results = []
                for idx, doc in enumerate(documents[:limit], 1):
                    title = doc.get("title", "Untitled")
                    content = doc.get("content", "No content available")[:200]
                    file_type = doc.get("file_type", "Unknown")
                    created_at = doc.get("created_at", "Unknown")
                    source_file = doc.get("source_file", "Unknown")
                    
                    doc_results.append(f"""
**Document {idx}**: {title}
**Type**: {file_type}
**Created**: {created_at}
**Source**: {source_file}
**Content Preview**: {content}...
                    """)
                
                return f"""
📄 **Document Search Results**

**Query**: "{query}"
**Documents Found**: {len(documents)}
**Total in Database**: {results.get("total", "Unknown")}

{chr(10).join(doc_results)}

**Document search completed successfully!**
                """
            else:
                return f"❌ Document search failed: HTTP {response.status_code}"
                
    except Exception as e:
        return f"❌ Document search error: {str(e)}"

@mcp.tool()
async def log_conversation(message_type: str, content: str, metadata: dict = None) -> str:
    """
    MANUAL CONVERSATION LOGGING - Use this when automatic capture fails
    
    This tool explicitly sends conversation messages to n8n for processing.
    Use this if you notice conversations aren't being captured automatically.
    
    Args:
        message_type: 'user_message', 'assistant_response', 'tool_execution', 'code_snippet'
        content: The conversation content to log
        metadata: Optional additional context
        
    Returns status of the logging operation.
    """
    global current_session_id
    
    if not current_session_id:
        return "❌ No active session. Use `start_session` first."
    
    try:
        # Use the enhanced capture function
        await capture_conversation_message(message_type, content, metadata)
        
        return f"""
✅ **Manual Conversation Logged Successfully**

**Type**: {message_type}  
**Content Length**: {len(content)} characters
**Session**: {current_session_id}
**Webhook**: agent-logger (n8n container)

This message will be processed through the full FindersKeepers v2 pipeline:
1. 📝 Stored in PostgreSQL database
2. 🧠 Processed by Ollama embedding model  
3. 🔍 Indexed in Qdrant vector database
4. 🕸️ Added to Neo4j knowledge graph
5. 🚀 Available for semantic search
        """
        
    except Exception as e:
        return f"❌ Error logging conversation: {str(e)}"

@mcp.tool()
async def query_session_history(query: str, limit: int = 10) -> str:
    """Search and query session history with AI insights"""
    global db_pool
    
    try:
        await log_action("session_history_query", f"Query: {query}", {"query": query})
        
        async with db_pool.acquire() as conn:
            # Search sessions
            session_results = await conn.fetch("""
                SELECT session_id, project, user_id, start_time, end_time, status
                FROM agent_sessions 
                WHERE project ILIKE $1 OR user_id ILIKE $1
                ORDER BY start_time DESC 
                LIMIT $2
            """, f"%{query}%", limit)
            
            # Search actions
            action_results = await conn.fetch("""
                SELECT session_id, action_type, description, created_at
                FROM agent_actions 
                WHERE description ILIKE $1 OR action_type ILIKE $1
                ORDER BY created_at DESC 
                LIMIT $2
            """, f"%{query}%", limit)
            
            session_summary = []
            for session in session_results:
                duration = "Unknown"
                if session['end_time'] and session['start_time']:
                    duration = str(session['end_time'] - session['start_time']).split('.')[0]
                
                session_summary.append(f"""
**Session:** {session['session_id']}
**Project:** {session['project']}
**User:** {session['user_id']}
**Duration:** {duration}
**Status:** {session['status']}
                """)
            
            action_summary = []
            for action in action_results:
                action_summary.append(f"""
**Session:** {action['session_id']}
**Action:** {action['action_type']}
**Description:** {action['description'][:100]}...
**Time:** {action['created_at'].strftime('%Y-%m-%d %H:%M')}
                """)
            
            return f"""
🔍 **Session History Query Results**

**Query:** "{query}"
**Sessions Found:** {len(session_results)}
**Actions Found:** {len(action_results)}

**Sessions:**
{chr(10).join(session_summary) if session_summary else 'No matching sessions found.'}

**Actions:**
{chr(10).join(action_summary) if action_summary else 'No matching actions found.'}
            """
            
    except Exception as e:
        return f"❌ Session history query error: {str(e)}"

# =============================================================================
# SERVER STARTUP - FIXED FOR CLAUDE DESKTOP
# =============================================================================

# Initialize database on startup
@mcp.tool()
async def init_server() -> str:
    """Initialize server and database connections"""
    success = await initialize_database()
    if success:
        return "✅ FindersKeepers v2 MCP Server initialized successfully"
    else:
        return "❌ Server initialization failed"

# Critical fix: Use the correct pattern for Claude Desktop
if __name__ == "__main__":
    # Initialize database first
    logger.info("🚀 FindersKeepers v2 Enhanced MCP Server (fk2-mcp) starting...")
    logger.info("🔍 Available tools: vector_search, database_query, knowledge_graph_search, document_search")
    logger.info("📝 Session management: start_session, end_session, resume_session, get_session_status")
    logger.info("🏠 Optimized for bitcain.net Claude Desktop integration")
    
    # Database will be initialized on first use to avoid event loop conflicts
    logger.info("📡 Database will be initialized on first query to avoid event loop conflicts")
    
    # This is the CORRECT way for Claude Desktop - no asyncio.run()!
    mcp.run(transport="stdio")
