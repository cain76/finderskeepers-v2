"""
Automatic Document Processing Pipeline - Core Module
This is integrated into the FastAPI application for automatic initialization
"""

import asyncio
import logging
import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from uuid import uuid4

import asyncpg
import httpx
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

class AutomaticProcessingPipeline:
    """Automatic document processing pipeline that triggers on document creation"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.postgres_url = os.getenv("POSTGRES_URL", "postgresql://finderskeepers:@postgres:5432/finderskeepers_v2")
            self.ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
            self.embedding_model = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
            self.chat_model = os.getenv("CHAT_MODEL", "llama3:8b")
            self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
            self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            self.neo4j_password = os.getenv("NEO4J_PASSWORD")
            self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
            self._initialized = True
    
    async def initialize(self):
        """Initialize the automatic processing pipeline"""
        try:
            # Create PostgreSQL trigger for automatic processing
            await self.setup_automatic_trigger()
            logger.info("✅ Automatic processing pipeline initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize automatic processing: {e}")
            return False
    
    async def setup_automatic_trigger(self):
        """Setup PostgreSQL trigger for automatic processing"""
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            # Check if trigger already exists
            trigger_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_trigger 
                    WHERE tgname = 'document_insert_trigger'
                )
            """)
            
            if not trigger_exists:
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
                    CREATE TRIGGER document_insert_trigger
                    AFTER INSERT ON documents
                    FOR EACH ROW
                    EXECUTE FUNCTION notify_document_insert();
                """)
                
                logger.info("✅ Database trigger created for automatic processing")
            else:
                logger.info("ℹ️ Database trigger already exists")
                
        finally:
            await conn.close()
    
    async def process_unprocessed_documents(self, limit: int = 10):
        """Process documents that haven't been fully processed"""
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
                LIMIT $1
            """, limit)
            
            if unprocessed:
                logger.info(f"🔍 Found {len(unprocessed)} unprocessed documents")
                
                for doc in unprocessed:
                    await self.process_document(dict(doc))
            
            return len(unprocessed)
                
        finally:
            await conn.close()
    
    async def process_document(self, doc: Dict[str, Any]):
        """Process a single document through the complete pipeline"""
        # Handle both dict and asyncpg.Record objects
        if hasattr(doc, 'items'):
            doc_dict = dict(doc)
        else:
            doc_dict = doc
            
        # Ensure metadata is a dict
        if isinstance(doc_dict.get('metadata'), str):
            import json
            try:
                doc_dict['metadata'] = json.loads(doc_dict['metadata'])
            except:
                doc_dict['metadata'] = {}
        elif doc_dict.get('metadata') is None:
            doc_dict['metadata'] = {}
            
        logger.info(f"📄 Processing document: {doc_dict.get('title', 'Untitled')[:50]}...")
        
        try:
            # Extract entities
            entities = await self.extract_entities_advanced(doc_dict.get('content', ''))
            
            # Generate embeddings
            embeddings = await self.generate_embeddings(doc_dict.get('content', ''))
            
            # Create knowledge graph
            relationships = await self.create_knowledge_graph(doc_dict, entities)
            
            # Store in vector database
            await self.store_in_vector_db(doc_dict, embeddings, entities)
            
            # Update metadata
            await self.update_document_metadata(doc_dict['id'], {
                "entities_extracted": True,
                "entity_count": len(entities),
                "relationships_created": True,
                "relationship_count": len(relationships),
                "embeddings_generated": True,
                "embedding_dimensions": len(embeddings),
                "processed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"✅ Processed: {doc_dict.get('title', 'Untitled')[:50]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process {doc_dict.get('id', 'unknown')}: {e}")
            return False
    
    async def extract_entities_advanced(self, content: str) -> List[Tuple[str, str, Dict]]:
        """Extract entities using Ollama with fallback to regex"""
        entities = []
        
        # Try Ollama first
        try:
            extraction_prompt = f"""Extract named entities from this text. 
            Return JSON array: [{{"type": "TECHNOLOGY", "name": "Docker", "context": "containerization"}}]
            
            Text: {content[:2000]}
            
            JSON:"""
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": extraction_prompt,
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 512}
                    }
                )
                
                if response.status_code == 200:
                    result_text = response.json().get("response", "[]")
                    # Extract JSON from response
                    start = result_text.find('[')
                    end = result_text.rfind(']') + 1
                    if start >= 0 and end > start:
                        extracted = json.loads(result_text[start:end])
                        for entity in extracted:
                            if isinstance(entity, dict) and 'type' in entity and 'name' in entity:
                                entities.append((
                                    entity['type'],
                                    entity['name'],
                                    {"context": entity.get('context', '')}
                                ))
        except:
            pass
        
        # Fallback to regex
        if not entities:
            # Extract technologies
            tech_keywords = ['Docker', 'Python', 'FastAPI', 'PostgreSQL', 'Neo4j', 'Redis', 'Ollama', 'Qdrant']
            for tech in tech_keywords:
                if tech.lower() in content.lower():
                    entities.append(("TECHNOLOGY", tech, {"source": "keyword"}))
            
            # Extract URLs
            url_pattern = r'https?://[^\s<>"\']+'
            for match in re.findall(url_pattern, content)[:5]:
                entities.append(("URL", match, {"source": "regex"}))
        
        # Deduplicate and limit
        unique = {}
        for entity_type, entity_name, metadata in entities:
            key = f"{entity_type}:{entity_name.lower()}"
            if key not in unique:
                unique[key] = (entity_type, entity_name, metadata)
        
        return list(unique.values())[:30]
    
    async def generate_embeddings(self, content: str) -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/embed",
                    json={
                        "model": self.embedding_model,
                        "input": content[:8000]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) > 0:
                        return embeddings[0] if isinstance(embeddings[0], list) else embeddings
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")

        return []

    async def infer_entity_relationships(
        self, content: str, entities: List[Tuple]
    ) -> List[Tuple[str, str, str, str]]:
        """Infer relationships between entities using the chat model."""
        if not content or not entities:
            return []

        entity_list = ", ".join(name for _, name, _ in entities[:20])
        prompt = f"""Given the following text and list of entities, identify any relationships between the entities.
Return a JSON array where each item is {{"source": "EntityA", "target": "EntityB", "relationship": "RELATION", "context": "short reason"}}.

Text:
{content[:2000]}

Entities: {entity_list}

JSON:"""

        relationships: List[Tuple[str, str, str, str]] = []

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.chat_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 512},
                    },
                )

            if response.status_code == 200:
                resp_text = response.json().get("response", "[]")
                start = resp_text.find("[")
                end = resp_text.rfind("]") + 1
                if start >= 0 and end > start:
                    try:
                        data = json.loads(resp_text[start:end])
                        for item in data:
                            if all(k in item for k in ["source", "target", "relationship"]):
                                relationships.append(
                                    (
                                        item["source"],
                                        item["target"],
                                        item["relationship"],
                                        item.get("context", ""),
                                    )
                                )
                    except Exception:
                        pass
        except Exception:
            pass

        return relationships

    async def create_knowledge_graph(self, doc: Dict, entities: List[Tuple]) -> List[Dict]:
        """Create knowledge graph relationships in Neo4j"""
        relationships = []

        inferred = await self.infer_entity_relationships(doc.get("content", ""), entities)

        try:
            driver = AsyncGraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )

            async with driver.session() as session:
                # Create document node
                await session.run(
                    """
                    MERGE (d:Document {id: $id})
                    SET d.title = $title,
                        d.project = $project,
                        d.doc_type = $doc_type,
                        d.updated_at = datetime()
                    """,
                    {
                        "id": str(doc['id']),
                        "title": doc['title'],
                        "project": doc['project'],
                        "doc_type": doc['doc_type'],
                    },
                )

                # Create entities and document->entity relationships
                for entity_type, entity_name, _ in entities:
                    await session.run(
                        """
                        MERGE (e:Entity {name: $name, type: $type})
                        SET e.updated_at = datetime()
                        """,
                        {"name": entity_name, "type": entity_type},
                    )

                    await session.run(
                        """
                        MATCH (d:Document {id: $doc_id})
                        MATCH (e:Entity {name: $entity_name, type: $entity_type})
                        MERGE (d)-[r:MENTIONS]->(e)
                        SET r.count = coalesce(r.count, 0) + 1
                        """,
                        {
                            "doc_id": str(doc['id']),
                            "entity_name": entity_name,
                            "entity_type": entity_type,
                        },
                    )

                    relationships.append(
                        {"type": "MENTIONS", "entity": entity_name}
                    )

                # Create inferred entity relationships
                for source, target, rel, context in inferred:
                    rel_type = re.sub(r"[^A-Z_]", "", rel.upper()) or "RELATED_TO"
                    await session.run(
                        f"""
                        MATCH (e1:Entity {{name: $source}})
                        MATCH (e2:Entity {{name: $target}})
                        MERGE (e1)-[r:{rel_type}]->(e2)
                        SET r.context = $context,
                            r.source_doc = $doc_id,
                            r.updated_at = datetime()
                        """,
                        {
                            "source": source,
                            "target": target,
                            "context": context,
                            "doc_id": str(doc['id']),
                        },
                    )
                    relationships.append(
                        {
                            "type": rel_type,
                            "source": source,
                            "target": target,
                            "context": context,
                        }
                    )

            await driver.close()
        except Exception as e:
            logger.warning(f"Neo4j operations failed: {e}")

        return relationships
    
    async def store_in_vector_db(self, doc: Dict, embeddings: List[float], entities: List[Tuple]):
        """Store in Qdrant vector database"""
        if not embeddings:
            return
        
        try:
            from qdrant_client import AsyncQdrantClient
            from qdrant_client.models import PointStruct, VectorParams, Distance
            
            client = AsyncQdrantClient(url=self.qdrant_url)
            
            # Ensure collection exists
            collection_name = "fk2_documents"
            try:
                await client.get_collection(collection_name)
            except:
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=len(embeddings),
                        distance=Distance.COSINE
                    )
                )
            
            # Store vector
            point = PointStruct(
                id=str(uuid4()),
                vector=embeddings,
                payload={
                    "document_id": str(doc['id']),
                    "title": doc['title'],
                    "project": doc['project'],
                    "entities": [{"type": t, "name": n} for t, n, _ in entities[:10]]
                }
            )
            
            await client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
        except Exception as e:
            logger.warning(f"Qdrant storage failed: {e}")
    
    async def update_document_metadata(self, doc_id: str, updates: Dict):
        """Update document metadata"""
        conn = await asyncpg.connect(self.postgres_url)
        
        try:
            existing = await conn.fetchval("""
                SELECT metadata FROM documents WHERE id = $1
            """, doc_id)
            
            metadata = json.loads(existing) if isinstance(existing, str) else (existing or {})
            metadata.update(updates)
            
            await conn.execute("""
                UPDATE documents 
                SET metadata = $2, updated_at = NOW()
                WHERE id = $1
            """, doc_id, json.dumps(metadata))
            
        finally:
            await conn.close()

# Singleton instance
processing_pipeline = AutomaticProcessingPipeline()
