#!/usr/bin/env python3
"""
FindersKeepers v2 MCP Knowledge Server
Provides agents with natural language access to the knowledge base

This server exposes tools, resources, and prompts that allow AI agents to:
- Search documents using semantic similarity
- Query the knowledge graph for relationships
- Retrieve agent session context and history
- Analyze document similarity and connections
"""

import asyncio
import logging
import os
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool, Prompt

from database.postgres_client import PostgresClient
from database.neo4j_client import Neo4jClient  
from database.qdrant_client import QdrantClient
from database.redis_client import RedisClient
from activity_logger import activity_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("FindersKeepers Knowledge Server")

# Database clients
postgres = PostgresClient()
neo4j = Neo4jClient()
qdrant = QdrantClient()
redis = RedisClient()

# ========================================
# TOOLS - Agent-callable functions
# ========================================

@mcp.tool()
async def search_documents(
    query: str,
    project: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10,
    min_score: float = 0.5
) -> Dict[str, Any]:
    """
    Search documents using semantic search across all knowledge sources.
    
    Args:
        query: Natural language search query
        project: Filter by project name (optional)
        tags: Filter by document tags (optional)
        limit: Maximum number of results (default: 10)
        min_score: Minimum similarity score 0.0-1.0 (default: 0.5)
    
    Returns:
        Dictionary with search results, metadata, and search statistics
    """
    try:
        logger.info(f"🔍 Searching documents: '{query}' (project: {project}, tags: {tags})")
        
        # Generate embeddings for the query using FastAPI backend
        embeddings = await qdrant.generate_embeddings(query)
        
        if not embeddings:
            return {
                "error": "Failed to generate embeddings for query",
                "query": query,
                "results": []
            }
        
        # Search in Qdrant vector database
        vector_results = await qdrant.search(
            embeddings=embeddings,
            project=project,
            tags=tags,
            limit=limit,
            min_score=min_score
        )
        
        # Enhance results with PostgreSQL metadata
        enhanced_results = []
        for result in vector_results:
            doc_metadata = await postgres.get_document_metadata(result["document_id"])
            enhanced_results.append({
                "content": result["content"],
                "score": result["score"],
                "document_id": result["document_id"],
                "chunk_id": result["chunk_id"],
                "metadata": doc_metadata,
                "preview": result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
            })
        
        result = {
            "query": query,
            "total_results": len(enhanced_results),
            "results": enhanced_results,
            "search_params": {
                "project": project, 
                "tags": tags,
                "limit": limit,
                "min_score": min_score
            },
            "embeddings_used": len(embeddings) > 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log successful search to n8n
        await activity_logger.log_tool_call(
            tool_name="search_documents",
            arguments={"query": query, "project": project, "tags": tags, "limit": limit},
            result=result
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        await activity_logger.log_error("search_documents", e)
        return {
            "error": str(e),
            "query": query,
            "results": [],
            "timestamp": datetime.utcnow().isoformat()
        }

@mcp.tool()
async def query_knowledge_graph(
    question: str,
    entity_types: Optional[List[str]] = None,
    max_depth: int = 2,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Query the Neo4j knowledge graph for entity relationships and context.
    
    Args:
        question: Natural language question about relationships
        entity_types: Types of entities to focus on (optional)
        max_depth: Maximum traversal depth in graph (default: 2)
        limit: Maximum number of results (default: 20)
    
    Returns:
        Graph query results with entities, relationships, and insights
    """
    try:
        logger.info(f"🧠 Querying knowledge graph: '{question}'")
        
        # Extract keywords from the question for entity matching
        keywords = await neo4j.extract_keywords(question)
        
        # Build and execute Cypher query
        graph_results = await neo4j.query_entities_and_relationships(
            keywords=keywords,
            entity_types=entity_types,
            max_depth=max_depth,
            limit=limit
        )
        
        result = {
            "question": question,
            "keywords_extracted": keywords,
            "graph_results": graph_results,
            "query_params": {
                "entity_types": entity_types,
                "max_depth": max_depth,
                "limit": limit
            },
            "entities_found": len(graph_results.get("entities", [])),
            "relationships_found": len(graph_results.get("relationships", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log knowledge graph query
        await activity_logger.log_tool_call(
            tool_name="query_knowledge_graph",
            arguments={"question": question, "entity_types": entity_types},
            result=result
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Knowledge graph query failed: {e}")
        return {
            "error": str(e),
            "question": question,
            "graph_results": {},
            "timestamp": datetime.utcnow().isoformat()
        }

@mcp.tool()
async def get_full_conversation_context(
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    project: Optional[str] = None,
    recent_actions: int = 10,
    include_files: bool = True,
    include_conversation_history: bool = True,
    conversation_limit: int = 50
) -> Dict[str, Any]:
    """
    Retrieve complete session context including conversation history from the knowledge base.
    
    Args:
        session_id: Specific session to retrieve (optional)
        agent_type: Filter by agent type like 'claude', 'gpt' (optional)
        project: Filter by project context (optional)
        recent_actions: Number of recent actions to include (default: 10)
        include_files: Whether to include file change information (default: True)
        include_conversation_history: Whether to include full conversation messages (default: True)
        conversation_limit: Maximum conversation messages to retrieve (default: 50)
    
    Returns:
        Complete session context with actions, conversation history, metadata, and file changes
    """
    try:
        logger.info(f"📋 Getting session context: {session_id or 'recent sessions'}")
        
        if session_id:
            # Get specific session
            session = await postgres.get_session(session_id)
            actions = await postgres.get_session_actions(session_id, limit=recent_actions)
        else:
            # Get recent sessions based on filters
            sessions = await postgres.get_recent_sessions(
                agent_type=agent_type,
                project=project,
                limit=3
            )
            session = sessions[0] if sessions else None
            actions = await postgres.get_recent_actions(
                agent_type=agent_type,
                project=project,
                limit=recent_actions
            )
        
        # Get file changes if requested
        file_changes = []
        if include_files and actions:
            file_changes = await postgres.get_files_affected_by_actions(
                [action["action_id"] for action in actions]
            )
        
        # Get conversation history if requested
        conversation_messages = []
        conversation_summary = {}
        if include_conversation_history and actions:
            # Filter actions to get conversation messages
            conversation_actions = [
                action for action in actions 
                if action.get("action_type", "").startswith("conversation:")
            ]
            
            # Process conversation messages with full context
            for conv_action in conversation_actions[:conversation_limit]:
                details = conv_action.get("details", {})
                conversation_messages.append({
                    "message_id": conv_action.get("action_id"),
                    "timestamp": conv_action.get("timestamp"),
                    "message_type": details.get("message_type"),
                    "content": details.get("full_content", ""),
                    "content_length": details.get("content_length", 0),
                    "emotional_indicators": details.get("emotional_indicators", []),
                    "topic_keywords": details.get("topic_keywords", []),
                    "tools_used": details.get("tools_used", []),
                    "files_referenced": details.get("files_referenced", []),
                    "reasoning": details.get("reasoning"),
                    "context": details.get("context", {})
                })
            
            # Generate conversation summary
            user_messages = [m for m in conversation_messages if m["message_type"] == "user_message"]
            ai_responses = [m for m in conversation_messages if m["message_type"] == "ai_response"]
            
            conversation_summary = {
                "total_messages": len(conversation_messages),
                "user_messages": len(user_messages),
                "ai_responses": len(ai_responses),
                "dominant_emotions": get_dominant_emotions(conversation_messages),
                "key_topics": get_key_topics(conversation_messages),
                "conversation_flow": analyze_conversation_flow(conversation_messages),
                "last_user_message": user_messages[0]["content"][:200] if user_messages else None,
                "last_ai_response": ai_responses[0]["content"][:200] if ai_responses else None
            }
        
        return {
            "session": session,
            "actions": actions,
            "file_changes": file_changes if include_files else [],
            "conversation_history": conversation_messages if include_conversation_history else [],
            "conversation_summary": conversation_summary if include_conversation_history else {},
            "summary": {
                "session_id": session["session_id"] if session else None,
                "agent_type": session["agent_type"] if session else None,
                "project": session["project"] if session else None,
                "action_count": len(actions),
                "files_affected": len(file_changes) if include_files else 0,
                "success_rate": sum(1 for a in actions if a.get("success", True)) / len(actions) if actions else 0
            },
            "filters": {
                "session_id": session_id,
                "agent_type": agent_type,
                "project": project
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session context retrieval failed: {e}")
        return {
            "error": str(e),
            "session": None,
            "actions": [],
            "timestamp": datetime.utcnow().isoformat()
        }

@mcp.tool()
async def analyze_document_similarity(
    document_id: str,
    similarity_threshold: float = 0.7,
    limit: int = 8,
    include_content: bool = False
) -> Dict[str, Any]:
    """
    Find documents similar to a given document using vector similarity.
    
    Args:
        document_id: ID of the reference document
        similarity_threshold: Minimum similarity score 0.0-1.0 (default: 0.7)
        limit: Maximum number of similar documents (default: 8)
        include_content: Whether to include full content in results (default: False)
    
    Returns:
        List of similar documents with similarity scores and metadata
    """
    try:
        logger.info(f"🔗 Analyzing similarity for document: {document_id}")
        
        # Get document embeddings from Qdrant
        doc_embeddings = await qdrant.get_document_embeddings(document_id)
        
        if not doc_embeddings:
            return {
                "error": "Document not found or no embeddings available",
                "document_id": document_id,
                "similar_documents": []
            }
        
        # Find similar documents
        similar_docs = await qdrant.find_similar_documents(
            embeddings=doc_embeddings,
            threshold=similarity_threshold,
            limit=limit,
            exclude_document_id=document_id
        )
        
        # Enhance with metadata from PostgreSQL
        enhanced_results = []
        for doc in similar_docs:
            metadata = await postgres.get_document_metadata(doc["document_id"])
            result = {
                "document_id": doc["document_id"],
                "similarity_score": doc["score"],
                "metadata": metadata,
                "preview": doc["content"][:150] + "..." if not include_content and len(doc["content"]) > 150 else None
            }
            
            if include_content:
                result["content"] = doc["content"]
                
            enhanced_results.append(result)
        
        # Get reference document metadata
        reference_doc = await postgres.get_document_metadata(document_id)
        
        return {
            "reference_document": {
                "document_id": document_id,
                "metadata": reference_doc
            },
            "similarity_threshold": similarity_threshold,
            "similar_documents": enhanced_results,
            "analysis": {
                "total_found": len(enhanced_results),
                "avg_similarity": sum(d["similarity_score"] for d in enhanced_results) / len(enhanced_results) if enhanced_results else 0,
                "highest_similarity": max((d["similarity_score"] for d in enhanced_results), default=0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document similarity analysis failed: {e}")
        return {
            "error": str(e),
            "document_id": document_id,
            "similar_documents": [],
            "timestamp": datetime.utcnow().isoformat()
        }

@mcp.tool()
async def initialize_claude_session(
    user_id: str = "local_user",
    project: str = "finderskeepers-v2",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Initialize a new Claude Code session with automatic logging and context retrieval.
    
    Args:
        user_id: User identifier (default: local_user)
        project: Project context (default: finderskeepers-v2)
        context: Additional session context (optional)
    
    Returns:
        Session information with current project status and recent activity summary
    """
    try:
        logger.info(f"🚀 Initializing Claude Code session for project: {project}")
        
        # Create session data for Claude Code
        session_context = {
            "client": "claude_code",
            "version": "latest",
            "started_at": datetime.utcnow().isoformat(),
            "connection_type": "mcp_tool_call",
            "auto_logging_enabled": True,
            "purpose": "Interactive development session",
            **(context or {})
        }
        
        session_data = {
            "agent_type": "claude-code",
            "user_id": user_id,
            "project": project,
            "context": session_context
        }
        
        # Call n8n Agent Session Logger webhook to create session
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{activity_logger.n8n_webhook_url}/webhook/agent-logger",
                json=session_data,
                timeout=10.0
            )
            
            session_id = None
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    session_response = result[0]
                    session_id = session_response.get("session_id")
            
            if not session_id:
                session_id = f"claude_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                
        # Get current project context and recent activity with FULL conversation history
        context_data = await get_full_conversation_context(
            project=project,
            recent_actions=20,
            include_files=True,
            include_conversation_history=True,
            conversation_limit=30
        )
        
        # Get project overview
        project_overview = await get_project_overview(
            project=project,
            include_recent_activity=True,
            activity_days=7
        )
        
        # Log the session initialization
        await activity_logger.log_action(
            action_type="claude_session_init",
            description=f"Claude Code session initialized for project {project}",
            details={
                "session_id": session_id,
                "project": project,
                "user_id": user_id,
                "initialization_method": "mcp_tool",
                "context_retrieved": True,
                "recent_sessions_found": len(context_data.get("actions", [])),
                "project_activity_level": project_overview.get("overview", {}).get("activity_level", "unknown")
            },
            success=True
        )
        
        return {
            "session_id": session_id,
            "status": "initialized",
            "project": project,
            "current_context": context_data,
            "project_overview": project_overview,
            "recommendations": generate_continuation_recommendations(context_data, project_overview),
            "message": f"✅ Claude Code session initialized! You have context from {len(context_data.get('actions', []))} recent actions.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Claude session initialization failed: {e}")
        await activity_logger.log_error("claude_session_init", e)
        return {
            "error": str(e),
            "status": "failed",
            "project": project,
            "timestamp": datetime.utcnow().isoformat()
        }

def generate_continuation_recommendations(context_data: Dict[str, Any], project_overview: Dict[str, Any]) -> List[str]:
    """Generate intelligent recommendations for continuing work based on recent activity"""
    recommendations = []
    
    # Analyze recent actions
    recent_actions = context_data.get("actions", [])
    if recent_actions:
        latest_action = recent_actions[0]
        action_type = latest_action.get("action_type", "")
        
        if "file_edit" in action_type or "fix" in action_type.lower():
            recommendations.append("🔧 Continue fixing issues or implementing changes from the last session")
        
        if "commit" in action_type.lower():
            recommendations.append("🚀 Consider pushing changes or starting new features")
            
        if "error" in action_type.lower() or not latest_action.get("success", True):
            recommendations.append("⚠️ Address the error from the previous session")
    
    # Analyze file changes
    file_changes = context_data.get("file_changes", [])
    if file_changes:
        recommendations.append(f"📄 Review changes to {len(file_changes)} files from recent sessions")
    
    # Analyze project activity level
    activity_level = project_overview.get("overview", {}).get("activity_level", "")
    if activity_level == "high":
        recommendations.append("🔥 High activity detected - review recent progress before continuing")
    elif activity_level == "low":
        recommendations.append("🌱 Low recent activity - good time to start new features or major changes")
    
    # Default recommendation
    if not recommendations:
        recommendations.append("🎯 Check project status and plan next development steps")
        
    return recommendations[:3]  # Limit to top 3 recommendations

@mcp.tool()
async def log_conversation_message(
    session_id: str,
    message_type: str,  # "user_message" or "ai_response"
    content: str,
    context: Optional[Dict[str, Any]] = None,
    reasoning: Optional[str] = None,
    tools_used: Optional[List[str]] = None,
    files_referenced: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Log detailed conversation messages for complete context preservation.
    
    Args:
        session_id: Session ID from initialize_claude_session
        message_type: "user_message", "ai_response", "system_message", "tool_result"
        content: Full message content
        context: Additional context (emotional tone, urgency, topic changes)
        reasoning: AI reasoning process and decision-making (for AI responses)
        tools_used: List of tools used in this interaction
        files_referenced: Files mentioned or referenced in the message
    
    Returns:
        Message logging confirmation with message_id
    """
    try:
        logger.info(f"💬 Logging conversation message: {message_type} for session {session_id}")
        
        message_data = {
            "session_id": session_id,
            "action_type": f"conversation:{message_type}",
            "description": f"Conversation {message_type}: {content[:100]}..." if len(content) > 100 else content,
            "details": {
                "message_type": message_type,
                "full_content": content,
                "content_length": len(content),
                "context": context or {},
                "reasoning": reasoning,
                "tools_used": tools_used or [],
                "files_referenced": files_referenced or [],
                "emotional_indicators": extract_emotional_context(content),
                "topic_keywords": extract_topic_keywords(content),
                "conversation_flow": "continuation" if message_type == "user_message" else "response"
            },
            "files_affected": files_referenced or [],
            "success": True
        }
        
        # Call n8n Agent Action Tracker webhook for conversation logging
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{activity_logger.n8n_webhook_url}/webhook/agent-actions",
                json=message_data,
                timeout=10.0
            )
            
            message_id = None
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    message_response = result[0]
                    message_id = message_response.get("action_id")
            
            if not message_id:
                message_id = f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        return {
            "message_id": message_id,
            "session_id": session_id,
            "status": "logged",
            "message_type": message_type,
            "content_length": len(content),
            "message": f"✅ Conversation {message_type} logged successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Conversation logging failed: {e}")
        return {
            "error": str(e),
            "status": "failed",
            "session_id": session_id,
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat()
        }

def extract_emotional_context(content: str) -> List[str]:
    """Extract emotional indicators from message content"""
    emotional_indicators = []
    content_lower = content.lower()
    
    if any(word in content_lower for word in ["!!", "excited", "amazing", "awesome", "love"]):
        emotional_indicators.append("high_enthusiasm")
    if any(word in content_lower for word in ["frustrated", "annoying", "hate", "terrible"]):
        emotional_indicators.append("frustration")
    if "?" in content and any(word in content_lower for word in ["how", "what", "why", "when", "where"]):
        emotional_indicators.append("inquiry")
    if any(word in content_lower for word in ["god", "ultimate", "all-knowing", "perfect"]):
        emotional_indicators.append("aspiration")
    if "MAJOR" in content or content.isupper():
        emotional_indicators.append("emphasis")
        
    return emotional_indicators

def extract_topic_keywords(content: str) -> List[str]:
    """Extract key topics and concepts from message content"""
    import re
    
    # Technical keywords
    tech_keywords = re.findall(r'\b(?:docker|gpu|cuda|mcp|session|logging|database|ai|llm|ollama|fastapi|neo4j|qdrant)\b', content.lower())
    
    # Action keywords  
    action_keywords = re.findall(r'\b(?:implement|fix|create|add|update|configure|test|deploy|commit|push)\b', content.lower())
    
    # Concept keywords
    concept_keywords = re.findall(r'\b(?:conversation|context|memory|knowledge|intelligence|automation|integration)\b', content.lower())
    
    return list(set(tech_keywords + action_keywords + concept_keywords))

def get_dominant_emotions(conversation_messages: List[Dict[str, Any]]) -> List[str]:
    """Analyze dominant emotional patterns in conversation"""
    emotion_counts = {}
    for message in conversation_messages:
        for emotion in message.get("emotional_indicators", []):
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    # Return top 3 emotions
    sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
    return [emotion for emotion, count in sorted_emotions[:3]]

def get_key_topics(conversation_messages: List[Dict[str, Any]]) -> List[str]:
    """Extract key topics discussed in conversation"""
    topic_counts = {}
    for message in conversation_messages:
        for topic in message.get("topic_keywords", []):
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Return top 5 topics
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, count in sorted_topics[:5]]

def analyze_conversation_flow(conversation_messages: List[Dict[str, Any]]) -> str:
    """Analyze the flow and pattern of the conversation"""
    if not conversation_messages:
        return "no_conversation"
    
    user_msg_count = len([m for m in conversation_messages if m["message_type"] == "user_message"])
    ai_msg_count = len([m for m in conversation_messages if m["message_type"] == "ai_response"])
    
    if user_msg_count > ai_msg_count:
        return "user_driven"
    elif ai_msg_count > user_msg_count:
        return "ai_driven"
    else:
        return "balanced_dialogue"

@mcp.tool()
async def log_claude_action(
    session_id: str,
    action_type: str,
    description: str,
    files_affected: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a Claude Code action for automatic session tracking.
    
    Args:
        session_id: Session ID from initialize_claude_session
        action_type: Type of action (file_edit, command, config_change, etc.)
        description: Human-readable description of the action
        files_affected: List of files modified (optional)
        details: Action-specific details (optional)
        success: Whether action completed successfully (default: True)
        error_message: Error message if action failed (optional)
    
    Returns:
        Action logging confirmation with action_id
    """
    try:
        logger.info(f"📝 Logging Claude action: {action_type} for session {session_id}")
        
        action_data = {
            "session_id": session_id,
            "action_type": action_type,
            "description": description,
            "details": details or {},
            "files_affected": files_affected or [],
            "success": success
        }
        
        if error_message:
            action_data["details"]["error_message"] = error_message
        
        # Call n8n Agent Action Tracker webhook
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{activity_logger.n8n_webhook_url}/webhook/agent-actions",
                json=action_data,
                timeout=10.0
            )
            
            action_id = None
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    action_response = result[0]
                    action_id = action_response.get("action_id")
            
            if not action_id:
                action_id = f"action_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        return {
            "action_id": action_id,
            "session_id": session_id,
            "status": "logged",
            "action_type": action_type,
            "success": success,
            "message": f"✅ Action '{action_type}' logged successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Claude action logging failed: {e}")
        return {
            "error": str(e),
            "status": "failed",
            "session_id": session_id,
            "action_type": action_type,
            "timestamp": datetime.utcnow().isoformat()
        }

@mcp.tool()
async def get_project_overview(
    project: str,
    include_recent_activity: bool = True,
    activity_days: int = 7
) -> Dict[str, Any]:
    """
    Get comprehensive overview of a project including documents, sessions, and activity.
    
    Args:
        project: Project name to analyze
        include_recent_activity: Whether to include recent session activity (default: True)
        activity_days: Number of days for recent activity (default: 7)
    
    Returns:
        Complete project overview with statistics and recent activity
    """
    try:
        logger.info(f"📊 Getting project overview: {project}")
        
        # Get project statistics
        project_stats = await postgres.get_project_statistics(project)
        
        # Get recent documents
        recent_docs = await postgres.get_recent_documents(project, limit=10)
        
        # Get recent activity if requested
        recent_activity = []
        if include_recent_activity:
            recent_activity = await postgres.get_recent_project_activity(
                project, 
                days=activity_days,
                limit=20
            )
        
        # Get knowledge graph entities for this project
        project_entities = await neo4j.get_project_entities(project, limit=15)
        
        return {
            "project": project,
            "statistics": project_stats,
            "recent_documents": recent_docs,
            "recent_activity": recent_activity if include_recent_activity else [],
            "knowledge_entities": project_entities,
            "overview": {
                "total_documents": project_stats.get("total_documents", 0),
                "total_sessions": project_stats.get("total_sessions", 0),
                "total_actions": project_stats.get("total_actions", 0),
                "activity_level": "high" if len(recent_activity) > 10 else "medium" if len(recent_activity) > 5 else "low"
            },
            "analysis_period": f"Last {activity_days} days",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Project overview failed: {e}")
        return {
            "error": str(e),
            "project": project,
            "statistics": {},
            "timestamp": datetime.utcnow().isoformat()
        }

# ========================================
# RESOURCES - Readable data sources
# ========================================

@mcp.resource("schema://database")
async def get_database_schema() -> str:
    """Provide the PostgreSQL database schema as a resource"""
    try:
        # Log resource access
        await activity_logger.log_resource_access("schema://database")
        
        schema_info = await postgres.get_detailed_schema()
        
        return f"""# FindersKeepers v2 Database Schema

## Core Tables

### Agent Session Tracking
- **agent_sessions**: Session metadata, context, timing
- **agent_actions**: Individual actions within sessions
- **config_changes**: Configuration change tracking

### Document Management  
- **documents**: Document metadata, project association
- **document_chunks**: Text chunks for vector search
- **knowledge_entities**: Graph entity references

## Vector & Graph Storage
- **Qdrant**: Vector embeddings for semantic search
- **Neo4j**: Knowledge graph with entities and relationships
- **Redis**: Session caching and real-time data

## Schema Details
{json.dumps(schema_info, indent=2)}

*Generated at: {datetime.utcnow().isoformat()}*
"""
    except Exception as e:
        return f"Error retrieving schema: {e}"

@mcp.resource("stats://knowledge-base")
async def get_knowledge_stats() -> str:
    """Provide comprehensive knowledge base statistics and health metrics"""
    try:
        # Log resource access
        await activity_logger.log_resource_access("stats://knowledge-base")
        
        # Get stats from all data sources
        postgres_stats = await postgres.get_comprehensive_stats()
        neo4j_stats = await neo4j.get_graph_stats()
        qdrant_stats = await qdrant.get_collection_stats()
        
        return f"""# FindersKeepers v2 Knowledge Base Statistics

## Document Storage (PostgreSQL)
- 📄 **Total Documents**: {postgres_stats.get('total_documents', 0):,}
- 🧩 **Total Chunks**: {postgres_stats.get('total_chunks', 0):,}
- 📊 **Total Sessions**: {postgres_stats.get('total_sessions', 0):,}
- ⚡ **Total Actions**: {postgres_stats.get('total_actions', 0):,}
- 📁 **Active Projects**: {postgres_stats.get('active_projects', 0)}

## Knowledge Graph (Neo4j)
- 🔗 **Total Nodes**: {neo4j_stats.get('total_nodes', 0):,}
- 🌐 **Total Relationships**: {neo4j_stats.get('total_relationships', 0):,}
- 🏷️ **Node Types**: {', '.join(neo4j_stats.get('node_types', []))}
- 📈 **Graph Density**: {neo4j_stats.get('density', 0):.3f}

## Vector Search (Qdrant)
- 🗂️ **Collections**: {len(qdrant_stats.get('collections', []))}
- 🔢 **Total Vectors**: {qdrant_stats.get('total_vectors', 0):,}
- 📐 **Vector Dimensions**: {qdrant_stats.get('vector_size', 0)}
- 💾 **Index Type**: {qdrant_stats.get('index_type', 'HNSW')}

## Performance Metrics
- 🚀 **Avg Query Time**: {postgres_stats.get('avg_query_time', 0):.2f}ms
- 📊 **Vector Search Speed**: {qdrant_stats.get('search_speed', 0)} queries/sec
- 🧠 **Graph Traversal**: {neo4j_stats.get('traversal_speed', 0)} nodes/sec

## Health Status
- ✅ **PostgreSQL**: {'Healthy' if postgres_stats.get('healthy', False) else 'Issues'}
- ✅ **Neo4j**: {'Healthy' if neo4j_stats.get('healthy', False) else 'Issues'}  
- ✅ **Qdrant**: {'Healthy' if qdrant_stats.get('healthy', False) else 'Issues'}

*Last Updated: {datetime.utcnow().isoformat()}*
*Knowledge Server Version: 2.0.0*
"""
    except Exception as e:
        return f"Error retrieving knowledge stats: {e}"

@mcp.resource("guide://knowledge-search")
async def get_search_guide() -> str:
    """Provide a comprehensive guide for effective knowledge searching"""
    # Log resource access
    await activity_logger.log_resource_access("guide://knowledge-search")
    
    return """# FindersKeepers v2 Knowledge Search Guide

## Effective Search Strategies

### 1. Semantic Search
Use **natural language** to find conceptually related content:
- ❓ "How to configure Docker with GPU support"
- ❓ "FastAPI authentication patterns"
- ❓ "Database migration procedures"

### 2. Project-Specific Search
Filter by project context for focused results:
- 🎯 project="bitcain" → BitCoin-related documents only
- 🎯 project="skellekey" → SkelleKey project documentation
- 🎯 project="finderskeepers" → This project's documentation

### 3. Tag-Based Filtering
Use tags to narrow down document types:
- 🏷️ tags=["configuration"] → Setup and config docs
- 🏷️ tags=["troubleshooting"] → Problem-solving guides
- 🏷️ tags=["architecture"] → System design documents

### 4. Knowledge Graph Queries
Explore relationships and connections:
- 🧠 "What entities are connected to user authentication?"
- 🧠 "Show relationships between Docker and GPU configuration"
- 🧠 "Find all procedures linked to database migrations"

### 5. Session Context Analysis
Understand agent activity and history:
- 📋 Recent sessions by agent type or project
- 📋 File changes and modifications tracking
- 📋 Success patterns and common issues

## Search Quality Tips

### Improve Results
- ✅ Use **specific technical terms** when searching for code
- ✅ Include **context** like "FastAPI" + "authentication" 
- ✅ Try **variations** of your query if results aren't helpful
- ✅ Use **filters** to narrow scope (project, tags, date ranges)

### Common Patterns
- 🔍 **"How to..."** → Procedural documentation
- 🔍 **"Error: [message]"** → Troubleshooting guides
- 🔍 **"[Technology] + [Feature]"** → Implementation examples
- 🔍 **"Configuration + [Service]"** → Setup documentation

### Advanced Techniques
- 🎯 **Similarity Analysis**: Find documents similar to one you know is relevant
- 🎯 **Project Overview**: Get comprehensive project status and activity
- 🎯 **Cross-Reference**: Use knowledge graph to find unexpected connections

## Example Queries

### Document Search Examples
```
search_documents(
  query="Docker GPU configuration with RTX 2080 Ti",
  project="finderskeepers",
  limit=5,
  min_score=0.6
)
```

### Knowledge Graph Examples  
```
query_knowledge_graph(
  question="What are the relationships between FastAPI and database connections?",
  max_depth=2,
  limit=15
)
```

### Session Analysis Examples
```
get_session_context(
  agent_type="claude",
  project="finderskeepers", 
  recent_actions=10,
  include_files=true
)
```

**Remember**: The knowledge base grows with every document you ingest, so search strategies that don't work today might work perfectly tomorrow!
"""

# ========================================
# PROMPTS - Guided interactions
# ========================================

@mcp.prompt()
async def knowledge_search_prompt() -> Prompt:
    """Provide a guided prompt template for knowledge searching"""
    return Prompt(
        name="knowledge_search",
        description="Guided knowledge base search with intelligent context",
        messages=[
            {
                "role": "user", 
                "content": """I need to search the FindersKeepers v2 knowledge base intelligently. Please help me find the most relevant information.

## What I'm Looking For:
**Search Query**: {query}

## Context Filters:
- **Project Focus**: {project}
- **Document Types**: {doc_types}
- **Time Period**: {time_period}
- **Minimum Relevance**: {min_score}

## Search Strategy:
1. **Semantic Search**: Find conceptually related content using AI embeddings
2. **Knowledge Graph**: Explore entity relationships and connections  
3. **Session History**: Check if agents have worked on this before
4. **Similarity Analysis**: Find documents similar to known relevant ones

## Additional Context:
{additional_context}

Please execute a comprehensive search across all knowledge sources and provide the most relevant results with explanations of why each result might be helpful.
"""
            }
        ],
        arguments=[
            {"name": "query", "description": "Main search query or question", "required": True},
            {"name": "project", "description": "Project context filter", "required": False},
            {"name": "doc_types", "description": "Comma-separated document types", "required": False},
            {"name": "time_period", "description": "Time period for search", "required": False},
            {"name": "min_score", "description": "Minimum relevance score (0.0-1.0)", "required": False},
            {"name": "additional_context", "description": "Any additional context or constraints", "required": False}
        ]
    )

# ========================================
# SERVER LIFECYCLE
# ========================================

async def startup():
    """Initialize database connections and verify system health"""
    logger.info("🔍 Starting FindersKeepers Knowledge MCP Server...")
    
    try:
        # Initialize activity logger for n8n workflow integration
        await activity_logger.initialize()
        
        # Initialize database connections
        await postgres.connect()
        logger.info("✅ PostgreSQL connected")
        
        await neo4j.connect()
        logger.info("✅ Neo4j connected")
        
        await qdrant.connect()
        logger.info("✅ Qdrant connected")
        
        await redis.connect()
        logger.info("✅ Redis connected")
        
        # Verify system health
        health_check = await perform_health_check()
        if health_check["all_healthy"]:
            logger.info("🚀 Knowledge server ready for agent queries!")
            await activity_logger.log_action(
                action_type="server_startup",
                description="MCP Knowledge Server started successfully",
                details=health_check
            )
        else:
            logger.warning(f"⚠️ Some services have issues: {health_check}")
            
    except Exception as e:
        logger.error(f"❌ Failed to start knowledge server: {e}")
        raise

async def shutdown():
    """Gracefully close all database connections"""
    logger.info("🔌 Shutting down FindersKeepers Knowledge MCP Server...")
    
    try:
        # Log shutdown to n8n
        await activity_logger.shutdown()
        
        await postgres.disconnect()
        await neo4j.disconnect()
        await qdrant.disconnect()
        await redis.disconnect()
        
        logger.info("👋 Knowledge server shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

async def perform_health_check() -> Dict[str, Any]:
    """Perform comprehensive health check of all services"""
    health = {
        "postgres": await postgres.health_check(),
        "neo4j": await neo4j.health_check(),
        "qdrant": await qdrant.health_check(),
        "redis": await redis.health_check()
    }
    
    health["all_healthy"] = all(health.values())
    health["timestamp"] = datetime.utcnow().isoformat()
    
    return health

if __name__ == "__main__":
    # Run the MCP server
    logger.info("🌟 FindersKeepers v2 Knowledge MCP Server")
    logger.info("🔗 Connecting AI agents to universal knowledge...")
    
    # Run startup before starting the server
    import asyncio
    asyncio.run(startup())
    
    try:
        mcp.run()
    finally:
        # Run shutdown on exit
        asyncio.run(shutdown())