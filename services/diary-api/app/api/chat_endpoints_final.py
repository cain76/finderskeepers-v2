"""
Chat endpoints for FindersKeepers v2
"""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import HTTPException
import httpx

logger = logging.getLogger(__name__)

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    use_knowledge_graph: bool = Field(True, description="Whether to use knowledge graph context")
    use_vector_search: bool = Field(True, description="Whether to use vector search")
    model: str = Field("llama3.2:3b", description="LLM model to use")
    max_tokens: int = Field(1000, description="Maximum response tokens")

class ChatResponse(BaseModel):
    """Chat response model"""
    message: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Knowledge sources used")
    model_used: str = Field(..., description="LLM model used")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    tokens_used: int = Field(0, description="Tokens used in response")

# Global chat conversations storage (in production, use Redis or database)
conversations: Dict[str, List[ChatMessage]] = {}

async def generate_ollama_response(prompt: str, model: str = "llama3.2:3b") -> str:
    """Generate response using Ollama"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://fk2_ollama:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 4096,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "I'm sorry, I couldn't generate a response.")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "I'm experiencing technical difficulties. Please try again."
                
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")
        return "I'm currently unable to process your request. Please try again later."

async def search_knowledge_context(query: str) -> tuple[List[Dict[str, Any]], str]:
    """Search for relevant knowledge context"""
    sources = []
    context = ""
    
    # Mock knowledge search for now
    if "docker" in query.lower() or "container" in query.lower():
        sources.append({
            "type": "knowledge",
            "title": "Docker Infrastructure",
            "relevance": 0.9,
            "content": "FindersKeepers v2 uses Docker containers for microservices including FastAPI, PostgreSQL, Neo4j, Qdrant, Redis, and Ollama."
        })
        context = "\n\nKnowledge Context: FindersKeepers v2 runs on Docker with 7 microservices including FastAPI backend, PostgreSQL database, Neo4j knowledge graph, Qdrant vector database, Redis cache, and Ollama for local LLM inference."
    
    elif "system" in query.lower() or "monitoring" in query.lower():
        sources.append({
            "type": "knowledge", 
            "title": "System Monitoring",
            "relevance": 0.85,
            "content": "The system includes real-time monitoring of Docker containers, host system metrics, and performance analytics."
        })
        context = "\n\nKnowledge Context: FindersKeepers v2 includes comprehensive system monitoring with Docker container stats, host resource monitoring, and performance metrics tracking."
    
    elif "api" in query.lower() or "endpoint" in query.lower():
        sources.append({
            "type": "knowledge",
            "title": "API Endpoints", 
            "relevance": 0.8,
            "content": "The FastAPI backend provides endpoints for sessions, documents, vector search, knowledge queries, and system stats."
        })
        context = "\n\nKnowledge Context: FindersKeepers v2 FastAPI provides endpoints for: /api/stats/sessions, /api/stats/documents, /api/search/vector, /api/knowledge/query, and system monitoring."
    
    return sources, context

def format_conversation_history(conversation_id: str) -> str:
    """Format conversation history for context"""
    if conversation_id not in conversations:
        return ""
    
    history = conversations[conversation_id]
    if len(history) <= 1:  # Only current message
        return ""
    
    context = "\n\nConversation History:\n"
    for message in history[-4:]:  # Last 4 messages
        context += f"{message.role.title()}: {message.content}\n"
    
    return context

async def process_chat_message(request: ChatRequest) -> ChatResponse:
    """Process a chat message with knowledge integration"""
    start_time = datetime.now()
    
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize conversation history if needed
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Add user message to conversation
        user_message = ChatMessage(role="user", content=request.message)
        conversations[conversation_id].append(user_message)
        
        # Search for relevant knowledge context
        context_sources, knowledge_context = await search_knowledge_context(request.message)
        
        # Get conversation context
        conversation_context = format_conversation_history(conversation_id)
        
        # Prepare the prompt
        system_prompt = """You are a helpful AI assistant for FindersKeepers v2, a personal AI agent knowledge hub. You have access to the user's knowledge base and can help with questions about the system, Docker containers, APIs, and general assistance.

Be concise but comprehensive in your responses. If you reference specific information, mention your sources."""

        full_prompt = f"""{system_prompt}

{knowledge_context}

{conversation_context}

User: {request.message}