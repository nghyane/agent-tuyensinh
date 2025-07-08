"""
Optional CrossEncoder reranker service
"""

import time
from typing import List, Optional
from sentence_transformers import CrossEncoder

from core.domain.entities import SearchCandidate
from shared.utils.metrics import MetricsCollectorImpl


class CrossEncoderReranker:
    """
    Optional CrossEncoder reranker for improved accuracy
    Trade-off: Better accuracy vs Higher latency
    """
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        metrics_collector: Optional[MetricsCollectorImpl] = None,
        enabled: bool = False  # Disabled by default for performance
    ):
        self.model_name = model_name
        self.metrics_collector = metrics_collector
        self.enabled = enabled
        self.available = False
        
        if self.enabled:
            self._load_model()
    
    def _load_model(self):
        """Load CrossEncoder model"""
        try:
            print(f"⏳ Loading CrossEncoder model: {self.model_name}")
            self.model = CrossEncoder(self.model_name)
            self.available = True
            print("✅ CrossEncoder loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load CrossEncoder: {e}")
            self.available = False
    
    async def rerank(
        self, 
        query: str, 
        candidates: List[SearchCandidate],
        top_k: Optional[int] = None
    ) -> List[SearchCandidate]:
        """
        Rerank candidates using CrossEncoder
        
        Args:
            query: Input query
            candidates: List of search candidates
            top_k: Number of top candidates to return
            
        Returns:
            Reranked candidates with updated scores
        """
        if not self.available or not candidates:
            return candidates
        
        try:
            start_time = time.time()
            
            # Create query-candidate pairs
            pairs = [(query, candidate.text) for candidate in candidates]
            
            # Get reranking scores
            scores = self.model.predict(pairs)
            
            # Update candidates with new scores
            reranked_candidates = []
            for i, candidate in enumerate(candidates):
                reranked_candidate = SearchCandidate(
                    text=candidate.text,
                    intent_id=candidate.intent_id,
                    score=float(scores[i]),  # Use reranker score
                    metadata={
                        **candidate.metadata,
                        "original_score": candidate.score,
                        "reranked": True
                    },
                    source=candidate.source
                )
                reranked_candidates.append(reranked_candidate)
            
            # Sort by new scores
            reranked_candidates.sort(key=lambda x: x.score, reverse=True)
            
            # Apply top_k limit
            if top_k:
                reranked_candidates = reranked_candidates[:top_k]
            
            # Record metrics
            if self.metrics_collector:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics_collector.record_histogram(
                    "reranker_duration_ms", 
                    duration_ms,
                    {"model": self.model_name}
                )
                self.metrics_collector.increment_counter(
                    "reranker_calls",
                    {"candidates_count": len(candidates)}
                )
            
            print(f"🔄 Reranked {len(candidates)} candidates in {(time.time() - start_time)*1000:.1f}ms")
            return reranked_candidates
            
        except Exception as e:
            print(f"❌ Reranking failed: {e}")
            if self.metrics_collector:
                self.metrics_collector.increment_counter("reranker_errors")
            return candidates  # Return original candidates on error
    
    def get_stats(self) -> dict:
        """Get reranker statistics"""
        return {
            "model_name": self.model_name,
            "enabled": self.enabled,
            "available": self.available
        }
