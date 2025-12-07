"""Google Sheets storage implementation."""

import asyncio
import logging
from datetime import datetime
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
            creds = Credentials.from_service_account_file(
                settings.google_application_credentials,
                scopes=SCOPES,
            )
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

            # Calculate statistics by category
            stats_by_category: dict[str, float] = {}
            total = 0.0

            for row in rows:
                if len(row) < 4:
                    continue

                category = row[1] if len(row) > 1 else "Unknown"
                try:
                    amount = float(row[3]) if len(row) > 3 else 0.0
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
