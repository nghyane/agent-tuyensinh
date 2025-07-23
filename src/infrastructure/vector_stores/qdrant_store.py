"""
Qdrant vector store implementation
"""

import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from core.domain.entities import SearchCandidate
from shared.types import Metadata


class QdrantVectorStore:
    """
    Qdrant vector store implementation for intent examples
    Tận dụng tối đa các tính năng có sẵn của QdrantClient
    """
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        collection_name: str = "intent_examples_python_hybrid",
        vector_size: int = 1536,
        distance: Distance = Distance.COSINE
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        
        try:
            # Khởi tạo QdrantClient với URL trực tiếp
            self.client = QdrantClient(
                url=url,
                api_key=api_key or os.getenv("QDRANT_API_KEY")
            )
            
            # Tự động tạo collection nếu chưa tồn tại
            self._ensure_collection()
            self.available = True
            
            print(f"✅ Qdrant connected: {url}")
            
        except Exception as e:
            print(f"❌ Qdrant connection failed: {e}")
            self.available = False
    
    def _ensure_collection(self):
        """Tự động tạo collection nếu chưa tồn tại"""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=self.distance
                )
            )
            print(f"✅ Created collection: {self.collection_name}")
        else:
            print(f"✅ Collection exists: {self.collection_name}")
    
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        score_threshold: float = 0.6
    ) -> List[SearchCandidate]:
        """Search for similar vectors using QdrantClient's search method"""
        if not self.available:
            return []
        
        try:
            # Sử dụng trực tiếp QdrantClient.search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold
            )
            
            # Chuyển đổi kết quả thành SearchCandidate
            candidates = [
                SearchCandidate(
                    text=point.payload.get("text", "") if point.payload else "",
                    intent_id=point.payload.get("intent_id", "unknown") if point.payload else "unknown",
                    score=point.score,
                    metadata=point.payload or {},
                    source="qdrant"
                )
                for point in search_result
            ]
            
            print(f"🔍 Qdrant search: {len(candidates)} candidates found")
            return candidates
            
        except Exception as e:
            print(f"❌ Qdrant search failed: {e}")
            return []
    
    async def add_documents(
        self, 
        texts: List[str], 
        vectors: List[List[float]], 
        metadata: List[Metadata]
    ) -> None:
        """Add documents using QdrantClient's upsert method"""
        if not self.available:
            return
        
        try:
            # Tạo points với ID tự động
            points = [
                PointStruct(
                    id=i,
                    vector=vector,
                    payload={"text": text, **meta}
                )
                for i, (text, vector, meta) in enumerate(zip(texts, vectors, metadata))
            ]
            
            # Sử dụng trực tiếp QdrantClient.upsert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"✅ Added {len(points)} documents to Qdrant")
            
        except Exception as e:
            print(f"❌ Failed to add documents to Qdrant: {e}")
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information using QdrantClient's get_collection"""
        if not self.available:
            return {"available": False}
        
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "available": True,
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            print(f"❌ Failed to get collection info: {e}")
            return {"available": False, "error": str(e)}
    
    def collection_exists(self) -> bool:
        """Check if collection exists using QdrantClient's collection_exists"""
        return self.available and self.client.collection_exists(self.collection_name)
    
    def delete_collection(self) -> bool:
        """Delete collection using QdrantClient's delete_collection"""
        if not self.available:
            return False
        
        try:
            self.client.delete_collection(self.collection_name)
            print(f"✅ Deleted collection: {self.collection_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete collection: {e}")
            return False
