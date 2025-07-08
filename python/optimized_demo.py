#!/usr/bin/env python3
"""
FPT University Agent - Optimized Hybrid Demo
Showcasing optimized intent detection with improved performance
"""

import sys
import asyncio
import time
from pathlib import Path
from typing import List

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Core imports
from core.domain.entities import DetectionContext, IntentResult
from infrastructure.intent_detection.rule_based import RuleBasedDetectorImpl
from infrastructure.intent_detection.rule_loader import ProductionRuleLoader
from infrastructure.caching.memory_cache import MemoryCacheService
from infrastructure.vector_stores.qdrant_store import QdrantVectorStore
from infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingService
from core.application.services.hybrid_intent_service import HybridIntentDetectionService, HybridConfig
from shared.utils.text_processing import VietnameseTextProcessor
from shared.utils.metrics import MetricsCollectorImpl
from shared.types import DetectionMethod

# Optimized test queries
OPTIMIZED_TEST_QUERIES = [
    "Học phí FPT 2025 bao nhiêu tiền?",
    "Tuition fee for AI program?", 
    "Điểm chuẩn FPT 2024 bao nhiêu?",
    "Campus FPT ở đâu?",
    "Portal FAP bị lỗi làm sao?",
    "Scholarship information for international students",
    "Hôm nay trời có mưa không?"  # Irrelevant query
]

def load_production_rules():
    """Load production rules with error handling"""
    try:
        loader = ProductionRuleLoader()
        rules = loader.load_rules()
        
        metadata = loader.get_rules_metadata()
        if metadata and metadata.get('coverage_areas'):
            print(f"📊 Rule Coverage: {', '.join(metadata['coverage_areas'])}")
        
        print(f"✅ Loaded {len(rules)} production rules")
        return rules
    except Exception as e:
        print(f"⚠️ Failed to load production rules: {e}")
        return []

async def run_optimized_demo():
    """Run optimized hybrid intent detection demo"""
    
    print("🚀 FPT University Agent - Optimized Hybrid Demo")
    print("=" * 55)
    
    # Initialize components with optimized settings
    print("🔧 Initializing optimized components...")
    
    text_processor = VietnameseTextProcessor()
    metrics_collector = MetricsCollectorImpl()
    cache_service = MemoryCacheService(max_size=500, default_ttl=600)  # Optimized cache
    
    # Load production rules
    rules = load_production_rules()
    if not rules:
        print("❌ No rules loaded, exiting...")
        return
    
    rule_detector = RuleBasedDetectorImpl(rules=rules, text_processor=text_processor)
    
    # Initialize vector components with graceful degradation
    vector_store = None
    embedding_service = None
    hybrid_service = None
    
    try:
        vector_store = QdrantVectorStore()
        embedding_service = OpenAIEmbeddingService(metrics_collector=metrics_collector)
        
        if vector_store.available and embedding_service.available:
            print("✅ Vector search components available")
            
            # Optimized hybrid configuration - Aligned with old system thresholds
            hybrid_config = HybridConfig(
                rule_high_confidence_threshold=0.7,   # Matched with old system
                rule_medium_confidence_threshold=0.3,  # Matched with old system
                vector_confidence_threshold=0.6,      # Slightly reduced for better recall
                early_exit_threshold=0.8,             # Reduced for better detection
                vector_top_k=3,  # Reduced for performance
                cache_ttl_seconds=600,  # Longer cache
                cache_min_confidence=0.5  # Only cache good results
            )
            
            hybrid_service = HybridIntentDetectionService(
                rule_detector=rule_detector,
                vector_store=vector_store,
                embedding_service=embedding_service,
                cache_service=cache_service,
                text_processor=text_processor,
                metrics_collector=metrics_collector,
                config=hybrid_config
            )
            
            # Check vector index status
            collection_info = await vector_store.get_collection_info()
            points_count = collection_info.get("points_count", 0)
            
            if points_count > 0:
                print(f"✅ Vector store ready with {points_count} indexed examples")
            else:
                print("⚠️ Vector store is empty - will use rule-based fallback")
        else:
            print("⚠️ Vector components not available - using rule-based only")
            
    except Exception as e:
        print(f"⚠️ Vector initialization failed: {e}")
        print("🔄 Falling back to rule-based detection")
    
    print("✅ Optimized components initialized!")
    print()
    
    # Performance testing
    print("🎯 Testing optimized intent detection...")
    print("-" * 45)
    
    total_start_time = time.time()
    results = []
    
    for i, query in enumerate(OPTIMIZED_TEST_QUERIES, 1):
        print(f"\n{i}. Query: '{query}'")
        
        context = DetectionContext(
            query=query,
            user_id="optimized_demo_user",
            language="vi" if any(ord(c) > 127 for c in query) else "en"
        )
        
        start_time = time.time()
        
        if hybrid_service:
            # Use optimized hybrid detection
            intent_result = await hybrid_service.detect_intent(context)
        else:
            # Fallback to rule-based only
            rule_match = await rule_detector.detect(query)
            if rule_match:
                intent_result = IntentResult(
                    id=rule_match.intent_id,
                    confidence=rule_match.score,
                    method=DetectionMethod.RULE,
                    metadata={
                        "matched_keywords": rule_match.matched_keywords,
                        "matched_patterns": rule_match.matched_patterns
                    }
                )
            else:
                intent_result = IntentResult(
                    id="general_info",
                    confidence=0.2,
                    method=DetectionMethod.FALLBACK
                )
        
        duration_ms = (time.time() - start_time) * 1000
        results.append((query, intent_result, duration_ms))
        
        # Display results with enhanced formatting
        confidence_icon = "🟢" if intent_result.confidence >= 0.7 else "🟡" if intent_result.confidence >= 0.5 else "🔴"
        method_icon = {
            DetectionMethod.RULE: "📏",
            DetectionMethod.VECTOR: "🔍", 
            DetectionMethod.HYBRID: "🔀",
            DetectionMethod.FALLBACK: "🔄"
        }.get(intent_result.method, "❓")
        
        print(f"   {confidence_icon} Intent: {intent_result.id}")
        print(f"   📊 Confidence: {intent_result.confidence:.3f}")
        print(f"   {method_icon} Method: {intent_result.method}")
        print(f"   ⚡ Duration: {duration_ms:.1f}ms")
        
        # Show optimization details
        if intent_result.metadata.get("matched_keywords"):
            keywords = intent_result.metadata["matched_keywords"][:3]  # Show first 3
            print(f"   🔑 Keywords: {keywords}")
        
        if intent_result.metadata.get("confidence_adjusted"):
            print(f"   🎯 Confidence boosted by vector similarity")
        
        await asyncio.sleep(0.05)  # Small delay for readability
    
    total_duration = time.time() - total_start_time
    
    # Enhanced performance summary
    print("\n📊 Optimized Performance Summary:")
    print("-" * 35)
    
    if hybrid_service:
        stats = await hybrid_service.get_performance_stats()
        
        if "counters" in stats:
            counters = stats["counters"]
            print(f"Rule detections: {counters.get('rule_detections', 0)}")
            print(f"Vector searches: {counters.get('vector_searches', 0)}")
            print(f"Cache hits: {counters.get('cache_hits', 0)}")
            print(f"Cache misses: {counters.get('cache_misses', 0)}")
        
        if "cache" in stats:
            cache_info = stats["cache"]
            hit_rate = cache_info.get('hit_rate', 0)
            print(f"Cache hit rate: {hit_rate:.1f}%")
    
    # Performance metrics
    avg_duration = sum(r[2] for r in results) / len(results)
    high_confidence_count = sum(1 for r in results if r[1].confidence >= 0.7)
    
    print(f"\nTotal processing time: {total_duration:.2f}s")
    print(f"Average query time: {avg_duration:.1f}ms")
    print(f"High confidence results: {high_confidence_count}/{len(results)}")
    print(f"Throughput: {len(results)/total_duration:.1f} queries/sec")
    
    print("\n🎉 Optimized demo completed!")
    print("✅ Enhanced hybrid intent detection ready for production!")

def main():
    """Main entry point"""
    try:
        asyncio.run(run_optimized_demo())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
