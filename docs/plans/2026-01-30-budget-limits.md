# Budget Limits Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add monthly budget limits per category with notifications when exceeded.

**Architecture:** Limits stored in separate Google Sheets worksheet "Лимиты". Bot command `/limit` for CRUD. Limit check happens after each expense addition. Stats show progress against limits.

**Tech Stack:** Python, aiogram, FastAPI, gspread, Google Sheets API

---

## Task 1: Storage Interface - Add Limit Methods

**Files:**
- Modify: `src/mcp/storage/interface.py`

**Step 1: Add abstract methods to StorageInterface**

Add after `add_expenses_batch` method (line ~107):

```python
@abstractmethod
async def get_limits(self, user_id: str) -> dict[str, Any]:
    """Get all budget limits.

    Args:
        user_id: User identifier

    Returns:
        dict with limits: {category: amount}
    """

@abstractmethod
async def set_limit(
    self,
    user_id: str,
    category: str,
    amount: float,
) -> dict[str, Any]:
    """Set budget limit for a category.

    Args:
        user_id: User identifier
        category: Expense category
        amount: Limit amount (0 to delete)

    Returns:
        dict with status and limit details
    """

@abstractmethod
async def delete_limit(
    self,
    user_id: str,
    category: str,
) -> dict[str, Any]:
    """Delete budget limit for a category.

    Args:
        user_id: User identifier
        category: Expense category

    Returns:
        dict with status
    """
```

**Step 2: Run linter to verify syntax**

Run: `poetry run ruff check src/mcp/storage/interface.py`
Expected: No errors (or only existing unrelated warnings)

**Step 3: Commit**

```bash
git add src/mcp/storage/interface.py
git commit -m "feat(storage): add limit methods to StorageInterface"
```

---

## Task 2: Storage Implementation - Limits in Google Sheets

**Files:**
- Modify: `src/mcp/storage/sheets.py`
- Test: `tests/test_mcp/test_storage_limits.py` (create)

**Step 1: Write failing tests for get_limits**

Create `tests/test_mcp/test_storage_limits.py`:

```python
"""Tests for budget limits storage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_worksheet():
    """Create mock worksheet."""
    ws = MagicMock()
    ws.get_all_values = MagicMock(return_value=[
        ["Категория", "Лимит"],
        ["Еда", "10000"],
        ["Транспорт", "5000"],
    ])
    ws.update = MagicMock()
    ws.delete_rows = MagicMock()
    return ws


@pytest.fixture
def mock_spreadsheet(mock_worksheet):
    """Create mock spreadsheet."""
    ss = MagicMock()
    ss.worksheet = MagicMock(return_value=mock_worksheet)
    ss.add_worksheet = MagicMock(return_value=mock_worksheet)
    return ss


@pytest.mark.asyncio
async def test_get_limits_returns_dict(mock_spreadsheet, mock_worksheet):
    """Test that get_limits returns category: amount dict."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values()]

        result = await storage.get_limits("user123")

        assert result["status"] == "success"
        assert result["limits"]["Еда"] == 10000.0
        assert result["limits"]["Транспорт"] == 5000.0


@pytest.mark.asyncio
async def test_get_limits_empty_sheet(mock_spreadsheet):
    """Test get_limits with empty limits sheet."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    mock_ws = MagicMock()
    mock_ws.get_all_values = MagicMock(return_value=[["Категория", "Лимит"]])
    mock_spreadsheet.worksheet = MagicMock(return_value=mock_ws)

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_ws, mock_ws.get_all_values()]

        result = await storage.get_limits("user123")

        assert result["status"] == "success"
        assert result["limits"] == {}


@pytest.mark.asyncio
async def test_set_limit_new_category(mock_spreadsheet, mock_worksheet):
    """Test setting limit for new category."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        # First call: get worksheet, second: get values, third: update
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values(), None]

        result = await storage.set_limit("user123", "Продукты", 15000)

        assert result["status"] == "success"
        assert result["category"] == "Продукты"
        assert result["limit"] == 15000


@pytest.mark.asyncio
async def test_set_limit_zero_deletes(mock_spreadsheet, mock_worksheet):
    """Test that setting limit to 0 deletes the limit."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values(), None]

        result = await storage.set_limit("user123", "Еда", 0)

        assert result["status"] == "success"
        assert result["deleted"] is True


@pytest.mark.asyncio
async def test_delete_limit(mock_spreadsheet, mock_worksheet):
    """Test deleting a limit."""
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    storage._spreadsheet = mock_spreadsheet
    storage._client = MagicMock()

    with patch.object(storage, '_run_sync', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [mock_worksheet, mock_worksheet.get_all_values(), None]

        result = await storage.delete_limit("user123", "Еда")

        assert result["status"] == "success"
```

**Step 2: Run tests to verify they fail**

Run: `poetry run pytest tests/test_mcp/test_storage_limits.py -v`
Expected: FAIL (methods not implemented)

**Step 3: Implement _get_limits_worksheet helper**

Add to `src/mcp/storage/sheets.py` after `_get_worksheet` method (~line 108):

```python
async def _get_limits_worksheet(self) -> gspread.Worksheet:
    """Get or create the limits worksheet."""
    await self._connect()

    worksheet_name = "Лимиты"

    try:
        worksheet = await self._run_sync(
            self._spreadsheet.worksheet, worksheet_name
        )
        logger.info(f"Using limits worksheet: {worksheet_name}")
    except gspread.WorksheetNotFound:
        logger.info(f"Creating limits worksheet: {worksheet_name}")
        worksheet = await self._run_sync(
            self._spreadsheet.add_worksheet,
            title=worksheet_name,
            rows=100,
            cols=2,
        )
        # Add headers
        await self._run_sync(
            worksheet.update,
            "A1:B1",
            [["Категория", "Лимит"]],
        )

    return worksheet
```

**Step 4: Implement get_limits**

Add to `src/mcp/storage/sheets.py` after `health_check` method (end of class):

```python
async def get_limits(self, user_id: str) -> dict[str, Any]:
    """Get all budget limits from Google Sheets."""
    try:
        worksheet = await self._get_limits_worksheet()

        all_values = await self._run_sync(worksheet.get_all_values)

        if not all_values or len(all_values) < 2:
            return {
                "status": "success",
                "user_id": user_id,
                "limits": {},
            }

        # Skip header row
        rows = all_values[1:]
        limits = {}

        for row in rows:
            if len(row) >= 2 and row[0] and row[1]:
                category = row[0]
                try:
                    amount = float(row[1].replace(",", ".").replace(" ", ""))
                    if amount > 0:
                        limits[category] = amount
                except (ValueError, TypeError):
                    continue

        logger.info(f"Got {len(limits)} limits for user {user_id}")

        return {
            "status": "success",
            "user_id": user_id,
            "limits": limits,
        }

    except Exception as e:
        logger.error(f"Failed to get limits: {e}")
        return {
            "status": "error",
            "error": str(e),
            "limits": {},
        }
```

**Step 5: Implement set_limit**

Add to `src/mcp/storage/sheets.py`:

```python
async def set_limit(
    self,
    user_id: str,
    category: str,
    amount: float,
) -> dict[str, Any]:
    """Set budget limit for a category."""
    try:
        worksheet = await self._get_limits_worksheet()

        all_values = await self._run_sync(worksheet.get_all_values)

        # Find existing row for this category
        row_index = None
        for i, row in enumerate(all_values):
            if len(row) >= 1 and row[0] == category:
                row_index = i + 1  # 1-indexed
                break

        if amount <= 0:
            # Delete limit
            if row_index and row_index > 1:  # Don't delete header
                await self._run_sync(worksheet.delete_rows, row_index)
                logger.info(f"Deleted limit for {category}")
                return {
                    "status": "success",
                    "user_id": user_id,
                    "category": category,
                    "deleted": True,
                }
            return {
                "status": "success",
                "user_id": user_id,
                "category": category,
                "deleted": False,
                "message": "Limit not found",
            }

        if row_index:
            # Update existing
            await self._run_sync(
                worksheet.update,
                f"B{row_index}",
                [[amount]],
            )
            logger.info(f"Updated limit for {category}: {amount}")
        else:
            # Add new row
            next_row = len(all_values) + 1
            await self._run_sync(
                worksheet.update,
                f"A{next_row}:B{next_row}",
                [[category, amount]],
            )
            logger.info(f"Added limit for {category}: {amount}")

        return {
            "status": "success",
            "user_id": user_id,
            "category": category,
            "limit": amount,
        }

    except Exception as e:
        logger.error(f"Failed to set limit: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
```

**Step 6: Implement delete_limit**

Add to `src/mcp/storage/sheets.py`:

```python
async def delete_limit(
    self,
    user_id: str,
    category: str,
) -> dict[str, Any]:
    """Delete budget limit for a category."""
    return await self.set_limit(user_id, category, 0)
```

**Step 7: Run tests to verify they pass**

Run: `poetry run pytest tests/test_mcp/test_storage_limits.py -v`
Expected: All PASS

**Step 8: Run linter**

Run: `poetry run ruff check src/mcp/storage/sheets.py`
Expected: No errors

**Step 9: Commit**

```bash
git add src/mcp/storage/sheets.py tests/test_mcp/test_storage_limits.py
git commit -m "feat(storage): implement budget limits in Google Sheets"
```

---

## Task 3: API Schemas for Limits

**Files:**
- Modify: `src/core/schemas.py`

**Step 1: Add limit request/response schemas**

Add at end of `src/core/schemas.py`:

```python
# Limit schemas


class GetLimitsRequest(BaseModel):
    """Request to get budget limits."""

    user_id: str = Field(..., min_length=1)


class SetLimitRequest(BaseModel):
    """Request to set a budget limit."""

    user_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., ge=0)


class DeleteLimitRequest(BaseModel):
    """Request to delete a budget limit."""

    user_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)


class LimitsResponse(BaseModel):
    """Response with budget limits."""

    status: str
    user_id: str
    limits: dict[str, float] = Field(default_factory=dict)


class LimitResponse(BaseModel):
    """Response for single limit operation."""

    status: str
    user_id: str
    category: str
    limit: float | None = None
    deleted: bool = False
    message: str | None = None
```

**Step 2: Run linter**

Run: `poetry run ruff check src/core/schemas.py`
Expected: No errors

**Step 3: Commit**

```bash
git add src/core/schemas.py
git commit -m "feat(schemas): add budget limit request/response models"
```

---

## Task 4: API Routes for Limits

**Files:**
- Modify: `src/api/routes/__init__.py`

**Step 1: Add limit endpoints**

Add imports at top of `src/api/routes/__init__.py`:

```python
from src.core.schemas import (
    QueryRequest,
    QueryResponse,
    GetLimitsRequest,
    SetLimitRequest,
    DeleteLimitRequest,
    LimitsResponse,
    LimitResponse,
)
```

Add routes after existing `/query` endpoint:

```python
@router.get("/limits/{user_id}", response_model=LimitsResponse)
async def get_limits(user_id: str) -> LimitsResponse:
    """Get all budget limits for a user."""
    from src.api.app import get_mcp_client

    logger.info(f"Getting limits for user {user_id}")

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/limits",
        json={"user_id": user_id},
    )

    return LimitsResponse(
        status=result.get("status", "success"),
        user_id=user_id,
        limits=result.get("limits", {}),
    )


@router.post("/limits", response_model=LimitResponse)
async def set_limit(request: SetLimitRequest) -> LimitResponse:
    """Set a budget limit for a category."""
    from src.api.app import get_mcp_client

    logger.info(f"Setting limit for user {request.user_id}: {request.category} = {request.amount}")

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/limits/set",
        json={
            "user_id": request.user_id,
            "category": request.category,
            "amount": request.amount,
        },
    )

    return LimitResponse(
        status=result.get("status", "success"),
        user_id=request.user_id,
        category=request.category,
        limit=result.get("limit"),
        deleted=result.get("deleted", False),
        message=result.get("message"),
    )


@router.delete("/limits/{user_id}/{category}", response_model=LimitResponse)
async def delete_limit(user_id: str, category: str) -> LimitResponse:
    """Delete a budget limit for a category."""
    from src.api.app import get_mcp_client

    logger.info(f"Deleting limit for user {user_id}: {category}")

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/limits/delete",
        json={
            "user_id": user_id,
            "category": category,
        },
    )

    return LimitResponse(
        status=result.get("status", "success"),
        user_id=user_id,
        category=category,
        deleted=True,
    )
```

**Step 2: Run linter**

Run: `poetry run ruff check src/api/routes/__init__.py`
Expected: No errors

**Step 3: Commit**

```bash
git add src/api/routes/__init__.py
git commit -m "feat(api): add limit endpoints to API Gateway"
```

---

## Task 5: MCP Service - Limit Endpoints

**Files:**
- Modify: `src/mcp/app.py`

**Step 1: Find MCP app.py and add limit routes**

First read the file to understand structure:

Run: `cat src/mcp/app.py | head -100`

Then add endpoints for limits. Add after existing routes:

```python
@app.post("/mcp/limits")
async def get_limits(request: dict) -> dict:
    """Get all budget limits."""
    user_id = request.get("user_id", "default")
    return await storage.get_limits(user_id)


@app.post("/mcp/limits/set")
async def set_limit(request: dict) -> dict:
    """Set a budget limit."""
    user_id = request.get("user_id", "default")
    category = request.get("category")
    amount = request.get("amount", 0)
    return await storage.set_limit(user_id, category, amount)


@app.post("/mcp/limits/delete")
async def delete_limit(request: dict) -> dict:
    """Delete a budget limit."""
    user_id = request.get("user_id", "default")
    category = request.get("category")
    return await storage.delete_limit(user_id, category)
```

**Step 2: Run linter**

Run: `poetry run ruff check src/mcp/app.py`
Expected: No errors

**Step 3: Commit**

```bash
git add src/mcp/app.py
git commit -m "feat(mcp): add limit endpoints to MCP service"
```

---

## Task 6: Bot Formatters for Limits

**Files:**
- Modify: `src/bot/formatters/messages.py`
- Modify: `src/bot/formatters/__init__.py`

**Step 1: Add format_limits function**

Add to `src/bot/formatters/messages.py` after `format_examples_message`:

```python
def format_limits(limits: dict[str, float]) -> str:
    """Format budget limits list.

    Args:
        limits: Dict of {category: limit_amount}

    Returns:
        Formatted HTML message
    """
    if not limits:
        msg = "📊 <b>Лимиты не установлены</b>\n\n"
        msg += "Установить: <code>/limit Категория Сумма</code>\n"
        msg += "Пример: <code>/limit Еда 10000</code>"
        return msg

    msg = "📊 <b>Ваши лимиты на месяц:</b>\n\n"

    for category, amount in sorted(limits.items()):
        emoji = get_category_emoji(category)
        msg += f"{emoji} <b>{category}</b>: {amount:,.0f}₽\n"

    msg += "\n<i>Изменить:</i> <code>/limit Категория Сумма</code>\n"
    msg += "<i>Удалить:</i> <code>/limit Категория 0</code>"

    return msg


def format_limit_set(category: str, amount: float) -> str:
    """Format limit set confirmation.

    Args:
        category: Category name
        amount: Limit amount

    Returns:
        Formatted HTML message
    """
    emoji = get_category_emoji(category)
    return f"✅ Лимит установлен: {emoji} <b>{category}</b> — {amount:,.0f}₽/месяц"


def format_limit_deleted(category: str) -> str:
    """Format limit deletion confirmation.

    Args:
        category: Category name

    Returns:
        Formatted HTML message
    """
    emoji = get_category_emoji(category)
    return f"✅ Лимит удален: {emoji} <b>{category}</b>"


def format_limit_exceeded(category: str, spent: float, limit: float) -> str:
    """Format limit exceeded warning.

    Args:
        category: Category name
        spent: Amount spent
        limit: Limit amount

    Returns:
        Formatted HTML warning
    """
    emoji = get_category_emoji(category)
    return f"\n\n⚠️ <b>Лимит превышен!</b>\n{emoji} {category}: {spent:,.0f} / {limit:,.0f}₽"
```

**Step 2: Update format_statistics for limits**

Replace `format_statistics` function in `src/bot/formatters/messages.py`:

```python
def format_statistics(
    stats: dict[str, Any],
    period: str = "неделю",
    limits: dict[str, float] | None = None,
) -> str:
    """Format statistics with progress bars.

    Args:
        stats: Statistics dictionary with categories and amounts
        period: Period description (неделю, месяц, год)
        limits: Optional dict of {category: limit} for monthly stats

    Returns:
        Formatted HTML message
    """
    if not stats or "categories" not in stats:
        return f"📊 <b>Статистика за {period}</b>\n\nДанных пока нет."

    categories = stats.get("categories", {})
    total = stats.get("total", 0)

    if not categories or total == 0:
        return f"📊 <b>Статистика за {period}</b>\n\nРасходов за этот период нет."

    msg = f"📊 <b>Статистика за {period}</b>\n\n"

    # Sort by amount descending
    sorted_categories = sorted(
        categories.items(), key=lambda x: x[1], reverse=True
    )

    # Use limits for progress bar if available (monthly stats)
    use_limits = limits and period == "месяц"

    for category, amount in sorted_categories:
        emoji = get_category_emoji(category)

        if use_limits and category in limits:
            limit = limits[category]
            percentage = (amount / limit) * 100 if limit > 0 else 0
            filled = min(int(percentage / 10), 10)
            bar = "█" * filled + "░" * (10 - filled)
            warning = " ⚠️" if percentage > 100 else ""
            msg += f"{emoji} <b>{category}</b>: {amount:,.0f} / {limit:,.0f}₽ {bar} {percentage:.0f}%{warning}\n"
        else:
            # No limit - show percentage of total
            percentage = (amount / total) * 100 if total > 0 else 0
            filled = int(percentage / 10)
            bar = "█" * filled + "░" * (10 - filled)
            msg += f"{emoji} <b>{category}</b>: {amount:,.0f}₽ {bar} {percentage:.0f}%\n"

    msg += f"\n💰 <b>Итого: {total:,.0f}₽</b>"

    return msg
```

**Step 3: Export new functions in __init__.py**

Update `src/bot/formatters/__init__.py`:

```python
"""Message formatters."""

from src.bot.formatters.messages import (
    CATEGORY_EMOJI,
    format_examples_message,
    format_expense_added,
    format_expense_deleted,
    format_expenses_list,
    format_help_message,
    format_limit_deleted,
    format_limit_exceeded,
    format_limit_set,
    format_limits,
    format_statistics,
    get_category_emoji,
)

__all__ = [
    "CATEGORY_EMOJI",
    "format_examples_message",
    "format_expense_added",
    "format_expense_deleted",
    "format_expenses_list",
    "format_help_message",
    "format_limit_deleted",
    "format_limit_exceeded",
    "format_limit_set",
    "format_limits",
    "format_statistics",
    "get_category_emoji",
]
```

**Step 4: Run linter**

Run: `poetry run ruff check src/bot/formatters/`
Expected: No errors

**Step 5: Commit**

```bash
git add src/bot/formatters/
git commit -m "feat(bot): add limit formatting functions"
```

---

## Task 7: Bot /limit Command Handler

**Files:**
- Modify: `src/bot/handlers/commands.py`

**Step 1: Add imports**

Add to imports in `src/bot/handlers/commands.py`:

```python
from src.bot.formatters import (
    format_examples_message,
    format_expenses_list,
    format_help_message,
    format_statistics,
    format_limits,
    format_limit_set,
    format_limit_deleted,
    CATEGORY_EMOJI,
)
```

**Step 2: Add /limit handler**

Add after `cmd_examples` handler:

```python
@router.message(Command("limit"))
async def cmd_limit(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /limit command - manage budget limits."""
    if not message.from_user:
        return

    if not api_client:
        logger.error(f"API client not configured for user {message.from_user.id}")
        await message.answer("API не настроен. Проверьте конфигурацию.")
        return

    user_id = str(message.from_user.id)
    args = message.text.split()[1:]  # Remove "/limit"

    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        if not args:
            # Show all limits
            result = await api_client.get(f"/api/limits/{user_id}")
            limits = result.get("limits", {})
            await message.answer(
                format_limits(limits),
                parse_mode="HTML",
            )

        elif len(args) == 2:
            category, amount_str = args[0], args[1]

            # Validate category
            if category not in CATEGORY_EMOJI:
                categories_list = ", ".join(sorted(CATEGORY_EMOJI.keys()))
                await message.answer(
                    f"❌ Неизвестная категория: <b>{category}</b>\n\n"
                    f"Доступные категории:\n<code>{categories_list}</code>",
                    parse_mode="HTML",
                )
                return

            # Parse amount
            try:
                amount = float(amount_str.replace(",", "."))
            except ValueError:
                await message.answer(
                    "❌ Неверная сумма. Используйте число.\n\n"
                    "Пример: <code>/limit Еда 10000</code>",
                    parse_mode="HTML",
                )
                return

            if amount <= 0:
                # Delete limit
                await api_client.delete(f"/api/limits/{user_id}/{category}")
                await message.answer(
                    format_limit_deleted(category),
                    parse_mode="HTML",
                )
            else:
                # Set limit
                await api_client.post(
                    "/api/limits",
                    json={
                        "user_id": user_id,
                        "category": category,
                        "amount": amount,
                    },
                )
                await message.answer(
                    format_limit_set(category, amount),
                    parse_mode="HTML",
                )

        else:
            await message.answer(
                "❌ Неверный формат команды.\n\n"
                "Использование:\n"
                "<code>/limit</code> — показать все лимиты\n"
                "<code>/limit Категория Сумма</code> — установить лимит\n"
                "<code>/limit Категория 0</code> — удалить лимит\n\n"
                "Пример: <code>/limit Еда 10000</code>",
                parse_mode="HTML",
            )

    except Exception as e:
        logger.error(
            f"Limit command failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer("Не удалось выполнить команду. Попробуйте позже.")
```

**Step 3: Add DELETE method to ServiceClient if missing**

Check if ServiceClient has delete method. If not, add to `src/core/http_client.py`:

```python
async def delete(self, path: str) -> dict:
    """Make DELETE request."""
    url = f"{self.base_url}{path}"
    async with self._session.delete(url) as response:
        response.raise_for_status()
        return await response.json()
```

**Step 4: Run linter**

Run: `poetry run ruff check src/bot/handlers/commands.py`
Expected: No errors

**Step 5: Commit**

```bash
git add src/bot/handlers/commands.py src/core/http_client.py
git commit -m "feat(bot): add /limit command handler"
```

---

## Task 8: Update /stats to Show Limits

**Files:**
- Modify: `src/bot/handlers/commands.py`
- Modify: `src/bot/handlers/callbacks.py`

**Step 1: Update cmd_stats to fetch limits**

Replace `cmd_stats` function in `src/bot/handlers/commands.py`:

```python
@router.message(Command("stats"))
async def cmd_stats(
    message: Message,
    api_client: ServiceClient | None = None,
) -> None:
    """Handle /stats command - show expense statistics."""
    if not message.from_user:
        return

    if not api_client:
        logger.error(f"API client not configured for user {message.from_user.id}")
        await message.answer("API не настроен. Проверьте конфигурацию.")
        return

    user_id = str(message.from_user.id)
    await message.bot.send_chat_action(message.chat.id, "typing")

    try:
        # Request statistics and limits in parallel
        stats_result = await api_client.post(
            "/api/query",
            json={
                "query": "покажи статистику за месяц",
                "user_id": user_id,
            },
        )

        limits_result = await api_client.get(f"/api/limits/{user_id}")
        limits = limits_result.get("limits", {})

        # Format with limits for monthly stats
        if "statistics" in stats_result:
            stats_text = format_statistics(
                stats_result["statistics"],
                period="месяц",
                limits=limits if limits else None,
            )
        else:
            stats_text = stats_result.get("response", "Нет данных")

        await message.answer(
            stats_text,
            parse_mode="HTML",
            reply_markup=get_stats_period_keyboard(),
        )

    except Exception as e:
        logger.error(
            f"Stats request failed for user {user_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await message.answer("Не удалось получить статистику. Попробуйте позже.")
```

**Step 2: Update callback handlers for stats periods**

Read `src/bot/handlers/callbacks.py` and update stats period callbacks similarly to fetch limits for month period.

**Step 3: Run linter**

Run: `poetry run ruff check src/bot/handlers/`
Expected: No errors

**Step 4: Commit**

```bash
git add src/bot/handlers/
git commit -m "feat(bot): integrate limits into /stats display"
```

---

## Task 9: Add Limit Check After Adding Expense

**Files:**
- Modify: `src/mcp/storage/sheets.py`
- Modify: `src/bot/handlers/__init__.py` (main message handler)

**Step 1: Update add_expense to return limit status**

Modify `add_expense` in `src/mcp/storage/sheets.py` to check limits after adding:

After successful add (before return), add:

```python
# Check if limit exceeded
limits_result = await self.get_limits(user_id)
limits = limits_result.get("limits", {})

limit_exceeded = None
if category in limits:
    # Get current month's spending for this category
    stats = await self.get_statistics(user_id, "month")
    spent = stats.get("by_category", {}).get(category, 0)
    limit = limits[category]
    if spent > limit:
        limit_exceeded = {
            "category": category,
            "spent": spent,
            "limit": limit,
        }

return {
    "status": "success",
    "user_id": user_id,
    "category": category,
    "amount": amount,
    "description": description,
    "date": date_str,
    "limit_exceeded": limit_exceeded,
}
```

**Step 2: Update bot handler to show limit warning**

In the main message handler (likely `src/bot/handlers/__init__.py`), after displaying expense added message, check for `limit_exceeded` and append warning:

```python
# After formatting expense added message
if result.get("limit_exceeded"):
    le = result["limit_exceeded"]
    response_text += format_limit_exceeded(
        le["category"],
        le["spent"],
        le["limit"],
    )
```

**Step 3: Run tests**

Run: `poetry run pytest -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add src/mcp/storage/sheets.py src/bot/handlers/
git commit -m "feat: add limit exceeded warning after adding expense"
```

---

## Task 10: Update Help Message

**Files:**
- Modify: `src/bot/formatters/messages.py`

**Step 1: Add /limit to help message**

Update `format_help_message` function, add to commands section:

```python
msg += "/limit - Управление лимитами\n"
```

**Step 2: Commit**

```bash
git add src/bot/formatters/messages.py
git commit -m "docs(bot): add /limit to help message"
```

---

## Task 11: Integration Testing

**Step 1: Run all tests**

Run: `poetry run pytest -v --cov=src --cov-report=term-missing`
Expected: All pass, coverage >= 50%

**Step 2: Manual testing checklist**

Start services locally:
```bash
docker-compose up -d
```

Test in Telegram:
1. `/limit` - should show "Лимиты не установлены"
2. `/limit Еда 10000` - should confirm limit set
3. `/limit` - should show Еда: 10,000₽
4. `/stats` - should show Еда with progress bar against limit
5. Add expense: "обед 500" - should add without warning
6. Add expenses until > 10000 - should show limit exceeded warning
7. `/limit Еда 0` - should confirm limit deleted
8. `/limit` - should show empty again

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete budget limits implementation (Iteration 12)"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Storage interface | `interface.py` |
| 2 | Storage implementation | `sheets.py`, tests |
| 3 | API schemas | `schemas.py` |
| 4 | API routes | `routes/__init__.py` |
| 5 | MCP endpoints | `mcp/app.py` |
| 6 | Bot formatters | `formatters/` |
| 7 | /limit command | `commands.py` |
| 8 | /stats integration | `commands.py`, `callbacks.py` |
| 9 | Limit check on add | `sheets.py`, handlers |
| 10 | Help message | `messages.py` |
| 11 | Testing | All files |
