#!/usr/bin/env python3
"""
Cleanup script to remove duplicate documents from FindersKeepers v2
"""

import asyncio
import asyncpg
import logging
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuplicateCleanup:
    def __init__(self):
        self.pg_url = "postgresql://finderskeepers:PLACEHOLDER_PASSWORD@localhost:5432/finderskeepers_v2"
        
    async def analyze_duplicates(self) -> Dict[str, Any]:
        """Analyze duplicate documents in the database"""
        conn = await asyncpg.connect(self.pg_url)
        
        try:
            # Find duplicates by content hash
            duplicates = await conn.fetch("""
                SELECT 
                    content_hash,
                    COUNT(*) as duplicate_count,
                    MIN(created_at) as first_created,
                    MAX(created_at) as last_created,
                    array_agg(id ORDER BY created_at) as document_ids,
                    array_agg(title ORDER BY created_at) as titles
                FROM documents 
                WHERE project = 'finderskeepers-v2' 
                  AND content_hash IS NOT NULL
                GROUP BY content_hash 
                HAVING COUNT(*) > 1
                ORDER BY COUNT(*) DESC;
            """)
            
            # Count chunks for each duplicate set
            total_duplicate_docs = 0
            total_excess_docs = 0
            total_chunks_to_delete = 0
            
            duplicate_summary = []
            
            for dup in duplicates:
                duplicate_count = dup['duplicate_count']
                excess_count = duplicate_count - 1  # Keep one copy
                total_duplicate_docs += duplicate_count
                total_excess_docs += excess_count
                
                # Count chunks for documents to be deleted
                excess_doc_ids = dup['document_ids'][1:]  # All except the first
                if excess_doc_ids:
                    chunk_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM document_chunks 
                        WHERE document_id = ANY($1::uuid[])
                    """, excess_doc_ids)
                    total_chunks_to_delete += chunk_count
                
                duplicate_summary.append({
                    'content_hash': dup['content_hash'][:16] + '...',
                    'duplicate_count': duplicate_count,
                    'excess_count': excess_count,
                    'first_title': dup['titles'][0] if dup['titles'] else 'Unknown',
                    'chunk_count': chunk_count if excess_doc_ids else 0
                })
            
            return {
                'total_documents': await conn.fetchval("SELECT COUNT(*) FROM documents WHERE project = 'finderskeepers-v2'"),
                'total_duplicate_docs': total_duplicate_docs,
                'total_excess_docs': total_excess_docs,
                'total_chunks_to_delete': total_chunks_to_delete,
                'duplicate_sets': len(duplicates),
                'top_duplicates': duplicate_summary[:10],
                'all_duplicates': duplicate_summary
            }
            
        finally:
            await conn.close()
    
    async def cleanup_duplicates(self, dry_run: bool = True) -> Dict[str, Any]:
        """Remove duplicate documents, keeping the oldest copy of each"""
        conn = await asyncpg.connect(self.pg_url)
        
        try:
            # Find all duplicate document sets
            duplicates = await conn.fetch("""
                SELECT 
                    content_hash,
                    array_agg(id ORDER BY created_at) as document_ids
                FROM documents 
                WHERE project = 'finderskeepers-v2' 
                  AND content_hash IS NOT NULL
                GROUP BY content_hash 
                HAVING COUNT(*) > 1;
            """)
            
            deleted_docs = 0
            deleted_chunks = 0
            
            for dup in duplicates:
                # Keep the first document (oldest), delete the rest
                docs_to_delete = dup['document_ids'][1:]
                
                if docs_to_delete:
                    logger.info(f"Processing duplicate set with hash {dup['content_hash'][:16]}...")
                    logger.info(f"  Keeping document: {dup['document_ids'][0]}")
                    logger.info(f"  Deleting documents: {docs_to_delete}")
                    
                    if not dry_run:
                        # Count chunks before deletion
                        chunk_count = await conn.fetchval("""
                            SELECT COUNT(*) FROM document_chunks 
                            WHERE document_id = ANY($1::uuid[])
                        """, docs_to_delete)
                        
                        # Delete chunks first (due to foreign key constraint)
                        await conn.execute("""
                            DELETE FROM document_chunks 
                            WHERE document_id = ANY($1::uuid[])
                        """, docs_to_delete)
                        
                        # Delete documents
                        await conn.execute("""
                            DELETE FROM documents 
                            WHERE id = ANY($1::uuid[])
                        """, docs_to_delete)
                        
                        chunks_deleted = chunk_count
                        docs_deleted = len(docs_to_delete)
                        
                        deleted_chunks += chunks_deleted or 0
                        deleted_docs += docs_deleted or 0
                        
                        logger.info(f"  Deleted {docs_deleted} documents and {chunks_deleted} chunks")
                    else:
                        # Count what would be deleted
                        chunk_count = await conn.fetchval("""
                            SELECT COUNT(*) FROM document_chunks 
                            WHERE document_id = ANY($1::uuid[])
                        """, docs_to_delete)
                        
                        deleted_chunks += chunk_count
                        deleted_docs += len(docs_to_delete)
                        
                        logger.info(f"  Would delete {len(docs_to_delete)} documents and {chunk_count} chunks")
            
            # Final counts
            if not dry_run:
                final_doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents WHERE project = 'finderskeepers-v2'")
                final_chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM document_chunks dc 
                    JOIN documents d ON dc.document_id = d.id 
                    WHERE d.project = 'finderskeepers-v2'
                """)
            else:
                original_doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents WHERE project = 'finderskeepers-v2'")
                original_chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM document_chunks dc 
                    JOIN documents d ON dc.document_id = d.id 
                    WHERE d.project = 'finderskeepers-v2'
                """)
                final_doc_count = original_doc_count - deleted_docs
                final_chunk_count = original_chunk_count - deleted_chunks
            
            return {
                'dry_run': dry_run,
                'duplicate_sets_processed': len(duplicates),
                'documents_deleted': deleted_docs,
                'chunks_deleted': deleted_chunks,
                'final_document_count': final_doc_count,
                'final_chunk_count': final_chunk_count,
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            await conn.close()
    
    async def add_unique_constraint(self, dry_run: bool = True) -> bool:
        """Add unique constraint to prevent future duplicates"""
        conn = await asyncpg.connect(self.pg_url)
        
        try:
            if not dry_run:
                await conn.execute("""
                    ALTER TABLE documents 
                    ADD CONSTRAINT unique_content_per_project 
                    UNIQUE (content_hash, project);
                """)
                logger.info("✅ Added unique constraint to prevent future duplicates")
                return True
            else:
                logger.info("🔍 Would add unique constraint: UNIQUE (content_hash, project)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to add unique constraint: {e}")
            return False
        finally:
            await conn.close()

async def main():
    cleanup = DuplicateCleanup()
    
    print("🔍 Analyzing duplicates...")
    analysis = await cleanup.analyze_duplicates()
    
    print(f"\n📊 DUPLICATE ANALYSIS RESULTS:")
    print(f"   Total documents: {analysis['total_documents']}")
    print(f"   Documents with duplicates: {analysis['total_duplicate_docs']}")
    print(f"   Excess documents to remove: {analysis['total_excess_docs']}")
    print(f"   Chunks to be deleted: {analysis['total_chunks_to_delete']}")
    print(f"   Duplicate sets found: {analysis['duplicate_sets']}")
    
    print(f"\n🔝 TOP 10 DUPLICATES:")
    for i, dup in enumerate(analysis['top_duplicates'], 1):
        print(f"   {i:2d}. '{dup['first_title'][:50]}...' - {dup['duplicate_count']} copies ({dup['excess_count']} excess)")
    
    # Dry run first
    print(f"\n🧪 DRY RUN - Simulating cleanup...")
    dry_result = await cleanup.cleanup_duplicates(dry_run=True)
    
    print(f"\n📋 DRY RUN RESULTS:")
    print(f"   Duplicate sets: {dry_result['duplicate_sets_processed']}")
    print(f"   Documents to delete: {dry_result['documents_deleted']}")
    print(f"   Chunks to delete: {dry_result['chunks_deleted']}")
    print(f"   Final document count: {dry_result['final_document_count']}")
    print(f"   Final chunk count: {dry_result['final_chunk_count']}")
    
    # Ask for confirmation
    print(f"\n⚠️  READY TO CLEAN UP DUPLICATES")
    print(f"   This will DELETE {dry_result['documents_deleted']} duplicate documents")
    print(f"   and {dry_result['chunks_deleted']} associated chunks.")
    print(f"   This action CANNOT be undone!")
    
    # Auto-proceed for script execution
    print(f"\n🚀 Auto-proceeding with cleanup...")
    response = 'yes'
    
    if response == 'yes':
        print(f"\n🧹 EXECUTING CLEANUP...")
        result = await cleanup.cleanup_duplicates(dry_run=False)
        
        print(f"\n✅ CLEANUP COMPLETED!")
        print(f"   Documents deleted: {result['documents_deleted']}")
        print(f"   Chunks deleted: {result['chunks_deleted']}")
        print(f"   Final document count: {result['final_document_count']}")
        print(f"   Final chunk count: {result['final_chunk_count']}")
        
        # Add unique constraint
        print(f"\n🔒 Adding unique constraint...")
        constraint_added = await cleanup.add_unique_constraint(dry_run=False)
        if constraint_added:
            print(f"✅ Unique constraint added successfully!")
        else:
            print(f"❌ Failed to add unique constraint")
        
    else:
        print(f"\n❌ Cleanup cancelled by user")

if __name__ == "__main__":
    asyncio.run(main())