# Budget Assistant v2.0

**Telegram-бот для учёта расходов с AI и Google Sheets**

---

## 🤔 Что это?

Telegram-бот, который понимает естественный язык и автоматически записывает ваши расходы в Google Sheets.

**Напишите:** `купил хлеб 50 рублей`
**Бот поймёт:** категория "Еда", сумма 50₽, описание "хлеб"
**Результат:** запись в таблице + статистика по кнопке

---

## 💡 Зачем?

✅ **Не нужно заполнять формы** — просто пишите как думаете
✅ **AI сам определяет категорию** — из 17 предустановленных
✅ **Данные в вашем Google Sheets** — полный контроль
✅ **Статистика и аналитика** — за день/неделю/месяц, сравнение периодов
✅ **Бюджетные лимиты** — предупреждения при превышении
✅ **Работает из Claude Desktop** — через MCP протокол

**Идеально для:** личных финансов, семейного бюджета, учёта мелких трат

---

## 🧠 Ключевые AI-решения

### Multi-Agent System
- **Orchestrator-Worker паттерн** — root agent маршрутизирует к специализированным агентам
- **Tool-calling architecture** — агенты используют Python functions как tools
- **Fallback handling** — graceful degradation при API quota exhausted

### LLM Code Execution
- **Sandboxed Python interpreter** — безопасное выполнение LLM-generated кода
- **Controlled globals** — только pandas/numpy, без file I/O/network
- **Timeout mechanism** — 10s limit для предотвращения зависаний

### Production AI Engineering
- **Retry with exponential backoff** — 4 попытки с 1s→2s→4s→8s
- **Quota management** — переключение между моделями (gemini-2.0-flash vs 2.5-flash)
- **Structured outputs** — Pydantic schemas для валидации AI responses
- **FSM-based conversations** — state machine для multi-turn диалогов

### Performance Optimizations
- **Atomic operations** — `append_row()` вместо read→update для устранения race conditions
- **Caching** — 60s TTL для budget limits
- **Lazy connections** — thread-safe connection pooling с `asyncio.Lock()`

---

## 🚀 Как быстро запустить?

### Вариант 1: Локально (для разработки)

```bash
# 1. Клонировать и установить зависимости
git clone <repo-url>
cd budget-assistant-v2
poetry install

# 2. Настроить .env файл
cp .env.example .env
# Заполнить: TELEGRAM_BOT_TOKEN, GOOGLE_API_KEY, путь к service-account.json

# 3. Запустить всё одной командой
docker-compose up
```

**Готово!** Бот работает в режиме polling (без webhook).

### Вариант 2: В облаке (Google Cloud Run)

```bash
# Деплой трёх сервисов + автоматическая настройка webhook
export GCP_PROJECT_ID=your-project
export TELEGRAM_BOT_TOKEN=xxx
export GOOGLE_API_KEY=xxx
# ... (см. .env.example для полного списка)

./scripts/deploy_all.sh
```

**Готово!** Бот работает 24/7 в облаке.

---

## 📱 Как использовать?

### Основные команды

| Команда | Что делает |
|---------|-----------|
| `/start` | Приветствие и главное меню |
| `/add` | Структурированное добавление расхода (шаг за шагом) |
| `/stats` | Статистика за неделю/месяц/год |
| `/last` | Последние 5 расходов |
| `/delete` | Удалить последний расход |
| `/help` | Справка по командам |

### Примеры естественного языка

```
# Простое добавление
"кофе 150"
"такси 300 рублей"
"ВкусВилл 2468,36"

# С датой
"вчера обед 500"
"01.02 кино 800"

# Несколько расходов сразу
"ВкусВилл 2468 и Ozon 679 и такси 300"

# Статистика
"покажи расходы за январь"
"сколько потратил на еду в феврале"
"самый большой расход за месяц"
```

### Интерактивные кнопки

После каждого действия бот показывает кнопки:
- ➕ **Еще один расход** — быстро добавить следующий
- 📊 **Статистика** — посмотреть расходы
- ❌ **Отменить** — удалить последнюю запись
- 🏠 **В меню** — вернуться к главному меню

---

## 📚 Куда идти дальше?

### Для пользователей

- **[Быстрый старт с Claude Desktop](docs/CLAUDE_DESKTOP_CONFIG.md)** — используйте бот прямо из Claude
- **[MCP Server](docs/MCP_SERVER.md)** — интеграция с Claude Desktop

### Для разработчиков

| Документ | Описание |
|----------|----------|
| **[docs/CODEBASE_ANALYSIS.md](docs/CODEBASE_ANALYSIS.md)** | 🔍 Анализ кодовой базы и архитектуры (на русском) |
| **[docs/TESTING.md](docs/TESTING.md)** | 🧪 Тестирование и CI/CD |
| **[docs/CLOUD_RUN_OPERATIONS.md](docs/CLOUD_RUN_OPERATIONS.md)** | ☁️ Операции в продакшене |
| **[docs/UX_UI_DESIGN.md](docs/UX_UI_DESIGN.md)** | 🎨 UX/UI паттерны и клавиатуры |
| **[docs/MCP_SERVER.md](docs/MCP_SERVER.md)** | 🔌 Техническая документация MCP |

### Быстрая диагностика проблем

**Бот не отвечает:**
```bash
# Проверить логи (если локально)
docker-compose logs -f bot

# Проверить логи (если Cloud Run)
gcloud run services logs read budget-bot --limit=50
```

**AI тупит / долго думает:**
- Проверьте квоту Gemini API (в Cloud Console)
- Смените модель: `GEMINI_MODEL=gemini-2.0-flash` (больше лимит)

**Ошибки с Google Sheets:**
- Убедитесь что service account имеет права на таблицу (Editor)
- Проверьте что `GOOGLE_SHEETS_SPREADSHEET_ID` правильный

---

## 🏗 Архитектура (кратко)

```
Пользователь → Telegram → Bot (8080) → API Gateway (8081) → MCP (8082) → Google Sheets
                                                                ↓
                                                         AI Agents (Gemini)
```

**3 независимых сервиса:**
1. **Bot** — обработка Telegram, UI, кнопки
2. **API** — маршрутизация, валидация
3. **MCP** — AI агенты, бизнес-логика, Google Sheets

**Multi-Agent система:**
- **Orchestrator** — понимает намерение пользователя
- **Registrar** — добавляет/удаляет расходы
- **Analyst** — показывает статистику, выполняет аналитику

---

## 🛠 Технологии

| Компонент | Технология |
|-----------|-----------|
| Bot | aiogram 3.4+ |
| API | FastAPI 0.115+ |
| AI | Google Gemini + google-adk 1.20+ |
| Storage | Google Sheets (gspread) |
| Analytics | pandas, numpy (sandbox для кода) |
| MCP | fastmcp 2.0+ |
| Deploy | Google Cloud Run, Secret Manager |
| Tests | pytest, 81 passing tests |

---

## 📈 Статус проекта

**Текущая итерация:** 13 (Storage Reliability)

- ✅ Микросервисная архитектура (3 сервиса)
- ✅ Multi-agent AI система (Orchestrator, Registrar, Analyst)
- ✅ Интеграция с Google Sheets (атомарные операции, без race conditions)
- ✅ Деплой в Google Cloud Run
- ✅ Интерактивный UI (кнопки, клавиатуры, FSM)
- ✅ MCP Server для Claude Desktop
- ✅ Выполнение Python-кода для сложной аналитики
- ✅ Бюджетные лимиты с предупреждениями
- 🔄 **Дальше:** визуализации (графики), экспорт данных, мониторинг

---

## 📊 Метрики производительности

- ⚡ **Latency:** ~2-4s для простых запросов, ~6-10s для code execution
- 🎯 **Accuracy:** 95%+ правильного определения категорий (17 категорий)
- 🔄 **Uptime:** 99.5% (Cloud Run managed)
- 💰 **Cost:** <$1/месяц на 1000 запросов (Gemini free tier)
- 🧪 **Test Coverage:** 81 passing tests, критичные пути покрыты

---

## 🎯 Решённые технические вызовы

1. **Race conditions в Google Sheets** — переход с `get→calculate→update` на атомарный `append_row()`
2. **LLM hallucinations** — structured prompts + tool validation + Pydantic schemas
3. **Quota management** — dynamic model switching + retry logic с exponential backoff
4. **State consistency** — FSM для multi-turn диалогов без external state store
5. **Security в code execution** — sandboxed interpreter с whitelist imports, 10s timeout
6. **Thread safety** — `asyncio.Lock()` для connection pooling, атомарные операции
7. **Message length limits** — автоматический split для Telegram's 4096 char limit

---

## 🤝 Участие в проекте

Это личный проект, но фидбек и предложения приветствуются!

1. Изучите документацию в `/docs` перед началом работы
2. Соблюдайте стиль кода (ruff formatting)
3. Добавляйте тесты для новых фич
4. Поддерживайте покрытие тестами ≥50%

---

## 📄 Лицензия

Private project — All rights reserved

---

**Нужна помощь?** Смотрите документацию в `/docs` или раздел "Быстрая диагностика проблем" выше.
