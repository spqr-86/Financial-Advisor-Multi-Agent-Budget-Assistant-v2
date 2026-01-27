# Cloud MCP Setup - Удалённый доступ к MCP через Claude Desktop

## Что сделано

MCP сервис развёрнут на Google Cloud Run с поддержкой **SSE (Server-Sent Events)** транспорта для удалённого доступа через интернет.

- **URL сервиса:** https://budget-mcp-751147398264.us-central1.run.app
- **SSE endpoint:** https://budget-mcp-751147398264.us-central1.run.app/mcp/
- **Транспорт:** `both` (HTTP REST для бота + SSE для Claude Desktop)

## Конфигурация Claude Desktop

Файл конфигурации создан в:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Содержимое:
```json
{
  "mcpServers": {
    "budget-assistant": {
      "url": "https://budget-mcp-751147398264.us-central1.run.app/mcp/",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

## Как использовать

1. **Перезапустите Claude Desktop**
   - Полностью закройте приложение (Cmd+Q)
   - Откройте снова

2. **Проверьте подключение**
   - Откройте новую беседу в Claude Desktop
   - В нижней части окна должна появиться иконка 🔌 или похожая
   - Нажмите на неё - должен быть виден сервер "budget-assistant"

3. **Протестируйте**
   - Напишите: "купил хлеб 50 рублей"
   - Claude автоматически использует MCP tools для добавления расхода
   - Проверьте: "покажи последние расходы"

## Доступные MCP Tools

- **process_query(query, user_id)** - основной tool для любых запросов
- **add_expense(category, amount, description, user_id)** - добавить расход
- **get_expenses(limit, category, user_id)** - посмотреть расходы
- **get_statistics(period, user_id)** - статистика
- **delete_last_expense(user_id)** - удалить последний расход

## MCP Resources

- **budget://help** - инструкция
- **budget://categories** - список категорий

## Примеры запросов

```
Добавить расход:
- "купил хлеб 50 рублей"
- "потратил 1500 на транспорт"

Просмотр:
- "покажи последние расходы"
- "статистика за неделю"
- "сколько потратил на еду?"

Удаление:
- "удали последний расход"
```

## Troubleshooting

### Claude Desktop не видит сервер

1. Проверьте конфигурацию:
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Проверьте логи Claude Desktop:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

3. Проверьте доступность SSE endpoint:
```bash
curl -N https://budget-mcp-751147398264.us-central1.run.app/mcp/
# Должен вернуть SSE stream (нажмите Ctrl+C для выхода)
```

### MCP tools не работают

1. Проверьте логи Cloud Run:
```bash
gcloud run logs tail budget-mcp --region us-central1 --project budjet-agent
```

2. Проверьте health endpoint:
```bash
curl https://budget-mcp-751147398264.us-central1.run.app/health
```

3. Проверьте переменные окружения:
```bash
gcloud run services describe budget-mcp \
  --region us-central1 \
  --format 'value(spec.template.spec.containers[0].env)' | grep MCP_TRANSPORT
# Должно быть: MCP_TRANSPORT=both
```

### Quota exceeded (Gemini API)

Если видите ошибки quota в логах:
```bash
# Переключить модель на gemini-2.0-flash (больше лимит)
gcloud run services update budget-mcp \
  --update-env-vars "GEMINI_MODEL=gemini-2.0-flash" \
  --region us-central1 \
  --project budjet-agent
```

## Архитектура

```
Claude Desktop → SSE (HTTPS) → Cloud Run (budget-mcp) → Google Sheets
                                    ↓
                              ADKBudgetAgent
                                    ↓
                         Orchestrator → Registrar/Analyst
```

## Преимущества облачного MCP

✅ Доступ из любого места (не только локально)
✅ Не нужно запускать локальные процессы
✅ Автоматическое масштабирование
✅ Общие данные (Google Sheets) для всех клиентов
✅ Cloud Run бесплатен для лёгкого использования

## Ограничения

- **Публичный доступ:** Endpoint доступен всем (без аутентификации)
- **Quota:** Gemini API имеет лимиты на free tier
- **Latency:** Небольшая задержка из-за сетевых запросов

## Security Note

⚠️ **ВАЖНО:** Сейчас SSE endpoint публично доступен без аутентификации. Для production использования рекомендуется:
- Добавить API key аутентификацию
- Или использовать Cloud Run IAM authentication
- Или добавить rate limiting

## Следующие шаги

1. ✅ Развёрнут MCP на Cloud Run с SSE
2. ✅ Настроен Claude Desktop
3. 🔄 Протестировать работу
4. 📋 Добавить аутентификацию (опционально)
5. 📊 Настроить мониторинг использования
