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
        # OpenRouter direct API - use actual API key
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.model = model or settings.llm_model

        if self.api_key:
            self.client = instructor.from_openai(
                AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=120.0),
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
                max_tokens=3000,
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
        # Map numbered citation index -> paper_id
        citation_index_to_id = {}

        # From vector chunks
        for idx, chunk in enumerate(context.get("vector_chunks", "").split("\n\n---\n\n")):
            if "Paper ID:" in chunk:
                import re
                match = re.search(r'Paper ID:\s*([^|]+)', chunk)
                if match:
                    paper_id = match.group(1).strip()
                    valid_paper_ids.add(paper_id)
                    citation_index_to_id[idx + 1] = paper_id  # 1-indexed

        # From seed papers
        for idx, line in enumerate(context.get("seed_papers", "").split("\n")):
            if "[ID:" in line:
                import re
                match = re.search(r'\[ID:\s*([^\]]+)\]', line)
                if match:
                    paper_id = match.group(1).strip()
                    valid_paper_ids.add(paper_id)
                    citation_index_to_id[idx + 1] = paper_id

        # From graph paths
        for path in context.get("graph_paths", "").split("\n\n---\n\n"):
            import re
            ids = re.findall(r'\(([^)]+)\)', path)
            for pid in ids:
                valid_paper_ids.add(pid)

        # Filter sources to only valid ones
        validated_sources = []
        for src in response.sources:
            # Check if paper_id is a numbered citation (e.g., "1", "2", "9")
            if src.paper_id.isdigit():
                idx = int(src.paper_id)
                mapped_id = citation_index_to_id.get(idx)
                if mapped_id:
                    src.paper_id = mapped_id
                    validated_sources.append(src)
                else:
                    logger.warning(f"Citation validation failed for numbered citation: [{src.paper_id}]")
            elif src.paper_id in valid_paper_ids or not valid_paper_ids:
                validated_sources.append(src)
            else:
                logger.warning(f"Citation validation failed for paper_id: {src.paper_id}")

        response.sources = validated_sources
        return response


class StreamingSynthesizer:
    """Streaming version for SSE responses."""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        # OpenRouter direct API - use actual API key
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.model = model or settings.llm_model

        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=120.0)
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
                max_tokens=3000,
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
    # Match both numbered [1] and paper_id [DOI/UUID/title] citations (allow spaces in paper_id)
    citations = re.findall(r'\[([^\]]+)\]', answer)

    # Extract valid paper IDs from context + map numbered citations
    valid_ids = set()
    citation_index_to_id = {}

    for idx, chunk in enumerate(context.get("vector_chunks", "").split("\n\n---\n\n")):
        if "Paper ID:" in chunk:
            match = re.search(r'Paper ID:\s*([^|]+)', chunk)
            if match:
                paper_id = match.group(1).strip()
                valid_ids.add(paper_id)
                citation_index_to_id[idx + 1] = paper_id

    for idx, line in enumerate(context.get("seed_papers", "").split("\n")):
        if "[ID:" in line:
            match = re.search(r'\[ID:\s*([^\]]+)\]', line)
            if match:
                paper_id = match.group(1).strip()
                valid_ids.add(paper_id)
                citation_index_to_id[idx + 1] = paper_id

    for path in context.get("graph_paths", "").split("\n\n---\n\n"):
        ids = re.findall(r'\(([^)]+)\)', path)
        for pid in ids:
            valid_ids.add(pid)

    unsupported = []
    for c in citations:
        c_stripped = c.strip()
        if c_stripped.isdigit():
            idx = int(c_stripped)
            if idx not in citation_index_to_id:
                unsupported.append(c_stripped)
        elif c_stripped not in valid_ids:
            unsupported.append(c_stripped)

    return {
        "total_citations": len(citations),
        "valid_citations": len(citations) - len(unsupported),
        "unsupported_citations": unsupported,
        "grounding_score": (len(citations) - len(unsupported)) / len(citations) if citations else 1.0,
    }