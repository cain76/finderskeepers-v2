"""
Smart format detection for incoming files
"""

import magic
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, Dict
import logging

from .models import FileFormat, ProcessingMethod

logger = logging.getLogger(__name__)

class FormatDetector:
    """Intelligent file format detection using multiple methods"""
    
    # File extension mappings
    EXTENSION_MAP = {
        # Documents
        '.pdf': FileFormat.PDF,
        '.docx': FileFormat.DOCX, 
        '.doc': FileFormat.DOCX,
        '.xlsx': FileFormat.XLSX,
        '.xls': FileFormat.XLSX,
        '.pptx': FileFormat.PPTX,
        '.ppt': FileFormat.PPTX,
        '.txt': FileFormat.TXT,
        '.md': FileFormat.MD,
        '.markdown': FileFormat.MD,
        '.csv': FileFormat.CSV,
        '.json': FileFormat.JSON,
        '.xml': FileFormat.XML,
        '.yaml': FileFormat.YAML,
        '.yml': FileFormat.YAML,
        
        # Images
        '.jpg': FileFormat.JPG,
        '.jpeg': FileFormat.JPG,
        '.png': FileFormat.PNG,
        '.gif': FileFormat.GIF,
        '.bmp': FileFormat.BMP,
        '.tiff': FileFormat.TIFF,
        '.tif': FileFormat.TIFF,
        
        # Audio
        '.mp3': FileFormat.MP3,
        '.wav': FileFormat.WAV,
        '.m4a': FileFormat.M4A,
        '.ogg': FileFormat.OGG,
        '.flac': FileFormat.FLAC,
        
        # Video
        '.mp4': FileFormat.MP4,
        '.avi': FileFormat.AVI,
        '.mov': FileFormat.MOV,
        '.mkv': FileFormat.MKV,
        '.webm': FileFormat.WEBM,
        
        # Archives
        '.zip': FileFormat.ZIP,
        '.tar': FileFormat.TAR,
        '.gz': FileFormat.GZ,
        '.rar': FileFormat.RAR,
        
        # Code
        '.py': FileFormat.PYTHON,
        '.js': FileFormat.JAVASCRIPT,
        '.java': FileFormat.JAVA,
        '.cpp': FileFormat.CPP,
        '.cc': FileFormat.CPP,
        '.go': FileFormat.GO,
        '.rs': FileFormat.RUST,
        
        # Web
        '.html': FileFormat.HTML,
        '.htm': FileFormat.HTML,
    }
    
    # MIME type mappings
    MIME_MAP = {
        'application/pdf': FileFormat.PDF,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': FileFormat.DOCX,
        'application/msword': FileFormat.DOCX,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': FileFormat.XLSX,
        'application/vnd.ms-excel': FileFormat.XLSX,
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': FileFormat.PPTX,
        'application/vnd.ms-powerpoint': FileFormat.PPTX,
        'text/plain': FileFormat.TXT,
        'text/markdown': FileFormat.MD,
        'text/csv': FileFormat.CSV,
        'application/json': FileFormat.JSON,
        'application/xml': FileFormat.XML,
        'text/xml': FileFormat.XML,
        'application/x-yaml': FileFormat.YAML,
        'text/yaml': FileFormat.YAML,
        
        'image/jpeg': FileFormat.JPG,
        'image/png': FileFormat.PNG,
        'image/gif': FileFormat.GIF,
        'image/bmp': FileFormat.BMP,
        'image/tiff': FileFormat.TIFF,
        
        'audio/mpeg': FileFormat.MP3,
        'audio/wav': FileFormat.WAV,
        'audio/x-wav': FileFormat.WAV,
        'audio/mp4': FileFormat.M4A,
        'audio/ogg': FileFormat.OGG,
        'audio/flac': FileFormat.FLAC,
        
        'video/mp4': FileFormat.MP4,
        'video/x-msvideo': FileFormat.AVI,
        'video/quicktime': FileFormat.MOV,
        'video/x-matroska': FileFormat.MKV,
        'video/webm': FileFormat.WEBM,
        
        'application/zip': FileFormat.ZIP,
        'application/x-tar': FileFormat.TAR,
        'application/gzip': FileFormat.GZ,
        'application/x-rar-compressed': FileFormat.RAR,
        
        # Web
        'text/html': FileFormat.HTML,
        'application/xhtml+xml': FileFormat.HTML,
    }
    
    # Format to processing method mapping
    FORMAT_PROCESSORS = {
        # Documents - Use Unstructured.io for most
        FileFormat.PDF: ProcessingMethod.UNSTRUCTURED_IO,
        FileFormat.DOCX: ProcessingMethod.UNSTRUCTURED_IO,
        FileFormat.XLSX: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.PPTX: ProcessingMethod.UNSTRUCTURED_IO,
        FileFormat.TXT: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.MD: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.CSV: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.JSON: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.XML: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.YAML: ProcessingMethod.LANGCHAIN_LOADER,
        
        # Images - OCR processing
        FileFormat.JPG: ProcessingMethod.EASYOCR,
        FileFormat.PNG: ProcessingMethod.EASYOCR,
        FileFormat.GIF: ProcessingMethod.EASYOCR,
        FileFormat.BMP: ProcessingMethod.EASYOCR,
        FileFormat.TIFF: ProcessingMethod.TESSERACT,
        
        # Audio - Whisper transcription
        FileFormat.MP3: ProcessingMethod.WHISPER,
        FileFormat.WAV: ProcessingMethod.WHISPER,
        FileFormat.M4A: ProcessingMethod.WHISPER,
        FileFormat.OGG: ProcessingMethod.WHISPER,
        FileFormat.FLAC: ProcessingMethod.WHISPER,
        
        # Video - Whisper with ffmpeg
        FileFormat.MP4: ProcessingMethod.WHISPER,
        FileFormat.AVI: ProcessingMethod.WHISPER,
        FileFormat.MOV: ProcessingMethod.WHISPER,
        FileFormat.MKV: ProcessingMethod.WHISPER,
        FileFormat.WEBM: ProcessingMethod.WHISPER,
        
        # Archives - Custom extraction
        FileFormat.ZIP: ProcessingMethod.CUSTOM,
        FileFormat.TAR: ProcessingMethod.CUSTOM,
        FileFormat.GZ: ProcessingMethod.CUSTOM,
        FileFormat.RAR: ProcessingMethod.CUSTOM,
        
        # Code - Syntax aware
        FileFormat.PYTHON: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.JAVASCRIPT: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.JAVA: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.CPP: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.GO: ProcessingMethod.LANGCHAIN_LOADER,
        FileFormat.RUST: ProcessingMethod.LANGCHAIN_LOADER,
        
        # Web - Use Unstructured.io for HTML (NOT CRAWL4AI to prevent MCP spawning)
        FileFormat.HTML: ProcessingMethod.UNSTRUCTURED_IO,
    }
    
    def __init__(self):
        """Initialize format detector"""
        self._magic_available = self._check_magic()
        
    def _check_magic(self) -> bool:
        """Check if python-magic is available"""
        try:
            magic.Magic()
            return True
        except:
            logger.warning("python-magic not available, falling back to mimetypes")
            return False
    
    def detect_format(self, file_path: str) -> Tuple[FileFormat, ProcessingMethod, Dict[str, any]]:
        """
        Detect file format using multiple methods
        
        Returns:
            - FileFormat enum
            - ProcessingMethod enum  
            - Detection metadata dict
        """
        path = Path(file_path)
        metadata = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size": path.stat().st_size if path.exists() else 0
        }
        
        # Try extension first (most reliable)
        format_type = self._detect_by_extension(path)
        if format_type != FileFormat.UNKNOWN:
            metadata["detection_method"] = "extension"
            processing_method = self.FORMAT_PROCESSORS.get(format_type, ProcessingMethod.CUSTOM)
            return format_type, processing_method, metadata
        
        # Try MIME type detection
        mime_type = self._detect_mime_type(file_path)
        metadata["mime_type"] = mime_type
        
        if mime_type:
            format_type = self._detect_by_mime(mime_type)
            if format_type != FileFormat.UNKNOWN:
                metadata["detection_method"] = "mime_type"
                processing_method = self.FORMAT_PROCESSORS.get(format_type, ProcessingMethod.CUSTOM)
                return format_type, processing_method, metadata
        
        # Try magic number detection
        if self._magic_available:
            magic_type = self._detect_by_magic(file_path)
            metadata["magic_type"] = magic_type
            format_type = self._parse_magic_result(magic_type)
            if format_type != FileFormat.UNKNOWN:
                metadata["detection_method"] = "magic"
                processing_method = self.FORMAT_PROCESSORS.get(format_type, ProcessingMethod.CUSTOM)
                return format_type, processing_method, metadata
        
        # Fallback to content analysis
        format_type = self._detect_by_content(file_path)
        if format_type != FileFormat.UNKNOWN:
            metadata["detection_method"] = "content_analysis"
            processing_method = self.FORMAT_PROCESSORS.get(format_type, ProcessingMethod.CUSTOM)
            return format_type, processing_method, metadata
        
        # Unknown format
        metadata["detection_method"] = "failed"
        return FileFormat.UNKNOWN, ProcessingMethod.CUSTOM, metadata
    
    def _detect_by_extension(self, path: Path) -> FileFormat:
        """Detect format by file extension"""
        ext = path.suffix.lower()
        return self.EXTENSION_MAP.get(ext, FileFormat.UNKNOWN)
    
    def _detect_mime_type(self, file_path: str) -> Optional[str]:
        """Detect MIME type"""
        try:
            # Try python-magic first
            if self._magic_available:
                mime = magic.Magic(mime=True)
                return mime.from_file(file_path)
        except:
            pass
        
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type
    
    def _detect_by_mime(self, mime_type: str) -> FileFormat:
        """Map MIME type to FileFormat"""
        return self.MIME_MAP.get(mime_type, FileFormat.UNKNOWN)
    
    def _detect_by_magic(self, file_path: str) -> Optional[str]:
        """Use python-magic for deep inspection"""
        try:
            m = magic.Magic()
            return m.from_file(file_path)
        except Exception as e:
            logger.error(f"Magic detection failed: {e}")
            return None
    
    def _parse_magic_result(self, magic_result: Optional[str]) -> FileFormat:
        """Parse magic result string to determine format"""
        if not magic_result:
            return FileFormat.UNKNOWN
        
        magic_lower = magic_result.lower()
        
        # Check for specific patterns
        if 'pdf' in magic_lower:
            return FileFormat.PDF
        elif 'microsoft word' in magic_lower or 'docx' in magic_lower:
            return FileFormat.DOCX
        elif 'microsoft excel' in magic_lower or 'xlsx' in magic_lower:
            return FileFormat.XLSX
        elif 'jpeg' in magic_lower or 'jpg' in magic_lower:
            return FileFormat.JPG
        elif 'png' in magic_lower:
            return FileFormat.PNG
        elif 'mp3' in magic_lower or 'mpeg audio' in magic_lower:
            return FileFormat.MP3
        elif 'mp4' in magic_lower or 'mpeg-4' in magic_lower:
            return FileFormat.MP4
        
        return FileFormat.UNKNOWN
    
    def _detect_by_content(self, file_path: str) -> FileFormat:
        """Analyze file content for format detection"""
        try:
            # Read first few bytes
            with open(file_path, 'rb') as f:
                header = f.read(16)
            
            # Check for known file signatures
            if header.startswith(b'%PDF'):
                return FileFormat.PDF
            elif header.startswith(b'PK\x03\x04'):
                # Could be ZIP or Office document
                if self._is_office_document(file_path):
                    return self._detect_office_type(file_path)
                return FileFormat.ZIP
            elif header.startswith(b'\xff\xd8\xff'):
                return FileFormat.JPG
            elif header.startswith(b'\x89PNG'):
                return FileFormat.PNG
            elif header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
                return FileFormat.MP3
            
            # Try text-based detection
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)
                
                if content.startswith('{') and '"' in content:
                    return FileFormat.JSON
                elif content.startswith('<?xml'):
                    return FileFormat.XML
                elif content.startswith('---\n') or '\n---\n' in content[:100]:
                    return FileFormat.YAML
                elif content.lower().startswith('<!doctype html') or content.lower().startswith('<html'):
                    return FileFormat.HTML
                
            except:
                pass
                
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
        
        return FileFormat.UNKNOWN
    
    def _is_office_document(self, file_path: str) -> bool:
        """Check if ZIP file is an Office document"""
        try:
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zf:
                names = zf.namelist()
                return any('[Content_Types].xml' in n for n in names)
        except:
            return False
    
    def _detect_office_type(self, file_path: str) -> FileFormat:
        """Determine specific Office document type"""
        try:
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zf:
                names = zf.namelist()
                if any('word/' in n for n in names):
                    return FileFormat.DOCX
                elif any('xl/' in n for n in names):
                    return FileFormat.XLSX
                elif any('ppt/' in n for n in names):
                    return FileFormat.PPTX
        except:
            pass
        return FileFormat.UNKNOWN
    
    def get_processing_method(self, format_type: FileFormat) -> ProcessingMethod:
        """Get recommended processing method for format"""
        return self.FORMAT_PROCESSORS.get(format_type, ProcessingMethod.CUSTOM)