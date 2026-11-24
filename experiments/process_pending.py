#!/usr/bin/env python3
"""Process pending papers from manifest."""

import json
import asyncio
import httpx
from pathlib import Path

API_BASE = "http://localhost:8000"
MANIFEST_FILE = Path("data/corpus/ingest_manifest.json")
METADATA_FILE = Path("data/corpus/metadata.json")
PDF_DIR = Path("data/corpus/pdfs")

async def main():
    # Load manifest
    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)

    # Load metadata
    with open(METADATA_FILE) as f:
        metadata = {p["arxiv_id"]: p for p in json.load(f)}

    # Find pending papers
    pending = [m for m in manifest if m.get("status") in ("pending", "processing")]
    print(f"Found {len(pending)} pending papers")

    if not pending:
        print("No pending papers to process")
        return

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        for i, entry in enumerate(pending):
            arxiv_id = entry.get("arxiv_id", "")
            if not arxiv_id:
                # Try to extract from file_path
                import re
                fp = entry.get("file_path", "")
                match = re.search(r'([0-9]{4}\.[0-9]{4,5}v[0-9]+)', fp)
                if match:
                    arxiv_id = match.group(1)

            if not arxiv_id:
                print(f"  [{i+1}/{len(pending)}] Skipping: no arxiv_id")
                continue

            # Get metadata
            paper_meta = metadata.get(arxiv_id, {})
            title = paper_meta.get("title", entry.get("title", arxiv_id))
            pdf_path = PDF_DIR / f"{arxiv_id}.pdf"

            if not pdf_path.exists():
                print(f"  [{i+1}/{len(pending)}] {arxiv_id}: PDF not found")
                entry["status"] = "failed"
                entry["error"] = "PDF not found"
                continue

            print(f"  [{i+1}/{len(pending)}] Ingesting {arxiv_id}: {title[:60]}...")
            entry["status"] = "processing"

            try:
                with open(pdf_path, "rb") as f:
                    files = {"file": (f"{arxiv_id}.pdf", f, "application/pdf")}
                    data = {
                        "title": title,
                        "doi": f"10.48550/arXiv.{arxiv_id}",
                        "authors": json.dumps(paper_meta.get("authors", [])),
                        "year": paper_meta.get("published", "")[:4] if paper_meta.get("published") else "2024",
                        "venue": "arXiv",
                        "keywords": json.dumps(paper_meta.get("categories", [])),
                    }
                    response = await client.post(f"{API_BASE}/api/v1/papers/ingest", files=files, data=data)

                if response.status_code == 200:
                    result = response.json()
                    job_id = result.get("paper_id", "")
                    print(f"    Job started: {job_id}")

                    # Poll for completion
                    for _ in range(60):  # max 5 minutes
                        await asyncio.sleep(5)
                        status_resp = await client.get(f"{API_BASE}/api/v1/papers/ingest/status/{job_id}")
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            if status_data.get("status") == "completed":
                                result_data = status_data.get("result", {})
                                chunks = result_data.get("chunks_indexed", 0)
                                print(f"    ✓ Success: {chunks} chunks")
                                entry["status"] = "success"
                                entry["paper_id"] = result_data.get("paper_id", "")
                                entry["chunks_indexed"] = chunks
                                entry["arxiv_id"] = arxiv_id
                                break
                            elif status_data.get("status") == "failed":
                                print(f"    ✗ Failed: {status_data.get('error', 'Unknown')}")
                                entry["status"] = "failed"
                                entry["error"] = status_data.get("error", "Unknown")
                                break
                    else:
                        print(f"    ⏱ Timeout")
                        entry["status"] = "timeout"
                else:
                    print(f"    ✗ HTTP {response.status_code}: {response.text}")
                    entry["status"] = "failed"
                    entry["error"] = response.text

            except Exception as e:
                print(f"    ✗ Error: {e}")
                entry["status"] = "error"
                entry["error"] = str(e)

            # Save progress
            with open(MANIFEST_FILE, "w") as f:
                json.dump(manifest, f, indent=2)

    # Summary
    success = [m for m in manifest if m.get("status") == "success"]
    failed = [m for m in manifest if m.get("status") in ("failed", "error", "timeout")]
    print(f"\n=== Complete ===")
    print(f"Total: {len(manifest)}")
    print(f"Success: {len(success)}")
    print(f"Failed: {len(failed)}")


if __name__ == "__main__":
    asyncio.run(main())