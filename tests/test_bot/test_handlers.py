"""Tests for bot handlers."""

import pytest
from unittest.mock import AsyncMock, Mock
from aiogram.types import Message, User, Chat

from src.bot.handlers import cmd_start, handle_text


@pytest.fixture
def mock_message():
    """Create mock Message."""
    message = Mock(spec=Message)
    message.from_user = Mock(spec=User)
    message.from_user.id = 123456
    message.from_user.first_name = "TestUser"
    message.answer = AsyncMock()
    message.bot = Mock()
    message.bot.send_chat_action = AsyncMock()
    message.chat = Mock(spec=Chat)
    message.chat.id = 123456
    message.text = "test message"
    return message


@pytest.mark.asyncio
async def test_cmd_start_success(mock_message):
    """Test /start command with valid user."""
    await cmd_start(mock_message)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "TestUser" in call_args
    assert "Budget Assistant v2.0" in call_args


@pytest.mark.asyncio
async def test_cmd_start_no_user():
    """Test /start command with no user (channel post)."""
    message = Mock(spec=Message)
    message.from_user = None
    message.answer = AsyncMock()

    await cmd_start(message)

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_cmd_start_no_first_name(mock_message):
    """Test /start command with user without first name."""
    mock_message.from_user.first_name = None

    await cmd_start(mock_message)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "друг" in call_args


@pytest.mark.asyncio
async def test_handle_text_success(mock_message, mock_service_client):
    """Test text handler with successful API call."""
    await handle_text(mock_message, api_client=mock_service_client)

    # Should show typing
    mock_message.bot.send_chat_action.assert_called_once_with(123456, "typing")

    # Should call API
    mock_service_client.post.assert_called_once_with(
        "/api/query",
        json={"query": "test message", "user_id": "123456"}
    )

    # Should answer user with HTML parse mode
    mock_message.answer.assert_called_once()
    call_kwargs = mock_message.answer.call_args[1]
    assert call_kwargs.get("parse_mode") == "HTML"


@pytest.mark.asyncio
async def test_handle_text_no_user():
    """Test text handler with no user."""
    message = Mock(spec=Message)
    message.from_user = None
    message.answer = AsyncMock()

    await handle_text(message, api_client=Mock())

    message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_handle_text_no_text(mock_message):
    """Test text handler with no text."""
    mock_message.text = None

    await handle_text(mock_message, api_client=Mock())

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_handle_text_no_api_client(mock_message):
    """Test text handler without API client."""
    await handle_text(mock_message, api_client=None)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "недоступен" in call_args.lower()


@pytest.mark.asyncio
async def test_handle_text_api_error(mock_message, mock_service_client):
    """Test text handler with API error."""
    mock_service_client.post.side_effect = Exception("API Error")

    await handle_text(mock_message, api_client=mock_service_client)

    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "ошибка" in call_args.lower()
