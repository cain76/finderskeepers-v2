"""
Universal Knowledge Ingestion Engine for FindersKeepers v2

This module provides comprehensive document ingestion capabilities supporting 50+ file formats
with intelligent processing, multi-database storage, and real-time progress tracking.

Key Features:
- Universal format support (documents, images, audio, video, archives, code)
- Smart format detection and optimal processing method selection
- Multi-database storage (PostgreSQL + Qdrant + Neo4j)
- Real-time WebSocket progress tracking
- Batch processing with concurrency controls
- OCR for images, transcription for audio/video
- Knowledge graph generation with entity extraction
"""

from .endpoints import router as ingestion_router
from .services import IngestionService
from .storage import StorageService
from .format_detector import FormatDetector
from .processors import DocumentProcessor
from .models import (
    IngestionRequest,
    IngestionResult,
    IngestionStatus,
    FileFormat,
    ProcessingMethod
)

__all__ = [
    "ingestion_router",
    "IngestionService",
    "StorageService", 
    "FormatDetector",
    "DocumentProcessor",
    "IngestionRequest",
    "IngestionResult",
    "IngestionStatus",
    "FileFormat",
    "ProcessingMethod"
]