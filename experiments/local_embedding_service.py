#!/usr/bin/env python3
"""Local Embedding Service using guard-embedding.service (port 8788)."""
import logging
import requests
from typing import List

logger = logging.getLogger(__name__)

class LocalEmbeddingService:
    """Generates embeddings using local guard-embedding.service."""

    def __init__(self, base_url: str = "http://localhost:8788"):
        self.base_url = base_url.rstrip("/")
        # Verify service is available
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            resp.raise_for_status()
            logger.info(f"Local Embedding Service connected: {resp.json()}")
        except Exception as e:
            logger.warning(f"Could not connect to local embedding service: {e}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                resp = requests.post(
                    f"{self.base_url}/embed",
                    json={"texts": batch},
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                embeddings.extend(data["embeddings"])
            except Exception as e:
                logger.error(f"Embedding batch failed: {e}")
                raise
        return embeddings

    def get_dimension(self) -> int:
        """Get embedding dimension (all-MiniLM-L6-v2 = 384)."""
        return 384


def get_embedding_service(model_key: str = "local") -> LocalEmbeddingService:
    """Factory function to get local embedding service."""
    return LocalEmbeddingService()