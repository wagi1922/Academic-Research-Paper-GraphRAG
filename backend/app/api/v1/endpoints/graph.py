"""
Graph Visualization Endpoint
Returns subgraph data for frontend visualization (Cytosigma/React Flow/D3).
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.retrieval.graph_traversal import GraphTraversal, get_neighbors
from app.core.neo4j_driver import get_neo4j_driver, get_neo4j_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/health")
async def health_check():
    """Health check endpoint under /api/v1/graph/health."""
    neo4j_status = "unknown"
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            await session.run("RETURN 1")
        neo4j_status = "connected"
    except Exception as e:
        neo4j_status = f"error: {str(e)}"

    return {
        "status": "healthy" if neo4j_status == "connected" else "degraded",
        "neo4j": neo4j_status,
        "version": "0.1.0",
    }


class VisualizeRequest(BaseModel):
    paper_id: str = None
    node_id: str = None
    depth: int = 2
    max_nodes: int = 100
    relation_types: list[str] = None


class GraphVisualizationResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]
    metadata: dict


@router.get("/visualize", response_model=GraphVisualizationResponse)
async def visualize_graph(
    paper_id: str = Query(None, description="Seed paper ID for traversal"),
    node_id: str = Query(None, description="Specific node ID for neighborhood"),
    depth: int = Query(2, ge=1, le=4, description="Traversal depth"),
    max_nodes: int = Query(100, ge=10, le=500, description="Max nodes to return"),
    relation_types: str = Query(None, description="Comma-separated relation types"),
):
    """
    Get subgraph for visualization.
    Provide either paper_id (for paper-centric view) or node_id (for node-centric view).
    """
    try:
        async for session in get_neo4j_session():
            traversal = GraphTraversal(session)

            rel_types = relation_types.split(",") if relation_types else None

            if paper_id:
                # Paper-centric multi-hop traversal
                result = await traversal.traverse_from_papers(
                    seed_paper_ids=[paper_id],
                    depth=depth,
                    max_nodes_per_hop=max_nodes,
                    relation_types=rel_types,
                )
                nodes = result.get("nodes", [])
                edges = result.get("edges", [])
                metadata = {
                    "type": "paper_traversal",
                    "seed_paper_id": paper_id,
                    "depth": depth,
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                }

            elif node_id:
                # Node-centric neighborhood
                result = await get_neighbors(
                    session=session,
                    node_id=node_id,
                    relation_types=rel_types,
                    limit=max_nodes,
                )
                nodes = result.get("nodes", [])
                edges = result.get("edges", [])
                metadata = {
                    "type": "node_neighborhood",
                    "center_node_id": node_id,
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                }

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either paper_id or node_id must be provided",
                )

            # Format for frontend (Cytoscape/React Flow compatible)
            formatted_nodes = [_format_node(n) for n in nodes]
            formatted_edges = [_format_edge(e) for e in edges]

            return GraphVisualizationResponse(
                nodes=formatted_nodes,
                edges=formatted_edges,
                metadata=metadata,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@router.get("/paper/{paper_id}/subgraph")
async def get_paper_subgraph(
    paper_id: str,
    depth: int = Query(2, ge=1, le=3),
    max_nodes: int = Query(50, ge=10, le=200),
):
    """Get paper-centered subgraph with citation network."""
    try:
        async for session in get_neo4j_session():
            traversal = GraphTraversal(session)
            result = await traversal.traverse_from_papers(
                seed_paper_ids=[paper_id],
                depth=depth,
                max_nodes_per_hop=max_nodes,
                relation_types=["CITES", "USES_METHOD", "USES_DATASET", "ADDRESSES_TOPIC", "WROTE"],
            )

            # Get paper details
            from app.retrieval.vector_search import get_paper_by_id
            paper = await get_paper_by_id(session, paper_id)

            return {
                "paper": _format_node(dict(paper)) if paper else None,
                "nodes": [_format_node(n) for n in result.get("nodes", [])],
                "edges": [_format_edge(e) for e in result.get("edges", [])],
                "paths": result.get("paths", []),
                "metadata": {
                    "paper_id": paper_id,
                    "depth": depth,
                    "total_nodes": len(result.get("nodes", [])),
                    "total_edges": len(result.get("edges", [])),
                },
            }

    except Exception as e:
        logger.error(f"Paper subgraph failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concept/{concept_name}/papers")
async def get_concept_papers(
    concept_name: str,
    limit: int = Query(20, ge=1, le=100),
):
    """Get papers addressing a specific concept."""
    try:
        async for session in get_neo4j_session():
            from app.retrieval.graph_traversal import find_papers_by_concept
            papers = await find_papers_by_concept(session, concept_name, limit)
            return {
                "concept": concept_name,
                "papers": [_format_node(dict(p)) for p in papers],
                "count": len(papers),
            }
    except Exception as e:
        logger.error(f"Concept papers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/method/{method_name}/papers")
async def get_method_papers(
    method_name: str,
    limit: int = Query(20, ge=1, le=100),
):
    """Get papers using a specific method."""
    try:
        async for session in get_neo4j_session():
            from app.retrieval.graph_traversal import find_papers_by_method
            papers = await find_papers_by_method(session, method_name, limit)
            return {
                "method": method_name,
                "papers": [_format_node(dict(p)) for p in papers],
                "count": len(papers),
            }
    except Exception as e:
        logger.error(f"Method papers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dataset/{dataset_name}/papers")
async def get_dataset_papers(
    dataset_name: str,
    limit: int = Query(20, ge=1, le=100),
):
    """Get papers using a specific dataset."""
    try:
        async for session in get_neo4j_session():
            from app.retrieval.graph_traversal import find_papers_by_dataset
            papers = await find_papers_by_dataset(session, dataset_name, limit)
            return {
                "dataset": dataset_name,
                "papers": [_format_node(dict(p)) for p in papers],
                "count": len(papers),
            }
    except Exception as e:
        logger.error(f"Dataset papers failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats():
    """Get overall graph statistics."""
    try:
        async for session in get_neo4j_session():
            queries = {
                "papers": "MATCH (p:Paper) RETURN count(p) as count",
                "authors": "MATCH (a:Author) RETURN count(a) as count",
                "concepts": "MATCH (c:Concept) RETURN count(c) as count",
                "methods": "MATCH (m:Method) RETURN count(m) as count",
                "datasets": "MATCH (d:Dataset) RETURN count(d) as count",
                "chunks": "MATCH (c:Chunk) RETURN count(c) as count",
                "citations": "MATCH ()-[r:CITES]->() RETURN count(r) as count",
                "relations": "MATCH ()-[r]->() RETURN count(r) as count",
            }

            stats = {}
            for key, query in queries.items():
                result = await session.run(query)
                record = await result.single()
                stats[key] = record["count"] if record else 0

            return stats

    except Exception as e:
        logger.error(f"Graph stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _format_node(node: dict) -> dict:
    """Format Neo4j node for frontend visualization."""
    from app.retrieval.graph_traversal import _serialize_neo4j_value
    
    # Serialize all node properties to handle Neo4j temporal types
    serialized_node = {k: _serialize_neo4j_value(v) for k, v in node.items()}
    
    labels = serialized_node.get("labels", [])
    primary_label = labels[0] if labels else "Node"

    # Extract display name
    name = (
        serialized_node.get("name")
        or serialized_node.get("title")
        or serialized_node.get("id")
        or "Unknown"
    )

    # Build node data
    return {
        "id": serialized_node.get("id", serialized_node.get("element_id", "unknown")),
        "label": name,
        "type": primary_label.lower(),
        "properties": {k: v for k, v in serialized_node.items() if k not in ["labels", "id", "element_id"]},
        "classes": primary_label.lower(),
    }


def _format_edge(edge: dict) -> dict:
    """Format Neo4j relationship for frontend visualization."""
    return {
        "id": edge.get("id", edge.get("element_id", "unknown")),
        "source": edge.get("source", edge.get("start_node", "")),
        "target": edge.get("target", edge.get("end_node", "")),
        "label": edge.get("type", edge.get("relationship_type", "RELATED")),
        "type": edge.get("type", edge.get("relationship_type", "RELATED")).lower(),
        "properties": edge.get("properties", {}),
    }