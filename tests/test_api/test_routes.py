# tests/test_api/test_routes.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_get_expenses_by_category():
    """API should return expenses filtered by category with pagination."""
    from src.api.app import app

    mock_result = {
        "expenses": [{"date": "28.01.2026", "description": "Test", "amount": 100}],
        "total": 100,
        "count": 1,
        "total_count": 1,
        "has_more": False,
    }

    with patch("src.api.app.get_mcp_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_result
        mock_get_client.return_value = mock_client

        client = TestClient(app)
        response = client.get("/api/expenses/123/Еда?period=2026_01&limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert "expenses" in data
        assert data["expenses"][0]["description"] == "Test"
