"""
Vector Indexing Service
Handles indexing of intent examples into vector store
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from infrastructure.vector_stores.qdrant_store import QdrantVectorStore
from infrastructure.embeddings.openai_embeddings import OpenAIEmbeddingService
from shared.utils.text_processing import VietnameseTextProcessor
from shared.utils.metrics import MetricsCollectorImpl


class VectorIndexingService:
    """
    Service for indexing intent examples into vector store
    """
    
    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embedding_service: OpenAIEmbeddingService,
        text_processor: Optional[VietnameseTextProcessor] = None,
        metrics_collector: Optional[MetricsCollectorImpl] = None
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.text_processor = text_processor or VietnameseTextProcessor()
        self.metrics_collector = metrics_collector
        
        print("🔧 Vector indexing service initialized")
    
    async def index_intent_examples(self, examples_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Index intent examples from JSON file into vector store
        
        Args:
            examples_file_path: Path to intent examples JSON file
            
        Returns:
            Indexing results and statistics
        """
        if examples_file_path is None:
            # Default to intent examples file
            current_dir = Path(__file__).parent.parent.parent.parent
            examples_file_path = current_dir / "data" / "intent-examples.json"
        
        examples_file = Path(examples_file_path)
        
        if not examples_file.exists():
            raise FileNotFoundError(f"Intent examples file not found: {examples_file}")
        
        print(f"📁 Loading intent examples from: {examples_file}")
        
        # Load intent examples
        with open(examples_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "intents" not in data:
            raise ValueError("Invalid intent examples format: missing 'intents' key")
        
        # Prepare texts and metadata for indexing
        texts = []
        metadata_list = []
        
        for intent in data["intents"]:
            intent_id = intent["id"]
            intent_name = intent.get("name", intent_id)
            
            # Add examples for this intent
            examples = intent.get("examples", [])
            for example in examples:
                if isinstance(example, str):
                    text = example
                    example_metadata = {}
                elif isinstance(example, dict):
                    text = example.get("text", "")
                    example_metadata = {k: v for k, v in example.items() if k != "text"}
                else:
                    continue
                
                if not text.strip():
                    continue
                
                # Normalize text
                normalized_text = self.text_processor.normalize_vietnamese(text)
                
                texts.append(normalized_text)
                metadata_list.append({
                    "intent_id": intent_id,
                    "intent_name": intent_name,
                    "original_text": text,
                    "language": self.text_processor.detect_language(text),
                    **example_metadata
                })
        
        print(f"📊 Prepared {len(texts)} examples for indexing")
        
        if not texts:
            return {
                "success": False,
                "error": "No valid examples found for indexing",
                "total_examples": 0
            }
        
        # Generate embeddings
        print("🔄 Generating embeddings...")
        embeddings = await self.embedding_service.embed_batch(texts)
        
        # Filter out failed embeddings
        valid_data = []
        for text, embedding, metadata in zip(texts, embeddings, metadata_list):
            if embedding is not None:
                valid_data.append((text, embedding, metadata))
        
        if not valid_data:
            return {
                "success": False,
                "error": "Failed to generate embeddings for any examples",
                "total_examples": len(texts),
                "failed_embeddings": len(texts)
            }
        
        # Separate valid data
        valid_texts, valid_embeddings, valid_metadata = zip(*valid_data)
        
        print(f"✅ Generated {len(valid_embeddings)} embeddings")
        
        # Index into vector store
        print("🔄 Indexing into vector store...")
        await self.vector_store.add_documents(
            texts=list(valid_texts),
            vectors=list(valid_embeddings),
            metadata=list(valid_metadata)
        )
        
        # Record metrics
        if self.metrics_collector:
            self.metrics_collector.increment_counter(
                "documents_indexed",
                value=len(valid_data)
            )
            self.metrics_collector.increment_counter(
                "indexing_operations"
            )
        
        # Get collection info
        collection_info = await self.vector_store.get_collection_info()
        
        result = {
            "success": True,
            "total_examples": len(texts),
            "indexed_examples": len(valid_data),
            "failed_embeddings": len(texts) - len(valid_data),
            "collection_info": collection_info
        }
        
        print(f"✅ Indexing completed: {result}")
        return result
    
    async def index_custom_examples(
        self, 
        examples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index custom examples into vector store
        
        Args:
            examples: List of examples with 'text', 'intent_id', and optional metadata
            
        Returns:
            Indexing results
        """
        if not examples:
            return {
                "success": False,
                "error": "No examples provided",
                "total_examples": 0
            }
        
        texts = []
        metadata_list = []
        
        for example in examples:
            if not isinstance(example, dict) or "text" not in example or "intent_id" not in example:
                continue
            
            text = example["text"].strip()
            if not text:
                continue
            
            # Normalize text
            normalized_text = self.text_processor.normalize_vietnamese(text)
            
            texts.append(normalized_text)
            metadata_list.append({
                "intent_id": example["intent_id"],
                "original_text": text,
                "language": self.text_processor.detect_language(text),
                **{k: v for k, v in example.items() if k not in ["text", "intent_id"]}
            })
        
        if not texts:
            return {
                "success": False,
                "error": "No valid examples found",
                "total_examples": len(examples)
            }
        
        # Generate embeddings
        embeddings = await self.embedding_service.embed_batch(texts)
        
        # Filter valid data
        valid_data = [
            (text, embedding, metadata)
            for text, embedding, metadata in zip(texts, embeddings, metadata_list)
            if embedding is not None
        ]
        
        if not valid_data:
            return {
                "success": False,
                "error": "Failed to generate embeddings",
                "total_examples": len(texts)
            }
        
        # Index into vector store
        valid_texts, valid_embeddings, valid_metadata = zip(*valid_data)
        
        await self.vector_store.add_documents(
            texts=list(valid_texts),
            vectors=list(valid_embeddings),
            metadata=list(valid_metadata)
        )
        
        return {
            "success": True,
            "total_examples": len(examples),
            "indexed_examples": len(valid_data),
            "failed_embeddings": len(texts) - len(valid_data)
        }
    
    async def get_indexing_stats(self) -> Dict[str, Any]:
        """Get indexing statistics"""
        stats = {}
        
        # Vector store info
        if self.vector_store:
            collection_info = await self.vector_store.get_collection_info()
            stats["vector_store"] = collection_info
        
        # Embedding service info
        if self.embedding_service:
            model_info = self.embedding_service.get_model_info()
            stats["embedding_service"] = model_info
        
        # Metrics
        if self.metrics_collector:
            metrics = self.metrics_collector.get_all_metrics()
            stats["metrics"] = metrics
        
        return stats
