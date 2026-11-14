"""
Vector Search Module
Neo4j Vector Index similarity search for paper/chunk retrieval.
"""

import logging
from typing import Optional
from neo4j import AsyncSession

logger = logging.getLogger(__name__)


class VectorSearch:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_papers(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[dict]:
        """Search papers by embedding similarity using Neo4j Vector Index."""
        query = """
        CALL db.index.vector.queryNodes('paper_abstract_vector_idx', $top_k, $embedding)
        YIELD node, score
        WHERE score >= $min_score
        RETURN node.id as paper_id, node.title as title, node.abstract as abstract,
               node.year as year, node.doi as doi, node.venue as venue,
               node.keywords as keywords, score
        ORDER BY score DESC
        """
        result = await self.session.run(
            query,
            top_k=top_k,
            embedding=query_embedding,
            min_score=min_score,
        )
        return [dict(record) for record in result]

    async def search_chunks(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        min_score: float = 0.0,
        paper_ids: list[str] = None,
    ) -> list[dict]:
        """Search chunks by embedding similarity."""
        base_query = """
        CALL db.index.vector.queryNodes('chunk_vector_idx', $top_k, $embedding)
        YIELD node, score
        WHERE score >= $min_score
        """

        if paper_ids:
            base_query += " AND node.paper_id IN $paper_ids "

        base_query += """
        RETURN node.id as chunk_id, node.paper_id as paper_id, node.text as text,
               node.chunk_index as chunk_index, node.metadata as metadata, score
        ORDER BY score DESC
        """

        params = {"top_k": top_k, "embedding": query_embedding, "min_score": min_score}
        if paper_ids:
            params["paper_ids"] = paper_ids

        result = await self.session.run(base_query, params)
        return [dict(record) for record in result]

    async def hybrid_search_papers(
        self,
        query_embedding: list[float],
        keywords: list[str],
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict]:
        """
        Hybrid search combining vector similarity and keyword matching.
        Uses Cypher to combine scores.
        """
        # This is a simplified hybrid - production would use more sophisticated fusion
        vector_results = await self.search_papers(query_embedding, top_k * 2)

        # Boost score for keyword matches
        for r in vector_results:
            keyword_boost = 0.0
            text = f"{r.get('title', '')} {r.get('abstract', '')} {' '.join(r.get('keywords', []))}".lower()
            for kw in keywords:
                if kw.lower() in text:
                    keyword_boost += 0.1
            r["hybrid_score"] = r["score"] * vector_weight + keyword_boost * keyword_weight

        # Re-sort by hybrid score
        vector_results.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
        return vector_results[:top_k]


async def get_paper_by_id(session: AsyncSession, paper_id: str) -> Optional[dict]:
    query = "MATCH (p:Paper {id: $id}) RETURN p"
    result = await session.run(query, id=paper_id)
    record = await result.single()
    return dict(record["p"]) if record else None


async def get_papers_by_ids(session: AsyncSession, paper_ids: list[str]) -> list[dict]:
    if not paper_ids:
        return []
    query = "MATCH (p:Paper) WHERE p.id IN $ids RETURN p"
    result = await session.run(query, ids=paper_ids)
    return [dict(record["p"]) for record in result]