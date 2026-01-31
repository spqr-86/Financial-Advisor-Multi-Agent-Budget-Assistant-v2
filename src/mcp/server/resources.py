"""MCP resources для предоставления контекста клиентам."""

from src.core.categories import get_categories_list

# Generate categories list for help text
_categories_text = "\n".join(f"- {cat}" for cat in get_categories_list())

HELP_TEXT = f"""# Budget Assistant v2.0

Я - AI помощник для управления семейным бюджетом.

## Что я умею:

### 📝 Добавление расходов
Примеры:
- "купил хлеб 50 рублей"
- "потратил на кино 500"
- "заправка бензином 2000"

### 📊 Просмотр расходов
Примеры:
- "покажи последние расходы"
- "что я покупал сегодня"
- "расходы на продукты"

### 📈 Статистика
Примеры:
- "статистика за месяц"
- "сколько потратил"
- "топ категорий по расходам"

### 🗑️ Удаление
- "удали последний расход" (если ошибся)

## Категории расходов:
{_categories_text}
"""

CATEGORIES_DATA = {
    "categories": get_categories_list()
}
