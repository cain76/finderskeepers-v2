#!/usr/bin/env python3
"""
Test PostgreSQL + pgvector vector similarity search
"""

import asyncio
import os
import psycopg2
import numpy as np
from typing import List
import json

# Database connection parameters
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "finderskeepers_v2",
    "user": "finderskeepers",
    "password": "fk2025secure"
}

def generate_test_embedding(size: int = 1536) -> List[float]:
    """Generate a random test embedding vector"""
    return np.random.normal(0, 1, size).tolist()

async def test_pgvector_connection():
    """Test PostgreSQL connection and pgvector functionality"""
    try:
        # Connect to PostgreSQL
        print("🔗 Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL connected: {version}")
        
        # Test pgvector extension
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print("✅ pgvector extension available")
        else:
            print("❌ pgvector extension not found")
            return False
            
        # Test vector operations
        print("\n🧮 Testing vector operations...")
        
        # Create test embeddings
        test_embedding_1 = generate_test_embedding()
        test_embedding_2 = generate_test_embedding()
        
        # Test vector distance calculation
        cursor.execute("""
            SELECT %s::vector <=> %s::vector as cosine_distance
        """, (test_embedding_1, test_embedding_2))
        distance = cursor.fetchone()[0]
        print(f"✅ Vector distance calculation: {distance:.4f}")
        
        # Test document_chunks table structure
        print("\n📊 Testing document_chunks table...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks' 
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("✅ Table structure:")
        for col_name, col_type in columns:
            print(f"   - {col_name}: {col_type}")
        
        # Test inserting a sample document with embedding
        print("\n📝 Testing document insertion with embedding...")
        
        # First, insert a test document
        cursor.execute("""
            INSERT INTO documents (title, content, project, doc_type, tags)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            "Test Document for Vector Search",
            "This is a test document to verify vector similarity search functionality.",
            "test-project",
            "test",
            ["test", "vector", "search"]
        ))
        doc_id = cursor.fetchone()[0]
        print(f"✅ Document inserted with ID: {doc_id}")
        
        # Insert document chunk with embedding
        cursor.execute("""
            INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
            VALUES (%s, %s, %s, %s::vector)
            RETURNING id;
        """, (
            doc_id,
            0,
            "This is a test document to verify vector similarity search functionality.",
            test_embedding_1
        ))
        chunk_id = cursor.fetchone()[0]
        print(f"✅ Document chunk inserted with ID: {chunk_id}")
        
        # Test vector similarity search using the stored function
        print("\n🔍 Testing vector similarity search...")
        cursor.execute("""
            SELECT * FROM search_similar_chunks(
                %s::vector,  -- query_embedding
                0.0,         -- similarity_threshold (very low for testing)
                5,           -- max_results
                'test-project'  -- filter_project
            );
        """, (test_embedding_1,))
        
        results = cursor.fetchall()
        print(f"✅ Found {len(results)} similar chunks:")
        for i, result in enumerate(results):
            chunk_id, doc_id, content, similarity, project, doc_title = result
            print(f"   {i+1}. Similarity: {similarity:.4f}")
            print(f"      Title: {doc_title}")
            print(f"      Content: {content[:50]}...")
            print(f"      Project: {project}")
        
        # Test with different embedding (should have lower similarity)
        print("\n🔍 Testing with different embedding...")
        cursor.execute("""
            SELECT * FROM search_similar_chunks(
                %s::vector,  -- query_embedding
                0.0,         -- similarity_threshold
                5,           -- max_results
                'test-project'  -- filter_project
            );
        """, (test_embedding_2,))
        
        results = cursor.fetchall()
        print(f"✅ Found {len(results)} similar chunks with different embedding:")
        for i, result in enumerate(results):
            chunk_id, doc_id, content, similarity, project, doc_title = result
            print(f"   {i+1}. Similarity: {similarity:.4f}")
        
        # Cleanup test data
        print("\n🧹 Cleaning up test data...")
        cursor.execute("DELETE FROM documents WHERE project = 'test-project';")
        print("✅ Test data cleaned up")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 PostgreSQL + pgvector test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_pgvector_connection())
    if success:
        print("\n✅ All pgvector tests passed!")
    else:
        print("\n❌ Some tests failed!")