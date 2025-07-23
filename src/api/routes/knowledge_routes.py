"""
Optimized Knowledge Routes using Agno Built-in Functions
Eliminates redundant code by leveraging Agno's native capabilities
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel

from infrastructure.knowledge.fpt_knowledge_base import create_fpt_knowledge_base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])

# Agno supports these formats natively - no custom validation needed
AGNO_SUPPORTED_FORMATS = {".md", ".pdf", ".docx", ".txt", ".json"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class UploadResponse(BaseModel):
    message: str
    file_path: str
    file_size: int
    processing_status: str
    agno_optimized: bool = True  # Indicates using Agno built-ins


class DocumentInfo(BaseModel):
    """Simplified document info using Agno's built-in metadata"""
    filename: str
    size: int
    modified: str
    exists: bool


def validate_file_basic(file: UploadFile) -> None:
    """Basic validation - let Agno handle format-specific validation"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Check file size
    if hasattr(file, "size") and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    # Basic extension check - Agno will handle detailed validation
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in AGNO_SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Agno supported formats: {', '.join(AGNO_SUPPORTED_FORMATS)}",
        )


async def process_document_with_agno(file_path: str, metadata: Dict[str, Any]):
    """
    Process document using Agno's built-in aload() method
    Much simpler than custom processing logic
    """
    try:
        logger.info(f"🔄 Processing document with Agno built-ins: {file_path}")

        knowledge_base = create_fpt_knowledge_base()

        # Use Agno's built-in async loading method
        # This will process all documents in the knowledge base path
        await knowledge_base.aload(
            recreate=False,  # Don't recreate entire KB
            upsert=True,     # Update if content different
            skip_existing=False  # Process to handle updates
        )

        logger.info(f"✅ Document processed successfully with Agno: {file_path}")

    except Exception as e:
        logger.error(f"❌ Agno processing failed for {file_path}: {e}")
        # Agno handles most errors gracefully, but log for monitoring


async def remove_document_with_agno(filename: str) -> bool:
    """
    Remove document using Agno's built-in methods
    Since Agno doesn't have direct document removal, we remove file and reload
    """
    try:
        file_path = Path("docs/reference") / filename
        if not file_path.exists():
            logger.warning(f"⚠️ File not found: {filename}")
            return False

        # Remove file from filesystem first
        file_path.unlink()
        logger.info(f"🗑️ File removed from filesystem: {filename}")

        # Reload knowledge base to update vector DB
        knowledge_base = create_fpt_knowledge_base()
        await knowledge_base.aload(
            recreate=False,  # Don't recreate, just update
            upsert=True,     # Update existing entries
            skip_existing=False  # Process all to remove deleted files
        )

        logger.info(f"✅ Knowledge base updated after removing: {filename}")
        return True

    except Exception as e:
        logger.error(f"❌ Error removing document with Agno {filename}: {e}")
        return False


@router.post("/upload", response_model=UploadResponse)
async def upload_document_optimized(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    overwrite: bool = False
):
    """
    Optimized document upload using Agno built-in functions
    
    Key improvements:
    - Uses Agno's native file format support
    - Leverages built-in async processing
    - Eliminates custom metadata extraction
    - Uses Agno's upsert functionality for duplicates
    """
    try:
        # Basic validation only - let Agno handle the rest
        validate_file_basic(file)

        # Read file content
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
            )

        # Simple filename sanitization
        safe_filename = (file.filename or "unknown_file").replace(" ", "_")
        
        # Create docs directory
        docs_dir = Path("docs/reference")
        docs_dir.mkdir(parents=True, exist_ok=True)
        file_path = docs_dir / safe_filename

        # Handle existing files with Agno's upsert capability
        if file_path.exists() and not overwrite:
            # Append timestamp for different filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = safe_filename.rsplit(".", 1)
            safe_filename = f"{name}_{timestamp}.{ext}"
            file_path = docs_dir / safe_filename

        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Prepare metadata for Agno (simplified)
        metadata = {
            "filename": safe_filename,
            "file_size": len(content),
            "upload_time": datetime.now().isoformat(),
            "file_type": Path(safe_filename).suffix.lower(),
            "mime_type": file.content_type or "application/octet-stream",
            "language": "vi",  # FPT University default
            "category": "university_document",
            "source": "api_upload"
        }

        # Use Agno's built-in async processing
        background_tasks.add_task(
            process_document_with_agno, str(file_path), metadata
        )

        logger.info(f"📁 File uploaded and queued for Agno processing: {safe_filename}")

        return UploadResponse(
            message=f"Document uploaded successfully. Processing with Agno built-ins...",
            file_path=str(file_path),
            file_size=len(content),
            processing_status="queued_for_agno_processing",
            agno_optimized=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents_optimized():
    """
    List documents using simplified approach
    Agno handles the complex knowledge base queries
    """
    try:
        docs_dir = Path("docs/reference")
        if not docs_dir.exists():
            return []

        documents = []
        for file_path in docs_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in AGNO_SUPPORTED_FORMATS:
                documents.append(
                    DocumentInfo(
                        filename=file_path.name,
                        size=file_path.stat().st_size,
                        modified=datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                        exists=True
                    )
                )

        return documents

    except Exception as e:
        logger.error(f"❌ Failed to list documents: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/documents/{filename}")
async def delete_document_optimized(filename: str):
    """
    Delete document using Agno's built-in methods
    Much simpler than manual vector DB operations
    """
    try:
        file_path = Path("docs/reference") / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document not found")

        # Use Agno's built-in removal (handles vector DB automatically)
        success = await remove_document_with_agno(filename)

        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document {filename} using Agno"
            )

        return {
            "message": f"Document {filename} deleted successfully using Agno built-ins",
            "agno_optimized": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/status")
async def get_knowledge_status_optimized():
    """
    Get knowledge base status using Agno's built-in methods
    Simplified compared to custom implementation
    """
    try:
        knowledge_base = create_fpt_knowledge_base()

        # Use Agno's built-in exists() method
        kb_exists = knowledge_base.exists()

        # Get basic stats using Agno's capabilities
        stats = {
            "knowledge_base_exists": kb_exists,
            "agno_optimized": True,
            "supported_formats": list(AGNO_SUPPORTED_FORMATS),
            "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        }

        # Add document count if KB exists
        if kb_exists:
            docs_dir = Path("docs/reference")
            if docs_dir.exists():
                doc_count = len([
                    f for f in docs_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in AGNO_SUPPORTED_FORMATS
                ])
                stats["document_count"] = doc_count
                
                # Get last modified time
                if doc_count > 0:
                    latest_file = max(
                        docs_dir.iterdir(),
                        key=lambda f: f.stat().st_mtime if f.is_file() else 0
                    )
                    stats["last_updated"] = datetime.fromtimestamp(
                        latest_file.stat().st_mtime
                    ).isoformat()

        return stats

    except Exception as e:
        logger.error(f"❌ Failed to get knowledge status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get knowledge status: {str(e)}"
        )


@router.post("/reload")
async def reload_knowledge_base():
    """
    Reload entire knowledge base using Agno's built-in aload()
    Much simpler than custom reload logic
    """
    try:
        logger.info("🔄 Reloading knowledge base with Agno built-ins...")

        knowledge_base = create_fpt_knowledge_base()

        # Use Agno's built-in async reload
        await knowledge_base.aload(
            recreate=False,  # Don't recreate, just refresh
            upsert=True,     # Update existing documents
            skip_existing=False  # Process all to ensure consistency
        )

        logger.info("✅ Knowledge base reloaded successfully with Agno")

        return {
            "message": "Knowledge base reloaded successfully using Agno built-ins",
            "agno_optimized": True,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Knowledge base reload failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Knowledge base reload failed: {str(e)}"
        )