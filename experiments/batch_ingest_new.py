#!/usr/bin/env python3
"""Batch ingest new papers from metadata.json not in manifest."""

import json
import asyncio
import httpx
from pathlib import Path

API_BASE = "http://localhost:8000"
MANIFEST_FILE = Path("data/corpus/ingest_manifest.json")
METADATA_FILE = Path("data/corpus/metadata.json")
PDF_DIR = Path("data/corpus/pdfs")

async def main():
    # Load manifest (already ingested)
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            manifest = json.load(f)
        # Handle both old format (file_path) and new format (arxiv_id)
        # Only skip papers that were successfully ingested
        ingested_ids = set()
        for m in manifest:
            if m.get("status") == "success":
                if "arxiv_id" in m:
                    ingested_ids.add(m["arxiv_id"])
                elif "file_path" in m:
                    import re
                    match = re.search(r'([0-9]{4}\.[0-9]{4,5}v[0-9]+)', m["file_path"])
                    if match:
                        ingested_ids.add(match.group(1))
        print(f"Already successfully ingested: {len(ingested_ids)} papers")
    else:
        manifest = []
        ingested_ids = set()

    # Load metadata (all papers)
    with open(METADATA_FILE) as f:
        metadata = json.load(f)
    print(f"Total metadata entries: {len(metadata)}")

    # Find new papers to ingest
    new_papers = []
    for paper in metadata:
        arxiv_id = paper.get("arxiv_id", "")
        if arxiv_id and arxiv_id not in ingested_ids:
            pdf_path = PDF_DIR / f"{arxiv_id}.pdf"
            if pdf_path.exists():
                new_papers.append(paper)

    print(f"New papers to ingest: {len(new_papers)}")

    if not new_papers:
        print("No new papers to ingest.")
        return

    # Ingest via API
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        for i, paper in enumerate(new_papers):
            arxiv_id = paper.get("arxiv_id", "")
            pdf_path = PDF_DIR / f"{arxiv_id}.pdf"

            print(f"\n[{i+1}/{len(new_papers)}] Ingesting {arxiv_id}: {paper['title'][:60]}...")

            try:
                with open(pdf_path, "rb") as f:
                    files = {"file": (f"{arxiv_id}.pdf", f, "application/pdf")}
                    data = {
                        "title": paper.get("title", ""),
                        "doi": f"10.48550/arXiv.{arxiv_id}",
                        "authors": json.dumps(paper.get("authors", [])),
                        "year": paper.get("published", "")[:4] if paper.get("published") else "",
                        "venue": "arXiv",
                        "keywords": json.dumps(paper.get("categories", [])),
                    }
                    response = await client.post(f"{API_BASE}/api/v1/papers/ingest", files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✓ Success: {result.get('paper_id', '')}, chunks: {result.get('chunks_indexed', 0)}")
                    manifest.append({
                        "arxiv_id": arxiv_id,
                        "title": paper.get("title", ""),
                        "status": "success",
                        "paper_id": result.get("paper_id", ""),
                        "chunks_indexed": result.get("chunks_indexed", 0),
                    })
                else:
                    print(f"  ✗ Failed: HTTP {response.status_code}: {response.text}")
                    manifest.append({
                        "arxiv_id": arxiv_id,
                        "title": paper.get("title", ""),
                        "status": "failed",
                        "error": response.text,
                    })

            except Exception as e:
                print(f"  ✗ Error: {e}")
                manifest.append({
                    "arxiv_id": arxiv_id,
                    "title": paper.get("title", ""),
                    "status": "error",
                    "error": str(e),
                })

            # Save progress periodically
            if (i + 1) % 5 == 0:
                with open(MANIFEST_FILE, "w") as f:
                    json.dump(manifest, f, indent=2)

    # Final save
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

    # Summary
    success_count = sum(1 for m in manifest if m.get("status") == "success")
    print(f"\n=== Ingestion Complete ===")
    print(f"Total in manifest: {len(manifest)}")
    print(f"Successful: {success_count}")


if __name__ == "__main__":
    asyncio.run(main())