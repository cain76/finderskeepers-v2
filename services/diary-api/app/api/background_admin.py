"""
Background Processor Admin API Endpoints
Control and monitor the automatic document processing scheduler
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/background", tags=["background_processor"])

class ProcessorControlRequest(BaseModel):
    action: str  # start, stop, force_process
    batch_size: Optional[int] = None

class ProcessorConfigUpdate(BaseModel):
    interval_minutes: Optional[int] = None
    batch_size: Optional[int] = None
    enabled: Optional[bool] = None

@router.get("/status")
async def get_processor_status():
    """Get the current status of the background processor"""
    try:
        from app.core.background_scheduler import background_processor
        status = background_processor.get_status()
        
        # Add additional stats if available
        import asyncpg
        import os
        
        postgres_url = os.getenv("POSTGRES_URL", 
                                "postgresql://finderskeepers:fk2025secure@postgres:5432/finderskeepers_v2")
        
        conn = await asyncpg.connect(postgres_url)
        try:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN embeddings IS NOT NULL THEN 1 END) as processed_documents,
                    COUNT(CASE WHEN embeddings IS NULL THEN 1 END) as unprocessed_documents
                FROM documents
            """)
            
            if stats:
                status['document_stats'] = {
                    'total': stats['total_documents'],
                    'processed': stats['processed_documents'],
                    'unprocessed': stats['unprocessed_documents'],
                    'progress_percent': round(stats['processed_documents'] / stats['total_documents'] * 100, 2) if stats['total_documents'] > 0 else 0
                }
                
                # Calculate estimates
                if status['running'] and stats['unprocessed_documents'] > 0:
                    batches_remaining = stats['unprocessed_documents'] // status['batch_size']
                    hours_remaining = (batches_remaining * status['interval_minutes']) / 60
                    status['estimates'] = {
                        'batches_remaining': batches_remaining,
                        'hours_to_complete': round(hours_remaining, 1),
                        'completion_eta': None  # Could calculate actual time
                    }
        finally:
            await conn.close()
        
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Failed to get processor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/control")
async def control_processor(request: ProcessorControlRequest):
    """Control the background processor (start/stop/force)"""
    try:
        from app.core.background_scheduler import background_processor
        
        if request.action == "start":
            await background_processor.start()
            return {"success": True, "message": "Background processor started"}
            
        elif request.action == "stop":
            await background_processor.stop()
            return {"success": True, "message": "Background processor stopped"}
            
        elif request.action == "force_process":
            processed = await background_processor.force_process_now(request.batch_size)
            return {
                "success": True, 
                "message": f"Force processed {processed} documents",
                "processed_count": processed
            }
        else:
            raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
            
    except Exception as e:
        logger.error(f"Failed to control processor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_processor_config(config: ProcessorConfigUpdate):
    """Update background processor configuration"""
    try:
        from app.core.background_scheduler import background_processor
        
        updated = []
        
        if config.interval_minutes is not None:
            background_processor.interval_minutes = config.interval_minutes
            updated.append(f"interval_minutes={config.interval_minutes}")
        
        if config.batch_size is not None:
            background_processor.batch_size = config.batch_size
            updated.append(f"batch_size={config.batch_size}")
        
        if config.enabled is not None:
            background_processor.enabled = config.enabled
            updated.append(f"enabled={config.enabled}")
            
            # Auto start/stop based on enabled state
            if config.enabled and not background_processor.running:
                await background_processor.start()
                updated.append("processor started")
            elif not config.enabled and background_processor.running:
                await background_processor.stop()
                updated.append("processor stopped")
        
        return {
            "success": True,
            "message": f"Configuration updated: {', '.join(updated)}",
            "current_config": background_processor.get_status()
        }
        
    except Exception as e:
        logger.error(f"Failed to update processor config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-batch")
async def process_batch_immediately(batch_size: int = 50):
    """Immediately process a batch of documents without waiting for the schedule"""
    try:
        from app.core.background_scheduler import background_processor
        
        logger.info(f"📄 Admin requested immediate processing of {batch_size} documents")
        processed = await background_processor.force_process_now(batch_size)
        
        return {
            "success": True,
            "message": f"Successfully processed {processed} documents",
            "processed_count": processed
        }
        
    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))
