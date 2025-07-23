"""
Hybrid Intent Detection Service
Combines rule-based and vector-based intent detection
"""

import time
import hashlib
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from core.domain.entities import IntentResult, DetectionContext, RuleMatch, SearchCandidate
from infrastructure.intent_detection.rule_based import RuleBasedDetectorImpl
from infrastructure.vector_stores.qdrant_store import QdrantVectorStore
from agno.embedder.openai import OpenAIEmbedder
from infrastructure.caching.memory_cache import MemoryCacheService
from shared.types import DetectionMethod, QueryText, IntentId
from shared.utils.text_processing import VietnameseTextProcessor

logger = logging.getLogger(__name__)

class IntentDetectionError(Exception):
    """Base exception for intent detection errors"""
    pass

class RuleDetectionError(IntentDetectionError):
    """Exception for rule-based detection errors"""
    pass

class VectorSearchError(IntentDetectionError):
    """Exception for vector search errors"""
    pass

@dataclass
class HybridConfig:
    """Configuration for hybrid intent detection"""
    rule_high_confidence_threshold: float = 0.7
    rule_medium_confidence_threshold: float = 0.3
    early_exit_threshold: float = 0.8
    vector_top_k: int = 3
    vector_confidence_threshold: float = 0.6
    cache_min_confidence: float = 0.8
    enable_caching: bool = True


class HybridIntentDetectionService:
    """
    Hybrid intent detection service combining rule-based and vector search
    """
    
    def __init__(
        self,
        rule_detector: RuleBasedDetectorImpl,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_service: Optional[OpenAIEmbedder] = None,
        cache_service: Optional[MemoryCacheService] = None,
        text_processor: Optional[VietnameseTextProcessor] = None,
        config: Optional[HybridConfig] = None
    ):
        self.rule_detector = rule_detector
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.cache_service = cache_service
        self.text_processor = text_processor or VietnameseTextProcessor()
        self.config = config or HybridConfig()
        
        # Check vector search availability
        self.vector_search_enabled = (
            self.vector_store and 
            self.vector_store.available and 
            self.embedding_service
        )
        
        print(f"🔧 Hybrid service initialized:")
        print(f"   - Rule-based: ✅")
        print(f"   - Vector search: {'✅' if self.vector_search_enabled else '❌'}")
        print(f"   - Caching: {'✅' if self.cache_service else '❌'}")
    
    async def detect_intent(self, context: DetectionContext) -> IntentResult:
        """
        Optimized hybrid intent detection with simplified logic

        Args:
            context: Detection context with query and metadata

        Returns:
            IntentResult with detected intent and confidence
        """
        start_time = time.time()
        query = context.query

        try:
            # Step 1: Check cache first (only for high-confidence results)
            if self.config.enable_caching and self.cache_service:
                cached_result = await self._get_cached_result(query)
                if cached_result and cached_result.confidence >= self.config.cache_min_confidence:
                    return cached_result

            # Step 2: Quick irrelevant query check
            if self.text_processor.is_irrelevant_query(query):
                return self._create_fallback_result(0.1, DetectionMethod.FALLBACK)

            # Step 3: Parallel detection for better performance
            rule_match = await self.rule_detector.detect(query)
            vector_result = None

            # Only do vector search if rule confidence is not high enough
            if not rule_match or rule_match.score < self.config.early_exit_threshold:
                vector_result = await self._vector_search(query)

            # Step 4: Choose best result based on confidence
            best_result = self._select_best_result(rule_match, vector_result)

            # Step 5: Cache only high-confidence results
            if best_result.confidence >= self.config.cache_min_confidence:
                await self._cache_result(query, best_result)

            return best_result

        except VectorSearchError as e:
            logger.warning(f"Vector search failed: {e}")
            return self._create_fallback_result(0.1, DetectionMethod.FALLBACK)
        except RuleDetectionError as e:
            logger.warning(f"Rule detection failed: {e}")
            return self._create_fallback_result(0.1, DetectionMethod.FALLBACK)
        except Exception as e:
            logger.error(f"Unexpected error in intent detection: {e}")
            return self._create_fallback_result(0.1, DetectionMethod.FALLBACK)
    
    async def _vector_search(self, query: str) -> Optional[IntentResult]:
        """Optimized vector search for intent detection"""
        if not self.vector_search_enabled:
            return None

        try:
            # Generate query embedding with timeout
            if not self.embedding_service:
                return None
            query_embedding = self.embedding_service.get_embedding(query)
            if not query_embedding:
                return None

            # Search in vector store with optimized parameters
            if not self.vector_store:
                return None
            candidates = await self.vector_store.search(
                query_vector=query_embedding,
                top_k=self.config.vector_top_k,
                score_threshold=self.config.vector_confidence_threshold * 0.8  # Lower threshold for search
            )

            if not candidates:
                return None

            # Use best candidate with confidence adjustment
            best_candidate = candidates[0]

            # Apply confidence boost for very high scores
            adjusted_confidence = best_candidate.score  # Use score directly
            if best_candidate.score >= 0.9:
                adjusted_confidence = min(0.95, adjusted_confidence * 1.1)

            return IntentResult(
                id=best_candidate.intent_id,
                confidence=adjusted_confidence,
                method=DetectionMethod.VECTOR,
                metadata={
                    "score": best_candidate.score,
                    "metadata": best_candidate.metadata
                }
            )

        except Exception as e:
            logger.warning(f"Vector search error: {e}")
            return None

    def _select_best_result(self, rule_match: Optional[RuleMatch], vector_result: Optional[IntentResult]) -> IntentResult:
        """Select the best result between rule-based and vector search"""
        # If both are None, return fallback
        if rule_match is None and vector_result is None:
            return self._create_fallback_result(0.1, DetectionMethod.FALLBACK)

        # If only vector_result exists
        if rule_match is None and vector_result is not None:
            return vector_result

        # If only rule_match exists
        if rule_match is not None and vector_result is None:
            return IntentResult(
                id=rule_match.intent_id,
                confidence=rule_match.score,
                method=DetectionMethod.RULE,
                metadata={"rule_match": rule_match.rule_metadata}
            )

        # Both exist, compare confidence scores
        if rule_match is not None and vector_result is not None:
            if rule_match.score >= vector_result.confidence:
                return IntentResult(
                    id=rule_match.intent_id,
                    confidence=rule_match.score,
                    method=DetectionMethod.RULE,
                    metadata={"rule_match": rule_match.rule_metadata}
                )
            else:
                return vector_result

        # Fallback case
        return self._create_fallback_result(0.1, DetectionMethod.FALLBACK)

    def _create_fallback_result(self, confidence: float, method: DetectionMethod) -> IntentResult:
        """Create fallback result when detection fails"""
        return IntentResult(
            id="unknown",
            confidence=confidence,
            method=method,
            metadata={"fallback": True}
        )

    async def _get_cached_result(self, query: str) -> Optional[IntentResult]:
        """Get cached result for query"""
        if not self.cache_service:
            return None

        cache_key = self._generate_cache_key(query)
        cached_data = await self.cache_service.get(cache_key)
        
        if cached_data:
            return IntentResult(**cached_data)
        return None

    async def _cache_result(self, query: str, result: IntentResult) -> None:
        """Cache intent detection result"""
        if not self.cache_service:
            return

        cache_key = self._generate_cache_key(query)
        cache_data = {
            "id": result.id,
            "confidence": result.confidence,
            "method": result.method,
            "category": result.category,
            "metadata": result.metadata,
            "timestamp": result.timestamp
        }
        await self.cache_service.set(cache_key, cache_data, ttl_seconds=3600)  # 1 hour TTL

    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"intent_detection:{query_hash}"
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        
        if self.cache_service:
            cache_stats = await self.cache_service.get_stats()
            stats["cache"] = cache_stats
        
        if self.vector_store:
            vector_info = await self.vector_store.get_collection_info()
            stats["vector_store"] = vector_info
        
        return stats
