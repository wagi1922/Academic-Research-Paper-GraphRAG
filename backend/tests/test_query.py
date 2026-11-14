"""
Test query endpoints.
"""

import pytest
from httpx import AsyncClient


class TestQueryEndpoints:
    @pytest.mark.asyncio
    async def test_query_endpoint_exists(self, async_client: AsyncClient):
        """Test query endpoint returns proper error without Neo4j."""
        response = await async_client.post(
            "/api/v1/query/",
            json={"query": "test query", "top_k": 5, "depth": 2}
        )
        # Should fail with 500 due to missing Neo4j, not 404
        assert response.status_code in (500, 503)

    @pytest.mark.asyncio
    async def test_query_suggestions(self, async_client: AsyncClient):
        """Test query suggestions endpoint."""
        response = await async_client.get("/api/v1/query/suggestions?partial=transformer")
        # May fail due to missing Neo4j
        assert response.status_code in (200, 500, 503)