"""Code executor with exec() sandbox for complex analytics."""

import asyncio
import concurrent.futures
import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

EXECUTION_TIMEOUT = 10.0  # seconds

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


def execute_in_sandbox(code: str, df: pd.DataFrame) -> str:
    """
    Execute Python code in a restricted sandbox.

    Args:
        code: Python code to execute
        df: DataFrame with expenses data

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

    try:
        # Execute code in restricted environment
        safe_locals: dict[str, Any] = {}
        exec(code, safe_globals, safe_locals)

        # Extract result
        result = safe_locals.get("result", "Код не вернул результат")
        return str(result)

    except Exception as e:
        logger.warning(f"Code execution error: {e}")
        return f"Ошибка выполнения: {str(e)}"


async def _get_expenses_for_analysis(user_id: str, limit: int = 1000) -> dict[str, Any]:
    """Get expenses from storage for analysis."""
    from src.mcp.agents.tools.sheets import get_storage

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
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
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
