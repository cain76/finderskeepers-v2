"""
Redis Client for MCP Knowledge Server
Handles caching and real-time data for knowledge operations
"""

import asyncio
import logging
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

# Import Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available")

logger = logging.getLogger(__name__)

class RedisClient:
    """Async Redis client for caching and real-time operations"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.db = int(os.getenv("REDIS_DB", "0"))
        
        # Cache settings
        self.default_ttl = 3600  # 1 hour default TTL
        self.search_cache_ttl = 1800  # 30 minutes for search results
        self.stats_cache_ttl = 300  # 5 minutes for statistics
        
    async def connect(self):
        """Initialize connection to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return
            
        try:
            self.client = redis.from_url(
                self.url,
                db=self.db,
                decode_responses=True,
                socket_timeout=10,
                socket_connect_timeout=10
            )
            
            # Test connection
            await self.client.ping()
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e} - caching disabled")
            self.client = None
            
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.client = None
            
    async def cache_search_results(
        self,
        query_hash: str,
        results: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache search results for faster repeated queries
        
        Args:
            query_hash: Hash of the search query
            results: Search results to cache
            ttl: Time to live in seconds
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            cache_key = f"search:{query_hash}"
            cache_data = {
                "results": results,
                "cached_at": datetime.utcnow().isoformat(),
                "result_count": len(results)
            }
            
            await self.client.setex(
                cache_key,
                ttl or self.search_cache_ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached search results: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache search results: {e}")
            return False
    
    async def get_cached_search_results(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached search results
        
        Args:
            query_hash: Hash of the search query
            
        Returns:
            Cached results or None if not found/expired
        """
        if not self.client:
            return None
            
        try:
            cache_key = f"search:{query_hash}"
            cached_data = await self.client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved cached search results: {cache_key}")
                return data["results"]
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached search results: {e}")
            return None
    
    async def cache_stats(
        self,
        stats_type: str,
        stats_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache statistics data
        
        Args:
            stats_type: Type of statistics (e.g., 'knowledge_base', 'project')
            stats_data: Statistics data to cache
            ttl: Time to live in seconds
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            cache_key = f"stats:{stats_type}"
            cache_data = {
                "stats": stats_data,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            await self.client.setex(
                cache_key,
                ttl or self.stats_cache_ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached statistics: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache statistics: {e}")
            return False
    
    async def get_cached_stats(self, stats_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached statistics
        
        Args:
            stats_type: Type of statistics to retrieve
            
        Returns:
            Cached statistics or None if not found/expired
        """
        if not self.client:
            return None
            
        try:
            cache_key = f"stats:{stats_type}"
            cached_data = await self.client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved cached statistics: {cache_key}")
                return data["stats"]
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached statistics: {e}")
            return None
    
    async def set_session_data(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store session-specific data
        
        Args:
            session_id: Session identifier
            data: Session data to store
            ttl: Time to live in seconds
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            cache_key = f"session:{session_id}"
            session_data = {
                "data": data,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await self.client.setex(
                cache_key,
                ttl or self.default_ttl,
                json.dumps(session_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set session data: {e}")
            return False
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session-specific data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        if not self.client:
            return None
            
        try:
            cache_key = f"session:{session_id}"
            cached_data = await self.client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                return data["data"]
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return None
    
    async def increment_query_counter(self, query_type: str) -> int:
        """
        Increment a query counter for analytics
        
        Args:
            query_type: Type of query being tracked
            
        Returns:
            New counter value
        """
        if not self.client:
            return 0
            
        try:
            counter_key = f"counter:{query_type}"
            count = await self.client.incr(counter_key)
            
            # Set expiration for daily reset
            if count == 1:  # First increment, set expiration
                tomorrow = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                ttl = int((tomorrow - datetime.utcnow()).total_seconds())
                await self.client.expire(counter_key, ttl)
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to increment query counter: {e}")
            return 0
    
    async def get_query_counters(self) -> Dict[str, int]:
        """
        Get all query counters for analytics
        
        Returns:
            Dictionary of counter names and values
        """
        if not self.client:
            return {}
            
        try:
            counter_keys = await self.client.keys("counter:*")
            counters = {}
            
            if counter_keys:
                values = await self.client.mget(counter_keys)
                for key, value in zip(counter_keys, values):
                    counter_name = key.replace("counter:", "")
                    counters[counter_name] = int(value) if value else 0
            
            return counters
            
        except Exception as e:
            logger.error(f"Failed to get query counters: {e}")
            return {}
    
    async def store_recent_queries(
        self,
        user_id: str,
        query: str,
        max_queries: int = 10
    ) -> bool:
        """
        Store recent queries for a user
        
        Args:
            user_id: User identifier
            query: Query string to store
            max_queries: Maximum number of recent queries to keep
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.client:
            return False
            
        try:
            list_key = f"recent_queries:{user_id}"
            
            # Add query to the beginning of the list
            await self.client.lpush(list_key, json.dumps({
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Trim list to max size
            await self.client.ltrim(list_key, 0, max_queries - 1)
            
            # Set expiration
            await self.client.expire(list_key, 86400)  # 24 hours
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store recent query: {e}")
            return False
    
    async def get_recent_queries(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent queries for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of queries to return
            
        Returns:
            List of recent queries with timestamps
        """
        if not self.client:
            return []
            
        try:
            list_key = f"recent_queries:{user_id}"
            queries = await self.client.lrange(list_key, 0, limit - 1)
            
            recent_queries = []
            for query_data in queries:
                query_info = json.loads(query_data)
                recent_queries.append(query_info)
            
            return recent_queries
            
        except Exception as e:
            logger.error(f"Failed to get recent queries: {e}")
            return []
    
    async def invalidate_cache_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern
        
        Args:
            pattern: Pattern to match (e.g., 'search:*', 'stats:*')
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
            
        try:
            keys = await self.client.keys(pattern)
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching '{pattern}'")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """
        Check if Redis is healthy and responding
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.client:
            return False
            
        try:
            response = await self.client.ping()
            return response is True
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached data
        
        Returns:
            Cache information dictionary
        """
        if not self.client:
            return {"available": False}
            
        try:
            info = await self.client.info("memory")
            
            # Get key counts by type
            search_keys = len(await self.client.keys("search:*"))
            stats_keys = len(await self.client.keys("stats:*"))
            session_keys = len(await self.client.keys("session:*"))
            counter_keys = len(await self.client.keys("counter:*"))
            
            return {
                "available": True,
                "memory_used": info.get("used_memory_human", "Unknown"),
                "total_keys": await self.client.dbsize(),
                "key_counts": {
                    "search_cache": search_keys,
                    "stats_cache": stats_keys,
                    "session_data": session_keys,
                    "query_counters": counter_keys
                },
                "default_ttl": self.default_ttl,
                "search_cache_ttl": self.search_cache_ttl,
                "stats_cache_ttl": self.stats_cache_ttl
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {"available": False, "error": str(e)}