"""
Redis Vector Cache Service - 2025 AI/ML Workload Optimization
Implements Vector Sets and LangCache for semantic caching of LLM responses
"""

import hashlib
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

logger = logging.getLogger(__name__)

class RedisVectorCache:
    """2025 Redis Vector Cache with semantic similarity and LangCache support"""
    
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        
        # Database allocation (matches redis.conf)
        self.DB_VECTOR_SEARCH = 0      # Vector search cache (embeddings, similarity)
        self.DB_SEMANTIC_CACHE = 1     # LLM responses with vector keys
        self.DB_SESSION_STATE = 2      # Session state management
        self.DB_ANALYTICS = 3          # Statistics & analytics cache
        self.DB_RATE_LIMITING = 4      # Rate limiting & API usage
        
        # Configuration
        self.similarity_threshold = 0.9
        self.cache_ttl = 3600  # 1 hour
        self.max_vector_dimension = 1024  # mxbai-embed-large
        
    async def _get_client(self, db: int = 0) -> redis.Redis:
        """Get Redis client for specific database"""
        if self._client is None:
            self._client = {}
        
        if db not in self._client:
            self._client[db] = redis.from_url(
                f"{self.redis_url}/{db}",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        
        return self._client[db]
    
    async def setup_vector_indices(self):
        """Setup Redis vector search indices for semantic caching"""
        try:
            # Vector search index for embeddings
            vector_client = await self._get_client(self.DB_VECTOR_SEARCH)
            
            # Create vector index for similarity search
            schema = (
                VectorField(
                    "embedding",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.max_vector_dimension,
                        "DISTANCE_METRIC": "COSINE",
                        "INITIAL_CAP": 1000,
                        "M": 16,
                        "EF_CONSTRUCTION": 200
                    }
                ),
                TextField("content"),
                TextField("cache_key"),
                TextField("response_type"),
                NumericField("timestamp"),
                NumericField("token_count"),
                TextField("model"),
                TextField("prompt_hash")
            )
            
            # Create index
            index_def = IndexDefinition(
                prefix=["vector_cache:"],
                index_type=IndexType.HASH
            )
            
            await vector_client.ft("vector_idx").create_index(
                schema, definition=index_def
            )
            
            logger.info("Vector search index created successfully")
            
        except Exception as e:
            if "Index already exists" in str(e):
                logger.info("Vector search index already exists")
            else:
                logger.error(f"Failed to create vector index: {e}")
    
    async def semantic_cache_set(
        self,
        prompt: str,
        response: str,
        embedding: List[float],
        model: str = "unknown",
        response_type: str = "completion",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store LLM response with semantic caching via embeddings
        
        Args:
            prompt: Original prompt text
            response: LLM response to cache
            embedding: Vector embedding of the prompt
            model: Model used for generation
            response_type: Type of response (completion, chat, etc.)
            metadata: Additional metadata
            
        Returns:
            Cache key for the stored response
        """
        try:
            # Generate cache key
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            cache_key = f"semantic:{model}:{response_type}:{prompt_hash}"
            
            # Store in semantic cache database
            cache_client = await self._get_client(self.DB_SEMANTIC_CACHE)
            
            cache_data = {
                "prompt": prompt,
                "response": response,
                "model": model,
                "response_type": response_type,
                "timestamp": datetime.utcnow().timestamp(),
                "token_count": len(response.split()),
                "metadata": json.dumps(metadata or {})
            }
            
            # Store response data
            await cache_client.hset(cache_key, mapping=cache_data)
            await cache_client.expire(cache_key, self.cache_ttl)
            
            # Store vector for similarity search
            vector_client = await self._get_client(self.DB_VECTOR_SEARCH)
            
            vector_key = f"vector_cache:{cache_key}"
            vector_data = {
                "embedding": np.array(embedding, dtype=np.float32).tobytes(),
                "content": prompt[:500],  # First 500 chars for search
                "cache_key": cache_key,
                "response_type": response_type,
                "timestamp": datetime.utcnow().timestamp(),
                "token_count": len(response.split()),
                "model": model,
                "prompt_hash": prompt_hash
            }
            
            await vector_client.hset(vector_key, mapping=vector_data)
            await vector_client.expire(vector_key, self.cache_ttl)
            
            logger.info(f"Cached semantic response: {cache_key}")
            return cache_key
            
        except Exception as e:
            logger.error(f"Failed to cache semantic response: {e}")
            raise
    
    async def semantic_cache_get(
        self,
        prompt: str,
        embedding: List[float],
        model: str = "unknown",
        response_type: str = "completion"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached LLM response using semantic similarity
        
        Args:
            prompt: Prompt to search for
            embedding: Vector embedding of the prompt
            model: Model to match
            response_type: Response type to match
            
        Returns:
            Cached response data if found, None otherwise
        """
        try:
            vector_client = await self._get_client(self.DB_VECTOR_SEARCH)
            
            # Convert embedding to bytes for Redis search
            query_vector = np.array(embedding, dtype=np.float32).tobytes()
            
            # Vector similarity search
            query = (
                Query(f"(@model:{model} @response_type:{response_type})=>[KNN 5 @embedding $query_vector AS score]")
                .sort_by("score")
                .paging(0, 5)
                .return_fields("cache_key", "score", "content", "timestamp")
                .dialect(2)
            )
            
            results = await vector_client.ft("vector_idx").search(
                query, {"query_vector": query_vector}
            )
            
            # Check if any results meet similarity threshold
            for result in results.docs:
                if float(result.score) >= self.similarity_threshold:
                    # Get full response from semantic cache
                    cache_client = await self._get_client(self.DB_SEMANTIC_CACHE)
                    cached_data = await cache_client.hgetall(result.cache_key)
                    
                    if cached_data:
                        logger.info(f"Semantic cache hit: {result.cache_key} (score: {result.score})")
                        return {
                            "cache_key": result.cache_key,
                            "similarity_score": float(result.score),
                            "prompt": cached_data.get("prompt"),
                            "response": cached_data.get("response"),
                            "model": cached_data.get("model"),
                            "response_type": cached_data.get("response_type"),
                            "timestamp": float(cached_data.get("timestamp", 0)),
                            "metadata": json.loads(cached_data.get("metadata", "{}"))
                        }
            
            logger.debug("No semantic cache match found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to search semantic cache: {e}")
            return None
    
    async def vector_set_add(
        self,
        set_name: str,
        item_id: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add item to vector set for similarity clustering"""
        try:
            vector_client = await self._get_client(self.DB_VECTOR_SEARCH)
            
            vector_key = f"vset:{set_name}:{item_id}"
            vector_data = {
                "embedding": np.array(embedding, dtype=np.float32).tobytes(),
                "item_id": item_id,
                "set_name": set_name,
                "timestamp": datetime.utcnow().timestamp(),
                "metadata": json.dumps(metadata or {})
            }
            
            await vector_client.hset(vector_key, mapping=vector_data)
            await vector_client.sadd(f"vset_members:{set_name}", item_id)
            
            logger.debug(f"Added to vector set {set_name}: {item_id}")
            
        except Exception as e:
            logger.error(f"Failed to add to vector set: {e}")
    
    async def vector_set_search(
        self,
        set_name: str,
        query_embedding: List[float],
        top_k: int = 10,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Search within a vector set for similar items"""
        try:
            vector_client = await self._get_client(self.DB_VECTOR_SEARCH)
            
            # Get all members of the set
            members = await vector_client.smembers(f"vset_members:{set_name}")
            
            results = []
            query_vector = np.array(query_embedding, dtype=np.float32)
            
            for member_id in members:
                vector_key = f"vset:{set_name}:{member_id}"
                data = await vector_client.hgetall(vector_key)
                
                if data and "embedding" in data:
                    # Calculate cosine similarity
                    stored_vector = np.frombuffer(data["embedding"], dtype=np.float32)
                    similarity = np.dot(query_vector, stored_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(stored_vector)
                    )
                    
                    if similarity >= similarity_threshold:
                        results.append({
                            "item_id": member_id,
                            "similarity": float(similarity),
                            "timestamp": float(data.get("timestamp", 0)),
                            "metadata": json.loads(data.get("metadata", "{}"))
                        })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to search vector set: {e}")
            return []
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {}
        
        try:
            for db_name, db_num in [
                ("vector_search", self.DB_VECTOR_SEARCH),
                ("semantic_cache", self.DB_SEMANTIC_CACHE),
                ("session_state", self.DB_SESSION_STATE),
                ("analytics", self.DB_ANALYTICS),
                ("rate_limiting", self.DB_RATE_LIMITING)
            ]:
                client = await self._get_client(db_num)
                info = await client.info("keyspace")
                
                db_key = f"db{db_num}"
                if db_key in info:
                    db_stats = info[db_key]
                    stats[db_name] = {
                        "keys": db_stats.get("keys", 0),
                        "expires": db_stats.get("expires", 0),
                        "avg_ttl": db_stats.get("avg_ttl", 0)
                    }
                else:
                    stats[db_name] = {"keys": 0, "expires": 0, "avg_ttl": 0}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        try:
            current_time = datetime.utcnow().timestamp()
            
            # Clean semantic cache
            cache_client = await self._get_client(self.DB_SEMANTIC_CACHE)
            keys = await cache_client.keys("semantic:*")
            
            for key in keys:
                timestamp = await cache_client.hget(key, "timestamp")
                if timestamp and (current_time - float(timestamp)) > self.cache_ttl:
                    await cache_client.delete(key)
                    logger.debug(f"Cleaned expired cache entry: {key}")
            
            logger.info("Cache cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup cache: {e}")
    
    async def close(self):
        """Close all Redis connections"""
        if self._client:
            for client in self._client.values():
                await client.close()
            self._client = None