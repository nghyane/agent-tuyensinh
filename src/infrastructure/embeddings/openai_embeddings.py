"""
OpenAI embeddings service
"""

import os
import time
from typing import List, Optional
from openai import OpenAI




class OpenAIEmbeddingService:
    """
    OpenAI embedding service for generating text embeddings
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "text-embedding-3-small"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model
        
        if not self.api_key:
            print("⚠️ OpenAI API key not found")
            self.available = False
            return
        
        try:
            # Initialize OpenAI client
            client_kwargs = {"api_key": self.api_key}
            
            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self.client = OpenAI(**client_kwargs)

            # Skip connection test during initialization for better reliability
            # Test will happen on first actual usage
            self.available = True
            print(f"✅ OpenAI embeddings initialized: {self.model}")
            print("ℹ️ Connection will be tested on first usage")

        except Exception as e:
            print(f"❌ OpenAI embeddings initialization failed: {e}")
            self.available = False
    
    def _test_connection(self):
        """Test OpenAI connection with a simple embedding"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input="test"
            )
            if response.data:
                print(f"✅ OpenAI connection test successful")
            else:
                raise Exception("No embedding data returned")
        except Exception as e:
            raise Exception(f"OpenAI connection test failed: {e}")
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for single text"""
        if not self.available:
            return None
        
        try:
            start_time = time.time()
            
            # Some API endpoints require input as list instead of string
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]  # Convert to list for compatibility
            )
            
            if response.data:
                embedding = response.data[0].embedding
                

                
                return embedding
            else:
                print(f"❌ No embedding data returned for text: {text[:50]}...")
                return None
                
        except Exception as e:
            return None
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts in batches"""
        if not self.available:
            return [None] * len(texts)
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self._embed_batch_internal(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def _embed_batch_internal(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Internal method to embed a batch of texts"""
        try:
            start_time = time.time()
            
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            
            embeddings = []
            for data in response.data:
                embeddings.append(data.embedding)
            

            return embeddings
            
        except Exception as e:
            return [None] * len(texts)
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension for the model"""
        model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return model_dimensions.get(self.model, 1536)
    
    def get_model_info(self) -> dict:
        """Get model information"""
        return {
            "model": self.model,
            "dimension": self.get_embedding_dimension(),
            "available": self.available,
            "base_url": self.base_url
        }
