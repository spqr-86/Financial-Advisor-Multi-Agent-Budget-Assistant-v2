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
