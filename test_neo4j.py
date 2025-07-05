#!/usr/bin/env python3
"""
Test Neo4j knowledge graph functionality
"""

import requests
import json
import base64
from typing import Dict, List, Any

# Neo4j connection parameters
NEO4J_CONFIG = {
    "uri": "http://localhost:7474",
    "username": "neo4j",
    "password": "fk2025neo4j"
}

class Neo4jTester:
    def __init__(self, uri: str, username: str, password: str):
        self.uri = uri
        self.auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def test_connection(self) -> bool:
        """Test basic Neo4j connection"""
        try:
            # Test the root endpoint first
            response = requests.get(f"{self.uri}/", headers=self.headers)
            if response.status_code == 200:
                print("✅ Neo4j connection successful")
                data = response.json()
                print(f"   Neo4j version: {data.get('neo4j_version', 'unknown')}")
                print(f"   Neo4j edition: {data.get('neo4j_edition', 'unknown')}")
                return True
            else:
                print(f"❌ Neo4j connection failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            return False
    
    def execute_cypher(self, query: str, parameters: Dict = None) -> Dict:
        """Execute a Cypher query using transaction API"""
        try:
            payload = {
                "statements": [
                    {
                        "statement": query,
                        "parameters": parameters or {}
                    }
                ]
            }
            
            response = requests.post(
                f"{self.uri}/db/neo4j/tx/commit",
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Query failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            return {}
    
    def create_test_nodes(self) -> bool:
        """Create test nodes for knowledge graph testing"""
        try:
            print("\n📝 Creating test knowledge graph nodes...")
            
            # Create project node
            query = """
            MERGE (p:Project {name: 'finderskeepers-v2', type: 'AI Knowledge Hub'})
            RETURN p
            """
            result = self.execute_cypher(query)
            if result:
                print("✅ Project node created")
            
            # Create technology nodes
            technologies = [
                {"name": "FastAPI", "type": "Web Framework", "language": "Python"},
                {"name": "PostgreSQL", "type": "Database", "category": "RDBMS"},
                {"name": "Neo4j", "type": "Database", "category": "Graph"},
                {"name": "Ollama", "type": "LLM Engine", "category": "AI"},
                {"name": "Docker", "type": "Containerization", "category": "DevOps"}
            ]
            
            for tech in technologies:
                query = """
                MERGE (t:Technology {name: $name})
                SET t.type = $type, t.category = $category
                RETURN t
                """
                result = self.execute_cypher(query, tech)
                if result:
                    print(f"✅ Technology node created: {tech['name']}")
            
            # Create relationships
            print("\n🔗 Creating relationships...")
            relationships = [
                ("finderskeepers-v2", "USES", "FastAPI"),
                ("finderskeepers-v2", "USES", "PostgreSQL"),
                ("finderskeepers-v2", "USES", "Neo4j"),
                ("finderskeepers-v2", "USES", "Ollama"),
                ("finderskeepers-v2", "USES", "Docker"),
                ("FastAPI", "CONNECTS_TO", "PostgreSQL"),
                ("FastAPI", "CONNECTS_TO", "Neo4j"),
                ("FastAPI", "INTEGRATES_WITH", "Ollama")
            ]
            
            for source, relation, target in relationships:
                query = """
                MATCH (s {name: $source}), (t {name: $target})
                MERGE (s)-[r:%s]->(t)
                RETURN r
                """ % relation
                
                result = self.execute_cypher(query, {"source": source, "target": target})
                if result:
                    print(f"✅ Relationship created: {source} -{relation}-> {target}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test node creation failed: {e}")
            return False
    
    def test_graph_queries(self) -> bool:
        """Test various graph query patterns"""
        try:
            print("\n🔍 Testing graph query patterns...")
            
            # Test 1: Find all technologies used by the project
            print("\n1. Technologies used by finderskeepers-v2:")
            query = """
            MATCH (p:Project {name: 'finderskeepers-v2'})-[:USES]->(t:Technology)
            RETURN t.name as technology, t.type as type, t.category as category
            ORDER BY t.name
            """
            result = self.execute_cypher(query)
            if result and 'results' in result and result['results']:
                data = result['results'][0]['data']
                for row in data:
                    tech, tech_type, category = row['row']
                    print(f"   - {tech} ({tech_type}, {category})")
            
            # Test 2: Find technology relationships
            print("\n2. Technology integration patterns:")
            query = """
            MATCH (t1:Technology)-[r]->(t2:Technology)
            RETURN t1.name as from_tech, type(r) as relationship, t2.name as to_tech
            """
            result = self.execute_cypher(query)
            if result and 'results' in result and result['results']:
                data = result['results'][0]['data']
                for row in data:
                    from_tech, relationship, to_tech = row['row']
                    print(f"   {from_tech} -{relationship}-> {to_tech}")
            
            # Test 3: Find database technologies
            print("\n3. Database technologies in the stack:")
            query = """
            MATCH (t:Technology)
            WHERE t.category = 'Database'
            RETURN t.name as name, t.type as type
            """
            result = self.execute_cypher(query)
            if result and 'results' in result and result['results']:
                data = result['results'][0]['data']
                for row in data:
                    name, db_type = row['row']
                    print(f"   - {name} ({db_type})")
            
            # Test 4: Path analysis
            print("\n4. Find paths from project to AI technologies:")
            query = """
            MATCH path = (p:Project {name: 'finderskeepers-v2'})-[*1..3]-(t:Technology)
            WHERE t.category = 'AI'
            RETURN t.name as ai_tech, length(path) as path_length
            """
            result = self.execute_cypher(query)
            if result and 'results' in result and result['results']:
                data = result['results'][0]['data']
                for row in data:
                    ai_tech, path_length = row['row']
                    print(f"   {ai_tech} (distance: {path_length})")
            
            return True
            
        except Exception as e:
            print(f"❌ Graph query testing failed: {e}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """Clean up test data"""
        try:
            print("\n🧹 Cleaning up test data...")
            query = """
            MATCH (n)
            WHERE n.name IN ['finderskeepers-v2', 'FastAPI', 'PostgreSQL', 'Neo4j', 'Ollama', 'Docker']
            DETACH DELETE n
            """
            result = self.execute_cypher(query)
            print("✅ Test data cleaned up")
            return True
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False

def main():
    """Main test function"""
    print("🔍 Neo4j Knowledge Graph Testing")
    print("=" * 50)
    
    # Initialize tester
    tester = Neo4jTester(**NEO4J_CONFIG)
    
    # Test connection
    if not tester.test_connection():
        return False
    
    # Create test data
    if not tester.create_test_nodes():
        return False
    
    # Test queries
    if not tester.test_graph_queries():
        return False
    
    # Cleanup
    if not tester.cleanup_test_data():
        return False
    
    print("\n🎉 Neo4j knowledge graph test completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ All Neo4j tests passed!")
    else:
        print("\n❌ Some Neo4j tests failed!")