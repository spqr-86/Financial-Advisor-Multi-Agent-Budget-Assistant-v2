# tests/test_bot/test_commands.py
import pytest
from src.bot.handlers.commands import parse_stats_args


def test_parse_stats_args_empty():
    """Empty args should return None, None."""
    category, period = parse_stats_args([])
    assert category is None
    assert period is None


def test_parse_stats_args_week():
    """'неделя' should be recognized as period."""
    category, period = parse_stats_args(["неделя"])
    assert category is None
    assert period == "week"


def test_parse_stats_args_month_name():
    """Month name should be recognized."""
    category, period = parse_stats_args(["январь"])
    assert category is None
    # Current month is January 2026 in the test environment (based on env)
    assert period == "2026_01"


def test_parse_stats_args_category():
    """Category name should be recognized."""
    category, period = parse_stats_args(["Еда"])
    assert category == "Еда"
    assert period is None  # Default to current month in handler


def test_parse_stats_args_category_and_month():
    """Both category and month."""
    category, period = parse_stats_args(["Еда", "январь"])
    assert category == "Еда"
    assert period == "2026_01"
