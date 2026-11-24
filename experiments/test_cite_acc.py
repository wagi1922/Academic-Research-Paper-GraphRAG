#!/usr/bin/env python3
"""Test citation accuracy with few-shot prompt fix.
Run when OpenRouter credits available.
"""
import os
import sys
import asyncio
import json
import re
from neo4j import AsyncGraphDatabase
from openai import AsyncOpenAI

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.retrieval.context_builder import ContextBuilder, RetrievalContext, build_prompt_with_citations
from app.schemas.entities import ExtractedEntities

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "graphrag123"

# Test queries with expected Paper IDs (gold set sample)
TEST_QUERIES = [
    {
        "query": "What is the RawBMamba model for audio deepfake detection?",
        "expected_paper_ids": ["2406.06086v2"]
    },
    {
        "query": "Which datasets are used for audio deepfake detection experiments in RawBMamba?",
        "expected_paper_ids": ["2406.06086v2"]
    },
    {
        "query": "How does Mamba architecture help in audio deepfake detection?",
        "expected_paper_ids": ["2406.06086v2"]
    },
    {
        "query": "What is the frontend feature extractor used in RawBMamba?",
        "expected_paper_ids": ["2406.06086v2"]
    },
    {
        "query": "How does the bidirectional feature fusion module work in RawBMamba?",
        "expected_paper_ids": ["2406.06086v2"]
    },
    {
        "query": "What are the training configurations for RawBMamba model?",
        "expected_paper_ids": ["2406.06086v2"]
    },
    {
        "query": "What is the sampling rate and input length for RawBMamba training?",
        "expected_paper_ids": ["2406.06086v2"]
    },
    {
        "query": "How does RawBMamba achieve end-to-end audio deepfake detection?",
        "expected_paper_ids": ["2406.06086v2"]
    },
]

async def retrieve_context(query: str) -> RetrievalContext:
    """Retrieve context from Neo4j for query."""
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # Extract keywords from query (simple approach: remove stop words, keep nouns/terms)
    import re
    stop_words = {'what', 'is', 'the', 'for', 'in', 'of', 'a', 'an', 'and', 'or', 'to', 'how', 'does', 'which', 'are', 'used', 'model', 'help', 'detection'}
    # Remove punctuation, split, filter
    words = re.findall(r'\b\w+\b', query.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    search_query = ' '.join(keywords[:5])
    
    # Fallback: if no keywords, use original query
    if not search_query:
        search_query = query
    
    # Use case-insensitive CONTAINS by converting both to lowercase
    # We'll do multiple searches with individual keywords for better recall
    search_terms = keywords[:3]  # Top 3 keywords
    
    # Simple vector search (placeholder - use actual retrieval pipeline)
    async with driver.session() as session:
        # Get chunks - try multiple search terms
        all_chunks = []
        for term in search_terms:
            result = await session.run("""
                MATCH (c:Chunk)
                WHERE toLower(c.text) CONTAINS toLower($search_term)
                RETURN c.id as id, c.text as text, c.paper_id as paper_id, 
                       c.title as title, 1.0 as score
                LIMIT 5
            """, search_term=term)
            
            async for record in result:
                chunk_data = {
                    "id": record["id"],
                    "text": record["text"],
                    "paper_id": record["paper_id"],
                    "title": record["title"],
                    "score": record["score"]
                }
                # Avoid duplicates
                if not any(c["id"] == chunk_data["id"] for c in all_chunks):
                    all_chunks.append(chunk_data)
        
        chunks = all_chunks[:8]
        
        # Get seed papers
        result = await session.run("""
            MATCH (p:Paper)
            WHERE toLower(p.title) CONTAINS toLower($search_query) OR toLower(p.abstract) CONTAINS toLower($search_query)
            RETURN p.paper_id as paper_id, p.title as title, p.year as year, p.doi as doi, 1.0 as score
            LIMIT 5
        """, search_query=search_query)
        
        seed_papers = []
        async for record in result:
            seed_papers.append({
                "paper_id": record["paper_id"],
                "title": record["title"],
                "year": record["year"],
                "doi": record["doi"],
                "score": record["score"]
            })
    
    await driver.close()
    
    return RetrievalContext(
        vector_chunks=chunks,
        graph_paths=[],
        extracted_entities=ExtractedEntities(),
        seed_papers=seed_papers
    )

async def test_cite_acc():
    """Test citation accuracy with current prompt."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    builder = ContextBuilder()
    results = []
    
    for i, test in enumerate(TEST_QUERIES):
        print(f"\n=== Testing: {test['query']} ===")
        
        context = await retrieve_context(test['query'])
        context_dict = builder.build(context)
        prompt = build_prompt_with_citations(context_dict, test['query'])
        
        print(f"Prompt length: {len(prompt)} chars")
        
        # Call LLM with retry for rate limit
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model="inclusionai/ling-3.2-flash:free",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
                break
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    wait_time = 10 * (attempt + 1)
                    print(f"Rate limited, waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        else:
            raise Exception("Max retries exceeded for rate limit")
        
        answer = response.choices[0].message.content or ""
        print(f"Answer: {answer}")
        
        # Check citation format
        citations = re.findall(r'\[([^\]]+)\]', answer)
        print(f"Citations found: {citations}")
        
        # Validate: every sentence should have citation
        # Better sentence split: keep delimiter
        sentences = re.split(r'(?<=[.!?])\s+', answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        cited_sentences = 0
        for sent in sentences:
            if re.search(r'\[[^\]]+\]', sent):
                cited_sentences += 1
        
        cite_acc = cited_sentences / len(sentences) if sentences else 0
        print(f"Sentences: {len(sentences)}, Cited: {cited_sentences}, cite_acc: {cite_acc:.2f}")
        
        results.append({
            "query": test['query'],
            "answer": answer,
            "citations": citations,
            "cite_acc": cite_acc,
            "sentences": len(sentences),
            "cited_sentences": cited_sentences
        })
    
    # Summary
    avg_cite_acc = sum(r['cite_acc'] for r in results) / len(results)
    print(f"\n=== SUMMARY ===")
    print(f"Average cite_acc: {avg_cite_acc:.2f}")
    print(f"Target: 0.85")
    print(f"Status: {'PASS' if avg_cite_acc >= 0.85 else 'FAIL'}")
    
    # Save results
    with open("experiments/results/cite_acc_test.json", "w") as f:
        json.dump({
            "avg_cite_acc": avg_cite_acc,
            "target": 0.85,
            "passed": avg_cite_acc >= 0.85,
            "details": results
        }, f, indent=2)

if __name__ == "__main__":
    asyncio.run(test_cite_acc())