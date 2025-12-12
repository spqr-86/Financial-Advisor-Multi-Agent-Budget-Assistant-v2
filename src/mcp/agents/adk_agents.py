"""Multi-agent system using google-adk patterns from 5-days course."""

import logging
import os
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.genai import types

from src.mcp.agents.tools.sheets import (
    add_expense_tool,
    delete_last_expense_tool,
    get_expenses_tool,
    get_statistics_tool,
)
from src.mcp.config import settings

logger = logging.getLogger(__name__)

# Setup API key in environment (ADK way)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Retry configuration for robustness
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# Registrar Agent - specialized in adding/deleting expenses
registrar_agent = LlmAgent(
    name="RegistrarAgent",
    model=Gemini(
        model=settings.gemini_model,  # Configurable via GEMINI_MODEL env var
        retry_options=retry_config,
    ),
    instruction="""Ты - агент-регистратор для семейного бюджета.

Твои возможности:
1. **add_expense_tool** - добавлять расходы в таблицу
2. **delete_last_expense_tool** - удалить последний расход (если пользователь ошибся)

Основные категории расходов:
- Продукты
- Транспорт
- Рестораны
- Развлечения
- ЖКХ
- Одежда
- Здоровье
- Прочее

КРИТИЧЕСКИ ВАЖНО:
Когда пользователь описывает покупку (например "купил хлеб 50 рублей"):
1. Определи категорию из списка выше
2. Извлеки сумму
3. Сформулируй краткое описание
4. ОБЯЗАТЕЛЬНО вызови add_expense_tool с параметрами: category, amount, description, user_id="default"
5. ТОЛЬКО ПОСЛЕ успешного вызова tool подтверди пользователю что расход добавлен

НЕ симулируй добавление! ВСЕГДА вызывай add_expense_tool для реального добавления в таблицу.
Отвечай кратко и дружелюбно на русском языке.""",
    tools=[add_expense_tool, delete_last_expense_tool],  # Передаем функции напрямую
    output_key="registrar_result",
)


# Analyst Agent - specialized in viewing expenses and statistics
analyst_agent = LlmAgent(
    name="AnalystAgent",
    model=Gemini(
        model=settings.gemini_model,  # Configurable via GEMINI_MODEL env var
        retry_options=retry_config,
    ),
    instruction="""Ты - агент-аналитик для семейного бюджета.

Твои возможности:
1. **get_expenses_tool** - показывать последние расходы
2. **get_statistics_tool** - показывать статистику по категориям

Когда пользователь просит показать расходы:
1. Используй get_expenses_tool с параметрами: limit, category (если указана), user_id="default"
2. Отформатируй ответ красиво с emoji, БЕЗ markdown таблиц
3. Формат для каждого расхода:
   <дата> | <emoji категории> <категория> | <описание> - <сумма>₽

   Примеры emoji:
   🍕 Еда, Продукты, Рестораны
   🚗 Транспорт
   🏠 Дом, ЖКХ
   🎮 Развлечения
   💊 Здоровье
   👕 Одежда
   🎓 Образование
   💼 Прочее

Когда пользователь просит статистику:
1. Используй get_statistics_tool с параметрами: period, user_id="default"
2. Отформатируй с emoji и прогресс-барами (используй символы █ и ░):
   <emoji> <категория>: <сумма>₽ ████████░░ <процент>%
3. В конце покажи общую сумму

ВАЖНО: НЕ используй markdown таблицы! Telegram их не поддерживает красиво.
Отвечай кратко и дружелюбно на русском языке.""",
    tools=[get_expenses_tool, get_statistics_tool],  # Передаем функции напрямую
    output_key="analyst_result",
)


# Root Agent (LLM Orchestrator) - coordinates specialized agents
root_agent = LlmAgent(
    name="BudgetOrchestrator",
    model=Gemini(
        model=settings.gemini_model,  # Configurable via GEMINI_MODEL env var
        retry_options=retry_config,
    ),
    instruction="""Ты - оркестратор системы управления семейным бюджетом.

У тебя есть два специализированных агента:

1. **RegistrarAgent** - для ДОБАВЛЕНИЯ или УДАЛЕНИЯ расходов
   Вызывай когда пользователь:
   - Описывает покупку ("купил хлеб 50 рублей", "потратил на кино 500")
   - Просит добавить расход
   - Просит удалить последний расход

2. **AnalystAgent** - для ПРОСМОТРА расходов и СТАТИСТИКИ
   Вызывай когда пользователь:
   - Хочет увидеть расходы ("покажи последние расходы", "что я купил")
   - Просит статистику ("статистика за месяц", "сколько потратил")
   - Спрашивает про суммы или категории

ВАЖНО:
1. СНАЧАЛА вызови нужного агента (RegistrarAgent или AnalystAgent)
2. ЗАТЕМ передай результат пользователю

Для приветствий и общих вопросов отвечай сам, не вызывая агентов.

Отвечай кратко и дружелюбно на русском языке.""",
    tools=[
        AgentTool(registrar_agent),  # Используем AgentTool для вложенных агентов
        AgentTool(analyst_agent),
    ],
)


class ADKBudgetAgent:
    """Budget agent system using google-adk architecture."""

    def __init__(self):
        """Initialize the ADK budget agent."""
        self.runner = InMemoryRunner(agent=root_agent)
        logger.info("ADKBudgetAgent initialized with google-adk patterns (5-days course)")

    async def process(self, query: str, user_id: str = "default") -> str:
        """
        Process user query through multi-agent system.

        Args:
            query: User's message
            user_id: User identifier (currently defaults to "default")

        Returns:
            Agent's response
        """
        try:
            logger.info(f"ADK processing query for user {user_id}: {query[:50]}...")

            # Run through ADK runner - returns list of events
            events = await self.runner.run_debug(query)

            # Extract text from events
            response_text = ""
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text

            if response_text:
                logger.info(f"ADK response: {response_text[:100]}...")
                return response_text
            else:
                logger.warning("No text in ADK response")
                return "Извините, не смог обработать запрос."

        except Exception as e:
            # Check if it's a quota/rate limit error (429)
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
                logger.error(
                    "🚨 GEMINI API QUOTA EXCEEDED! "
                    f"Model quota exhausted. Error: {e}",
                    exc_info=True
                )
                return "Извините, превышен лимит запросов к AI. Попробуйте позже."

            logger.error(f"Error in ADK agent: {e}", exc_info=True)
            return f"Произошла ошибка: {str(e)}"
