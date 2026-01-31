"""Callback query handlers for inline buttons."""

import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from src.bot.decorators import require_api_client
from src.bot.formatters import (
    format_category_detail,
    format_examples_message,
    format_expense_deleted,
    format_expenses_list,
    format_help_message,
    format_statistics,
)
from src.bot.keyboards.inline import (
    get_back_to_menu_keyboard,
    get_back_to_stats_keyboard,
    get_category_detail_keyboard,
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
        "🏠 <b>Главное меню</b>\n\nВыберите действие или напишите сообщение:",
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
    """Handle show stats button - shows monthly stats with limits by default."""
    if not callback.message or not callback.from_user:
        return

    user_id = str(callback.from_user.id)

    # Show loading state
    await callback.message.edit_text("⏳ Загружаю статистику...")

    try:
        # Fetch stats and limits in parallel (use direct endpoint, not AI)
        result, limits_result = await asyncio.gather(
            api_client.get(f"/api/statistics/{user_id}/month"),
            api_client.get(f"/api/limits/{user_id}"),
        )
        limits = limits_result.get("limits", {})
        logger.info(f"Show stats for user {user_id}: loaded {len(limits)} limits")

        stats_text = format_statistics(
            result["statistics"],
            period="месяц",
            limits=limits if limits else None,
        )

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
            f"Delete callback failed for user {user_id}: {type(e).__name__}: {e}",
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
            f"Delete callback failed for user {user_id}: {type(e).__name__}: {e}",
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
        "💰 <b>Добавление расхода</b>\n\n📂 <b>Шаг 1/3:</b> Выбери категорию",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data == "stats_week")
@require_api_client
async def callback_stats_period(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle stats week button."""
    if not callback.message or not callback.from_user or not callback.data:
        return

    user_id = str(callback.from_user.id)

    await callback.message.edit_text("⏳ Загружаю статистику...")

    try:
        result = await api_client.get(f"/api/statistics/{user_id}/week")
        stats_text = format_statistics(
            result.get("statistics", {}),
            period="неделю",
            limits=None,
        )

        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_back_to_stats_keyboard(),
        )

    except Exception as e:
        logger.error(f"Stats week callback failed: {e}", exc_info=True)
        await callback.message.edit_text(
            "Не удалось получить статистику.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data == "stats_select_period")
async def callback_stats_select_period(callback: CallbackQuery) -> None:
    """Show period selection keyboard."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "📊 <b>Статистика</b>\n\nВыберите период:",
        parse_mode="HTML",
        reply_markup=get_stats_period_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stats_month_"))
@require_api_client
async def callback_stats_specific_month(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle specific month stats button (stats_month_YYYY_MM)."""
    if not callback.message or not callback.from_user or not callback.data:
        return

    # Parse: stats_month_2026_01 -> year=2026, month=01
    parts = callback.data.split("_")
    year = parts[2]
    month = parts[3]
    period = f"{year}_{month}"

    user_id = str(callback.from_user.id)

    await callback.message.edit_text("⏳ Загружаю статистику...")

    try:
        # Fetch stats and limits
        result_raw, limits_result = await asyncio.gather(
            api_client.get(
                f"/api/statistics/{user_id}/month",
                params={"period": period},
            ),
            api_client.get(f"/api/limits/{user_id}"),
        )
        result = result_raw.get("statistics", {})
        limits = limits_result.get("limits", {})

        period_display = _format_period_display(period)
        stats_text = format_statistics(
            result,
            period=period_display,
            limits=limits,
        )

        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_back_to_stats_keyboard(),
        )
    except Exception as e:
        logger.error(f"Stats month callback failed: {e}", exc_info=True)
        await callback.message.edit_text(
            "Не удалось получить статистику.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("cat_more_"))
@require_api_client
async def callback_category_more(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle 'show more' in category detail (cat_more_Category_period_offset)."""
    if not callback.message or not callback.from_user or not callback.data:
        return

    # Parse: cat_more_Еда_2026_01_10 -> category=Еда, period=2026_01, offset=10
    parts = callback.data.split("_")
    category = parts[2]
    period = f"{parts[3]}_{parts[4]}"
    offset = int(parts[5])

    user_id = str(callback.from_user.id)

    try:
        result = await api_client.get(
            f"/api/expenses/{user_id}/{category}",
            params={"period": period, "limit": 10, "offset": offset},
        )

        period_display = _format_period_display(period)
        text = format_category_detail(
            category=category,
            period=period_display,
            expenses=result.get("expenses", []),
            total=result.get("total", 0),
            shown=offset + result.get("count", 0),
            total_count=result.get("total_count", 0),
        )

        keyboard = get_category_detail_keyboard(
            category=category,
            period=period,
            offset=offset,
            has_more=result.get("has_more", False),
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Category more callback failed: {e}", exc_info=True)
        await callback.message.edit_text(
            "Не удалось загрузить данные.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


def _format_period_display(period: str) -> str:
    """Convert period code to display string."""
    if period == "week":
        return "неделю"
    if "_" in period:
        year, month = period.split("_")
        from src.bot.keyboards.inline import MONTH_NAMES

        return f"{MONTH_NAMES[int(month) - 1]} {year}"
    return period
