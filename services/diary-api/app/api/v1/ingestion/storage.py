"""
Storage service for managing multi-database document storage
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
from uuid import uuid4

import asyncpg
import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from neo4j import AsyncGraphDatabase

from .models import (
    IngestionRequest,
    ProcessedChunk,
    DocumentMetadata,
    FileFormat
)

logger = logging.getLogger(__name__)

class StorageService:
    """Service for coordinating storage across PostgreSQL, Qdrant, and Neo4j"""
    
    def __init__(self):
        # Database connections will be initialized on first use
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._qdrant_client: Optional[AsyncQdrantClient] = None
        self._neo4j_driver = None
        
        # Configuration from environment
        self.pg_dsn = os.getenv("DATABASE_URL", "postgresql://finderskeepers:fk2025secure@postgres:5432/finderskeepers_v2")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j://neo4j:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "fk2025neo4j")
        
        # Collection names
        self.qdrant_collection = "fk2_documents"
        self.embedding_dimension = 1536  # mxbai-embed-large dimension
        
    async def _ensure_pg_pool(self):
        """Ensure PostgreSQL connection pool exists"""
        if self._pg_pool is None:
            self._pg_pool = await asyncpg.create_pool(self.pg_dsn, min_size=1, max_size=10)
            
    async def _ensure_qdrant(self):
        """Ensure Qdrant client and collection exist"""
        if self._qdrant_client is None:
            self._qdrant_client = AsyncQdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
                timeout=30
            )
            
            # Create collection if it doesn't exist
            try:
                collections = await self._qdrant_client.get_collections()
                if not any(c.name == self.qdrant_collection for c in collections.collections):
                    await self._qdrant_client.create_collection(
                        collection_name=self.qdrant_collection,
                        vectors_config=VectorParams(
                            size=self.embedding_dimension,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created Qdrant collection: {self.qdrant_collection}")
            except Exception as e:
                logger.error(f"Failed to ensure Qdrant collection: {e}")
                
    def _ensure_neo4j(self):
        """Ensure Neo4j driver exists"""
        if self._neo4j_driver is None:
            self._neo4j_driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
    async def store_document(
        self,
        request: IngestionRequest,
        metadata: DocumentMetadata,
        chunks: List[ProcessedChunk]
    ) -> str:
        """
        Store document and chunks across all databases
        
        Returns:
            Document ID
        """
        document_id = f"doc_{uuid4().hex[:12]}"
        
        try:
            # Store in PostgreSQL
            await self._store_in_postgres(document_id, request, metadata, chunks)
            
            # Store embeddings in Qdrant
            if any(chunk.embeddings for chunk in chunks):
                await self._store_in_qdrant(document_id, request, chunks)
            
            # Create knowledge graph relationships
            await self._store_in_neo4j(document_id, request, metadata, chunks)
            
            logger.info(f"Successfully stored document {document_id} across all databases")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to store document: {e}")
            # Consider rollback logic here
            raise
            
    async def _store_in_postgres(
        self,
        document_id: str,
        request: IngestionRequest,
        metadata: DocumentMetadata,
        chunks: List[ProcessedChunk]
    ):
        """Store document and chunks in PostgreSQL"""
        await self._ensure_pg_pool()
        
        async with self._pg_pool.acquire() as conn:
            async with conn.transaction():
                # Insert document using actual schema columns
                combined_content = " ".join(chunk.content for chunk in chunks)
                await conn.execute("""
                    INSERT INTO documents (
                        id, title, content, project, doc_type,
                        tags, metadata, embeddings
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    document_id,
                    metadata.title,
                    combined_content,
                    request.project,
                    request.metadata.get('doc_type', 'ingested'),
                    request.tags,
                    json.dumps({
                        **request.metadata,
                        "filename": getattr(request, 'filename', ''),
                        "file_path": getattr(request, 'file_path', ''),
                        "format": metadata.format.value,
                        "processing_method": metadata.processing_method.value,
                        "word_count": metadata.word_count,
                        "language": metadata.language,
                        "ingestion_id": request.ingestion_id,
                        "file_size": getattr(request, 'file_size', 0),
                        "mime_type": getattr(request, 'mime_type', 'text/plain')
                    }),
                    chunks[0].embeddings if chunks and chunks[0].embeddings else None
                )
                
                # Insert chunks using actual schema columns
                for chunk in chunks:
                    await conn.execute("""
                        INSERT INTO document_chunks (
                            id, document_id, chunk_index, content,
                            embedding, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        chunk.chunk_id,
                        document_id,
                        chunk.metadata.chunk_index,
                        chunk.content,
                        chunk.embeddings,
                        json.dumps({
                            "start_char": chunk.metadata.start_char,
                            "end_char": chunk.metadata.end_char,
                            "page_number": chunk.metadata.page_number,
                            "section": getattr(chunk.metadata, 'section', None),
                            "language": chunk.language,
                            "token_count": chunk.token_count
                        })
                    )
                    
    async def _store_in_qdrant(
        self,
        document_id: str,
        request: IngestionRequest,
        chunks: List[ProcessedChunk]
    ):
        """Store embeddings in Qdrant for fast vector search"""
        await self._ensure_qdrant()
        
        points = []
        for chunk in chunks:
            if chunk.embeddings:
                # Convert string chunk_id to integer hash for Qdrant compatibility
                point_id = abs(hash(chunk.chunk_id)) % (2**31)  # Ensure positive 32-bit integer
                point = PointStruct(
                    id=point_id,
                    vector=chunk.embeddings,
                    payload={
                        "chunk_id": chunk.chunk_id,  # Store original string ID in payload
                        "document_id": document_id,
                        "chunk_index": chunk.metadata.chunk_index,
                        "content": chunk.content[:500],  # First 500 chars for preview
                        "project": request.project,
                        "tags": request.tags,
                        "filename": request.filename,
                        "token_count": chunk.token_count,
                        "language": chunk.language,
                        "metadata": {
                            "start_char": chunk.metadata.start_char,
                            "end_char": chunk.metadata.end_char,
                            "page_number": chunk.metadata.page_number
                        }
                    }
                )
                points.append(point)
        
        if points:
            # Batch upload to Qdrant
            await self._qdrant_client.upsert(
                collection_name=self.qdrant_collection,
                points=points
            )
            logger.info(f"Stored {len(points)} embeddings in Qdrant for document {document_id}")
            
    async def _store_in_neo4j(
        self,
        document_id: str,
        request: IngestionRequest,
        metadata: DocumentMetadata,
        chunks: List[ProcessedChunk]
    ):
        """Create knowledge graph relationships in Neo4j"""
        self._ensure_neo4j()
        
        async with self._neo4j_driver.session() as session:
            try:
                # Create Document node
                await session.run("""
                    MERGE (d:Document {id: $id})
                    SET d.filename = $filename,
                        d.format = $format,
                        d.project = $project,
                        d.language = $language,
                        d.created_at = datetime($created_at),
                        d.word_count = $word_count
                """, {
                    "id": document_id,
                    "filename": request.filename,
                    "format": metadata.format.value,
                    "project": request.project,
                    "language": metadata.language,
                    "created_at": datetime.utcnow().isoformat(),
                    "word_count": metadata.word_count
                })
                
                # Create Project node and relationship
                await session.run("""
                    MERGE (p:Project {name: $project})
                    WITH p
                    MATCH (d:Document {id: $document_id})
                    MERGE (d)-[:BELONGS_TO]->(p)
                """, {
                    "project": request.project,
                    "document_id": document_id
                })
                
                # Create Tag nodes and relationships
                for tag in request.tags:
                    await session.run("""
                        MERGE (t:Tag {name: $tag})
                        WITH t
                        MATCH (d:Document {id: $document_id})
                        MERGE (d)-[:TAGGED_WITH]->(t)
                    """, {
                        "tag": tag,
                        "document_id": document_id
                    })
                
                # Extract and create Entity nodes from content
                # This is simplified - in production, use NER
                entities = await self._extract_entities(chunks)
                for entity_type, entity_name in entities:
                    await session.run("""
                        MERGE (e:Entity {name: $name, type: $type})
                        WITH e
                        MATCH (d:Document {id: $document_id})
                        MERGE (d)-[:MENTIONS]->(e)
                    """, {
                        "name": entity_name,
                        "type": entity_type,
                        "document_id": document_id
                    })
                
                logger.info(f"Created knowledge graph for document {document_id}")
                
            except Exception as e:
                logger.error(f"Failed to create knowledge graph: {e}")
                # Non-critical, continue without graph
                
    async def _extract_entities(self, chunks: List[ProcessedChunk]) -> List[Tuple[str, str]]:
        """
        Extract entities from document chunks
        In production, use spaCy or similar NER
        """
        entities = []
        
        # Simple pattern matching for demonstration
        # In reality, use proper NER
        combined_text = " ".join(chunk.content for chunk in chunks[:5])  # First 5 chunks
        
        # Extract potential file paths
        import re
        file_pattern = r'[a-zA-Z0-9_\-/]+\.[a-zA-Z]{2,4}'
        for match in re.findall(file_pattern, combined_text):
            if len(match) > 5:  # Filter out small matches
                entities.append(("FILE", match))
        
        # Extract potential URLs
        url_pattern = r'https?://[^\s]+'
        for match in re.findall(url_pattern, combined_text):
            entities.append(("URL", match))
        
        # Extract potential function/class names (for code)
        code_pattern = r'(def|class|function|const|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for match in re.findall(code_pattern, combined_text):
            entities.append(("CODE", match[1]))
        
        # Deduplicate
        return list(set(entities))[:20]  # Limit to 20 entities
        
    async def search_similar(
        self,
        query_embedding: List[float],
        project: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector search"""
        await self._ensure_qdrant()
        
        # Build filter
        filter_conditions = []
        if project:
            filter_conditions.append({
                "key": "project",
                "match": {"value": project}
            })
        if tags:
            for tag in tags:
                filter_conditions.append({
                    "key": "tags",
                    "match": {"any": [tag]}
                })
        
        # Search Qdrant
        search_result = self._qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_embedding,
            query_filter={"must": filter_conditions} if filter_conditions else None,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Format results
        results = []
        for hit in search_result:
            results.append({
                "chunk_id": hit.payload.get("chunk_id", hit.id),  # Use original chunk_id from payload
                "score": hit.score,
                "document_id": hit.payload.get("document_id"),
                "content": hit.payload.get("content"),
                "metadata": hit.payload.get("metadata"),
                "filename": hit.payload.get("filename"),
                "project": hit.payload.get("project"),
                "tags": hit.payload.get("tags")
            })
        
        return results
        
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document details from PostgreSQL"""
        await self._ensure_pg_pool()
        
        async with self._pg_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM documents WHERE id = $1
            """, document_id)
            
            if row:
                return dict(row)
            return None
            
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks for a document"""
        await self._ensure_pg_pool()
        
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM document_chunks 
                WHERE document_id = $1 
                ORDER BY chunk_index
            """, document_id)
            
            return [dict(row) for row in rows]
            
    async def delete_document(self, document_id: str):
        """Delete document from all databases"""
        try:
            # Delete from PostgreSQL (cascades to chunks)
            await self._ensure_pg_pool()
            async with self._pg_pool.acquire() as conn:
                await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
            
            # Delete from Qdrant
            await self._ensure_qdrant()
            chunk_ids = await self._get_chunk_ids(document_id)
            if chunk_ids:
                self._qdrant_client.delete(
                    collection_name=self.qdrant_collection,
                    points_selector=chunk_ids
                )
            
            # Delete from Neo4j
            self._ensure_neo4j()
            async with self._neo4j_driver.session() as session:
                await session.run("""
                    MATCH (d:Document {id: $id})
                    DETACH DELETE d
                """, {"id": document_id})
                
            logger.info(f"Deleted document {document_id} from all databases")
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
            
    async def _get_chunk_ids(self, document_id: str) -> List[str]:
        """Get all chunk IDs for a document"""
        await self._ensure_pg_pool()
        
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id FROM document_chunks WHERE document_id = $1
            """, document_id)
            
            return [row["id"] for row in rows]
            
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all storage backends"""
        health = {
            "postgres": False,
            "qdrant": False,
            "neo4j": False
        }
        
        # Check PostgreSQL
        try:
            await self._ensure_pg_pool()
            async with self._pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health["postgres"] = True
        except:
            pass
        
        # Check Qdrant
        try:
            await self._ensure_qdrant()
            self._qdrant_client.get_collections()
            health["qdrant"] = True
        except:
            pass
        
        # Check Neo4j
        try:
            self._ensure_neo4j()
            async with self._neo4j_driver.session() as session:
                await session.run("RETURN 1")
            health["neo4j"] = True
        except:
            pass
        
        return health
        
    async def close(self):
        """Clean up connections"""
        if self._pg_pool:
            await self._pg_pool.close()
        if self._neo4j_driver:
            await self._neo4j_driver.close()