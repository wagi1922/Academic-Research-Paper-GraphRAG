"""
Query Endpoint
Handles natural language queries with GraphRAG retrieval and synthesis.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.schemas.entities import QueryRequest, QueryResponse
from app.retrieval.vector_search import VectorSearch
from app.retrieval.graph_traversal import GraphTraversal
from app.retrieval.context_builder import ContextBuilder, RetrievalContext, build_prompt
from app.retrieval.synthesizer import AnswerSynthesizer, validate_answer_grounding
from app.core.neo4j_driver import get_neo4j_session
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


class QueryResponseExtended(QueryResponse):
    """Extended response with retrieval metadata."""
    retrieval_metadata: dict = {}


@router.post("/", response_model=QueryResponseExtended)
async def query_graphrag(request: QueryRequest):
    """
    Main GraphRAG query endpoint.
    Pipeline: vector search -> graph traversal -> context building -> LLM synthesis -> validation.
    """
    try:
        async with get_neo4j_session() as session:
            # Initialize components
            vector_search = VectorSearch(session)
            graph_traversal = GraphTraversal(session)
            context_builder = ContextBuilder(
                max_vector_chunks=request.top_k,
                max_graph_paths=request.depth,
            )
            synthesizer = AnswerSynthesizer(
                api_key=settings.openrouter_api_key,
                model=settings.llm_model,
            )

            # Step 1: Generate query embedding (placeholder - needs embedding model)
            # In production, call embedding API here
            query_embedding = await _get_query_embedding(request.query)

            # Step 2: Vector search for seed papers
            vector_results = await vector_search.search_papers(
                query_embedding=query_embedding,
                top_k=request.top_k,
                min_score=0.3,
            )

            if not vector_results:
                return QueryResponseExtended(
                    answer="Tidak ditemukan paper yang relevan untuk pertanyaan Anda.",
                    sources=[],
                    graph_path=[],
                    extracted_entities={},
                    retrieval_metadata={"vector_results": 0, "graph_paths": 0},
                )

            # Extract seed paper IDs
            seed_paper_ids = [r["paper_id"] for r in vector_results]

            # Step 3: Graph traversal from seed papers
            graph_result = await graph_traversal.traverse_from_papers(
                seed_paper_ids=seed_paper_ids,
                depth=request.depth,
                max_nodes_per_hop=50,
            )

            # Step 4: Also search chunks for more granular context
            chunk_results = await vector_search.search_chunks(
                query_embedding=query_embedding,
                top_k=request.top_k * 2,
                paper_ids=seed_paper_ids,
            )

            # Step 5: Build context
            context = RetrievalContext(
                vector_chunks=chunk_results,
                graph_paths=graph_result.get("paths", []),
                extracted_entities=None,  # Could extract from seed papers
                seed_papers=vector_results,
            )
            context_dict = context_builder.build(context)

            # Step 6: Synthesize answer
            response = await synthesizer.synthesize(
                query=request.query,
                context=context_dict,
            )

            # Step 7: Validate grounding
            grounding = await validate_answer_grounding(
                answer=response.answer,
                context=context_dict,
            )

            # Build extended response
            return QueryResponseExtended(
                answer=response.answer,
                sources=response.sources,
                graph_path=response.graph_path,
                extracted_entities=response.extracted_entities,
                retrieval_metadata={
                    "vector_results": len(vector_results),
                    "chunk_results": len(chunk_results),
                    "graph_paths": len(graph_result.get("paths", [])),
                    "seed_papers": seed_paper_ids,
                    "grounding_score": grounding.get("grounding_score", 0),
                    "valid_citations": grounding.get("valid_citations", 0),
                    "total_citations": grounding.get("total_citations", 0),
                },
            )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions(
    partial: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
):
    """Get query suggestions based on indexed papers."""
    # This would query paper titles, concepts, methods for autocomplete
    # Simplified placeholder
    suggestions = [
        "Apa metode yang digunakan dalam paper tentang...",
        "Bagaimana performa model X pada dataset Y?",
        "Paper mana yang mengutip paper Z?",
        "Konsep apa yang berkaitan dengan...",
        "Dataset apa yang digunakan untuk task...",
    ]
    return {"suggestions": [s for s in suggestions if partial.lower() in s.lower()][:limit]}


async def _get_query_embedding(query: str) -> list[float]:
    """
    Generate embedding for query.
    Placeholder - replace with actual embedding API call.
    """
    # In production, call OpenRouter embedding API or local model
    # For now, return dummy embedding (768 dims for nomic-embed-text)
    import hashlib
    hash_obj = hashlib.md5(query.encode())
    # Generate pseudo-embedding from hash
    embedding = [(int(hash_obj.hexdigest()[i:i+2], 16) - 128) / 128.0 for i in range(0, 32, 2)]
    # Pad to 768 dims
    embedding = embedding * (768 // len(embedding))
    return embedding[:768]


@router.post("/stream")
async def query_stream(request: QueryRequest):
    """
    Streaming query endpoint (SSE).
    Returns tokens as they are generated.
    """
    from fastapi.responses import StreamingResponse
    from app.retrieval.synthesizer import StreamingSynthesizer

    async def generate():
        try:
            async with get_neo4j_session() as session:
                vector_search = VectorSearch(session)
                graph_traversal = GraphTraversal(session)
                context_builder = ContextBuilder(
                    max_vector_chunks=request.top_k,
                    max_graph_paths=request.depth,
                )

                query_embedding = await _get_query_embedding(request.query)
                vector_results = await vector_search.search_papers(query_embedding, request.top_k)

                if not vector_results:
                    yield "data: Tidak ditemukan paper relevan.\n\n"
                    return

                seed_paper_ids = [r["paper_id"] for r in vector_results]
                graph_result = await graph_traversal.traverse_from_papers(seed_paper_ids, request.depth)
                chunk_results = await vector_search.search_chunks(query_embedding, request.top_k * 2, seed_paper_ids)

                context = RetrievalContext(
                    vector_chunks=chunk_results,
                    graph_paths=graph_result.get("paths", []),
                    extracted_entities=None,
                    seed_papers=vector_results,
                )
                context_dict = context_builder.build(context)

                synthesizer = StreamingSynthesizer(
                    api_key=settings.openrouter_api_key,
                    model=settings.llm_model,
                )

                async for token in synthesizer.stream_synthesize(request.query, context_dict):
                    yield f"data: {token}\n\n"

                yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")