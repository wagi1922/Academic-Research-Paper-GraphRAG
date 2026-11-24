"""
Read-only catalog endpoints for the frontend:
papers list/detail, chunks, citations, entities.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.core.neo4j_driver import get_neo4j_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["catalog"])

PAPER_RETURN = """
    p.id AS id, p.title AS title, p.abstract AS abstract, p.year AS year,
    p.doi AS doi, p.venue AS venue, p.keywords AS keywords,
    [(a:Author)-[:WROTE]->(p) | a.name] AS authors
"""

PAPER_WHERE = """
    ($q IS NULL OR toLower(coalesce(p.title, '')) CONTAINS $ql
     OR any(k IN coalesce(p.keywords, []) WHERE toLower(k) CONTAINS $ql))
    AND ($year IS NULL OR p.year = $year)
"""


def _paper_row(row: dict) -> dict[str, object]:
    return {
        "id": row["id"],
        "title": row["title"],
        "abstract": row["abstract"],
        "year": row["year"],
        "doi": row["doi"],
        "venue": row["venue"],
        "keywords": row["keywords"] or [],
        "authors": row.get("authors") or [],
    }


@router.get("")
@router.get("/")
async def list_papers(
    q: Optional[str] = Query(None, description="Search in title/keywords"),
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List papers with optional search and year filter."""
    ql = (q or "").lower() or None
    try:
        async for session in get_neo4j_session():
            where = PAPER_WHERE
            params = {"q": q, "ql": ql, "year": year, "limit": limit, "offset": offset}

            count_res = await session.run(f"MATCH (p:Paper) WHERE {where} RETURN count(p) AS total", **params)
            total = (await count_res.single())["total"]

            res = await session.run(
                f"MATCH (p:Paper) WHERE {where} "
                f"RETURN {PAPER_RETURN} "
                "ORDER BY p.year DESC, p.title ASC "
                "SKIP $offset LIMIT $limit",
                **params,
            )
            papers = [_paper_row(dict(r)) async for r in res]

            return {"papers": papers, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"List papers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Simple title/keyword search (alias used by frontend)."""
    return await list_papers(q=q, year=None, limit=limit, offset=0)


@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """Paper detail with computed counts and connected entities."""
    try:
        async for session in get_neo4j_session():
            base = await session.run(
                f"MATCH (p:Paper {{id: $id}}) RETURN {PAPER_RETURN}", id=paper_id
            )
            record = await base.single()
            if not record:
                raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
            paper = _paper_row(dict(record))

            chunk_res = await session.run(
                "MATCH (p:Paper {id: $id})-[:HAS_CHUNK]->(c:Chunk) RETURN count(c) AS n",
                id=paper_id,
            )
            paper["chunk_count"] = (await chunk_res.single())["n"]

            cite_res = await session.run(
                "MATCH (p:Paper {id: $id})-[:CITES]->() RETURN count(*) AS n", id=paper_id
            )
            paper["citation_count"] = (await cite_res.single())["n"]

            cited_by_res = await session.run(
                "MATCH (:Paper)-[:CITES]->(p:Paper {id: $id}) RETURN count(*) AS n", id=paper_id
            )
            paper["citing_count"] = (await cited_by_res.single())["n"]

            ent_res = await session.run(
                """
                MATCH (p:Paper {id: $id})
                OPTIONAL MATCH (p)-[:ADDRESSES_TOPIC]->(c:Concept)
                OPTIONAL MATCH (p)-[:USES_METHOD]->(m:Method)
                OPTIONAL MATCH (p)-[:USES_DATASET]->(d:Dataset)
                OPTIONAL MATCH (a:Author)-[:WROTE]->(p)
                RETURN collect(DISTINCT c.name) AS concepts,
                       collect(DISTINCT m.name) AS methods,
                       collect(DISTINCT d.name) AS datasets,
                       collect(DISTINCT a.name) AS authors
                """,
                id=paper_id,
            )
            ent = dict(await ent_res.single())
            paper["concepts"] = [x for x in ent["concepts"] if x] or []
            paper["methods"] = [x for x in ent["methods"] if x] or []
            paper["datasets"] = [x for x in ent["datasets"] if x] or []
            paper["authors"] = [x for x in ent["authors"] if x]

            return paper
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get paper failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}/chunks")
async def get_paper_chunks(
    paper_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List chunks of a paper (ordered by chunk_index)."""
    try:
        async for session in get_neo4j_session():
            total_res = await session.run(
                "MATCH (:Paper {id: $id})-[:HAS_CHUNK]->(c:Chunk) RETURN count(c) AS total",
                id=paper_id,
            )
            total = (await total_res.single())["total"]

            res = await session.run(
                """
                MATCH (:Paper {id: $id})-[:HAS_CHUNK]->(c:Chunk)
                RETURN c.id AS id, c.paper_id AS paper_id, c.text AS text,
                       c.chunk_index AS chunk_index, c.metadata AS metadata
                ORDER BY c.chunk_index ASC
                SKIP $offset LIMIT $limit
                """,
                id=paper_id, offset=offset, limit=limit,
            )
            chunks = []
            async for r in res:
                row = dict(r)
                meta = row.get("metadata")
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except json.JSONDecodeError:
                        meta = {"raw": meta}
                row["metadata"] = meta or {}
                chunks.append(row)

            return {"chunks": chunks, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Get chunks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{paper_id}/citations")
async def get_paper_citations(
    paper_id: str,
    direction: str = Query("both", pattern="^(both|outgoing|incoming)$"),
    limit: int = Query(50, ge=1, le=200),
):
    """Citation edges for a paper: outgoing (cites) and incoming (cited by)."""
    try:
        async for session in get_neo4j_session():
            exists = await session.run(
                "MATCH (p:Paper {id: $id}) RETURN count(p) AS n", id=paper_id
            )
            if (await exists.single())["n"] == 0:
                raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

            result = {"paper_id": paper_id, "outgoing": [], "incoming": []}

            if direction in ("both", "outgoing"):
                res = await session.run(
                    """
                    MATCH (p:Paper {id: $id})-[:CITES]->(t:Paper)
                    RETURN t.id AS paper_id, t.title AS title, t.year AS year,
                           t.venue AS venue, t.doi AS doi
                    ORDER BY t.year DESC, t.title ASC
                    LIMIT $limit
                    """,
                    id=paper_id, limit=limit,
                )
                result["outgoing"] = [dict(r) for r in await res.data()]

            if direction in ("both", "incoming"):
                res = await session.run(
                    """
                    MATCH (s:Paper)-[:CITES]->(p:Paper {id: $id})
                    RETURN s.id AS paper_id, s.title AS title, s.year AS year,
                           s.venue AS venue, s.doi AS doi
                    ORDER BY s.year DESC, s.title ASC
                    LIMIT $limit
                    """,
                    id=paper_id, limit=limit,
                )
                result["incoming"] = [dict(r) for r in await res.data()]

            # Counts
            for key, q in [
                ("outgoing_count", "MATCH (p:Paper {id: $id})-[:CITES]->() RETURN count(*) AS n"),
                ("incoming_count", "MATCH (:Paper)-[:CITES]->(p:Paper {id: $id}) RETURN count(*) AS n"),
            ]:
                r = await session.run(q, id=paper_id)
                result[key] = (await r.single())["n"]

            return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get citations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- Entities ----------------

# Per-type config: node label, node var, relation pattern (Paper side), extra property
_ENTITY_QUERIES = {
    "concept": {
        "label": "Concept", "var": "c",
        "pattern": "(p:Paper)-[:ADDRESSES_TOPIC]->(c:Concept)",
        "extra": "c.category",
    },
    "method": {
        "label": "Method", "var": "m",
        "pattern": "(p:Paper)-[:USES_METHOD]->(m:Method)",
        "extra": "m.description",
    },
    "dataset": {
        "label": "Dataset", "var": "d",
        "pattern": "(p:Paper)-[:USES_DATASET]->(d:Dataset)",
        "extra": "d.domain",
    },
    "author": {
        "label": "Author", "var": "a",
        "pattern": "(a:Author)-[:WROTE]->(p:Paper)",
        "extra": "a.institution",
    },
    "paper": {
        "label": "Paper", "var": "p",
        "pattern": "",
        "extra": "p.year",
        "name_field": "title",
    },
}


async def _query_entities(session, etype: str, ql: Optional[str], limit: int) -> list[dict]:
    cfg = _ENTITY_QUERIES[etype]
    var = cfg["var"]
    name_field = cfg.get("name_field", "name")
    name_col = f"{var}.{name_field}"
    id_col = f"{var}.id"
    where = f"WHERE toLower({name_col}) CONTAINS $ql " if ql else ""
    pattern = cfg['pattern']
    optional_match = f"OPTIONAL MATCH {pattern}" if pattern else ""
    query = f"""
    MATCH ({var}:{cfg['label']})
    {where}
    {optional_match}
    WITH {var}, count(DISTINCT p) AS paper_count
    RETURN {id_col} AS id, {name_col} AS name, {cfg['extra']} AS extra, paper_count
    ORDER BY paper_count DESC, name ASC
    LIMIT $limit
    """
    params: dict[str, str | int] = {"limit": limit}
    if ql:
        params["ql"] = ql
    res = await session.run(query, **params)
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "type": etype,
            "paper_count": row["paper_count"],
            "extra": row.get("extra"),
        }
        async for row in res
    ]


@router.get("/entities/all")
@router.get("/entities/all/")
async def list_all_entities(limit: int = Query(25, ge=1, le=200)):
    """All entity types merged, sorted by paper count."""
    try:
        async for session in get_neo4j_session():
            entities = []
            for etype in _ENTITY_QUERIES:
                entities.extend(await _query_entities(session, etype, None, limit))
            entities.sort(key=lambda e: e["paper_count"], reverse=True)
            return {"entities": entities[:limit], "total": len(entities)}
    except Exception as e:
        logger.error(f"List entities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Entities router mounted under /api/v1/entities (own prefix in main.py mount below)
entities_router = APIRouter(prefix="/entities", tags=["catalog"])


@entities_router.get("")
@entities_router.get("/")
async def list_entities(
    type: Optional[str] = Query(None, pattern="^(concept|method|dataset|author|paper)$"),
    q: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """List entities (concepts, methods, datasets, authors) with paper counts."""
    ql = (q or "").lower() or None
    try:
        async for session in get_neo4j_session():
            if type:
                entities = await _query_entities(session, type, ql, limit)
                return {"entities": entities, "total": len(entities)}
            entities = []
            for etype in _ENTITY_QUERIES:
                entities.extend(await _query_entities(session, etype, ql, limit))
            entities.sort(key=lambda e: e["paper_count"], reverse=True)
            return {"entities": entities[:limit], "total": len(entities)}
    except Exception as e:
        logger.error(f"List entities failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
