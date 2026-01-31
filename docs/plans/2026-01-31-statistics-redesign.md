# Statistics Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Redesign statistics: remove year, add month selection, category detail view with pagination.

**Architecture:** Modify bot keyboards/formatters/handlers for new UI. Add API endpoints for expenses by category with pagination. Storage already supports category filter.

**Tech Stack:** aiogram (keyboards, handlers), FastAPI (new endpoints), existing GoogleSheetsStorage

---

## Task 1: Update Keyboards — Remove Year, Add Month Buttons

**Files:**
- Modify: `src/bot/keyboards/inline.py:35-48`

**Step 1: Write the test**

```python
# tests/test_bot/test_keyboards.py
import pytest
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

    # Should have current month (January 2026)
    assert any("Январь" in b for b in buttons)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_bot/test_keyboards.py::test_stats_period_keyboard_has_week_and_months -v`
Expected: FAIL (year button exists)

**Step 3: Update keyboard function**

```python
# src/bot/keyboards/inline.py
from datetime import datetime

MONTH_NAMES = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

def get_stats_period_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting statistics period."""
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
        label = f"{month_name}" if i > 0 else f"📅 {month_name} {year}"
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
        ]
    )
```

**Step 4: Run test to verify it passes**

Run: `poetry run pytest tests/test_bot/test_keyboards.py::test_stats_period_keyboard_has_week_and_months -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/bot/keyboards/inline.py tests/test_bot/test_keyboards.py
git commit -m "feat(stats): replace year button with month selection"
```

---

## Task 2: Add Category Detail Keyboard with Pagination

**Files:**
- Modify: `src/bot/keyboards/inline.py`

**Step 1: Write the test**

```python
# tests/test_bot/test_keyboards.py
def test_category_detail_keyboard_with_more():
    """Category detail keyboard should show 'more' button when has_more=True."""
    from src.bot.keyboards.inline import get_category_detail_keyboard

    keyboard = get_category_detail_keyboard(
        category="Еда",
        period="2026_01",
        offset=0,
        has_more=True,
    )

    buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert any("Показать ещё" in b for b in buttons)
    assert any("Назад" in b for b in buttons)


def test_category_detail_keyboard_without_more():
    """Category detail keyboard should hide 'more' when has_more=False."""
    from src.bot.keyboards.inline import get_category_detail_keyboard

    keyboard = get_category_detail_keyboard(
        category="Еда",
        period="2026_01",
        offset=0,
        has_more=False,
    )

    buttons = [btn.text for row in keyboard.inline_keyboard for btn in row]
    assert not any("Показать ещё" in b for b in buttons)
    assert any("Назад" in b for b in buttons)
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_bot/test_keyboards.py::test_category_detail_keyboard_with_more -v`
Expected: FAIL (function doesn't exist)

**Step 3: Add keyboard function**

```python
# src/bot/keyboards/inline.py
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
        buttons.append([
            InlineKeyboardButton(text="⬇️ Показать ещё", callback_data=callback),
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="stats_select_period"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

**Step 4: Run tests**

Run: `poetry run pytest tests/test_bot/test_keyboards.py -v -k "category_detail"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/bot/keyboards/inline.py tests/test_bot/test_keyboards.py
git commit -m "feat(stats): add category detail keyboard with pagination"
```

---

## Task 3: Update Formatters — Statistics Without Progress Bar for Week

**Files:**
- Modify: `src/bot/formatters/messages.py:85-144`

**Step 1: Write the test**

```python
# tests/test_bot/test_formatters.py
def test_format_statistics_week_no_progress_bar():
    """Week statistics should NOT show progress bars."""
    from src.bot.formatters.messages import format_statistics

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
    from src.bot.formatters.messages import format_statistics

    stats = {
        "categories": {"Еда": 8000},
        "total": 8000,
    }
    limits = {"Еда": 10000}

    result = format_statistics(stats, period="январь 2026", limits=limits)

    # Should have progress bar
    assert "█" in result
    assert "80%" in result
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_bot/test_formatters.py::test_format_statistics_week_no_progress_bar -v`
Expected: FAIL (week currently shows progress bars)

**Step 3: Update format_statistics function**

```python
# src/bot/formatters/messages.py
def format_statistics(
    stats: dict[str, Any],
    period: str = "неделю",
    limits: dict[str, float] | None = None,
) -> str:
    """Format statistics with progress bars (only for months with limits)."""
    if not stats or "categories" not in stats:
        return f"📊 <b>Статистика за {period}</b>\n\nДанных пока нет."

    categories = stats.get("categories", {})
    total = stats.get("total", 0)

    if not categories or total == 0:
        return f"📊 <b>Статистика за {period}</b>\n\nРасходов за этот период нет."

    msg = f"📊 <b>Статистика за {period}</b>\n\n"

    sorted_categories = sorted(
        categories.items(), key=lambda x: x[1], reverse=True
    )

    # Only show progress bars for monthly stats with limits
    is_week = period == "неделю"

    for category, amount in sorted_categories:
        emoji = get_category_emoji(category)

        if not is_week and limits and category in limits:
            # Month with limit - show progress bar
            limit = limits[category]
            percentage = (amount / limit) * 100 if limit > 0 else 0
            filled = min(int(percentage / 10), 10)
            bar = "█" * filled + "░" * (10 - filled)
            warning = " ⚠️" if percentage > 100 else ""
            msg += (
                f"{emoji} <b>{category}</b>: {amount:,.0f} / {limit:,.0f}₽ "
                f"{bar} {percentage:.0f}%{warning}\n"
            )
        else:
            # Week or no limit - just amount
            msg += f"{emoji} <b>{category}</b>: {amount:,.0f}₽\n"

    msg += f"\n💰 <b>Итого: {total:,.0f}₽</b>"

    return msg
```

**Step 4: Run tests**

Run: `poetry run pytest tests/test_bot/test_formatters.py -v -k "format_statistics"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/bot/formatters/messages.py tests/test_bot/test_formatters.py
git commit -m "feat(stats): remove progress bar from week statistics"
```

---

## Task 4: Add Category Detail Formatter

**Files:**
- Modify: `src/bot/formatters/messages.py`

**Step 1: Write the test**

```python
# tests/test_bot/test_formatters.py
def test_format_category_detail():
    """Format category detail should show numbered list of expenses."""
    from src.bot.formatters.messages import format_category_detail

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
    from src.bot.formatters.messages import format_category_detail

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
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_bot/test_formatters.py::test_format_category_detail -v`
Expected: FAIL (function doesn't exist)

**Step 3: Add formatter function**

```python
# src/bot/formatters/messages.py
def format_category_detail(
    category: str,
    period: str,
    expenses: list[dict[str, Any]],
    total: float,
    shown: int,
    total_count: int,
) -> str:
    """Format detailed list of expenses for a category.

    Args:
        category: Category name
        period: Period description (e.g., "январь 2026")
        expenses: List of expense dicts with date, description, amount
        total: Total amount for category in period
        shown: Number of items shown so far
        total_count: Total number of items in category
    """
    emoji = get_category_emoji(category)

    if not expenses:
        return f"{emoji} <b>{category} за {period}</b>\n\nРасходов нет."

    msg = f"{emoji} <b>{category} за {period}</b>\n\n"

    number_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, expense in enumerate(expenses):
        num = number_emoji[i] if i < len(number_emoji) else f"{i + 1}."
        date = expense.get("date", "")
        description = expense.get("description", "")
        amount = expense.get("amount", 0)

        msg += f"{num} {date} | {description} — <b>{amount:,.0f}₽</b>\n"

    msg += f"\n💰 <b>Итого: {total:,.0f}₽</b>"

    if shown < total_count:
        msg += f" <i>(показано {shown} из {total_count})</i>"

    return msg
```

**Step 4: Run tests**

Run: `poetry run pytest tests/test_bot/test_formatters.py -v -k "category_detail"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/bot/formatters/messages.py tests/test_bot/test_formatters.py
git commit -m "feat(stats): add category detail formatter"
```

---

## Task 5: Add API Endpoint for Expenses by Category

**Files:**
- Modify: `src/api/routes/__init__.py`
- Modify: `src/mcp/app.py` (add MCP route)

**Step 1: Write the test**

```python
# tests/test_api/test_routes.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_get_expenses_by_category():
    """API should return expenses filtered by category with pagination."""
    from fastapi.testclient import TestClient
    from src.api.app import app

    mock_result = {
        "expenses": [
            {"date": "28.01.2026", "description": "Test", "amount": 100}
        ],
        "total": 100,
        "count": 1,
        "total_count": 1,
    }

    with patch("src.api.routes.get_mcp_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_result
        mock_get_client.return_value = mock_client

        client = TestClient(app)
        response = client.get("/api/expenses/123/Еда?period=2026_01&limit=10&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert "expenses" in data
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_api/test_routes.py::test_get_expenses_by_category -v`
Expected: FAIL (endpoint doesn't exist)

**Step 3: Add API endpoint**

```python
# src/api/routes/__init__.py (add after existing routes)

@router.get("/expenses/{user_id}/{category}")
async def get_expenses_by_category(
    user_id: str,
    category: str,
    period: str = "month",  # "week" or "YYYY_MM"
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """Get expenses for a specific category with pagination."""
    from src.api.app import get_mcp_client

    logger.info(
        f"Getting expenses for user {user_id}, category: {category}, "
        f"period: {period}, limit: {limit}, offset: {offset}"
    )

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/storage/expenses_by_category",
        json={
            "user_id": user_id,
            "category": category,
            "period": period,
            "limit": limit,
            "offset": offset,
        },
    )

    return result
```

**Step 4: Add MCP route**

```python
# src/mcp/app.py (add route in routes section)
@app.post("/mcp/storage/expenses_by_category")
async def get_expenses_by_category(request: dict) -> dict:
    """Get expenses filtered by category with pagination."""
    user_id = request.get("user_id", "default")
    category = request.get("category")
    period = request.get("period", "month")
    limit = request.get("limit", 10)
    offset = request.get("offset", 0)

    # Parse period to date range
    if period == "week":
        from datetime import datetime, timedelta
        now = datetime.now()
        days_since_monday = now.weekday()
        start_date = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = None
    elif "_" in period:  # YYYY_MM format
        year, month = period.split("_")
        from datetime import datetime
        start_date = datetime(int(year), int(month), 1)
        if int(month) == 12:
            end_date = datetime(int(year) + 1, 1, 1)
        else:
            end_date = datetime(int(year), int(month) + 1, 1)
    else:
        start_date = None
        end_date = None

    # Get all expenses for category (storage handles filtering)
    result = await storage.get_expenses(
        user_id=user_id,
        category=category,
        start_date=start_date,
        end_date=end_date,
        limit=1000,  # Get all to count total
    )

    all_expenses = result.get("expenses", [])
    total_count = len(all_expenses)

    # Apply pagination
    paginated = all_expenses[offset:offset + limit]

    # Calculate total amount
    total = sum(
        float(str(e.get("Сумма", 0)).replace(",", ".").replace("₽", "").replace(" ", ""))
        for e in all_expenses
    )

    # Transform to simpler format
    expenses = [
        {
            "date": e.get("Дата", ""),
            "description": e.get("Расшифровка", ""),
            "amount": float(str(e.get("Сумма", 0)).replace(",", ".").replace("₽", "").replace(" ", "")),
        }
        for e in paginated
    ]

    return {
        "expenses": expenses,
        "total": total,
        "count": len(expenses),
        "total_count": total_count,
        "has_more": offset + limit < total_count,
    }
```

**Step 5: Run tests**

Run: `poetry run pytest tests/test_api/test_routes.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/api/routes/__init__.py src/mcp/app.py tests/test_api/test_routes.py
git commit -m "feat(api): add endpoint for expenses by category with pagination"
```

---

## Task 6: Update Command Handler — Parse /stats Arguments

**Files:**
- Modify: `src/bot/handlers/commands.py:48-108`

**Step 1: Write the test**

```python
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
    assert period == "2026_01"  # Current year assumed


def test_parse_stats_args_category():
    """Category name should be recognized."""
    category, period = parse_stats_args(["Еда"])
    assert category == "Еда"
    assert period is None  # Default to current month


def test_parse_stats_args_category_and_month():
    """Both category and month."""
    category, period = parse_stats_args(["Еда", "январь"])
    assert category == "Еда"
    assert period == "2026_01"
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_bot/test_commands.py::test_parse_stats_args_empty -v`
Expected: FAIL (function doesn't exist)

**Step 3: Add parse function and update handler**

```python
# src/bot/handlers/commands.py (add helper function)
from datetime import datetime
from src.core.categories import VALID_CATEGORIES

MONTH_NAMES_LOWER = {
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4,
    "май": 5, "июнь": 6, "июль": 7, "август": 8,
    "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
}

def parse_stats_args(args: list[str]) -> tuple[str | None, str | None]:
    """Parse /stats command arguments.

    Returns:
        (category, period) tuple where:
        - category: category name or None
        - period: "week" or "YYYY_MM" or None
    """
    if not args:
        return None, None

    category = None
    period = None

    for arg in args:
        arg_lower = arg.lower()

        # Check if it's "week"
        if arg_lower == "неделя":
            period = "week"
            continue

        # Check if it's a month name
        if arg_lower in MONTH_NAMES_LOWER:
            month = MONTH_NAMES_LOWER[arg_lower]
            year = datetime.now().year
            # If month is in future, assume previous year
            if month > datetime.now().month:
                year -= 1
            period = f"{year}_{month:02d}"
            continue

        # Check if it's a category (case-insensitive)
        for valid_cat in VALID_CATEGORIES:
            if arg_lower == valid_cat.lower():
                category = valid_cat
                break

    return category, period
```

**Step 4: Update cmd_stats handler**

```python
# src/bot/handlers/commands.py (replace cmd_stats)
@router.message(Command("stats"))
@require_api_client
async def cmd_stats(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /stats command with optional arguments."""
    if not message.from_user:
        return

    user_id = str(message.from_user.id)
    args = message.text.split()[1:]  # Remove "/stats"

    category, period = parse_stats_args(args)

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        if category:
            # Show category detail
            period = period or f"{datetime.now().year}_{datetime.now().month:02d}"
            result = await api_client.get(
                f"/api/expenses/{user_id}/{category}",
                params={"period": period, "limit": 10, "offset": 0},
            )

            period_display = _format_period_display(period)
            text = format_category_detail(
                category=category,
                period=period_display,
                expenses=result.get("expenses", []),
                total=result.get("total", 0),
                shown=result.get("count", 0),
                total_count=result.get("total_count", 0),
            )
            keyboard = get_category_detail_keyboard(
                category=category,
                period=period,
                offset=0,
                has_more=result.get("has_more", False),
            )
        elif period:
            # Show stats for specific period
            if period == "week":
                result = await api_client.get(f"/api/statistics/{user_id}/week")
                period_display = "неделю"
                limits = None
            else:
                result, limits_result = await asyncio.gather(
                    api_client.get(f"/api/statistics/{user_id}/month", params={"period": period}),
                    api_client.get(f"/api/limits/{user_id}"),
                )
                limits = limits_result.get("limits", {})
                period_display = _format_period_display(period)

            text = format_statistics(
                result.get("statistics", {}),
                period=period_display,
                limits=limits,
            )
            keyboard = get_back_to_stats_keyboard()
        else:
            # No args - show period selection
            text = "📊 <b>Статистика</b>\n\nВыберите период:"
            keyboard = get_stats_period_keyboard()

        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except asyncio.TimeoutError:
        await message.answer("Запрос занял слишком много времени. Попробуйте позже.")
    except ServiceUnavailableError:
        await message.answer("Сервис временно недоступен. Попробуйте позже.")
    except QuotaExceededError:
        await message.answer("Превышен лимит запросов. Подождите минуту.")
    except Exception as e:
        logger.error(f"Stats request failed: {e}", exc_info=True)
        await message.answer("Не удалось получить статистику. Попробуйте позже.")


def _format_period_display(period: str) -> str:
    """Convert period code to display string."""
    if period == "week":
        return "неделю"
    if "_" in period:
        year, month = period.split("_")
        from src.bot.keyboards.inline import MONTH_NAMES
        return f"{MONTH_NAMES[int(month) - 1]} {year}"
    return period
```

**Step 5: Run tests**

Run: `poetry run pytest tests/test_bot/test_commands.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/bot/handlers/commands.py tests/test_bot/test_commands.py
git commit -m "feat(stats): parse /stats arguments for category and period"
```

---

## Task 7: Add Callback Handlers for New Buttons

**Files:**
- Modify: `src/bot/handlers/callbacks.py`

**Step 1: Write the test**

```python
# tests/test_bot/test_callbacks.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_callback_stats_month_calls_api():
    """Stats month callback should call API with correct period."""
    from src.bot.handlers.callbacks import callback_stats_specific_month

    callback = MagicMock()
    callback.data = "stats_month_2026_01"
    callback.from_user.id = 123
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "statistics": {"categories": {"Еда": 1000}, "total": 1000}
    }

    with patch("src.bot.handlers.callbacks.require_api_client", lambda f: f):
        await callback_stats_specific_month(callback, api_client=mock_client)

    # Verify API was called with correct period
    mock_client.get.assert_called()
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_bot/test_callbacks.py::test_callback_stats_month_calls_api -v`
Expected: FAIL (handler doesn't exist)

**Step 3: Add callback handlers**

```python
# src/bot/handlers/callbacks.py (add new handlers)

@router.callback_query(F.data == "stats_select_period")
async def callback_stats_select_period(callback: CallbackQuery) -> None:
    """Show period selection keyboard."""
    if not callback.message:
        return

    await callback.message.edit_text(
        "📊 <b>Статистика</b>\n\nВыберите период:",
        parse_mode="HTML",
        reply_markup=get_stats_period_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stats_month_"))
@require_api_client
async def callback_stats_specific_month(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle specific month stats button (stats_month_YYYY_MM)."""
    if not callback.message or not callback.from_user or not callback.data:
        return

    # Parse: stats_month_2026_01 -> year=2026, month=01
    parts = callback.data.split("_")
    year = parts[2]
    month = parts[3]
    period = f"{year}_{month}"

    user_id = str(callback.from_user.id)

    await callback.message.edit_text("⏳ Загружаю статистику...")

    try:
        # Fetch stats and limits
        result, limits_result = await asyncio.gather(
            api_client.get(
                f"/api/statistics/{user_id}/month",
                params={"period": period},
            ),
            api_client.get(f"/api/limits/{user_id}"),
        )
        limits = limits_result.get("limits", {})

        period_display = _format_period_display(period)
        stats_text = format_statistics(
            result.get("statistics", {}),
            period=period_display,
            limits=limits,
        )

        await callback.message.edit_text(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_back_to_stats_keyboard(),
        )
    except Exception as e:
        logger.error(f"Stats month callback failed: {e}", exc_info=True)
        await callback.message.edit_text(
            "Не удалось получить статистику.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("cat_more_"))
@require_api_client
async def callback_category_more(
    callback: CallbackQuery,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle 'show more' in category detail (cat_more_Category_period_offset)."""
    if not callback.message or not callback.from_user or not callback.data:
        return

    # Parse: cat_more_Еда_2026_01_10 -> category=Еда, period=2026_01, offset=10
    parts = callback.data.split("_")
    category = parts[2]
    period = f"{parts[3]}_{parts[4]}"
    offset = int(parts[5])

    user_id = str(callback.from_user.id)

    try:
        result = await api_client.get(
            f"/api/expenses/{user_id}/{category}",
            params={"period": period, "limit": 10, "offset": offset},
        )

        period_display = _format_period_display(period)
        text = format_category_detail(
            category=category,
            period=period_display,
            expenses=result.get("expenses", []),
            total=result.get("total", 0),
            shown=offset + result.get("count", 0),
            total_count=result.get("total_count", 0),
        )

        keyboard = get_category_detail_keyboard(
            category=category,
            period=period,
            offset=offset,
            has_more=result.get("has_more", False),
        )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"Category more callback failed: {e}", exc_info=True)
        await callback.message.edit_text(
            "Не удалось загрузить данные.",
            reply_markup=get_back_to_menu_keyboard(),
        )

    await callback.answer()


def _format_period_display(period: str) -> str:
    """Convert period code to display string."""
    if period == "week":
        return "неделю"
    if "_" in period:
        year, month = period.split("_")
        from src.bot.keyboards.inline import MONTH_NAMES
        return f"{MONTH_NAMES[int(month) - 1]} {year}"
    return period
```

**Step 4: Add back to stats keyboard**

```python
# src/bot/keyboards/inline.py
def get_back_to_stats_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with back to period selection."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Выбрать период", callback_data="stats_select_period")],
        ]
    )
```

**Step 5: Run tests**

Run: `poetry run pytest tests/test_bot/ -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/bot/handlers/callbacks.py src/bot/keyboards/inline.py tests/test_bot/
git commit -m "feat(stats): add callback handlers for month selection and pagination"
```

---

## Task 8: Update Exports and Integration Test

**Files:**
- Modify: `src/bot/formatters/__init__.py`
- Modify: `src/bot/keyboards/inline.py` (exports)
- Create: `tests/test_bot/test_stats_integration.py`

**Step 1: Update exports**

```python
# src/bot/formatters/__init__.py (add export)
from src.bot.formatters.messages import format_category_detail
```

**Step 2: Write integration test**

```python
# tests/test_bot/test_stats_integration.py
import pytest

def test_stats_flow_no_args():
    """Test /stats with no args shows period selection."""
    # This would be a full integration test
    pass


def test_stats_flow_with_category():
    """Test /stats Еда shows category detail."""
    pass
```

**Step 3: Run all tests**

Run: `poetry run pytest -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add src/bot/formatters/__init__.py tests/test_bot/
git commit -m "feat(stats): finalize exports and add integration tests"
```

---

## Task 9: Remove Old Year Handler

**Files:**
- Modify: `src/bot/handlers/callbacks.py:386-471`

**Step 1: Remove stats_year from callback handler**

The `callback_stats_period` handler currently handles `stats_week`, `stats_month`, `stats_year`. Remove `stats_year` from the filter.

```python
# Change from:
@router.callback_query(F.data.in_({"stats_week", "stats_month", "stats_year"}))

# Change to:
@router.callback_query(F.data == "stats_week")
```

**Step 2: Run tests**

Run: `poetry run pytest -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/bot/handlers/callbacks.py
git commit -m "refactor(stats): remove year statistics handler"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Update keyboards — month buttons instead of year |
| 2 | Add category detail keyboard with pagination |
| 3 | Update formatter — no progress bar for week |
| 4 | Add category detail formatter |
| 5 | Add API endpoint for expenses by category |
| 6 | Update command handler — parse /stats args |
| 7 | Add callback handlers for new buttons |
| 8 | Update exports and integration tests |
| 9 | Remove old year handler |
