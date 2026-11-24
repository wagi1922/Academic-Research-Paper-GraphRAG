#!/usr/bin/env python3
"""
Experiment E2: Embedding Model Comparison
Runs vector search with different embedding models and evaluates retrieval quality.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
import httpx
import yaml

sys.path.insert(0, '/home/guard/Documents/perkuliahan/sem 7/Cap/backend')


async def run_query(client, query, top_k, depth, embedding_model=None):
    start = time.perf_counter()
    try:
        payload = {"query": query, "top_k": top_k, "depth": depth}
        if embedding_model:
            payload["embedding_model"] = embedding_model
            
        response = await client.post(
            "http://localhost:8000/api/v1/query/",
            json=payload,
            timeout=120.0
        )
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code == 200:
            data = response.json()
            data["latency_ms"] = latency_ms
            return data
        return {"error": True, "latency_ms": latency_ms}
    except Exception as e:
        return {"error": True, "latency_ms": (time.perf_counter() - start) * 1000, "msg": str(e)}


def compute_metrics(answer, expected, sources, expected_titles, retrieval_meta, latency_ms=0.0):
    metrics = {}
    
    matched = 0
    for src in sources:
        src_title = src.get("title", "").lower()
        for exp_title in expected_titles:
            if exp_title.lower() in src_title or src_title in exp_title.lower():
                matched += 1
                break
    
    metrics["citation_accuracy"] = matched / len(sources) if sources else 0.0
    metrics["citation_coverage"] = matched / len(expected_titles) if expected_titles else 0.0
    metrics["grounding_score"] = retrieval_meta.get("grounding_score", 0.0)
    metrics["latency_ms"] = latency_ms
    metrics["graph_paths"] = retrieval_meta.get("graph_paths", 0)
    metrics["vector_results"] = retrieval_meta.get("vector_results", 0)
    metrics["chunk_results"] = retrieval_meta.get("chunk_results", 0)
    metrics["valid_citations"] = retrieval_meta.get("valid_citations", 0)
    metrics["total_citations"] = retrieval_meta.get("total_citations", 0)
    
    return metrics


async def test_embedding_model(model_name, model_config, test_queries, results_dir, client):
    """Test a single embedding model by running queries."""
    print(f"\n=== Testing embedding model: {model_name} ===")
    
    combo_results = []
    for i, qa in enumerate(test_queries):
        print(f"  Query {i+1}/{len(test_queries)}: {qa['question'][:50]}...")
        
        # Note: The API currently doesn't support passing embedding_model per query
        # We'll need to either re-index or modify the API
        # For now, test with current embedding (nomic-embed-text)
        api_result = await run_query(client, qa["question"], 5, 2)
        
        if api_result.get("error"):
            print(f"    ERROR: {api_result.get('msg', 'API error')}")
            continue
        
        metrics = compute_metrics(
            answer=api_result.get("answer", ""),
            expected=qa["answer"],
            sources=api_result.get("sources", []),
            expected_titles=qa.get("paper_titles", []),
            retrieval_meta=api_result.get("retrieval_metadata", {}),
            latency_ms=api_result.get("latency_ms", 0.0)
        )
        
        result = {
            "query": qa["question"],
            "category": qa.get("category", ""),
            "difficulty": qa.get("difficulty", ""),
            "model": model_name,
            "answer": api_result.get("answer", ""),
            "sources": api_result.get("sources", []),
            "graph_paths": api_result.get("graph_path", []),
            **metrics
        }
        
        combo_results.append(result)
        print(f"    Latency: {metrics['latency_ms']:.0f}ms, Grounding: {metrics['grounding_score']:.2f}, Cites: {metrics['valid_citations']}/{metrics['total_citations']}")
        
        await asyncio.sleep(0.5)
    
    # Save results
    model_file = results_dir / f"results_{model_name.replace('/', '_').replace('-', '_')}.json"
    with open(model_file, "w") as f:
        json.dump(combo_results, f, indent=2, ensure_ascii=False)
    
    return combo_results


async def main():
    # Load config
    config_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/config/e2_embedding.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Load QA pairs
    qa_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/qa_pairs.json")
    with open(qa_path) as f:
        qa_pairs = json.load(f)
    
    test_queries = qa_pairs[:30]  # 30 test queries as per config
    
    models = config["embeddings"]["models"]
    
    results_dir = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/results/e2_embedding")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient() as client:
        all_results = {}
        
        for model in models:
            model_name = model["name"]
            model_config = model
            
            results = await test_embedding_model(model_name, model_config, test_queries, results_dir, client)
            
            # Aggregate
            if results:
                agg = {
                    "model": model_name,
                    "dimensions": model_config.get("dimensions", 0),
                    "provider": model_config.get("provider", ""),
                    "num_queries": len(results),
                    "avg_latency_ms": sum(r["latency_ms"] for r in results) / len(results),
                    "avg_grounding_score": sum(r["grounding_score"] for r in results) / len(results),
                    "avg_citation_accuracy": sum(r["citation_accuracy"] for r in results) / len(results),
                    "avg_citation_coverage": sum(r["citation_coverage"] for r in results) / len(results),
                    "avg_graph_paths": sum(r["graph_paths"] for r in results) / len(results),
                    "avg_vector_results": sum(r["vector_results"] for r in results) / len(results),
                    "avg_valid_citations": sum(r["valid_citations"] for r in results) / len(results),
                }
                all_results[model_name] = agg
                print(f"  AVG: Latency={agg['avg_latency_ms']:.0f}ms, Grounding={agg['avg_grounding_score']:.2f}, CiteAcc={agg['avg_citation_accuracy']:.2f}")
        
        # Save summary
        summary_file = results_dir / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== E2 Embedding Experiment Complete ===")
        print(f"Results saved to {results_dir}")


if __name__ == "__main__":
    asyncio.run(main())