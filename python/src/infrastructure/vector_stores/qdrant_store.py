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
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "intent_examples_python_hybrid",
        vector_size: int = 1536,
        distance: Distance = Distance.COSINE
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        
        try:
            self.client = QdrantClient(host=host, port=port)
            self._ensure_collection()
            self.available = True
            print(f"✅ Qdrant connected: {host}:{port}")
        except Exception as e:
            print(f"❌ Qdrant connection failed: {e}")
            self.available = False
    
    def _ensure_collection(self):
        """Ensure collection exists"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
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
                
        except Exception as e:
            print(f"❌ Collection setup failed: {e}")
            raise
    
    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        score_threshold: float = 0.6
    ) -> List[SearchCandidate]:
        """Search for similar vectors"""
        if not self.available:
            return []
        
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold
            )
            
            candidates = []
            for point in search_result:
                metadata = point.payload or {}
                
                candidate = SearchCandidate(
                    text=metadata.get("text", ""),
                    intent_id=metadata.get("intent_id", "unknown"),
                    score=point.score,
                    metadata=metadata,
                    source="qdrant"
                )
                candidates.append(candidate)
            
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
        """Add documents to vector store"""
        if not self.available:
            return
        
        try:
            points = []
            for i, (text, vector, meta) in enumerate(zip(texts, vectors, metadata)):
                point = PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "text": text,
                        **meta
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            print(f"✅ Added {len(points)} documents to Qdrant")
            
        except Exception as e:
            print(f"❌ Failed to add documents to Qdrant: {e}")
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
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
