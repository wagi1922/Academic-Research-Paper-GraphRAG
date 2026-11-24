#!/usr/bin/env python3
"""
Re-index Neo4j embeddings using local SentenceTransformers (MiniLM-L6-v2, 384-d).

Covers BOTH vector indexes:
  - chunk_vector_idx  (Chunk.embedding, 384-d, cosine)
  - paper_vector_idx  (Paper.embedding,  384-d, cosine)  <- added: paper-level retrieval

Drops existing indexes, recreates them, embeds all chunks and papers in batches.
Papers embedded from title + abstract (abstract = first 2000 chars of full text).
"""
import asyncio
import logging

from neo4j import AsyncGraphDatabase
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "graphrag123"

MODEL_NAME = "all-MiniLM-L6-v2"  # 384 dimensions
BATCH_SIZE = 64
DIMENSIONS = 384
CHUNK_INDEX = "chunk_vector_idx"
PAPER_INDEX = "paper_vector_idx"


async def get_rows(driver, query):
    async with driver.session() as session:
        result = await session.run(query)
        return await result.data()


async def drop_index(driver, name):
    async with driver.session() as session:
        await session.run(f"DROP INDEX {name} IF EXISTS")
    logger.info(f"Dropped index (if existed): {name}")


async def create_vector_index(driver, label, prop, name):
    async with driver.session() as session:
        await session.run(f"""
            CREATE VECTOR INDEX {name} IF NOT EXISTS
            FOR (n:{label}) ON (n.{prop})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {DIMENSIONS},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
        """)
    logger.info(f"Created vector index {name} on {label}.{prop}")


async def embed_chunks(driver, model):
    rows = await get_rows(driver, "MATCH (c:Chunk) RETURN c.id AS id, c.text AS text ORDER BY c.id")
    logger.info(f"Embedding {len(rows)} chunks")
    ids = [r["id"] for r in rows]
    texts = [r["text"] for r in rows]
    for i in range(0, len(rows), BATCH_SIZE):
        batch_ids = ids[i:i + BATCH_SIZE]
        vecs = model.encode(texts[i:i + BATCH_SIZE], normalize_embeddings=True, show_progress_bar=False)
        params = [{"id": cid, "emb": v.tolist()} for cid, v in zip(batch_ids, vecs)]
        async with driver.session() as session:
            await session.run(
                "UNWIND $params AS p MATCH (c:Chunk {id: p.id}) SET c.embedding = p.emb",
                params=params,
            )
        logger.info(f"  chunks {i + 1}..{min(i + BATCH_SIZE, len(rows))} done")


async def embed_papers(driver, model):
    rows = await get_rows(driver, "MATCH (p:Paper) RETURN p.id AS id, p.title AS title, p.abstract AS abstract ORDER BY p.id")
    logger.info(f"Embedding {len(rows)} papers")
    params = []
    for r in rows:
        text = f"{r['title']}. {r['abstract'] or ''}"
        vec = model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0].tolist()
        params.append({"id": r["id"], "emb": vec})
    async with driver.session() as session:
        await session.run(
            "UNWIND $params AS p MATCH (paper:Paper {id: p.id}) SET paper.embedding = p.emb",
            params=params,
        )


async def main():
    logger.info(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info(f"Model loaded: {model.get_sentence_embedding_dimension()} dimensions")

    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    try:
        async with driver.session() as session:
            await session.run("RETURN 1")
        logger.info("Neo4j connected")

        await drop_index(driver, CHUNK_INDEX)
        await drop_index(driver, PAPER_INDEX)
        await create_vector_index(driver, "Chunk", "embedding", CHUNK_INDEX)
        await create_vector_index(driver, "Paper", "embedding", PAPER_INDEX)

        await embed_chunks(driver, model)
        await embed_papers(driver, model)

        # Verify + smoke-test both indexes
        async with driver.session() as session:
            for label, idx in (("Chunk", CHUNK_INDEX), ("Paper", PAPER_INDEX)):
                cnt = await session.run(
                    f"MATCH (n:{label}) WHERE n.embedding IS NOT NULL RETURN count(n) AS cnt"
                )
                logger.info(f"{label} with embeddings: {(await cnt.single())['cnt']}")
            test_emb = model.encode(["graphrag attack evaluation"])[0].tolist()
            for idx, alias in ((CHUNK_INDEX, "chunk"), (PAPER_INDEX, "paper")):
                res = await session.run(
                    f"CALL db.index.vector.queryNodes('{idx}', 3, $emb) YIELD node, score "
                    f"RETURN node.id AS id, score",
                    emb=test_emb,
                )
                rows = await res.data()
                logger.info(f"Vector search test [{alias}]: {len(rows)} hits -> "
                            + ", ".join(f"{r['id'][:24]}:{r['score']:.3f}" for r in rows))

        logger.info("Re-index complete (chunks + papers)!")
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(main())
