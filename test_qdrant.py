#!/usr/bin/env python3
"""
Test Qdrant vector database performance
"""

import requests
import json
import numpy as np
import time
from typing import List, Dict, Any

# Qdrant connection parameters
QDRANT_CONFIG = {
    "host": "localhost",
    "port": 6333,
    "base_url": "http://localhost:6333"
}

class QdrantTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        self.collection_name = "test_knowledge_collection"
    
    def test_connection(self) -> bool:
        """Test basic Qdrant connection"""
        try:
            response = requests.get(f"{self.base_url}/collections")
            if response.status_code == 200:
                print("✅ Qdrant connection successful")
                data = response.json()
                print(f"   Collections: {len(data['result']['collections'])}")
                return True
            else:
                print(f"❌ Qdrant connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Qdrant connection failed: {e}")
            return False
    
    def create_test_collection(self, vector_size: int = 1536) -> bool:
        """Create a test collection for vector search"""
        try:
            print(f"\n📊 Creating test collection '{self.collection_name}'...")
            
            payload = {
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine"
                }
            }
            
            response = requests.put(
                f"{self.base_url}/collections/{self.collection_name}",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code in [200, 201]:
                print("✅ Test collection created successfully")
                return True
            else:
                print(f"❌ Collection creation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Collection creation failed: {e}")
            return False
    
    def generate_test_vectors(self, count: int, vector_size: int = 1536) -> List[Dict]:
        """Generate test vectors with metadata"""
        print(f"\n🧮 Generating {count} test vectors...")
        
        vectors = []
        for i in range(count):
            vector = np.random.normal(0, 1, vector_size).tolist()
            
            vectors.append({
                "id": i + 1,
                "vector": vector,
                "payload": {
                    "text": f"This is test document {i + 1} for vector search testing",
                    "category": ["ai", "vector", "search"][i % 3],
                    "project": "finderskeepers-v2",
                    "importance": np.random.uniform(0.1, 1.0),
                    "created_at": f"2025-07-05T{i:02d}:00:00Z"
                }
            })
        
        print(f"✅ Generated {count} test vectors")
        return vectors
    
    def insert_vectors_batch(self, vectors: List[Dict]) -> bool:
        """Insert vectors in batch for performance testing"""
        try:
            print(f"\n📝 Inserting {len(vectors)} vectors in batch...")
            start_time = time.time()
            
            payload = {
                "points": vectors
            }
            
            response = requests.put(
                f"{self.base_url}/collections/{self.collection_name}/points",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            insert_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Batch insert successful in {insert_time:.2f} seconds")
                print(f"   Rate: {len(vectors) / insert_time:.1f} vectors/second")
                return True
            else:
                print(f"❌ Batch insert failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Batch insert failed: {e}")
            return False
    
    def test_vector_search(self, query_vector: List[float], limit: int = 10) -> bool:
        """Test vector similarity search performance"""
        try:
            print(f"\n🔍 Testing vector search (top {limit} results)...")
            start_time = time.time()
            
            payload = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            }
            
            response = requests.post(
                f"{self.base_url}/collections/{self.collection_name}/points/search",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            search_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data["result"]
                
                print(f"✅ Search completed in {search_time * 1000:.1f} ms")
                print(f"   Found {len(results)} results:")
                
                for i, result in enumerate(results[:5]):  # Show top 5
                    score = result["score"]
                    payload = result["payload"]
                    print(f"   {i+1}. Score: {score:.4f}")
                    print(f"      Text: {payload['text'][:50]}...")
                    print(f"      Category: {payload['category']}")
                
                return True
            else:
                print(f"❌ Search failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
    
    def test_filtered_search(self, query_vector: List[float]) -> bool:
        """Test filtered vector search with metadata filters"""
        try:
            print(f"\n🎯 Testing filtered search...")
            start_time = time.time()
            
            payload = {
                "vector": query_vector,
                "limit": 5,
                "filter": {
                    "must": [
                        {
                            "key": "category",
                            "match": {
                                "value": "ai"
                            }
                        },
                        {
                            "key": "importance",
                            "range": {
                                "gte": 0.5
                            }
                        }
                    ]
                },
                "with_payload": True
            }
            
            response = requests.post(
                f"{self.base_url}/collections/{self.collection_name}/points/search",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            search_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data["result"]
                
                print(f"✅ Filtered search completed in {search_time * 1000:.1f} ms")
                print(f"   Found {len(results)} results matching filters:")
                
                for i, result in enumerate(results):
                    score = result["score"]
                    payload = result["payload"]
                    print(f"   {i+1}. Score: {score:.4f}, Category: {payload['category']}, Importance: {payload['importance']:.2f}")
                
                return True
            else:
                print(f"❌ Filtered search failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Filtered search failed: {e}")
            return False
    
    def test_performance_benchmarks(self, vectors: List[Dict]) -> bool:
        """Run performance benchmarks"""
        try:
            print(f"\n⚡ Running performance benchmarks...")
            
            # Test multiple search queries
            search_times = []
            query_vector = vectors[0]["vector"]  # Use first vector as query
            
            for i in range(10):
                start_time = time.time()
                
                payload = {
                    "vector": query_vector,
                    "limit": 10,
                    "with_payload": False
                }
                
                response = requests.post(
                    f"{self.base_url}/collections/{self.collection_name}/points/search",
                    headers=self.headers,
                    data=json.dumps(payload)
                )
                
                if response.status_code == 200:
                    search_time = time.time() - start_time
                    search_times.append(search_time * 1000)  # Convert to ms
            
            if search_times:
                avg_time = np.mean(search_times)
                min_time = np.min(search_times)
                max_time = np.max(search_times)
                
                print(f"✅ Search performance (10 queries):")
                print(f"   Average: {avg_time:.1f} ms")
                print(f"   Min: {min_time:.1f} ms")
                print(f"   Max: {max_time:.1f} ms")
                print(f"   QPS: {1000 / avg_time:.1f} queries/second")
            
            # Test collection info
            response = requests.get(f"{self.base_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                collection_info = response.json()["result"]
                print(f"\n📊 Collection statistics:")
                print(f"   Vectors count: {collection_info['points_count']}")
                
                # Handle different possible API response structures
                config = collection_info.get('config', {})
                params = config.get('params', {})
                vectors_config = config.get('vectors', {})
                
                # Try different possible keys for vector size
                vector_size = (
                    params.get('vector_size') or 
                    vectors_config.get('size') or 
                    'unknown'
                )
                
                # Try different possible keys for distance metric
                distance = (
                    params.get('distance') or 
                    vectors_config.get('distance') or 
                    'unknown'
                )
                
                print(f"   Vector size: {vector_size}")
                print(f"   Distance metric: {distance}")
            else:
                print(f"   Could not retrieve collection info: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance benchmarks failed: {e}")
            return False
    
    def cleanup_test_collection(self) -> bool:
        """Clean up test collection"""
        try:
            print(f"\n🧹 Cleaning up test collection...")
            response = requests.delete(f"{self.base_url}/collections/{self.collection_name}")
            
            if response.status_code == 200:
                print("✅ Test collection cleaned up")
                return True
            else:
                print(f"❌ Cleanup failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False

def main():
    """Main test function"""
    print("🔍 Qdrant Vector Database Testing")
    print("=" * 50)
    
    # Initialize tester
    tester = QdrantTester(QDRANT_CONFIG["base_url"])
    
    # Test connection
    if not tester.test_connection():
        return False
    
    # Cleanup any existing test collection first
    tester.cleanup_test_collection()
    
    # Create test collection
    if not tester.create_test_collection():
        return False
    
    # Generate test vectors
    test_vectors = tester.generate_test_vectors(100)  # 100 vectors for testing
    
    # Insert vectors
    if not tester.insert_vectors_batch(test_vectors):
        return False
    
    # Test vector search
    query_vector = test_vectors[50]["vector"]  # Use middle vector as query
    if not tester.test_vector_search(query_vector):
        return False
    
    # Test filtered search
    if not tester.test_filtered_search(query_vector):
        return False
    
    # Run performance benchmarks
    if not tester.test_performance_benchmarks(test_vectors):
        return False
    
    # Cleanup
    if not tester.cleanup_test_collection():
        return False
    
    print("\n🎉 Qdrant vector database test completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ All Qdrant tests passed!")
    else:
        print("\n❌ Some Qdrant tests failed!")