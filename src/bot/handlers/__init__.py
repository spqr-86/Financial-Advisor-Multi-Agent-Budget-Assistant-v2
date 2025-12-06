"""Bot handlers."""

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.core.http_client import ServiceClient

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

    if not api_client:
        await message.answer("API не настроен. Проверьте конфигурацию.")
        return

    # Show typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        result = await api_client.post(
            "/api/query",
            json={"query": message.text, "user_id": user_id},
        )
        response = result.get("response", "Нет ответа")
        await message.answer(response)

    except Exception as e:
        logger.error(f"API request failed: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
