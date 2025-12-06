"""Tests for MCP Service."""

import pytest
from httpx import AsyncClient

from src.mcp.app import app


@pytest.mark.asyncio
async def test_health_check(mock_env):
    """Test health endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "mcp"


@pytest.mark.asyncio
async def test_query_endpoint(mock_env):
    """Test /mcp/query endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/mcp/query",
            json={"query": "test query", "user_id": "123"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "MCP Echo:" in data["response"]
    assert data["user_id"] == "123"
