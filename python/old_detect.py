"""
Hybrid Intent Detection Service
"""
import os
import functools
import json
import hashlib
import time
from functools import lru_cache
from dotenv import load_dotenv
from .intent_rules import INTENT_RULES
from typing import Optional, Dict, Any, List, Tuple
from qdrant_client import QdrantClient
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.settings import Settings
from llama_index.core.schema import NodeWithScore
from sentence_transformers import CrossEncoder
try:
    from unidecode import unidecode
    UNIDECODE_AVAILABLE = True
except ImportError:
    UNIDECODE_AVAILABLE = False
    print("⚠️ unidecode không có sẵn, sẽ sử dụng normalization đơn giản")

load_dotenv()


class HybridIntentDetectionService:
    """
    Phát hiện intent từ câu query.
    Ưu tiên rule-based, fallback với vector-based.
    """

    def __init__(self):
        self.rule_patterns = INTENT_RULES
        self._load_config()

        # Ngưỡng chung cho rule-based
        self.high_confidence_threshold = 0.7
        self.medium_confidence_threshold = 0.3

        # Reranker threshold được tăng lên để tránh false positive
        self.reranker_threshold = 2.0

        # Cache cho query results
        self.query_cache = {}
        self.cache_ttl = 300  # 5 phút

        # Performance tracking
        self.performance_stats = {
            "rule_calls": 0,
            "vector_calls": 0,
            "cache_hits": 0,
            "total_time": 0
        }

        # Tải mô hình Cross-Encoder
        try:
            print("⏳ Đang tải mô hình Cross-Encoder...")
            self.cross_encoder = CrossEncoder(
                'cross-encoder/ms-marco-MiniLM-L-6-v2')
            print("✅ Cross-Encoder đã được tải thành công.")
            self.reranker_enabled = True
        except Exception as e:
            print(
                f"⚠️ Không thể tải Cross-Encoder, Reranker sẽ bị vô hiệu hóa: {e}")
            self.reranker_enabled = False

        # Khởi tạo vector search
        self._init_vector_search()

    def _load_config(self):
        """Tải các cấu hình động từ file JSON."""
        file_path = os.path.join(
            os.path.dirname(
                __file__), '..', 'data', 'intent-examples-augmented.json'
        )
        with open(file_path, 'r', encoding='utf-8') as f:
            intent_data = json.load(f)

        # Load ngưỡng tin cậy động cho vector search
        self.vector_thresholds = {
            intent["id"]: intent.get("vector_confidence_threshold", 0.6)
            for intent in intent_data["intents"]
        }

    @staticmethod
    def _compare_matches(item1: Dict[str, Any], item2: Dict[str, Any]) -> int:
        """
        Hàm so sánh để sắp xếp các intent matches.
        - Ưu tiên intent xuất hiện trước nếu khoảng cách vị trí > 20 ký tự.
        - Ngược lại, ưu tiên intent có điểm cao hơn.
        """
        position1, score1 = item1['position'], item1['score']
        position2, score2 = item2['position'], item2['score']

        if abs(position1 - position2) > 20:
            return position1 - position2

        if score1 > score2:
            return -1
        if score2 > score1:
            return 1
        return 0

    def _normalize_vietnamese_text(self, text: str) -> str:
        """
        Chuẩn hóa text tiếng Việt để xử lý tốt hơn các trường hợp không dấu.
        """
        if not text:
            return text

        # Bước 1: Chuyển về lowercase
        text = text.lower().strip()

        # Bước 2: Mapping các từ viết tắt phổ biến và technical terms
        abbreviation_map = {
            'fpt': 'fpt university',
            'cntt': 'công nghệ thông tin',
            'it': 'information technology',
            'ai': 'artificial intelligence',
            'se': 'software engineering',
            'bkhn': 'bach khoa ha noi',
            'hcm': 'ho chi minh',
            'hn': 'ha noi',
            'ojt': 'on job training'
        }

        # Bước 2.1: Mapping technical terms với học phí
        technical_tuition_map = {
            'se program tuition': 'software engineering học phí',
            'it program tuition': 'information technology học phí',
            'ai program tuition': 'artificial intelligence học phí',
            'program tuition': 'chương trình học phí',
            'tuition fee': 'học phí',
            'course fee': 'học phí khóa học',
            'program fee': 'học phí chương trình'
        }

        # Áp dụng technical tuition mapping trước (ưu tiên cao hơn)
        for tech_term, replacement in technical_tuition_map.items():
            text = text.replace(tech_term, replacement)

        for abbr, full in abbreviation_map.items():
            text = text.replace(abbr, full)

        # Bước 3: Mapping tiếng Việt không dấu
        vietnamese_map = {
            'hoc phi': 'học phí',
            'nganh': 'ngành',
            'an toan thong tin': 'an toàn thông tin',
            'han chot': 'hạn chót',
            'nop ho so': 'nộp hồ sơ',
            'diem chuan': 'điểm chuẩn',
            'hoc bong': 'học bổng',
            'thu vien': 'thư viện',
            'ky tuc xa': 'ký túc xá',
            'so sanh': 'so sánh',
            'tuong lai': 'tương lai',
            'viec lam': 'việc làm'
        }

        for no_accent, with_accent in vietnamese_map.items():
            text = text.replace(no_accent, with_accent)

        # Bước 4: Sử dụng unidecode nếu có sẵn để xử lý các trường hợp khác
        if UNIDECODE_AVAILABLE:
            # Tạo phiên bản không dấu để so sánh
            text_no_accent = unidecode(text)
            # Giữ nguyên text gốc nhưng có thể sử dụng text_no_accent để matching
            return text

        return text

    def _init_vector_search(self):
        """Khởi tạo kết nối Qdrant và LlamaIndex cho vector search"""
        try:
            # Kết nối Qdrant
            self.qdrant_client = QdrantClient(
                host=os.getenv("QDRANT_HOST", "localhost"),
                port=int(os.getenv("QDRANT_PORT", 6333))
            )

            # Cấu hình embedding model
            Settings.embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=os.getenv("OPENAI_API_KEY"),
                api_base=os.getenv("OPENAI_BASE_URL")
            )
            Settings.llm = None

            # Tạo vector store
            vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name="intent_examples_python_hybrid"
            )

            # Tạo index từ vector store
            self.vector_index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store
            )

            # Tạo query engine với top_k lớn hơn cho Reranker
            self.query_engine = self.vector_index.as_query_engine(
                similarity_top_k=5
            )

            self.vector_search_enabled = True
            print("✅ Vector search đã được khởi tạo thành công")

        except Exception as e:
            print(f"⚠️ Không thể khởi tạo vector search: {e}")
            self.vector_search_enabled = False

    def _generate_cache_key(self, query: str) -> str:
        """Tạo cache key cho query"""
        return hashlib.md5(query.lower().encode()).hexdigest()

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Kiểm tra cache có còn hợp lệ không"""
        return time.time() - timestamp < self.cache_ttl

    def _get_cached_result(self, query: str) -> Optional[Dict[str, Any]]:
        """Lấy kết quả từ cache nếu có"""
        cache_key = self._generate_cache_key(query)
        if cache_key in self.query_cache:
            cached_data = self.query_cache[cache_key]
            if self._is_cache_valid(cached_data['timestamp']):
                self.performance_stats["cache_hits"] += 1
                return cached_data['result']
            else:
                # Xóa cache hết hạn
                del self.query_cache[cache_key]
        return None

    def _cache_result(self, query: str, result: Dict[str, Any]) -> None:
        """Lưu kết quả vào cache"""
        cache_key = self._generate_cache_key(query)
        self.query_cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }

        # Giới hạn cache size (chỉ giữ 1000 entries gần nhất)
        if len(self.query_cache) > 1000:
            # Xóa 20% cache cũ nhất
            sorted_cache = sorted(
                self.query_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for key, _ in sorted_cache[:200]:
                del self.query_cache[key]

    def _is_irrelevant_query(self, query: str) -> bool:
        """
        Kiểm tra xem query có phải là câu hỏi ngoài phạm vi không.
        """
        irrelevant_keywords = [
            'thời tiết', 'weather', 'mưa', 'nắng', 'trời', 'rain', 'sun',
            'nấu ăn', 'cooking', 'món ăn', 'recipe', 'phở', 'cơm',
            'giá vàng', 'gold price', 'chứng khoán', 'stock', 'bitcoin',
            'bóng đá', 'football', 'world cup', 'thể thao', 'sport',
            'âm nhạc', 'music', 'ca sĩ', 'singer', 'bài hát', 'song'
        ]

        query_lower = query.lower()
        for keyword in irrelevant_keywords:
            if keyword in query_lower:
                return True
        return False

    def detect(self, query: str) -> Dict[str, Any]:
        """
        Phát hiện intent chính từ câu query.
        Sử dụng hybrid approach: rule-based + vector search + reranker.
        """
        start_time = time.time()

        # Step 0: Kiểm tra cache trước
        cached_result = self._get_cached_result(query)
        if cached_result:
            return cached_result

        # Step 1: Kiểm tra câu hỏi irrelevant
        if self._is_irrelevant_query(query):
            result = self._create_fallback_intent(0.1)
            self._cache_result(query, result)
            return result

        # Step 2: Rule-based detection
        rule_result = self._detect_intent_rule(query)
        self.performance_stats["rule_calls"] += 1

        # Early exit với confidence rất cao (>= 0.9)
        if rule_result and rule_result["confidence"] >= 0.9:
            result = {
                "id": rule_result["intentId"],
                "confidence": rule_result["confidence"],
                "method": "rule"
            }
            self._cache_result(query, result)
            self.performance_stats["total_time"] += time.time() - start_time
            return result

        if rule_result and rule_result["confidence"] >= self.high_confidence_threshold:
            result = {
                "id": rule_result["intentId"],
                "confidence": rule_result["confidence"],
                "method": "rule"
            }
            self._cache_result(query, result)
            self.performance_stats["total_time"] += time.time() - start_time
            return result

        # Step 3: Vector-based detection + Reranking
        vector_result = self._detect_intent_vector(query)
        self.performance_stats["vector_calls"] += 1

        # Logic kết hợp mới: ưu tiên kết quả rerank
        if vector_result and vector_result.get("method") == "rerank":
            # Đặt ngưỡng tin cậy cho điểm rerank để tránh false positives
            # Điểm rerank > 2.0 mới được xem là đáng tin cậy
            if vector_result["confidence"] > self.reranker_threshold:
                result = {
                    "id": vector_result["intentId"],
                    "confidence": vector_result["confidence"],
                    "method": "rerank"
                }
                self._cache_result(query, result)
                self.performance_stats["total_time"] += time.time() - \
                    start_time
                return result
            else:
                print(
                    f"   ⚠️ Điểm Rerank ({vector_result['confidence']:.2f}) thấp hơn ngưỡng ({self.reranker_threshold}), bỏ qua.")

        # Fallback về rule-based nếu vector/rerank không có kết quả đáng tin
        if rule_result:
            result = {
                "id": rule_result["intentId"],
                "confidence": rule_result["confidence"],
                "method": "rule"
            }
            self._cache_result(query, result)
            self.performance_stats["total_time"] += time.time() - start_time
            return result

        # Fallback cuối cùng
        result = self._create_fallback_intent(0.1)
        self._cache_result(query, result)
        self.performance_stats["total_time"] += time.time() - start_time
        return result

    def _detect_intent_rule(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Logic phát hiện intent bằng rule-based.
        Cải tiến để xử lý multi-intent queries bằng cách ưu tiên vị trí xuất hiện.
        Tối ưu performance bằng early exit và optimized matching.
        """
        # Chuẩn hóa query trước khi xử lý
        query_normalized = self._normalize_vietnamese_text(query)
        query_lower = query_normalized.lower()
        all_matches: List[Dict[str, Any]] = []

        # Sắp xếp patterns theo weight giảm dần để kiểm tra high-priority trước
        sorted_patterns = sorted(
            self.rule_patterns, key=lambda x: x["matchers"]["weight"], reverse=True)

        for pattern in sorted_patterns:
            score = 0
            first_match_position = float('inf')
            matchers = pattern["matchers"]

            # Keyword matching với early exit
            keyword_found = False
            for keyword in matchers["keywords"]:
                keyword_index = query_lower.find(keyword)
                if keyword_index != -1:
                    score += 0.4 * matchers["weight"]
                    first_match_position = min(
                        first_match_position, keyword_index)
                    keyword_found = True
                    # Early exit nếu đã tìm thấy keyword có weight cao
                    if matchers["weight"] > 1.3 and score >= 0.8:
                        break

            # Pattern matching chỉ khi cần thiết
            if keyword_found or matchers["weight"] > 1.2:
                for regex in matchers["patterns"]:
                    match = regex.search(query_lower)
                    if match:
                        score += 0.6 * matchers["weight"]
                        first_match_position = min(
                            first_match_position, match.start())

            if score > 0:
                all_matches.append({
                    "intentId": pattern["intentId"],
                    "score": min(score, 1.0),
                    "position": first_match_position
                })

                # Early exit nếu tìm thấy match với confidence rất cao
                if score >= 1.0 and matchers["weight"] > 1.3:
                    return {
                        "intentId": pattern["intentId"],
                        "confidence": min(score, 1.0),
                    }

        if not all_matches:
            return None

        # Handle multi-intent queries
        if len(all_matches) > 1:
            all_matches.sort(key=functools.cmp_to_key(self._compare_matches))

            best_match = all_matches[0]
            # Nếu intent xuất hiện đầu tiên có điểm quá yếu, fallback về intent có điểm cao nhất
            if best_match['score'] < 0.6:
                best_match = max(all_matches, key=lambda x: x['score'])
        else:
            best_match = all_matches[0]

        return {
            "intentId": best_match["intentId"],
            "confidence": best_match["score"],
        }

    def _rerank_with_cross_encoder(self, query: str, nodes: List[NodeWithScore]) -> Optional[Dict[str, Any]]:
        """Sử dụng Cross-Encoder để xếp hạng lại các node ứng viên."""
        if not self.reranker_enabled or not nodes:
            return None

        try:
            # Tạo các cặp (query, node_text) để đưa vào model
            sentence_pairs = [(query, node.get_text()) for node in nodes]

            # Tính điểm số
            scores = self.cross_encoder.predict(sentence_pairs)

            # Gắn điểm số mới vào các node và tìm node tốt nhất
            best_node = None
            highest_score = -1

            print("   --- Reranker Scores ---")
            for i, node in enumerate(nodes):
                rerank_score = scores[i]
                intent_id = node.metadata.get("intent_id", "N/A")
                print(
                    f"   - Candidate: {intent_id:<20} | Score: {rerank_score:.4f}")
                if rerank_score > highest_score:
                    highest_score = rerank_score
                    best_node = node
            print("   -----------------------")

            if best_node:
                return {
                    "intentId": best_node.metadata.get("intent_id"),
                    # Chuyển numpy.float32 thành float
                    "confidence": float(highest_score),
                    "method": "rerank"
                }
        except Exception as e:
            print(f"❌ Lỗi trong quá trình Reranking: {e}")

        return None

    def _detect_intent_vector(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Phát hiện intent bằng Vector Search (Retriever).
        Nếu Reranker được bật, nó sẽ được gọi để tinh chỉnh kết quả.
        """
        try:
            response = self.query_engine.query(query)

            if not response.source_nodes:
                print("   ⚠️ Không tìm thấy kết quả vector search")
                return None

            # Nếu reranker được bật, sử dụng nó
            if self.reranker_enabled:
                print("   🔍 Vector search đã tìm thấy ứng viên, chuyển sang Reranker...")
                return self._rerank_with_cross_encoder(query, response.source_nodes)

            # Logic cũ nếu không có reranker
            best_node = response.source_nodes[0]
            intent_id = best_node.metadata.get("intent_id")
            similarity_score = best_node.score if hasattr(
                best_node, 'score') else 0.0  # Mặc định là 0

            print(
                f"   🎯 Vector match: {intent_id} (score: {similarity_score:.3f})")

            # Lấy ngưỡng động cho intent cụ thể
            dynamic_threshold = self.vector_thresholds.get(intent_id, 0.6)

            # Chỉ chấp nhận kết quả vector search nếu điểm tin cậy đủ cao
            if intent_id and similarity_score >= dynamic_threshold:
                return {
                    "intentId": intent_id,
                    "confidence": min(similarity_score, 1.0)
                }

            print(
                f"   ⚠️ Điểm vector search ({similarity_score:.3f}) thấp hơn ngưỡng động ({dynamic_threshold}), bỏ qua kết quả.")

        except Exception as e:
            print(f"❌ Lỗi khi thực hiện vector search: {e}")

        return None

    def _create_fallback_intent(self, confidence: float) -> Dict[str, Any]:
        """Tạo intent mặc định khi không có match nào"""
        return {
            "id": "general_info",
            "confidence": confidence,
            "method": "fallback"
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Lấy thống kê performance"""
        total_calls = self.performance_stats["rule_calls"] + \
            self.performance_stats["vector_calls"]

        return {
            "total_calls": total_calls,
            "rule_calls": self.performance_stats["rule_calls"],
            "vector_calls": self.performance_stats["vector_calls"],
            "cache_hits": self.performance_stats["cache_hits"],
            "cache_hit_rate": self.performance_stats["cache_hits"] / max(total_calls, 1) * 100,
            # ms
            "avg_response_time": self.performance_stats["total_time"] / max(total_calls, 1) * 1000,
            "cache_size": len(self.query_cache)
        }

    def reset_performance_stats(self):
        """Reset thống kê performance"""
        self.performance_stats = {
            "rule_calls": 0,
            "vector_calls": 0,
            "cache_hits": 0,
            "total_time": 0
        }

    def clear_cache(self):
        """Xóa cache"""
        self.query_cache.clear()
