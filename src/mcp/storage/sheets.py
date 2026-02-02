"""Google Sheets storage implementation."""

import asyncio
import logging
from datetime import datetime, timedelta
from functools import partial
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from src.core.cache import limits_cache
from src.core.categories import VALID_CATEGORIES
from src.core.constants import WORKSHEET_EXPENSES, WORKSHEET_LIMITS
from src.mcp.config import settings
from src.mcp.storage.interface import StorageInterface

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GoogleSheetsStorage(StorageInterface):
    """Google Sheets implementation of storage interface."""

    def __init__(self):
        """Initialize Google Sheets storage."""
        self._client: gspread.Client | None = None
        self._spreadsheet: gspread.Spreadsheet | None = None
        self._connect_lock: asyncio.Lock | None = None

    def _get_connect_lock(self) -> asyncio.Lock:
        """Get or create connection lock (must be called from async context)."""
        if self._connect_lock is None:
            self._connect_lock = asyncio.Lock()
        return self._connect_lock

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def _connect(self) -> None:
        """Connect to Google Sheets (thread-safe with lock)."""
        async with self._get_connect_lock():
            if self._client is not None:
                return

            try:
                # Support both file path (local) and JSON string (Cloud Run)
                credentials_source = settings.credentials_source

                if credentials_source.startswith("{"):
                    # JSON string from Secret Manager
                    import json

                    creds_dict = json.loads(credentials_source)
                    creds = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=SCOPES,
                    )
                    logger.info("Connected to Google Sheets using JSON credentials")
                else:
                    # File path (local dev)
                    creds = Credentials.from_service_account_file(
                        credentials_source,
                        scopes=SCOPES,
                    )
                    logger.info(
                        f"Connected to Google Sheets using file: {credentials_source}"
                    )

                self._client = gspread.authorize(creds)

                # Find or create spreadsheet
                if settings.google_sheets_spreadsheet_id:
                    self._spreadsheet = await self._run_sync(
                        self._client.open_by_key, settings.google_sheets_spreadsheet_id
                    )
                else:
                    try:
                        self._spreadsheet = await self._run_sync(
                            self._client.open, settings.google_sheets_spreadsheet_name
                        )
                    except gspread.SpreadsheetNotFound:
                        logger.info(
                            f"Creating new spreadsheet: "
                            f"{settings.google_sheets_spreadsheet_name}"
                        )
                        self._spreadsheet = await self._run_sync(
                            self._client.create, settings.google_sheets_spreadsheet_name
                        )

                logger.info(f"Connected to spreadsheet: {self._spreadsheet.title}")

            except Exception as e:
                logger.error(f"Failed to connect to Google Sheets: {e}")
                raise

    async def _get_worksheet(self) -> gspread.Worksheet:
        """Get the main expenses worksheet."""
        await self._connect()

        worksheet_name = WORKSHEET_EXPENSES

        try:
            worksheet = await self._run_sync(
                self._spreadsheet.worksheet, worksheet_name
            )
            logger.debug(f"Using worksheet: {worksheet_name}")
        except gspread.WorksheetNotFound:
            logger.error(f"Worksheet '{worksheet_name}' not found!")
            raise ValueError(
                f"Worksheet '{worksheet_name}' does not exist in the spreadsheet"
            )

        return worksheet

    async def _get_limits_worksheet(self) -> gspread.Worksheet:
        """Get or create the limits worksheet."""
        await self._connect()

        worksheet_name = WORKSHEET_LIMITS

        try:
            worksheet = await self._run_sync(
                self._spreadsheet.worksheet, worksheet_name
            )
            logger.debug(f"Using limits worksheet: {worksheet_name}")
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

    def _calculate_month_spent_for_category(
        self,
        all_values: list[list[str]],
        target_category: str,
    ) -> float:
        """Calculate month spending for a category from already loaded data.

        This avoids a second API call when checking limits after adding expense.
        """
        if not all_values or len(all_values) < 2:
            return 0.0

        now = datetime.now()
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total = 0.0
        for row in all_values[1:]:  # Skip header
            if len(row) < 4:
                continue

            # Check category match
            category = row[1] if len(row) > 1 else ""
            if category != target_category:
                continue

            # Check date is in current month
            date_str = row[0] if len(row) > 0 else ""
            if date_str:
                try:
                    row_date = datetime.strptime(date_str, "%d.%m.%Y")
                    if row_date < start_date:
                        continue
                except ValueError:
                    pass

            # Parse amount
            try:
                amount_str = row[3] if len(row) > 3 else "0"
                amount_str = (
                    amount_str.replace(",", ".")
                    .replace("₽", "")
                    .replace(" ", "")
                    .replace("\u00a0", "")
                    .strip()
                )
                total += float(amount_str) if amount_str else 0.0
            except (ValueError, TypeError):
                pass

        return total

    async def add_expense(
        self,
        user_id: str,
        category: str,
        amount: float,
        description: str,
        date: datetime | None = None,
    ) -> dict[str, Any]:
        """Add expense to Google Sheets.

        Adds to 'Траты и бюджет' worksheet with columns:
        Дата | Категория | Расшифровка | Сумма

        Uses append_row() for atomic operation without race conditions.
        """
        try:
            worksheet = await self._get_worksheet()

            expense_date = date or datetime.now()
            date_str = expense_date.strftime("%d.%m.%Y")

            # Check limits first (cached, usually no API call)
            limits_result = await self.get_limits(user_id)
            limits = limits_result.get("limits", {})

            # Only read data if we need to check limits for this category
            limit_exceeded = None
            if category in limits:
                all_values = await self._run_sync(worksheet.get, "A:D")
                # Defensive check: worksheet.get may return None for empty ranges
                if all_values is None:
                    all_values = []
                spent_before = self._calculate_month_spent_for_category(
                    all_values, category
                )
                spent = spent_before + amount  # Include expense we're about to add
                limit = limits[category]
                if spent > limit:
                    limit_exceeded = {
                        "category": category,
                        "spent": spent,
                        "limit": limit,
                    }

            # Atomic append - no race condition possible
            await self._run_sync(
                worksheet.append_row,
                [date_str, category, description, amount],
                value_input_option="USER_ENTERED",
            )

            logger.info(
                f"Added expense for user {user_id}: {category} - {amount}"
            )

            return {
                "status": "success",
                "user_id": user_id,
                "category": category,
                "amount": amount,
                "description": description,
                "date": date_str,
                "limit_exceeded": limit_exceeded,
            }

        except Exception as e:
            logger.error(f"Failed to add expense: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def get_expenses(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get expenses from Google Sheets."""
        try:
            worksheet = await self._get_worksheet()

            # Get only first 4 columns (A:D) to avoid conflicts with other tables
            # Columns: Дата, Категория, Расшифровка, Сумма
            all_values = await self._run_sync(worksheet.get, "A:D")

            if not all_values or len(all_values) < 2:
                return {
                    "status": "success",
                    "user_id": user_id,
                    "expenses": [],
                    "count": 0,
                }

            # First row is headers, rest are data
            rows = all_values[1:]

            # Convert to list of dicts
            records = []
            for row in rows:
                # Pad row if needed
                while len(row) < 4:
                    row.append("")

                record = {
                    "Дата": row[0],
                    "Категория": row[1],
                    "Расшифровка": row[2],
                    "Сумма": row[3],
                }
                records.append(record)

            # Filter by category if needed
            if category:
                records = [r for r in records if r.get("Категория") == category]

            # Sort by date (newest first)
            def parse_date(record: dict) -> datetime:
                try:
                    return datetime.strptime(record.get("Дата", ""), "%d.%m.%Y")
                except (ValueError, TypeError):
                    return datetime.min

            records.sort(key=parse_date, reverse=True)

            # Apply limit (get first N records after sorting)
            records = records[:limit]

            return {
                "status": "success",
                "user_id": user_id,
                "expenses": records,
                "count": len(records),
            }

        except Exception as e:
            logger.error(f"Failed to get expenses: {e}")
            return {
                "status": "error",
                "error": str(e),
                "expenses": [],
                "count": 0,
            }

    async def get_statistics(
        self,
        user_id: str,
        period: str = "month",
    ) -> dict[str, Any]:
        """Get expense statistics from Google Sheets."""
        try:
            worksheet = await self._get_worksheet()

            # Get only first 4 columns (A:D)
            all_values = await self._run_sync(worksheet.get, "A:D")

            if not all_values or len(all_values) < 2:
                return {
                    "status": "success",
                    "user_id": user_id,
                    "period": period,
                    "total": 0.0,
                    "by_category": {},
                    "categories_count": 0,
                }

            # Skip header row
            rows = all_values[1:]

            # Calculate date range based on period
            now = datetime.now()
            end_date = None  # For specific month periods

            if period == "day":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                # Calendar week: from Monday of current week
                days_since_monday = now.weekday()  # Monday=0, Sunday=6
                start_date = (now - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif period == "month":
                # Calendar month: from 1st day of current month
                start_date = now.replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            elif period == "year":
                start_date = now - timedelta(days=365)
            elif "_" in period:
                # Specific month: YYYY_MM format (e.g., "2026_01" for January 2026)
                try:
                    year_str, month_str = period.split("_")
                    year = int(year_str)
                    month = int(month_str)
                    start_date = datetime(year, month, 1)
                    # End date: first day of next month
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1)
                    else:
                        end_date = datetime(year, month + 1, 1)
                except ValueError:
                    start_date = None
            else:
                start_date = None  # All time

            # Calculate statistics by category
            stats_by_category: dict[str, float] = {}
            total = 0.0

            for row in rows:
                if len(row) < 4:
                    continue

                # Parse date (format: DD.MM.YYYY)
                date_str = row[0] if len(row) > 0 else ""
                if start_date and date_str:
                    try:
                        row_date = datetime.strptime(date_str, "%d.%m.%Y")
                        if row_date < start_date:
                            continue  # Skip rows before period
                        if end_date and row_date >= end_date:
                            continue  # Skip rows after period (for specific months)
                    except ValueError:
                        pass  # Include rows with invalid dates

                category = row[1] if len(row) > 1 else "Unknown"

                # Parse amount - handle both comma and dot as decimal separator
                try:
                    amount_str = row[3] if len(row) > 3 else "0"
                    # Replace comma with dot and remove currency symbols
                    # Note: Google Sheets uses non-breaking space (\u00a0) as
                    # thousands separator, not regular space
                    amount_str = (
                        amount_str.replace(",", ".")
                        .replace("₽", "")
                        .replace(" ", "")
                        .replace("\u00a0", "")  # non-breaking space
                        .strip()
                    )
                    amount = float(amount_str) if amount_str else 0.0
                except (ValueError, TypeError):
                    amount = 0.0

                stats_by_category[category] = (
                    stats_by_category.get(category, 0) + amount
                )
                total += amount

            return {
                "status": "success",
                "user_id": user_id,
                "period": period,
                "total": total,
                "by_category": stats_by_category,
                "categories_count": len(stats_by_category),
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def delete_last_expense(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """Delete the last expense from Google Sheets."""
        try:
            worksheet = await self._get_worksheet()

            # Read only column A to find row count (optimization: O(n) vs O(n*4))
            col_a = await self._run_sync(worksheet.get, "A:A")

            # Defensive check: worksheet.get may return None for empty ranges
            if col_a is None or len(col_a) <= 1:
                return {
                    "status": "error",
                    "error": "No expenses to delete",
                }

            # Last row number (1-indexed, including header)
            last_row_number = len(col_a)

            # Read only the last row's data (4 cells instead of entire table)
            last_row_data = await self._run_sync(
                worksheet.get, f"A{last_row_number}:D{last_row_number}"
            )

            # Flatten and pad if needed
            last_row_data = last_row_data[0] if last_row_data else []
            while len(last_row_data) < 4:
                last_row_data.append("")

            deleted_expense = {
                "Дата": last_row_data[0],
                "Категория": last_row_data[1],
                "Расшифровка": last_row_data[2],
                "Сумма": last_row_data[3],
            }

            # Delete the last row
            await self._run_sync(worksheet.delete_rows, last_row_number)

            logger.info(f"Deleted last expense for user {user_id}: {deleted_expense}")

            return {
                "status": "success",
                "user_id": user_id,
                "deleted_expense": deleted_expense,
            }

        except Exception as e:
            logger.error(f"Failed to delete last expense: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

    async def add_expenses_batch(
        self,
        user_id: str,
        expenses: list[dict],
    ) -> dict[str, Any]:
        """Add multiple expenses using batch API.

        Uses append_rows() for atomic operation without race conditions.
        """
        try:
            worksheet = await self._get_worksheet()

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
                    errors.append({"index": i, "expense": exp, "error": str(e)})

            # Atomic append - no race condition possible
            if rows_to_add:
                await self._run_sync(
                    worksheet.append_rows,
                    rows_to_add,
                    value_input_option="USER_ENTERED",
                )

            logger.info(
                f"Batch added {len(rows_to_add)} expenses for user {user_id}, "
                f"failed: {len(errors)}"
            )

            return {
                "added": len(rows_to_add),
                "failed": len(errors),
                "total": len(expenses),
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Failed to batch add expenses: {e}")
            return {
                "added": 0,
                "failed": len(expenses),
                "total": len(expenses),
                "errors": [{"error": str(e)}],
            }

    async def health_check(self) -> dict[str, Any]:
        """Check Google Sheets connection health."""
        try:
            await self._connect()

            # Try to get spreadsheet info
            title = await self._run_sync(lambda: self._spreadsheet.title)

            return {
                "status": "healthy",
                "backend": "google_sheets",
                "spreadsheet": title,
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "backend": "google_sheets",
                "error": str(e),
            }

    async def get_limits(self, user_id: str) -> dict[str, Any]:
        """Get all budget limits from Google Sheets (cached for 60s)."""
        # Check cache first
        cache_key = f"limits:{user_id}"
        cached = limits_cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Limits cache hit for user {user_id}")
            return cached

        try:
            worksheet = await self._get_limits_worksheet()

            all_values = await self._run_sync(worksheet.get_all_values)
            logger.info(
                f"Limits worksheet '{worksheet.title}' has {len(all_values)} rows"
            )

            if not all_values or len(all_values) < 2:
                result = {
                    "status": "success",
                    "user_id": user_id,
                    "limits": {},
                }
                limits_cache.set(cache_key, result)
                return result

            # Skip header row
            rows = all_values[1:]
            limits = {}

            for row in rows:
                if len(row) >= 2 and row[0] and row[1]:
                    category = row[0]
                    try:
                        amount = float(
                            row[1]
                            .replace(",", ".")
                            .replace(" ", "")
                            .replace("\u00a0", "")  # non-breaking space
                        )
                        if amount > 0:
                            limits[category] = amount
                    except (ValueError, TypeError):
                        continue

            logger.info(f"Got {len(limits)} limits for user {user_id}")

            result = {
                "status": "success",
                "user_id": user_id,
                "limits": limits,
            }
            limits_cache.set(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Failed to get limits: {e}")
            return {
                "status": "error",
                "error": str(e),
                "limits": {},
            }

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
                    # Invalidate cache
                    limits_cache.invalidate(f"limits:{user_id}")
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

            # Invalidate cache after update
            limits_cache.invalidate(f"limits:{user_id}")

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

    async def delete_limit(
        self,
        user_id: str,
        category: str,
    ) -> dict[str, Any]:
        """Delete budget limit for a category."""
        return await self.set_limit(user_id, category, 0)
