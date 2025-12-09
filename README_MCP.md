# Budget Assistant MCP Server - Quick Start

## Что это?

Budget Assistant теперь доступен как MCP (Model Context Protocol) сервер, что позволяет использовать его прямо из Claude Desktop!

## Быстрая настройка

### 1. Установка зависимостей

```bash
cd budget-assistant-v2
poetry install
```

### 2. Настройка переменных окружения

Создайте `.env` файл:

```env
GOOGLE_API_KEY=your-gemini-api-key
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id
```

### 3. Конфигурация Claude Desktop

Откройте файл конфигурации Claude Desktop:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Добавьте:

```json
{
  "mcpServers": {
    "budget-assistant": {
      "command": "/full/path/to/budget-assistant-v2/scripts/run_mcp_stdio.sh",
      "cwd": "/full/path/to/budget-assistant-v2"
    }
  }
}
```

**Важно:** Замените `/full/path/to/` на реальный absolute путь к проекту!

**macOS пример:**
```json
{
  "mcpServers": {
    "budget-assistant": {
      "command": "/Users/petrbaldaev/Dev/budget-assistant-v2/scripts/run_mcp_stdio.sh",
      "cwd": "/Users/petrbaldaev/Dev/budget-assistant-v2"
    }
  }
}
```

### 4. Сделать скрипт исполняемым

```bash
chmod +x scripts/run_mcp_stdio.sh
```

### 5. Перезапустить Claude Desktop

Полностью закройте и откройте заново Claude Desktop.

### 6. Готово!

Теперь в Claude Desktop можно писать:
- "купил хлеб 50 рублей" - добавит расход
- "покажи мои расходы" - покажет последние траты
- "статистика за месяц" - выведет аналитику
- "удали последний расход" - удалит ошибочную запись

Claude автоматически будет использовать Budget Assistant tool.

## Проверка работы

1. Откройте новую беседу в Claude Desktop
2. Напишите: "купил хлеб 50 рублей"
3. Claude должен ответить что-то вроде: "Отлично! Я добавил расход..."

## Troubleshooting

### Ошибка: "command not found"
```bash
# Сделайте скрипт исполняемым:
chmod +x scripts/run_mcp_stdio.sh
```

### Tool не появляется в Claude
- Проверьте пути в конфигурации (должны быть абсолютные)
- Убедитесь что скрипт исполняемый
- Перезапустите Claude Desktop

### Ошибки при выполнении
- Проверьте логи: `~/Library/Logs/Claude/mcp-server-budget-assistant.log` (macOS)
- Убедитесь что все env переменные установлены
- Проверьте что service-account.json существует

### Telegram Bot перестал работать?
Не должен! HTTP REST API сохранен для Bot. Если Bot не работает - это отдельная проблема, не связанная с MCP сервером.

## Дополнительные возможности

### Тестирование с MCP Inspector

```bash
./scripts/test_mcp_inspector.sh
# Откройте: npx @modelcontextprotocol/inspector
# Подключитесь к: http://localhost:8083/mcp/sse
```

### Доступные Tools

- **process_query** - основной tool, обрабатывает любой запрос через AI
- **add_expense** - прямое добавление расхода (без AI)
- **get_expenses** - просмотр расходов
- **get_statistics** - статистика
- **delete_last_expense** - удаление последнего расхода

### Resources

- **budget://help** - инструкция по использованию
- **budget://categories** - список категорий расходов

## Полная документация

- `docs/MCP_SERVER.md` - полное руководство
- `docs/CLAUDE_DESKTOP_CONFIG.md` - детальная инструкция по настройке
- `CLAUDE.md` - общая документация проекта

## Нужна помощь?

Создайте issue на GitHub или обратитесь к документации в `docs/`.
