"""Abstract storage interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class StorageInterface(ABC):
    """Abstract interface for storage backends."""

    @abstractmethod
    async def add_expense(
        self,
        user_id: str,
        category: str,
        amount: float,
        description: str,
        date: datetime | None = None,
    ) -> dict[str, Any]:
        """Add an expense record.

        Args:
            user_id: User identifier
            category: Expense category
            amount: Expense amount
            description: Expense description
            date: Expense date (defaults to now)

        Returns:
            dict with status and expense details
        """

    @abstractmethod
    async def get_expenses(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get expenses with filters.

        Args:
            user_id: User identifier
            start_date: Filter from this date
            end_date: Filter until this date
            category: Filter by category
            limit: Maximum number of records

        Returns:
            dict with expenses list
        """

    @abstractmethod
    async def get_statistics(
        self,
        user_id: str,
        period: str = "month",
    ) -> dict[str, Any]:
        """Get expense statistics.

        Args:
            user_id: User identifier
            period: Period for statistics (day, week, month, year)

        Returns:
            dict with statistics by category
        """

    @abstractmethod
    async def delete_last_expense(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """Delete the last expense record.

        Args:
            user_id: User identifier

        Returns:
            dict with status and deleted expense info
        """

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

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check storage health.

        Returns:
            dict with health status
        """
