# Claude Desktop Configuration для Budget Assistant

## Обзор

Этот документ описывает как настроить Budget Assistant MCP сервер для работы с Claude Desktop.

## Расположение конфигурации

Claude Desktop хранит конфигурацию MCP серверов в JSON файле:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

## Базовая конфигурация

Создайте или отредактируйте `claude_desktop_config.json`:

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

### Важно

1. **Absolute paths:** Пути должны быть абсолютными, не относительными
2. **Executable:** Скрипт должен быть исполняемым (`chmod +x`)
3. **Working directory:** `cwd` должен указывать на корень проекта

## Конфигурация с Environment Variables

Если нужно переопределить переменные окружения:

```json
{
  "mcpServers": {
    "budget-assistant": {
      "command": "/absolute/path/to/budget-assistant-v2/scripts/run_mcp_stdio.sh",
      "cwd": "/absolute/path/to/budget-assistant-v2",
      "env": {
        "GOOGLE_API_KEY": "your-api-key",
        "GOOGLE_APPLICATION_CREDENTIALS": "/absolute/path/to/service-account.json",
        "GOOGLE_SHEETS_SPREADSHEET_ID": "your-spreadsheet-id",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Примечание:** Если `.env` файл настроен правильно, секция `env` не обязательна.

## Примеры

### macOS

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

### Linux

```json
{
  "mcpServers": {
    "budget-assistant": {
      "command": "/home/user/projects/budget-assistant-v2/scripts/run_mcp_stdio.sh",
      "cwd": "/home/user/projects/budget-assistant-v2"
    }
  }
}
```

### Windows (PowerShell)

```json
{
  "mcpServers": {
    "budget-assistant": {
      "command": "C:\\Users\\User\\Projects\\budget-assistant-v2\\scripts\\run_mcp_stdio.sh",
      "cwd": "C:\\Users\\User\\Projects\\budget-assistant-v2"
    }
  }
}
```

## Проверка конфигурации

### 1. Проверить что скрипт работает

```bash
/absolute/path/to/budget-assistant-v2/scripts/run_mcp_stdio.sh
```

Должен запуститься MCP сервер в stdio режиме.

### 2. Проверить логи Claude Desktop

- **macOS:** `~/Library/Logs/Claude/mcp-server-budget-assistant.log`
- **Windows:** `%APPDATA%\Claude\Logs\mcp-server-budget-assistant.log`
- **Linux:** `~/.config/Claude/logs/mcp-server-budget-assistant.log`

### 3. Проверить что tool доступен

1. Откройте Claude Desktop
2. Создайте новую беседу
3. Напишите: "купил хлеб 50 рублей"
4. Claude должен использовать `process_query` tool

## Множественные MCP серверы

Можно добавить несколько MCP серверов:

```json
{
  "mcpServers": {
    "budget-assistant": {
      "command": "/path/to/budget-assistant-v2/scripts/run_mcp_stdio.sh",
      "cwd": "/path/to/budget-assistant-v2"
    },
    "another-server": {
      "command": "/path/to/another-server/run.sh",
      "cwd": "/path/to/another-server"
    }
  }
}
```

## Troubleshooting

### Сервер не запускается

**Проблема:** Claude Desktop не видит MCP сервер

**Решения:**
1. Проверьте absolute paths в конфигурации
2. Убедитесь что скрипт исполняемый: `ls -l scripts/run_mcp_stdio.sh`
3. Проверьте что poetry установлен и доступен в PATH
4. Перезапустите Claude Desktop

### Tools не появляются

**Проблема:** Tools не отображаются в Claude Desktop

**Решения:**
1. Проверьте логи MCP сервера
2. Убедитесь что `.env` файл настроен правильно
3. Проверьте что Google Sheets credentials валидные
4. Попробуйте запустить сервер вручную для диагностики

### Ошибки выполнения

**Проблема:** Tools выполняются с ошибками

**Решения:**
1. Проверьте `GOOGLE_API_KEY` - валидный ли
2. Проверьте `GOOGLE_APPLICATION_CREDENTIALS` - файл существует
3. Проверьте `GOOGLE_SHEETS_SPREADSHEET_ID` - правильный ли
4. Проверьте квоту Gemini API: https://ai.google.dev/

### Логи не создаются

**Проблема:** Логи отсутствуют

**Решение:**
- Логи создаются Claude Desktop автоматически
- Если их нет - возможно сервер не запускается вообще
- Проверьте запуск скрипта вручную

## Дополнительные настройки

### Изменить уровень логирования

В секции `env`:

```json
"env": {
  "LOG_LEVEL": "DEBUG"
}
```

### Использовать другой Gemini model

```json
"env": {
  "GEMINI_MODEL": "gemini-2.5-flash"
}
```

### Указать другой transport (для тестирования)

**Примечание:** Для Claude Desktop используйте только `stdio`!

```json
"env": {
  "MCP_TRANSPORT": "stdio"
}
```

## Полезные ссылки

- [Claude Desktop MCP Documentation](https://docs.claude.com/en/docs/mcp)
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18)
- [Budget Assistant README_MCP.md](../README_MCP.md)
- [Budget Assistant MCP_SERVER.md](./MCP_SERVER.md)
