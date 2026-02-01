"""Budget tools for AI agent to interact with Google Sheets."""

import logging
from typing import Any

from src.mcp.storage.sheets import GoogleSheetsStorage

logger = logging.getLogger(__name__)

# Global storage instance
_storage: GoogleSheetsStorage | None = None


def get_storage() -> GoogleSheetsStorage:
    """Get or create storage instance."""
    global _storage
    if _storage is None:
        _storage = GoogleSheetsStorage()
    return _storage


async def add_expense_tool(
    category: str,
    amount: float,
    description: str,
    user_id: str = "default",
    date: str | None = None,
) -> dict[str, Any]:
    """
    Добавить расход в бюджет.

    Args:
        category: Категория расхода (Еда, Прочее, Алкоголь, Здоровье/красота/гигиена,
                  Спорт, Творчество/книги/обучение, Маркетплейсы,
                  Бытовая техника/электроника, Подписки, Коммуналка,
                  Кино/театры/музеи, Одежда, Подарки, Связь, Рестораны, Кредит, Кредитка)
        amount: Сумма в рублях (число, например 150.50)
        description: Описание покупки (например "хлеб и молоко", "кофе")
        user_id: ID пользователя (опционально)
        date: Дата расхода в формате DD.MM.YYYY (опционально, по умолчанию сегодня)

    Returns:
        Результат добавления расхода
    """
    from datetime import datetime

    storage = get_storage()

    # Parse date if provided
    expense_date = None
    if date:
        try:
            expense_date = datetime.strptime(date, "%d.%m.%Y")
        except ValueError:
            logger.warning(f"Invalid date format: {date}, using today")

    result = await storage.add_expense(
        user_id=user_id,
        category=category,
        amount=amount,
        description=description,
        date=expense_date,
    )
    logger.info(f"AI added expense: {category} - {amount} (date: {date or 'today'})")
    return result


async def get_expenses_tool(
    limit: int = 10,
    category: str | None = None,
    user_id: str = "default",
) -> dict[str, Any]:
    """
    Получить последние расходы из бюджета.

    Args:
        limit: Сколько последних записей показать (по умолчанию 10)
        category: Фильтр по категории (опционально)
        user_id: ID пользователя (опционально)

    Returns:
        Список последних расходов
    """
    storage = get_storage()
    result = await storage.get_expenses(
        user_id=user_id,
        limit=limit,
        category=category,
    )
    logger.info(f"AI requested expenses: limit={limit}, category={category}")
    return result


async def get_statistics_tool(
    period: str = "month",
    user_id: str = "default",
) -> dict[str, Any]:
    """
    Получить статистику расходов по категориям.

    Args:
        period: Период (day, week, month, year) - пока не используется,
                показывает все расходы
        user_id: ID пользователя (опционально)

    Returns:
        Статистика: общая сумма и суммы по категориям
    """
    storage = get_storage()
    result = await storage.get_statistics(
        user_id=user_id,
        period=period,
    )
    logger.info(f"AI requested statistics: period={period}")
    return result


async def delete_last_expense_tool(
    user_id: str = "default",
) -> dict[str, Any]:
    """
    Удалить последний добавленный расход.

    Полезно если пользователь ошибся при вводе.

    Args:
        user_id: ID пользователя (опционально)

    Returns:
        Информация об удаленном расходе
    """
    storage = get_storage()
    result = await storage.delete_last_expense(user_id=user_id)
    logger.info("AI deleted last expense")
    return result


def get_budget_tools() -> list[callable]:
    """Get list of budget tools for AI agent."""
    return [
        add_expense_tool,
        get_expenses_tool,
        get_statistics_tool,
        delete_last_expense_tool,
    ]
