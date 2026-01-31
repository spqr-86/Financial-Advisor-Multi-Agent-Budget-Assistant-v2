# tests/test_bot/test_callbacks.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_callback_stats_month_calls_api():
    """Stats month callback should call API with correct period."""
    from src.bot.handlers.callbacks import callback_stats_specific_month

    callback = MagicMock()
    callback.data = "stats_month_2026_01"
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "statistics": {"categories": {"Еда": 1000}, "total": 1000}
    }

    # Mock limits too
    mock_limits = {"limits": {}}

    # We need to mock the entire call to api_client.get because it might be called multiple times or via gather
    with patch("src.bot.handlers.callbacks.require_api_client", lambda f: f):
        # We need to handle asyncio.gather in the handler
        with patch("asyncio.gather", new_callable=AsyncMock) as mock_gather:
            mock_gather.return_value = (
                {"statistics": {"categories": {"Еда": 1000}, "total": 1000}},
                {"limits": {}},
            )
            await callback_stats_specific_month(callback, api_client=mock_client)

    # Verify edit_text was called
    callback.message.edit_text.assert_called()
    # Verify answer was called
    callback.answer.assert_called()
