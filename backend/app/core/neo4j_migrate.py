#!/usr/bin/env python3
"""
Neo4j Schema Migration Script for GraphRAG
Creates constraints, indexes, and vector index for the Academic Paper Knowledge Graph.
Run: python backend/app/core/neo4j_migrate.py
"""

import asyncio
import logging
from neo4j import AsyncGraphDatabase
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Cypher statements for schema creation
SCHEMA_STATEMENTS = [
    # ============================================================
    # CONSTRAINTS (Unique & Existence)
    # ============================================================
    # Paper
    "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT paper_doi_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.doi IS UNIQUE",
    # Author
    "CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE",
    # Concept
    "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
    # Method
    "CREATE CONSTRAINT method_id_unique IF NOT EXISTS FOR (m:Method) REQUIRE m.id IS UNIQUE",
    # Dataset
    "CREATE CONSTRAINT dataset_id_unique IF NOT EXISTS FOR (d:Dataset) REQUIRE d.id IS UNIQUE",

    # ============================================================
    # INDEXES (Performance)
    # ============================================================
    # Paper
    "CREATE INDEX paper_title_idx IF NOT EXISTS FOR (p:Paper) ON (p.title)",
    "CREATE INDEX paper_year_idx IF NOT EXISTS FOR (p:Paper) ON (p.year)",
    "CREATE INDEX paper_embedding_idx IF NOT EXISTS FOR (p:Paper) ON (p.embedding)",

    # Author
    "CREATE INDEX author_name_idx IF NOT EXISTS FOR (a:Author) ON (a.name)",
    "CREATE INDEX author_institution_idx IF NOT EXISTS FOR (a:Author) ON (a.institution)",

    # Concept
    "CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name)",
    "CREATE INDEX concept_category_idx IF NOT EXISTS FOR (c:Concept) ON (c.category)",

    # Method
    "CREATE INDEX method_name_idx IF NOT EXISTS FOR (m:Method) ON (m.name)",

    # Dataset
    "CREATE INDEX dataset_name_idx IF NOT EXISTS FOR (d:Dataset) ON (d.name)",
    "CREATE INDEX dataset_domain_idx IF NOT EXISTS FOR (d:Dataset) ON (d.domain)",

    # ============================================================
    # VECTOR INDEX (Neo4j 5.13+)
    # For semantic search on Paper abstracts/chunks
    # ============================================================
    """
    CREATE VECTOR INDEX paper_abstract_vector_idx IF NOT EXISTS
    FOR (p:Paper) ON (p.embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
        }
    }
    """,

    # ============================================================
    # FULLTEXT INDEX (for keyword search fallback)
    # ============================================================
    """
    CREATE FULLTEXT INDEX paper_fulltext_idx IF NOT EXISTS
    FOR (p:Paper) ON EACH [p.title, p.abstract, p.keywords]
    """,
]


# Additional: Chunk nodes for RAG (optional, separate from Paper)
CHUNK_STATEMENTS = [
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE INDEX chunk_paper_id_idx IF NOT EXISTS FOR (c:Chunk) ON (c.paper_id)",
    "CREATE INDEX chunk_embedding_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding)",
    """
    CREATE VECTOR INDEX chunk_vector_idx IF NOT EXISTS
    FOR (c:Chunk) ON (c.embedding)
    OPTIONS {
        indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
        }
    }
    """,
]


async def run_migration(include_chunks: bool = True):
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        await driver.verify_connectivity()
        logger.info("Connected to Neo4j successfully")

        async with driver.session(database=settings.neo4j_database) as session:
            # Run main schema statements
            for i, stmt in enumerate(SCHEMA_STATEMENTS):
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    await session.run(stmt)
                    logger.info(f"✓ Executed statement {i+1}/{len(SCHEMA_STATEMENTS)}")
                except Exception as e:
                    # Some statements might fail if already exists (IF NOT EXISTS handles most)
                    if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                        logger.info(f"⊘ Statement {i+1} already exists (skipped)")
                    else:
                        logger.warning(f"⚠ Statement {i+1} warning: {e}")

            # Run chunk statements if requested
            if include_chunks:
                for i, stmt in enumerate(CHUNK_STATEMENTS):
                    stmt = stmt.strip()
                    if not stmt:
                        continue
                    try:
                        await session.run(stmt)
                        logger.info(f"✓ Chunk statement {i+1}/{len(CHUNK_STATEMENTS)}")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                            logger.info(f"⊘ Chunk statement {i+1} already exists (skipped)")
                        else:
                            logger.warning(f"⚠ Chunk statement {i+1} warning: {e}")

        # Verify created constraints and indexes
        await verify_schema(driver)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await driver.close()
        logger.info("Migration completed")


async def verify_schema(driver):
    """Verify constraints and indexes were created."""
    async with driver.session(database=settings.neo4j_database) as session:
        # Check constraints
        result = await session.run("SHOW CONSTRAINTS")
        constraints = await result.data()
        logger.info(f"Constraints ({len(constraints)}):")
        for c in constraints:
            logger.info(f"  - {c.get('name')}: {c.get('type')} on {c.get('labelsOrTypes')} {c.get('properties')}")

        # Check indexes
        result = await session.run("SHOW INDEXES")
        indexes = await result.data()
        logger.info(f"Indexes ({len(indexes)}):")
        for idx in indexes:
            logger.info(f"  - {idx.get('name')}: {idx.get('type')} on {idx.get('labelsOrTypes')} {idx.get('properties')}")

        # Check vector indexes specifically
        vector_indexes = [i for i in indexes if i.get('type') == 'VECTOR']
        logger.info(f"Vector indexes: {len(vector_indexes)}")
        for vi in vector_indexes:
            logger.info(f"  - {vi.get('name')}: {vi.get('labelsOrTypes')}.{vi.get('properties')}")


async def drop_all_schema():
    """DANGER: Drop all constraints and indexes. Use with caution!"""
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        await driver.verify_connectivity()
        async with driver.session(database=settings.neo4j_database) as session:
            # Drop constraints
            result = await session.run("SHOW CONSTRAINTS")
            constraints = await result.data()
            for record in constraints:
                name = record.get("name")
                if name:
                    await session.run(f"DROP CONSTRAINT {name} IF EXISTS")
                    logger.info(f"Dropped constraint: {name}")

            # Drop indexes
            result = await session.run("SHOW INDEXES")
            indexes = await result.data()
            for record in indexes:
                name = record.get("name")
                if name:
                    await session.run(f"DROP INDEX {name} IF EXISTS")
                    logger.info(f"Dropped index: {name}")

        logger.info("All schema dropped")
    finally:
        await driver.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        confirm = input("⚠️  This will DROP all constraints and indexes. Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            asyncio.run(drop_all_schema())
        else:
            print("Cancelled.")
    else:
        asyncio.run(run_migration(include_chunks=True))