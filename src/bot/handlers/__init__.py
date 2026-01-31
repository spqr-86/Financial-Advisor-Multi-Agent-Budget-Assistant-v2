"""Bot handlers."""

import asyncio
import logging
import re

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.bot.decorators import require_api_client
from src.bot.formatters import format_statistics
from src.bot.keyboards import get_after_add_keyboard, get_main_menu_keyboard
from src.bot.utils import send_chunked_message
from src.core.exceptions import QuotaExceededError, ServiceUnavailableError
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
@require_api_client
async def handle_text(
    message: Message,
    api_client: ServiceClient | None = None,
    request_id: str | None = None,
) -> None:
    """Handle all text messages."""
    if not message.from_user or not message.text:
        return

    user_id = str(message.from_user.id)
    req_id = request_id or "no-id"
    query_preview = (
        message.text[:50] + "..." if len(message.text) > 50 else message.text
    )

    # Show typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    logger.info(f"[{req_id}] Processing query from user {user_id}: {query_preview}")

    try:
        # Check if this is a monthly stats request (to load limits)
        query_lower = message.text.lower()
        is_monthly_stats = (
            "месяц" in query_lower
            and any(kw in query_lower for kw in ["статистик", "расход", "потратил"])
        )

        if is_monthly_stats:
            # Fetch stats and limits in parallel for monthly stats
            result, limits_result = await asyncio.gather(
                api_client.post(
                    "/api/query",
                    json={"query": message.text, "user_id": user_id},
                ),
                api_client.get(f"/api/limits/{user_id}"),
            )
            limits = limits_result.get("limits", {})
            logger.info(
                f"[{req_id}] Monthly stats for user {user_id}: "
                f"loaded {len(limits)} limits"
            )
        else:
            result = await api_client.post(
                "/api/query",
                json={"query": message.text, "user_id": user_id},
            )
            limits = None

        # If response contains statistics data, format it properly with limits
        if "statistics" in result:
            period = "месяц" if is_monthly_stats else "неделю"
            response = format_statistics(
                result["statistics"],
                period=period,
                limits=limits if limits else None,
            )
        else:
            response = result.get("response", "Нет ответа")

        logger.info(f"[{req_id}] Response for user {user_id}: {len(response)} chars")

        # Detect if expense was added
        show_keyboard = any(
            kw in response.lower()
            for kw in ["добавлен", "записал", "сохранил", "добавил"]
        )
        keyboard = get_after_add_keyboard() if show_keyboard else None

        # Handle limit warnings
        limit_warning_pattern = (
            r"⚠️ Превышен лимит по категории ([^:]+): ([\d,]+)₽ из ([\d,]+)₽"
        )
        limit_match = re.search(limit_warning_pattern, response)

        if limit_match:
            await _handle_limit_warning(message, response, limit_match, keyboard)
        else:
            await send_chunked_message(message, response, keyboard)

    except asyncio.TimeoutError:
        logger.warning(f"[{req_id}] Request timeout for user {user_id}: {query_preview}")
        await message.answer(
            "Обработка запроса заняла слишком много времени. "
            "Попробуйте упростить запрос или повторите позже."
        )

    except ServiceUnavailableError:
        logger.warning(f"[{req_id}] Service unavailable for user {user_id}")
        await message.answer(
            "Сервис временно недоступен. Попробуйте через несколько минут."
        )

    except QuotaExceededError:
        logger.warning(f"[{req_id}] Quota exceeded for user {user_id}")
        await message.answer(
            "Превышен лимит запросов к AI. Подождите минуту и попробуйте снова."
        )

    except Exception as e:
        logger.error(
            f"[{req_id}] API request failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer("Произошла ошибка. Попробуйте позже.")


async def _handle_limit_warning(
    message: Message,
    response: str,
    limit_match: re.Match,
    keyboard,
) -> None:
    """Handle response with limit warning - send main text and warning separately."""
    from src.bot.formatters import format_limit_exceeded

    category = limit_match.group(1).strip()
    spent_str = limit_match.group(2).replace(",", "")
    limit_str = limit_match.group(3).replace(",", "")

    try:
        spent = float(spent_str)
        limit = float(limit_str)

        # Remove warning from main response
        clean_response = re.sub(
            r"⚠️ Превышен лимит по категории [^:]+: [\d,]+₽ из [\d,]+₽",
            "",
            response,
        ).strip()

        # Send main response
        await send_chunked_message(message, clean_response, keyboard)

        # Send formatted warning
        await message.answer(
            format_limit_exceeded(category, spent, limit),
            parse_mode="HTML",
        )

    except (ValueError, IndexError):
        # Parsing failed - send as-is
        await send_chunked_message(message, response, keyboard)
