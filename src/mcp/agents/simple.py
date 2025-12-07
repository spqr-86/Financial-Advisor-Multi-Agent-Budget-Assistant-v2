"""Simple budget agent using Google Gemini."""

import logging
from typing import Any

import google.generativeai as genai

from src.mcp.agents.tools.sheets import get_budget_tools
from src.mcp.config import settings

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """Ты - финансовый ассистент для семейного бюджета.

Твои возможности:
1. **add_expense_tool** - добавлять расходы в таблицу
2. **get_expenses_tool** - показывать последние расходы
3. **get_statistics_tool** - показывать статистику по категориям
4. **delete_last_expense_tool** - удалить последний расход (если пользователь ошибся)

Основные категории расходов:
- Продукты
- Транспорт
- Рестораны
- Развлечения
- ЖКХ
- Одежда
- Здоровье
- Прочее

Когда пользователь описывает покупку (например "купил хлеб 50 рублей" или "потратил на кино 500"):
1. Определи категорию из списка выше
2. Извлеки сумму
3. Сформулируй краткое описание
4. Вызови add_expense_tool с этими параметрами
5. Подтверди пользователю что расход добавлен

Когда пользователь просит показать расходы или статистику:
1. Используй get_expenses_tool или get_statistics_tool
2. Отформатируй ответ понятно и структурированно

Когда пользователь говорит что ошибся или просит удалить:
1. Используй delete_last_expense_tool
2. Подтверди что удалили

Отвечай кратко и дружелюбно на русском языке.
Если не уверен в категории - спроси у пользователя.
"""


class SimpleBudgetAgent:
    """Simple budget agent powered by Google Gemini."""

    def __init__(self):
        """Initialize the agent."""
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)

        # Get budget tools
        self.tools = get_budget_tools()

        # Create model with tools
        # Using gemini-1.5-flash (stable) instead of 2.0-exp to avoid quota issues
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION,
            tools=self.tools,
        )

        # Store chat sessions per user
        self._chats: dict[str, Any] = {}

        logger.info("SimpleBudgetAgent initialized with Gemini 1.5 Flash")

    def _get_chat(self, user_id: str):
        """Get or create chat session for user."""
        if user_id not in self._chats:
            self._chats[user_id] = self.model.start_chat(enable_automatic_function_calling=True)
        return self._chats[user_id]

    async def process(self, query: str, user_id: str) -> str:
        """
        Process user query with AI agent.

        Args:
            query: User's message
            user_id: User identifier

        Returns:
            Agent's response
        """
        try:
            logger.info(f"Processing query for user {user_id}: {query[:50]}...")

            # Get chat session
            chat = self._get_chat(user_id)

            # Send message (automatic function calling enabled)
            response = chat.send_message(query)

            # Extract text response
            if response.text:
                logger.info(f"Agent response: {response.text[:100]}...")
                return response.text
            else:
                logger.warning("No text in response")
                return "Извините, не смог обработать запрос."

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return f"Произошла ошибка: {str(e)}"
