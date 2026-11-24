"""
Query Endpoint
Handles natural language queries GraphRAG retrieval and synthesis.
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
from app.ingestion.embedding_service import get_embedding_service
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
    If retrieval_only=True, skip LLM synthesis and return retrieval results only.
    """
    import time
    start_time = time.perf_counter()
    try:
        async for session in get_neo4j_session():
            vector_search = VectorSearch(session)
            graph_traversal = GraphTraversal(session)
            context_builder = ContextBuilder(
                max_vector_chunks=request.top_k,
                max_graph_paths=request.depth,
            )

            # Step 1: Generate query embedding
            query_embedding = await _get_query_embedding(request.query)

            # Step 2: Vector search for seed papers
            vector_results = await vector_search.search_papers(
                query_embedding,
                top_k=request.top_k,
                min_score=0.3,
            )

            if not vector_results:
                return QueryResponseExtended(
                    answer="Tidak ditemukan paper yang relevan dengan pertanyaan Anda.",
                    sources=[],
                    graph_path=[],
                    extracted_entities={},
                    retrieval_metadata={
                        "vector_results": 0,
                        "chunk_results": 0,
                        "graph_paths": 0,
                        "seed_papers": [],
                        "grounding_score": 0,
                        "valid_citations": 0,
                        "total_citations": 0,
                        "latency_ms": (time.perf_counter() - start_time) * 1000,
                    },
                )

            seed_paper_ids = [r["paper_id"] for r in vector_results]

            # Step 3: Graph traversal from seed papers
            graph_result = await graph_traversal.traverse_from_papers(
                seed_paper_ids,
                depth=request.depth,
                max_nodes_per_hop=50,
            )

            # Step 4: Vector search for chunks within seed papers
            chunk_results = await vector_search.search_chunks(
                query_embedding,
                top_k=request.top_k * 2,
                paper_ids=seed_paper_ids,
            )

            # Step 5: Build context
            context = RetrievalContext(
                vector_chunks=chunk_results,
                graph_paths=graph_result.get("paths", []),
                extracted_entities=None,
                seed_papers=vector_results,
            )
            context_dict = context_builder.build(context)

            # Step 6: If retrieval_only, skip LLM synthesis and return retrieval results
            if request.retrieval_only:
                # Format sources from vector_results
                sources = [
                    {
                        "paper_id": r["paper_id"],
                        "title": r.get("title", ""),
                        "year": r.get("year"),
                        "authors": r.get("authors", []),
                        "relevance_score": r.get("score", 0),
                        "citation_text": None,
                    }
                    for r in vector_results
                ]
                # Format graph paths
                graph_paths = [
                    {
                        "source": p.get("source", ""),
                        "relation": p.get("relation", ""),
                        "target": p.get("target", ""),
                        "source_type": p.get("source_type", ""),
                        "target_type": p.get("target_type", ""),
                    }
                    for p in graph_result.get("paths", [])
                ]

                return QueryResponseExtended(
                    answer=f"Retrieval-only mode. Found {len(vector_results)} seed papers, {len(chunk_results)} chunks, {len(graph_result.get('paths', []))} graph paths.",
                    sources=sources,
                    graph_path=graph_paths,
                    extracted_entities={},
                    retrieval_metadata={
                        "vector_results": len(vector_results),
                        "chunk_results": len(chunk_results),
                        "graph_paths": len(graph_result.get("paths", [])),
                        "seed_papers": seed_paper_ids,
                        "grounding_score": 0,
                        "valid_citations": 0,
                        "total_citations": 0,
                        "latency_ms": (time.perf_counter() - start_time) * 1000,
                    },
                )

            # Step 6 (normal): Synthesize answer with LLM
            synthesizer = AnswerSynthesizer(
                api_key=settings.openrouter_api_key,
                model=settings.llm_model,
            )
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
                    "latency_ms": (time.perf_counter() - start_time) * 1000,
                },
            )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions(
    partial: str = Query("", description="Partial query text for filtering"),
    limit: int = Query(6, ge=1, le=20),
):
    """Query suggestions derived from indexed concepts and paper titles."""
    suggestions: list[str] = [
        "Apa metode terbaik untuk deteksi deepfake audio?",
        "Dataset apa saja digunakan untuk evaluasi?",
        "Bagaimana performa model LSTM-Attention untuk prediksi inflasi?",
        "Konsep apa yang berkaitan dengan retrieval augmented generation?",
        "Paper mana yang mengutip ECAPA-TDNN?",
    ]
    try:
        async for session in get_neo4j_session():
            res = await session.run("MATCH (c:Concept) RETURN c.name AS name ORDER BY name LIMIT 15")
            concepts = [r["name"] for r in await res.data()]
            suggestions += [f"Apa itu {c}?" for c in concepts[:6]]
            res2 = await session.run("MATCH (p:Paper) RETURN p.title AS title ORDER BY p.year DESC LIMIT 10")
            titles = [r["title"] for r in await res2.data()]
            suggestions += [f"Ringkas: {t[:80]}" for t in titles[:3]]
    except Exception as e:
        logger.debug(f"Suggestions graph lookup skipped: {e}")
    q = partial.strip().lower()
    if q:
        suggestions = [s for s in suggestions if q in s.lower()]
    unique: list[str] = []
    for s in suggestions:
        if s not in unique:
            unique.append(s)
    return {"suggestions": unique[:limit]}


async def _get_query_embedding(query: str) -> list[float]:
    """Generate embedding for query using OpenRouter embedding service."""
    service = await get_embedding_service()
    if not service:
        raise ValueError("Embedding service not configured: missing OpenRouter API key")
    return await service.embed_text(query)


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
            async for session in get_neo4j_session():
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

        except Exception as e:
            logger.error(f"Stream query failed: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")