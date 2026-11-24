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
from app.ingestion.embedding_service import get_embedding_service
from app.core.neo4j_driver import get_neo4j_session
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["ingestion"])


class IngestJobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[IngestResponse] = None
    error: Optional[str] = None


# In-memory job tracking (replace with Redis/DB in production)
ingestion_jobs: dict[str, IngestJobStatus] = {}


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
    stats = None

    try:
        # Step 1: Parse PDF
        job.status = "processing"
        job.progress = 10
        job.message = "Parsing PDF..."

        parser = PDFParser(grobid_url=settings.grobid_url)
        content = await file.read()
        parse_result = await parser.parse_pdf_grobid_bytes(content, file.filename or "document.pdf")

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

        # Get embeddings for semantic chunking
        embeddings = None
        if chunking_strategy.startswith("semantic_"):
            embedding_service = await get_embedding_service()
            if embedding_service:
                # Create langchain embeddings wrapper using OpenRouter
                from langchain_openai import OpenAIEmbeddings
                embeddings = OpenAIEmbeddings(
                    api_key=embedding_service.api_key,
                    base_url=embedding_service.base_url,
                    model=embedding_service.model,
                    timeout=60,
                    max_retries=2,
                )
                job.message = f"Chunking text with {chunking_strategy}..."

        # Get LLM client for proposition chunking
        llm_client = None
        if chunking_strategy.startswith("proposition_") and settings.openrouter_api_key and settings.openrouter_api_key not in ("***", "", "placeholder"):
            from openai import AsyncOpenAI
            llm_client = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=120.0,
            )
            job.message = f"Chunking text with {chunking_strategy}..."

        chunker = get_chunker(chunking_strategy, embeddings=embeddings, llm_client=llm_client)
        chunks = chunker.chunk(full_text, metadata)

        # Step 3: Extract entities (optional - requires OpenRouter API key)
        job.progress = 50
        job.message = "Extracting entities..."

        entities = ExtractedEntities()
        if settings.openrouter_api_key and settings.openrouter_api_key not in ("***", "", "placeholder") and not settings.openrouter_api_key.startswith("«redacted:sk-…»"):
            extractor = EntityExtractor(
                api_key=settings.openrouter_api_key,
                model=settings.llm_model,
                timeout=120.0,
            )
            entities = await extractor.extract_from_chunks([c.text for c in chunks], title)
        else:
            job.message = "Skipping entity extraction (no valid OpenRouter API key)"
            logger.warning("OpenRouter API key not set or placeholder, skipping entity extraction")

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
    titles: list[str] = Form([]),
    years: list[int] = Form([]),
    dois: list[str] = Form([]),
    venues: list[str] = Form([]),
    chunking_strategy: str = Form("fixed_512_50"),
):
    """Ingest multiple papers at once with optional metadata."""
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
        titles=titles,
        years=years,
        dois=dois,
        venues=venues,
        chunking_strategy=chunking_strategy,
    )

    return {"job_id": job_id, "status": "processing", "total_files": len(files)}


async def _process_batch_ingestion(
    job_id: str,
    files: list[UploadFile],
    titles: list[str],
    years: list[int],
    dois: list[str],
    venues: list[str],
    chunking_strategy: str,
):
    """Background task for batch ingestion - full pipeline."""
    job = ingestion_jobs[job_id]
    job.status = "processing"
    total = len(files)
    results = []

    for idx, file in enumerate(files):
        job.progress = int((idx / total) * 90)
        job.message = f"Processing {idx+1}/{total}: {file.filename or f'file_{idx}'}"

        try:
            # Full ingestion pipeline per file
            content = await file.read()
            filename = file.filename or f"document_{idx}.pdf"

            # Use provided metadata or derive from filename
            title = titles[idx] if idx < len(titles) and titles[idx] else filename.replace(".pdf", "")
            year = years[idx] if idx < len(years) and years[idx] else 2024
            doi = dois[idx] if idx < len(dois) and dois[idx] else None
            venue = venues[idx] if idx < len(venues) and venues[idx] else "arXiv"

            paper_id = doi or str(uuid.uuid4())[:12]

            # Step 1: Parse PDF
            parser = PDFParser(grobid_url=settings.grobid_url)
            parse_result = await parser.parse_pdf_grobid_bytes(content, filename)

            if not parse_result or not parse_result.get("full_text"):
                results.append({"file": filename, "status": "failed", "error": "Parse failed"})
                continue

            full_text = parse_result["full_text"]
            metadata = {
                "title": title,
                "year": year,
                "doi": doi,
                "venue": venue,
                "keywords": [],
                "sections": parse_result.get("sections", []),
            }

            # Step 2: Chunk text
            # Get embeddings for semantic chunking
            embeddings = None
            if chunking_strategy.startswith("semantic_"):
                embedding_service = await get_embedding_service()
                if embedding_service:
                    from langchain_openai import OpenAIEmbeddings
                    embeddings = OpenAIEmbeddings(
                        api_key=embedding_service.api_key,
                        base_url=embedding_service.base_url,
                        model=embedding_service.model,
                        timeout=60,
                        max_retries=2,
                    )

            # Get LLM client for proposition chunking
            llm_client = None
            if chunking_strategy.startswith("proposition_") and settings.openrouter_api_key and settings.openrouter_api_key not in ("***", "", "placeholder"):
                from openai import AsyncOpenAI
                llm_client = AsyncOpenAI(
                    api_key=settings.openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                    timeout=120.0,
                )

            chunker = get_chunker(chunking_strategy, embeddings=embeddings, llm_client=llm_client)
            chunks = chunker.chunk(full_text, metadata)

            # Step 3: Extract entities (optional - requires OpenRouter API key)
            entities = ExtractedEntities()
            if settings.openrouter_api_key and settings.openrouter_api_key not in ("***", "", "placeholder") and not settings.openrouter_api_key.startswith("«redacted:sk-…»"):
                extractor = EntityExtractor(
                    api_key=settings.openrouter_api_key,
                    model=settings.llm_model,
                    timeout=120.0,
                )
                entities = await extractor.extract_from_chunks([c.text for c in chunks], title)
            else:
                logger.warning("OpenRouter API key not set or placeholder, skipping entity extraction")

            # Step 4: Write to Neo4j
            paper = PaperCreate(
                id=paper_id,
                title=title,
                abstract=full_text[:2000],
                year=year,
                doi=doi,
                venue=venue,
                keywords=[],
            )

            chunk_objects = []
            for i, chunk in enumerate(chunks):
                chunk_objects.append(ChunkCreate(
                    id=f"{paper_id}_chunk_{i}",
                    paper_id=paper_id,
                    text=chunk.text,
                    chunk_index=i,
                    embedding=None,
                    metadata=chunk.metadata,
                ))

            async for session in get_neo4j_session():
                writer = GraphWriter(session)
                stats = await writer.ingest_paper_with_entities(paper, entities, chunk_objects)

            results.append({
                "file": filename,
                "status": "success",
                "paper_id": paper_id,
                "chunks": stats["chunks_created"],
            })

        except Exception as e:
            results.append({"file": filename, "status": "failed", "error": str(e)})

    job.progress = 100
    job.status = "completed"
    success_count = sum(1 for r in results if r.get('status') == 'success')
    job.message = f"Batch completed: {success_count}/{total} successful"
    job.result = None
