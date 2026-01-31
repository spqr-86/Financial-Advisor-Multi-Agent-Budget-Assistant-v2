"""Command handlers for the bot."""

import asyncio
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.formatters import (
    CATEGORY_EMOJI,
    format_examples_message,
    format_expenses_list,
    format_help_message,
    format_limit_deleted,
    format_limit_set,
    format_limits,
    format_statistics,
)
from src.bot.decorators import require_api_client
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
@require_api_client
async def cmd_stats(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /stats command - show expense statistics."""
    if not message.from_user:
        return

    user_id = str(message.from_user.id)
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Request statistics and limits in parallel
        stats_result, limits_result = await asyncio.gather(
            api_client.post(
                "/api/query",
                json={
                    "query": "покажи статистику за месяц",
                    "user_id": user_id,
                },
            ),
            api_client.get(f"/api/limits/{user_id}"),
        )
        limits = limits_result.get("limits", {})

        # Format with limits for monthly stats
        if "statistics" in stats_result:
            stats_text = format_statistics(
                stats_result["statistics"],
                period="месяц",
                limits=limits if limits else None,
            )
        else:
            stats_text = stats_result.get("response", "Нет данных")

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

    except Exception as e:
        logger.error(
            f"Limit command failed for user {user_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer(
            "Не удалось выполнить команду. Попробуйте позже."
        )
