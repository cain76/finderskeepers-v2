"""
FindersKeepers v2 - Background Document Processing Scheduler
Automatically processes unprocessed documents in batches at regular intervals
For bitcain.net - AI GOD MODE
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class BackgroundDocumentProcessor:
    """Periodic background task to process unprocessed documents"""
    
    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.processed_total = 0
        self.last_run = None
        
        # Configuration from environment or defaults
        self.interval_minutes = int(os.getenv("PROCESS_INTERVAL_MINUTES", "5"))
        self.batch_size = int(os.getenv("PROCESS_BATCH_SIZE", "50"))
        self.enabled = os.getenv("ENABLE_BACKGROUND_PROCESSING", "true").lower() == "true"
        
        logger.info(f"📊 Background processor configured:")
        logger.info(f"  - Interval: {self.interval_minutes} minutes")
        logger.info(f"  - Batch size: {self.batch_size} documents")
        logger.info(f"  - Enabled: {self.enabled}")
    
    async def start(self):
        """Start the background processing task"""
        if not self.enabled:
            logger.info("⏸️ Background processing is disabled")
            return
        
        if self.running:
            logger.warning("⚠️ Background processor already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_periodic_processing())
        logger.info("✅ Background document processor started")
    
    async def stop(self):
        """Stop the background processing task"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("⏹️ Background document processor stopped")
        logger.info(f"📊 Total documents processed: {self.processed_total}")
    
    async def _run_periodic_processing(self):
        """Main loop for periodic document processing"""
        logger.info("🔄 Starting periodic document processing loop")
        
        # Initial delay to let the system fully start
        await asyncio.sleep(30)
        
        while self.running:
            try:
                # Process documents
                processed_count = await self._process_batch()
                
                if processed_count > 0:
                    self.processed_total += processed_count
                    logger.info(f"✅ Batch complete: {processed_count} documents processed")
                    logger.info(f"📊 Total processed since startup: {self.processed_total}")
                else:
                    logger.debug("📭 No unprocessed documents found in this batch")
                
                self.last_run = datetime.now()
                
                # Wait for next interval
                await asyncio.sleep(self.interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("🛑 Background processing cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in background processing: {e}")
                # Wait before retrying
                await asyncio.sleep(60)
    
    async def _process_batch(self):
        """Process a batch of unprocessed documents"""
        try:
            from app.core.automatic_processing import AutomaticProcessingPipeline
            
            pipeline = AutomaticProcessingPipeline()
            
            logger.info(f"🔍 Checking for unprocessed documents (batch size: {self.batch_size})")
            
            # Process unprocessed documents
            processed_count = await pipeline.process_unprocessed_documents(limit=self.batch_size)
            
            if processed_count > 0:
                logger.info(f"📄 Processed {processed_count} documents in this batch")
                
                # Log statistics
                await self._log_processing_stats(processed_count)
            
            return processed_count
            
        except Exception as e:
            logger.error(f"❌ Failed to process batch: {e}")
            return 0
    
    async def _log_processing_stats(self, batch_count: int):
        """Log processing statistics to help track progress"""
        try:
            import asyncpg
            
            postgres_url = os.getenv("POSTGRES_URL", 
                                    "postgresql://finderskeepers:fk2025secure@postgres:5432/finderskeepers_v2")
            
            conn = await asyncpg.connect(postgres_url)
            
            try:
                # Get current statistics
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(CASE WHEN embeddings IS NOT NULL THEN 1 END) as processed_documents,
                        COUNT(CASE WHEN embeddings IS NULL THEN 1 END) as unprocessed_documents
                    FROM documents
                """)
                
                if stats:
                    total = stats['total_documents']
                    processed = stats['processed_documents']
                    unprocessed = stats['unprocessed_documents']
                    
                    progress_percent = (processed / total * 100) if total > 0 else 0
                    
                    logger.info(f"📈 Processing Progress:")
                    logger.info(f"  - Total documents: {total}")
                    logger.info(f"  - Processed: {processed} ({progress_percent:.1f}%)")
                    logger.info(f"  - Remaining: {unprocessed}")
                    
                    if unprocessed > 0:
                        estimated_batches = unprocessed // self.batch_size
                        estimated_time_hours = (estimated_batches * self.interval_minutes) / 60
                        logger.info(f"  - Estimated time to complete: {estimated_time_hours:.1f} hours")
                    else:
                        logger.info(f"  🎉 ALL DOCUMENTS PROCESSED!")
                        
            finally:
                await conn.close()
                
        except Exception as e:
            logger.warning(f"Could not log statistics: {e}")
    
    async def force_process_now(self, batch_size: Optional[int] = None):
        """Force immediate processing of a batch (for admin panel)"""
        size = batch_size or self.batch_size
        logger.info(f"⚡ Force processing {size} documents immediately")
        processed = await self._process_batch()
        return processed
    
    def get_status(self):
        """Get current processor status"""
        return {
            "running": self.running,
            "enabled": self.enabled,
            "interval_minutes": self.interval_minutes,
            "batch_size": self.batch_size,
            "processed_total": self.processed_total,
            "last_run": self.last_run.isoformat() if self.last_run else None
        }

# Global instance
background_processor = BackgroundDocumentProcessor()
