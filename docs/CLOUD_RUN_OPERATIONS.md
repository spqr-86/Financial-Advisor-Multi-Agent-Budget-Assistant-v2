# Cloud Run Operations Guide

Руководство по управлению Budget Assistant v2 в Google Cloud Run.

## Содержание

- [Переменные окружения](#переменные-окружения)
- [Просмотр логов](#просмотр-логов)
- [Управление сервисами](#управление-сервисами)
- [Замена модели Gemini](#замена-модели-gemini)
- [Работа с секретами](#работа-с-секретами)
- [Мониторинг и диагностика](#мониторинг-и-диагностика)
- [Откат изменений](#откат-изменений)

---

## Переменные окружения

Установите переменные для всех команд:

```bash
export GCP_PROJECT_ID=budjet-agent
export GCP_REGION=us-central1
```

Добавьте в `~/.bashrc` или `~/.zshrc` для постоянного использования:

```bash
echo 'export GCP_PROJECT_ID=budjet-agent' >> ~/.zshrc
echo 'export GCP_REGION=us-central1' >> ~/.zshrc
source ~/.zshrc
```

---

## Просмотр логов

### Последние логи сервиса

```bash
# MCP Service (AI и Google Sheets)
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=50

# API Gateway
gcloud run services logs read budget-api \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=50

# Telegram Bot
gcloud run services logs read budget-bot \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=50
```

### Логи в реальном времени (tail)

```bash
# Следить за логами MCP в реальном времени
gcloud run services logs tail budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}

# Ctrl+C для остановки
```

### Поиск по логам

```bash
# Ошибки в MCP
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=100 | grep -i "error\|exception\|failed"

# Проблемы с квотой Gemini
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=100 | grep -i "quota\|exhausted\|429"

# Проблемы с Google Sheets
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=100 | grep -i "worksheet\|spreadsheet\|sheets"

# Успешные добавления расходов
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=50 | grep "AI added expense"
```

### Логи за период времени

```bash
# Логи за последний час
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=200 \
    --format="table(timestamp,severity,textPayload)"
```

---

## Управление сервисами

### Список всех сервисов

```bash
gcloud run services list \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}
```

### Детальная информация о сервисе

```bash
# Полная конфигурация MCP
gcloud run services describe budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}

# Только URL
gcloud run services describe budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --format='value(status.url)'
```

### Проверка здоровья сервисов

```bash
# Получить URL всех сервисов
MCP_URL=$(gcloud run services describe budget-mcp --region ${GCP_REGION} --format 'value(status.url)' --project ${GCP_PROJECT_ID})
API_URL=$(gcloud run services describe budget-api --region ${GCP_REGION} --format 'value(status.url)' --project ${GCP_PROJECT_ID})
BOT_URL=$(gcloud run services describe budget-bot --region ${GCP_REGION} --format 'value(status.url)' --project ${GCP_PROJECT_ID})

# Проверить health endpoints
curl ${MCP_URL}/health
curl ${API_URL}/health
curl ${BOT_URL}/health
```

### Список ревизий (версий)

```bash
# Все ревизии MCP сервиса
gcloud run revisions list \
    --service=budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}

# Показать какая ревизия получает трафик
gcloud run services describe budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --format='table(status.traffic)'
```

---

## Замена модели Gemini

### Быстрая замена модели

**Когда нужно:** Превышена квота текущей модели (429 RESOURCE_EXHAUSTED)

```bash
# Узнать текущую модель
gcloud run services describe budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --format='value(spec.template.spec.containers[0].env[?(@.name=="GEMINI_MODEL")].value)'

# Заменить на gemini-2.0-flash (рекомендуется)
gcloud run services update budget-mcp \
    --update-env-vars "GEMINI_MODEL=gemini-2.0-flash" \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}
```

### Доступные модели

| Модель | Free Tier Quota | Рекомендация |
|--------|----------------|--------------|
| `gemini-2.0-flash` | 15 req/min | ✅ **Рекомендуется** |
| `gemini-2.5-flash` | 5 req/min | ⚠️ Слишком низкая квота |
| `gemini-flash-latest` | Зависит от версии | ⚠️ Может меняться |

### Проверка результата

```bash
# Дождитесь завершения деплоя (1-2 минуты)
# Проверьте логи на наличие новой модели
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=10 | grep "model:"
```

---

## Работа с секретами

### Список секретов

```bash
gcloud secrets list --project=${GCP_PROJECT_ID}
```

### Просмотр версий секрета

```bash
# Показать все версии секрета
gcloud secrets versions list google-api-key \
    --project=${GCP_PROJECT_ID}
```

### Обновление секрета

```bash
# Обновить Telegram bot token
printf "NEW_TOKEN_VALUE" > /tmp/new-token.txt
gcloud secrets versions add telegram-bot-token \
    --data-file=/tmp/new-token.txt \
    --project=${GCP_PROJECT_ID}
rm /tmp/new-token.txt

# Перезапустить сервис для применения нового секрета
gcloud run services update budget-bot \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}
```

### Чтение значения секрета (для отладки)

```bash
# Прочитать актуальное значение (осторожно - показывает в терминале!)
gcloud secrets versions access latest \
    --secret=google-api-key \
    --project=${GCP_PROJECT_ID}
```

---

## Мониторинг и диагностика

### Webhook статус (Telegram)

```bash
# Получить текущую конфигурацию webhook
BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token --project=${GCP_PROJECT_ID})
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo" | jq .

# Проверить что webhook указывает на правильный URL
# Должен быть: https://budget-bot-*.run.app/webhook
```

### Проверка Google Sheets доступа

```bash
# Получить email service account
cat service-account.json | jq -r .client_email

# Убедитесь что этот email имеет доступ к таблице (Editor)
# Откройте Google Sheets → Share → проверьте наличие budget-bot@...iam.gserviceaccount.com
```

### Метрики и использование ресурсов

```bash
# Открыть Cloud Run в консоли
echo "https://console.cloud.google.com/run?project=${GCP_PROJECT_ID}"

# В консоли можно посмотреть:
# - Количество запросов
# - Latency (время ответа)
# - Использование памяти/CPU
# - Количество холодных стартов
```

### Проверка квоты Gemini API

```bash
# Логи с ошибками квоты за последний час
gcloud run services logs read budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION} \
    --limit=200 | grep -A 3 "RESOURCE_EXHAUSTED"

# Если видите много ошибок 429 - смените модель (см. раздел выше)
```

---

## Откат изменений

### Откат на предыдущую ревизию

```bash
# 1. Получить список ревизий
gcloud run revisions list \
    --service=budget-mcp \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}

# 2. Откатиться на конкретную ревизию (замените REVISION_NAME)
gcloud run services update-traffic budget-mcp \
    --to-revisions=REVISION_NAME=100 \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}

# Пример:
# gcloud run services update-traffic budget-mcp \
#     --to-revisions=budget-mcp-00007-abc=100 \
#     --project=${GCP_PROJECT_ID} \
#     --region=${GCP_REGION}
```

### Откат через повторный деплой

```bash
# Вернуться к конкретному коммиту и задеплоить
git checkout <commit-hash>
./scripts/deploy_mcp.sh  # или deploy_all.sh
git checkout dev  # вернуться обратно
```

---

## Настройка удалённого MCP (SSE)

### Включить SSE endpoint для Claude Desktop

**Когда нужно:** Хотите использовать MCP через интернет (Claude Desktop без локального запуска)

```bash
# Обновить MCP сервис для поддержки SSE
gcloud run services update budget-mcp \
    --update-env-vars "MCP_TRANSPORT=both" \
    --project=${GCP_PROJECT_ID} \
    --region=${GCP_REGION}

# Получить URL SSE endpoint
MCP_URL=$(gcloud run services describe budget-mcp --region ${GCP_REGION} --format 'value(status.url)' --project ${GCP_PROJECT_ID})
echo "${MCP_URL}/mcp/"
```

### Настроить Claude Desktop для удалённого MCP

Создайте/отредактируйте `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "budget-assistant": {
      "url": "https://budget-mcp-xxx.run.app/mcp/",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

Замените URL на ваш реальный Cloud Run URL.

**Перезапустите Claude Desktop** для применения изменений.

**См. также:** `docs/CLOUD_MCP_SETUP.md` для полной инструкции.

---

## Быстрые команды (cheatsheet)

```bash
# Настройка переменных
export GCP_PROJECT_ID=budjet-agent
export GCP_REGION=us-central1

# Смотреть логи в реальном времени
gcloud run services logs tail budget-mcp --project=${GCP_PROJECT_ID} --region=${GCP_REGION}

# Проверить здоровье
curl $(gcloud run services describe budget-mcp --region ${GCP_REGION} --format 'value(status.url)' --project ${GCP_PROJECT_ID})/health

# Сменить модель Gemini
gcloud run services update budget-mcp --update-env-vars "GEMINI_MODEL=gemini-2.0-flash" --project=${GCP_PROJECT_ID} --region=${GCP_REGION}

# Перезапустить сервис
gcloud run services update budget-mcp --project=${GCP_PROJECT_ID} --region=${GCP_REGION}

# Список сервисов
gcloud run services list --project=${GCP_PROJECT_ID} --region=${GCP_REGION}

# Посмотреть ошибки
gcloud run services logs read budget-mcp --project=${GCP_PROJECT_ID} --region=${GCP_REGION} --limit=50 | grep -i error
```

---

## Полезные ссылки

- **Cloud Run Console**: https://console.cloud.google.com/run?project=budjet-agent
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager?project=budjet-agent
- **Cloud Logging**: https://console.cloud.google.com/logs?project=budjet-agent
- **Gemini API Quotas**: https://ai.google.dev/gemini-api/docs/rate-limits
- **Container Registry**: https://console.cloud.google.com/gcr/images/budjet-agent

---

## Получение помощи

При возникновении проблем:

1. **Проверьте логи** всех трех сервисов
2. **Проверьте health endpoints** (curl /health)
3. **Проверьте webhook** (для проблем с Telegram)
4. **Проверьте квоту Gemini** (при ошибках добавления расходов)
5. **Проверьте Google Sheets доступ** (service account email должен быть в Share)

Если проблема не решается - смотрите раздел Troubleshooting в `CLAUDE.md`.
