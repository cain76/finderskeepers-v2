"""
Enhanced document ingestion that uses the automatic processing pipeline
"""

import logging
from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime
import json
import asyncpg

from app.core import processing_pipeline

logger = logging.getLogger(__name__)

async def process_document_with_pipeline(doc_data: Dict[str, Any], doc_id: str = None) -> str:
    """
    Process document using the automatic processing pipeline
    This ensures ALL documents get:
    - Advanced entity extraction
    - Full embeddings
    - Complete knowledge graph
    - Metadata tracking
    """
    try:
        if not doc_id:
            doc_id = str(uuid4())
        
        logger.info(f"🚀 Processing document '{doc_data['title']}' with automatic pipeline")
        
        # First, store the document in PostgreSQL (this will trigger the automatic processing)
        conn = await asyncpg.connect(processing_pipeline.postgres_url)
        
        try:
            # Insert document into database
            await conn.execute("""
                INSERT INTO documents (id, title, content, project, doc_type, tags, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    updated_at = NOW()
            """,
                doc_id,
                doc_data['title'],
                doc_data['content'],
                doc_data['project'],
                doc_data.get('doc_type', 'general'),
                doc_data.get('tags', []),
                json.dumps(doc_data.get('metadata', {}))
            )
            
            logger.info(f"📝 Document {doc_id} stored in PostgreSQL")
            
            # Get the document record
            doc = await conn.fetchrow("""
                SELECT id, title, content, project, doc_type, tags, metadata
                FROM documents WHERE id = $1
            """, doc_id)
            
            if doc:
                # Process it immediately through our pipeline
                await processing_pipeline.process_document(dict(doc))
                logger.info(f"✅ Document {doc_id} processed through automatic pipeline")
            
            return doc_id
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Failed to process document with pipeline: {e}")
        raise

async def get_document_with_processing_status(doc_id: str) -> Dict[str, Any]:
    """
    Get document with full processing status
    """
    conn = await asyncpg.connect(processing_pipeline.postgres_url)
    
    try:
        doc = await conn.fetchrow("""
            SELECT 
                id,
                title,
                content,
                project,
                doc_type,
                tags,
                metadata,
                embeddings IS NOT NULL as has_embeddings,
                created_at,
                updated_at
            FROM documents
            WHERE id = $1
        """, doc_id)
        
        if doc:
            doc_dict = dict(doc)
            metadata = json.loads(doc_dict['metadata']) if isinstance(doc_dict['metadata'], str) else doc_dict.get('metadata', {})
            
            # Add processing status
            doc_dict['processing_status'] = {
                'entities_extracted': metadata.get('entities_extracted', False),
                'entity_count': metadata.get('entity_count', 0),
                'embeddings_generated': metadata.get('embeddings_generated', False) or doc_dict['has_embeddings'],
                'relationships_created': metadata.get('relationships_created', False),
                'relationship_count': metadata.get('relationship_count', 0),
                'processed_at': metadata.get('processed_at'),
                'fully_processed': all([
                    metadata.get('entities_extracted', False),
                    metadata.get('embeddings_generated', False) or doc_dict['has_embeddings'],
                    metadata.get('relationships_created', False)
                ])
            }
            
            return doc_dict
        
        return None
        
    finally:
        await conn.close()
