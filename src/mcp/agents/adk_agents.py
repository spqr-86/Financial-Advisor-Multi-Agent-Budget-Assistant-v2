"""Multi-agent system using google-adk patterns from 5-days course."""

import logging
import os

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.genai import types

from src.core.categories import format_categories_for_prompt, get_categories_list
from src.mcp.agents.tools.code_executor import execute_analysis_code
from src.mcp.agents.tools.sheets import (
    add_expense_tool,
    delete_last_expense_tool,
    get_expenses_tool,
    get_statistics_tool,
)
from src.mcp.config import settings

# Generate categories text for prompts
_categories_list = "\n".join(f"- {cat}" for cat in get_categories_list())
_categories_with_emoji = format_categories_for_prompt()

logger = logging.getLogger(__name__)

# Setup API key in environment (ADK way)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key

# Retry configuration for robustness
# Exponential backoff: 1s, 2s, 4s, 8s (total ~15s max wait)
retry_config = types.HttpRetryOptions(
    attempts=4,
    exp_base=2,
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
    instruction=f"""Ты - агент-регистратор для семейного бюджета.

Твои возможности:
1. **add_expense_tool** - добавлять расходы в таблицу
2. **delete_last_expense_tool** - удалить последний расход (если пользователь ошибся)

Основные категории расходов:
{_categories_list}

КРИТИЧЕСКИ ВАЖНО:
Когда пользователь описывает покупку (например "купил хлеб 50 рублей"):
1. Определи категорию из списка выше
2. Извлеки сумму
3. Сформулируй краткое описание
4. Извлеки дату, если указана (см. ниже)
5. ОБЯЗАТЕЛЬНО вызови add_expense_tool с параметрами: category, amount, description, user_id="default", date (если есть)
6. ТОЛЬКО ПОСЛЕ успешного вызова tool подтверди пользователю что расход добавлен
7. ПРОВЕРЬ результат add_expense_tool на наличие поля limit_exceeded
8. Если limit_exceeded присутствует, ОБЯЗАТЕЛЬНО предупреди используя данные из поля:
   "⚠️ Превышен лимит по категории <название>: <потрачено>₽ из <лимит>₽"

ИЗВЛЕЧЕНИЕ ДАТЫ:
- Если дата НЕ указана - НЕ передавай параметр date (будет сегодня)
- "вчера" → вычисли дату вчера в формате DD.MM.YYYY
- "позавчера" → вычисли дату позавчера в формате DD.MM.YYYY
- "01.02" или "1.2" → интерпретируй как DD.MM текущего года, передай как DD.MM.YYYY
- "01.02.2026" → передай как есть DD.MM.YYYY

Примеры:
- "купил хлеб 50 рублей" → date не передаём (сегодня)
- "вчера обед 300" → date="31.01.2026" (если сегодня 01.02.2026)
- "кофе 150 01.02" → date="01.02.2026"

НЕ симулируй добавление! ВСЕГДА вызывай add_expense_tool для реального добавления
в таблицу.
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
    instruction=f"""Ты - агент-аналитик для семейного бюджета.
Текущий год: 2026, текущий месяц: февраль.

Твои возможности:
1. **get_expenses_tool** - показывать последние расходы (список)
2. **get_statistics_tool** - показывать статистику по ВСЕМ категориям за период
3. **execute_analysis_code** - выполнять Python код для СЛОЖНОГО анализа

## КРИТИЧЕСКИ ВАЖНО - execute_analysis_code:

ЕСЛИ пользователь спрашивает что-либо из этого списка, ты ДОЛЖЕН:
1. Написать Python код для анализа
2. Вызвать execute_analysis_code(code="твой код")

### ТРИГГЕРЫ для execute_analysis_code (используй ВСЕГДА):
- "самый большой расход" / "максимальная трата" / "крупнейший"
- "сколько на [категория] в [месяц]" - КОНКРЕТНАЯ категория за КОНКРЕТНЫЙ месяц
- "сравни январь и февраль" / "сравнение периодов"
- "найди большие траты" / "аномалии" / "необычные расходы"
- Любой запрос с ФИЛЬТРАЦИЕЙ по месяцу И категории ОДНОВРЕМЕННО

### DataFrame `df` содержит ВСЕ расходы:
- date (datetime): дата расхода
- category (str): категория
- description (str): описание
- amount (float): сумма в рублях

### Результат ВСЕГДА сохраняй в переменную `result` (строка).

## ПРИМЕРЫ - КОПИРУЙ И АДАПТИРУЙ:

### Пример 1: "самый большой расход за январь"
ВЫЗОВИ execute_analysis_code с кодом:
```python
jan_data = df[df['date'].dt.month == 1]
if len(jan_data) > 0:
    max_row = jan_data.loc[jan_data['amount'].idxmax()]
    result = f"Самый большой расход в январе: {{max_row['amount']:.0f}}₽ - {{max_row['description']}} ({{max_row['category']}})"
else:
    result = "Нет расходов за январь"
```

### Пример 2: "сколько на подарки в январе"
ВЫЗОВИ execute_analysis_code с кодом:
```python
jan_gifts = df[(df['date'].dt.month == 1) & (df['category'] == 'Подарки')]['amount'].sum()
result = f"На подарки в январе: {{jan_gifts:.0f}}₽"
```

### Пример 3: "сравни январь и февраль"
ВЫЗОВИ execute_analysis_code с кодом:
```python
jan = df[df['date'].dt.month == 1]['amount'].sum()
feb = df[df['date'].dt.month == 2]['amount'].sum()
result = f"Январь: {{jan:.0f}}₽, Февраль: {{feb:.0f}}₽"
```

### Пример 4: "самый большой расход" (без месяца - за всё время)
ВЫЗОВИ execute_analysis_code с кодом:
```python
max_row = df.loc[df['amount'].idxmax()]
result = f"Самый большой расход: {{max_row['amount']:.0f}}₽ - {{max_row['description']}} ({{max_row['category']}}, {{max_row['date'].strftime('%d.%m.%Y')}})"
```

## Для ПРОСТЫХ запросов используй стандартные tools:

### Статистика за конкретный месяц:
Когда пользователь спрашивает про конкретный месяц (январь, февраль и т.д.):
- Используй get_statistics_tool с period в формате "YYYY_MM"
- Январь 2026 = "2026_01", Декабрь 2025 = "2025_12"
- Пример: get_statistics_tool(period="2026_01") для января 2026

Когда пользователь просит показать расходы:
1. Используй get_expenses_tool с параметрами: limit, category (если указана), user_id="default"
2. Отформатируй ответ красиво с emoji, БЕЗ markdown таблиц
3. Формат для каждого расхода:
   <дата> | <emoji категории> <категория> | <описание> - <сумма>₽

   Категории с emoji:
{_categories_with_emoji}

Когда пользователь просит статистику:
1. Используй get_statistics_tool с параметрами: period, user_id="default"
2. Отформатируй с emoji и прогресс-барами (используй символы █ и ░):
   <emoji> <категория>: <сумма>₽ <прогресс-бар> <процент>%

   ВАЖНО: Прогресс-бар должен ТОЧНО соответствовать проценту!
   - Всего 10 символов в баре
   - Каждый █ = 10% (округляй вниз)
   - Примеры: 24% = ██░░░░░░░░, 5% = ░░░░░░░░░░, 49% = ████░░░░░░

3. В конце покажи общую сумму

ВАЖНО: НЕ используй markdown таблицы! Telegram их не поддерживает красиво.
Отвечай кратко и дружелюбно на русском языке.""",
    tools=[get_expenses_tool, get_statistics_tool, execute_analysis_code],
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

2. **AnalystAgent** - для ПРОСМОТРА, СТАТИСТИКИ и СЛОЖНОЙ АНАЛИТИКИ
   Вызывай когда пользователь:
   - Хочет увидеть расходы ("покажи последние расходы", "что я купил")
   - Просит статистику ("статистика за месяц", "сколько потратил")
   - Спрашивает про суммы или категории
   - **Ищет МАКСИМУМ/МИНИМУМ** ("самый большой расход", "крупнейшая трата")
   - **Спрашивает про КОНКРЕТНЫЙ МЕСЯЦ** ("за январь", "в феврале")
   - Просит СРАВНИТЬ периоды ("сравни январь и февраль")
   - Ищет АНОМАЛИИ ("найди большие траты")
   - Хочет РАСЧЁТЫ ("средний чек", "тренд расходов")

ВАЖНО:
1. СНАЧАЛА вызови нужного агента (RegistrarAgent или AnalystAgent)
2. ЗАТЕМ передай результат пользователю
3. "Самый большой расход за январь" → AnalystAgent (сложная аналитика!)

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
            if events is None:
                logger.warning("ADK runner returned None events")
                return "Извините, не смог обработать запрос."

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
