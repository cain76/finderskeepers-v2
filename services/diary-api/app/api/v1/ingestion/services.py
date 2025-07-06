"""
Main ingestion service orchestrating the processing pipeline
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import json
import httpx

from .models import (
    IngestionRequest, 
    IngestionStatus,
    IngestionResult, 
    URLIngestionRequest,
    ProcessingProgress,
    ProcessedChunk,
    DocumentMetadata
)
from .format_detector import FormatDetector
from .processors import DocumentProcessor
from .storage import StorageService

logger = logging.getLogger(__name__)

class IngestionService:
    """Main service for orchestrating document ingestion"""
    
    def __init__(self):
        self.format_detector = FormatDetector()
        self.processor = DocumentProcessor()
        self.storage = StorageService()
        self.active_tasks: Dict[str, Dict] = {}
        
    async def process_file(
        self, 
        request: IngestionRequest,
        progress_callback: Optional[Callable] = None
    ) -> IngestionResult:
        """
        Process a single file through the ingestion pipeline
        """
        start_time = datetime.utcnow()
        
        try:
            # Update status
            await self._update_progress(
                request.ingestion_id, 
                IngestionStatus.PROCESSING,
                0,
                "Starting file processing",
                progress_callback
            )
            
            # Detect format
            format_type, processing_method, detection_metadata = self.format_detector.detect_format(
                request.file_path
            )
            
            await self._update_progress(
                request.ingestion_id,
                IngestionStatus.PROCESSING,
                10,
                f"Detected format: {format_type.value}",
                progress_callback,
                {"format": format_type.value, "method": processing_method.value}
            )
            
            # Process document
            chunks, doc_metadata = await self.processor.process(
                request.file_path,
                format_type,
                processing_method,
                detection_metadata
            )
            
            await self._update_progress(
                request.ingestion_id,
                IngestionStatus.CHUNKING,
                30,
                f"Created {len(chunks)} chunks",
                progress_callback,
                {"chunks": len(chunks)}
            )
            
            # Generate embeddings for chunks
            chunks_with_embeddings = await self._generate_embeddings(chunks)
            
            await self._update_progress(
                request.ingestion_id,
                IngestionStatus.EMBEDDING,
                60,
                "Generated embeddings",
                progress_callback
            )
            
            # Store in databases
            document_id = await self.storage.store_document(
                request,
                doc_metadata,
                chunks_with_embeddings
            )
            
            await self._update_progress(
                request.ingestion_id,
                IngestionStatus.STORING,
                90,
                "Stored in knowledge base",
                progress_callback,
                {"document_id": document_id}
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Final result
            result = IngestionResult(
                ingestion_id=request.ingestion_id,
                status=IngestionStatus.COMPLETED,
                message=f"Successfully processed {request.filename}",
                progress=100,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                processing_time=processing_time,
                document_id=document_id,
                chunks_created=len(chunks),
                total_tokens=sum(c.token_count for c in chunks),
                embeddings_generated=True,
                details={
                    "format": format_type.value,
                    "method": processing_method.value,
                    "file_size": request.file_size,
                    "chunks": len(chunks)
                }
            )
            
            await self._update_progress(
                request.ingestion_id,
                IngestionStatus.COMPLETED,
                100,
                "Processing complete",
                progress_callback,
                result.dict()
            )
            
            # Clean up temporary file
            if os.path.exists(request.file_path):
                os.remove(request.file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Ingestion failed for {request.ingestion_id}: {e}")
            
            # Update error status
            result = IngestionResult(
                ingestion_id=request.ingestion_id,
                status=IngestionStatus.FAILED,
                message="Processing failed",
                progress=0,
                started_at=start_time,
                error=str(e),
                error_details={"exception": type(e).__name__}
            )
            
            await self._update_progress(
                request.ingestion_id,
                IngestionStatus.FAILED,
                0,
                f"Error: {str(e)}",
                progress_callback,
                result.dict()
            )
            
            return result

    async def process_url(
        self,
        ingestion_id: str,
        request: URLIngestionRequest,
        progress_callback: Optional[Callable] = None
    ) -> IngestionResult:
        """Process content from URL"""
        start_time = datetime.utcnow()
        
        try:
            await self._update_progress(
                ingestion_id,
                IngestionStatus.PROCESSING,
                0,
                f"Fetching content from {request.url}",
                progress_callback
            )
            
            # Use Crawl4AI or similar for web scraping
            content = await self._fetch_url_content(request.url)
            
            # Save content to temporary file
            temp_file = Path(f"/tmp/fk2_ingestion/{ingestion_id}_web.html")
            temp_file.parent.mkdir(exist_ok=True)
            temp_file.write_text(content)
            
            # Create file ingestion request
            file_request = IngestionRequest(
                ingestion_id=ingestion_id,
                file_path=str(temp_file),
                filename=f"web_{request.url.replace('/', '_')[:50]}.html",
                project=request.project,
                tags=request.tags + ["web", "url"],
                metadata={**request.metadata, "source_url": request.url},
                file_size=len(content),
                mime_type="text/html"
            )
            
            # Process as file
            result = await self.process_file(file_request, progress_callback)
            
            # Handle recursive crawling if requested
            if request.recursive and request.max_depth > 0:
                # Extract links and queue them
                # This would be implemented with proper URL parsing and queueing
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"URL ingestion failed: {e}")
            return IngestionResult(
                ingestion_id=ingestion_id,
                status=IngestionStatus.FAILED,
                message="URL processing failed",
                progress=0,
                started_at=start_time,
                error=str(e)
            )

    async def process_folder(
        self,
        batch_id: str,
        folder_path: Path,
        project: str,
        recursive: bool,
        patterns: List[str],
        tags: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[IngestionResult]:
        """Process all files in a folder"""
        results = []
        
        try:
            # Find all matching files
            files = []
            if recursive:
                for pattern in patterns:
                    files.extend(folder_path.rglob(pattern))
            else:
                for pattern in patterns:
                    files.extend(folder_path.glob(pattern))
            
            # Filter out directories
            files = [f for f in files if f.is_file()]
            
            await self._update_progress(
                batch_id,
                IngestionStatus.PROCESSING,
                0,
                f"Found {len(files)} files to process",
                progress_callback,
                {"total_files": len(files)}
            )
            
            # Process files concurrently (with limit)
            semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
            
            async def process_with_semaphore(file_path):
                async with semaphore:
                    ingestion_id = f"ing_{hash(str(file_path))}"
                    request = IngestionRequest(
                        ingestion_id=ingestion_id,
                        file_path=str(file_path),
                        filename=file_path.name,
                        project=project,
                        tags=tags + ["folder"],
                        metadata={"batch_id": batch_id, "folder": str(folder_path)},
                        file_size=file_path.stat().st_size,
                        batch_id=batch_id
                    )
                    return await self.process_file(request)
            
            # Process all files
            tasks = [process_with_semaphore(f) for f in files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update final progress
            successful = sum(1 for r in results if isinstance(r, IngestionResult) and r.status == IngestionStatus.COMPLETED)
            await self._update_progress(
                batch_id,
                IngestionStatus.COMPLETED,
                100,
                f"Processed {successful}/{len(files)} files successfully",
                progress_callback,
                {"successful": successful, "total": len(files)}
            )
            
            return [r for r in results if isinstance(r, IngestionResult)]
            
        except Exception as e:
            logger.error(f"Folder processing failed: {e}")
            return results

    async def _generate_embeddings(self, chunks: List[ProcessedChunk]) -> List[ProcessedChunk]:
        """Generate embeddings for chunks using local Ollama"""
        try:
            # Get Ollama client (from main.py pattern)
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
            embedding_model = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for chunk in chunks:
                    try:
                        response = await client.post(
                            f"{ollama_url}/api/embed",
                            json={
                                "model": embedding_model,
                                "input": chunk.content
                            }
                        )
                        if response.status_code == 200:
                            data = response.json()
                            embeddings = data.get("embeddings", [])
                            if embeddings and len(embeddings) > 0:
                                chunk.embeddings = embeddings[0] if isinstance(embeddings[0], list) else embeddings
                    except Exception as e:
                        logger.warning(f"Failed to generate embeddings for chunk {chunk.chunk_id}: {e}")
                        # Continue without embeddings
            
            return chunks
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return chunks without embeddings
            return chunks

    async def _fetch_url_content(self, url: str) -> str:
        """Fetch content from URL"""
        try:
            # In production, use Crawl4AI or similar
            # For now, simple HTTP fetch
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"URL fetch failed: {e}")
            raise

    async def _update_progress(
        self,
        ingestion_id: str,
        status: IngestionStatus,
        progress: float,
        message: str,
        callback: Optional[Callable] = None,
        details: Dict[str, Any] = None
    ):
        """Update and broadcast progress"""
        progress_update = ProcessingProgress(
            ingestion_id=ingestion_id,
            status=status,
            progress=progress,
            current_step=status.value,
            message=message,
            details=details or {}
        )
        
        # Store in active tasks
        self.active_tasks[ingestion_id] = progress_update.dict()
        
        # Call callback if provided
        if callback:
            await callback(progress_update.dict())

    async def get_status(self, ingestion_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of ingestion task"""
        return self.active_tasks.get(ingestion_id)

    async def health_check(self) -> Dict[str, Any]:
        """Check health of ingestion service"""
        health = {
            "format_detector": True,
            "processor": True,
            "storage": await self.storage.health_check(),
            "active_tasks": len(self.active_tasks),
            "ollama": False
        }
        
        # Check Ollama
        try:
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{ollama_url}/api/version")
                health["ollama"] = response.status_code == 200
        except:
            pass
        
        health["all_healthy"] = all(v for k, v in health.items() if k != "active_tasks")
        
        return health