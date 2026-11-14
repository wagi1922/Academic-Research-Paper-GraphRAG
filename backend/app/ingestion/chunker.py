"""
Text Chunking Module
Supports multiple chunking strategies: fixed-size, semantic, and proposition-based.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict
    token_count: Optional[int] = None


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        pass


class FixedSizeChunker(BaseChunker):
    """Fixed-size chunking with overlap."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: list[str] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        if not text.strip():
            return []

        docs = self.splitter.create_documents([text], metadatas=[metadata or {}])
        chunks = []
        for i, doc in enumerate(docs):
            chunks.append(Chunk(
                text=doc.page_content,
                index=i,
                metadata={**(metadata or {}), **doc.metadata},
            ))
        logger.debug(f"FixedSizeChunker: {len(chunks)} chunks from {len(text)} chars")
        return chunks


class SemanticChunkerWrapper(BaseChunker):
    """Semantic chunking using embedding similarity."""

    def __init__(
        self,
        embeddings: Embeddings,
        breakpoint_threshold_type: str = "percentile",
        breakpoint_threshold_amount: float = 95.0,
        min_chunk_size: int = 100,
    ):
        self.splitter = SemanticChunker(
            embeddings=embeddings,
            breakpoint_threshold_type=breakpoint_threshold_type,
            breakpoint_threshold_amount=breakpoint_threshold_amount,
            min_chunk_size=min_chunk_size,
        )

    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        if not text.strip():
            return []

        docs = self.splitter.create_documents([text], metadatas=[metadata or {}])
        chunks = []
        for i, doc in enumerate(docs):
            chunks.append(Chunk(
                text=doc.page_content,
                index=i,
                metadata={**(metadata or {}), **doc.metadata},
            ))
        logger.debug(f"SemanticChunker: {len(chunks)} chunks from {len(text)} chars")
        return chunks


class PropositionChunker(BaseChunker):
    """
    Proposition-based chunking using LLM to extract atomic claims.
    Each chunk = one atomic proposition/claim from the text.
    """

    def __init__(self, llm_client, max_propositions_per_chunk: int = 1):
        self.llm_client = llm_client
        self.max_propositions_per_chunk = max_propositions_per_chunk

    async def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        if not text.strip():
            return []

        # Use LLM to extract atomic propositions
        prompt = f"""Extract atomic propositions/claims from the following text.
Each proposition should be a single, self-contained factual claim.
Return as a JSON list of strings.

Text:
{text[:8000]}  # Limit input size

Propositions (JSON array):"""

        try:
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )
            import json
            propositions = json.loads(response.choices[0].message.content)
            if not isinstance(propositions, list):
                propositions = [str(propositions)]

            chunks = []
            for i, prop in enumerate(propositions):
                chunks.append(Chunk(
                    text=str(prop),
                    index=i,
                    metadata={**(metadata or {}), "chunk_type": "proposition"},
                ))
            logger.debug(f"PropositionChunker: {len(chunks)} propositions from {len(text)} chars")
            return chunks

        except Exception as e:
            logger.warning(f"Proposition chunking failed, falling back to fixed-size: {e}")
            # Fallback to fixed-size
            fallback = FixedSizeChunker(chunk_size=512, chunk_overlap=50)
            return fallback.chunk(text, metadata)


def get_chunker(
    strategy: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    embeddings: Optional[Embeddings] = None,
    llm_client=None,
) -> BaseChunker:
    """Factory function to get chunker by strategy name."""
    strategy = strategy.lower()

    # Check CHUNKING_STRATEGIES dict first for experiment configs
    if strategy in CHUNKING_STRATEGIES:
        return CHUNKING_STRATEGIES[strategy]()

    if strategy in ("fixed", "fixed_size", "recursive"):
        return FixedSizeChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    elif strategy in ("semantic", "semantic_chunker"):
        if embeddings is None:
            raise ValueError("SemanticChunker requires embeddings model")
        return SemanticChunkerWrapper(embeddings=embeddings)

    elif strategy in ("proposition", "proposition_based", "llm"):
        if llm_client is None:
            raise ValueError("PropositionChunker requires LLM client")
        return PropositionChunker(llm_client=llm_client)

    else:
        logger.warning(f"Unknown chunking strategy '{strategy}', defaulting to fixed-size")
        return FixedSizeChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


# Strategy aliases for experiment configs
CHUNKING_STRATEGIES = {
    "fixed_512_50": lambda: FixedSizeChunker(512, 50),
    "fixed_1024_100": lambda: FixedSizeChunker(1024, 100),
    "semantic_bert": lambda emb: SemanticChunkerWrapper(embeddings=emb),
    "proposition_llm": lambda llm: PropositionChunker(llm_client=llm),
}