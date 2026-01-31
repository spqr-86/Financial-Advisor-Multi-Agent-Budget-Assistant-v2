# План рефакторинга Budget Assistant v2

## Обзор

**Текущее состояние:** 45 файлов, ~4500 строк кода
**Выявлено проблем:** 42 (качество кода) + 11 (производительность)

---

## Фаза 1: Производительность (критично)

### 1.1 Параллельные запросы в handlers
**Файлы:** `src/bot/handlers/commands.py`, `src/bot/handlers/callbacks.py`
**Проблема:** Последовательные HTTP запросы
**Решение:** `asyncio.gather()` для независимых запросов

```python
# Было (commands.py:62-73)
stats_result = await api_client.post("/api/query", ...)
limits_result = await api_client.get(f"/api/limits/{user_id}")

# Стало
stats_result, limits_result = await asyncio.gather(
    api_client.post("/api/query", ...),
    api_client.get(f"/api/limits/{user_id}"),
)
```

**Эффект:** `/stats` в 2 раза быстрее

---

### 1.2 Убрать двойное чтение при добавлении расхода
**Файл:** `src/mcp/storage/sheets.py:140-208`
**Проблема:** `add_expense()` читает таблицу, потом `get_statistics()` читает снова

```python
# Было
all_values = await self._run_sync(worksheet.get_all_values)  # Чтение 1
# ... добавление ...
stats = await self.get_statistics(user_id, "month")  # Чтение 2 (внутри опять get_all_values)

# Стало
all_values = await self._run_sync(worksheet.get_all_values)
# ... добавление ...
stats = self._calculate_statistics_from_values(all_values, "month")  # Без повторного чтения
```

**Эффект:** Добавление расхода на 30-40% быстрее

---

### 1.3 Исправить retry config для Gemini
**Файл:** `src/mcp/agents/adk_agents.py:31-37`
**Проблема:** `exp_base=7` приводит к ретраям до 40 минут

```python
# Было
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,  # 1s, 7s, 49s, 343s, 2401s
    initial_delay=1,
)

# Стало
retry_config = types.HttpRetryOptions(
    attempts=4,
    exp_base=2,  # 1s, 2s, 4s, 8s (max 15s total)
    initial_delay=1,
)
```

**Эффект:** Быстрый fail при ошибках квоты вместо зависания

---

### 1.4 Кэширование лимитов
**Файл:** `src/mcp/storage/sheets.py`
**Проблема:** Лимиты читаются на каждый запрос, хотя меняются редко

```python
# Новый файл: src/core/cache.py
from functools import lru_cache
from datetime import datetime, timedelta

class TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._cache[key] = (value, datetime.now())

# В sheets.py
_limits_cache = TTLCache(ttl_seconds=60)

async def get_limits(self, user_id: str) -> dict[str, Any]:
    cached = _limits_cache.get(f"limits:{user_id}")
    if cached:
        return cached
    # ... fetch from sheets ...
    _limits_cache.set(f"limits:{user_id}", result)
    return result
```

**Эффект:** 70% запросов лимитов из кэша

---

### 1.5 Range-запросы вместо полного сканирования
**Файл:** `src/mcp/storage/sheets.py`
**Проблема:** `get("A:D")` загружает всю таблицу

```python
# Было (для get_expenses с limit=5)
all_values = await self._run_sync(worksheet.get, "A:D")  # Все 1000+ строк
records = records[-limit:]  # Берём только 5

# Стало
# Сначала узнаём последнюю строку (можно кэшировать)
last_row = len(await self._run_sync(worksheet.col_values, 1))
start_row = max(2, last_row - limit + 1)
values = await self._run_sync(worksheet.get, f"A{start_row}:D{last_row}")
```

**Эффект:** На 90% меньше данных при `/last`

---

## Фаза 2: Устранение дублирования

### 2.1 Декоратор @require_api_client
**Файлы:** `src/bot/handlers/commands.py`, `src/bot/handlers/callbacks.py`
**Проблема:** 10+ мест с одинаковой проверкой

```python
# Новый файл: src/bot/decorators.py
from functools import wraps

def require_api_client(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        api_client = kwargs.get("api_client")
        message = args[0] if args else kwargs.get("message")

        if not api_client:
            logger.error("API client not configured")
            await message.answer("Сервис временно недоступен")
            return
        return await func(*args, **kwargs)
    return wrapper

# Использование
@router.message(Command("stats"))
@require_api_client
async def cmd_stats(message: Message, api_client: ServiceClient) -> None:
    # api_client гарантированно не None
```

**Эффект:** -70 строк дублирования

---

### 2.2 Утилита send_chunked_message()
**Файл:** `src/bot/handlers/__init__.py:121-170`
**Проблема:** Один и тот же цикл отправки 3 раза

```python
# В src/bot/utils.py
async def send_chunked_message(
    message: Message,
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML",
    delay: float = 0.5,
) -> None:
    """Отправить длинное сообщение частями."""
    chunks = split_long_message(text)

    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await message.answer(
            chunk,
            parse_mode=parse_mode,
            reply_markup=keyboard if is_last else None,
        )
        if not is_last:
            await asyncio.sleep(delay)
```

**Эффект:** -50 строк дублирования

---

### 2.3 Константы в одном месте
**Новый файл:** `src/core/constants.py`

```python
# Таймауты
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
CACHE_TTL_LIMITS = 60
CACHE_TTL_STATS = 30

# Telegram
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
MESSAGE_CHUNK_DELAY = 0.5

# Google Sheets
WORKSHEET_EXPENSES = "Траты и бюджет"
WORKSHEET_LIMITS = "Лимиты"

# Progress bar
PROGRESS_BAR_WIDTH = 10
PROGRESS_BAR_FILLED = "█"
PROGRESS_BAR_EMPTY = "░"
```

**Эффект:** Все magic numbers в одном месте

---

## Фаза 3: Структура и типизация

### 3.1 Pydantic модели для limits endpoints
**Файл:** `src/core/schemas.py`

```python
# Добавить
class GetLimitsRequest(BaseModel):
    user_id: str = "default"

class SetLimitRequest(BaseModel):
    user_id: str = "default"
    category: str
    amount: float = Field(gt=0)

class DeleteLimitRequest(BaseModel):
    user_id: str = "default"
    category: str

class LimitsResponse(BaseModel):
    status: str
    limits: dict[str, float]
```

**Эффект:** Типобезопасность + автовалидация

---

### 3.2 Разбить handle_text на части
**Файл:** `src/bot/handlers/__init__.py` (137 строк → 4 функции)

```python
async def handle_text(message: Message, api_client: ServiceClient | None) -> None:
    """Главный обработчик текста."""
    if not _validate_request(message, api_client):
        return

    response = await _send_to_api(message, api_client)
    if not response:
        return

    await _send_response(message, response)

async def _validate_request(message: Message, api_client: ServiceClient | None) -> bool:
    ...

async def _send_to_api(message: Message, api_client: ServiceClient) -> dict | None:
    ...

async def _send_response(message: Message, response: dict) -> None:
    ...
```

**Эффект:** Читаемость, тестируемость

---

### 3.3 Dependency Injection для singletons
**Файл:** `src/core/container.py`

```python
import asyncio
from typing import TypeVar, Generic

T = TypeVar("T")

class Singleton(Generic[T]):
    def __init__(self, factory):
        self._factory = factory
        self._instance: T | None = None
        self._lock = asyncio.Lock()

    async def get(self) -> T:
        if self._instance is None:
            async with self._lock:
                if self._instance is None:
                    self._instance = self._factory()
        return self._instance

# Использование
storage_singleton = Singleton(GoogleSheetsStorage)
agent_singleton = Singleton(ADKBudgetAgent)
```

**Эффект:** Нет race conditions, чистая архитектура

---

## Фаза 4: Улучшение надёжности

### 4.1 Специфичная обработка ошибок
**Файлы:** Все handlers

```python
# Вместо
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    await message.answer("Произошла ошибка")

# Сделать
except asyncio.TimeoutError:
    await message.answer("Сервис не отвечает, попробуйте позже")
except ServiceUnavailableError:
    await message.answer("Сервис временно недоступен")
except QuotaExceededError:
    await message.answer("Превышен лимит запросов, подождите минуту")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    await message.answer("Неизвестная ошибка")
```

---

### 4.2 Request ID для трейсинга
**Файлы:** `src/bot/middlewares/__init__.py`, все handlers

```python
import uuid

class RequestIdMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        request_id = str(uuid.uuid4())[:8]
        data["request_id"] = request_id

        # Добавляем в логгер
        logger = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {"request_id": request_id}
        )
        data["logger"] = logger

        return await handler(event, data)
```

**Эффект:** Легко отследить путь запроса через все сервисы

---

## Фаза 5: Очистка

### 5.1 Удалить unused imports
```
src/bot/handlers/structured.py:7  — StateFilter
```

### 5.2 Удалить TODO комментарии или реализовать
```
src/mcp/app.py:80  — "TODO: Check agent system health"
```

### 5.3 Унифицировать стиль импортов
- Все импорты в начале файла
- Группировка: stdlib → third-party → local

---

## Порядок выполнения

### Неделя 1: Производительность
| День | Задача | Файлы |
|------|--------|-------|
| 1 | 1.1 asyncio.gather() в handlers | commands.py, callbacks.py |
| 1 | 1.3 Fix retry config | adk_agents.py |
| 2 | 1.2 Убрать двойное чтение | sheets.py |
| 3 | 1.4 TTL кэш для лимитов | cache.py (new), sheets.py |
| 4-5 | 1.5 Range-запросы | sheets.py |

### Неделя 2: Дублирование
| День | Задача | Файлы |
|------|--------|-------|
| 1 | 2.1 @require_api_client | decorators.py (new), handlers |
| 2 | 2.2 send_chunked_message() | utils.py, handlers |
| 3 | 2.3 Константы | constants.py (new) |

### Неделя 3: Структура
| День | Задача | Файлы |
|------|--------|-------|
| 1-2 | 3.1 Pydantic для limits | schemas.py, routes |
| 3 | 3.2 Разбить handle_text | handlers/__init__.py |
| 4-5 | 3.3 DI container | container.py (new) |

### Неделя 4: Надёжность + Очистка
| День | Задача | Файлы |
|------|--------|-------|
| 1-2 | 4.1 Специфичные exceptions | handlers |
| 3 | 4.2 Request ID | middlewares |
| 4-5 | 5.1-5.3 Cleanup | все файлы |

---

## Метрики успеха

| Метрика | До | После |
|---------|-----|-------|
| `/stats` время ответа | ~2s | ~1s |
| Добавление расхода | ~1.5s | ~1s |
| Строк дублирования | ~200 | ~30 |
| Покрытие типами | ~60% | ~90% |
| Magic numbers | ~15 | 0 |

---

## Риски

1. **Кэширование лимитов** — пользователь не увидит изменение сразу (решение: инвалидация при set_limit)
2. **Range-запросы** — нужно знать последнюю строку (решение: кэшировать metadata)
3. **DI container** — требует рефакторинга всех точек создания (решение: делать постепенно)

---

## Файлы для создания

```
src/
├── core/
│   ├── cache.py        # TTL кэш
│   ├── constants.py    # Все константы
│   └── container.py    # DI singleton
├── bot/
│   └── decorators.py   # @require_api_client
```

## Файлы для изменения

```
src/bot/handlers/__init__.py    # Разбить, добавить send_chunked
src/bot/handlers/commands.py    # asyncio.gather, декораторы
src/bot/handlers/callbacks.py   # asyncio.gather, декораторы
src/bot/utils.py                # send_chunked_message
src/mcp/storage/sheets.py       # Кэш, range-запросы
src/mcp/agents/adk_agents.py    # Fix retry
src/core/schemas.py             # Pydantic для limits
```
