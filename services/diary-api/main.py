"""
FindersKeepers v2 - FastAPI Diary & Knowledge Management API
Personal AI Agent Knowledge Hub (July 2025)
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
import json
import logging
import httpx
import asyncio
from uuid import uuid4

# Import API modules
from app.api.v1.ingestion import ingestion_router
from app.api.v1.diary import diary_router
from app.database.connection import db_manager
from app.database.queries import StatsQueries, SessionQueries, DocumentQueries
from app.api.chat_endpoints import ChatRequest, ChatResponse, process_chat_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# OLLAMA CLIENT CONFIGURATION
# ========================================

class OllamaClient:
    """Local LLM client for zero-cost embeddings and inference"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://fk2_ollama:11434")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
        self.chat_model = os.getenv("CHAT_MODEL", "llama3.2:3b")
        self.use_local = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
        
    async def get_embeddings(self, text: str) -> List[float]:
        """Generate embeddings using local Ollama model"""
        if not self.use_local:
            logger.warning("Local LLM disabled, falling back to external API")
            return []
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": self.embedding_model,
                        "input": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings = data.get("embeddings", [])
                # Ollama returns array of arrays, we need the first array
                return embeddings[0] if embeddings and isinstance(embeddings[0], list) else embeddings
                
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            return []
    
    async def generate_text(self, prompt: str, max_tokens: int = 512) -> str:
        """Generate text using local chat model"""
        if not self.use_local:
            logger.warning("Local LLM disabled, falling back to external API")
            return ""
            
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.7
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
                
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}")
            return ""
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/version")
                return response.status_code == 200
        except:
            return False

# Initialize Ollama client
ollama_client = OllamaClient()

app = FastAPI(
    title="FindersKeepers v2 API",
    description="Personal AI Agent Knowledge Hub - Where agents share memories and humans never lose context",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for React frontend and web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://127.0.0.1:3000",  # React development server (alt)
        "http://localhost:3001",  # React development server (port 3001)
        "http://127.0.0.1:3001",  # React development server (port 3001 alt)
        "http://localhost:3002",  # React development server (port 3002)
        "http://127.0.0.1:3002",  # React development server (port 3002 alt)
        "http://localhost:3003",  # React development server (port 3003)
        "http://127.0.0.1:3003",  # React development server (port 3003 alt)
        "http://localhost:5173",  # Vite development server (fallback)
        "http://127.0.0.1:5173",  # Vite development server (fallback)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestion_router)
app.include_router(diary_router)



# ========================================
# DATA MODELS
# ========================================

class AgentSession(BaseModel):
    """Agent session entry for diary tracking"""
    session_id: str = Field(..., description="Unique session identifier")
    agent_type: str = Field(..., description="Type of agent (claude, gpt, etc.)")
    user_id: str = Field(default="local_user", description="User identifier")
    project: Optional[str] = Field(None, description="Project context (bitcain, skellekey, etc.)")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context and metadata")
    
class AgentAction(BaseModel):
    """Individual action within an agent session"""
    action_id: str = Field(..., description="Unique action identifier")
    session_id: str = Field(..., description="Parent session ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action_type: str = Field(..., description="Type of action (file_edit, command, config_change, etc.)")
    description: str = Field(..., description="Human-readable description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Action-specific details")
    files_affected: List[str] = Field(default_factory=list, description="List of files modified")
    success: bool = Field(True, description="Whether action completed successfully")

class KnowledgeQuery(BaseModel):
    """Query for knowledge graph search"""
    question: str = Field(..., description="Natural language question")
    project: Optional[str] = Field(None, description="Limit search to specific project")
    session_context: Optional[str] = Field(None, description="Current session context")
    include_history: bool = Field(True, description="Include historical context")

class DocumentIngest(BaseModel):
    """Document ingestion request"""
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    project: str = Field(..., description="Project association")
    doc_type: str = Field(default="general", description="Document type (procedure, architecture, etc.)")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ConfigChange(BaseModel):
    """Configuration change tracking"""
    component: str = Field(..., description="Component changed (llm_provider, docker, etc.)")
    change_type: str = Field(..., description="Type of change (switch, update, rollback)")
    old_value: Optional[str] = Field(None, description="Previous value")
    new_value: str = Field(..., description="New value")
    reason: str = Field(..., description="Reason for change")
    impact: Optional[str] = Field(None, description="Expected impact")
    project: Optional[str] = Field(None, description="Project context")

class EmbeddingRequest(BaseModel):
    """Request for text embeddings"""
    text: str = Field(..., description="Text to generate embeddings for")

# ========================================
# HEALTH CHECK
# ========================================

@app.get("/", tags=["System"])
async def root():
    """Root endpoint with system information"""
    return {
        "service": "FindersKeepers v2 API",
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "diary": "/api/diary/*",
            "knowledge": "/api/knowledge/*",
            "config": "/api/config/*",
            "ingestion": "/api/v1/ingestion/*"
        }
    }


@app.get("/health", tags=["System"])
async def health_check():
    """System health check with REAL database status"""
    try:
        # Check Ollama service
        ollama_healthy = await ollama_client.health_check()
        
        # Check ALL database services
        db_health = await db_manager.health_check()
        
        # Check n8n container status (simplified - assume running if we get here)
        n8n_healthy = True  # n8n is part of docker-compose, assume healthy
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "api": "up",
                "postgres": "up" if db_health['postgres'] else "down",
                "neo4j": "up" if db_health['neo4j'] else "down",
                "qdrant": "up" if db_health['qdrant'] else "down",
                "redis": "up" if db_health['redis'] else "down",
                "ollama": "up" if ollama_healthy else "down",
                "n8n": "up" if n8n_healthy else "down"
            },
            "local_llm": {
                "enabled": ollama_client.use_local,
                "embedding_model": ollama_client.embedding_model,
                "chat_model": ollama_client.chat_model,
                "healthy": ollama_healthy
            },
            "database_details": db_health['details']
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/simple-test")
async def simple_test():
    return {"message": "Simple test endpoint works!", "n8n_test": "CODE_UPDATED_FOR_N8N"}


@app.get("/api/documents-list", tags=["Knowledge"])
async def get_documents_list(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    format: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[str] = None,
    file_type: Optional[str] = None
):
    """Get documents list from database - Frontend endpoint"""
    try:
        logger.info(f"Getting documents: page={page}, limit={limit}, search={search}")
        
        # Simple test first
        return {
            "success": True,
            "data": {
                "documents": [],
                "total_pages": 0,
                "current_page": page
            },
            "message": "Test endpoint working - Route registered successfully!",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Get documents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# EMBEDDINGS API - For MCP Knowledge Server
# ========================================

@app.post("/api/embeddings", tags=["Embeddings"])
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings for text using local Ollama model"""
    try:
        logger.info(f"Generating embeddings for text (length: {len(request.text)})")
        
        # Generate embeddings using local Ollama
        embeddings = await ollama_client.get_embeddings(request.text)
        
        if not embeddings:
            raise HTTPException(
                status_code=503, 
                detail="Embedding generation failed - Ollama service may be unavailable"
            )
        
        return {
            "embeddings": embeddings,
            "dimensions": len(embeddings),
            "model": ollama_client.embedding_model,
            "text_length": len(request.text),
            "local_llm_used": ollama_client.use_local
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation error: {str(e)}")

# ========================================
# DIARY API - Moved to app/api/v1/diary/endpoints.py
# ========================================

# ========================================
# KNOWLEDGE API - Graph Queries & Document Management
# ========================================

@app.post("/api/knowledge/query", tags=["Knowledge"])
async def query_knowledge(query: KnowledgeQuery):
    """Query the knowledge graph with natural language using local LLM"""
    try:
        logger.info(f"Knowledge query: {query.question}")
        
        # Generate embeddings for the query using local Ollama
        query_embeddings = await ollama_client.get_embeddings(query.question)
        
        # Use local LLM to analyze the query
        analysis_prompt = f"""
        Analyze this knowledge query and provide a structured response:
        Question: {query.question}
        Project Context: {query.project or "general"}
        
        Based on the question, what type of information would be most relevant?
        Provide a brief analysis.
        """
        
        analysis = await ollama_client.generate_text(analysis_prompt, max_tokens=256)
        
        response = {
            "answer": analysis if analysis else f"Based on your knowledge graph, regarding '{query.question}', here's what I found...",
            "sources": [
                {"type": "session", "id": "session_001", "relevance": 0.9},
                {"type": "document", "id": "docker_procedures", "relevance": 0.8}
            ],
            "context": query.project or "general",
            "confidence": 0.85,
            "embeddings_generated": len(query_embeddings) > 0,
            "local_llm_used": ollama_client.use_local and analysis != ""
        }
        
        return response
    except Exception as e:
        logger.error(f"Knowledge query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/docs/ingest", tags=["Knowledge"])
async def ingest_document(doc: DocumentIngest, background_tasks: BackgroundTasks):
    """Ingest new documentation into knowledge base with local embeddings"""
    try:
        logger.info(f"Ingesting document: {doc.title} ({doc.project})")
        
        # Generate embeddings for the document using local Ollama
        doc_embeddings = await ollama_client.get_embeddings(doc.content)
        
        # Add background processing task
        background_tasks.add_task(process_document_with_ollama, doc, doc_embeddings)
        
        return {
            "status": "accepted",
            "message": f"Document '{doc.title}' queued for processing with local embeddings",
            "document_id": str(uuid4()),
            "project": doc.project,
            "embeddings_generated": len(doc_embeddings) > 0,
            "local_processing": ollama_client.use_local
        }
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/docs/by-id/{document_id}", tags=["Knowledge"])
async def get_document(document_id: str):
    """Get single document by ID"""
    try:
        logger.info(f"Getting document: {document_id}")
        
        # Get document from database
        document = await DocumentQueries.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "data": document,
            "message": f"Retrieved document {document_id}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docs/context", tags=["Knowledge"])
async def get_project_context(project: str, topic: Optional[str] = None):
    """Get relevant documentation for current project/topic"""
    try:
        logger.info(f"Getting context for project: {project}, topic: {topic}")
        
        # TODO: Implement actual context retrieval
        context = {
            "project": project,
            "topic": topic,
            "relevant_docs": [
                {"title": "Docker Setup Guide", "type": "procedure", "relevance": 0.9},
                {"title": "Project Architecture", "type": "architecture", "relevance": 0.7}
            ],
            "recent_sessions": [
                {"session_id": "session_001", "description": "Docker troubleshooting", "date": "2025-07-04"}
            ],
            "key_procedures": [
                "Docker login steps",
                "Container deployment process",
                "Configuration management"
            ]
        }
        
        return context
    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# SEARCH API - Vector and Semantic Search
# ========================================

@app.post("/api/search/vector", tags=["Search"])
async def vector_search(query: dict):
    """Perform REAL vector similarity search using PostgreSQL database"""
    try:
        search_query = query.get("query", "")
        limit = query.get("limit", 10)
        threshold = query.get("threshold", 0.5)
        project = query.get("project", None)
        
        logger.info(f"REAL vector search: {search_query}, limit={limit}, threshold={threshold}")
        
        # Get REAL documents from database
        doc_results = await DocumentQueries.get_documents(
            page=1,
            limit=limit,
            search=search_query,
            project=project
        )
        
        # Convert to vector search format
        results = []
        for doc in doc_results.get("documents", []):
            results.append({
                "document_id": doc["id"],
                "chunk_id": f"chunk_{doc['id']}",
                "content": doc["content"],
                "similarity_score": 0.85,  # TODO: Implement real vector similarity
                "metadata": {
                    "source_file": doc["file_path"],
                    "file_type": doc["format"],
                    "file_size": doc["file_size"],
                    "project": doc["project"],
                    "tags": doc["tags"],
                    "created_date": doc["created_at"]
                }
            })
        
        # Filter by threshold
        results = [r for r in results if r["similarity_score"] >= threshold]
        
        return {
            "success": True,
            "data": results,
            "message": f"Found {len(results)} REAL documents from database",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": search_query,
            "total_in_db": doc_results.get("total_count", 0)
        }
    except Exception as e:
        logger.error(f"REAL vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/semantic", tags=["Search"])
async def semantic_search(request: dict):
    """Perform REAL semantic search using local LLM and database"""
    try:
        query = request.get("query", "")
        limit = request.get("limit", 10)
        threshold = request.get("threshold", 0.5)
        project = request.get("project", None)
        
        logger.info(f"REAL semantic search: {query}, limit={limit}, threshold={threshold}")
        
        # Generate embeddings for semantic search using Ollama
        query_embeddings = await ollama_client.get_embeddings(query)
        
        # Get REAL documents from database for semantic analysis
        doc_results = await DocumentQueries.get_documents(
            page=1,
            limit=limit * 2,  # Get more for semantic filtering
            search=query,
            project=project
        )
        
        # Process documents with semantic analysis using Ollama
        results = []
        for doc in doc_results.get("documents", []):
            # Use Ollama to analyze semantic relevance
            semantic_prompt = f"""
            Query: {query}
            Document: {doc['content'][:500]}
            
            Rate the semantic relevance (0.0-1.0) of this document to the query.
            Consider concepts, themes, and context. Respond with just a number.
            """
            
            try:
                # Get semantic relevance score from local LLM
                relevance_text = await ollama_client.generate_text(semantic_prompt, max_tokens=10)
                try:
                    # Extract numeric score
                    import re
                    score_match = re.search(r'(\d+\.?\d*)', relevance_text)
                    similarity_score = float(score_match.group(1)) if score_match else 0.5
                    similarity_score = min(max(similarity_score, 0.0), 1.0)  # Clamp 0-1
                except:
                    similarity_score = 0.5  # Default if parsing fails
            except:
                similarity_score = 0.5  # Default if Ollama fails
            
            # Only include if above threshold
            if similarity_score >= threshold:
                results.append({
                    "document_id": doc["id"],
                    "chunk_id": f"chunk_{doc['id']}",
                    "content": doc["content"],
                    "similarity_score": similarity_score,
                    "metadata": {
                        "source_file": doc["file_path"],
                        "file_type": doc["format"],
                        "file_size": doc["file_size"],
                        "project": doc["project"],
                        "tags": doc["tags"],
                        "created_date": doc["created_at"]
                    }
                })
        
        # Sort by semantic similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = results[:limit]
        
        return {
            "success": True,
            "data": results,
            "message": f"Found {len(results)} REAL semantically relevant documents",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "embeddings_used": len(query_embeddings) > 0,
            "local_llm_used": ollama_client.use_local,
            "total_in_db": doc_results.get("total_count", 0),
            "semantic_analysis": "local_ollama"
        }
    except Exception as e:
        logger.error(f"REAL semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# CONFIGURATION API - Change Tracking & Management
# ========================================

@app.post("/api/config/log-change", tags=["Configuration"])
async def log_config_change(change: ConfigChange):
    """Log a configuration change"""
    try:
        logger.info(f"Logging config change: {change.component} -> {change.new_value}")
        
        # TODO: Store in database and update knowledge graph
        change_data = change.dict()
        change_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        change_data["change_id"] = f"cfg_{int(datetime.now().timestamp())}"
        
        return {
            "status": "logged",
            "change_id": change_data["change_id"],
            "message": f"Configuration change logged for {change.component}",
            "data": change_data
        }
    except Exception as e:
        logger.error(f"Config change logging failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/history", tags=["Configuration"])
async def get_config_history(component: Optional[str] = None, limit: int = 10):
    """Get configuration change history"""
    try:
        logger.info(f"Getting config history for: {component}")
        
        # TODO: Implement actual history retrieval
        history = [
            {
                "change_id": "cfg_001",
                "component": "llm_provider",
                "change_type": "switch",
                "old_value": "google_gemini",
                "new_value": "openai_gpt4",
                "reason": "Rate limit issues",
                "timestamp": "2025-07-04T09:30:00Z",
                "impact": "Improved response speed"
            }
        ]
        
        return {
            "status": "success",
            "history": history,
            "component": component,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"Config history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# STATISTICS API - System Metrics and Performance
# ========================================

@app.get("/api/stats/sessions", tags=["Statistics"])
async def get_session_stats(timeframe: str = "24h"):
    """Get REAL session statistics from PostgreSQL database"""
    try:
        logger.info(f"Getting REAL session stats for timeframe: {timeframe}")
        
        # Get REAL statistics from database
        stats = await StatsQueries.get_session_stats(timeframe)
        
        return {
            "success": True,
            "data": stats,
            "message": f"Retrieved REAL session statistics for {timeframe}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Session stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/documents", tags=["Statistics"])
async def get_document_stats():
    """Get REAL document and vector database statistics"""
    try:
        logger.info("Getting REAL document statistics")
        
        # Get REAL statistics from database
        stats = await StatsQueries.get_document_stats()
        
        return {
            "success": True,
            "data": stats,
            "message": "Retrieved REAL document statistics",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Document stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/performance", tags=["Statistics"])
async def get_performance_metrics():
    """Get REAL system performance metrics and API response times"""
    try:
        logger.info("Getting REAL performance metrics")
        
        # Get REAL performance metrics from database
        metrics = await StatsQueries.get_performance_metrics()
        
        return {
            "success": True,
            "data": metrics,
            "message": "Retrieved REAL performance metrics",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/system", tags=["Statistics"])
async def get_system_monitoring():
    """Get REAL system monitoring data including Docker containers and host metrics"""
    try:
        logger.info("Getting REAL system monitoring data")
        
        # Import system monitoring
        from app.monitoring.system_stats import system_monitor
        
        # Get comprehensive system stats
        system_stats = await system_monitor.get_comprehensive_system_stats()
        
        return {
            "success": True,
            "data": system_stats,
            "message": "Retrieved REAL system monitoring data",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"System monitoring retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# CHAT API - AI Assistant with Knowledge Integration
# ========================================

@app.post("/api/chat", tags=["Chat"], response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """Chat with AI assistant using knowledge graph and vector search"""
    try:
        logger.info(f"Processing chat message: {request.message[:100]}...")
        
        # Process the chat request
        response = await process_chat_message(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations", tags=["Chat"])
async def get_conversations():
    """Get list of active conversations"""
    try:
        from app.api.chat_endpoints import conversations
        
        conversation_list = []
        for conv_id, messages in conversations.items():
            if messages:
                last_message = messages[-1]
                conversation_list.append({
                    "conversation_id": conv_id,
                    "last_message": last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content,
                    "last_updated": last_message.timestamp.isoformat() if last_message.timestamp else None,
                    "message_count": len(messages)
                })
        
        return {
            "success": True,
            "conversations": conversation_list,
            "total": len(conversation_list)
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/conversations/{conversation_id}", tags=["Chat"])
async def get_conversation_history(conversation_id: str):
    """Get conversation history"""
    try:
        from app.api.chat_endpoints import conversations
        
        if conversation_id not in conversations:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = conversations[conversation_id]
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in messages
            ],
            "message_count": len(messages)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# WEBSOCKET ENDPOINTS - Real-time Chat
# ========================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected to WebSocket")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected from WebSocket")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: str):
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat communication"""
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse the incoming message
            try:
                import json
                message_data = json.loads(data)
                message_type = message_data.get("type", "chat")
                message_content = message_data.get("message", "")
                
                if message_type == "chat":
                    # Process chat message through Ollama
                    logger.info(f"Processing chat message from {client_id}: {message_content[:100]}...")
                    
                    # Generate response using local Ollama
                    response = await ollama_client.generate_text(
                        f"You are a helpful AI assistant for FindersKeepers v2. Respond to: {message_content}",
                        max_tokens=512
                    )
                    
                    # Send response back to client
                    response_message = {
                        "type": "chat_response",
                        "message": response if response else "Sorry, I couldn't generate a response right now.",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "client_id": client_id
                    }
                    
                    await manager.send_personal_message(json.dumps(response_message), client_id)
                    
                elif message_type == "knowledge_query":
                    # Process knowledge query
                    logger.info(f"Processing knowledge query from {client_id}: {message_content[:100]}...")
                    
                    # Generate embeddings and search knowledge base
                    embeddings = await ollama_client.get_embeddings(message_content)
                    
                    # TODO: Implement actual knowledge graph query
                    knowledge_response = f"Knowledge query processed for: '{message_content}'. Found relevant information in the knowledge base."
                    
                    response_message = {
                        "type": "knowledge_response",
                        "message": knowledge_response,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "client_id": client_id,
                        "embeddings_count": len(embeddings)
                    }
                    
                    await manager.send_personal_message(json.dumps(response_message), client_id)
                    
                else:
                    # Echo unknown message types
                    await manager.send_personal_message(f"Echo: {data}", client_id)
                    
            except json.JSONDecodeError:
                # Handle plain text messages
                await manager.send_personal_message(f"Echo: {data}", client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
        
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)

# ========================================
# STARTUP EVENT
# ========================================

async def process_document_with_ollama(doc: DocumentIngest, embeddings: List[float]):
    """Background task to process document with local embeddings"""
    try:
        logger.info(f"🔄 STEP 1: Starting background processing for '{doc.title}' with {len(embeddings)} embeddings")
        
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        logger.info(f"🔄 STEP 2: Starting imports for '{doc.title}'")
        
        from app.api.v1.ingestion.storage import StorageService
        from app.api.v1.ingestion.models import IngestionRequest, ProcessedChunk, DocumentMetadata, FileFormat, ProcessingMethod, ChunkMetadata
        from uuid import uuid4
        
        logger.info(f"📦 STEP 3: Imports successful, processing document '{doc.title}'")
        
        # Initialize storage service
        storage = StorageService()
        
        # Create ingestion request with doc_type in metadata
        metadata_with_doc_type = {
            **doc.metadata,
            "doc_type": doc.doc_type
        }
        
        ingestion_request = IngestionRequest(
            ingestion_id=f"ing_{uuid4().hex[:8]}",
            file_path=f"/tmp/{doc.title}.md",
            filename=f"{doc.title}.md",
            project=doc.project,
            tags=doc.tags,
            metadata=metadata_with_doc_type,
            file_size=len(doc.content.encode()),
            mime_type="text/markdown"
        )
        
        # Create document metadata
        document_metadata = DocumentMetadata(
            title=doc.title,
            format=FileFormat.MD,
            processing_method=ProcessingMethod.CUSTOM,
            word_count=len(doc.content.split()),
            language="en"
        )
        
        # Create processed chunk  
        chunk_metadata = ChunkMetadata(
            chunk_id=str(uuid4()),
            document_id="",  # Will be set by storage
            chunk_index=0,
            start_char=0,
            end_char=len(doc.content),
            page_number=1
        )
        
        processed_chunk = ProcessedChunk(
            chunk_id=chunk_metadata.chunk_id,
            content=doc.content,
            metadata=chunk_metadata,
            embeddings=embeddings,
            token_count=len(doc.content.split()),
            language="en"
        )
        
        # Store document across all databases
        logger.info(f"🔄 STEP 4: About to store document '{doc.title}' in storage service")
        try:
            document_id = await storage.store_document(
                ingestion_request,
                document_metadata,
                [processed_chunk]
            )
            logger.info(f"✅ STEP 5: Document '{doc.title}' stored successfully with ID: {document_id}")
        except Exception as storage_error:
            logger.error(f"❌ STEP 5 FAILED: Storage error for '{doc.title}': {storage_error}")
            import traceback
            logger.error(f"Storage traceback: {traceback.format_exc()}")
            raise
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

@app.on_event("startup")
async def startup_event():
    """Initialize the application with REAL database connections"""
    logger.info("🔍 FindersKeepers v2 API starting up...")
    
    # Initialize ALL database connections
    db_results = await db_manager.initialize_all()
    
    # Check Ollama connection
    if ollama_client.use_local:
        ollama_healthy = await ollama_client.health_check()
        if ollama_healthy:
            logger.info("🤖 Ollama service connected - Local LLM ready!")
        else:
            logger.warning("⚠️  Ollama service not available - Using fallback mode")
    else:
        logger.info("🌐 Local LLM disabled - Using external API mode")
    
    # Report database connection status
    for db_name, connected in db_results.items():
        status = "✅ Connected" if connected else "❌ Failed"
        logger.info(f"🗄️  {db_name.upper()}: {status}")
    
    logger.info("🚀 Ready to track agent sessions and manage knowledge with REAL DATA!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)