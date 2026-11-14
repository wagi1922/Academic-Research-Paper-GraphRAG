"""
Test retrieval module components.
"""

import pytest
from app.retrieval.context_builder import ContextBuilder, RetrievalContext, build_prompt, SYSTEM_PROMPT
from app.schemas.entities import ExtractedEntities, SourceCitation


class TestContextBuilder:
    def test_context_builder_init(self):
        """Test ContextBuilder initialization."""
        builder = ContextBuilder(
            max_vector_chunks=5,
            max_graph_paths=3,
            max_chunk_chars=1000,
        )
        assert builder.max_vector_chunks == 5
        assert builder.max_graph_paths == 3
        assert builder.max_chunk_chars == 1000

    def test_build_empty_context(self):
        """Test building context with empty data."""
        builder = ContextBuilder()
        context = RetrievalContext(
            vector_chunks=[],
            graph_paths=[],
            extracted_entities=ExtractedEntities(),
            seed_papers=[],
        )
        result = builder.build(context)

        assert "vector_chunks" in result
        assert "graph_paths" in result
        assert "extracted_entities" in result
        assert "seed_papers" in result
        assert "Tidak ada" in result["vector_chunks"]
        assert "Tidak ada" in result["graph_paths"]

    def test_format_vector_chunks(self):
        """Test vector chunk formatting."""
        builder = ContextBuilder(max_chunk_chars=50)
        chunks = [
            {
                "paper_id": "paper1",
                "text": "This is a very long text that should be truncated because it exceeds the maximum chunk characters limit.",
                "score": 0.85,
                "title": "Test Paper",
            }
        ]
        context = RetrievalContext(
            vector_chunks=chunks,
            graph_paths=[],
            extracted_entities=ExtractedEntities(),
            seed_papers=[],
        )
        result = builder.build(context)
        formatted = result["vector_chunks"]

        assert "Test Paper" in formatted
        assert "paper1" in formatted
        assert "0.850" in formatted
        # Should be truncated
        assert len(formatted) < 200

    def test_format_graph_paths(self):
        """Test graph path formatting."""
        builder = ContextBuilder()
        paths = [
            {
                "type": "citation_chain",
                "nodes": [
                    {"id": "n1", "name": "Paper A", "labels": ["Paper"]},
                    {"id": "n2", "name": "Paper B", "labels": ["Paper"]},
                ],
                "relationships": [
                    {"source": "n1", "target": "n2", "type": "CITES"},
                ],
            }
        ]
        context = RetrievalContext(
            vector_chunks=[],
            graph_paths=paths,
            extracted_entities=ExtractedEntities(),
            seed_papers=[],
        )
        result = builder.build(context)
        formatted = result["graph_paths"]

        assert "citation_chain" in formatted
        assert "Paper A" in formatted
        assert "Paper B" in formatted
        assert "CITES" in formatted

    def test_format_entities(self):
        """Test entity formatting."""
        builder = ContextBuilder()
        entities = ExtractedEntities(
            authors=[
                {"name": "John Doe", "institution": "Univ A"},
                {"name": "Jane Smith", "institution": None},
            ],
            concepts=[
                {"name": "Transformer", "category": "architecture"},
                {"name": "Attention", "category": "mechanism"},
            ],
            methods=[
                {"name": "Self-Attention", "description": "Attention mechanism"},
            ],
            datasets=[
                {"name": "WMT14", "domain": "translation"},
            ],
            relations=[
                {"source_type": "Paper", "source_name": "Paper A", "relation": "USES_METHOD", "target_type": "Method", "target_name": "Self-Attention"},
            ],
        )
        context = RetrievalContext(
            vector_chunks=[],
            graph_paths=[],
            extracted_entities=entities,
            seed_papers=[],
        )
        result = builder.build(context)
        formatted = result["extracted_entities"]

        assert "John Doe (Univ A)" in formatted
        assert "Jane Smith" in formatted
        assert "Transformer [architecture]" in formatted
        assert "Self-Attention" in formatted
        assert "WMT14 (translation)" in formatted
        assert "USES_METHOD" in formatted

    def test_build_prompt(self):
        """Test prompt building."""
        context_dict = {
            "vector_chunks": "Test chunk content",
            "graph_paths": "Test path content",
            "extracted_entities": "Test entities",
            "seed_papers": "Test papers",
        }
        prompt = build_prompt(context_dict, "Apa itu Transformer?")

        assert "Apa itu Transformer?" in prompt
        assert "Test chunk content" in prompt
        assert "Test path content" in prompt
        assert "Test entities" in prompt
        assert "Test papers" in prompt
        assert SYSTEM_PROMPT in prompt


class TestRetrievalContext:
    def test_retrieval_context_dataclass(self):
        """Test RetrievalContext dataclass creation."""
        context = RetrievalContext(
            vector_chunks=[{"text": "test"}],
            graph_paths=[{"type": "test"}],
            extracted_entities=ExtractedEntities(),
            seed_papers=[{"id": "1"}],
        )
        assert len(context.vector_chunks) == 1
        assert len(context.graph_paths) == 1
        assert context.extracted_entities is not None
        assert len(context.seed_papers) == 1