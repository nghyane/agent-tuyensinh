"""
Local embedding provider using sentence-transformers
"""

import time
from typing import List, Optional, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class LocalEmbeddingProvider:
    """
    Local embedding provider using sentence-transformers
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize_embeddings: bool = True
    ):
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.model = None
        self.embedding_dimension = 384  # Default for all-MiniLM-L6-v2
        
        print(f"🧠 Local embedding provider initialized: {model_name}")
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("⚠️ sentence-transformers not available, using dummy embeddings")
        else:
            self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence transformer model"""
        try:
            print(f"📥 Loading model: {self.model_name}...")
            start_time = time.time()
            
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            
            load_time = time.time() - start_time
            print(f"✅ Model loaded in {load_time:.1f}s, dimension: {self.embedding_dimension}")
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.model = None
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        return (await self.embed_texts([text]))[0]
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None:
                # Return dummy embeddings for demo
                return self._generate_dummy_embeddings(texts)
            
            start_time = time.time()
            
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            processing_time = time.time() - start_time
            
            print(f"🧠 Generated {len(texts)} embeddings in {processing_time*1000:.1f}ms")
            
            # Convert to list of lists
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return self._generate_dummy_embeddings(texts)
    
    def _generate_dummy_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate dummy embeddings for demo purposes"""
        import hashlib
        import random
        
        embeddings = []
        
        for text in texts:
            # Use text hash as seed for consistent dummy embeddings
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            
            # Generate dummy embedding
            embedding = [random.uniform(-1, 1) for _ in range(self.embedding_dimension)]
            embeddings.append(embedding)
        
        return embeddings
    
    async def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.embedding_dimension
    
    async def is_available(self) -> bool:
        """Check if the embedding provider is available"""
        return SENTENCE_TRANSFORMERS_AVAILABLE and self.model is not None
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dimension": self.embedding_dimension,
            "normalize_embeddings": self.normalize_embeddings,
            "available": await self.is_available(),
            "library_available": SENTENCE_TRANSFORMERS_AVAILABLE
        }
