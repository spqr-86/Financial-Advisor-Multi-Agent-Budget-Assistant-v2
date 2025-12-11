"""Telegram keyboards module."""

from src.bot.keyboards.inline import (
    get_after_add_keyboard,
    get_back_to_menu_keyboard,
    get_confirm_delete_keyboard,
    get_main_menu_keyboard,
    get_stats_period_keyboard,
)

__all__ = [
    "get_after_add_keyboard",
    "get_main_menu_keyboard",
    "get_stats_period_keyboard",
    "get_confirm_delete_keyboard",
    "get_back_to_menu_keyboard",
]
