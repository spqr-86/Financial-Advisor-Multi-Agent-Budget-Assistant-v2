# Batch Expense Import Design

**Date:** 2026-01-27
**Status:** Approved
**Author:** Claude Code (brainstorming session)

## Problem Statement

Users want to import bank statements (PDF) via Claude Code and add all transactions to Budget Assistant at once. Currently, adding expenses one-by-one is inefficient and consumes too many Google Sheets API calls.

## Use Case

1. User loads PDF bank statement in Claude Code
2. Claude parses PDF, extracts transactions
3. Claude calls MCP tool `add_expenses_batch` with array of expenses
4. All transactions added to Google Sheets in one API call

## Requirements

- **Input format:** Array of objects `[{category, amount, description, date}, ...]`
- **Error handling:** Partial success - add what's valid, return detailed error report
- **Category validation:** Auto-replace unknown categories with "Прочее"
- **Performance:** Use batch API (`append_rows`) instead of individual calls

## Design

### 1. MCP Tool Interface

New tool in `src/mcp/server/app.py`:

```python
@mcp.tool()
async def add_expenses_batch(
    expenses: list[dict],
    user_id: str = "default"
) -> dict:
    """
    Массовое добавление расходов (для импорта выписок).

    Args:
        expenses: Список расходов, каждый содержит:
            - category: str (Продукты, Транспорт, и т.д.)
            - amount: float (сумма в рублях)
            - description: str (описание)
            - date: str (опционально, формат "DD.MM.YYYY")
        user_id: ID пользователя

    Returns:
        {
            "status": "success" | "partial" | "error",
            "added": 8,
            "failed": 2,
            "total": 10,
            "errors": [{"index": 3, "error": "..."}]
        }
    """
    return await tools.add_expenses_batch_direct(
        expenses=expenses,
        user_id=user_id
    )
```

### 2. Storage Layer

**Interface change** (`src/mcp/storage/interface.py`):

```python
@abstractmethod
async def add_expenses_batch(
    self,
    user_id: str,
    expenses: list[dict],
) -> dict[str, Any]:
    """Add multiple expenses in one batch.

    Args:
        user_id: User identifier
        expenses: List of expense dicts with keys:
            - category: str
            - amount: float
            - description: str
            - date: str (optional, format "DD.MM.YYYY")

    Returns:
        dict with:
            - added: int (count of successfully added)
            - failed: int (count of failed)
            - total: int (total count)
            - errors: list[dict] (error details with index)
    """
```

**Implementation** (`src/mcp/storage/sheets.py`):

```python
async def add_expenses_batch(
    self,
    user_id: str,
    expenses: list[dict],
) -> dict[str, Any]:
    """Add multiple expenses using batch API."""
    worksheet = await self._get_worksheet()

    VALID_CATEGORIES = {
        "Продукты", "Транспорт", "Рестораны",
        "Развлечения", "ЖКХ", "Одежда", "Здоровье", "Прочее"
    }

    rows_to_add = []
    errors = []

    # Validate and prepare rows in memory
    for i, exp in enumerate(expenses):
        try:
            # Category validation with auto-fallback
            category = exp.get("category", "Прочее")
            if category not in VALID_CATEGORIES:
                category = "Прочее"

            # Date handling
            date_str = exp.get("date")
            if not date_str:
                date_str = datetime.now().strftime("%d.%m.%Y")

            # Required fields
            amount = float(exp["amount"])
            description = exp.get("description", "")

            rows_to_add.append([date_str, category, description, amount])

        except Exception as e:
            errors.append({
                "index": i,
                "expense": exp,
                "error": str(e)
            })

    # Single API call for all valid rows
    if rows_to_add:
        await self._run_sync(worksheet.append_rows, rows_to_add)

    logger.info(
        f"Batch added {len(rows_to_add)} expenses for user {user_id}, "
        f"failed: {len(errors)}"
    )

    return {
        "added": len(rows_to_add),
        "failed": len(errors),
        "total": len(expenses),
        "errors": errors
    }
```

### 3. Wrapper Layer

New function in `src/mcp/server/tools.py`:

```python
async def add_expenses_batch_direct(
    expenses: list[dict],
    user_id: str = "default"
) -> dict[str, Any]:
    """
    Массовое добавление расходов напрямую (без AI обработки).

    Args:
        expenses: Список расходов
        user_id: ID пользователя

    Returns:
        Результат с детальным отчётом
    """
    from src.mcp.storage.sheets import GoogleSheetsStorage

    storage = GoogleSheetsStorage()
    result = await storage.add_expenses_batch(
        user_id=user_id,
        expenses=expenses
    )

    # Determine overall status
    if result["failed"] == 0:
        status = "success"
    elif result["added"] == 0:
        status = "error"
    else:
        status = "partial"

    return {
        "status": status,
        **result
    }
```

## Files Changed

| File | Change | Lines |
|------|--------|-------|
| `src/mcp/storage/interface.py` | +1 abstract method | ~15 |
| `src/mcp/storage/sheets.py` | +1 implementation | ~40 |
| `src/mcp/server/tools.py` | +1 wrapper function | ~20 |
| `src/mcp/server/app.py` | +1 MCP tool | ~25 |

**Total:** ~100 lines of new code across 4 files.

## Example Usage

**Claude Code workflow:**

```python
# After parsing PDF
expenses = [
    {
        "category": "Продукты",
        "amount": 1250.50,
        "description": "Лента",
        "date": "15.01.2025"
    },
    {
        "category": "Транспорт",
        "amount": 89,
        "description": "Метро"
        # date omitted - will use current date
    },
    {
        "category": "Unknown",  # Will be replaced with "Прочее"
        "amount": 450,
        "description": "Кофемания"
    }
]

# MCP tool call
result = await add_expenses_batch(expenses=expenses, user_id="telegram_123456")
```

**Response:**

```json
{
  "status": "success",
  "added": 3,
  "failed": 0,
  "total": 3,
  "errors": []
}
```

**With errors:**

```json
{
  "status": "partial",
  "added": 2,
  "failed": 1,
  "total": 3,
  "errors": [
    {
      "index": 1,
      "expense": {"category": "Транспорт", "amount": "invalid"},
      "error": "could not convert string to float: 'invalid'"
    }
  ]
}
```

## Testing Strategy

1. **Unit test:** `tests/test_storage/test_sheets_batch.py`
   - Valid batch of 3 expenses
   - Unknown category → auto-replace with "Прочее"
   - Invalid amount → partial success with error report
   - Empty list → success with 0 added

2. **Integration test:** MCP tool → storage → Google Sheets
   - End-to-end flow with mock worksheet

3. **Manual test:** Claude Code + real PDF
   - Load bank statement PDF
   - Let Claude parse and call tool
   - Verify all transactions in Google Sheets

## Performance Impact

**Before:** 50 transactions = 50 API calls (~5-10 seconds)
**After:** 50 transactions = 1 API call (~0.5-1 second)

**Google Sheets API quota:**
- Read/write requests: 300 per minute per project
- Batch operations count as 1 request regardless of row count
- Batch insert of 100 rows is significantly faster and more quota-efficient

## Edge Cases

1. **Empty list:** Return `{added: 0, failed: 0, total: 0, errors: []}`
2. **All invalid:** Return `{status: "error", added: 0, failed: N, errors: [...]}`
3. **Duplicate dates:** Allow - no deduplication (user's responsibility)
4. **Missing description:** Use empty string ""
5. **Future dates:** Allow - no validation (bank statements can have pending transactions)

## Future Enhancements

- Add optional deduplication by (date, amount, description)
- Support CSV import in addition to PDF
- Add progress callback for very large batches (1000+ rows)
- Add dry-run mode to preview what will be added
