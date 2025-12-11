# Budget Assistant v2.0

AI-powered Telegram bot for personal finance management using multi-agent architecture and Google Sheets integration.

## Overview

Budget Assistant is an intelligent financial management bot that helps track expenses through natural language conversations in Telegram. It uses Google's Gemini AI with a multi-agent system to understand your spending patterns, categorize expenses automatically, and provide financial insights.

**Key Features:**
- =¬ Natural language expense tracking (":C?8; E;51 50 @C1;59")
- > Multi-agent AI system with specialized agents (Orchestrator, Registrar, Analyst)
- =Ê Automatic categorization and Google Sheets integration
- =È Expense statistics and analysis
- = User access control
-  Cloud-native deployment on Google Cloud Run

## Architecture

The project uses a **microservices architecture** with three independent services:

```
User (Telegram) ’ Bot (8080) ’ API Gateway (8081) ’ MCP Service (8082) ’ Google Sheets
```

- **Telegram Bot** - Handles user interactions, rate limiting, access control
- **API Gateway** - Routes requests, validates data, handles errors
- **MCP Service** - Multi-agent AI system, business logic, Google Sheets integration

## Quick Start

### Local Development

```bash
# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your tokens

# Run with docker-compose (recommended)
docker-compose up

# Or run manually (3 terminals)
poetry run python -m src.mcp.app       # Terminal 1 (port 8082)
poetry run python -m src.api.app       # Terminal 2 (port 8081)
poetry run python -m src.bot.run_polling  # Terminal 3 (polling mode)
```

### Cloud Run Deployment

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project
export GCP_REGION=us-central1
export TELEGRAM_BOT_TOKEN=your-token
export GOOGLE_API_KEY=your-api-key
export WEBHOOK_SECRET=your-secret
export GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id

# Deploy all services
./scripts/deploy_all.sh
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete developer guide and architecture overview
- **[Cloud Run Operations](docs/CLOUD_RUN_OPERATIONS.md)** - Production operations guide
- **[Google Cloud Setup](docs/GOOGLE_CLOUD_SETUP.md)** - Cloud deployment instructions
- **[Testing Guide](docs/TESTING.md)** - Testing strategies and procedures
- **[Code Guide](docs/CODE_GUIDE.md)** - Beginner-friendly architecture guide (Russian)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Bot Framework | aiogram 3.4+ |
| Web Framework | FastAPI 0.115+ |
| AI Framework | google-adk 1.20+ (Agent Development Kit) |
| AI Model | Google Gemini (gemini-2.0-flash) |
| Storage | Google Sheets via gspread |
| Deployment | Google Cloud Run + Secret Manager |
| Testing | pytest + pytest-asyncio |

## Project Status

**Current**: Iteration 9/10 - Production deployment complete

-  Microservices architecture (3 services)
-  Multi-agent AI system with google-adk
-  Google Sheets integration
-  Cloud Run deployment with Docker
-  Secret Manager integration
-  Production polish (timeouts, logging, graceful shutdown)
- ó Monitoring and metrics (Iteration 10)

## Requirements

- Python 3.11+
- Poetry for dependency management
- Docker & docker-compose (for local dev)
- Google Cloud Project (for production)
- Telegram Bot Token
- Google Gemini API Key
- Google Service Account with Sheets access

## Testing

```bash
# Run all tests
poetry run pytest

# With coverage report
poetry run pytest --cov=src --cov-report=html

# Current coverage: 55.66% (56 tests passing)
```

## Environment Variables

### Required for all environments:
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from BotFather
- `GOOGLE_API_KEY` - Gemini API key
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON
- `GOOGLE_SHEETS_SPREADSHEET_ID` - Google Sheets spreadsheet ID

### Local development:
- `BUDGET_API_URL=http://localhost:8081`
- `MCP_API_URL=http://localhost:8082`

### Production (Cloud Run):
- `GCP_PROJECT_ID` - Google Cloud project ID
- `GCP_REGION` - Cloud Run region (default: us-central1)
- `WEBHOOK_SECRET` - Random secret for webhook validation

See `.env.example` for complete list.

## Common Operations

### View logs (Cloud Run)
```bash
gcloud run services logs read budget-mcp --project=${GCP_PROJECT_ID} --region=${GCP_REGION} --limit=50
```

### Change Gemini model
```bash
gcloud run services update budget-mcp --update-env-vars "GEMINI_MODEL=gemini-2.0-flash" --project=${GCP_PROJECT_ID} --region=${GCP_REGION}
```

### Check health
```bash
curl https://budget-bot-*.run.app/health
```

See [Cloud Run Operations Guide](docs/CLOUD_RUN_OPERATIONS.md) for more commands.

## Contributing

This is a personal project, but suggestions and feedback are welcome!

1. Check [CLAUDE.md](CLAUDE.md) for development guidelines
2. Follow the existing code style (ruff formatting)
3. Add tests for new features
4. Maintain 50%+ test coverage

## License

Private project - All rights reserved

## Author

Developed with assistance from Claude (Anthropic) using Claude Code CLI.

---

**Need help?** Check the documentation in `/docs` or see troubleshooting section in CLAUDE.md.
