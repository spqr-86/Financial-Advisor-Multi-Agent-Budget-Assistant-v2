"""Tests for API Gateway."""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from src.api.app import app


@pytest.mark.asyncio
async def test_health_check(mock_env):
    """Test health endpoint."""
    with patch("src.api.app.get_mcp_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.health_check.return_value = True
        mock_get_client.return_value = mock_client

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"
        assert data["dependencies"]["mcp"] is True


@pytest.mark.asyncio
async def test_health_check_degraded(mock_env):
    """Test health endpoint when MCP is down."""
    with patch("src.api.app.get_mcp_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.health_check.return_value = False
        mock_get_client.return_value = mock_client

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["dependencies"]["mcp"] is False


@pytest.mark.asyncio
async def test_query_endpoint(mock_env):
    """Test /api/query endpoint."""
    with patch("src.api.app.get_mcp_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post.return_value = {"response": "MCP Echo: test"}
        mock_get_client.return_value = mock_client

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/query",
                json={"query": "test", "user_id": "123"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "MCP Echo: test"
        assert data["user_id"] == "123"
