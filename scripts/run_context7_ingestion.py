#!/usr/bin/env python3
"""
FindersKeepers v2 Context7 Knowledge Base Ingestion Script

This script ingests the curated Context7 documentation directly into the 
FindersKeepers v2 knowledge base using the actual Context7 documentation
retrieved via MCP.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FindersKeepersIngester:
    """Ingests documentation into FindersKeepers v2 knowledge base."""
    
    def __init__(self):
        self.fastapi_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=60.0)
        self.success_count = 0
        self.failure_count = 0
    
    async def check_fastapi_health(self) -> bool:
        """Check if FastAPI service is running."""
        try:
            response = await self.client.get(f"{self.fastapi_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"FastAPI health check failed: {e}")
            return False
    
    async def ingest_document(self, title: str, content: str, tags: List[str], 
                            project: str = "finderskeepers-v2") -> bool:
        """Ingest a document into the knowledge base via FastAPI."""
        try:
            payload = {
                "filename": f"{title.lower().replace(' ', '_').replace('/', '_')}.md",
                "content": content,
                "project": project,
                "tags": tags,
                "metadata": {
                    "doc_type": "technology_documentation",
                    "source": "context7_mcp_ingestion", 
                    "ingestion_date": datetime.utcnow().isoformat(),
                    "technology": title
                }
            }
            
            response = await self.client.post(
                f"{self.fastapi_url}/api/docs/ingest",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully ingested: {title}")
                self.success_count += 1
                return True
            else:
                logger.error(f"❌ Failed to ingest {title}: {response.status_code} - {response.text}")
                self.failure_count += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception ingesting {title}: {e}")
            self.failure_count += 1
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

async def main():
    """Main execution function."""
    logger.info("🚀 Starting FindersKeepers v2 Context7 Documentation Ingestion")
    
    ingester = FindersKeepersIngester()
    
    try:
        # Check if FastAPI is running
        if not await ingester.check_fastapi_health():
            logger.error("❌ FastAPI service is not accessible. Please start the service first.")
            return
        
        # Curated documentation entries from Context7
        documentation_entries = [
            {
                "title": "FastAPI Framework for FindersKeepers v2",
                "content": """# FastAPI Framework Documentation for FindersKeepers v2

## Overview
FastAPI is the core backend API framework for FindersKeepers v2, providing high-performance REST endpoints for agent session tracking, knowledge queries, and document management.

## Key Features for Our Architecture
- **Async/Await Support**: Perfect for I/O-bound operations with PostgreSQL, Neo4j, Redis, and Qdrant
- **Dependency Injection**: Enables clean separation of concerns and easy testing
- **Automatic OpenAPI Documentation**: Self-documenting APIs for agent interaction
- **Type Safety**: Pydantic integration ensures data validation

## FindersKeepers v2 Implementation Patterns

### Core Dependency Injection
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

# Neo4j dependency  
async def get_neo4j_session():
    driver = get_neo4j_driver()
    async with driver.session() as session:
        yield session

# Usage in endpoints
@app.post("/api/diary/sessions")
async def create_session(
    session_data: SessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    neo4j: Annotated[AsyncSession, Depends(get_neo4j_session)]
):
    # Implementation
    pass
```

### Async Endpoint Patterns
```python
@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/api/knowledge/query")
async def knowledge_query(
    query: KnowledgeQuery,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Async database operations
    results = await db.execute(query_stmt)
    return results
```

### Background Tasks Integration
```python
from fastapi import BackgroundTasks

@app.post("/api/docs/ingest")
async def ingest_document(
    document: DocumentCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Immediate response
    doc_id = await create_document_record(db, document)
    
    # Background processing
    background_tasks.add_task(process_embeddings, doc_id)
    background_tasks.add_task(update_neo4j_graph, doc_id)
    
    return {"doc_id": doc_id, "status": "processing"}
```

## FindersKeepers v2 Specific Usage

### Agent Session Management
- **POST /api/diary/sessions**: Create new agent sessions
- **POST /api/diary/actions**: Log agent actions with file tracking
- **GET /api/diary/search**: Search session history with vector similarity

### Knowledge Management  
- **POST /api/knowledge/query**: Natural language queries against Neo4j graph
- **POST /api/docs/ingest**: Document ingestion with automatic embedding
- **GET /api/docs/context**: Project-specific context retrieval

### Configuration Tracking
- **POST /api/config/log-change**: Log configuration changes with rollback
- **GET /api/config/history**: Retrieve change history

## Integration with FindersKeepers v2 Stack

### PostgreSQL + pgvector
```python
# Vector similarity search
@app.get("/api/docs/search")
async def search_documents(
    query: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Use pgvector for semantic search
    embedding = await generate_embedding(query)
    
    stmt = select(Document).where(
        Document.embedding.cosine_distance(embedding) < 0.3
    ).limit(10)
    
    results = await db.execute(stmt)
    return results.scalars().all()
```

### Neo4j Integration
```python
# Knowledge graph queries
@app.post("/api/knowledge/graph-query") 
async def graph_query(
    query: str,
    neo4j: Annotated[AsyncSession, Depends(get_neo4j_session)]
):
    cypher = "MATCH (n)-[r]->(m) WHERE n.name = $query RETURN n, r, m"
    result = await neo4j.run(cypher, query=query)
    return [record.data() for record in result]
```

### Redis Caching
```python
# Session caching
@app.middleware("http")
async def add_redis_cache(request: Request, call_next):
    redis_client = request.app.state.redis
    cache_key = f"session:{request.headers.get('session-id')}"
    
    cached = await redis_client.get(cache_key)
    if cached:
        return JSONResponse(content=json.loads(cached))
    
    response = await call_next(request)
    await redis_client.setex(cache_key, 300, response.body)
    return response
```

## Best Practices for FindersKeepers v2

1. **Always use async/await** for database operations
2. **Implement proper dependency injection** for database connections
3. **Use Pydantic models** for request/response validation
4. **Handle exceptions gracefully** with proper HTTP status codes
5. **Log all agent actions** for session tracking
6. **Use background tasks** for heavy operations like embedding generation

## Error Handling Patterns
```python
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

@app.post("/api/sessions")
async def create_session(session_data: SessionCreate):
    try:
        result = await db_operation(session_data)
        return result
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Session already exists")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Performance Considerations
- Use connection pooling for database connections
- Implement proper caching strategies with Redis
- Use background tasks for non-critical operations
- Monitor endpoint performance with metrics
- Implement rate limiting for public endpoints

This documentation provides the essential FastAPI patterns and practices specifically tailored for the FindersKeepers v2 architecture and tech stack.
""",
                "tags": ["finderskeepers-v2", "fastapi", "backend", "api", "python", "async", "rest", "tech-stack", "documentation", "context7"]
            },
            
            {
                "title": "Neo4j Graph Database for FindersKeepers v2",
                "content": """# Neo4j Graph Database Documentation for FindersKeepers v2

## Overview
Neo4j serves as the knowledge graph database in FindersKeepers v2, storing entity relationships, semantic links between documents and agent sessions, and enabling powerful graph-based queries for knowledge discovery.

## Role in FindersKeepers v2 Architecture
- **Knowledge Graph**: Stores relationships between entities, documents, and sessions
- **Semantic Linking**: Connects related concepts across agent interactions
- **Graph Queries**: Enables complex relationship-based searches
- **Context Discovery**: Finds related information through graph traversal

## Python Driver Integration

### Connection Setup
```python
from neo4j import GraphDatabase, AsyncGraphDatabase
import asyncio

# For FindersKeepers v2 async architecture
class Neo4jManager:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def close(self):
        await self.driver.close()
    
    async def execute_query(self, query: str, parameters: dict = None):
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]

# Usage in FastAPI dependency
async def get_neo4j_session():
    neo4j_manager = Neo4jManager(
        uri="bolt://localhost:7687",
        user="neo4j", 
        password="fk2025neo4j"
    )
    try:
        yield neo4j_manager
    finally:
        await neo4j_manager.close()
```

### Agent Session Tracking
```python
# Create agent session node
async def create_agent_session(neo4j: Neo4jManager, session_data: dict):
    query = """
    CREATE (s:AgentSession {
        session_id: $session_id,
        user_id: $user_id,
        project: $project,
        agent_type: $agent_type,
        created_at: datetime($created_at),
        context: $context
    })
    RETURN s
    """
    return await neo4j.execute_query(query, session_data)

# Link session to documents
async def link_session_document(neo4j: Neo4jManager, session_id: str, doc_id: str, relationship_type: str):
    query = """
    MATCH (s:AgentSession {session_id: $session_id})
    MATCH (d:Document {doc_id: $doc_id})
    CREATE (s)-[r:INTERACTED_WITH {type: $rel_type, timestamp: datetime()}]->(d)
    RETURN r
    """
    return await neo4j.execute_query(query, {
        "session_id": session_id,
        "doc_id": doc_id, 
        "rel_type": relationship_type
    })
```

### Knowledge Entity Management
```python
# Create knowledge entities from documents
async def create_knowledge_entity(neo4j: Neo4jManager, entity_data: dict):
    query = """
    MERGE (e:Entity {name: $name, type: $entity_type})
    ON CREATE SET 
        e.created_at = datetime(),
        e.description = $description,
        e.confidence = $confidence
    ON MATCH SET
        e.updated_at = datetime(),
        e.confidence = CASE 
            WHEN $confidence > e.confidence THEN $confidence 
            ELSE e.confidence 
        END
    RETURN e
    """
    return await neo4j.execute_query(query, entity_data)

# Link entities to documents
async def link_entity_document(neo4j: Neo4jManager, entity_name: str, doc_id: str, relation_type: str):
    query = """
    MATCH (e:Entity {name: $entity_name})
    MATCH (d:Document {doc_id: $doc_id})
    MERGE (e)-[r:MENTIONED_IN {type: $relation_type}]->(d)
    ON CREATE SET r.created_at = datetime(), r.count = 1
    ON MATCH SET r.count = r.count + 1, r.updated_at = datetime()
    RETURN r
    """
    return await neo4j.execute_query(query, {
        "entity_name": entity_name,
        "doc_id": doc_id,
        "relation_type": relation_type
    })
```

### Relationship Discovery Queries
```python
# Find related documents through entity connections
async def find_related_documents(neo4j: Neo4jManager, doc_id: str, max_depth: int = 2):
    query = """
    MATCH (source:Document {doc_id: $doc_id})
    MATCH (source)<-[:MENTIONED_IN]-(entity:Entity)-[:MENTIONED_IN]->(related:Document)
    WHERE related.doc_id <> $doc_id
    RETURN related.doc_id as doc_id, 
           related.title as title,
           collect(entity.name) as shared_entities,
           count(entity) as entity_count
    ORDER BY entity_count DESC
    LIMIT 10
    """
    return await neo4j.execute_query(query, {"doc_id": doc_id})

# Find knowledge patterns across sessions
async def find_session_patterns(neo4j: Neo4jManager, user_id: str):
    query = """
    MATCH (u:User {user_id: $user_id})-[:OWNS]->(s:AgentSession)
    MATCH (s)-[:INTERACTED_WITH]->(d:Document)<-[:MENTIONED_IN]-(e:Entity)
    RETURN e.name as entity,
           e.type as entity_type,
           count(DISTINCT s) as session_count,
           count(DISTINCT d) as document_count,
           collect(DISTINCT s.session_id)[..5] as recent_sessions
    ORDER BY session_count DESC, document_count DESC
    LIMIT 20
    """
    return await neo4j.execute_query(query, {"user_id": user_id})
```

### Context Graph Queries
```python
# Get comprehensive context for an agent session
async def get_session_context(neo4j: Neo4jManager, session_id: str):
    query = """
    MATCH (s:AgentSession {session_id: $session_id})
    OPTIONAL MATCH (s)-[:INTERACTED_WITH]->(d:Document)
    OPTIONAL MATCH (d)<-[:MENTIONED_IN]-(e:Entity)
    OPTIONAL MATCH (e)-[:MENTIONED_IN]->(related_docs:Document)
    WHERE related_docs <> d
    
    RETURN s.session_id as session_id,
           s.project as project,
           s.agent_type as agent_type,
           collect(DISTINCT d.title) as documents_accessed,
           collect(DISTINCT e.name) as entities_discovered,
           collect(DISTINCT related_docs.title) as suggested_documents
    """
    return await neo4j.execute_query(query, {"session_id": session_id})

# Find knowledge gaps and opportunities
async def find_knowledge_gaps(neo4j: Neo4jManager, project: str):
    query = """
    MATCH (s:AgentSession {project: $project})-[:INTERACTED_WITH]->(d:Document)
    MATCH (d)<-[:MENTIONED_IN]-(e:Entity)
    
    // Find entities with low connection counts (potential gaps)
    WITH e, count(DISTINCT d) as doc_count, count(DISTINCT s) as session_count
    WHERE doc_count < 3 OR session_count < 2
    
    RETURN e.name as entity,
           e.type as entity_type,
           e.description as description,
           doc_count,
           session_count,
           CASE 
             WHEN doc_count < 2 THEN 'Under-documented'
             WHEN session_count < 2 THEN 'Rarely-accessed'
             ELSE 'Normal'
           END as gap_type
    ORDER BY doc_count ASC, session_count ASC
    LIMIT 15
    """
    return await neo4j.execute_query(query, {"project": project})
```

## Integration with FindersKeepers v2 Components

### PostgreSQL Synchronization
```python
# Sync entity references between Neo4j and PostgreSQL
async def sync_entity_references(neo4j: Neo4jManager, db_session):
    # Get entities from Neo4j
    neo4j_entities = await neo4j.execute_query("""
        MATCH (e:Entity)
        RETURN e.name as name, e.type as type, e.confidence as confidence
    """)
    
    # Update PostgreSQL entity_references table
    for entity in neo4j_entities:
        await db_session.execute(
            text("""
                INSERT INTO entity_references (name, type, confidence, source)
                VALUES (:name, :type, :confidence, 'neo4j')
                ON CONFLICT (name, type) DO UPDATE SET
                    confidence = GREATEST(entity_references.confidence, :confidence),
                    updated_at = NOW()
            """),
            entity
        )
    await db_session.commit()
```

### Qdrant Vector Integration
```python
# Create knowledge graph embeddings for vector search
async def create_graph_embeddings(neo4j: Neo4jManager, qdrant_client):
    # Get entity relationships as text
    relationships = await neo4j.execute_query("""
        MATCH (e1:Entity)-[r]->(e2:Entity)
        RETURN e1.name + ' ' + type(r) + ' ' + e2.name as relationship_text,
               e1.name as source_entity,
               e2.name as target_entity,
               type(r) as relationship_type
    """)
    
    # Generate embeddings and store in Qdrant
    for rel in relationships:
        embedding = await generate_embedding(rel['relationship_text'])
        
        await qdrant_client.upsert(
            collection_name="knowledge_graph",
            points=[{
                "id": f"{rel['source_entity']}_{rel['relationship_type']}_{rel['target_entity']}",
                "vector": embedding,
                "payload": {
                    "source_entity": rel['source_entity'],
                    "target_entity": rel['target_entity'],
                    "relationship_type": rel['relationship_type'],
                    "relationship_text": rel['relationship_text']
                }
            }]
        )
```

## Performance Optimization for FindersKeepers v2

### Query Optimization
```python
# Optimized queries with proper indexing
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_session_id ON :AgentSession(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_document_id ON :Document(doc_id)", 
    "CREATE INDEX IF NOT EXISTS idx_entity_name ON :Entity(name)",
    "CREATE INDEX IF NOT EXISTS idx_entity_type ON :Entity(type)",
    "CREATE INDEX IF NOT EXISTS idx_project ON :AgentSession(project)"
]

async def create_indexes(neo4j: Neo4jManager):
    for index_query in INDEXES:
        await neo4j.execute_query(index_query)
```

### Connection Pool Management
```python
class Neo4jPool:
    def __init__(self, uri: str, auth: tuple, max_connections: int = 100):
        self.driver = AsyncGraphDatabase.driver(
            uri, 
            auth=auth,
            max_connection_lifetime=30 * 60,  # 30 minutes
            max_connection_pool_size=max_connections,
            connection_acquisition_timeout=60
        )
    
    async def get_session(self):
        return self.driver.session()
```

## Best Practices for FindersKeepers v2

1. **Use parameterized queries** to prevent Cypher injection
2. **Implement proper indexes** for frequently queried properties
3. **Use MERGE for upsert operations** to avoid duplicates
4. **Batch operations** when possible for better performance
5. **Monitor query performance** with PROFILE keyword
6. **Use async patterns** to integrate with FastAPI
7. **Implement proper error handling** for connection failures
8. **Regular backup** of graph data for disaster recovery

This documentation provides the essential Neo4j patterns specifically designed for the FindersKeepers v2 knowledge graph architecture.
""",
                "tags": ["finderskeepers-v2", "neo4j", "graph-database", "cypher", "relationships", "knowledge-graph", "python-driver", "tech-stack", "documentation", "context7"]
            },
            
            {
                "title": "Qdrant Vector Database for FindersKeepers v2", 
                "content": """# Qdrant Vector Database Documentation for FindersKeepers v2

## Overview
Qdrant serves as the high-performance vector database in FindersKeepers v2, optimized for semantic search, document retrieval, and similarity operations across our knowledge base.

## Role in FindersKeepers v2 Architecture
- **Semantic Search**: Fast similarity search across document embeddings
- **Document Retrieval**: Context-aware document discovery for agent queries
- **Similarity Operations**: Finding related content based on vector similarity
- **Knowledge Discovery**: Enabling AI-powered content recommendations

## Python Client Integration

### Connection Setup
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import asyncio

class QdrantManager:
    def __init__(self, url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.collections = {
            "documents": "finderskeepers_documents",
            "sessions": "finderskeepers_sessions", 
            "entities": "finderskeepers_entities",
            "knowledge_graph": "finderskeepers_graph"
        }
    
    async def ensure_collections(self):
        """Ensure all required collections exist with proper configuration."""
        for name, collection_name in self.collections.items():
            await self._create_collection_if_not_exists(collection_name, name)
    
    async def _create_collection_if_not_exists(self, collection_name: str, collection_type: str):
        """Create collection with appropriate vector configuration."""
        try:
            collections = self.client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if collection_name not in existing:
                # Different vector dimensions for different content types
                vector_config = {
                    "documents": VectorParams(size=1536, distance=Distance.COSINE),  # OpenAI embeddings
                    "sessions": VectorParams(size=768, distance=Distance.COSINE),    # Session context
                    "entities": VectorParams(size=384, distance=Distance.COSINE),    # Entity embeddings  
                    "knowledge_graph": VectorParams(size=1024, distance=Distance.COSINE)  # Graph relationships
                }
                
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=vector_config.get(collection_type, vector_config["documents"])
                )
                
                # Create indexes for better performance
                await self._setup_collection_indexes(collection_name, collection_type)
                
        except Exception as e:
            print(f"Error creating collection {collection_name}: {e}")
```

### Document Ingestion Pipeline
```python
class DocumentVectorizer:
    def __init__(self, qdrant_manager: QdrantManager, embedding_service):
        self.qdrant = qdrant_manager
        self.embedding_service = embedding_service
    
    async def ingest_document(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Ingest document with chunking and vector generation."""
        
        # Chunk document for better retrieval
        chunks = await self._chunk_document(content, chunk_size=512, overlap=50)
        
        points = []
        for i, chunk in enumerate(chunks):
            # Generate embedding for chunk
            embedding = await self.embedding_service.generate(chunk)
            
            point = PointStruct(
                id=f"{doc_id}_chunk_{i}",
                vector=embedding,
                payload={
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "content": chunk,
                    "project": metadata.get("project", "finderskeepers-v2"),
                    "doc_type": metadata.get("doc_type", "document"),
                    "title": metadata.get("title", ""),
                    "tags": metadata.get("tags", []),
                    "ingestion_date": metadata.get("ingestion_date"),
                    "source": metadata.get("source", "unknown"),
                    "chunk_type": "content"
                }
            )
            points.append(point)
        
        # Batch upsert for better performance
        await self._batch_upsert(
            collection_name=self.qdrant.collections["documents"],
            points=points
        )
        
        # Create document-level embedding for high-level similarity
        doc_summary = await self._generate_document_summary(content)
        doc_embedding = await self.embedding_service.generate(doc_summary)
        
        doc_point = PointStruct(
            id=f"{doc_id}_summary",
            vector=doc_embedding,
            payload={
                "doc_id": doc_id,
                "chunk_index": -1,  # Indicates document summary
                "content": doc_summary,
                "project": metadata.get("project"),
                "doc_type": metadata.get("doc_type"),
                "title": metadata.get("title"),
                "tags": metadata.get("tags", []),
                "chunk_type": "summary"
            }
        )
        
        self.qdrant.client.upsert(
            collection_name=self.qdrant.collections["documents"],
            points=[doc_point]
        )
        
        return {"doc_id": doc_id, "chunks_created": len(chunks), "status": "success"}
```

### Semantic Search Implementation
```python
class SemanticSearchEngine:
    def __init__(self, qdrant_manager: QdrantManager, embedding_service):
        self.qdrant = qdrant_manager
        self.embedding_service = embedding_service
    
    async def search_documents(
        self, 
        query: str, 
        project: str = None,
        doc_types: List[str] = None,
        tags: List[str] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across document collection."""
        
        # Generate query embedding
        query_embedding = await self.embedding_service.generate(query)
        
        # Build filter conditions
        filter_conditions = []
        
        if project:
            filter_conditions.append({
                "key": "project",
                "match": {"value": project}
            })
        
        if doc_types:
            filter_conditions.append({
                "key": "doc_type", 
                "match": {"any": doc_types}
            })
        
        if tags:
            filter_conditions.append({
                "key": "tags",
                "match": {"any": tags}
            })
        
        # Construct filter
        search_filter = None
        if filter_conditions:
            search_filter = {
                "must": filter_conditions
            }
        
        # Perform search
        search_results = self.qdrant.client.search(
            collection_name=self.qdrant.collections["documents"],
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False
        )
        
        # Process and rank results
        results = []
        for result in search_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "doc_id": result.payload["doc_id"],
                "title": result.payload.get("title", ""),
                "content": result.payload["content"],
                "chunk_index": result.payload["chunk_index"],
                "chunk_type": result.payload["chunk_type"],
                "tags": result.payload.get("tags", []),
                "doc_type": result.payload.get("doc_type", ""),
                "source": result.payload.get("source", "")
            })
        
        return results
    
    async def find_similar_documents(
        self, 
        doc_id: str, 
        limit: int = 5,
        exclude_self: bool = True
    ) -> List[Dict[str, Any]]:
        """Find documents similar to the given document."""
        
        # Get the document summary vector
        doc_vector_result = self.qdrant.client.retrieve(
            collection_name=self.qdrant.collections["documents"],
            ids=[f"{doc_id}_summary"],
            with_vectors=True
        )
        
        if not doc_vector_result:
            return []
        
        doc_vector = doc_vector_result[0].vector
        
        # Build filter to exclude self if requested
        search_filter = None
        if exclude_self:
            search_filter = {
                "must_not": [
                    {
                        "key": "doc_id",
                        "match": {"value": doc_id}
                    }
                ]
            }
        
        # Search for similar documents (summary vectors only)
        similar_docs = self.qdrant.client.search(
            collection_name=self.qdrant.collections["documents"],
            query_vector=doc_vector,
            query_filter={
                "must": [
                    {
                        "key": "chunk_type",
                        "match": {"value": "summary"}
                    }
                ] + (search_filter["must_not"] if search_filter else [])
            },
            limit=limit,
            with_payload=True
        )
        
        return [
            {
                "doc_id": result.payload["doc_id"],
                "title": result.payload.get("title", ""),
                "score": result.score,
                "tags": result.payload.get("tags", []),
                "doc_type": result.payload.get("doc_type", "")
            }
            for result in similar_docs
        ]
```

### Agent Session Context Management
```python
class SessionContextManager:
    def __init__(self, qdrant_manager: QdrantManager, embedding_service):
        self.qdrant = qdrant_manager
        self.embedding_service = embedding_service
    
    async def create_session_context_vector(
        self, 
        session_id: str, 
        session_data: Dict[str, Any]
    ):
        """Create vector representation of agent session context."""
        
        # Generate context text from session data
        context_text = self._generate_session_context_text(session_data)
        context_embedding = await self.embedding_service.generate(context_text)
        
        session_point = PointStruct(
            id=session_id,
            vector=context_embedding,
            payload={
                "session_id": session_id,
                "user_id": session_data.get("user_id"),
                "project": session_data.get("project", "finderskeepers-v2"),
                "agent_type": session_data.get("agent_type", "claude"),
                "context_text": context_text,
                "session_start": session_data.get("session_start"),
                "last_activity": session_data.get("last_activity"),
                "document_ids": session_data.get("document_ids", []),
                "action_count": session_data.get("action_count", 0),
                "session_type": "agent_session"
            }
        )
        
        self.qdrant.client.upsert(
            collection_name=self.qdrant.collections["sessions"],
            points=[session_point]
        )
    
    async def find_relevant_context(
        self, 
        current_query: str, 
        session_id: str = None,
        user_id: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant context from previous sessions and documents."""
        
        query_embedding = await self.embedding_service.generate(current_query)
        
        # Search across both documents and sessions
        results = []
        
        # Search documents
        doc_results = self.qdrant.client.search(
            collection_name=self.qdrant.collections["documents"],
            query_vector=query_embedding,
            limit=limit,
            score_threshold=0.6,
            with_payload=True
        )
        
        # Search session contexts
        session_filter = None
        if user_id:
            session_filter = {
                "must": [
                    {
                        "key": "user_id",
                        "match": {"value": user_id}
                    }
                ]
            }
            
            if session_id:
                session_filter["must_not"] = [
                    {
                        "key": "session_id", 
                        "match": {"value": session_id}
                    }
                ]
        
        session_results = self.qdrant.client.search(
            collection_name=self.qdrant.collections["sessions"],
            query_vector=query_embedding,
            query_filter=session_filter,
            limit=limit//2,
            score_threshold=0.6,
            with_payload=True
        )
        
        # Combine and format results
        for result in doc_results:
            results.append({
                "type": "document",
                "id": result.payload["doc_id"],
                "title": result.payload.get("title", ""),
                "content": result.payload["content"][:200] + "...",
                "score": result.score,
                "source": "document_search"
            })
        
        for result in session_results:
            results.append({
                "type": "session",
                "id": result.payload["session_id"],
                "context": result.payload["context_text"][:200] + "...",
                "score": result.score,
                "agent_type": result.payload.get("agent_type"),
                "source": "session_context"
            })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
```

### Performance Optimization
```python
class QdrantOptimizer:
    def __init__(self, qdrant_manager: QdrantManager):
        self.qdrant = qdrant_manager
    
    async def optimize_collections(self):
        """Optimize collections for better performance."""
        
        for collection_name in self.qdrant.collections.values():
            # Optimize indexing
            self.qdrant.client.update_collection(
                collection_name=collection_name,
                optimizer_config={
                    "deleted_threshold": 0.2,
                    "vacuum_min_vector_number": 1000,
                    "default_segment_number": 0,
                    "max_segment_size": 20000,
                    "memmap_threshold": 50000,
                    "indexing_threshold": 20000,
                    "flush_interval_sec": 5,
                    "max_optimization_threads": 2
                }
            )
    
    async def setup_collection_indexes(self, collection_name: str):
        """Setup payload indexes for faster filtering."""
        
        # Common indexes for all collections
        indexes = [
            {"field_name": "project", "field_schema": "keyword"},
            {"field_name": "doc_type", "field_schema": "keyword"},
            {"field_name": "tags", "field_schema": "keyword"},
            {"field_name": "source", "field_schema": "keyword"}
        ]
        
        # Collection-specific indexes
        if "documents" in collection_name:
            indexes.extend([
                {"field_name": "doc_id", "field_schema": "keyword"},
                {"field_name": "chunk_type", "field_schema": "keyword"},
                {"field_name": "chunk_index", "field_schema": "integer"}
            ])
        elif "sessions" in collection_name:
            indexes.extend([
                {"field_name": "session_id", "field_schema": "keyword"},
                {"field_name": "user_id", "field_schema": "keyword"},
                {"field_name": "agent_type", "field_schema": "keyword"}
            ])
        
        # Create indexes
        for index_config in indexes:
            try:
                self.qdrant.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=index_config["field_name"],
                    field_schema=index_config["field_schema"]
                )
            except Exception as e:
                print(f"Index creation failed for {index_config['field_name']}: {e}")
```

## Integration with FindersKeepers v2 Stack

### PostgreSQL Integration
```python
# Sync document metadata between PostgreSQL and Qdrant
async def sync_document_metadata(db_session, qdrant_manager: QdrantManager):
    # Get documents from PostgreSQL that need vector indexing
    docs_query = """
    SELECT doc_id, title, content, project, doc_type, tags, created_at
    FROM documents 
    WHERE vector_indexed = false 
    ORDER BY created_at DESC 
    LIMIT 100
    """
    
    docs = await db_session.execute(text(docs_query))
    
    for doc in docs:
        # Process document in Qdrant
        await document_vectorizer.ingest_document(
            doc_id=doc.doc_id,
            content=doc.content,
            metadata={
                "title": doc.title,
                "project": doc.project,
                "doc_type": doc.doc_type,
                "tags": doc.tags,
                "created_at": doc.created_at.isoformat()
            }
        )
        
        # Mark as indexed in PostgreSQL
        await db_session.execute(
            text("UPDATE documents SET vector_indexed = true WHERE doc_id = :doc_id"),
            {"doc_id": doc.doc_id}
        )
    
    await db_session.commit()
```

### Neo4j Graph Integration
```python
# Create vector embeddings for graph relationships
async def create_graph_relationship_vectors(neo4j_manager, qdrant_manager: QdrantManager):
    # Get relationship texts from Neo4j
    relationships = await neo4j_manager.execute_query("""
        MATCH (e1:Entity)-[r]->(e2:Entity)
        RETURN e1.name as source, type(r) as relationship, e2.name as target,
               e1.name + ' ' + type(r) + ' ' + e2.name as relationship_text
    """)
    
    # Create vectors for relationships
    points = []
    for rel in relationships:
        embedding = await embedding_service.generate(rel['relationship_text'])
        
        point = PointStruct(
            id=f"{rel['source']}_{rel['relationship']}_{rel['target']}",
            vector=embedding,
            payload={
                "source_entity": rel['source'],
                "target_entity": rel['target'],
                "relationship_type": rel['relationship'],
                "relationship_text": rel['relationship_text'],
                "entity_type": "graph_relationship"
            }
        )
        points.append(point)
    
    # Batch upsert
    await qdrant_manager._batch_upsert(
        collection_name=qdrant_manager.collections["knowledge_graph"],
        points=points
    )
```

## Best Practices for FindersKeepers v2

1. **Use appropriate vector dimensions** for different content types
2. **Implement proper chunking** for long documents  
3. **Create semantic hierarchies** with document and chunk embeddings
4. **Use payload indexes** for fast filtering on metadata
5. **Batch operations** for better performance
6. **Monitor collection sizes** and optimize regularly
7. **Implement proper error handling** for vector operations
8. **Use semantic caching** to avoid redundant embedding generation

This documentation provides comprehensive Qdrant integration patterns specifically designed for the FindersKeepers v2 vector search architecture.
""",
                "tags": ["finderskeepers-v2", "qdrant", "vector-database", "similarity-search", "embeddings", "semantic-search", "python-client", "tech-stack", "documentation", "context7"]
            }
        ]
        
        # Ingest each documentation entry
        for entry in documentation_entries:
            await ingester.ingest_document(
                title=entry["title"],
                content=entry["content"],
                tags=entry["tags"]
            )
            
            # Brief pause between ingestions
            await asyncio.sleep(1)
        
        # Print summary
        total_processed = ingester.success_count + ingester.failure_count
        logger.info("\n" + "="*60)
        logger.info("📊 CONTEXT7 DOCUMENTATION INGESTION SUMMARY")
        logger.info("="*60)
        logger.info(f"📚 Total Documents: {len(documentation_entries)}")
        logger.info(f"✅ Successfully Processed: {ingester.success_count}")
        logger.info(f"❌ Failed: {ingester.failure_count}")
        logger.info(f"📈 Success Rate: {(ingester.success_count/total_processed*100):.1f}%")
        logger.info("="*60)
        
        if ingester.success_count > 0:
            logger.info("🎉 Context7 documentation ingestion completed!")
            logger.info("💡 Your FindersKeepers v2 system now has comprehensive tech stack documentation")
            logger.info("🔍 Use the search endpoints to query this knowledge")
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        await ingester.close()

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  🧠 FindersKeepers v2 Context7 Documentation Ingestion          ║
║                                                                  ║
║  This script ingests curated Context7 documentation into your   ║
║  knowledge base with real-world examples and integration        ║
║  patterns for your tech stack.                                  ║
║                                                                  ║
║  Prerequisites:                                                  ║
║  • FastAPI service running on localhost:8000                    ║
║  • PostgreSQL with pgvector available                           ║
║  • All database services running                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Run the async main function
    asyncio.run(main())