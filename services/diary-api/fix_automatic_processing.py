#!/usr/bin/env python3
"""
AUTOMATIC DOCUMENT PROCESSING PIPELINE FIX
Fixes the automatic processing of documents in FindersKeepers v2
This ensures documents are properly processed through all stages:
1. Entity extraction
2. Embedding generation
3. Vector database population
4. Knowledge graph relationship creation
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import json
import re
from datetime import datetime
from uuid import uuid4

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.connection import db_manager
import httpx
import asyncpg
from neo4j import AsyncGraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomaticProcessingPipeline:
    """Automatic document processing pipeline that triggers on document creation"""
    
    def __init__(self):
        self.postgres_url = os.getenv("POSTGRES_URL", "postgresql://finderskeepers:fk2025secure@postgres:5432/finderskeepers_v2")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
        self.chat_model = os.getenv("CHAT_MODEL", "llama3:8b")
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "fk2025neo4j")
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        
    async def process_unprocessed_documents(self):
        """Find and process documents that haven't been fully processed"""
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Find documents without embeddings or relationships
            unprocessed = await conn.fetch("""
                SELECT id, title, content, project, doc_type, tags, metadata
                FROM documents
                WHERE embeddings IS NULL 
                   OR metadata->>'entities_extracted' IS NULL
                   OR metadata->>'relationships_created' IS NULL
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            logger.info(f"🔍 Found {len(unprocessed)} unprocessed documents")
            
            for doc in unprocessed:
                await self.process_document(dict(doc))
                
        finally:
            await conn.close()
    
    async def process_document(self, doc: Dict[str, Any]):
        """Process a single document through the complete pipeline"""
        logger.info(f"📄 Processing document: {doc['title']}")
        
        try:
            # Step 1: Extract entities using improved NER
            entities = await self.extract_entities_advanced(doc['content'])
            logger.info(f"  ✅ Extracted {len(entities)} entities")
            
            # Step 2: Generate embeddings
            embeddings = await self.generate_embeddings(doc['content'])
            logger.info(f"  ✅ Generated {len(embeddings)} dimensional embeddings")
            
            # Step 3: Create knowledge graph relationships
            relationships = await self.create_knowledge_graph(doc, entities)
            logger.info(f"  ✅ Created {len(relationships)} relationships in Neo4j")
            
            # Step 4: Store in vector database
            await self.store_in_vector_db(doc, embeddings, entities)
            logger.info(f"  ✅ Stored in Qdrant vector database")
            
            # Step 5: Update document metadata
            await self.update_document_metadata(doc['id'], {
                "entities_extracted": True,
                "entity_count": len(entities),
                "relationships_created": True,
                "relationship_count": len(relationships),
                "embeddings_generated": True,
                "embedding_dimensions": len(embeddings),
                "processed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"✨ Successfully processed document: {doc['title']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process document {doc['id']}: {e}")
    
    async def extract_entities_advanced(self, content: str) -> List[Tuple[str, str, Dict]]:
        """
        Advanced entity extraction using Ollama for NER
        Returns: List of (entity_type, entity_name, metadata) tuples
        """
        entities = []
        
        # Use Ollama for entity extraction
        extraction_prompt = f"""
        Extract all named entities from the following text. 
        Identify: PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, CONCEPT, FILE, URL, CODE_ELEMENT
        
        Format your response as JSON array:
        [
            {{"type": "PERSON", "name": "John Doe", "context": "developer"}},
            {{"type": "TECHNOLOGY", "name": "Docker", "context": "containerization"}},
            ...
        ]
        
        Text: {content[:3000]}
        
        Response (JSON only):
        """
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": extraction_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1024
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "[]")
                    
                    # Parse JSON response
                    try:
                        # Clean up response if needed
                        response_text = response_text.strip()
                        if not response_text.startswith('['):
                            # Find JSON array in response
                            start = response_text.find('[')
                            end = response_text.rfind(']') + 1
                            if start >= 0 and end > start:
                                response_text = response_text[start:end]
                        
                        extracted = json.loads(response_text)
                        
                        for entity in extracted:
                            if isinstance(entity, dict) and 'type' in entity and 'name' in entity:
                                entities.append((
                                    entity['type'],
                                    entity['name'],
                                    {"context": entity.get('context', ''), "source": "ollama_ner"}
                                ))
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse Ollama NER response as JSON")
        
        except Exception as e:
            logger.warning(f"Ollama NER failed: {e}, falling back to regex")
        
        # Fallback: Basic regex extraction
        if not entities:
            entities.extend(self.extract_entities_regex(content))
        
        # Deduplicate
        unique_entities = {}
        for entity_type, entity_name, metadata in entities:
            key = f"{entity_type}:{entity_name.lower()}"
            if key not in unique_entities:
                unique_entities[key] = (entity_type, entity_name, metadata)
        
        return list(unique_entities.values())[:50]  # Limit to 50 entities
    
    def extract_entities_regex(self, content: str) -> List[Tuple[str, str, Dict]]:
        """Fallback regex-based entity extraction"""
        entities = []
        
        # Extract file paths
        file_pattern = r'[a-zA-Z0-9_\-/]+\.[a-zA-Z]{2,4}'
        for match in re.findall(file_pattern, content):
            if len(match) > 5:
                entities.append(("FILE", match, {"source": "regex"}))
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"\']+'
        for match in re.findall(url_pattern, content):
            entities.append(("URL", match, {"source": "regex"}))
        
        # Extract code elements
        code_patterns = [
            (r'class\s+([A-Z][a-zA-Z0-9_]*)', "CLASS"),
            (r'def\s+([a-z_][a-zA-Z0-9_]*)', "FUNCTION"),
            (r'const\s+([A-Z_][A-Z0-9_]*)', "CONSTANT"),
        ]
        
        for pattern, entity_type in code_patterns:
            for match in re.findall(pattern, content):
                entities.append((entity_type, match, {"source": "regex"}))
        
        # Extract potential technology names (capitalized words)
        tech_pattern = r'\b([A-Z][a-zA-Z]+(?:[A-Z][a-zA-Z]+)*)\b'
        tech_keywords = ['Docker', 'Python', 'FastAPI', 'PostgreSQL', 'Neo4j', 'Redis', 'Ollama']
        for match in re.findall(tech_pattern, content):
            if match in tech_keywords or len(match) > 3:
                entities.append(("TECHNOLOGY", match, {"source": "regex"}))
        
        return entities[:30]  # Limit
    
    async def generate_embeddings(self, content: str) -> List[float]:
        """Generate embeddings using Ollama with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.ollama_url}/api/embed",
                        json={
                            "model": self.embedding_model,
                            "input": content[:8000]  # Limit content size
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        embeddings = data.get("embeddings", [])
                        if embeddings and len(embeddings) > 0:
                            return embeddings[0] if isinstance(embeddings[0], list) else embeddings
                    
            except Exception as e:
                logger.warning(f"Embedding generation attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
        
        # Return empty embeddings if all retries fail
        logger.error("All embedding generation attempts failed")
        return []
    
    async def create_knowledge_graph(self, doc: Dict, entities: List[Tuple]) -> List[Dict]:
        """Create rich knowledge graph relationships in Neo4j"""
        relationships = []
        
        driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        try:
            async with driver.session() as session:
                # Create document node
                await session.run("""
                    MERGE (d:Document {id: $id})
                    SET d.title = $title,
                        d.project = $project,
                        d.doc_type = $doc_type,
                        d.content_preview = $content_preview,
                        d.updated_at = datetime()
                """, {
                    "id": str(doc['id']),
                    "title": doc['title'],
                    "project": doc['project'],
                    "doc_type": doc['doc_type'],
                    "content_preview": doc['content'][:500]
                })
                
                # Create project node and relationship
                await session.run("""
                    MATCH (d:Document {id: $doc_id})
                    MERGE (p:Project {name: $project})
                    MERGE (d)-[:BELONGS_TO]->(p)
                """, {
                    "doc_id": str(doc['id']),
                    "project": doc['project']
                })
                relationships.append({"type": "BELONGS_TO", "target": doc['project']})
                
                # Create entity nodes and relationships
                for entity_type, entity_name, metadata in entities:
                    # Create entity node
                    await session.run("""
                        MERGE (e:Entity {name: $name, type: $type})
                        SET e.updated_at = datetime()
                    """, {
                        "name": entity_name,
                        "type": entity_type
                    })
                    
                    # Create document-entity relationship
                    await session.run("""
                        MATCH (d:Document {id: $doc_id})
                        MATCH (e:Entity {name: $entity_name, type: $entity_type})
                        MERGE (d)-[r:MENTIONS]->(e)
                        SET r.context = $context,
                            r.count = coalesce(r.count, 0) + 1
                    """, {
                        "doc_id": str(doc['id']),
                        "entity_name": entity_name,
                        "entity_type": entity_type,
                        "context": metadata.get('context', '')
                    })
                    relationships.append({
                        "type": "MENTIONS",
                        "entity": entity_name,
                        "entity_type": entity_type
                    })
                
                # Create entity-to-entity relationships based on co-occurrence
                entity_pairs = []
                for i, (type1, name1, _) in enumerate(entities):
                    for type2, name2, _ in entities[i+1:]:
                        if name1 != name2:
                            entity_pairs.append((name1, type1, name2, type2))
                
                for name1, type1, name2, type2 in entity_pairs[:20]:  # Limit relationships
                    await session.run("""
                        MATCH (e1:Entity {name: $name1, type: $type1})
                        MATCH (e2:Entity {name: $name2, type: $type2})
                        MERGE (e1)-[r:RELATED_TO]->(e2)
                        SET r.count = coalesce(r.count, 0) + 1,
                            r.source_doc = $doc_id,
                            r.updated_at = datetime()
                    """, {
                        "name1": name1,
                        "type1": type1,
                        "name2": name2,
                        "type2": type2,
                        "doc_id": str(doc['id'])
                    })
                    relationships.append({
                        "type": "RELATED_TO",
                        "source": name1,
                        "target": name2
                    })
                
        finally:
            await driver.close()
        
        return relationships
    
    async def store_in_vector_db(self, doc: Dict, embeddings: List[float], entities: List[Tuple]):
        """Store document embeddings in Qdrant vector database"""
        if not embeddings:
            logger.warning(f"No embeddings to store for document {doc['id']}")
            return
        
        try:
            from qdrant_client import AsyncQdrantClient
            from qdrant_client.models import PointStruct, VectorParams, Distance
            
            client = AsyncQdrantClient(url=self.qdrant_url)
            
            # Ensure collection exists
            collection_name = "fk2_documents"
            try:
                collections = await client.get_collections()
                if not any(c.name == collection_name for c in collections.collections):
                    await client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=len(embeddings),
                            distance=Distance.COSINE
                        )
                    )
            except:
                pass  # Collection might already exist
            
            # Create payload with rich metadata
            payload = {
                "document_id": str(doc['id']),
                "title": doc['title'],
                "content": doc['content'][:1000],  # Store preview
                "project": doc['project'],
                "doc_type": doc['doc_type'],
                "tags": doc['tags'] if doc['tags'] else [],
                "entities": [{"type": t, "name": n} for t, n, _ in entities[:20]],
                "entity_count": len(entities),
                "indexed_at": datetime.utcnow().isoformat()
            }
            
            # Store in Qdrant
            point = PointStruct(
                id=str(uuid4()),
                vector=embeddings,
                payload=payload
            )
            
            await client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(f"  ✅ Stored document {doc['id']} in Qdrant")
            
        except Exception as e:
            logger.error(f"Failed to store in Qdrant: {e}")
    
    async def update_document_metadata(self, doc_id: str, metadata_updates: Dict):
        """Update document metadata to track processing status"""
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Get existing metadata
            existing = await conn.fetchval("""
                SELECT metadata FROM documents WHERE id = $1
            """, doc_id)
            
            if existing:
                metadata = json.loads(existing) if isinstance(existing, str) else existing
            else:
                metadata = {}
            
            # Update metadata
            metadata.update(metadata_updates)
            
            # Store updated metadata
            await conn.execute("""
                UPDATE documents 
                SET metadata = $2,
                    updated_at = NOW()
                WHERE id = $1
            """, doc_id, json.dumps(metadata))
            
        finally:
            await conn.close()
    
    async def setup_automatic_trigger(self):
        """Setup PostgreSQL trigger for automatic processing"""
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Create notification function
            await conn.execute("""
                CREATE OR REPLACE FUNCTION notify_document_insert()
                RETURNS trigger AS $$
                BEGIN
                    PERFORM pg_notify('new_document', NEW.id::text);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # Create trigger
            await conn.execute("""
                DROP TRIGGER IF EXISTS document_insert_trigger ON documents;
                CREATE TRIGGER document_insert_trigger
                AFTER INSERT ON documents
                FOR EACH ROW
                EXECUTE FUNCTION notify_document_insert();
            """)
            
            logger.info("✅ Automatic processing trigger created")
            
        finally:
            await conn.close()
    
    async def listen_for_new_documents(self):
        """Listen for new document notifications and process them"""
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Add listener
            await conn.add_listener('new_document', self.handle_new_document)
            
            logger.info("👂 Listening for new documents...")
            
            # Keep connection alive
            while True:
                await asyncio.sleep(60)
                
        finally:
            await conn.close()
    
    async def handle_new_document(self, connection, pid, channel, payload):
        """Handle new document notification"""
        logger.info(f"📨 New document notification: {payload}")
        
        conn = await asyncpg.connect(self.postgres_url)
        try:
            doc = await conn.fetchrow("""
                SELECT id, title, content, project, doc_type, tags, metadata
                FROM documents WHERE id = $1
            """, payload)
            
            if doc:
                await self.process_document(dict(doc))
        finally:
            await conn.close()

async def main():
    """Main entry point for automatic processing pipeline"""
    pipeline = AutomaticProcessingPipeline()
    
    logger.info("🚀 Starting Automatic Document Processing Pipeline")
    
    # Setup automatic trigger
    await pipeline.setup_automatic_trigger()
    
    # Process any unprocessed documents
    await pipeline.process_unprocessed_documents()
    
    # Start listening for new documents
    # await pipeline.listen_for_new_documents()
    
    logger.info("✅ Automatic processing complete")

if __name__ == "__main__":
    asyncio.run(main())
