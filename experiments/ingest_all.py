#!/usr/bin/env python3
"""Full re-ingest of all corpus PDFs with retry + Grobid health check.

Sequential (concurrency 1) to avoid Grobid 503 overload.
Resume-capable via progress file. Idempotent: paper_id = filename stem (doi field).
Requires: Grobid :8070 + backend :8000 running.
"""
import asyncio
import json
from pathlib import Path

import aiohttp

PDF_DIR = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/data/corpus/pdfs")
API = "http://localhost:8000"
PROGRESS_FILE = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/experiments/ingest_all_progress.json")
GROBID_HEALTH = "http://localhost:8070/api/isalive"
MAX_RETRIES = 3
RETRY_BACKOFF = 20  # seconds


def extract_metadata(filename: Path) -> dict:
    name = filename.stem
    if name[0].isdigit() and "." in name:
        return {
            "title": name.replace("v1", "").replace("v2", "").replace("v3", "").replace("v4", ""),
            "year": 2020,
            "doi": name,
            "venue": "arXiv",
        }
    if name.startswith("1-s2.0-"):
        return {
            "title": name.replace("1-s2.0-", "").replace("-main", "").replace("_1", "").replace(".en.id", ""),
            "year": 2023,
            "doi": name,
            "venue": "Elsevier",
        }
    return {"title": name, "year": 2023, "doi": name, "venue": "Unknown"}


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"done": [], "failed": []}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


async def wait_grobid(session: aiohttp.ClientSession):
    while True:
        try:
            async with session.get(GROBID_HEALTH, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        print("  [grobid down] waiting 15s...", flush=True)
        await asyncio.sleep(15)


async def ingest_one(session: aiohttp.ClientSession, pdf: Path) -> bool:
    meta = extract_metadata(pdf)
    data = aiohttp.FormData()
    data.add_field("file", open(pdf, "rb"), filename=pdf.name, content_type="application/pdf")
    data.add_field("title", meta["title"])
    data.add_field("year", str(meta["year"]))
    data.add_field("doi", meta["doi"])
    data.add_field("venue", meta["venue"])
    data.add_field("keywords", "")
    data.add_field("chunking_strategy", "fixed_512_50")

    async with session.post(f"{API}/api/v1/papers/ingest", data=data) as resp:
        if resp.status != 200:
            print(f"  HTTP {resp.status}: {await resp.text()}", flush=True)
            return False
        result = await resp.json()

    job_id = result.get("paper_id")  # single endpoint returns paper_id = job_id
    for _ in range(120):  # poll up to 10 min
        await asyncio.sleep(5)
        try:
            async with session.get(f"{API}/api/v1/papers/ingest/status/{job_id}") as resp:
                st = await resp.json()
            if st.get("status") in ("completed", "failed"):
                if st.get("status") == "completed":
                    return True
                print(f"  job failed: {st.get('message')}", flush=True)
                return False
        except Exception:
            pass
    return False


async def main():
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    progress = load_progress()
    todo = [p for p in pdfs if p.stem not in progress["done"] and p.stem not in progress["failed"]]
    print(f"PDFs total: {len(pdfs)}, already done: {len(progress['done'])}, failed: {len(progress['failed'])}, to do: {len(todo)}")

    if not todo:
        print("Nothing to do.")
        return

    timeout = aiohttp.ClientTimeout(total=900)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i, pdf in enumerate(todo, 1):
            print(f"[{i}/{len(todo)}] {pdf.name}", flush=True)
            success = False
            for attempt in range(1, MAX_RETRIES + 1):
                await wait_grobid(session)
                try:
                    success = await ingest_one(session, pdf)
                except Exception as e:
                    print(f"  attempt {attempt} error: {e}", flush=True)
                    success = False
                if success:
                    break
                if attempt < MAX_RETRIES:
                    print(f"  retry {attempt}/{MAX_RETRIES} after {RETRY_BACKOFF}s", flush=True)
                    await asyncio.sleep(RETRY_BACKOFF)

            if success:
                progress["done"].append(pdf.stem)
                print("  OK", flush=True)
            else:
                progress["failed"].append(pdf.stem)
                print(f"  FAILED after {MAX_RETRIES} attempts", flush=True)
            save_progress(progress)

    print(f"\nDone. success={len(progress['done'])} failed={len(progress['failed'])}")
    if progress["failed"]:
        print("Failed files:")
        for f in progress["failed"]:
            print(f"  {f}")


if __name__ == "__main__":
    asyncio.run(main())
