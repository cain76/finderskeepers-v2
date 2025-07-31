"""
Entity extraction endpoint for FindersKeepers v2
Allows automatic entity extraction for individual documents
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import httpx
import logging
from datetime import datetime
from uuid import UUID

from app.database.connection import db_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/entities", tags=["Entity Extraction"])


class EntityExtractionRequest(BaseModel):
    """Request model for entity extraction"""
    document_id: UUID
    force_reprocess: bool = False


class EntityExtractionResponse(BaseModel):
    """Response model for entity extraction"""
    document_id: str
    entities_extracted: int
    relationships_created: int
    status: str
    message: str


async def extract_entities_from_document(doc_id: UUID, doc_title: str, doc_content: str, doc_project: str) -> Dict[str, Any]:
    """Extract entities from a single document using Ollama"""
    
    # Prepare prompt for Ollama
    prompt = f"""Extract entities and relationships from this technical documentation.
Focus on: Technologies, Tools, Services, APIs, Concepts, Projects, Programming Languages.

Document: {doc_title}
Project: {doc_project}
Content: {doc_content[:3000]}

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

    try:
        # Call Ollama API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://fk2_ollama:11434/api/generate",
                json={
                    "model": "llama3:8b",
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1000
                    }
                }
            )
            
            result = response.json()
            response_text = result.get('response', '{}')
            
            # Parse JSON response
            extracted = json.loads(response_text)
            
            if not isinstance(extracted, dict) or 'entities' not in extracted:
                raise ValueError("Invalid extraction format")
                
            return extracted
            
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return {"entities": [], "relationships": []}


@router.post("/extract", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    background_tasks: BackgroundTasks
):
    """Extract entities from a specific document"""
    try:
        # Get document from database
        async with db_manager.get_postgres_connection() as conn:
            doc = await conn.fetchrow("""
                SELECT id, title, content, project, doc_type
                FROM documents
                WHERE id = $1
            """, request.document_id)
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Check if already processed (unless force_reprocess is True)
            if not request.force_reprocess:
                existing = await conn.fetchval("""
                    SELECT COUNT(*) FROM entity_references
                    WHERE reference_id = $1 AND reference_type = 'document'
                """, request.document_id)
                
                if existing > 0:
                    return EntityExtractionResponse(
                        document_id=str(request.document_id),
                        entities_extracted=0,
                        relationships_created=0,
                        status="skipped",
                        message="Document already has entities extracted"
                    )
        
        # Extract entities
        extracted = await extract_entities_from_document(
            doc['id'], doc['title'], doc['content'], doc['project']
        )
        
        entity_count = 0
        rel_count = 0
        
        # Store in Neo4j
        if db_manager.neo4j_driver:
            async with db_manager.neo4j_driver.session() as session:
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
                
                # Create entities
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
                    """, 
                    name=entity['name'], 
                    type=entity.get('type', 'UNKNOWN'),
                    description=entity.get('description', ''),
                    doc_id=str(doc['id']))
                    
                    entity_count += 1
                
                # Create relationships
                for rel in extracted.get('relationships', []):
                    if not (rel.get('from') and rel.get('to')):
                        continue
                        
                    rel_type = rel.get('type', 'RELATES_TO').replace(' ', '_').upper()
                    
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
        async with db_manager.get_postgres_connection() as conn:
            for entity in extracted.get('entities', []):
                if not entity.get('name'):
                    continue
                
                entity_id = f"{entity.get('type', 'UNKNOWN').lower()}_{entity['name'].lower().replace(' ', '_')}"
                
                # Insert/update entity
                await conn.execute("""
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
                
                # Create reference
                await conn.execute("""
                    INSERT INTO entity_references (entity_id, reference_type, reference_id, relevance_score)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                """,
                entity_id,
                'document',
                doc['id'],
                0.9)
        
        return EntityExtractionResponse(
            document_id=str(request.document_id),
            entities_extracted=entity_count,
            relationships_created=rel_count,
            status="success",
            message=f"Successfully extracted {entity_count} entities and {rel_count} relationships"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-batch")
async def extract_entities_batch(
    document_ids: List[UUID],
    background_tasks: BackgroundTasks
):
    """Extract entities from multiple documents"""
    results = []
    
    for doc_id in document_ids:
        try:
            result = await extract_entities(
                EntityExtractionRequest(document_id=doc_id),
                background_tasks
            )
            results.append(result)
        except Exception as e:
            results.append({
                "document_id": str(doc_id),
                "status": "error",
                "message": str(e)
            })
    
    return {
        "processed": len(results),
        "results": results
    }


@router.get("/status/{document_id}")
async def get_entity_status(document_id: UUID):
    """Check if a document has entities extracted"""
    async with db_manager.get_postgres_connection() as conn:
        entity_count = await conn.fetchval("""
            SELECT COUNT(*) FROM entity_references
            WHERE reference_id = $1 AND reference_type = 'document'
        """, document_id)
        
        return {
            "document_id": str(document_id),
            "has_entities": entity_count > 0,
            "entity_count": entity_count
        }