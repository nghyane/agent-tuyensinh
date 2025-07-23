"""
API Routes for FPT University Knowledge Base Management
Focused on essential document management for FPT University
"""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from infrastructure.knowledge.fpt_knowledge_base import create_fpt_knowledge_base

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload document to FPT University knowledge base
    Supports: .md, .pdf, .docx, .txt, .json files
    """
    # Validate file type
    allowed_extensions = {".md", ".pdf", ".docx", ".txt", ".json"}

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}",
        )

    # Save file to docs/reference
    docs_dir = Path("docs/reference")
    docs_dir.mkdir(parents=True, exist_ok=True)

    file_path = docs_dir / file.filename

    content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    # Add to knowledge base
    manager = create_fpt_knowledge_base()
    manager.load_knowledge_base(recreate=True)

    return {
        "message": "Document uploaded and knowledge base reloaded",
        "file_path": str(file_path),
        "file_size": len(content),
    }


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
    manager = create_fpt_knowledge_base()
    manager.load_knowledge_base(recreate=True)

    return {"message": f"Document {filename} deleted successfully"}


@router.get("/status")
async def get_knowledge_status():
    """
    Get FPT University knowledge base status
    """
    manager = create_fpt_knowledge_base()
    exists = manager.exists()

    docs_dir = Path("docs/reference")
    document_count = len(list(docs_dir.glob("*"))) if docs_dir.exists() else 0

    return {
        "exists": exists,
        "type": "MarkdownKnowledgeBase",
        "path": "docs/reference",
        "document_count": document_count,
    }
