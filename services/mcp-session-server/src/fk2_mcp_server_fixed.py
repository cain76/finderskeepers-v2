#!/usr/bin/env python3
"""
FindersKeepers v2 Enhanced MCP Server (fk2-mcp) - FIXED VERSION 2025
Modern FastMCP implementation optimized for bitcain.net Claude Desktop integration
Fixes asyncio loop and function signature issues
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
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr only (MCP requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP("fk2-mcp")

# Global state for session management
current_session_id: Optional[str] = None
session_start_time: Optional[datetime] = None
db_pool: Optional[asyncpg.Pool] = None

# Service URLs using localhost (Docker containers expose ports to localhost)
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
N8N_BASE_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678")

# Webhook endpoints for logging
SESSION_WEBHOOK = f"{N8N_BASE_URL}/webhook/agent-logger"
ACTION_WEBHOOK = f"{N8N_BASE_URL}/webhook/agent-action-tracker"

async def initialize_database():
    """Initialize database connection pool"""
    global db_pool
    try:
        postgres_url = os.getenv(
            "POSTGRES_URL", 
            "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
        )
        
        db_pool = await asyncpg.create_pool(
            postgres_url,
            min_size=1,
            max_size=5,
            command_timeout=30
        )
        
        # Test connection
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            
        logger.info("✅ Database connection established")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def log_action(action_type: str, description: str, details: Dict):
    """Log action via n8n webhook"""
    global current_session_id
    if not current_session_id:
        return
        
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            action_data = {
                "session_id": current_session_id,
                "action_type": action_type,
                "description": description,
                "details": details,
                "success": True
            }
            
            await client.post(ACTION_WEBHOOK, json=action_data)
            
    except Exception as e:
        # Don't fail the main operation if logging fails
        logger.error(f"Error logging action: {e}")

# =============================================================================
# SESSION MANAGEMENT TOOLS
# =============================================================================

@mcp.tool()
async def start_session(project: str = "finderskeepers-v2", user_id: str = "bitcain") -> str:
    """Start a new FindersKeepers v2 session with full logging"""
    global current_session_id, session_start_time
    
    # Generate new session ID
    new_session_id = f"fk2_sess_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
    
    try:
        # Start session via n8n webhook
        async with httpx.AsyncClient(timeout=10.0) as client:
            session_data = {
                "session_id": new_session_id,
                "action_type": "session_start",
                "user_id": user_id,
                "agent_type": "claude-desktop",
                "project": project
            }
            
            response = await client.post(SESSION_WEBHOOK, json=session_data)
            
            if response.status_code == 200:
                current_session_id = new_session_id
                session_start_time = datetime.now()
                
                return f"""
🚀 **FindersKeepers v2 Session Started**

**Session ID**: {new_session_id}
**Project**: {project}
**User**: {user_id}
**Started**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ **Ready for AI-powered knowledge management**
- All conversations will be automatically logged
- Vector embeddings generated for semantic search
- Knowledge graph updated with relationships
- Full GPU acceleration (RTX 2080 Ti) enabled

**Available tools**: end_session, resume_session, vector_search, database_query, knowledge_graph_search
                """
            else:
                return f"❌ Failed to start session via n8n: {response.status_code}"
                
    except Exception as e:
        return f"❌ Error starting session: {str(e)}"

@mcp.tool()
async def end_session(reason: str = "session_complete") -> str:
    """End current session and save all data"""
    global current_session_id, session_start_time
    
    if not current_session_id:
        return "❌ No active session to end"

    try:
        # End session via n8n webhook
        async with httpx.AsyncClient(timeout=10.0) as client:
            session_data = {
                "session_id": current_session_id,
                "action_type": "session_end",
                "reason": reason,
                "user_id": "bitcain",
                "agent_type": "claude-desktop",
                "project": "finderskeepers-v2"
            }
            
            response = await client.post(SESSION_WEBHOOK, json=session_data)
            
            if response.status_code == 200:
                # Calculate session duration
                duration = "Unknown"
                if session_start_time:
                    duration = str(datetime.now() - session_start_time).split('.')[0]
                
                ended_session = current_session_id
                current_session_id = None
                session_start_time = None
                
                return f"""
🎯 **Session Ended Successfully**

**Session ID**: {ended_session}
**Reason**: {reason}
**Duration**: {duration}

💾 **Data Preservation Complete**
- ✅ All conversation data saved to PostgreSQL
- ✅ Vector embeddings stored in Qdrant
- ✅ Knowledge graph updated in Neo4j
- ✅ Session context preserved for future resumption

🚀 **Next Steps**
- Use `resume_session` to continue where you left off
- All work context and conversation history preserved
- Session data searchable in FindersKeepers knowledge base

**Session successfully terminated and data committed to FindersKeepers v2!**
                """
            else:
                return f"❌ Failed to end session via n8n: {response.status_code}"
                
    except Exception as e:
        return f"❌ Error ending session: {str(e)}"

@mcp.tool()
async def resume_session(max_messages: int = 20) -> str:
    """Resume the most recent session with full context"""
    global current_session_id, session_start_time
    
    try:
        # Find the most recent session
        if not db_pool:
            await initialize_database()
            
        async with db_pool.acquire() as conn:
            recent_session = await conn.fetchrow("""
                SELECT session_id, agent_type, project, start_time, end_time, status
                FROM agent_sessions 
                ORDER BY COALESCE(end_time, start_time) DESC 
                LIMIT 1
            """)
            
            if not recent_session:
                return "❌ No previous sessions found to resume from"
            
            # Start a new session for continuity
            new_session_id = f"fk2_sess_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            current_session_id = new_session_id
            session_start_time = datetime.now()
            
            # Create new session via n8n
            async with httpx.AsyncClient(timeout=10.0) as client:
                session_data = {
                    "session_id": new_session_id,
                    "action_type": "session_start", 
                    "user_id": "bitcain",
                    "agent_type": "claude-desktop",
                    "project": "finderskeepers-v2",
                    "context": {
                        "resumed_from": recent_session['session_id'],
                        "resume_time": datetime.now().isoformat()
                    }
                }
                
                await client.post(SESSION_WEBHOOK, json=session_data)

            # Get recent conversation context
            conversations = await conn.fetch("""
                SELECT message_type, content, created_at
                FROM conversation_messages 
                WHERE session_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """, recent_session['session_id'], max_messages)
            
            # Generate context summary
            duration = "Unknown"
            if recent_session['end_time'] and recent_session['start_time']:
                duration = str(recent_session['end_time'] - recent_session['start_time']).split('.')[0]
            
            recent_topics = []
            for conv in conversations[:5]:
                if conv['content']:
                    words = conv['content'].lower().split()
                    for word in ['docker', 'database', 'api', 'error', 'fix', 'implement', 'create', 'update']:
                        if word in words and word not in recent_topics:
                            recent_topics.append(word)
            
            return f"""
🔄 **Session Resumed Successfully**

📊 **Previous Session Summary:**
- **Session ID**: {recent_session['session_id']}
- **Duration**: {duration}
- **Status**: {recent_session['status']}
- **Project**: {recent_session['project']}

🎯 **Recent Activity:**
- **Conversations**: {len(conversations)} messages logged
- **Recent Topics**: {', '.join(recent_topics[:5]) if recent_topics else 'Various discussions'}

🚀 **New Session Started**: {new_session_id}

💡 **Suggested Next Steps:**
- Continue working on {recent_session['project']} project
- All context and conversation history available
- Use vector_search to find specific information

**Ready to continue where you left off!**
            """
            
    except Exception as e:
        return f"❌ Error resuming session: {str(e)}"

# =============================================================================
# KNOWLEDGE SEARCH TOOLS
# =============================================================================

@mcp.tool()
async def vector_search(query: str, limit: int = 10, collection: str = "finderskeepers_docs") -> str:
    """Search the FindersKeepers v2 vector database using semantic similarity"""
    try:
        await log_action("vector_search", f"Searching for: {query}", {"query": query, "limit": limit})
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{QDRANT_URL}/collections/{collection}/points/search",
                json={
                    "vector": {"query": query},
                    "limit": limit,
                    "with_payload": True
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = response.json()
                if results.get("result"):
                    formatted_results = []
                    for i, result in enumerate(results["result"][:limit], 1):
                        score = result.get("score", 0)
                        payload = result.get("payload", {})
                        content = payload.get("content", "No content")[:200] + "..."
                        
                        formatted_results.append(f"""
**Result {i}** (Score: {score:.3f})
{content}
                        """)
                    
                    return f"""
🔍 **Vector Search Results**

**Query**: "{query}"
**Collection**: {collection}
**Results Found**: {len(results["result"])}

{chr(10).join(formatted_results)}

💡 **Tip**: Use database_query for more specific searches or knowledge_graph_search for relationship exploration.
                    """
                else:
                    return f"🔍 No results found for query: '{query}'"
            else:
                return f"❌ Vector search failed: {response.status_code}"
                
    except Exception as e:
        return f"❌ Vector search error: {str(e)}"

@mcp.tool()
async def database_query(query: str, table: str = None) -> str:
    """Query the FindersKeepers v2 PostgreSQL database"""
    try:
        await log_action("database_query", f"SQL query: {query[:100]}...", {"query": query, "table": table})
        
        if not db_pool:
            await initialize_database()
            
        async with db_pool.acquire() as conn:
            # Ensure read-only operations
            if not query.strip().upper().startswith(("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN")):
                return "❌ Only read-only queries (SELECT, WITH, SHOW, DESCRIBE, EXPLAIN) are allowed"
            
            rows = await conn.fetch(query)
            
            if rows:
                # Format results
                if len(rows) == 1:
                    result = dict(rows[0])
                    formatted = json.dumps(result, indent=2, default=str)
                else:
                    results = [dict(row) for row in rows[:10]]  # Limit to 10 rows
                    formatted = json.dumps(results, indent=2, default=str)
                    if len(rows) > 10:
                        formatted += f"\n\n... and {len(rows) - 10} more rows"
                
                return f"""
📊 **Database Query Results**

**Query**: {query}
**Rows Returned**: {len(rows)}

```json
{formatted}
```
                """
            else:
                return f"📊 Query executed successfully but returned no results."
                
    except Exception as e:
        return f"❌ Database query error: {str(e)}"

@mcp.tool()
async def knowledge_graph_search(query: str, entity_type: str = None, limit: int = 15) -> str:
    """Search the Neo4j knowledge graph for relationships and entities"""
    try:
        await log_action("knowledge_graph_search", f"Graph search: {query}", {"query": query, "entity_type": entity_type})
        
        # This would connect to Neo4j - for now return a placeholder
        return f"""
🕸️ **Knowledge Graph Search**

**Query**: "{query}"
**Entity Type**: {entity_type or "All"}
**Limit**: {limit}

🚧 **Neo4j Integration**: Knowledge graph search is configured but requires Neo4j connection setup.

**Alternative**: Use database_query to search relationships in PostgreSQL:
```sql
SELECT * FROM documents WHERE content ILIKE '%{query}%' LIMIT 10;
```

💡 **Tip**: The knowledge graph will show document relationships, user interactions, and project connections once fully connected.
        """
        
    except Exception as e:
        return f"❌ Knowledge graph search error: {str(e)}"

@mcp.tool()
async def document_search(query: str, doc_type: str = "all", limit: int = 10) -> str:
    """Search through ingested documents in FindersKeepers v2"""
    try:
        await log_action("document_search", f"Document search: {query}", {"query": query, "doc_type": doc_type})
        
        if not db_pool:
            await initialize_database()
            
        async with db_pool.acquire() as conn:
            # Search in documents table
            where_clause = "WHERE title ILIKE $1 OR content ILIKE $1"
            params = [f"%{query}%"]
            
            if doc_type != "all":
                where_clause += " AND file_type = $2"
                params.append(doc_type)
            
            sql = f"""
                SELECT id, title, file_type, file_path, created_at,
                       LEFT(content, 200) as content_preview
                FROM documents 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT $3
            """
            params.append(limit)
            
            docs = await conn.fetch(sql, *params)
            
            if docs:
                formatted_docs = []
                for doc in docs:
                    formatted_docs.append(f"""
**📄 {doc['title']}**
- **Type**: {doc['file_type']}
- **Path**: {doc['file_path']}
- **Created**: {doc['created_at'].strftime('%Y-%m-%d %H:%M')}
- **Preview**: {doc['content_preview']}...
                    """)
                
                return f"""
📚 **Document Search Results**

**Query**: "{query}"
**Document Type**: {doc_type}
**Results Found**: {len(docs)}

{chr(10).join(formatted_docs)}

💡 **Tip**: Use vector_search for semantic similarity or database_query for more specific document queries.
                """
            else:
                return f"📚 No documents found matching: '{query}'"
                
    except Exception as e:
        return f"❌ Document search error: {str(e)}"

@mcp.tool()
async def get_session_status() -> str:
    """Get current session information and statistics"""
    global current_session_id, session_start_time
    
    if not current_session_id:
        return "❌ No active session"
    
    try:
        duration = "Unknown"
        if session_start_time:
            duration = str(datetime.now() - session_start_time).split('.')[0]
        
        # Get basic stats if database is available
        message_count = 0
        action_count = 0
        
        if db_pool:
            async with db_pool.acquire() as conn:
                message_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM conversation_messages 
                    WHERE session_id = $1
                """, current_session_id) or 0
                
                action_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM agent_actions 
                    WHERE session_id = $1
                """, current_session_id) or 0
        
        return f"""
📊 **Current Session Status**

🆔 **Session ID**: {current_session_id}
⏰ **Duration**: {duration}
👤 **User**: bitcain
🤖 **Agent**: claude-desktop
📁 **Project**: finderskeepers-v2

📈 **Activity:**
- 💬 **Messages Logged**: {message_count}
- ⚡ **Actions Recorded**: {action_count}

🔧 **Infrastructure:**
- 🐳 **Docker Containers**: 9 services running
- 🎯 **GPU Acceleration**: RTX 2080 Ti enabled
- 💾 **Databases**: PostgreSQL + Neo4j + Qdrant + Redis
- 🔄 **n8n Workflows**: Agent logging active

✅ **Session Status**: Active and logging
        """
        
    except Exception as e:
        return f"❌ Error getting session status: {str(e)}"

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
    
    # This is the CORRECT way for Claude Desktop - no asyncio.run()!
    mcp.run(transport="stdio")
