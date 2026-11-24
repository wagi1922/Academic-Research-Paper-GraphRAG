"""
Graph Traversal Module
Multi-hop graph traversal for GraphRAG context expansion.
"""

import logging
from typing import Optional
from neo4j import AsyncSession
from neo4j.time import DateTime, Date, Time, Duration

logger = logging.getLogger(__name__)


def _serialize_neo4j_value(value):
    """Convert Neo4j temporal types to JSON-serializable values."""
    if isinstance(value, DateTime):
        return value.iso_format()
    if isinstance(value, Date):
        return value.iso_format()
    if isinstance(value, Time):
        return value.iso_format()
    if isinstance(value, Duration):
        return str(value)
    if isinstance(value, dict):
        return {k: _serialize_neo4j_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize_neo4j_value(v) for v in value]
    return value


class GraphTraversal:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def traverse_from_papers(
        self,
        seed_paper_ids: list[str],
        depth: int = 2,
        max_nodes_per_hop: int = 50,
        relation_types: list[str] = None,
    ) -> dict:
        """
        Multi-hop traversal from seed papers.
        Returns subgraph: nodes and edges.
        """
        if not seed_paper_ids:
            return {"nodes": [], "edges": [], "paths": []}

        # Default relation types for academic graph
        if relation_types is None:
            relation_types = [
                "CITES",
                "USES_METHOD",
                "USES_DATASET",
                "ADDRESSES_TOPIC",
                "WROTE",
            ]

        rel_filter = "|".join(relation_types)

        # Multi-hop traversal query
        query = f"""
        MATCH (seed:Paper)
        WHERE seed.id IN $seed_ids
        CALL apoc.path.subgraphAll(seed, {{
            maxLevel: $depth,
            relationshipFilter: '{rel_filter}',
            limit: $max_nodes
        }})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """

        result = await self.session.run(
            query,
            seed_ids=seed_paper_ids,
            depth=depth,
            max_nodes=max_nodes_per_hop,
        )
        record = await result.single()

        if not record:
            return {"nodes": [], "edges": [], "paths": []}

        nodes = [self._node_to_dict(n) for n in record["nodes"]]
        edges = [self._rel_to_dict(r) for r in record["relationships"]]

        # Also get explicit paths for citation chains
        paths = await self._get_explicit_paths(seed_paper_ids, depth, relation_types)

        return {
            "nodes": nodes,
            "edges": edges,
            "paths": paths,
            "seed_paper_ids": seed_paper_ids,
            "depth": depth,
        }

    async def _get_explicit_paths(
        self,
        seed_paper_ids: list[str],
        depth: int,
        relation_types: list[str],
    ) -> list[dict]:
        """Get explicit paths for important relations (citations, method chains)."""
        rel_filter = "|".join(relation_types)
        paths = []

        # Citation chains (backward and forward)
        for direction in ["out", "in"]:
            if direction == "out":
                pattern = f"(seed:Paper)-[:{rel_filter}*1..{depth}]->(connected:Paper)"
            else:
                pattern = f"(seed:Paper)<-[:{rel_filter}*1..{depth}]-(connected:Paper)"
            query = f"""
            MATCH path = {pattern}
            WHERE seed.id IN $seed_ids
            RETURN path
            LIMIT 20
            """
            result = await self.session.run(query, seed_ids=seed_paper_ids)
            async for record in result:
                path = record["path"]
                paths.append({
                    "type": "citation_chain",
                    "nodes": [self._node_to_dict(n) for n in path.nodes],
                    "relationships": [self._rel_to_dict(r) for r in path.relationships],
                })

        # Method sharing chains
        query = f"""
        MATCH path = (seed:Paper)-[:USES_METHOD]->(:Method)<-[:USES_METHOD]-(other:Paper)
        WHERE seed.id IN $seed_ids
        RETURN path
        LIMIT 10
        """
        result = await self.session.run(query, seed_ids=seed_paper_ids)
        async for record in result:
            path = record["path"]
            paths.append({
                "type": "method_sharing",
                "nodes": [self._node_to_dict(n) for n in path.nodes],
                "relationships": [self._rel_to_dict(r) for r in path.relationships],
            })

        return paths

    def _node_to_dict(self, node) -> dict:
        labels = list(node.labels)
        props = _serialize_neo4j_value(dict(node))
        if isinstance(props, dict):
            props["labels"] = labels
            props["id"] = node.element_id
        else:
            props = {"labels": labels, "id": node.element_id}
        return props

    def _rel_to_dict(self, rel) -> dict:
        props = _serialize_neo4j_value(dict(rel))
        if not isinstance(props, dict):
            props = {}
        return {
            "type": rel.type,
            "source": rel.start_node.element_id,
            "target": rel.end_node.element_id,
            "properties": props,
            "id": rel.element_id,
            "label": rel.type,
        }


async def get_neighbors(
    session: AsyncSession,
    node_id: str,
    relation_types: list[str] = None,
    direction: str = "both",
    limit: int = 50,
) -> dict:
    """Get immediate neighbors of a node."""
    if relation_types is None:
        relation_types = ["CITES", "USES_METHOD", "USES_DATASET", "ADDRESSES_TOPIC", "WROTE"]

    rel_filter = "|".join(relation_types)
    dir_symbol = "" if direction == "both" else (">" if direction == "out" else "<")

    query = f"""
    MATCH (n) WHERE elementId(n) = $node_id
    CALL apoc.path.subgraphAll(n, {{
        maxLevel: 1,
        relationshipFilter: '{dir_symbol}{rel_filter}',
        limit: $limit
    }})
    YIELD nodes, relationships
    RETURN nodes, relationships
    """

    result = await session.run(query, node_id=node_id, limit=limit)
    record = await result.single()

    if not record:
        return {"nodes": [], "edges": []}

    return {
        "nodes": [_node_to_fe_dict(n) for n in record["nodes"]],
        "edges": [_rel_to_fe_dict(r) for r in record["relationships"]],
    }


def _node_to_fe_dict(node) -> dict:
    labels = list(node.labels)
    props = _serialize_neo4j_value(dict(node))
    if isinstance(props, dict):
        props["labels"] = labels
        props["id"] = node.element_id
    else:
        props = {"labels": labels, "id": node.element_id}
    return props


def _rel_to_fe_dict(rel) -> dict:
    props = _serialize_neo4j_value(dict(rel))
    if not isinstance(props, dict):
        props = {}
    return {
        "type": rel.type,
        "source": rel.start_node.element_id,
        "target": rel.end_node.element_id,
        "properties": props,
        "id": rel.element_id,
        "label": rel.type,
    }


async def find_papers_by_method(
    session: AsyncSession,
    method_name: str,
    limit: int = 20,
) -> list[dict]:
    """Find papers that use a specific method."""
    query = """
    MATCH (p:Paper)-[:USES_METHOD]->(m:Method {name: $method_name})
    RETURN p
    ORDER BY p.year DESC
    LIMIT $limit
    """
    result = await session.run(query, method_name=method_name, limit=limit)
    records = []
    async for record in result:
        records.append(dict(record["p"]))
    return records


async def find_papers_by_dataset(
    session: AsyncSession,
    dataset_name: str,
    limit: int = 20,
) -> list[dict]:
    """Find papers that use a specific dataset."""
    query = """
    MATCH (p:Paper)-[:USES_DATASET]->(d:Dataset {name: $dataset_name})
    RETURN p
    ORDER BY p.year DESC
    LIMIT $limit
    """
    result = await session.run(query, dataset_name=dataset_name, limit=limit)
    records = []
    async for record in result:
        records.append(dict(record["p"]))
    return records


async def find_papers_by_concept(
    session: AsyncSession,
    concept_name: str,
    limit: int = 20,
) -> list[dict]:
    """Find papers addressing a specific concept."""
    query = """
    MATCH (p:Paper)-[:ADDRESSES_TOPIC]->(c:Concept {name: $concept_name})
    RETURN p
    ORDER BY p.year DESC
    LIMIT $limit
    """
    result = await session.run(query, concept_name=concept_name, limit=limit)
    records = []
    async for record in result:
        records.append(dict(record["p"]))
    return records