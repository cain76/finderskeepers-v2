#!/usr/bin/env python3
"""
Simple Context7 Documentation Ingestion Script for FindersKeepers v2
"""

import asyncio
import logging
from datetime import datetime

import httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def ingest_document(title: str, content: str, tags: list):
    """Ingest a single document."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "filename": f"{title.lower().replace(' ', '_').replace('/', '_')}.md",
            "content": content,
            "project": "finderskeepers-v2",
            "tags": tags,
            "metadata": {
                "doc_type": "technology_documentation",
                "source": "context7_mcp_ingestion", 
                "ingestion_date": datetime.utcnow().isoformat(),
                "technology": title
            }
        }
        
        try:
            response = await client.post(
                "http://localhost:8000/api/docs/ingest",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully ingested: {title}")
                return True
            else:
                logger.error(f"❌ Failed to ingest {title}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception ingesting {title}: {e}")
            return False

async def main():
    """Main execution function."""
    logger.info("🚀 Starting Context7 Documentation Ingestion")
    
    # Check FastAPI health
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code != 200:
                logger.error("❌ FastAPI service not healthy")
                return
    except Exception as e:
        logger.error(f"❌ Cannot connect to FastAPI: {e}")
        return
    
    # FastAPI Documentation
    fastapi_content = """# FastAPI Framework Documentation for FindersKeepers v2

## Overview
FastAPI serves as the core backend API framework for FindersKeepers v2, providing high-performance REST endpoints for agent session tracking, knowledge queries, and document management.

## Key Integration Patterns for FindersKeepers v2

### Dependency Injection Setup
```python
from fastapi import Depends, FastAPI
from typing import Annotated

# Database dependency
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Usage in endpoints
@app.post("/api/diary/sessions")
async def create_session(
    session_data: SessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Implementation
    pass
```

### Core Endpoint Patterns
- **POST /api/diary/sessions**: Create new agent sessions
- **POST /api/diary/actions**: Log agent actions with file tracking  
- **GET /api/diary/search**: Search session history
- **POST /api/knowledge/query**: Natural language queries
- **POST /api/docs/ingest**: Document ingestion with embeddings

### Async Programming Best Practices
1. Always use async/await for database operations
2. Implement proper dependency injection
3. Use Pydantic models for validation
4. Handle exceptions with proper HTTP status codes
5. Use background tasks for heavy operations

This provides the essential FastAPI patterns for FindersKeepers v2 architecture.
"""

    # Neo4j Documentation  
    neo4j_content = """# Neo4j Graph Database Documentation for FindersKeepers v2

## Overview
Neo4j serves as the knowledge graph database in FindersKeepers v2, storing entity relationships, semantic links between documents and agent sessions, and enabling powerful graph-based queries.

## Python Driver Integration

### Connection Setup
```python
from neo4j import AsyncGraphDatabase

class Neo4jManager:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def execute_query(self, query: str, parameters: dict = None):
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]
```

### Agent Session Tracking
```python
# Create agent session node
async def create_agent_session(neo4j: Neo4jManager, session_data: dict):
    query = '''
    CREATE (s:AgentSession {
        session_id: $session_id,
        user_id: $user_id,
        project: $project,
        agent_type: $agent_type,
        created_at: datetime($created_at)
    })
    RETURN s
    '''
    return await neo4j.execute_query(query, session_data)
```

### Knowledge Discovery Queries
```python
# Find related documents through entity connections
async def find_related_documents(neo4j: Neo4jManager, doc_id: str):
    query = '''
    MATCH (source:Document {doc_id: $doc_id})
    MATCH (source)<-[:MENTIONED_IN]-(entity:Entity)-[:MENTIONED_IN]->(related:Document)
    WHERE related.doc_id <> $doc_id
    RETURN related.doc_id as doc_id, 
           related.title as title,
           collect(entity.name) as shared_entities
    ORDER BY size(shared_entities) DESC
    LIMIT 10
    '''
    return await neo4j.execute_query(query, {"doc_id": doc_id})
```

## Best Practices for FindersKeepers v2
1. Use parameterized queries to prevent Cypher injection
2. Implement proper indexes for frequently queried properties
3. Use MERGE for upsert operations
4. Use async patterns for FastAPI integration
5. Monitor query performance with PROFILE

This provides essential Neo4j patterns for FindersKeepers v2 knowledge graph architecture.
"""

    # Qdrant Documentation
    qdrant_content = """# Qdrant Vector Database Documentation for FindersKeepers v2

## Overview
Qdrant serves as the high-performance vector database in FindersKeepers v2, optimized for semantic search, document retrieval, and similarity operations.

## Python Client Integration

### Connection Setup
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class QdrantManager:
    def __init__(self, url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.collections = {
            "documents": "finderskeepers_documents",
            "sessions": "finderskeepers_sessions"
        }
    
    async def ensure_collections(self):
        '''Ensure collections exist with proper configuration.'''
        for name, collection_name in self.collections.items():
            collections = self.client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if collection_name not in existing:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
```

### Document Ingestion Pipeline
```python
async def ingest_document(self, doc_id: str, content: str, metadata: dict):
    '''Ingest document with chunking and vector generation.'''
    
    # Generate embedding
    embedding = await self.embedding_service.generate(content)
    
    point = PointStruct(
        id=doc_id,
        vector=embedding,
        payload={
            "doc_id": doc_id,
            "content": content,
            "project": metadata.get("project", "finderskeepers-v2"),
            "title": metadata.get("title", ""),
            "tags": metadata.get("tags", [])
        }
    )
    
    self.client.upsert(
        collection_name=self.collections["documents"],
        points=[point]
    )
```

### Semantic Search Implementation
```python
async def search_documents(self, query: str, project: str = None, limit: int = 10):
    '''Perform semantic search across document collection.'''
    
    query_embedding = await self.embedding_service.generate(query)
    
    # Build filter conditions
    search_filter = None
    if project:
        search_filter = {
            "must": [{
                "key": "project",
                "match": {"value": project}
            }]
        }
    
    # Perform search
    search_results = self.client.search(
        collection_name=self.collections["documents"],
        query_vector=query_embedding,
        query_filter=search_filter,
        limit=limit,
        score_threshold=0.7,
        with_payload=True
    )
    
    return [
        {
            "doc_id": result.payload["doc_id"],
            "title": result.payload.get("title", ""),
            "score": result.score,
            "content": result.payload["content"][:200] + "..."
        }
        for result in search_results
    ]
```

## Best Practices for FindersKeepers v2
1. Use appropriate vector dimensions for content types
2. Implement proper chunking for long documents
3. Use payload indexes for fast filtering
4. Batch operations for better performance
5. Monitor collection sizes and optimize regularly

This provides comprehensive Qdrant integration patterns for FindersKeepers v2 vector search architecture.
"""

    # Documentation entries to ingest
    docs = [
        {
            "title": "FastAPI Framework for FindersKeepers v2",
            "content": fastapi_content,
            "tags": ["finderskeepers-v2", "fastapi", "backend", "api", "python", "async", "tech-stack", "documentation", "context7"]
        },
        {
            "title": "Neo4j Graph Database for FindersKeepers v2", 
            "content": neo4j_content,
            "tags": ["finderskeepers-v2", "neo4j", "graph-database", "cypher", "knowledge-graph", "python-driver", "tech-stack", "documentation", "context7"]
        },
        {
            "title": "Qdrant Vector Database for FindersKeepers v2",
            "content": qdrant_content, 
            "tags": ["finderskeepers-v2", "qdrant", "vector-database", "similarity-search", "embeddings", "semantic-search", "tech-stack", "documentation", "context7"]
        }
    ]
    
    # Ingest each document
    success_count = 0
    for doc in docs:
        success = await ingest_document(doc["title"], doc["content"], doc["tags"])
        if success:
            success_count += 1
        await asyncio.sleep(1)
    
    # Print summary
    logger.info(f"\n📊 Ingestion Summary: {success_count}/{len(docs)} documents successful")
    logger.info("🎉 Context7 documentation ingestion completed!")

if __name__ == "__main__":
    asyncio.run(main())