#!/usr/bin/env python3
"""
Embedding Service for GraphRAG — LOCAL MiniLM (all-MiniLM-L6-v2, 384-d).

Backed by the host-side guard-embedding.service (stdlib http.server, OpenAI-compatible
/v1/embeddings endpoint on 127.0.0.1:8788). The backend container uses
network_mode: host, so localhost:8788 reaches the host service.

Why local: OpenRouter has NO free embedding model (nomic-embed-text-v1.5:free etc.
return 400 "does not exist"), and the free-tier daily LLM budget must be reserved
for entity extraction and answer synthesis. MiniLM is deterministic and free.
"""
import logging
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates text embeddings via the local MiniLM service (OpenAI-compatible API)."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.api_key = "local"  # kept for compatibility with OpenAIEmbeddings wrapper
        self.base_url = (base_url or settings.embedding_url).rstrip("/") + "/v1"
        self.model = model or settings.embedding_model
        self._client = httpx.AsyncClient(timeout=120.0)

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = await self._client.post(
                f"{self.base_url}/embeddings",
                json={"input": batch, "model": self.model},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            embeddings.extend(
                [d["embedding"] for d in sorted(data, key=lambda x: x["index"])]
            )
            logger.debug(f"Embedded batch {i//batch_size + 1}: {len(batch)} texts")
        return embeddings


async def get_embedding_service() -> EmbeddingService:
    """Factory function (no API key required for local service)."""
    return EmbeddingService()
