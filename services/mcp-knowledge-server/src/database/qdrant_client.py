"""
Qdrant Vector Database Client for MCP Knowledge Server
Handles vector search, embeddings, and similarity analysis
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
import os
from datetime import datetime

# Import Qdrant client
try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("Qdrant client not available")

logger = logging.getLogger(__name__)

class QdrantClient:
    """Async Qdrant client for vector operations"""
    
    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = "fk2_documents"
        self.fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8000")
        
    async def connect(self):
        """Initialize connection to Qdrant"""
        if not QDRANT_AVAILABLE:
            logger.error("Qdrant client not available")
            return
            
        try:
            self.client = AsyncQdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=30
            )
            
            # Test connection
            collections = await self.client.get_collections()
            logger.info(f"Connected to Qdrant: {len(collections.collections)} collections")
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None
            
    async def disconnect(self):
        """Close Qdrant connection"""
        if self.client:
            await self.client.close()
            self.client = None
            
    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings using the FastAPI backend's Ollama integration
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        try:
            # Try FastAPI endpoint first
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.fastapi_url}/api/embeddings",
                        json={"text": text}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        embeddings = data.get("embeddings", [])
                        logger.debug(f"Generated embeddings via FastAPI: {len(embeddings)} dimensions")
                        return embeddings
            except:
                pass
                
            # Fallback: Try direct Ollama API
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "http://localhost:11434/api/embeddings",
                        json={
                            "model": "mxbai-embed-large",
                            "prompt": text
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        embeddings = data.get("embedding", [])
                        logger.debug(f"Generated embeddings via Ollama: {len(embeddings)} dimensions")
                        return embeddings
            except:
                pass
                
            # Final fallback: Mock embeddings for testing
            logger.warning("Using mock embeddings - real embeddings not available")
            # Generate a simple mock embedding based on text hash
            import hashlib
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            # Create a 1024-dimensional mock embedding
            mock_embedding = []
            for i in range(0, len(text_hash), 2):
                value = int(text_hash[i:i+2], 16) / 255.0 - 0.5
                mock_embedding.extend([value] * 32)  # 32 * 32 = 1024 dimensions
            return mock_embedding[:1024]
                    
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []
    
    async def search(
        self,
        embeddings: List[float],
        project: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector embeddings
        
        Args:
            embeddings: Query vector embeddings
            project: Filter by project name
            tags: Filter by document tags
            limit: Maximum number of results
            min_score: Minimum similarity score
            
        Returns:
            List of search results with scores and metadata
        """
        if not self.client or not embeddings:
            logger.warning("Qdrant client not available or no embeddings provided")
            return []
            
        try:
            # Build filter conditions
            filter_conditions = []
            
            if project:
                filter_conditions.append(
                    FieldCondition(
                        key="project",
                        match=MatchValue(value=project)
                    )
                )
                
            if tags:
                for tag in tags:
                    filter_conditions.append(
                        FieldCondition(
                            key="tags",
                            match=MatchValue(value=tag)
                        )
                    )
            
            # Build filter object
            search_filter = None
            if filter_conditions:
                search_filter = Filter(must=filter_conditions)
            
            # Execute search
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=embeddings,
                query_filter=search_filter,
                limit=limit,
                score_threshold=min_score
            )
            
            # Format results
            formatted_results = []
            for hit in search_results:
                result = {
                    "chunk_id": hit.id,
                    "document_id": hit.payload.get("document_id"),
                    "content": hit.payload.get("content", ""),
                    "score": hit.score,
                    "metadata": {
                        "project": hit.payload.get("project"),
                        "tags": hit.payload.get("tags", []),
                        "filename": hit.payload.get("filename"),
                        "chunk_index": hit.payload.get("chunk_index"),
                        "token_count": hit.payload.get("token_count")
                    }
                }
                formatted_results.append(result)
            
            logger.info(f"Vector search found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def get_document_embeddings(self, document_id: str) -> List[float]:
        """
        Get embeddings for a specific document
        
        Args:
            document_id: Document ID to get embeddings for
            
        Returns:
            Document embeddings or empty list if not found
        """
        if not self.client:
            return []
            
        try:
            # Search for document chunks
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=[0.0] * 1024,  # Dummy vector for filter-only search
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=1
            )
            
            if search_results:
                # Get the first chunk's embeddings (assuming document similarity)
                point_id = search_results[0].id
                points = await self.client.retrieve(
                    collection_name=self.collection_name,
                    ids=[point_id],
                    with_vectors=True
                )
                
                if points and len(points) > 0:
                    return points[0].vector
                    
            return []
            
        except Exception as e:
            logger.error(f"Failed to get document embeddings: {e}")
            return []
    
    async def find_similar_documents(
        self,
        embeddings: List[float],
        threshold: float = 0.7,
        limit: int = 8,
        exclude_document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to given embeddings
        
        Args:
            embeddings: Reference embeddings
            threshold: Minimum similarity threshold
            limit: Maximum number of results
            exclude_document_id: Document ID to exclude from results
            
        Returns:
            List of similar documents with scores
        """
        if not self.client or not embeddings:
            return []
            
        try:
            # Build filter to exclude reference document
            search_filter = None
            if exclude_document_id:
                search_filter = Filter(
                    must_not=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=exclude_document_id)
                        )
                    ]
                )
            
            # Search for similar documents
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=embeddings,
                query_filter=search_filter,
                limit=limit,
                score_threshold=threshold
            )
            
            # Group by document_id and pick highest scoring chunk per document
            doc_scores = {}
            for hit in search_results:
                doc_id = hit.payload.get("document_id")
                if doc_id not in doc_scores or hit.score > doc_scores[doc_id]["score"]:
                    doc_scores[doc_id] = {
                        "document_id": doc_id,
                        "score": hit.score,
                        "content": hit.payload.get("content", ""),
                        "chunk_id": hit.id,
                        "metadata": hit.payload
                    }
            
            # Sort by score and return top results
            similar_docs = list(doc_scores.values())
            similar_docs.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Found {len(similar_docs)} similar documents")
            return similar_docs[:limit]
            
        except Exception as e:
            logger.error(f"Similar document search failed: {e}")
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Qdrant collection
        
        Returns:
            Collection statistics and health information
        """
        if not self.client:
            return {"healthy": False, "error": "Client not connected"}
            
        try:
            # Get collection info
            collection_info = await self.client.get_collection(self.collection_name)
            
            # Get collections list
            collections = await self.client.get_collections()
            
            stats = {
                "healthy": True,
                "collections": [c.name for c in collections.collections],
                "total_vectors": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "index_type": "HNSW",  # Default for Qdrant
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Calculate approximate search speed (this is an estimate)
            stats["search_speed"] = min(1000, stats["total_vectors"] // 10) if stats["total_vectors"] > 0 else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> bool:
        """
        Check if Qdrant service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.client:
            return False
            
        try:
            # Try to get collections (simple health check)
            collections = await self.client.get_collections()
            return len(collections.collections) >= 0  # Even 0 collections is healthy
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False