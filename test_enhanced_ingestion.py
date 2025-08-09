#!/usr/bin/env python3
"""
Test the enhanced document ingestion with full automatic processing
"""

import asyncio
import httpx
import json
from datetime import datetime
from uuid import uuid4

async def test_enhanced_ingestion():
    """Test the enhanced ingestion endpoint"""
    
    print("🧪 TESTING ENHANCED DOCUMENT INGESTION")
    print("=" * 60)
    
    # Create unique test document
    test_doc = {
        "title": f"Enhanced Test {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "content": """
        This document tests the ENHANCED automatic processing pipeline.
        
        Technologies: Docker, Kubernetes, PostgreSQL, Neo4j, FastAPI, Python
        
        URLs:
        - https://github.com/finderskeepers/v2
        - https://api.finderskeepers.com/docs
        
        Code elements:
        - class DocumentProcessor
        - def process_document()
        - const PIPELINE_VERSION = "2.0"
        
        People: John Doe (developer), Jane Smith (architect)
        Organizations: FindersKeepers Inc, OpenAI, Anthropic
        
        This comprehensive test ensures all entity types are extracted.
        """,
        "project": "enhanced-test",
        "doc_type": "technical",
        "tags": ["enhanced", "test", "pipeline", "automatic"],
        "metadata": {
            "test_id": f"enhanced_{uuid4().hex[:8]}",
            "test_type": "full_pipeline"
        }
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Ingest document
        print("\n📤 Step 1: Ingesting document with enhanced pipeline...")
        response = await client.post(
            "http://localhost:8000/api/docs/ingest",
            json=test_doc
        )
        
        if response.status_code == 200:
            result = response.json()
            doc_id = result.get("document_id")
            print(f"✅ Document ingested: {doc_id}")
            print(f"   Pipeline processing: {result.get('pipeline_processing')}")
            print(f"   Features: {json.dumps(result.get('features', {}), indent=4)}")
        else:
            print(f"❌ Ingestion failed: {response.status_code}")
            print(response.text)
            return
        
        # Step 2: Wait for processing
        print("\n⏳ Step 2: Waiting for automatic processing...")
        await asyncio.sleep(8)
        
        # Step 3: Check processing status
        print("\n🔍 Step 3: Checking document processing status...")
        response = await client.get(f"http://localhost:8000/api/docs/by-id/{doc_id}")
        
        if response.status_code == 200:
            doc_data = response.json().get("data", {})
            processing_status = doc_data.get("processing_status", {})
            
            print("\n📊 Processing Status:")
            print(f"  ✓ Entities extracted: {processing_status.get('entities_extracted')}")
            print(f"  ✓ Entity count: {processing_status.get('entity_count')}")
            print(f"  ✓ Embeddings generated: {processing_status.get('embeddings_generated')}")
            print(f"  ✓ Relationships created: {processing_status.get('relationships_created')}")
            print(f"  ✓ Relationship count: {processing_status.get('relationship_count')}")
            print(f"  ✓ Fully processed: {processing_status.get('fully_processed')}")
            
            if processing_status.get('fully_processed'):
                print("\n🎉 Document fully processed!")
            else:
                print("\n⚠️  Document not fully processed yet")
        else:
            print(f"❌ Failed to get document: {response.status_code}")
        
        # Step 4: Test processing status endpoint
        print("\n📋 Step 4: Checking all unprocessed documents...")
        response = await client.get(
            "http://localhost:8000/api/docs/processing-status",
            params={"status": "unprocessed", "limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json().get("data", [])
            print(f"Found {len(data)} unprocessed documents")
            for doc in data[:3]:
                print(f"  - {doc['title'][:50]}...")
        
        # Step 5: Test vector search
        print("\n🔎 Step 5: Testing vector search for our document...")
        response = await client.post(
            "http://localhost:8000/api/search/vector",
            json={
                "query": "Docker Kubernetes enhanced pipeline",
                "limit": 5,
                "project": "enhanced-test"
            }
        )
        
        if response.status_code == 200:
            results = response.json().get("data", [])
            print(f"✅ Vector search found {len(results)} results")
            if results:
                for i, result in enumerate(results[:3]):
                    print(f"  {i+1}. {result.get('payload', {}).get('title', 'Unknown')[:50]}")
        
        # Step 6: Query knowledge graph
        print("\n🧠 Step 6: Querying knowledge graph...")
        response = await client.post(
            "http://localhost:8000/api/knowledge/query",
            json={
                "question": "What technologies are mentioned?",
                "project": "enhanced-test"
            }
        )
        
        if response.status_code == 200:
            kg_data = response.json()
            relationships = kg_data.get("relationships", [])
            print(f"✅ Found {len(relationships)} relationships")
            if relationships:
                print("  Sample relationships:")
                for rel in relationships[:5]:
                    print(f"    {rel.get('source')} --[{rel.get('relationship')}]--> {rel.get('target')}")
    
    print("\n" + "=" * 60)
    print("✨ ENHANCED INGESTION TEST COMPLETE!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_ingestion())
