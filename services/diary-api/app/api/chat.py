"""
Chat API for FindersKeepers v2
Enables natural language interaction with knowledge graph and LLMs
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

class ChatService:
    """Service for handling chat interactions with knowledge and LLMs"""
    
    def __init__(self):
        self.ollama_base_url = "http://fk2_ollama:11434"
        self.conversations: Dict[str, List[ChatMessage]] = {}
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request with knowledge integration"""
        start_time = datetime.now()
        
        try:
            # Generate conversation ID if not provided
            conversation_id = request.conversation_id or f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize conversation history if needed
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            # Add user message to conversation
            user_message = ChatMessage(role="user", content=request.message)
            self.conversations[conversation_id].append(user_message)
            
            # Gather context from knowledge sources
            context_sources = []
            knowledge_context = ""
            
            if request.use_vector_search:
                vector_results = await self._search_vector_database(request.message)
                if vector_results:
                    context_sources.extend(vector_results)
                    knowledge_context += self._format_vector_context(vector_results)
            
            if request.use_knowledge_graph:
                graph_results = await self._query_knowledge_graph(request.message)
                if graph_results:
                    context_sources.extend(graph_results)
                    knowledge_context += self._format_graph_context(graph_results)
            
            # Prepare conversation context
            conversation_context = self._format_conversation_history(conversation_id)
            
            # Generate response using LLM
            assistant_response = await self._generate_llm_response(
                user_message=request.message,
                knowledge_context=knowledge_context,
                conversation_context=conversation_context,
                model=request.model,
                max_tokens=request.max_tokens
            )
            
            # Add assistant message to conversation
            assistant_message = ChatMessage(role="assistant", content=assistant_response)
            self.conversations[conversation_id].append(assistant_message)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ChatResponse(
                message=assistant_response,
                conversation_id=conversation_id,
                sources=context_sources,
                model_used=request.model,
                response_time_ms=response_time,
                tokens_used=len(assistant_response.split())  # Rough token estimate
            )
            
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")
    
    async def _search_vector_database(self, query: str) -> List[Dict[str, Any]]:
        """Search vector database for relevant documents"""
        try:
            # This would integrate with the existing vector search endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/search/vector",
                    json={"query": query, "limit": 3, "min_score": 0.7}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("results"):
                        return [
                            {
                                "type": "document",
                                "id": result.get("document_id"),
                                "title": result.get("metadata", {}).get("title", "Unknown"),
                                "relevance": result.get("score", 0),
                                "content": result.get("content", "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content", "")
                            }
                            for result in data["results"]
                        ]
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
        return []
    
    async def _query_knowledge_graph(self, query: str) -> List[Dict[str, Any]]:
        """Query knowledge graph for relevant entities and relationships"""
        try:
            # This would integrate with Neo4j knowledge graph
            # For now, return mock results
            return [
                {
                    "type": "entity",
                    "id": "entity_001",
                    "name": "FindersKeepers v2",
                    "type_name": "Project",
                    "relevance": 0.9,
                    "relationships": ["CONTAINS", "IMPLEMENTS", "USES"]
                }
            ]
        except Exception as e:
            logger.warning(f"Knowledge graph query failed: {e}")
        return []
    
    def _format_vector_context(self, results: List[Dict[str, Any]]) -> str:
        """Format vector search results as context"""
        if not results:
            return ""
        
        context = "\\n\\n**Relevant Documents:**\\n"
        for result in results:
            context += f"- **{result['title']}** (relevance: {result['relevance']:.2f})\\n"
            context += f"  {result['content']}\\n\\n"
        
        return context
    
    def _format_graph_context(self, results: List[Dict[str, Any]]) -> str:
        """Format knowledge graph results as context"""
        if not results:
            return ""
        
        context = "\\n\\n**Knowledge Graph Entities:**\\n"
        for result in results:
            context += f"- **{result['name']}** ({result['type_name']})\\n"
            context += f"  Relationships: {', '.join(result['relationships'])}\\n\\n"
        
        return context
    
    def _format_conversation_history(self, conversation_id: str) -> str:
        """Format conversation history for context"""
        if conversation_id not in self.conversations:
            return ""
        
        history = self.conversations[conversation_id]
        if len(history) <= 1:  # Only current message
            return ""
        
        context = "\\n\\n**Conversation History:**\\n"
        for message in history[-4:]:  # Last 4 messages
            context += f"{message.role.title()}: {message.content}\\n"
        
        return context
    
    async def _generate_llm_response(
        self, 
        user_message: str, 
        knowledge_context: str, 
        conversation_context: str,
        model: str,
        max_tokens: int
    ) -> str:
        """Generate response using local LLM"""
        try:
            # Prepare the prompt with context
            system_prompt = """You are a helpful AI assistant for FindersKeepers v2, a personal AI agent knowledge hub. You have access to the user's knowledge base including documents, session history, and entity relationships.

Use the provided context to give accurate, helpful responses. If you don't have enough information, say so clearly. Always be concise but comprehensive.

When referencing specific documents or data, mention your sources."""

            prompt = f"""{system_prompt}

{knowledge_context}

{conversation_context}

User: {user_message}