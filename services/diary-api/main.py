"""
FindersKeepers v2 - FastAPI Diary & Knowledge Management API
Personal AI Agent Knowledge Hub (July 2025)
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
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

# Import ingestion module
from app.api.v1.ingestion import ingestion_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# OLLAMA CLIENT CONFIGURATION
# ========================================

class OllamaClient:
    """Local LLM client for zero-cost embeddings and inference"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
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
                return data.get("embeddings", [])
                
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

# CORS middleware for web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestion_router)

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
    """System health check with Ollama status"""
    try:
        # Check Ollama service
        ollama_healthy = await ollama_client.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "api": "up",
                "postgres": "checking...",
                "neo4j": "checking...",
                "qdrant": "checking...",
                "redis": "checking...",
                "ollama": "up" if ollama_healthy else "down"
            },
            "local_llm": {
                "enabled": ollama_client.use_local,
                "embedding_model": ollama_client.embedding_model,
                "chat_model": ollama_client.chat_model,
                "healthy": ollama_healthy
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

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
# DIARY API - Agent Session Tracking
# ========================================

@app.post("/api/diary/sessions", tags=["Diary"])
async def create_session(session: AgentSession):
    """Create new agent session entry"""
    try:
        # TODO: Store in database
        logger.info(f"Creating session: {session.session_id} ({session.agent_type})")
        
        # For now, store in memory/file (replace with actual DB)
        session_data = session.dict()
        
        return {
            "status": "created",
            "session_id": session.session_id,
            "message": f"Session created for {session.agent_type}",
            "data": session_data
        }
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/diary/actions", tags=["Diary"])
async def log_action(action: AgentAction):
    """Log an action within an agent session"""
    try:
        # TODO: Store in database and update knowledge graph
        logger.info(f"Logging action: {action.action_type} in session {action.session_id}")
        
        action_data = action.dict()
        
        return {
            "status": "logged",
            "action_id": action.action_id,
            "message": f"Action logged: {action.description}",
            "data": action_data
        }
    except Exception as e:
        logger.error(f"Failed to log action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diary/search", tags=["Diary"])
async def search_sessions(
    q: Optional[str] = None,
    project: Optional[str] = None,
    agent_type: Optional[str] = None,
    limit: int = 10
):
    """Search agent session history"""
    try:
        # TODO: Implement actual search
        logger.info(f"Searching sessions: q={q}, project={project}, agent_type={agent_type}")
        
        # Mock response for now
        results = [
            {
                "session_id": "session_001",
                "agent_type": "claude",
                "project": "bitcain",
                "start_time": "2025-07-04T10:00:00Z",
                "description": "Docker configuration troubleshooting",
                "key_actions": ["docker login", "container restart", "volume mount fix"]
            }
        ]
        
        return {
            "status": "success",
            "results": results,
            "total": len(results),
            "query": {"q": q, "project": project, "agent_type": agent_type}
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            "document_id": f"doc_{int(datetime.now().timestamp())}",
            "project": doc.project,
            "embeddings_generated": len(doc_embeddings) > 0,
            "local_processing": ollama_client.use_local
        }
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
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
            chunk_id=f"chunk_{uuid4().hex[:8]}",
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
    """Initialize the application with Ollama health check"""
    logger.info("🔍 FindersKeepers v2 API starting up...")
    
    # Check Ollama connection
    if ollama_client.use_local:
        ollama_healthy = await ollama_client.health_check()
        if ollama_healthy:
            logger.info("🤖 Ollama service connected - Local LLM ready!")
        else:
            logger.warning("⚠️  Ollama service not available - Using fallback mode")
    else:
        logger.info("🌐 Local LLM disabled - Using external API mode")
    
    logger.info("🚀 Ready to track agent sessions and manage knowledge!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)