"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("BUDGET_API_URL", "http://localhost:8081")
    monkeypatch.setenv("MCP_API_URL", "http://localhost:8082")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    monkeypatch.setenv("ENVIRONMENT", "test")


@pytest.fixture
def mock_service_client():
    """Mock ServiceClient for testing."""
    from unittest.mock import AsyncMock
    mock = Mock()
    mock.post = AsyncMock(return_value={"response": "test response", "user_id": "123"})
    mock.get = AsyncMock(return_value={"status": "healthy"})
    mock.health_check = AsyncMock(return_value=True)
    mock.close = AsyncMock(return_value=None)
    return mock
