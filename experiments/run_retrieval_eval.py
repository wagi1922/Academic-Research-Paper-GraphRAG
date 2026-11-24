#!/usr/bin/env python3
"""Retrieval Evaluation using local embeddings.
Queries Neo4j vector index directly, bypassing API and OpenRouter key limit."""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from neo4j import AsyncGraphDatabase
from experiments.local_embedding_service import get_embedding_service


@dataclass
class RetrievalResult:
    query: str
    top_k: int
    depth: int
    vector_results: int
    chunk_results: int
    graph_paths: int
    seed_papers: List[str]
    latency_ms: float


@dataclass
class ExperimentConfig:
    name: str
    top_k: int
    depth: int


class RetrievalEvaluator:
    """Evaluates retrieval performance using local embeddings."""

    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "graphrag123",
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.embedding_service = get_embedding_service("local")
        self.embedding_model = "all-MiniLM-L6-v2"

    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password),
        )

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def search_papers(self, query_embedding: List[float], top_k: int, min_score: float = 0.0) -> List[Dict]:
        """Search papers by embedding similarity."""
        query = """
        CALL db.index.vector.queryNodes('paper_vector_idx', $top_k, $embedding)
        YIELD node, score
        WHERE score >= $min_score
        RETURN node.id as paper_id, node.title as title, node.abstract as abstract,
               node.year as year, node.doi as doi, node.venue as venue,
               node.keywords as keywords, score
        ORDER BY score DESC
        """
        async with self.driver.session() as session:
            result = await session.run(query, top_k=top_k, embedding=query_embedding, min_score=min_score)
            return [dict(record) async for record in result]

    async def search_chunks(self, query_embedding: List[float], top_k: int, min_score: float = 0.0, paper_ids: List[str] = None) -> List[Dict]:
        """Search chunks by embedding similarity."""
        base_query = """
        CALL db.index.vector.queryNodes('chunk_vector_idx', $top_k, $embedding)
        YIELD node, score
        WHERE score >= $min_score
        """
        if paper_ids:
            base_query += " AND node.paper_id IN $paper_ids "

        base_query += """
        RETURN node.id as chunk_id, node.paper_id as paper_id, node.text as text,
               node.chunk_index as chunk_index, node.metadata as metadata, score
        ORDER BY score DESC
        """

        params = {"top_k": top_k, "embedding": query_embedding, "min_score": min_score}
        if paper_ids:
            params["paper_ids"] = paper_ids

        async with self.driver.session() as session:
            result = await session.run(base_query, params)
            return [dict(record) async for record in result]

    async def traverse_graph(self, seed_paper_ids: List[str], depth: int, max_nodes_per_hop: int = 50) -> List[Dict]:
        """Traverse citation graph from seed papers."""
        if depth <= 0 or not seed_paper_ids:
            return []

        paths = []
        current_papers = seed_paper_ids
        visited = set(seed_paper_ids)

        for hop in range(depth):
            if not current_papers:
                break

            # Query for outgoing CITES edges
            query = """
            MATCH (p:Paper)-[r:CITES]->(cited:Paper)
            WHERE p.id IN $paper_ids
            RETURN p.id as source, type(r) as relation, cited.id as target,
                   'Paper' as source_type, 'Paper' as target_type
            LIMIT $limit
            """
            async with self.driver.session() as session:
                result = await session.run(query, paper_ids=current_papers, limit=max_nodes_per_hop)
                hop_paths = [dict(record) async for record in result]
                paths.extend(hop_paths)

                # Get next hop papers
                next_papers = [p["target"] for p in hop_paths if p["target"] not in visited]
                current_papers = next_papers
                visited.update(next_papers)

        return paths

    async def evaluate_query(
        self,
        query: str,
        top_k: int = 5,
        depth: int = 2,
    ) -> RetrievalResult:
        """Evaluate a single query."""
        start_time = time.perf_counter()

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Vector search for papers
        vector_results = await self.search_papers(query_embedding, top_k, min_score=0.0)
        seed_paper_ids = [r["paper_id"] for r in vector_results]

        # Vector search for chunks
        chunk_results = await self.search_chunks(query_embedding, top_k * 2, paper_ids=seed_paper_ids)

        # Graph traversal
        graph_paths = await self.traverse_graph(seed_paper_ids, depth)

        latency_ms = (time.perf_counter() - start_time) * 1000

        return RetrievalResult(
            query=query,
            top_k=top_k,
            depth=depth,
            vector_results=len(vector_results),
            chunk_results=len(chunk_results),
            graph_paths=len(graph_paths),
            seed_papers=seed_paper_ids,
            latency_ms=latency_ms,
        )

    async def run_experiment(
        self,
        queries: List[str],
        configs: List[ExperimentConfig],
        output_dir: str = "experiments/results/retrieval_eval",
    ) -> List[Dict]:
        """Run retrieval evaluation across multiple configs."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        all_results = []

        for config in configs:
            print(f"\n=== Running config: {config.name} ===")
            print(f"  top_k: {config.top_k}, depth: {config.depth}")

            config_results = []
            for i, query in enumerate(queries):
                result = await self.evaluate_query(query, config.top_k, config.depth)
                config_results.append(asdict(result))
                print(f"  Query {i+1}/{len(queries)}: {result.vector_results} papers, {result.chunk_results} chunks, {result.graph_paths} paths, {result.latency_ms:.1f}ms")

            # Save config results
            output_file = Path(output_dir) / f"{config.name}.json"
            with open(output_file, "w") as f:
                json.dump(config_results, f, indent=2)

            all_results.extend(config_results)

        # Save combined results
        summary = {
            "total_queries": len(queries),
            "configs_tested": len(configs),
            "total_runs": len(all_results),
            "embedding_model": self.embedding_model,
        }
        with open(Path(output_dir) / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        return all_results


async def main():
    """Run retrieval evaluation on E3/E4 test queries."""

    # Test queries from E3/E4 experiments
    test_queries = [
        "What is the key innovation of Transformer architecture?",
        "How does self-attention mechanism work in Transformers?",
        "What is the ASVspoof 2015 challenge for speaker verification?",
        "How does LSTM-Attention model work for time series forecasting?",
        "What are the main findings of GraphRAG under Fire paper?",
        "How does XAI improve interpretability of deep learning models?",
        "What is the difference between fixed and semantic chunking?",
        "How does ECAPA-TDNN detect deepfake audio?",
        "What is the role of attention bottleneck in Transformer models?",
        "How does hybrid LSTM-Attention improve inflation prediction?",
    ]

    # Experiment configs - test retrieval params with local embeddings
    configs = [
        # Retrieval param comparison (E3)
        ExperimentConfig("e3_topk5_depth1", 5, 1),
        ExperimentConfig("e3_topk10_depth1", 10, 1),
        ExperimentConfig("e3_topk5_depth2", 5, 2),
        ExperimentConfig("e3_topk10_depth2", 10, 2),
        ExperimentConfig("e3_topk15_depth2", 15, 2),
        ExperimentConfig("e3_topk10_depth3", 10, 3),
    ]

    evaluator = RetrievalEvaluator()
    await evaluator.connect()

    try:
        results = await evaluator.run_experiment(test_queries, configs)
        print(f"\n=== Experiment Complete ===")
        print(f"Total runs: {len(results)}")
        print(f"Results saved to: experiments/results/retrieval_eval/")

        # Print summary
        for config in configs:
            config_results = [r for r in results if r["query"] == test_queries[0]]  # just first query for quick check
            # Actually, let's compute averages
            config_runs = [r for r in results if r["top_k"] == config.top_k and r["depth"] == config.depth]
            if config_runs:
                avg_papers = sum(r["vector_results"] for r in config_runs) / len(config_runs)
                avg_chunks = sum(r["chunk_results"] for r in config_runs) / len(config_runs)
                avg_paths = sum(r["graph_paths"] for r in config_runs) / len(config_runs)
                avg_latency = sum(r["latency_ms"] for r in config_runs) / len(config_runs)
                print(f"  {config.name}: avg_papers={avg_papers:.1f}, avg_chunks={avg_chunks:.1f}, avg_paths={avg_paths:.1f}, avg_latency={avg_latency:.1f}ms")
    finally:
        await evaluator.close()


if __name__ == "__main__":
    asyncio.run(main())