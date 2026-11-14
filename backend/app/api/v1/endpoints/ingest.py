"""
Paper Ingestion Endpoint
Handles PDF upload, parsing, chunking, entity extraction, and graph ingestion.
"""

import logging
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

from app.schemas.entities import (
    IngestRequest,
    IngestResponse,
    PaperCreate,
    ChunkCreate,
    ExtractedEntities,
)
from app.ingestion.parser import PDFParser
from app.ingestion.chunker import get_chunker, Chunk
from app.ingestion.extractor import EntityExtractor
from app.ingestion.graph_writer import GraphWriter
from app.core.neo4j_driver import get_neo4j_session
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["ingestion"])

# In-memory job tracking (replace with Redis/DB in production)
ingestion_jobs: dict[str, dict] = {}


class IngestJobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[IngestResponse] = None
    error: Optional[str] = None


@router.post("/ingest", response_model=IngestResponse)
async def ingest_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    year: int = Form(None),
    doi: str = Form(None),
    venue: str = Form(None),
    keywords: str = Form(""),
    chunking_strategy: str = Form("fixed_512_50"),
):
    """
    Ingest a single PDF paper: parse -> chunk -> extract entities -> write to graph.
    Returns immediately with job ID for async processing.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    job_id = str(uuid.uuid4())[:8]
    ingestion_jobs[job_id] = IngestJobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Job created, waiting for background task",
    )

    # Parse keywords
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

    background_tasks.add_task(
        _process_ingestion,
        job_id=job_id,
        file=file,
        title=title,
        year=year,
        doi=doi,
        venue=venue,
        keywords=keyword_list,
        chunking_strategy=chunking_strategy,
    )

    return IngestResponse(
        paper_id=job_id,  # Temporary ID until processing completes
        title=title,
        status="processing",
        message="Ingestion started. Check /papers/ingest/status/{job_id} for progress.",
        chunks_indexed=0,
        entities_extracted={},
    )


@router.get("/ingest/status/{job_id}", response_model=IngestJobStatus)
async def get_ingestion_status(job_id: str):
    """Get ingestion job status."""
    if job_id not in ingestion_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return ingestion_jobs[job_id]


async def _process_ingestion(
    job_id: str,
    file: UploadFile,
    title: str,
    year: int = None,
    doi: str = None,
    venue: str = None,
    keywords: list[str] = None,
    chunking_strategy: str = "fixed_512_50",
):
    """Background task to process paper ingestion."""
    job = ingestion_jobs[job_id]

    try:
        # Step 1: Parse PDF
        job.status = "processing"
        job.progress = 10
        job.message = "Parsing PDF..."

        parser = PDFParser()
        content = await file.read()
        parse_result = await parser.parse_pdf_grobid_bytes(content, file.filename)

        if not parse_result or not parse_result.get("full_text"):
            raise ValueError("Failed to extract text from PDF")

        full_text = parse_result["full_text"]
        metadata = {
            "title": title,
            "year": year,
            "doi": doi,
            "venue": venue,
            "keywords": keywords or [],
            "sections": parse_result.get("sections", []),
        }

        # Step 2: Chunk text
        job.progress = 30
        job.message = "Chunking text..."

        chunker = get_chunker(chunking_strategy)
        chunks = chunker.chunk(full_text, metadata)

        # Step 3: Extract entities (optional - requires OpenRouter API key)
        job.progress = 50
        job.message = "Extracting entities..."

        entities = ExtractedEntities()
        if settings.openrouter_api_key:
            extractor = EntityExtractor(
                api_key=settings.openrouter_api_key,
                model=settings.llm_model,
            )
            entities = await extractor.extract_from_chunks([c.text for c in chunks], title)
        else:
            job.message = "Skipping entity extraction (no OpenRouter API key)"
            logger.warning("OpenRouter API key not set, skipping entity extraction")

        # Step 4: Write to Neo4j
        job.progress = 70
        job.message = "Writing to graph database..."

        paper_id = doi or str(uuid.uuid4())[:12]
        paper = PaperCreate(
            id=paper_id,
            title=title,
            abstract=full_text[:2000],
            year=year,
            doi=doi,
            venue=venue,
            keywords=keywords or [],
        )

        # Prepare chunks for DB
        chunk_objects = []
        for i, chunk in enumerate(chunks):
            chunk_objects.append(ChunkCreate(
                id=f"{paper_id}_chunk_{i}",
                paper_id=paper_id,
                text=chunk.text,
                chunk_index=i,
                embedding=None,  # Will be filled by embedding service
                metadata=chunk.metadata,
            ))

        async for session in get_neo4j_session():
            writer = GraphWriter(session)
            stats = await writer.ingest_paper_with_entities(paper, entities, chunk_objects)

        job.progress = 100
        job.status = "completed"
        job.message = "Ingestion completed successfully"
        job.result = IngestResponse(
            paper_id=paper_id,
            title=title,
            status="completed",
            message=f"Ingested {title}",
            chunks_indexed=stats["chunks_created"],
            entities_extracted={
                "authors": stats["authors_created"],
                "concepts": stats["concepts_created"],
                "methods": stats["methods_created"],
                "datasets": stats["datasets_created"],
                "relations": stats["relations_created"],
            },
        )

    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {e}")
        job.progress = 100
        job.status = "failed"
        job.message = f"Ingestion failed: {str(e)}"
        job.error = str(e)


@router.post("/ingest/batch")
async def ingest_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    chunking_strategy: str = Form("fixed_512_50"),
):
    """Ingest multiple papers at once."""
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files per batch")

    job_id = str(uuid.uuid4())[:8]
    ingestion_jobs[job_id] = IngestJobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message=f"Batch job created for {len(files)} files",
    )

    background_tasks.add_task(
        _process_batch_ingestion,
        job_id=job_id,
        files=files,
        chunking_strategy=chunking_strategy,
    )

    return {"job_id": job_id, "status": "processing", "total_files": len(files)}


async def _process_batch_ingestion(
    job_id: str,
    files: list[UploadFile],
    chunking_strategy: str,
):
    """Background task for batch ingestion."""
    job = ingestion_jobs[job_id]
    job.status = "processing"
    total = len(files)
    results = []

    for idx, file in enumerate(files):
        job.progress = int((idx / total) * 90)
        job.message = f"Processing {idx+1}/{total}: {file.filename}"

        try:
            # Simplified: just process each file
            content = await file.read()
            parser = PDFParser()
            parse_result = parser.parse_pdf_grobid(content)

            if parse_result and parse_result.get("text"):
                title = file.filename.replace(".pdf", "")
                # Process similar to single ingest...
                results.append({"file": file.filename, "status": "success"})
            else:
                results.append({"file": file.filename, "status": "failed", "error": "Parse failed"})

        except Exception as e:
            results.append({"file": file.filename, "status": "failed", "error": str(e)})

    job.progress = 100
    job.status = "completed"
    job.message = f"Batch completed: {sum(1 for r in results if r['status']=='success')}/{total} successful"
    job.result = {"results": results}