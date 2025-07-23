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
from infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingService
from infrastructure.caching.memory_cache import MemoryCacheService
from shared.types import DetectionMethod, QueryText, IntentId
from shared.utils.text_processing import VietnameseTextProcessor

logger = logging.getLogger(__name__)

class IntentDetectionError(Exception):
    """Base exception for intent detection errors"""
    pass

class VectorSearchError(IntentDetectionError):
    """Exception for vector search failures"""
    pass

class RuleDetectionError(IntentDetectionError):
    """Exception for rule-based detection failures"""
    pass


@dataclass
class HybridConfig:
    """Optimized configuration for hybrid intent detection"""
    # Rule-based thresholds - Aligned with old system for better results
    rule_high_confidence_threshold: float = 0.7   # Matched with old system (was 0.75)
    rule_medium_confidence_threshold: float = 0.3  # Matched with old system (was 0.4)
    early_exit_threshold: float = 0.8  # Reduced from 0.85 for better detection

    # Vector search thresholds
    vector_confidence_threshold: float = 0.6  # Reduced from 0.65 for better recall
    vector_top_k: int = 3  # Reduced for performance

    # Caching optimization
    enable_caching: bool = True
    cache_ttl_seconds: int = 600  # Longer cache for stable results
    cache_min_confidence: float = 0.5  # Only cache good results


class HybridIntentDetectionService:
    """
    Hybrid intent detection service combining rule-based and vector search
    """
    
    def __init__(
        self,
        rule_detector: RuleBasedDetectorImpl,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_service: Optional[OpenAIEmbeddingService] = None,
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
            self.embedding_service and 
            self.embedding_service.available
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
            query_embedding = await self.embedding_service.embed_text(query)
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
            adjusted_confidence = best_candidate.score  # Use score directly, not normalized_score
            if best_candidate.score >= 0.9:
                adjusted_confidence = min(0.95, adjusted_confidence * 1.1)

            return IntentResult(
                id=best_candidate.intent_id,
                confidence=adjusted_confidence,
                method=DetectionMethod.VECTOR,
                metadata={
                    "vector_score": best_candidate.score,
                    "source_text": best_candidate.text[:100],  # Truncate for performance
                    "candidates_count": len(candidates),
                    "confidence_adjusted": adjusted_confidence != best_candidate.score
                }
            )

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise VectorSearchError(f"Vector search failed: {e}") from e
    
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
        """Cache result for query"""
        if not self.cache_service or not self.config.enable_caching:
            return
        
        cache_key = self._generate_cache_key(query)
        cache_data = {
            "id": result.id,
            "confidence": result.confidence,
            "method": result.method,
            "metadata": result.metadata,
            "timestamp": result.timestamp
        }
        
        await self.cache_service.set(
            cache_key, 
            cache_data, 
            ttl_seconds=self.config.cache_ttl_seconds
        )
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key for query"""
        normalized_query = self.text_processor.normalize_vietnamese(query)
        return f"intent:{hashlib.md5(normalized_query.encode()).hexdigest()}"
    
    def _select_best_result(self, rule_match: Optional[Any], vector_result: Optional[IntentResult]) -> IntentResult:
        """
        Select the best result from rule-based and vector search
        Optimized logic with clear priority rules
        """
        # Priority 1: High confidence rule match (early exit)
        if rule_match and rule_match.score >= self.config.early_exit_threshold:
            return self._create_rule_result(rule_match, DetectionMethod.RULE)

        # Priority 2: High confidence vector result
        if vector_result and vector_result.confidence >= self.config.vector_confidence_threshold:
            # If both are high confidence, prefer the higher one
            if rule_match and rule_match.score >= self.config.rule_high_confidence_threshold:
                if vector_result.confidence > rule_match.score:
                    return vector_result
                else:
                    return self._create_rule_result(rule_match, DetectionMethod.HYBRID)
            return vector_result

        # Priority 3: High confidence rule match
        if rule_match and rule_match.score >= self.config.rule_high_confidence_threshold:
            return self._create_rule_result(rule_match, DetectionMethod.RULE)

        # Priority 4: Medium confidence rule match
        if rule_match and rule_match.score >= self.config.rule_medium_confidence_threshold:
            return self._create_rule_result(rule_match, DetectionMethod.RULE)

        # Priority 5: Any vector result
        if vector_result:
            return vector_result

        # Final fallback
        return self._create_fallback_result(0.2, DetectionMethod.FALLBACK)

    def _create_rule_result(self, rule_match: Any, method: DetectionMethod) -> IntentResult:
        """Create IntentResult from rule match"""
        return IntentResult(
            id=rule_match.intent_id,
            confidence=rule_match.score,
            method=method,
            metadata={
                "matched_keywords": rule_match.matched_keywords,
                "matched_patterns": rule_match.matched_patterns,
                "rule_weight": rule_match.weight
            }
        )

    def _create_fallback_result(self, confidence: float, method: DetectionMethod) -> IntentResult:
        """Create fallback intent result"""
        return IntentResult(
            id="unknown",
            confidence=confidence,
            method=method,
            metadata={"fallback": True, "reason": "no_intent_detected"}
        )
    
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
