"""
FastAPI Application Entry Point
Academic & Research Paper GraphRAG System.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.neo4j_driver import close_neo4j_driver
from app.api.v1.endpoints import ingest, query, graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Academic GraphRAG API...")
    # Startup: Neo4j driver initialized lazily on first use
    yield
    # Shutdown
    logger.info("Shutting down Academic GraphRAG API...")
    await close_neo4j_driver()


app = FastAPI(
    title="Academic & Research Paper GraphRAG",
    description="GraphRAG system for academic paper ingestion, query, and visualization",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.v1.endpoints import ingest, query, graph, catalog

app.include_router(ingest.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(catalog.router, prefix="/api/v1")
app.include_router(catalog.entities_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Academic & Research Paper GraphRAG",
        "version": "0.1.0",
        "description": "GraphRAG system for academic paper knowledge graph",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.core.neo4j_driver import get_neo4j_driver

    neo4j_status = "unknown"
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            await session.run("RETURN 1")
        neo4j_status = "connected"
    except Exception as e:
        neo4j_status = f"error: {str(e)}"

    return {
        "status": "healthy" if neo4j_status == "connected" else "degraded",
        "neo4j": neo4j_status,
        "version": "0.1.0",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )