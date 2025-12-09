# 🧪 Тестирование Budget Assistant v2.0

Полная инструкция по автоматическому и ручному тестированию проекта.

---

## 📊 Текущее состояние

- **Всего тестов:** 48
- **Покрытие:** 82.90%
- **Статус:** ✅ Все тесты проходят
- **CI/CD:** GitHub Actions автоматически запускает тесты

---

## 1. Автоматическое тестирование

### 1.1 Запуск всех тестов

```bash
# Запустить все тесты
poetry run pytest

# Быстрый запуск (без coverage)
poetry run pytest -q

# С подробным выводом
poetry run pytest -v

# Конкретный файл
poetry run pytest tests/test_core/test_schemas.py

# Конкретный тест
poetry run pytest tests/test_core/test_schemas.py::test_query_request_valid
```

### 1.2 Coverage (покрытие кода)

```bash
# С отчетом в консоли
poetry run pytest --cov=src --cov-report=term-missing

# Сгенерировать HTML отчет
poetry run pytest --cov=src --cov-report=html

# Открыть HTML отчет
open htmlcov/index.html

# С минимальным порогом (fail если меньше 50%)
poetry run pytest --cov=src --cov-fail-under=50
```

### 1.3 Структура тестов

```
tests/
├── conftest.py              # Общие fixtures
├── test_core/               # Тесты ядра (100% coverage)
│   ├── test_schemas.py      # Pydantic модели
│   ├── test_exceptions.py   # Исключения
│   └── test_http_client.py  # HTTP клиент
├── test_api/                # Тесты API Gateway
│   └── test_app.py          # Endpoints + health
├── test_mcp/                # Тесты MCP Service
│   └── test_app.py          # Endpoints + health
└── test_bot/                # Тесты Telegram бота
    ├── test_handlers.py     # Обработчики сообщений
    └── test_middlewares.py  # Middleware компоненты
```

### 1.4 Детальное покрытие

| Модуль | Тесты | Coverage | Статус |
|--------|-------|----------|--------|
| **Core** | | | |
| `src/core/schemas.py` | 8 | 100% | ✅ |
| `src/core/exceptions.py` | 8 | 100% | ✅ |
| `src/core/http_client.py` | 10 | 98% | ✅ |
| `src/core/config.py` | - | 91% | ✅ |
| **Bot** | | | |
| `src/bot/handlers/` | 8 | 100% | ✅ |
| `src/bot/middlewares/` | 9 | 100% | ✅ |
| `src/bot/app.py` | - | 0% | ⚠️ (требует Telegram) |
| **API Gateway** | | | |
| `src/api/app.py` | 3 | 76% | ✅ |
| `src/api/routes/` | 3 | 100% | ✅ |
| **MCP Service** | | | |
| `src/mcp/app.py` | 2 | 86% | ✅ |
| `src/mcp/routes/` | 2 | 100% | ✅ |

---

## 2. Ручное тестирование

### 2.1 Локальный запуск сервисов

#### Вариант 1: С .env файлом (рекомендуется для разработки)

**Шаг 1: Создать .env файл**
```bash
cp .env.example .env
# Заполнить обязательные поля:
# - TELEGRAM_BOT_TOKEN (из @BotFather)
# - GOOGLE_API_KEY (для Gemini)
```

**Шаг 2: Запустить сервисы в 3 терминалах**

**Терминал 1 — MCP Service (порт 8082):**
```bash
poetry run python -m src.mcp.app
```

**Терминал 2 — API Gateway (порт 8081):**
```bash
poetry run python -m src.api.app
```

**Терминал 3 — Telegram Bot (polling режим):**
```bash
poetry run python -m src.bot.run_polling
```

**Важно:** Используйте `src.bot.run_polling` для локальной разработки. Файл `src.bot.app` работает только в webhook режиме (для продакшена с публичным URL).

#### Вариант 2: С переменными окружения

**Терминал 1 — MCP Service (порт 8082):**
```bash
poetry run python -m src.mcp.app
```

**Терминал 2 — API Gateway (порт 8081):**
```bash
export MCP_API_URL=http://localhost:8082
poetry run python -m src.api.app
```

**Терминал 3 — Telegram Bot (polling режим):**
```bash
export TELEGRAM_BOT_TOKEN=your-token
export BUDGET_API_URL=http://localhost:8081
poetry run python -m src.bot.run_polling
```

#### Вариант 3: Docker Compose (будет добавлено)

```bash
docker-compose up
```

### 2.2 Проверка health endpoints

```bash
# MCP Service
curl http://localhost:8082/health
# Ожидается: {"status":"healthy","service":"mcp","version":"2.0.0"}

# API Gateway
curl http://localhost:8081/health
# Ожидается: {"status":"healthy","service":"api-gateway","version":"2.0.0","dependencies":{"mcp":true}}

# Bot
curl http://localhost:8080/health
# Ожидается: {"status":"healthy","service":"bot","version":"2.0.0"}
```

### 2.3 Тестирование цепочки Bot → API → MCP

#### Тест 1: Прямой вызов MCP
```bash
curl -X POST http://localhost:8082/mcp/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "тестовый запрос",
    "user_id": "123"
  }'

# Ожидается: {"response":"MCP Echo: тестовый запрос","user_id":"123","session_id":"123"}
```

#### Тест 2: Через API Gateway
```bash
curl -X POST http://localhost:8081/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "проверка API Gateway",
    "user_id": "456"
  }'

# Ожидается: {"response":"MCP Echo: проверка API Gateway","user_id":"456","session_id":"456"}
```

#### Тест 3: Telegram бот

Для этого нужен настроенный бот:

1. Получить токен от [@BotFather](https://t.me/BotFather)
2. Установить переменную:
   ```bash
   export TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```
3. Запустить бота (терминал 3)
4. Написать боту в Telegram:
   - `/start` — проверка приветствия
   - `test message` — проверка обработки текста

### 2.4 Проверка обработки ошибок

#### Тест: MCP недоступен

```bash
# Остановить MCP (Ctrl+C в терминале 1)

# Проверить API health (должен быть degraded)
curl http://localhost:8081/health
# Ожидается: {"status":"degraded","service":"api-gateway","version":"2.0.0","dependencies":{"mcp":false}}

# Попробовать запрос (должна быть ошибка)
curl -X POST http://localhost:8081/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "user_id": "123"}'
# Ожидается: {"error":"Service temporarily unavailable","code":"SERVICE_UNAVAILABLE"}
```

#### Тест: Невалидные данные

```bash
# Пустой query
curl -X POST http://localhost:8081/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "", "user_id": "123"}'
# Ожидается: 422 Validation Error

# Нет user_id
curl -X POST http://localhost:8081/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
# Ожидается: 422 Validation Error
```

### 2.5 Проверка middleware

#### Тест: Rate Limiting

Отправить 11 сообщений боту подряд за минуту:
- Первые 10 — обработаются
- 11-е — получим "Подождите минуту..."

#### Тест: Access Control

```bash
# Добавить в .env:
TELEGRAM_ADMIN_IDS=123456789

# Запустить бота
# Попробовать написать с другого аккаунта → "Доступ ограничен"
```

---

## 3. Сценарии тестирования

### 3.1 Перед коммитом

```bash
# 1. Проверить линтер
poetry run ruff check src/

# 2. Запустить тесты
poetry run pytest

# 3. Проверить coverage
poetry run pytest --cov=src --cov-fail-under=50

# 4. Проверить типы (опционально)
# poetry run mypy src/
```

### 3.2 Перед деплоем на Cloud Run

```bash
# 1. Собрать Docker образы
docker build -f docker/Dockerfile.mcp -t budget-mcp .
docker build -f docker/Dockerfile.api -t budget-api .
docker build -f docker/Dockerfile.bot -t budget-bot .

# 2. Запустить контейнеры локально
docker run -p 8082:8082 -e GOOGLE_API_KEY=test budget-mcp
docker run -p 8081:8081 -e MCP_API_URL=http://host.docker.internal:8082 budget-api
docker run -p 8080:8080 -e BUDGET_API_URL=http://host.docker.internal:8081 -e TELEGRAM_BOT_TOKEN=test budget-bot

# 3. Проверить health endpoints
curl http://localhost:8082/health
curl http://localhost:8081/health
curl http://localhost:8080/health

# 4. Проверить логи
docker logs <container_id>
```

### 3.3 После деплоя на Cloud Run

```bash
# 1. Получить URL сервисов
export MCP_URL=$(gcloud run services describe budget-mcp --region us-central1 --format 'value(status.url)')
export API_URL=$(gcloud run services describe budget-api --region us-central1 --format 'value(status.url)')
export BOT_URL=$(gcloud run services describe budget-bot --region us-central1 --format 'value(status.url)')

# 2. Проверить health
curl $MCP_URL/health
curl $API_URL/health
curl $BOT_URL/health

# 3. Проверить логи
gcloud run services logs read budget-mcp --region us-central1 --limit 50
gcloud run services logs read budget-api --region us-central1 --limit 50
gcloud run services logs read budget-bot --region us-central1 --limit 50

# 4. Тест через Telegram
# Написать боту /start и проверить ответ
```

---

## 4. Smoke тесты для Production

### 4.1 Базовые проверки

| # | Проверка | Команда | Ожидаемый результат |
|---|----------|---------|---------------------|
| 1 | MCP health | `curl $MCP_URL/health` | `{"status":"healthy"}` |
| 2 | API health | `curl $API_URL/health` | `{"status":"healthy","dependencies":{"mcp":true}}` |
| 3 | Bot health | `curl $BOT_URL/health` | `{"status":"healthy"}` |
| 4 | Bot /start | Написать `/start` в Telegram | Получить приветствие |
| 5 | Echo message | Написать `test` в Telegram | Получить `MCP Echo: test` |

### 4.2 Функциональные проверки (после Итерации 5-7)

| # | Проверка | Действие | Ожидаемый результат |
|---|----------|----------|---------------------|
| 6 | Добавление расхода | `купил хлеб 50` | Расход добавлен в Google Sheets |
| 7 | Просмотр расходов | `покажи расходы` | Список последних расходов |
| 8 | Статистика | `статистика за месяц` | Таблица по категориям |
| 9 | Совет | `дай совет` | AI совет по экономии |
| 10 | Rate limit | 11 запросов подряд | 11-й заблокирован |

---

## 5. CI/CD (GitHub Actions)

### 5.1 Автоматические проверки

При каждом push/PR:
- ✅ Ruff линтинг
- ✅ Pytest с минимум 50% coverage
- ✅ Проверка на Python 3.11

### 5.2 Просмотр результатов

```bash
# В GitHub UI
https://github.com/your-repo/actions

# Или через CLI
gh run list
gh run view <run-id>
```

---

## 6. Troubleshooting

### Проблема: Тесты не запускаются

```bash
# Переустановить зависимости
poetry install

# Очистить кеш
poetry cache clear . --all
rm -rf .pytest_cache htmlcov .coverage
```

### Проблема: ModuleNotFoundError

```bash
# Убедиться что src в PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Или использовать poetry
poetry run pytest
```

### Проблема: Тесты падают с "Token is invalid"

```bash
# Установить тестовый токен
export TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

### Проблема: Coverage меньше 50%

```bash
# Посмотреть какие файлы не покрыты
poetry run pytest --cov=src --cov-report=term-missing

# Посмотреть HTML отчет
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 7. Best Practices

### 7.1 Написание тестов

✅ **DO:**
- Один тест = одна проверка
- Использовать fixtures для переиспользования
- Моковать внешние сервисы (HTTP, DB)
- Называть тесты понятно: `test_<что>_<условие>`

❌ **DON'T:**
- Тесты зависящие от порядка выполнения
- Тесты зависящие от внешних сервисов
- Тесты без assert

### 7.2 Пример хорошего теста

```python
@pytest.mark.asyncio
async def test_query_request_with_session():
    """Test QueryRequest with session_id."""
    # Arrange
    req = QueryRequest(
        query="test",
        user_id="123",
        session_id="session_123"
    )

    # Act & Assert
    assert req.session_id == "session_123"
```

---

## 8. Чеклист перед release

- [ ] Все тесты проходят: `poetry run pytest`
- [ ] Coverage >= 50%: `poetry run pytest --cov=src --cov-fail-under=50`
- [ ] Линтер без ошибок: `poetry run ruff check src/`
- [ ] Docker образы собираются без ошибок
- [ ] Локальное тестирование цепочки Bot → API → MCP
- [ ] Health endpoints возвращают 200 OK
- [ ] Обновлен CHANGELOG.md
- [ ] Обновлен README.md
- [ ] Git tag создан: `git tag v2.0.0`
