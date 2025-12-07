# 📘 Руководство по коду Budget Assistant v2.0

> Объяснение архитектуры и текущего состояния проекта для начинающих

---

## 🎯 Что это за проект?

**Budget Assistant** — это Telegram-бот для учета расходов и финансовых советов на основе AI.

Пользователь пишет боту "купил хлеб 50 руб", а бот:
1. Записывает расход в Google Sheets
2. Анализирует паттерны трат
3. Дает персонализированные советы по экономии

---

## 🏗️ Архитектура: 3 независимых сервиса

Представьте ресторан с тремя отделами:

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Telegram  │      │              │      │             │
│     Bot     │─────▶│ API Gateway  │─────▶│ MCP Service │
│  (официант) │      │  (менеджер)  │      │   (повар)   │
│   :8080     │      │    :8081     │      │    :8082    │
└─────────────┘      └──────────────┘      └─────────────┘
```

### 1️⃣ **Telegram Bot** (порт 8080) — Официант

**Что делает:**
- Принимает сообщения от пользователей в Telegram
- Показывает "печатает..." пока обрабатывается запрос
- Отправляет ответы обратно пользователю

**Файлы:**
- `src/bot/app.py` — главный файл, запускает бота
- `src/bot/handlers/` — обработчики команд (/start, текстовые сообщения)
- `src/bot/middlewares/` — "фильтры" для проверок (rate limiting, доступ)
- `src/bot/config.py` — настройки (токен бота, URL API)

**Простыми словами:**
Когда вы пишете "/start" в Telegram, бот:
1. Проверяет, не спамите ли вы (RateLimitMiddleware)
2. Проверяет, есть ли у вас доступ (AccessControlMiddleware)
3. Вызывает функцию `cmd_start()` из handlers
4. Отправляет приветственное сообщение

### 2️⃣ **API Gateway** (порт 8081) — Менеджер

**Что делает:**
- Принимает запросы от бота
- Проверяет данные (валидация)
- Перенаправляет на MCP Service
- Обрабатывает ошибки

**Файлы:**
- `src/api/app.py` — FastAPI приложение
- `src/api/routes/` — endpoints (URL-адреса для запросов)
- `src/api/config.py` — настройки (URL MCP сервиса)

**Простыми словами:**
Когда бот отправляет `{"query": "купил хлеб 50", "user_id": "123"}`:
1. API Gateway проверяет формат (есть ли query? есть ли user_id?)
2. Отправляет запрос в MCP Service
3. Получает ответ и возвращает боту
4. Если MCP недоступен, возвращает ошибку "Service unavailable"

### 3️⃣ **MCP Service** (порт 8082) — Повар

**Что делает:**
- Обрабатывает запросы с помощью AI (Google Gemini)
- Работает с Google Sheets (в будущем)
- Логика обработки расходов и советов

**Файлы:**
- `src/mcp/app.py` — FastAPI приложение
- `src/mcp/routes/` — endpoints
- `src/mcp/config.py` — настройки (Google API ключ)
- `prompts/` — промпты для AI (пока не используются)

**Простыми словами:**
Сейчас MCP просто отвечает "MCP Echo: [ваш текст]" для тестирования.
В будущем он будет:
1. Распознавать расходы ("купил хлеб 50" → категория "Еда", сумма 50)
2. Записывать в Google Sheets
3. Генерировать AI советы

---

## 🧩 Общие компоненты (src/core/)

Это "библиотека" общих инструментов, которую используют все 3 сервиса:

### `src/core/config.py` — Базовые настройки

```python
class BaseAppSettings(BaseSettings):
    log_level: str = "INFO"          # Уровень логирования
    environment: str = "development"  # Окружение (dev/prod)
```

Каждый сервис наследует эти настройки и добавляет свои.

### `src/core/schemas.py` — Форматы данных

**Pydantic модели** — это как "формы" для проверки данных.

```python
class QueryRequest(BaseModel):
    query: str       # Текст сообщения (минимум 1 символ)
    user_id: str     # ID пользователя (обязательно)
    session_id: str | None = None  # ID сессии (опционально)
```

Если вы отправите пустой `query=""`, Pydantic вернет ошибку валидации.

### `src/core/exceptions.py` — Обработка ошибок

Вместо непонятных ошибок Python, мы возвращаем красивые JSON:

```python
raise ServiceUnavailableError()
# Вернет: {"error": "Service temporarily unavailable", "code": "SERVICE_UNAVAILABLE"}
```

### `src/core/http_client.py` — HTTP клиент с retry

**ServiceClient** — это "почтальон" между сервисами.

```python
client = ServiceClient("http://localhost:8082")
response = await client.post("/mcp/query", json={"query": "test"})
```

Если запрос упал, он автоматически повторит попытку 3 раза с паузами.

---

## 🧪 Тестирование

### Что уже протестировано?

**48 тестов, покрытие 82.90%**

```
✅ Core (100%) — schemas, exceptions, http_client
✅ Bot handlers (100%) — /start, текстовые сообщения
✅ Bot middlewares (100%) — rate limiting, access control
✅ API Gateway (76%) — endpoints, health checks
✅ MCP Service (86%) — endpoints, health checks
```

### Как запустить тесты?

```bash
# Все тесты
poetry run pytest

# С покрытием
poetry run pytest --cov=src --cov-report=term-missing

# HTML отчет
poetry run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Пример теста

```python
@pytest.mark.asyncio
async def test_cmd_start_success(mock_message):
    """Тест команды /start с валидным пользователем."""
    await cmd_start(mock_message)

    # Проверяем, что бот отправил ответ
    mock_message.answer.assert_called_once()

    # Проверяем, что в ответе есть имя пользователя
    call_args = mock_message.answer.call_args[0][0]
    assert "TestUser" in call_args
```

**Что это делает:**
1. Создает поддельное сообщение от пользователя
2. Вызывает функцию `cmd_start()`
3. Проверяет, что бот отправил приветствие с именем

---

## 📦 Зависимости (pyproject.toml)

### Основные библиотеки:

```toml
[tool.poetry.dependencies]
python = "^3.11"                    # Python версии 3.11+
fastapi = "^0.115.6"               # Веб-фреймворк для API
uvicorn = {extras = ["standard"]}  # ASGI сервер для запуска FastAPI
aiogram = "^3.16.0"                # Telegram Bot API
pydantic = "^2.10.5"               # Валидация данных
pydantic-settings = "^2.1.0"       # Настройки из .env
aiohttp = "^3.11.11"               # Асинхронный HTTP клиент
```

### Для разработки:

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"           # Тестирование
pytest-asyncio = "^0.23.8"  # Асинхронные тесты
pytest-cov = "^4.1.0"       # Покрытие кода
ruff = "^0.8.5"             # Линтер (проверка стиля)
httpx = "^0.28.1"           # HTTP клиент для тестов
```

---

## 🚀 Нужно ли деплоить сейчас?

### ❌ **НЕТ, не деплоим на продакшен!**

### Почему рано деплоить?

**Текущий статус: Итерация 4 из 10 завершена**

#### ✅ Что УЖЕ работает:

1. **Базовая инфраструктура**
   - ✅ Архитектура 3 сервисов настроена
   - ✅ HTTP клиент с retry логикой
   - ✅ Обработка ошибок
   - ✅ Валидация данных (Pydantic)
   - ✅ Health endpoints для мониторинга

2. **Telegram Bot**
   - ✅ Команда /start
   - ✅ Обработка текстовых сообщений
   - ✅ Rate limiting (защита от спама)
   - ✅ Access control (список разрешенных пользователей)
   - ✅ Middleware для проверок

3. **API Gateway**
   - ✅ Endpoint `/api/query`
   - ✅ Health check с проверкой MCP
   - ✅ Валидация запросов
   - ✅ Обработка ошибок от MCP

4. **MCP Service**
   - ✅ Endpoint `/mcp/query` (echo режим)
   - ✅ Health check
   - ✅ Базовая структура

5. **Тестирование**
   - ✅ 48 тестов, покрытие 82.90%
   - ✅ CI/CD в GitHub Actions

#### ❌ Что НЕ работает (критично):

1. **Google Sheets интеграция** ⚠️
   - ❌ Нет сохранения расходов
   - ❌ Нет чтения истории
   - → Без этого бот бесполезен!

2. **AI обработка** ⚠️
   - ❌ Google Gemini не подключен
   - ❌ Нет распознавания расходов
   - ❌ Нет генерации советов
   - → Сейчас бот просто эхо, а не помощник

3. **Продакшен настройки** ⚠️
   - ❌ Нет Docker Compose для деплоя
   - ❌ Нет конфигурации для Cloud Run
   - ❌ Нет мониторинга и логирования
   - ❌ Нет обработки секретов

### Что можно деплоить для ТЕСТИРОВАНИЯ?

Вы МОЖЕТЕ развернуть для локального/staging тестирования, чтобы:

✅ **Проверить работу цепочки Bot → API → MCP**
✅ **Протестировать webhook от Telegram**
✅ **Проверить работу в облаке (Cloud Run)**

### Как протестировать локально?

#### Вариант 1: С файлом .env (рекомендуется)

```bash
# 1. Создать .env файл (если еще нет)
cp .env.example .env
# Заполнить TELEGRAM_BOT_TOKEN и GOOGLE_API_KEY

# 2. Запустить сервисы в 3 терминалах:

# Терминал 1 - MCP Service
poetry run python -m src.mcp.app

# Терминал 2 - API Gateway
poetry run python -m src.api.app

# Терминал 3 - Telegram Bot (polling режим для разработки)
poetry run python -m src.bot.run_polling
```

#### Вариант 2: С переменными окружения

```bash
# Терминал 1 - MCP Service
poetry run python -m src.mcp.app

# Терминал 2 - API Gateway
export MCP_API_URL=http://localhost:8082
poetry run python -m src.api.app

# Терминал 3 - Telegram Bot (polling режим)
export TELEGRAM_BOT_TOKEN=your-token
export BUDGET_API_URL=http://localhost:8081
poetry run python -m src.bot.run_polling
```

**Важно:** Для локальной разработки используйте `run_polling.py` (polling режим), а не `app.py` (webhook режим). Webhook работает только в продакшене с публичным URL.

Затем написать боту в Telegram:
- `/start` → получить приветствие ✅
- `test message` → получить "MCP Echo: test message" ✅

### Когда можно деплоить на продакшен?

**Минимальный набор для продакшена:**

1. ✅ Итерация 4 — Тесты (ГОТОВО)
2. ⏳ Итерация 5 — Google Sheets интеграция
3. ⏳ Итерация 6 — Google Gemini интеграция
4. ⏳ Итерация 7 — Обработка расходов
5. ⏳ Итерация 8 — Cloud Run deployment
6. ⏳ Итерация 9 — Мониторинг и логирование
7. ⏳ Итерация 10 — Production тестирование

**Рекомендация:** Деплой на продакшен после Итерации 8.

---

## 🛠️ Быстрые команды

### Разработка

```bash
# Установить зависимости
poetry install

# Запустить тесты
poetry run pytest

# Проверить код
poetry run ruff check src/

# Запустить сервисы
poetry run python -m src.mcp.app           # MCP Service (порт 8082)
poetry run python -m src.api.app           # API Gateway (порт 8081)
poetry run python -m src.bot.run_polling   # Bot в polling режиме (для разработки)
poetry run python -m src.bot.app           # Bot в webhook режиме (для продакшена)
```

### Git

```bash
# Посмотреть статус
git status

# Добавить файлы
git add .

# Закоммитить
git commit -m "feat: add new feature"

# Запушить
git push origin dev
```

---

## 📚 Дополнительные материалы

- **REBUILD_PLAN.md** — полный план разработки (10 итераций)
- **TESTING.md** — подробное руководство по тестированию
- **README.md** — общая информация о проекте
- **.env.example** — пример файла с переменными окружения

---

## 🤔 Частые вопросы (FAQ)

### 1. Почему 3 сервиса, а не 1?

**Микросервисная архитектура:**
- ✅ Можно масштабировать каждый сервис отдельно
- ✅ Можно перезапустить MCP без остановки бота
- ✅ Можно заменить Telegram на другой мессенджер (WhatsApp, Discord)
- ✅ Легче тестировать и разрабатывать

### 2. Зачем middleware в боте?

**Middleware** — это "фильтры" для всех сообщений:
- **RateLimitMiddleware** — блокирует спам (10 сообщений в минуту)
- **AccessControlMiddleware** — разрешает доступ только определенным пользователям
- **APIClientMiddleware** — добавляет HTTP клиент в каждый handler

### 3. Что такое lifespan handlers?

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код ДО запуска приложения
    logger.info("Starting...")
    yield
    # Код ПОСЛЕ остановки приложения
    logger.info("Stopping...")
```

Это как конструктор/деструктор:
- **До yield** — инициализация (подключение к БД, создание клиентов)
- **После yield** — очистка (закрытие соединений)

### 4. Почему Pydantic v2?

Pydantic v1 устарел и не поддерживается. В v2:
- ⚡ Быстрее в 5-50 раз
- 🛡️ Лучше валидация
- 📝 Новый синтаксис: `model_config` вместо `class Config`

### 5. Что такое retry logic в HTTP клиенте?

Если запрос к MCP упал:
1. Ждем 1 секунду → повторяем
2. Упал снова → ждем 2 секунды → повторяем
3. Упал снова → ждем 4 секунды → повторяем
4. Упал снова → возвращаем ошибку

Это делает систему устойчивее к временным сбоям.

---

## 🎯 Текущий статус проекта

```
Итерация 4 / 10 — Тестирование ✅ ЗАВЕРШЕНА

Следующая итерация: Google Sheets интеграция
Ожидаемое время до MVP: 6 итераций
Готовность к продакшену: 40%
```

**Вердикт:** Проект в активной разработке. Инфраструктура готова, но функциональность пока минимальная. Деплой на продакшен — РАНО. Можно деплоить на staging для тестирования архитектуры.
