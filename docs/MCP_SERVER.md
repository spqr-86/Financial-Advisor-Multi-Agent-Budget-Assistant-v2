# MCP Server для Budget Assistant v2.0

## Обзор

Budget Assistant v2.0 теперь поддерживает два способа взаимодействия:

1. **HTTP REST API** (порт 8082) - для Telegram Bot через API Gateway (существующая архитектура)
2. **MCP Protocol** (stdio/SSE) - для Claude Desktop, Cursor, MCP Inspector

## Архитектура: Dual Interface Pattern

```
┌─────────────────────────────────────────┐
│      MCP Service (Port 8082)            │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ HTTP REST    │  │   MCP Server    │ │
│  │ (FastAPI)    │  │   (FastMCP)     │ │
│  │              │  │                 │ │
│  │ /mcp/query   │  │ stdio transport │ │
│  │ /health      │  │ SSE transport   │ │
│  └──────┬───────┘  └────────┬────────┘ │
│         │                   │          │
│         └─────────┬─────────┘          │
│                   ▼                    │
│         ┌──────────────────┐           │
│         │  ADKBudgetAgent  │           │
│         │  (google-adk)    │           │
│         └──────────────────┘           │
│                   │                    │
│                   ▼                    │
│         ┌──────────────────┐           │
│         │ StorageInterface │           │
│         │ (Google Sheets)  │           │
│         └──────────────────┘           │
└─────────────────────────────────────────┘
```

## Режимы работы

### Stdio Mode (Claude Desktop, Cursor)

Запуск:
```bash
./scripts/run_mcp_stdio.sh
# или
poetry run python -m src.mcp.server.run_stdio
```

**Использование:**
- Claude Desktop (см. `CLAUDE_DESKTOP_CONFIG.md`)
- Cursor IDE
- Другие MCP-совместимые клиенты

**Особенности:**
- Сервер запускается как subprocess
- Коммуникация через stdin/stdout
- JSON-RPC 2.0 protocol

### SSE Mode (Web clients, MCP Inspector)

Запуск:
```bash
export MCP_TRANSPORT=sse
poetry run python -m src.mcp.app
```

**Endpoint:** `http://localhost:8083/mcp/sse`

**Использование:**
- MCP Inspector для тестирования
- Веб-клиенты
- Кастомные интеграции

**Особенности:**
- Server-Sent Events transport
- HTTP-based, легко тестировать
- Доступен через браузер

### Both Modes (Production)

Запуск:
```bash
export MCP_TRANSPORT=both
poetry run python -m src.mcp.app
```

**Использование:**
- Production deployment
- Одновременно HTTP REST + MCP SSE

**Особенности:**
- Порт 8082 для HTTP REST
- Endpoint `/mcp/sse` для MCP SSE
- Обратная совместимость

## MCP Tools

### 1. process_query (Основной tool)

Обрабатывает любой запрос пользователя через AI агентную систему.

**Сигнатура:**
```python
async def process_query(query: str, user_id: str = "default") -> str
```

**Параметры:**
- `query` (str, required): Запрос на русском языке
- `user_id` (str, optional): ID пользователя (default: "default")

**Возвращает:** str - ответ агентной системы

**Примеры:**
```python
# Добавление расхода
await process_query("купил хлеб 50 рублей")
# → "Отлично! Я добавил расход: Продукты, 50 рублей."

# Просмотр расходов
await process_query("покажи последние расходы")
# → "| Дата | Категория | Описание | Сумма |\n..."

# Статистика
await process_query("статистика за месяц")
# → "Общая сумма: 5000 руб.\nПродукты: 2000 руб.\n..."

# Удаление
await process_query("удали последний расход")
# → "Последний расход удален: Продукты, 50 рублей"
```

### 2. add_expense (Прямой tool)

Добавляет расход напрямую без AI обработки.

**Сигнатура:**
```python
async def add_expense(
    category: str,
    amount: float,
    description: str,
    user_id: str = "default"
) -> dict
```

**Параметры:**
- `category` (str): Категория расхода (Продукты, Транспорт, Рестораны, Развлечения, ЖКХ, Одежда, Здоровье, Прочее)
- `amount` (float): Сумма в рублях
- `description` (str): Описание покупки
- `user_id` (str, optional): ID пользователя

**Возвращает:** dict - результат добавления

**Пример:**
```python
await add_expense(
    category="Продукты",
    amount=150.50,
    description="хлеб и молоко"
)
```

### 3. get_expenses (Просмотр)

Получает последние расходы.

**Сигнатура:**
```python
async def get_expenses(
    limit: int = 10,
    category: str | None = None,
    user_id: str = "default"
) -> dict
```

**Параметры:**
- `limit` (int): Количество записей (default: 10)
- `category` (str, optional): Фильтр по категории
- `user_id` (str): ID пользователя

**Возвращает:** dict с полями `expenses`, `count`

### 4. get_statistics (Статистика)

Получает статистику расходов по категориям.

**Сигнатура:**
```python
async def get_statistics(
    period: str = "month",
    user_id: str = "default"
) -> dict
```

**Параметры:**
- `period` (str): Период (day, week, month, year) - пока не используется
- `user_id` (str): ID пользователя

**Возвращает:** dict с полями `total`, `by_category`

### 5. delete_last_expense (Удаление)

Удаляет последний добавленный расход.

**Сигнатура:**
```python
async def delete_last_expense(user_id: str = "default") -> dict
```

**Параметры:**
- `user_id` (str): ID пользователя

**Возвращает:** dict с информацией об удаленном расходе

## MCP Resources

### budget://help

Инструкция по использованию Budget Assistant.

**Тип:** text/plain

**Содержимое:** Полная инструкция с примерами команд и категориями

**Использование в Claude:**
```
# Claude автоматически загружает ресурс при необходимости
# Можно явно запросить: "покажи help для budget assistant"
```

### budget://categories

Список доступных категорий расходов.

**Тип:** application/json

**Содержимое:**
```json
{
  "categories": [
    "Продукты",
    "Транспорт",
    "Рестораны",
    "Развлечения",
    "ЖКХ",
    "Одежда",
    "Здоровье",
    "Прочее"
  ]
}
```

## MCP Prompts

### expense_prompt

Шаблон для добавления расхода.

**Параметры:**
- `item` (str): Название покупки
- `amount` (float): Сумма

**Генерирует:** "Добавь расход: {item} за {amount} рублей"

### statistics_prompt

Шаблон для запроса статистики.

**Параметры:**
- `period` (str, default="месяц"): Период

**Генерирует:** "Покажи статистику расходов за {period}"

### expenses_prompt

Шаблон для просмотра расходов.

**Параметры:**
- `limit` (int, default=10): Количество

**Генерирует:** "Покажи последние {limit} расходов"

## Тестирование

### С MCP Inspector

```bash
# 1. Запустить сервер в SSE режиме
./scripts/test_mcp_inspector.sh

# 2. В другом терминале запустить Inspector
npx @modelcontextprotocol/inspector

# 3. В браузере откроется http://localhost:6274
# 4. Подключиться к: http://localhost:8083/mcp/sse
# 5. Тестировать tools через UI
```

### С Claude Desktop

См. `CLAUDE_DESKTOP_CONFIG.md`

### С pytest (планируется)

```bash
poetry run pytest tests/test_mcp_server/ -v
```

## Развертывание

### Локальная разработка

```bash
# Stdio mode (для Claude Desktop)
./scripts/run_mcp_stdio.sh

# SSE mode (для тестирования)
./scripts/test_mcp_inspector.sh
```

### Docker

```bash
# С поддержкой обоих режимов
docker-compose up mcp
# Порты: 8082 (HTTP), 8083 (SSE)
```

### Cloud Run

MCP SSE endpoint автоматически доступен при deploy:

```bash
./scripts/deploy_mcp.sh
```

**Важно:** Stdio mode работает только локально. Для Cloud Run используйте SSE transport.

## Troubleshooting

### Q: Claude Desktop не видит сервер

**A:**
1. Проверьте absolute paths в `claude_desktop_config.json`
2. Убедитесь что скрипт executable: `chmod +x scripts/run_mcp_stdio.sh`
3. Проверьте логи: `~/Library/Logs/Claude/mcp-server-budget-assistant.log`
4. Попробуйте запустить скрипт вручную

### Q: SSE endpoint не отвечает

**A:**
1. Проверьте что `MCP_TRANSPORT=sse` или `both`
2. Убедитесь порт 8083 свободен: `lsof -i :8083`
3. Проверьте логи FastAPI
4. Попробуйте curl: `curl http://localhost:8083/mcp/sse`

### Q: Tools возвращают ошибки

**A:**
1. Проверьте Google Sheets credentials
2. Убедитесь Gemini API key валидный
3. Проверьте квоту: https://ai.google.dev/gemini-api/docs/rate-limits
4. Проверьте переменную `GEMINI_MODEL` в `.env`

### Q: HTTP REST API перестал работать

**A:** HTTP API не должен быть затронут. Если не работает:
1. Проверьте порт 8082 доступен
2. Проверьте логи MCP Service
3. MCP Server не влияет на HTTP API - они работают независимо

## Конфигурация

### Environment Variables

```env
# MCP Server
MCP_TRANSPORT=stdio          # stdio | sse | both
MCP_SSE_HOST=0.0.0.0
MCP_SSE_PORT=8083

# Google AI (используется MCP tools)
GOOGLE_API_KEY=your-api-key
GEMINI_MODEL=gemini-flash-latest

# Google Sheets (используется storage)
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-id

# Logging
LOG_LEVEL=INFO
```

### Programmatic Configuration

```python
from src.mcp.server.config import MCPServerSettings

settings = MCPServerSettings()
print(settings.mcp_transport)  # stdio, sse, both
print(settings.mcp_sse_port)   # 8083
```

## Расширение

### Добавление нового Tool

1. Создать async функцию в `src/mcp/server/tools.py`
2. Добавить в `src/mcp/server/app.py` с декоратором `@mcp.tool()`
3. Задокументировать в docstring

**Пример:**
```python
# tools.py
async def my_custom_tool(param: str) -> str:
    # Implementation
    pass

# app.py
@mcp.tool()
async def my_custom_tool(param: str) -> str:
    """Tool description for AI."""
    return await tools.my_custom_tool(param)
```

### Добавление Resource

```python
# resources.py
MY_RESOURCE_TEXT = "content"

# app.py
@mcp.resource("budget://my-resource")
async def get_my_resource() -> str:
    return resources.MY_RESOURCE_TEXT
```

## Performance

- **Stdio mode:** Низкая latency, subprocess overhead
- **SSE mode:** HTTP overhead, но легко масштабировать
- **Agent processing:** Зависит от Gemini API (~1-3 секунды)
- **Storage (Sheets):** ~200-500ms per operation

## Security

- **Authentication:** Пока не реализована (user_id="default")
- **Authorization:** Через TELEGRAM_ADMIN_IDS для Bot
- **API Keys:** Храните в `.env`, не коммитьте
- **Credentials:** service-account.json - file permissions 600

## Related Documentation

- [README_MCP.md](../README_MCP.md) - Quick start
- [CLAUDE_DESKTOP_CONFIG.md](./CLAUDE_DESKTOP_CONFIG.md) - Claude Desktop setup
- [CLAUDE.md](../CLAUDE.md) - Общая документация проекта
- [REBUILD_PLAN.md](./REBUILD_PLAN.md) - План разработки
