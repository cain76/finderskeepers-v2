#!/usr/bin/env python3
"""
Extract entities from documents using Ollama llama3:8b model
and populate Neo4j knowledge graph with relationships
"""

import asyncio
import asyncpg
from neo4j import AsyncGraphDatabase
import httpx
import json
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/media/cain/linux_storage/projects/finderskeepers-v2/logs/entity_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PG_DSN = "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "fk2025neo4j"
OLLAMA_URL = "http://localhost:11434/api/generate"
async def extract_entities_from_documents():
    """Use Ollama llama3:8b to extract entities from all documents"""
    
    # Database connections
    logger.info("Connecting to databases...")
    pg_conn = await asyncpg.connect(PG_DSN)
    neo4j_driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    
    try:
        # Get documents that need entity extraction
        # Check entity_references table to find documents without entities
        docs = await pg_conn.fetch("""
            SELECT d.id, d.title, d.content, d.project, d.doc_type 
            FROM documents d
            WHERE NOT EXISTS (
                SELECT 1 FROM entity_references er 
                WHERE er.reference_id = d.id 
                AND er.reference_type = 'document'
            )
            AND d.project IS NOT NULL
            AND d.content IS NOT NULL
            AND LENGTH(d.content) > 100  -- Skip very short documents
            ORDER BY d.created_at DESC
            LIMIT 100  -- Process in batches
        """)
        
        logger.info(f"Processing {len(docs)} documents for entity extraction...")
        
        success_count = 0
        error_count = 0        
        for doc in docs:
            try:
                # Prepare prompt for Ollama
                prompt = f"""Extract entities and relationships from this technical documentation.
Focus on: Technologies, Tools, Services, APIs, Concepts, Projects, Programming Languages.

Document: {doc['title']}
Project: {doc['project']}
Content: {doc['content'][:3000]}

Return only valid JSON in this exact format:
{{
    "entities": [
        {{"name": "Docker", "type": "TECHNOLOGY", "description": "Container platform"}},
        {{"name": "n8n", "type": "TOOL", "description": "Workflow automation"}}
    ],
    "relationships": [
        {{"from": "n8n", "to": "Docker", "type": "RUNS_ON", "properties": {{"version": "latest"}}}}
    ]
}}

Entity types: TECHNOLOGY, TOOL, SERVICE, API, CONCEPT, PROJECT, LANGUAGE
Relationship types: USES, RUNS_ON, DEPENDS_ON, INTEGRATES_WITH, IMPLEMENTS, PART_OF"""
                
                # Call Ollama API
                logger.info(f"Extracting entities from: {doc['title'][:50]}...")
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(                        OLLAMA_URL,
                        json={
                            "model": "llama3:8b",
                            "prompt": prompt,
                            "format": "json",
                            "stream": False,
                            "options": {
                                "temperature": 0.1,  # Low temperature for consistent output
                                "num_predict": 1000
                            }
                        }
                    )
                    
                    result = response.json()
                    response_text = result.get('response', '{}')
                    
                    # Try to parse JSON response
                    try:
                        extracted = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON decode error for {doc['title']}: {e}")
                        logger.debug(f"Raw response: {response_text[:200]}...")
                        continue
                
                # Validate extracted data
                if not isinstance(extracted, dict) or 'entities' not in extracted:
                    logger.warning(f"Invalid extraction format for {doc['title']}")
                    continue                
                # Store in Neo4j
                async with neo4j_driver.session() as session:
                    # Create document node
                    await session.run("""
                        MERGE (d:Document {id: $id})
                        SET d.title = $title, 
                            d.project = $project,
                            d.created = datetime(),
                            d.type = 'technical_doc',
                            d.doc_type = $doc_type
                    """, id=str(doc['id']), title=doc['title'], project=doc['project'], 
                        doc_type=doc.get('doc_type', 'general'))
                    
                    # Create entities and relationships to document
                    entity_count = 0
                    for entity in extracted.get('entities', []):
                        if not entity.get('name'):
                            continue
                            
                        await session.run("""
                            MERGE (e:Entity {name: $name})
                            SET e.type = $type,
                                e.description = $description,
                                e.updated = datetime()
                            WITH e
                            MATCH (d:Document {id: $doc_id})
                            MERGE (d)-[:CONTAINS {extracted_by: 'llama3:8b', extracted_at: datetime()}]->(e)
                        """,                         name=entity['name'], 
                        type=entity.get('type', 'UNKNOWN'),
                        description=entity.get('description', ''),
                        doc_id=str(doc['id']))
                        
                        entity_count += 1
                    
                    # Create entity-to-entity relationships
                    rel_count = 0
                    for rel in extracted.get('relationships', []):
                        if not (rel.get('from') and rel.get('to')):
                            continue
                            
                        rel_type = rel.get('type', 'RELATES_TO').replace(' ', '_').upper()
                        
                        # Create the relationship with dynamic type
                        query = f"""
                            MERGE (e1:Entity {{name: $from_entity}})
                            MERGE (e2:Entity {{name: $to_entity}})
                            MERGE (e1)-[r:{rel_type}]->(e2)
                            SET r.properties = $props,
                                r.created = datetime(),
                                r.source_doc = $doc_id
                        """
                        
                        await session.run(query, 
                            from_entity=rel['from'], 
                            to_entity=rel['to'], 
                            props=json.dumps(rel.get('properties', {})),
                            doc_id=str(doc['id']))
                        
                        rel_count += 1                
                # Store in PostgreSQL
                for entity in extracted.get('entities', []):
                    if not entity.get('name'):
                        continue
                    
                    # Generate entity ID
                    entity_id = f"{entity.get('type', 'UNKNOWN').lower()}_{entity['name'].lower().replace(' ', '_')}"
                    
                    # First insert/update the entity in knowledge_entities
                    await pg_conn.execute("""
                        INSERT INTO knowledge_entities (entity_id, entity_type, name, properties)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (entity_id) DO UPDATE
                        SET properties = knowledge_entities.properties || EXCLUDED.properties,
                            updated_at = CURRENT_TIMESTAMP
                    """, 
                    entity_id,
                    entity.get('type', 'UNKNOWN'), 
                    entity['name'],
                    json.dumps({
                        'description': entity.get('description', ''),
                        'project': doc['project'],
                        'extracted_by': 'llama3:8b',
                        'metadata': entity
                    }))
                    
                    # Then create the reference to the document
                    await pg_conn.execute("""
                        INSERT INTO entity_references (entity_id, reference_type, reference_id, relevance_score)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT DO NOTHING
                    """,
                    entity_id,
                    'document',
                    doc['id'],
                    0.9)  # High relevance since it's directly extracted
                
                logger.info(f"✅ Extracted {entity_count} entities and {rel_count} relationships from: {doc['title'][:50]}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to process {doc['title']}: {e}")
                error_count += 1
                continue
        
        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Entity Extraction Complete!")
        logger.info(f"✅ Successfully processed: {success_count} documents")
        logger.info(f"❌ Failed: {error_count} documents")        
        # Get statistics
        entity_count = await pg_conn.fetchval("SELECT COUNT(DISTINCT entity_id) FROM knowledge_entities")
        doc_with_entities = await pg_conn.fetchval("""
            SELECT COUNT(DISTINCT reference_id) 
            FROM entity_references 
            WHERE reference_type = 'document'
        """)
        
        # Neo4j statistics
        async with neo4j_driver.session() as session:
            neo4j_stats = await session.run("""
                MATCH (e:Entity)
                WITH COUNT(e) as entity_count
                MATCH ()-[r]->()
                WITH entity_count, COUNT(r) as rel_count
                MATCH (d:Document)
                RETURN entity_count, rel_count, COUNT(d) as doc_count
            """)
            stats = await neo4j_stats.single()
            
            logger.info(f"\n📊 Database Statistics:")
            logger.info(f"PostgreSQL - Unique entities: {entity_count}")
            logger.info(f"PostgreSQL - Documents with entities: {doc_with_entities}")
            logger.info(f"Neo4j - Entities: {stats['entity_count']}")
            logger.info(f"Neo4j - Relationships: {stats['rel_count']}")
            logger.info(f"Neo4j - Documents: {stats['doc_count']}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await pg_conn.close()
        await neo4j_driver.close()
        logger.info("Database connections closed.")


# Main execution
if __name__ == "__main__":
    print("🚀 Starting FindersKeepers v2 Entity Extraction with llama3:8b...")
    print("📝 Logs will be written to: /media/cain/linux_storage/projects/finderskeepers-v2/logs/entity_extraction.log")
    asyncio.run(extract_entities_from_documents())