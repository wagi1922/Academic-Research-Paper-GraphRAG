#!/usr/bin/env python3
"""Re-embed all chunks with OpenRouter FREE embedding models.
DEPRECATED: This script used local sentence-transformers. Use openrouter_reembed_chunks.py instead.
"""
import asyncio
import logging
from neo4j import AsyncGraphDatabase
# from sentence_transformers import SentenceTransformer  # REMOVED - local model not allowed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "graphrag123"

# Use OpenRouter FREE embedding models (via OpenAI-compatible API)
# pip install openai
from openai import AsyncOpenAI
import os

# OpenRouter FREE models:
# - nomic-embed-text-v1.5:free (768 dim) -> API pakai nomic-embed-text-v1.5
# - inclusionai/ling-3.2-flash:free (1024 dim)
MODEL_NAME = "nomic-embed-text-v1.5"  # Free OpenRouter model (tanpa :free suffix)
BATCH_SIZE = 100

async def reembed_chunks():
    # Use OpenRouter API
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable required")
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    logger.info(f"Using OpenRouter model: {MODEL_NAME}")

    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    async with driver.session() as session:
        # Get all chunk IDs and texts
        result = await session.run("""
            MATCH (c:Chunk)
            RETURN c.id as id, c.text as text
            ORDER BY c.id
        """)
        
        chunks = []
        async for record in result:
            chunks.append({"id": record["id"], "text": record["text"]})
        
        logger.info(f"Found {len(chunks)} chunks to re-embed")
        
        # Process in batches
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            texts = [c["text"] for c in batch]
            
            # Generate embeddings via OpenRouter
            response = await client.embeddings.create(
                model=MODEL_NAME,
                input=texts,
            )
            embeddings = [d.embedding for d in response.data]
            
            # Update Neo4j
            update_data = []
            for j, chunk in enumerate(batch):
                update_data.append({
                    "id": chunk["id"],
                    "embedding": embeddings[j]
                })
            
            await session.run("""
                UNWIND $data AS d
                MATCH (c:Chunk {id: d.id})
                SET c.embedding = d.embedding
            """, data=update_data)
            
            logger.info(f"Re-embedded batch {i//BATCH_SIZE + 1}/{(len(chunks) + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} chunks)")
    
    await driver.close()
    logger.info("Re-embedding complete!")

if __name__ == "__main__":
    asyncio.run(reembed_chunks())