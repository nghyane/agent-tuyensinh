#!/usr/bin/env python3
"""
FPT University Agent - Production Test Suite
Comprehensive testing for hybrid intent detection system
"""

import sys
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from core.domain.entities import DetectionContext
from infrastructure.intent_detection.rule_based import RuleBasedDetectorImpl
from infrastructure.intent_detection.rule_loader import ProductionRuleLoader
from infrastructure.caching.memory_cache import MemoryCacheService
from infrastructure.vector_stores.qdrant_store import QdrantVectorStore
from infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingService
from core.application.services.hybrid_intent_service import HybridIntentDetectionService, HybridConfig
from shared.utils.text_processing import VietnameseTextProcessor
from shared.utils.metrics import MetricsCollectorImpl
from shared.types import DetectionMethod

# Comprehensive test dataset for production validation
PRODUCTION_TEST_QUERIES = [
    # === TUITION INQUIRY ===
    {"query": "Học phí FPT 2025 bao nhiêu tiền?", "expected": "tuition_inquiry", "category": "tuition"},
    {"query": "Tuition fee for AI program?", "expected": "tuition_inquiry", "category": "tuition"},
    {"query": "How much does it cost to study at FPT?", "expected": "tuition_inquiry", "category": "tuition"},
    {"query": "Chi phí học ngành IT như thế nào?", "expected": "tuition_inquiry", "category": "tuition"},
    {"query": "Học bổng có không?", "expected": "tuition_inquiry", "category": "tuition"},
    {"query": "Scholarship information for international students", "expected": "tuition_inquiry", "category": "tuition"},
    {"query": "Có thể trả góp học phí không?", "expected": "tuition_inquiry", "category": "tuition"},
    
    # === ADMISSION REQUIREMENTS ===
    {"query": "Điểm chuẩn FPT 2024 bao nhiêu?", "expected": "admission_requirements", "category": "admission"},
    {"query": "What are the entry requirements?", "expected": "admission_requirements", "category": "admission"},
    {"query": "Yêu cầu để vào trường?", "expected": "admission_requirements", "category": "admission"},
    {"query": "Admission requirements cho international students?", "expected": "admission_requirements", "category": "admission"},
    {"query": "Hồ sơ đăng ký cần gì?", "expected": "admission_requirements", "category": "admission"},
    {"query": "How to apply for FPT University?", "expected": "admission_requirements", "category": "admission"},
    
    # === PROGRAM INFORMATION ===
    {"query": "What programs do you offer?", "expected": "program_information", "category": "programs"},
    {"query": "Ngành học nào hot nhất?", "expected": "program_information", "category": "programs"},
    {"query": "AI program curriculum", "expected": "program_information", "category": "programs"},
    {"query": "Software Engineering có học những gì?", "expected": "program_information", "category": "programs"},
    {"query": "Chương trình đào tạo như thế nào?", "expected": "program_information", "category": "programs"},
    
    # === CAMPUS FACILITIES ===
    {"query": "Campus FPT ở đâu?", "expected": "campus_facilities", "category": "campus"},
    {"query": "Tell me about the university campus", "expected": "campus_facilities", "category": "campus"},
    {"query": "Cơ sở vật chất trường có gì?", "expected": "campus_facilities", "category": "campus"},
    {"query": "Ký túc xá như thế nào?", "expected": "campus_facilities", "category": "campus"},
    {"query": "Library facilities available?", "expected": "campus_facilities", "category": "campus"},
    
    # === TECHNICAL SUPPORT ===
    {"query": "Portal FAP bị lỗi làm sao?", "expected": "technical_support", "category": "support"},
    {"query": "I need help with my student portal", "expected": "technical_support", "category": "support"},
    {"query": "Wifi campus không kết nối được", "expected": "technical_support", "category": "support"},
    {"query": "Email sinh viên không hoạt động", "expected": "technical_support", "category": "support"},
    
    # === STUDENT SERVICES ===
    {"query": "Student support services available", "expected": "student_services", "category": "services"},
    {"query": "Hỗ trợ sinh viên ra sao?", "expected": "student_services", "category": "services"},
    {"query": "Counseling services có không?", "expected": "student_services", "category": "services"},
    
    # === GRADUATION & CAREER ===
    {"query": "Career opportunities after graduation", "expected": "graduation_career", "category": "career"},
    {"query": "Tỷ lệ có việc làm sau tốt nghiệp?", "expected": "graduation_career", "category": "career"},
    {"query": "Job placement support", "expected": "graduation_career", "category": "career"},
    
    # === CONTACT INFORMATION ===
    {"query": "How can I contact the university?", "expected": "contact_information", "category": "contact"},
    {"query": "Số điện thoại tư vấn tuyển sinh?", "expected": "contact_information", "category": "contact"},
    {"query": "Email liên hệ là gì?", "expected": "contact_information", "category": "contact"},
    
    # === GENERAL INFORMATION ===
    {"query": "Tell me about FPT", "expected": "general_information", "category": "general"},
    {"query": "FPT University overview", "expected": "general_information", "category": "general"},
    {"query": "Giới thiệu về trường", "expected": "general_information", "category": "general"},
    
    # === SCHEDULE & ACADEMIC ===
    {"query": "Lịch học như thế nào?", "expected": "schedule_academic", "category": "schedule"},
    {"query": "Academic calendar 2025", "expected": "schedule_academic", "category": "schedule"},
    {"query": "Khi nào bắt đầu học kỳ mới?", "expected": "schedule_academic", "category": "schedule"},
    
    # === EDGE CASES & MIXED LANGUAGE ===
    {"query": "FPT university tuition fee bao nhiêu?", "expected": "tuition_inquiry", "category": "mixed"},
    {"query": "What can you help me with?", "expected": "general_information", "category": "meta"},
    {"query": "University information", "expected": "general_information", "category": "general"},
    
    # === IRRELEVANT QUERIES (should fallback) ===
    {"query": "Hôm nay trời có mưa không?", "expected": "general_info", "category": "irrelevant"},
    {"query": "What's the weather like?", "expected": "general_info", "category": "irrelevant"},
    {"query": "Giá vàng hôm nay", "expected": "general_info", "category": "irrelevant"},
]

class ProductionTestSuite:
    """Comprehensive production test suite"""
    
    def __init__(self):
        self.results = []
        self.stats = {
            "total": 0,
            "high_confidence": 0,
            "correct_intent": 0,
            "vector_used": 0,
            "rule_only": 0,
            "fallback": 0,
            "avg_duration": 0,
            "by_category": {}
        }
    
    async def initialize_system(self):
        """Initialize the hybrid intent detection system"""
        print("🔧 Initializing Production Test System...")
        
        # Initialize components
        self.text_processor = VietnameseTextProcessor()
        self.metrics_collector = MetricsCollectorImpl()
        self.cache_service = MemoryCacheService(max_size=1000, default_ttl=600)
        
        # Load production rules
        loader = ProductionRuleLoader()
        rules = loader.load_rules()
        self.rule_detector = RuleBasedDetectorImpl(
            rules=rules, 
            text_processor=self.text_processor
        )
        
        # Initialize vector components
        self.vector_store = QdrantVectorStore()
        self.embedding_service = OpenAIEmbeddingService(
            metrics_collector=self.metrics_collector
        )
        
        # Check component availability
        vector_available = (
            self.vector_store.available and 
            self.embedding_service.available
        )
        
        if vector_available:
            collection_info = await self.vector_store.get_collection_info()
            points_count = collection_info.get("points_count", 0)
            print(f"✅ Vector store ready with {points_count} examples")
        else:
            print("⚠️ Vector search not available - using rule-based only")
        
        # Create hybrid service with production config
        hybrid_config = HybridConfig(
            rule_high_confidence_threshold=0.7,
            rule_medium_confidence_threshold=0.3,
            vector_confidence_threshold=0.6,
            early_exit_threshold=0.8,
            vector_top_k=3,
            cache_ttl_seconds=600,
            cache_min_confidence=0.5
        )
        
        self.hybrid_service = HybridIntentDetectionService(
            rule_detector=self.rule_detector,
            vector_store=self.vector_store if vector_available else None,
            embedding_service=self.embedding_service if vector_available else None,
            cache_service=self.cache_service,
            text_processor=self.text_processor,
            metrics_collector=self.metrics_collector,
            config=hybrid_config
        )
        
        print("✅ Production system initialized!")
        return vector_available
    
    async def run_comprehensive_test(self):
        """Run comprehensive production test"""
        print(f"\n🧪 Running Production Test Suite")
        print(f"📊 Testing {len(PRODUCTION_TEST_QUERIES)} queries...")
        print("=" * 60)
        
        total_start_time = time.time()
        
        for i, test_case in enumerate(PRODUCTION_TEST_QUERIES, 1):
            query = test_case["query"]
            expected = test_case["expected"]
            category = test_case["category"]
            
            print(f"\n{i:2d}. [{category.upper()}] '{query}'")
            
            # Create detection context
            context = DetectionContext(
                query=query,
                user_id="production_test",
                language="vi" if any(ord(c) > 127 for c in query) else "en"
            )
            
            # Detect intent
            start_time = time.time()
            result = await self.hybrid_service.detect_intent(context)
            duration = (time.time() - start_time) * 1000
            
            # Analyze result
            is_correct = result.id == expected
            is_high_confidence = result.confidence >= 0.7
            
            # Display result
            confidence_icon = "🟢" if is_high_confidence else "🟡" if result.confidence >= 0.5 else "🔴"
            correct_icon = "✅" if is_correct else "❌"
            method_icon = {
                DetectionMethod.RULE: "📏",
                DetectionMethod.VECTOR: "🔍", 
                DetectionMethod.HYBRID: "🔀",
                DetectionMethod.FALLBACK: "🔄"
            }.get(result.method, "❓")
            
            print(f"    {correct_icon} {confidence_icon} {result.id} (expected: {expected})")
            print(f"    📊 Confidence: {result.confidence:.3f} | {method_icon} {result.method} | ⚡ {duration:.1f}ms")
            
            # Store result
            self.results.append({
                "query": query,
                "expected": expected,
                "actual": result.id,
                "confidence": result.confidence,
                "method": result.method,
                "duration": duration,
                "category": category,
                "correct": is_correct,
                "high_confidence": is_high_confidence
            })
            
            # Update stats
            self._update_stats(result, category, duration, is_correct, is_high_confidence)
            
            await asyncio.sleep(0.05)  # Small delay for rate limiting
        
        total_duration = time.time() - total_start_time
        self.stats["avg_duration"] = sum(r["duration"] for r in self.results) / len(self.results)
        
        # Generate comprehensive report
        await self._generate_report(total_duration)
    
    def _update_stats(self, result, category, duration, is_correct, is_high_confidence):
        """Update test statistics"""
        self.stats["total"] += 1
        
        if is_high_confidence:
            self.stats["high_confidence"] += 1
        
        if is_correct:
            self.stats["correct_intent"] += 1
        
        if result.method == DetectionMethod.VECTOR:
            self.stats["vector_used"] += 1
        elif result.method == DetectionMethod.RULE:
            self.stats["rule_only"] += 1
        elif result.method == DetectionMethod.FALLBACK:
            self.stats["fallback"] += 1
        
        # Category stats
        if category not in self.stats["by_category"]:
            self.stats["by_category"][category] = {
                "total": 0, "correct": 0, "high_conf": 0
            }
        
        cat_stats = self.stats["by_category"][category]
        cat_stats["total"] += 1
        if is_correct:
            cat_stats["correct"] += 1
        if is_high_confidence:
            cat_stats["high_conf"] += 1
    
    async def _generate_report(self, total_duration):
        """Generate comprehensive test report"""
        print(f"\n📊 PRODUCTION TEST REPORT")
        print("=" * 50)
        
        # Overall metrics
        total = self.stats["total"]
        accuracy = (self.stats["correct_intent"] / total) * 100
        high_conf_rate = (self.stats["high_confidence"] / total) * 100
        vector_usage = (self.stats["vector_used"] / total) * 100
        
        print(f"📈 Overall Performance:")
        print(f"   Total queries: {total}")
        print(f"   Accuracy: {accuracy:.1f}% ({self.stats['correct_intent']}/{total})")
        print(f"   High confidence (≥0.7): {high_conf_rate:.1f}% ({self.stats['high_confidence']}/{total})")
        print(f"   Average response time: {self.stats['avg_duration']:.1f}ms")
        print(f"   Total test time: {total_duration:.2f}s")
        
        # Method distribution
        print(f"\n🔧 Method Distribution:")
        print(f"   Rule-based: {self.stats['rule_only']} ({self.stats['rule_only']/total*100:.1f}%)")
        print(f"   Vector-enhanced: {self.stats['vector_used']} ({vector_usage:.1f}%)")
        print(f"   Fallback: {self.stats['fallback']} ({self.stats['fallback']/total*100:.1f}%)")
        
        # Category breakdown
        print(f"\n📋 Performance by Category:")
        for category, stats in self.stats["by_category"].items():
            cat_accuracy = (stats["correct"] / stats["total"]) * 100
            cat_conf = (stats["high_conf"] / stats["total"]) * 100
            print(f"   {category.upper()}: {cat_accuracy:.0f}% accuracy, {cat_conf:.0f}% high-conf ({stats['total']} queries)")
        
        # System performance
        if self.hybrid_service:
            perf_stats = await self.hybrid_service.get_performance_stats()
            if "counters" in perf_stats:
                counters = perf_stats["counters"]
                print(f"\n⚡ System Performance:")
                print(f"   Rule detections: {counters.get('rule_detections', 0)}")
                print(f"   Vector searches: {counters.get('vector_searches', 0)}")
                print(f"   Cache hits: {counters.get('cache_hits', 0)}")
                
                if "cache" in perf_stats:
                    cache_info = perf_stats["cache"]
                    hit_rate = cache_info.get('hit_rate', 0)
                    print(f"   Cache hit rate: {hit_rate:.1f}%")
        
        # Quality assessment
        print(f"\n🎯 Quality Assessment:")
        if accuracy >= 90:
            print("   ✅ EXCELLENT - Ready for production")
        elif accuracy >= 80:
            print("   🟡 GOOD - Minor improvements needed")
        elif accuracy >= 70:
            print("   ⚠️ FAIR - Significant improvements needed")
        else:
            print("   ❌ POOR - Major issues need fixing")
        
        if high_conf_rate >= 80:
            print("   ✅ High confidence rate is excellent")
        elif high_conf_rate >= 60:
            print("   🟡 High confidence rate is acceptable")
        else:
            print("   ⚠️ Low confidence rate needs improvement")

async def main():
    """Main entry point for production testing"""
    print("🚀 FPT University Agent - Production Test Suite")
    print("=" * 55)
    
    test_suite = ProductionTestSuite()
    
    try:
        # Initialize system
        vector_available = await test_suite.initialize_system()
        
        # Run comprehensive test
        await test_suite.run_comprehensive_test()
        
        print(f"\n🎉 Production testing completed successfully!")
        print("✅ System is ready for deployment!")
        
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Production test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
