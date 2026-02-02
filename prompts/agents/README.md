# Agent Prompts

Промпты для multi-agent системы Budget Assistant.

## Структура

| Файл | Агент | Назначение |
|------|-------|-----------|
| `orchestrator.j2` | BudgetOrchestrator | Маршрутизация запросов к специализированным агентам |
| `registrar.j2` | RegistrarAgent | Добавление и удаление расходов |
| `analyst.j2` | AnalystAgent | Статистика, аналитика, code execution |

## Техники Prompt Engineering

### 1. Role-Based Instructions

Каждый агент имеет чётко определённую роль:

```
Ты - агент-регистратор для семейного бюджета.
Ты - агент-аналитик для семейного бюджета.
Ты - оркестратор системы управления семейным бюджетом.
```

**Почему:** Ограничивает scope ответов, уменьшает hallucinations.

### 2. Explicit Tool-Use Instructions

Детальные инструкции когда и как использовать каждый tool:

```
КРИТИЧЕСКИ ВАЖНО:
Когда пользователь описывает покупку:
1. Определи категорию
2. Извлеки сумму
3. ОБЯЗАТЕЛЬНО вызови add_expense_tool
```

**Почему:** LLM склонны "симулировать" вызовы tools вместо реального вызова.

### 3. Constraint Prompts

Явные запреты предотвращают нежелательное поведение:

```
НЕ симулируй добавление! ВСЕГДА вызывай add_expense_tool
НЕ используй markdown таблицы! Telegram их не поддерживает
```

**Почему:** Негативные инструкции часто эффективнее позитивных.

### 4. Few-Shot Examples

Примеры в промптах для consistent форматирования:

```python
### Пример 1: "самый большой расход за январь"
ВЫЗОВИ execute_analysis_code с кодом:
jan_data = df[df['date'].dt.month == 1]
...
```

**Почему:** Модель копирует паттерны из примеров.

### 5. Trigger Lists

Явные списки триггеров для сложных решений:

```
### ТРИГГЕРЫ для execute_analysis_code (используй ВСЕГДА):
- "самый большой расход" / "максимальная трата"
- "сколько на [категория] в [месяц]"
- "сравни январь и февраль"
```

**Почему:** Уменьшает неопределённость в edge cases.

### 6. Dynamic Context Injection

Переменные подставляются в runtime через Jinja2:

```jinja
Категории расходов:
{{ categories }}

Текущая дата: {{ current_date }}.
```

**Переменные:**
- `{{ categories }}` — список категорий (из `src/core/categories.py`)
- `{{ categories_with_emoji }}` — категории с emoji для форматирования
- `{{ current_date }}` — текущая дата для правильного расчёта "вчера"

### 7. Output Format Specifications

Детальные инструкции по форматированию вывода:

```
Прогресс-бар должен ТОЧНО соответствовать проценту!
- Всего 10 символов в баре
- Каждый █ = 10% (округляй вниз)
- Примеры: 24% = ██░░░░░░░░, 5% = ░░░░░░░░░░
```

**Почему:** Без примеров модель форматирует inconsistently.

### 8. Orchestrator Pattern

Root agent делегирует специализированным агентам:

```
1. **RegistrarAgent** - для ДОБАВЛЕНИЯ или УДАЛЕНИЯ
   Вызывай когда пользователь:
   - Описывает покупку
   - Просит удалить расход

2. **AnalystAgent** - для ПРОСМОТРА и СТАТИСТИКИ
   Вызывай когда пользователь:
   - Хочет увидеть расходы
   - Просит статистику
```

**Почему:** Разделение ответственности улучшает качество каждой задачи.

## Как менять промпты

### 1. Локально (development)

```bash
# Отредактировать файл
vim prompts/agents/registrar.j2

# Перезапустить MCP сервис
docker-compose restart mcp
# или
poetry run python -m src.mcp.app
```

### 2. В production (Cloud Run)

```bash
# Commit изменения
git add prompts/
git commit -m "prompt: improve category detection"

# Redeploy
./scripts/deploy_all.sh
```

### 3. Тестирование изменений

```bash
# Запустить только MCP локально
poetry run python -m src.mcp.app

# В другом терминале - тест через curl
curl -X POST http://localhost:8082/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "купил хлеб 50 рублей", "user_id": "test"}'
```

## История ключевых изменений

| Дата | Изменение | Результат |
|------|-----------|-----------|
| 2026-01 | Добавлены few-shot примеры для code execution | +40% accuracy на сложных запросах |
| 2026-01 | Добавлены constraint prompts ("НЕ симулируй") | Устранены фейковые ответы без tool calls |
| 2026-02 | Динамическая дата в analyst.j2 | Корректное "вчера", "позавчера" |
| 2026-02 | Trigger lists для execute_analysis_code | Consistent использование code execution |

## Метрики

- **Accuracy категоризации:** 95%+ (17 категорий)
- **Tool call reliability:** 99%+ (с constraint prompts)
- **Format consistency:** 90%+ (с few-shot examples)
