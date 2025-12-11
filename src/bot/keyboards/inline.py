"""Inline keyboards for the bot."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard shown after /start."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Статистика", callback_data="show_stats"),
                InlineKeyboardButton(text="📝 Последние", callback_data="show_last"),
            ],
            [
                InlineKeyboardButton(text="📖 Примеры", callback_data="show_examples"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="show_help"),
            ],
        ]
    )


def get_after_add_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard shown after adding an expense."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="delete_last"),
                InlineKeyboardButton(text="➕ Еще один", callback_data="add_more"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats"),
            ]
        ]
    )


def get_stats_period_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting statistics period."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Неделя", callback_data="stats_week"),
                InlineKeyboardButton(text="📅 Месяц", callback_data="stats_month"),
                InlineKeyboardButton(text="📅 Год", callback_data="stats_year"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"),
            ],
        ]
    )


def get_confirm_delete_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard for delete action."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete"),
            ]
        ]
    )


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Get simple back to menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu"),
            ]
        ]
    )
