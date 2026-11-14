"""
LLM Synthesis Module
Generates grounded answers with citation validation.
"""

import logging
import json
from typing import Optional
from openai import AsyncOpenAI
import instructor

from app.schemas.entities import (
    QueryResponse,
    SourceCitation,
    GraphPathElement,
    ExtractedEntities,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnswerSynthesizer:
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
    ):
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.model = model or settings.llm_model

        if self.api_key:
            self.client = instructor.from_openai(
                AsyncOpenAI(api_key=self.api_key, base_url=self.base_url),
                mode=instructor.Mode.JSON,
            )
        else:
            self.client = None
            logger.warning("No API key provided for AnswerSynthesizer")

    async def synthesize(
        self,
        query: str,
        context: dict,
        extracted_entities: ExtractedEntities = None,
        stream: bool = False,
    ) -> QueryResponse:
        """Generate answer with citations and grounding."""
        if not self.client:
            return QueryResponse(
                answer="Error: LLM client not configured. Please set OPENROUTER_API_KEY.",
                sources=[],
                graph_path=[],
                extracted_entities={},
                metadata={"error": "no_llm_client"},
            )

        from app.retrieval.context_builder import build_prompt
        prompt = build_prompt(context, query)

        try:
            # Use structured output for citations
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant. Answer based on context with citations."},
                    {"role": "user", "content": prompt},
                ],
                response_model=QueryResponse,
                temperature=0.1,
                max_tokens=2000,
            )

            # Validate citations against sources
            response = self._validate_citations(response, context)

            return response

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return QueryResponse(
                answer=f"Maaf, terjadi kesalahan saat menghasilkan jawaban: {str(e)}",
                sources=[],
                graph_path=[],
                extracted_entities={},
                metadata={"error": str(e)},
            )

    def _validate_citations(self, response: QueryResponse, context: dict) -> QueryResponse:
        """Validate that cited sources exist in retrieved context."""
        # Extract paper IDs from vector chunks and graph paths
        valid_paper_ids = set()

        # From vector chunks
        for chunk in context.get("vector_chunks", "").split("\n\n---\n\n"):
            if "Paper:" in chunk:
                # Parse paper ID from format: [Chunk X | Paper: Title (paper_id) | Score: ...]
                import re
                match = re.search(r'\(([^)]+)\)', chunk)
                if match:
                    valid_paper_ids.add(match.group(1))

        # From seed papers
        for line in context.get("seed_papers", "").split("\n"):
            if "(" in line and ")" in line:
                import re
                match = re.search(r'\(([^)]+)\)', line)
                if match:
                    valid_paper_ids.add(match.group(1))

        # From graph paths
        for path in context.get("graph_paths", "").split("\n\n---\n\n"):
            import re
            ids = re.findall(r'\(([^)]+)\)', path)
            valid_paper_ids.update(ids)

        # Filter sources to only valid ones
        validated_sources = []
        for src in response.sources:
            if src.paper_id in valid_paper_ids or not valid_paper_ids:
                validated_sources.append(src)
            else:
                logger.warning(f"Citation validation failed for paper_id: {src.paper_id}")

        response.sources = validated_sources
        return response


class StreamingSynthesizer:
    """Streaming version for SSE responses."""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.model = model or settings.llm_model

        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None

    async def stream_synthesize(
        self,
        query: str,
        context: dict,
    ):
        """Stream answer tokens via async generator."""
        if not self.client:
            yield "Error: LLM client not configured."
            return

        from app.retrieval.context_builder import build_prompt
        prompt = build_prompt(context, query)

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant. Answer based on context with citations."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming synthesis failed: {e}")
            yield f"Error: {str(e)}"


async def validate_answer_grounding(
    answer: str,
    context: dict,
    llm_client=None,
) -> dict:
    """
    Validate that answer claims are grounded in context.
    Returns validation report with unsupported claims.
    """
    # This would use a separate LLM call to check grounding
    # Simplified version: check citation format
    import re
    citations = re.findall(r'\[([A-Za-z0-9_\-]+)\]', answer)

    # Extract valid paper IDs from context
    valid_ids = set()
    for chunk in context.get("vector_chunks", "").split("\n\n---\n\n"):
        match = re.search(r'\(([^)]+)\)', chunk)
        if match:
            valid_ids.add(match.group(1))

    unsupported = [c for c in citations if c not in valid_ids]

    return {
        "total_citations": len(citations),
        "valid_citations": len(citations) - len(unsupported),
        "unsupported_citations": unsupported,
        "grounding_score": (len(citations) - len(unsupported)) / len(citations) if citations else 1.0,
    }