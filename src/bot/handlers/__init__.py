"""Bot handlers."""

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.bot.keyboards import get_main_menu_keyboard
from src.bot.utils import split_long_message
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

    welcome_text = (
        f"👋 Привет, <b>{name}</b>!\n\n"
        "Я <b>Budget Assistant v2.0</b> - твой личный помощник по финансам\n\n"
        "🎯 <b>Что я умею:</b>\n"
        "• Записываю расходы в Google Sheets\n"
        "• Автоматически определяю категории\n"
        "• Показываю статистику и аналитику\n"
        "• Даю советы по экономии\n\n"
        "📝 <b>Попробуй написать:</b>\n"
        "<code>купил хлеб 50 рублей</code>\n\n"
        "или используй кнопки ниже ⬇️"
    )

    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
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
    query_preview = (
        message.text[:50] + "..." if len(message.text) > 50 else message.text
    )

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

        # Detect if expense was added and show appropriate keyboard
        # Simple heuristic: look for success indicators
        from src.bot.keyboards import get_after_add_keyboard

        show_after_add_keyboard = any(
            keyword in response.lower()
            for keyword in ["добавлен", "записал", "сохранил", "добавил"]
        )

        # Send all chunks
        for i, chunk in enumerate(message_chunks):
            # Add keyboard only to the last message if expense was added
            keyboard = None
            if show_after_add_keyboard and i == len(message_chunks) - 1:
                keyboard = get_after_add_keyboard()

            await message.answer(
                chunk,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

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
