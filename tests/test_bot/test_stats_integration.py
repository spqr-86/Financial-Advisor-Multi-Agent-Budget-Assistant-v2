# tests/test_bot/test_stats_integration.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery


@pytest.mark.asyncio
async def test_stats_flow_no_args():
    """Test /stats with no args shows period selection."""
    with patch("src.bot.decorators.require_api_client", lambda f: f):
        from src.bot.handlers.commands import cmd_stats

        message = AsyncMock(spec=Message)
        message.from_user = MagicMock()
        message.from_user.id = 123
        message.text = "/stats"
        message.answer = AsyncMock()
        message.chat = MagicMock()
        message.chat.id = 456
        message.bot.send_chat_action = AsyncMock()

        await cmd_stats(message)

    # Verify period selection keyboard was sent
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Выберите период" in args[0]
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_stats_flow_with_category():
    """Test /stats Еда shows category detail."""
    from src.bot.handlers.commands import cmd_stats

    message = AsyncMock(spec=Message)
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.text = "/stats Еда"
    message.answer = AsyncMock()
    message.chat = MagicMock()
    message.chat.id = 456
    message.bot.send_chat_action = AsyncMock()

    api_client = AsyncMock()
    api_client.get.return_value = {
        "expenses": [],
        "total": 0,
        "count": 0,
        "total_count": 0,
        "has_more": False,
    }

    with patch("src.bot.handlers.commands.require_api_client", lambda f: f):
        await cmd_stats(message, api_client=api_client)

    # Verify category detail was shown
    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args
    assert "Еда" in args[0]
    assert "Расходов нет" in args[0]
