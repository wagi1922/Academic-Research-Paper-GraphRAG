#!/usr/bin/env python3
"""Backfill embeddings for existing papers and chunks in Neo4j."""
import asyncio
import sys
sys.path.insert(0, "/home/guard/Documents/perkuliahan/sem 7/Cap/backend")

from app.ingestion.embedding_service import EmbeddingService, get_embedding_service
from app.core.neo4j_driver import get_neo4j_session
from app.core.config import settings


async def backfill_paper_embeddings():
    """Generate embeddings for papers that don't have them."""
    service = await get_embedding_service()
    if not service:
        print("No OpenRouter API key configured, skipping paper embeddings")
        return

    async for session in get_neo4j_session():
        # Find papers without embeddings
        query = """
        MATCH (p:Paper)
        WHERE p.embedding IS NULL AND p.abstract IS NOT NULL
        RETURN p.id as paper_id, p.title as title, p.abstract as abstract
        LIMIT 100
        """
        result = await session.run(query)
        papers = [dict(record) async for record in result]

        print(f"Found {len(papers)} papers without embeddings")

        for paper in papers:
            try:
                text = f"{paper['title']}. {paper['abstract']}"
                embedding = await service.embed_text(text)

                # Update paper with embedding
                update_query = """
                MATCH (p:Paper {id: $paper_id})
                SET p.embedding = $embedding
                RETURN p.id
                """
                await session.run(update_query, paper_id=paper['paper_id'], embedding=embedding)
                print(f"  Updated: {paper['title'][:60]}")
            except Exception as e:
                print(f"  Error for {paper['title'][:60]}: {e}")

        print("Paper embeddings backfill complete")


async def backfill_chunk_embeddings():
    """Generate embeddings for chunks that don't have them."""
    service = await get_embedding_service()
    if not service:
        print("No OpenRouter API key configured, skipping chunk embeddings")
        return

    async for session in get_neo4j_session():
        # Find chunks without embeddings
        query = """
        MATCH (c:Chunk)
        WHERE c.embedding IS NULL AND c.text IS NOT NULL
        RETURN c.id as chunk_id, c.text as text
        LIMIT 500
        """
        result = await session.run(query)
        chunks = [dict(record) async for record in result]

        print(f"Found {len(chunks)} chunks without embeddings")

        # Process in batches
        batch_size = 20
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c['text'] for c in batch]

            try:
                embeddings = await service.embed_batch(texts)

                # Update each chunk
                for chunk, embedding in zip(batch, embeddings):
                    update_query = """
                    MATCH (c:Chunk {id: $chunk_id})
                    SET c.embedding = $embedding
                    RETURN c.id
                    """
                    await session.run(update_query, chunk_id=chunk['chunk_id'], embedding=embedding)

                print(f"  Updated batch {i//batch_size + 1}: {len(batch)} chunks")
            except Exception as e:
                print(f"  Error in batch {i//batch_size + 1}: {e}")

        print("Chunk embeddings backfill complete")


async def main():
    print("Starting embedding backfill...")
    print(f"Using model: {settings.embedding_model}")
    print(f"API key configured: {'Yes' if settings.openrouter_api_key else 'No'}")

    await backfill_paper_embeddings()
    await backfill_chunk_embeddings()

    print("Backfill complete!")


if __name__ == "__main__":
    asyncio.run(main())