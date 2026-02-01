# Code Execution для сложной аналитики

**Дата:** 2026-02-01
**Статус:** Дизайн утверждён

## Проблема

Стандартные tools (get_expenses, get_statistics) не покрывают сложные аналитические запросы:
- Сравнение периодов ("расходы в январе vs феврале")
- Поиск аномалий ("необычно большие траты")
- Произвольные вычисления ("средний чек в выходные")

## Решение

Добавить tool `execute_analysis_code` для AnalystAgent, который позволяет LLM генерировать и выполнять Python код для анализа данных.

## Архитектура

```
User: "сравни расходы на еду в январе и феврале"
         ↓
   Orchestrator → AnalystAgent
         ↓
   AnalystAgent решает: стандартных tools недостаточно
         ↓
   Вызывает execute_analysis_code с:
     - code: сгенерированный Python код
     - user_id: идентификатор пользователя
         ↓
   Tool выполняет код через RestrictedPython
     - Загружает расходы в pandas DataFrame `df`
     - Запускает код в sandbox
     - Возвращает результат (строка)
         ↓
   AnalystAgent форматирует ответ пользователю
```

## Ключевые решения

| Аспект | Решение | Обоснование |
|--------|---------|-------------|
| Архитектура | Tool для AnalystAgent | Минимальные изменения, Analyst уже понимает контекст |
| Безопасность | RestrictedPython | Баланс между защитой и простотой |
| Данные | DataFrame с расходами | Простой контракт, pandas достаточно |
| Результат | Текстовая строка | MVP, графики можно добавить позже |

## Структура tool

**Файл:** `src/mcp/agents/tools/code_executor.py`

### Tool Definition

```python
execute_analysis_code_tool = FunctionTool(
    name="execute_analysis_code",
    description="""
    Выполняет Python код для сложного анализа расходов.
    Используй когда стандартных get_expenses/get_statistics недостаточно:
    - Сравнение периодов
    - Поиск аномалий
    - Произвольные вычисления

    Код получает DataFrame `df` с колонками:
    - date (datetime): дата расхода
    - category (str): категория
    - description (str): описание
    - amount (float): сумма в рублях

    Код должен записать результат в переменную `result` (строка).
    """,
    func=execute_analysis_code
)
```

### Параметры

- `code: str` — Python код для выполнения
- `user_id: str` — для загрузки расходов нужного пользователя

### Возвращает

Строка с результатом анализа или сообщение об ошибке.

## Sandbox с RestrictedPython

### Разрешённые модули

```python
ALLOWED_MODULES = {
    'pandas': pd,
    'pd': pd,
    'numpy': np,
    'np': np,
    'datetime': datetime,
    'timedelta': timedelta,
}
```

### Разрешённые builtins

```python
SAFE_BUILTINS = {
    **safe_builtins,
    'sum': sum,
    'min': min,
    'max': max,
    'len': len,
    'round': round,
    'abs': abs,
    'sorted': sorted,
    'list': list,
    'dict': dict,
    'str': str,
    'int': int,
    'float': float,
}
```

### Что блокируется

- `import` произвольных модулей
- Доступ к `__class__`, `__bases__` (escape из sandbox)
- Файловые операции (`open`, `os`, `sys`)
- Сетевые вызовы

### Ограничения

- Timeout: 10 секунд
- Код должен вернуть строку через переменную `result`

## Реализация

### execute_in_sandbox

```python
from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def execute_in_sandbox(code: str, df: pd.DataFrame, timeout: int = 10) -> str:
    # 1. Компилируем код с ограничениями
    byte_code = compile_restricted(code, '<analysis>', 'exec')

    # 2. Подготавливаем безопасное окружение
    restricted_globals = {
        '__builtins__': SAFE_BUILTINS,
        '_getiter_': default_guarded_getiter,
        '_iter_unpack_sequence_': guarded_iter_unpack_sequence,
        'df': df,
        **ALLOWED_MODULES,
    }
    restricted_locals = {}

    # 3. Выполняем
    exec(byte_code, restricted_globals, restricted_locals)

    # 4. Извлекаем результат
    result = restricted_locals.get('result', 'Код не вернул результат')
    return str(result)
```

### execute_analysis_code (async wrapper)

```python
import asyncio
import concurrent.futures

async def execute_analysis_code(code: str, user_id: str) -> str:
    try:
        # 1. Загружаем расходы
        expenses = await storage.get_expenses(user_id=user_id, limit=1000)
        df = expenses_to_dataframe(expenses)

        if df.empty:
            return "Нет данных для анализа"

        # 2. Компиляция
        try:
            byte_code = compile_restricted(code, '<analysis>', 'exec')
        except SyntaxError as e:
            return f"Ошибка синтаксиса: {e.msg}"

        # 3. Выполнение с timeout
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(pool, run_sandboxed, byte_code, df),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                return "Превышено время выполнения (10 сек)"

        return result

    except Exception as e:
        logger.error(f"Code execution error: {e}", exc_info=True)
        return f"Ошибка выполнения: {str(e)}"
```

## Обработка ошибок

| Тип ошибки | Сообщение пользователю |
|------------|------------------------|
| Синтаксис | "Ошибка синтаксиса: invalid syntax line 3" |
| Timeout | "Превышено время выполнения (10 сек)" |
| Runtime | "Ошибка выполнения: division by zero" |
| Нет данных | "Нет данных для анализа" |

## Изменения в AnalystAgent

### Промпт (prompts/agents/analyst.txt)

Добавить:

```
Для СЛОЖНЫХ запросов используй execute_analysis_code:
- Сравнение периодов ("расходы в январе vs феврале")
- Вычисление трендов ("растут ли траты на еду")
- Поиск аномалий ("необычно большие траты")
- Произвольные расчёты ("средний чек в выходные")

При использовании execute_analysis_code:
1. Пиши простой и понятный Python код
2. Используй pandas для работы с df
3. Результат сохраняй в переменную result (строка)
4. Форматируй result понятно для пользователя
```

### Регистрация tool (adk_agents.py)

```python
analyst_agent = LlmAgent(
    name="AnalystAgent",
    model=model,
    instruction=analyst_prompt,
    tools=[
        get_expenses_tool,
        get_statistics_tool,
        execute_analysis_code_tool,  # новый tool
    ],
)
```

## Примеры использования

### Сравнение периодов

**Запрос:** "сравни расходы на еду в январе и феврале"

```python
jan = df[(df['date'].dt.month == 1) & (df['category'] == 'Еда')]['amount'].sum()
feb = df[(df['date'].dt.month == 2) & (df['category'] == 'Еда')]['amount'].sum()

diff = feb - jan
pct = (diff / jan * 100) if jan > 0 else 0

result = f"Еда в январе: {jan:.0f}₽\nЕда в феврале: {feb:.0f}₽\nРазница: {diff:+.0f}₽ ({pct:+.1f}%)"
```

### Поиск максимума

**Запрос:** "найди самую большую трату за последний месяц"

```python
from datetime import timedelta
last_month = df[df['date'] >= df['date'].max() - timedelta(days=30)]
max_row = last_month.loc[last_month['amount'].idxmax()]

result = f"Самая большая трата: {max_row['amount']:.0f}₽ — {max_row['description']} ({max_row['category']}, {max_row['date'].strftime('%d.%m')})"
```

### Сравнение будни/выходные

**Запрос:** "средний чек в выходные vs будни"

```python
df['is_weekend'] = df['date'].dt.dayofweek >= 5
weekend_avg = df[df['is_weekend']]['amount'].mean()
weekday_avg = df[~df['is_weekend']]['amount'].mean()

result = f"Средний чек:\n• Будни: {weekday_avg:.0f}₽\n• Выходные: {weekend_avg:.0f}₽"
```

## Зависимости

Добавить в pyproject.toml:

```toml
RestrictedPython = "^7.0"
```

pandas и numpy уже используются.

## Файлы для создания/изменения

| Файл | Действие |
|------|----------|
| `src/mcp/agents/tools/code_executor.py` | Создать |
| `src/mcp/agents/tools/__init__.py` | Экспортировать tool |
| `src/mcp/agents/adk_agents.py` | Добавить tool к AnalystAgent |
| `prompts/agents/analyst.txt` | Добавить инструкции |
| `pyproject.toml` | Добавить RestrictedPython |
| `tests/test_mcp/test_code_executor.py` | Создать тесты |

## Тестирование

### Unit тесты

- Успешное выполнение простого кода
- Обработка синтаксических ошибок
- Timeout при долгом выполнении
- Блокировка опасных операций (import os, open())
- Пустой DataFrame

### Интеграционные тесты

- End-to-end через AnalystAgent
- Проверка что LLM корректно генерирует код
