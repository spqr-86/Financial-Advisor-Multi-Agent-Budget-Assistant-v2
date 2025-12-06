# Budget Assistant v2.0 — План разработки

## Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Telegram  │────▶│     API     │────▶│     MCP     │
│     Bot     │     │   Gateway   │     │   Service   │
│   :8080     │     │   :8081     │     │   :8082     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │  Google Sheets  │
                                     │   + AI Agents   │
                                     └─────────────────┘
```

### Принципы
- Каждый сервис = отдельный контейнер
- Каждый коммит = работающий деплой
- Конфигурация через переменные окружения
- Единые схемы данных в `src/core/schemas.py`
- Централизованная обработка ошибок

---

## Структура проекта

```
budget-assistant-v2/
├── src/
│   ├── __init__.py
│   ├── core/                    # Общие компоненты
│   │   ├── __init__.py
│   │   ├── config.py            # Базовые настройки
│   │   ├── schemas.py           # Pydantic модели
│   │   ├── exceptions.py        # Кастомные исключения
│   │   └── http_client.py       # HTTP клиент с retry
│   ├── bot/                     # Telegram бот
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── handlers/
│   │   │   └── __init__.py
│   │   └── middlewares/
│   │       └── __init__.py
│   ├── api/                     # API Gateway
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   └── routes/
│   │       └── __init__.py
│   └── mcp/                     # MCP Service (AI логика)
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── routes/
│       │   └── __init__.py
│       ├── agents/              # AI агенты
│       │   ├── __init__.py
│       │   ├── orchestrator.py
│       │   ├── registrar.py
│       │   ├── analyst.py
│       │   └── tools/
│       │       ├── __init__.py
│       │       └── sheets.py
│       └── storage/             # Хранилище данных
│           ├── __init__.py
│           ├── interface.py
│           └── sheets.py
├── prompts/
│   └── agents/
│       ├── orchestrator.txt
│       ├── registrar.txt
│       └── analyst.txt
├── docker/
│   ├── Dockerfile.bot
│   ├── Dockerfile.api
│   └── Dockerfile.mcp
├── scripts/
│   ├── deploy_bot.sh
│   ├── deploy_api.sh
│   └── deploy_mcp.sh
├── tests/
│   ├── conftest.py
│   ├── test_bot/
│   ├── test_api/
│   └── test_mcp/
├── .env.example
├── .gitignore
├── pyproject.toml
├── poetry.lock
└── README.md
```

---

## Итерации

### Итерация 0: Инициализация ✅
- [x] Структура проекта
- [x] pyproject.toml + Poetry
- [x] .gitignore, .env.example
- [x] Базовый конфиг

### Итерация 1: Telegram Bot ✅
- [x] Минимальный бот с /start
- [x] Webhook для Cloud Run
- [x] Health check endpoint
- [x] Dockerfile.bot

### Итерация 2: API Gateway ✅
- [x] FastAPI приложение
- [x] /api/query endpoint (placeholder)
- [x] Dockerfile.api

### Итерация 3: MCP Service ✅
- [x] FastAPI приложение
- [x] /mcp/query endpoint (placeholder)
- [x] Dockerfile.mcp

### Итерация 4: Интеграция сервисов ✅
- [x] HTTP клиент с retry логикой
- [x] Bot → API → MCP цепочка
- [x] Единые схемы данных
- [x] Exception handlers
- [x] Middleware для бота

---

### Итерация 5: Google Sheets

**Цель:** Добавить слой хранения данных.

#### 5.1 Storage Interface

**`src/mcp/storage/interface.py`:**
```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

class StorageInterface(ABC):
    """Абстрактный интерфейс хранилища."""

    @abstractmethod
    async def add_expense(
        self,
        category: str,
        amount: float,
        description: str,
        date: datetime | None = None,
    ) -> dict[str, Any]:
        """Добавить расход."""

    @abstractmethod
    async def get_expenses(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Получить расходы с фильтрами."""

    @abstractmethod
    async def get_statistics(
        self,
        period: str = "month",
    ) -> dict[str, Any]:
        """Получить статистику."""
```

#### 5.2 Google Sheets Implementation

**`src/mcp/storage/sheets.py`:**
```python
import gspread
from google.oauth2.service_account import Credentials

from src.mcp.config import settings
from src.mcp.storage.interface import StorageInterface

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

class GoogleSheetsStorage(StorageInterface):
    """Google Sheets реализация хранилища."""

    def __init__(self):
        self._client: gspread.Client | None = None
        self._worksheet: gspread.Worksheet | None = None

    async def _connect(self) -> None:
        if self._worksheet is not None:
            return

        creds = Credentials.from_service_account_file(
            settings.google_sheets_credentials,
            scopes=SCOPES,
        )
        self._client = gspread.authorize(creds)

        try:
            spreadsheet = self._client.open(settings.spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = self._client.create(settings.spreadsheet_name)

        try:
            self._worksheet = spreadsheet.worksheet("Расходы")
        except gspread.WorksheetNotFound:
            self._worksheet = spreadsheet.add_worksheet("Расходы", 1000, 4)
            self._worksheet.append_row(["Дата", "Категория", "Описание", "Сумма"])

    async def add_expense(self, category, amount, description, date=None):
        await self._connect()
        date_str = (date or datetime.now()).strftime("%d.%m.%Y")
        self._worksheet.append_row([date_str, category, description, amount])
        return {"status": "success", "amount": amount, "category": category}

    # ... остальные методы
```

#### 5.3 Test Endpoints

Добавить в `src/mcp/routes/__init__.py`:
```python
@router.post("/test/add-expense")
async def test_add_expense():
    storage = GoogleSheetsStorage()
    return await storage.add_expense("тест", 100, "Тестовый расход")
```

#### 5.4 Коммит
```bash
git add .
git commit -m "feat(storage): add Google Sheets integration

- Add StorageInterface abstraction
- Implement GoogleSheetsStorage
- Auto-create spreadsheet if not exists
- Add test endpoints"
```

---

### Итерация 6: AI Agent (базовый)

**Цель:** Добавить обработку запросов через AI агента.

#### 6.1 Зависимости

Раскомментировать в `pyproject.toml`:
```toml
google-adk = "^0.1.0"
google-generativeai = "^0.3.0"
```

И обновить версии:
```toml
fastapi = "^0.115.0"
uvicorn = "^0.34.0"
```

#### 6.2 Budget Tools

**`src/mcp/agents/tools/sheets.py`:**
```python
from google.adk.tools.tool_context import ToolContext
from src.mcp.storage.sheets import GoogleSheetsStorage

storage = GoogleSheetsStorage()

async def add_expense(
    tool_context: ToolContext,
    category: str,
    amount: float,
    description: str,
) -> dict:
    """
    Добавить расход в бюджет.

    Args:
        category: Категория (продукты, транспорт, рестораны, и т.д.)
        amount: Сумма в рублях
        description: Описание покупки
    """
    return await storage.add_expense(category, amount, description)

async def get_expenses(tool_context: ToolContext, limit: int = 10) -> dict:
    """Получить последние расходы."""
    return await storage.get_expenses(limit=limit)

async def get_statistics(tool_context: ToolContext, period: str = "month") -> dict:
    """Получить статистику расходов."""
    return await storage.get_statistics(period=period)

BUDGET_TOOLS = [add_expense, get_expenses, get_statistics]
```

#### 6.3 Simple Agent

**`src/mcp/agents/simple.py`:**
```python
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App

from src.mcp.agents.tools.sheets import BUDGET_TOOLS

SYSTEM_PROMPT = """Ты - финансовый ассистент для семейного бюджета.

Твои возможности:
1. Добавлять расходы (add_expense)
2. Показывать последние расходы (get_expenses)
3. Показывать статистику (get_statistics)

Категории расходов: продукты, транспорт, рестораны, развлечения, ЖКХ, одежда, здоровье, прочее.

Когда пользователь пишет о покупке - извлеки категорию, сумму и описание, затем вызови add_expense.

Отвечай кратко и дружелюбно на русском языке.
"""

class SimpleBudgetAgent:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.agent = LlmAgent(
            name="BudgetAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=SYSTEM_PROMPT,
            tools=BUDGET_TOOLS,
        )
        self.app = App(name="budget_assistant", root_agent=self.agent)
        self.runner = Runner(app=self.app, session_service=self.session_service)

    async def process(self, query: str, user_id: str) -> str:
        # Создать сессию если нужно
        try:
            await self.session_service.create_session(
                app_name="budget_assistant",
                user_id=user_id,
                session_id=user_id,
            )
        except:
            pass

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)],
        )

        response = ""
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=user_id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response += part.text

        return response or "Не удалось обработать запрос"
```

#### 6.4 Интеграция в MCP

Обновить `src/mcp/routes/__init__.py`:
```python
from src.mcp.agents.simple import SimpleBudgetAgent

_agent: SimpleBudgetAgent | None = None

def get_agent() -> SimpleBudgetAgent:
    global _agent
    if _agent is None:
        _agent = SimpleBudgetAgent()
    return _agent

@router.post("/query", response_model=QueryResponse)
async def process_mcp_query(request: QueryRequest) -> QueryResponse:
    agent = get_agent()
    response = await agent.process(request.query, request.user_id)
    return QueryResponse(
        response=response,
        user_id=request.user_id,
        session_id=request.session_id or request.user_id,
    )
```

#### 6.5 Коммит
```bash
git add .
git commit -m "feat(agents): add simple AI agent with budget tools

- Add budget tools (add_expense, get_expenses, get_statistics)
- Implement SimpleBudgetAgent with Gemini 2.0
- Integrate agent into /mcp/query endpoint"
```

---

### Итерация 7: Multi-Agent System

**Цель:** Разделить логику на специализированных агентов.

#### 7.1 Промпты агентов

**`prompts/agents/orchestrator.txt`:**
```
Ты - координатор финансовых ассистентов.

Делегируй задачи:
- RegistrarAgent: добавление расходов ("купил", "потратил", "заплатил")
- AnalystAgent: статистика и аналитика ("сколько", "покажи", "статистика")
- AdvisorAgent: советы ("совет", "рекомендация", "как сэкономить")

ВАЖНО: После получения ответа от агента - ОБЯЗАТЕЛЬНО передай его пользователю!
```

**`prompts/agents/registrar.txt`:**
```
Ты - специалист по добавлению расходов.

1. Извлеки из текста: категорию, сумму, описание
2. Вызови add_expense
3. Подтверди добавление пользователю

Категории: продукты, транспорт, рестораны, развлечения, ЖКХ, одежда, здоровье, прочее
```

**`prompts/agents/analyst.txt`:**
```
Ты - аналитик расходов.

Используй get_expenses и get_statistics для анализа.
Форматируй ответы с эмодзи и таблицами где уместно.
```

#### 7.2 Multi-Agent System

**`src/mcp/agents/orchestrator.py`:**
```python
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App

from src.mcp.agents.tools.sheets import BUDGET_TOOLS

PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts" / "agents"

def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text() if path.exists() else f"You are {name}."

class BudgetAssistantSystem:
    def __init__(self):
        self.session_service = InMemorySessionService()

        # Создаем специализированных агентов
        self.registrar = LlmAgent(
            name="RegistrarAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("registrar"),
            tools=BUDGET_TOOLS,
        )

        self.analyst = LlmAgent(
            name="AnalystAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("analyst"),
            tools=BUDGET_TOOLS,
        )

        self.advisor = LlmAgent(
            name="AdvisorAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("advisor"),
            tools=BUDGET_TOOLS,
        )

        # Оркестратор
        self.orchestrator = LlmAgent(
            name="OrchestratorAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("orchestrator"),
            tools=[
                AgentTool(agent=self.registrar),
                AgentTool(agent=self.analyst),
                AgentTool(agent=self.advisor),
            ],
        )

        self.app = App(name="budget_assistant", root_agent=self.orchestrator)
        self.runner = Runner(app=self.app, session_service=self.session_service)

    async def process(self, query: str, user_id: str) -> str:
        # ... аналогично SimpleBudgetAgent
```

#### 7.3 Коммит
```bash
git add .
git commit -m "feat(agents): implement multi-agent system

- Add Orchestrator, Registrar, Analyst, Advisor agents
- Use AgentTool for agent-to-agent communication
- Load prompts from files"
```

---

### Итерация 8: Полировка

**Цель:** Добавить production-ready фичи.

#### 8.1 Rate Limiting (уже готово)

Middleware в `src/bot/middlewares/__init__.py`.

#### 8.2 Access Control (уже готово)

Middleware в `src/bot/middlewares/__init__.py`.

#### 8.3 Timeout Wrapper

**`src/core/utils.py`:**
```python
import asyncio

async def with_timeout(coro, timeout: int = 30, fallback: str = "Таймаут"):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return fallback

def split_message(text: str, max_len: int = 4000) -> list[str]:
    """Разбить длинное сообщение для Telegram."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    return chunks
```

#### 8.4 Финальный коммит
```bash
git add .
git commit -m "feat: add rate limiting, access control, timeouts

- Add RateLimitMiddleware (10 req/min)
- Add AccessControlMiddleware for admin_ids
- Add timeout wrapper for API calls
- Add message splitting for long responses
- Project ready for production!"
```

---

## Команды разработки

```bash
# Установка зависимостей
poetry install

# Запуск сервисов локально
poetry run python -m src.bot.app    # Bot на :8080
poetry run python -m src.api.app    # API на :8081
poetry run python -m src.mcp.app    # MCP на :8082

# Тесты
poetry run pytest

# Линтер
poetry run ruff check src/
poetry run ruff format src/

# Docker build
docker build -f docker/Dockerfile.bot -t budget-bot .
docker build -f docker/Dockerfile.api -t budget-api .
docker build -f docker/Dockerfile.mcp -t budget-mcp .
```

---

## Переменные окружения

```bash
# === BOT ===
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ADMIN_IDS=123456789,987654321
WEBHOOK_SECRET=random-secret-string
BUDGET_API_URL=http://localhost:8081

# === API GATEWAY ===
MCP_API_URL=http://localhost:8082

# === MCP ===
GOOGLE_API_KEY=your-gemini-api-key
SPREADSHEET_NAME=Бюджет

# === COMMON ===
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

## Деплой на Cloud Run

```bash
# Деплой всех сервисов
./scripts/deploy_mcp.sh   # Сначала MCP
./scripts/deploy_api.sh   # Затем API (нужен URL MCP)
./scripts/deploy_bot.sh   # Последним Bot (нужен URL API)

# Проверка
gcloud run services list
gcloud run services logs read budget-bot --region us-central1 --limit 50
```

---

## Чеклист готовности

### После каждой итерации:
- [ ] Код проходит `ruff check`
- [ ] Локальный тест проходит
- [ ] Docker image собирается
- [ ] Сервисы общаются друг с другом

### Финальная проверка:
- [ ] `/start` работает
- [ ] Добавление расхода работает ("купил хлеб 100")
- [ ] Статистика работает ("покажи статистику")
- [ ] Rate limit работает
- [ ] Длинные ответы не ломают бота
- [ ] Credentials не в git
- [ ] Логи читаемые
