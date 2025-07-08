"""
Document processors for different file formats
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
import tempfile
import json
import yaml
import csv
from datetime import datetime
from uuid import uuid4

# Document processing libraries
try:
    from unstructured.partition.auto import partition
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    logging.warning("Unstructured.io not available - install with 'pip install unstructured[all-docs]'")

# LangChain loaders
try:
    from langchain_community.document_loaders import (
        TextLoader, CSVLoader, JSONLoader, 
        UnstructuredMarkdownLoader, PyPDFLoader
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available - install with 'pip install langchain-community'")

# OCR libraries
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except (ImportError, OSError) as e:
    EASYOCR_AVAILABLE = False
    logging.warning(f"EasyOCR not available: {e}")

# Audio transcription
try:
    import whisper
    WHISPER_AVAILABLE = True
except (ImportError, OSError) as e:
    WHISPER_AVAILABLE = False
    logging.warning(f"Whisper not available: {e}")

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - install with 'pip install Pillow'")

from .models import FileFormat, ProcessingMethod, ProcessedChunk, DocumentMetadata, ChunkMetadata

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Base class for document processing"""
    
    def __init__(self):
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        self.ocr_reader = None
        self.whisper_model = None
        
    async def process(
        self, 
        file_path: str, 
        format_type: FileFormat, 
        processing_method: ProcessingMethod,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """
        Process a document and return chunks with metadata
        """
        try:
            # Route to appropriate processor
            if processing_method == ProcessingMethod.UNSTRUCTURED_IO:
                return await self._process_with_unstructured(file_path, format_type, metadata)
            elif processing_method == ProcessingMethod.LANGCHAIN_LOADER:
                return await self._process_with_langchain(file_path, format_type, metadata)
            elif processing_method == ProcessingMethod.EASYOCR:
                return await self._process_with_ocr(file_path, format_type, metadata)
            elif processing_method == ProcessingMethod.WHISPER:
                return await self._process_with_whisper(file_path, format_type, metadata)
            elif processing_method == ProcessingMethod.CUSTOM:
                return await self._process_custom(file_path, format_type, metadata)
            else:
                raise ValueError(f"Unknown processing method: {processing_method}")
                
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise

    async def _process_with_unstructured(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Process using Unstructured.io"""
        if not UNSTRUCTURED_AVAILABLE:
            raise ImportError("Unstructured.io not available")
        
        try:
            # Partition the document
            elements = partition(filename=file_path)
            
            # Extract text and metadata
            full_text = "\n\n".join([str(el) for el in elements])
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("filename", "Unknown"),
                format=format_type,
                processing_method=ProcessingMethod.UNSTRUCTURED_IO,
                pages=len([el for el in elements if hasattr(el, 'metadata') and el.metadata.page_number]),
                word_count=len(full_text.split()),
                language=self._detect_language(full_text[:1000])
            )
            
            # Chunk the text
            chunks = self._chunk_text(full_text, file_path)
            
            return chunks, doc_metadata
            
        except Exception as e:
            logger.error(f"Unstructured processing failed: {e}")
            raise

    async def _process_with_langchain(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Process using LangChain loaders"""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain not available")
        
        try:
            # Select appropriate loader
            if format_type == FileFormat.TXT:
                loader = TextLoader(file_path)
            elif format_type == FileFormat.CSV:
                loader = CSVLoader(file_path)
            elif format_type == FileFormat.JSON:
                loader = JSONLoader(file_path)
            elif format_type == FileFormat.MD:
                loader = UnstructuredMarkdownLoader(file_path)
            elif format_type == FileFormat.PDF:
                loader = PyPDFLoader(file_path)
            else:
                # Fallback to text loader
                loader = TextLoader(file_path)
            
            # Load documents
            documents = loader.load()
            
            # Combine text
            full_text = "\n\n".join([doc.page_content for doc in documents])
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("filename", "Unknown"),
                format=format_type,
                processing_method=ProcessingMethod.LANGCHAIN_LOADER,
                word_count=len(full_text.split()),
                language=self._detect_language(full_text[:1000])
            )
            
            # Extract additional metadata from first document
            # Note: Store LangChain metadata in format-specific field
            if documents and documents[0].metadata:
                # Store in pdf_metadata field for now (can be used for any format)
                doc_metadata.pdf_metadata = documents[0].metadata
            
            # Chunk the text
            chunks = self._chunk_text(full_text, file_path)
            
            return chunks, doc_metadata
            
        except Exception as e:
            logger.error(f"LangChain processing failed: {e}")
            raise

    async def _process_with_ocr(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Process images with OCR"""
        if not EASYOCR_AVAILABLE:
            raise ImportError("EasyOCR not available")
        
        try:
            # Initialize OCR reader if needed
            if self.ocr_reader is None:
                self.ocr_reader = easyocr.Reader(['en'])  # Add more languages as needed
            
            # Read text from image
            result = self.ocr_reader.readtext(file_path)
            
            # Extract text
            full_text = " ".join([text[1] for text in result])
            
            # Get image metadata
            image_meta = {}
            if PIL_AVAILABLE:
                with Image.open(file_path) as img:
                    image_meta = {
                        "width": img.width,
                        "height": img.height,
                        "format": img.format,
                        "mode": img.mode
                    }
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("filename", "Unknown"),
                format=format_type,
                processing_method=ProcessingMethod.EASYOCR,
                word_count=len(full_text.split()),
                language=self._detect_language(full_text),
                image_metadata=image_meta
            )
            
            # Chunk the text
            chunks = self._chunk_text(full_text, file_path)
            
            return chunks, doc_metadata
            
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise

    async def _process_with_whisper(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Process audio/video with Whisper"""
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper not available")
        
        try:
            # Initialize Whisper model if needed
            if self.whisper_model is None:
                self.whisper_model = whisper.load_model("base")  # Use larger models for better accuracy
            
            # For video files, extract audio first
            audio_path = file_path
            if format_type in [FileFormat.MP4, FileFormat.AVI, FileFormat.MOV, FileFormat.MKV]:
                audio_path = await self._extract_audio_from_video(file_path)
            
            # Transcribe audio
            result = self.whisper_model.transcribe(audio_path)
            
            # Extract text and metadata
            full_text = result["text"]
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("filename", "Unknown"),
                format=format_type,
                processing_method=ProcessingMethod.WHISPER,
                word_count=len(full_text.split()),
                language=result.get("language", "unknown"),
                audio_metadata={
                    "duration": result.get("duration"),
                    "language": result.get("language"),
                    "segments": len(result.get("segments", []))
                }
            )
            
            # Chunk the text with timestamps
            chunks = self._chunk_transcription(result, file_path)
            
            # Clean up temporary audio file
            if audio_path != file_path and os.path.exists(audio_path):
                os.remove(audio_path)
            
            return chunks, doc_metadata
            
        except Exception as e:
            logger.error(f"Whisper processing failed: {e}")
            raise

    async def _process_custom(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Custom processing for special formats"""
        
        if format_type in [FileFormat.ZIP, FileFormat.TAR, FileFormat.GZ]:
            return await self._process_archive(file_path, format_type, metadata)
        elif format_type in [FileFormat.PYTHON, FileFormat.JAVASCRIPT, FileFormat.JAVA]:
            return await self._process_code(file_path, format_type, metadata)
        else:
            # Fallback to text processing
            return await self._process_as_text(file_path, format_type, metadata)

    async def _process_archive(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Process archive files"""
        import zipfile
        import tarfile
        
        chunks = []
        extracted_files = []
        
        try:
            # Extract archive to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                if format_type == FileFormat.ZIP:
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        zf.extractall(temp_dir)
                        extracted_files = zf.namelist()
                elif format_type == FileFormat.TAR or format_type == FileFormat.GZ:
                    with tarfile.open(file_path, 'r:*') as tf:
                        tf.extractall(temp_dir)
                        extracted_files = tf.getnames()
                
                # Process each extracted file
                # Note: In real implementation, this would recursively process files
                # For now, just create a summary chunk
                summary = f"Archive contains {len(extracted_files)} files:\n"
                summary += "\n".join(extracted_files[:20])  # First 20 files
                if len(extracted_files) > 20:
                    summary += f"\n... and {len(extracted_files) - 20} more files"
                
                chunks = self._chunk_text(summary, file_path)
            
            # Create metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("filename", "Unknown"),
                format=format_type,
                processing_method=ProcessingMethod.CUSTOM,
                word_count=len(summary.split())
            )
            
            return chunks, doc_metadata
            
        except Exception as e:
            logger.error(f"Archive processing failed: {e}")
            raise

    async def _process_code(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Process code files with syntax awareness"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            # Extract code structure (simplified)
            lines = code_content.split('\n')
            functions = []
            classes = []
            imports = []
            
            for line in lines:
                line_stripped = line.strip()
                if format_type == FileFormat.PYTHON:
                    if line_stripped.startswith('def '):
                        functions.append(line_stripped)
                    elif line_stripped.startswith('class '):
                        classes.append(line_stripped)
                    elif line_stripped.startswith('import ') or line_stripped.startswith('from '):
                        imports.append(line_stripped)
            
            # Create enhanced content with structure
            enhanced_content = f"File: {metadata.get('filename', 'Unknown')}\n\n"
            if imports:
                enhanced_content += "Imports:\n" + "\n".join(imports) + "\n\n"
            if classes:
                enhanced_content += "Classes:\n" + "\n".join(classes) + "\n\n"
            if functions:
                enhanced_content += "Functions:\n" + "\n".join(functions) + "\n\n"
            enhanced_content += "Full Code:\n" + code_content
            
            # Chunk the enhanced content
            chunks = self._chunk_text(enhanced_content, file_path)
            
            # Create metadata
            doc_metadata = DocumentMetadata(
                title=metadata.get("filename", "Unknown"),
                format=format_type,
                processing_method=ProcessingMethod.CUSTOM,
                word_count=len(code_content.split()),
                language="code"
            )
            
            return chunks, doc_metadata
            
        except Exception as e:
            logger.error(f"Code processing failed: {e}")
            raise

    async def _process_as_text(
        self, 
        file_path: str, 
        format_type: FileFormat,
        metadata: Dict[str, Any]
    ) -> Tuple[List[ProcessedChunk], DocumentMetadata]:
        """Fallback text processing"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            chunks = self._chunk_text(content, file_path)
            
            doc_metadata = DocumentMetadata(
                title=metadata.get("filename", "Unknown"),
                format=format_type,
                processing_method=ProcessingMethod.CUSTOM,
                word_count=len(content.split()),
                language=self._detect_language(content[:1000])
            )
            
            return chunks, doc_metadata
            
        except Exception as e:
            logger.error(f"Text processing failed: {e}")
            raise

    def _chunk_text(self, text: str, source_file: str) -> List[ProcessedChunk]:
        """Chunk text into smaller pieces"""
        chunks = []
        document_id = str(uuid4())
        
        # Simple character-based chunking (can be improved with semantic chunking)
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk_text = text[i:i + self.chunk_size]
            
            chunk_metadata = ChunkMetadata(
                chunk_id=str(uuid4()),
                document_id=document_id,
                chunk_index=len(chunks),
                start_char=i,
                end_char=min(i + self.chunk_size, len(text))
            )
            
            chunks.append(ProcessedChunk(
                chunk_id=chunk_metadata.chunk_id,
                content=chunk_text,
                metadata=chunk_metadata,
                token_count=len(chunk_text.split()),
                language=self._detect_language(chunk_text[:100])
            ))
        
        return chunks

    def _chunk_transcription(self, whisper_result: Dict, source_file: str) -> List[ProcessedChunk]:
        """Chunk transcription with timestamps"""
        chunks = []
        document_id = str(uuid4())
        
        # Use Whisper segments for natural chunking
        current_chunk = []
        current_text = ""
        
        for segment in whisper_result.get("segments", []):
            segment_text = segment["text"]
            current_text += segment_text + " "
            current_chunk.append(segment)
            
            # Create chunk when reaching size limit
            if len(current_text) >= self.chunk_size:
                chunk_metadata = ChunkMetadata(
                    chunk_id=f"{document_id}_chunk_{len(chunks)}",
                    document_id=document_id,
                    chunk_index=len(chunks),
                    start_char=int(current_chunk[0]["start"]),
                    end_char=int(current_chunk[-1]["end"])
                )
                
                chunks.append(ProcessedChunk(
                    chunk_id=chunk_metadata.chunk_id,
                    content=current_text.strip(),
                    metadata=chunk_metadata,
                    token_count=len(current_text.split()),
                    language=whisper_result.get("language", "unknown")
                ))
                
                current_chunk = []
                current_text = ""
        
        # Add final chunk
        if current_text:
            chunk_metadata = ChunkMetadata(
                chunk_id=f"{document_id}_chunk_{len(chunks)}",
                document_id=document_id,
                chunk_index=len(chunks),
                start_char=int(current_chunk[0]["start"]) if current_chunk else 0,
                end_char=int(current_chunk[-1]["end"]) if current_chunk else 0
            )
            
            chunks.append(ProcessedChunk(
                chunk_id=chunk_metadata.chunk_id,
                content=current_text.strip(),
                metadata=chunk_metadata,
                token_count=len(current_text.split()),
                language=whisper_result.get("language", "unknown")
            ))
        
        return chunks

    async def _extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg"""
        try:
            import subprocess
            
            # Create temporary audio file
            audio_path = tempfile.mktemp(suffix=".wav")
            
            # Run ffmpeg to extract audio
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # WAV format
                "-ar", "16000",  # 16kHz sample rate for Whisper
                "-ac", "1",  # Mono
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError("ffmpeg audio extraction failed")
            
            return audio_path
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise

    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        # In production, use langdetect or similar
        # For now, return "en" as default
        return "en"