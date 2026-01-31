"""Inline keyboards for the bot."""

from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

MONTH_NAMES = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]


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
    """Get keyboard for selecting statistics period.

    Shows week button + last 4 months (current + 3 past).
    Month callbacks use format: stats_month_YYYY_MM
    """
    now = datetime.now()
    current_month = now.month  # 1-12
    current_year = now.year

    # Generate last 4 months (current + 3 past)
    months = []
    for i in range(4):
        month_idx = current_month - i
        year = current_year
        if month_idx <= 0:
            month_idx += 12
            year -= 1
        month_name = MONTH_NAMES[month_idx - 1]
        # Callback: stats_month_YYYY_MM
        callback = f"stats_month_{year}_{month_idx:02d}"
        # Current month gets year suffix for clarity
        label = f"📅 {month_name} {year}" if i == 0 else month_name
        months.append((label, callback))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Неделя", callback_data="stats_week"),
                InlineKeyboardButton(text=months[0][0], callback_data=months[0][1]),
            ],
            [
                InlineKeyboardButton(text=months[1][0], callback_data=months[1][1]),
                InlineKeyboardButton(text=months[2][0], callback_data=months[2][1]),
                InlineKeyboardButton(text=months[3][0], callback_data=months[3][1]),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад в меню", callback_data="back_to_menu"
                ),
            ],
        ]
    )


def get_confirm_delete_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard for delete action."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить", callback_data="confirm_delete"
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete"),
            ]
        ]
    )


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Get simple back to menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад в меню", callback_data="back_to_menu"
                ),
            ]
        ]
    )


def get_category_detail_keyboard(
    category: str,
    period: str,
    offset: int,
    has_more: bool,
) -> InlineKeyboardMarkup:
    """Get keyboard for category detail view with pagination.

    Args:
        category: Category name
        period: Period string (e.g., "2026_01" or "week")
        offset: Current offset for pagination
        has_more: Whether there are more items to load
    """
    buttons = []

    if has_more:
        next_offset = offset + 10
        callback = f"cat_more_{category}_{period}_{next_offset}"
        buttons.append(
            [
                InlineKeyboardButton(text="⬇️ Показать ещё", callback_data=callback),
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="stats_select_period"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
