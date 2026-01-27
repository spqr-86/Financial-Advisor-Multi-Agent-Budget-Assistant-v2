"""Message formatting functions with emoji and HTML."""

from datetime import datetime
from typing import Any

# Category emoji mapping
CATEGORY_EMOJI = {
    "Аренда": "🏠",
    "Детский сад": "👶",
    "Продукты": "🛒",
    "Транспорт": "🚗",
    "Еда": "🍔",
    "Прочее": "💼",
    "Алкоголь": "🍷",
    "Здоровье, красота, гигиена": "💊",
    "Спорт": "⚽",
    "Творчество, книги, обучение": "📚",
    "WB": "🛍️",
    "Яндекс.Маркет": "📦",
    "Подписки": "📺",
    "Коммуналка": "💡",
    "Кино, театры, музеи": "🎭",
    "Одежда": "👕",
    "Подарки": "🎁",
    "Связь": "📱",
    "Рестораны": "🍽️",
    "Кредит": "🏦",
    "Кредитка": "💳",
}


def get_category_emoji(category: str) -> str:
    """Get emoji for a category, with fallback."""
    # Try exact match first
    if category in CATEGORY_EMOJI:
        return CATEGORY_EMOJI[category]

    # Try case-insensitive match
    category_lower = category.lower()
    for cat_name, emoji in CATEGORY_EMOJI.items():
        if cat_name.lower() == category_lower:
            return emoji

    # Default emoji
    return "💼"


def format_expense_added(
    category: str,
    amount: float,
    description: str = "",
    date: str = "",
) -> str:
    """Format expense added confirmation message.

    Args:
        category: Expense category
        amount: Expense amount
        description: Optional description
        date: Optional date (DD.MM.YYYY)

    Returns:
        Formatted HTML message
    """
    emoji = get_category_emoji(category)

    if not date:
        date = datetime.now().strftime("%d.%m.%Y")

    msg = "✅ <b>Расход добавлен!</b>\n\n"
    msg += f"📝 Категория: {emoji} <code>{category}</code>\n"
    msg += f"💰 Сумма: <b>{amount:.0f}₽</b>\n"

    if description:
        msg += f"📄 Описание: {description}\n"

    msg += f"📅 Дата: {date}"

    return msg


def format_expense_deleted() -> str:
    """Format expense deletion confirmation message."""
    return "✅ <b>Последний расход удален!</b>"


def format_expenses_list(expenses: list[dict[str, Any]], limit: int = 5) -> str:
    """Format list of expenses.

    Args:
        expenses: List of expense dictionaries
        limit: Number of expenses to show

    Returns:
        Formatted HTML message
    """
    if not expenses:
        return "📝 <b>Расходов пока нет</b>\n\nНапишите что-нибудь вроде:\n<code>купил хлеб 50 рублей</code>"

    msg = f"📝 <b>Последние {min(limit, len(expenses))} расходов:</b>\n\n"

    number_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, expense in enumerate(expenses[:limit]):
        num = number_emoji[i] if i < len(number_emoji) else f"{i + 1}."

        date = expense.get("date", "")
        category = expense.get("category", "Другое")
        emoji = get_category_emoji(category)
        description = expense.get("description", "")
        amount = expense.get("amount", 0)

        msg += f"{num} {date} | {emoji} <b>{category}</b> | {description} - <b>{amount:.0f}₽</b>\n"

    return msg


def format_statistics(stats: dict[str, Any], period: str = "неделю") -> str:
    """Format statistics with progress bars.

    Args:
        stats: Statistics dictionary with categories and amounts
        period: Period description (неделю, месяц, год)

    Returns:
        Formatted HTML message
    """
    if not stats or "categories" not in stats:
        return f"📊 <b>Статистика за {period}</b>\n\nДанных пока нет."

    categories = stats.get("categories", {})
    total = stats.get("total", 0)

    if not categories or total == 0:
        return f"📊 <b>Статистика за {period}</b>\n\nРасходов за этот период нет."

    msg = f"📊 <b>Статистика за {period}</b>\n\n"

    # Sort by amount descending
    sorted_categories = sorted(
        categories.items(), key=lambda x: x[1], reverse=True
    )

    for category, amount in sorted_categories:
        emoji = get_category_emoji(category)
        percentage = (amount / total) * 100 if total > 0 else 0

        # Progress bar (10 blocks)
        filled = int(percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)

        msg += f"{emoji} <b>{category}</b>: {amount:.0f}₽ {bar} {percentage:.0f}%\n"

    msg += f"\n💰 <b>Итого: {total:.0f}₽</b>"

    return msg


def format_help_message() -> str:
    """Format help message with examples and instructions."""
    msg = "❓ <b>Как использовать бота</b>\n\n"

    msg += "📝 <b>ТЕКСТОМ</b> (естественный язык):\n"
    msg += "• <code>купил хлеб 50 рублей</code>\n"
    msg += "• <code>потратил 1000 на такси</code>\n"
    msg += "• <code>покажи расходы за неделю</code>\n"
    msg += "• <code>статистика по категории еда</code>\n\n"

    msg += "🔘 <b>КНОПКАМИ:</b>\n"
    msg += "Используй кнопки внизу для быстрого доступа\n\n"

    msg += "📂 <b>КАТЕГОРИИ:</b>\n"
    categories_list = " | ".join(
        [f"{emoji} {name}" for name, emoji in CATEGORY_EMOJI.items()]
    )
    msg += categories_list + "\n\n"

    msg += "⚡ <b>КОМАНДЫ:</b>\n"
    msg += "/start - Начать работу\n"
    msg += "/help - Эта справка\n"
    msg += "/stats - Статистика\n"
    msg += "/last - Последние расходы\n"
    msg += "/delete - Удалить последний расход"

    return msg


def format_examples_message() -> str:
    """Format examples message with common use cases."""
    msg = "📖 <b>Примеры использования</b>\n\n"

    msg += "<b>Добавление расходов:</b>\n"
    msg += "• <code>купил кофе 150</code>\n"
    msg += "• <code>потратил 500 на обед</code>\n"
    msg += "• <code>такси домой 300 рублей</code>\n"
    msg += "• <code>продукты в магазине 2500</code>\n\n"

    msg += "<b>Просмотр расходов:</b>\n"
    msg += "• <code>покажи расходы</code>\n"
    msg += "• <code>что я покупал сегодня</code>\n"
    msg += "• <code>последние траты</code>\n\n"

    msg += "<b>Статистика:</b>\n"
    msg += "• <code>статистика</code>\n"
    msg += "• <code>статистика за неделю</code>\n"
    msg += "• <code>сколько потратил на еду</code>\n\n"

    msg += "<b>Удаление:</b>\n"
    msg += "• <code>удали последний расход</code>\n"
    msg += "• <code>отмени последнюю трату</code>\n\n"

    msg += "💡 <b>Совет:</b> Пишите естественно, бот поймет!"

    return msg
