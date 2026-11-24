#!/usr/bin/env python3
"""
Experiment E4: Ablation Study - Focused Version
Test contribution of each GraphRAG component with subset of queries.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
import httpx
import yaml

sys.path.insert(0, '/home/guard/Documents/perkuliahan/sem 7/Cap/backend')


async def run_query(client, query, config_name, config):
    start = time.perf_counter()
    try:
        top_k = config.get("top_k", 5)
        depth = config.get("depth", 2)
        use_vector = config.get("use_vector", True)
        use_graph = config.get("use_graph", True)
        use_citation_validation = config.get("citation_validation", True)
        
        # For ablation, map configs to API params
        if config_name == "vector_only":
            depth = 0
        elif config_name == "graph_only_seeded":
            top_k = 0
        
        response = await client.post(
            "http://localhost:8000/api/v1/query/",
            json={"query": query, "top_k": top_k, "depth": depth},
            timeout=180.0
        )
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code == 200:
            data = response.json()
            data["latency_ms"] = latency_ms
            data["config"] = config_name
            return data
        return {"error": True, "latency_ms": latency_ms, "config": config_name}
    except Exception as e:
        return {"error": True, "latency_ms": (time.perf_counter() - start) * 1000, "msg": str(e), "config": config_name}


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


async def test_config(config_name, config, test_queries, results_dir, client):
    print(f"\n=== Testing config: {config_name} ===")
    print(f"    {config.get('description', '')}")
    
    combo_results = []
    for i, qa in enumerate(test_queries):
        print(f"  Query {i+1}/{len(test_queries)}: {qa['question'][:50]}...")
        
        api_result = await run_query(client, qa["question"], config_name, config)
        
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
            "config": config_name,
            "answer": api_result.get("answer", ""),
            "sources": api_result.get("sources", []),
            "graph_paths": api_result.get("graph_path", []),
            **metrics
        }
        
        combo_results.append(result)
        print(f"    Latency: {metrics['latency_ms']:.0f}ms, Grounding: {metrics['grounding_score']:.2f}, Cites: {metrics['valid_citations']}/{metrics['total_citations']}")
        
        await asyncio.sleep(0.5)
    
    # Save results
    config_file = results_dir / f"results_{config_name}.json"
    with open(config_file, "w") as f:
        json.dump(combo_results, f, indent=2, ensure_ascii=False)
    
    return combo_results


async def main():
    # Load config
    config_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/config/e4_ablation.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Load QA pairs
    qa_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/qa_pairs.json")
    with open(qa_path) as f:
        qa_pairs = json.load(f)
    
    test_queries = qa_pairs[:10]  # 10 test queries for focused run
    
    # Key configurations for ablation
    configurations = [
        cfg for cfg in config["configurations"] 
        if cfg["name"] in ["full_graphrag", "vector_only", "vector_plus_graph", "no_citation_validation"]
    ]
    
    results_dir = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/results/e4_ablation_focused")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient() as client:
        all_results = {}
        
        for cfg in configurations:
            config_name = cfg["name"]
            config_data = cfg
            
            results = await test_config(config_name, config_data, test_queries, results_dir, client)
            
            # Aggregate
            if results:
                agg = {
                    "config": config_name,
                    "description": config_data.get("description", ""),
                    "enabled": config_data.get("enabled", {}),
                    "num_queries": len(results),
                    "avg_latency_ms": sum(r["latency_ms"] for r in results) / len(results),
                    "avg_grounding_score": sum(r["grounding_score"] for r in results) / len(results),
                    "avg_citation_accuracy": sum(r["citation_accuracy"] for r in results) / len(results),
                    "avg_citation_coverage": sum(r["citation_coverage"] for r in results) / len(results),
                    "avg_graph_paths": sum(r["graph_paths"] for r in results) / len(results),
                    "avg_vector_results": sum(r["vector_results"] for r in results) / len(results),
                    "avg_valid_citations": sum(r["valid_citations"] for r in results) / len(results),
                    "avg_total_citations": sum(r["total_citations"] for r in results) / len(results),
                }
                all_results[config_name] = agg
                print(f"  AVG: Latency={agg['avg_latency_ms']:.0f}ms, Grounding={agg['avg_grounding_score']:.2f}, CiteAcc={agg['avg_citation_accuracy']:.2f}, Cov={agg['avg_citation_coverage']:.2f}")
        
        # Save summary
        summary_file = results_dir / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== E4 Ablation Focused Experiment Complete ===")
        print(f"Results saved to {results_dir}")
        
        # Print comparison table
        print("\n=== ABLATION SUMMARY ===")
        print(f"{'Config':<30} {'Latency':>10} {'Grounding':>10} {'CiteAcc':>10} {'Coverage':>10} {'Paths':>6}")
        print("-" * 80)
        for name, agg in all_results.items():
            print(f"{name:<30} {agg['avg_latency_ms']:>10.0f} {agg['avg_grounding_score']:>10.2f} {agg['avg_citation_accuracy']:>10.2f} {agg['avg_citation_coverage']:>10.2f} {agg['avg_graph_paths']:>6.1f}")


if __name__ == "__main__":
    asyncio.run(main())