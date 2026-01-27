"""Reply keyboards for the bot."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def get_categories_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for selecting expense category."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛒 Продукты"),
                KeyboardButton(text="🚗 Транспорт"),
                KeyboardButton(text="🍔 Еда"),
            ],
            [
                KeyboardButton(text="🏠 Аренда"),
                KeyboardButton(text="💡 Коммуналка"),
                KeyboardButton(text="📱 Связь"),
            ],
            [
                KeyboardButton(text="👕 Одежда"),
                KeyboardButton(text="💊 Здоровье, красота, гигиена"),
                KeyboardButton(text="🍽️ Рестораны"),
            ],
            [
                KeyboardButton(text="🎁 Подарки"),
                KeyboardButton(text="🎭 Кино, театры, музеи"),
                KeyboardButton(text="💼 Прочее"),
            ],
            [
                KeyboardButton(text="❌ Отмена"),
            ],
        ],
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
