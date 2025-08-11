"""
Knowledge Graph API endpoints for FindersKeepers v2
Provides Neo4j graph search, entity relationships, and knowledge queries
"""

from fastapi import APIRouter, HTTPException, Query
from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# LLM configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://fk2_ollama:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3:8b")

class Neo4jService:
    """Service for Neo4j graph database operations"""
    
    def __init__(self):
        self.driver = None
    
    async def get_driver(self):
        """Get or create Neo4j driver"""
        if not self.driver:
            self.driver = AsyncGraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return self.driver
    
    async def close(self):
        """Close Neo4j driver"""
        if self.driver:
            await self.driver.close()
            self.driver = None

neo4j_service = Neo4jService()

@router.post("/search")
async def search_knowledge(request: dict):
    """
    Search knowledge graph using full-text search
    Returns top entities and documents matching the query
    """
    query = request.get("query", "")
    limit = request.get("limit", 10)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter required")
    
    logger.info(f"Knowledge graph search: {query}")
    
    try:
        driver = await neo4j_service.get_driver()
        
        async with driver.session() as session:
            # Try full-text search first
            result = await session.run("""
                CALL db.index.fulltext.queryNodes('entity_search', $search_term) 
                YIELD node, score
                WHERE score > 0.1
                RETURN node, score, labels(node) as labels
                ORDER BY score DESC
                LIMIT $limit
            """, search_term=query, limit=limit)
            
            nodes = []
            async for record in result:
                node_data = dict(record["node"])
                node_data["_labels"] = record["labels"]
                node_data["_score"] = record["score"]
                nodes.append(node_data)
            
            # If no full-text results, try pattern matching
            if not nodes:
                result = await session.run("""
                    MATCH (n)
                    WHERE n.name CONTAINS $search_term 
                       OR n.title CONTAINS $search_term 
                       OR n.content CONTAINS $search_term
                    RETURN n as node, 0.5 as score, labels(n) as labels
                    LIMIT $limit
                """, search_term=query, limit=limit)
                
                async for record in result:
                    node_data = dict(record["node"])
                    node_data["_labels"] = record["labels"]
                    node_data["_score"] = record["score"]
                    nodes.append(node_data)
        
        return {
            "success": True,
            "data": nodes,
            "query": query,
            "total": len(nodes),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/related/{document_id}")
async def get_related_documents(document_id: str):
    """
    Find documents related to a given document via shared entities
    """
    logger.info(f"Finding related documents for: {document_id}")
    
    try:
        driver = await neo4j_service.get_driver()
        
        async with driver.session() as session:
            result = await session.run("""
                MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(e:Entity)<-[:CONTAINS]-(related:Document)
                WHERE d.id <> related.id
                WITH related, COUNT(DISTINCT e) as connection_strength
                RETURN related, connection_strength
                ORDER BY connection_strength DESC
                LIMIT 10
            """, doc_id=document_id)
            
            related_docs = []
            async for record in result:
                doc_data = dict(record["related"])
                doc_data["connection_strength"] = record["connection_strength"]
                related_docs.append(doc_data)
        
        return {
            "success": True,
            "document_id": document_id,
            "related": related_docs,
            "total": len(related_docs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Related documents search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/{entity_id}/relationships")
async def get_entity_relationships(entity_id: str):
    """
    Get all relationships for a specific entity
    """
    logger.info(f"Getting relationships for entity: {entity_id}")
    
    try:
        driver = await neo4j_service.get_driver()
        
        async with driver.session() as session:
            # Get outgoing relationships
            outgoing_result = await session.run("""
                MATCH (e:Entity {id: $entity_id})-[r]->(target)
                RETURN type(r) as relationship_type, 
                       collect({
                           id: target.id,
                           name: target.name,
                           labels: labels(target)
                       }) as targets
            """, entity_id=entity_id)
            
            # Get incoming relationships
            incoming_result = await session.run("""
                MATCH (source)-[r]->(e:Entity {id: $entity_id})
                RETURN type(r) as relationship_type,
                       collect({
                           id: source.id,
                           name: source.name,
                           labels: labels(source)
                       }) as sources
            """, entity_id=entity_id)
            
            outgoing = {}
            async for record in outgoing_result:
                outgoing[record["relationship_type"]] = record["targets"]
            
            incoming = {}
            async for record in incoming_result:
                incoming[record["relationship_type"]] = record["sources"]
        
        return {
            "success": True,
            "entity_id": entity_id,
            "outgoing_relationships": outgoing,
            "incoming_relationships": incoming,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Entity relationships query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_knowledge_graph(request: dict):
    """
    Advanced knowledge graph query with QA capabilities
    Used by MCP server for knowledge_graph_search tool
    """
    question = request.get("question", "")
    project = request.get("project", "finderskeepers-v2")
    include_history = request.get("include_history", True)
    
    if not question:
        raise HTTPException(status_code=400, detail="Question parameter required")
    
    logger.info(f"Knowledge graph QA query: {question}")
    
    try:
        driver = await neo4j_service.get_driver()
        
        async with driver.session() as session:
            # Search for relevant entities and documents
            search_result = await session.run("""
                MATCH (n)
                WHERE (n.content CONTAINS $search_term 
                       OR n.name CONTAINS $search_term 
                       OR n.title CONTAINS $search_term)
                   AND (n.project = $project OR $project IS NULL)
                WITH n, 
                     CASE 
                        WHEN n.content CONTAINS $search_term THEN 2.0
                        WHEN n.title CONTAINS $search_term THEN 1.5
                        ELSE 1.0
                     END as relevance
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN n as node, 
                       labels(n) as labels,
                       relevance,
                       collect(DISTINCT {
                           type: type(r),
                           connected_to: connected.name,
                           connected_labels: labels(connected)
                       }) as relationships
                ORDER BY relevance DESC
                LIMIT 10
            """, search_term=question, project=project)
            
            sources = []
            context_nodes = []
            
            async for record in search_result:
                node_data = dict(record["node"])
                
                source = {
                    "type": record["labels"][0] if record["labels"] else "Unknown",
                    "id": node_data.get("id", "unknown"),
                    "relevance": record["relevance"],
                    "content": node_data.get("content", "")[:500],
                    "relationships": record["relationships"]
                }
                sources.append(source)
                context_nodes.append(node_data)
            
            # Generate answer using LLM based on sources
            if sources:
                # Build context from top sources
                context = "\n\n".join([
                    f"Source {i+1} ({s['type']}): {s['content']}"
                    for i, s in enumerate(sources[:3])
                ])

                prompt = (
                    "You are a helpful assistant answering questions based on a knowledge graph.\n"
                    f"Question: {question}\n\nContext:\n{context}\n\n"
                    "Provide a concise answer using only the given context."
                )

                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(
                            f"{OLLAMA_URL}/api/generate",
                            json={"model": CHAT_MODEL, "prompt": prompt, "stream": False},
                        )
                        data = response.json()
                        answer = data.get("response", "").strip()
                except Exception as e:
                    logger.error(f"LLM generation failed: {e}")
                    answer = "Unable to generate an answer from the model."

                confidence = min(1.0, sources[0]['relevance'] / 2.0)
            else:
                answer = (
                    f"No specific information found about '{question}' in the knowledge graph."
                )
                confidence = 0.0
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "question": question,
            "project": project,
            "model": CHAT_MODEL,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Knowledge graph query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.on_event("shutdown")
async def shutdown():
    """Clean up Neo4j connection on shutdown"""
    await neo4j_service.close()
