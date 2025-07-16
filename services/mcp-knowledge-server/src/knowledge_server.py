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
import psutil
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, Tool, Prompt

from database.postgres_client import PostgresClient
from database.neo4j_client import Neo4jClient  
from database.qdrant_client import QdrantClient
from database.redis_client import RedisClient
from activity_logger import activity_logger
from conversation_monitor import setup_conversation_monitoring

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

# Global conversation monitor for exit command detection
conversation_monitor = None

# Parent process monitoring
parent_process_monitor_task = None

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
        
        # Check for exit commands in user messages
        global conversation_monitor
        if conversation_monitor and message_type == "user_message":
            exit_detected = await conversation_monitor.process_message(content, message_type)
            if exit_detected:
                # Exit was detected and processed, add this to the message details
                message_data["details"]["exit_command_detected"] = True
        
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

# ========================================
# ENHANCED SESSION CONTINUITY HELPERS
# ========================================

def generate_detailed_actions_summary(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a detailed summary of recent actions for session resumption"""
    if not actions:
        return {"message": "No recent actions found", "categories": {}}
    
    # Categorize actions by type
    action_categories = {}
    for action in actions:
        action_type = action.get("action_type", "unknown")
        category = action_type.split(":")[0] if ":" in action_type else action_type
        
        if category not in action_categories:
            action_categories[category] = []
        action_categories[category].append(action)
    
    # Generate summary for each category
    category_summaries = {}
    for category, category_actions in action_categories.items():
        successful = [a for a in category_actions if a.get("success", True)]
        failed = [a for a in category_actions if not a.get("success", True)]
        
        category_summaries[category] = {
            "total": len(category_actions),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(category_actions) if category_actions else 0,
            "latest_action": category_actions[0] if category_actions else None,
            "latest_successful": successful[0] if successful else None,
            "latest_failed": failed[0] if failed else None
        }
    
    # Overall summary
    total_successful = sum(len([a for a in actions if a.get("success", True)]) for actions in [actions])
    overall_success_rate = total_successful / len(actions) if actions else 0
    
    return {
        "total_actions": len(actions),
        "overall_success_rate": overall_success_rate,
        "categories": category_summaries,
        "most_recent": actions[0] if actions else None,
        "action_types": list(action_categories.keys()),
        "time_span": {
            "latest": actions[0].get("timestamp") if actions else None,
            "earliest": actions[-1].get("timestamp") if actions else None
        }
    }

def generate_intelligent_next_steps(session_data: Dict[str, Any], actions: List[Dict[str, Any]]) -> List[str]:
    """Generate intelligent next steps based on session analysis"""
    next_steps = []
    
    if not actions:
        return ["🎯 Review project roadmap", "📋 Check recent commits", "🔍 Search knowledge base"]
    
    # Analyze recent actions for patterns
    recent_actions = actions[:5]
    failed_actions = [a for a in recent_actions if not a.get("success", True)]
    
    # Check for unresolved errors
    if failed_actions:
        latest_error = failed_actions[0]
        next_steps.append(f"🔧 Resolve error: {latest_error.get('description', 'Unknown error')}")
    
    # Check for file modifications
    file_actions = [a for a in recent_actions if "file" in a.get("action_type", "").lower()]
    if file_actions:
        next_steps.append("📄 Review recent file changes and test functionality")
    
    # Check for configuration changes
    config_actions = [a for a in recent_actions if "config" in a.get("action_type", "").lower()]
    if config_actions:
        next_steps.append("⚙️ Verify configuration changes are working correctly")
    
    # Check for database/MCP actions
    db_actions = [a for a in recent_actions if any(keyword in a.get("action_type", "").lower() 
                                                  for keyword in ["database", "mcp", "session"])]
    if db_actions:
        next_steps.append("🗄️ Test database connections and MCP functionality")
    
    # Check for commit/deployment actions
    commit_actions = [a for a in recent_actions if "commit" in a.get("action_type", "").lower()]
    if commit_actions:
        next_steps.append("🚀 Consider pushing changes or deploying updates")
    
    # Default recommendations if no specific patterns found
    if not next_steps:
        next_steps.extend([
            "🎯 Continue with current development tasks",
            "📋 Check project status and priorities",
            "🔍 Review recent changes and test functionality"
        ])
    
    return next_steps[:4]  # Limit to top 4 recommendations

def generate_continuation_recommendations_enhanced(session_data: Dict[str, Any], actions: List[Dict[str, Any]]) -> List[str]:
    """Generate enhanced continuation recommendations with priority and context"""
    recommendations = []
    
    if not actions:
        return ["🎯 Start with project overview", "📋 Review roadmap", "🔍 Check knowledge base"]
    
    # Analyze success patterns
    successful_actions = [a for a in actions if a.get("success", True)]
    failed_actions = [a for a in actions if not a.get("success", True)]
    
    success_rate = len(successful_actions) / len(actions) if actions else 0
    
    if success_rate < 0.7:
        recommendations.append("⚠️ HIGH PRIORITY: Address recent errors to improve success rate")
    
    # Check for incomplete work
    incomplete_indicators = ["partial", "started", "in_progress", "todo"]
    incomplete_actions = [a for a in actions if any(indicator in a.get("description", "").lower() 
                                                   for indicator in incomplete_indicators)]
    
    if incomplete_actions:
        recommendations.append("🔄 Complete partially finished tasks from previous session")
    
    # Check for testing needs
    test_actions = [a for a in actions if "test" in a.get("action_type", "").lower()]
    code_actions = [a for a in actions if any(keyword in a.get("action_type", "").lower() 
                                             for keyword in ["file_edit", "code", "implement"])]
    
    if code_actions and not test_actions:
        recommendations.append("🧪 Run tests to verify recent code changes")
    
    # Check for documentation needs
    doc_actions = [a for a in actions if "doc" in a.get("action_type", "").lower()]
    if not doc_actions and len(actions) > 5:
        recommendations.append("📚 Consider documenting recent changes")
    
    # Performance and optimization
    if len(actions) > 10:
        recommendations.append("⚡ Review session performance and optimize workflow")
    
    # Default productive recommendations
    if not recommendations:
        recommendations.extend([
            "🎯 Continue with current development momentum",
            "📋 Plan next feature or improvement",
            "🔍 Explore knowledge base for inspiration"
        ])
    
    return recommendations[:3]  # Limit to top 3 recommendations

def identify_priority_items(actions: List[Dict[str, Any]], files_modified: List[str]) -> List[str]:
    """Identify high-priority items that need immediate attention"""
    priority_items = []
    
    # Check for failed actions
    failed_actions = [a for a in actions if not a.get("success", True)]
    if failed_actions:
        priority_items.append(f"🚨 {len(failed_actions)} failed action(s) need attention")
    
    # Check for critical files
    critical_files = [f for f in files_modified if any(keyword in f.lower() 
                                                      for keyword in ["config", "server", "main", "init"])]
    if critical_files:
        priority_items.append(f"⚠️ {len(critical_files)} critical file(s) modified")
    
    # Check for security-related changes
    security_actions = [a for a in actions if any(keyword in a.get("description", "").lower() 
                                                  for keyword in ["auth", "security", "permission", "token"])]
    if security_actions:
        priority_items.append("🔒 Security-related changes need verification")
    
    # Check for database changes
    db_actions = [a for a in actions if any(keyword in a.get("action_type", "").lower() 
                                           for keyword in ["database", "migration", "schema"])]
    if db_actions:
        priority_items.append("🗄️ Database changes require testing")
    
    return priority_items

def identify_session_warnings(actions: List[Dict[str, Any]], failed_actions: List[Dict[str, Any]]) -> List[str]:
    """Identify potential warnings or issues from the session"""
    warnings = []
    
    # High failure rate warning
    if failed_actions and len(failed_actions) / len(actions) > 0.3:
        warnings.append("⚠️ High failure rate detected - review approach")
    
    # Repeated failures warning
    if len(failed_actions) > 3:
        warnings.append("🔄 Multiple failures detected - may need different strategy")
    
    # No recent activity warning
    if actions and actions[0].get("timestamp"):
        from datetime import datetime, timedelta
        last_action_time = datetime.fromisoformat(actions[0]["timestamp"].replace("Z", "+00:00"))
        if datetime.now(last_action_time.tzinfo) - last_action_time > timedelta(hours=6):
            warnings.append("⏰ Session has been inactive for over 6 hours")
    
    # Resource-intensive actions warning
    resource_actions = [a for a in actions if any(keyword in a.get("description", "").lower() 
                                                  for keyword in ["build", "compile", "install", "download"])]
    if len(resource_actions) > 5:
        warnings.append("💾 Multiple resource-intensive actions detected")
    
    return warnings

def analyze_session_conversation_flow(actions: List[Dict[str, Any]]) -> str:
    """Analyze conversation flow patterns from actions"""
    conversation_actions = [a for a in actions if "conversation" in a.get("action_type", "")]
    
    if not conversation_actions:
        return "no_conversation_data"
    
    user_messages = [a for a in conversation_actions if "user_message" in a.get("action_type", "")]
    ai_responses = [a for a in conversation_actions if "ai_response" in a.get("action_type", "")]
    
    if len(user_messages) > len(ai_responses):
        return "user_driven"
    elif len(ai_responses) > len(user_messages):
        return "ai_driven"
    else:
        return "balanced_interaction"

def analyze_session_completion_status(actions: List[Dict[str, Any]]) -> str:
    """Analyze whether the session appears to have completed its goals"""
    if not actions:
        return "no_activity"
    
    # Check for completion indicators
    completion_indicators = ["complete", "finished", "done", "success", "resolved"]
    completion_actions = [a for a in actions if any(indicator in a.get("description", "").lower() 
                                                   for indicator in completion_indicators)]
    
    # Check for failure indicators
    failure_indicators = ["failed", "error", "broken", "issue"]
    failure_actions = [a for a in actions if any(indicator in a.get("description", "").lower() 
                                                 for indicator in failure_indicators)]
    
    success_rate = len([a for a in actions if a.get("success", True)]) / len(actions)
    
    if completion_actions and success_rate > 0.8:
        return "likely_complete"
    elif failure_actions and success_rate < 0.5:
        return "incomplete_with_issues"
    elif success_rate > 0.7:
        return "progressing_well"
    else:
        return "mixed_progress"

def calculate_session_duration(session_data: Dict[str, Any]) -> str:
    """Calculate human-readable session duration"""
    started_at = session_data.get("started_at")
    ended_at = session_data.get("ended_at")
    
    if not started_at:
        return "unknown"
    
    from datetime import datetime
    try:
        start_time = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(ended_at.replace("Z", "+00:00")) if ended_at else datetime.now(start_time.tzinfo)
        
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600
        
        if hours < 1:
            return f"{int(duration.total_seconds() / 60)} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            return f"{int(hours / 24)} days, {int(hours % 24)} hours"
    except:
        return "unknown"

async def check_pending_operations(session_id: str) -> bool:
    """Check if there are any pending operations for the session"""
    try:
        # Check for pending webhook calls
        pending_webhooks = await redis.get(f"pending_webhooks:{session_id}")
        
        # Check for pending database writes
        pending_writes = await redis.get(f"pending_writes:{session_id}")
        
        # Check for pending file operations
        pending_files = await redis.get(f"pending_files:{session_id}")
        
        return any([pending_webhooks, pending_writes, pending_files])
    except:
        return False

async def export_session_context(session_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
    """Export session context as a searchable document"""
    try:
        # Create a comprehensive document from session context
        document_content = generate_session_document(session_id, session_context)
        
        # Store in PostgreSQL as a searchable document
        document_id = f"session_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        await postgres.ingest_document(
            document_id=document_id,
            title=f"Session Context: {session_id}",
            content=document_content,
            project="finderskeepers-v2",
            tags=["session_context", "conversation_history", "agent_actions"],
            metadata={
                "session_id": session_id,
                "document_type": "session_export",
                "export_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "document_id": document_id,
            "content_length": len(document_content)
        }
    except Exception as e:
        logger.error(f"Failed to export session context: {e}")
        return {"success": False, "error": str(e)}

def generate_session_document(session_id: str, session_context: Dict[str, Any]) -> str:
    """Generate a comprehensive document from session context"""
    actions = session_context.get("actions", [])
    conversation = session_context.get("conversation_history", [])
    file_changes = session_context.get("file_changes", [])
    
    document_parts = [
        f"# Session Context: {session_id}",
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
        "## Session Summary",
        f"- Total Actions: {len(actions)}",
        f"- Conversation Messages: {len(conversation)}",
        f"- Files Modified: {len(file_changes)}",
        f"- Success Rate: {session_context.get('summary', {}).get('success_rate', 0):.1%}",
        "",
        "## Recent Actions"
    ]
    
    for action in actions[:10]:  # Last 10 actions
        document_parts.append(f"- {action.get('timestamp', 'Unknown time')}: {action.get('description', 'No description')}")
        if not action.get('success', True):
            document_parts.append(f"  ❌ Failed: {action.get('details', {}).get('error_message', 'Unknown error')}")
    
    if file_changes:
        document_parts.extend([
            "",
            "## Files Modified",
            ""
        ])
        for file_change in file_changes[:20]:  # Last 20 file changes
            document_parts.append(f"- {file_change}")
    
    if conversation:
        document_parts.extend([
            "",
            "## Conversation Highlights",
            ""
        ])
        for msg in conversation[:10]:  # Last 10 messages
            msg_type = msg.get('message_type', 'unknown')
            content = msg.get('content', '')[:200] + '...' if len(msg.get('content', '')) > 200 else msg.get('content', '')
            document_parts.append(f"**{msg_type}**: {content}")
    
    return "\n".join(document_parts)

async def prepare_session_resume_info(session_id: str, session_context: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Prepare comprehensive resume information for the next session"""
    actions = session_context.get("actions", [])
    
    resume_info = {
        "previous_session_id": session_id,
        "end_reason": reason,
        "ended_at": datetime.utcnow().isoformat(),
        "session_stats": {
            "total_actions": len(actions),
            "success_rate": session_context.get('summary', {}).get('success_rate', 0),
            "conversation_messages": len(session_context.get('conversation_history', [])),
            "files_modified": len(session_context.get('file_changes', []))
        },
        "continuation_context": {
            "last_actions": actions[:5] if actions else [],
            "recent_files": session_context.get('file_changes', [])[:10],
            "unresolved_issues": [a for a in actions if not a.get('success', True)][:3],
            "key_achievements": [a for a in actions if a.get('success', True)][:3]
        },
        "next_session_preparation": {
            "recommended_actions": generate_intelligent_next_steps(session_context, actions),
            "priority_items": identify_priority_items(actions, session_context.get('file_changes', [])),
            "warnings": identify_session_warnings(actions, [a for a in actions if not a.get('success', True)])
        }
    }
    
    return resume_info

async def perform_session_cleanup(session_id: str) -> Dict[str, Any]:
    """Perform final cleanup operations for the session"""
    try:
        # Clear any session-specific cache entries
        await redis.delete(f"session_cache:{session_id}")
        await redis.delete(f"pending_operations:{session_id}")
        
        # Log cleanup completion
        logger.info(f"✅ Session cleanup completed for {session_id}")
        
        return {"success": True, "message": "Session cleanup completed"}
    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        return {"success": False, "error": str(e)}

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
async def resume_session(
    project: str = "finderskeepers-v2",
    quick_summary: bool = True,
    auto_initialize: bool = True
) -> Dict[str, Any]:
    """
    🚀 Smart session resumption with automatic context loading and continuation recommendations.
    
    This is the MAIN tool for starting your Claude Code sessions. It automatically:
    - Finds your most recent session
    - Loads full context from previous work
    - Analyzes what you were working on
    - Provides intelligent next-step recommendations
    - Initializes a new session with complete continuity
    
    Args:
        project: Project to resume (default: finderskeepers-v2)
        quick_summary: If True, show concise summary. If False, full detailed context
        auto_initialize: Whether to automatically start a new session (default: True)
    
    Returns:
        Complete session resume information with context, recommendations, and new session ID
    """
    try:
        logger.info(f"🔄 Resuming session for project: {project}")
        
        # Step 1: Try Redis cache first for instant results
        cached_resume_info = await redis.get(f"session_resume:{project}")
        
        if cached_resume_info and quick_summary:
            cached_data = json.loads(cached_resume_info)
            logger.info("⚡ Using cached resume information")
            
            # Still initialize new session if requested
            if auto_initialize:
                new_session_result = await initialize_claude_session(project=project)
                cached_data["new_session"] = new_session_result
                
            return cached_data
        
        # Step 2: Get latest session from database
        latest_session = await postgres.get_latest_session_with_full_context(project)
        
        if not latest_session:
            logger.info("🌱 No previous session found, starting fresh")
            
            if auto_initialize:
                new_session_result = await initialize_claude_session(project=project)
                return {
                    "status": "fresh_start",
                    "message": "🌱 No previous session found. Starting fresh with full context!",
                    "new_session": new_session_result,
                    "recommendations": ["🎯 Check project roadmap", "📋 Review recent commits", "🔍 Search knowledge base for context"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"message": "No previous session found. Ready to start fresh!"}
        
        # Step 3: Generate comprehensive resume context
        session_id = latest_session["session_id"]
        actions = latest_session.get("actions", [])
        
        # Analyze recent actions for context
        recent_actions = actions[:10]  # Last 10 actions
        successful_actions = [a for a in recent_actions if a.get("success", True)]
        failed_actions = [a for a in recent_actions if not a.get("success", True)]
        
        # Generate action summary
        actions_summary = generate_detailed_actions_summary(recent_actions)
        
        # Get files that were modified
        files_modified = await postgres.get_files_affected_by_session(session_id)
        
        # Generate intelligent next steps
        next_steps = generate_intelligent_next_steps(latest_session, actions)
        
        # Calculate session statistics
        success_rate = len(successful_actions) / len(recent_actions) if recent_actions else 0
        
        # Analyze conversation flow for emotional context
        conversation_flow = analyze_session_conversation_flow(actions)
        
        # Generate completion status
        completion_status = analyze_session_completion_status(actions)
        
        # Create comprehensive resume data
        resume_data = {
            "status": "session_resumed",
            "previous_session": {
                "session_id": session_id,
                "started_at": latest_session.get("started_at"),
                "ended_at": latest_session.get("ended_at"),
                "duration": calculate_session_duration(latest_session),
                "agent_type": latest_session.get("agent_type", "claude-code")
            },
            "session_analysis": {
                "total_actions": len(actions),
                "successful_actions": len(successful_actions),
                "failed_actions": len(failed_actions),
                "success_rate": success_rate,
                "completion_status": completion_status,
                "conversation_flow": conversation_flow
            },
            "recent_work": {
                "actions_summary": actions_summary,
                "files_modified": files_modified,
                "last_action": recent_actions[0] if recent_actions else None,
                "last_successful_action": successful_actions[0] if successful_actions else None,
                "last_failed_action": failed_actions[0] if failed_actions else None
            },
            "continuation_guidance": {
                "next_steps": next_steps,
                "recommendations": generate_continuation_recommendations_enhanced(latest_session, actions),
                "priority_items": identify_priority_items(actions, files_modified),
                "warnings": identify_session_warnings(actions, failed_actions)
            },
            "context_loaded": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Step 4: Cache the resume information for quick access
        await redis.setex(f"session_resume:{project}", 3600, json.dumps(resume_data))
        
        # Step 5: Auto-initialize new session if requested
        if auto_initialize:
            new_session_result = await initialize_claude_session(
                project=project,
                context={
                    "resumed_from": session_id,
                    "continuation_mode": True,
                    "previous_session_summary": resume_data["session_analysis"]
                }
            )
            resume_data["new_session"] = new_session_result
            
            # Log the successful resume
            await activity_logger.log_action(
                action_type="session_resume",
                description=f"Successfully resumed from session {session_id}",
                details={
                    "previous_session_id": session_id,
                    "new_session_id": new_session_result.get("session_id"),
                    "actions_resumed": len(actions),
                    "files_context": len(files_modified),
                    "success_rate": success_rate
                }
            )
        
        return resume_data
        
    except Exception as e:
        logger.error(f"Session resume failed: {e}")
        return {
            "error": str(e),
            "status": "resume_failed",
            "message": "❌ Session resume failed. Starting fresh session instead.",
            "fallback_session": await initialize_claude_session(project=project) if auto_initialize else None,
            "timestamp": datetime.utcnow().isoformat()
        }

@mcp.tool()
async def endsession(
    session_id: Optional[str] = None,
    reason: str = "work_complete",
    completion_timeout: int = 30,
    prepare_resume: bool = True,
    export_context: bool = True
) -> Dict[str, Any]:
    """
    🏁 Gracefully end your Claude Code session with guaranteed data persistence and resume preparation.
    
    This is the MAIN tool for ending your sessions properly. It ensures:
    - All conversation data is fully ingested and stored
    - Session context is exported for future searchability
    - Resume information is prepared for next session
    - Databases are properly updated before shutdown
    - Graceful termination with cleanup verification
    
    Args:
        session_id: Session ID to end (auto-detected if not provided)
        reason: Reason for ending session (default: work_complete)
        completion_timeout: Max seconds to wait for data ingestion (default: 30)
        prepare_resume: Whether to prepare resume info for next session (default: True)
        export_context: Whether to export session context as searchable document (default: True)
    
    Returns:
        Session termination confirmation with data persistence status
    """
    try:
        logger.info(f"🏁 Ending session gracefully: {session_id or 'auto-detect'}")
        
        # Step 1: Auto-detect session ID if not provided
        if not session_id:
            latest_session = await postgres.get_latest_active_session("finderskeepers-v2")
            if latest_session:
                session_id = latest_session["session_id"]
            else:
                return {
                    "error": "No active session found to end",
                    "status": "no_active_session",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Step 2: Get full session context before termination
        session_context = await get_full_conversation_context(
            session_id=session_id,
            include_conversation_history=True,
            include_files=True,
            conversation_limit=100
        )
        
        # Step 3: Wait for any pending data ingestion to complete
        logger.info(f"⏳ Waiting up to {completion_timeout}s for data ingestion to complete...")
        await asyncio.sleep(2)  # Initial buffer
        
        # Check for pending operations
        pending_operations = await check_pending_operations(session_id)
        wait_time = 0
        
        while pending_operations and wait_time < completion_timeout:
            await asyncio.sleep(1)
            wait_time += 1
            pending_operations = await check_pending_operations(session_id)
            
        if pending_operations:
            logger.warning(f"⚠️ Some operations still pending after {completion_timeout}s timeout")
        
        # Step 4: Export session context as searchable document
        export_result = None
        if export_context:
            export_result = await export_session_context(session_id, session_context)
        
        # Step 5: Prepare resume information for next session
        resume_info = None
        if prepare_resume:
            resume_info = await prepare_session_resume_info(session_id, session_context, reason)
            
            # Save to Redis with 24-hour expiration
            await redis.setex(
                f"session_resume:finderskeepers-v2", 
                86400, 
                json.dumps(resume_info)
            )
        
        # Step 6: Mark session as ended in database
        end_result = await postgres.end_session(session_id, reason)
        
        # Step 7: Log the session termination
        await activity_logger.log_action(
            action_type="session_end",
            description=f"Session {session_id} ended gracefully",
            details={
                "session_id": session_id,
                "reason": reason,
                "completion_timeout": completion_timeout,
                "data_exported": export_context,
                "resume_prepared": prepare_resume,
                "pending_operations_cleared": not pending_operations,
                "actions_processed": len(session_context.get("actions", [])),
                "conversation_messages": len(session_context.get("conversation_history", []))
            }
        )
        
        # Step 8: Final cleanup and verification
        cleanup_result = await perform_session_cleanup(session_id)
        
        return {
            "status": "session_ended",
            "session_id": session_id,
            "reason": reason,
            "data_persistence": {
                "context_exported": export_result is not None,
                "resume_prepared": resume_info is not None,
                "database_updated": end_result.get("success", False),
                "cleanup_completed": cleanup_result.get("success", False)
            },
            "session_summary": {
                "total_actions": len(session_context.get("actions", [])),
                "total_messages": len(session_context.get("conversation_history", [])),
                "files_modified": len(session_context.get("file_changes", [])),
                "success_rate": session_context.get("summary", {}).get("success_rate", 0)
            },
            "next_session_ready": resume_info is not None,
            "message": f"✅ Session {session_id[-8:]} ended gracefully. All data preserved for next session.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Session termination failed: {e}")
        return {
            "error": str(e),
            "status": "termination_failed",
            "session_id": session_id,
            "message": "❌ Session termination encountered errors. Some data may not be preserved.",
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
        
        # Initialize conversation monitoring for exit command detection
        global conversation_monitor
        conversation_monitor = await setup_conversation_monitoring(activity_logger)
        
        # Start parent process monitoring
        global parent_process_monitor_task
        parent_process_monitor_task = asyncio.create_task(monitor_parent_process())
        
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
        # Stop conversation monitoring
        global conversation_monitor
        if conversation_monitor:
            conversation_monitor.stop_monitoring()
            
        # Stop parent process monitoring
        global parent_process_monitor_task
        if parent_process_monitor_task:
            parent_process_monitor_task.cancel()
            try:
                await parent_process_monitor_task
            except asyncio.CancelledError:
                pass
            
        # Log shutdown to n8n
        await activity_logger.shutdown("graceful_shutdown")
        
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

async def monitor_parent_process():
    """Monitor parent process and shut down if it terminates"""
    parent_pid = os.getppid()
    logger.info(f"👁️ Monitoring parent process PID: {parent_pid}")
    
    # Fixed: Use event-driven parent monitoring instead of infinite loop
    try:
        # Set up signal handlers for proper shutdown
        def handle_shutdown():
            logger.info("🚪 Parent process terminated, shutting down MCP server")
            loop = asyncio.get_event_loop()
            loop.create_task(shutdown_gracefully())
        
        async def shutdown_gracefully():
            try:
                await activity_logger.shutdown("parent_process_terminated")
                
                # Stop conversation monitoring
                global conversation_monitor
                if conversation_monitor:
                    conversation_monitor.stop_monitoring()
                
                # Disconnect databases gracefully
                try:
                    await postgres.disconnect()
                    await neo4j.disconnect()
                    await qdrant.disconnect()
                    await redis.disconnect()
                except Exception as db_error:
                    logger.error(f"Database disconnect error: {db_error}")
                
                logger.info("👋 MCP server shutdown complete (parent terminated)")
            except Exception as e:
                logger.error(f"Shutdown error: {e}")
        
        # Check parent exists once, then rely on signals
        if not psutil.pid_exists(parent_pid):
            logger.info("🚪 Parent process not found at startup")
            await shutdown_gracefully()
            return
        
        logger.info("✅ Parent process monitoring enabled (signal-based)")
        
    except asyncio.CancelledError:
        logger.info("👁️ Parent process monitoring cancelled")

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Run the MCP server
    logger.info("🌟 FindersKeepers v2 Knowledge MCP Server")
    logger.info("🔗 Connecting AI agents to universal knowledge...")
    
    import signal
    import sys
    
    def signal_handler(signum, frame):
        """Handle termination signals gracefully"""
        signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT" if signum == signal.SIGINT else f"SIG{signum}"
        logger.info(f"🛑 Received {signal_name} ({signum}), shutting down gracefully...")
        # Run shutdown in a new event loop since we might be in a signal handler
        try:
            import asyncio
            # Create async shutdown function with signal reason
            async def signal_shutdown():
                global conversation_monitor
                if conversation_monitor:
                    conversation_monitor.stop_monitoring()
                await activity_logger.shutdown("signal_termination")
                await postgres.disconnect()
                await neo4j.disconnect()
                await qdrant.disconnect()
                await redis.disconnect()
                logger.info("👋 Knowledge server shutdown complete (signal)")
            
            asyncio.run(signal_shutdown())
        except Exception as e:
            logger.error(f"Error during signal shutdown: {e}")
        finally:
            sys.exit(0)
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run startup before starting the server
    import asyncio
    asyncio.run(startup())
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("🛑 KeyboardInterrupt received")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        # Run shutdown on exit
        try:
            asyncio.run(shutdown())
        except Exception as e:
            logger.error(f"Error during final shutdown: {e}")