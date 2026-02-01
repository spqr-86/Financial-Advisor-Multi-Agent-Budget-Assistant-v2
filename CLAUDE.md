# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Budget Assistant v2.0** is a Telegram-based AI financial management bot that tracks expenses and provides personalized financial advice. The project uses a microservices architecture with three independent services communicating via HTTP.

**Current Status:** Iteration 11 (UX/UI Phase 2) - Structured /add command with FSM, reply keyboards, and step-by-step expense flow. Phase 1 complete with interactive buttons, commands, and rich formatting. Cloud Run deployment active with full production setup.

**Core Functionality:**
- Accept expense descriptions from users via Telegram ("купил хлеб 50 рублей")
- Automatically categorize and record expenses in Google Sheets
- Provide expense statistics and analysis
- Generate AI-powered financial advice using Google Gemini
- Support multiple users with access control

## Architecture: Three-Service Design

```
User (Telegram) → Bot (8080) → API Gateway (8081) → MCP Service (8082) → Google Sheets
```

**Why three services?**
- Separation of concerns: Bot handles Telegram, API handles routing, MCP handles intelligence
- Independent scaling: Each service can be scaled separately
- Fault isolation: MCP failure doesn't crash the bot
- Technology flexibility: Can replace Telegram with other platforms without changing API/MCP

### Service Breakdown

**1. Telegram Bot (Port 8080)** - `src/bot/`
- Handles Telegram interactions (webhook in production, polling in development)
- Implements rate limiting (10 req/min per user)
- Access control via TELEGRAM_ADMIN_IDS whitelist
- Middleware stack: APIClientMiddleware → RateLimitMiddleware → AccessControlMiddleware → Handlers
- **UX/UI (Iteration 10-11):** Interactive keyboards, HTML formatting, emoji categories, contextual buttons, FSM-based structured input
  - `keyboards/` - Inline and reply keyboards for user interactions
  - `formatters/` - Message formatting with HTML and emoji
  - `handlers/commands.py` - Bot commands (/help, /stats, /last, /delete, /examples)
  - `handlers/callbacks.py` - Inline button callback handlers
  - `handlers/structured.py` - FSM-based /add command with step-by-step flow (Iteration 11)
  - `states.py` - FSM state definitions for structured conversations

**2. API Gateway (Port 8081)** - `src/api/`
- Validates requests using Pydantic models
- Proxies to MCP service with health checking
- Returns 503 if MCP unavailable with "degraded" status
- Exception handling and error response formatting

**3. MCP Service (Port 8082)** - `src/mcp/`
- Multi-agent AI system using google-adk patterns
- Google Sheets integration for data persistence
- Business logic and expense processing
- Three specialized agents: Orchestrator, Registrar, Analyst

## Multi-Agent System (Iteration 7)

The project uses **google-adk** (Agent Development Kit) patterns with a root orchestrator agent that routes to specialized agents:

**BudgetOrchestrator (root_agent):**
- Analyzes user intent and routes to appropriate specialist
- Coordinates between agents
- Handles fallback responses

**RegistrarAgent:**
- Handles expense creation ("купил", "потратил")
- Handles expense deletion
- Tools: `add_expense_tool`, `delete_last_expense_tool`

**AnalystAgent:**
- Handles expense viewing and statistics ("покажи", "статистика")
- Handles complex analytics with code execution (comparisons, trends, anomalies)
- Tools: `get_expenses_tool`, `get_statistics_tool`, `execute_analysis_code`

**Agent prompts:** Located in `prompts/agents/` (orchestrator.txt, registrar.txt, analyst.txt)

**Implementation:** `src/mcp/agents/adk_agents.py` contains the main ADKBudgetAgent class that orchestrates all agents.

## Code Execution for Complex Analytics (Iteration 12)

AnalystAgent now has `execute_analysis_code` tool for complex queries that can't be handled by standard tools.

**When it's used:**
- Period comparisons ("compare food expenses in January vs February")
- Trend analysis ("are my food expenses growing")
- Anomaly detection ("find unusually large expenses")
- Custom calculations ("average check on weekends")

**How it works:**
1. LLM generates Python code based on user query
2. Code runs using exec() with controlled globals/locals (pandas, numpy, safe builtins only)
3. Code receives pandas DataFrame `df` with expense data
4. Result must be saved to `result` variable (string)
5. Timeout: 10 seconds

**Security:**
- Whitelist users only (TELEGRAM_ADMIN_IDS)
- No file I/O, network, or unsafe builtins
- LLM-generated code (not user input directly)

**Implementation:** `src/mcp/agents/tools/code_executor.py`

## Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Bot Framework | aiogram ^3.4.0 | Telegram Bot API wrapper |
| Web Framework | FastAPI ^0.115.0 | REST API for services |
| ASGI Server | uvicorn ^0.34.0 | Production HTTP server |
| Data Validation | Pydantic ^2.5.0 | Request/response validation |
| HTTP Client | aiohttp ^3.9.0 | Async inter-service communication |
| AI Model | google-generativeai ^0.8.0 | Gemini API access |
| Multi-Agent Framework | google-adk ^1.20.0 | Agent orchestration (Iteration 7) |
| Data Storage | gspread ^5.12.0 | Google Sheets API client |
| Data Analysis | pandas ^2.0.0, numpy ^1.24.0 | DataFrame operations for code execution |
| Testing | pytest ^7.4.0, pytest-asyncio ^0.23.0 | Async testing |
| Linting | ruff ^0.1.0 | Code style checking |

## Common Development Commands

### Installation & Setup
```bash
# Install all dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your tokens (TELEGRAM_BOT_TOKEN, GOOGLE_API_KEY, etc.)
```

### Running Services Locally (Development)

**Option 1: Using docker-compose (Recommended for Iteration 9+)**

```bash
# Build all images
docker-compose build

# Start all services (foreground)
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f bot
docker-compose logs -f api
docker-compose logs -f mcp

# Stop all
docker-compose down

# Rebuild and restart
docker-compose up --build
```

**Option 2: Manual startup (3 terminals)**

Run all three services in separate terminals:

```bash
# Terminal 1: MCP Service (port 8082)
poetry run python -m src.mcp.app

# Terminal 2: API Gateway (port 8081)
poetry run python -m src.api.app

# Terminal 3: Bot in polling mode (for development)
poetry run python -m src.bot.run_polling

# For production (webhook mode):
poetry run python -m src.bot.app
```

### Testing

```bash
# Run all tests with coverage (minimum 50% required)
poetry run pytest

# Run specific test file
poetry run pytest tests/test_core/test_schemas.py

# Run specific test
poetry run pytest tests/test_core/test_schemas.py::test_query_request_empty_query

# Generate HTML coverage report
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Quick run without coverage
poetry run pytest -q
```

**Current Test Coverage (Iteration 8):** 55.66% (56 tests)
- Core: 100%
- Bot handlers: 92.86%
- Bot middlewares: 100%
- Bot utils (Iteration 8): 87.80% (8 new tests for message splitting)
- API Gateway: 58.70%
- MCP Service: 55.00%
- Note: 51/56 tests passing (5 old API/MCP tests have httpx syntax issues unrelated to Iteration 8 changes)

### Code Quality

```bash
# Lint code (automatically runs in CI/CD)
poetry run ruff check src/

# Format code
poetry run ruff format src/
```

### Git Commits

**IMPORTANT:** Do NOT add "🤖 Generated with Claude Code" or "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>" to commit messages in this project.

```bash
# Standard commit message format
git commit -m "type: brief description

Optional longer explanation of the change
"

# Example
git commit -m "fix: update test_sheets.py to use environment variables

- Load settings from .env using python-dotenv
- Use correct worksheet name 'Траты и бюджет'
- Match production code behavior
"
```

### Docker

**Important:** All Dockerfiles use `--without dev` flag for Poetry (not `--no-dev` which is deprecated in Poetry 1.2+).

```bash
# Build images
docker build -f docker/Dockerfile.bot -t budget-bot .
docker build -f docker/Dockerfile.api -t budget-api .
docker build -f docker/Dockerfile.mcp -t budget-mcp .

# Run with environment variables
docker run -p 8082:8082 -e GOOGLE_API_KEY=xxx budget-mcp
docker run -p 8081:8081 -e MCP_API_URL=http://host.docker.internal:8082 budget-api
docker run -p 8080:8080 -e BUDGET_API_URL=http://host.docker.internal:8081 budget-bot
```

**Health checks:** `docker-compose.yml` uses Python-based health checks (not curl, which isn't available in python:3.11-slim images).

## Core Patterns & Modules

### Configuration (`src/core/config.py`)
- All services extend `BaseAppSettings` (Pydantic BaseSettings)
- Loads from `.env` file or environment variables
- Each service has its own settings class: `BotSettings`, `APISettings`, `MCPSettings`
- Key settings: `TELEGRAM_BOT_TOKEN`, `BUDGET_API_URL`, `MCP_API_URL`, `GOOGLE_API_KEY`, `GOOGLE_SHEETS_SPREADSHEET_ID`

### Data Validation (`src/core/schemas.py`)
- Pydantic v2 models for all requests/responses
- Core schemas: `QueryRequest`, `QueryResponse`, `HealthResponse`, `AddExpenseRequest`
- Automatic validation with rich error messages
- Used for OpenAPI documentation generation

### Exception Handling (`src/core/exceptions.py`)
- Custom exception hierarchy extending `BudgetException`
- Exceptions: `ServiceUnavailableError` (503), `ValidationError` (400), `NotFoundError` (404), `RateLimitError` (429), `AgentError` (500)
- Automatic HTTP response conversion via exception handlers
- Pattern: `raise ServiceUnavailableError("MCP service is down")`

### HTTP Client with Retry Logic (`src/core/http_client.py`)
- `ServiceClient` class handles inter-service communication
- Exponential backoff retry strategy (3 attempts by default, Iteration 8: 1s, 2s, 4s)
- Automatically retries on 5xx errors and network failures
- Logs all retry attempts with timing information (Iteration 8)
- Raises `ServiceUnavailableError` after exhausting retries
- Separate handling for `asyncio.TimeoutError` (Iteration 8)

### Bot Utilities (`src/bot/utils.py`) - Iteration 8
- `split_long_message(text, max_length=4096)`: Smart message splitting for Telegram's character limit
  - Splits by: paragraphs → sentences → words → characters (in that order of preference)
  - Returns list of message chunks, each ≤ max_length
  - Preserves readability by avoiding mid-word splits
  - Used automatically in handlers
- `TELEGRAM_MAX_MESSAGE_LENGTH`: Constant for Telegram's 4096 character limit

### Graceful Shutdown (`src/core/shutdown.py`) - Iteration 8
- `setup_shutdown_handlers(callback)`: Registers SIGTERM/SIGINT handlers
- Used in FastAPI lifespan handlers for clean Cloud Run deployment
- Currently implemented directly in app.py files (may be refactored to use this utility)

### Bot Keyboards (`src/bot/keyboards/`) - Iteration 10
- **Inline keyboards** (`inline.py`): Interactive buttons attached to messages
  - `get_main_menu_keyboard()` - Main menu after /start (Статистика, Последние, Примеры, Помощь)
  - `get_after_add_keyboard()` - Actions after adding expense (Отменить, Еще один, Статистика)
  - `get_stats_period_keyboard()` - Period selection (Неделя, Месяц, Год)
  - `get_confirm_delete_keyboard()` - Deletion confirmation dialog
  - `get_back_to_menu_keyboard()` - Simple back button
- **Reply keyboards** (`reply.py`): Keyboard replacement buttons (Phase 2)
  - `get_categories_keyboard()` - Category selection for /add command
  - `get_amount_keyboard()` - Quick amount selection buttons
- Pattern: All keyboard functions return `InlineKeyboardMarkup` or `ReplyKeyboardMarkup`
- Usage: Pass as `reply_markup` parameter to `message.answer()`

### Message Formatters (`src/bot/formatters/`) - Iteration 10
- **HTML formatting** (`messages.py`): Rich text formatting with emoji and structure
  - `CATEGORY_EMOJI` - Dict mapping categories to emoji (🍕 Еда, 🚗 Транспорт, etc.)
  - `format_expense_added()` - Success message after adding expense
  - `format_expenses_list()` - List of recent expenses with numbering
  - `format_statistics()` - Statistics with progress bars (████████░░ 45%)
  - `format_help_message()` - Interactive help with examples
  - `format_examples_message()` - Usage examples grouped by action
- Pattern: All format functions return HTML-formatted strings
- Usage: Pass formatted text to `message.answer(text, parse_mode="HTML")`
- Progress bars: Use filled blocks (█) and empty blocks (░) for visual percentage

### Bot Command Handlers (`src/bot/handlers/`) - Iteration 10
- **commands.py**: Slash command handlers
  - `/help` - Interactive help with back button
  - `/stats` - Statistics with period selection buttons
  - `/last` - Recent 5 expenses with formatting
  - `/delete` - Delete with confirmation keyboard
  - `/examples` - Usage examples categorized by action
- **callbacks.py**: Inline button callback handlers
  - `back_to_menu` - Return to main menu
  - `show_help`, `show_examples` - Display help/examples
  - `show_stats`, `show_last` - Fetch and display data
  - `confirm_delete`, `cancel_delete` - Handle deletion flow
  - `stats_week`, `stats_month`, `stats_year` - Period-specific stats
- Pattern: Commands use `@router.message(Command("name"))`, callbacks use `@router.callback_query(F.data == "action")`
- All handlers require `api_client: ServiceClient` injected by middleware

## Storage Layer

### Interface (`src/mcp/storage/interface.py`)
- `StorageInterface` abstract base class defines contract
- Methods: `add_expense()`, `get_expenses()`, `get_statistics()`, `delete_last_expense()`, `health_check()`
- Allows swapping implementations (currently Google Sheets, could be PostgreSQL later)

### Google Sheets Implementation (`src/mcp/storage/sheets.py`)
- `GoogleSheetsStorage` implements `StorageInterface`
- Uses service account credentials from `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- Worksheet name: "Траты и бюджет"
- Columns: Дата | Категория | Расшифровка | Сумма
- Date format: "DD.MM.YYYY"
- Async wrapping of synchronous gspread calls using executor
- Lazy connection: connects on first use, reuses connection

## Request Flow

1. User sends message to Telegram bot
2. Bot receives via webhook (production) or polling (development)
3. Middlewares process: Rate limit → Access control → API client injection
4. Handler calls API Gateway with `QueryRequest` (with timeout handling, Iteration 8)
5. API Gateway validates and proxies to MCP Service (logs timing and user_id, Iteration 8)
6. MCP Service processes with multi-agent system (logs AI processing time, Iteration 8):
   - Orchestrator analyzes intent
   - Routes to RegistrarAgent (for "купил") or AnalystAgent (for "покажи")
   - Agent uses appropriate tool (add_expense, get_expenses, etc.)
   - Tool interacts with Google Sheets storage
7. Response flows back through the stack
8. Bot splits long responses if >4096 chars (Iteration 8)
9. Bot sends response to user (multiple messages if split, with 0.5s delay between chunks)

## Important Implementation Notes

### Bot Development
- **Always use polling mode for local development:** `poetry run python -m src.bot.run_polling`
- **Webhook mode requires public URL:** Only works in production with valid HTTPS endpoint
- **Handler pattern:** All handlers must check `if not message.from_user: return` for safety
- **Typing indicator:** Use `await message.bot.send_chat_action(message.chat.id, "typing")` before long operations
- **Middleware order matters:** APIClientMiddleware → RateLimitMiddleware → AccessControlMiddleware
- **Long message handling (Iteration 8):** Use `split_long_message()` from `src/bot/utils.py` to split responses exceeding Telegram's 4096 character limit. Handler automatically splits and sends with 0.5s delay between chunks.
- **Timeout handling (Iteration 8):** Catch `asyncio.TimeoutError` separately for user-friendly messages. HTTP client automatically retries with exponential backoff (1s, 2s, 4s).
- **UX/UI patterns (Iteration 10-11):**
  - Use `parse_mode="HTML"` for all formatted messages
  - Import formatters from `src.bot.formatters` for consistent styling
  - Add inline keyboards via `reply_markup=get_*_keyboard()` from `src.bot.keyboards`
  - Register callback handlers in `callbacks.py` using `@router.callback_query(F.data == "action")`
  - Always inject `api_client: ServiceClient` for handlers that need API access
  - Use category emoji from `CATEGORY_EMOJI` dict for visual consistency
- **FSM (Finite State Machine) patterns (Iteration 11):**
  - Define states in `src/bot/states.py` using `StatesGroup` and `State`
  - Use `StateFilter` to match specific states in handlers
  - Access state data with `state.get_data()` and update with `state.update_data(key=value)`
  - Clear state after completing flow with `await state.clear()`
  - Reply keyboards (`get_categories_keyboard()`, `get_amount_keyboard()`) used during FSM flows
  - Remove reply keyboard after FSM completes with `remove_keyboard()`
  - Register FSM router FIRST in dispatcher (before commands/callbacks) to intercept state-specific messages

### API Gateway Development
- **Always check MCP health:** Use `get_mcp_client().health_check()` in health endpoint
- **Return degraded status:** If MCP unavailable, return `{"status": "degraded", "dependencies": {"mcp": false}}`
- **Pydantic auto-validation:** Request validation happens automatically via type hints

### MCP Service Development
- **Agent system using google-adk:** All agents defined in `src/mcp/agents/adk_agents.py`
- **Tools in separate module:** Tool definitions in `src/mcp/agents/tools/sheets.py`
- **Prompts in files:** Agent instructions loaded from `prompts/agents/*.txt`
- **Storage operations:** Always use `StorageInterface` methods, never direct Google Sheets calls
- **Model selection:** Use `gemini-2.0-flash` for stable quota. Avoid experimental models like `gemini-2.0-flash-exp` in production (low free-tier quota). Available models: `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-flash-latest`. Check quota errors with 🚨 emoji in logs.

### Testing
- **Async tests:** All tests use `@pytest.mark.asyncio` decorator
- **Fixtures in conftest.py:** Common fixtures like `mock_env`, `mock_service_client`
- **Mock pattern:** Use `unittest.mock.Mock` and `AsyncMock` for async functions
- **CI/CD enforcement:** Tests must pass and coverage must be ≥50% for PR merge

### Error Handling & Logging (Iteration 8)
- **Each layer has error handling:** Bot catches ServiceClient errors, API returns 503 if MCP down, HTTP client retries automatically
- **User-friendly messages:** Bot shows "произошла ошибка" on failures, not technical details
- **Comprehensive logging (Iteration 8):**
  - Bot handlers: user_id, query preview (50 chars), response length, message chunk count
  - API Gateway: request timing, response size, user tracking
  - MCP Service: AI processing time, detailed metrics
  - HTTP Client: request duration, retry attempts, status codes
  - All errors include full traceback (`exc_info=True`)
- **Graceful shutdown (Iteration 8):** SIGTERM/SIGINT handlers registered in all services for clean Cloud Run deployment
  - API Gateway: closes HTTP client connections
  - MCP Service: closes storage and agent connections
  - Detailed shutdown logging at each step

## Environment Variables

**Required for Bot:**
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from BotFather
- `BUDGET_API_URL` - URL of API Gateway (http://localhost:8081 for local dev)
- `TELEGRAM_ADMIN_IDS` - Comma-separated list of allowed user IDs
- `WEBHOOK_SECRET` - Random secret for webhook validation (production only)

**Required for API:**
- `MCP_API_URL` - URL of MCP Service (http://localhost:8082 for local dev)
- `REQUEST_TIMEOUT` - HTTP request timeout in seconds (default: 30)

**Required for MCP:**
- `GOOGLE_API_KEY` - Gemini API key
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON file
- `GOOGLE_SHEETS_SPREADSHEET_ID` - Spreadsheet ID from Google Sheets URL
- `GEMINI_MODEL` - Gemini model name (default: `gemini-2.0-flash`, recommended). Use this to quickly switch models when quota exhausted. Avoid `gemini-2.5-flash` (only 5 req/min free tier).

**MCP Server (optional):**
- `MCP_TRANSPORT` - Transport mode for MCP Server (`stdio` | `sse` | `both`). Use `both` for Cloud Run with remote access.

**Common (all services):**
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT` - Environment name (development, production)

## Development Roadmap

| Iteration | Status | Focus |
|-----------|--------|-------|
| 0 | ✅ | Project setup, Poetry, structure |
| 1 | ✅ | Telegram Bot with handlers and webhook |
| 2 | ✅ | API Gateway with FastAPI |
| 3 | ✅ | MCP Service skeleton |
| 4 | ✅ | Integration testing, HTTP client, 48 tests |
| 5 | ✅ | Google Sheets integration |
| 6 | ✅ | AI Agent v1 with Gemini |
| 7 | ✅ | Multi-Agent System with google-adk |
| 8 | ✅ | Production Polish: timeouts, message splitting, logging, graceful shutdown |
| 9 | ✅ | Cloud Run Deployment: docker-compose, Secret Manager, deployment scripts |
| 10 | ✅ | UX/UI Phase 1: Interactive buttons, commands, HTML formatting, emoji categories |
| **11** | **✅** | **UX/UI Phase 2: Structured /add with FSM, reply keyboards, step-by-step flow** |

**Next Focus:** UX/UI Phase 3 - Visualizations (matplotlib charts), budget limits, data export; Production monitoring (Cloud Logging, Error Reporting)

## CI/CD Pipeline

**GitHub Actions:** `.github/workflows/ci.yml`
- Triggers on push to `dev` branch and all pull requests
- Steps: Checkout → Python setup → Install deps → Ruff linting → Pytest
- Requirements: Linting must pass, tests must pass, coverage ≥50%

## Cloud Run Deployment (Iteration 9)

### Prerequisites

1. Google Cloud Project with billing enabled
2. gcloud CLI installed and authenticated
3. Docker installed locally
4. Environment variables configured in .env

### Setup (One-time)

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project ${GCP_PROJECT_ID}

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Configure Docker for GCR
gcloud auth configure-docker
```

### Deploy All Services

```bash
# Export required variables
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1
export TELEGRAM_BOT_TOKEN=your-token
export GOOGLE_API_KEY=your-api-key
export WEBHOOK_SECRET=your-secret
export GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
export TELEGRAM_ADMIN_IDS=123456,789012

# Deploy (runs all deployment scripts in order)
./scripts/deploy_all.sh
```

The `deploy_all.sh` script will:
1. Create/verify secrets in Google Secret Manager
2. Deploy MCP Service → retrieve URL
3. Deploy API Gateway with MCP_API_URL → retrieve URL
4. Deploy Bot with BUDGET_API_URL → retrieve URL
5. Set Telegram webhook automatically

### Verify Deployment

```bash
# Check service status
gcloud run services list --project=${GCP_PROJECT_ID}

# Test health endpoints
BOT_URL=$(gcloud run services describe budget-bot --region ${GCP_REGION} --format 'value(status.url)')
curl ${BOT_URL}/health

# View logs
gcloud run logs tail budget-bot --region ${GCP_REGION}
gcloud run logs tail budget-api --region ${GCP_REGION}
gcloud run logs tail budget-mcp --region ${GCP_REGION}
```

### Troubleshooting

**Google Sheets access denied:**
```bash
# If you see "Failed to add expense: 'NoneType' object has no attribute 'worksheet'"
# The service account needs access to your Google Sheets spreadsheet

# 1. Get service account email:
cat service-account.json | grep client_email

# 2. Share your Google Sheets with this email (Editor permissions):
#    Open spreadsheet → Share button → Add email → Editor role
```

**Service account issues (deleted default compute SA):**
```bash
# If deployment fails with "Permission 'iam.serviceaccounts.actAs' denied"
# Create a custom service account for Cloud Run:

gcloud iam service-accounts create cloud-run-sa \
    --display-name="Cloud Run Service Account" \
    --project=${GCP_PROJECT_ID}

# Grant access to secrets:
for secret in google-api-key service-account-json telegram-bot-token webhook-secret; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:cloud-run-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=${GCP_PROJECT_ID}
done

# Update deployment scripts to use this SA (already done in scripts/deploy_*.sh)
```

**Bot not receiving messages:**
```bash
# Check webhook status
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"

# Should show your Cloud Run URL
# If wrong, redeploy or manually set:
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=https://budget-bot-xxx.run.app/webhook&secret_token=${WEBHOOK_SECRET}"
```

**MCP service errors (Gemini quota):**
```bash
# Check logs for quota issues
gcloud run services logs read budget-mcp --limit=50 --region=${GCP_REGION} | grep -i "quota\|exhausted"

# Switch model if quota exceeded (gemini-2.5-flash has only 5 req/min free tier!)
# Recommended: gemini-2.0-flash (higher quota)
gcloud run services update budget-mcp \
    --update-env-vars "GEMINI_MODEL=gemini-2.0-flash" \
    --region ${GCP_REGION} \
    --project ${GCP_PROJECT_ID}
```

**Update secrets:**
```bash
# Update a secret value
echo -n "new-token-value" | gcloud secrets versions add telegram-bot-token \
    --data-file=- --project=${GCP_PROJECT_ID}

# Redeploy service to pick up new secret
gcloud run services update budget-bot --region ${GCP_REGION}
```

**View detailed service info:**
```bash
# Service configuration
gcloud run services describe budget-bot --region ${GCP_REGION}

# Recent deployments
gcloud run revisions list --service budget-bot --region ${GCP_REGION}
```

### Cost Estimation

**Light usage (~1000 messages/month):**
- Cloud Run: Free tier (2M requests/month)
- Secret Manager: $0.36/month
- Container Registry: Free tier
- **Total: < $1/month**

## MCP Server (Iteration 10)

Budget Assistant теперь поддерживает **Model Context Protocol (MCP)** - стандарт от Anthropic для интеграции AI-приложений с внешними инструментами. Это позволяет использовать Budget Assistant прямо из Claude Desktop!

### Архитектура: Dual Interface

MCP Service теперь предоставляет два интерфейса параллельно:
- **HTTP REST API** (порт 8082) - для Telegram Bot через API Gateway (существующая архитектура)
- **MCP Protocol** (stdio/SSE) - для Claude Desktop, Cursor, MCP Inspector

Оба интерфейса используют одну и ту же бизнес-логику (ADKBudgetAgent и GoogleSheetsStorage).

### Доступные режимы

**1. Stdio (Claude Desktop, Cursor):**
```bash
./scripts/run_mcp_stdio.sh
# или
poetry run python -m src.mcp.server.run_stdio
```

**2. SSE (MCP Inspector, веб-клиенты):**
```bash
export MCP_TRANSPORT=sse
poetry run python -m src.mcp.app
# Endpoint: http://localhost:8083/mcp/sse
```

**3. Both (Production):**
```bash
export MCP_TRANSPORT=both
poetry run python -m src.mcp.app
# HTTP REST: :8082
# MCP SSE: :8082/mcp/sse
```

### MCP Tools

Доступные инструменты для Claude:
- **process_query(query, user_id)** - основной tool, обрабатывает любой запрос через AI систему
  - Примеры: "купил хлеб 50 рублей", "покажи расходы", "статистика"
- **add_expense(category, amount, description, user_id)** - прямое добавление расхода
- **get_expenses(limit, category, user_id)** - просмотр расходов
- **get_statistics(period, user_id)** - статистика по категориям
- **delete_last_expense(user_id)** - удаление последнего расхода

### MCP Resources

- **budget://help** - инструкция по использованию
- **budget://categories** - список категорий расходов (JSON)

### Быстрый старт с Claude Desktop

1. **Убедитесь что зависимости установлены:**
```bash
poetry install  # fastmcp ^2.0.0 будет установлен
```

2. **Настройте `.env` (если еще не настроен):**
```env
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
MCP_TRANSPORT=stdio  # для Claude Desktop
```

3. **Сделайте скрипт исполняемым:**
```bash
chmod +x scripts/run_mcp_stdio.sh
```

4. **Настройте Claude Desktop:**

Откройте конфигурацию:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

Добавьте:
```json
{
  "mcpServers": {
    "budget-assistant": {
      "command": "/absolute/path/to/budget-assistant-v2/scripts/run_mcp_stdio.sh",
      "cwd": "/absolute/path/to/budget-assistant-v2"
    }
  }
}
```

**Важно:** Используйте absolute paths (например `/Users/petrbaldaev/Dev/budget-assistant-v2`).

5. **Перезапустите Claude Desktop**

6. **Тестируйте:**
- Откройте новую беседу в Claude
- Напишите: "купил хлеб 50 рублей"
- Claude автоматически использует `budget-assistant` tool

### Тестирование с MCP Inspector

```bash
# Запустить в SSE режиме
./scripts/test_mcp_inspector.sh

# В браузере
npx @modelcontextprotocol/inspector
# Подключиться к: http://localhost:8083/mcp/sse
```

### Структура файлов

```
src/mcp/server/
├── __init__.py          # Экспорты
├── config.py            # MCPServerSettings
├── app.py               # FastMCP сервер с tools/resources/prompts
├── tools.py             # Обертки над ADKBudgetAgent
├── resources.py         # Контекст для Claude (help, categories)
└── run_stdio.py         # Entry point для stdio режима

scripts/
├── run_mcp_stdio.sh     # Запуск для Claude Desktop
└── test_mcp_inspector.sh # Запуск для MCP Inspector
```

### Документация

- **`README_MCP.md`** - Quick start guide для пользователей
- **`docs/MCP_SERVER.md`** - Полная техническая документация
- **`docs/CLAUDE_DESKTOP_CONFIG.md`** - Детальная инструкция по настройке Claude Desktop

### Environment Variables (новые)

```env
MCP_TRANSPORT=stdio          # stdio | sse | both
MCP_SSE_HOST=0.0.0.0
MCP_SSE_PORT=8083
```

### Troubleshooting

**Claude Desktop не видит сервер:**
1. Проверьте absolute paths в `claude_desktop_config.json`
2. Убедитесь скрипт executable: `chmod +x scripts/run_mcp_stdio.sh`
3. Проверьте логи: `~/Library/Logs/Claude/mcp-server-budget-assistant.log` (macOS)

**SSE endpoint не отвечает:**
1. Проверьте `MCP_TRANSPORT=sse` или `both` в `.env`
2. Убедитесь порт 8083 свободен: `lsof -i :8083`

**Telegram Bot перестал работать:**
- Не должен! HTTP REST API на порту 8082 сохранен для обратной совместимости.
- MCP Server работает параллельно, не влияя на Bot/API Gateway.

### Dependencies

Добавлена зависимость:
- **fastmcp** ^2.0.0 - высокоуровневый framework для MCP серверов

## Common Gotchas

1. **Don't commit secrets:** Never commit `.env`, `service-account.json`, or any credentials
2. **Always read files before editing:** Use Read tool before Edit/Write to preserve formatting
3. **Polling vs Webhook:** Use `run_polling.py` for local dev, `app.py` for production
4. **Service startup order:** Start MCP first (8082), then API (8081), then Bot (8080)
5. **Test coverage threshold:** Minimum 50% coverage enforced in CI/CD
6. **Pydantic v2 syntax:** Use `model_config` not `class Config`
7. **Middleware execution order:** They run in the order they're added to dispatcher
8. **Agent system:** Always use `LlmAgent` from google-adk for tool-based agents, not the base `Agent` class
9. **Long messages (Iteration 8):** Telegram has 4096 char limit. Use `split_long_message()` from `src/bot/utils.py` to split automatically. Handler does this by default.
10. **Timeout errors (Iteration 8):** Always catch `asyncio.TimeoutError` separately from general exceptions for better user messages. HTTP client retries 3 times with exponential backoff.
11. **Logging best practices (Iteration 8):** Always log user_id, request timing, and use `exc_info=True` for exceptions. Check `src/bot/handlers/__init__.py` for examples.
12. **Graceful shutdown (Iteration 8):** Services handle SIGTERM/SIGINT for Cloud Run. Don't block shutdown in custom code.
13. **Gemini API quota issues:** If bot times out (30s+) with no response, check MCP logs for quota exceeded errors. **Recommended:** Use `GEMINI_MODEL=gemini-2.0-flash` (15 req/min free tier). **Avoid:** `gemini-2.5-flash` (only 5 req/min). For Cloud Run deployment, use: `gcloud run services update budget-mcp --update-env-vars "GEMINI_MODEL=gemini-2.0-flash" --region us-central1 --project ${GCP_PROJECT_ID}`. See [Cloud Run Operations](docs/CLOUD_RUN_OPERATIONS.md) for details.

## Additional Documentation

- `docs/CODE_GUIDE.md` - Beginner-friendly architecture guide (Russian)
- `docs/TESTING.md` - Testing strategies and manual test procedures
- `docs/REBUILD_PLAN.md` - Complete 10-iteration development plan
- `docs/GOOGLE_CLOUD_SETUP.md` - Cloud deployment instructions
- **`docs/CLOUD_RUN_OPERATIONS.md`** - Production operations guide (logs, monitoring, model switching)
- **`docs/CLOUD_MCP_SETUP.md`** - Remote MCP access via Claude Desktop (SSE over Cloud Run)
- **`docs/UX_UI_DESIGN.md`** - Full UX/UI design guide with 3-phase roadmap (keyboards, formatters, visualizations)
- `docs/MCP_SERVER.md` - MCP Server technical documentation (local stdio/SSE modes)
- `docs/CLAUDE_DESKTOP_CONFIG.md` - Claude Desktop configuration for local MCP
- `.env.example` - Environment variables template
- `README.md` - Project overview
