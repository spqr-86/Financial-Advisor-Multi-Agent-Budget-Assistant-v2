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
| 0 | Инициализация | 15 мин | Пустой проект с CI/CD для 3 сервисов |
| 1 | Минимальный бот | 30 мин | Бот отвечает "Hello" |
| 2 | API Gateway | 20 мин | Легковесный FastAPI прокси |
| 3 | MCP Сервис | 30 мин | FastAPI для AI-логики |
| 4 | Интеграция сервисов | 30 мин | Бот ↔ API ↔ MCP |
| 5 | Google Sheets в MCP | 45 мин | Storage layer в MCP |
| 6 | AI Agent в MCP | 45 мин | Один агент + MCP tools |
| 7 | Multi-Agent System | 60 мин | Orchestrator + 3 агента в MCP |
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
│   ├── api/                 # API Gateway
│   └── mcp/                 # MCP (Multi-Agent Control Plane) Service
│       ├── __init__.py
│       ├── app.py
│       ├── agents/
│       ├── storage/
│       └── routes/
│   └── core/                # Shared utilities
├── prompts/
│   └── agents/
├── docker/
│   ├── Dockerfile.bot
│   ├── Dockerfile.api
│   └── Dockerfile.mcp
├── scripts/
│   ├── deploy_api.sh
│   ├── deploy_bot.sh
│   └── deploy_mcp.sh
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

# === SERVICE URLS ===
# Используются ботом для вызова API Gateway
BUDGET_API_URL=http://localhost:8081 
# Используются API Gateway для вызова MCP
MCP_API_URL=http://localhost:8082

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

- Add project skeleton with 3 services: bot, api, mcp
- Add .gitignore, .env.example, pyproject.toml
- Set up for Google Cloud Run deployment"
```

---

## Итерация 1: Минимальный Telegram бот

(Содержимое этой итерации остается без изменений, так как бот не зависит от новой архитектуры на данном этапе)

### 1.1 Конфигурация, 1.2 Минимальный бот, 1.3 Dockerfile, 1.4 Deploy script...
(Все шаги из оригинального плана остаются здесь)

---

## Итерация 2: API Gateway

### 2.1 FastAPI приложение

**`src/api/app.py`:**
```python
"""FastAPI Gateway for Budget Assistant."""
from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(title="Budget Assistant API Gateway", version="2.0.0")
app.include_router(router)

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}
```

**`src/api/routes/__init__.py`:**
```python
"""API routes."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api")

class QueryRequest(BaseModel):
    query: str
    user_id: str

class QueryResponse(BaseModel):
    response: str

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query (placeholder, will proxy to MCP)."""
    # TODO: Proxy to MCP in Iteration 4
    return QueryResponse(response=f"API Echo: {request.query}")
```

### 2.2 Dockerfile

**`docker/Dockerfile.api`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/api/ ./src/api/
COPY src/core/ ./src/core/
ENV PYTHONUNBUFFERED=1
ENV PORT=8081
EXPOSE 8081
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8081"]
```

### 2.3 Deploy script

**`scripts/deploy_api.sh`:** (Скрипт будет похож на deploy_bot.sh, но с именем `budget-api` и портом 8081)

### 2.4 Коммит
```bash
git add .
git commit -m "feat(api): add minimal API gateway service"
```

---

## Итерация 3: MCP Сервис

### 3.1 FastAPI приложение

**`src/mcp/app.py`:**
```python
"""FastAPI MCP Service for Budget Assistant."""
from fastapi import FastAPI
from src.mcp.routes import router

app = FastAPI(title="Budget Assistant MCP", version="2.0.0")
app.include_router(router)

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp"}
```

**`src/mcp/routes/__init__.py`:**
```python
"""MCP routes."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/mcp")

class MCPQueryRequest(BaseModel):
    query: str
    user_id: str

class MCPQueryResponse(BaseModel):
    response: str

@router.post("/query", response_model=MCPQueryResponse)
async def process_mcp_query(request: MCPQueryRequest):
    """Process user query (placeholder for agent)."""
    # TODO: Add agent processing in Iteration 6
    return MCPQueryResponse(response=f"MCP Echo: {request.query}")
```

### 3.2 Dockerfile

**`docker/Dockerfile.mcp`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/mcp/ ./src/mcp/
COPY src/core/ ./src/core/
# Prompts и credentials понадобятся позже
# COPY prompts/ ./prompts/
# COPY credentials.json ./credentials.json
ENV PYTHONUNBUFFERED=1
ENV PORT=8082
EXPOSE 8082
CMD ["uvicorn", "src.mcp.app:app", "--host", "0.0.0.0", "--port", "8082"]
```

### 3.3 Deploy script

**`scripts/deploy_mcp.sh`:** (Новый скрипт для деплоя `budget-mcp` на порт 8082)

### 3.4 Коммит
```bash
git add .
git commit -m "feat(mcp): add minimal MCP service for AI logic"
```

---

## Итерация 4: Интеграция сервисов

### 4.1 HTTP клиент для MCP

**`src/api/mcp_client.py`:** (Аналогично `BudgetAPIClient` из старого плана, но для вызова MCP)

### 4.2 Обновление API Gateway

Обновить `src/api/routes/__init__.py` для вызова MCP сервиса через `mcp_client`.

### 4.3 Интеграция Бот ↔ API

Этот шаг остается таким же, как в старой "Итерации 3". Бот вызывает API Gateway.

### 4.4 Коммит
```bash
git add .
git commit -m "feat(integration): connect bot-api-mcp services"
```

---

## Итерация 5: Google Sheets в MCP

(Содержимое этой итерации переносится из старой "Итерации 4", но все пути к файлам теперь внутри `src/mcp/`, например `src/mcp/storage/sheets.py`)

---

## Итерация 6: AI Agent в MCP

(Содержимое этой итерации переносится из старой "Итерации 5", но все пути к файлам теперь внутри `src/mcp/`, например `src/mcp/agents/simple.py`, и агент интегрируется в MCP, а не в API)

---

## Итерация 7: Multi-Agent System

(Содержимое этой итерации переносится из старой "Итерации 6", реализуется внутри MCP)

---

## Итерация 8: Полировка и безопасность

(Содержимое этой итерации переносится из старой "Итерации 7", применяется к соответствующим сервисам)