"""
Test configuration and fixtures.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

# Test settings
TEST_NEO4J_URI = "bolt://localhost:7687"
TEST_NEO4J_USER = "neo4j"
TEST_NEO4J_PASSWORD = "testpassword"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client for API tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_paper_data():
    """Sample paper data for testing."""
    return {
        "title": "Attention Is All You Need",
        "year": 2017,
        "doi": "10.48550/arXiv.1706.03762",
        "venue": "NeurIPS 2017",
        "keywords": ["transformer", "attention", "machine translation", "NLP"],
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks..."
    }


@pytest.fixture
def sample_chunks():
    """Sample text chunks for testing."""
    return [
        "The Transformer model architecture relies entirely on attention mechanisms.",
        "Self-attention allows the model to weigh the importance of different words.",
        "Multi-head attention performs attention in parallel multiple times.",
    ]