"""MCP tools - обертки над ADKBudgetAgent и storage."""

import logging
from typing import Any

from src.mcp.agents import ADKBudgetAgent

logger = logging.getLogger(__name__)

# Глобальный агент (lazy initialization)
_agent: ADKBudgetAgent | None = None


def get_agent() -> ADKBudgetAgent:
    """Get or create agent instance."""
    global _agent
    if _agent is None:
        logger.info("Initializing ADKBudgetAgent for MCP server...")
        _agent = ADKBudgetAgent()
    return _agent


async def process_query(query: str, user_id: str = "default") -> str:
    """
    Обработать запрос пользователя через AI-агентную систему.

    Args:
        query: Запрос на русском языке (например "купил хлеб 50 рублей")
        user_id: ID пользователя (опционально, по умолчанию "default")

    Returns:
        Ответ агентной системы с результатом обработки запроса
    """
    agent = get_agent()
    return await agent.process(query=query, user_id=user_id)


# ОПЦИОНАЛЬНО: Прямые tools для специфических операций (минуя оркестратор)

async def add_expense_direct(
    category: str,
    amount: float,
    description: str,
    user_id: str = "default"
) -> dict[str, Any]:
    """
    Добавить расход напрямую (без AI обработки).

    Args:
        category: Категория расхода
        amount: Сумма в рублях
        description: Описание покупки
        user_id: ID пользователя

    Returns:
        Результат добавления расхода
    """
    from src.mcp.agents.tools.sheets import add_expense_tool

    return await add_expense_tool(
        category=category,
        amount=amount,
        description=description,
        user_id=user_id
    )


async def get_expenses_direct(
    limit: int = 10,
    category: str | None = None,
    user_id: str = "default"
) -> dict[str, Any]:
    """
    Получить последние расходы напрямую.

    Args:
        limit: Количество последних записей
        category: Фильтр по категории (опционально)
        user_id: ID пользователя

    Returns:
        Список расходов
    """
    from src.mcp.agents.tools.sheets import get_expenses_tool

    return await get_expenses_tool(
        limit=limit,
        category=category,
        user_id=user_id
    )


async def get_statistics_direct(
    period: str = "month",
    user_id: str = "default"
) -> dict[str, Any]:
    """
    Получить статистику расходов напрямую.

    Args:
        period: Период (day, week, month, year)
        user_id: ID пользователя

    Returns:
        Статистика расходов
    """
    from src.mcp.agents.tools.sheets import get_statistics_tool

    return await get_statistics_tool(
        period=period,
        user_id=user_id
    )


async def delete_last_expense_direct(
    user_id: str = "default"
) -> dict[str, Any]:
    """
    Удалить последний расход напрямую.

    Args:
        user_id: ID пользователя

    Returns:
        Информация об удаленном расходе
    """
    from src.mcp.agents.tools.sheets import delete_last_expense_tool

    return await delete_last_expense_tool(user_id=user_id)


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
