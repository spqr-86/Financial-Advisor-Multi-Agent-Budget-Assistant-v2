# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Budget Assistant v2.0** is a Telegram-based AI financial management bot that tracks expenses and provides personalized financial advice. The project uses a microservices architecture with three independent services communicating via HTTP.

**Current Status:** Iteration 8/10 - Production polish complete; message splitting, enhanced logging, timeout handling, and graceful shutdown implemented.

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
- Tools: `get_expenses_tool`, `get_statistics_tool`

**Agent prompts:** Located in `prompts/agents/` (orchestrator.txt, registrar.txt, analyst.txt)

**Implementation:** `src/mcp/agents/adk_agents.py` contains the main ADKBudgetAgent class that orchestrates all agents.

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

**Important:** Run all three services in separate terminals for local development.

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

### Docker

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

### API Gateway Development
- **Always check MCP health:** Use `get_mcp_client().health_check()` in health endpoint
- **Return degraded status:** If MCP unavailable, return `{"status": "degraded", "dependencies": {"mcp": false}}`
- **Pydantic auto-validation:** Request validation happens automatically via type hints

### MCP Service Development
- **Agent system using google-adk:** All agents defined in `src/mcp/agents/adk_agents.py`
- **Tools in separate module:** Tool definitions in `src/mcp/agents/tools/sheets.py`
- **Prompts in files:** Agent instructions loaded from `prompts/agents/*.txt`
- **Storage operations:** Always use `StorageInterface` methods, never direct Google Sheets calls

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

**Common (all services):**
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT` - Environment name (development, production)

## Development Roadmap (10 Iterations)

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
| **8** | **✅** | **Production Polish: timeouts, message splitting, logging, graceful shutdown** |
| 9 | ⏳ | Cloud Run deployment |
| 10 | ⏳ | Production monitoring and metrics |

**Next Focus:** Iteration 9 - Cloud Run deployment (Docker optimization, Cloud Run configuration, secrets management)

## CI/CD Pipeline

**GitHub Actions:** `.github/workflows/ci.yml`
- Triggers on push to `dev` branch and all pull requests
- Steps: Checkout → Python setup → Install deps → Ruff linting → Pytest
- Requirements: Linting must pass, tests must pass, coverage ≥50%

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

## Additional Documentation

- `docs/CODE_GUIDE.md` - Beginner-friendly architecture guide (Russian)
- `docs/TESTING.md` - Testing strategies and manual test procedures
- `docs/REBUILD_PLAN.md` - Complete 10-iteration development plan
- `docs/GOOGLE_CLOUD_SETUP.md` - Cloud deployment instructions
- `.env.example` - Environment variables template
- `README.md` - Project overview
