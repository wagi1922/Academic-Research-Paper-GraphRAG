"""
Test ingestion endpoints.
"""

import pytest
from httpx import AsyncClient


class TestIngestEndpoints:
    @pytest.mark.asyncio
    async def test_ingest_status_not_found(self, async_client: AsyncClient):
        """Test getting status for non-existent job."""
        response = await async_client.get("/api/v1/papers/ingest/status/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_ingest_batch_too_many_files(self, async_client: AsyncClient):
        """Test batch ingest with too many files."""
        files = [("files", (f"test{i}.pdf", b"dummy", "application/pdf")) for i in range(25)]
        response = await async_client.post("/api/v1/papers/ingest/batch", files=files)
        assert response.status_code == 400
        assert "Maximum 20 files" in response.text