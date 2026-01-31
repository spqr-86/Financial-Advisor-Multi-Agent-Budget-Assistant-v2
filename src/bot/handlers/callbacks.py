"""Callback query handlers for inline buttons."""

import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.bot.decorators import require_api_client
from src.bot.formatters import (
    format_examples_message,
    format_expense_deleted,
    format_expenses_list,
    format_help_message,
    format_statistics,
)
from src.bot.keyboards.inline import (
    get_back_to_menu_keyboard,
    get_main_menu_keyboard,
    get_stats_period_keyboard,
)
from src.bot.keyboards.reply import get_categories_keyboard
from src.bot.states import AddExpenseStates
from src.core.exceptions import QuotaExceededError, ServiceUnavailableError
from src.core.http_client import ServiceClient

logger = logging.getLogger(__name__)

router = Router(name="callbacks")


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery) -> None:
    """Handle back to menu button."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие или напишите сообщение:",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "show_help")
async def callback_show_help(callback: CallbackQuery) -> None:
    """Handle show help button."""
    if not callback.message:
        return

    help_text = format_help_message()
    await callback.message.edit_text(
        help_text,
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "show_examples")
async def callback_show_examples(callback: CallbackQuery) -> None:
    """Handle show examples button."""
    if not callback.message:
        return

    examples_text = format_examples_message()
    await callback.message.edit_text(
        examples_text,
        parse_mode="HTML",
        reply_markup=get_back_to_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "show_stats")
@require_api_client
async def callback_show_stats(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle show stats button."""
    if not callback.message or not callback.from_user:
        return

    user_id = str(callback.from_user.id)

    # Show loading state
    await callback.message.edit_text("⏳ Загружаю статистику...")

    try:
        result = await api_client.post(
            "/api/query",
            json={
                "query": "покажи статистику за неделю",
                "user_id": user_id,
            },
        )

        if "statistics" in result:
            stats_text = format_statistics(result["statistics"], period="неделю")
        else:
            stats_text = result.get("response", "Нет данных")

        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_stats_period_keyboard(),
        )

    except asyncio.TimeoutError:
        logger.warning(f"Stats callback timeout for user {user_id}")
        await callback.message.edit_text(
            "Запрос занял слишком много времени. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except ServiceUnavailableError:
        logger.warning(f"Service unavailable for stats callback from user {user_id}")
        await callback.message.edit_text(
            "Сервис временно недоступен. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except QuotaExceededError:
        logger.warning(f"Quota exceeded for stats callback from user {user_id}")
        await callback.message.edit_text(
            "Превышен лимит запросов. Подождите минуту.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except Exception as e:
        logger.error(
            f"Stats callback failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await callback.message.edit_text(
            "Не удалось получить статистику. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data == "show_last")
@require_api_client
async def callback_show_last(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle show last expenses button."""
    if not callback.message or not callback.from_user:
        return

    user_id = str(callback.from_user.id)

    # Show loading state
    await callback.message.edit_text("⏳ Загружаю последние расходы...")

    try:
        result = await api_client.post(
            "/api/query",
            json={
                "query": "покажи последние 5 расходов",
                "user_id": user_id,
            },
        )

        if "expenses" in result:
            expenses_text = format_expenses_list(result["expenses"], limit=5)
        else:
            expenses_text = result.get("response", "Нет данных")

        await callback.message.edit_text(
            expenses_text,
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except asyncio.TimeoutError:
        logger.warning(f"Last expenses callback timeout for user {user_id}")
        await callback.message.edit_text(
            "Запрос занял слишком много времени. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except ServiceUnavailableError:
        logger.warning(f"Service unavailable for last callback from user {user_id}")
        await callback.message.edit_text(
            "Сервис временно недоступен. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except QuotaExceededError:
        logger.warning(f"Quota exceeded for last callback from user {user_id}")
        await callback.message.edit_text(
            "Превышен лимит запросов. Подождите минуту.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except Exception as e:
        logger.error(
            f"Last expenses callback failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await callback.message.edit_text(
            "Не удалось получить список расходов. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data == "confirm_delete")
@require_api_client
async def callback_confirm_delete(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle confirm delete button."""
    if not callback.message or not callback.from_user:
        return

    user_id = str(callback.from_user.id)

    # Show loading state
    await callback.message.edit_text("⏳ Удаляю последний расход...")

    try:
        await api_client.post(
            "/api/query",
            json={
                "query": "удали последний расход",
                "user_id": user_id,
            },
        )

        delete_text = format_expense_deleted()

        await callback.message.edit_text(
            delete_text,
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except asyncio.TimeoutError:
        logger.warning(f"Delete callback timeout for user {user_id}")
        await callback.message.edit_text(
            "Запрос занял слишком много времени. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except ServiceUnavailableError:
        logger.warning(f"Service unavailable for delete callback from user {user_id}")
        await callback.message.edit_text(
            "Сервис временно недоступен. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except QuotaExceededError:
        logger.warning(f"Quota exceeded for delete callback from user {user_id}")
        await callback.message.edit_text(
            "Превышен лимит запросов. Подождите минуту.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except Exception as e:
        logger.error(
            f"Delete callback failed for user {user_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )
        await callback.message.edit_text(
            "Не удалось удалить расход. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data == "cancel_delete")
async def callback_cancel_delete(callback: CallbackQuery) -> None:
    """Handle cancel delete button."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "❌ Удаление отменено",
        reply_markup=get_back_to_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "delete_last")
@require_api_client
async def callback_delete_last(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle delete last expense button (from after_add keyboard)."""
    if not callback.message or not callback.from_user:
        return

    user_id = str(callback.from_user.id)

    try:
        await api_client.post(
            "/api/query",
            json={
                "query": "удали последний расход",
                "user_id": user_id,
            },
        )

        delete_text = format_expense_deleted()

        await callback.message.edit_text(
            delete_text,
            parse_mode="HTML",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except asyncio.TimeoutError:
        logger.warning(f"Delete last callback timeout for user {user_id}")
        await callback.message.edit_text(
            "Запрос занял слишком много времени. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except ServiceUnavailableError:
        logger.warning(f"Service unavailable for delete last from user {user_id}")
        await callback.message.edit_text(
            "Сервис временно недоступен. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except QuotaExceededError:
        logger.warning(f"Quota exceeded for delete last from user {user_id}")
        await callback.message.edit_text(
            "Превышен лимит запросов. Подождите минуту.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except Exception as e:
        logger.error(
            f"Delete callback failed for user {user_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )
        await callback.message.edit_text(
            "Не удалось удалить расход. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer("Расход удален")


@router.callback_query(F.data == "add_more")
async def callback_add_more(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle add more expense button - start structured /add flow."""
    if not callback.message:
        return

    # Start FSM flow for adding expense
    await state.set_state(AddExpenseStates.category)

    # Delete the previous message (with inline keyboard)
    await callback.message.delete()

    # Send new message with reply keyboard
    await callback.message.answer(
        "💰 <b>Добавление расхода</b>\n\n"
        "📂 <b>Шаг 1/3:</b> Выбери категорию",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data.in_({"stats_week", "stats_month", "stats_year"}))
@require_api_client
async def callback_stats_period(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle stats period selection buttons."""
    if not callback.message or not callback.from_user or not callback.data:
        return

    period_map = {
        "stats_week": ("неделю", "покажи статистику за неделю"),
        "stats_month": ("месяц", "покажи статистику за месяц"),
        "stats_year": ("год", "покажи статистику за год"),
    }

    period_name, query = period_map.get(callback.data, ("неделю", "покажи статистику"))
    user_id = str(callback.from_user.id)

    await callback.message.edit_text("⏳ Загружаю статистику...")

    try:
        # Fetch stats and limits in parallel for monthly stats
        if callback.data == "stats_month":
            result, limits_result = await asyncio.gather(
                api_client.post(
                    "/api/query",
                    json={"query": query, "user_id": user_id},
                ),
                api_client.get(f"/api/limits/{user_id}"),
            )
            limits = limits_result.get("limits", {})
        else:
            result = await api_client.post(
                "/api/query",
                json={"query": query, "user_id": user_id},
            )
            limits = None

        if "statistics" in result:
            stats_text = format_statistics(
                result["statistics"],
                period=period_name,
                limits=limits if limits else None,
            )
        else:
            stats_text = result.get("response", "Нет данных")

        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_stats_period_keyboard(),
        )

    except asyncio.TimeoutError:
        logger.warning(f"Stats period callback timeout for user {user_id}")
        await callback.message.edit_text(
            "Запрос занял слишком много времени. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except ServiceUnavailableError:
        logger.warning(f"Service unavailable for stats period from user {user_id}")
        await callback.message.edit_text(
            "Сервис временно недоступен. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except QuotaExceededError:
        logger.warning(f"Quota exceeded for stats period from user {user_id}")
        await callback.message.edit_text(
            "Превышен лимит запросов. Подождите минуту.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    except Exception as e:
        logger.error(
            f"Stats period callback failed for user {user_id}: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )
        await callback.message.edit_text(
            "Не удалось получить статистику. Попробуйте позже.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()
