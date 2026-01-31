"""Tests for bot keyboards."""

from datetime import datetime

from src.bot.keyboards.inline import get_stats_period_keyboard


def test_stats_period_keyboard_has_week_and_months():
    """Stats keyboard should have week + current month + 3 past months."""
    keyboard = get_stats_period_keyboard()

    # Flatten all button texts
    buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]

    # Should have week
    assert any("Неделя" in b for b in buttons)

    # Should NOT have year
    assert not any("Год" in b for b in buttons)

    # Should have current month (based on current date)
    now = datetime.now()
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    current_month_name = month_names[now.month - 1]
    assert any(current_month_name in b for b in buttons)


def test_stats_period_keyboard_has_four_months():
    """Stats keyboard should have exactly 4 month buttons."""
    keyboard = get_stats_period_keyboard()

    # Flatten all callback data
    callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]

    # Count month callbacks (format: stats_month_YYYY_MM)
    month_callbacks = [c for c in callbacks if c and c.startswith("stats_month_")]
    assert len(month_callbacks) == 4


def test_stats_period_keyboard_month_callback_format():
    """Month buttons should have callback format stats_month_YYYY_MM."""
    keyboard = get_stats_period_keyboard()

    # Find month callbacks
    callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
    month_callbacks = [c for c in callbacks if c and c.startswith("stats_month_")]

    # Verify format
    for callback in month_callbacks:
        parts = callback.split("_")
        assert len(parts) == 4  # stats, month, YYYY, MM
        assert parts[0] == "stats"
        assert parts[1] == "month"
        assert len(parts[2]) == 4  # YYYY
        assert len(parts[3]) == 2  # MM
        assert parts[2].isdigit()
        assert parts[3].isdigit()


def test_stats_period_keyboard_has_back_button():
    """Stats keyboard should have back to menu button."""
    keyboard = get_stats_period_keyboard()

    # Flatten all callback data
    callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]

    assert "back_to_menu" in callbacks
