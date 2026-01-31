"""Tests for bot formatters."""

import pytest
from src.bot.formatters.messages import format_statistics


def test_format_statistics_week_no_progress_bar():
    """Week statistics should NOT show progress bars."""
    stats = {
        "categories": {"Еда": 3500, "Транспорт": 1200},
        "total": 4700,
    }

    result = format_statistics(stats, period="неделю")

    # Should NOT have progress bar characters
    assert "█" not in result
    assert "░" not in result
    assert "%" not in result

    # Should have amounts
    assert "3,500₽" in result or "3 500₽" in result
    assert "Итого" in result


def test_format_statistics_month_with_limit_shows_progress():
    """Month statistics WITH limits should show progress bars."""
    stats = {
        "categories": {"Еда": 8000},
        "total": 8000,
    }
    limits = {"Еда": 10000}

    result = format_statistics(stats, period="январь 2026", limits=limits)

    # Should have progress bar
    assert "█" in result
    assert "80%" in result
