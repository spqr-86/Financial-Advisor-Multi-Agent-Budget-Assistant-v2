"""Tests for core exceptions."""

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    BudgetException,
    ServiceUnavailableError,
    RateLimitError,
    budget_exception_handler,
)


def test_budget_exception_default():
    """Test BudgetException with defaults."""
    exc = BudgetException()
    assert exc.status_code == 500
    assert exc.detail == "Internal server error"
    assert exc.code == "INTERNAL_ERROR"


def test_budget_exception_custom():
    """Test BudgetException with custom values."""
    exc = BudgetException(detail="Custom error", code="CUSTOM")
    assert exc.detail == "Custom error"
    assert exc.code == "CUSTOM"


def test_service_unavailable_error():
    """Test ServiceUnavailableError."""
    exc = ServiceUnavailableError()
    assert exc.status_code == 503
    assert exc.detail == "Service temporarily unavailable"


def test_rate_limit_error():
    """Test RateLimitError."""
    exc = RateLimitError()
    assert exc.status_code == 429


@pytest.mark.asyncio
async def test_budget_exception_handler():
    """Test budget_exception_handler."""
    request = Request(scope={"type": "http", "method": "GET", "path": "/test"})
    exc = ServiceUnavailableError(detail="Test unavailable")

    response = await budget_exception_handler(request, exc)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 503
    assert response.body == b'{"error":"Test unavailable","code":"SERVICE_UNAVAILABLE"}'
