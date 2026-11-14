"""
Graph Writer Module
Batch Cypher operations for injecting entities and relations into Neo4j.
"""

import logging
from typing import Optional
from neo4j import AsyncSession
from app.schemas.entities import (
    ExtractedEntities,
    PaperCreate,
    ChunkCreate,
    AuthorEntity,
    ConceptEntity,
    MethodEntity,
    DatasetEntity,
    RelationEntity,
    EntityType,
    RelationType,
)

logger = logging.getLogger(__name__)


class GraphWriter:
    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================================
    # Paper Operations
    # ============================================================

    async def create_paper(self, paper: PaperCreate) -> str:
        """Create or merge Paper node."""
        query = """
        MERGE (p:Paper {id: $id})
        SET p.title = $title,
            p.abstract = $abstract,
            p.year = $year,
            p.doi = $doi,
            p.venue = $venue,
            p.keywords = $keywords,
            p.embedding = $embedding,
            p.updated_at = datetime()
        RETURN p.id
        """
        # Explicitly pass only the fields in the query to avoid extra fields
        params = {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "year": paper.year,
            "doi": paper.doi,
            "venue": paper.venue,
            "keywords": paper.keywords,
            "embedding": paper.embedding,
        }
        result = await self.session.run(query, **params)
        record = await result.single()
        return record["p.id"] if record else paper.id

    async def get_paper(self, paper_id: str) -> Optional[dict]:
        query = "MATCH (p:Paper {id: $id}) RETURN p"
        result = await self.session.run(query, id=paper_id)
        record = await result.single()
        return dict(record["p"]) if record else None

    # ============================================================
    # Entity Operations (Batch)
    # ============================================================

    async def create_authors(self, authors: list[AuthorEntity], paper_id: str) -> int:
        if not authors:
            return 0

        query = """
        UNWIND $authors AS author
        MERGE (a:Author {id: author.id})
        SET a.name = author.name,
            a.institution = author.institution,
            a.updated_at = datetime()
        WITH a, author
        MATCH (p:Paper {id: $paper_id})
        MERGE (a)-[:WROTE]->(p)
        RETURN count(a) as created
        """

        # Generate stable IDs for authors
        author_data = []
        for a in authors:
            author_id = f"author_{abs(hash(a.name.lower().strip())) % 10**12}"
            author_data.append({
                "id": author_id,
                "name": a.name.strip(),
                "institution": a.institution.strip() if a.institution else None,
            })

        result = await self.session.run(query, authors=author_data, paper_id=paper_id)
        record = await result.single()
        return record["created"] if record else 0

    async def create_concepts(self, concepts: list[ConceptEntity], paper_id: str) -> int:
        if not concepts:
            return 0

        query = """
        UNWIND $concepts AS concept
        MERGE (c:Concept {id: concept.id})
        SET c.name = concept.name,
            c.category = concept.category,
            c.updated_at = datetime()
        WITH c, concept
        MATCH (p:Paper {id: $paper_id})
        MERGE (p)-[:ADDRESSES_TOPIC]->(c)
        RETURN count(c) as created
        """

        concept_data = []
        for c in concepts:
            concept_id = f"concept_{abs(hash(c.name.lower().strip())) % 10**12}"
            concept_data.append({
                "id": concept_id,
                "name": c.name.strip(),
                "category": c.category.strip(),
            })

        result = await self.session.run(query, concepts=concept_data, paper_id=paper_id)
        record = await result.single()
        return record["created"] if record else 0

    async def create_methods(self, methods: list[MethodEntity], paper_id: str) -> int:
        if not methods:
            return 0

        query = """
        UNWIND $methods AS method
        MERGE (m:Method {id: method.id})
        SET m.name = method.name,
            m.description = method.description,
            m.updated_at = datetime()
        WITH m, method
        MATCH (p:Paper {id: $paper_id})
        MERGE (p)-[:USES_METHOD]->(m)
        RETURN count(m) as created
        """

        method_data = []
        for m in methods:
            method_id = f"method_{abs(hash(m.name.lower().strip())) % 10**12}"
            method_data.append({
                "id": method_id,
                "name": m.name.strip(),
                "description": m.description.strip() if m.description else None,
            })

        result = await self.session.run(query, methods=method_data, paper_id=paper_id)
        record = await result.single()
        return record["created"] if record else 0

    async def create_datasets(self, datasets: list[DatasetEntity], paper_id: str) -> int:
        if not datasets:
            return 0

        query = """
        UNWIND $datasets AS dataset
        MERGE (d:Dataset {id: dataset.id})
        SET d.name = dataset.name,
            d.domain = dataset.domain,
            d.updated_at = datetime()
        WITH d, dataset
        MATCH (p:Paper {id: $paper_id})
        MERGE (p)-[:USES_DATASET]->(d)
        RETURN count(d) as created
        """

        dataset_data = []
        for d in datasets:
            dataset_id = f"dataset_{abs(hash(d.name.lower().strip())) % 10**12}"
            dataset_data.append({
                "id": dataset_id,
                "name": d.name.strip(),
                "domain": d.domain.strip() if d.domain else None,
            })

        result = await self.session.run(query, datasets=dataset_data, paper_id=paper_id)
        record = await result.single()
        return record["created"] if record else 0

    # ============================================================
    # Relations (Cross-paper, etc.)
    # ============================================================

    async def create_relations(self, relations: list[RelationEntity]) -> int:
        if not relations:
            return 0

        # Group by relation type for batch processing
        created = 0
        for rel_type in RelationType:
            type_relations = [r for r in relations if r.relation == rel_type]
            if not type_relations:
                continue

            query = f"""
            UNWIND $rels AS rel
            MATCH (source:{rel_type.source_type.value} {{name: rel.source_name}})
            MATCH (target:{rel_type.target_type.value} {{name: rel.target_name}})
            MERGE (source)-[:{rel_type.value}]->(target)
            RETURN count(*) as created
            """

            rel_data = [{
                "source_name": r.source_name.strip(),
                "target_name": r.target_name.strip(),
            } for r in type_relations]

            try:
                result = await self.session.run(query, rels=rel_data)
                record = await result.single()
                created += record["created"] if record else 0
            except Exception as e:
                logger.warning(f"Failed to create {rel_type.value} relations: {e}")

        return created

    # ============================================================
    # Chunk Operations (for RAG)
    # ============================================================

    async def create_chunks(self, chunks: list[ChunkCreate]) -> int:
        if not chunks:
            return 0

        query = """
        UNWIND $chunks AS chunk
        MERGE (c:Chunk {id: chunk.id})
        SET c.paper_id = chunk.paper_id,
            c.text = chunk.text,
            c.chunk_index = chunk.chunk_index,
            c.embedding = chunk.embedding,
            c.metadata = chunk.metadata,
            c.created_at = datetime()
        WITH c, chunk
        MATCH (p:Paper {id: chunk.paper_id})
        MERGE (p)-[:HAS_CHUNK]->(c)
        RETURN count(c) as created
        """

        # Serialize metadata to JSON string since Neo4j doesn't support Map properties
        import json
        chunk_data = []
        for c in chunks:
            chunk_dict = c.model_dump()
            # Convert metadata dict to JSON string
            if chunk_dict.get("metadata"):
                chunk_dict["metadata"] = json.dumps(chunk_dict["metadata"])
            chunk_data.append(chunk_dict)

        result = await self.session.run(query, chunks=chunk_data)
        record = await result.single()
        return record["created"] if record else 0

    # ============================================================
    # Batch Ingestion (Main Entry Point)
    # ============================================================

    async def ingest_paper_with_entities(
        self,
        paper: PaperCreate,
        entities: ExtractedEntities,
        chunks: list[ChunkCreate] = None,
    ) -> dict:
        """Complete ingestion: paper + entities + relations + chunks in one transaction."""
        stats = {
            "paper_id": paper.id,
            "authors_created": 0,
            "concepts_created": 0,
            "methods_created": 0,
            "datasets_created": 0,
            "relations_created": 0,
            "chunks_created": 0,
        }

        # Create paper
        await self.create_paper(paper)

        # Create entities linked to paper
        stats["authors_created"] = await self.create_authors(entities.authors, paper.id)
        stats["concepts_created"] = await self.create_concepts(entities.concepts, paper.id)
        stats["methods_created"] = await self.create_methods(entities.methods, paper.id)
        stats["datasets_created"] = await self.create_datasets(entities.datasets, paper.id)

        # Create cross-paper relations
        stats["relations_created"] = await self.create_relations(entities.relations)

        # Create chunks
        if chunks:
            stats["chunks_created"] = await self.create_chunks(chunks)

        logger.info(f"Ingestion complete for {paper.id}: {stats}")
        return stats


async def ingest_paper_batch(
    session: AsyncSession,
    papers_data: list[dict],  # Each: {paper, entities, chunks}
) -> list[dict]:
    """Batch ingest multiple papers."""
    writer = GraphWriter(session)
    results = []

    for data in papers_data:
        paper = PaperCreate(**data["paper"])
        entities = ExtractedEntities(**data["entities"])
        chunks = [ChunkCreate(**c) for c in data.get("chunks", [])]

        stats = await writer.ingest_paper_with_entities(paper, entities, chunks)
        results.append(stats)

    return results