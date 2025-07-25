"""
Service factory for FPT University Agent
"""

import os
from typing import Optional

from api.agents.fpt_agent import get_fpt_agent
from core.application.services.hybrid_intent_service import (
    HybridConfig,
    HybridIntentDetectionService,
)
from infrastructure.caching.memory_cache import MemoryCacheService
from infrastructure.embeddings import get_embedding_service
from infrastructure.intent_detection.rule_based import RuleBasedDetectorImpl
from infrastructure.intent_detection.rule_loader import ProductionRuleLoader
from infrastructure.vector_stores.qdrant_store import QdrantVectorStore
from shared.utils.text_processing import VietnameseTextProcessor
from agno.agent import Agent
from agno.storage.postgres import PostgresStorage
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.postgres import PostgresMemoryDb


class ServiceFactory:
    """Factory for creating and managing services"""

    def __init__(self):
        self.text_processor = None
        self.cache_service = None
        self.intent_service = None
        self.storage_service = None
        self.memory_service = None
        self._model_id: str = "gpt-4o"
        self._debug_mode: bool = False

    async def initialize_services(
        self, model_id: str = "gpt-4o", debug_mode: bool = False
    ):
        """Initialize all services"""
        print("🔧 Initializing FPT University Agent services...")

        try:
            # Store config for agent creation
            self._model_id = model_id
            self._debug_mode = debug_mode

            # Initialize core services
            self.text_processor = VietnameseTextProcessor()
            self.cache_service = MemoryCacheService(max_size=100, default_ttl=600)

            # --- Initialize Storage and Memory once ---
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is required")

            self.storage_service = PostgresStorage(
                table_name="fpt_agent_sessions", db_url=db_url
            )
            self.memory_service = Memory(
                db=PostgresMemoryDb(table_name="fpt_user_memories", db_url=db_url),
                delete_memories=True,
                clear_memories=True,
            )
            print("   ✅ Storage and Memory services initialized")
            # -----------------------------------------

            # Load production rules
            loader = ProductionRuleLoader()
            rules = loader.load_rules()
            print(f"   ✅ Loaded {len(rules)} production rules")

            rule_detector = RuleBasedDetectorImpl(
                rules=rules, text_processor=self.text_processor
            )

            # Initialize vector store and embeddings
            vector_store = QdrantVectorStore(
                url=os.getenv("QDRANT_URL", "http://localhost:6333"),
                api_key=os.getenv("QDRANT_API_KEY"),
            )

            # Sử dụng global embedding service
            embedding_service = get_embedding_service()

            # Create hybrid intent service
            hybrid_config = HybridConfig(
                rule_high_confidence_threshold=0.7,
                rule_medium_confidence_threshold=0.3,
                early_exit_threshold=0.8,
                vector_top_k=3,
            )

            self.intent_service = HybridIntentDetectionService(
                rule_detector=rule_detector,
                vector_store=vector_store,
                embedding_service=embedding_service,
                cache_service=self.cache_service,
                text_processor=self.text_processor,
                config=hybrid_config,
            )

            print("✅ All services initialized successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize services: {e}")
            return False

    def get_text_processor(self) -> Optional[VietnameseTextProcessor]:
        """Get text processor"""
        return self.text_processor

    def get_cache_service(self) -> Optional[MemoryCacheService]:
        """Get cache service"""
        return self.cache_service

    def get_intent_service(self) -> Optional[HybridIntentDetectionService]:
        """Get intent detection service"""
        return self.intent_service

    def get_fpt_agent(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> Agent:
        """Creates and returns a new FPT agent instance for each request."""
        if not self.intent_service:
            raise ValueError("Intent service is not initialized.")

        return get_fpt_agent(
            model_id=self._model_id,
            user_id=user_id,
            session_id=session_id,
            intent_service=self.intent_service,
            storage=self.storage_service,
            memory=self.memory_service,
            debug_mode=self._debug_mode,
        )
