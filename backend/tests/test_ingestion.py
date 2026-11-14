"""
Test ingestion module components.
"""

import pytest
from app.ingestion.chunker import FixedSizeChunker, Chunk, get_chunker, CHUNKING_STRATEGIES
from app.schemas.entities import ExtractedEntities, AuthorEntity, ConceptEntity


class TestChunker:
    def test_fixed_size_chunker_basic(self):
        """Test basic fixed-size chunking."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a test sentence. " * 10  # ~240 chars
        chunks = chunker.chunk(text, {"source": "test"})

        assert len(chunks) > 1
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.metadata.get("source") == "test" for c in chunks)

    def test_fixed_size_chunker_empty(self):
        """Test chunking empty text."""
        chunker = FixedSizeChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_fixed_size_chunker_whitespace(self):
        """Test chunking whitespace-only text."""
        chunker = FixedSizeChunker()
        chunks = chunker.chunk("   \n\n  ")
        assert chunks == []

    def test_get_chunker_fixed(self):
        """Test chunker factory for fixed strategy."""
        chunker = get_chunker("fixed_512_50")
        assert isinstance(chunker, FixedSizeChunker)
        assert chunker.chunk_size == 512
        assert chunker.chunk_overlap == 50

    def test_get_chunker_fixed_1024(self):
        """Test chunker factory for fixed 1024 strategy."""
        chunker = get_chunker("fixed_1024_100")
        assert isinstance(chunker, FixedSizeChunker)
        assert chunker.chunk_size == 1024
        assert chunker.chunk_overlap == 100

    def test_get_chunker_unknown_defaults_to_fixed(self):
        """Test unknown strategy defaults to fixed."""
        chunker = get_chunker("unknown_strategy")
        assert isinstance(chunker, FixedSizeChunker)

    def test_chunking_strategies_dict(self):
        """Test CHUNKING_STRATEGIES dict has expected keys."""
        assert "fixed_512_50" in CHUNKING_STRATEGIES
        assert "fixed_1024_100" in CHUNKING_STRATEGIES
        assert "semantic_bert" in CHUNKING_STRATEGIES
        assert "proposition_llm" in CHUNKING_STRATEGIES


class TestSchemas:
    def test_extracted_entities_empty(self):
        """Test empty ExtractedEntities."""
        entities = ExtractedEntities()
        assert entities.authors == []
        assert entities.concepts == []
        assert entities.methods == []
        assert entities.datasets == []
        assert entities.relations == []

    def test_extracted_entities_with_data(self):
        """Test ExtractedEntities with sample data."""
        entities = ExtractedEntities(
            authors=[AuthorEntity(name="John Doe", institution="University X")],
            concepts=[ConceptEntity(name="Transformer", category="architecture")],
        )
        assert len(entities.authors) == 1
        assert len(entities.concepts) == 1
        assert entities.authors[0].name == "John Doe"
        assert entities.concepts[0].category == "architecture"