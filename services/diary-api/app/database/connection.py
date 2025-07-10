"""
Database connection management for FindersKeepers v2
Real database connectivity with PostgreSQL, Neo4j, and Qdrant
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import asyncpg
from neo4j import AsyncGraphDatabase
import redis.asyncio as aioredis
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection management"""
    
    def __init__(self):
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver: Optional[AsyncGraphDatabase] = None
        self.redis_client: Optional[aioredis.Redis] = None
        self.qdrant_client: Optional[QdrantClient] = None
        
        # Configuration from environment - use Docker service names
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'fk2_postgres'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'finderskeepers_v2'),
            'user': os.getenv('POSTGRES_USER', 'finderskeepers'),
            'password': os.getenv('POSTGRES_PASSWORD', 'fk2025secure'),
        }
        
        self.neo4j_config = {
            'uri': os.getenv('NEO4J_URI', 'bolt://fk2_neo4j:7687'),
            'username': os.getenv('NEO4J_USERNAME', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'fk2025neo4j'),
        }
        
        self.redis_config = {
            'host': os.getenv('REDIS_HOST', 'fk2_redis'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
        }
        
        self.qdrant_config = {
            'host': os.getenv('QDRANT_HOST', 'fk2_qdrant'),
            'port': int(os.getenv('QDRANT_PORT', '6333')),
        }
    
    async def initialize_postgres(self) -> bool:
        """Initialize PostgreSQL connection pool"""
        try:
            logger.info("🔄 Initializing PostgreSQL connection pool...")
            self.postgres_pool = await asyncpg.create_pool(
                **self.postgres_config,
                min_size=5,
                max_size=20,
                command_timeout=30
            )
            
            # Test connection
            async with self.postgres_pool.acquire() as conn:
                await conn.execute('SELECT 1')
                
            logger.info("✅ PostgreSQL connection pool initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL initialization failed: {e}")
            return False
    
    async def initialize_neo4j(self) -> bool:
        """Initialize Neo4j connection"""
        try:
            logger.info("🔄 Initializing Neo4j connection...")
            self.neo4j_driver = AsyncGraphDatabase.driver(
                self.neo4j_config['uri'],
                auth=(self.neo4j_config['username'], self.neo4j_config['password'])
            )
            
            # Test connection
            async with self.neo4j_driver.session() as session:
                await session.run("RETURN 1")
                
            logger.info("✅ Neo4j connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Neo4j initialization failed: {e}")
            return False
    
    async def initialize_redis(self) -> bool:
        """Initialize Redis connection"""
        try:
            logger.info("🔄 Initializing Redis connection...")
            self.redis_client = aioredis.from_url(
                f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}"
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("✅ Redis connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            return False
    
    async def initialize_qdrant(self) -> bool:
        """Initialize Qdrant connection"""
        try:
            logger.info("🔄 Initializing Qdrant connection...")
            self.qdrant_client = QdrantClient(
                host=self.qdrant_config['host'],
                port=self.qdrant_config['port']
            )
            
            # Test connection
            collections = self.qdrant_client.get_collections()
            
            logger.info("✅ Qdrant connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Qdrant initialization failed: {e}")
            return False
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all database connections"""
        results = {}
        
        # Initialize all databases concurrently
        tasks = [
            ("postgres", self.initialize_postgres()),
            ("neo4j", self.initialize_neo4j()),
            ("redis", self.initialize_redis()),
            ("qdrant", self.initialize_qdrant())
        ]
        
        for name, task in tasks:
            results[name] = await task
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"🎯 Database initialization: {success_count}/{total_count} successful")
        return results
    
    async def close_all(self):
        """Close all database connections"""
        if self.postgres_pool:
            await self.postgres_pool.close()
            logger.info("🔒 PostgreSQL pool closed")
        
        if self.neo4j_driver:
            await self.neo4j_driver.close()
            logger.info("🔒 Neo4j driver closed")
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔒 Redis client closed")
        
        if self.qdrant_client:
            # Qdrant client doesn't have async close method
            logger.info("🔒 Qdrant client closed")
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """Get PostgreSQL connection from pool"""
        if not self.postgres_pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        
        async with self.postgres_pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def get_neo4j_session(self):
        """Get Neo4j session"""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        async with self.neo4j_driver.session() as session:
            yield session
    
    def get_redis_client(self):
        """Get Redis client"""
        if not self.redis_client:
            raise RuntimeError("Redis client not initialized")
        return self.redis_client
    
    def get_qdrant_client(self):
        """Get Qdrant client"""
        if not self.qdrant_client:
            raise RuntimeError("Qdrant client not initialized")
        return self.qdrant_client
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all databases"""
        health_status = {
            'postgres': False,
            'neo4j': False,
            'redis': False,
            'qdrant': False,
            'details': {}
        }
        
        # PostgreSQL health check
        try:
            async with self.get_postgres_connection() as conn:
                result = await conn.fetchval('SELECT NOW()')
                health_status['postgres'] = True
                health_status['details']['postgres'] = {
                    'status': 'healthy',
                    'timestamp': result.isoformat(),
                    'pool_size': self.postgres_pool.get_size() if hasattr(self.postgres_pool, 'get_size') else 'unknown',
                    'pool_free': 'unknown'
                }
        except Exception as e:
            health_status['details']['postgres'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Neo4j health check
        try:
            async with self.get_neo4j_session() as session:
                result = await session.run("CALL db.ping()")
                health_status['neo4j'] = True
                health_status['details']['neo4j'] = {
                    'status': 'healthy',
                    'database': 'neo4j'
                }
        except Exception as e:
            health_status['details']['neo4j'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Redis health check
        try:
            redis_client = self.get_redis_client()
            await redis_client.ping()
            health_status['redis'] = True
            health_status['details']['redis'] = {
                'status': 'healthy',
                'ping': 'pong'
            }
        except Exception as e:
            health_status['details']['redis'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Qdrant health check
        try:
            qdrant_client = self.get_qdrant_client()
            collections = qdrant_client.get_collections()
            health_status['qdrant'] = True
            health_status['details']['qdrant'] = {
                'status': 'healthy',
                'collections_count': len(collections.collections)
            }
        except Exception as e:
            health_status['details']['qdrant'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return health_status

# Global database manager instance
db_manager = DatabaseManager()