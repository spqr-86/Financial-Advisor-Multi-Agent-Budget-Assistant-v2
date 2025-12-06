"""Tests for core schemas."""

import pytest
from pydantic import ValidationError

from src.core.schemas import QueryRequest, QueryResponse, HealthResponse, ErrorResponse


def test_query_request_valid():
    """Test QueryRequest with valid data."""
    req = QueryRequest(query="test query", user_id="123")
    assert req.query == "test query"
    assert req.user_id == "123"
    assert req.session_id is None


def test_query_request_with_session():
    """Test QueryRequest with session_id."""
    req = QueryRequest(query="test", user_id="123", session_id="session_123")
    assert req.session_id == "session_123"


def test_query_request_empty_query():
    """Test QueryRequest fails with empty query."""
    with pytest.raises(ValidationError):
        QueryRequest(query="", user_id="123")


def test_query_request_empty_user_id():
    """Test QueryRequest fails with empty user_id."""
    with pytest.raises(ValidationError):
        QueryRequest(query="test", user_id="")


def test_query_response():
    """Test QueryResponse."""
    resp = QueryResponse(response="test response", user_id="123", session_id="session_123")
    assert resp.response == "test response"
    assert resp.user_id == "123"
    assert resp.session_id == "session_123"


def test_health_response_default():
    """Test HealthResponse with defaults."""
    health = HealthResponse(service="test")
    assert health.status == "healthy"
    assert health.service == "test"
    assert health.version == "2.0.0"
    assert health.dependencies is None


def test_health_response_with_deps():
    """Test HealthResponse with dependencies."""
    health = HealthResponse(
        status="degraded",
        service="api",
        dependencies={"mcp": False}
    )
    assert health.status == "degraded"
    assert health.dependencies == {"mcp": False}


def test_error_response():
    """Test ErrorResponse."""
    error = ErrorResponse(error="Test error", detail="Details here", code="TEST_ERROR")
    assert error.error == "Test error"
    assert error.detail == "Details here"
    assert error.code == "TEST_ERROR"
