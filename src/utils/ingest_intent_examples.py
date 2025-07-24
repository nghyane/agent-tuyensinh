#!/usr/bin/env python3
"""
Script to ingest intent examples from a JSON file into the vector store.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from infrastructure.embeddings import get_embedding_service
from infrastructure.vector_stores.qdrant_store import QdrantVectorStore
from shared.utils.text_processing import VietnameseTextProcessor


class IntentIngestor:
    """Ingests intent examples into a vector store."""

    def __init__(self, vector_store: QdrantVectorStore, embedding_service: Any):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.text_processor = VietnameseTextProcessor()

    async def ingest_from_file(self, file_path: Path):
        """
        Reads intent examples from a JSON file and ingests them.

        Args:
            file_path: Path to the JSON file containing intent examples.
        """
        if not file_path.exists():
            print(f"❌ Error: Intent examples file not found at '{file_path}'")
            return

        print(f"📄 Reading intent examples from '{file_path}'...")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        intents = data.get("intents", [])
        if not intents:
            print("⚠️ No intents found in the file.")
            return

        print(f"Found {len(intents)} intents. Processing examples...")
        
        all_texts = []
        all_vectors = []
        all_metadata = []

        for intent in intents:
            intent_id = intent.get("id")
            examples = intent.get("examples", [])
            
            if not intent_id or not examples:
                continue

            print(f"  - Processing intent: '{intent_id}' with {len(examples)} examples.")
            
            # Generate embeddings for all examples of an intent
            embeddings = [self.embedding_service.get_embedding(ex) for ex in examples]

            for i, example in enumerate(examples):
                # Simple text normalization
                normalized_text = self.text_processor.normalize_vietnamese(example)
                
                all_texts.append(example)
                all_vectors.append(embeddings[i])
                all_metadata.append({
                    "intent_id": intent_id,
                    "normalized_text": normalized_text,
                    "source": "intent-examples.json",
                })

        if all_texts:
            print(f"\n✨ Ingesting {len(all_texts)} points into the vector store...")
            await self.vector_store.add_documents(
                texts=all_texts, 
                vectors=all_vectors, 
                metadata=all_metadata
            )
            print("✅ Ingestion complete!")
        else:
            print("No points to ingest.")


async def main():
    """Main function to run the ingestion script."""
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    print("🚀 Starting Intent Example Ingestion...")
    print(f"Connecting to Qdrant at: {qdrant_url}")

    # Initialize services
    vector_store = QdrantVectorStore(url=qdrant_url, api_key=qdrant_api_key)
    embedding_service = get_embedding_service()

    # Create and run the ingestor
    ingestor = IntentIngestor(vector_store, embedding_service)
    file_path = current_dir.parent / "data" / "intent-examples.json"
    
    await ingestor.ingest_from_file(file_path)

    print("🏁 Ingestion process finished.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main()) 