# 🚀 План перестройки: Multi-Agent Budget Assistant v2.0

**Цель:** Создать проект с нуля, используя лучшие практики, чистую историю коммитов и непрерывный деплой.

**Принципы:**
- 🎯 Каждый коммит = работающий деплой
- ✅ Тестирование после каждой итерации
- 📝 Понятные коммит-сообщения (Conventional Commits)
- 🔒 Безопасность с первого дня
- 🏗️ Инкрементальная архитектура

---

## 📋 Структура итераций

| Итерация | Название | Время | Результат |
|----------|----------|-------|-----------|
| 0 | Инициализация | 15 мин | Пустой проект с CI/CD |
| 1 | Минимальный бот | 30 мин | Бот отвечает "Hello" |
| 2 | API сервер | 30 мин | FastAPI + health check |
| 3 | Интеграция бот ↔ API | 20 мин | Бот вызывает API |
| 4 | Google Sheets | 45 мин | Storage layer |
| 5 | MCP сервер | 45 мин | Standalone MCP с tools |
| 6 | AI Agent (базовый) | 45 мин | Один агент + MCP tools |
| 7 | Multi-Agent System | 60 мин | Orchestrator + 3 агента |
| 8 | Полировка | 30 мин | Rate limiting, timeouts |

**Общее время:** ~6 часов

---

## Итерация 0: Инициализация проекта

### 0.1 Создание репозитория

```bash
# Создать новую директорию
mkdir budget-assistant-v2
cd budget-assistant-v2

# Инициализация git
git init
git branch -M main
```

### 0.2 Структура проекта

```
budget-assistant-v2/
├── src/
│   ├── bot/                 # Telegram bot
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── handlers/
│   │   └── middlewares/
│   ├── api/                 # FastAPI server
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── routes/
│   ├── agents/              # AI agents
│   │   ├── __init__.py
│   │   ├── system.py
│   │   └── tools/
│   ├── storage/             # Data layer
│   │   ├── __init__.py
│   │   ├── interface.py
│   │   └── sheets.py
│   └── core/                # Shared utilities
│       ├── __init__.py
│       ├── config.py
│       └── logging.py
├── prompts/
│   └── agents/
├── docker/
│   ├── Dockerfile.bot
│   └── Dockerfile.api
├── scripts/
│   ├── deploy_api.sh
│   └── deploy_bot.sh
├── tests/
├── .env.example
├── .gitignore
├── .dockerignore
├── pyproject.toml
└── README.md
```

### 0.3 Базовые файлы

**`.gitignore`:**
```gitignore
# Python
__pycache__/
*.py[cod]
venv/
.venv/
*.egg-info/

# Environment
.env
.env.local

# Credentials (NEVER commit!)
credentials.json
*.pem
*.key

# IDE
.vscode/
.idea/

# Logs & DB
*.log
*.db
*.sqlite

# OS
.DS_Store
```

**`.env.example`:**
```bash
# === REQUIRED ===
TELEGRAM_BOT_TOKEN=your-bot-token
GOOGLE_API_KEY=your-gemini-api-key

# === GOOGLE CLOUD ===
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# === GOOGLE SHEETS ===
SPREADSHEET_NAME=Бюджет
# credentials.json должен быть в корне проекта

# === OPTIONAL ===
TELEGRAM_ADMIN_IDS=123456789,987654321
WEBHOOK_SECRET=random-secret-string
LOG_LEVEL=INFO
```

**`pyproject.toml`:**
```toml
[project]
name = "budget-assistant"
version = "2.0.0"
description = "Multi-Agent Budget Assistant with Telegram Bot"
requires-python = ">=3.11"

dependencies = [
    # Telegram Bot
    "aiogram>=3.4.0",
    "aiohttp>=3.9.0",

    # API Server
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",

    # AI Agents
    "google-adk>=0.1.0",
    "google-generativeai>=0.3.0",

    # Google Sheets
    "gspread>=5.12.0",
    "google-auth>=2.25.0",

    # Utilities
    "python-dotenv>=1.0.0",
    "python-dateutil>=2.8.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
]
```

### 0.4 Первый коммит

```bash
git add .
git commit -m "chore: initialize project structure

- Add project skeleton with src/, docker/, scripts/
- Add .gitignore, .env.example, pyproject.toml
- Set up for Google Cloud Run deployment"
```

---

## Итерация 1: Минимальный Telegram бот

### 1.1 Конфигурация

**`src/core/config.py`:**
```python
"""Centralized configuration with Pydantic validation."""

from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings with validation."""

    # Telegram
    telegram_bot_token: str
    telegram_admin_ids: List[int] = []
    webhook_secret: Optional[str] = None

    # API
    budget_api_url: Optional[str] = None

    # Gemini
    google_api_key: str = ""

    # Google Sheets
    spreadsheet_name: str = "Бюджет"
    google_sheets_credentials: str = "credentials.json"

    # Runtime
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
```

### 1.2 Минимальный бот

**`src/bot/app.py`:**
```python
"""Telegram Bot - Webhook mode for Cloud Run."""

import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from src.core.config import settings
from src.bot.handlers import router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def create_app() -> web.Application:
    """Create aiohttp application with bot webhook."""

    # Initialize bot
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)

    # Create web app
    app = web.Application()

    # Health check
    async def health(request):
        return web.json_response({"status": "healthy"})

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    # Setup webhook
    webhook_path = "/webhook"
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret
    ).register(app, path=webhook_path)

    setup_application(app, dp, bot=bot)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8080)
```

**`src/bot/handlers/__init__.py`:**
```python
"""Bot handlers."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router(name="main")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я Budget Assistant v2.0 🚀"
    )
```

### 1.3 Dockerfile

**`docker/Dockerfile.bot`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source
COPY src/ ./src/

# Environment
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["python", "-m", "src.bot.app"]
```

### 1.4 Deploy script

**`scripts/deploy_bot.sh`:**
```bash
#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="budget-bot"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🤖 Deploying Telegram Bot..."

# Build & push
docker build -f docker/Dockerfile.bot -t ${IMAGE} .
docker push ${IMAGE}

# Deploy
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --set-env-vars "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}"

# Get URL and set webhook
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)')

curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${SERVICE_URL}/webhook"

echo "✅ Bot deployed: ${SERVICE_URL}"
```

### 1.5 Тестирование

```bash
# Локально
export TELEGRAM_BOT_TOKEN="your-token"
python -m src.bot.app

# В другом терминале - симуляция webhook
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"update_id": 1, "message": {"message_id": 1, "chat": {"id": 123, "type": "private"}, "from": {"id": 123, "first_name": "Test"}, "text": "/start"}}'
```

### 1.6 Коммит

```bash
git add .
git commit -m "feat(bot): add minimal Telegram bot with webhook

- Add aiogram 3.x bot with /start handler
- Add health check endpoint
- Add Dockerfile and deploy script
- Ready for Cloud Run deployment"
```

### 1.7 Деплой и проверка

```bash
chmod +x scripts/deploy_bot.sh
./scripts/deploy_bot.sh

# Проверить в Telegram: /start
```

---

## Итерация 2: API сервер

### 2.1 FastAPI приложение

**`src/api/app.py`:**
```python
"""FastAPI server for Budget Assistant."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.api.routes import router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Budget Assistant API",
    version="2.0.0"
)

# CORS - restrict in production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)


@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**`src/api/routes/__init__.py`:**
```python
"""API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api")


class QueryRequest(BaseModel):
    query: str
    user_id: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    response: str
    user_id: str
    session_id: str


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query (placeholder)."""

    # TODO: Add agent processing in Iteration 5
    return QueryResponse(
        response=f"Echo: {request.query}",
        user_id=request.user_id,
        session_id=request.session_id or request.user_id
    )
```

### 2.2 Dockerfile

**`docker/Dockerfile.api`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source and credentials
COPY src/ ./src/
COPY prompts/ ./prompts/
COPY credentials.json ./credentials.json

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["python", "-m", "src.api.app"]
```

### 2.3 Deploy script

**`scripts/deploy_api.sh`:**
```bash
#!/bin/bash
set -e

PROJECT_ID="${GCP_PROJECT_ID:?Error: GCP_PROJECT_ID not set}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="budget-api"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying API Server..."

docker build -f docker/Dockerfile.api -t ${IMAGE} .
docker push ${IMAGE}

gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --timeout 300 \
    --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY},SPREADSHEET_NAME=${SPREADSHEET_NAME:-Бюджет}"

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region ${REGION} --format 'value(status.url)')

echo "✅ API deployed: ${SERVICE_URL}"
echo "   Test: curl ${SERVICE_URL}/health"
```

### 2.4 Тестирование

```bash
# Локально
python -m src.api.app

# Тест
curl -X POST http://localhost:8080/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "user_id": "123"}'
```

### 2.5 Коммит

```bash
git add .
git commit -m "feat(api): add FastAPI server with /api/query endpoint

- Add FastAPI app with health check
- Add query endpoint (placeholder for agents)
- Add Dockerfile and deploy script
- Restrict CORS in production mode"
```

---

## Итерация 3: Интеграция Бот ↔ API

### 3.1 HTTP клиент

**`src/bot/api_client.py`:**
```python
"""HTTP client for Budget API."""

import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)


class BudgetAPIClient:
    """Async HTTP client for Budget API."""

    def __init__(self, api_url: str, timeout: int = 30):
        self.api_url = api_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def query(self, text: str, user_id: str) -> str:
        """Send query to API and return response."""
        session = await self._get_session()

        try:
            async with session.post(
                f"{self.api_url}/api/query",
                json={"query": text, "user_id": user_id}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "")
                else:
                    logger.error(f"API error: {resp.status}")
                    return "❌ Ошибка сервера"

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error: {e}")
            return "❌ Сервер недоступен"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "❌ Произошла ошибка"
```

### 3.2 Middleware для инъекции клиента

**`src/bot/middlewares/api.py`:**
```python
"""API client middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

from src.core.config import settings
from src.bot.api_client import BudgetAPIClient


class APIClientMiddleware(BaseMiddleware):
    """Inject API client into handlers."""

    def __init__(self):
        self._client: BudgetAPIClient | None = None

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Lazy init
        if self._client is None and settings.budget_api_url:
            self._client = BudgetAPIClient(settings.budget_api_url)

        data["api_client"] = self._client
        data["user_id"] = str(event.from_user.id)

        return await handler(event, data)
```

### 3.3 Обновление handlers

**`src/bot/handlers/__init__.py`:**
```python
"""Bot handlers with API integration."""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from src.bot.api_client import BudgetAPIClient

router = Router(name="main")


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я Budget Assistant v2.0 🚀\n\n"
        "Напиши что-нибудь, и я обработаю!"
    )


@router.message(F.text)
async def handle_text(
    message: Message,
    api_client: BudgetAPIClient | None,
    user_id: str
):
    """Handle all text messages."""
    if not api_client:
        await message.answer("⚠️ API не настроен")
        return

    # Show typing
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Call API
    response = await api_client.query(message.text, user_id)

    await message.answer(response)
```

### 3.4 Регистрация middleware

Обновить `src/bot/app.py`:
```python
from src.bot.middlewares.api import APIClientMiddleware

# После создания dp:
dp.message.middleware(APIClientMiddleware())
```

### 3.5 Коммит

```bash
git add .
git commit -m "feat(bot): integrate bot with API server

- Add BudgetAPIClient with timeout handling
- Add APIClientMiddleware for dependency injection
- Handle all text messages through API
- Add graceful error handling"
```

### 3.6 Деплой и проверка

```bash
# Деплой API
./scripts/deploy_api.sh

# Получить URL API
export BUDGET_API_URL=$(gcloud run services describe budget-api \
    --region us-central1 --format 'value(status.url)')

# Деплой бота с API URL
./scripts/deploy_bot.sh

# Проверить: отправить сообщение боту
```

---

## Итерация 4: Google Sheets интеграция

### 4.1 Абстракция хранилища

**`src/storage/interface.py`:**
```python
"""Storage interface for expenses."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class StorageInterface(ABC):
    """Abstract interface for expense storage."""

    @abstractmethod
    async def add_expense(
        self,
        category: str,
        amount: float,
        description: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Add expense."""
        pass

    @abstractmethod
    async def get_expenses(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get expenses with filters."""
        pass

    @abstractmethod
    async def get_statistics(
        self,
        period: str = "month"
    ) -> Dict[str, Any]:
        """Get spending statistics."""
        pass
```

### 4.2 Google Sheets реализация

**`src/storage/sheets.py`:**
```python
"""Google Sheets storage implementation."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

import gspread
from google.oauth2.service_account import Credentials

from src.storage.interface import StorageInterface
from src.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


class GoogleSheetsStorage(StorageInterface):
    """Google Sheets implementation."""

    def __init__(self):
        self.spreadsheet_name = settings.spreadsheet_name
        self.credentials_path = settings.google_sheets_credentials
        self._client = None
        self._worksheet = None

    async def _connect(self):
        """Lazy connection to Google Sheets."""
        if self._worksheet is not None:
            return

        creds = Credentials.from_service_account_file(
            self.credentials_path, scopes=SCOPES
        )
        self._client = gspread.authorize(creds)

        try:
            spreadsheet = self._client.open(self.spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            spreadsheet = self._client.create(self.spreadsheet_name)
            logger.info(f"Created spreadsheet: {self.spreadsheet_name}")

        try:
            self._worksheet = spreadsheet.worksheet("Расходы")
        except gspread.WorksheetNotFound:
            self._worksheet = spreadsheet.add_worksheet("Расходы", 1000, 4)
            self._worksheet.append_row(["Дата", "Категория", "Описание", "Сумма"])
            logger.info("Created worksheet: Расходы")

    async def add_expense(
        self,
        category: str,
        amount: float,
        description: str,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        await self._connect()

        date_str = (date or datetime.now()).strftime("%d.%m.%Y")

        self._worksheet.append_row([date_str, category, description, amount])

        logger.info(f"Added expense: {amount}₽ on {category}")

        return {
            "status": "success",
            "data": {
                "date": date_str,
                "category": category,
                "amount": amount,
                "description": description
            }
        }

    async def get_expenses(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        await self._connect()

        records = self._worksheet.get_all_records()

        # Filter (simplified)
        filtered = records[-limit:] if len(records) > limit else records

        total = sum(float(r.get("Сумма", 0)) for r in filtered)

        return {
            "status": "success",
            "data": {
                "expenses": filtered,
                "count": len(filtered),
                "total": total
            }
        }

    async def get_statistics(self, period: str = "month") -> Dict[str, Any]:
        await self._connect()

        records = self._worksheet.get_all_records()

        # Group by category
        by_category = {}
        for r in records:
            cat = r.get("Категория", "прочее")
            amt = float(r.get("Сумма", 0))
            by_category[cat] = by_category.get(cat, 0) + amt

        total = sum(by_category.values())

        return {
            "status": "success",
            "data": {
                "total": total,
                "by_category": by_category,
                "period": period
            }
        }
```

### 4.3 Тестовый endpoint

Добавить в `src/api/routes/__init__.py`:
```python
from src.storage.sheets import GoogleSheetsStorage

storage = GoogleSheetsStorage()


@router.post("/test/add-expense")
async def test_add_expense():
    """Test adding expense."""
    result = await storage.add_expense(
        category="тест",
        amount=100,
        description="Тестовый расход"
    )
    return result


@router.get("/test/expenses")
async def test_get_expenses():
    """Test getting expenses."""
    return await storage.get_expenses(limit=10)
```

### 4.4 Коммит

```bash
git add .
git commit -m "feat(storage): add Google Sheets integration

- Add StorageInterface abstraction
- Implement GoogleSheetsStorage
- Auto-create spreadsheet if not exists
- Add test endpoints for verification"
```

### 4.5 Деплой и тестирование

```bash
./scripts/deploy_api.sh

# Тест
curl -X POST "$BUDGET_API_URL/test/add-expense"
curl "$BUDGET_API_URL/test/expenses"

# Проверить Google Sheets - должна появиться запись
```

---

## Итерация 5: Базовый AI Agent

### 5.1 Tools для агента

**`src/agents/tools.py`:**
```python
"""Tools for AI agents."""

from typing import Dict, Any
from google.adk.tools.tool_context import ToolContext

from src.storage.sheets import GoogleSheetsStorage

storage = GoogleSheetsStorage()


async def add_expense(
    tool_context: ToolContext,
    category: str,
    amount: float,
    description: str,
    date: str = None
) -> Dict[str, Any]:
    """
    Add expense to budget.

    Args:
        category: Category (продукты, транспорт, рестораны, etc.)
        amount: Amount in rubles
        description: What was purchased
        date: Date (optional, defaults to today)
    """
    result = await storage.add_expense(
        category=category,
        amount=amount,
        description=description
    )
    return result


async def get_expenses(
    tool_context: ToolContext,
    limit: int = 10
) -> Dict[str, Any]:
    """Get recent expenses."""
    return await storage.get_expenses(limit=limit)


async def get_statistics(
    tool_context: ToolContext,
    period: str = "month"
) -> Dict[str, Any]:
    """Get spending statistics."""
    return await storage.get_statistics(period=period)


BUDGET_TOOLS = [add_expense, get_expenses, get_statistics]
```

### 5.2 Simple Agent

**`src/agents/simple.py`:**
```python
"""Simple single-agent implementation."""

import logging
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App

from src.agents.tools import BUDGET_TOOLS

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Ты - финансовый ассистент для семейного бюджета.

Твои возможности:
1. Добавлять расходы (add_expense)
2. Показывать последние расходы (get_expenses)
3. Показывать статистику (get_statistics)

Категории расходов: продукты, транспорт, рестораны, развлечения, ЖКХ, одежда, здоровье, прочее.

Когда пользователь пишет о покупке - извлеки категорию, сумму и описание, затем вызови add_expense.
После успешного добавления - подтверди пользователю.

Отвечай кратко и дружелюбно на русском языке.
"""


class SimpleBudgetAgent:
    """Simple budget agent with tools."""

    def __init__(self):
        self.session_service = InMemorySessionService()

        self.agent = LlmAgent(
            name="BudgetAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=SYSTEM_PROMPT,
            tools=BUDGET_TOOLS
        )

        self.app = App(name="budget_assistant", root_agent=self.agent)
        self.runner = Runner(app=self.app, session_service=self.session_service)

        logger.info("✅ SimpleBudgetAgent initialized")

    async def process(self, query: str, user_id: str) -> str:
        """Process user query."""
        session_id = user_id

        # Create session if needed
        try:
            await self.session_service.create_session(
                app_name="budget_assistant",
                user_id=user_id,
                session_id=session_id
            )
        except:
            pass  # Session exists

        # Run agent
        content = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        response = ""
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response += part.text

        return response or "Не удалось обработать запрос"
```

### 5.3 Интеграция в API

Обновить `src/api/routes/__init__.py`:
```python
from src.agents.simple import SimpleBudgetAgent

# Singleton
_agent: SimpleBudgetAgent | None = None


async def get_agent() -> SimpleBudgetAgent:
    global _agent
    if _agent is None:
        _agent = SimpleBudgetAgent()
    return _agent


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query through AI agent."""
    agent = await get_agent()

    response = await agent.process(
        query=request.query,
        user_id=request.user_id
    )

    return QueryResponse(
        response=response,
        user_id=request.user_id,
        session_id=request.session_id or request.user_id
    )
```

### 5.4 Коммит

```bash
git add .
git commit -m "feat(agents): add simple AI agent with budget tools

- Add budget tools (add_expense, get_expenses, get_statistics)
- Implement SimpleBudgetAgent with Gemini 2.0
- Integrate agent into /api/query endpoint
- Add system prompt for expense parsing"
```

### 5.5 Деплой и тестирование

```bash
./scripts/deploy_api.sh

# Тест через curl
curl -X POST "$BUDGET_API_URL/api/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "купил хлеб за 50 рублей", "user_id": "test"}'

# Тест через бота
# Отправить: "купил продукты на 1200"
```

---

## Итерация 6: Multi-Agent System

### 6.1 Промпты агентов

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

### 6.2 Multi-Agent System

**`src/agents/system.py`:**
```python
"""Multi-agent budget system."""

import logging
from pathlib import Path
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.apps.app import App
from google.adk.tools import AgentTool

from src.agents.tools import BUDGET_TOOLS

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "agents"


def load_prompt(name: str) -> str:
    """Load prompt from file."""
    path = PROMPTS_DIR / f"{name}.txt"
    if path.exists():
        return path.read_text()
    return f"You are {name}."


class BudgetAssistantSystem:
    """Multi-agent budget assistant."""

    def __init__(self):
        self.session_service = InMemorySessionService()

        # Create specialized agents
        self.registrar = LlmAgent(
            name="RegistrarAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("registrar"),
            tools=BUDGET_TOOLS
        )

        self.analyst = LlmAgent(
            name="AnalystAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("analyst"),
            tools=BUDGET_TOOLS
        )

        self.advisor = LlmAgent(
            name="AdvisorAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("advisor"),
            tools=BUDGET_TOOLS
        )

        # Orchestrator
        self.orchestrator = LlmAgent(
            name="OrchestratorAgent",
            model=Gemini(model="gemini-2.0-flash"),
            instruction=load_prompt("orchestrator"),
            tools=[
                AgentTool(agent=self.registrar),
                AgentTool(agent=self.analyst),
                AgentTool(agent=self.advisor),
            ]
        )

        self.app = App(name="budget_assistant", root_agent=self.orchestrator)
        self.runner = Runner(app=self.app, session_service=self.session_service)

        logger.info("✅ BudgetAssistantSystem initialized")

    async def process(self, query: str, user_id: str) -> str:
        """Process query through multi-agent system."""
        try:
            await self.session_service.create_session(
                app_name="budget_assistant",
                user_id=user_id,
                session_id=user_id
            )
        except:
            pass

        content = types.Content(
            role="user",
            parts=[types.Part(text=query)]
        )

        response = ""
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=user_id,
            new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text and part.text.strip():
                        response += part.text

        return response or "Не удалось обработать запрос"
```

### 6.3 Коммит

```bash
git add .
git commit -m "feat(agents): implement multi-agent system

- Add Orchestrator, Registrar, Analyst, Advisor agents
- Use AgentTool for agent-to-agent communication
- Load prompts from files
- Replace simple agent with multi-agent system"
```

---

## Итерация 7: Полировка и безопасность

### 7.1 Rate Limiting

**`src/bot/middlewares/rate_limit.py`:**
```python
"""Rate limiting middleware."""

from collections import defaultdict
from datetime import datetime, timedelta
from aiogram import BaseMiddleware
from aiogram.types import Message


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 10, window: int = 60):
        self.limit = limit
        self.window = timedelta(seconds=window)
        self.requests: dict[int, list] = defaultdict(list)

    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        now = datetime.now()

        # Clean old
        self.requests[user_id] = [
            t for t in self.requests[user_id]
            if now - t < self.window
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.limit:
            await event.answer("⏳ Подождите минуту...")
            return

        self.requests[user_id].append(now)
        return await handler(event, data)
```

### 7.2 Access Control

**`src/bot/middlewares/access.py`:**
```python
"""Access control middleware."""

from aiogram import BaseMiddleware
from aiogram.types import Message
from src.core.config import settings


class AccessControlMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if settings.telegram_admin_ids:
            if event.from_user.id not in settings.telegram_admin_ids:
                await event.answer("🔒 Доступ ограничен")
                return

        return await handler(event, data)
```

### 7.3 Timeout wrapper

**`src/bot/utils.py`:**
```python
"""Bot utilities."""

import asyncio


async def with_timeout(coro, timeout: int = 30, fallback: str = "⏱️ Таймаут"):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return fallback


def split_message(text: str, max_len: int = 4000) -> list[str]:
    """Split long message for Telegram."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Find last newline before limit
        split_at = text.rfind('\n', 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    return chunks
```

### 7.4 Финальный коммит

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

## 📊 Чеклист готовности

### После каждой итерации:

- [ ] Код компилируется без ошибок
- [ ] Локальный тест проходит
- [ ] Docker image собирается
- [ ] Деплой на Cloud Run успешен
- [ ] Функционал работает в Telegram
- [ ] Коммит сделан с понятным сообщением

### Финальная проверка:

- [ ] `/start` работает
- [ ] Добавление расхода работает ("купил хлеб 100")
- [ ] Статистика работает ("покажи статистику")
- [ ] Советы работают ("дай совет")
- [ ] Rate limit работает
- [ ] Длинные ответы не ломают бота
- [ ] Credentials не в git
- [ ] Логи читаемые

---

## 🔗 Полезные команды

```bash
# Логи бота
gcloud run services logs read budget-bot --region us-central1 --limit 50

# Логи API
gcloud run services logs read budget-api --region us-central1 --limit 50

# Статус сервисов
gcloud run services list

# Удалить сервис
gcloud run services delete budget-bot --region us-central1

# Локальный запуск
python -m src.bot.app
python -m src.api.app
```

---

**Автор:** Claude Code
**Дата:** 2025-12-06
