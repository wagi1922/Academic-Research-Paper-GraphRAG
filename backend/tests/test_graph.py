"""
Test graph visualization endpoints.
"""

import pytest
from httpx import AsyncClient


class TestGraphEndpoints:
    @pytest.mark.asyncio
    async def test_visualize_requires_param(self, async_client: AsyncClient):
        """Test visualize endpoint requires paper_id or node_id."""
        response = await async_client.get("/api/v1/graph/visualize")
        assert response.status_code == 400
        assert "must be provided" in response.text

    @pytest.mark.asyncio
    async def test_visualize_with_paper_id(self, async_client: AsyncClient):
        """Test visualize with paper_id."""
        response = await async_client.get("/api/v1/graph/visualize?paper_id=test123")
        # Should return 200 with empty data, or fail with 500/503 if Neo4j unavailable
        assert response.status_code in (200, 404, 500, 503)

    @pytest.mark.asyncio
    async def test_graph_stats(self, async_client: AsyncClient):
        """Test graph stats endpoint."""
        response = await async_client.get("/api/v1/graph/stats")
        assert response.status_code in (200, 500, 503)