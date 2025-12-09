# Руководство по локальному тестированию Budget Assistant v2.0

Это руководство поможет вам запустить и протестировать все функции Budget Assistant локально, включая улучшения из Итерации 8.

## 📋 Содержание

1. [Подготовка окружения](#шаг-1-подготовка-окружения)
2. [Запуск сервисов](#шаг-2-запуск-сервисов-3-терминала)
3. [Проверка работы](#шаг-3-проверка-работы-сервисов)
4. [Тестирование функций Итерации 8](#шаг-4-тестирование-новых-функций-итерации-8)
5. [Проверка статистики](#шаг-5-проверка-статистики-и-метрик)
6. [Чек-лист проверки](#-чек-лист-проверки-итерации-8)
7. [Решение проблем](#-что-делать-если-что-то-не-работает)

---

## Шаг 1: Подготовка окружения

### 1.1. Создайте файл `.env`

```bash
cp .env.example .env
```

### 1.2. Заполните `.env` необходимыми токенами

```bash
# Bot
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
TELEGRAM_ADMIN_IDS=ваш_telegram_id
BUDGET_API_URL=http://localhost:8081

# API Gateway
MCP_API_URL=http://localhost:8082
REQUEST_TIMEOUT=30

# MCP
GOOGLE_API_KEY=ваш_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
GOOGLE_SHEETS_SPREADSHEET_ID=id_вашей_таблицы

# Common
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### Где взять токены

| Токен | Как получить |
|-------|-------------|
| **TELEGRAM_BOT_TOKEN** | https://t.me/BotFather → `/newbot` |
| **TELEGRAM_ADMIN_IDS** | https://t.me/userinfobot → отправьте `/start` |
| **GOOGLE_API_KEY** | https://aistudio.google.com/app/apikey |
| **GOOGLE_SHEETS_SPREADSHEET_ID** | Из URL таблицы (между `/d/` и `/edit`) |

---

## Шаг 2: Запуск сервисов (3 терминала)

**ВАЖНО:** Запускайте сервисы в указанном порядке!

### Терминал 1 - MCP Service (порт 8082)

```bash
poetry run python -m src.mcp.app
```

**Ожидаемый вывод:**
```
INFO - Starting MCP Service...
INFO - Shutdown handlers registered (SIGTERM, SIGINT)
INFO - AI agent system ready (lazy initialization)
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8082
```

---

### Терминал 2 - API Gateway (порт 8081)

```bash
poetry run python -m src.api.app
```

**Ожидаемый вывод:**
```
INFO - Starting API Gateway...
INFO - Shutdown handlers registered (SIGTERM, SIGINT)
INFO - Application startup complete.
INFO - Uvicorn running on http://0.0.0.0:8081
```

---

### Терминал 3 - Telegram Bot (polling mode)

```bash
poetry run python -m src.bot.run_polling
```

**Ожидаемый вывод:**
```
INFO - Starting bot in polling mode...
INFO - Bot @ваш_бот started
INFO - Polling...
```

---

## Шаг 3: Проверка работы сервисов

### 3.1. Проверьте health endpoints

В новом терминале или браузере:

**MCP Service:**
```bash
curl http://localhost:8082/health
```

Ожидается:
```json
{"status":"healthy","service":"mcp","version":"2.0.0"}
```

**API Gateway:**
```bash
curl http://localhost:8081/health
```

Ожидается:
```json
{"status":"healthy","service":"api-gateway","version":"2.0.0","dependencies":{"mcp":true}}
```

---

## Шаг 4: Тестирование новых функций Итерации 8

### ✅ Тест 1: Обычное сообщение

**Действие:** Отправьте боту в Telegram:
```
/start
```

**Ожидается:**
- Бот ответит: "Привет, {ваше_имя}! Я Budget Assistant v2.0..."

**Проверьте логи в Терминале 3 (Bot):**
```
INFO - Processing query from user 123456789: /start
INFO - Sending response to user 123456789: 62 chars in 1 message(s)
```

---

### ✅ Тест 2: Добавление расхода

**Действие:** Отправьте боту:
```
купил хлеб 50 рублей
```

**Ожидается:**
- Бот покажет "печатает..."
- Ответит с подтверждением добавления расхода

**Проверьте логи:**

**Терминал 3 (Bot):**
```
INFO - Processing query from user 123456789: купил хлеб 50 рублей
INFO - Sending response to user 123456789: XXX chars in 1 message(s)
```

**Терминал 2 (API):**
```
INFO - Received query from user 123456789: купил хлеб 50 рублей
INFO - Query processed for user 123456789 in 2.45s (response: XXX chars)
```

**Терминал 1 (MCP):**
```
INFO - MCP processing query from user 123456789: купил хлеб 50 рублей
INFO - MCP query processed for user 123456789 in 2.43s (response: XXX chars)
```

---

### ✅ Тест 3: Длинное сообщение (разбивка > 4096 символов)

**Действие:** Отправьте боту:
```
расскажи подробно про все мои расходы за последние 3 месяца с детальной аналитикой и рекомендациями
```

**Ожидается:**
- Если ответ > 4096 символов, бот отправит несколько сообщений
- Между сообщениями будет пауза 0.5 секунды

**Проверьте логи в Терминале 3:**
```
INFO - Processing query from user 123456789: расскажи подробно про все мои расходы...
INFO - Sending response to user 123456789: 5234 chars in 2 message(s)
```

**Если видите "in 2 message(s)" или больше - разбивка работает! ✅**

---

### ✅ Тест 4: Таймаут (симуляция)

**Способ 1 - Изменить таймаут в .env:**
```bash
# В .env установите очень короткий таймаут
REQUEST_TIMEOUT=1
```

Перезапустите API Gateway (Терминал 2), отправьте сложный запрос.

**Ожидается:**
- Пользователь получит: "Обработка запроса заняла слишком много времени. Попробуйте упростить запрос или повторите позже."

**Логи покажут:**
```
WARNING - Request timeout for user 123456789: ...
```

**Верните таймаут обратно:**
```bash
REQUEST_TIMEOUT=30
```

---

### ✅ Тест 5: Retry логика (симуляция недоступности MCP)

**Действие:**
1. Остановите MCP Service (Терминал 1): `Ctrl+C`
2. Отправьте боту любое сообщение
3. Наблюдайте за логами

**Ожидается в Терминале 2 (API):**
```
WARNING - Request failed to http://localhost:8082/mcp/query after 0.52s: ClientConnectorError...
DEBUG - Retrying in 1s...
WARNING - Request failed to http://localhost:8082/mcp/query after 1.03s: ClientConnectorError...
DEBUG - Retrying in 2s...
WARNING - Request failed to http://localhost:8082/mcp/query after 2.04s: ClientConnectorError...
ERROR - Query failed for user 123456789 after 3.65s: ServiceUnavailableError...
```

**Пользователь получит:**
```
Произошла ошибка. Попробуйте позже.
```

**Запустите MCP обратно!**

---

### ✅ Тест 6: Graceful Shutdown

**Действие в любом терминале с сервисом:**
```
Ctrl+C
```

**Ожидается:**
```
INFO - Received SIGINT, initiating graceful shutdown...
INFO - Shutting down API Gateway gracefully...
INFO - Closing MCP client connection...
INFO - API Gateway shutdown complete
```

**Проверяет:**
- ✅ SIGINT обрабатывается
- ✅ HTTP клиенты закрываются
- ✅ Логирование на каждом этапе

---

## Шаг 5: Проверка статистики и метрик

### 5.1. Просмотр статистики
```
покажи мои расходы за неделю
```

### 5.2. Просмотр категорий
```
статистика по категориям
```

### 5.3. Удаление последнего расхода
```
удали последний расход
```

---

## 🎯 Чек-лист проверки Итерации 8

### Логирование работает
- [ ] В логах видны user_id
- [ ] В логах видно время выполнения (X.XXs)
- [ ] В логах видно preview запроса (первые 50 символов)

### Разбивка длинных сообщений
- [ ] Сообщения > 4096 символов разбиваются
- [ ] В логах: "in N message(s)" где N > 1
- [ ] Между сообщениями есть пауза

### Таймаут обработка
- [ ] При таймауте понятное сообщение пользователю
- [ ] Retry логика с exponential backoff (1s, 2s, 4s)
- [ ] В логах видны попытки retry

### Graceful shutdown
- [ ] Ctrl+C обрабатывается корректно
- [ ] Все соединения закрываются
- [ ] Подробные логи shutdown процесса

---

## 🐛 Что делать если что-то не работает

### Проблема: "API не настроен"
```bash
# Проверьте, что все 3 сервиса запущены
# Проверьте .env переменные
```

### Проблема: "Service unavailable"
```bash
# Убедитесь что MCP запущен первым (порт 8082)
# Проверьте curl http://localhost:8082/health
```

### Проблема: Бот не отвечает
```bash
# Проверьте TELEGRAM_BOT_TOKEN
# Проверьте что бот запущен в polling mode
# Проверьте что ваш user_id в TELEGRAM_ADMIN_IDS
```

### Проблема: Ошибки Google Sheets
```bash
# Проверьте GOOGLE_APPLICATION_CREDENTIALS путь
# Проверьте что service account имеет доступ к таблице
# Проверьте GOOGLE_SHEETS_SPREADSHEET_ID
```

---

## 📊 Ожидаемые результаты

После всех тестов вы должны увидеть:

1. ✅ Все 3 сервиса работают стабильно
2. ✅ Логи содержат user_id, timing, и подробности
3. ✅ Длинные сообщения автоматически разбиваются
4. ✅ Retry происходит при недоступности сервисов
5. ✅ Graceful shutdown работает корректно
6. ✅ Расходы успешно добавляются в Google Sheets
7. ✅ AI агенты корректно обрабатывают запросы

---

## 📝 Дополнительные тесты

### Тест производительности
Отправьте 5-10 сообщений подряд и проверьте:
- Rate limiting работает (10 req/min)
- Логи показывают правильное время обработки
- Нет утечек памяти (проверьте `htop` или Activity Monitor)

### Тест длительной работы
Оставьте сервисы запущенными на 1 час:
- Нет падений или зависаний
- Логи не переполняются
- Google Sheets синхронизация работает стабильно

---

**Готово!** Все улучшения Итерации 8 работают! 🎉

Если обнаружите проблемы, проверьте логи всех 3 сервисов - они теперь очень подробные и помогут быстро найти причину.
