"""Reply keyboards for the bot (for structured input in future phases)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_categories_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for selecting expense category.

    Note: This will be used in Phase 2 for /add command with FSM.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🍕 Еда"),
                KeyboardButton(text="🚗 Транспорт"),
                KeyboardButton(text="🏠 Дом"),
            ],
            [
                KeyboardButton(text="🎮 Развлечения"),
                KeyboardButton(text="💊 Здоровье"),
                KeyboardButton(text="👕 Одежда"),
            ],
            [
                KeyboardButton(text="🎓 Образование"),
                KeyboardButton(text="💼 Другое"),
                KeyboardButton(text="❌ Отмена"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_amount_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for quick amount selection.

    Note: This will be used in Phase 2 for /add command with FSM.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="50₽"),
                KeyboardButton(text="100₽"),
                KeyboardButton(text="200₽"),
                KeyboardButton(text="500₽"),
            ],
            [
                KeyboardButton(text="1000₽"),
                KeyboardButton(text="2000₽"),
                KeyboardButton(text="5000₽"),
                KeyboardButton(text="❌ Отмена"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
