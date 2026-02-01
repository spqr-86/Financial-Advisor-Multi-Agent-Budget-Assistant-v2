"""Code executor with exec() sandbox for complex analytics."""

import logging
from typing import Any

import numpy as np
import pandas as pd

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
