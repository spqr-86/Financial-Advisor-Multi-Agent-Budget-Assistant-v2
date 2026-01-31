"""Command handlers for the bot."""

import asyncio
import logging

from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.decorators import require_api_client
from src.bot.formatters import (
    CATEGORY_EMOJI,
    format_category_detail,
    format_examples_message,
    format_expenses_list,
    format_help_message,
    format_limit_deleted,
    format_limit_set,
    format_limits,
    format_statistics,
)
from src.bot.keyboards.inline import (
    get_back_to_menu_keyboard,
    get_back_to_stats_keyboard,
    get_category_detail_keyboard,
    get_category_period_keyboard,
    get_confirm_delete_keyboard,
    get_stats_period_keyboard,
)
from src.bot.utils import format_period_display
from src.core.categories import VALID_CATEGORIES
from src.core.exceptions import QuotaExceededError, ServiceUnavailableError
from src.core.http_client import ServiceClient

logger = logging.getLogger(__name__)

router = Router(name="commands")

MONTH_NAMES_LOWER = {
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,
}


def parse_stats_args(args: list[str]) -> tuple[str | None, str | None]:
    """Parse /stats command arguments.

    Returns:
        (category, period) tuple where:
        - category: category name or None
        - period: "week" or "YYYY_MM" or None
    """
    if not args:
        return None, None

    category = None
    period = None

    for arg in args:
        arg_lower = arg.lower()

        # Check if it's "week"
        if arg_lower == "неделя":
            period = "week"
            continue

        # Check if it's a month name
        if arg_lower in MONTH_NAMES_LOWER:
            month = MONTH_NAMES_LOWER[arg_lower]
            year = datetime.now().year
            # If month is in future, assume previous year
            if month > datetime.now().month:
                year -= 1
            period = f"{year}_{month:02d}"
            continue

        # Check if it's a category (case-insensitive)
        for valid_cat in VALID_CATEGORIES:
            if arg_lower == valid_cat.lower():
                category = valid_cat
                break

    return category, period


@router.message(Command("stats"))
@require_api_client
async def cmd_stats(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /stats command with optional arguments."""
    if not message.from_user:
        return

    user_id = str(message.from_user.id)
    args = message.text.split()[1:]  # Remove "/stats"

    category, period = parse_stats_args(args)

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        if category and period:
            # Show category detail for specific period
            result = await api_client.get(
                f"/api/expenses/{user_id}/{category}",
                params={"period": period, "limit": 10, "offset": 0},
            )

            period_display = format_period_display(period)
            text = format_category_detail(
                category=category,
                period=period_display,
                expenses=result.get("expenses", []),
                total=result.get("total", 0),
                shown=result.get("count", 0),
                total_count=result.get("total_count", 0),
            )
            keyboard = get_category_detail_keyboard(
                category=category,
                period=period,
                offset=0,
                has_more=result.get("has_more", False),
            )
        elif category:
            # Category without period - show period selection
            from src.core.categories import get_category_emoji

            emoji = get_category_emoji(category)
            text = f"{emoji} <b>{category}</b>\n\nВыберите период:"
            keyboard = get_category_period_keyboard(category)
        elif period:
            # Show stats for specific period
            if period == "week":
                result = await api_client.get(f"/api/statistics/{user_id}/week")
                period_display = "неделю"
                limits = None
            else:
                # Request statistics and limits in parallel
                result_raw, limits_result = await asyncio.gather(
                    api_client.get(
                        f"/api/statistics/{user_id}/month",
                        params={"period": period},
                    ),
                    api_client.get(f"/api/limits/{user_id}"),
                )
                result = result_raw.get("statistics", {})
                limits = limits_result.get("limits", {})
                period_display = format_period_display(period)

            text = format_statistics(
                result,
                period=period_display,
                limits=limits,
            )
            keyboard = get_back_to_stats_keyboard()
        else:
            # No args - show period selection
            text = "📊 <b>Статистика</b>\n\nВыберите период:"
            keyboard = get_stats_period_keyboard()

        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except asyncio.TimeoutError:
        await message.answer("Запрос занял слишком много времени. Попробуйте позже.")
    except ServiceUnavailableError:
        await message.answer("Сервис временно недоступен. Попробуйте позже.")
    except QuotaExceededError:
        await message.answer("Превышен лимит запросов. Подождите минуту.")
    except Exception as e:
        logger.error(f"Stats request failed: {e}", exc_info=True)
        await message.answer("Не удалось получить статистику. Попробуйте позже.")


@router.message(Command("last"))
@require_api_client
async def cmd_last(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /last command - show recent expenses."""
    if not message.from_user:
        return

    user_id = str(message.from_user.id)
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Request recent expenses from API
        result = await api_client.post(
            "/api/query",
            json={
                "query": "покажи последние 5 расходов",
                "user_id": user_id,
            },
        )

        # Try to parse structured response or use plain text
        if "expenses" in result:
            expenses_text = format_expenses_list(result["expenses"], limit=5)
        else:
            expenses_text = result.get("response", "Нет данных")

        await message.answer(
            expenses_text,
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except asyncio.TimeoutError:
        logger.warning(f"Last expenses request timeout for user {user_id}")
        await message.answer("Запрос занял слишком много времени. Попробуйте позже.")

    except ServiceUnavailableError:
        logger.warning(f"Service unavailable for last request from user {user_id}")
        await message.answer("Сервис временно недоступен. Попробуйте позже.")

    except QuotaExceededError:
        logger.warning(f"Quota exceeded for last request from user {user_id}")
        await message.answer("Превышен лимит запросов. Подождите минуту.")

    except Exception as e:
        logger.error(
            f"Last expenses request failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer("Не удалось получить список расходов. Попробуйте позже.")


@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    """Handle /delete command - confirm before deleting last expense."""
    if not message.from_user:
        return

    await message.answer(
        "⚠️ <b>Удалить последний расход?</b>\n\nЭто действие нельзя отменить.",
        parse_mode="HTML",
        reply_markup=get_confirm_delete_keyboard(),
    )


@router.message(Command("examples"))
async def cmd_examples(message: Message) -> None:
    """Handle /examples command - show usage examples."""
    if not message.from_user:
        return

    examples_text = format_examples_message()
    await message.answer(
        examples_text,
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard(),
    )


@router.message(Command("limit"))
@require_api_client
async def cmd_limit(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /limit command - manage budget limits."""
    if not message.from_user:
        return

    user_id = str(message.from_user.id)
    args = message.text.split()[1:]  # Remove "/limit"

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        if not args:
            # Show all limits
            result = await api_client.get(f"/api/limits/{user_id}")
            limits = result.get("limits", {})
            await message.answer(
                format_limits(limits),
                parse_mode="HTML",
            )

        elif len(args) == 2:
            category, amount_str = args[0], args[1]

            # Validate category
            if category not in CATEGORY_EMOJI:
                categories_list = ", ".join(sorted(CATEGORY_EMOJI.keys()))
                await message.answer(
                    f"❌ Неизвестная категория: <b>{category}</b>\n\n"
                    f"Доступные категории:\n<code>{categories_list}</code>",
                    parse_mode="HTML",
                )
                return

            # Parse amount
            try:
                amount = float(amount_str.replace(",", "."))
            except ValueError:
                await message.answer(
                    "❌ Неверная сумма. Используйте число.\n\n"
                    "Пример: <code>/limit Еда 10000</code>",
                    parse_mode="HTML",
                )
                return

            if amount <= 0:
                # Delete limit
                await api_client.delete(f"/api/limits/{user_id}/{category}")
                await message.answer(
                    format_limit_deleted(category),
                    parse_mode="HTML",
                )
            else:
                # Set limit
                await api_client.post(
                    "/api/limits",
                    json={
                        "user_id": user_id,
                        "category": category,
                        "amount": amount,
                    },
                )
                await message.answer(
                    format_limit_set(category, amount),
                    parse_mode="HTML",
                )

        else:
            await message.answer(
                "❌ Неверный формат команды.\n\n"
                "Использование:\n"
                "<code>/limit</code> — показать все лимиты\n"
                "<code>/limit Категория Сумма</code> — установить лимит\n"
                "<code>/limit Категория 0</code> — удалить лимит\n\n"
                "Пример: <code>/limit Еда 10000</code>",
                parse_mode="HTML",
            )

    except asyncio.TimeoutError:
        logger.warning(f"Limit command timeout for user {user_id}")
        await message.answer("Запрос занял слишком много времени. Попробуйте позже.")

    except ServiceUnavailableError:
        logger.warning(f"Service unavailable for limit command from user {user_id}")
        await message.answer("Сервис временно недоступен. Попробуйте позже.")

    except QuotaExceededError:
        logger.warning(f"Quota exceeded for limit command from user {user_id}")
        await message.answer("Превышен лимит запросов. Подождите минуту.")

    except Exception as e:
        logger.error(
            f"Limit command failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer("Не удалось выполнить команду. Попробуйте позже.")
