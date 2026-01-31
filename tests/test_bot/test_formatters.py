"""Tests for bot formatters."""

import pytest
from src.bot.formatters.messages import format_statistics, format_category_detail


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


def test_format_category_detail():
    """Format category detail should show numbered list of expenses."""
    expenses = [
        {"date": "28.01", "description": "Обед в кафе", "amount": 450},
        {"date": "27.01", "description": "Продукты", "amount": 1200},
    ]

    result = format_category_detail(
        category="Еда",
        period="январь 2026",
        expenses=expenses,
        total=1650,
        shown=2,
        total_count=2,
    )

    assert "Еда за январь 2026" in result
    assert "1️⃣" in result
    assert "28.01" in result
    assert "Обед в кафе" in result
    assert "450₽" in result
    assert "Итого: 1,650₽" in result or "Итого: 1 650₽" in result


def test_format_category_detail_with_more():
    """Format should show 'shown X of Y' when there are more items."""
    expenses = [{"date": "28.01", "description": "Test", "amount": 100}]

    result = format_category_detail(
        category="Еда",
        period="январь 2026",
        expenses=expenses,
        total=500,
        shown=10,
        total_count=25,
    )

    assert "показано 10 из 25" in result
