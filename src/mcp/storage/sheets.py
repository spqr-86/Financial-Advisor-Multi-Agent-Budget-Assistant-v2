"""Google Sheets storage implementation."""

import asyncio
import logging
from datetime import datetime, timedelta
from functools import partial
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

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

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(func, *args, **kwargs)
        )

    async def _connect(self) -> None:
        """Connect to Google Sheets."""
        if self._client is not None:
            return

        try:
            # Support both file path (local) and JSON string (Cloud Run)
            credentials_source = settings.credentials_source

            if credentials_source.startswith('{'):
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
                logger.info(f"Connected to Google Sheets using file: {credentials_source}")

            self._client = gspread.authorize(creds)

            # Find or create spreadsheet
            if settings.google_sheets_spreadsheet_id:
                self._spreadsheet = await self._run_sync(
                    self._client.open_by_key,
                    settings.google_sheets_spreadsheet_id
                )
            else:
                try:
                    self._spreadsheet = await self._run_sync(
                        self._client.open,
                        settings.google_sheets_spreadsheet_name
                    )
                except gspread.SpreadsheetNotFound:
                    logger.info(
                        f"Creating new spreadsheet: {settings.google_sheets_spreadsheet_name}"
                    )
                    self._spreadsheet = await self._run_sync(
                        self._client.create,
                        settings.google_sheets_spreadsheet_name
                    )

            logger.info(f"Connected to spreadsheet: {self._spreadsheet.title}")

        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise

    async def _get_worksheet(self) -> gspread.Worksheet:
        """Get the main expenses worksheet."""
        await self._connect()

        worksheet_name = "Траты и бюджет"

        try:
            worksheet = await self._run_sync(
                self._spreadsheet.worksheet,
                worksheet_name
            )
            logger.info(f"Using worksheet: {worksheet_name}")
        except gspread.WorksheetNotFound:
            logger.error(f"Worksheet '{worksheet_name}' not found!")
            raise ValueError(f"Worksheet '{worksheet_name}' does not exist in the spreadsheet")

        return worksheet

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
        """
        try:
            worksheet = await self._get_worksheet()

            expense_date = date or datetime.now()
            date_str = expense_date.strftime("%d.%m.%Y")

            # Append row: Дата, Категория, Расшифровка, Сумма
            await self._run_sync(
                worksheet.append_row,
                [date_str, category, description, amount]
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
            headers = all_values[0]
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

            # Apply limit (get last N records)
            records = records[-limit:] if len(records) > limit else records

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
            if period == "day":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_date = now - timedelta(days=7)
            elif period == "month":
                start_date = now - timedelta(days=30)
            elif period == "year":
                start_date = now - timedelta(days=365)
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
                            continue  # Skip rows outside period
                    except ValueError:
                        pass  # Include rows with invalid dates

                category = row[1] if len(row) > 1 else "Unknown"

                # Parse amount - handle both comma and dot as decimal separator
                try:
                    amount_str = row[3] if len(row) > 3 else "0"
                    # Replace comma with dot and remove currency symbols
                    amount_str = amount_str.replace(",", ".").replace("₽", "").replace(" ", "").strip()
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

            # Get all rows to find the last one
            all_values = await self._run_sync(worksheet.get, "A:D")

            if not all_values or len(all_values) <= 1:
                return {
                    "status": "error",
                    "error": "No expenses to delete",
                }

            # Last row number (1-indexed, including header)
            last_row_number = len(all_values)
            last_row_data = all_values[-1]

            # Pad row if needed
            while len(last_row_data) < 4:
                last_row_data.append("")

            deleted_expense = {
                "Дата": last_row_data[0],
                "Категория": last_row_data[1],
                "Расшифровка": last_row_data[2],
                "Сумма": last_row_data[3],
            }

            # Delete the last row
            await self._run_sync(
                worksheet.delete_rows,
                last_row_number
            )

            logger.info(
                f"Deleted last expense for user {user_id}: {deleted_expense}"
            )

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
        """Add multiple expenses using batch API."""
        try:
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

        except Exception as e:
            logger.error(f"Failed to batch add expenses: {e}")
            return {
                "added": 0,
                "failed": len(expenses),
                "total": len(expenses),
                "errors": [{"error": str(e)}]
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
