"""Bot handlers."""

import logging
import asyncio

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.core.http_client import ServiceClient
from src.bot.utils import split_long_message

logger = logging.getLogger(__name__)

router = Router(name="main")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    # Safe access to from_user (can be None in channel posts)
    if not message.from_user:
        return

    name = message.from_user.first_name or "друг"
    await message.answer(
        f"Привет, {name}!\n\n"
        "Я Budget Assistant v2.0\n\n"
        "Напиши что-нибудь, и я обработаю!"
    )


@router.message(F.text)
async def handle_text(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle all text messages."""
    if not message.from_user or not message.text:
        return

    user_id = str(message.from_user.id)
    query_preview = message.text[:50] + "..." if len(message.text) > 50 else message.text

    if not api_client:
        logger.error(f"API client not configured for user {user_id}")
        await message.answer("API не настроен. Проверьте конфигурацию.")
        return

    # Show typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    logger.info(f"Processing query from user {user_id}: {query_preview}")

    try:
        result = await api_client.post(
            "/api/query",
            json={"query": message.text, "user_id": user_id},
        )
        response = result.get("response", "Нет ответа")

        # Split long messages into chunks
        message_chunks = split_long_message(response)

        logger.info(
            f"Sending response to user {user_id}: "
            f"{len(response)} chars in {len(message_chunks)} message(s)"
        )

        # Send all chunks
        for i, chunk in enumerate(message_chunks):
            await message.answer(chunk)
            # Small delay between messages to avoid rate limits
            if i < len(message_chunks) - 1:
                await asyncio.sleep(0.5)

    except asyncio.TimeoutError:
        logger.warning(f"Request timeout for user {user_id}: {query_preview}")
        await message.answer(
            "Обработка запроса заняла слишком много времени. "
            "Попробуйте упростить запрос или повторите позже."
        )

    except Exception as e:
        logger.error(
            f"API request failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer("Произошла ошибка. Попробуйте позже.")
