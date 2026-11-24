#!/usr/bin/env python3
"""
Quick E3 test: 3 queries × 3 combos
"""

import asyncio
import json
import time
import sys
from pathlib import Path
import httpx
import yaml

sys.path.insert(0, '/home/guard/Documents/perkuliahan/sem 7/Cap/backend')


async def run_query(client, query, top_k, depth):
    start = time.perf_counter()
    try:
        response = await client.post(
            "http://localhost:8000/api/v1/query/",
            json={"query": query, "top_k": top_k, "depth": depth},
            timeout=60.0
        )
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code == 200:
            data = response.json()
            data["latency_ms"] = latency_ms
            return data
        return {"error": True, "latency_ms": latency_ms}
    except Exception as e:
        return {"error": True, "latency_ms": (time.perf_counter() - start) * 1000, "msg": str(e)}


async def main():
    # Load QA pairs
    qa_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/qa_pairs.json")
    with open(qa_path) as f:
        qa_pairs = json.load(f)
    
    # Test subset: 3 queries
    test_queries = qa_pairs[:3]
    
    # Test subset: 3 combos
    combos = [
        {"top_k": 5, "depth": 1},
        {"top_k": 5, "depth": 2},
        {"top_k": 10, "depth": 2},
    ]
    
    async with httpx.AsyncClient() as client:
        for combo in combos:
            top_k = combo["top_k"]
            depth = combo["depth"]
            print(f"\n=== top_k={top_k}, depth={depth} ===")
            
            for qa in test_queries:
                q = qa["question"]
                print(f"  Q: {q[:50]}...")
                result = await run_query(client, q, top_k, depth)
                
                if result.get("error"):
                    print(f"    ERROR: {result.get('msg', 'API error')}")
                else:
                    meta = result.get("retrieval_metadata", {})
                    print(f"    Latency: {result['latency_ms']:.0f}ms")
                    print(f"    Grounding: {meta.get('grounding_score', 0):.2f}")
                    print(f"    Valid cites: {meta.get('valid_citations', 0)}/{meta.get('total_citations', 0)}")
                    print(f"    Graph paths: {meta.get('graph_paths', 0)}")
                    print(f"    Vector results: {meta.get('vector_results', 0)}")
                    print(f"    Chunk results: {meta.get('chunk_results', 0)}")
                
                await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())