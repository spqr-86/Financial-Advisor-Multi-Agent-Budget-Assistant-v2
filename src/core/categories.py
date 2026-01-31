"""Single source of truth for expense categories."""

# Main category → emoji mapping
CATEGORY_EMOJI: dict[str, str] = {
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

# Set of valid category names (derived from CATEGORY_EMOJI)
VALID_CATEGORIES: set[str] = set(CATEGORY_EMOJI.keys())

# Categories shown in reply keyboard (subset for quick access)
KEYBOARD_CATEGORIES: list[list[str]] = [
    ["Продукты", "Транспорт", "Еда"],
    ["Аренда", "Коммуналка", "Связь"],
    ["Одежда", "Здоровье, красота, гигиена", "Рестораны"],
    ["Подарки", "Кино, театры, музеи", "Прочее"],
]


def get_category_emoji(category: str) -> str:
    """Get emoji for a category, with fallback.

    Args:
        category: Category name

    Returns:
        Emoji string, or default 💼 if not found
    """
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


def get_category_with_emoji(category: str) -> str:
    """Get category name with emoji prefix.

    Args:
        category: Category name

    Returns:
        String like "🛒 Продукты"
    """
    emoji = get_category_emoji(category)
    return f"{emoji} {category}"


def parse_category_with_emoji(text: str) -> str:
    """Parse category from text that may include emoji.

    Args:
        text: Text like "🛒 Продукты" or just "Продукты"

    Returns:
        Clean category name like "Продукты"
    """
    # Try to match "emoji category" pattern
    for category, emoji in CATEGORY_EMOJI.items():
        if text == f"{emoji} {category}" or text == category:
            return category

    # Return as-is if no match
    return text


def get_categories_list() -> list[str]:
    """Get list of all category names.

    Returns:
        List of category names
    """
    return list(CATEGORY_EMOJI.keys())


def format_categories_for_prompt() -> str:
    """Format categories with emoji for AI prompts.

    Returns:
        Formatted string like:
        🏠 Аренда
        👶 Детский сад
        ...
    """
    return "\n".join(
        f"   {emoji} {category}" for category, emoji in CATEGORY_EMOJI.items()
    )
