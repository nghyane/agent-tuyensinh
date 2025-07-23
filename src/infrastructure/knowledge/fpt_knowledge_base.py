"""
FPT University Knowledge Base with Qdrant integration
"""

import os
import time
from typing import Any, Dict, List, Optional

from agno.knowledge.markdown import MarkdownKnowledgeBase
from agno.reranker.cohere import CohereReranker
from agno.vectordb.qdrant.qdrant import Qdrant
from agno.vectordb.search import SearchType

from infrastructure.embeddings import get_embedding_service


class FPTUniversityKnowledgeManager:
    """
    Optimized Manager for FPT University Knowledge Base
    """

    def __init__(
        self,
        collection_name: str = "fpt_university_knowledge",
        knowledge_path: str = "docs/reference",
    ):
        # Sử dụng global embedding service
        self.embedder = get_embedding_service()

        # Cấu hình reranker nếu có API key
        self.reranker = None
        cohere_api_key = os.getenv("COHERE_API_KEY")
        if cohere_api_key:
            self.reranker = CohereReranker(
                model="rerank-multilingual-v3.0", api_key=cohere_api_key
            )

        # Cấu hình Qdrant
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        self.vector_db = Qdrant(
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection=collection_name,
            search_type=SearchType.vector,
            embedder=self.embedder,
            reranker=self.reranker,
            timeout=30.0,
        )

        # Knowledge base chính
        self.knowledge_base = MarkdownKnowledgeBase(
            path=knowledge_path, vector_db=self.vector_db
        )

    def load_knowledge_base(self, recreate: bool = False) -> None:
        """
        Load knowledge base with retry logic
        """
        max_retries = 3
        retry_delay: float = 5.0

        for attempt in range(max_retries):
            try:
                print(
                    f"📚 Loading knowledge base "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )
                self.knowledge_base.load(recreate=recreate)
                print("✅ Knowledge base loaded successfully!")
                return

            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

    def search_knowledge(
        self, query: str, num_documents: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base

        Args:
            query: Search query
            num_documents: Number of documents to return

        Returns:
            List of search results
        """
        results = self.knowledge_base.search(query=query, num_documents=num_documents)
        return [
            {"content": doc.content, "metadata": getattr(doc, "metadata", {})}
            for doc in results
        ]

    def exists(self) -> bool:
        """
        Check if knowledge base exists
        """
        max_retries = 3
        retry_delay: float = 2.0

        for attempt in range(max_retries):
            try:
                return self.knowledge_base.exists()
            except Exception as e:
                print(f"❌ Exists check attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    return False

        return False


def create_fpt_knowledge_base(
    collection_name: str = "fpt_university_knowledge",
    knowledge_path: str = "docs/reference",
) -> FPTUniversityKnowledgeManager:
    """
    Create FPT University Knowledge Manager

    Returns:
        FPTUniversityKnowledgeManager instance
    """
    return FPTUniversityKnowledgeManager(
        collection_name=collection_name, knowledge_path=knowledge_path
    )
