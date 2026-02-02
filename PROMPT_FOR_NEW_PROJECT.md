# 🤖 Промпт для настройки документации в новом проекте

> Скопируй этот промпт и отправь AI assistant (Claude, ChatGPT, etc.) в новом проекте

---

```
Настрой систему документации и управления промптами для моего проекта.

## Контекст проекта
- **Название:** [ИМЯ_ПРОЕКТА]
- **Назначение:** [ЧТО_ДЕЛАЕТ_ПРОЕКТ]
- **Технологии:** [ОСНОВНОЙ_СТЕК]
- **Язык документации:** [русский/английский]
- **Использует LLM:** [да/нет]

## Задачи

### 1. README.md (читается за 30-60 секунд)

Создай README.md со следующей структурой:

#### 🤔 Что это?
- 2-3 предложения описание проекта
- Пример: "Напишите X → Бот сделает Y → Результат Z"

#### 💡 Зачем?
- 5-7 ключевых преимуществ (чекбоксы ✅)
- Идеально для: [use cases]

#### 🧠 Ключевые [AI/технические] решения (если применимо)
- Архитектурные паттерны
- Production-ready решения
- Оптимизации производительности

#### 🚀 Как быстро запустить?
- Вариант 1: Локально
- Вариант 2: Docker/Облако

#### 📱 Как использовать?
- Основные команды (таблица)
- Примеры использования

#### 📚 Куда идти дальше?
- Для пользователей (quick start guides)
- Для разработчиков (technical docs)
- Быстрая диагностика проблем

#### 🏗 Архитектура (кратко)
- Диаграмма компонентов
- Краткое описание сервисов/модулей

#### 🛠 Технологии
- Таблица: Компонент | Технология | Версия

#### 📈 Статус проекта
- Текущая итерация/версия
- Что работает (чеклист ✅)
- Что дальше (🔄)

**Требования:**
- Без лишних англицизмов (только технические термины)
- Естественный язык (не перевод с английского)
- Для портфолио: добавь "Решённые технические вызовы", "Метрики"

---

### 2. docs/CODEBASE_ANALYSIS.md (для разработчиков)

Создай техническую карту кодовой базы:

#### ⚡ TL;DR
- Архитектура одной строкой
- Запуск в 3 команды
- Где основной код (3-4 файла)

#### ⚙️ Как это работает (упрощённо)
- Mermaid диаграмма последовательности (sequenceDiagram)
- 5 шагов обработки (таблица)

#### 🚀 Первые шаги разработчика
- **Хочу запустить локально** — команды установки
- **Хочу понять [компонент A]** — 2-3 ключевых файла
- **Хочу понять [компонент B]** — 2-3 ключевых файла
- **Хочу добавить новую фичу** — пошаговый гайд
- **Хочу пофиксить баг** — где логи, типичные ошибки
- **Хочу изменить промпт и протестировать** (если используешь LLM):
  - Где находятся промпты
  - Как редактировать (Jinja2 синтаксис)
  - Как протестировать (3 варианта)
- **Хочу написать тест** — структура, команды
- **Хочу задеплоить** — команды деплоя

#### 🗺 Карта кодовой базы
- Таблицы файлов по слоям/модулям
- Файл | Описание

#### 🔬 Углублённо (для продвинутых)
- Детальный алгоритм (20 шагов в <details>)
- Архитектурные паттерны
- Известные проблемы и TODO

---

### 3. Система промптов (ТОЛЬКО если используешь LLM)

Создай структуру:
```
prompts/
├── agents/                    # или другое название
│   ├── README.md             # Документация prompt engineering
│   └── [agent_name].j2       # Промпты (пока пустые, я заполню)
└── loader.py                 # Загрузчик с Jinja2
```

#### prompts/loader.py
```python
"""Prompt loader utility using Jinja2 templates."""

import logging
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

# Base directory for prompts
PROMPTS_DIR = Path(__file__).parent
AGENTS_DIR = PROMPTS_DIR / "agents"  # или твоё название

# Jinja2 environment
_env = Environment(
    loader=FileSystemLoader(AGENTS_DIR),
    autoescape=False,
)


def load_prompt(name: str, **variables) -> str:
    """
    Load and render a prompt template.

    Args:
        name: Template name without extension (e.g., "agent1")
        **variables: Variables to inject into the template

    Returns:
        Rendered prompt string
    """
    template_name = f"{name}.j2"

    try:
        template = _env.get_template(template_name)
        rendered = template.render(**variables)
        logger.debug(f"Loaded prompt '{name}' with {len(variables)} variables")
        return rendered
    except TemplateNotFound:
        logger.error(f"Prompt template not found: {template_name}")
        raise FileNotFoundError(f"Prompt not found: {AGENTS_DIR / template_name}")


# Добавь функции-хелперы для каждого промпта:
# def load_agent1_prompt(**kwargs) -> str:
#     return load_prompt("agent1", **kwargs)
```

#### prompts/agents/README.md
Документируй использованные prompt engineering техники:

1. **Role-Based Instructions** — чёткое определение роли
2. **Explicit Tool-Use Instructions** — когда и как использовать инструменты
3. **Constraint Prompts** — явные запреты
4. **Few-Shot Examples** — примеры в промптах
5. **Trigger Lists** — списки триггеров для действий
6. **Dynamic Context Injection** — переменные через Jinja2
7. **Output Format Specifications** — детальное форматирование
8. **Orchestrator Pattern** (если multi-agent) — делегирование задач

Для каждой техники:
- Почему используется
- Пример из промпта
- Результат

Также добавь:
- Как менять промпты (edit .j2 → restart service)
- Как тестировать (локально, staging, production)

---

### 4. AGENTS.md (для AI coding assistants)

Создай краткий справочник:

#### 🚀 Commands & Development
```bash
# Installation
[команды установки]

# Testing
[команды тестов]

# Quality Assurance
[линтеры, форматтеры]

# Running Locally
[команды запуска]
```

#### 🎨 Code Style Guidelines
- Naming conventions
- Typing requirements
- Async patterns
- Docstring style

#### 🤖 [Специфика проекта]
- AI Agent System (если есть)
- Storage Layer patterns
- API structure

#### 📝 Git & Documentation
- Commit message format
- Documentation update rules

**Цель:** AI assistant понимает проект за 30 секунд.

---

## Принципы

1. **README за минуту** — пользователь понимает проект за 30-60 сек
2. **Без воды** — только нужная информация
3. **Без англицизмов** — естественный язык, технические термины OK
4. **Для портфолио** — показываем решённые вызовы и метрики
5. **Jinja2 для промптов** — индустриальный стандарт
6. **Версионируем промпты** — они в git, меняются как код

---

## Начни

1. Создай README.md
2. Создай docs/CODEBASE_ANALYSIS.md с TL;DR
3. Если LLM: создай prompts/loader.py и структуру
4. Создай AGENTS.md

После создания покажи мне структуру и попроси review.
```

---

## Для копирования в другой проект

Скопируй:
1. **Этот промпт целиком** → отправь AI в новом проекте
2. **prompts/loader.py** → без изменений (универсальный)
3. **Структуру docs/** → адаптируй под свой проект

---

**Основано на Budget Assistant v2.0 (Iteration 13+)**
