"""
FPT University Knowledge Base with Qdrant integration
Optimized direct usage of Agno's MarkdownKnowledgeBase
"""

import os
from pathlib import Path
from typing import Optional

from agno.knowledge.markdown import MarkdownKnowledgeBase
from agno.reranker.cohere import CohereReranker
from agno.vectordb.qdrant.qdrant import Qdrant
from agno.vectordb.search import SearchType

from infrastructure.embeddings import get_embedding_service


def create_fpt_knowledge_base(
    collection_name: str = "fpt_university_knowledge",
    knowledge_path: str = "docs/reference",
) -> MarkdownKnowledgeBase:
    """
    Create optimized FPT University Knowledge Base using Agno directly
    
    Returns:
        MarkdownKnowledgeBase instance with optimized configuration
    """
    # Sử dụng global embedding service
    embedder = get_embedding_service()

    # Cấu hình reranker nếu có API key
    reranker = None
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if cohere_api_key:
        reranker = CohereReranker(
            model="rerank-multilingual-v3.0", api_key=cohere_api_key
        )

    # Cấu hình Qdrant với timeout tối ưu
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    vector_db = Qdrant(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection=collection_name,
        search_type=SearchType.vector,
        embedder=embedder,
        reranker=reranker,
        timeout=30.0,
    )

    # Tạo knowledge base trực tiếp với cấu hình tối ưu
    knowledge_base = MarkdownKnowledgeBase(
        path=knowledge_path, 
        vector_db=vector_db
    )

    return knowledge_base


# Usage examples for different scenarios:
# 
# 1. Upload new document (recommended for FPT University):
#    await knowledge_base.aload(recreate=False, upsert=True, skip_existing=False)
#
# 2. Initial setup:
#    knowledge_base.load(recreate=True, upsert=False, skip_existing=True)
#
# 3. Update existing documents:
#    await knowledge_base.aload(recreate=False, upsert=True, skip_existing=False)
#
# 4. Complete rebuild:
#    knowledge_base.load(recreate=True, upsert=False, skip_existing=False)


def get_knowledge_stats(knowledge_base: MarkdownKnowledgeBase) -> dict:
    """
    Get knowledge base statistics
    
    Args:
        knowledge_base: The knowledge base instance
        
    Returns:
        Dictionary with knowledge base statistics
    """
    try:
        # Get basic stats
        exists = knowledge_base.exists()
        knowledge_path = Path(str(knowledge_base.path))
        
        if not knowledge_path.exists():
            return {
                "exists": False,
                "document_count": 0,
                "total_size": 0,
                "path": str(knowledge_path),
                "type": "MarkdownKnowledgeBase"
            }
        
        # Count documents and calculate total size
        documents = []
        total_size = 0
        
        for file_path in knowledge_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.md', '.txt', '.json']:
                stat = file_path.stat()
                documents.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
                total_size += stat.st_size
        
        return {
            "exists": exists,
            "document_count": len(documents),
            "total_size": total_size,
            "path": str(knowledge_path),
            "documents": documents,
            "type": "MarkdownKnowledgeBase"
        }
        
    except Exception as e:
        return {"error": str(e), "type": "MarkdownKnowledgeBase"}



