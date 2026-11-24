#!/usr/bin/env python3
"""ArXiv Paper Downloader for Corpus Expansion.
Downloads papers relevant to GraphRAG capstone topics."""

import asyncio
import aiohttp
import feedparser
import os
import time
from pathlib import Path
from typing import List, Dict
import xml.etree.ElementTree as ET


ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Search queries for relevant topics
SEARCH_QUERIES = [
    # Transformers & Attention
    'all:"transformer" AND all:"attention" AND cat:cs.CL',
    'all:"attention mechanism" AND cat:cs.LG',
    'all:"self-attention" AND cat:cs.CL',

    # XAI / Explainable AI
    'all:"explainable AI" OR all:"XAI" AND cat:cs.LG',
    'all:"SHAP" OR all:"LIME" AND cat:cs.LG',
    'all:"feature attribution" AND cat:cs.LG',

    # Time Series Forecasting / Inflation
    'all:"LSTM" AND all:"attention" AND cat:stat.ML',
    'all:"time series forecasting" AND all:"inflation" AND cat:econ.GN',
    'all:"hybrid LSTM" AND cat:stat.ML',

    # Deepfake Detection / Audio
    'all:"deepfake" AND all:"audio" AND cat:cs.SD',
    'all:"ECAPA-TDNN" AND cat:cs.SD',
    'all:"ASVspoof" AND cat:cs.SD',

    # Graph Neural Networks / GraphRAG
    'all:"GraphRAG" OR all:"graph RAG" AND cat:cs.IR',
    'all:"retrieval augmented generation" AND all:"graph" AND cat:cs.IR',
    'all:"citation graph" AND cat:cs.DL',
]

# Fallback: broader queries
BROAD_QUERIES = [
    'cat:cs.CL AND submittedDate:[20230101 TO 20241231]',
    'cat:cs.LG AND submittedDate:[20230101 TO 20241231]',
    'cat:cs.IR AND submittedDate:[20230101 TO 20241231]',
    'cat:cs.SD AND submittedDate:[20230101 TO 20241231]',
    'cat:stat.ML AND submittedDate:[20230101 TO 20241231]',
]


async def search_arxiv(session: aiohttp.ClientSession, query: str, max_results: int = 50) -> List[Dict]:
    """Search arXiv API for papers."""
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    async with session.get(ARXIV_API_URL, params=params) as response:
        content = await response.text()
        feed = feedparser.parse(content)
        papers = []
        for entry in feed.entries:
            arxiv_id = entry.id.split("/abs/")[-1]
            papers.append({
                "arxiv_id": arxiv_id,
                "title": entry.title,
                "summary": entry.summary,
                "authors": [a.name for a in entry.authors],
                "published": entry.published,
                "categories": [tag.term for tag in entry.tags],
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            })
        return papers


async def download_pdf(session: aiohttp.ClientSession, pdf_url: str, output_path: Path) -> bool:
    """Download PDF from arXiv."""
    try:
        async with session.get(pdf_url) as response:
            if response.status == 200:
                content = await response.read()
                output_path.write_bytes(content)
                return True
            else:
                print(f"  Failed to download {pdf_url}: HTTP {response.status}")
                return False
    except Exception as e:
        print(f"  Error downloading {pdf_url}: {e}")
        return False


async def download_papers(
    output_dir: str = "data/corpus/pdfs",
    metadata_dir: str = "data/corpus",
    max_per_query: int = 20,
    max_total: int = 100,
) -> Dict:
    """Download papers from arXiv based on search queries."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metadata_path = Path(metadata_dir)
    metadata_path.mkdir(parents=True, exist_ok=True)

    # Load existing metadata to avoid duplicates
    existing_metadata_file = metadata_path / "metadata.json"
    if existing_metadata_file.exists():
        import json
        with open(existing_metadata_file) as f:
            existing_metadata = json.load(f)
        existing_ids = {p.get("arxiv_id", "") for p in existing_metadata}
    else:
        existing_metadata = []
        existing_ids = set()

    # Also check existing PDF files
    existing_pdfs = {f.stem for f in output_path.glob("*.pdf")}
    existing_ids.update(existing_pdfs)

    all_new_papers = []
    downloaded_count = 0

    async with aiohttp.ClientSession() as session:
        # Try specific queries first
        for query in SEARCH_QUERIES:
            if downloaded_count >= max_total:
                break
            print(f"\nSearching: {query}")
            papers = await search_arxiv(session, query, max_results=max_per_query)

            for paper in papers:
                if downloaded_count >= max_total:
                    break
                arxiv_id = paper["arxiv_id"]
                if arxiv_id in existing_ids:
                    print(f"  Skipping {arxiv_id} (already exists)")
                    continue

                print(f"  Downloading {arxiv_id}: {paper['title'][:60]}...")
                pdf_path = output_path / f"{arxiv_id}.pdf"
                success = await download_pdf(session, paper["pdf_url"], pdf_path)

                if success:
                    all_new_papers.append(paper)
                    existing_ids.add(arxiv_id)
                    downloaded_count += 1
                    print(f"    ✓ Saved to {pdf_path}")
                else:
                    if pdf_path.exists():
                        pdf_path.unlink()

                # Be nice to arXiv API
                await asyncio.sleep(0.5)

        # If we still need more, try broad queries
        if downloaded_count < max_total:
            for query in BROAD_QUERIES:
                if downloaded_count >= max_total:
                    break
                print(f"\nSearching (broad): {query}")
                papers = await search_arxiv(session, query, max_results=max_per_query)

                for paper in papers:
                    if downloaded_count >= max_total:
                        break
                    arxiv_id = paper["arxiv_id"]
                    if arxiv_id in existing_ids:
                        continue

                    print(f"  Downloading {arxiv_id}: {paper['title'][:60]}...")
                    pdf_path = output_path / f"{arxiv_id}.pdf"
                    success = await download_pdf(session, paper["pdf_url"], pdf_path)

                    if success:
                        all_new_papers.append(paper)
                        existing_ids.add(arxiv_id)
                        downloaded_count += 1
                        print(f"    ✓ Saved to {pdf_path}")
                    else:
                        if pdf_path.exists():
                            pdf_path.unlink()

                    await asyncio.sleep(0.5)

    # Save updated metadata
    if all_new_papers:
        import json
        updated_metadata = existing_metadata + all_new_papers
        with open(metadata_path / "metadata.json", "w") as f:
            json.dump(updated_metadata, f, indent=2)

        # Update ingest manifest
        manifest_file = metadata_path / "ingest_manifest.json"
        if manifest_file.exists():
            with open(manifest_file) as f:
                manifest = json.load(f)
        else:
            manifest = []

        for paper in all_new_papers:
            manifest.append({
                "arxiv_id": paper["arxiv_id"],
                "title": paper["title"],
                "status": "pending",
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            })

        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2)

    return {
        "downloaded": downloaded_count,
        "new_papers": all_new_papers,
        "total_papers": len(existing_ids),
    }


async def main():
    print("=== ArXiv Corpus Expansion ===")
    result = await download_papers(max_total=50)
    print(f"\n=== Complete ===")
    print(f"Downloaded: {result['downloaded']} new papers")
    print(f"Total papers in corpus: {result['total_papers']}")


if __name__ == "__main__":
    asyncio.run(main())