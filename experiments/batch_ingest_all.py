#!/usr/bin/env python3
"""Batch ingest all PDFs from data/corpus/pdfs/"""
import os
import asyncio
import aiohttp
import json
from pathlib import Path

PDF_DIR = Path("/home/guard/Documents/perkuliahan/sem 7/Cap/data/corpus/pdfs")
API_URL = "http://localhost:8000/api/v1/papers/ingest/batch"
CONCURRENCY = 2  # Limit concurrent to avoid overwhelming Grobid/LLM

pdfs = sorted([f for f in PDF_DIR.glob("*.pdf")])
print(f"Total PDFs: {len(pdfs)}")

# Metadata mapping (filename -> title, year, doi, venue)
# For arXiv papers, extract from filename
def extract_metadata(filename):
    name = filename.stem
    # arXiv format: YYMM.NNNNNvX or similar
    if name.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")) and "." in name:
        # Looks like arXiv ID
        return {
            "title": name.replace("v1", "").replace("v2", "").replace("v3", "").replace("v4", ""),
            "year": "2020",  # placeholder
            "doi": name,
            "venue": "arXiv"
        }
    # Elsevier/ScienceDirect format
    if name.startswith("1-s2.0-"):
        return {
            "title": name.replace("1-s2.0-", "").replace("-main", "").replace("_1", "").replace(".en.id", ""),
            "year": "2023",
            "doi": name,
            "venue": "Elsevier"
        }
    return {
        "title": name,
        "year": "2023",
        "doi": name,
        "venue": "Unknown"
    }

async def ingest_one(session, pdf_path, semaphore):
    async with semaphore:
        meta = extract_metadata(pdf_path)
        filename = pdf_path.name
        
        # Prepare form data
        data = aiohttp.FormData()
        data.add_field('files', open(pdf_path, 'rb'), filename=filename, content_type='application/pdf')
        data.add_field('titles', meta['title'])
        data.add_field('years', meta['year'])
        data.add_field('dois', meta['doi'])
        data.add_field('venues', meta['venue'])
        data.add_field('chunking_strategy', 'fixed_512_50')
        
        try:
            async with session.post(API_URL, data=data) as resp:
                result = await resp.json()
                job_id = result.get('job_id')
                print(f"✓ {filename} -> job {job_id}")
                return job_id
        except Exception as e:
            print(f"✗ {filename} -> ERROR: {e}")
            return None
        finally:
            # Close file handle
            for field in data._fields:
                if hasattr(field[1], 'close'):
                    field[1].close()

async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    timeout = aiohttp.ClientTimeout(total=600)  # 10 min per request
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [ingest_one(session, pdf, semaphore) for pdf in pdfs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Save job IDs
    job_ids = [r for r in results if isinstance(r, str)]
    with open("experiments/batch_job_ids.json", "w") as f:
        json.dump(job_ids, f, indent=2)
    print(f"\nSubmitted {len(job_ids)} jobs. Job IDs saved to experiments/batch_job_ids.json")

if __name__ == "__main__":
    asyncio.run(main())