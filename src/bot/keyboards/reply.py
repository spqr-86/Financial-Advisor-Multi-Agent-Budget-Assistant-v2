"""Reply keyboards for the bot."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from src.core.categories import KEYBOARD_CATEGORIES, get_category_with_emoji


def get_categories_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for selecting expense category."""
    keyboard = [
        [KeyboardButton(text=get_category_with_emoji(cat)) for cat in row]
        for row in KEYBOARD_CATEGORIES
    ]
    keyboard.append([KeyboardButton(text="❌ Отмена")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_amount_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for quick amount selection."""
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


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard."""
    return ReplyKeyboardRemove()
