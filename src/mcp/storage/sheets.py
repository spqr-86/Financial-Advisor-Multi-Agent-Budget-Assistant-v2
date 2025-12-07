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

    async def _get_or_create_user_worksheet(
        self, user_id: str
    ) -> gspread.Worksheet:
        """Get or create user-specific worksheet."""
        await self._connect()

        worksheet_name = f"User_{user_id}"

        try:
            worksheet = await self._run_sync(
                self._spreadsheet.worksheet,
                worksheet_name
            )
        except gspread.WorksheetNotFound:
            logger.info(f"Creating worksheet for user {user_id}")
            worksheet = await self._run_sync(
                self._spreadsheet.add_worksheet,
                title=worksheet_name,
                rows=1000,
                cols=5
            )
            # Add header row
            await self._run_sync(
                worksheet.append_row,
                ["Дата", "Категория", "Описание", "Сумма", "Timestamp"]
            )

        return worksheet

    async def add_expense(
        self,
        user_id: str,
        category: str,
        amount: float,
        description: str,
        date: datetime | None = None,
    ) -> dict[str, Any]:
        """Add expense to Google Sheets."""
        try:
            worksheet = await self._get_or_create_user_worksheet(user_id)

            expense_date = date or datetime.now()
            date_str = expense_date.strftime("%d.%m.%Y")
            timestamp = expense_date.isoformat()

            await self._run_sync(
                worksheet.append_row,
                [date_str, category, description, amount, timestamp]
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
            worksheet = await self._get_or_create_user_worksheet(user_id)

            # Get all records
            records = await self._run_sync(worksheet.get_all_records)

            # Filter records
            filtered = records

            if start_date:
                filtered = [
                    r for r in filtered
                    if datetime.fromisoformat(r.get("Timestamp", ""))
                    >= start_date
                ]

            if end_date:
                filtered = [
                    r for r in filtered
                    if datetime.fromisoformat(r.get("Timestamp", ""))
                    <= end_date
                ]

            if category:
                filtered = [
                    r for r in filtered
                    if r.get("Категория") == category
                ]

            # Apply limit
            filtered = filtered[:limit]

            return {
                "status": "success",
                "user_id": user_id,
                "expenses": filtered,
                "count": len(filtered),
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
            worksheet = await self._get_or_create_user_worksheet(user_id)
            records = await self._run_sync(worksheet.get_all_records)

            # Calculate statistics by category
            stats_by_category: dict[str, float] = {}
            total = 0.0

            for record in records:
                category = record.get("Категория", "Unknown")
                amount = float(record.get("Сумма", 0))

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
