"""Tests for bot middlewares."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from aiogram.types import Message, User

from src.bot.middlewares import (
    APIClientMiddleware,
    RateLimitMiddleware,
    AccessControlMiddleware,
)


@pytest.fixture
def mock_message():
    """Create mock Message."""
    message = Mock(spec=Message)
    message.from_user = Mock(spec=User)
    message.from_user.id = 123456
    message.answer = AsyncMock()
    return message


@pytest.fixture
def mock_handler():
    """Create mock handler."""
    return AsyncMock(return_value=None)


@pytest.mark.asyncio
async def test_api_client_middleware(mock_message, mock_handler, mock_service_client):
    """Test APIClientMiddleware injects client."""
    middleware = APIClientMiddleware(mock_service_client)
    data = {}

    await middleware(mock_handler, mock_message, data)

    assert data["api_client"] == mock_service_client
    mock_handler.assert_called_once_with(mock_message, data)


@pytest.mark.asyncio
async def test_rate_limit_middleware_allows(mock_message, mock_handler):
    """Test RateLimitMiddleware allows request under limit."""
    middleware = RateLimitMiddleware(limit=5, window=60)
    data = {}

    # First request should pass
    await middleware(mock_handler, mock_message, data)

    mock_handler.assert_called_once_with(mock_message, data)
    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limit_middleware_blocks(mock_message, mock_handler):
    """Test RateLimitMiddleware blocks when limit exceeded."""
    middleware = RateLimitMiddleware(limit=2, window=60)
    data = {}

    # First two requests should pass
    await middleware(mock_handler, mock_message, data)
    await middleware(mock_handler, mock_message, data)

    # Third should be blocked
    await middleware(mock_handler, mock_message, data)

    assert mock_handler.call_count == 2  # Only called twice
    mock_message.answer.assert_called_once_with("Подождите минуту...")


@pytest.mark.asyncio
async def test_rate_limit_middleware_cleans_old(mock_message, mock_handler):
    """Test RateLimitMiddleware cleans old requests."""
    middleware = RateLimitMiddleware(limit=2, window=1)  # 1 second window
    middleware.requests[123456] = [
        datetime.now() - timedelta(seconds=2)  # Old request
    ]
    data = {}

    # Should clean old request and allow new ones
    await middleware(mock_handler, mock_message, data)
    await middleware(mock_handler, mock_message, data)

    assert mock_handler.call_count == 2
    assert len(middleware.requests[123456]) == 2


@pytest.mark.asyncio
async def test_rate_limit_middleware_no_user(mock_handler):
    """Test RateLimitMiddleware with no user."""
    middleware = RateLimitMiddleware(limit=2, window=60)
    message = Mock(spec=Message)
    message.from_user = None
    data = {}

    await middleware(mock_handler, message, data)

    mock_handler.assert_called_once_with(message, data)


@pytest.mark.asyncio
async def test_access_control_middleware_allows_admin(mock_message, mock_handler):
    """Test AccessControlMiddleware allows admin."""
    middleware = AccessControlMiddleware(admin_ids=[123456])
    data = {}

    await middleware(mock_handler, mock_message, data)

    mock_handler.assert_called_once_with(mock_message, data)
    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_access_control_middleware_blocks_non_admin(mock_message, mock_handler):
    """Test AccessControlMiddleware blocks non-admin."""
    middleware = AccessControlMiddleware(admin_ids=[999999])
    data = {}

    result = await middleware(mock_handler, mock_message, data)

    assert result is None
    mock_handler.assert_not_called()
    mock_message.answer.assert_called_once_with("Доступ ограничен")


@pytest.mark.asyncio
async def test_access_control_middleware_empty_list(mock_message, mock_handler):
    """Test AccessControlMiddleware with empty admin list (allows all)."""
    middleware = AccessControlMiddleware(admin_ids=[])
    data = {}

    await middleware(mock_handler, mock_message, data)

    mock_handler.assert_called_once_with(mock_message, data)


@pytest.mark.asyncio
async def test_access_control_middleware_no_user(mock_handler):
    """Test AccessControlMiddleware with no user."""
    middleware = AccessControlMiddleware(admin_ids=[123456])
    message = Mock(spec=Message)
    message.from_user = None
    data = {}

    result = await middleware(mock_handler, message, data)

    assert result is None
    mock_handler.assert_not_called()
