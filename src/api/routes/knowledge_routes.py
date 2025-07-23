"""
API Routes for FPT University Knowledge Base Management
Focused on essential document management for FPT University
"""

import asyncio
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks
from pydantic import BaseModel

from infrastructure.knowledge.fpt_knowledge_base import create_fpt_knowledge_base, get_knowledge_stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".md", ".pdf", ".docx", ".txt", ".json"}
ALLOWED_MIME_TYPES = {
    "text/markdown": ".md",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "application/json": ".json"
}

class UploadResponse(BaseModel):
    message: str
    file_path: str
    file_size: int
    file_hash: str
    metadata: Dict[str, Any]
    processing_status: str

class DocumentMetadata(BaseModel):
    filename: str
    file_size: int
    file_hash: str
    upload_time: datetime
    file_type: str
    mime_type: str
    language: str = "vi"  # Default to Vietnamese for FPT University
    category: str = "university_document"
    source: str = "manual_upload"

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Check file size
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate MIME type if available
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"MIME type not supported: {file.content_type}"
        )

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext

    return filename

def generate_file_hash(content: bytes) -> str:
    """Generate SHA-256 hash of file content"""
    return hashlib.sha256(content).hexdigest()

def extract_metadata(file: UploadFile, content: bytes, file_path: str) -> DocumentMetadata:
    """Extract metadata from uploaded file"""
    file_hash = generate_file_hash(content)
    
    # Ensure filename is not None
    filename = file.filename or "unknown_file"
    file_type = Path(filename).suffix.lower()

    return DocumentMetadata(
        filename=filename,
        file_size=len(content),
        file_hash=file_hash,
        upload_time=datetime.now(),
        file_type=file_type,
        mime_type=file.content_type or "application/octet-stream"
    )

async def process_document_background(file_path: str, file_hash: str):
    """Background task to process document and reload knowledge base"""
    try:
        logger.info(f"🔄 Processing document: {file_path}")
        
        # Create knowledge base directly
        knowledge_base = create_fpt_knowledge_base()
        
        # Strategy: Use skip_existing=False with upsert=True for upload scenarios
        # This handles duplicate filenames with different content by updating
        # and ensures all documents are properly indexed
        await knowledge_base.aload(
            recreate=False,      # Don't recreate, just add/update
            upsert=True,         # Update if filename exists but content different
            skip_existing=False  # Process all documents to handle duplicates
        )
        
        logger.info(f"✅ Document processed successfully: {file_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to process document {file_path}: {e}")
        # Could implement retry logic here

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload document to FPT University knowledge base
    Supports: .md, .pdf, .docx, .txt, .json files

    Features:
    - File validation and sanitization
    - Metadata extraction
    - Background processing
    - Duplicate detection
    - Progress tracking
    """
    try:
        # Validate file
        validate_file(file)

        # Read file content
        content = await file.read()

        # Check file size after reading
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # Generate file hash for duplicate detection
        file_hash = generate_file_hash(content)

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename or "unknown_file")

        # Create docs directory
        docs_dir = Path("docs/reference")
        docs_dir.mkdir(parents=True, exist_ok=True)

        file_path = docs_dir / safe_filename

        # Check for duplicate files
        if file_path.exists():
            # Check if it's the same content
            existing_hash = generate_file_hash(file_path.read_bytes())
            if existing_hash == file_hash:
                raise HTTPException(
                    status_code=409,
                    detail="File with identical content already exists"
                )
            else:
                # Different content, append timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(safe_filename)
                safe_filename = f"{name}_{timestamp}{ext}"
                file_path = docs_dir / safe_filename

        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Extract metadata
        metadata = extract_metadata(file, content, str(file_path))

        # Add background task for knowledge base processing
        if background_tasks:
            background_tasks.add_task(
                process_document_background,
                str(file_path),
                file_hash
            )

        logger.info(f"📁 File uploaded successfully: {safe_filename}")

        return UploadResponse(
            message="Document uploaded successfully. Processing in background...",
            file_path=str(file_path),
            file_size=len(content),
            file_hash=file_hash,
            metadata=metadata.model_dump(),
            processing_status="uploaded"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/documents")
async def list_documents():
    """
    List all documents in FPT University knowledge base
    """
    docs_dir = Path("docs/reference")
    if not docs_dir.exists():
        return []

    documents = []
    for file_path in docs_dir.iterdir():
        if file_path.is_file():
            documents.append(
                {
                    "path": file_path.name,
                    "exists": True,
                    "size": file_path.stat().st_size,
                }
            )

    return documents


@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Delete document from FPT University knowledge base
    """
    file_path = Path("docs/reference") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")

    file_path.unlink()

    # Reload knowledge base to reflect changes
    knowledge_base = create_fpt_knowledge_base()
    knowledge_base.load(recreate=True)

    return {"message": f"Document {filename} deleted successfully"}


@router.get("/status")
async def get_knowledge_status():
    """
    Get FPT University knowledge base status with detailed information
    """
    try:
        knowledge_base = create_fpt_knowledge_base()
        
        # Use the optimized stats function
        stats = get_knowledge_stats(knowledge_base)
        
        # Add last_updated if documents exist
        if stats.get("documents"):
            stats["last_updated"] = max([
                datetime.fromtimestamp(doc["modified"]).isoformat() 
                for doc in stats["documents"]
            ])
        else:
            stats["last_updated"] = None

        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get knowledge status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get knowledge status: {str(e)}"
        )

@router.get("/processing-status/{file_hash}")
async def get_processing_status(file_hash: str):
    """
    Get processing status for a specific document
    """
    # This could be enhanced with a proper database to track processing status
    # For now, we'll return a simple response
    return {
        "file_hash": file_hash,
        "status": "completed",  # This should be tracked in a real implementation
        "message": "Document processing completed"
    }
