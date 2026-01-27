"""Structured input handlers with FSM for step-by-step expense adding."""

import logging
import re

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.formatters import format_expense_added
from src.bot.keyboards import (
    get_after_add_keyboard,
    get_amount_keyboard,
    get_categories_keyboard,
    remove_keyboard,
)
from src.bot.states import AddExpenseStates
from src.core.http_client import ServiceClient

logger = logging.getLogger(__name__)

router = Router(name="structured")


# Category name mapping (with emoji removed)
CATEGORY_MAP = {
    "🛒 Продукты": "Продукты",
    "🚗 Транспорт": "Транспорт",
    "🍔 Еда": "Еда",
    "🏠 Аренда": "Аренда",
    "💡 Коммуналка": "Коммуналка",
    "📱 Связь": "Связь",
    "👕 Одежда": "Одежда",
    "💊 Здоровье, красота, гигиена": "Здоровье, красота, гигиена",
    "🍽️ Рестораны": "Рестораны",
    "🎁 Подарки": "Подарки",
    "🎭 Кино, театры, музеи": "Кино, театры, музеи",
    "💼 Прочее": "Прочее",
}


@router.message(Command("add"))
async def cmd_add_start(message: Message, state: FSMContext) -> None:
    """Start structured expense adding flow.

    Step 1: Ask for category.
    """
    if not message.from_user:
        return

    await state.set_state(AddExpenseStates.category)

    await message.answer(
        "💰 <b>Добавление расхода</b>\n\n"
        "📂 <b>Шаг 1/3:</b> Выбери категорию",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(),
    )


@router.message(AddExpenseStates.category, F.text == "❌ Отмена")
async def add_cancel_category(message: Message, state: FSMContext) -> None:
    """Cancel adding expense from category step."""
    await state.clear()
    await message.answer(
        "❌ Добавление расхода отменено",
        parse_mode="HTML",
        reply_markup=remove_keyboard(),
    )


@router.message(AddExpenseStates.category, F.text)
async def add_category_selected(message: Message, state: FSMContext) -> None:
    """Process category selection.

    Step 2: Ask for amount.
    """
    if not message.text:
        return

    # Map category with emoji to clean category name
    category = CATEGORY_MAP.get(message.text, message.text)

    # Save category to state
    await state.update_data(category=category)
    await state.set_state(AddExpenseStates.amount)

    await message.answer(
        f"✅ Категория: <b>{category}</b>\n\n"
        "💰 <b>Шаг 2/3:</b> Введи сумму\n\n"
        "Можешь написать число (например, <code>150</code>) "
        "или выбрать из кнопок:",
        parse_mode="HTML",
        reply_markup=get_amount_keyboard(),
    )


@router.message(AddExpenseStates.amount, F.text == "❌ Отмена")
async def add_cancel_amount(message: Message, state: FSMContext) -> None:
    """Cancel adding expense from amount step."""
    await state.clear()
    await message.answer(
        "❌ Добавление расхода отменено",
        parse_mode="HTML",
        reply_markup=remove_keyboard(),
    )


@router.message(AddExpenseStates.amount, F.text)
async def add_amount_entered(message: Message, state: FSMContext) -> None:
    """Process amount input.

    Step 3: Ask for description (optional).
    """
    if not message.text:
        return

    # Extract number from text (e.g., "500₽" -> 500)
    amount_text = message.text.replace("₽", "").replace(",", ".").strip()

    # Try to parse as number
    try:
        amount = float(amount_text)
        if amount <= 0:
            await message.answer(
                "❌ Сумма должна быть больше нуля. Попробуй еще раз:",
                parse_mode="HTML",
            )
            return

        # Save amount to state
        await state.update_data(amount=amount)
        await state.set_state(AddExpenseStates.description)

        await message.answer(
            f"✅ Сумма: <b>{amount:.0f}₽</b>\n\n"
            "📝 <b>Шаг 3/3:</b> Добавь описание (опционально)\n\n"
            "Напиши что купил, или отправь /skip чтобы пропустить",
            parse_mode="HTML",
            reply_markup=remove_keyboard(),
        )

    except ValueError:
        await message.answer(
            "❌ Не могу распознать сумму. "
            "Введи число (например, <code>150</code> или <code>1500</code>):",
            parse_mode="HTML",
        )


@router.message(AddExpenseStates.description, Command("skip"))
async def add_skip_description(
    message: Message,
    state: FSMContext,
    api_client: ServiceClient | None = None,
) -> None:
    """Skip description and save expense."""
    await add_finish(message, state, api_client, description="")


@router.message(AddExpenseStates.description, F.text)
async def add_description_entered(
    message: Message,
    state: FSMContext,
    api_client: ServiceClient | None = None,
) -> None:
    """Process description and save expense."""
    if not message.text:
        return

    await add_finish(message, state, api_client, description=message.text)


async def add_finish(
    message: Message,
    state: FSMContext,
    api_client: ServiceClient | None,
    description: str,
) -> None:
    """Finish adding expense - send to API and clear state."""
    if not message.from_user:
        return

    if not api_client:
        logger.error(f"API client not configured for user {message.from_user.id}")
        await message.answer("API не настроен. Проверьте конфигурацию.")
        await state.clear()
        return

    # Get data from state
    data = await state.get_data()
    category = data.get("category", "Другое")
    amount = data.get("amount", 0)

    user_id = str(message.from_user.id)

    # Show typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Send to API
        # Note: We use the natural language endpoint here because the backend
        # expects a query string. The AI will understand this structured format.
        query = f"добавь расход категория {category} сумма {amount}"
        if description:
            query += f" описание {description}"

        logger.info(
            f"Adding structured expense for user {user_id}: "
            f"{category}, {amount}₽, '{description}'"
        )

        result = await api_client.post(
            "/api/query",
            json={"query": query, "user_id": user_id},
        )

        # Format success message
        success_text = format_expense_added(
            category=category,
            amount=amount,
            description=description,
        )

        await message.answer(
            success_text,
            parse_mode="HTML",
            reply_markup=get_after_add_keyboard(),
        )

        # Clear state
        await state.clear()

    except Exception as e:
        logger.error(
            f"Failed to add expense for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer(
            "❌ Не удалось добавить расход. Попробуй позже.",
            parse_mode="HTML",
        )
        await state.clear()
