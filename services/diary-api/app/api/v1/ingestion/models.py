"""
Data models for the ingestion system
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class IngestionStatus(str, Enum):
    """Status of an ingestion task"""
    QUEUED = "queued"
    PROCESSING = "processing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class FileFormat(str, Enum):
    """Supported file formats"""
    # Documents
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "markdown"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    YAML = "yaml"
    
    # Images
    JPG = "jpg"
    PNG = "png"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    
    # Audio
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    OGG = "ogg"
    FLAC = "flac"
    
    # Video
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"
    
    # Archives
    ZIP = "zip"
    TAR = "tar"
    GZ = "gz"
    RAR = "rar"
    
    # Code
    PYTHON = "py"
    JAVASCRIPT = "js"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"
    RUST = "rs"
    
    # Web
    HTML = "html"
    
    # Other
    UNKNOWN = "unknown"

class ProcessingMethod(str, Enum):
    """Processing methods for different formats"""
    UNSTRUCTURED_IO = "unstructured_io"
    LANGCHAIN_LOADER = "langchain_loader"
    PYMUPDF = "pymupdf"
    EASYOCR = "easyocr"
    TESSERACT = "tesseract"
    WHISPER = "whisper"
    WHISPERX = "whisperx"
    # CRAWL4AI = "crawl4ai"  # REMOVED: Prevented MCP server spawning
    CUSTOM = "custom"

class IngestionRequest(BaseModel):
    """Request model for file ingestion"""
    ingestion_id: str = Field(..., description="Unique ingestion identifier")
    file_path: str = Field(..., description="Path to the file to ingest")
    filename: str = Field(..., description="Original filename")
    project: str = Field(..., description="Project to associate with")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type if available")
    batch_id: Optional[str] = Field(None, description="Batch identifier if part of batch")
    priority: int = Field(default=5, description="Processing priority (1-10)")

class URLIngestionRequest(BaseModel):
    """Request model for URL ingestion"""
    url: str = Field(..., description="URL to ingest")
    project: str = Field(..., description="Project to associate with")
    recursive: bool = Field(default=False, description="Crawl recursively")
    max_depth: int = Field(default=2, description="Maximum crawl depth")
    include_patterns: List[str] = Field(default_factory=list, description="URL patterns to include")
    exclude_patterns: List[str] = Field(default_factory=list, description="URL patterns to exclude")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class BatchIngestionRequest(BaseModel):
    """Request model for batch file ingestion"""
    batch_id: str = Field(..., description="Unique batch identifier")
    files: List[IngestionRequest] = Field(..., description="List of files to process")
    project: str = Field(..., description="Project to associate with")
    concurrent_limit: int = Field(default=5, description="Max concurrent processing")

class ChunkMetadata(BaseModel):
    """Metadata for a document chunk"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    chunk_index: int = Field(..., description="Position in document")
    start_char: int = Field(..., description="Starting character position")
    end_char: int = Field(..., description="Ending character position")
    page_number: Optional[int] = Field(None, description="Page number if applicable")
    section: Optional[str] = Field(None, description="Document section/chapter")

class ProcessedChunk(BaseModel):
    """A processed document chunk with embeddings"""
    chunk_id: str
    content: str
    metadata: ChunkMetadata
    embeddings: Optional[List[float]] = None
    token_count: int
    language: Optional[str] = None

class IngestionResult(BaseModel):
    """Result of an ingestion operation"""
    ingestion_id: str
    status: IngestionStatus
    message: str
    progress: float = Field(ge=0, le=100, description="Progress percentage")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    
    # Success details
    document_id: Optional[str] = None
    chunks_created: int = 0
    total_tokens: int = 0
    embeddings_generated: bool = False
    
    # Error details
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

class DocumentMetadata(BaseModel):
    """Metadata extracted from documents"""
    title: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    pages: Optional[int] = None
    word_count: Optional[int] = None
    language: Optional[str] = None
    format: FileFormat
    processing_method: ProcessingMethod
    
    # Format-specific metadata
    pdf_metadata: Optional[Dict[str, Any]] = None
    image_metadata: Optional[Dict[str, Any]] = None
    audio_metadata: Optional[Dict[str, Any]] = None
    video_metadata: Optional[Dict[str, Any]] = None

class ProcessingProgress(BaseModel):
    """Real-time processing progress update"""
    ingestion_id: str
    status: IngestionStatus
    progress: float
    current_step: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IngestionStats(BaseModel):
    """Statistics for ingestion operations"""
    total_ingested: int
    total_chunks: int
    total_tokens: int
    total_size_bytes: int
    formats_processed: Dict[str, int]
    projects: Dict[str, int]
    processing_times: Dict[str, float]
    error_count: int
    success_rate: float