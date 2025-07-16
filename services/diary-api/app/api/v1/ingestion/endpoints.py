"""
Ingestion API endpoints for universal content processing
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging
import json
import uuid
import asyncio
from pathlib import Path
import aiofiles

from .services import IngestionService
from .models import (
    IngestionRequest, 
    IngestionStatus, 
    IngestionResult,
    BatchIngestionRequest,
    URLIngestionRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ingestion", tags=["Ingestion"])

# WebSocket connections for progress tracking
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
    async def send_progress(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except:
                # Connection lost, remove it
                self.disconnect(client_id)

manager = ConnectionManager()
ingestion_service = IngestionService()

# ========================================
# SINGLE FILE UPLOAD
# ========================================

@router.post("/single", response_model=IngestionResult)
async def ingest_single_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project: str = Form(...),
    tags: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    process_async: bool = Form(True)
):
    """
    Ingest a single file of any supported format.
    
    Supported formats:
    - Documents: PDF, DOCX, XLSX, PPTX, TXT, MD, CSV, JSON, XML, YAML
    - Images: JPG, PNG, GIF, BMP (with OCR)
    - Audio: MP3, WAV, M4A, OGG (with transcription)
    - Video: MP4, AVI, MOV, MKV (audio extraction + transcription)
    - Archives: ZIP, TAR, GZ (recursive processing)
    """
    try:
        # Generate ingestion ID
        ingestion_id = f"ing_{uuid.uuid4().hex[:8]}"
        
        # Parse tags and metadata
        tag_list = tags.split(",") if tags else []
        meta_dict = json.loads(metadata) if metadata else {}
        
        # Save uploaded file temporarily
        temp_dir = Path("/tmp/fk2_ingestion")
        temp_dir.mkdir(exist_ok=True)
        
        file_path = temp_dir / f"{ingestion_id}_{file.filename}"
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create ingestion request
        request = IngestionRequest(
            ingestion_id=ingestion_id,
            file_path=str(file_path),
            filename=file.filename,
            project=project,
            tags=tag_list,
            metadata=meta_dict,
            file_size=len(content),
            mime_type=file.content_type
        )
        
        # Process synchronously or async
        if process_async:
            background_tasks.add_task(
                ingestion_service.process_file,
                request,
                lambda progress: asyncio.create_task(
                    manager.send_progress(ingestion_id, progress)
                )
            )
            
            return IngestionResult(
                ingestion_id=ingestion_id,
                status=IngestionStatus.QUEUED,
                message=f"File '{file.filename}' queued for processing",
                progress=0,
                details={"file_size": len(content), "mime_type": file.content_type}
            )
        else:
            # Process synchronously
            result = await ingestion_service.process_file(request)
            return result
            
    except Exception as e:
        logger.error(f"Single file ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# BATCH FILE UPLOAD
# ========================================

@router.post("/batch", response_model=List[IngestionResult])
async def ingest_batch_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    project: str = Form(...),
    tags: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """
    Ingest multiple files in a single batch operation.
    Files are processed concurrently for optimal performance.
    """
    try:
        # Generate batch ID
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        results = []
        
        # Parse common tags and metadata
        tag_list = tags.split(",") if tags else []
        meta_dict = json.loads(metadata) if metadata else {}
        meta_dict["batch_id"] = batch_id
        
        # Process each file
        for file in files:
            ingestion_id = f"ing_{uuid.uuid4().hex[:8]}"
            
            # Save file temporarily
            temp_dir = Path("/tmp/fk2_ingestion")
            temp_dir.mkdir(exist_ok=True)
            
            file_path = temp_dir / f"{ingestion_id}_{file.filename}"
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Create ingestion request
            request = IngestionRequest(
                ingestion_id=ingestion_id,
                file_path=str(file_path),
                filename=file.filename,
                project=project,
                tags=tag_list,
                metadata=meta_dict,
                file_size=len(content),
                mime_type=file.content_type,
                batch_id=batch_id
            )
            
            # Queue for background processing
            background_tasks.add_task(
                ingestion_service.process_file,
                request,
                lambda progress: asyncio.create_task(
                    manager.send_progress(batch_id, progress)
                )
            )
            
            results.append(IngestionResult(
                ingestion_id=ingestion_id,
                status=IngestionStatus.QUEUED,
                message=f"File '{file.filename}' queued in batch {batch_id}",
                progress=0,
                details={"batch_id": batch_id, "file_size": len(content)}
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# URL INGESTION
# ========================================

@router.post("/url", response_model=IngestionResult)
async def ingest_from_url(
    background_tasks: BackgroundTasks,
    request: URLIngestionRequest
):
    """
    Ingest content from a URL using intelligent web scraping.
    Supports single pages or recursive crawling of entire sites.
    """
    try:
        # Generate ingestion ID
        ingestion_id = f"url_{uuid.uuid4().hex[:8]}"
        
        # Queue URL processing
        background_tasks.add_task(
            ingestion_service.process_url,
            ingestion_id,
            request,
            lambda progress: asyncio.create_task(
                manager.send_progress(ingestion_id, progress)
            )
        )
        
        return IngestionResult(
            ingestion_id=ingestion_id,
            status=IngestionStatus.QUEUED,
            message=f"URL '{request.url}' queued for processing",
            progress=0,
            details={
                "url": request.url,
                "recursive": request.recursive,
                "max_depth": request.max_depth
            }
        )
        
    except Exception as e:
        logger.error(f"URL ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# FOLDER UPLOAD
# ========================================

@router.post("/folder")
async def ingest_folder(
    background_tasks: BackgroundTasks,
    folder_path: str = Form(...),
    project: str = Form(...),
    recursive: bool = Form(True),
    file_patterns: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    """
    Ingest all files from a local folder path.
    Supports recursive processing and file pattern filtering.
    """
    try:
        # Validate folder path
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise HTTPException(status_code=400, detail="Invalid folder path")
        
        # Generate batch ID
        batch_id = f"folder_{uuid.uuid4().hex[:8]}"
        
        # Parse parameters
        patterns = file_patterns.split(",") if file_patterns else ["*"]
        tag_list = tags.split(",") if tags else []
        
        # Queue folder processing
        background_tasks.add_task(
            ingestion_service.process_folder,
            batch_id,
            folder,
            project,
            recursive,
            patterns,
            tag_list,
            lambda progress: asyncio.create_task(
                manager.send_progress(batch_id, progress)
            )
        )
        
        return {
            "batch_id": batch_id,
            "status": "queued",
            "message": f"Folder '{folder_path}' queued for processing",
            "details": {
                "recursive": recursive,
                "patterns": patterns
            }
        }
        
    except Exception as e:
        logger.error(f"Folder ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# PROGRESS TRACKING
# ========================================

@router.websocket("/progress/{client_id}")
async def websocket_progress(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time progress tracking.
    Connect with ingestion_id or batch_id to receive updates.
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@router.get("/status/{ingestion_id}")
async def get_ingestion_status(ingestion_id: str):
    """Get the current status of an ingestion task"""
    try:
        status = await ingestion_service.get_status(ingestion_id)
        if not status:
            raise HTTPException(status_code=404, detail="Ingestion not found")
        return status
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# SUPPORTED FORMATS
# ========================================

@router.get("/formats")
async def get_supported_formats():
    """Get list of all supported file formats and their processing methods"""
    return {
        "documents": {
            "pdf": {"method": "PyMuPDF4LLM + OCR fallback", "extensions": [".pdf"]},
            "word": {"method": "python-docx", "extensions": [".docx", ".doc"]},
            "excel": {"method": "openpyxl + pandas", "extensions": [".xlsx", ".xls", ".csv"]},
            "powerpoint": {"method": "python-pptx", "extensions": [".pptx", ".ppt"]},
            "text": {"method": "Direct parsing", "extensions": [".txt", ".md", ".rst", ".log"]},
            "code": {"method": "Syntax-aware parsing", "extensions": [".py", ".js", ".java", ".cpp", ".go", ".rs"]},
            "structured": {"method": "JSON/XML parsers", "extensions": [".json", ".xml", ".yaml", ".yml"]}
        },
        "images": {
            "photos": {"method": "EasyOCR + Vision analysis", "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]},
            "screenshots": {"method": "Tesseract + preprocessing", "extensions": [".png", ".jpg"]},
            "scanned": {"method": "Document OCR pipeline", "extensions": [".tiff", ".tif"]}
        },
        "audio": {
            "speech": {"method": "OpenAI Whisper", "extensions": [".mp3", ".wav", ".m4a", ".ogg", ".flac"]},
            "podcasts": {"method": "WhisperX + diarization", "extensions": [".mp3", ".m4a"]}
        },
        "video": {
            "general": {"method": "ffmpeg + Whisper", "extensions": [".mp4", ".avi", ".mov", ".mkv", ".webm"]}
        },
        "archives": {
            "compressed": {"method": "Recursive extraction", "extensions": [".zip", ".tar", ".gz", ".rar", ".7z"]}
        },
        "web": {
            "urls": {"method": "HTTP fetch + Unstructured.io", "patterns": ["http://*", "https://*"]},
            "social": {"method": "API extraction", "platforms": ["twitter.com", "linkedin.com"]}
        }
    }

# ========================================
# HEALTH CHECK
# ========================================

@router.get("/health")
async def ingestion_health():
    """Check health of ingestion service and dependencies"""
    try:
        health = await ingestion_service.health_check()
        return {
            "status": "healthy" if health["all_healthy"] else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": health
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }