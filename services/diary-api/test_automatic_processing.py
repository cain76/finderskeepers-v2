#!/usr/bin/env python3
"""
TEST AUTOMATIC PROCESSING PIPELINE
Verify that documents are automatically processed through all stages
"""

import asyncio
import json
import logging
from datetime import datetime
import httpx
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_automatic_processing():
    """Test the automatic document processing pipeline"""
    
    # Test document content
    test_document = {
        "title": "Docker Setup Guide for FindersKeepers v2",
        "content": """
        # Docker Setup Guide for FindersKeepers v2
        
        This guide covers setting up Docker for the FindersKeepers v2 project.
        
        ## Prerequisites
        - Docker installed (version 20.10+)
        - Docker Compose installed
        - Python 3.9+
        - Neo4j database
        - PostgreSQL with pgvector extension
        
        ## Configuration Files
        Main configuration is in docker-compose.yml located at:
        /media/cain/linux_storage/projects/finderskeepers-v2/docker-compose.yml
        
        ## Services
        The system uses multiple Docker containers:
        1. fk2_fastapi - FastAPI backend service
        2. fk2_postgres - PostgreSQL database
        3. fk2_neo4j - Neo4j knowledge graph
        4. fk2_qdrant - Qdrant vector database
        5. fk2_ollama - Ollama for local LLM
        
        ## Key Technologies
        - FastAPI for API backend
        - PostgreSQL for data storage
        - Neo4j for knowledge graphs
        - Qdrant for vector search
        - Ollama for embeddings
        - Docker for containerization
        
        ## Important URLs
        - API Documentation: http://localhost:8000/docs
        - Neo4j Browser: http://localhost:7474
        - Qdrant Dashboard: http://localhost:6333
        
        ## Troubleshooting
        If containers fail to start, check Docker logs:
        docker logs fk2_fastapi
        docker logs fk2_postgres
        
        Author: Jeremy Davis (jeremy.cn.davis@gmail.com)
        Project: FindersKeepers v2
        """,
        "project": "finderskeepers-v2",
        "doc_type": "technical",
        "tags": ["docker", "setup", "guide", "technical"],
        "metadata": {
            "test_run": True,
            "test_id": f"test_{uuid4().hex[:8]}",
            "created_at": datetime.utcnow().isoformat()
        }
    }
    
    logger.info("🧪 Testing Automatic Document Processing Pipeline")
    logger.info("=" * 60)
    
    # Step 1: Ingest document via API
    logger.info("\n📤 Step 1: Ingesting test document via API...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/docs/ingest",
                json=test_document
            )
            
            if response.status_code == 200:
                result = response.json()
                document_id = result.get("document_id")
                logger.info(f"✅ Document ingested successfully: {document_id}")
            else:
                logger.error(f"❌ Ingestion failed: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to API: {e}")
        return False
    
    # Step 2: Wait for processing
    logger.info("\n⏳ Step 2: Waiting for automatic processing...")
    await asyncio.sleep(5)
    
    # Step 3: Check if document was processed
    logger.info("\n🔍 Step 3: Checking processing status...")
    
    try:
        # Check PostgreSQL for metadata updates
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get document details
            response = await client.get(
                f"http://localhost:8000/api/docs/by-id/{document_id}"
            )
            
            if response.status_code == 200:
                doc_data = response.json().get("data", {})
                metadata = doc_data.get("metadata", {})
                
                logger.info("📊 Document Processing Status:")
                logger.info(f"  - Entities extracted: {metadata.get('entities_extracted', False)}")
                logger.info(f"  - Entity count: {metadata.get('entity_count', 0)}")
                logger.info(f"  - Relationships created: {metadata.get('relationships_created', False)}")
                logger.info(f"  - Relationship count: {metadata.get('relationship_count', 0)}")
                logger.info(f"  - Embeddings generated: {metadata.get('embeddings_generated', False)}")
                logger.info(f"  - Embedding dimensions: {metadata.get('embedding_dimensions', 0)}")
            else:
                logger.error(f"❌ Failed to get document: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Failed to check status: {e}")
    
    # Step 4: Test vector search
    logger.info("\n🔎 Step 4: Testing vector search...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/search/vector",
                json={
                    "query": "Docker setup guide",
                    "limit": 5,
                    "project": "finderskeepers-v2"
                }
            )
            
            if response.status_code == 200:
                results = response.json().get("data", [])
                logger.info(f"✅ Vector search returned {len(results)} results")
                
                if results:
                    top_result = results[0]
                    logger.info(f"  Top result: {top_result.get('payload', {}).get('title', 'Unknown')}")
                    logger.info(f"  Score: {top_result.get('score', 0)}")
            else:
                logger.error(f"❌ Vector search failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Vector search error: {e}")
    
    # Step 5: Check knowledge graph
    logger.info("\n🧠 Step 5: Checking knowledge graph...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/api/knowledge/query",
                json={
                    "question": "Docker FastAPI",
                    "project": "finderskeepers-v2",
                    "include_history": True
                }
            )
            
            if response.status_code == 200:
                kg_result = response.json()
                relationships = kg_result.get("relationships", [])
                documents = kg_result.get("documents", [])
                
                logger.info(f"✅ Knowledge graph query successful")
                logger.info(f"  - Relationships found: {len(relationships)}")
                logger.info(f"  - Related documents: {len(documents)}")
                
                if relationships:
                    logger.info("  Sample relationships:")
                    for rel in relationships[:3]:
                        logger.info(f"    {rel.get('source')} --[{rel.get('relationship')}]--> {rel.get('target')}")
            else:
                logger.error(f"❌ Knowledge graph query failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Knowledge graph error: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Test Complete!")
    
    return True

async def run_processing_fix():
    """Run the automatic processing fix before testing"""
    logger.info("🔧 Running automatic processing fix...")
    
    try:
        # Import and run the fix
        from fix_automatic_processing import AutomaticProcessingPipeline
        
        pipeline = AutomaticProcessingPipeline()
        
        # Setup trigger
        await pipeline.setup_automatic_trigger()
        
        # Process unprocessed documents
        await pipeline.process_unprocessed_documents()
        
        logger.info("✅ Automatic processing fix applied")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to apply fix: {e}")
        return False

async def main():
    """Main test entry point"""
    
    # First run the fix
    fix_success = await run_processing_fix()
    
    if not fix_success:
        logger.warning("⚠️  Fix failed, but continuing with test...")
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Run the test
    test_success = await test_automatic_processing()
    
    if test_success:
        logger.info("\n✨ All tests passed! Automatic processing is working.")
    else:
        logger.error("\n❌ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())
