"""
Global embedding service for FPT University Agent
"""

import os

from agno.embedder.openai import OpenAIEmbedder

# Global embedding service instance
_embedding_service = None


def get_embedding_service() -> OpenAIEmbedder:
    """
    Get global embedding service instance

    Returns:
        OpenAIEmbedder instance
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = OpenAIEmbedder(
            id="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url= "https://api.openai.com/v1"
            # os.getenv("OPENAI_BASE_URL"
        )
        print(f"✅ Global embedding service initialized: {_embedding_service.id}")

    return _embedding_service


def reset_embedding_service():
    """Reset global embedding service (useful for testing)"""
    global _embedding_service
    _embedding_service = None
