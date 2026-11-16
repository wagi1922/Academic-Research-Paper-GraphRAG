#!/usr/bin/env python3
"""Embedding Service for GraphRAG.
Generates embeddings using OpenRouter API (nomic-embed-text).
"""
import asyncio
import logging
from typing import Optional
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates text embeddings via OpenRouter API."""

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
    ):
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.model = model or settings.embedding_model

        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
            logger.warning("No API key provided for EmbeddingService")

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not self.client:
            raise ValueError("EmbeddingService not configured: missing API key")

        # Truncate to model max tokens (nomic-embed-text: 8192 tokens ~ 32k chars)
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars]

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str], batch_size: int = 10) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches."""
        if not self.client:
            raise ValueError("EmbeddingService not configured: missing API key")

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Truncate each text
            max_chars = 30000
            batch = [t[:max_chars] if len(t) > max_chars else t for t in batch]

            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
            )
            batch_embeddings = [d.embedding for d in response.data]
            embeddings.extend(batch_embeddings)
            logger.debug(f"Embedded batch {i//batch_size + 1}: {len(batch)} texts")

        return embeddings


async def get_embedding_service() -> Optional[EmbeddingService]:
    """Factory function to get embedding service if configured."""
    if settings.openrouter_api_key:
        return EmbeddingService()
    return None