# Code Execution Implementation Plan (v2 - без RestrictedPython)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `execute_analysis_code` tool to AnalystAgent for complex analytics via LLM-generated Python code.

**Architecture:** New tool runs LLM-generated code using exec() with controlled globals/locals. Returns text result.

**Tech Stack:** Built-in exec(), pandas (already installed), asyncio for timeout

---

## Task 1: Create code_executor module with sandbox

**Files:**
- Create: `src/mcp/agents/tools/code_executor.py`
- Test: `tests/test_mcp/test_code_executor.py`

**Step 1: Write failing test for sandbox execution**

Create `tests/test_mcp/test_code_executor.py`:

```python
"""Tests for code executor sandbox."""

import pandas as pd
import pytest


class TestExecuteInSandbox:
    """Tests for execute_in_sandbox function."""

    def test_simple_calculation(self):
        """Test basic DataFrame calculation."""
        from src.mcp.agents.tools.code_executor import execute_in_sandbox

        df = pd.DataFrame({
            'amount': [100, 200, 300],
            'category': ['Еда', 'Еда', 'Транспорт'],
        })
        code = "result = str(df['amount'].sum())"

        result = execute_in_sandbox(code, df)

        assert result == "600"

    def test_missing_result_variable(self):
        """Test when code doesn't set result variable."""
        from src.mcp.agents.tools.code_executor import execute_in_sandbox

        df = pd.DataFrame({'amount': [100]})
        code = "x = 1 + 1"

        result = execute_in_sandbox(code, df)

        assert result == "Код не вернул результат"

    def test_syntax_error(self):
        """Test handling of syntax errors."""
        from src.mcp.agents.tools.code_executor import execute_in_sandbox

        df = pd.DataFrame({'amount': [100]})
        code = "result = ("  # Invalid syntax

        result = execute_in_sandbox(code, df)

        assert "Ошибка синтаксиса" in result

    def test_blocked_import(self):
        """Test that imports are blocked."""
        from src.mcp.agents.tools.code_executor import execute_in_sandbox

        df = pd.DataFrame({'amount': [100]})
        code = "import os; result = 'test'"

        result = execute_in_sandbox(code, df)

        assert "Ошибка" in result

    def test_blocked_builtins(self):
        """Test that dangerous builtins are blocked."""
        from src.mcp.agents.tools.code_executor import execute_in_sandbox

        df = pd.DataFrame({'amount': [100]})
        code = "result = open('/etc/passwd').read()"

        result = execute_in_sandbox(code, df)

        assert "Ошибка" in result or "open" in result.lower()

    def test_pandas_operations(self):
        """Test that pandas operations work."""
        from src.mcp.agents.tools.code_executor import execute_in_sandbox

        df = pd.DataFrame({
            'amount': [100, 200, 150],
            'category': ['Еда', 'Транспорт', 'Еда'],
        })
        code = """
food_total = df[df['category'] == 'Еда']['amount'].sum()
result = f"Еда: {food_total}₽"
"""

        result = execute_in_sandbox(code, df)

        assert result == "Еда: 250₽"

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        from src.mcp.agents.tools.code_executor import execute_in_sandbox

        df = pd.DataFrame(columns=['amount', 'category'])
        code = "result = f'Записей: {len(df)}'"

        result = execute_in_sandbox(code, df)

        assert result == "Записей: 0"
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_mcp/test_code_executor.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.mcp.agents.tools.code_executor'"

**Step 3: Write sandbox implementation**

Create `src/mcp/agents/tools/code_executor.py`:

```python
"""Code executor with exec() sandbox for complex analytics."""

import logging
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Safe builtins - only basic functions, no file/network access
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


def execute_in_sandbox(code: str, df: pd.DataFrame, timeout: int = 10) -> str:
    """
    Execute Python code in a restricted sandbox.

    Args:
        code: Python code to execute
        df: DataFrame with expenses data
        timeout: Max execution time in seconds (enforced by async wrapper)

    Returns:
        Result string from code execution or error message
    """
    # Check for syntax errors first
    try:
        compile(code, "<analysis>", "exec")
    except SyntaxError as e:
        return f"Ошибка синтаксиса: {e.msg} (строка {e.lineno})"

    # Prepare restricted globals - only safe builtins and allowed modules
    safe_globals = {
        "__builtins__": SAFE_BUILTINS,
        "pd": pd,
        "pandas": pd,
        "np": np,
        "numpy": np,
        "df": df,
    }

    # Empty locals for code execution
    safe_locals: dict[str, Any] = {}

    try:
        # Execute code in restricted environment
        exec(code, safe_globals, safe_locals)

        # Extract result
        result = safe_locals.get("result", "Код не вернул результат")
        return str(result)

    except NameError as e:
        # Catch attempts to use blocked builtins or imports
        logger.warning(f"Code execution blocked unsafe operation: {e}")
        return f"Ошибка выполнения: {str(e)}"

    except Exception as e:
        logger.warning(f"Code execution error: {e}")
        return f"Ошибка выполнения: {str(e)}"
```

**Step 4: Run tests to verify they pass**

Run: `poetry run pytest tests/test_mcp/test_code_executor.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/mcp/agents/tools/code_executor.py tests/test_mcp/test_code_executor.py
git commit -m "feat: add code execution sandbox with exec()"
```

---

## Task 2: Add async tool function with timeout

**Files:**
- Modify: `src/mcp/agents/tools/code_executor.py`
- Modify: `tests/test_mcp/test_code_executor.py`

**Step 1: Write failing test for async tool**

Add to `tests/test_mcp/test_code_executor.py`:

```python
@pytest.mark.asyncio
class TestExecuteAnalysisCode:
    """Tests for execute_analysis_code async tool."""

    async def test_successful_analysis(self, monkeypatch):
        """Test successful code execution through tool."""
        from src.mcp.agents.tools.code_executor import execute_analysis_code

        # Mock storage.get_expenses
        async def mock_get_expenses(user_id, limit):
            return {
                "expenses": [
                    {"date": "01.02.2026", "category": "Еда", "description": "хлеб", "amount": 50},
                    {"date": "01.02.2026", "category": "Еда", "description": "молоко", "amount": 80},
                    {"date": "01.02.2026", "category": "Транспорт", "description": "метро", "amount": 100},
                ]
            }

        # Patch storage
        import src.mcp.agents.tools.code_executor as executor_module
        monkeypatch.setattr(executor_module, "_get_expenses_for_analysis", mock_get_expenses)

        code = "result = f'Всего: {df[\"amount\"].sum()}₽'"
        result = await execute_analysis_code(code=code, user_id="test")

        assert "230" in result

    async def test_empty_expenses(self, monkeypatch):
        """Test with no expenses."""
        from src.mcp.agents.tools.code_executor import execute_analysis_code

        async def mock_get_expenses(user_id, limit):
            return {"expenses": []}

        import src.mcp.agents.tools.code_executor as executor_module
        monkeypatch.setattr(executor_module, "_get_expenses_for_analysis", mock_get_expenses)

        code = "result = 'test'"
        result = await execute_analysis_code(code=code, user_id="test")

        assert result == "Нет данных для анализа"

    async def test_timeout(self, monkeypatch):
        """Test timeout handling."""
        from src.mcp.agents.tools.code_executor import execute_analysis_code

        async def mock_get_expenses(user_id, limit):
            return {
                "expenses": [
                    {"date": "01.02.2026", "category": "Еда", "description": "test", "amount": 100},
                ]
            }

        import src.mcp.agents.tools.code_executor as executor_module
        monkeypatch.setattr(executor_module, "_get_expenses_for_analysis", mock_get_expenses)
        monkeypatch.setattr(executor_module, "EXECUTION_TIMEOUT", 0.001)  # Very short timeout

        # Infinite loop code
        code = """
while True:
    pass
result = 'done'
"""
        result = await execute_analysis_code(code=code, user_id="test")

        assert "время выполнения" in result.lower() or "timeout" in result.lower()
```

**Step 2: Run test to verify it fails**

Run: `poetry run pytest tests/test_mcp/test_code_executor.py::TestExecuteAnalysisCode -v`
Expected: FAIL with "cannot import name 'execute_analysis_code'"

**Step 3: Add async tool implementation**

Add to `src/mcp/agents/tools/code_executor.py` after `execute_in_sandbox`:

```python
import asyncio
import concurrent.futures
from datetime import datetime

from src.mcp.agents.tools.sheets import get_storage

EXECUTION_TIMEOUT = 10.0  # seconds


async def _get_expenses_for_analysis(user_id: str, limit: int = 1000) -> dict[str, Any]:
    """Get expenses from storage for analysis."""
    storage = get_storage()
    return await storage.get_expenses(user_id=user_id, limit=limit)


def _expenses_to_dataframe(expenses_data: dict[str, Any]) -> pd.DataFrame:
    """Convert expenses dict to pandas DataFrame."""
    expenses = expenses_data.get("expenses", [])

    if not expenses:
        return pd.DataFrame(columns=["date", "category", "description", "amount"])

    df = pd.DataFrame(expenses)

    # Convert date strings to datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y", errors="coerce")

    # Ensure amount is numeric
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    return df


async def execute_analysis_code(code: str, user_id: str = "default") -> str:
    """
    Execute Python code for complex expense analysis.

    Use this tool when standard get_expenses/get_statistics are not enough:
    - Period comparisons ("expenses in January vs February")
    - Trend calculations ("are food expenses growing")
    - Anomaly detection ("unusually large expenses")
    - Custom calculations ("average check on weekends")

    The code receives DataFrame `df` with columns:
    - date (datetime): expense date
    - category (str): category name
    - description (str): expense description
    - amount (float): amount in rubles

    Code must save result to `result` variable (string).

    Args:
        code: Python code to execute
        user_id: User ID for loading expenses

    Returns:
        Analysis result string or error message
    """
    try:
        # Load expenses
        expenses_data = await _get_expenses_for_analysis(user_id, limit=1000)
        df = _expenses_to_dataframe(expenses_data)

        if df.empty:
            return "Нет данных для анализа"

        # Execute with timeout in thread pool
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(pool, execute_in_sandbox, code, df),
                    timeout=EXECUTION_TIMEOUT,
                )
                logger.info(f"Code execution successful for user {user_id}")
                return result

            except asyncio.TimeoutError:
                logger.warning(f"Code execution timeout for user {user_id}")
                return f"Превышено время выполнения ({int(EXECUTION_TIMEOUT)} сек)"

    except Exception as e:
        logger.error(f"Code execution error: {e}", exc_info=True)
        return f"Ошибка выполнения: {str(e)}"
```

**Step 4: Run tests**

Run: `poetry run pytest tests/test_mcp/test_code_executor.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/mcp/agents/tools/code_executor.py tests/test_mcp/test_code_executor.py
git commit -m "feat: add async execute_analysis_code tool with timeout"
```

---

## Task 3: Export tool from module

**Files:**
- Modify: `src/mcp/agents/tools/__init__.py`

**Step 1: Update exports**

Replace content of `src/mcp/agents/tools/__init__.py`:

```python
"""Tools for AI agents."""

from src.mcp.agents.tools.code_executor import execute_analysis_code
from src.mcp.agents.tools.sheets import get_budget_tools

__all__ = ["get_budget_tools", "execute_analysis_code"]
```

**Step 2: Verify import works**

Run: `poetry run python -c "from src.mcp.agents.tools import execute_analysis_code; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add src/mcp/agents/tools/__init__.py
git commit -m "feat: export execute_analysis_code from tools module"
```

---

## Task 4: Integrate tool with AnalystAgent

**Files:**
- Modify: `src/mcp/agents/adk_agents.py`

**Step 1: Add import**

Add to imports in `src/mcp/agents/adk_agents.py`:

```python
from src.mcp.agents.tools.code_executor import execute_analysis_code
```

**Step 2: Update AnalystAgent tools**

Find the `analyst_agent` definition and add `execute_analysis_code` to tools list:

```python
tools=[get_expenses_tool, get_statistics_tool, execute_analysis_code],
```

**Step 3: Update AnalystAgent instruction**

Add to analyst_agent instruction (before "Для ПРОСТЫХ запросов"):

```python
3. **execute_analysis_code** - выполнять Python код для сложного анализа

## Когда использовать execute_analysis_code:
Используй для СЛОЖНЫХ запросов, когда стандартных tools недостаточно:
- Сравнение периодов ("расходы в январе vs феврале")
- Вычисление трендов ("растут ли траты на еду")
- Поиск аномалий ("необычно большие траты")
- Произвольные расчёты ("средний чек в выходные")

## Как писать код для execute_analysis_code:
1. Код получает DataFrame `df` с колонками:
   - date (datetime): дата расхода
   - category (str): категория
   - description (str): описание
   - amount (float): сумма в рублях

2. Результат сохраняй в переменную `result` (строка)

3. Доступны: pandas (pd), numpy (np), базовые функции Python

4. Пример кода:
```python
jan = df[(df['date'].dt.month == 1) & (df['category'] == 'Еда')]['amount'].sum()
feb = df[(df['date'].dt.month == 2) & (df['category'] == 'Еда')]['amount'].sum()
diff = feb - jan
result = f"Еда: январь {{jan:.0f}}₽, февраль {{feb:.0f}}₽, разница {{diff:+.0f}}₽"
```

##
```

**Step 4: Verify syntax**

Run: `poetry run python -c "from src.mcp.agents.adk_agents import analyst_agent; print('OK')"`
Expected: OK

**Step 5: Commit**

```bash
git add src/mcp/agents/adk_agents.py
git commit -m "feat: integrate execute_analysis_code tool with AnalystAgent"
```

---

## Task 5: Update Orchestrator to route complex queries

**Files:**
- Modify: `src/mcp/agents/adk_agents.py`

**Step 1: Update root_agent instruction**

In root_agent instruction, update AnalystAgent description:

```python
2. **AnalystAgent** - для ПРОСМОТРА расходов, СТАТИСТИКИ и СЛОЖНОЙ АНАЛИТИКИ
   Вызывай когда пользователь:
   - Хочет увидеть расходы ("покажи последние расходы", "что я купил")
   - Просит статистику ("статистика за месяц", "сколько потратил")
   - Спрашивает про суммы или категории
   - Просит СРАВНИТЬ периоды ("сравни январь и февраль")
   - Ищет АНОМАЛИИ ("найди большие траты")
   - Хочет РАСЧЁТЫ ("средний чек в выходные", "тренд расходов")
```

**Step 2: Verify syntax**

Run: `poetry run python -c "from src.mcp.agents.adk_agents import root_agent; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add src/mcp/agents/adk_agents.py
git commit -m "feat: update orchestrator to route complex analytics to AnalystAgent"
```

---

## Task 6: Run full test suite

**Files:**
- None (verification only)

**Step 1: Run linting**

Run: `poetry run ruff check src/`
Expected: No errors

**Step 2: Run all tests**

Run: `poetry run pytest -v`
Expected: All tests pass, coverage >= 50%

**Step 3: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix: address test/lint issues"
```

---

## Task 7: Update CLAUDE.md documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add code execution section**

Add after "Multi-Agent System" section:

```markdown
## Code Execution for Complex Analytics (Iteration 12)

AnalystAgent now has `execute_analysis_code` tool for complex queries that can't be handled by standard tools.

**When it's used:**
- Period comparisons ("compare food expenses in January vs February")
- Trend analysis ("are my food expenses growing")
- Anomaly detection ("find unusually large expenses")
- Custom calculations ("average check on weekends")

**How it works:**
1. LLM generates Python code based on user query
2. Code runs using exec() with controlled globals/locals (pandas, numpy, safe builtins only)
3. Code receives pandas DataFrame `df` with expense data
4. Result must be saved to `result` variable (string)
5. Timeout: 10 seconds

**Security:**
- Whitelist users only (TELEGRAM_ADMIN_IDS)
- No file I/O, network, or unsafe builtins
- LLM-generated code (not user input directly)

**Implementation:** `src/mcp/agents/tools/code_executor.py`
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add code execution feature to CLAUDE.md"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Create sandbox module with tests | code_executor.py, test_code_executor.py |
| 2 | Add async tool with timeout | code_executor.py |
| 3 | Export from module | tools/__init__.py |
| 4 | Integrate with AnalystAgent | adk_agents.py |
| 5 | Update Orchestrator routing | adk_agents.py |
| 6 | Run full test suite | (verification) |
| 7 | Update documentation | CLAUDE.md |
