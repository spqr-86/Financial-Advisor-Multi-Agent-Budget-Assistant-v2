"""MCP Server для Budget Assistant на базе FastMCP."""

import logging

from fastmcp import FastMCP

from src.mcp.server import resources, tools
from src.mcp.server.config import settings

logger = logging.getLogger(__name__)

# Создаем MCP сервер
mcp = FastMCP(
    name=settings.mcp_server_name,
    version=settings.mcp_server_version,
)


# === TOOLS ===


@mcp.tool()
async def process_query(query: str, user_id: str = "default") -> str:
    """
    Обработать запрос пользователя через AI-агентную систему бюджета.

    Используйте этот tool для всех операций с бюджетом:
    - Добавление расходов: "купил хлеб 50 рублей"
    - Просмотр расходов: "покажи последние расходы"
    - Статистика: "статистика за месяц"
    - Удаление: "удали последний расход"

    Args:
        query: Запрос на русском языке
        user_id: ID пользователя (опционально, по умолчанию "default")

    Returns:
        Ответ агентной системы
    """
    return await tools.process_query(query=query, user_id=user_id)


# ОПЦИОНАЛЬНО: Прямые tools для direct access


@mcp.tool()
async def add_expense(
    category: str,
    amount: float,
    description: str,
    user_id: str = "default"
) -> dict:
    """
    Добавить расход напрямую (без AI обработки).

    Args:
        category: Категория (Аренда, Детский сад, Продукты, Транспорт, Еда, Прочее,
                  Алкоголь, Здоровье/красота/гигиена, Спорт, Творчество/книги/обучение,
                  WB, Яндекс.Маркет, Подписки, Коммуналка, Кино/театры/музеи, Одежда,
                  Подарки, Связь, Рестораны, Кредит, Кредитка)
        amount: Сумма в рублях
        description: Описание покупки
        user_id: ID пользователя (опционально)

    Returns:
        Результат добавления расхода
    """
    return await tools.add_expense_direct(
        category=category,
        amount=amount,
        description=description,
        user_id=user_id
    )


@mcp.tool()
async def get_expenses(
    limit: int = 10,
    category: str | None = None,
    user_id: str = "default"
) -> dict:
    """
    Получить последние расходы.

    Args:
        limit: Количество последних записей (по умолчанию 10)
        category: Фильтр по категории (опционально)
        user_id: ID пользователя (опционально)

    Returns:
        Список расходов
    """
    return await tools.get_expenses_direct(
        limit=limit,
        category=category,
        user_id=user_id
    )


@mcp.tool()
async def get_statistics(period: str = "month", user_id: str = "default") -> dict:
    """
    Получить статистику расходов по категориям.

    Args:
        period: Период (day, week, month, year) - пока не используется
        user_id: ID пользователя (опционально)

    Returns:
        Статистика: общая сумма и суммы по категориям
    """
    return await tools.get_statistics_direct(period=period, user_id=user_id)


@mcp.tool()
async def delete_last_expense(user_id: str = "default") -> dict:
    """
    Удалить последний добавленный расход.

    Args:
        user_id: ID пользователя (опционально)

    Returns:
        Информация об удаленном расходе
    """
    return await tools.delete_last_expense_direct(user_id=user_id)


@mcp.tool()
async def add_expenses_batch(
    expenses: list[dict],
    user_id: str = "default"
) -> dict:
    """
    Массовое добавление расходов (для импорта банковских выписок).

    Используйте этот tool для добавления множества расходов за один раз,
    например при импорте банковской выписки или загрузке истории расходов.

    Args:
        expenses: Список расходов, каждый содержит:
            - category: str (21 категория: Аренда, Детский сад, Продукты, Транспорт,
              Еда, Прочее, Алкоголь, Здоровье/красота/гигиена, Спорт,
              Творчество/книги/обучение, WB, Яндекс.Маркет, Подписки, Коммуналка,
              Кино/театры/музеи, Одежда, Подарки, Связь, Рестораны, Кредит, Кредитка)
            - amount: float (сумма в рублях)
            - description: str (описание покупки)
            - date: str (опционально, формат "DD.MM.YYYY", по умолчанию текущая дата)
        user_id: ID пользователя (опционально)

    Returns:
        {
            "status": "success" | "partial" | "error",
            "added": количество успешно добавленных расходов,
            "failed": количество неудачных попыток,
            "total": общее количество,
            "errors": список ошибок с индексами (если есть)
        }
    """
    return await tools.add_expenses_batch_direct(
        expenses=expenses,
        user_id=user_id
    )


# === RESOURCES ===


@mcp.resource("budget://help")
async def get_help() -> str:
    """Получить инструкцию по использованию Budget Assistant."""
    return resources.HELP_TEXT


@mcp.resource("budget://categories")
async def get_categories() -> dict:
    """Получить список категорий расходов."""
    return resources.CATEGORIES_DATA


# === PROMPTS ===


@mcp.prompt()
async def expense_prompt(item: str, amount: float) -> str:
    """Шаблон для добавления расхода."""
    return f"Добавь расход: {item} за {amount} рублей"


@mcp.prompt()
async def statistics_prompt(period: str = "месяц") -> str:
    """Шаблон для запроса статистики."""
    return f"Покажи статистику расходов за {period}"


@mcp.prompt()
async def expenses_prompt(limit: int = 10) -> str:
    """Шаблон для просмотра расходов."""
    return f"Покажи последние {limit} расходов"
