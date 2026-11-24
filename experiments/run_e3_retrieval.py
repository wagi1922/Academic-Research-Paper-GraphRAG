#!/usr/bin/env python3
"""
Experiment E3: Retrieval Parameter Sweep
Tests different top_k and depth combinations against the GraphRAG API.
"""

import asyncio
import json
import time
import os
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import httpx
import yaml

# Add backend to path
sys.path.insert(0, '/home/guard/Documents/perkuliahan/sem 7/Cap/backend')

from app.core.config import settings


@dataclass
class ExperimentResult:
    query: str
    expected_answer: str
    expected_paper_titles: List[str]
    category: str
    difficulty: str
    top_k: int
    depth: int
    answer: str
    sources: List[Dict]
    graph_paths: List
    latency_ms: float
    grounding_score: float
    valid_citations: int
    total_citations: int
    token_usage: Dict = None


async def run_query(
    client: httpx.AsyncClient,
    query: str,
    top_k: int,
    depth: int,
    base_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    """Run a single query against the GraphRAG API."""
    start = time.perf_counter()
    try:
        response = await client.post(
            f"{base_url}/api/v1/query/",
            json={"query": query, "top_k": top_k, "depth": depth},
            timeout=60.0
        )
        latency_ms = (time.perf_counter() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            data["latency_ms"] = latency_ms
            return data
        else:
            return {
                "answer": f"API Error: {response.status_code}",
                "sources": [],
                "graph_path": [],
                "extracted_entities": {},
                "retrieval_metadata": {},
                "latency_ms": latency_ms,
                "error": True
            }
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "answer": f"Request failed: {str(e)}",
            "sources": [],
            "graph_path": [],
            "extracted_entities": {},
            "retrieval_metadata": {},
            "latency_ms": latency_ms,
            "error": True
        }


def compute_metrics(
    answer: str,
    expected: str,
    sources: List[Dict],
    expected_titles: List[str],
    retrieval_meta: Dict
) -> Dict[str, float]:
    """Compute evaluation metrics for a single query."""
    metrics = {}
    
    # Citation accuracy: check if cited sources match expected papers
    cited_paper_ids = {s.get("paper_id", "") for s in sources}
    expected_paper_ids = set()
    for title in expected_titles:
        expected_paper_ids.add(title)  # Using titles as IDs for matching
    
    # Simple matching - check if any expected title appears in sources
    matched = 0
    for src in sources:
        src_title = src.get("title", "").lower()
        for exp_title in expected_titles:
            if exp_title.lower() in src_title or src_title in exp_title.lower():
                matched += 1
                break
    
    metrics["citation_accuracy"] = matched / len(sources) if sources else 0.0
    metrics["citation_coverage"] = matched / len(expected_titles) if expected_titles else 0.0
    
    # Grounding score from API
    metrics["grounding_score"] = retrieval_meta.get("grounding_score", 0.0)
    
    # Latency
    metrics["latency_ms"] = retrieval_meta.get("latency_ms", 0.0)
    
    # Token usage (approximate)
    token_input = len(answer.split()) * 1.3  # rough estimate
    token_output = len(answer.split()) * 1.3
    metrics["tokens_input"] = token_input
    metrics["tokens_output"] = token_output
    
    # Graph utilization
    metrics["graph_paths"] = retrieval_meta.get("graph_paths", 0)
    metrics["vector_results"] = retrieval_meta.get("vector_results", 0)
    metrics["chunk_results"] = retrieval_meta.get("chunk_results", 0)
    
    return metrics


async def run_experiment():
    # Load config
    config_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/config/e3_retrieval_params.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Load QA pairs
    qa_path = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/qa_pairs.json")
    with open(qa_path) as f:
        qa_pairs = json.load(f)
    
    # Filter test queries (use all for now)
    test_queries = qa_pairs[:config["evaluation"]["test_queries"]]
    
    # Get parameter combinations
    combinations = config["retrieval_params"]["combinations"]
    
    results_dir = Path(config["output"]["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient() as client:
        all_results = []
        
        for combo in combinations:
            top_k = combo["top_k"]
            depth = combo["depth"]
            combo_name = f"topk{top_k}_depth{depth}"
            
            print(f"\n=== Running {combo_name} ===")
            
            combo_results = []
            for i, qa in enumerate(test_queries):
                print(f"  Query {i+1}/{len(test_queries)}: {qa['question'][:60]}...")
                
                api_result = await run_query(client, qa["question"], top_k, depth)
                
                metrics = compute_metrics(
                    answer=api_result.get("answer", ""),
                    expected=qa["answer"],
                    sources=api_result.get("sources", []),
                    expected_titles=qa.get("paper_titles", []),
                    retrieval_meta=api_result.get("retrieval_metadata", {})
                )
                
                result = ExperimentResult(
                    query=qa["question"],
                    expected_answer=qa["answer"],
                    expected_paper_titles=qa.get("paper_titles", []),
                    category=qa.get("category", ""),
                    difficulty=qa.get("difficulty", ""),
                    top_k=top_k,
                    depth=depth,
                    answer=api_result.get("answer", ""),
                    sources=api_result.get("sources", []),
                    graph_paths=api_result.get("graph_path", []),
                    latency_ms=api_result.get("latency_ms", 0),
                    grounding_score=api_result.get("retrieval_metadata", {}).get("grounding_score", 0),
                    valid_citations=api_result.get("retrieval_metadata", {}).get("valid_citations", 0),
                    total_citations=api_result.get("retrieval_metadata", {}).get("total_citations", 0),
                    token_usage={"input": metrics["tokens_input"], "output": metrics["tokens_output"]}
                )
                
                # Add computed metrics
                result_dict = asdict(result)
                result_dict.update(metrics)
                combo_results.append(result_dict)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            # Save combo results
            combo_file = results_dir / f"results_{combo_name}.json"
            with open(combo_file, "w") as f:
                json.dump(combo_results, f, indent=2, ensure_ascii=False)
            
            # Aggregate metrics
            agg = {
                "combo": combo_name,
                "top_k": top_k,
                "depth": depth,
                "num_queries": len(combo_results),
                "avg_latency_ms": sum(r["latency_ms"] for r in combo_results) / len(combo_results),
                "avg_grounding_score": sum(r["grounding_score"] for r in combo_results) / len(combo_results),
                "avg_citation_accuracy": sum(r["citation_accuracy"] for r in combo_results) / len(combo_results),
                "avg_citation_coverage": sum(r["citation_coverage"] for r in combo_results) / len(combo_results),
                "avg_graph_paths": sum(r["graph_paths"] for r in combo_results) / len(combo_results),
                "avg_vector_results": sum(r["vector_results"] for r in combo_results) / len(combo_results),
            }
            
            all_results.append(agg)
            print(f"  Avg latency: {agg['avg_latency_ms']:.0f}ms, Grounding: {agg['avg_grounding_score']:.2f}, Citation Acc: {agg['avg_citation_accuracy']:.2f}")
        
        # Save summary
        summary_file = results_dir / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== E3 Experiment Complete ===")
        print(f"Results saved to {results_dir}")
        print(f"Summary: {summary_file}")


if __name__ == "__main__":
    asyncio.run(run_experiment())