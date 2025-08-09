#!/usr/bin/env python3
"""
Emergency bulk embedding processor for FindersKeepers v2
Processes unembedded documents directly using the database
"""

import asyncio
import asyncpg
import httpx
import json
import logging
from typing import List
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BulkEmbeddingProcessor:
    def __init__(self):
        self.db_url = "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
        self.ollama_url = "http://localhost:11434"
        self.embedding_model = "mxbai-embed-large"
        
    async def get_embeddings(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/embed",
                    json={
                        "model": self.embedding_model,
                        "input": text
                    }
                )
                response.raise_for_status()
                data = response.json()
                embeddings = data.get("embeddings", [])
                return embeddings[0] if embeddings and isinstance(embeddings[0], list) else embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []
    
    async def process_batch(self, batch_size: int = 100):
        """Process a batch of unembedded documents"""
        try:
            # Connect to database
            conn = await asyncpg.connect(self.db_url)
            logger.info(f"🔗 Connected to database")
            
            # Get unprocessed documents
            docs = await conn.fetch("""
                SELECT id, title, content 
                FROM documents 
                WHERE embeddings IS NULL 
                ORDER BY created_at ASC 
                LIMIT $1
            """, batch_size)
            
            if not docs:
                logger.info("✅ No unprocessed documents found!")
                await conn.close()
                return 0
                
            logger.info(f"📄 Processing {len(docs)} documents...")
            processed_count = 0
            
            for i, doc in enumerate(docs, 1):
                try:
                    logger.info(f"🔄 Processing {i}/{len(docs)}: {doc['title'][:50]}...")
                    
                    # Generate embeddings
                    embeddings = await self.get_embeddings(doc['content'])
                    
                    if embeddings:
                        # Convert embeddings list to JSON string for PostgreSQL storage
                        embeddings_json = json.dumps(embeddings)
                        
                        # Update document with embeddings
                        await conn.execute("""
                            UPDATE documents 
                            SET embeddings = $1,
                                metadata = COALESCE(metadata, '{}'::jsonb) || $2,
                                updated_at = NOW()
                            WHERE id = $3
                        """, 
                        embeddings_json,  # Store as JSON string, not raw list
                        json.dumps({"embeddings_generated": True, "processed_by": "emergency_script"}),
                        doc['id'])
                        
                        processed_count += 1
                        logger.info(f"✅ Processed: {doc['title'][:50]}... ({processed_count}/{len(docs)})")
                    else:
                        logger.error(f"❌ Failed to generate embeddings for: {doc['title'][:50]}...")
                        
                    # Small delay to avoid overwhelming the system
                    if i % 10 == 0:
                        await asyncio.sleep(1)
                        
                except Exception as doc_error:
                    logger.error(f"❌ Error processing document {doc['id']}: {doc_error}")
                    continue
            
            await conn.close()
            logger.info(f"🎉 Batch complete: {processed_count}/{len(docs)} documents processed")
            return processed_count
            
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            return 0
    
    async def get_unprocessed_count(self):
        """Get count of unprocessed documents"""
        try:
            conn = await asyncpg.connect(self.db_url)
            result = await conn.fetchrow("SELECT COUNT(*) as count FROM documents WHERE embeddings IS NULL")
            await conn.close()
            return result['count']
        except Exception as e:
            logger.error(f"❌ Failed to get count: {e}")
            return 0

async def main():
    processor = BulkEmbeddingProcessor()
    
    # Get initial count
    initial_count = await processor.get_unprocessed_count()
    logger.info(f"📊 Found {initial_count} unprocessed documents")
    
    if initial_count == 0:
        logger.info("✅ No documents need processing!")
        return
    
    total_processed = 0
    batch_num = 1
    
    while True:
        logger.info(f"🚀 Starting batch {batch_num}...")
        
        # Process a batch
        processed = await processor.process_batch(batch_size=100)
        total_processed += processed
        
        if processed == 0:
            logger.info("✅ All documents processed!")
            break
            
        # Check remaining count
        remaining = await processor.get_unprocessed_count()
        logger.info(f"📊 Progress: {total_processed} processed, {remaining} remaining")
        
        batch_num += 1
        
        # Small delay between batches
        await asyncio.sleep(2)
    
    final_count = await processor.get_unprocessed_count()
    logger.info(f"🎉 COMPLETE: Processed {initial_count - final_count} documents. {final_count} remaining.")

if __name__ == "__main__":
    print("🚀 FindersKeepers v2 - Emergency Bulk Embedding Processor")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Processing stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
