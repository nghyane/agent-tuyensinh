"""
Service factory for FPT University Agent
"""

from core.domain.entities import DetectionContext
from infrastructure.intent_detection.rule_based import RuleBasedDetectorImpl
from infrastructure.intent_detection.rule_loader import ProductionRuleLoader
from infrastructure.caching.memory_cache import MemoryCacheService
from infrastructure.vector_stores.qdrant_store import QdrantVectorStore
from infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingService
from core.application.services.hybrid_intent_service import HybridIntentDetectionService, HybridConfig
from shared.utils.text_processing import VietnameseTextProcessor
from api.agents.fpt_agent import get_fpt_agent


class ServiceFactory:
    """Factory for creating and managing services"""
    
    def __init__(self):
        self.text_processor = None
        self.cache_service = None
        self.intent_service = None
        self.fpt_agent = None
    
    async def initialize_services(self, model_id: str = "gpt-4o", debug_mode: bool = False):
        """Initialize all services"""
        print("🔧 Initializing FPT University Agent services...")
        
        try:
            # Initialize core services
            self.text_processor = VietnameseTextProcessor()
            self.cache_service = MemoryCacheService(max_size=100, default_ttl=600)
            
            # Load production rules
            loader = ProductionRuleLoader()
            rules = loader.load_rules()
            print(f"   ✅ Loaded {len(rules)} production rules")
            
            rule_detector = RuleBasedDetectorImpl(rules=rules, text_processor=self.text_processor)
            
            # Initialize vector store and embeddings
            vector_store = QdrantVectorStore()
            embedding_service = OpenAIEmbeddingService()
            
            # Create hybrid intent service
            hybrid_config = HybridConfig(
                rule_high_confidence_threshold=0.7,
                rule_medium_confidence_threshold=0.3,
                early_exit_threshold=0.8,
                vector_top_k=3
            )
            
            self.intent_service = HybridIntentDetectionService(
                rule_detector=rule_detector,
                vector_store=vector_store,
                embedding_service=embedding_service,
                cache_service=self.cache_service,
                text_processor=self.text_processor,
                config=hybrid_config
            )
            
            # Create FPT agent
            self.fpt_agent = get_fpt_agent(
                model_id=model_id,
                intent_service=self.intent_service,
                debug_mode=debug_mode,
            )
            
            print("✅ All services initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize services: {e}")
            print("⚠️  Server will start with limited functionality")
            return False
    
    def get_agent(self):
        """Get the FPT agent"""
        return self.fpt_agent
    
    def get_intent_service(self):
        """Get the intent service"""
        return self.intent_service 