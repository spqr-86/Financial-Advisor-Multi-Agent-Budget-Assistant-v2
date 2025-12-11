"""Command handlers for the bot."""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.formatters import (
    format_examples_message,
    format_expenses_list,
    format_help_message,
    format_statistics,
)
from src.bot.keyboards.inline import (
    get_back_to_menu_keyboard,
    get_confirm_delete_keyboard,
    get_stats_period_keyboard,
)
from src.core.http_client import ServiceClient

logger = logging.getLogger(__name__)

router = Router(name="commands")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    if not message.from_user:
        return

    help_text = format_help_message()
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard(),
    )


@router.message(Command("stats"))
async def cmd_stats(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /stats command - show expense statistics."""
    if not message.from_user:
        return

    if not api_client:
        logger.error(f"API client not configured for user {message.from_user.id}")
        await message.answer("API не настроен. Проверьте конфигурацию.")
        return

    user_id = str(message.from_user.id)
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Request statistics from API
        result = await api_client.post(
            "/api/query",
            json={
                "query": "покажи статистику за неделю",
                "user_id": user_id,
            },
        )

        # Try to parse structured response or use plain text
        if "statistics" in result:
            stats_text = format_statistics(result["statistics"], period="неделю")
        else:
            stats_text = result.get("response", "Нет данных")

        await message.answer(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_stats_period_keyboard(),
        )

    except Exception as e:
        logger.error(
            f"Stats request failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer("Не удалось получить статистику. Попробуйте позже.")


@router.message(Command("last"))
async def cmd_last(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /last command - show recent expenses."""
    if not message.from_user:
        return

    if not api_client:
        logger.error(f"API client not configured for user {message.from_user.id}")
        await message.answer("API не настроен. Проверьте конфигурацию.")
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
